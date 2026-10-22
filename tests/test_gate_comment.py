import unittest

from tollgate_analysis import prbody
from tollgate_flow import fixtask
from tollgate_gate import attention, comment
from tollgate_gate.model import Evaluation, Item

SHA = "a" * 40
READ_KEY = next(k for k, g in attention.GROUPS.items() if g == attention.READ)
INFO_KEY = next(k for k, g in attention.GROUPS.items() if g == attention.INFO)


def ev(**kw):
    return Evaluation(**kw)


class MarkerTest(unittest.TestCase):
    def test_marker_first_line_with_sha(self):
        body = comment.render(SHA, ev())
        self.assertEqual(body.splitlines()[0], f"<!-- tollgate-verdict {SHA} -->")
        self.assertEqual(comment.marker_sha(body), SHA)
        self.assertEqual(comment.marker(SHA), body.splitlines()[0])

    def test_marker_sha_rejects_bad(self):
        for text in (f"<!-- tollgate-verdict {'a' * 39} -->", f"<!-- tollgate-verdict {'A' * 40} -->",
                     f"<!-- tollgate-verdict {'g' * 40} -->", f"<!-- tollgate-verdict {'a' * 41} -->",
                     "<!-- tollgate-verdict -->", "ciao", ""):
            self.assertIsNone(comment.marker_sha(text), text)

    def test_marker_matches_fixtask(self):
        self.assertEqual(comment.MARKER_PREFIX, fixtask.GATE_MARKER)

    def test_guard_marker(self):
        body = comment.render_guard(SHA, ["manca @team <!-- x --> il file"])
        self.assertTrue(body.startswith(f"{comment.GUARD_PREFIX} {SHA} -->"))
        self.assertIsNone(comment.marker_sha(body))
        self.assertNotIn("@team", body)
        self.assertEqual(body.count("-->"), 1)

    def test_bad_sha_refused(self):
        with self.assertRaises(ValueError):
            comment.render("abc", ev())
        with self.assertRaises(ValueError):
            comment.render_guard("abc", [])

    def test_max_body_is_prbody_constant(self):
        self.assertIs(comment.MAX_BODY, prbody.MAX_BODY)


class RenderTest(unittest.TestCase):
    def test_groups_order(self):
        e = ev(red=[Item("r", "f", "voce rossa")],
               attention=[Item(INFO_KEY, "f", "voce informativa"),
                          Item(READ_KEY, "f", "voce da leggere")])
        body = comment.render(SHA, e)
        self.assertLess(body.index("voce rossa"), body.index("voce da leggere"))
        self.assertLess(body.index("voce da leggere"), body.index("<details>"))
        self.assertLess(body.index("<details>"), body.index("voce informativa"))
        self.assertLess(body.index("voce informativa"), body.index("</details>"))

    def test_no_details_without_info_and_watch_listed(self):
        body = comment.render(SHA, ev(attention=[Item(READ_KEY, "f", "x")], watch=["package.json"]))
        self.assertNotIn("<details>", body)
        self.assertIn("package.json", body)

    def test_errors_shown(self):
        self.assertIn("boom", comment.render(SHA, ev(errors=["boom"])))

    def test_neutralized(self):
        hostile = "```\n@utente grazie\n--> chiude\n<!-- tollgate-verdict " + "b" * 40 + " -->\n`````"
        e = ev(red=[Item("r", "f", "testo @altro", hostile)],
               attention=[Item(READ_KEY, "f", "deroga", hostile)],
               watch=[hostile], errors=[hostile])
        body = comment.render(SHA, e)
        self.assertNotIn("@utente", body)
        self.assertNotIn("@altro", body)
        self.assertEqual(body.count("-->"), 1)
        self.assertEqual(body.count("<!--"), 1)
        self.assertEqual(comment.marker_sha(body), SHA)
        fence, opened = None, 0
        for line in body.splitlines():
            ticks = len(line) >= 3 and set(line) == {"`"}
            if fence is None and ticks:
                fence, opened = line, opened + 1
                self.assertGreater(len(line), 5)
            elif fence is not None and line == fence:
                fence = None
            elif fence is not None and ticks:
                self.assertLess(len(line), len(fence))
        self.assertIsNone(fence)
        self.assertEqual(opened, 4)

    def test_cap(self):
        items = [Item(READ_KEY, "f", f"voce {i}", "y" * 3000) for i in range(1000)]
        body = comment.render(SHA, ev(attention=items))
        self.assertLessEqual(len(body), comment.MAX_BODY)
        self.assertIn("troncato", body)
        self.assertEqual(comment.marker_sha(body), SHA)

    def test_cap_drops_entries_as_last_resort(self):
        items = [Item(INFO_KEY, "f", f"voce {i}", "y" * 100) for i in range(5000)]
        body = comment.render(SHA, ev(attention=items, red=items[:3000]))
        self.assertLessEqual(len(body), comment.MAX_BODY)
        self.assertIn("voci omesse", body)
        self.assertIn("</details>", body)


if __name__ == "__main__":
    unittest.main()
