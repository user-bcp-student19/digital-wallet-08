"""Reanudación del flujo: marcado de tareas por compuertas y selección de pasos a regenerar."""

import tempfile
import unittest
from pathlib import Path

from crew.task_status import mark_done
from crew.workflow import redo_from

TASKS = """# Tasks

## 1. Base de datos [backend]
- [ ] 1.1 Crear esquema
- [ ] 1.2 Crear índices

## 2. Frontend [frontend]
- [ ] 2.1 Crear login

## 3. Pruebas [testing]
- [ ] 3.1 E2E
"""

KEYS = ["specifier", "architect", "backend", "frontend", "testing", "security", "chapter"]


class MarkDoneTests(unittest.TestCase):
    def test_marks_only_the_tagged_section_when_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp) / "tasks.md"
            tasks.write_text(TASKS, encoding="utf-8")
            self.assertEqual(mark_done(tasks, "backend", True), 2)
            text = tasks.read_text(encoding="utf-8")
            self.assertIn("- [x] 1.1 Crear esquema", text)
            self.assertIn("- [x] 1.2 Crear índices", text)
            self.assertIn("- [ ] 2.1 Crear login", text)
            self.assertIn("- [ ] 3.1 E2E", text)

    def test_does_nothing_when_gates_are_not_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp) / "tasks.md"
            tasks.write_text(TASKS, encoding="utf-8")
            self.assertEqual(mark_done(tasks, "backend", False), 0)
            self.assertNotIn("[x]", tasks.read_text(encoding="utf-8"))

    def test_missing_file_is_ignored(self):
        self.assertEqual(mark_done(Path("no-existe/tasks.md"), "backend", True), 0)


class RedoTests(unittest.TestCase):
    def test_redo_includes_later_steps(self):
        self.assertEqual(redo_from(KEYS, {"frontend"}), {"frontend", "testing", "security", "chapter"})

    def test_empty_redo_selects_nothing(self):
        self.assertEqual(redo_from(KEYS, set()), set())

    def test_unknown_step_is_rejected(self):
        with self.assertRaises(ValueError):
            redo_from(KEYS, {"deploy"})


if __name__ == "__main__":
    unittest.main()
