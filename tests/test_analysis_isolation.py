import ast
import unittest

from tests.helpers import BIN

FORBIDDEN = ("tollgate_core", "tollgate_hooks", "tollgate_checks")


def _forbidden(name: str) -> bool:
    root = name.split(".")[0]
    return root in FORBIDDEN


def violations(source: str) -> list[str]:
    """Riferimenti vietati: import statici e dinamici, e stringhe uguali a un nome vietato
    o che ne cominciano con «<nome>.» (es. importlib.import_module("tollgate_core"))."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if _forbidden(a.name)]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if _forbidden(node.module or ""):
                found.append(node.module)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(node.value == f or node.value.startswith(f + ".") for f in FORBIDDEN):
                found.append(node.value)
    return found


class IsolationTest(unittest.TestCase):
    def test_analysis_imports_only_stdlib_and_itself(self):
        files = sorted((BIN / "tollgate_analysis").glob("*.py"))
        names = {p.name for p in files}
        self.assertIn("globs.py", names)
        self.assertGreaterEqual(len(files), 5)
        for path in files:
            with self.subTest(file=path.name):
                self.assertEqual(violations(path.read_text(encoding="utf-8")), [])

    def test_detector_catches_static_and_dynamic_references(self):
        self.assertEqual(violations("import tollgate_core.db"), ["tollgate_core.db"])
        self.assertEqual(violations("from tollgate_hooks import x"), ["tollgate_hooks"])
        self.assertEqual(violations('import importlib\nimportlib.import_module("tollgate_core")'),
                         ["tollgate_core"])
        self.assertEqual(violations('__import__("tollgate_checks.x")'), ["tollgate_checks.x"])
        self.assertEqual(violations('x = "tollgate_hooks.runner"'), ["tollgate_hooks.runner"])
        self.assertEqual(violations("import json\nfrom . import globs"), [])


if __name__ == "__main__":
    unittest.main()
