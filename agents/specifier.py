"""Especificador: convierte el Issue en una propuesta y en deltas de especificación OpenSpec."""
import re
from crewai import Agent, Task
from agents.brief import feature_brief
from crew.llm_config import llm

KEY = 'specs'
LABEL = 'Especificación OpenSpec'
SPEC_FILE = 'specification.md'
EXTRACT_CODE = False

CAPABILITY_RE = re.compile(r"<<<(PROPUESTA|CAPACIDAD:[a-z0-9]+(?:-[a-z0-9]+)*|FIN)>>>")

INSTRUCTIONS = """Actúa como Analista de Especificaciones en un flujo de Specification-Driven Development (SDD) con OpenSpec.
Convierte el Issue y sus criterios de aceptación en una propuesta y en especificaciones verificables.
Entrega EXACTAMENTE estas secciones, en este orden, con sus marcadores:

<<<PROPUESTA>>>
Contenido de proposal.md con las secciones `## Why`, `## What Changes`, `## Capabilities` y `## Impact`.
En `## Capabilities`, `### New Capabilities` lista una viñeta por capacidad con el formato: - `nombre-en-kebab`: descripción.
Deja `### Modified Capabilities` vacía, salvo que cambie un requisito de una capacidad existente en openspec/specs/.

<<<CAPACIDAD:nombre-en-kebab>>>
Delta de especificación de esa capacidad, empezando por `## ADDED Requirements`.
Cada requisito usa `### Requirement: <nombre>` con texto en presente que contenga SHALL o MUST,
y al menos un `#### Scenario: <nombre>` con `- **WHEN** ...` y `- **THEN** ...`.
Repite el marcador <<<CAPACIDAD:...>>> por cada capacidad.

<<<FIN>>>

Cada criterio de aceptación debe quedar cubierto por al menos un escenario. No inventes requisitos que el Issue no pida.
"""

agent = Agent(
    role='Analista de Especificaciones',
    goal='Producir la propuesta OpenSpec y los deltas de especificación con escenarios verificables.',
    backstory='Analista de requisitos senior, experto en especificaciones con escenarios WHEN/THEN.',
    llm=llm,
    verbose=True,
    allow_delegation=False,
    human_input=False,  # La aprobación humana la gestiona main.py
)


def parse_specification(text: str) -> tuple[str, dict[str, str]]:
    """Devuelve (propuesta, {capacidad: delta}) según los marcadores <<<PROPUESTA>>> y <<<CAPACIDAD:nombre>>>."""
    parts = CAPABILITY_RE.split(text)
    sections = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    capabilities = {name.removeprefix("CAPACIDAD:"): body
                    for name, body in sections.items() if name.startswith("CAPACIDAD:")}
    return sections.get("PROPUESTA", ""), capabilities


def build_task(feature: dict) -> Task:
    return Task(
        description=INSTRUCTIONS + feature_brief(feature)
                    + "\n" + str(feature.get("description", ""))
                    + "\n" + str(feature.get("acceptance_criteria", [])),
        expected_output=(
            "Documento con <<<PROPUESTA>>>, uno o más <<<CAPACIDAD:nombre-en-kebab>>> con deltas "
            "OpenSpec (requisitos con SHALL/MUST y escenarios WHEN/THEN) y <<<FIN>>>."
        ),
        agent=agent,
    )
