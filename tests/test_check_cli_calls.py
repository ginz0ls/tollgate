import json
import unittest

from tests.helpers import BIN
from tests.hookkit import SESSION, Lab

PROGRAM = BIN / "tollgate"


class CliCallsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.signal = self.lab.ts.dir / "cli" / f"{SESSION}.json"

    def tearDown(self):
        self.lab.close()

    def signals(self):
        return json.loads(self.signal.read_text())

    def test_coordinator_call_records_signal(self):
        r = self.lab.bash(f"'{PROGRAM}' start 7")
        self.assertEqual(r.exit, 0)
        entry = self.signals()["start"]
        self.assertEqual(entry["argv"][0], "start")
        self.assertEqual(entry["argv"], ["start", "7"])
        self.assertEqual(entry["cwd"], str(self.lab.wt))

    def test_act_and_start_keep_separate_entries(self):
        self.lab.bash(f"'{PROGRAM}' start 7")
        self.lab.bash(f"'{PROGRAM}' act apply")
        self.assertEqual(sorted(self.signals()), ["act", "start"])

    def test_python_form_records_signal(self):
        r = self.lab.bash(f"python3 '{PROGRAM}' start 7")
        self.assertEqual(r.exit, 0)
        self.assertEqual(self.signals()["start"]["argv"], ["start", "7"])

    def test_python_form_with_double_quoted_spaced_path(self):
        """La forma delle skill: python3 "<percorso con spazi>/bin/tollgate" (nel checkout di
        prova il percorso ha spazi)."""
        self.assertIn(" ", str(PROGRAM))
        self.assertEqual(self.lab.bash(f'python3 "{PROGRAM}" start 7').exit, 0)
        self.assertEqual(self.signals()["start"]["argv"], ["start", "7"])
        self.assertEqual(self.lab.bash(f'python3 "{PROGRAM}" act apply').exit, 0)
        self.assertEqual(sorted(self.signals()), ["act", "start"])
        for cmd in (f'python3 "{PROGRAM}" task start 1', f'python3 "{PROGRAM}" start 7',
                    f'python3 "{PROGRAM}" act apply', f'python3 "{PROGRAM}" status --checkpoint'):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="ag-1").exit, 2)

    def test_other_subcommands_leave_no_signal(self):
        for cmd in (f"'{PROGRAM}' verify", f"'{PROGRAM}' task start 1",
                    f"'{PROGRAM}' status", "git status"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd).exit, 0)
        self.assertFalse(self.signal.exists())

    def test_subagent_cannot_run_coordinator_commands(self):
        for cmd in (f"'{PROGRAM}' task start 1", f"'{PROGRAM}' act apply",
                    f"'{PROGRAM}' status --checkpoint", f"'{PROGRAM}' start 7",
                    f"python3 '{PROGRAM}' task start 1"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="ag-1").exit, 2)
        for cmd in (f"'{PROGRAM}' verify", f"'{PROGRAM}' block open needs_you --reason x",
                    f"'{PROGRAM}' status"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="ag-1").exit, 0)
        self.assertFalse(self.signal.exists())

    def test_cd_then_call_records_effective_dir(self):
        sub = self.lab.wt / "src"
        sub.mkdir(exist_ok=True)
        self.lab.bash(f"cd '{sub}' && '{PROGRAM}' start 7")
        self.assertEqual(self.signals()["start"]["cwd"], str(sub))

    def test_unwritable_state_does_not_deny(self):
        (self.lab.ts.dir / "cli").write_text("file, non cartella")
        self.assertEqual(self.lab.bash(f"'{PROGRAM}' start 7").exit, 0)


if __name__ == "__main__":
    unittest.main()
