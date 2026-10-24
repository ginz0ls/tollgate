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

    def test_pending_waiver_still_covers_locally(self):
        # Decisione 9: in locale una deroga dichiarata scioglie la violazione anche se
        # è pending; il blocco su ciò che è in attesa arriva da open-pr (P3).
        f = wf(w(1, "test", pattern="**"))
        self.assertEqual(waivers.status(f, approved_ids=set(), sensitive=lambda p: False),
                         {"w-7-1": "pending"})
        v = Violation("skip_added", "t.py", "", "test")
        self.assertEqual(waivers.unresolved([v], f), [])

    def test_test_deleted_needs_all_ids(self):
        v = Violation("test_deleted", "t.py", "", "test", ("t::a", "t::b"))
        self.assertFalse(waivers.covers(w(1, "test", "t.py", tests=["t::a"]), v))
        self.assertTrue(waivers.covers(w(1, "test", "t.py", tests=["t::a", "t::b"]), v))

    def test_violation_without_ids_needs_same_type_and_path(self):
        v = Violation("skip_added", "t.py", "", "test")
        self.assertTrue(waivers.covers(w(1, "test", "t.py"), v))
        self.assertFalse(waivers.covers(w(1, "test", "other.py"), v))
        self.assertFalse(waivers.covers(w(1, "ci", "t.py"), v))

    def test_parse_rejects_non_list_waiver(self):
        head = 'schema_version = 1\nissue = 7\nbranch = "b"\n'
        with self.assertRaises(ValueError):
            waivers.parse(head + "waiver = 5\n")
        with self.assertRaises(ValueError):
            waivers.parse(head + '[waiver]\nid = "w-7-1"\ntype = "scope"\nfile = "a"\n'
                                 'choice = ""\nwhy = ""\ncost = ""\n')

    def test_parse_rejects_duplicate_ids(self):
        f = wf(w(1, "scope", "a"), w(1, "scope", "b"))
        with self.assertRaises(ValueError):
            waivers.parse(waivers.dumps(f))

    def test_id_with_trailing_newline_rejected(self):
        """`$` accetta un `\\n` finale: l'id `w-7-1\\n` non è un id."""
        head = 'schema_version = 1\nissue = 7\nbranch = "b"\n'
        for wid in ("w-7-1\\n", "w-7-1\\n\\n"):
            with self.subTest(wid=wid):
                with self.assertRaises(ValueError):
                    waivers.parse(head + f'[[waiver]]\nid = "{wid}"\ntype = "scope"\n'
                                  'file = "a"\nchoice = "c"\nwhy = "w"\ncost = "k"\n')
        self.assertEqual(waivers.parse(head + '[[waiver]]\nid = "w-7-1"\ntype = "scope"\n'
                                       'file = "a"\nchoice = "c"\nwhy = "w"\ncost = "k"\n'
                                       ).waivers[0].id, "w-7-1")


if __name__ == "__main__":
    unittest.main()
