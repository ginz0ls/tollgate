import unittest

from tollgate_analysis import waivers
from tollgate_analysis.testguard import Violation


def wf(*items):
    return waivers.WaiverFile(issue=7, branch="tg/7-x", waivers=list(items))


def w(n, type_, file=None, pattern=None, tests=()):
    return waivers.Waiver(f"w-7-{n}", type_, file, pattern, list(tests), "scelta", "perché",
                          "costo", "agent")


class WaiversTest(unittest.TestCase):
    def test_roundtrip_with_tricky_text(self):
        f = wf(waivers.Waiver("w-7-1", "scope", "src/a.py", None, [], 'virgolette " e \\',
                              "```\n@utente", "c", "agent"))
        back = waivers.parse(waivers.dumps(f))
        self.assertEqual(back, f)

    def test_parse_rejects_bad(self):
        with self.assertRaises(ValueError):
            waivers.parse('schema_version = 1\nissue = 7\nbranch = "b"\n[[waiver]]\nid = "x"\n'
                          'type = "boh"\nfile = "a"\nchoice = ""\nwhy = ""\ncost = ""\n')

    def test_next_id(self):
        self.assertEqual(waivers.next_id(wf()), "w-7-1")
        self.assertEqual(waivers.next_id(wf(w(1, "scope", "a"), w(4, "scope", "b"))), "w-7-5")

    def test_status_rules(self):
        f = wf(w(1, "scope", "a"), w(2, "scope", "b"), w(3, "scope", "c"),
               w(4, "test", "t", tests=["x"]), w(5, "command", "cfg"),
               w(6, "scope", pattern="src/**"), w(7, "scope", "auth/x"))
        st = waivers.status(f, approved_ids={"w-7-4"}, sensitive=lambda p: p.startswith("auth/"))
        self.assertEqual(st, {"w-7-1": "valid", "w-7-2": "valid", "w-7-3": "pending",
                              "w-7-4": "valid", "w-7-5": "valid", "w-7-6": "pending",
                              "w-7-7": "pending"})

    def test_covers(self):
        v_scope = Violation("out_of_scope", "src/x.py", "", "scope")
        v_ids = Violation("test_id_missing", "t.py", "", "test", ("t::a", "t::b"))
        self.assertTrue(waivers.covers(w(1, "scope", "src/x.py"), v_scope))
        self.assertTrue(waivers.covers(w(1, "scope", pattern="src/**"), v_scope))
        self.assertFalse(waivers.covers(w(1, "test", "src/x.py"), v_scope))
        self.assertFalse(waivers.covers(w(1, "test", "t.py", tests=["t::a"]), v_ids))
        self.assertTrue(waivers.covers(w(1, "test", "t.py", tests=["t::a", "t::b"]), v_ids))
        self.assertEqual(waivers.unresolved([v_scope, v_ids], wf(w(1, "scope", "src/x.py"))),
                         [v_ids])
        self.assertEqual(waivers.unresolved([v_scope], None), [v_scope])


if __name__ == "__main__":
    unittest.main()
