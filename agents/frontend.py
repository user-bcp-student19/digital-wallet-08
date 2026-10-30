from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'FrontEnd'
SPEC_FILE = 'src/frontend_mock.py'
EXTRACT_CODE = True

INSTRUCTIONS = """Actúa como Desarrollador Frontend / UI Client.
Tu entrada principal son los contratos de API y los endpoints implementados por el agente Backend (servidor FastAPI corriendo en http://localhost:8000).
"""

agent = Agent(
        role='Desarrollador Frontend',
        goal='Crear una experiencia de usuario fluida, conectada de manera directa y funcional a las APIs de FastAPI generadas por el Backend, reflejando los estados del pago.',
        backstory=('Eres especialista en interfaces web y clientes de API orientados a pasarelas de pago, experto en consumir servicios FastAPI con enfoque en UX y reducción de fricción en checkout.'),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        human_input=False,  # Validación humana de flujos de usuario
)

def build_task(feature: dict, backend_task=None) -> Task:
    """
    Construye la tarea de frontend. Si se proporciona backend_task, 
    CrewAI le pasa automáticamente la salida del Backend como contexto 
    para que conozca los endpoints exactos implementados.
    """
    task_kwargs = {
        "description": INSTRUCTIONS + "\nFeature: " + str(feature.get("title", "")),
        "expected_output": (
            "Cliente o interfaz frontend implementada (ej. en Streamlit o script cliente) "
            "que consuma exitosamente los endpoints expuestos por la API FastAPI del Backend."
        ),
        "agent": agent,
    }
    
    # Vinculamos el contexto del Backend para que el Frontend consuma las APIs reales
    if backend_task:
        task_kwargs["context"] = [backend_task]
        
    return Task(**task_kwargs)