"""Frontend: implementa en Angular el cliente que consume la API Python generada por el Backend."""
import json
import posixpath
import re
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

from crewai import Agent, Task
from crew.llm_config import llm
from agents.backend import SECRET_RE, incomplete_output, parse_files, spec_routes, write_files  # noqa: F401

KEY = 'frontend'
LABEL = 'FrontEnd'
SPEC_FILE = 'src/frontend_mock.py'
EXTRACT_CODE = True

OUTPUT_SUBDIR = Path("frontend-angular") / "web"
FRONTEND_GUARDRAIL_RETRIES = 10
BACKEND_PORT_TARGET = "localhost:8000"
REQUIRED_FILES = [
    "package.json", "angular.json", "tsconfig.json", "tsconfig.app.json", "proxy.conf.json",
    "src/index.html", "src/main.ts", "src/styles.scss",
    "src/app/app.component.ts", "src/app/app.config.ts",
]
ALLOWED_SUFFIXES = {".ts", ".html", ".scss", ".css", ".json", ".md", ".txt"}
MAX_FILES = 60
MAX_FILE_BYTES = 200_000

INSTRUCTIONS = """Actúa como Desarrollador Frontend especializado en Angular (versión 18 o superior, componentes standalone).
Recibes aprobados por el humano: el diagrama de arquitectura (architecture.mmd), el diagrama de secuencia
(sequence.mmd), el contrato OpenAPI del API local y el código del API Python/FastAPI que generó el agente Backend
(se ejecuta con `uvicorn app.main:app` en http://localhost:8000).

Implementa la aplicación Angular basándote estrictamente en esos artefactos:
- Una pantalla/componente por cada participante de interfaz del diagrama de secuencia y por cada componente web del
  diagrama de arquitectura; sigue el orden de interacciones del diagrama de secuencia.
- Consume ÚNICAMENTE las rutas que el Backend realmente implementó (se te entrega su lista exacta "Rutas expuestas por
  el Backend", con método y path completo, incluido el prefijo). No inventes endpoints ni uses URLs externas.
- Un servicio Angular (`HttpClient`) que consuma TODAS esas rutas, con interfaces TypeScript para sus
  peticiones/respuestas (según los modelos Pydantic del Backend) y manejo de los códigos de error (mensajes claros).
  Escribe cada URL completa en una sola cadena, p. ej. `${this.base}/accounts/${id}/consents`.
- Define la URL base con el prefijo real de las rutas del Backend (p. ej. `/v1`).
- Usa un proxy de desarrollo (`proxy.conf.json`) con ese prefijo como clave y destino http://localhost:8000 para evitar
  CORS; `package.json` debe tener `"start": "ng serve --proxy-config proxy.conf.json"`.
- Formularios reactivos con validación y estados de carga/error/éxito. Sin datos sensibles en logs ni en localStorage.
- Código completo y ejecutable: sin TODO, sin pantallas vacías. Prohibido: eval, new Function, document.write,
  innerHTML, bypassSecurityTrust*. No escribas secretos ni tokens en el código.

FORMATO DE SALIDA OBLIGATORIO. Entrega cada archivo así (rutas relativas, con `/`), sin texto fuera de este formato
salvo una breve nota final:

<<<FILE: package.json>>>
```json
{ "...": "contenido completo" }
```
<<<FILE: src/app/app.component.ts>>>
```typescript
// contenido completo
```
<<<FIN>>>

Archivos obligatorios: package.json (con @angular/core, @angular/common y rxjs), angular.json, tsconfig.json,
tsconfig.app.json, proxy.conf.json, src/index.html (con <app-root>), src/main.ts (bootstrapApplication),
src/styles.scss, src/app/app.component.ts y src/app/app.config.ts (con provideHttpClient).
Todo import relativo y todo templateUrl/styleUrl debe corresponder a un archivo que entregues.
"""

agent = Agent(
    role='Desarrollador Frontend',
    goal='Crear una aplicación Angular fluida, conectada de manera directa y funcional a la API Python del Backend y fiel a los diagramas de arquitectura y secuencia aprobados.',
    backstory=('Eres especialista en interfaces web Angular y clientes de API orientados a pasarelas de pago y onboarding, experto en consumir servicios FastAPI con enfoque en UX y reducción de fricción.'),
    llm=llm,
    verbose=True,
    allow_delegation=False,
    human_input=False,  # La aprobación humana la gestiona main.py
)


# ── Validación ─────────────────────────────────────────────────────
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
OPTIONAL_END_TAGS = {"p", "li", "option", "td", "th", "tr", "thead", "tbody", "dt", "dd"}
FORBIDDEN_TS = [
    (re.compile(r"\beval\s*\("), "eval()"),
    (re.compile(r"\bnew\s+Function\s*\("), "new Function()"),
    (re.compile(r"document\.write\s*\("), "document.write()"),
    (re.compile(r"bypassSecurityTrust"), "bypassSecurityTrust*"),
    (re.compile(r"\.innerHTML\s*="), "asignación a innerHTML"),
    (re.compile(r"\[innerHTML\]"), "[innerHTML]"),
    (re.compile(r"\bTODO\b|\bFIXME\b"), "TODO/FIXME pendiente"),
    (re.compile(r"localStorage\.setItem\([^)]*(password|contrase)", re.I), "contraseña en localStorage"),
]
REGEX_PRECEDERS = set("(,=:[!&|?{};")


def _unsafe_path(path: str) -> str | None:
    p = PurePosixPath(path)
    if not path or p.is_absolute() or re.match(r"^[A-Za-z]:", path) or ".." in p.parts:
        return "debe ser relativa y sin '..'"
    if p.suffix not in ALLOWED_SUFFIXES:
        return f"extensión no permitida ({p.suffix or 'sin extensión'})"
    if "node_modules" in p.parts:
        return "no incluyas node_modules"
    return None


def check_ts_syntax(src: str) -> str | None:
    """Comprueba balance de (), [], {}, cadenas, plantillas y comentarios en TypeScript. None si es correcto."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[tuple[str, int]] = []
    i, n, line, prev = 0, len(src), 1, ""
    while i < n:
        c = src[i]
        in_template = bool(stack) and stack[-1][0] == "`"
        if in_template:
            if c == "\\":
                i += 2
                continue
            if c == "\n":
                line += 1
            if c == "`":
                stack.pop()
                prev = "a"
            elif c == "$" and src[i + 1:i + 2] == "{":
                stack.append(("${", line))
                prev = "{"
                i += 1
            i += 1
            continue
        if c == "\n":
            line += 1
            i += 1
            continue
        if c.isspace():
            i += 1
            continue
        two = src[i:i + 2]
        if two == "//":
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if two == "/*":
            j = src.find("*/", i + 2)
            if j < 0:
                return f"línea {line}: comentario /* sin cerrar"
            line += src.count("\n", i, j)
            i = j + 2
            continue
        if c in "'\"":
            j = i + 1
            while j < n and src[j] != c:
                if src[j] == "\\":
                    j += 1
                elif src[j] == "\n":
                    return f"línea {line}: cadena sin cerrar"
                j += 1
            if j >= n:
                return f"línea {line}: cadena sin cerrar"
            i, prev = j + 1, "a"
            continue
        if c == "`":
            stack.append(("`", line))
            i += 1
            continue
        if c == "/" and (prev == "" or prev in REGEX_PRECEDERS or src[:i].rstrip().endswith("return")):
            j, in_class = i + 1, False
            while j < n and (in_class or src[j] != "/"):
                if src[j] == "\\":
                    j += 1
                elif src[j] == "[":
                    in_class = True
                elif src[j] == "]":
                    in_class = False
                elif src[j] == "\n":
                    return f"línea {line}: expresión regular sin cerrar"
                j += 1
            i, prev = j + 1, "a"
            continue
        if c in "([{":
            stack.append((c, line))
        elif c in ")]}":
            if c == "}" and stack and stack[-1][0] == "${":
                stack.pop()
            elif not stack or stack[-1][0] != pairs[c]:
                return f"línea {line}: '{c}' sin su apertura correspondiente"
            else:
                stack.pop()
        prev = c if not (c.isalnum() or c in "_$") else "a"
        i += 1
    if stack:
        symbol, opened = stack[-1]
        return f"'{symbol}' abierto en la línea {opened} nunca se cierra"
    return None


class _TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if tag not in self.stack:
            self.errors.append(f"</{tag}> sin etiqueta de apertura (línea {self.getpos()[0]})")
            return
        while self.stack[-1] != tag:
            open_tag = self.stack.pop()
            if open_tag not in OPTIONAL_END_TAGS:
                self.errors.append(f"<{open_tag}> sin cerrar antes de </{tag}> (línea {self.getpos()[0]})")
        self.stack.pop()


def check_html(src: str) -> str | None:
    parser = _TagChecker()
    parser.feed(src)
    parser.close()
    unclosed = [t for t in parser.stack if t not in OPTIONAL_END_TAGS]
    if parser.errors:
        return parser.errors[0]
    if unclosed:
        return f"etiqueta(s) sin cerrar: {', '.join(unclosed[:5])}"
    return None


def _json_error(path: str, content: str) -> str | None:
    try:
        json.loads(content)
    except json.JSONDecodeError as exc:
        if path.startswith("tsconfig"):  # tsconfig admite comentarios
            try:
                json.loads(re.sub(r"^\s*//.*$|/\*.*?\*/", "", content, flags=re.M | re.S))
                return None
            except json.JSONDecodeError:
                pass
        return f"{path}: JSON inválido (línea {exc.lineno}): {exc.msg}"
    return None


def _check_relative_refs(files: dict[str, str]) -> list[str]:
    """Imports relativos, templateUrl y styleUrl(s) deben existir entre los archivos entregados."""
    errors = []
    for path, content in files.items():
        if not path.endswith(".ts"):
            continue
        base = PurePosixPath(path).parent
        for ref in re.findall(r"""from\s+['"](\.{1,2}/[^'"]+)['"]""", content):
            target = posixpath.normpath(posixpath.join(base.as_posix(), ref))
            if not any(c in files for c in (target, f"{target}.ts", f"{target}/index.ts")):
                errors.append(f"{path}: importa '{ref}' pero no entregaste {target}.ts")
        for ref in re.findall(r"""(?:templateUrl|styleUrl)\s*:\s*['"]\./([^'"]+)['"]""", content) + \
                [r for grp in re.findall(r"styleUrls\s*:\s*\[([^\]]*)\]", content)
                 for r in re.findall(r"""['"]\./([^'"]+)['"]""", grp)]:
            if (base / ref).as_posix() not in files:
                errors.append(f"{path}: referencia './{ref}' pero no entregaste {(base / ref).as_posix()}")
    return errors


def _path_regex(path: str) -> re.Pattern:
    pattern = "".join(
        "/" + (r"(?:\$\{[^}]*\}|[^/'\"`?\s]+)" if part == "{}" else re.escape(part))
        for part in path.strip("/").split("/"))
    return re.compile(pattern + r"(?![A-Za-z0-9_{$/-])")


def _path_variants(path: str, strip_max: int) -> list[str]:
    """El path completo y sus versiones sin los primeros segmentos (el prefijo suele vivir en una constante base)."""
    parts = path.strip("/").split("/")
    return ["/" + "/".join(parts[n:]) for n in range(0, min(strip_max, len(parts) - 1) + 1)
            if n == 0 or parts[n] != "{}"]


def _common_prefix_len(paths: list[str]) -> int:
    split = [p.strip("/").split("/") for p in paths]
    count = 0
    for segments in zip(*split):
        if len(set(segments)) != 1:
            break
        count += 1
    return count


def required_routes(spec: set[tuple[str, str]], served: set[tuple[str, str]] | None) -> set[tuple[str, str]]:
    """Rutas que el frontend debe consumir: las del Backend que implementan el contrato (o todas las servidas)."""
    if not served:
        return {r for r in spec if r[1] != "/"}
    if not spec:
        return {r for r in served if r[1] != "/"}
    required = {(m, f) for m, f in served if any(m == sm and (f == sp or f.endswith(sp)) for sm, sp in spec)}
    return {r for r in (required or served) if r[1] != "/"}


def missing_endpoints(files: dict[str, str], required: set[tuple[str, str]]) -> list[str]:
    """Rutas del Backend cuyo path no aparece en ningún archivo .ts del frontend."""
    code = "\n".join(c for p, c in files.items() if p.endswith(".ts"))
    strip_max = _common_prefix_len([p for _, p in required]) if len(required) > 1 else 0
    return sorted({f"{m} {p}" for m, p in required
                   if not any(_path_regex(v).search(code) for v in _path_variants(p, strip_max))})


HTTP_CALL_RE = re.compile(
    r"\.(get|post|put|patch|delete)\s*(?:<[^()]*?>)?\s*\(\s*(`(?:[^`\\]|\\.)*`|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")",
    re.S)


def _called_url(literal: str) -> str | None:
    """Path normalizado de una URL literal usada en una llamada http; None si no parece una URL."""
    url = literal[1:-1]
    if url.startswith("http"):
        return url
    url = re.sub(r"^\$\{[^}]*\}", "", url)
    if not url.startswith("/"):
        return None
    url = re.sub(r"\$\{[^}]*\}", "{}", url.split("?")[0])
    return "/" + url.strip("/") if url.strip("/") else None


def check_http_calls(files: dict[str, str], served: set[tuple[str, str]]) -> list[str]:
    """Cada llamada HttpClient con URL literal debe corresponder a una ruta (y método) realmente servida por el Backend."""
    errors = []
    for path, content in files.items():
        if not path.endswith(".ts"):
            continue
        for method, literal in HTTP_CALL_RE.findall(content):
            url = _called_url(literal)
            if url is None:
                continue
            if url.startswith("http"):
                if BACKEND_PORT_TARGET not in url:
                    errors.append(f"{path}: llama a una URL externa {url[:60]}; el frontend solo debe consumir el API del Backend")
                continue
            matches = [(m, f) for m, f in served if f == url or f.endswith(url) or url.endswith(f)]
            if not any(m == method.upper() for m, _ in matches):
                if matches:
                    errors.append(f"{path}: {method.upper()} {url} no existe en el Backend; expone "
                                  + ", ".join(sorted({f'{m} {f}' for m, f in matches})[:3]))
                else:
                    errors.append(f"{path}: {method.upper()} {url} no es una ruta del Backend")
    return errors


def check_proxy(proxy: str, required: set[tuple[str, str]]) -> str | None:
    """El proxy de desarrollo debe cubrir los paths reales del Backend."""
    try:
        config = json.loads(proxy)
    except json.JSONDecodeError:
        return None
    if not isinstance(config, dict) or any(isinstance(v, dict) and "pathRewrite" in v for v in config.values()):
        return None
    contexts = [k.rstrip("*").rstrip("/") for k in config]
    uncovered = sorted({p for _, p in required if not any(p.startswith(c + "/") or p == c for c in contexts)})
    if uncovered:
        return (f"proxy.conf.json no cubre las rutas del Backend (claves: {', '.join(config) or 'ninguna'}); "
                f"p. ej. {uncovered[0]}")
    return None


def validate_files(files: dict[str, str], spec: set[tuple[str, str]],
                   served: set[tuple[str, str]] | None = None) -> list[str]:
    """Devuelve la lista de problemas de la app Angular entregada (vacía si todo es correcto)."""
    if not files:
        return ["no se encontró ningún archivo con el formato <<<FILE: ruta>>> + bloque de código"]
    errors = []
    if len(files) > MAX_FILES:
        errors.append(f"demasiados archivos ({len(files)}); máximo {MAX_FILES}")
    errors += [f"falta {req}" for req in REQUIRED_FILES if req not in files]

    for path, content in files.items():
        reason = _unsafe_path(path)
        if reason:
            errors.append(f"ruta inválida '{path}': {reason}")
            continue
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            errors.append(f"{path}: supera {MAX_FILE_BYTES} bytes")
        if SECRET_RE.search(content):
            errors.append(f"{path}: contiene un secreto o credencial escrita en el código")
        if path.endswith(".json"):
            error = _json_error(path, content)
            if error:
                errors.append(error)
        elif path.endswith(".ts"):
            error = check_ts_syntax(content)
            if error:
                errors.append(f"{path}: {error}")
        elif path.endswith(".html"):
            error = check_html(content)
            if error:
                errors.append(f"{path}: {error}")
        if path.endswith((".ts", ".html")):
            for rule, label in FORBIDDEN_TS:
                if rule.search(content):
                    errors.append(f"{path}: contiene {label}, no permitido")

    package = files.get("package.json", "")
    if package and not _json_error("package.json", package):
        data = json.loads(package)
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        for dep in ("@angular/core", "@angular/common", "rxjs"):
            if dep not in deps:
                errors.append(f"package.json debe declarar la dependencia {dep}")
        if "proxy.conf.json" not in str(data.get("scripts", {}).get("start", "")):
            errors.append('package.json: "start" debe ser "ng serve --proxy-config proxy.conf.json"')
    angular = files.get("angular.json", "")
    if angular and not _json_error("angular.json", angular) and "projects" not in json.loads(angular):
        errors.append("angular.json debe definir 'projects'")
    proxy = files.get("proxy.conf.json", "")
    if proxy and not _json_error("proxy.conf.json", proxy) and BACKEND_PORT_TARGET not in proxy:
        errors.append(f"proxy.conf.json debe apuntar al backend (http://{BACKEND_PORT_TARGET})")
    if "<app-root" not in files.get("src/index.html", "<app-root"):
        errors.append("src/index.html debe contener <app-root>")
    if "bootstrapApplication" not in files.get("src/main.ts", "bootstrapApplication"):
        errors.append("src/main.ts debe arrancar con bootstrapApplication(...)")
    if "provideHttpClient" not in files.get("src/app/app.config.ts", "provideHttpClient"):
        errors.append("src/app/app.config.ts debe registrar provideHttpClient()")
    if not any("HttpClient" in c for p, c in files.items() if p.endswith(".ts") and p != "src/app/app.config.ts"):
        errors.append("ningún servicio o componente inyecta HttpClient ('@angular/common/http') para llamar al backend")

    errors += _check_relative_refs(files)
    required = required_routes(spec, served)
    if served and not errors:
        errors += check_http_calls(files, served)
        proxy_error = check_proxy(proxy, required) if proxy else None
        if proxy_error:
            errors.append(proxy_error)
    if required and not errors:
        missing = missing_endpoints(files, required)
        if missing:
            errors.append("el frontend no consume estas rutas implementadas por el Backend: " + ", ".join(missing))
    return errors


def build_guardrail(openapi_text: str = "", served: set[tuple[str, str]] | None = None):
    """Crea el guardrail del Frontend, que verifica la app Angular contra las rutas realmente servidas por el Backend."""
    spec = spec_routes(openapi_text)

    def validate_frontend_output(output):
        text = str(getattr(output, "raw", output) or "")
        errors = incomplete_output(text) + validate_files(parse_files(text), spec, served)
        if errors:
            return False, ("Aplicación Angular inválida. Corrige y vuelve a entregar TODOS los archivos con el formato "
                           "<<<FILE: ruta>>> + bloque de código + <<<FIN>>>:\n- " + "\n- ".join(errors[:12]))
        return True, text

    validate_frontend_output.max_retries = FRONTEND_GUARDRAIL_RETRIES
    return validate_frontend_output


def build_task(feature: dict, backend_task=None) -> Task:
    """
    Construye la tarea de frontend. Si se proporciona backend_task,
    CrewAI le pasa automáticamente la salida del Backend como contexto
    para que conozca los endpoints exactos implementados.
    """
    task_kwargs = {
        "description": INSTRUCTIONS + "\nFeature: " + str(feature.get("title", "")),
        "expected_output": (
            "Archivos de una aplicación Angular en formato <<<FILE: ruta>>> con bloque de código, que consuma "
            "con HttpClient todos los endpoints de la API FastAPI del Backend y siga los diagramas de arquitectura "
            "y secuencia, terminados con <<<FIN>>>."
        ),
        "agent": agent,
    }

    # Vinculamos el contexto del Backend para que el Frontend consuma las APIs reales
    if backend_task:
        task_kwargs["context"] = [backend_task]

    return Task(**task_kwargs)
