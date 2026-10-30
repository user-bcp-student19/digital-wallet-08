from crewai import Agent, Task
from pathlib import Path

from agents.brief import feature_brief
from crew.dev_loop import FRONTEND_PROFILE, DevResult, run_dev_loop
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'FrontEnd'
SPEC_FILE = 'frontend_spec.md'
# Igual que el backend: el agente crea los archivos con herramientas y las compuertas ng build/ng test.
EXTRACT_CODE = False
PROFILE = FRONTEND_PROFILE

INSTRUCTIONS = """Actúa como Desarrollador Frontend / UI Client.
Tu entrada principal son los contratos de API y los endpoints implementados por el agente Backend (servidor FastAPI corriendo en http://localhost:8000).
Implementa la interfaz en Angular con TypeScript: componentes standalone, HttpClient y formularios reactivos. No uses Streamlit ni otro framework de UI.

No ejecutes `ng new`: crea tú mismo los archivos del proyecto (package.json, angular.json, tsconfig.json, src/main.ts, src/index.html, src/styles.css, componentes y servicios) con write_file.
Consume únicamente los endpoints listados en la sección "Endpoints del backend" de la tarea.
Tienes herramientas para crear y leer archivos, listar el espacio de trabajo, instalar dependencias (run_npm_install), compilar (run_ng_build) y ejecutar pruebas (run_ng_test).
Crea package.json y ejecuta run_npm_install. Después escribe el código y sus pruebas, y corrige hasta que run_ng_build y run_ng_test terminen en verde antes de finalizar.
"""

agent = Agent(
        role='Desarrollador Frontend',
        goal='Crear una experiencia de usuario fluida, conectada de manera directa y funcional a las APIs de FastAPI generadas por el Backend, reflejando los estados del pago.',
        backstory=('Eres especialista en interfaces web con Angular y TypeScript, y en clientes de API orientados a pasarelas de pago, experto en consumir servicios FastAPI con enfoque en UX y reducción de fricción en checkout.'),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        human_input=False,  # Validación humana de flujos de usuario
)


def develop(task_description: str, workspace: Path) -> DevResult:
    """Ejecuta el bucle de desarrollo con herramientas y devuelve el resultado para el informe."""
    return run_dev_loop(llm, task_description, workspace, profile=PROFILE)

def build_task(feature: dict, backend_task=None) -> Task:
    """
    Construye la tarea de frontend. Si se proporciona backend_task, 
    CrewAI le pasa automáticamente la salida del Backend como contexto 
    para que conozca los endpoints exactos implementados.
    """
    task_kwargs = {
        "description": INSTRUCTIONS + feature_brief(feature),
        "expected_output": (
            "Aplicación Angular (TypeScript) con componentes, servicios HttpClient y pruebas unitarias, "
            "que consuma exitosamente los endpoints expuestos por la API FastAPI del Backend."
        ),
        "agent": agent,
    }
    
    # Vinculamos el contexto del Backend para que el Frontend consuma las APIs reales
    if backend_task:
        task_kwargs["context"] = [backend_task]
        
    return Task(**task_kwargs)