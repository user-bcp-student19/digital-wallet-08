"""Orquestador CrewAI: Arquitecto -> Backend -> Frontend -> QA -> Chapter, con guardrails y HITL."""
import re
from pathlib import Path
from crewai import Crew, Process

from agents import architect, backend, frontend, testing, chapter
from mcp_github import fetch_issues  # Cliente MCP de GitHub pendiente de crear

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
    print(f"  Guardado: {path}")


def make_task(module, feature: dict, context: str = "", guardrail=None):
    """Crea la Task del módulo de agente y le añade contexto y guardrail."""
    task = module.build_task(feature)
    task.description += context
    task.guardrail = guardrail or guard_task_output
    return task


def execute(agent, task) -> str:
    result = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True).kickoff()
    return str(getattr(result, "raw", result))


# ── HITL ───────────────────────────────────────────────────────────
def run_with_hitl(module, feature: dict, context: str, max_attempts: int | None, guardrail=None) -> str:
    """Ejecuta el agente hasta aprobación humana. max_attempts=None significa sin límite."""
    feedback, attempt = "", 1
    while max_attempts is None or attempt <= max_attempts:
        text = execute(module.agent, make_task(module, feature, context + feedback, guardrail))
        print(f"\n===== OUTPUT: {module.LABEL} (intento {attempt}) =====\n{text[:3000]}\n")
        choice = input("[s] aprobar  [r] reintentar con feedback  [n] abortar: ").strip().lower()
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
    issues = fetch_issues()  # Lista de dicts con number, title y body
    if not issues:
        raise SystemExit("No se encontraron issues en el repositorio.")

    requirements = guard_input("\n".join(f"#{i['number']} {i['title']}\n{i.get('body', '')}" for i in issues))
    feature = {
        "title": "Issues de digital-wallet-08",
        "description": requirements,
        "acceptance_criteria": [f"#{i['number']} {i['title']}" for i in issues],
    }
    openapi = read_openapi()

    # 1. Arquitecto: diagramas, OpenAPI e informe; aprobación humana obligatoria
    arch_text = run_with_hitl(architect, feature,
                              f"\n\n## Contratos OpenAPI disponibles\n{openapi}",
                              max_attempts=None, guardrail=architect.validate_output)
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
    backend_context = (
        f"\n\n## Diagrama de arquitectura (Mermaid)\n```mermaid\n{arch_artifacts['architecture.mmd']}\n```"
        f"\n\n## Diagrama de secuencia (Mermaid)\n```mermaid\n{arch_artifacts['sequence.mmd']}\n```"
        f"\n\n## Contrato OpenAPI\n```yaml\n{arch_artifacts['openapi.yaml']}\n```"
    )
    backend_text = run_with_hitl(backend, feature, backend_context, max_attempts=MAX_BACKEND_ATTEMPTS)
    save(DIRS["api"] / f"{backend.KEY}.md", backend_text)
    save(DIRS["informes"] / f"{backend.KEY}.md", backend_text)

    # 3. Frontend
    frontend_text = execute(frontend.agent, make_task(frontend, feature,
                            f"\n\n## Endpoints implementados por el Backend\n{backend_text}"))
    save(DIRS["web"] / f"{frontend.KEY}.md", frontend_text)
    save(DIRS["informes"] / f"{frontend.KEY}.md", frontend_text)

    # 4. QA
    qa_text = execute(testing.agent, make_task(testing, feature,
                      f"\n\n## Contrato y implementación del Backend\n{backend_text}"))
    save(DIRS["qa"] / f"{testing.KEY}.md", qa_text)
    save(DIRS["informes"] / f"{testing.KEY}.md", qa_text)

    # 5. Chapter (revisión final a partir de los informes)
    chapter_text = execute(chapter.agent, make_task(chapter, feature,
                           f"\n\n## Informes de los agentes\n{read_informes()}"))
    save(DIRS["informes"] / chapter.SPEC_FILE, chapter_text)

    print("\nFlujo completado. Veredicto del Chapter (extracto):")
    print(chapter_text[-800:])


if __name__ == "__main__":
    main()