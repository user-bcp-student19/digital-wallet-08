"""Exercise the six-role pipeline without calling Copilot or GitHub."""

import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import main as app
from crew.workflow import ROLES, STEPS, DATA_ROLES, build_tasks, workflow_steps, include_data


FEATURE = {
    "title": "Transfer funds",
    "description": "Transfer funds between accounts",
    "acceptance_criteria": ["Reject a transfer with insufficient funds"],
}

SPEC_OUTPUT = (
    "<<<PROPUESTA>>>\n## Why\nTransfers need validation.\n## What Changes\n- Validate balance.\n"
    "## Impact\nNone.\n"
    "<<<CAPACIDAD:transfer-funds>>>\n## ADDED Requirements\n"
    "### Requirement: Reject insufficient funds\nThe system SHALL reject transfers above the balance.\n"
    "#### Scenario: Insufficient funds\n- **WHEN** the amount exceeds the balance\n- **THEN** the transfer is rejected\n"
    "<<<FIN>>>"
)

ARCH_OUTPUT = (
    "<<<ARQUITECTURA>>>\n```mermaid\ngraph TD\nA-->B\n```\n"
    "<<<SECUENCIA>>>\n```mermaid\nsequenceDiagram\nA->>B: transfer\n```\n"
    "<<<OPENAPI>>>\n```yaml\nopenapi: 3.0.3\ninfo:\n  title: Transfers\n  version: 1.0.0\npaths: {}\n```\n"
    "<<<INFORME>>>\nInforme de arquitectura.\n"
    "<<<TAREAS>>>\n## 1. Backend\n- [ ] 1.1 Validar saldo\n"
    "<<<FIN>>>"
)


class WorkflowTests(unittest.TestCase):
    def test_each_role_builds_its_own_task(self):
        tasks = build_tasks(FEATURE)
        self.assertEqual(
            list(tasks),
            ["specs", "architect", "backend", "frontend", "testing", "security", "chapter"],
        )
        for role in ROLES:
            self.assertIs(tasks[role.KEY].agent, role.agent)
            self.assertIn("Transfer funds", tasks[role.KEY].description)
            self.assertIn(FEATURE["description"], tasks[role.KEY].description)
            for criterion in FEATURE["acceptance_criteria"]:
                self.assertIn(criterion, tasks[role.KEY].description)
            self.assertTrue(Path(role.__file__).is_file())

    def test_pipeline_saves_all_roles_and_resumes(self):
        self.check_pipeline(False)

    def test_seven_role_pipeline_saves_sql_passes_context_and_resumes(self):
        self.check_pipeline(True)

    def test_invalid_activation_is_rejected(self):
        with patch.dict("os.environ", {"CREWAI_INCLUDE_DATA": "maybe"}):
            with self.assertRaises(ValueError):
                include_data()

    def test_data_retry_rejection_and_resume_keep_human_gate(self):
        self.check_pipeline(True, interrupt_data=True)

    def test_real_openspec_cli_accepts_generated_change(self):
        if shutil.which("openspec") is None:
            self.skipTest("OpenSpec CLI no instalada (npm install -g @fission-ai/openspec)")
        with tempfile.TemporaryDirectory() as tmp:
            openspec = Path(tmp) / "openspec"
            openspec.mkdir()
            shutil.copy(app.OPENSPEC_DIR / "config.yaml", openspec / "config.yaml")
            change = openspec / "changes" / "transfer-funds"
            with patch.object(app, "OPENSPEC_DIR", openspec), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(app.check_output("specs", change, SPEC_OUTPUT), "")
                for rel, text in app.openspec_artifacts("specs", SPEC_OUTPUT).items():
                    (change / rel).parent.mkdir(parents=True, exist_ok=True)
                    (change / rel).write_text(text, encoding="utf-8")
                self.assertEqual(app.check_output("architect", change, ARCH_OUTPUT), "")
                for rel, text in app.openspec_artifacts("architect", ARCH_OUTPUT).items():
                    (change / rel).write_text(text, encoding="utf-8")
                valid, message = app.run_openspec_validate(change.name, cwd=Path(tmp))
            self.assertTrue(valid, message)

    def check_pipeline(self, with_data, interrupt_data=False):
        roles = DATA_ROLES if with_data else ROLES
        steps = workflow_steps(with_data)
        calls = []

        def run(agent, task):
            key = next(role.KEY for role in roles if role.agent is agent)
            calls.append((key, task.description))
            if key == "specs":
                return SPEC_OUTPUT
            if key == "architect":
                return ARCH_OUTPUT
            if key == "data":
                return "Approved data contract.\n```sql\n-- migration.sql\nCREATE TABLE accounts (id INTEGER PRIMARY KEY);\n```"
            if key == "backend":
                return "```python\n# balance_service.py\nclass BalanceService:\n    pass\n```"
            if key == "frontend":
                return "```typescript\n// balance.service.ts\nexport class BalanceService {}\n```"
            if key == "testing":
                return "Coverage report. NO EJECUTADO.\n```python\n# test_balance.py\ndef test_balance():\n    pass\n```"
            return f"Approved output from {key}. No model was called."

        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict("os.environ", {"CREWAI_INCLUDE_DATA": str(with_data).lower()}))
            output = Path(tmp)
            openspec = output / "openspec"
            change = openspec / "changes" / "transfer-funds"
            openspec.mkdir()
            (openspec / "config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
            stack.enter_context(patch.object(app, "OPENSPEC_DIR", openspec))
            stack.enter_context(patch.object(app, "run_openspec_validate", return_value=(True, "")))
            stack.enter_context(patch.object(app, "OUTPUT_DIR", output))
            stack.enter_context(
                patch.object(app, "CHECKPOINT_FILE", output / ".checkpoint.json")
            )
            stack.enter_context(patch.object(app, "proj_tools", return_value=[]))
            stack.enter_context(
                patch.object(
                    app,
                    "list_projects",
                    return_value=[{"id": "P1", "title": "Team backlog"}],
                )
            )
            stack.enter_context(
                patch.object(
                    app,
                    "list_project_items",
                    return_value=[{"title": FEATURE["title"]}],
                )
            )
            stack.enter_context(
                patch("mcp_projects.get_feature_from_item", return_value=FEATURE)
            )
            stack.enter_context(patch.object(app, "run_role", side_effect=lambda key, agent, task, change: (run(agent, task), None)))
            data_decisions = iter([("r", "Add a uniqueness constraint"), ("n", "")])
            def approve(label, result):
                if interrupt_data and label == "Datos y persistencia":
                    decision = next(data_decisions, ("s", ""))
                    if decision[0] != "s":
                        self.assertTrue((change / "reports/data_spec.md").is_file(), "el borrador debe quedar en disco para revisión")
                    return decision
                return "s", ""
            stack.enter_context(patch.object(app, "hitl_approve", side_effect=approve))
            stack.enter_context(patch("builtins.input", return_value="1"))
            stack.enter_context(patch("sys.argv", ["main.py"]))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if interrupt_data:
                with self.assertRaises(SystemExit):
                    app.main()
                rejected = json.loads((output / ".checkpoint.json").read_text())
                self.assertEqual(rejected["steps"]["data"]["status"], "rejected")
                self.assertNotIn("backend", rejected["steps"])
                self.assertIn("Add a uniqueness constraint", calls[3][1])
            app.main()

            expected = [role.KEY for role in roles]
            if interrupt_data:
                expected[2:3] = ["data", "data", "data"]
            self.assertEqual([key for key, _ in calls], expected)
            for name in ("proposal.md", "specs/transfer-funds/spec.md", "design.md", "tasks.md", "openapi.yaml"):
                self.assertTrue((change / name).is_file(), name)
            for key, _, _, spec, _ in steps:
                if key not in ("specs", "architect"):
                    self.assertTrue((change / "reports" / spec).is_file(), key)
            self.assertTrue((change / "code/backend/tests/test_balance.py").is_file())
            self.assertFalse((output / "backend").exists(), "el código no debe escribirse en output/")
            chapter_prompt = calls[-1][1]
            self.assertIn("Coverage report", chapter_prompt)
            self.assertIn("Approved output from security", chapter_prompt)
            checkpoint = json.loads((output / ".checkpoint.json").read_text())
            self.assertEqual(len(checkpoint["steps"]), len(roles))
            if with_data:
                self.assertEqual(list(dict.fromkeys(key for key, _ in calls))[:4], ["specs", "architect", "data", "backend"])
                self.assertIn("Approved data contract", next(prompt for key, prompt in calls if key == "backend"))
                self.assertIn("Approved data contract", chapter_prompt)
                self.assertTrue((change / "code/db/migration.sql").is_file())
            self.assertTrue(
                all(
                    step["status"] == "approved"
                    for step in checkpoint["steps"].values()
                )
            )

            app.main()
            self.assertEqual(
                len(calls), len(expected), "Approved steps must not call the model again"
            )
            before = (output / ".checkpoint.json").read_text()
            with patch.dict("os.environ", {"CREWAI_INCLUDE_DATA": str(not with_data).lower()}):
                with self.assertRaises(SystemExit) as stopped:
                    app.main()
                self.assertEqual(stopped.exception.code, 1)
            self.assertEqual((output / ".checkpoint.json").read_text(), before)


if __name__ == "__main__":
    unittest.main()
