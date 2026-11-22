"""Di chi è il turno (C1, Task 8, decisione 8): funzione pura."""
import unittest

from tollgate_analysis import turn
from tollgate_analysis.turn import TurnFacts, waiting_on


class WaitingOnTest(unittest.TestCase):
    def test_decision_wins(self):
        self.assertEqual(waiting_on(TurnFacts("pr_open", [{"kind": "block", "id": 3}])),
                         "decision")

    def test_user_phases(self):
        self.assertEqual(turn.USER_PHASES, ("pr_open", "approval"))
        for phase in ("pr_open", "approval"):
            with self.subTest(phase=phase):
                self.assertEqual(waiting_on(TurnFacts(phase, [])), "user")

    def test_agent_otherwise(self):
        for phase in ("execution", "spec_audit", "plan", "review", "blocked"):
            with self.subTest(phase=phase):
                self.assertEqual(waiting_on(TurnFacts(phase, [])), "agent")


if __name__ == "__main__":
    unittest.main()
