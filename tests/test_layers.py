import ast
import unittest

from tests.helpers import BIN

# Radice di composizione: la CLI importa l'intero sistema (hook runner e flusso).
COMPOSITION_ROOT = "tollgate_core/cli.py"
UPPER = ("tollgate_flow", "tollgate_hooks", "tollgate_checks")
FLOW_FORBIDDEN = ("tollgate_hooks", "tollgate_checks")


def imported(source: str) -> set[str]:
    """Radici dei moduli importati, anche dentro le funzioni."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


def package_imports(package: str, forbidden: tuple, exempt=()) -> list[str]:
    bad = []
    for path in sorted((BIN / package).glob("*.py")):
        rel = f"{package}/{path.name}"
        if rel in exempt:
            continue
        for name in sorted(imported(path.read_text(encoding="utf-8")) & set(forbidden)):
            bad.append(f"{rel} importa {name}")
    return bad


class LayersTest(unittest.TestCase):
    def test_imports(self):
        self.assertTrue((BIN / "tollgate_flow" / "__init__.py").is_file())
        self.assertEqual(package_imports("tollgate_flow", FLOW_FORBIDDEN), [])
        self.assertEqual(package_imports("tollgate_core", UPPER, exempt=(COMPOSITION_ROOT,)), [])

    def test_detector_sees_imports_inside_functions(self):
        self.assertEqual(imported("def f():\n    from tollgate_flow import x\n"),
                         {"tollgate_flow"})
        self.assertEqual(imported("import os.path\nfrom . import a"), {"os"})


if __name__ == "__main__":
    unittest.main()
