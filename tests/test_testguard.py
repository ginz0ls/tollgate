import unittest
from unittest import mock

from tollgate_analysis.testguard import (DEFAULT_TEST_GLOBS, Change, GuardConfig, check)

CFG = GuardConfig(test_globs=DEFAULT_TEST_GLOBS, fixture_globs=["**/fixtures/**/*.json"],
                  ci_globs=[".github/workflows/**"],
                  verification_globs=["**/vitest.config.*", "**/conftest.py"],
                  verification_watch=["**/package.json", "**/pyproject.toml"])

JS_BASE = "describe('a', () => {\n  it('x', () => { expect(1).toBe(1) })\n  it('y', () => {})\n})\n"
PY_BASE = "def test_a():\n    assert 1\n\ndef test_b():\n    assert 2\n"


def kinds(changes):
    return sorted(v.kind for v in check(changes, CFG).violations)


class TestGuardTest(unittest.TestCase):
    def test_deleted_test_file(self):
        self.assertEqual(kinds([Change("D", "src/__tests__/a.test.js", None, JS_BASE, None)]),
                         ["test_deleted"])

    def test_xdescribe_added(self):
        head = JS_BASE.replace("describe(", "xdescribe(")
        self.assertIn("skip_added", kinds([Change("M", "src/a.test.ts", None, JS_BASE, head)]))

    def test_pytest_skip_added(self):
        head = PY_BASE.replace("    assert 2", "    pytest.skip('no')\n    assert 2")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["skip_added"])

    def test_pytest_mark_skip_added(self):
        head = "import pytest\n" + PY_BASE.replace("def test_b", "@pytest.mark.skip\ndef test_b")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["skip_added", "test_id_missing"])

    def test_assertion_replaced_by_comment(self):
        head = PY_BASE.replace("    assert 2", "    # assert 2\n    pass")
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                         ["asserts_decreased"])

    def test_missing_id(self):
        head = "def test_a():\n    assert 1\n    assert 2\n"
        v = check([Change("M", "tests/test_x.py", None, PY_BASE, head)], CFG).violations
        self.assertEqual([(x.kind, x.ids) for x in v],
                         [("test_id_missing", ("tests.test_x::test_b",))])

    def test_process_exit_is_fine(self):
        head = JS_BASE.replace("expect(1).toBe(1)", "expect(1).toBe(1); process.exit(0)")
        self.assertEqual(kinds([Change("M", "src/a.test.ts", None, JS_BASE, head)]), [])

    def test_rename_with_same_tests(self):
        self.assertEqual(kinds([Change("R", "tests/test_y.py", "tests/test_x.py",
                                       PY_BASE, PY_BASE)]), [])

    def test_ci_fixture_verification_threshold(self):
        changes = [
            Change("M", ".github/workflows/ci.yml", None, "a", "b"),
            Change("M", "tests/fixtures/data/x.json", None, "{}", "{\"a\": 1}"),
            Change("M", "vitest.config.ts", None, "lines: 90", "lines: 80"),
        ]
        self.assertEqual(kinds(changes), ["ci_changed", "fixture_changed", "threshold_lowered",
                                          "verification_changed"])

    def test_watch_is_info_only(self):
        r = check([Change("M", "package.json", None, "{}", "{\"x\": 1}")], CFG)
        self.assertEqual((r.violations, r.watched), ([], ["package.json"]))

    def test_new_file_with_skip(self):
        head = "def test_a():\n    pytest.skip('x')\n"
        self.assertEqual(kinds([Change("A", "tests/test_new.py", None, None, head)]),
                         ["skip_added"])

    def test_unparsable_head(self):
        self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, "def (:\n")]),
                         ["unparsable"])

    def test_binary_and_latin1_do_not_crash(self):
        # Byte reali non UTF-8 (Latin-1): il testo arriva decodificato in Latin-1, come da file.
        raw = b"x = 'caff\xe8'\n"
        with self.assertRaises(UnicodeDecodeError):
            raw.decode("utf-8")
        latin1 = raw.decode("latin-1")
        r = check([Change("M", "tests/data.bin", None, None, None, binary=True),
                   Change("M", "tests/test_l.py", None, latin1, latin1)],
                  CFG)
        self.assertEqual(r.violations, [])


PREFIX_RE_QUOTE = "const s = 'a'.replace(/\"/g, '')\n"
PREFIX_RE_SLASH = "const r = /[//]/; const q = 'x'\n"
PREFIX_RE_RETURN = "function f(x) { return /\"/.test(x) }\n"
PREFIX_TPL = "const t = `a ${ `it's ${ 'x' }` }`\n"
PREFIX_JSX = "const v = <p>don't</p>\n"


class TestScannerRobustness(unittest.TestCase):
    CASES = [(PREFIX_RE_QUOTE, "src/a.test.ts"), (PREFIX_RE_SLASH, "src/a.test.ts"),
             (PREFIX_RE_RETURN, "src/a.test.ts"), (PREFIX_TPL, "src/a.test.ts"),
             (PREFIX_JSX, "src/a.test.tsx")]

    def _diff(self, prefix, path, edit):
        return kinds([Change("M", path, None, prefix + JS_BASE, prefix + edit(JS_BASE))])

    def test_skip_added_after_tricky_lexing(self):
        for prefix, path in self.CASES:
            with self.subTest(prefix=prefix):
                self.assertIn("skip_added", self._diff(
                    prefix, path, lambda t: t.replace("it('y'", "it.skip('y'")))
                self.assertIn("skip_added", self._diff(
                    prefix, path, lambda t: t.replace("it('y'", "xit('y'")))

    def test_expect_removed_after_tricky_lexing(self):
        for prefix, path in self.CASES:
            with self.subTest(prefix=prefix):
                self.assertIn("asserts_decreased", self._diff(
                    prefix, path, lambda t: t.replace("expect(1).toBe(1)", "1")))

    def test_python_skip_markers(self):
        for line in ("self.skipTest('no')", "raise SkipTest('no')",
                     "raise unittest.SkipTest('no')", "pytest.importorskip('x')"):
            with self.subTest(line=line):
                head = PY_BASE.replace("    assert 1", f"    {line}\n    assert 1")
                self.assertIn("skip_added",
                              kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]))

    def test_skip_still_flagged_when_python_scanner_fails(self):
        head = PY_BASE.replace("    assert 1", "    pytest.skip('no')\n    assert 1")
        with mock.patch("tollgate_analysis.testguard.py_code", return_value=None):
            self.assertEqual(kinds([Change("M", "tests/test_x.py", None, PY_BASE, head)]),
                             ["skip_added", "unparsable"])

    def test_binary_deleted_test(self):
        self.assertEqual(kinds([Change("D", "tests/a.test.ts", None, None, None, binary=True)]),
                         ["test_deleted"])

    def test_threshold_removed_from_package_json(self):
        base = '{"jest": {"coverageThreshold": {"global": {"lines": 90}}}}'
        self.assertEqual(kinds([Change("M", "package.json", None, base, '{"jest": {}}')]),
                         ["threshold_lowered"])

    def test_commented_threshold_counts_as_removed(self):
        self.assertEqual(kinds([Change("M", "packages/web/.nycrc", None, '{"lines": 90}',
                                       '{\n  # "lines": 90\n}\n')]), ["threshold_lowered"])

    def test_nycrc_lowered(self):
        self.assertEqual(kinds([Change("M", ".nycrc", None, '{"lines": 90}', '{"lines": 10}')]),
                         ["threshold_lowered"])

    def test_coveragerc_lowered_after_star_slash_glob(self):
        base = "omit =\n    */tests/*\n    */migrations/*\n[report]\nfail_under = 80\n"
        head = base.replace("fail_under = 80", "fail_under = 10")
        self.assertEqual(kinds([Change("M", ".coveragerc", None, base, head)]),
                         ["threshold_lowered"])

    def test_setup_cfg_lowered_after_star_slash_glob(self):
        base = "[coverage:report]\nomit =\n    */tests/*\nfail_under = 80\n"
        head = base.replace("fail_under = 80", "fail_under = 10")
        self.assertEqual(kinds([Change("M", "setup.cfg", None, base, head)]),
                         ["threshold_lowered"])

    def test_unchanged_coveragerc_with_star_slash_glob_is_clean(self):
        base = "omit =\n    */tests/*\n[report]\nfail_under = 80\n"
        self.assertEqual(kinds([Change("M", ".coveragerc", None, base, base)]), [])

    def test_commented_threshold_in_nycrc_json_counts_as_removed(self):
        self.assertEqual(kinds([Change("M", ".nycrc.json", None, '{"lines": 90}',
                                       '{\n  // "lines": 90\n}\n')]), ["threshold_lowered"])

    def test_coverage_config_deleted(self):
        self.assertEqual(kinds([Change("D", ".coveragerc", None, "fail_under = 90\n", None)]),
                         ["threshold_lowered"])


if __name__ == "__main__":
    unittest.main()
