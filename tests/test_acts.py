import unittest
from datetime import timedelta

from tests.helpers import TempState
from tollgate_core import acts, clock, db, events, phases

T0 = clock.parse("2026-10-08T10:00:00.000000Z")


class ActsTest(unittest.TestCase):
    def setUp(self):
        self.t = TempState()
        self.conn = db.open_db(self.t.state)
        self.w = phases.create_work(self.conn, repo_key="github.com/o/r", issue=1, level="L1",
                                    now=T0)
        self.w2 = phases.create_work(self.conn, repo_key="github.com/o/r", issue=2, level="L1",
                                     now=T0)

    def tearDown(self):
        self.conn.close()
        self.t.cleanup()

    def waiver(self, **kw):
        base = dict(type_="approve", object_="waiver", target="w-1-3",
                    typed_text="/tollgate:approve waiver w-1-3", session="s1", work=self.w,
                    now=T0, ttl_minutes=10)
        base.update(kw)
        return acts.record_act(self.conn, **base)

    def usable(self, **kw):
        base = dict(type_="approve", object_="waiver", target="w-1-3", work=self.w,
                    session="s1", now=T0 + timedelta(minutes=5))
        base.update(kw)
        return acts.find_usable(self.conn, **base)

    def test_record_and_event(self):
        a = self.waiver()
        self.assertEqual(a, "a-1")
        e = [x for x in events.export_events(self.conn, 0) if x["type"] == "act"][0]
        self.assertEqual(e["data"]["act_id"], "a-1")
        self.assertEqual((e["data"]["type"], e["data"]["object"], e["data"]["target"]),
                         ("approve", "waiver", "w-1-3"))
        self.assertEqual(e["data"]["source"], "claude-code")

    def test_binding_and_ttl(self):
        self.waiver()
        self.assertIsNotNone(self.usable())
        self.assertIsNone(self.usable(session="s2"))
        self.assertIsNone(self.usable(work=self.w2))
        self.assertIsNone(self.usable(target="w-1-4"))
        self.assertIsNotNone(self.usable(now=T0 + timedelta(minutes=9, seconds=59)))
        self.assertIsNone(self.usable(now=T0 + timedelta(minutes=10)))

    def test_consume_once(self):
        a = self.waiver()
        acts.consume(self.conn, a, now=T0)
        self.assertIsNone(self.usable())
        with self.assertRaises(acts.ActError):
            acts.consume(self.conn, a, now=T0)

    def test_finish_bound_to_head_not_session_or_time(self):
        acts.record_act(self.conn, type_="finish", typed_text="/tollgate:finish", session="s1",
                        work=self.w, head_sha="abc", now=T0, ttl_minutes=10)
        later = T0 + timedelta(hours=3)
        self.assertIsNotNone(acts.find_usable(self.conn, type_="finish", work=self.w,
                                              session="s9", now=later, head_sha="abc"))
        self.assertIsNone(acts.find_usable(self.conn, type_="finish", work=self.w,
                                           session="s1", now=T0, head_sha="def"))
        self.assertIsNone(acts.find_usable(self.conn, type_="finish", work=self.w2,
                                           session="s1", now=T0, head_sha="abc"))
        self.assertEqual(acts.expire_stale(self.conn, now=later), [])
        self.assertEqual(acts.invalidate_finish(self.conn, self.w, "def", now=later), ["a-1"])
        self.assertIsNone(acts.find_usable(self.conn, type_="finish", work=self.w,
                                           session="s1", now=later, head_sha="abc"))

    def test_expire_stale(self):
        a = self.waiver()
        b = self.waiver(target="w-1-4", now=T0 + timedelta(minutes=8))
        self.assertEqual(acts.expire_stale(self.conn, now=T0 + timedelta(minutes=10)), [a])
        types = [e["type"] for e in events.export_events(self.conn, 0)]
        self.assertIn("act_expired", types)
        self.assertIsNotNone(self.usable(target="w-1-4", now=T0 + timedelta(minutes=10)))
        self.assertNotEqual(a, b)

    def test_without_work(self):
        acts.record_act(self.conn, type_="adopt", target="3", typed_text="/tollgate:adopt #3",
                        session="s1", work=None, now=T0, ttl_minutes=10)
        self.assertIsNotNone(acts.find_usable(self.conn, type_="adopt", target="3", work=None,
                                              session="s1", now=T0))

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.waiver(type_="boh")
        with self.assertRaises(ValueError):
            self.waiver(object_="boh")
        with self.assertRaises(ValueError):
            acts.record_act(self.conn, type_="finish", typed_text="/tollgate:finish",
                            session="s1", work=self.w, now=T0, ttl_minutes=10)

    def test_one_shot(self):
        self.assertTrue(acts.is_one_shot("finish", None))
        self.assertTrue(acts.is_one_shot("approve", "effect"))
        self.assertTrue(acts.is_one_shot("abandon", None))
        self.assertFalse(acts.is_one_shot("approve", "waiver"))
