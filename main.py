"""Orquestador SDD: un item de GitHub Projects pasa por cada rol con aprobación humana."""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    # En consolas de Windows (cp1252) los emojis de CrewAI rompen los paneles de progreso.
    stream.reconfigure(encoding="utf-8", errors="replace")

from crewai import Crew, Process

# crew.workflow carga .env (vía crew.llm_config) antes de que mcp_projects lea sus variables.
from agents import architect, backend, frontend, specifier
from crew.dev_loop import render_report, verify_gates
from crew.task_status import mark_done
from crew.workflow import build_tasks, include_data, redo_from, workflow_steps
from mcp_projects import list_project_items, list_projects

BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "output"
CHECKPOINT_FILE = OUTPUT_DIR / ".checkpoint.json"
OPENSPEC_DIR = BASE / "openspec"
OPENAPI_DIR = BASE / "client" / "openapi"
# Roles que escriben código con herramientas y cuyas compuertas marcan tareas de tasks.md.
CODE_ROLES = {"backend": backend, "frontend": frontend}

SECRET_RE = re.compile(r"(gho_|ghp_|sk-)[A-Za-z0-9_]+|api[_-]?key\s*[:=]\s*\S+", re.I)
INJECTION_RE = re.compile(r"ignore (all )?previous instructions|ignora (las )?instrucciones anteriores", re.I)
CODE_BLOCK_RE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)
FILE_HEADER_RE = re.compile(r"^(?:#|//|--)\s*([\w.\-]+\.\w+)$")
ROUTE_RE = re.compile(r"@(?:router|app)\.(get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']")


# ── Guardrails ─────────────────────────────────────────────────────
def guard_input(text: str) -> str:
    """Bloquea prompt injection, redacta secretos y limita el tamaño del input."""
    if INJECTION_RE.search(text):
        raise ValueError("Input bloqueado: posible prompt injection.")
    return SECRET_RE.sub("[REDACTED]", text)[:20000]


def proj_tools() -> list:
    """Herramientas MCP expuestas a los agentes. Vacía: CopilotLLM no ejecuta herramientas en S1."""
    return []


# ── Utilidades ─────────────────────────────────────────────────────
def read_openapi() -> str:
    files = sorted(OPENAPI_DIR.glob("*.y*ml")) + sorted(OPENAPI_DIR.glob("*.json"))
    files += sorted((BASE / "client").glob("*openapi*.y*ml"))
    return "\n\n".join(f"# {f.name}\n{f.read_text(encoding='utf-8')[:8000]}" for f in files) or "(sin contratos)"


def save(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  Guardado: {path}")


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def backend_routes(change: Path) -> str:
    """Endpoints HTTP que el backend ya implementó. El frontend solo puede consumir estos."""
    base = change / "code" / "backend" / "app"
    routes = [f"{method.upper()} {path}"
              for file in sorted(base.rglob("*.py"))
              for method, path in ROUTE_RE.findall(file.read_text(encoding="utf-8"))]
    return "\n".join(f"- {route}" for route in routes) or "(el backend aún no expone endpoints)"


# ── Checkpoint ─────────────────────────────────────────────────────
def load_checkpoint() -> dict | None:
    if not CHECKPOINT_FILE.exists():
        return None
    return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))


def save_checkpoint(state: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Artefactos ─────────────────────────────────────────────────────
def extract_files(text: str) -> dict[str, str]:
    """Devuelve {nombre: contenido} de los bloques de código que empiezan con '# nombre.ext' (o // o --)."""
    files = {}
    for block in CODE_BLOCK_RE.findall(text):
        lines = block.strip("\n").split("\n", 1)
        match = FILE_HEADER_RE.match(lines[0].strip())
        if match and len(lines) > 1:
            files[Path(match.group(1)).name] = lines[1]
    return files


def code_path(key: str, name: str) -> Path:
    """Ruta relativa dentro de code/ del cambio OpenSpec."""
    if key == "data":
        return Path("db") / name
    if key == "backend":
        return Path("backend") / name
    if key == "frontend":
        return Path("frontend") / name
    base = "backend/tests" if name.endswith(".py") else "frontend/tests"
    return Path(base) / name


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "feature"


def change_dir(feature: dict) -> Path:
    return OPENSPEC_DIR / "changes" / slugify(feature["title"])


def openspec_artifacts(key: str, output: str) -> dict[str, str]:
    """Archivos del cambio OpenSpec (ruta relativa al cambio) que aporta un paso. Vacío si no aporta ninguno."""
    if key == "specs":
        proposal, capabilities = specifier.parse_specification(output)
        files = {"proposal.md": proposal + "\n"}
        files.update({f"specs/{name}/spec.md": body + "\n" for name, body in capabilities.items()})
        return files
    if key == "architect":
        return architect.openspec_files(output)
    return {}


def run_openspec_validate(name: str, cwd: Path = BASE) -> tuple[bool, str]:
    cli = shutil.which("openspec")
    if cli is None:
        return False, "OpenSpec CLI no encontrada. Instálala con: npm install -g @fission-ai/openspec"
    result = subprocess.run([cli, "validate", name, "--strict", "--no-interactive"], cwd=cwd,
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def check_output(key: str, change: Path, output: str) -> str:
    """Aviso si la salida no cumple su formato. Valida el cambio con OpenSpec en una copia temporal."""
    if key == "architect":
        valid, message = architect.validate_output(output)
        if not valid:
            return message
    if key not in ("specs", "architect"):
        return ""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "openspec" / "changes" / change.name
        target.parent.mkdir(parents=True)
        shutil.copy(OPENSPEC_DIR / "config.yaml", root / "openspec" / "config.yaml")
        if change.exists():
            shutil.copytree(change, target)
        for rel, text in openspec_artifacts(key, output).items():
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            (target / rel).write_text(text, encoding="utf-8")
        valid, message = run_openspec_validate(change.name, cwd=root)
    return "" if valid else message


def save_deliverables(key: str, spec_file: str, output: str, extracts_code: bool, change: Path,
                      overwrite: bool = True) -> None:
    """Escribe en disco todo lo que aporta un paso: artefactos OpenSpec o informe, y código si aplica.

    Se llama antes de la decisión humana para que el revisor pueda abrir los archivos.
    Un reintento sobrescribe el borrador anterior. Con overwrite=False (paso reutilizado)
    conserva los archivos existentes, para no perder ediciones humanas ni marcas de tareas.
    """
    def write(path: Path, text: str) -> None:
        if not overwrite and path.exists():
            print(f"  Conservado (ya existe): {path}")
            return
        save(path, text)

    artifacts = openspec_artifacts(key, output)
    if artifacts:
        for rel, text in artifacts.items():
            write(change / rel, text)
    else:
        write(change / "reports" / spec_file, output)
    if not extracts_code:
        return
    files = extract_files(output)
    if not files:
        print(f"  Aviso: {key} no entregó archivos con nombre en sus bloques de código.")
    for name, content in files.items():
        write(change / "code" / code_path(key, name), content)


# ── Ejecución y HITL ───────────────────────────────────────────────
def choose(options: list[dict], prompt: str) -> dict:
    if not options:
        fail("No hay opciones disponibles en GitHub Projects.")
    for number, option in enumerate(options, 1):
        print(f"  {number}. {option.get('title', option)}")
    try:
        index = int(input(prompt).strip()) - 1
    except ValueError:
        fail("Selección no válida.")
    if not 0 <= index < len(options):
        fail("Selección fuera de rango.")
    return options[index]


def run_step(agent, task) -> str:
    result = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True).kickoff()
    return str(getattr(result, "raw", result))


def run_role(key: str, agent, task, change: Path) -> tuple[str, bool | None]:
    """Backend y frontend escriben y prueban su código con herramientas; el resto responde en texto.

    Devuelve (salida, compuertas en verde). Para los pasos sin compuertas, el segundo valor es None.
    """
    module = CODE_ROLES.get(key)
    if module:
        workspace = change / "code" / key
        result = module.develop(task.description, workspace)
        return render_report(result, workspace, module.LABEL), result.approved
    return run_step(agent, task), None


def backend_context(key: str, change: Path) -> list[tuple[str, str]]:
    """Contexto extra por paso: el frontend recibe los endpoints reales que ya expone el backend."""
    if key == "frontend":
        return [("Endpoints del backend (solo estos puedes consumir)", backend_routes(change))]
    return []


def hitl_approve(label: str, result: str) -> tuple[str, str]:
    """Muestra la salida y devuelve (decisión, feedback). Decisión: s aprobar, r reintentar, n abortar."""
    print(f"\n===== OUTPUT: {label} =====\n{result}\n")
    while True:
        choice = input("[s] aprobar  [r] reintentar con feedback  [n] abortar: ").strip().lower()
        if choice in ("s", "n"):
            return choice, ""
        if choice == "r":
            return choice, input("Feedback para el agente: ").strip()
        print("Opción no válida.")


def build_step_task(key: str, feature: dict, with_data: bool, context: list[tuple[str, str]], feedback: str):
    task = build_tasks(feature, with_data)[key]
    task.description += "".join(f"\n\n## {label}\n{text}" for label, text in context) + feedback
    return task


# ── Main ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Flujo SDD con aprobación humana por paso.")
    parser.add_argument("--redo", default="",
                        help="Pasos a regenerar, separados por coma (p. ej. frontend). Incluye los posteriores.")
    args, _ = parser.parse_known_args()
    with_data = include_data()
    step_keys = [key for key, *_ in workflow_steps(with_data)]
    try:
        rerun = redo_from(step_keys, {key.strip() for key in args.redo.split(",") if key.strip()})
    except ValueError as error:
        fail(str(error))
    checkpoint = load_checkpoint()
    if checkpoint and checkpoint["mode"] != with_data:
        fail(f"El checkpoint se creó con CREWAI_INCLUDE_DATA={str(checkpoint['mode']).lower()}. "
             f"Cambia la variable o elimina {CHECKPOINT_FILE}.")

    project = choose(list_projects(), "Proyecto: ")
    item = choose(list_project_items(project["id"]), "Item: ")
    feature = architect.load_issue(item)
    feature = {**feature, "description": guard_input(str(feature.get("description", "")))}

    if checkpoint and checkpoint["feature"]["title"] != feature["title"]:
        fail(f"El checkpoint pertenece a '{checkpoint['feature']['title']}'. "
             f"Elimina {CHECKPOINT_FILE} para trabajar otro item.")
    if not (OPENSPEC_DIR / "config.yaml").exists():
        fail("Falta openspec/config.yaml. Ejecuta: openspec init --tools none --no-animation .")
    state = checkpoint or {"mode": with_data, "feature": feature, "steps": {}}
    for key in rerun:
        state["steps"].pop(key, None)
    if rerun:
        print(f"Regenerando desde: {', '.join(key for key in step_keys if key in rerun)}")
    change = change_dir(feature)
    print(f"\nCambio OpenSpec: {change}")

    context = [("Contratos OpenAPI de client/openapi", read_openapi())]
    tasks_file = change / "tasks.md"
    for key, label, agent, spec_file, extracts_code in workflow_steps(with_data):
        record = state["steps"].get(key, {})
        module = CODE_ROLES.get(key)
        if record.get("status") == "approved":
            print(f"\n[{label}] aprobado previamente; se reutiliza su salida.")
            save_deliverables(key, spec_file, record["output"], extracts_code, change, overwrite=False)
            if module:
                green = record.get("green")
                if green is None:
                    green, _ = verify_gates(change / "code" / key, module.PROFILE)
                    print(f"  Compuertas de {label}: {'EN VERDE' if green else 'FALLAN'}")
                print(f"  Tareas marcadas: {mark_done(tasks_file, key, bool(green))}")
            context.append((label, record["output"]))
            continue

        feedback = ""
        while True:
            print(f"\n>>> Ejecutando: {label}")
            task = build_step_task(key, feature, with_data, context + backend_context(key, change), feedback)
            output, green = run_role(key, agent, task, change)
            save_deliverables(key, spec_file, output, extracts_code, change)
            print(f"Borradores escritos en: {change}")
            message = check_output(key, change, output)
            if message:
                print(f"Aviso de validación: {message}")
            decision, comment = hitl_approve(label, output)
            if decision == "s":
                break
            if decision == "n":
                state["steps"][key] = {"status": "rejected"}
                save_checkpoint(state)
                fail(f"{label}: abortado por el usuario.")
            feedback += f"\n\n## Correcciones solicitadas por el humano\n{comment}"

        state["steps"][key] = {"status": "approved", "output": output, "green": green}
        save_checkpoint(state)
        if module:
            print(f"  Tareas marcadas: {mark_done(tasks_file, key, bool(green))}")
        context.append((label, output))

    valid, message = run_openspec_validate(change.name)
    print(f"\nValidación OpenSpec del cambio '{change.name}': {'OK' if valid else 'ERRORES'}")
    if message:
        print(message)
    print(f"\nFlujo completado. Artefactos OpenSpec y código en {change}")


if __name__ == "__main__":
    main()
