import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from tests.helpers import ROOT, TempState, make_origin_repo

FAKE_BIN = textwrap.dedent('''\
    #!/usr/bin/env python3
    import os, sys, time
    sys.stdin.read()
    m = os.environ.get("FAKE_MODE", "0")
    if m == "sleep":
        time.sleep(30)
    if m == "raise":
        raise RuntimeError("guasto")
    print("OUT")
    sys.stderr.write("ERR\\n")
    sys.exit(int(m))
''')
TOML = 'schema_version = 1\n[gate]\nmode = "protected"\n[hooks]\ntimeout_s = 1\n'
TOOLS = ["bash", "git", "sed", "tr", "head", "cat", "date", "mkdir", "rm", "mktemp", "sleep",
         "awk", "dirname", "kill", "env"]


class WrapperTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate wrapper "))
        self.plugin = self.tmp / "plugin"
        (self.plugin / "hooks").mkdir(parents=True)
        (self.plugin / "bin").mkdir()
        shutil.copy(ROOT / "hooks" / "run", self.plugin / "hooks" / "run")
        (self.plugin / "bin" / "tollgate").write_text(FAKE_BIN)
        (self.plugin / "bin" / "tollgate").chmod(0o755)
        self.repo, _, _ = make_origin_repo(self.tmp / "r", {"a.txt": "a\n"}, TOML)
        self.plain = self.tmp / "plain"
        self.plain.mkdir()

    def tearDown(self):
        self.ts.cleanup()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_wrapper(self, event, payload=None, *, cwd=None, mode="0", path=None):
        payload = payload or {"hook_event_name": event, "session_id": "s1",
                              "cwd": str(cwd or self.repo), "tool_name": "Bash",
                              "tool_input": {"command": "ls"}}
        env = self.ts.env()
        env["FAKE_MODE"] = mode
        if path is not None:
            env["PATH"] = path
        t0 = time.monotonic()
        r = subprocess.run([str(self.plugin / "hooks" / "run"), event],
                           input=json.dumps(payload), capture_output=True, text=True, env=env,
                           cwd=str(cwd or self.repo), timeout=30)
        return r, time.monotonic() - t0

    def off_payload(self, args, cwd=None):
        return {"hook_event_name": "UserPromptExpansion", "session_id": "s1",
                "cwd": str(cwd or self.repo), "command_name": "tollgate:off",
                "command_args": args, "expansion_type": "slash_command"}

    def test_control_errors_become_2(self):
        for mode in ("1", "127", "raise"):
            with self.subTest(mode=mode):
                r, _ = self.run_wrapper("PreToolUse", mode=mode)
                self.assertEqual(r.returncode, 2)
                self.assertIn(f"touch {self.ts.dir}/OFF", r.stderr)
                self.assertIn(str(self.plugin / "bin" / "tollgate"), r.stderr)

    def test_timeout_becomes_2(self):
        r, elapsed = self.run_wrapper("PreToolUse", mode="sleep")
        self.assertEqual(r.returncode, 2)
        self.assertLess(elapsed, 10)

    def test_informative_errors_become_0(self):
        for event in ("PostToolUse", "SubagentStop", "SessionStart", "UserPromptExpansion"):
            with self.subTest(event=event):
                self.assertEqual(self.run_wrapper(event, mode="1")[0].returncode, 0)

    def test_zero_and_two_pass_through(self):
        r, _ = self.run_wrapper("PreToolUse", mode="2")
        self.assertEqual((r.returncode, r.stdout.strip()), (2, "OUT"))
        self.assertEqual(self.run_wrapper("SubagentStop", mode="2")[0].returncode, 2)
        self.assertEqual(self.run_wrapper("PreToolUse", mode="0")[0].returncode, 0)

    def test_inactive_repo_exits_0_without_running(self):
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, mode="2")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_bound_marker_makes_any_dir_active(self):
        (self.ts.dir / "bound").mkdir()
        (self.ts.dir / "bound" / "s1").touch()
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, mode="2")
        self.assertEqual(r.returncode, 2)

    def test_json_str_takes_first_occurrence(self):
        # cwd di primo livello non attivo; un `cwd` annidato in tool_input punterebbe al repo.
        payload = {"hook_event_name": "PreToolUse", "session_id": "s1",
                   "cwd": str(self.plain),
                   "tool_input": {"command": "ls", "cwd": str(self.repo)}}
        r, _ = self.run_wrapper("PreToolUse", payload, cwd=self.plain, mode="2")
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_user_prompt_submit_without_notification_never_starts_python(self):
        payload = {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
                   "cwd": str(self.repo), "prompt": "ciao"}
        r, _ = self.run_wrapper("UserPromptSubmit", payload, mode="0")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_user_prompt_submit_with_notification_runs_engine(self):
        payload = {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
                   "cwd": str(self.repo), "prompt": "<task-notification>x</task-notification>"}
        r, _ = self.run_wrapper("UserPromptSubmit", payload, mode="0")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "OUT"))

    def _path_without_python(self):
        d = self.tmp / "nopy"
        d.mkdir(exist_ok=True)
        for t in TOOLS:
            src = shutil.which(t)
            if src and not (d / t).exists():
                os.symlink(src, d / t)
        return str(d)

    def test_without_python(self):
        path = self._path_without_python()
        self.assertEqual(self.run_wrapper("PreToolUse", path=path)[0].returncode, 2)
        self.assertEqual(self.run_wrapper("PostToolUse", path=path)[0].returncode, 0)
        r, _ = self.run_wrapper("PreToolUse", cwd=self.plain, path=path)
        self.assertEqual(r.returncode, 0)
        prompt = {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
                  "cwd": str(self.repo), "prompt": "ciao"}
        r, _ = self.run_wrapper("UserPromptSubmit", prompt, path=path)
        self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_off_on_and_expiry(self):
        off = self.off_payload("2")
        r, _ = self.run_wrapper("UserPromptExpansion", off, mode="2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("until=", (self.ts.dir / "OFF").read_text())
        r, _ = self.run_wrapper("PreToolUse", mode="2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("spento", r.stderr)
        self.assertIn("PreToolUse", (self.ts.dir / "skipped.log").read_text())
        on = dict(off, command_name="tollgate:on", command_args="")
        self.run_wrapper("UserPromptExpansion", on)
        self.assertFalse((self.ts.dir / "OFF").exists())
        log = (self.ts.dir / "off.log").read_text().splitlines()
        self.assertRegex(log[0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.000000Z off \d+$")
        self.assertRegex(log[1], r"Z on$")
        (self.ts.dir / "OFF").write_text(f"until={int(time.time()) - 60}\n")
        self.assertEqual(self.run_wrapper("PreToolUse", mode="2")[0].returncode, 2)
        self.assertFalse((self.ts.dir / "OFF").exists())

    def test_off_without_hours(self):
        off = self.off_payload("", cwd=self.plain)
        r, _ = self.run_wrapper("UserPromptExpansion", off, cwd=self.plain)
        self.assertEqual((self.ts.dir / "OFF").read_text(), "")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("non è un numero intero", r.stderr)
        self.assertRegex((self.ts.dir / "off.log").read_text(), r"Z off\n$")

    def test_off_hours_with_leading_zero_is_decimal(self):
        now = int(time.time())
        r, _ = self.run_wrapper("UserPromptExpansion", self.off_payload("08"), mode="2")
        self.assertEqual(r.returncode, 0)
        until = int((self.ts.dir / "OFF").read_text().split("=")[1])
        self.assertLess(abs(until - (now + 8 * 3600)), 60)
        self.assertIn("spento per 08 ore", r.stderr)

    def test_off_invalid_hours_means_no_expiry_and_warns(self):
        r, _ = self.run_wrapper("UserPromptExpansion", self.off_payload("0.5"), mode="2")
        self.assertEqual(r.returncode, 0)
        self.assertEqual((self.ts.dir / "OFF").read_text(), "")
        self.assertIn("non è un numero intero di ore", r.stderr)
        self.assertRegex((self.ts.dir / "off.log").read_text(), r"Z off\n$")


if __name__ == "__main__":
    unittest.main()
