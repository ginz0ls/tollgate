import types
import unittest
from unittest import mock

from tests.hookkit import DEFAULT_FILES, DEFAULT_TOML, Lab
import json

from tollgate_analysis import worksize
from tollgate_core import phases, scope, sizes, tasks
from tollgate_hooks import apply
from tollgate_hooks.model import record

SECTIONS = ["Fatti verificati", "Decisioni", "Interfacce", "Must-have", "Scope",
            "Punti di arresto", "Rischi"]
NO_IGNORE = {k: v for k, v in DEFAULT_FILES.items() if k != ".gitignore"}


def plan_text(must_have="M1. Somma — test: tests.test_app::test_somma",
              files=("- Modify: `src/app.py`", "- Test: `tests/test_app.py`")):
    out = []
    for s in SECTIONS:
        out += [f"## {s}", must_have if s == "Must-have" else "x", ""]
    out += ["### Task 1: Somma", *files, "", "### Task 2: Doc", "- Create: `docs/uso.md`"]
    return "\n".join(out) + "\n"


def big_plan(tasks=5, slices=0):
    """Un piano con `tasks` task e, se serve, una sezione «Fette previste» con `slices` voci."""
    text = plan_text().rstrip("\n") + "\n"
    for n in range(3, tasks + 1):
        text += f"\n### Task {n}: Extra {n}\n- Create: `docs/extra{n}.md`\n"
    if slices:
        text += "\n## Fette previste\n" + "".join(f"{i}. Fetta {i}\n" for i in range(1, slices + 1))
    return text


class LevelTest(unittest.TestCase):
    def test_l0_grows_to_l1_and_plan(self):
        lab = Lab(level="L0", phase="execution")
        try:
            for i in range(3):
                (lab.wt / f"src/f{i}.py").write_text("x = 1\n")
            r = lab.post_edit(lab.wt / "src/f2.py")
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["level"], w["phase"]), ("L1", "plan"))
            self.assertIn("L1", r.stdout)
        finally:
            lab.close()

    def test_sensitive_path_goes_l2(self):
        lab = Lab()
        try:
            (lab.wt / "src/auth").mkdir()
            (lab.wt / "src/auth/x.py").write_text("x = 1\n")
            lab.post_edit(lab.wt / "src/auth/x.py", agent_id="a1")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L2")
        finally:
            lab.close()

    def test_l0_with_sensitive_path_goes_l2_in_plan(self):
        lab = Lab(level="L0", phase="execution")
        try:
            (lab.wt / "src/auth").mkdir()
            (lab.wt / "src/auth/x.py").write_text("x = 1\n")
            r = lab.post_edit(lab.wt / "src/auth/x.py")
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["level"], w["phase"]), ("L2", "plan"))
            ev = json.loads(lab.conn.execute(
                "SELECT data FROM events WHERE type = 'size_decided' "
                "ORDER BY seq DESC").fetchone()[0])
            self.assertEqual(ev["cause"], "level")
            line = f"taglia: {worksize.LABELS[ev['applied']]} — {ev['reason']}"
            self.assertIn(line, json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])
        finally:
            lab.close()

    def test_failed_edit_event_recomputes_level(self):
        lab = Lab(level="L0", phase="execution")
        try:
            (lab.wt / "src/big.txt").write_text("x" * 5000)
            lab.post_edit(lab.wt / "src/big.txt", hook_event_name="PostToolUseFailure")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L1")
        finally:
            lab.close()

    def test_untracked_file_counts_for_size(self):
        lab = Lab(level="L0", phase="execution")
        try:
            (lab.wt / "src/big.txt").write_text("x" * 5000)  # una riga, oltre l0_max_bytes
            lab.post_edit(lab.wt / "src/big.txt")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L1")
        finally:
            lab.close()

    def test_tracked_diff_counts_for_size(self):
        lab = Lab(level="L0", phase="execution")
        try:
            (lab.wt / "src/app.py").write_text("x" * 5000 + "\n")
            lab.post_edit(lab.wt / "src/app.py")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L1")
        finally:
            lab.close()

    def test_output_dirs_do_not_raise_level(self):
        lab = Lab(level="L0", phase="execution", files=NO_IGNORE)
        try:
            (lab.wt / "reports").mkdir()
            (lab.wt / "reports/junit.xml").write_text("<x/>\n" * 500)
            (lab.wt / "coverage").mkdir()
            (lab.wt / "coverage/lcov.info").write_text("l\n" * 500)
            (lab.wt / ".tollgate-run").mkdir()
            (lab.wt / ".tollgate-run/out.log").write_text("o\n" * 500)
            (lab.wt / "src/app.py").write_text("def somma(a, b):\n    return b + a\n")
            lab.post_edit(lab.wt / "src/app.py")
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["level"], w["phase"]), ("L0", "execution"))
            # controllo: lo stesso volume fuori da output_dirs alza il livello
            (lab.wt / "out").mkdir()
            (lab.wt / "out/junit.xml").write_text("<x/>\n" * 500)
            lab.post_edit(lab.wt / "out/junit.xml")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L1")
        finally:
            lab.close()

    def test_edit_outside_worktree_does_nothing(self):
        lab = Lab(level="L0", phase="execution")
        try:
            for i in range(3):
                (lab.wt / f"src/f{i}.py").write_text("x = 1\n")
            (lab.tmp / "fuori.txt").write_text("x\n")
            lab.post_edit(lab.tmp / "fuori.txt")
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L0")
        finally:
            lab.close()


class PlanCheckHookTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(phase="plan")
        self.plan = self.lab.wt / "docs/superpowers/plans/2026-10-09-somma.md"
        self.plan.parent.mkdir(parents=True)

    def tearDown(self):
        self.lab.close()

    def test_complete_plan_registers_scope(self):
        self.plan.write_text(plan_text())
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 0, r.stderr)
        w = phases.get_work(self.lab.conn, self.lab.work)
        self.assertEqual((w["phase"], w["plan_path"]),
                         ("execution", "docs/superpowers/plans/2026-10-09-somma.md"))
        self.assertEqual(scope.paths(self.lab.conn, self.lab.work),
                         {"src/app.py", "tests/test_app.py", "docs/uso.md"})
        self.assertEqual(tasks.get_task(self.lab.conn, self.lab.work, 2)["state"], "pending")

    def test_incomplete_plan_vetoed_and_not_registered(self):
        self.plan.write_text(plan_text().replace("## Rischi", "## Altro"))
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 2)
        self.assertIn("## Rischi", r.stderr)
        self.assertEqual(scope.paths(self.lab.conn, self.lab.work), set())
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "plan")

    def test_pattern_and_must_have_without_test(self):
        for text in (plan_text(files=("- Modify: `src/*.py`",)),
                     plan_text(must_have="M1. Somma senza test")):
            with self.subTest(text=text[-60:]):
                self.plan.write_text(text)
                self.assertEqual(self.lab.post_edit(self.plan).exit, 2)

    def test_plan_component_off(self):
        lab = Lab(phase="plan", toml=DEFAULT_TOML
                  + "[components]\nplan_check = false\n")
        try:
            plan = lab.wt / "docs/superpowers/plans/p.md"
            plan.parent.mkdir(parents=True)
            plan.write_text("niente\n")
            self.assertEqual(lab.post_edit(plan).exit, 0)
            self.assertEqual(phases.get_work(lab.conn, lab.work)["phase"], "plan")
        finally:
            lab.close()

    def test_l2_plan_only_sets_path(self):
        lab = Lab(level="L2", phase="plan")
        try:
            plan = lab.wt / "docs/superpowers/plans/p.md"
            plan.parent.mkdir(parents=True)
            plan.write_text(plan_text())
            r = lab.post_edit(plan)
            self.assertEqual(r.exit, 0, r.stderr)
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["phase"], w["plan_path"], w["plan_sha"]),
                             ("plan", "docs/superpowers/plans/p.md", None))
            self.assertEqual(scope.paths(lab.conn, lab.work), set())
            self.assertIn("/tollgate:spec-audit", r.stdout)
            self.assertIn("/tollgate:approve plan", r.stdout)
            self.assertNotIn("plan-adversary", r.stdout)
        finally:
            lab.close()

    def test_level_failure_does_not_block_plan_registration(self):
        from tollgate_core import git as core_git
        self.plan.write_text(plan_text())
        with mock.patch("tollgate_checks.post_edit.level_records",
                        side_effect=core_git.GitError("boom")):
            r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(phases.get_work(self.lab.conn, self.lab.work)["phase"], "execution")
        self.assertIn("livello", r.stdout)

    def test_second_plan_is_ignored(self):
        self.plan.write_text(plan_text())
        self.lab.post_edit(self.plan)
        other = self.lab.wt / "docs/superpowers/plans/altro.md"
        other.write_text("niente\n")
        self.assertEqual(self.lab.post_edit(other).exit, 0)


class PlanSizeTest(unittest.TestCase):
    """La taglia alla registrazione del piano dagli hook (C1, decisione 2)."""

    def setUp(self):
        self.lab = Lab(phase="plan")
        self.plan = self.lab.wt / "docs/superpowers/plans/2026-10-09-somma.md"
        self.plan.parent.mkdir(parents=True)

    def tearDown(self):
        self.lab.close()

    def work(self):
        return phases.get_work(self.lab.conn, self.lab.work)

    def size_events(self):
        return [json.loads(r[0]) for r in self.lab.conn.execute(
            "SELECT data FROM events WHERE type = 'size_decided' ORDER BY seq")]

    def reopen_plan(self):
        scope.reset_plan(self.lab.conn, self.lab.work, now=self.lab.now)
        phases.set_phase(self.lab.conn, self.lab.ts.state, self.lab.work, "plan", "reopen_plan",
                         now=self.lab.now)

    def test_plan_registration_decides_size(self):
        self.plan.write_text(big_plan(tasks=5))
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(self.work()["size"], "medium")
        (ev,) = self.size_events()
        self.assertEqual((ev["cause"], ev["signals"]["tasks"]), ("plan", 5))
        line = next(x for x in r.stdout.splitlines() if "taglia:" in x)
        self.assertIn("taglia: medio — piano con 5 task", line)

    def test_injected_line_equals_decided_line(self):
        self.plan.write_text(big_plan(tasks=5))
        r = self.lab.post_edit(self.plan)
        (ev,) = self.size_events()
        expected = worksize.preview(worksize.Signals(**ev["signals"]), None, None,
                                    cause="plan").line
        self.assertIn(expected, r.stdout)

    def test_l1_plan_with_three_slices_stays_medium(self):
        self.plan.write_text(big_plan(tasks=2, slices=3))
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(self.work()["size"], "medium")
        (ev,) = self.size_events()
        self.assertEqual((ev["proposed"], ev["applied"]), ("large", "medium"))
        self.assertIn("/tollgate:approve spec", r.stdout)

    def test_plan_after_reopen_does_not_shrink(self):
        self.plan.write_text(big_plan(tasks=5))
        self.lab.post_edit(self.plan)
        self.assertEqual(self.work()["size"], "medium")
        self.reopen_plan()
        self.plan.write_text(plan_text(files=("- Modify: `src/app.py`",)).split("### Task 2")[0])
        r = self.lab.post_edit(self.plan)
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(self.work()["phase"], "execution")
        self.assertEqual(self.work()["size"], "medium")
        self.assertEqual(self.size_events()[-1]["proposed"], "small")

    def test_reopen_plan_on_pre_c1_work(self):
        self.plan.write_text(big_plan(tasks=2))
        self.lab.post_edit(self.plan)
        self.lab.conn.execute("UPDATE work_items SET size = NULL, size_by = NULL")
        self.lab.conn.execute("DELETE FROM events WHERE type = 'size_decided'")
        self.reopen_plan()
        self.assertIsNone(self.work()["size"])
        self.assertEqual(self.size_events(), [])
        self.plan.write_text(big_plan(tasks=5))
        self.lab.post_edit(self.plan)
        self.assertEqual(self.work()["size"], "medium")
        self.assertEqual(len(self.size_events()), 1)


class LevelSizeTest(unittest.TestCase):
    def test_level_rise_raises_size(self):
        lab = Lab(phase="execution")
        try:
            sizes.decide(lab.conn, lab.work, worksize.Signals("L1", 1, 0, 1),
                         cause="start", now=lab.now)
            self.assertEqual(phases.get_work(lab.conn, lab.work)["size"], "small")
            (lab.wt / "src/auth").mkdir()
            (lab.wt / "src/auth/x.py").write_text("x = 1\n")
            lab.post_edit(lab.wt / "src/auth/x.py", agent_id="a1")
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["level"], w["size"]), ("L2", "medium"))
            ev = json.loads(lab.conn.execute(
                "SELECT data FROM events WHERE type = 'size_decided' "
                "ORDER BY seq DESC").fetchone()[0])
            self.assertEqual(ev["cause"], "level")
        finally:
            lab.close()

    def test_level_rise_says_the_new_size(self):
        """F3: la riga iniettata con il livello nuovo è quella dell'evento `size_decided`."""
        lab = Lab(phase="execution")
        try:
            sizes.decide(lab.conn, lab.work, worksize.Signals("L1", 1, 0, 1),
                         cause="start", now=lab.now)
            (lab.wt / "src/auth").mkdir()
            (lab.wt / "src/auth/x.py").write_text("x = 1\n")
            r = lab.post_edit(lab.wt / "src/auth/x.py", agent_id="a1")
            ev = json.loads(lab.conn.execute(
                "SELECT data FROM events WHERE type = 'size_decided' "
                "ORDER BY seq DESC").fetchone()[0])
            self.assertEqual((ev["cause"], ev["applied"]), ("level", "medium"))
            line = f"taglia: {worksize.LABELS[ev['applied']]} — {ev['reason']}"
            self.assertIn("il lavoro sale a L2", r.stdout)
            self.assertIn(line, json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])
        finally:
            lab.close()

    def test_level_cap_lowering_does_not_decide_size(self):
        lab = Lab(level="L2", phase="plan")
        try:
            worksize_signals = worksize.Signals("L2", 0, 0, 1)
            sizes.decide(lab.conn, lab.work, worksize_signals, cause="start", now=lab.now)
            phases.set_level_cap(lab.conn, lab.work, "L1", "motivo", [], now=lab.now)
            w = phases.get_work(lab.conn, lab.work)
            self.assertEqual((w["level"], w["size"]), ("L1", "medium"))
            self.assertEqual(lab.conn.execute(
                "SELECT count(*) FROM events WHERE type = 'size_decided'").fetchone()[0], 1)
        finally:
            lab.close()

    def test_level_op_with_same_or_lower_level_does_not_decide_size(self):
        """Riga 9: l'operazione `level` decide la taglia solo quando il livello sale."""
        lab = Lab(level="L2", phase="plan")
        try:
            ctx = types.SimpleNamespace(event=types.SimpleNamespace(session="s1"), now=lab.now)
            apply.apply(lab.conn, None, ctx, record("level", work=lab.work, level="L2"))
            with self.assertRaises(phases.TransitionError):
                apply.apply(lab.conn, None, ctx, record("level", work=lab.work, level="L1"))
            self.assertEqual(phases.get_work(lab.conn, lab.work)["level"], "L2")
            self.assertEqual(lab.conn.execute(
                "SELECT count(*) FROM events WHERE type = 'size_decided'").fetchone()[0], 0)
        finally:
            lab.close()

    def test_no_size_event_without_level_rise(self):
        lab = Lab(phase="execution")
        try:
            (lab.wt / "src/app.py").write_text("def somma(a, b):\n    return b + a\n")
            lab.post_edit(lab.wt / "src/app.py")
            self.assertEqual(lab.conn.execute(
                "SELECT count(*) FROM events WHERE type = 'size_decided'").fetchone()[0], 0)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
