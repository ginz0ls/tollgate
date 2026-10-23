"""La CI del plugin (`.github/workflows/ci.yml`): la suite su GitHub, con la stessa forma della
macchina di sviluppo (checkout in un percorso con uno spazio, `ResourceWarning` come errori)."""
import re
import unittest

from tests.helpers import ROOT
from tests.test_gate_workflows import EXPR, field, jobs, mapping, run_lines, section, steps
from tollgate_analysis import workflows

CI = ROOT / ".github" / "workflows" / "ci.yml"
SUITE = ('PYTHONS=python PYTHONWARNINGS=error::ResourceWarning tests/run 2>&1 | tee suite.log')


def text() -> str:
    return CI.read_text(encoding="utf-8")


def suite_job() -> list[str]:
    return jobs(text())["suite"]


def step_named(name: str) -> list[str]:
    found = [s for s in steps(text()) if field(s, "name") == name]
    assert len(found) == 1, name
    return found[0]


class CiWorkflowTest(unittest.TestCase):
    def test_triggers_and_permissions(self):
        self.assertEqual(sorted(mapping(section(text(), "on"), 2)), ["pull_request", "push"])
        # `push` senza filtri: tutti i rami
        self.assertEqual(mapping(section(text(), "on"), 2)["push"], "")
        self.assertEqual(section(text(), "push", 2), [])
        self.assertEqual(mapping(section(text(), "permissions"), 2), {"contents": "read"})
        self.assertNotIn("permissions:", "\n".join(suite_job()))
        self.assertEqual(mapping(section(text(), "concurrency"), 2)["cancel-in-progress"], "true")

    def test_matrix_and_timeout(self):
        job = suite_job()
        self.assertEqual(list(jobs(text())), ["suite"])
        self.assertEqual(mapping(section("\n".join(job), "matrix", 6), 8),
                         {"python": '["3.11", "3.13"]'})
        self.assertEqual(mapping(job, 4)["timeout-minutes"], "60")
        self.assertEqual(mapping(job, 4)["runs-on"], "ubuntu-latest")

    def test_checkout_path_with_space(self):
        checkout = [s for s in steps(text()) if (field(s, "uses") or "").startswith("actions/checkout@")]
        self.assertEqual(len(checkout), 1)
        self.assertEqual(field(checkout[0], "path"), '"tollgate src"')
        self.assertEqual(field(checkout[0], "persist-credentials"), "false")
        self.assertEqual(mapping(section("\n".join(section(text(), "defaults")), "run", 2), 4),
                         {"working-directory": '"tollgate src"'})
        setup = [s for s in steps(text()) if (field(s, "uses") or "").startswith("actions/setup-python@")]
        self.assertEqual(field(setup[0], "python-version"), "${{ matrix.python }}")

    def test_suite_step_uses_tests_run(self):
        self.assertEqual(run_lines("\n".join(step_named("suite"))), [SUITE])

    def test_suite_step_fails_when_tests_fail(self):
        """Senza `shell: bash` (`-eo pipefail`) il `tee` finale darebbe verde con la suite rossa."""
        step = step_named("suite")
        self.assertTrue(field(step, "shell") == "bash"
                        or any("set -o pipefail" in line for line in run_lines("\n".join(step))))

    def test_unclosed_database_fails(self):
        step = step_named("nessun database lasciato aperto")
        self.assertEqual(field(step, "shell"), "bash")
        body = "\n".join(run_lines("\n".join(step)))
        self.assertRegex(body, r'grep -q "unclosed database" suite\.log')
        self.assertIn("exit 1", body)

    def test_no_expressions_in_run_lines(self):
        found = run_lines(text())
        self.assertTrue(found)
        for line in found:
            self.assertNotIn(EXPR, line)

    def test_passes_workflow_rules(self):
        self.assertEqual(workflows.problems(text()), [])

    def test_actions_use_current_major_versions(self):
        uses = re.findall(r"uses:\s*(\S+)", text())
        self.assertEqual(uses, ["actions/checkout@v7", "actions/setup-python@v7"])
