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

    def test_interpreter_options_before_the_script(self):
        for cmd in (f'python3 -B "{PROGRAM}" start 7', f"python3 -W error -B '{PROGRAM}' start 7",
                    f"python3 -X dev '{PROGRAM}' start 7"):
            with self.subTest(cmd=cmd):
                self.signal.unlink(missing_ok=True)
                self.assertEqual(self.lab.bash(cmd).exit, 0)
                self.assertEqual(self.signals()["start"]["argv"], ["start", "7"])
        for cmd in (f'python3 -B "{PROGRAM}" task done 1', f"python3 -W error '{PROGRAM}' act apply",
                    f"python3 -B -X dev '{PROGRAM}' status --checkpoint"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="ag-1").exit, 2)
        self.assertEqual(self.lab.bash(f'python3 -B "{PROGRAM}" verify', agent_id="ag-1").exit, 0)

    def test_subagent_cannot_hide_the_program_in_an_expansion(self):
        for cmd in (f'p="{PROGRAM}"; python3 "$p" task done 1',
                    f'P="{PROGRAM}" python3 $P act apply',
                    f'python3 "$(echo {PROGRAM})" task done 1',
                    f"python3 `echo '{PROGRAM}'` start 7",
                    f'p="{PROGRAM}"; "$p" task done 1',
                    f'python3 -B "$p" status --checkpoint'):
            with self.subTest(cmd=cmd):
                r = self.lab.bash(cmd, agent_id="ag-1")
                self.assertEqual(r.exit, 2)
        for cmd in (f'p="{PROGRAM}"; python3 "$p" verify', 'python3 -c "print(1)"',
                    'python3 "$x" tasks', 'echo "$HOME" start'):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="ag-1").exit, 0)
        self.assertFalse(self.signal.exists())

    def test_uncertain_program_denial_says_what_to_do(self):
        r = self.lab.bash(f'p="{PROGRAM}"; python3 "$p" task done 1', agent_id="ag-1")
        self.assertEqual(r.exit, 2)
        self.assertIn("percorso dello script in modo letterale", r.stderr)
        self.assertIn("senza variabile né $(…)", r.stderr)
        r = self.lab.bash(f"python3 '{PROGRAM}' task done 1", agent_id="ag-1")
        self.assertEqual(r.exit, 2)
        self.assertNotIn("in modo letterale", r.stderr)

    def test_subagent_unparsable_command_naming_the_program_is_denied(self):
        self.assertEqual(
            self.lab.bash(f"python3 '{PROGRAM}' task done 1 \"unchiuso", agent_id="ag-1").exit, 2)
        self.assertEqual(self.lab.bash('echo "unchiuso', agent_id="ag-1").exit, 0)
        self.assertEqual(
            self.lab.bash(f"python3 '{PROGRAM}' status --checkpoint \"unchiuso",
                          agent_id="ag-1").exit, 2)
        self.assertEqual(
            self.lab.bash(f"python3 '{PROGRAM}' verify \"unchiuso", agent_id="ag-1").exit, 0)
        self.assertEqual(self.lab.bash(f"python3 '{PROGRAM}' start 7 \"unchiuso").exit, 0)

    def test_gate_publish_denied_to_everyone(self):
        for cmd in (f"'{PROGRAM}' gate base-ids --sha x --out o --publish",
                    f'python3 "{PROGRAM}" gate base-ids --publish --sha x --out o',
                    f"python3 -B '{PROGRAM}' gate evaluate --event e --publish",
                    f"'{PROGRAM}' gate base-publish --ids d --event e --publish",
                    f"cd /tmp && '{PROGRAM}' gate sentinel --publish=1",
                    f'p="{PROGRAM}"; python3 "$p" gate guard --publish'):
            for agent in (None, "ag-1"):
                with self.subTest(cmd=cmd, agent=agent):
                    r = self.lab.bash(cmd, agent_id=agent)
                    self.assertEqual(r.exit, 2)
                    self.assertIn("GitHub Actions", r.stderr)
        self.assertEqual(self.lab.bash(f"python3 '{PROGRAM}' gate base-ids \"unchiuso --pub",
                                       ).exit, 2)

    def test_gate_publish_abbreviations_denied(self):
        for opt in ("--pu", "--pub", "--publi", "--pub=1", "--publish=x"):
            for agent in (None, "ag-1"):
                with self.subTest(opt=opt, agent=agent):
                    r = self.lab.bash(f"'{PROGRAM}' gate base-ids --sha x {opt}", agent_id=agent)
                    self.assertEqual(r.exit, 2)
        for opt in ("--p", "--pull", "--publisher", "--out=--pub"):
            with self.subTest(opt=opt):
                self.assertEqual(self.lab.bash(f"'{PROGRAM}' gate base-ids {opt}").exit, 0)

    def test_gate_without_publish_is_not_denied(self):
        for cmd in (f"'{PROGRAM}' gate run --event e --out o",
                    f"'{PROGRAM}' gate base-ids --sha x --out o", f"'{PROGRAM}' verify --publish",
                    "echo gate --publish"):
            for agent in (None, "ag-1"):
                with self.subTest(cmd=cmd, agent=agent):
                    self.assertEqual(self.lab.bash(cmd, agent_id=agent).exit, 0)

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

    def test_p3b_subcommands_signalled(self):
        for cmd, sub, argv in ((f"'{PROGRAM}' finish open-pr", "finish", ["finish", "open-pr"]),
                               (f"'{PROGRAM}' sync", "sync", ["sync"]),
                               (f"'{PROGRAM}' adopt 7", "adopt", ["adopt", "7"]),
                               (f"'{PROGRAM}' cleanup --confirm", "cleanup",
                                ["cleanup", "--confirm"]),
                               (f"'{PROGRAM}' abandon 7", "abandon", ["abandon", "7"]),
                               (f"'{PROGRAM}' finish check", "finish", ["finish", "check"])):
            with self.subTest(cmd=cmd):
                self.signal.unlink(missing_ok=True)
                self.assertEqual(self.lab.bash(cmd).exit, 0)
                self.assertEqual(self.signals()[sub]["argv"], argv)
        self.signal.unlink(missing_ok=True)
        self.assertEqual(self.lab.bash(f"'{PROGRAM}' review prepare").exit, 0)
        self.assertFalse(self.signal.exists())

    def test_subagent_denied_p3b_commands(self):
        for cmd in (f"'{PROGRAM}' finish check", f"'{PROGRAM}' review prepare",
                    f"'{PROGRAM}' sync", f"'{PROGRAM}' adopt 7", f"'{PROGRAM}' cleanup",
                    f"'{PROGRAM}' abandon 7"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="ag-1").exit, 2)
        self.assertFalse(self.signal.exists())

    def test_audit_is_coordinator_only(self):
        for cmd in (f"'{PROGRAM}' audit prepare", f"python3 \"{PROGRAM}\" audit prepare --confirm",
                    f"'{PROGRAM}' audit decline"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="ag-1").exit, 2)
                self.assertEqual(self.lab.bash(cmd).exit, 0)
        self.assertFalse(self.signal.exists())    # `audit` non legge la sessione: nessun segnale

    def test_parse_failure_message_explains(self):
        r = self.lab.bash(f"python3 '{PROGRAM}' task done 1 \"unchiuso", agent_id="ag-1")
        self.assertEqual(r.exit, 2)
        self.assertIn("modo letterale", r.stderr)


if __name__ == "__main__":
    unittest.main()
