import json
import unittest

from tollgate_analysis import auditrules as ar

CODE, SPEC, PLAN = "ab12cd34", "s" * 40, "p" * 40
COUNTS = {"blocker": 0, "major": 1, "moderate": 3, "minor": 2}


def line(**over):
    data = {"v": 1, "kind": "spec-adversarial", "number": 2, "viewpoint": None,
            "spec_sha": SPEC, "code": CODE, "counts": dict(COUNTS)}
    data.update(over)
    return json.dumps({k: v for k, v in data.items() if v is not ...})


def parse(text, **over):
    args = dict(kind="spec-adversarial", number=2, code=CODE, spec_sha=SPEC, plan_sha=None,
                viewpoint=None)
    args.update(over)
    return ar.parse_round_json(text, **args)


def rows(*items):
    return [(v, o) for v, o in items]


def empties(n_each, viewpoints=ar.VIEWPOINTS):
    return [(v, "empty") for _ in range(n_each) for v in viewpoints]


class OutcomeTest(unittest.TestCase):
    def test_outcome_and_clean(self):
        c = {"blocker": 0, "major": 0, "moderate": 1, "minor": 0}
        self.assertEqual(ar.outcome(c), "findings")
        self.assertTrue(ar.is_clean(c))
        self.assertFalse(ar.is_clean({**c, "major": 1}))
        self.assertFalse(ar.is_clean({**c, "blocker": 1}))
        only_minor = {"blocker": 0, "major": 0, "moderate": 0, "minor": 4}
        self.assertEqual(ar.outcome(only_minor), "empty")
        self.assertTrue(ar.is_clean(only_minor))

    def test_viewpoints_and_labels(self):
        self.assertEqual(len(ar.VIEWPOINTS), 8)
        self.assertEqual(ar.VIEWPOINTS[0], "executor")
        self.assertEqual(set(ar.VIEWPOINT_LABELS), set(ar.VIEWPOINTS))
        self.assertEqual(ar.VIEWPOINT_LABELS["executor"], "chi esegue")
        self.assertEqual(ar.VIEWPOINT_LABELS["integrator"], "chi integra")
        self.assertEqual(ar.SEVERITIES, ("blocker", "major", "moderate", "minor"))


class RoundJsonTest(unittest.TestCase):
    def test_round_json_valid_and_matrix(self):
        r = parse("prosa\n" + line())
        self.assertTrue(r.valid)
        self.assertEqual(r.problems, [])
        self.assertEqual(r.counts, COUNTS)
        for over in ({"code": "zzzzzzzz"}, {"number": 3}, {"kind": "spec-lens"},
                     {"spec_sha": "x" * 40}):
            r = parse(line(), **over)
            self.assertFalse(r.valid, over)
            self.assertEqual(len(r.problems), 1)
            self.assertIsNone(r.counts)
        # viewpoint: giusto per spec-lens, sbagliato altrimenti
        lens = line(kind="spec-lens", viewpoint="user")
        self.assertTrue(parse(lens, kind="spec-lens", viewpoint="user").valid)
        self.assertFalse(parse(lens, kind="spec-lens", viewpoint="executor").valid)
        self.assertFalse(parse(line(viewpoint="user"), viewpoint=None).valid)
        self.assertFalse(parse(line(kind="spec-lens"), kind="spec-lens", viewpoint="user").valid)

    def test_round_json_counts_rules(self):
        for bad in ({"blocker": "0", "major": 0, "moderate": 0, "minor": 0},
                    {"blocker": -1, "major": 0, "moderate": 0, "minor": 0},
                    {"blocker": 0, "major": 0, "moderate": 0},
                    {"blocker": True, "major": 0, "moderate": 0, "minor": 0},
                    {"blocker": 1.5, "major": 0, "moderate": 0, "minor": 0}, [1, 2], "x"):
            r = parse(line(counts=bad))
            self.assertFalse(r.valid, bad)
            self.assertIsNone(r.counts)

    def test_round_json_missing_and_ignored_outcome(self):
        r = parse("solo prosa, nessun JSON")
        self.assertFalse(r.valid)
        self.assertEqual(r.problems, ["manca la riga JSON del giro (18.3)"])
        r = parse(line(outcome="empty"))
        self.assertTrue(r.valid)
        self.assertEqual(ar.outcome(r.counts), "findings")

    def test_round_json_plan_sha_only_for_plan_adversarial(self):
        self.assertTrue(parse(line(), plan_sha=PLAN).valid)
        text = line(kind="plan-adversarial", plan_sha=PLAN)
        self.assertTrue(parse(text, kind="plan-adversarial", plan_sha=PLAN).valid)
        r = parse(text, kind="plan-adversarial", plan_sha="q" * 40)
        self.assertFalse(r.valid)
        r = parse(line(kind="plan-adversarial"), kind="plan-adversarial", plan_sha=PLAN)
        self.assertFalse(r.valid)

    def test_round_json_last_wins_and_problems_hide_values(self):
        first = line(counts={"blocker": 9, "major": 9, "moderate": 9, "minor": 9})
        r = parse(first + "\ntesto\n" + line())
        self.assertEqual(r.counts, COUNTS)
        secret = "SEGRETO-da-non-riportare"
        r = parse(line(code=secret, counts={"blocker": secret}))
        self.assertFalse(r.valid)
        self.assertNotIn(secret, " ".join(r.problems))


class LensStateTest(unittest.TestCase):
    def test_major_resets_viewpoint_counter(self):
        st = ar.lens_state(rows(("executor", "empty"), ("executor", "empty")))
        self.assertEqual(st.streak["executor"], 2)
        st = ar.lens_state(rows(("executor", "empty"), ("executor", "empty"),
                                ("executor", "findings")))
        self.assertEqual(st.streak["executor"], 0)
        self.assertEqual(st.cycles["executor"], ["empty", "empty", "findings"])
        self.assertEqual(st.total, 3)

    def test_closed_needs_two_empty_each(self):
        st = ar.lens_state(empties(2))
        self.assertTrue(st.closed)
        self.assertEqual(st.total, 16)
        self.assertFalse(ar.lens_state(empties(2)[:-1]).closed)
        self.assertFalse(ar.lens_state([]).closed)
        # un ciclo con rilievi dopo la chiusura la riapre
        self.assertFalse(ar.lens_state(empties(2) + [("skeptic", "findings")]).closed)

    def test_superseded_rows_are_ignored(self):
        st = ar.lens_state([("executor", "superseded"), ("executor", "empty")])
        self.assertEqual(st.total, 1)

    def test_next_viewpoint_rotates_and_repeats_findings(self):
        self.assertEqual(ar.next_viewpoint(ar.lens_state([]), None), "executor")
        st = ar.lens_state([("executor", "empty")])
        self.assertEqual(ar.next_viewpoint(st, "executor"), "user")
        # executor con rilievi, gli altri a 2: torna executor
        data = [(v, "empty") for v in ar.VIEWPOINTS[1:] for _ in range(2)]
        data.append(("executor", "findings"))
        st = ar.lens_state(data)
        self.assertFalse(st.closed)
        self.assertEqual(ar.next_viewpoint(st, "executor"), "executor")
        # salta i punti di vista già a 2
        st = ar.lens_state([("executor", "empty")] * 2 + [("user", "empty")])
        self.assertEqual(ar.next_viewpoint(st, "user"), "attacker")
        # ad audit chiuso: il successivo di last, circolare
        st = ar.lens_state(empties(2))
        self.assertEqual(ar.next_viewpoint(st, "integrator"), "executor")
        self.assertEqual(ar.next_viewpoint(st, "executor"), "user")
        self.assertEqual(ar.next_viewpoint(st, None), "executor")


class RenderTest(unittest.TestCase):
    def test_render_lens_status_has_all_viewpoints(self):
        st = ar.lens_state([("executor", "empty"), ("executor", "findings"),
                            ("user", "empty")])
        text = ar.render_lens_status(st, issue=7, cap=30, suspended=False)
        self.assertIn("Punto di vista | Cicli | Vuoti di fila | Ultimo esito", text)
        for v in ar.VIEWPOINTS:
            self.assertIn(v, text)
            self.assertIn(ar.VIEWPOINT_LABELS[v], text)
        self.assertIn("stato: aperto", text)
        self.assertIn("cicli fatti: 3 (tetto 30)", text)
        self.assertIn("#7", text)
        closed = ar.render_lens_status(ar.lens_state(empties(2)), issue=7, cap=30,
                                       suspended=False)
        self.assertIn("stato: chiuso", closed)
        susp = ar.render_lens_status(st, issue=7, cap=30, suspended=True)
        self.assertIn("stato: sospeso", susp)
        self.assertNotIn("stato: aperto", susp)


if __name__ == "__main__":
    unittest.main()
