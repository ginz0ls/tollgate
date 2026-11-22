"""La fotografia per il gestionale (C1, Task 8, decisione 8)."""
import io
import json
import socket
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import cli, db, effects, events, phases, snapshot, tasks

T0 = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 11, 21, 11, 0, tzinfo=timezone.utc)
HOST = "macchina-prova"
KEYS = {"repo_key", "issue", "level", "level_cap", "size", "size_by", "slices", "phase",
        "phase_before_block", "branch", "pr_number", "tasks", "turn", "waiting_user", "waiting",
        "cost", "created", "updated", "last_event_at"}


def all_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from all_keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from all_keys(v)


class SnapshotBase(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.addCleanup(self.ts.cleanup)
        self.conn = db.open_db(self.ts.state)
        self.addCleanup(self.conn.close)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=7, level="L1",
                                    now=T0, branch="tg/7-prova")

    def ev(self, type_, data=None, *, session="A", work=True):
        return events.record_event(self.conn, type_, data or {}, now=T1, session=session,
                                   work=self.w if work else None)

    def cost(self, agent, task, tokens):
        self.ev("cost", {"agent": agent, "type": "implementer", "task": task, "tokens": tokens,
                         "by_model": {}, "usd": None, "source": "transcript"})

    def ask(self, tool_use_id, session):
        return self.ev("stop_asked", {"tool_use_id": tool_use_id,
                                      "questions": [{"header": "h", "question": "d?",
                                                     "options": []}]}, session=session)

    def build(self):
        return snapshot.build(self.conn, now=T1, host=HOST)

    def work_item(self):
        (item,) = self.build()["works"]
        return item


class SnapshotShapeTest(SnapshotBase):
    def test_snapshot_shape(self):
        tasks.add_task(self.conn, self.w, 1, source="plan", now=T0)
        tasks.add_task(self.conn, self.w, 2, source="plan", now=T0)
        self.cost("a1", 1, 100)
        self.cost("a2", 2, 40)
        self.cost("a1", 1, 250)
        snap = self.build()
        self.assertEqual((snap["v"], snap["host"]), (snapshot.SNAPSHOT_VERSION, HOST))
        self.assertEqual(snapshot.SNAPSHOT_VERSION, 1)
        self.assertEqual(set(snap), {"v", "at", "host", "works"})
        (item,) = snap["works"]
        self.assertEqual(set(item), KEYS)
        self.assertEqual(item["cost"]["tokens"], 290)
        self.assertEqual(item["cost"]["by_task"], {1: 250, 2: 40})
        self.assertEqual(item["tasks"], {"pending": 2})
        self.assertEqual((item["repo_key"], item["issue"], item["phase"], item["branch"]),
                         ("github.com/o/r", 7, "plan", "tg/7-prova"))
        self.assertEqual((item["turn"], item["waiting"], item["waiting_user"]),
                         ("agent", [], 0))
        self.assertEqual(item["last_event_at"], events.export_events(self.conn, 0)[-1]["at"])
        json.dumps(snap, sort_keys=True)

    def test_cost_last_per_agent(self):
        self.cost("a1", 1, 100)
        self.cost("a1", 1, 250)
        self.cost("a2", 1, 50)
        self.assertEqual(self.work_item()["cost"]["tokens"], 300)

    def test_cost_without_task_counts_only_in_total(self):
        self.cost("a1", None, 70)
        self.assertEqual(self.work_item()["cost"], {"tokens": 70, "by_task": {}})

    def test_no_cost(self):
        self.assertEqual(self.work_item()["cost"], {"tokens": 0, "by_task": {}})

    def test_snapshot_skips_closed(self):
        phases.create_work(self.conn, repo_key="github.com/o/r", issue=8, level="L1", now=T0)
        self.conn.execute("UPDATE work_items SET phase = 'closed' WHERE id = ?", (self.w,))
        self.conn.commit()
        self.assertEqual([i["issue"] for i in self.build()["works"]], [8])

    def test_snapshot_pre_c1_work(self):
        self.conn.execute("UPDATE work_items SET size = NULL, size_by = NULL, slices = NULL "
                          "WHERE id = ?", (self.w,))
        self.conn.commit()
        item = self.work_item()
        self.assertEqual((item["size"], item["size_by"], item["slices"]), (None, None, None))

    def test_snapshot_has_no_free_text(self):
        phases.open_block(self.conn, self.ts.state, self.w, "needs_you", "segreto-di-prova",
                          now=T1)
        self.ev("ruling", {"what": "segreto-di-prova", "why": "x", "cost": "y"})
        self.ask("t1", "A")
        snap = self.build()
        text = json.dumps(snap, ensure_ascii=False)
        self.assertNotIn("segreto-di-prova", text)
        found = set(all_keys(snap)) & {"reason", "what", "question", "worktree"}
        self.assertTrue(not found, f"chiavi di testo libero nella fotografia: {sorted(found)}")


class WaitingItemsTest(SnapshotBase):
    def items(self):
        return snapshot.waiting_items(self.conn, self.w)

    def test_waiting_items(self):
        self.ask("tA", "A")
        self.ev("stop_answered", {"tool_use_id": "tA", "answers": {}, "source": "tool_response"},
                session="A")
        block = phases.open_block(self.conn, self.ts.state, self.w, "needs_you", "r", now=T1)
        effects.request(self.conn, key="k" * 64, command="git push", work=self.w, sha=None,
                        now=T1)
        self.conn.execute("INSERT INTO intents (work, action, idempotency_key, data, state, at) "
                          "VALUES (?, 'pr', 'pr:1', '{}', 'requested', 'x')", (self.w,))
        self.conn.commit()
        self.ev("subagent_stop", {"id": "x"}, session="B")
        self.ask("tB", "B")
        self.assertEqual(self.items(), [{"kind": "block", "id": block},
                                        {"kind": "effect", "id": effects.effect_id("k" * 64)},
                                        {"kind": "question", "id": "tB"}])
        item = self.work_item()
        self.assertEqual((item["turn"], item["waiting_user"]), ("decision", 3))
        self.assertEqual(item["waiting"], self.items())

    def test_closed_block_and_executed_effect_do_not_wait(self):
        phases.open_block(self.conn, self.ts.state, self.w, "needs_you", "r", now=T1)
        self.conn.execute("UPDATE blocks SET closed = 'x'")
        effects.request(self.conn, key="k" * 64, command="c", work=self.w, sha=None, now=T1)
        effects.mark_executed(self.conn, key="k" * 64, act_id="a", now=T1)
        self.assertEqual(self.items(), [])

    def test_answers_are_scanned_once_per_snapshot(self):
        """Riga 27: le `stop_answered` si rileggono una volta sola, non una per lavoro."""
        phases.create_work(self.conn, repo_key="github.com/o/r", issue=8, level="L1", now=T0,
                           branch="tg/8-prova")
        self.ask("t1", "A")
        scans = []
        self.conn.set_trace_callback(
            lambda sql: scans.append(sql) if "type = 'stop_answered'" in sql else None)
        try:
            items = self.build()["works"]
        finally:
            self.conn.set_trace_callback(None)
        self.assertEqual(len(items), 2)
        self.assertEqual(len(scans), 1, scans)

    def test_unanswered_question_expires(self):
        cases = {
            "act": (lambda: self.ev("act", {"type": "approve"}, session="U"), []),
            "session_start of another session": (
                lambda: self.ev("session_start", {"source": "startup"}, session="Z"), []),
            "second question": (lambda: self.ask("t2", "A"), [{"kind": "question", "id": "t2"}]),
            "only subagent_stop and cost": (
                lambda: (self.ev("subagent_stop", {"id": "x"}, session="B"),
                         self.cost("a1", 1, 5)), [{"kind": "question", "id": "t1"}]),
        }
        for name, (after, expected) in cases.items():
            with self.subTest(name):
                self.conn.execute("DELETE FROM events")
                self.conn.commit()
                self.ask("t1", "A")
                after()
                self.assertEqual(self.items(), expected)

    def test_act_of_another_work_does_not_close(self):
        other = phases.create_work(self.conn, repo_key="github.com/o/r", issue=9, level="L1",
                                   now=T0)
        self.ask("t1", "A")
        events.record_event(self.conn, "act", {}, now=T1, session="U", work=other)
        self.assertEqual(self.items(), [{"kind": "question", "id": "t1"}])

    def test_question_without_tool_use_id_never_waits(self):
        self.ev("stop_asked", {"tool_use_id": None, "questions": []})
        self.assertEqual(self.items(), [])

    def test_pr_open_counts_user(self):
        self.conn.execute("UPDATE work_items SET phase = 'pr_open' WHERE id = ?", (self.w,))
        self.conn.commit()
        item = self.work_item()
        self.assertEqual((item["turn"], item["waiting_user"], item["waiting"]), ("user", 1, []))


class CliSnapshotTest(unittest.TestCase):
    def test_cli_snapshot_without_db(self):
        ts = TempState()
        self.addCleanup(ts.cleanup)
        import os
        from unittest import mock
        out = io.StringIO()
        with mock.patch.dict(os.environ, {"TOLLGATE_STATE": str(ts.dir)}), \
                mock.patch.object(socket, "gethostname", return_value=HOST), \
                redirect_stdout(out):
            code = cli.main(["snapshot"])
        self.assertEqual(code, 0)
        snap = json.loads(out.getvalue())
        self.assertEqual((snap["v"], snap["host"], snap["works"]), (1, HOST, []))
        self.assertIn("at", snap)
        self.assertFalse(ts.state.db_path.exists())


if __name__ == "__main__":
    unittest.main()
