KEY = 'product_owner'
LABEL = 'Product Owner'
SPEC_FILE = 'product_backlog_refinement.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Actúa como Product Owner experto en pasarelas de pago y billeteras digitales (Wallet MVP Perú).
Analiza la historia de usuario provista, valida que los criterios de aceptación y el contexto del negocio 
(tasas de caída en checkout, MAU, reglas de bajo monto, manejo de errores de proveedor) estén completamente alineados 
con los objetivos de producto. 

Asegúrate de:
- Clarificar las reglas de negocio y los límites de monto por proveedor.
- Definir claramente el alcance del MVP para evitar sobreingeniería.
- Validar las expectativas sobre los estados terminales (APPROVED, REJECTED, DELAYED_APPROVAL, TIMEOUT).
"""

agent = Agent(
        role='Product Owner',
        goal='Garantizar la alineación de la solución técnica con los objetivos de negocio, la métrica de MAU y la reducción de caída en checkout del MVP.',
        backstory=('Eres un Product Owner enfocado en productos fintech en LatAm con amplia experiencia en pasarelas de pago. '
                   'Priorizas la experiencia de usuario y el cumplimiento de las metas de negocio.'),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        human_input=True,  # Aplica Human-in-the-Loop para validación de negocio
)

def build_task(feature: dict) -> Task:
    return Task(
        description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                    + "\n" + str(feature.get("description", ""))
                    + "\n" + str(feature.get("acceptance_criteria", [])),
        expected_output="Documento de refinamiento con alcance validado, prioridades de negocio y criterios de aceptación comerciales.",
        agent=agent,
    )