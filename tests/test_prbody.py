import unittest

from tests.test_prblock import facts
from tollgate_analysis import prblock, prbody

BLOCK = prblock.build(facts(issue=7))


def render(**kw):
    args = dict(issue=7, level="L1", dod_lines=["[sì] Ricevuta green sullo SHA"], notes=[],
                waivers=[], warnings=[], block=BLOCK)
    args.update(kw)
    return prbody.render(**args)


class NeutralizeTest(unittest.TestCase):
    def test_fence_longer_than_any_backtick_run(self):
        out = prbody.neutralize("ciao ````` mondo")
        first = out.splitlines()[0]
        self.assertEqual(set(first), {"`"})
        self.assertGreater(len(first), 5)
        self.assertEqual(out.splitlines()[-1], first)

    def test_mentions_and_comment_markers_defused(self):
        out = prbody.neutralize("@utente e @team/x <!-- c --> --> fine")
        self.assertNotIn("@utente", out)
        self.assertIn("@​utente", out)
        self.assertNotIn("<!--", out)
        self.assertNotIn("-->", out)

    def test_truncated(self):
        out = prbody.neutralize("x" * 10_000)
        self.assertIn("… (troncato)", out)
        self.assertLess(len(out), prbody.MAX_TEXT + 100)
        short = prbody.neutralize("y" * 50, max_len=10)
        self.assertIn("… (troncato)", short)
        self.assertNotIn("y" * 11, short)
        self.assertNotIn("troncato", prbody.neutralize("breve"))


class RenderTest(unittest.TestCase):
    def test_closes_line_first(self):
        body = render()
        self.assertEqual(body.splitlines()[0], "Closes #7")
        self.assertTrue(body.rstrip().endswith("-->"))
        self.assertEqual(prblock.parse(body), BLOCK)

    def test_sections_present(self):
        body = render(notes=[{"severity": "minor", "file": "a.py", "line": 3, "rule": "R-1",
                              "text": "nota"}],
                      waivers=["w-7-1 scope src/x.py: valida"], warnings=["revisione spenta"])
        for text in ("L1", "Ricevuta green sullo SHA", "nota", "w-7-1", "revisione spenta"):
            self.assertIn(text, body)

    def test_long_entries_do_not_hide_later_ones_or_sections(self):
        notes = [{"severity": "minor", "file": f"f{i}.py", "line": i, "rule": "R-1",
                  "text": f"nota{i} " + "x" * 3000} for i in (1, 2, 3)]
        body = render(notes=notes, waivers=["w-7-1 scope a.py [valid]", "w-7-2 test b.py [pending]"],
                      warnings=["avviso finale"],
                      dod_lines=["[sì] prima voce", "[no] " + "d" * 3000, "[sì] ultima voce"])
        for i in (1, 2, 3):
            self.assertIn(f"nota{i} ", body)
        self.assertEqual(body.count("… (troncato)"), 4)
        for text in ("prima voce", "ultima voce", "w-7-1", "w-7-2", "avviso finale"):
            self.assertIn(text, body)
        self.assertEqual(prblock.parse(body), BLOCK)

    def test_unverified_section_with_reason_and_neutralized(self):
        body = render(unverified=[{"severity": "major", "file": "a.py", "line": 2, "rule": "R-1",
                                   "text": "ping @utente", "verification_reason": "ciclo superato"}])
        self.assertIn("## Rilievi non verificati", body)
        self.assertIn("[major] a.py:2", body)
        self.assertIn("non verificato: ciclo superato", body)
        self.assertNotIn("@utente", body)
        self.assertNotIn("Rilievi non verificati", render())

    def test_missing_file_or_line_in_note(self):
        body = render(notes=[{"severity": "minor", "file": None, "line": None, "rule": None,
                              "text": "t"}])
        self.assertNotIn("None", body.split("<!-- tollgate")[0])

    def test_hostile_finding_text_neutralized_and_block_roundtrips(self):
        hostile = ("```\n@utente grazie\n--> chiude\n<!-- tollgate {\"issue\": 99} -->\n"
                   "<script>alert(1)</script>\n" + "z" * 10_000)
        body = render(
            notes=[{"severity": "moderate", "file": "a`b.py", "line": 1, "rule": "R-```1",
                    "text": hostile}],
            waivers=[hostile], warnings=[hostile], dod_lines=[hostile])
        self.assertEqual(body.count("<!-- tollgate"), 1)
        self.assertNotIn("@utente", body)
        self.assertEqual(prblock.parse(body), BLOCK)
        self.assertEqual(body.count("-->"), 1)
        self.assertLess(len(body), 4 * (prbody.MAX_TEXT + 600) + 3000)
        # ogni testo ostile sta in un recinto che nessuna sua riga può chiudere
        fence, opened = None, 0
        for line in body.splitlines():
            ticks = len(line) >= 3 and set(line) == {"`"}
            if fence is None and ticks:
                fence, opened = line, opened + 1
            elif fence is not None and line == fence:
                fence = None
            elif fence is not None and ticks:
                self.assertLess(len(line), len(fence))
        self.assertIsNone(fence)
        self.assertEqual(opened, 4)


if __name__ == "__main__":
    unittest.main()
