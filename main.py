"""Orquestador CrewAI: Arquitecto -> Backend -> Frontend -> QA -> Chapter, con guardrails y HITL."""
import logging
import re
import shutil
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from crewai import Crew, Process
from crewai.types.streaming import StreamChunkType
from lab_copilot.runtime import set_progress_listener
from crewai.events import crewai_event_bus
from crewai.events.types.agent_events import AgentExecutionStartedEvent, AgentExecutionCompletedEvent, AgentExecutionErrorEvent
from crewai.events.types.llm_events import LLMCallStartedEvent, LLMCallCompletedEvent, LLMCallFailedEvent
from crewai.events.types.tool_usage_events import ToolUsageStartedEvent, ToolUsageFinishedEvent, ToolUsageErrorEvent
from crewai.events.types.task_events import TaskStartedEvent, TaskCompletedEvent, TaskFailedEvent

from agents import architect, backend, frontend, testing, chapter
import qa_runner
# ── MCP clients ────────────────────────────────────────────────────
from mcp_projects import (
    list_tools,
    list_tools as proj_tools,
    list_projects,
    list_project_items,
    get_feature_from_item,
)

BASE = Path(__file__).parent
OUTPUT = BASE / "output"
DIRS = {
    "arquitectura": OUTPUT / "arquitectura",
    "api": OUTPUT / "api",
    "backend": OUTPUT / backend.OUTPUT_SUBDIR,
    "frontend": OUTPUT / frontend.OUTPUT_SUBDIR,
    "qa": OUTPUT / "qa",
    "informes": BASE / "informes",
}
OPENAPI_DIR = BASE / "client" / "openapi"
MAX_BACKEND_ATTEMPTS = 3
GUARDRAIL_MAX_RETRIES = 50

for d in (OUTPUT, *DIRS.values()):
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = OUTPUT / "ejecucion.log"


class _Tee:
    """Duplica todo lo que se imprime en consola (prints, streaming, tracebacks) en el archivo de log."""

    def __init__(self, stream, file):
        self._stream, self._file = stream, file

    def write(self, text):
        try:
            self._stream.write(text)
        except UnicodeEncodeError:
            self._stream.write(text.encode("ascii", "replace").decode("ascii"))
        self._stream.flush()
        self._file.write(text)
        self._file.flush()
        return len(text)

    def flush(self):
        self._stream.flush()
        self._file.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


if not isinstance(sys.stdout, _Tee):
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    _log_file = open(LOG_FILE, "a", encoding="utf-8")
    sys.stdout, sys.stderr = _Tee(sys.stdout, _log_file), _Tee(sys.stderr, _log_file)

log = logging.getLogger("digital_wallet")
if not log.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    log.addHandler(_handler)
    log.setLevel(logging.INFO)
    log.propagate = False

# ── Eventos en vivo de CrewAI ──────────────────────────────────────
_llm_started: dict = {}


def _short(value, limit: int = 300) -> str:
    text = str(value).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


_llm_progress = {"text": 0, "reasoning": 0, "next_report": 2000, "first_text": False, "first_reasoning": False}


def _on_model_progress(kind: str, info: dict) -> None:
    """Progreso en vivo del modelo Copilot: texto por consola y hitos en el log."""
    p = _llm_progress
    if kind == "start":
        p.update(text=0, reasoning=0, next_report=2000, first_text=False, first_reasoning=False)
        log.info("[LLM] Solicitud enviada a %s (prompt de %d caracteres). Esperando respuesta...",
                 info["model"], info["prompt_chars"])
    elif kind == "reasoning":
        p["reasoning"] += len(info["delta"])
        if not p["first_reasoning"]:
            p["first_reasoning"] = True
            log.info("[LLM] El modelo está razonando (%.1fs)...", info["elapsed"])
    elif kind == "text":
        if not p["first_text"]:
            p["first_text"] = True
            log.info("[LLM] Primer token recibido a los %.1fs. Generando respuesta...", info["elapsed"])
        p["text"] += len(info["delta"])
        print(info["delta"], end="", flush=True)
        if p["text"] >= p["next_report"]:
            log.info("[LLM] Generando... %d caracteres recibidos", p["text"])
            p["next_report"] += 2000
    elif kind == "wait":
        state = "generando" if p["first_text"] else "razonando" if p["first_reasoning"] else "esperando al modelo"
        log.info("[LLM] Sigue en curso (%.0fs, %s): razonamiento=%d car., texto=%d car.",
                 info["elapsed"], state, p["reasoning"], p["text"])
    elif kind == "tool":
        log.info("[TOOL] El modelo ejecuta: %s", info["name"])
    elif kind == "usage":
        log.info("[LLM] Uso: entrada=%s tokens, salida=%s tokens, primer token=%ss",
                 info.get("input_tokens"), info.get("output_tokens"), info.get("ttft"))
    elif kind == "end":
        log.info("[LLM] Respuesta completa: %d caracteres en %.1fs", info["chars"], info["elapsed"])
    elif kind == "error":
        log.error("[LLM] Error: %s", _short(info["message"]))


set_progress_listener(_on_model_progress)


@crewai_event_bus.on(TaskStartedEvent)
def _on_task_started(source, event):
    log.info("[TAREA] Tarea iniciada: %s", _short(getattr(event, "task_name", None) or getattr(getattr(event, "task", None), "description", ""), 120))


@crewai_event_bus.on(TaskCompletedEvent)
def _on_task_completed(source, event):
    log.info("[TAREA] Tarea completada")


@crewai_event_bus.on(TaskFailedEvent)
def _on_task_failed(source, event):
    log.error("[TAREA] Tarea fallida: %s", _short(getattr(event, "error", "")))


@crewai_event_bus.on(AgentExecutionStartedEvent)
def _on_agent_started(source, event):
    log.info("[AGENTE] Agente en ejecución: %s", getattr(getattr(event, "agent", None), "role", "?"))


@crewai_event_bus.on(AgentExecutionCompletedEvent)
def _on_agent_completed(source, event):
    log.info("[AGENTE] Agente terminó: %s", getattr(getattr(event, "agent", None), "role", "?"))


@crewai_event_bus.on(AgentExecutionErrorEvent)
def _on_agent_error(source, event):
    log.error("[AGENTE] Error del agente: %s", _short(getattr(event, "error", "")))


@crewai_event_bus.on(LLMCallStartedEvent)
def _on_llm_started(source, event):
    _llm_started[getattr(event, "call_id", None)] = time.time()
    log.info("[LLM] Solicitud al LLM (%s): %d mensajes", getattr(event, "model", "?"), len(getattr(event, "messages", None) or []))


@crewai_event_bus.on(LLMCallCompletedEvent)
def _on_llm_completed(source, event):
    started = _llm_started.pop(getattr(event, "call_id", None), None)
    elapsed = f" en {time.time() - started:.1f}s" if started else ""
    log.info("[LLM] LLM respondió%s", elapsed)


@crewai_event_bus.on(LLMCallFailedEvent)
def _on_llm_failed(source, event):
    log.error("[LLM] LLM falló: %s", _short(getattr(event, "error", "")))


@crewai_event_bus.on(ToolUsageStartedEvent)
def _on_tool_started(source, event):
    log.info("[TOOL] Herramienta: %s args=%s", getattr(event, "tool_name", "?"), _short(getattr(event, "tool_args", "")))


@crewai_event_bus.on(ToolUsageFinishedEvent)
def _on_tool_finished(source, event):
    log.info("[TOOL] Herramienta terminada: %s", getattr(event, "tool_name", "?"))


@crewai_event_bus.on(ToolUsageErrorEvent)
def _on_tool_error(source, event):
    log.error("[TOOL] Error en herramienta %s: %s", getattr(event, "tool_name", "?"), _short(getattr(event, "error", "")))


def _logged_guardrail(fn):
    """Envuelve un guardrail para registrar su veredicto en el log."""
    name = getattr(fn, "__name__", "guardrail")

    def wrapper(output):
        ok, detail = fn(output)
        if ok:
            log.info("[GUARDRAIL] %s: OK", name)
        else:
            log.warning("[GUARDRAIL] %s RECHAZÓ la salida: %s", name, _short(detail))
        return ok, detail

    wrapper.__name__ = name
    return wrapper


SECRET_RE = re.compile(r"(gho_|ghp_|sk-)[A-Za-z0-9_]+|api[_-]?key\s*[:=]\s*\S+", re.I)
INJECTION_RE = re.compile(r"ignore (all )?previous instructions|ignora (las )?instrucciones anteriores", re.I)


# ── Guardrails ─────────────────────────────────────────────────────
def guard_input(text: str) -> str:
    """Bloquea prompt injection, redacta secretos y limita el tamaño del input."""
    if INJECTION_RE.search(text):
        raise ValueError("Input bloqueado: posible prompt injection.")
    return SECRET_RE.sub("[REDACTED]", text)[:20000]


def guard_task_output(output):
    """Valida la salida del agente antes de aceptarla."""
    text = str(getattr(output, "raw", output) or "")
    if len(text.strip()) < 50:
        return False, "Salida vacía o demasiado corta. Regenera el contenido completo."
    if SECRET_RE.search(text):
        return False, "La salida contiene un secreto. Elimínalo y regenera."
    return True, text


# ── Utilidades ─────────────────────────────────────────────────────
def read_openapi() -> str:
    files = sorted(OPENAPI_DIR.glob("*.y*ml")) + sorted(OPENAPI_DIR.glob("*.json"))
    files += sorted((BASE / "client").glob("*openapi*.y*ml"))
    return "\n\n".join(f"# {f.name}\n{f.read_text(encoding='utf-8')[:8000]}" for f in files) or "(sin contratos)"


def read_informes() -> str:
    return "\n\n".join(f"## {f.name}\n{f.read_text(encoding='utf-8')}" for f in sorted(DIRS["informes"].glob("*.md")))


def save(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    log.info("Guardado: %s", path)


def make_task(module, feature: dict, context: str = "", guardrail=None):
    """Crea la Task del módulo de agente y le añade contexto y guardrail."""
    task = module.build_task(feature)
    task.description += context
    task.guardrail = _logged_guardrail(guardrail or guard_task_output)
    if guardrail:
        # Un guardrail específico reintenta hasta cumplirse; puede fijar su propio tope con .max_retries
        task.guardrail_max_retries = getattr(guardrail, "max_retries", GUARDRAIL_MAX_RETRIES)
    return task


def execute(agent, task) -> str:
    log.info("Ejecutando agente: %s (streaming)", agent.role)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False, stream=True)
    streaming = crew.kickoff()
    print(f"\n----- [{agent.role}] respuesta en vivo -----")
    chars, tool_calls, last_type = 0, 0, StreamChunkType.TEXT
    for chunk in streaming:
        if chunk.chunk_type == StreamChunkType.TOOL_CALL and chunk.tool_call:
            if chunk.tool_call.tool_name:
                tool_calls += 1
                log.info("[%s] llama a la herramienta: %s", agent.role, chunk.tool_call.tool_name)
            print(chunk.tool_call.arguments, end="", flush=True)
        else:
            if last_type == StreamChunkType.TOOL_CALL:
                print()
            print(chunk.content, end="", flush=True)
            chars += len(chunk.content)
        last_type = chunk.chunk_type
    print(f"\n----- [{agent.role}] fin -----")
    log.info("[%s] streaming completado (%d caracteres, %d llamadas a herramientas)", agent.role, chars, tool_calls)
    result = streaming.result
    return str(getattr(result, "raw", result))


# ── HITL ───────────────────────────────────────────────────────────
def run_with_hitl(module, feature: dict, context: str, max_attempts: int | None, guardrail=None) -> str:
    """Ejecuta el agente hasta aprobación humana. max_attempts=None significa sin límite."""
    feedback, attempt = "", 1
    while max_attempts is None or attempt <= max_attempts:
        text = execute(module.agent, make_task(module, feature, context + feedback, guardrail))
        log.info("%s: intento %d generado (%d caracteres)", module.LABEL, attempt, len(text))
        print(f"\n===== OUTPUT: {module.LABEL} (intento {attempt}, {len(text)} caracteres) — texto completo mostrado arriba =====\n")
        choice = input("[s] aprobar  [r] reintentar con feedback  [n] abortar: ").strip().lower()
        log.info("%s: decisión humana '%s'", module.LABEL, choice or "(vacía)")
        if choice == "s":
            return text
        if choice == "n":
            raise SystemExit(f"{module.LABEL}: abortado por el usuario.")
        comment = input("Feedback para el agente: ").strip()
        feedback = f"\n\n## Correcciones solicitadas por el humano\n{comment}"
        attempt += 1
    raise SystemExit(f"{module.LABEL}: sin aprobación tras {max_attempts} intentos. Ciclo cerrado.")


def ask_choice(prompt: str, valid: set[str]) -> str:
    """Pide una opción al usuario hasta recibir una válida y la registra en el log."""
    while True:
        choice = input(prompt).strip().lower()
        log.info("Decisión humana: '%s'", choice or "(vacía)")
        if choice in valid:
            return choice
        print("  Entrada inválida.")


# ── QA: servicios, Karate, Selenium y aprobación humana ────────────
def run_qa_stage(feature: dict, context: str, guardrail, backend_dir: Path, frontend_dir: Path) -> None:
    """Paso 0: el agente genera las pruebas. 1: levanta Backend y Frontend. 2: ejecuta Karate y Selenium.
    3: pausa para aprobación humana con un resumen. 4: genera output/qa/ e informes/testing.md."""
    feedback = ""

    def generate() -> dict[str, str]:
        text = execute(testing.agent, make_task(testing, feature, context + feedback, guardrail))
        generated = backend.parse_files(text)
        log.info("QA: %d archivos de prueba generados (%s)", len(generated), ", ".join(sorted(generated)))
        return generated

    files = generate()

    print("\n===== QA · Paso 1: entorno y servicios =====")
    checks = qa_runner.preflight(backend_dir, frontend_dir)
    print(qa_runner.format_preflight(checks))
    blocked = [c for c in checks if not c.ok and not c.action]
    skip_reason = ""
    if blocked:
        skip_reason = "faltan requisitos: " + "; ".join(f"{c.name} ({c.detail})" for c in blocked)
        log.error("QA: no se pueden levantar los servicios — %s", skip_reason)
    else:
        pending = [c.action for c in checks if not c.ok and c.action]
        print("\nSe levantarán el Backend (http://localhost:8000) y el Frontend (http://localhost:4200) ejecutando el código generado."
              + ("\nAcciones previas:\n" + "\n".join(f"  - {a}" for a in pending) if pending else ""))
        if ask_choice("[s] levantar servicios y ejecutar pruebas  [n] omitir (quedará NO EJECUTADO): ", {"s", "n"}) == "n":
            skip_reason = "ejecución omitida por el usuario"

    jar, python = None, None
    if not skip_reason:
        try:
            jar = qa_runner.karate_jar() or qa_runner.download_karate()
        except Exception as exc:
            log.error("QA: no se pudo obtener Karate: %s", exc)
        try:
            python = qa_runner.prepare_selenium_python()
        except Exception as exc:
            log.error("QA: no se pudo preparar Selenium: %s", exc)

    with (nullcontext() if skip_reason else qa_runner.Services(backend_dir, frontend_dir)) as services:
        statuses = services.start() if services else []
        for status in statuses:
            print(f"  {'OPERATIVO' if status.ok else 'CON ERROR'}: {status.name} {status.url} — {status.detail}")
        run = None
        while True:
            if run is not None:
                shutil.rmtree(run.workdir, ignore_errors=True)
            log.info("QA · Paso 2: ejecutando pruebas automatizadas (Karate y Selenium)")
            run = qa_runner.run_suites(files, statuses, jar, python, skip_reason)

            print("\n===== QA · Paso 3: resumen preliminar (pendiente de aprobación) =====")
            print(qa_runner.format_summary(run))
            choice = ask_choice("\n[s] aprobar y generar reportes  [r] regenerar pruebas con feedback y reejecutar  "
                                "[x] reejecutar sin cambios  [n] abortar: ", {"s", "r", "x", "n"})
            if choice == "n":
                shutil.rmtree(run.workdir, ignore_errors=True)
                raise SystemExit("QA: abortado por el usuario; no se generaron reportes.")
            if choice == "r":
                comment = input("Feedback para el agente: ").strip()
                feedback = (f"\n\n## Resultados de la ejecución anterior\n{qa_runner.format_summary(run)}"
                            f"\n\n## Correcciones solicitadas por el humano\n{comment}")
                files = generate()
            if choice == "s":
                break

    log.info("QA · Paso 4: generando output/qa/ e informes/testing.md")
    written = qa_runner.publish(run, files, DIRS["qa"], DIRS["informes"] / "testing.md", feature,
                                backend_dir.relative_to(BASE).as_posix(), frontend_dir.relative_to(BASE).as_posix())
    for path in written:
        log.info("Guardado: %s", path)
    log.info("QA: resultado global %s", qa_runner.global_status(run))


# ── Main ───────────────────────────────────────────────────────────
def main():
    print("\n[MCP Proyectos] Autenticando...")
    log.info("Inicio del flujo. Conectando a MCP Proyectos.")
    list_tools()
    print("[MCP Proyectos] Herramientas cargadas correctamente.")

    projects = list_projects()
    log.info("Proyectos encontrados: %d", len(projects))
    if not projects:
        raise SystemExit("[MCP Proyectos] No se encontraron proyectos.")

    if len(projects) == 1:
        selected_project = projects[0]
        print(f"\n[MCP Proyectos] Proyecto asignado: {selected_project['title']}")
    else:
        print("\n[MCP Proyectos] Proyectos disponibles:")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project.get('title', '(sin título)')}")

        while True:
            selection = input(
                f"\nSelecciona el número de proyecto [1-{len(projects)}]: "
            ).strip()
            if selection.isdigit() and 1 <= int(selection) <= len(projects):
                selected_project = projects[int(selection) - 1]
                break
            print("  Entrada inválida.")

    log.info("Proyecto seleccionado: %s", selected_project["title"])
    backlog = list_project_items(selected_project["id"])
    log.info("Items en el backlog: %d", len(backlog))
    if not backlog:
        raise SystemExit("[MCP Proyectos] El proyecto no tiene items en el backlog.")

    print(f"\n[MCP Proyectos] Backlog de '{selected_project['title']}':")
    for i, item in enumerate(backlog, 1):
        number = f"#{item['number']} — " if item.get("number") else ""
        print(f"  {i}. {number}{item.get('title', '(sin título)')}")

    while True:
        selection = input(
            f"\nSelecciona el número de issue/feature [1-{len(backlog)}]: "
        ).strip()
        if selection.isdigit() and 1 <= int(selection) <= len(backlog):
            selected_item = backlog[int(selection) - 1]
            break
        print("  Entrada inválida.")

    log.info("Item seleccionado: %s", selected_item.get("title"))
    feature = get_feature_from_item(selected_item)
    log.info("Issue cargado: %s (%d criterios de aceptación)",
             feature["title"], len(feature.get("acceptance_criteria", [])))
    print(f"\n[MCP Proyectos] Issue cargado: {feature['title']}")

    openapi = read_openapi()

    # Continúa aquí el flujo actual: Arquitecto -> Backend -> Frontend -> QA -> Chapter
    log.info("Inicia Arquitecto")

    # 1. Arquitecto: diagramas, OpenAPI e informe; aprobación humana obligatoria
    arch_text = run_with_hitl(architect, feature,
                              f"\n\n## Contratos OpenAPI disponibles\n{openapi}",
                              max_attempts=None, guardrail=architect.validate_output)
    log.info("Arquitecto aprobado. Guardando artefactos.")
    
    sections = architect.parse_sections(arch_text)
    arch_artifacts = {
        "architecture.mmd": architect.extract_block(sections["ARQUITECTURA"]),
        "sequence.mmd": architect.extract_block(sections["SECUENCIA"]),
        "openapi.yaml": architect.extract_block(sections["OPENAPI"]),
    }
    for name, content in arch_artifacts.items():
        save(DIRS["arquitectura"] / name, content)
    save(DIRS["informes"] / f"{architect.KEY}.md", sections["INFORME"])

    # 2. Backend: recibe architecture.mmd, sequence.mmd y openapi.yaml aprobados e implementa FastAPI en output/backend-python/api
    log.info("Inicia Backend (máximo %d intentos). Destino: %s", MAX_BACKEND_ATTEMPTS, DIRS["backend"])
    backend_context = (
        f"\n\n## Diagrama de arquitectura (Mermaid) — architecture.mmd\n```mermaid\n{arch_artifacts['architecture.mmd']}\n```"
        f"\n\n## Diagrama de secuencia (Mermaid) — sequence.mmd\n```mermaid\n{arch_artifacts['sequence.mmd']}\n```"
        f"\n\n## Contrato OpenAPI del API local — openapi.yaml\n```yaml\n{arch_artifacts['openapi.yaml']}\n```"
        f"\n\n## Contratos OpenAPI de servicios externos (client/openapi)\n{openapi}"
    )
    backend_text = run_with_hitl(backend, feature, backend_context, max_attempts=MAX_BACKEND_ATTEMPTS,
                                 guardrail=backend.build_guardrail(arch_artifacts["openapi.yaml"]))
    backend_files = backend.parse_files(backend_text)
    written, removed = backend.sync_project(backend_files, DIRS["backend"])
    for path in written:
        log.info("Guardado: %s", path)
    for path in removed:
        log.info("Eliminado (obsoleto de una generación anterior): %s", path)
    log.info("Backend: proyecto completo con %d archivos en %s", len(backend_files), DIRS["backend"])
    backend_report = (
        "# Informe Backend\n\nProyecto FastAPI completo generado a partir de architecture.mmd, sequence.mmd y openapi.yaml.\n\n"
        f"Carpeta: `{DIRS['backend'].relative_to(BASE).as_posix()}`\n\n"
        "Ejecución: `pip install -r requirements.txt` y `uvicorn app.main:app --reload` (puerto 8000); pruebas: `pytest`.\n\n"
        "## Archivos\n" + "\n".join(f"- `{p}`" for p in sorted(backend_files)) + "\n"
    )
    save(DIRS["informes"] / f"{backend.KEY}.md", backend_report)

    # 3. Frontend: recibe architecture.mmd, sequence.mmd y el API Python del Backend; implementa Angular en output/frontend-angular/web
    log.info("Inicia Frontend. Destino: %s", DIRS["frontend"])
    backend_sources = "\n\n".join(
        f"### {p}\n```python\n{c}```" for p, c in sorted(backend_files.items()) if p.endswith(".py"))
    served = backend.runtime_routes(backend_files) or backend.served_routes(backend_files)
    served_list = "\n".join(f"- {m} {p}" for m, p in sorted(served, key=lambda r: (r[1], r[0])))
    log.info("Rutas expuestas por el Backend (%d):\n%s", len(served), served_list)
    frontend_context = (
        f"\n\n## Diagrama de arquitectura (Mermaid) — architecture.mmd\n```mermaid\n{arch_artifacts['architecture.mmd']}\n```"
        f"\n\n## Diagrama de secuencia (Mermaid) — sequence.mmd\n```mermaid\n{arch_artifacts['sequence.mmd']}\n```"
        f"\n\n## Rutas expuestas por el Backend (http://localhost:8000) — consúmelas todas\n{served_list}"
        f"\n\n## Contrato OpenAPI del API Python — openapi.yaml\n```yaml\n{arch_artifacts['openapi.yaml']}\n```"
        f"\n\n## Código del API Python generado por el Backend\n{backend_sources}"
    )
    frontend_text = execute(frontend.agent, make_task(frontend, feature, frontend_context,
                            frontend.build_guardrail(arch_artifacts["openapi.yaml"], served)))
    frontend_files = frontend.parse_files(frontend_text)
    for path in frontend.write_files(frontend_files, DIRS["frontend"]):
        log.info("Guardado: %s", path)
    log.info("Frontend: %d archivos escritos en %s", len(frontend_files), DIRS["frontend"])
    frontend_report = (
        "# Informe Frontend\n\nAplicación Angular que consume el API Python del Backend, generada a partir de "
        "architecture.mmd, sequence.mmd y openapi.yaml.\n\n"
        f"Carpeta: `{DIRS['frontend'].relative_to(BASE).as_posix()}` (ejecutar con `npm install` y `npm start`)\n\n## Archivos\n"
        + "\n".join(f"- `{p}`" for p in sorted(frontend_files)) + "\n"
    )
    save(DIRS["informes"] / f"{frontend.KEY}.md", frontend_report)

    # 4. QA: genera pruebas Karate/Selenium, levanta los servicios, las ejecuta y pide aprobación humana antes de reportar
    log.info("Inicia QA")
    app_sources = "\n\n".join(
        f"### {p}\n```python\n{c[:6000]}```" for p, c in sorted(backend_files.items())
        if p.startswith("app/") and p.endswith(".py"))
    ui_sources = "\n\n".join(
        f"### {p}\n```\n{c[:6000]}\n```" for p, c in sorted(frontend_files.items())
        if p.startswith("src/app/") and p.endswith((".html", ".ts")))
    qa_context = (
        f"\n\n## Rutas reales del Backend (http://localhost:8000) — cubre todas con Karate\n{served_list}"
        f"\n\n## Contrato OpenAPI del API\n```yaml\n{arch_artifacts['openapi.yaml']}\n```"
        f"\n\n## Código del Backend (modelos y routers, para validar esquemas y errores)\n{app_sources}"
        f"\n\n## Código del Frontend Angular (http://localhost:4200) — usa SOLO selectores que existan aquí\n{ui_sources}"
    )
    qa_guardrail = testing.build_guardrail(served, backend.spec_routes(arch_artifacts["openapi.yaml"]), frontend_files)
    run_qa_stage(feature, qa_context, qa_guardrail, DIRS["backend"], DIRS["frontend"])

    # 5. Chapter (revisión final a partir de los informes)
    log.info("Inicia Chapter")
    chapter_text = execute(chapter.agent, make_task(chapter, feature,
                           f"\n\n## Informes de los agentes\n{read_informes()}"))
    save(DIRS["informes"] / chapter.SPEC_FILE, chapter_text)

    log.info("Flujo completado. Log guardado en %s", LOG_FILE)
    print("\nFlujo completado. Veredicto del Chapter (extracto):")
    print(chapter_text[-800:])


if __name__ == "__main__":
    main()