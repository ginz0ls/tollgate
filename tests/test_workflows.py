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

    def test_any_escape_in_a_double_quoted_string_is_red_except_in_run(self):
        BS = "\\"
        red = [
            f'on: [\n  push,\n  "pull_request_{BS}x74arget"\n]\n',
            f'on:\n  [push, "pull_request_{BS}x74arget"]\n',
            f'permissions: {{\n  "{BS}x73tatuses"\n  : write\n}}\n',
            f'permissions:\n  "{BS}\n  x73tatuses": write\n',
            f'name: "a{BS}tb"\n',
            f'env:\n  A: "x{BS}ny"\n',
            f'steps:\n  - name: "x{BS}u0041"\n    run: echo\n',
            f'name: "multi\n  line {BS}x41"\n',
        ]
        for body in red:
            with self.subTest(body=body):
                self.assert_red(wf("") + body, "escape")
        ok = [
            f'    steps:\n      - run: "echo {BS}"ciao{BS}""\n',
            f'    steps:\n      - name: x\n        run: "echo {BS}"a{BS}n"\n',
            f'    steps:\n      - run: "echo {BS}"a\n          b{BS}" c"\n        name: y\n',
            f'    steps:\n      - run: |\n          echo "a{BS}tb"\n        name: y\n',
            f'    steps:\n      - run: >-\n          echo "a{BS}tb"\n',
            f'    steps:\n      - name: it\'s {BS}fine\n      - run: echo "a{BS}n"\n',
            f'    steps:\n      - name: \'a{BS}tb\'\n',
            f'    steps:\n      - name: x # "a{BS}tb"\n',
            f'    env:\n      A: |\n        "x{BS}ny"\n',
        ]
        for body in ok:
            with self.subTest(body=body):
                self.assertEqual(workflows.problems(wf(body)), [])

    def test_block_scalar_ends_at_the_next_key(self):
        text = wf('    steps:\n      - run: |\n          echo\n        env:\n          A: "x\\ny"\n')
        self.assert_red(text, "escape")

    def test_flow_collection_over_several_lines_fails_closed(self):
        BS = "\\"
        red = [
            # un `|` finale dentro un flusso non apre uno scalare a blocco
            f'permissions: {{contents: read, a: b - |\n  , "{BS}x73tatuses": write}}\n',
            f'on: {{push: {{}}, a: b - |\n  , !!str "pull_request_{BS}x74arget": {{}}}}\n',
            "on: [push,\n  pull_request]\n",
            "env: {A: '[',\n  B: x}\n",
        ]
        for body in red:
            with self.subTest(body=body):
                self.assert_red(wf("") + body, "flusso su più righe")
        self.assertEqual(workflows.problems(wf("    env: {A: '[', B: \"}\"}\n")), [])

    def test_quote_inside_a_flow_only_at_node_start(self):
        BS = "\\"
        self.assert_red(wf("", on=f'on: [push, -"x, "pull_request_{BS}x74arget"]\n'))
        self.assert_red(wf("    env: {A: x\"y}\n"), "virgolette")
        self.assertEqual(workflows.problems(wf("    env: {A: \"x\", 'B': 'y'}\n")), [])

    def test_quote_at_line_start_spanning_lines_fails_closed(self):
        BS = "\\"
        # continuazione di uno scalare semplice: per YAML `"y` è testo, non una stringa
        for cont in ('  "y\n', '  - "y\n'):
            with self.subTest(cont=cont):
                text = f'name: x\n{cont}on: [push, "pull_request_{BS}x74arget"]\n' \
                       "permissions: {}\n"
                self.assert_red(text, "su più righe")
        self.assertEqual(workflows.problems(wf('    env:\n      A: x\n        "y" z\n')), [])

    def test_single_quotes_doubled(self):
        BS = "\\"
        self.assert_red(wf("") + f"name: 'a'': \"'\non: [\"pull_request_{BS}x74arget\"]\n", "escape")
        self.assertEqual(workflows.problems(wf("    env:\n      A: 'it''s # x'\n")), [])

    def test_block_scalar_only_when_it_is_the_whole_value(self):
        BS = "\\"
        ok = [
            "    steps:\n      - run: |\n          if [ -f x ]; then echo {\n          a=[\n",
            "    steps:\n      - run: |2\n            &x y\n          ! grep z\n",
            "    steps:\n      - run: >-  # commento\n          !x\n",
            "    steps:\n      - |\n        !x\n",
        ]
        for body in ok:
            with self.subTest(body=body):
                self.assertEqual(workflows.problems(wf(body)), [])
        red = [
            ("    env:\n      A: a |\n        &x y\n", "àncora"),
            ("    env:\n      A: a |\n        !!str x\n", "tag"),
            ('    env:\n      A: a |\n        "' + BS + 'x41"\n', "escape"),
            # la riga dopo la fine del blocco torna controllata
            ("    steps:\n      - run: |\n          echo\n      - name: !!str x\n", "tag"),
            ("    steps:\n      - run: |\n          echo\n        env: {A: \"" + BS + "t\"}\n",
             "escape"),
            # rientro del contenuto: la prima riga lo fissa, una riga meno rientrata chiude
            ("    steps:\n      - run: |\n            echo\n          &a b\n", "àncora"),
            # con l'indicatore il rientro è fissato: `|2` sotto `run` (colonna 8) vuole 10
            ("    steps:\n      - run: |2\n         &a b\n", "àncora"),
        ]
        for body, needle in red:
            with self.subTest(body=body):
                self.assert_red(wf(body), needle)

    def test_complex_key_fails_closed(self):
        self.assert_red(wf("    permissions:\n      ? statuses\n      : write\n"), "chiave")
        self.assert_red(wf("    permissions:\n      ?\n"))
        self.assertEqual(workflows.problems(wf("    steps:\n      - run: echo ?\n")), [])

    def test_yaml_tags_fail_closed(self):
        BS = "\\"
        red = [
            f'on: [push, !!str "pull_request_{BS}x74arget"]\n',
            f'on:\n  - !!str "pull_request_{BS}x74arget"\n',
            f'permissions:\n  !!str "{BS}x73tatuses": write\n',
            f'permissions: {{!!str "{BS}x73tatuses": write}}\n',
            f'on: [!<tag:yaml.org,2002:str> "pull_request_{BS}x74arget"]\n',
            'on: !!str push\n',
            'name: !custom x\n',
            'steps: [!t a]\n',
            'env:\n  A: !!str 1\n',
        ]
        for body in red:
            with self.subTest(body=body):
                self.assert_red(wf("") + body, "tag")
        for body in ("    steps:\n      - run: echo a != b\n",
                     "    steps:\n      - run: |\n          ! grep -q x f\n          cp *.txt &x\n",
                     "    steps:\n      - name: x # !tag\n"):
            with self.subTest(body=body):
                self.assertEqual(workflows.problems(wf(body)), [])

    def test_tabs_after_colon_in_permissions(self):
        for body in ("    permissions:\n      statuses:\twrite\n",
                     "    permissions: {checks:\twrite}\n",
                     "    permissions: {statuses :\twrite}\n",
                     "    permissions:\n      statuses: \t write\n"):
            with self.subTest(body=body):
                self.assert_red(wf(body))
        self.assertEqual(workflows.problems(wf("    permissions:\n      statuses:\tread\n")), [])
        self.assertEqual(workflows.problems("on: push\npermissions\t: {}\n"), [])
        self.assertEqual(workflows.problems("on: push\npermissions:\tread-all\n"), [])

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

    def test_flow_mapping_without_space_is_red(self):
        """`{statuses:write}` (senza spazio dopo i due punti) non si legge come una chiave con
        valore: fail-closed, rosso."""
        for top in ("permissions: {statuses:write}\n",
                    "permissions: {contents: read, statuses:write}\n",
                    "permissions: {checks:write}\n",
                    'permissions: {"statuses":write}\n'):
            with self.subTest(top=top):
                self.assert_red(wf("", top=top), "invece di read o none")

    def test_unknown_permission_value_is_red(self):
        """Un valore diverso da `read` e `none` per `statuses` o `checks` è rosso, qualunque
        sia la forma in cui si scrive (anche in una collezione a flusso senza spazio)."""
        for scope in workflows.GUARDED_SCOPES:
            for value in ("write", "bogus", "Read", "NONE", "admin", "true", "read-all",
                          "${{ inputs.level }}", "write # read", "'write'"):
                with self.subTest(scope=scope, value=value):
                    self.assert_red(wf("", top=f"permissions:\n  {scope}: {value}\n"),
                                    "invece di read o none")
                    self.assert_red(wf("", top="permissions: {" + f"{scope}:{value}" + "}\n"),
                                    "invece di read o none")
            for value in ("read", "none", "'read'", '"none"'):
                with self.subTest(scope=scope, ok=value):
                    self.assertEqual(workflows.problems(
                        wf("", top=f"permissions:\n  {scope}: {value}\n")), [])


if __name__ == "__main__":
    unittest.main()
