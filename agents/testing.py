"""QA: genera pruebas de API con Karate y pruebas funcionales web con Selenium; qa_runner.py las ejecuta de verdad."""
import ast
import re
from pathlib import PurePosixPath

from crewai import Agent, Task
from crew.llm_config import llm
from agents.backend import SECRET_RE, incomplete_output, parse_files
from agents.frontend import required_routes

KEY = 'testing'
LABEL = 'Ingeniero de pruebas de software especializado en automatización de apis y frontend'
SPEC_FILE = 'testing_report.md'
EXTRACT_CODE = True

TESTING_GUARDRAIL_RETRIES = 10
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:4200"
ALLOWED_SUFFIXES = {".feature", ".js", ".json", ".py", ".txt", ".md", ".properties"}
MAX_FILES = 40
MAX_FILE_BYTES = 200_000
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

INSTRUCTIONS = """Actúa como Ingeniero de QA y Automatización de Pruebas experto, dentro de una orquestación CrewAI de
desarrollo guiado por especificaciones (SDD). Recibes los artefactos del Backend (API Python/FastAPI en
http://localhost:8000) y del Frontend (Angular en http://localhost:4200), y los criterios de aceptación de la funcionalidad.
Tú diseñas las pruebas; el orquestador levantará los servicios, las ejecutará y medirá los resultados reales.

Genera pruebas trazables, reproducibles y basadas SOLO en lo que existe:
- API con **Karate Framework**: valida método, ruta, cabeceras, códigos HTTP, esquema de la respuesta y errores de las
  rutas reales del Backend (se te entrega la lista exacta). Casos positivos, negativos y de borde.
- Interfaz web con **Selenium** (Python + pytest): automatiza la interfaz Angular usando únicamente selectores que existan
  en el código del Frontend que se te entrega (ids, name, formControlName, data-testid), con esperas explícitas
  (WebDriverWait), sin `time.sleep` largos.
- Si un criterio abarca API e interfaz, incluye una prueba de integración.
- Datos de prueba sintéticos; nunca credenciales ni datos reales. No inventes rutas, selectores ni resultados.

ESTRUCTURA OBLIGATORIA (rutas relativas, con `/`):
- `karate/karate-config.js`: define `baseUrl` leyendo `karate.properties['baseUrl']` con valor por defecto
  http://localhost:8000.
- `karate/features/*.feature`: cada Scenario con `Given url baseUrl + '/ruta'` (o `Given path`), `When method <verbo>` y
  `Then status <código>`, más `match` sobre la respuesta cuando aplique. Etiqueta cada Scenario con el criterio que cubre.
- `selenium/conftest.py`: fixture `driver` con Chrome headless (`--headless=new`), `BASE_URL` desde la variable de entorno
  (por defecto http://localhost:4200) y captura de pantalla al fallar en `os.environ.get("REPORT_DIR", "reports")/screenshots`.
- `selenium/test_*.py`: pruebas pytest con funciones `test_*`.
- `selenium/requirements.txt` con selenium y pytest.
Prohibido: URLs externas (solo localhost), eval, exec, os.system, subprocess, secretos en el código.

FORMATO DE SALIDA OBLIGATORIO: cada archivo así, con su bloque de código envuelto en ```, terminando con <<<FIN>>>:

<<<FILE: karate/features/cuentas.feature>>>
```gherkin
Feature: ...
```
<<<FILE: selenium/test_onboarding.py>>>
```python
# ...
```
<<<FIN>>>

No generes informes ni marques pruebas como ejecutadas: el informe lo compila el orquestador con resultados reales.
"""

agent = Agent(
    role='Ingeniero de pruebas de software especializado en APIs y frontend',
    goal='Diseñar pruebas Karate (API) y Selenium (web) trazables y reproducibles que verifiquen los criterios de aceptación, los contratos y la interfaz real, sin inventar resultados.',
    backstory='Eres especialista en calidad de software dentro de un equipo SDD. Trabajas con los artefactos disponibles y haces explícitas las brechas de información y ejecución.',
    llm=llm,
    verbose=True,
    allow_delegation=False,
    human_input=False,  # La aprobación humana de los resultados la gestiona main.py
)


# ── Guardrail ──────────────────────────────────────────────────────
EXTERNAL_URL_RE = re.compile(r"https?://(?!localhost\b|127\.0\.0\.1\b)[^\s'\"`)]+", re.I)
SCENARIO_SPLIT_RE = re.compile(r"^\s*Scenario(?: Outline)?:", re.M)
KARATE_METHOD_RE = re.compile(r"\bmethod\s+(get|post|put|patch|delete)\b", re.I)
KARATE_STATUS_RE = re.compile(r"\bstatus\s+\d{3}\b|response(?:Status)?\s*==\s*\d{3}", re.I)
SELENIUM_BY_RE = re.compile(r"""By\.(ID|NAME|CSS_SELECTOR)\s*,\s*(["'])(.+?)\2""")
CSS_ID_RE = re.compile(r"#([A-Za-z_][\w-]*)")
CSS_ATTR_RE = re.compile(r"""\[\s*(name|id|data-testid|formcontrolname)\s*=\s*["']?([\w-]+)["']?\s*\]""", re.I)
FORBIDDEN_CALLS = {"eval", "exec"}


def _unsafe_path(path: str) -> str | None:
    p = PurePosixPath(path)
    if not path or p.is_absolute() or ".." in p.parts or path.startswith(".") or ":" in path:
        return "debe ser relativa y sin '..'"
    if p.parts[0] not in {"karate", "selenium"}:
        return "debe estar bajo karate/ o selenium/"
    if p.suffix not in ALLOWED_SUFFIXES:
        return f"extensión no permitida ({p.suffix or 'sin extensión'})"
    return None


def frontend_selectors(frontend_files: dict[str, str]) -> dict[str, set[str]]:
    """Ids, names y data-testid presentes en las plantillas y componentes del Frontend."""
    text = "\n".join(c for p, c in frontend_files.items() if p.endswith((".html", ".ts")))
    return {
        "id": set(re.findall(r"""\bid\s*=\s*["']([\w-]+)["']""", text)),
        "name": set(re.findall(r"""\b(?:name|formControlName)\s*=\s*["']([\w-]+)["']""", text)),
        "data-testid": set(re.findall(r"""\bdata-testid\s*=\s*["']([\w-]+)["']""", text)),
    }


def _selector_tokens(kind: str, value: str) -> list[tuple[str, str]]:
    """(tipo, valor) de cada selector verificable de una llamada By.*; ignora selectores por clase o etiqueta."""
    if kind == "ID":
        return [("id", value)]
    if kind == "NAME":
        return [("name", value)]
    tokens = [("id", m) for m in CSS_ID_RE.findall(re.sub(CSS_ATTR_RE, "", value))]
    for attr, val in CSS_ATTR_RE.findall(value):
        attr = attr.lower()
        tokens.append(("name" if attr == "formcontrolname" else attr, val))
    return tokens


def _route_covered(method: str, path: str, scenarios: list[str]) -> bool:
    segments = [s for s in path.strip("/").split("/") if s and s != "{}"]
    return any(re.search(rf"\bmethod\s+{method}\b", s, re.I) and all(seg in s for seg in segments) for s in scenarios)


def check_karate(files: dict[str, str], required: set[tuple[str, str]]) -> list[str]:
    errors = []
    config = files.get("karate/karate-config.js")
    if config is None:
        errors.append("falta karate/karate-config.js con baseUrl")
    elif "baseUrl" not in config:
        errors.append("karate/karate-config.js debe definir baseUrl")
    features = {p: c for p, c in files.items() if p.startswith("karate/features/") and p.endswith(".feature")}
    if not features:
        errors.append("faltan pruebas Karate: karate/features/*.feature")
    scenarios: list[str] = []
    for path, content in sorted(features.items()):
        if not re.search(r"^\s*Feature:", content, re.M):
            errors.append(f"{path}: debe comenzar con 'Feature:'")
        blocks = SCENARIO_SPLIT_RE.split(content)[1:]
        if not blocks:
            errors.append(f"{path}: no define ningún 'Scenario:'")
        for block in blocks:
            title = block.strip().splitlines()[0][:60] if block.strip() else "?"
            if not KARATE_METHOD_RE.search(block):
                errors.append(f"{path}: el Scenario '{title}' no llama a ningún 'method get|post|put|patch|delete'")
            if not KARATE_STATUS_RE.search(block):
                errors.append(f"{path}: el Scenario '{title}' no verifica el código HTTP ('status 200')")
            scenarios.append(block)
    if scenarios and not any(e.startswith("faltan") for e in errors):
        uncovered = sorted(f"{m} {p}" for m, p in required if not _route_covered(m.lower(), p, scenarios))
        if uncovered and not errors:
            errors.append("las pruebas Karate no cubren estas rutas del Backend: " + ", ".join(uncovered))
    return errors


def check_selenium(files: dict[str, str], frontend: dict[str, set[str]] | None) -> list[str]:
    errors = []
    py_files = {p: c for p, c in files.items() if p.startswith("selenium/") and p.endswith(".py")}
    tests = {p: c for p, c in py_files.items() if PurePosixPath(p).name.startswith("test_")}
    if not tests:
        errors.append("faltan pruebas Selenium: selenium/test_*.py")
    if "selenium/conftest.py" not in files:
        errors.append("falta selenium/conftest.py con el fixture driver (Chrome headless)")
    if "selenium/requirements.txt" not in files:
        errors.append("falta selenium/requirements.txt")
    has_test_fn = False
    for path, content in py_files.items():
        try:
            tree = ast.parse(content, filename=path)
        except SyntaxError as exc:
            errors.append(f"{path}: error de sintaxis en línea {exc.lineno}: {exc.msg}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and path in tests:
                has_test_fn = True
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name in FORBIDDEN_CALLS or (name == "system" and getattr(getattr(node.func, "value", None), "id", "") == "os"):
                    errors.append(f"{path}: llamada prohibida '{name}' (línea {node.lineno})")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(m.split(".")[0] == "subprocess" for m in modules):
                    errors.append(f"{path}: import prohibido 'subprocess' (línea {node.lineno})")
    if tests and not has_test_fn:
        errors.append("selenium/test_*.py no define funciones test_*")
    all_py = "\n".join(py_files.values())
    if py_files and "selenium" not in all_py:
        errors.append("las pruebas deben usar Selenium (from selenium import webdriver)")
    if py_files and not re.search(r"--headless", all_py):
        errors.append("Chrome debe ejecutarse headless (--headless=new) en selenium/conftest.py")
    if py_files and "BASE_URL" not in all_py:
        errors.append("selenium debe leer BASE_URL de la variable de entorno (por defecto http://localhost:4200)")
    if frontend and not errors:
        missing = []
        for path, content in sorted(tests.items()):
            for kind, _, value in SELENIUM_BY_RE.findall(content):
                for token_kind, token in _selector_tokens(kind, value):
                    if token not in frontend.get(token_kind, set()) and (path, token_kind, token) not in missing:
                        missing.append((path, token_kind, token))
        if missing:
            shown = ", ".join(f"{k}='{t}' ({p})" for p, k, t in missing[:8])
            available = ", ".join(sorted(frontend["id"] | frontend["name"] | frontend["data-testid"])[:25]) or "ninguno"
            errors.append(f"selectores que NO existen en el Frontend: {shown}. Selectores disponibles: {available}")
    return errors


def validate_files(files: dict[str, str], served: set[tuple[str, str]] | None = None,
                   spec: set[tuple[str, str]] | None = None, frontend: dict[str, set[str]] | None = None) -> list[str]:
    """Problemas de las pruebas entregadas (lista vacía si son válidas)."""
    if not files:
        return ["no se encontró ningún archivo con el formato <<<FILE: ruta>>> + bloque de código"]
    errors = []
    if len(files) > MAX_FILES:
        errors.append(f"demasiados archivos ({len(files)}); máximo {MAX_FILES}")
    for path, content in files.items():
        reason = _unsafe_path(path)
        if reason:
            errors.append(f"ruta inválida '{path}': {reason}")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            errors.append(f"{path}: supera {MAX_FILE_BYTES} bytes")
        if SECRET_RE.search(content):
            errors.append(f"{path}: contiene un secreto o credencial escrita en el código")
        external = EXTERNAL_URL_RE.search(content)
        if external and path.endswith((".feature", ".js", ".py")):
            errors.append(f"{path}: usa una URL externa ({external.group()[:60]}); solo se permite localhost")
    if errors:
        return errors
    required = required_routes(spec or set(), served) if (served or spec) else set()
    return check_karate(files, required) + check_selenium(files, frontend)


def build_guardrail(served: set[tuple[str, str]] | None = None, spec: set[tuple[str, str]] | None = None,
                    frontend_files: dict[str, str] | None = None):
    """Guardrail de QA: pruebas Karate/Selenium bien formadas, que cubran las rutas reales del Backend y usen
    solo selectores que existen en el Frontend."""
    frontend = frontend_selectors(frontend_files) if frontend_files else None

    def validate_testing_output(output):
        text = str(getattr(output, "raw", output) or "")
        errors = incomplete_output(text) + validate_files(parse_files(text), served, spec, frontend)
        if errors:
            return False, ("Pruebas inválidas. Corrige y vuelve a entregar TODOS los archivos con el formato "
                           "<<<FILE: ruta>>> + bloque de código + <<<FIN>>>:\n- " + "\n- ".join(errors[:12]))
        return True, text

    validate_testing_output.max_retries = TESTING_GUARDRAIL_RETRIES
    return validate_testing_output


def build_task(feature: dict) -> Task:
    feature_context = (
        f"Título: {feature.get('title', '')}\n"
        f"Descripción: {feature.get('description', '')}\n"
        f"Criterios de aceptación: {feature.get('acceptance_criteria', [])}"
    )

    return Task(
        description=f"{INSTRUCTIONS}\n\nFuncionalidad a probar:\n{feature_context}",
        expected_output=(
            "Archivos de prueba en formato <<<FILE: ruta>>> con bloque de código: karate/karate-config.js, "
            "karate/features/*.feature (Karate para la API) y selenium/conftest.py, selenium/test_*.py, "
            "selenium/requirements.txt (Selenium para la interfaz web), terminados con <<<FIN>>>."
        ),
        agent=agent,
    )
