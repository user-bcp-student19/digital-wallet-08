from pathlib import Path

from crewai import Agent, Task
from agents.brief import feature_brief
from crew.dev_loop import BACKEND_PROFILE, DevResult, run_dev_loop
from crew.llm_config import llm

KEY = 'backend'
LABEL = 'Backend'
SPEC_FILE = 'backend_spec.md'
# El código lo escribe el propio agente con herramientas (crew/dev_loop.py), no se extrae de bloques.
EXTRACT_CODE = False
PROFILE = BACKEND_PROFILE

INSTRUCTIONS = """Actúa como Ingeniero Backend especializado en FastAPI y Python.
Tu entrada principal es la especificación técnica y el diagrama en lenguaje Mermaid generado por el Arquitecto.
Además, ten en cuenta que encontrarás las especificaciones OpenAPI de las APIs y pasarelas externas que debe consumir el flujo dentro de la carpeta `client/openapi`.

Basándote estrictamente en el diagrama de secuencia, los componentes locales y los contratos OpenAPI provistos en `client/openapi`, implementa los endpoints y la lógica de negocio correspondiente en FastAPI, asegurando la validación de cabeceras, códigos HTTP y la integración con los servicios externos según lo especificado.

Tienes herramientas para crear y leer archivos, listar el espacio de trabajo y ejecutar pytest y ruff. Escribe el código y sus pruebas, ejecuta pytest y corrige hasta que todas pasen antes de finalizar.
"""

agent = Agent(
        role='Ingeniero Backend Senior',
        goal='Implementar una API robusta, idempotente y de alto rendimiento en FastAPI siguiendo fielmente el diseño de arquitectura, el diagrama Mermaid y las especificaciones OpenAPI de client/openapi.',
        backstory=('Eres experto en desarrollo backend transaccional y diseño guiado por especificaciones (SDD), traduciendo diagramas de secuencia, contratos OpenAPI externos y arquitectura en código limpio de producción en Python.'),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        human_input=False,  # Permite revisar el código generado antes de continuar
)


def develop(task_description: str, workspace: Path) -> DevResult:
    """Ejecuta el bucle de desarrollo con herramientas y devuelve el resultado para el informe."""
    return run_dev_loop(llm, task_description, workspace, profile=PROFILE)


agent = Agent(
        role='Ingeniero Backend Senior',
        goal='Implementar una API robusta, idempotente y de alto rendimiento en FastAPI siguiendo fielmente el diseño de arquitectura, el diagrama Mermaid y las especificaciones OpenAPI de client/openapi.',
        backstory=('Eres experto en desarrollo backend transaccional y diseño guiado por especificaciones (SDD), traduciendo diagramas de secuencia, contratos OpenAPI externos y arquitectura en código limpio de producción en Python.'),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        human_input=False,  # Permite revisar el código generado antes de continuar
)

def build_task(feature: dict, architect_task=None) -> Task:
    """
    Construye la tarea de backend. Si se proporciona architect_task, 
    CrewAI le pasa automáticamente la salida del Arquitecto como contexto (incluyendo el Mermaid).
    """
    task_kwargs = {
        "description": INSTRUCTIONS + feature_brief(feature),
        "expected_output": (
            "Código FastAPI en app/ y pruebas pytest en tests/ dentro del espacio de trabajo, "
            "estructurado según el diagrama de arquitectura, client/openapi y el contrato definidos por el Arquitecto, "
            "con pytest en verde y un resumen final."
        ),
        "agent": agent,
    }
    
    # Vinculamos el contexto del Arquitecto para que el Backend lea el Mermaid y las referencias
    if architect_task:
        task_kwargs["context"] = [architect_task]
        
    return Task(**task_kwargs)