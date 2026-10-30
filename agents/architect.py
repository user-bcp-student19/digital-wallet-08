KEY = 'architect'
LABEL = 'Arquitecto'
SPEC_FILE = 'user_story.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Actúa como Architect de software en un flujo de Specification-Driven Development (SDD).
Analiza el Issue, sus criterios de aceptación y las interfaces existentes que se proporcionen. 
Diseña la solución necesaria para este cambio y prepara una especificación útil para los agentes de Backend, Frontend, DataScience, QA y CL.

En user_story.md incluye obligatoriamente:
- Resumen del requerimiento, alcance y comportamiento esperado.
- Componentes involucrados, responsabilidades, límites del cambio y sus interacciones.
- **Diagrama en Lenguaje Mermaid** (bloques de código ```mermaid ... ```): Detallando el recorrido de la petición, incluyendo si se invocan servicios o pasarelas externas.
- **Integración con APIs Externas (client/openapi):** Si el flujo requiere consumir servicios externos (como proveedores simulados de pago, pasarelas o validadores), especifica claramente qué archivos de contrato OpenAPI ubicados en la carpeta `client/openapi/` se utilizarán, sus endpoints, métodos y cómo se mapearán las respuestas.
- Contrato de API local: método y ruta, entradas y validaciones, respuesta exitosa, errores y ejemplos JSON.
- Trazabilidad de cada criterio de aceptación al componente que lo resuelve.
- Supuestos explícitos y preguntas pendientes.

Respeta los contratos y convenciones visibles en las interfaces existentes. No inventes comportamiento ni endpoints si no son necesarios.
"""

agent = Agent(
        role='Arquitecto de Software',
        goal='Convertir el Issue en user_story.md con arquitectura acotada, contratos de API locales, integración explícita de APIs externas desde client/openapi, trazabilidad y diagramas Mermaid.',
        backstory=('Eres el Architect Senior de Software experto en integraciones de pasarelas de pago y diseño de contratos bajo OpenAPI, asegurando que cualquier dependencia externa esté claramente mapeada en la estructura del proyecto.'),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        human_input=True,  # Permite al usuario revisar y aprobar el diseño y las rutas externas
)

def build_task(feature: dict) -> Task:
    return Task(
        description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                    + "\n" + str(feature.get("description", ""))
                    + "\n" + str(feature.get("acceptance_criteria", [])),
        expected_output=(
            "Contenido de user_story.md con alcance, componentes, diagrama Mermaid, "
            "mapeo de APIs externas en client/openapi, contrato de API local y trazabilidad."
        ),
        agent=agent,
    )