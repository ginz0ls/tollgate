import ast
import unittest

from tests.helpers import BIN

FORBIDDEN = ("tollgate_core", "tollgate_hooks", "tollgate_checks")


class IsolationTest(unittest.TestCase):
    def test_analysis_imports_only_stdlib_and_itself(self):
        for path in sorted((BIN / "tollgate_analysis").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                for n in names:
                    with self.subTest(file=path.name, module=n):
                        self.assertFalse(n.split(".")[0] in FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
