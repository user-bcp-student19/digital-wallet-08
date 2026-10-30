"""Backend: implementa en FastAPI el diseño aprobado (Mermaid + OpenAPI) y lo entrega como proyecto completo."""
import ast
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

import yaml
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'backend'
LABEL = 'Backend'
SPEC_FILE = 'src/main.py'
EXTRACT_CODE = True

OUTPUT_SUBDIR = Path("backend-python") / "api"
BACKEND_GUARDRAIL_RETRIES = 10
MAIN_MODULE = "app/main.py"
MANIFEST = ".generated_files.json"
SMOKE_TIMEOUT_SECONDS = 60
REQUIRED_FILES = ["app/__init__.py", "app/main.py", "app/config.py", "requirements.txt", "README.md", ".env.example"]
ALLOWED_SUFFIXES = {".py", ".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".example", ".ini", ".cfg"}
ALLOWED_NAMES = {"Dockerfile", ".gitignore", ".dockerignore"}
MAX_FILES = 70
MAX_FILE_BYTES = 200_000
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}

INSTRUCTIONS = """Actúa como Ingeniero Backend especializado en FastAPI y Python.
Recibes aprobados por el humano: el diagrama de arquitectura (architecture.mmd), el diagrama de secuencia
(sequence.mmd) y el contrato OpenAPI del API local. Además, las especificaciones OpenAPI de las APIs y pasarelas
externas están en `client/openapi` (se incluyen como contexto).

Debes entregar el PROYECTO COMPLETO y ejecutable (no fragmentos), basado estrictamente en esos artefactos:
- Un módulo por componente local del diagrama de arquitectura (routers, servicios, repositorios, clientes externos).
- Respeta el recorrido del diagrama de secuencia (orden de llamadas, validaciones, errores y pasarelas externas).
- Implementa TODOS los paths y métodos del contrato OpenAPI local, con sus modelos Pydantic, códigos HTTP,
  validación de cabeceras y el esquema de error definido.
- Consume los servicios externos con `httpx` y timeouts explícitos; mapea sus errores como indica el contrato.
- Persistencia en memoria (diccionarios) salvo que el diseño indique otra cosa. Código completo y ejecutable:
  sin TODO, sin `raise NotImplementedError`, sin funciones vacías.
- Configuración por variables de entorno, TODAS con valor por defecto para que `uvicorn app.main:app` arranque sin
  `.env`. Nunca escribas secretos, tokens ni contraseñas en el código.
- Prohibido: eval, exec, os.system, subprocess, pickle y `shell=True`.

Estructura obligatoria del proyecto (rutas relativas a la raíz del proyecto):
- `app/__init__.py`, `app/main.py` (define `app = FastAPI(...)`, registra routers y manejadores de error),
  `app/config.py` (configuración desde variables de entorno con valores por defecto).
- `app/schemas/` (modelos Pydantic de peticiones/respuestas/errores), `app/routers/` (un router por componente o tag),
  `app/services/` (lógica de negocio), `app/repositories/` (persistencia en memoria), `app/clients/` (servicios
  externos), `app/errors.py` (excepciones y esquema de error). Cada carpeta con su `__init__.py`.
- `tests/__init__.py` y `tests/test_*.py` con pruebas (pytest + `fastapi.testclient.TestClient`) que cubran los
  endpoints y sus errores; los servicios externos se sustituyen por dobles, sin llamadas de red reales.
- `requirements.txt` con TODAS las dependencias que importa el código (fastapi, uvicorn, httpx, pydantic-settings si lo
  usas, pytest, etc.). `.env.example` con todas las variables de config. `README.md` con instalación, variables y cómo
  ejecutar (`uvicorn app.main:app --reload`, puerto 8000) y probar (`pytest`). `Dockerfile` (opcional) y `.gitignore`.
- Todo import local debe corresponder a un archivo que entregues.

FORMATO DE SALIDA OBLIGATORIO. Entrega cada archivo así (rutas relativas, con `/`), cada uno con su bloque de código
envuelto en ``` (si el archivo contiene bloques ``` internos, como un README, el cierre del archivo es el ``` final).
Sin texto fuera de este formato salvo una breve nota tras `<<<FIN>>>`:

<<<FILE: app/main.py>>>
```python
# contenido completo del archivo
```
<<<FILE: requirements.txt>>>
```text
fastapi
uvicorn
httpx
```
<<<FIN>>>
"""

agent = Agent(
    role='Ingeniero Backend Senior',
    goal='Implementar una API robusta, idempotente y de alto rendimiento en FastAPI siguiendo fielmente el diseño de arquitectura, el diagrama Mermaid y las especificaciones OpenAPI de client/openapi.',
    backstory=('Eres experto en desarrollo backend transaccional y diseño guiado por especificaciones (SDD), traduciendo diagramas de secuencia, contratos OpenAPI externos y arquitectura en código limpio de producción en Python.'),
    llm=llm,
    verbose=True,
    allow_delegation=False,
    human_input=False,  # La aprobación humana la gestiona main.py
)


# ── Parseo y escritura de archivos ─────────────────────────────────
FILE_MARKER_RE = re.compile(r"<<<FILE:\s*([^>\n]+?)\s*>>>")
FIN_MARKER = "<<<FIN>>>"


def _file_blocks(text: str) -> list[tuple[str, str, bool]]:
    """Divide la salida en (ruta, contenido, cerrado). El cierre de cada archivo es el último ``` de su bloque,
    de modo que un README con bloques ``` internos no se trunca."""
    markers = list(FILE_MARKER_RE.finditer(text))
    blocks = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        chunk = text[marker.end():end]
        if FIN_MARKER in chunk:
            chunk = chunk.split(FIN_MARKER)[0]
        chunk = chunk.strip()
        path = marker.group(1).strip().replace("\\", "/").removeprefix("./")
        opening = re.match(r"```[a-zA-Z0-9_+.-]*[ \t]*\n", chunk)
        if not opening or not chunk.endswith("```") or len(chunk) < opening.end() + 3:
            blocks.append((path, "", False))
            continue
        blocks.append((path, chunk[opening.end():-3].rstrip() + "\n", True))
    return blocks


def parse_files(text: str) -> dict[str, str]:
    """Extrae {ruta_relativa: contenido} de los bloques <<<FILE: ruta>>> + bloque de código."""
    return {path: content for path, content, closed in _file_blocks(text) if closed}


def incomplete_output(text: str) -> list[str]:
    """Problemas de integridad de la respuesta: archivos sin cerrar o respuesta cortada (sin <<<FIN>>>)."""
    problems = [f"el archivo {path or '(sin ruta)'} no tiene su bloque de código completo y cerrado con ```"
                for path, _, closed in _file_blocks(text) if not closed]
    if FILE_MARKER_RE.search(text) and FIN_MARKER not in text:
        problems.append("la respuesta está incompleta: falta <<<FIN>>> al final (¿se cortó?); entrega todos los archivos")
    return problems


def write_files(files: dict[str, str], root: Path) -> list[Path]:
    """Escribe los archivos bajo root, rechazando cualquier ruta que escape de él."""
    root = root.resolve()
    written = []
    for rel, content in files.items():
        target = (root / rel).resolve()
        if root != target and root not in target.parents:
            raise ValueError(f"Ruta fuera de {root}: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(target)
    return written


def sync_project(files: dict[str, str], root: Path) -> tuple[list[Path], list[Path]]:
    """Escribe el proyecto y borra solo los archivos que una generación anterior creó y esta ya no incluye."""
    root = root.resolve()
    manifest = root / MANIFEST
    removed = []
    if manifest.exists():
        try:
            previous = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = []
        for rel in previous:
            stale = (root / rel).resolve()
            if rel not in files and root in stale.parents and stale.is_file():
                stale.unlink()
                removed.append(stale)
    written = write_files(files, root)
    manifest.write_text(json.dumps(sorted(files), indent=2), encoding="utf-8")
    return written, removed


# ── Contrato OpenAPI y rutas implementadas ─────────────────────────
def _norm_path(path: str) -> str:
    path = re.sub(r"\{[^}]*\}", "{}", path.strip())
    return "/" + path.strip("/") if path.strip("/") else "/"


def spec_routes(openapi_text: str) -> set[tuple[str, str]]:
    """Pares (método, path) definidos en el OpenAPI aprobado."""
    try:
        paths = (yaml.safe_load(openapi_text) or {}).get("paths") or {}
        return {(m.upper(), _norm_path(p)) for p, ops in paths.items() if isinstance(ops, dict)
                for m in ops if m.lower() in HTTP_METHODS}
    except (yaml.YAMLError, AttributeError):
        return set()


def _first_str_arg(call: ast.Call) -> str | None:
    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
        return call.args[0].value
    return None


def code_routes(trees: dict[str, ast.AST]) -> set[tuple[str, str]]:
    """Rutas declaradas con @app.get(...)/@router.post(...), combinadas con los prefix de los routers."""
    routes, prefixes = [], {""}
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        prefixes.add(kw.value.value)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for deco in node.decorator_list:
                    if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute) \
                            and deco.func.attr in HTTP_METHODS:
                        path = _first_str_arg(deco)
                        if path is not None:
                            routes.append((deco.func.attr.upper(), path))
    full = set()
    for method, path in routes:
        for p1 in prefixes:
            for p2 in prefixes:
                full.add((method, _norm_path(p1 + p2 + path)))
    return full


def _missing_routes(spec: set[tuple[str, str]], implemented: set[tuple[str, str]]) -> list[str]:
    missing = []
    for method, path in sorted(spec):
        if not any(m == method and (p == path or p.endswith(path)) for m, p in implemented):
            missing.append(f"{method} {path}")
    return missing


def _module_file(module: str, files: dict[str, str]) -> str | None:
    for candidate in (f"{module}.py", f"{module}/__init__.py"):
        if candidate in files:
            return candidate
    return None


def _call_prefix(call: ast.Call) -> str:
    for kw in call.keywords:
        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
    return ""


def served_routes(files: dict[str, str]) -> set[tuple[str, str]]:
    """Rutas (método, path completo) que el backend realmente expone: resuelve los prefix de APIRouter e include_router."""
    trees = {}
    for path, content in files.items():
        if path.endswith(".py"):
            try:
                trees[path] = ast.parse(content)
            except SyntaxError:
                continue
    own: dict[tuple[str, str], str] = {}
    apps: set[tuple[str, str]] = set()
    routes: list[tuple[tuple[str, str], str, str]] = []
    includes: list[tuple[tuple[str, str], ast.expr, str, str]] = []
    imports: dict[tuple[str, str], tuple[str, str]] = {}

    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call):
                func = node.value.func
                kind = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and kind in {"APIRouter", "FastAPI"}:
                        own[(path, target.id)] = _call_prefix(node.value) if kind == "APIRouter" else ""
                        if kind == "FastAPI":
                            apps.add((path, target.id))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for deco in node.decorator_list:
                    if (isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute)
                            and deco.func.attr in HTTP_METHODS and isinstance(deco.func.value, ast.Name)):
                        route_path = _first_str_arg(deco)
                        if route_path is not None:
                            routes.append(((path, deco.func.value.id), deco.func.attr.upper(), route_path))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "include_router" and isinstance(node.func.value, ast.Name) and node.args:
                includes.append(((path, node.func.value.id), node.args[0], _call_prefix(node), path))
            elif isinstance(node, ast.ImportFrom):
                base = PurePosixPath(path).parent
                for _ in range(max(node.level - 1, 0)):
                    base = base.parent
                module = (node.module or "").replace(".", "/")
                module_path = (base / module).as_posix() if node.level else module
                module_path = "" if module_path == "." else module_path
                module_file = _module_file(module_path, files) if module_path else None
                for alias in node.names:
                    local = alias.asname or alias.name
                    submodule = _module_file(f"{module_path}/{alias.name}".lstrip("/"), files)
                    if submodule and not (module_file and any(k[0] == module_file and k[1] == alias.name for k in own)):
                        imports[(path, local)] = ("module", submodule)
                    elif module_file:
                        imports[(path, local)] = ("name", f"{module_file}::{alias.name}")

    def resolve(expr: ast.expr, path: str) -> tuple[str, str] | None:
        if isinstance(expr, ast.Name):
            if (path, expr.id) in own:
                return (path, expr.id)
            kind, target = imports.get((path, expr.id), ("", ""))
            if kind == "name":
                file, name = target.split("::")
                return (file, name) if (file, name) in own else None
        elif isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
            kind, target = imports.get((path, expr.value.id), ("", ""))
            if kind == "module" and (target, expr.attr) in own:
                return (target, expr.attr)
        return None

    totals: dict[tuple[str, str], set[str]] = {app: {""} for app in apps}
    edges = [(parent, resolve(child, path), inc) for parent, child, inc, path in includes]
    for _ in range(len(edges) + 1):  # propaga prefijos de padres a hijos hasta estabilizar
        changed = False
        for parent, child, inc in edges:
            if child is None or parent not in totals:
                continue
            new = {p + inc + own[child] for p in totals[parent]}
            if not new <= totals.setdefault(child, set()):
                totals[child] |= new
                changed = True
        if not changed:
            break

    served = set()
    for owner, method, route_path in routes:
        for prefix in totals.get(owner, ()):
            served.add((method, _norm_path(prefix + route_path)))
    return served or code_routes(trees)


# ── Guardrail ──────────────────────────────────────────────────────
SECRET_RE = re.compile(
    r"(gho_|ghp_|sk-)[A-Za-z0-9_]{8,}|(api[_-]?key|secret|token|password)\s*=\s*[\"'][^\"']{6,}[\"']", re.I)
FORBIDDEN_CALLS = {"eval", "exec"}
FORBIDDEN_MODULES = {"subprocess", "pickle"}


def _unsafe_path(path: str) -> str | None:
    p = PurePosixPath(path)
    if not path or p.is_absolute() or re.match(r"^[A-Za-z]:", path) or ".." in p.parts:
        return "debe ser relativa y sin '..'"
    if p.suffix not in ALLOWED_SUFFIXES and p.name not in ALLOWED_NAMES:
        return f"extensión no permitida ({p.suffix or 'sin extensión'})"
    if p.name == MANIFEST:
        return "nombre reservado"
    return None


def _check_python(path: str, source: str) -> tuple[ast.AST | None, list[str]]:
    errors = []
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return None, [f"{path}: error de sintaxis en línea {exc.lineno}: {exc.msg}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            is_os_system = name == "system" and getattr(getattr(node.func, "value", None), "id", "") == "os"
            if name in FORBIDDEN_CALLS or is_os_system:
                errors.append(f"{path}: llamada prohibida '{name}' (línea {node.lineno})")
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    errors.append(f"{path}: 'shell=True' prohibido (línea {node.lineno})")
        if isinstance(node, ast.Import):
            modules = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            modules = [node.module or ""]
        else:
            modules = []
        for module in modules:
            if module.split(".")[0] in FORBIDDEN_MODULES:
                errors.append(f"{path}: import prohibido '{module}' (línea {node.lineno})")
        if isinstance(node, ast.Raise) and "NotImplementedError" in ast.dump(node):
            errors.append(f"{path}: contiene 'raise NotImplementedError' (línea {node.lineno}); implementa la lógica")
    return tree, errors


def _module_exists(module_path: str, file_set: set[str]) -> bool:
    return (f"{module_path}.py" in file_set or f"{module_path}/__init__.py" in file_set
            or any(f.startswith(module_path + "/") for f in file_set))


def _check_local_imports(trees: dict[str, ast.AST], file_set: set[str]) -> list[str]:
    """Todo import de un paquete local debe corresponder a un archivo entregado."""
    tops = {f.split("/")[0].removesuffix(".py") for f in file_set}
    errors = []
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                base = PurePosixPath(path).parent
                for _ in range(node.level - 1):
                    base = base.parent
                module = (node.module or "").replace(".", "/")
                target = (base / module).as_posix() if module else base.as_posix()
                if module and not _module_exists(target, file_set):
                    errors.append(f"{path}: import relativo a '{node.module}' sin archivo correspondiente")
                continue
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                if module and module.split(".")[0] in tops:
                    mod_path = module.replace(".", "/")
                    if not _module_exists(mod_path, file_set):
                        errors.append(f"{path}: importa '{module}' pero no entregaste {mod_path}.py")
    return errors


STDLIB_MODULES = set(sys.stdlib_module_names)
IMPORT_TO_PACKAGE = {
    "yaml": "pyyaml", "jwt": "pyjwt", "jose": "python-jose", "multipart": "python-multipart",
    "dotenv": "python-dotenv", "pydantic_settings": "pydantic-settings", "email_validator": "email-validator",
    "PIL": "pillow", "dateutil": "python-dateutil", "bs4": "beautifulsoup4",
}
IMPLICIT_MODULES = {"pydantic", "pydantic_core", "starlette", "typing_extensions", "anyio", "annotated_types"}
SMOKE_ENV_KEYS = {"PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP", "HOME",
                  "USERPROFILE", "APPDATA", "LOCALAPPDATA"}
SMOKE_SCRIPT = """
import json, sys
sys.path.insert(0, ".")
from app.main import app
schema = app.openapi()
print("__PATHS__" + json.dumps({p: sorted(ops) for p, ops in schema.get("paths", {}).items()}))
"""
_smoke_cache: dict[str, tuple[set[tuple[str, str]] | None, str | None]] = {}


def _declared_packages(requirements: str) -> set[str]:
    declared = set()
    for line in requirements.splitlines():
        line = line.split("#")[0].strip()
        match = re.match(r"[A-Za-z0-9_.\-]+", line) if line and not line.startswith("-") else None
        if match:
            declared.add(re.sub(r"[_.]", "-", match.group().lower()))
    return declared


def _check_requirements(requirements: str, trees: dict[str, ast.AST], local_tops: set[str]) -> list[str]:
    """Toda librería de terceros que importa el código (app y tests) debe estar en requirements.txt."""
    declared = _declared_packages(requirements)
    missing: dict[str, str] = {}
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level:
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                top = module.split(".")[0]
                if not top or top in STDLIB_MODULES or top in local_tops or top in IMPLICIT_MODULES:
                    continue
                package = re.sub(r"[_.]", "-", IMPORT_TO_PACKAGE.get(top, top).lower())
                if package not in declared:
                    missing.setdefault(package, path)
    return [f"requirements.txt no declara '{pkg}' (se importa en {path})" for pkg, path in sorted(missing.items())]


def _check_project_structure(files: dict[str, str], trees: dict[str, ast.AST]) -> list[str]:
    errors = [f"falta {req}" for req in REQUIRED_FILES if req not in files]
    for prefix, label in (("app/routers/", "app/routers/ con al menos un router"),
                          ("app/services/", "app/services/ con la lógica de negocio"),
                          ("app/schemas", "app/schemas/ (o schemas.py) con los modelos Pydantic")):
        if not any(f.startswith(prefix) and f.endswith(".py") for f in files):
            errors.append(f"falta {label}")
    test_files = [f for f in files if f.startswith("tests/") and PurePosixPath(f).name.startswith("test_")
                  and f.endswith(".py")]
    has_tests = any(isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                    for f in test_files if f in trees for n in ast.walk(trees[f]))
    if not has_tests:
        errors.append("faltan pruebas: tests/test_*.py con funciones test_*")
    if "uvicorn app.main:app" not in files.get("README.md", "uvicorn app.main:app"):
        errors.append("README.md debe explicar cómo ejecutar: uvicorn app.main:app --reload")
    if ".env.example" in files and not files[".env.example"].strip():
        errors.append(".env.example no puede estar vacío")
    config = files.get("app/config.py", "")
    if config and not re.search(r"environ|getenv|BaseSettings", config):
        errors.append("app/config.py debe leer la configuración de variables de entorno")
    return errors


def smoke_test(files: dict[str, str]) -> tuple[set[tuple[str, str]] | None, str | None]:
    """Arranca el proyecto en una carpeta temporal (import app.main + app.openapi()) con un entorno limpio.
    Devuelve (rutas realmente servidas, error). Rutas None sin error = no se pudo ejecutar por el entorno."""
    if os.getenv("BACKEND_SMOKE_TEST", "1") == "0":
        return None, None
    key = hashlib.sha256(json.dumps(sorted(files.items())).encode("utf-8")).hexdigest()
    if key in _smoke_cache:
        return _smoke_cache[key]
    local_tops = {f.split("/")[0].removesuffix(".py") for f in files}
    env = {k: v for k, v in os.environ.items() if k.upper() in SMOKE_ENV_KEYS}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        write_files(files, Path(tmp))
        try:
            proc = subprocess.run([sys.executable, "-c", SMOKE_SCRIPT], cwd=tmp, env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=SMOKE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            result = (None, f"el proyecto no termina de arrancar en {SMOKE_TIMEOUT_SECONDS}s (import app.main)")
            _smoke_cache[key] = result
            return result
    if proc.returncode != 0:
        missing_module = re.search(r"ModuleNotFoundError: No module named '([\w.]+)'", proc.stderr)
        if missing_module and missing_module.group(1).split(".")[0] not in local_tops:
            logging.getLogger("digital_wallet").warning(
                "[BACKEND] Prueba de arranque omitida: falta instalar '%s' en este entorno", missing_module.group(1))
            result = (None, None)
        else:
            tail = "\n".join(proc.stderr.strip().splitlines()[-6:])
            result = (None, f"el proyecto no arranca (import app.main y app.openapi()):\n{tail[-700:]}")
    else:
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("__PATHS__")), None)
        paths = json.loads(line[len("__PATHS__"):]) if line else {}
        result = ({(m.upper(), _norm_path(p)) for p, methods in paths.items() for m in methods
                   if m in HTTP_METHODS}, None)
    _smoke_cache[key] = result
    return result


def runtime_routes(files: dict[str, str]) -> set[tuple[str, str]] | None:
    """Rutas que el proyecto expone al arrancar de verdad (None si no se pudo ejecutar)."""
    return smoke_test(files)[0]


def validate_files(files: dict[str, str], spec: set[tuple[str, str]], run_smoke: bool = True) -> list[str]:
    """Devuelve la lista de problemas del proyecto entregado (vacía si todo es correcto)."""
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
            errors.append(f"{path}: contiene un secreto o credencial escrita en el código; usa variables de entorno")
    errors += [f"falta {req}" for req in REQUIRED_FILES if req not in files]
    req = files.get("requirements.txt")
    if req is not None and not all(re.search(rf"^{pkg}\b", req, re.I | re.M) for pkg in ("fastapi", "uvicorn")):
        errors.append("requirements.txt debe incluir fastapi y uvicorn")

    trees = {}
    for path, content in files.items():
        if path.endswith(".py"):
            tree, py_errors = _check_python(path, content)
            errors += py_errors
            if tree is not None:
                trees[path] = tree
    if MAIN_MODULE in files and "FastAPI(" not in files[MAIN_MODULE]:
        errors.append(f"{MAIN_MODULE} debe crear la aplicación con FastAPI(...)")
    if trees:
        errors += _check_local_imports(trees, set(files))
        errors += [e for e in _check_project_structure(files, trees) if e not in errors]
        if req is not None:
            errors += _check_requirements(req, trees, {f.split("/")[0].removesuffix(".py") for f in files})
    implemented = None
    if run_smoke and not errors:
        implemented, smoke_error = smoke_test(files)
        if smoke_error:
            errors.append(smoke_error)
    if spec and not errors:
        missing = _missing_routes(spec, implemented if implemented is not None else code_routes(trees))
        if missing:
            errors.append("faltan endpoints del contrato OpenAPI: " + ", ".join(missing))
    return errors


def build_guardrail(openapi_text: str = ""):
    """Crea el guardrail del Backend: proyecto completo, arrancable y que implemente el OpenAPI aprobado."""
    spec = spec_routes(openapi_text)

    def validate_backend_output(output):
        text = str(getattr(output, "raw", output) or "")
        errors = incomplete_output(text) + validate_files(parse_files(text), spec)
        if errors:
            return False, ("Proyecto backend inválido. Corrige y vuelve a entregar el proyecto COMPLETO (todos los archivos) "
                           "con el formato <<<FILE: ruta>>> + bloque de código + <<<FIN>>>:\n- " + "\n- ".join(errors[:12]))
        return True, text

    validate_backend_output.max_retries = BACKEND_GUARDRAIL_RETRIES
    return validate_backend_output


def build_task(feature: dict, architect_task=None) -> Task:
    """
    Construye la tarea de backend. Si se proporciona architect_task,
    CrewAI le pasa automáticamente la salida del Arquitecto como contexto (incluyendo el Mermaid).
    """
    task_kwargs = {
        "description": INSTRUCTIONS + "\nFeature: " + str(feature.get("title", "")),
        "expected_output": (
            "Proyecto Python/FastAPI COMPLETO en formato <<<FILE: ruta>>> con bloque de código: app/ (config, schemas, "
            "routers, services, repositories, clients, errors, main), tests/, requirements.txt, .env.example, README.md, "
            "que arranque con uvicorn app.main:app e implemente todos los endpoints del contrato OpenAPI según los "
            "diagramas de arquitectura y secuencia, terminado con <<<FIN>>>."
        ),
        "agent": agent,
    }

    # Vinculamos el contexto del Arquitecto para que el Backend lea el Mermaid y las referencias
    if architect_task:
        task_kwargs["context"] = [architect_task]

    return Task(**task_kwargs)
