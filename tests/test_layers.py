import ast
import subprocess
import sys
import unittest

from tests.helpers import BIN

# Radice di composizione: la CLI importa l'intero sistema (hook runner e flusso).
COMPOSITION_ROOT = "tollgate_core/cli.py"
UPPER = ("tollgate_flow", "tollgate_gate", "tollgate_hooks", "tollgate_checks")
FLOW_FORBIDDEN = ("tollgate_hooks", "tollgate_checks")
# Il gate gira su GitHub senza DB locale: dal nucleo importa solo i moduli senza stato.
GATE_CORE_ALLOWED = frozenset(
    ["tollgate_core", "tollgate_core.VERSION"]
    + [f"tollgate_core.{m}" for m in ("clock", "paths", "git", "config", "runner", "diffcheck",
                                      "ghcli")])
GATE_FORBIDDEN = ("tollgate_flow", "tollgate_hooks", "tollgate_checks")


def imported(source: str) -> set[str]:
    """Radici dei moduli importati, anche dentro le funzioni."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


def imported_modules(source: str, package: str) -> set[str]:
    """Nomi completi dei moduli importati, anche dentro le funzioni; gli import relativi sono
    risolti rispetto a `package`. `from <pacchetto> import x` dà `<pacchetto>.x` (x può essere
    un modulo); `from <pacchetto>.<modulo> import x` dà `<pacchetto>.<modulo>`."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[:len(package.split(".")) - (node.level - 1)]
                module = ".".join(base + ([node.module] if node.module else []))
            else:
                module = node.module or ""
            if "." not in module:
                found |= {f"{module}.{a.name}" for a in node.names if a.name != "*"} or {module}
            else:
                found.add(module)
    return found


def gate_import_problems(source: str, package: str = "tollgate_gate") -> list[str]:
    """Import vietati a un modulo di `tollgate_gate`: del nucleo solo i moduli senza stato, e
    nessun import dagli strati sopra (flusso, hook, controlli)."""
    bad = []
    for name in sorted(imported_modules(source, package)):
        root = name.split(".")[0]
        if root in GATE_FORBIDDEN or (root == "tollgate_core" and name not in GATE_CORE_ALLOWED):
            bad.append(name)
    return bad


def package_imports(package: str, forbidden: tuple, exempt=()) -> list[str]:
    bad = []
    for path in sorted((BIN / package).glob("*.py")):
        rel = f"{package}/{path.name}"
        if rel in exempt:
            continue
        for name in sorted(imported(path.read_text(encoding="utf-8")) & set(forbidden)):
            bad.append(f"{rel} importa {name}")
    return bad


def gate_modules() -> list[str]:
    return sorted(p.stem for p in (BIN / "tollgate_gate").glob("*.py"))


class LayersTest(unittest.TestCase):
    def test_imports(self):
        self.assertTrue((BIN / "tollgate_flow" / "__init__.py").is_file())
        self.assertEqual(package_imports("tollgate_flow", FLOW_FORBIDDEN), [])
        self.assertEqual(package_imports("tollgate_core", UPPER, exempt=(COMPOSITION_ROOT,)), [])

    def test_detector_sees_imports_inside_functions(self):
        self.assertEqual(imported("def f():\n    from tollgate_flow import x\n"),
                         {"tollgate_flow"})
        self.assertEqual(imported("import os.path\nfrom . import a"), {"os"})

    def test_imported_modules_full_names(self):
        self.assertEqual(imported_modules("from . import git", "tollgate_core"),
                         {"tollgate_core.git"})
        self.assertEqual(imported_modules("from .config import Config", "tollgate_core"),
                         {"tollgate_core.config"})
        self.assertEqual(imported_modules("from tollgate_core.config import Config",
                                          "tollgate_gate"), {"tollgate_core.config"})
        self.assertEqual(imported_modules("from tollgate_core import db, git", "tollgate_gate"),
                         {"tollgate_core.db", "tollgate_core.git"})
        self.assertEqual(imported_modules("import os.path\nimport tollgate_core.db",
                                          "tollgate_gate"), {"os.path", "tollgate_core.db"})
        self.assertEqual(imported_modules("def f():\n    from .. import x\n", "tollgate_gate.sub"),
                         {"tollgate_gate.x"})
        self.assertEqual(imported_modules("from ..core import y", "tollgate_gate.sub"),
                         {"tollgate_gate.core"})

    def test_gate_imports_allowlist(self):
        self.assertEqual(gate_import_problems("import tollgate_core.db"), ["tollgate_core.db"])
        self.assertEqual(gate_import_problems("from tollgate_core import db"),
                         ["tollgate_core.db"])
        self.assertEqual(gate_import_problems("def f():\n    from tollgate_core.cli import main"),
                         ["tollgate_core.cli"])
        self.assertEqual(gate_import_problems("from tollgate_flow import gh"),
                         ["tollgate_flow.gh"])
        self.assertEqual(gate_import_problems(
            "from tollgate_core import VERSION, git, clock\nfrom tollgate_core.config import C\n"
            "from tollgate_core.ghcli import api\nfrom tollgate_core import runner, diffcheck\n"
            "from tollgate_core.paths import State\nfrom tollgate_analysis import plan\n"
            "from . import l2tree\n"), [])
        for path in sorted((BIN / "tollgate_gate").glob("*.py")):
            with self.subTest(file=path.name):
                self.assertEqual(gate_import_problems(path.read_text(encoding="utf-8")), [])

    def test_core_does_not_import_gate(self):
        self.assertIn("tollgate_gate", UPPER)
        self.assertEqual(package_imports("tollgate_core", ("tollgate_gate",),
                                         exempt=(COMPOSITION_ROOT,)), [])
        self.assertEqual(imported("def f():\n    from tollgate_gate import x\n"),
                         {"tollgate_gate"})

    def test_gate_runtime_has_no_db(self):
        modules = gate_modules()
        self.assertIn("l2tree", modules)
        code = (
            "import importlib, sys\n"
            f"sys.path.insert(0, {str(BIN)!r})\n"
            f"for m in {modules!r}:\n"
            "    importlib.import_module('tollgate_gate' if m == '__init__' "
            "else 'tollgate_gate.' + m)\n"
            "print('tollgate_core.db' in sys.modules or 'sqlite3' in sys.modules)\n")
        r = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           timeout=60)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "False"), r.stderr)

    def test_flow_may_import_gate(self):
        self.assertEqual([n for n in imported("from tollgate_gate import l2tree")
                          if n in FLOW_FORBIDDEN], [])
        flow = (BIN / "tollgate_flow" / "l2tree.py").read_text(encoding="utf-8")
        self.assertIn("tollgate_gate", imported(flow))
        self.assertEqual(package_imports("tollgate_flow", FLOW_FORBIDDEN), [])


if __name__ == "__main__":
    unittest.main()
