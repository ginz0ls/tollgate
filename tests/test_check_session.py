import json
import unittest
from datetime import timedelta

from tests.hookkit import SESSION, T0, Lab, sample
from tollgate_core import phases, sessions, subagents


def start_payload(lab, session, cwd=None, source="startup"):
    return sample("SessionStart-none", session_id=session, cwd=str(cwd or lab.wt), source=source)


def context_of(r):
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout else ""


class SessionStartTest(unittest.TestCase):
    def test_binds_new_session_in_worktree(self):
        lab = Lab()
        try:
            r = lab.hook(start_payload(lab, "s-nuova"))
            self.assertEqual(r.exit, 0)
            self.assertIn("s-nuova", json.loads(phases.get_work(lab.conn, lab.work)["sessions"]))
            self.assertTrue((lab.ts.dir / "bound" / "s-nuova").is_file())
            ctx = context_of(r)
            self.assertIn("#7", ctx)
            self.assertIn("execution", ctx)
            self.assertLessEqual(len(ctx.splitlines()), 10)
            self.assertLessEqual(len(ctx), 1500)
        finally:
            lab.close()

    def test_main_checkout_does_not_bind(self):
        lab = Lab(bind=False)
        try:
            lab.hook(start_payload(lab, "s-fuori", cwd=lab.main))
            self.assertNotIn("s-fuori", json.loads(phases.get_work(lab.conn,
                                                                   lab.work)["sessions"]))
        finally:
            lab.close()

    def test_interrupts_only_dead_sessions(self):
        lab = Lab()
        try:
            sessions.touch(lab.conn, "morta", now=T0 - timedelta(hours=2))
            sessions.touch(lab.conn, "viva", now=lab.now)
            for aid, sess in (("a-morto", "morta"), ("a-vivo", "viva")):
                subagents.start(lab.conn, agent_id=aid, type_="tollgate:implementer",
                                session=sess, work=lab.work, task=None, base_sha=lab.base,
                                fingerprint="f", now=T0)
            lab.hook(start_payload(lab, SESSION, source="resume"))
            self.assertEqual(subagents.get(lab.conn, "a-morto")["state"], "interrupted")
            self.assertEqual(subagents.get(lab.conn, "a-vivo")["state"], "running")
        finally:
            lab.close()

    def test_checkpoint_is_injected(self):
        lab = Lab()
        try:
            cp = lab.wt / "docs/superpowers/reviews/7/checkpoint.md"
            cp.parent.mkdir(parents=True)
            cp.write_text("Prossimo passo: task 3\n")
            r = lab.hook(start_payload(lab, SESSION, source="clear"))
            self.assertIn("Prossimo passo: task 3", context_of(r))
        finally:
            lab.close()

    def test_long_checkpoint_keeps_its_last_lines(self):
        lab = Lab()
        try:
            cp = lab.wt / "docs/superpowers/reviews/7/checkpoint.md"
            cp.parent.mkdir(parents=True)
            cp.write_text("\n".join(f"riga {i}" for i in range(1, 40))
                          + "\nProssimo passo: task 3 ULTIMO\n")
            r = lab.hook(start_payload(lab, SESSION, source="clear"))
            ctx = context_of(r)
            self.assertIn("Prossimo passo: task 3 ULTIMO", ctx)
            self.assertLessEqual(len(ctx.splitlines()), 10)
            self.assertLessEqual(len(ctx), 1500)
        finally:
            lab.close()

    def test_orphan_tg_branch_points_to_adopt(self):
        lab = Lab(work=False)
        try:
            r = lab.hook(start_payload(lab, "s1"))
            self.assertIn("/tollgate:adopt #7", context_of(r))
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
