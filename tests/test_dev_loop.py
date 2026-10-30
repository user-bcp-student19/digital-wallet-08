"""Exercise the backend tool loop with a scripted model and a real pytest run."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from crew.dev_loop import FRONTEND_PROFILE, parse_calls, resolve_inside, run_dev_loop

CALC = """<<<TOOL write_file app/calc.py>>>
def add(a, b):
    return a + b
<<<END>>>"""

CALC_TESTS = """<<<TOOL write_file tests/test_calc.py>>>
from app.calc import add

def test_add():
    assert add(2, 3) == 5
<<<END>>>"""

BUGGY_CALC = """<<<TOOL write_file app/calc.py>>>
def add(a, b):
    return a - b
<<<END>>>"""

FIXED_CALC = """<<<TOOL write_file app/calc.py>>>
def add(a, b):
    return a + b
<<<END>>>"""

PYTEST = "<<<TOOL run_pytest>>>\n<<<END>>>"
FINISH = "<<<TOOL finish>>>\nAPI de suma lista.\n<<<END>>>"


class ScriptedLLM:
    """Devuelve respuestas predefinidas y guarda los prompts recibidos."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def call(self, prompt):
        self.prompts.append(prompt)
        if not self.replies:
            raise AssertionError("El modelo fue llamado más veces de lo esperado")
        return self.replies.pop(0)


class DevLoopTests(unittest.TestCase):
    def run_loop(self, llm, workspace, max_iterations=12):
        with contextlib.redirect_stdout(io.StringIO()):
            return run_dev_loop(llm, "Implementa la suma.", workspace, max_iterations)

    def test_writes_tests_and_finishes_when_pytest_is_green(self):
        llm = ScriptedLLM([CALC + "\n" + CALC_TESTS, PYTEST, FINISH])
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "backend"
            result = self.run_loop(llm, workspace)
            self.assertTrue(result.approved)
            self.assertEqual(result.iterations, 3)
            self.assertEqual(result.summary, "API de suma lista.")
            self.assertIn("app/calc.py", result.files)
            self.assertIn("OK (pytest)", result.last_tests)
            self.assertTrue((workspace / "tests/test_calc.py").is_file())
            self.assertFalse(list(workspace.rglob("__pycache__")), "no debe generar __pycache__")

    def test_failing_pytest_is_fed_back_and_fixed(self):
        llm = ScriptedLLM([
            BUGGY_CALC + "\n" + CALC_TESTS,
            PYTEST,
            FINISH,  # rechazado: las pruebas fallan
            FIXED_CALC,
            PYTEST,
            FINISH,
        ])
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_loop(llm, Path(tmp) / "backend")
            self.assertTrue(result.approved)
            self.assertEqual(result.iterations, 6)
            # Cada prompt contiene las acciones previas, no la respuesta en curso.
            self.assertIn("FALLO (pytest)", llm.prompts[2])
            self.assertIn("assert", llm.prompts[2])
            self.assertIn("RECHAZADO", llm.prompts[3])

    def test_finish_is_rejected_after_a_write_without_retesting(self):
        llm = ScriptedLLM([
            CALC + "\n" + CALC_TESTS,
            PYTEST,
            BUGGY_CALC,
            FINISH,  # rechazado: se escribió después de la última ejecución verde
            "Sin herramientas.",
        ])
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_loop(llm, Path(tmp) / "backend", max_iterations=5)
            self.assertFalse(result.approved)
            self.assertIn("RECHAZADO", llm.prompts[4])

    def test_paths_outside_the_workspace_are_blocked(self):
        llm = ScriptedLLM([
            "<<<TOOL write_file ../evil.py>>>\nprint('x')\n<<<END>>>",
            "<<<TOOL write_file C:/evil.py>>>\nprint('x')\n<<<END>>>",
            "Sin herramientas aquí.",
        ])
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "backend"
            result = self.run_loop(llm, workspace, max_iterations=3)
            self.assertFalse(result.approved)
            self.assertIn("Ruta no permitida", llm.prompts[1])
            self.assertIn("Ruta no permitida", llm.prompts[2])
            self.assertFalse((Path(tmp) / "evil.py").exists())
            self.assertEqual(result.files, [])

    def test_parse_calls_handles_fences_and_tools_without_arguments(self):
        reply = (
            "<<<TOOL write_file app/a.py>>>\n```python\nx = 1\n```\n<<<END>>>\n"
            "<<<TOOL list_files>>>\n<<<END>>>"
        )
        calls = parse_calls(reply)
        self.assertEqual(calls[0], ("write_file", "app/a.py", "```python\nx = 1\n```\n"))
        self.assertEqual(calls[1], ("list_files", "", ""))

    def test_resolve_inside_rejects_escapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(resolve_inside(root, "app/a.py"), (root / "app" / "a.py").resolve())
            for bad in ("../x.py", "/etc/passwd", "C:/x.py", ""):
                with self.subTest(path=bad), self.assertRaises(ValueError):
                    resolve_inside(root, bad)

    def test_frontend_profile_rejects_backend_tools_and_needs_both_gates(self):
        llm = ScriptedLLM([PYTEST, FINISH, "Sin herramientas."])
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                result = run_dev_loop(llm, "Crea la UI.", Path(tmp) / "frontend", 3, FRONTEND_PROFILE)
            self.assertFalse(result.approved)
            self.assertIn("no disponible para este agente: 'run_pytest'", llm.prompts[1])
            self.assertIn("run_ng_build, run_ng_test", llm.prompts[2])


if __name__ == "__main__":
    unittest.main()
