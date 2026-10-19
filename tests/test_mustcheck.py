import unittest

from tollgate_analysis import mustcheck
from tollgate_analysis.plan import MustHave

A, B = "tests.test_x::test_a", "tests.test_x::test_b"


class MustCheckTest(unittest.TestCase):
    def test_present_and_green(self):
        r = mustcheck.check([MustHave("M1", "a", [A]), MustHave("M2", "b", [A, B])], {A, B}, set())
        self.assertEqual((r.ok, r.missing, r.failed, r.manual), (True, [], [], []))

    def test_absent_is_false(self):
        r = mustcheck.check([MustHave("M1", "a", [A]), MustHave("M2", "b", [B])], {A}, set())
        self.assertEqual((r.ok, r.missing, r.failed), (False, [f"M2: {B}"], []))

    def test_failed_is_false(self):
        r = mustcheck.check([MustHave("M1", "a", [A])], {A}, {A})
        self.assertEqual((r.ok, r.missing, r.failed), (False, [], [f"M1: {A}"]))

    def test_failed_counts_even_if_not_in_run(self):
        r = mustcheck.check([MustHave("M1", "a", [A])], set(), {A})
        self.assertEqual((r.ok, r.missing, r.failed), (False, [], [f"M1: {A}"]))

    def test_manual_is_listed_and_not_false(self):
        r = mustcheck.check([MustHave("M1", "a", [A]), MustHave("M3", "colore", ["manuale"])],
                            {A}, set())
        self.assertEqual((r.ok, r.manual), (True, ["M3"]))

    def test_manual_with_a_missing_test_is_false(self):
        r = mustcheck.check([MustHave("M3", "x", ["manuale", B])], set(), set())
        self.assertEqual((r.ok, r.manual, r.missing), (False, ["M3"], [f"M3: {B}"]))

    def test_must_have_without_tests_checks_nothing(self):
        self.assertTrue(mustcheck.check([MustHave("M1", "a", [])], set(), set()).ok)


if __name__ == "__main__":
    unittest.main()
