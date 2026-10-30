"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'chapter'
LABEL = 'Chapter'
SPEC_FILE = 'chapter_review.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Actúa como CHAPTER, revisor final de la funcionalidad. Contrasta cada criterio de aceptación con la arquitectura, la persistencia disponible, la implementación, las pruebas y la seguridad, usando las entregas aprobadas incluidas en el contexto.

Detecta contratos incompatibles entre las entregas, criterios sin cobertura y hallazgos pendientes. Para cada observación, indica evidencia concreta, responsable del cambio, cambio requerido y cómo verificarlo. No inventes evidencia ni presentes pruebas propuestas como ejecutadas; señala explícitamente las pruebas pendientes y sus comandos cuando estén disponibles.

Emite VEREDICTO: APROBADO solo si la evidencia demuestra que todos los criterios están cubiertos y no hay incompatibilidades ni hallazgos pendientes que impidan aceptar la solución. En caso contrario, emite VEREDICTO: RECHAZADO y enumera los motivos y correcciones. Justifica el veredicto con evidencia y distingue los resultados verificados de los pendientes.

Tu veredicto es una recomendación técnica: no apruebes entregas en nombre de personas ni sustituyas la aprobación humana del flujo."""
agent = Agent(role='Chapter de Ingenieria de Software',
              goal="Contrastar los requisitos con todas las entregas, justificar un veredicto y definir correcciones verificables. Revisor final de arquitectura, datos, código, pruebas y seguridad",
              backstory="Eres Chapter de Ingenieria de Software, responsable de la revisión integral final. Evalúas trazabilidad, compatibilidad y evidencia objetiva, conservando siempre la autoridad de aprobación humana.",
              llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output="""Un archivo Markdown para guardar como chapter_review.md, con esta estructura:

# Revisión Chapter de Ingenieria de Software
VEREDICTO: APROBADO o VEREDICTO: RECHAZADO

## Motivos del veredicto
Justificación con evidencia de las entregas revisadas.

## Matriz de criterios de aceptación
Para cada criterio: criterio, evidencia de arquitectura, persistencia (o indicar que no se entregó), implementación, pruebas y seguridad; resultado y brechas.

## Contratos incompatibles y hallazgos pendientes
Para cada observación: evidencia, responsable, cambio requerido y cómo verificarlo.

## Pruebas pendientes
Prueba y comando disponible, o indicar que no se proporcionó comando. Distinguir claramente lo pendiente de lo ejecutado.

No afirmes que la revisión reemplaza la aprobación humana.""", agent=agent)
