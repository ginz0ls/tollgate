import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, TempState
from tests.hookkit import SESSION, Lab
from tests.test_check_agents import agent_payload

CTX = ROOT / "statusline" / "ctx"


def payload(session="s1", pct=42):
    d = {"session_id": session, "context_window": {}}
    if pct is not None:
        d["context_window"]["used_percentage"] = pct
    return json.dumps(d)


class CtxTest(unittest.TestCase):
    def setUp(self):
        self.ts = TempState()
        self.home = tempfile.mkdtemp(prefix="tollgate-home-")
        self.addCleanup(self.ts.cleanup)

    def run_ctx(self, stdin, *args, env=None):
        e = dict(env or self.ts.env())
        e["HOME"] = self.home
        return subprocess.run([str(CTX), *args], input=stdin, capture_output=True, text=True,
                              env=e)

    def written(self, session="s1"):
        return json.loads((self.ts.dir / "ctx" / f"{session}.json").read_text())

    def test_executable(self):
        self.assertTrue(os.access(CTX, os.X_OK))

    def test_writes_used_pct(self):
        r = self.run_ctx(payload())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertEqual(self.written(), {"used_pct": 42})
        self.assertEqual(sorted(p.name for p in (self.ts.dir / "ctx").iterdir()), ["s1.json"])

    def test_float_pct(self):
        self.run_ctx(payload(pct=12.5))
        self.assertEqual(self.written(), {"used_pct": 12.5})

    def test_null_when_missing(self):
        self.run_ctx(payload(pct=None))
        self.assertEqual(self.written(), {"used_pct": None})

    def test_null_when_not_a_number(self):
        self.run_ctx(json.dumps({"session_id": "s1",
                                 "context_window": {"used_percentage": "42"}}))
        self.assertEqual(self.written(), {"used_pct": None})

    def test_passes_stdin_to_wrapped_command(self):
        text = payload()
        r = self.run_ctx(text, "cat")
        self.assertEqual(r.stdout, text)

    def test_wrapped_command_is_a_shell_string(self):
        r = self.run_ctx(payload(), "cat | tr a-z A-Z")
        self.assertEqual(r.stdout, payload().upper())

    def test_exit_code_of_wrapped_command(self):
        self.assertEqual(self.run_ctx(payload(), "exit 3").returncode, 3)

    def test_wrapped_command_runs_on_garbage_input(self):
        r = self.run_ctx("non e' json", "cat")
        self.assertEqual(r.stdout, "non e' json")
        self.assertFalse((self.ts.dir / "ctx").exists())

    def test_unsafe_session_ignored(self):
        for bad in ("../x", "a/b", "", "a b", "a.json"):
            with self.subTest(session=bad):
                r = self.run_ctx(payload(session=bad), "cat")
                self.assertEqual(r.stdout, payload(session=bad))
        self.assertFalse((self.ts.dir / "ctx").exists())
        self.assertFalse((self.ts.dir.parent / "x.json").exists())

    def test_unwritable_state_does_not_break_wrapped_command(self):
        (self.ts.dir / "ctx").write_text("un file, non una cartella")
        r = self.run_ctx(payload(), "echo ok")
        self.assertEqual(r.stdout, "ok\n")

    def test_no_command_prints_nothing(self):
        r = self.run_ctx(payload())
        self.assertEqual((r.stdout, r.stderr, r.returncode), ("", "", 0))

    def test_state_without_sentinel_not_used(self):
        other = Path(tempfile.mkdtemp(prefix="tollgate-nosentinel-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(other, ignore_errors=True))
        env = dict(os.environ, TOLLGATE_STATE=str(other))
        self.run_ctx(payload(), env=env)
        self.assertFalse((other / "ctx").exists())
        self.assertTrue((Path(self.home) / ".local/state/tollgate/ctx/s1.json").exists())

    def test_context_guard_reads_it(self):
        lab = Lab()
        self.addCleanup(lab.ts.cleanup)
        self.run_ctx(payload(session=SESSION, pct=60), env=lab.ts.env())
        r = lab.hook(agent_payload(lab, "Explore"))
        self.assertEqual(r.exit, 2)
        self.assertIn("contesto", r.stderr)


if __name__ == "__main__":
    unittest.main()
