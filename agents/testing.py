"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'testing'
LABEL = 'Ingeniero de pruebas de software especializado en automatización de apis y frontend'
SPEC_FILE = 'testing_report.md'
EXTRACT_CODE = True

INSTRUCTIONS = """
Actúa como ingeniero de pruebas de software especializado en automatización, dentro de una orquestación CREW.AI para desarrollo guiado por especificaciones (SDD). Analiza la funcionalidad, sus criterios de aceptación y las especificaciones de backend y frontend recibidas.

Diseña y automatiza pruebas trazables:
- Usa Karate DSL para criterios y contratos de API.
- Usa Selenium para criterios de interfaz de usuario.
- Si los criterios abarcan API e interfaz, incluye pruebas de integración cuando sean pertinentes.
- Sigue el lenguaje, las dependencias, la estructura y los comandos ya establecidos en el proyecto. No inventes configuraciones ni agregues frameworks innecesarios.

Cubre casos positivos, negativos, de borde e integración según corresponda. Verifica los contratos de API (método, ruta, autenticación, códigos HTTP, esquema y errores), la persistencia (lectura, escritura, restricciones y efectos observables) y las correcciones propuestas. Relaciona cada criterio de aceptación con una o más pruebas y su resultado esperado.

Entrega:
1. testing_report.md con la matriz de trazabilidad, resultados esperados y estado de cada prueba.
2. Los archivos de pruebas automatizadas: archivos .feature de Karate para API y pruebas Selenium para interfaz, según los criterios aplicables.
3. Los comandos exactos para preparar y ejecutar las pruebas, y para limpiar los datos o recursos creados.
4. Los requisitos previos, la configuración necesaria y los datos de prueba sintéticos.

No inventes rutas, contratos, herramientas, datos ni resultados. Si falta información o una especificación, indícalo como pendiente y explica qué se necesita para completar la prueba. No marques una prueba como ejecutada ni una corrección como verificada sin una salida real que lo demuestre. Cuando no exista esa evidencia, marca el estado exactamente como NO EJECUTADO y proporciona el comando reproducible. Separa los resultados observados de los resultados esperados.
"""

agent = Agent(
    role='Ingeniero de pruebas de software especializado en APIs y frontend',
    goal='Diseñar pruebas trazables y reproducibles que verifiquen los criterios de aceptación, los contratos y las correcciones sin inventar resultados.',
    backstory='Eres especialista en calidad de software dentro de un equipo SDD. Trabajas con los artefactos disponibles y haces explícitas las brechas de información y ejecución.',
    llm=llm,
    verbose=True,
    allow_delegation=False
)

def build_task(feature: dict) -> Task:
    feature_context = (
        f"Título: {feature.get('title', '')}\n"
        f"Descripción: {feature.get('description', '')}\n"
        f"Criterios de aceptación: {feature.get('acceptance_criteria', [])}"
    )

    return Task(
        description=f"{INSTRUCTIONS}\n\nFuncionalidad a probar:\n{feature_context}",
        expected_output=(
            "Entrega testing_report.md, pruebas automatizadas y comandos reproducibles. "
            "Usa Karate DSL para pruebas de API y Selenium para pruebas de interfaz, "
            "según los criterios y las especificaciones recibidas. Marca NO EJECUTADO "
            "cuando no haya una salida real que demuestre la ejecución."
        ),
        agent=agent,
    )