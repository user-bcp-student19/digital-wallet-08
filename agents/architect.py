"""Arquitecto: genera diagramas Mermaid, contrato OpenAPI y su informe."""
import re
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'architect'
LABEL = 'Arquitecto'
SPEC_FILE = 'architect.md'
EXTRACT_CODE = False

MARKERS = ["ARQUITECTURA", "SECUENCIA", "OPENAPI", "INFORME"]

INSTRUCTIONS = """Actúa como Arquitecto de Software en un flujo de Specification-Driven Development (SDD).
Analiza el Issue, sus criterios de aceptación y los contratos OpenAPI de `client/openapi/`.
Diseña la solución y entrega EXACTAMENTE estas secciones, en este orden, con sus marcadores:

<<<ARQUITECTURA>>>
Diagrama de arquitectura en un bloque ```mermaid ... ``` (componentes, límites y servicios externos).

<<<SECUENCIA>>>
Diagrama de secuencia en un bloque ```mermaid ... ``` (recorrido de la petición, incluidas las pasarelas externas).

<<<OPENAPI>>>
Contrato OpenAPI 3.0 del API local en un bloque ```yaml ... ``` (paths, métodos, esquemas, respuestas y errores).
Si el flujo consume servicios externos, refleja en el contrato cómo se mapean sus respuestas según los archivos de client/openapi/.

<<<INFORME>>>
Informe Markdown con: resumen y alcance, componentes y responsabilidades, APIs externas de client/openapi utilizadas,
trazabilidad de cada criterio de aceptación al componente que lo resuelve, supuestos y preguntas pendientes.

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


def parse_sections(text: str) -> dict[str, str]:
    """Separa la salida del agente en secciones según los marcadores <<<NOMBRE>>>."""
    parts = re.split(r"<<<(ARQUITECTURA|SECUENCIA|OPENAPI|INFORME)>>>", text)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def extract_block(section: str) -> str:
    """Devuelve el contenido del primer bloque de código de una sección."""
    match = re.search(r"```[a-zA-Z]*\n(.*?)```", section, re.DOTALL)
    return match.group(1).strip() if match else section.strip()


def validate_output(output):
    """Guardrail: exige las cuatro secciones, dos diagramas Mermaid y un YAML OpenAPI."""
    text = str(getattr(output, "raw", output) or "")
    sections = parse_sections(text)
    missing = [m for m in MARKERS if not sections.get(m)]
    if missing:
        return False, f"Faltan secciones: {', '.join(missing)}. Usa los marcadores <<<NOMBRE>>>."
    if "```mermaid" not in sections["ARQUITECTURA"] or "```mermaid" not in sections["SECUENCIA"]:
        return False, "ARQUITECTURA y SECUENCIA deben incluir bloques ```mermaid."
    if "openapi:" not in sections["OPENAPI"]:
        return False, "OPENAPI debe contener un documento YAML con la clave openapi:."
    return True, text


def build_task(feature: dict) -> Task:
    return Task(
        description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                    + "\n" + str(feature.get("description", ""))
                    + "\n" + str(feature.get("acceptance_criteria", [])),
        expected_output=(
            "Documento con las secciones <<<ARQUITECTURA>>>, <<<SECUENCIA>>>, <<<OPENAPI>>>, "
            "<<<INFORME>>> y <<<FIN>>>, con diagramas Mermaid, contrato OpenAPI YAML e informe."
        ),
        agent=agent,
    )