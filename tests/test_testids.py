import unittest

from tollgate_analysis import scan, testids

JS = """
import { describe, it, expect } from 'vitest'
// it('commentato', () => {})
describe('format', () => {
  it('handles UTC', () => { expect(1).toBe(1) })
  describe("nested", () => {
    test(`deep`, () => {})
  })
  it.skip('saltato', () => {})
})
it('top', () => {})
"""

PY = '''
import pytest, unittest

def test_a():
    assert 1

@pytest.mark.skip
def test_skipped():
    pass

class TestGroup:
    def test_b(self):
        assert "assert dentro una stringa"

class Other(unittest.TestCase):
    def test_c(self):
        self.assertEqual(1, 1)
'''


class TestIdsTest(unittest.TestCase):
    def test_js_vitest_and_jest_forms(self):
        active, skipped = testids.test_ids(JS, "src/date.test.ts", js_form="vitest")
        self.assertEqual(set(active.values()), {
            "src/date.test.ts::format > handles UTC", "src/date.test.ts::format > nested > deep",
            "src/date.test.ts::top"})
        self.assertEqual(skipped, {"format > saltato"})
        active, _ = testids.test_ids(JS, "src/date.test.ts", js_form="jest")
        self.assertIn("src/date.test.ts::format handles UTC", active.values())

    def test_python_pytest_form(self):
        active, skipped = testids.test_ids(PY, "tests/test_x.py", js_form="vitest")
        self.assertEqual(set(active.values()), {"tests.test_x::test_a",
                                                "tests.test_x.TestGroup::test_b",
                                                "tests.test_x.Other::test_c"})
        self.assertEqual(skipped, {"test_skipped"})
        self.assertIn("TestGroup::test_b", active)

    def test_python_syntax_error(self):
        self.assertIsNone(testids.test_ids("def test_a(:\n", "tests/test_x.py", js_form="vitest"))

    def test_go(self):
        active, _ = testids.test_ids("func TestSum(t *testing.T) {}\n", "pkg/sum_test.go",
                                     js_form="vitest")
        self.assertEqual(set(active.values()), {"pkg::TestSum"})

    def test_code_without_comments_and_strings(self):
        self.assertNotIn("commentato", scan.js_code("// it('commentato')\nx = 'testo'"))
        self.assertNotIn("dentro", scan.py_code("x = 'assert dentro'  # assert commento\n"))
        self.assertIsNone(scan.py_code("x = '\n"))


class ScanRobustnessTest(unittest.TestCase):
    def test_regex_literal_is_not_a_string(self):
        self.assertEqual(scan.js_code("x = /'/g; y"), "x = S ; y")

    def test_division_is_not_a_regex(self):
        self.assertEqual(scan.js_code("a = b / c / d"), "a = b / c / d")

    def test_template_nested_quotes_do_not_shift_state(self):
        out = scan.js_code("x = `a ${ `it's ${ 'q' }` }`; y")
        self.assertEqual(out.split()[-2:], [";", "y"])
        self.assertNotIn("it", out.split())

    def test_fstring_expression_not_counted(self):
        self.assertNotIn("assert_x", scan.py_code('x = f"{assert_x}"\n').split())


if __name__ == "__main__":
    unittest.main()
