"""Arquitecto: genera diagramas Mermaid, contrato OpenAPI y su informe."""
import re
from crewai import Agent, Task
from agents.brief import feature_brief
from crew.llm_config import llm
import mcp_projects

KEY = 'architect'
LABEL = 'Arquitecto'
SPEC_FILE = 'architect.md'
EXTRACT_CODE = False

MARKERS = ["ARQUITECTURA", "SECUENCIA", "OPENAPI", "INFORME", "TAREAS"]

INSTRUCTIONS = """Actúa como Arquitecto de Software en un flujo de Specification-Driven Development (SDD) con OpenSpec.
Analiza la propuesta y las especificaciones OpenSpec aprobadas, el Issue, sus criterios de aceptación y los contratos OpenAPI de `client/openapi/`.
Cada requisito de la especificación debe tener un componente que lo cumpla.
Diseña la solución completa, considerando que, cuando sea necesario, habrá que crear:
- Contratos OpenAPI propios del API local (no existen contratos previos para ese alcance).
- Un microservicio en FastAPI que exponga esos contratos y consuma las APIs externas de `client/openapi/`.
- Una base de datos temporal (por ejemplo SQLite en un archivo o en memoria) para la persistencia del caso, si el Issue la requiere y no existe un contrato de datos definido.
Indica en el informe qué componentes se crean, cuáles se reutilizan y por qué. No añadas componentes que el Issue no necesite.
Diseña la solución y entrega EXACTAMENTE estas secciones, en este orden, con sus marcadores:

<<<ARQUITECTURA>>>
Diagrama de arquitectura en un bloque ```mermaid ... ``` (componentes, límites, microservicio, base de datos temporal y servicios externos).

<<<SECUENCIA>>>
Diagrama de secuencia en un bloque ```mermaid ... ``` (recorrido de la petición, incluidas las pasarelas externas y la base de datos).

<<<OPENAPI>>>
Contrato OpenAPI 3.0 del API local del microservicio en un bloque ```yaml ... ``` (paths, métodos, esquemas, respuestas y errores).
Si el flujo consume servicios externos, refleja en el contrato cómo se mapean sus respuestas según los archivos de client/openapi/.

<<<INFORME>>>
Informe Markdown con: resumen y alcance, componentes a crear y componentes reutilizados (microservicio, base de datos temporal, contratos),
responsabilidades, APIs externas de client/openapi utilizadas, esquema de la base de datos temporal (tablas y campos),
trazabilidad de cada criterio de aceptación al componente que lo resuelve, supuestos y preguntas pendientes.

<<<TAREAS>>>
Lista de tareas de implementación en formato OpenSpec: grupos `## 1. Nombre del grupo [backend]` y tareas `- [ ] 1.1 descripción`,
en orden de implementación (base de datos temporal, microservicio, frontend, pruebas). La etiqueta final del grupo indica quién lo implementa: `[backend]`, `[frontend]` o `[testing]`. Cada tarea referencia el requisito que cumple.

<<<FIN>>>

No inventes endpoints ni comportamiento que no sean necesarios para el Issue.
"""

agent = Agent(
    role='Arquitecto de Software',
    goal='Producir diagramas Mermaid de arquitectura y secuencia, el contrato OpenAPI del API local y el informe de diseño.',
    backstory='Architect Senior experto en integraciones de pasarelas de pago y diseño de contratos OpenAPI.',
    llm=llm,
    verbose=True,
    allow_delegation=False,
    human_input=False,  # La aprobación humana la gestiona main.py
)


def load_issue(item: dict) -> dict:
    """Se conecta al MCP de GitHub Projects y devuelve el issue (título, body, criterios) del item."""
    return mcp_projects.get_feature_from_item(item)


def parse_sections(text: str) -> dict[str, str]:
    """Separa la salida del agente en secciones según los marcadores <<<NOMBRE>>>."""
    parts = re.split(r"<<<(ARQUITECTURA|SECUENCIA|OPENAPI|INFORME|TAREAS)>>>", text)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def extract_block(section: str) -> str:
    """Devuelve el contenido del primer bloque de código de una sección."""
    match = re.search(r"```[a-zA-Z]*\n(.*?)```", section, re.DOTALL)
    return match.group(1).strip() if match else section.strip()


def openspec_files(output: str) -> dict[str, str]:
    """Convierte la salida aprobada en los archivos del cambio: design.md, tasks.md y openapi.yaml."""
    sections = parse_sections(output)
    design = (
        "# Diseño\n\n## Arquitectura\n\n" + sections.get("ARQUITECTURA", "")
        + "\n\n## Secuencia\n\n" + sections.get("SECUENCIA", "")
        + "\n\n## Contrato OpenAPI\n\n" + sections.get("OPENAPI", "")
        + "\n\n" + sections.get("INFORME", "") + "\n"
    )
    return {
        "design.md": design,
        "tasks.md": "# Tasks\n\n" + sections.get("TAREAS", "") + "\n",
        "openapi.yaml": extract_block(sections.get("OPENAPI", "")) + "\n",
    }


def validate_output(output):
    """Guardrail: exige las cinco secciones, dos diagramas Mermaid, un YAML OpenAPI y tareas en formato OpenSpec."""
    text = str(getattr(output, "raw", output) or "")
    sections = parse_sections(text)
    missing = [m for m in MARKERS if not sections.get(m)]
    if missing:
        return False, f"Faltan secciones: {', '.join(missing)}. Usa los marcadores <<<NOMBRE>>>."
    if "```mermaid" not in sections["ARQUITECTURA"] or "```mermaid" not in sections["SECUENCIA"]:
        return False, "ARQUITECTURA y SECUENCIA deben incluir bloques ```mermaid."
    if "openapi:" not in sections["OPENAPI"]:
        return False, "OPENAPI debe contener un documento YAML con la clave openapi:."
    if "- [ ]" not in sections["TAREAS"]:
        return False, "TAREAS debe contener tareas en formato `- [ ] 1.1 descripción`."
    return True, text


def build_task(feature: dict) -> Task:
    return Task(
        description=INSTRUCTIONS + feature_brief(feature)
                    + "\n" + str(feature.get("description", ""))
                    + "\n" + str(feature.get("acceptance_criteria", [])),
        expected_output=(
            "Documento con las secciones <<<ARQUITECTURA>>>, <<<SECUENCIA>>>, <<<OPENAPI>>>, "
            "<<<INFORME>>>, <<<TAREAS>>> y <<<FIN>>>, con diagramas Mermaid, contrato OpenAPI YAML, "
            "informe y tareas en formato OpenSpec."
        ),
        agent=agent,
    )