import unittest

from tollgate_analysis import naming


class NamingTest(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(naming.slug("Aggiungi l'export CSV!"), "aggiungi-l-export-csv")
        self.assertEqual(naming.slug("Città più veloce 🚀"), "citta-piu-veloce")
        self.assertEqual(naming.slug("$(rm -rf ~)"), "rm-rf")
        self.assertEqual(naming.slug(""), "issue")
        self.assertEqual(naming.slug("🚀🚀"), "issue")
        self.assertEqual(len(naming.slug("a" * 80)), 40)

    def test_slug_never_ends_with_dash_after_cut(self):
        self.assertEqual(naming.slug("a" * 39 + " bbb"), "a" * 39)

    def test_branch_name_adds_suffix_when_taken(self):
        self.assertEqual(naming.branch_name(7, "Demo", set()), "tg/7-demo")
        self.assertEqual(naming.branch_name(7, "Demo", {"tg/7-demo"}), "tg/7-demo-2")
        self.assertEqual(naming.branch_name(7, "Demo", {"tg/7-demo", "tg/7-demo-2"}),
                         "tg/7-demo-3")

    def test_implementer_name(self):
        self.assertEqual(naming.implementer_name(7, 3), "tg-7-t3")
        self.assertEqual(naming.implementer_name(7, 3, 4), "tg-7-t3-r4")
        self.assertEqual(naming.implementer_name(7, 3, 2), "tg-7-t3")


if __name__ == "__main__":
    unittest.main()
