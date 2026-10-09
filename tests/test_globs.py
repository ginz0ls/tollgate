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

    def test_is_pattern_only_star_and_question(self):
        self.assertFalse(globs.is_pattern("app/[id]/page.tsx"))
        self.assertFalse(globs.is_pattern("src/[ab].py"))
        self.assertTrue(globs.is_pattern("a?b"))
        self.assertTrue(globs.is_pattern("src/*.py"))

    def test_brackets_count_as_glob_for_specificity(self):
        self.assertEqual(globs.literal_segments("web/[id]/**"), 1)

    def test_closing_bracket_first_is_literal(self):
        self.assertTrue(globs.match("src/[]a]", "src/]"))
        self.assertTrue(globs.match("src/[]a]", "src/a"))
        self.assertFalse(globs.match("src/[]a]", "src/b"))
        self.assertTrue(globs.match("src/[!]x]", "src/y"))
        self.assertFalse(globs.match("src/[!]x]", "src/]"))
        self.assertFalse(globs.match("src/[!]x]", "src/x"))

    def test_escaped_closing_bracket_and_literal_brackets(self):
        self.assertTrue(globs.match(r"src/[\]]", "src/]"))
        self.assertTrue(globs.match("src/[[]", "src/["))
        self.assertTrue(globs.match("src/[&~|^]", "src/&"))
        self.assertTrue(globs.match("src/[&~|^]", "src/^"))
        self.assertTrue(globs.match("src/[&~|^]", "src/|"))

    def test_posix_classes(self):
        self.assertTrue(globs.match("src/[[:alpha:]]x", "src/ax"))
        self.assertFalse(globs.match("src/[[:alpha:]]x", "src/1x"))
        self.assertTrue(globs.match("src/[[:digit:]]", "src/7"))

    def test_reversed_range_matches_nothing_without_error(self):
        self.assertFalse(globs.match("src/[z-a]", "src/m"))
        self.assertFalse(globs.match("src/[z-a]", "src/z"))
        self.assertTrue(globs.match("src/[a-]", "src/-"))

    def test_invalid_patterns_never_match_and_do_not_raise(self):
        for bad, path in [("src/[ab", "src/a"), ("src/[[:foo:]]", "src/a"),
                          ("src/a\\", "src/a\\"), ("src/[", "src/["), ("src/[!", "src/x")]:
            with self.subTest(pattern=bad):
                self.assertFalse(globs.match(bad, path))
        self.assertFalse(globs.match_any(["src/[ab"], "src/a"))

    def test_invalid_patterns_emit_no_warning(self):
        import warnings
        globs.compile.cache_clear()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertTrue(globs.match("src/[[:alpha:]]", "src/a"))
            globs.match("src/[z-a]", "src/a")
            globs.match("src/[[:foo:]]", "src/a")
        self.assertEqual([w for w in caught if issubclass(w.category, FutureWarning)], [])

    def test_slash_never_matched_by_classes(self):
        self.assertFalse(globs.match("a[/]b", "a/b"))
        self.assertFalse(globs.match("a[!x]b", "a/b"))
        self.assertTrue(globs.match("a[!x]b", "a.b"))

    def test_backslash_escapes_next_char(self):
        self.assertTrue(globs.match(r"\*x", "*x"))
        self.assertFalse(globs.match(r"\*x", "ax"))
        self.assertTrue(globs.match(r"\!a", "!a"))
        self.assertFalse(globs.match(r"\!a", "a"))

    def test_double_star_inside_segment_is_single_star(self):
        self.assertTrue(globs.match("a**b", "axxb"))
        self.assertFalse(globs.match("a**b", "a/xb"))

    def test_leading_bang_is_negation_not_a_match(self):
        self.assertFalse(globs.match("!x", "x"))
        self.assertFalse(globs.match("!x", "!x"))

    def test_negation_last_match_wins(self):
        self.assertTrue(globs.match_any(["*.py", "!legacy.py"], "a.py"))
        self.assertFalse(globs.match_any(["*.py", "!legacy.py"], "legacy.py"))
        self.assertTrue(globs.match_any(["!legacy.py", "*.py"], "legacy.py"))
        self.assertFalse(globs.match_any(["!a.py"], "a.py"))

    def test_escape_makes_literal_path(self):
        for p in ["*x", "[a]", "!a", "a?b", "back\\slash", "dir/[id]/page.tsx", "x.py",
                  "**/y"]:
            with self.subTest(path=p):
                self.assertTrue(globs.match(globs.escape(p), p))
        self.assertFalse(globs.match(globs.escape("*x"), "ax"))
        self.assertFalse(globs.match(globs.escape("[a]"), "a"))
        self.assertFalse(globs.match(globs.escape("x.py"), "a/x.py"))
        self.assertTrue(globs.match(globs.escape("x.py"), "x.py"))


if __name__ == "__main__":
    unittest.main()
