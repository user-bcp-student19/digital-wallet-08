"""Ejecución real de las pruebas QA: levanta Backend y Frontend, corre Karate (API) y Selenium (web),
mide los resultados y genera los reportes. Nada de lo que informa es inventado: todo sale de la salida de las herramientas."""
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from agents.backend import sync_project, write_files

log = logging.getLogger("digital_wallet")

BACKEND_HOST, BACKEND_PORT = "127.0.0.1", 8000
FRONTEND_PORT = 4200
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"
KARATE_VERSION = os.getenv("KARATE_VERSION", "1.5.1")
KARATE_URL = os.getenv("KARATE_JAR_URL", f"https://github.com/karatelabs/karate/releases/download/v{KARATE_VERSION}/karate-{KARATE_VERSION}.jar")
TOOLS_DIR = Path(os.getenv("QA_TOOLS_DIR", Path.home() / ".digital-wallet-qa"))
BACKEND_START_TIMEOUT = 90
FRONTEND_START_TIMEOUT = 420
INSTALL_TIMEOUT = 1500
KARATE_TIMEOUT = 600
SELENIUM_TIMEOUT = 900

PASSED, FAILED, ERROR, NOT_RUN = "PASSED", "FAILED", "ERROR", "NO EJECUTADO"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
KARATE_SUMMARY_RE = re.compile(r"scenarios:\s*(\d+)\s*\|\s*passed:\s*(\d+)\s*\|\s*failed:\s*(\d+)")
KARATE_ERROR_RE = re.compile(r"(?:status code was|match failed|assertion failed|did not evaluate to 'true'|"
                             r"javascript evaluation failed)[^\n]*", re.I)
SECRET_ENV_RE = re.compile(r"TOKEN|SECRET|PASSWORD|API[_-]?KEY|COPILOT|^GH_|^GITHUB_", re.I)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    action: str = ""  # lo que hará el flujo si falta (instalar, descargar...)


@dataclass
class ServiceStatus:
    name: str
    url: str
    ok: bool
    detail: str = ""


@dataclass
class SuiteResult:
    name: str
    tool: str
    status: str = NOT_RUN
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    command: str = ""
    reason: str = ""
    tests: list[tuple[str, str, str]] = field(default_factory=list)  # (grupo, nombre, estado)
    failures: list[str] = field(default_factory=list)
    output_tail: str = ""


@dataclass
class QARun:
    workdir: Path
    karate: SuiteResult
    selenium: SuiteResult
    services: list[ServiceStatus]
    started: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# ── Utilidades ─────────────────────────────────────────────────────
def _clean_env(**extra: str) -> dict[str, str]:
    """Entorno heredado sin credenciales (tokens, claves, Copilot, GitHub) para ejecutar código generado."""
    env = {k: v for k, v in os.environ.items() if not SECRET_ENV_RE.search(k)}
    env.update(extra)
    return env


def _clean(text: str) -> str:
    return ANSI_RE.sub("", text or "")


def _tail(text: str, lines: int = 30, width: int = 240) -> str:
    """Últimas líneas de una salida, sin colores y con cada línea recortada (las respuestas JSON pueden pesar KB)."""
    return "\n".join(ln if len(ln) <= width else ln[:width] + " …" for ln in _clean(text).strip().splitlines()[-lines:])


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env or _clean_env(), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _has_modules(python: str, modules: tuple[str, ...]) -> bool:
    try:
        return subprocess.run([python, "-c", "import " + ", ".join(modules)], capture_output=True, timeout=60).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _port_open(port: int) -> bool:
    for host in ("127.0.0.1", "::1"):
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            continue
    return False


def _listeners(port: int) -> list[tuple[int, str]]:
    """(pid, línea de comandos) de los procesos que escuchan en el puerto."""
    if os.name == "nt":
        script = (f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
                  "Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { "
                  "$p = Get-CimInstance Win32_Process -Filter \"ProcessId=$_\"; \"$_`t$($p.CommandLine)\" }")
        out = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30).stdout
    else:
        pids = subprocess.run(["lsof", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"], capture_output=True, text=True).stdout.split()
        out = "\n".join(f"{pid}\t" + subprocess.run(["ps", "-p", pid, "-o", "args="], capture_output=True, text=True).stdout.strip()
                        for pid in pids)
    result = []
    for line in out.splitlines():
        pid, _, cmd = line.partition("\t")
        if pid.strip().isdigit():
            result.append((int(pid), cmd))
    return result


def _kill_pid(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.kill(pid, 9)
        except OSError:
            pass


def free_port(port: int, marker: str) -> bool:
    """Detiene SOLO a los procesos que escuchan en el puerto y cuya línea de comandos contiene `marker`
    (la carpeta generada por el pipeline, p. ej. restos de una ejecución anterior). Devuelve True si el puerto queda libre."""
    for pid, cmd in _listeners(port):
        if marker.lower() in cmd.lower():
            log.info("[QA] Deteniendo proceso %s del pipeline que sigue escuchando en el puerto %d", pid, port)
            _kill_pid(pid)
    deadline = time.time() + 8
    while time.time() < deadline and _port_open(port):
        time.sleep(0.5)
    return not _port_open(port)


def _wait_http(url: str, timeout: int, proc: subprocess.Popen | None = None) -> tuple[bool, str]:
    deadline = time.time() + timeout
    last = "sin respuesta"
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            return False, f"el proceso terminó con código {proc.returncode} antes de responder"
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status < 500:
                    return True, f"HTTP {response.status}"
                last = f"HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                return True, f"HTTP {exc.code}"
            last = f"HTTP {exc.code}"
        except (urllib.error.URLError, OSError) as exc:
            last = str(getattr(exc, "reason", exc))[:80]
        time.sleep(1.5)
    return False, f"no respondió en {timeout}s ({last})"


def find_chrome() -> str | None:
    candidates = [shutil.which(n) for n in ("chrome", "google-chrome", "chromium", "chromium-browser")]
    for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            candidates.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
    candidates.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    return next((c for c in candidates if c and Path(c).is_file()), None)


# ── Herramientas: Karate y Selenium ────────────────────────────────
def karate_jar() -> Path | None:
    env = os.getenv("KARATE_JAR")
    if env and Path(env).is_file():
        return Path(env)
    jar = TOOLS_DIR / f"karate-{KARATE_VERSION}.jar"
    return jar if jar.is_file() and jar.stat().st_size > 10_000_000 else None


def download_karate() -> Path:
    """Descarga el JAR oficial de Karate (karatelabs/karate en GitHub) a la caché del usuario."""
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    jar = TOOLS_DIR / f"karate-{KARATE_VERSION}.jar"
    tmp = jar.with_suffix(".part")
    log.info("[QA] Descargando Karate %s desde %s", KARATE_VERSION, KARATE_URL)
    with urllib.request.urlopen(KARATE_URL, timeout=60) as response, tmp.open("wb") as out:
        total, done, step = int(response.headers.get("Content-Length") or 0), 0, 0
        while chunk := response.read(1 << 20):
            out.write(chunk)
            done += len(chunk)
            if done // (20 << 20) > step:
                step = done // (20 << 20)
                log.info("[QA] Karate: %d/%d MB", done >> 20, total >> 20)
    tmp.replace(jar)
    return jar


def selenium_python() -> str | None:
    """Intérprete con selenium y pytest ya instalados (el actual o el venv de caché), o None."""
    if _has_modules(sys.executable, ("selenium", "pytest")):
        return sys.executable
    cached = _venv_python(TOOLS_DIR / "venv")
    return str(cached) if cached.is_file() and _has_modules(str(cached), ("selenium", "pytest")) else None


def prepare_selenium_python(extra_requirements: str = "") -> str:
    """Crea (si hace falta) un venv de caché con selenium y pytest y devuelve su intérprete."""
    python = selenium_python()
    if python and not extra_requirements:
        return python
    venv = TOOLS_DIR / "venv"
    if not _venv_python(venv).is_file():
        log.info("[QA] Creando entorno virtual para Selenium en %s", venv)
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True, timeout=300)
    pip = [str(_venv_python(venv)), "-m", "pip", "install", "-q", "selenium", "pytest"]
    if extra_requirements:
        req = TOOLS_DIR / "selenium-extra-requirements.txt"
        req.write_text(extra_requirements, encoding="utf-8")
        pip += ["-r", str(req)]
    log.info("[QA] Instalando selenium y pytest...")
    result = subprocess.run(pip, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=INSTALL_TIMEOUT)
    if result.returncode != 0:
        raise RuntimeError("pip install selenium pytest falló:\n" + _tail(result.stderr or result.stdout, 8))
    return str(_venv_python(venv))


def preflight(backend_dir: Path, frontend_dir: Path) -> list[Check]:
    """Estado de las herramientas necesarias y de lo que el flujo hará si faltan."""
    chrome = find_chrome()
    return [
        Check("Backend (output/backend-python/api)", (backend_dir / "app/main.py").is_file(),
              str(backend_dir) if (backend_dir / "app/main.py").is_file() else "no existe app/main.py"),
        Check("Frontend (output/frontend-angular/web)", (frontend_dir / "package.json").is_file(),
              str(frontend_dir) if (frontend_dir / "package.json").is_file() else "no existe package.json"),
        Check("Java", bool(shutil.which("java")), shutil.which("java") or "no encontrado (necesario para Karate)"),
        Check("Node.js y npm", bool(shutil.which("node") and shutil.which("npm")),
              shutil.which("npm") or "no encontrado (necesario para el Frontend Angular)"),
        Check("Google Chrome", bool(chrome), chrome or "no encontrado (necesario para Selenium)"),
        Check(f"Karate {KARATE_VERSION}", karate_jar() is not None,
              str(karate_jar()) if karate_jar() else "no instalado",
              f"se descargará de GitHub (~70 MB) a {TOOLS_DIR}"),
        Check("Python con selenium y pytest", selenium_python() is not None,
              selenium_python() or "no instalado", f"se creará un entorno virtual en {TOOLS_DIR / 'venv'}"),
        Check("Dependencias del Backend", (backend_dir / ".venv").is_dir(),
              "entorno virtual .venv presente" if (backend_dir / ".venv").is_dir() else "sin .venv",
              "se creará .venv y se ejecutará pip install -r requirements.txt"),
        Check("Dependencias del Frontend", (frontend_dir / "node_modules").is_dir(),
              "node_modules presente" if (frontend_dir / "node_modules").is_dir() else "sin node_modules",
              "se ejecutará npm install"),
    ]


def format_preflight(checks: list[Check]) -> str:
    lines = []
    for c in checks:
        mark = "OK " if c.ok else ("-> " if c.action else "XX ")
        extra = f"  [{c.action}]" if not c.ok and c.action else ""
        lines.append(f"  {mark} {c.name}: {c.detail}{extra}")
    return "\n".join(lines)


# ── Servicios ──────────────────────────────────────────────────────
class Services:
    """Levanta el Backend (uvicorn) y el Frontend (ng serve), y los apaga siempre al terminar."""

    def __init__(self, backend_dir: Path, frontend_dir: Path):
        self.backend_dir, self.frontend_dir = backend_dir, frontend_dir
        self.logdir = Path(tempfile.mkdtemp(prefix="qa-services-"))
        self.procs: dict[str, subprocess.Popen] = {}
        self.statuses: list[ServiceStatus] = []

    def __enter__(self) -> "Services":
        return self

    def __exit__(self, *exc) -> None:
        self.stop()

    def _spawn(self, name: str, cmd: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen:
        logfile = (self.logdir / f"{name}.log").open("wb")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=logfile, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                creationflags=flags, start_new_session=os.name != "nt")
        self.procs[name] = proc
        return proc

    def log_tail(self, name: str, lines: int = 25) -> str:
        path = self.logdir / f"{name}.log"
        return _tail(path.read_text(encoding="utf-8", errors="replace"), lines) if path.exists() else ""

    def start_backend(self) -> ServiceStatus:
        name, url = "Backend", BACKEND_URL
        try:
            if _port_open(BACKEND_PORT) and not free_port(BACKEND_PORT, str(self.backend_dir)):
                return ServiceStatus(name, url, False, f"el puerto {BACKEND_PORT} ya está en uso por otro proceso; libéralo y reintenta")
            venv = self.backend_dir / ".venv"
            if not _venv_python(venv).is_file():
                log.info("[QA] Creando .venv del Backend")
                subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True, timeout=300)
            python = str(_venv_python(venv))
            log.info("[QA] Instalando dependencias del Backend (pip install -r requirements.txt)")
            install = _run([python, "-m", "pip", "install", "-q", "-r", "requirements.txt"], self.backend_dir, timeout=INSTALL_TIMEOUT)
            if install.returncode != 0:
                return ServiceStatus(name, url, False, "pip install falló: " + _tail(install.stderr or install.stdout, 6))
            log.info("[QA] Arrancando Backend en %s", BACKEND_URL)
            proc = self._spawn("backend", [python, "-m", "uvicorn", "app.main:app", "--host", BACKEND_HOST,
                                           "--port", str(BACKEND_PORT)], self.backend_dir,
                               _clean_env(PYTHONDONTWRITEBYTECODE="1"))
            ok, detail = _wait_http(f"http://{BACKEND_HOST}:{BACKEND_PORT}/openapi.json", BACKEND_START_TIMEOUT, proc)
            return ServiceStatus(name, url, ok, detail if ok else f"{detail}\n{self.log_tail('backend')}")
        except (subprocess.SubprocessError, OSError) as exc:
            return ServiceStatus(name, url, False, f"{type(exc).__name__}: {exc}")

    def start_frontend(self) -> ServiceStatus:
        name, url = "Frontend", FRONTEND_URL
        npm = shutil.which("npm")
        if not npm:
            return ServiceStatus(name, url, False, "npm no está instalado")
        try:
            if _port_open(FRONTEND_PORT) and not free_port(FRONTEND_PORT, str(self.frontend_dir)):
                return ServiceStatus(name, url, False, f"el puerto {FRONTEND_PORT} ya está en uso por otro proceso; libéralo y reintenta")
            env = _clean_env(NG_CLI_ANALYTICS="false", CI="true", NO_COLOR="1", FORCE_COLOR="0")
            if not (self.frontend_dir / "node_modules").is_dir():
                log.info("[QA] Instalando dependencias del Frontend (npm install); puede tardar varios minutos")
                install = _run([npm, "install", "--no-audit", "--no-fund"], self.frontend_dir, env, INSTALL_TIMEOUT)
                if install.returncode != 0:
                    return ServiceStatus(name, url, False, "npm install falló: " + _tail(install.stderr or install.stdout, 8))
            log.info("[QA] Arrancando Frontend en %s (la primera compilación puede tardar)", FRONTEND_URL)
            proc = self._spawn("frontend", [npm, "start", "--", "--port", str(FRONTEND_PORT)], self.frontend_dir, env)
            ok, detail = _wait_http(FRONTEND_URL, FRONTEND_START_TIMEOUT, proc)
            return ServiceStatus(name, url, ok, detail if ok else f"{detail}\n{self.log_tail('frontend')}")
        except (subprocess.SubprocessError, OSError) as exc:
            return ServiceStatus(name, url, False, f"{type(exc).__name__}: {exc}")

    def start(self) -> list[ServiceStatus]:
        backend = self.start_backend()
        frontend = self.start_frontend() if backend.ok else ServiceStatus(
            "Frontend", FRONTEND_URL, False, "no se intentó: el Backend no está operativo")
        self.statuses = [backend, frontend]
        for status in self.statuses:
            (log.info if status.ok else log.error)("[QA] %s %s: %s", status.name, "OPERATIVO" if status.ok else "CON ERROR",
                                                   status.detail.splitlines()[0] if status.detail else "")
        return self.statuses

    def stop(self) -> None:
        for name, proc in list(self.procs.items()):
            if proc.poll() is None:
                log.info("[QA] Deteniendo %s", name)
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
                else:
                    try:
                        os.killpg(proc.pid, 15)
                    except OSError:
                        proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
        # El árbol de procesos puede quedar a medias (lanzador del venv / hijo): barre lo que siga escuchando
        for name, port, folder in (("backend", BACKEND_PORT, self.backend_dir), ("frontend", FRONTEND_PORT, self.frontend_dir)):
            if name in self.procs and _port_open(port) and not free_port(port, str(folder)):
                log.error("[QA] El puerto %d sigue ocupado tras detener %s; ciérralo manualmente", port, name)
        self.procs.clear()


# ── Ejecución de las suites ────────────────────────────────────────
def _karate_scenarios(reports: Path) -> list[tuple[str, str, str]]:
    tests = []
    for path in sorted(reports.rglob("*.karate-json.txt")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        group = data.get("relativePath") or data.get("name") or path.stem
        for scenario in data.get("scenarioResults", []):
            tests.append((str(group), str(scenario.get("name") or scenario.get("refId") or "?"),
                          FAILED if scenario.get("failed") else PASSED))
    return tests


def run_karate(work: Path, jar: Path | None, base_url: str = BACKEND_URL) -> SuiteResult:
    result = SuiteResult("API", "Karate")
    features = work / "karate" / "features"
    if not shutil.which("java"):
        result.reason = "Java no está instalado"
        return result
    if jar is None:
        result.reason = "no está disponible el JAR de Karate"
        return result
    if not features.is_dir():
        result.reason = "no hay pruebas en karate/features"
        return result
    reports = work / "reports" / "karate"
    shutil.rmtree(reports, ignore_errors=True)
    cmd = ["java", "-Dfile.encoding=UTF-8", "-Dstdout.encoding=UTF-8", f"-DbaseUrl={base_url}",
           "-jar", str(jar), "-o", str(reports), "features"]
    result.command = f"java -DbaseUrl={base_url} -jar karate-{KARATE_VERSION}.jar -o reports features"
    start = time.time()
    try:
        proc = _run(cmd, work / "karate", timeout=KARATE_TIMEOUT)
    except subprocess.TimeoutExpired:
        result.status, result.reason, result.duration = ERROR, f"Karate excedió {KARATE_TIMEOUT}s", time.time() - start
        return result
    result.duration = time.time() - start
    output = _clean((proc.stdout or "") + "\n" + (proc.stderr or ""))
    result.output_tail = _tail(output, 40)
    summary = KARATE_SUMMARY_RE.search(output)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "karate-output.txt").write_text(output, encoding="utf-8")
    if not summary:
        result.status, result.reason = ERROR, f"Karate no produjo un resumen de resultados (código de salida {proc.returncode})"
        return result
    result.total, result.passed, result.failed = int(summary[1]), int(summary[2]), int(summary[3])
    result.status = PASSED if result.failed == 0 and proc.returncode == 0 else FAILED
    result.tests = _karate_scenarios(reports)
    reasons = list(dict.fromkeys(m.group().strip()[:220] for m in KARATE_ERROR_RE.finditer(output)))[:5]
    result.failures = [f"{g} :: {n}" for g, n, s in result.tests if s == FAILED]
    if result.status == FAILED:
        result.failures += [f"detalle: {r}" for r in reasons] or ["ver reports/karate-output.txt"]
    return result


def _parse_junit(path: Path) -> tuple[list[tuple[str, str, str]], dict[str, int], list[str]]:
    tests, failures = [], []
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    root = ET.parse(path).getroot()
    for case in root.iter("testcase"):
        group, name = case.get("classname") or "", case.get("name") or "?"
        problem = case.find("failure") if case.find("failure") is not None else case.find("error")
        if problem is not None:
            counts["failed"] += 1
            tests.append((group, name, FAILED))
            failures.append(f"{group}::{name} — {(problem.get('message') or '').strip().splitlines()[0][:200] if problem.get('message') else 'falló'}")
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
            tests.append((group, name, "SKIPPED"))
        else:
            counts["passed"] += 1
            tests.append((group, name, PASSED))
    return tests, counts, failures


def run_selenium(work: Path, python: str | None, base_url: str = FRONTEND_URL, api_url: str = BACKEND_URL) -> SuiteResult:
    result = SuiteResult("Web", "Selenium")
    folder = work / "selenium"
    if python is None:
        result.reason = "no hay un Python con selenium y pytest"
        return result
    if not find_chrome():
        result.reason = "Google Chrome no está instalado"
        return result
    if not any(folder.glob("test_*.py")):
        result.reason = "no hay pruebas en selenium/test_*.py"
        return result
    reports = work / "reports" / "selenium"
    shutil.rmtree(reports, ignore_errors=True)
    (reports / "screenshots").mkdir(parents=True, exist_ok=True)
    junit = reports / "junit.xml"
    cmd = [python, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider", f"--junitxml={junit}", "."]
    result.command = "pytest -q --junitxml=reports/junit.xml"
    env = _clean_env(BASE_URL=base_url, API_URL=api_url, HEADLESS="1", REPORT_DIR=str(reports), PYTHONDONTWRITEBYTECODE="1")
    start = time.time()
    try:
        proc = _run(cmd, folder, env, SELENIUM_TIMEOUT)
    except subprocess.TimeoutExpired:
        result.status, result.reason, result.duration = ERROR, f"Selenium excedió {SELENIUM_TIMEOUT}s", time.time() - start
        return result
    result.duration = time.time() - start
    output = _clean((proc.stdout or "") + "\n" + (proc.stderr or ""))
    result.output_tail = _tail(output, 40)
    (reports / "pytest-output.txt").write_text(output, encoding="utf-8")
    if not junit.is_file():
        result.status, result.reason = ERROR, f"pytest no generó junit.xml (código de salida {proc.returncode})"
        return result
    try:
        result.tests, counts, result.failures = _parse_junit(junit)
    except ET.ParseError as exc:
        result.status, result.reason = ERROR, f"junit.xml ilegible: {exc}"
        return result
    result.passed, result.failed, result.skipped = counts["passed"], counts["failed"], counts["skipped"]
    result.total = result.passed + result.failed + result.skipped
    result.status = ERROR if result.total == 0 else (FAILED if result.failed else PASSED)
    if result.total == 0:
        result.reason = "pytest no recolectó ninguna prueba"
    return result


def run_suites(files: dict[str, str], services: list[ServiceStatus], jar: Path | None, python: str | None,
               skip_reason: str = "") -> QARun:
    """Escribe las pruebas en una carpeta temporal y ejecuta Karate y Selenium según los servicios operativos."""
    work = Path(tempfile.mkdtemp(prefix="qa-run-"))
    write_files(files, work)
    up = {s.name: s.ok for s in services}
    karate, selenium = SuiteResult("API", "Karate"), SuiteResult("Web", "Selenium")
    if skip_reason:
        karate.reason = selenium.reason = skip_reason
    else:
        if up.get("Backend"):
            karate = run_karate(work, jar)
        else:
            karate.reason = "el Backend no está operativo"
        if up.get("Backend") and up.get("Frontend"):
            selenium = run_selenium(work, python)
        else:
            selenium.reason = "el Frontend o el Backend no están operativos"
    return QARun(work, karate, selenium, services)


# ── Resumen, publicación e informe ─────────────────────────────────
def global_status(run: QARun) -> str:
    statuses = {run.karate.status, run.selenium.status}
    if statuses & {FAILED, ERROR}:
        return "FALLIDO"
    if NOT_RUN in statuses:
        return "INCOMPLETO (hay pruebas NO EJECUTADAS)"
    return "APROBADO"


def _row(s: SuiteResult) -> str:
    if s.status == NOT_RUN:
        return f"{s.tool:<9} {s.name:<4} {NOT_RUN}  — {s.reason}"
    detail = f"{s.passed}/{s.total} pasadas, {s.failed} falladas, {s.skipped} omitidas, {s.duration:.1f}s"
    return f"{s.tool:<9} {s.name:<4} {s.status:<8} {detail}" + (f"  — {s.reason}" if s.reason else "")


def format_summary(run: QARun) -> str:
    lines = ["Servicios:"] + [f"  {'OK' if s.ok else 'XX'} {s.name} {s.url}: {s.detail.splitlines()[0] if s.detail else ''}"
                              for s in run.services]
    lines += ["Pruebas:", f"  {_row(run.karate)}", f"  {_row(run.selenium)}"]
    for suite in (run.karate, run.selenium):
        lines += [f"  FALLO [{suite.tool}]: {f}" for f in suite.failures[:8]]
    lines.append(f"Resultado global: {global_status(run)}")
    return "\n".join(lines)


def _suite_section(s: SuiteResult, folder: str) -> str:
    out = [f"## {s.name} — {s.tool}", "", f"- **Estado:** {s.status}"]
    if s.reason:
        out.append(f"- **Motivo:** {s.reason}")
    if s.status != NOT_RUN:
        out += [f"- **Resultados:** {s.passed} pasadas, {s.failed} falladas, {s.skipped} omitidas de {s.total}",
                f"- **Duración:** {s.duration:.1f} s"]
    out += [f"- **Implementación y reportes:** `output/qa/{folder}/`"]
    if s.command:
        out.append(f"- **Comando ejecutado:** `{s.command}`")
    if s.tests:
        out += ["", "| Grupo | Prueba | Estado |", "|---|---|---|"]
        out += [f"| {g} | {n.replace('|', '/')} | {st} |" for g, n, st in s.tests]
    if s.failures:
        out += ["", "**Fallos observados:**"] + [f"- {f}" for f in s.failures]
    if s.status in {FAILED, ERROR} and s.output_tail:
        out += ["", "<details><summary>Salida (últimas líneas)</summary>", "", "```text", s.output_tail, "```", "", "</details>"]
    return "\n".join(out)


def render_report(run: QARun, feature: dict, approved_at: str, rel_backend: str, rel_frontend: str) -> str:
    criteria = feature.get("acceptance_criteria") or []
    gaps = [f"{s.tool}: {s.reason}" for s in (run.karate, run.selenium) if s.status in {NOT_RUN, ERROR}]
    gaps += [f"{c.name}: {c.detail.splitlines()[0]}" for c in run.services if not c.ok]
    verdict = global_status(run)
    parts = [
        f"# Informe ejecutivo de pruebas — {feature.get('title', '')}", "",
        f"- **Fecha de ejecución:** {run.started}",
        f"- **Aprobación humana de los resultados:** {approved_at}",
        f"- **Resultado global:** **{verdict}**", "",
        "## Resumen", "",
        "| Suite | Herramienta | Estado | Total | Pasadas | Falladas | Omitidas | Duración |", "|---|---|---|---|---|---|---|---|",
    ]
    for s in (run.karate, run.selenium):
        parts.append(f"| {s.name} | {s.tool} | {s.status} | {s.total} | {s.passed} | {s.failed} | {s.skipped} | {s.duration:.1f} s |")
    parts += ["", "## Entorno", ""]
    parts += [f"- **{s.name}** ({s.url}): {'operativo' if s.ok else 'CON ERROR'}"
              + ("" if s.ok or not s.detail else f" — {s.detail.splitlines()[0]}") for s in run.services]
    parts += ["", "## Criterios de aceptación de la funcionalidad", ""]
    parts += [f"- {c}" for c in criteria] or ["- (la funcionalidad no define criterios de aceptación)"]
    parts += ["", _suite_section(run.karate, "karate"), "", _suite_section(run.selenium, "selenium"), "",
              "## Brechas y pendientes", ""]
    parts += [f"- {g}" for g in gaps] or ["- Ninguna: todas las suites se ejecutaron."]
    parts += [
        "", "## Cómo reproducir", "", "```bash",
        f"cd {rel_backend} && pip install -r requirements.txt && uvicorn app.main:app --port {BACKEND_PORT}",
        f"cd {rel_frontend} && npm install && npm start",
        f"cd output/qa/karate && java -DbaseUrl={BACKEND_URL} -jar karate-{KARATE_VERSION}.jar -o reports features",
        f"cd output/qa/selenium && pip install -r requirements.txt && BASE_URL={FRONTEND_URL} pytest -q",
        "```", "",
        "> Los resultados provienen de la ejecución real de Karate y Selenium; una suite que no pudo ejecutarse figura como "
        "NO EJECUTADO con su motivo, sin resultados inventados.", "",
    ]
    return "\n".join(parts)


def _split(files: dict[str, str], prefix: str) -> dict[str, str]:
    return {rel[len(prefix):]: content for rel, content in files.items() if rel.startswith(prefix)}


def publish(run: QARun, files: dict[str, str], qa_dir: Path, report_path: Path, feature: dict,
            rel_backend: str, rel_frontend: str) -> list[Path]:
    """Paso 4: tras la aprobación humana, escribe output/qa/{karate,selenium}/ (código + reportes) e informes/testing.md."""
    written: list[Path] = []
    for folder in ("karate", "selenium"):
        target = qa_dir / folder
        paths, removed = sync_project(_split(files, f"{folder}/"), target)
        written += paths
        for old in removed:
            log.info("[QA] Eliminado (obsoleto de una generación anterior): %s", old)
        source = run.workdir / "reports" / folder
        dest = target / "reports"
        shutil.rmtree(dest, ignore_errors=True)
        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            dest.mkdir(parents=True, exist_ok=True)
        suite = run.karate if folder == "karate" else run.selenium
        result_file = dest / "resultado.json"
        result_file.write_text(json.dumps({
            "suite": suite.name, "tool": suite.tool, "status": suite.status, "total": suite.total, "passed": suite.passed,
            "failed": suite.failed, "skipped": suite.skipped, "duration_seconds": round(suite.duration, 2),
            "command": suite.command, "reason": suite.reason, "tests": suite.tests, "failures": suite.failures,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(result_file)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(run, feature, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                         rel_backend, rel_frontend), encoding="utf-8")
    written.append(report_path)
    shutil.rmtree(run.workdir, ignore_errors=True)
    return written
