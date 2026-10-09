import unittest
from datetime import datetime, timezone

from tests.helpers import TempState
from tollgate_core import db, effects

T0 = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.conn = db.open_db(self.ts.state)

    def tearDown(self):
        self.conn.close()
        self.ts.cleanup()

    def test_id_is_deterministic(self):
        k1 = effects.effect_key("npm publish", None, "abc")
        self.assertEqual(k1, effects.effect_key("npm publish", None, "abc"))
        self.assertNotEqual(k1, effects.effect_key("npm publish", None, "def"))
        self.assertRegex(effects.effect_id(k1), r"^e-[0-9a-f]{8}$")

    def test_request_execute_request_again(self):
        k = effects.effect_key("npm publish", None, "abc")
        effects.request(self.conn, key=k, command="npm publish", work=None, sha="abc",
                        now=T0, session="s1")
        self.assertEqual(effects.get(self.conn, k)["state"], "requested")
        self.assertIsNone(effects.executed_at(effects.get(self.conn, k)))
        effects.mark_executed(self.conn, key=k, act_id="a-3", now=T0, session="s1")
        self.assertEqual(effects.get(self.conn, k)["state"], "executed")
        effects.request(self.conn, key=k, command="npm publish", work=None, sha="abc",
                        now=T0, session="s1")
        row = effects.get(self.conn, k)
        self.assertEqual(row["state"], "requested")
        self.assertEqual(effects.executed_at(row), "2026-10-09T10:00:00.000000Z")
        types = [r[0] for r in self.conn.execute("SELECT type FROM events ORDER BY seq")]
        self.assertEqual(types, ["effect_requested", "effect_executed", "effect_requested"])


if __name__ == "__main__":
    unittest.main()
