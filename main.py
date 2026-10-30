"""Orquestador CrewAI: Arquitecto -> Backend -> Frontend -> QA -> Chapter, con guardrails y HITL."""
import logging
import re
from pathlib import Path
from crewai import Crew, Process

from agents import architect, backend, frontend, testing, chapter
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
    "web": OUTPUT / "web",
    "qa": OUTPUT / "qa",
    "informes": BASE / "informes",
}
OPENAPI_DIR = BASE / "client" / "openapi"
MAX_BACKEND_ATTEMPTS = 3

for d in (OUTPUT, *DIRS.values()):
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = OUTPUT / "ejecucion.log"
log = logging.getLogger("digital_wallet")
if not log.handlers:
    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    for _handler in (logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")):
        _handler.setFormatter(_fmt)
        log.addHandler(_handler)
    log.setLevel(logging.INFO)
    log.propagate = False

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
    task.guardrail = guardrail or guard_task_output
    return task


def execute(agent, task) -> str:
    log.info("Ejecutando agente: %s", agent.role)
    result = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True).kickoff()
    return str(getattr(result, "raw", result))


# ── HITL ───────────────────────────────────────────────────────────
def run_with_hitl(module, feature: dict, context: str, max_attempts: int | None, guardrail=None) -> str:
    """Ejecuta el agente hasta aprobación humana. max_attempts=None significa sin límite."""
    feedback, attempt = "", 1
    while max_attempts is None or attempt <= max_attempts:
        text = execute(module.agent, make_task(module, feature, context + feedback, guardrail))
        log.info("%s: intento %d generado (%d caracteres)", module.LABEL, attempt, len(text))
        print(f"\n===== OUTPUT: {module.LABEL} (intento {attempt}) =====\n{text[:3000]}\n")
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

    # 2. Backend: recibe solo los tres artefactos aprobados (HITL con máximo de intentos)
    log.info("Inicia Backend (máximo %d intentos)", MAX_BACKEND_ATTEMPTS)
    backend_context = (
        f"\n\n## Diagrama de arquitectura (Mermaid)\n```mermaid\n{arch_artifacts['architecture.mmd']}\n```"
        f"\n\n## Diagrama de secuencia (Mermaid)\n```mermaid\n{arch_artifacts['sequence.mmd']}\n```"
        f"\n\n## Contrato OpenAPI\n```yaml\n{arch_artifacts['openapi.yaml']}\n```"
    )
    backend_text = run_with_hitl(backend, feature, backend_context, max_attempts=MAX_BACKEND_ATTEMPTS)
    save(DIRS["api"] / f"{backend.KEY}.md", backend_text)
    save(DIRS["informes"] / f"{backend.KEY}.md", backend_text)

    # 3. Frontend
    log.info("Inicia Frontend")
    frontend_text = execute(frontend.agent, make_task(frontend, feature,
                            f"\n\n## Endpoints implementados por el Backend\n{backend_text}"))
    save(DIRS["web"] / f"{frontend.KEY}.md", frontend_text)
    save(DIRS["informes"] / f"{frontend.KEY}.md", frontend_text)

    # 4. QA
    log.info("Inicia QA")
    qa_text = execute(testing.agent, make_task(testing, feature,
                      f"\n\n## Contrato y implementación del Backend\n{backend_text}"))
    save(DIRS["qa"] / f"{testing.KEY}.md", qa_text)
    save(DIRS["informes"] / f"{testing.KEY}.md", qa_text)

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