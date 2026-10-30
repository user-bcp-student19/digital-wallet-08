"""Marca como hechas las tareas de tasks.md cuando las compuertas del paso pasan en verde."""
import re
from pathlib import Path

SECTION_RE = re.compile(r"^##\s.*\[([a-z_]+)\]\s*$")
OPEN_TASK_RE = re.compile(r"^(\s*-\s*)\[ \]")


def mark_done(tasks_file: Path, step: str, green: bool) -> int:
    """Cambia '- [ ]' a '- [x]' en las secciones etiquetadas con [step]. Devuelve cuántas marcó."""
    if not green or not tasks_file.is_file():
        return 0
    marked = 0
    section = None
    lines = []
    for line in tasks_file.read_text(encoding="utf-8").splitlines(keepends=True):
        if line.startswith("## "):
            match = SECTION_RE.match(line.rstrip("\r\n"))
            section = match.group(1) if match else None
        elif section == step and OPEN_TASK_RE.match(line):
            line = OPEN_TASK_RE.sub(r"\1[x]", line, count=1)
            marked += 1
        lines.append(line)
    if marked:
        tasks_file.write_text("".join(lines), encoding="utf-8")
    return marked
