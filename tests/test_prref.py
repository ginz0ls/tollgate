import unittest

from tollgate_analysis import prref


class PrrefTest(unittest.TestCase):
    def test_issue_from_branch(self):
        self.assertEqual(prref.issue_from_branch("tg/7-fix-login"), 7)
        self.assertEqual(prref.issue_from_branch("tg/120-a"), 120)
        for ref in ("tg/x", "tg/7", "tg/-7-x", "feature/tg/7-x", "xtg/7-x", "", "tollgate-config/a"):
            with self.subTest(ref=ref):
                self.assertIsNone(prref.issue_from_branch(ref))

    def test_closes_issue_variants(self):
        for body, want in (("Closes #3", 3), ("fixes #3", 3), ("Resolves #3", 3),
                           ("CLOSED #4", 4), ("Fix #5", 5), ("resolved #6", 6),
                           ("Closes: #7", 7), ("Descrizione\n\nCloses #3\n", 3),
                           ("Closes #3, #4", 3)):
            with self.subTest(body=body):
                self.assertEqual(prref.closes_issue(body), want)

    def test_first_line_wins(self):
        self.assertEqual(prref.closes_issue("Closes #3\nFixes #4"), 3)
        self.assertEqual(prref.closes_issue("testo\nFixes #4\nCloses #3"), 4)

    def test_without_keyword_is_none(self):
        for body in ("#3", "vedi #3", "Closes 3", "Closes #", "", "disclosures #3",
                     "Closes https://example.org/#3"):
            with self.subTest(body=body):
                self.assertIsNone(prref.closes_issue(body))

    def test_branch_kinds(self):
        self.assertTrue(prref.is_tg_branch("tg/7-x"))
        self.assertFalse(prref.is_tg_branch("tg/x"))
        self.assertFalse(prref.is_tg_branch("dependabot/npm/x"))
        self.assertTrue(prref.is_config_branch("tollgate-config/waiver-ci"))
        self.assertFalse(prref.is_config_branch("tollgate-config"))
        self.assertFalse(prref.is_config_branch("tg/7-x"))

    def test_closes_in_quote_or_html_comment_ignored(self):
        """Una parola chiave citata o dentro un commento HTML non chiude nulla (il corpo è testo
        della PR, non una dichiarazione di tollgate): vale la prima riga che la ha davvero."""
        for body in ("> Closes #3", "  > Closes #3", ">Fixes #3", "<!-- Closes #3 -->",
                     "x <!-- Closes #3 --> y", "<!--\nCloses #3\n-->", "<!-- Closes #3",
                     "> citazione\n> Closes #3\n"):
            with self.subTest(body=body):
                self.assertIsNone(prref.closes_issue(body))
        self.assertEqual(prref.closes_issue("> Closes #3\nCloses #4"), 4)
        self.assertEqual(prref.closes_issue("<!-- Closes #3 -->\nFixes #5"), 5)
        self.assertEqual(prref.closes_issue("<!--\nnota\n-->\nCloses #6"), 6)
        self.assertEqual(prref.closes_issue("<!-- a --> Closes #7"), 7)


if __name__ == "__main__":
    unittest.main()
