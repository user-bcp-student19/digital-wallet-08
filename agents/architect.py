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


MERMAID_FENCE_RE = re.compile(r"```mermaid[ \t]*\n(.*?)```", re.DOTALL)
ARCH_DIAGRAM_TYPES = {
    "graph", "flowchart", "C4Context", "C4Container", "C4Component", "C4Dynamic",
    "C4Deployment", "classDiagram", "stateDiagram", "stateDiagram-v2", "erDiagram", "block-beta",
}
FLOW_DIRECTIONS = {"TD", "TB", "BT", "RL", "LR"}
SEQ_BLOCK_OPENERS = {"alt", "opt", "loop", "par", "critical", "break", "rect", "box"}
SEQ_ARROW_RE = re.compile(r"(-->>|->>|--x|-x|--\)|-\)|-->|->)")
SEQ_MESSAGE_RE = re.compile(r"^[^\s:]+\s*(?:-->>|->>|--x|-x|--\)|-\)|-->|->)[+-]?\s*[^\s:]+\s*:\s*\S")
UNQUOTED_PARENS_RE = re.compile(r'\b\w+\[(?![\(\[/\\"])([^\]"\n]*[()][^\]"\n]*)\]')


def _mermaid_lines(code: str) -> list[str]:
    """Líneas útiles del diagrama: sin frontmatter, directivas %%{init}%%, comentarios ni líneas vacías."""
    code = re.sub(r"\A\s*---\n.*?\n---\n", "", code, flags=re.DOTALL)
    lines = [ln.strip() for ln in code.splitlines()]
    return [ln for ln in lines if ln and not ln.startswith("%%")]


def validate_mermaid(code: str, kind: str) -> list[str]:
    """Valida la sintaxis Mermaid sin dependencias externas. kind: 'architecture' | 'sequence'."""
    lines = _mermaid_lines(code)
    if not lines:
        return ["el bloque mermaid está vacío"]

    header = lines[0].rstrip(";").split()
    diagram = header[0]
    errors: list[str] = []

    if kind == "sequence":
        if diagram != "sequenceDiagram":
            return [f"debe empezar con 'sequenceDiagram' (empieza con '{lines[0]}')"]
        depth, messages = 0, 0
        for n, line in enumerate(lines[1:], 2):
            word = line.split()[0]
            if word in SEQ_BLOCK_OPENERS:
                depth += 1
            elif word == "end":
                depth -= 1
                if depth < 0:
                    errors.append(f"línea {n}: 'end' sin bloque abierto")
                    depth = 0
            if SEQ_ARROW_RE.search(line) and not word.lower() == "note":
                messages += 1
                if ";" in line:
                    errors.append(f"línea {n}: no uses ';' en mensajes ({line!r})")
                elif not SEQ_MESSAGE_RE.match(line):
                    errors.append(f"línea {n}: mensaje inválido, usa 'A->>B: texto' ({line!r})")
        if depth > 0:
            errors.append(f"{depth} bloque(s) alt/opt/loop/par sin 'end'")
        if messages == 0:
            errors.append("no contiene ningún mensaje entre participantes")
        return errors[:8]

    if diagram not in ARCH_DIAGRAM_TYPES:
        return [f"tipo de diagrama no válido '{diagram}'; usa 'flowchart TD' o 'graph TD'"]
    if diagram in {"graph", "flowchart"}:
        if len(header) > 1 and header[1] not in FLOW_DIRECTIONS:
            errors.append(f"dirección inválida '{header[1]}'; usa TD, TB, BT, RL o LR")
        if len(lines) < 2:
            errors.append("el flowchart no tiene nodos ni relaciones")
        depth = 0
        for n, line in enumerate(lines[1:], 2):
            word = line.split()[0]
            if word == "subgraph":
                depth += 1
            elif word == "end":
                depth -= 1
                if depth < 0:
                    errors.append(f"línea {n}: 'end' sin 'subgraph'")
                    depth = 0
            if line.count('"') % 2:
                errors.append(f"línea {n}: comillas sin cerrar ({line!r})")
            plain = re.sub(r'"[^"]*"', '""', line)
            for open_c, close_c in ("[]", "{}", "()"):
                if plain.count(open_c) != plain.count(close_c):
                    errors.append(f"línea {n}: '{open_c}' y '{close_c}' desbalanceados ({line!r})")
                    break
            if UNQUOTED_PARENS_RE.search(line):
                errors.append(f"línea {n}: etiqueta con paréntesis sin comillas; usa A[\"Texto (detalle)\"] ({line!r})")
        if depth > 0:
            errors.append(f"{depth} 'subgraph' sin 'end'")
    return errors[:8]


def validate_mermaid_blocks(sections: dict[str, str]) -> str | None:
    """Devuelve un mensaje de corrección si algún diagrama Mermaid es inválido, o None si ambos son correctos."""
    problems = []
    for key, kind in (("ARQUITECTURA", "architecture"), ("SECUENCIA", "sequence")):
        match = MERMAID_FENCE_RE.search(sections[key])
        if not match:
            problems.append(f"{key}: falta un bloque ```mermaid ... ``` correctamente cerrado con ```.")
            continue
        errors = validate_mermaid(match.group(1), kind)
        if errors:
            problems.append(f"{key}: " + "; ".join(errors))
    if not problems:
        return None
    return ("Mermaid inválido. Corrige y vuelve a entregar TODAS las secciones: " + " | ".join(problems)
            + ". Reglas: ARQUITECTURA empieza con 'flowchart TD'; SECUENCIA con 'sequenceDiagram'; "
              "textos con paréntesis o caracteres especiales entre comillas dobles; cierra cada subgraph/alt/loop con 'end'.")


def validate_output(output):
    """Guardrail: exige las cuatro secciones, dos diagramas Mermaid válidos y un YAML OpenAPI."""
    text = str(getattr(output, "raw", output) or "")
    sections = parse_sections(text)
    missing = [m for m in MARKERS if not sections.get(m)]
    if missing:
        return False, f"Faltan secciones: {', '.join(missing)}. Usa los marcadores <<<NOMBRE>>>."
    mermaid_error = validate_mermaid_blocks(sections)
    if mermaid_error:
        return False, mermaid_error
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