import unittest
from pathlib import Path

from tollgate_analysis import protected


class ProtectedTest(unittest.TestCase):
    def test_repo_files(self):
        roots = [Path("/stato"), Path("/home/u/.claude/plugins")]
        for rel in ["tollgate.toml", ".github/workflows/tollgate-gate.yml",
                    ".github/tollgate/cli/x.py", ".tollgate/waivers/7.toml",
                    "docs/superpowers/reviews/7/r.md", ".claude/settings.json",
                    ".claude/settings.local.json"]:
            with self.subTest(rel=rel):
                self.assertTrue(protected.is_protected(rel, Path("/r") / rel, abs_roots=roots))
        self.assertFalse(protected.is_protected("src/a.py", Path("/r/src/a.py"), abs_roots=roots))
        self.assertFalse(protected.is_protected("docs/superpowers/plans/p.md",
                                                Path("/r/docs/superpowers/plans/p.md"),
                                                abs_roots=roots))

    def test_absolute_roots(self):
        roots = [Path("/stato"), Path("/r/.git/hooks")]
        self.assertTrue(protected.is_protected(None, Path("/stato/tollgate.db"), abs_roots=roots))
        self.assertTrue(protected.is_protected(None, Path("/r/.git/hooks/pre-commit"),
                                               abs_roots=roots))
        self.assertFalse(protected.is_protected(None, Path("/altro/x"), abs_roots=roots))

    def test_tollgate_file(self):
        self.assertTrue(protected.is_tollgate_file("tollgate.toml"))
        self.assertFalse(protected.is_tollgate_file(".tollgate/waivers/7.toml"))


if __name__ == "__main__":
    unittest.main()
