import json
import unittest

from tests.helpers import TempState
from tollgate_core import clock, db, intents, phases

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


class IntentsTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def row(self, key):
        return self.conn.execute("SELECT * FROM intents WHERE idempotency_key = ?",
                                 (key,)).fetchone()

    def test_request_is_idempotent(self):
        a = intents.request(self.conn, work=self.w, action="pr", key="pr:1:abc",
                            data={"sha": "abc"}, now=T0)
        intents.complete(self.conn, "pr:1:abc", outcome="fatto", now=T0)
        b = intents.request(self.conn, work=self.w, action="pr", key="pr:1:abc",
                            data={"sha": "abc", "n": 2}, now=T0)
        self.assertEqual(a, b)
        row = self.row("pr:1:abc")
        self.assertEqual(row["state"], "requested")
        self.assertEqual(json.loads(row["data"]), {"sha": "abc", "n": 2})
        self.assertEqual(self.conn.execute("SELECT count(*) FROM intents").fetchone()[0], 1)

    def test_unknown_action_refused(self):
        with self.assertRaises(ValueError):
            intents.request(self.conn, work=self.w, action="boh", key="k", data={}, now=T0)

    def test_complete_marks_executed(self):
        intents.request(self.conn, work=self.w, action="sync", key="sync:1:a-3", data={}, now=T0)
        intents.complete(self.conn, "sync:1:a-3", outcome="ok", now=T0)
        row = self.row("sync:1:a-3")
        self.assertEqual((row["state"], row["outcome"]), ("executed", "ok"))

    def test_complete_unknown_key_refused(self):
        with self.assertRaises(ValueError):
            intents.complete(self.conn, "nope", outcome="x", now=T0)

    def test_force_taken_once(self):
        key = intents.authorize_force(self.conn, self.w, reason="rebase", now=T0)
        self.assertEqual(key, f"force:{self.w}:1")
        self.assertEqual(self.row(key)["state"], "authorized")
        self.assertEqual(intents.take_force(self.conn, self.w, now=T0), key)
        self.assertEqual(self.row(key)["state"], "used")
        self.assertIsNone(intents.take_force(self.conn, self.w, now=T0))

    def test_force_keys_are_distinct_and_latest_is_taken_first(self):
        k1 = intents.authorize_force(self.conn, self.w, reason="a", now=T0)
        k2 = intents.authorize_force(self.conn, self.w, reason="b", now=T0)
        self.assertNotEqual(k1, k2)
        self.assertEqual(intents.take_force(self.conn, self.w, now=T0), k2)
        self.assertEqual(intents.take_force(self.conn, self.w, now=T0), k1)

    def test_pending_lists_requested(self):
        intents.request(self.conn, work=self.w, action="pr", key="pr:1:a", data={}, now=T0)
        intents.request(self.conn, work=self.w, action="pr", key="pr:1:b", data={}, now=T0)
        intents.request(self.conn, work=self.w, action="sync", key="sync:1:x", data={}, now=T0)
        intents.complete(self.conn, "pr:1:a", outcome="ok", now=T0)
        self.assertEqual([r["idempotency_key"]
                          for r in intents.pending(self.conn, self.w, "pr")], ["pr:1:b"])
        self.assertEqual(len(intents.pending(self.conn, self.w, "sync")), 1)
        self.assertEqual(intents.pending(self.conn, self.w, "force_push"), [])

    def test_sync_conflict_reason_prefix(self):
        self.assertEqual(intents.SYNC_CONFLICT_REASON, "sync: conflitto nel rebase")
