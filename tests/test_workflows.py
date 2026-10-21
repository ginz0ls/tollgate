import unittest

from tollgate_analysis import workflows

CLEAN = """name: ci
on: push
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 -B -m unittest
"""


def wf(body: str, *, top: str = "permissions: {contents: read}\n", on: str = "on: push\n") -> str:
    return f"name: x\n{on}{top}jobs:\n  a:\n    runs-on: ubuntu-latest\n{body}"


class WorkflowsTest(unittest.TestCase):
    def assert_red(self, text, needle=None):
        found = workflows.problems(text)
        self.assertTrue(found, text)
        if needle:
            self.assertTrue(any(needle in p for p in found), found)

    def test_constants(self):
        self.assertEqual(workflows.FORBIDDEN_EVENTS, ("pull_request_target", "workflow_run"))
        self.assertEqual(workflows.GUARDED_SCOPES, ("statuses", "checks"))
        self.assertEqual(workflows.SAFE_VALUES, ("read", "none"))

    def test_clean_workflow(self):
        self.assertEqual(workflows.problems(CLEAN), [])
        self.assertEqual(workflows.problems(wf("")), [])
        self.assertEqual(workflows.problems("on: push\npermissions: {contents: read}\n"), [])

    def test_forbidden_events(self):
        self.assert_red(wf("", on="on: pull_request_target\n"), "pull_request_target")
        self.assert_red(wf("", on="on: workflow_run\n"), "workflow_run")
        self.assert_red(wf("", on="on:\n  - push\n  - pull_request_target\n"))
        self.assert_red(wf("", on="on:\n  workflow_run:\n    workflows: [x]\n"))
        self.assert_red(wf("", on="on:\n  pull_request_target:\n    branches: [main]\n"))
        self.assertEqual(workflows.problems(wf("", on="on: [push, pull_request]\n")), [])

    def test_forbidden_permissions_any_level(self):
        self.assert_red(wf("    permissions:\n      statuses: write\n"), "statuses")
        self.assert_red(wf("    permissions:\n      checks: write\n"), "checks")
        self.assert_red(wf("", top="permissions: write-all\n"), "write-all")
        self.assert_red(wf("    permissions: write-all\n"), "write-all")
        self.assert_red(wf("    permissions:\n      statuses: admin\n"))
        self.assert_red(wf("    permissions:\n      statuses: read-all\n"))

    def test_quoted_and_flow_forms(self):
        for body in ('    permissions:\n      statuses: "write"\n',
                     "    permissions:\n      statuses: 'write'\n",
                     "    permissions: {statuses: write}\n",
                     "    permissions: {contents: read, checks: write}\n",
                     '    permissions:\n      "statuses": write\n',
                     "    permissions:\n      statuses:   write   # commento\n",
                     "    permissions:\n      statuses:\n        write\n",
                     "    permissions: {\n      statuses: write\n    }\n"):
            with self.subTest(body=body):
                self.assert_red(wf(body))
        self.assert_red(wf("", top="permissions: {statuses: write}\n"))
        self.assert_red(wf("", on="on: [push, pull_request_target]\n"))
        self.assert_red(wf("", on='on: ["pull_request_target"]\n'))
        for body in ("    permissions:\n      statuses: read\n",
                     "    permissions:\n      checks: none\n",
                     '    permissions:\n      statuses: "read"\n',
                     "    permissions: {statuses: read, checks: none}\n"):
            with self.subTest(body=body):
                self.assertEqual(workflows.problems(wf(body)), [])

    def test_job_named_like_a_scope_is_not_a_permission(self):
        text = "on: push\npermissions: {}\njobs:\n  checks:\n    runs-on: x\n  statuses:\n    runs-on: y\n"
        self.assertEqual(workflows.problems(text), [])

    def test_anchors_and_aliases_fail_closed(self):
        self.assert_red(wf("    permissions: &perm\n      contents: read\n"), "àncora")
        self.assert_red(wf("    permissions: *perm\n"), "alias")
        self.assert_red(wf("    <<: *perm\n"))
        self.assert_red(wf("    <<: {runs-on: x}\n"))
        self.assert_red(wf("    steps:\n      - *step\n"))
        self.assert_red(wf("    steps: [*a, b]\n"))
        self.assertEqual(workflows.problems(wf("    steps:\n      - run: a && b\n")), [])
        self.assertEqual(workflows.problems(wf("    env:\n      CRON: '* * * * *'\n")), [])

    def test_escapes_in_double_quoted_keys_and_events_fail_closed(self):
        self.assert_red(wf('    permissions:\n      "\\x73tatuses": write\n'), "escape")
        self.assert_red(wf("", on='on: "pull_request_\\x74arget"\n'), "escape")
        self.assert_red(wf("", on='on: ["pull_request_\\x74arget"]\n'))
        self.assert_red(wf("", on='on:\n  - "pull_request_\\x74arget"\n'))
        self.assert_red(wf("", on='on:\n  "pull_request_\\x74arget":\n'))
        self.assert_red(wf("    permissions: {\"\\x73tatuses\": write}\n"))
        # un escape in una stringa ordinaria non conta
        self.assertEqual(workflows.problems(wf('    steps:\n      - run: "echo \\"ciao\\""\n')),
                         [])
        self.assertEqual(workflows.problems(wf('    env:\n      A: "x\\ny"\n')), [])

    def test_complex_key_fails_closed(self):
        self.assert_red(wf("    permissions:\n      ? statuses\n      : write\n"), "chiave")
        self.assert_red(wf("    permissions:\n      ?\n"))
        self.assertEqual(workflows.problems(wf("    steps:\n      - run: echo ?\n")), [])

    def test_yaml_extension(self):
        self.assertTrue(workflows.is_workflow_path(".github/workflows/ci.yml"))
        self.assertTrue(workflows.is_workflow_path(".github/workflows/ci.yaml"))
        for rel in (".github/workflows/ci.txt", ".github/workflows/sub/ci.yml",
                    ".github/workflow/ci.yml", "x/.github/workflows/ci.yml",
                    ".github/workflows/.yml.bak", ".github/actions/a/action.yml"):
            with self.subTest(rel=rel):
                self.assertFalse(workflows.is_workflow_path(rel))

    def test_missing_top_level_permissions(self):
        self.assert_red("on: push\njobs:\n  a:\n    runs-on: x\n", "permissions di primo livello")
        # permissions solo nei job: rosso
        self.assert_red("on: push\njobs:\n  a:\n    permissions:\n      contents: read\n",
                        "permissions di primo livello")
        self.assertEqual(workflows.problems("on: push\npermissions: {}\n"), [])
        self.assertEqual(workflows.problems("on: push\n\"permissions\": read-all\n"), [])

    def test_comments_and_strings_ignored(self):
        text = wf("    steps:\n      # pull_request_target e statuses: write\n"
                  "      - run: echo ciao # workflow_run\n")
        self.assertEqual(workflows.problems(text), [])
        self.assertEqual(workflows.problems("# permissions: read\non: push\n"),
                         ["manca il blocco permissions di primo livello"])
        # in una stringa di run: conta (fail-closed)
        self.assert_red(wf("    steps:\n      - run: echo pull_request_target\n"),
                        "pull_request_target")
        self.assert_red(wf("    steps:\n      - run: |\n          echo workflow_run\n"))
        self.assert_red(wf("    steps:\n      - run: echo 'a # b' workflow_run\n"))

    def test_unreadable_is_a_problem(self):
        self.assert_red(CLEAN.replace("      - run", "\t- run"), "tabulazione")
        self.assert_red(CLEAN.replace("ci", "c\ufffdi", 1), "non UTF-8")
        self.assert_red(CLEAN + b"\xff".decode("utf-8", "surrogateescape"), "non UTF-8")
        self.assert_red(CLEAN + "\x00", "non UTF-8")
        # una tabulazione dopo il rientro non è un rientro
        self.assertEqual(workflows.problems(CLEAN.replace("echo", "echo\t")), [])

    def test_line_numbers(self):
        found = workflows.problems(wf("", on="on: pull_request_target\n"))
        self.assertEqual(found, ["usa pull_request_target (riga 2)"])


if __name__ == "__main__":
    unittest.main()
