import unittest

from tollgate_analysis import worksize
from tollgate_analysis.worksize import Signals, areas, preview, propose


class ProposeTest(unittest.TestCase):
    def test_small_by_default(self):
        self.assertEqual(propose(Signals("L1", 3, 1, 1)).size, "small")

    def test_medium_thresholds(self):
        for s in (Signals("L1", 4, 1, 1), Signals("L1", 1, 2, 1), Signals("L2", 0, 0, 1)):
            self.assertEqual(propose(s).size, "medium", s)
        self.assertEqual(propose(Signals("L0", 3, 1, 1)).size, "small")

    def test_large_with_slices(self):
        p = propose(Signals("L1", 1, 1, 3))
        self.assertEqual(p.size, "large")
        self.assertIn("3 fette", p.reason)

    def test_reason_names_the_signals(self):
        reason = propose(Signals("L1", 6, 2, 1)).reason
        self.assertIn("6 task", reason)
        self.assertIn("2 aree", reason)

    def test_constants(self):
        self.assertEqual(worksize.SIZES, ("small", "medium", "large"))
        self.assertEqual(worksize.LABELS["medium"], "medio")
        self.assertEqual((worksize.MEDIUM_MIN_TASKS, worksize.MEDIUM_MIN_AREAS), (4, 2))


class AreasTest(unittest.TestCase):
    def test_areas_counts_verticals_only(self):
        profiles = {"ai": {"kind": "vertical", "paths": ["ai/**"]},
                    "infra": {"kind": "vertical", "paths": ["/vercel.json"]}}
        paths = ["ai/a.py", "ai/b.py", "vercel.json", "README.md"]
        self.assertEqual(areas(paths, profiles), 2)

    def test_no_profiles_no_areas(self):
        self.assertEqual(areas(["a.py"], {}), 0)


class PreviewTest(unittest.TestCase):
    def test_large_needs_the_yes(self):
        s = Signals("L1", 1, 1, 3)
        p = preview(s, "small", "rules", cause="plan")
        self.assertEqual(p.applied, "medium")
        self.assertIn("approve spec", p.line)
        self.assertEqual(preview(s, "small", "rules", cause="approve_spec",
                                 confirmed=True).applied, "large")

    def test_never_goes_down(self):
        self.assertEqual(preview(Signals("L1", 0, 0, 1), "medium", "rules",
                                 cause="plan").applied, "medium")

    def test_user_size_is_kept(self):
        p = preview(Signals("L2", 9, 3, 1), "small", "user", cause="plan")
        self.assertEqual(p.applied, "small")
        for part in ("piccolo", "scelta dall'utente", "medio"):
            self.assertIn(part, p.line)

    def test_user_size_yields_to_the_yes_on_slices(self):
        s = Signals("L1", 1, 1, 3)
        self.assertEqual(preview(s, "small", "user", cause="approve_spec",
                                 confirmed=True).applied, "large")

    def test_large_line_never_says_stays_medium(self):
        for s, cur, by in ((Signals("L2", 5, 1, 3), "large", "rules"),
                           (Signals("L1", 1, 1, 3), "large", "user")):
            p = preview(s, cur, by, cause="plan")
            self.assertEqual(p.applied, "large")
            self.assertNotIn("resta medio", p.line)

    def test_user_small_with_large_proposal(self):
        p = preview(Signals("L1", 1, 1, 3), "small", "user", cause="plan")
        self.assertEqual(p.applied, "small")
        self.assertIn("piccolo", p.line)
        self.assertIn("scelta dall'utente", p.line)
        self.assertNotIn("resta medio", p.line)

    def test_l2_unauthorised_large_uses_normal_form(self):
        p = preview(Signals("L2", 1, 1, 3), "medium", "rules", cause="plan")
        self.assertEqual(p.applied, "medium")
        self.assertTrue(p.line.startswith("taglia: medio"))

    def test_normal_line(self):
        p = preview(Signals("L1", 6, 2, 1), None, None, cause="plan")
        self.assertEqual(p.line, "taglia: medio — piano con 6 task su 2 aree")

    def test_lines_never_use_bare_program_name(self):
        import re
        for s in (Signals("L1", 1, 1, 3), Signals("L2", 6, 2, 1), Signals("L1", 0, 0, 1)):
            for cur, by in ((None, None), ("small", "user"), ("medium", "rules")):
                line = preview(s, cur, by, cause="plan").line
                self.assertIsNone(re.search(r"(?<![:/\w])tollgate [a-z]", line), line)


if __name__ == "__main__":
    unittest.main()
