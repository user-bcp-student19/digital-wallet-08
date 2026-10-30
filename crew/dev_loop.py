"""Bucle de desarrollo con herramientas para el agente Backend.

CopilotLLM no admite llamadas nativas a funciones, así que las herramientas se piden
en texto con bloques ``<<<TOOL nombre argumento>>> ... <<<END>>>``. Cada acción se
ejecuta dentro de un espacio de trabajo aislado (solo rutas relativas, sin comandos
arbitrarios) y su resultado vuelve al modelo en la siguiente iteración. El bucle
termina cuando ``run_pytest`` queda en verde y el agente llama a ``finish``, o cuando
se agota el límite de iteraciones.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_ITERATIONS = 12
MAX_ACTIONS_PER_TURN = 20
MAX_FILE_BYTES = 200_000
MAX_LISTED_FILES = 200
READ_CHARS = 20_000
OBSERVATION_CHARS = 4_000
HISTORY_CHARS = 40_000
COMMAND_TIMEOUT = 180
INSTALL_TIMEOUT = 600

CALL_RE = re.compile(
    r"<<<TOOL[ \t]+([a-z_]+)(?:[ \t]+([^\n<>]+?))?[ \t]*>>>\n?(.*?)<<<END>>>", re.DOTALL
)
# Variables de entorno con credenciales no se heredan en los comandos del agente.
SECRET_ENV_RE = re.compile(r"TOKEN|SECRET|PASSWORD|CREDENTIAL|API_?KEY|PRIVATE", re.IGNORECASE)

# Comandos de las herramientas run_*. "python" usa el intérprete actual.
COMMANDS = {
    "run_pytest": ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
    "run_ruff": ["python", "-m", "ruff", "check", "."],
    "run_npm_install": ["npm", "install", "--no-audit", "--no-fund"],
    "run_ng_build": ["npx", "ng", "build"],
    "run_ng_test": ["npx", "ng", "test", "--watch=false", "--browsers=ChromeHeadless"],
}

TOOL_DOCS = {
    "write_file": "write_file <ruta>: crea o reemplaza un archivo con su contenido completo.",
    "read_file": "read_file <ruta>: devuelve el contenido de un archivo.",
    "list_files": "list_files: lista los archivos del espacio de trabajo.",
    "run_pytest": "run_pytest: ejecuta las pruebas con pytest. Ejecútalo después de cada cambio.",
    "run_ruff": "run_ruff: ejecuta el linter ruff (informativo, no bloquea la entrega).",
    "run_npm_install": "run_npm_install: ejecuta npm install en la raíz del proyecto. Ejecútalo después de crear package.json.",
    "run_ng_build": "run_ng_build: ejecuta ng build. Debe terminar en verde.",
    "run_ng_test": "run_ng_test: ejecuta ng test con ChromeHeadless en modo CI. Debe terminar en verde.",
}


@dataclass(frozen=True)
class Profile:
    """Herramientas de un agente y compuertas que deben estar en verde para finalizar."""
    tools: tuple[str, ...]
    gates: tuple[str, ...]
    rules: tuple[str, ...]
    max_iterations: int = MAX_ITERATIONS
    # (herramienta, archivo manifiesto, carpeta): instala dependencias si falta la carpeta.
    bootstrap: tuple[str, str, str] | None = None


COMMON_RULES = (
    'Las rutas son relativas al espacio de trabajo: nunca uses rutas absolutas ni "..".',
    "Puedes pedir varias herramientas en una misma respuesta; se ejecutan en orden.",
    "Si una compuerta falla, lee la salida, corrige el código y vuelve a ejecutarla.",
    "Nunca escribas secretos ni credenciales en el código.",
)

BACKEND_PROFILE = Profile(
    tools=("write_file", "read_file", "list_files", "run_pytest", "run_ruff"),
    gates=("run_pytest",),
    rules=("Organiza el código en app/ (FastAPI) y las pruebas en tests/ (pytest).",),
)

FRONTEND_PROFILE = Profile(
    tools=("write_file", "read_file", "list_files", "run_npm_install", "run_ng_build", "run_ng_test"),
    gates=("run_ng_build", "run_ng_test"),
    rules=(
        "Escribe a mano el proyecto Angular en la raíz del espacio de trabajo (package.json, angular.json, "
        "tsconfig.json, src/). No ejecutes ng new.",
        "Usa componentes standalone, HttpClient y pruebas Jasmine/Karma en src/**/*.spec.ts.",
        "En karma.conf.js configura ChromeHeadless con singleRun para que ng test termine.",
    ),
    max_iterations=20,
    bootstrap=("run_npm_install", "package.json", "node_modules"),
)


def protocol(profile: Profile) -> str:
    lines = [f"- {TOOL_DOCS[name]}" for name in profile.tools]
    lines.append("- finish: termina tu trabajo. El cuerpo es el resumen para el revisor humano. "
                 f"Solo se acepta si {' y '.join(profile.gates)} terminaron en verde después de tu última escritura.")
    rules = "\n".join(f"- {rule}" for rule in (*profile.rules, *COMMON_RULES))
    return ("## Herramientas disponibles\n"
            "No ejecutas nada por ti mismo. Pide cada acción escribiendo un bloque con este formato exacto:\n\n"
            "<<<TOOL write_file ruta/archivo.ext>>>\ncontenido completo del archivo\n<<<END>>>\n\n"
            + "\n".join(lines) + "\n\nReglas:\n" + rules)


@dataclass
class DevResult:
    approved: bool
    summary: str
    iterations: int
    last_tests: str
    files: list[str]


def parse_calls(reply: str) -> list[tuple[str, str, str]]:
    """Devuelve (herramienta, argumento, cuerpo) de cada bloque en el orden en que aparecen."""
    return [(name, (arg or "").strip(), body) for name, arg, body in CALL_RE.findall(reply)]


def resolve_inside(root: Path, rel: str) -> Path:
    path = Path(rel)
    if not rel or path.is_absolute() or ".." in path.parts or ":" in rel:
        raise ValueError(f"Ruta no permitida: '{rel}'")
    target = (root / path).resolve()
    if root.resolve() not in target.parents:
        raise ValueError(f"Ruta fuera del espacio de trabajo: '{rel}'")
    return target


def _body(raw: str) -> str:
    """Quita el salto final y las cercas ``` que el modelo pueda añadir dentro del bloque."""
    lines = raw.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines) + "\n" if lines else ""


def _files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())[:MAX_LISTED_FILES]


def _tail(text: str) -> str:
    return text[-OBSERVATION_CHARS:]


def _argv(command: list[str]) -> list[str]:
    """'python' apunta al intérprete actual; npm y npx se resuelven a su .cmd en Windows."""
    if command[0] == "python":
        return [sys.executable, *command[1:]]
    return [shutil.which(command[0]) or command[0], *command[1:]]


def _run(command: list[str], root: Path, timeout: int = COMMAND_TIMEOUT) -> tuple[bool, str]:
    env = {k: v for k, v in os.environ.items() if not SECRET_ENV_RE.search(k)}
    env.update(PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run(_argv(command), cwd=root, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"Tiempo agotado tras {timeout} s"
    except OSError as error:
        return False, f"No se pudo ejecutar '{command[0]}': {error}"
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def execute(name: str, arg: str, body: str, root: Path) -> tuple[str, bool | None]:
    """Ejecuta una herramienta. Devuelve (observación, resultado de pruebas o None)."""
    try:
        if name == "write_file":
            target = resolve_inside(root, arg)
            content = _body(body)
            if len(content.encode("utf-8")) > MAX_FILE_BYTES:
                raise ValueError(f"Archivo demasiado grande (máximo {MAX_FILE_BYTES} bytes)")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"OK: {arg} escrito ({content.count(chr(10))} líneas)", None
        if name == "read_file":
            target = resolve_inside(root, arg)
            if not target.is_file():
                raise ValueError(f"No existe el archivo: '{arg}'")
            return target.read_text(encoding="utf-8")[:READ_CHARS], None
        if name == "list_files":
            return "\n".join(_files(root)) or "(vacío)", None
        if name in COMMANDS:
            timeout = INSTALL_TIMEOUT if name == "run_npm_install" else COMMAND_TIMEOUT
            ok, output = _run(COMMANDS[name], root, timeout)
            return f"{'OK' if ok else 'FALLO'} ({name.removeprefix('run_')}):\n{_tail(output)}", ok
        return f"ERROR: herramienta desconocida '{name}'", None
    except (ValueError, OSError) as error:
        return f"ERROR: {error}", None


def _prompt(task: str, root: Path, history: list[str], profile: Profile) -> str:
    transcript = "\n\n".join(history)[-HISTORY_CHARS:] or "(todavía sin acciones)"
    files = "\n".join(_files(root)) or "(vacío)"
    return (f"{task}\n\n{protocol(profile)}\n\n## Archivos actuales del espacio de trabajo\n{files}"
            f"\n\n## Historial de acciones de esta ejecución\n{transcript}")


def run_dev_loop(llm: Any, task: str, root: Path, max_iterations: int | None = None,
                 profile: Profile = BACKEND_PROFILE) -> DevResult:
    """Itera llm → acciones → resultados hasta que las compuertas pasan o se agota el límite."""
    max_iterations = max_iterations or profile.max_iterations
    root.mkdir(parents=True, exist_ok=True)
    history: list[str] = []
    green: set[str] = set()
    last_tests = "(las compuertas no se han ejecutado)"

    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteración {iteration}/{max_iterations} del agente ---", flush=True)
        calls = parse_calls(llm.call(_prompt(task, root, history, profile)))
        if not calls:
            print("  Sin herramientas válidas en la respuesta; se pide reintentar.", flush=True)
            history.append("SISTEMA: no encontré ninguna herramienta válida. Usa exactamente el formato <<<TOOL ...>>> ... <<<END>>>.")
            continue

        for name, arg, body in calls[:MAX_ACTIONS_PER_TURN]:
            if name == "finish":
                if set(profile.gates) <= green:
                    return DevResult(True, body.strip(), iteration, last_tests, _files(root))
                pending = ", ".join(gate for gate in profile.gates if gate not in green)
                observation = (f"RECHAZADO: no puedes finalizar. Faltan compuertas en verde: {pending}. "
                               "Deben terminar en verde después de tu última escritura.")
                print(f"  → finish rechazado: {observation}", flush=True)
                history.append(f"ACCIÓN finish\nRESULTADO:\n{observation}")
                continue
            if name not in profile.tools:
                observation = f"ERROR: herramienta no disponible para este agente: '{name}'"
                print(f"  → {observation}", flush=True)
                history.append(f"ACCIÓN {name}\nRESULTADO:\n{observation}")
                continue

            print(f"  → {name} {arg}".rstrip(), flush=True)
            observation, outcome = execute(name, arg, body, root)
            print("  ← " + observation[:600].replace("\n", "\n    "), flush=True)
            history.append(f"ACCIÓN {name} {arg}".rstrip() + f"\nRESULTADO:\n{observation}")
            if name == "write_file":
                green.clear()
            if name in profile.gates:
                green.add(name) if outcome else green.discard(name)
                last_tests = observation

    return DevResult(False, "Límite de iteraciones alcanzado sin compuertas en verde.",
                     max_iterations, last_tests, _files(root))


def verify_gates(root: Path, profile: Profile = BACKEND_PROFILE) -> tuple[bool, str]:
    """Vuelve a ejecutar las compuertas sin modelo. Sirve de evidencia para marcar tareas."""
    if not root.is_dir():
        return False, "(no existe el espacio de trabajo)"
    logs: list[str] = []
    if profile.bootstrap:
        tool, manifest, marker = profile.bootstrap
        if (root / manifest).is_file() and not (root / marker).exists():
            observation, ok = execute(tool, "", "", root)
            logs.append(observation)
            if not ok:
                return False, "\n\n".join(logs)
    for gate in profile.gates:
        observation, ok = execute(gate, "", "", root)
        logs.append(observation)
        if not ok:
            return False, "\n\n".join(logs)
    return True, "\n\n".join(logs)


def render_report(result: DevResult, workspace: Path, label: str) -> str:
    status = ("COMPUERTAS EN VERDE: listo para revisión humana." if result.approved
              else "INCOMPLETO: las compuertas no pasan. Revisa antes de aprobar.")
    files = "\n".join(f"- {name}" for name in result.files) or "- (sin archivos)"
    return (
        f"# Informe del agente {label}\n\n"
        f"Estado: {status}\n"
        f"Iteraciones usadas: {result.iterations}\n"
        f"Espacio de trabajo: {workspace}\n\n"
        f"## Resumen del agente\n{result.summary or '(sin resumen)'}\n\n"
        f"## Archivos\n{files}\n\n"
        f"## Última ejecución de compuertas\n```\n{result.last_tests}\n```\n"
    )
