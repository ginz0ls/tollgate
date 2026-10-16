import json
import unittest
from datetime import timedelta

from tests.flowkit import SESSION, FlowLab
from tests.hookkit import DEFAULT_TOML
from tests.test_check_acts import expand
from tollgate_core import acts, clock, config, phases, sessions, subagents, tasks
from tollgate_flow import actapply


class ApplyCase(unittest.TestCase):
    def make(self, **kw):
        kw.setdefault("issue", 7)
        fl = FlowLab(**kw)
        self.addCleanup(fl.close)
        self.fl = fl
        return fl

    def act(self, name, args, session=SESSION):
        """Registra l'atto con l'hook di UserPromptExpansion e ne dà l'identificativo."""
        r = expand(self.fl.lab, name, args, session=session)
        self.assertEqual(r.exit, 0, r.stderr)
        return self.fl.conn.execute("SELECT act_id FROM acts ORDER BY n DESC").fetchone()[0]

    def apply(self, act_id=None, *, session=SESSION, delta=0):
        now = self.fl.now + timedelta(seconds=delta)
        sessions.note_cli_call(self.fl.ts.state, session, str(self.fl.wt), ["act"], now=now)
        return actapply.apply_act(self.fl.ts.state, self.fl.wt, act_id, now=now)

    def work(self):
        return phases.get_work(self.fl.conn, self.fl.work)

    def state_of(self, act_id):
        return self.fl.conn.execute("SELECT state FROM acts WHERE act_id = ?",
                                    (act_id,)).fetchone()[0]

    def block_task(self):
        fl = self.fl
        tasks.add_task(fl.conn, fl.work, 1, source="piano", now=fl.now)
        tasks.task_event(fl.conn, fl.work, 1, "start", now=fl.now)
        tasks.task_event(fl.conn, fl.work, 1, "report_blocked", now=fl.now)

    def open_block(self, reason="r"):
        return phases.open_block(self.fl.conn, self.fl.ts.state, self.fl.work, "needs_you",
                                 reason, now=self.fl.now)


class ResolveTest(ApplyCase):
    def test_resolve_closes_block_and_unblocks_tasks(self):
        fl = self.make()
        self.block_task()
        b = self.open_block("serve una scelta")
        self.assertEqual(self.work()["phase"], "blocked")
        a = self.act("tollgate:resolve", f"{b} procedi con la A")
        msg = self.apply()
        self.assertEqual(self.work()["phase"], "execution")
        row = fl.conn.execute("SELECT closed, resolution FROM blocks WHERE id = ?",
                              (b,)).fetchone()
        self.assertIsNotNone(row["closed"])
        self.assertEqual(row["resolution"], "procedi con la A")
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["state"], "pending")
        self.assertEqual(self.state_of(a), "consumed")
        self.assertIn(str(b), msg)

    def test_tasks_stay_blocked_while_another_block_is_open(self):
        fl = self.make()
        self.block_task()
        b1 = self.open_block("uno")
        self.open_block("due")
        self.act("tollgate:resolve", f"{b1} ok")
        self.apply()
        self.assertEqual(self.work()["phase"], "blocked")
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["state"], "blocked")

    def test_resolve_refuses_unknown_or_closed_block(self):
        self.make()
        a1 = self.act("tollgate:resolve", "999 nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "blocco"):
            self.apply()
        self.assertEqual(self.state_of(a1), "consumed")
        b = self.open_block()
        self.act("tollgate:resolve", f"{b} nota")
        self.apply()
        a3 = self.act("tollgate:resolve", f"{b} ancora")
        with self.assertRaisesRegex(actapply.ActApplyError, "blocco"):
            self.apply(a3)

    def test_resolve_refuses_non_ascii_digits(self):
        fl = self.make()
        self.open_block()
        a = self.act("tollgate:resolve", "² nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "non è un blocco aperto"):
            self.apply()
        self.assertEqual(self.state_of(a), "consumed")
        self.assertEqual(self.work()["phase"], "blocked")

    def test_resolve_refuses_block_of_other_work(self):
        fl = self.make()
        other = phases.create_work(fl.conn, repo_key="github.com/o/altro", issue=9, level="L1",
                                   now=fl.now)
        phases.set_phase(fl.conn, fl.ts.state, other, "execution", "advance", now=fl.now)
        b = phases.open_block(fl.conn, fl.ts.state, other, "needs_you", "r", now=fl.now)
        self.act("tollgate:resolve", f"{b} nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "blocco"):
            self.apply()
        self.assertEqual(phases.get_work(fl.conn, other)["phase"], "blocked")

    def test_resolve_writer_interrupts(self):
        fl = self.make()
        tasks.add_task(fl.conn, fl.work, 1, source="piano", now=fl.now)
        tasks.task_event(fl.conn, fl.work, 1, "start", now=fl.now)
        for aid, typ in (("ag-impl", "tollgate:implementer"),
                         ("ag-rev", "probe:reviewer-frontend"), ("ag-exp", "Explore")):
            subagents.start(fl.conn, agent_id=aid, type_=typ, session=SESSION, work=fl.work,
                            task=1 if aid == "ag-impl" else None, base_sha=None,
                            fingerprint=None, now=fl.now)
        self.act("tollgate:resolve", "writer")
        self.apply()
        self.assertEqual(subagents.get(fl.conn, "ag-impl")["state"], "interrupted")
        self.assertEqual(subagents.get(fl.conn, "ag-rev")["state"], "running")
        self.assertEqual(subagents.get(fl.conn, "ag-exp")["state"], "running")
        self.assertEqual(tasks.get_task(fl.conn, fl.work, 1)["state"], "pending")


class ApproveLevelTest(ApplyCase):
    def test_approve_level_cap_holds_until_new_sensitive_path(self):
        fl = self.make(level="L2", phase="execution")
        old = fl.wt / "src" / "auth" / "old.py"
        old.parent.mkdir(parents=True)
        old.write_text("x = 1\n")
        fl.post_edit(old)
        self.assertEqual(self.work()["level"], "L2")
        a = self.act("tollgate:approve", "level L1 solo un rinomino")
        self.apply()
        w = self.work()
        self.assertEqual((w["level"], w["level_cap"], w["level_cap_reason"]),
                         ("L1", "L1", "solo un rinomino"))
        self.assertEqual(json.loads(w["level_cap_paths"]), ["src/auth/old.py"])
        self.assertEqual(self.state_of(a), "consumed")
        other = fl.wt / "src" / "other.py"
        other.write_text("y = 2\n")
        fl.post_edit(other)
        self.assertEqual(self.work()["level"], "L1")
        new = fl.wt / "src" / "auth" / "x.py"
        new.write_text("z = 3\n")
        fl.post_edit(new)
        self.assertEqual(self.work()["level"], "L2")

    def test_approve_level_refused_outside_target_sequence(self):
        self.make(level="L2", phase="spec_audit")
        a = self.act("tollgate:approve", "level L1 motivo")
        with self.assertRaisesRegex(actapply.ActApplyError, "spec_audit"):
            self.apply()
        self.assertEqual(self.work()["level"], "L2")
        self.assertEqual(self.state_of(a), "consumed")

    def test_cap_paths_exclude_output_dirs(self):
        fl = self.make(level="L2", phase="execution")
        out = fl.wt / "reports" / "auth"
        out.mkdir(parents=True)
        (out / "r.xml").write_text("<x/>\n")
        (fl.wt / "src" / "auth").mkdir(parents=True)
        (fl.wt / "src" / "auth" / "a.py").write_text("a = 1\n")
        self.act("tollgate:approve", "level L1 motivo")
        self.apply()
        self.assertEqual(json.loads(self.work()["level_cap_paths"]), ["src/auth/a.py"])

    def test_cap_paths_include_old_path_of_renames(self):
        fl = self.make(level="L2", phase="execution", files={"src/auth/old.py": "a = 1\n"})
        fl.git("mv", "src/auth/old.py", "src/moved.py", repo=fl.wt)
        self.act("tollgate:approve", "level L1 motivo")
        self.apply()
        self.assertEqual(json.loads(self.work()["level_cap_paths"]), ["src/auth/old.py"])

    def test_approve_level_needs_valid_level_and_reason(self):
        self.make(level="L2", phase="execution")
        self.act("tollgate:approve", "level L9 motivo")
        with self.assertRaisesRegex(actapply.ActApplyError, "livello"):
            self.apply()
        self.act("tollgate:approve", "level L1")
        with self.assertRaisesRegex(actapply.ActApplyError, "motivo"):
            self.apply()
        self.assertEqual(self.work()["level"], "L2")


class RefusalTest(ApplyCase):
    def test_act_of_other_session_or_expired_refused(self):
        self.make()
        b = self.open_block()
        other = self.act("tollgate:resolve", f"{b} nota", session="altra")
        with self.assertRaisesRegex(actapply.ActApplyError, "atto"):
            self.apply(other)
        with self.assertRaisesRegex(actapply.ActApplyError, "nessun atto"):
            self.apply()
        mine = self.act("tollgate:resolve", f"{b} nota")
        with self.assertRaisesRegex(actapply.ActApplyError, "atto"):
            self.apply(mine, delta=3600)
        self.assertEqual(self.work()["phase"], "blocked")

    def test_act_consumed_once(self):
        self.make()
        b = self.open_block()
        a = self.act("tollgate:resolve", f"{b} nota")
        self.apply(a)
        with self.assertRaisesRegex(actapply.ActApplyError, "atto"):
            self.apply(a)

    def test_unknown_act_type_refused(self):
        self.make()
        a = self.act("tollgate:approve", "waiver w-7-1")
        with self.assertRaisesRegex(actapply.ActApplyError, "non si applica con act apply"):
            self.apply(a)
        self.assertEqual(self.state_of(a), "pending")

    def test_without_id_takes_last_applicable_pending(self):
        self.make()
        b = self.open_block()
        a1 = self.act("tollgate:resolve", f"{b} nota")
        a2 = self.act("tollgate:approve", "waiver w-7-1")
        self.apply()
        self.assertEqual((self.state_of(a1), self.state_of(a2)), ("consumed", "pending"))

    def test_session_not_recognised(self):
        fl = self.make()
        with self.assertRaisesRegex(actapply.ActApplyError, "sessione non riconosciuta"):
            actapply.apply_act(fl.ts.state, fl.wt, None, now=fl.now)

    def test_no_work_for_directory(self):
        fl = self.make()
        sessions.note_cli_call(fl.ts.state, SESSION, str(fl.main), ["act"], now=fl.now)
        with self.assertRaisesRegex(actapply.ActApplyError, "nessun lavoro"):
            actapply.apply_act(fl.ts.state, fl.main, None, now=fl.now)


class CliTest(ApplyCase):
    def test_cli_refuses_with_message_and_exit_1(self):
        fl = self.make()
        self.open_block()
        r = fl.cli("act", "apply", cwd=fl.wt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("tollgate:", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_cli_applies_act_recorded_now(self):
        fl = self.make()
        b = phases.open_block(fl.conn, fl.ts.state, fl.work, "needs_you", "r", now=clock.now())
        acts.record_act(fl.conn, type_="resolve", target=str(b), args=[str(b), "fatto"],
                        typed_text="/tollgate:resolve", session=SESSION, work=fl.work,
                        now=clock.now(), ttl_minutes=10)
        r = fl.cli("act", "apply", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.work()["phase"], "execution")


class ConfigTest(unittest.TestCase):
    def test_is_readonly(self):
        cfg = config.load_config_text(DEFAULT_TOML)
        for t in ("tollgate:task-reviewer", "Explore", "probe:reviewer-frontend",
                  "probe:final-x"):
            self.assertTrue(config.is_readonly(cfg, t), t)
        for t in ("tollgate:implementer", "general-purpose", None, ""):
            self.assertFalse(config.is_readonly(cfg, t), t)

    def test_output_excludes(self):
        out = config.output_excludes(config.load_config_text(DEFAULT_TOML))
        self.assertEqual(out, ["reports/", "coverage/", ".tollgate-run/"])
