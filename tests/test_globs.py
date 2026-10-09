import unittest

from tollgate_analysis import globs


class GlobsTest(unittest.TestCase):
    def test_gitignore_dialect(self):
        cases = [
            ("**/__tests__/**", "src/__tests__/a.test.js", True),
            ("**/test_*.py", "test_x.py", True),
            ("**/test_*.py", "a/b/test_x.py", True),
            ("web/**", "web/a/b.ts", True),
            ("web/**", "x/web/a.ts", False),
            ("*.md", "docs/a.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/x.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/plans/x.md", True),
            ("docs/superpowers/**/*.md", "docs/superpowers/plans/x.py", False),
            ("/tollgate.toml", "tollgate.toml", True),
            ("/tollgate.toml", "sub/tollgate.toml", False),
            (".github/workflows/tollgate-*.yml", ".github/workflows/tollgate-verdict.yml", True),
            (".github/workflows/tollgate-*.yml", ".github/workflows/ci.yml", False),
            ("reports/", "reports/junit.xml", True),
            ("**", "qualunque/cosa.txt", True),
            ("**/*.test.*", "src/a.test.ts", True),
            ("scripts/check*", "scripts/check-all.sh", True),
            ("src/[ab].py", "src/a.py", True),
            ("src/[!ab].py", "src/a.py", False),
        ]
        for pattern, path, expected in cases:
            with self.subTest(pattern=pattern, path=path):
                self.assertEqual(globs.match(pattern, path), expected)

    def test_helpers(self):
        self.assertTrue(globs.is_pattern("src/*.py"))
        self.assertFalse(globs.is_pattern("src/a.py"))
        self.assertEqual(globs.literal_segments("web/admin/**"), 2)
        self.assertEqual(globs.literal_segments("**/*.ts"), 0)


if __name__ == "__main__":
    unittest.main()
