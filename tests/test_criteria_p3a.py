"""Criteri di accettazione di P3a dal programma vero (spec 15): hooks/run e bin/tollgate come li
lancia Claude Code, su un repo temporaneo con HOME, stato e gh finti (FlowLab)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests import test_start
from tests.flowkit import SESSION, FlowLab
from tests.helpers import BIN, ROOT
from tests.hookkit import DEFAULT_TOML, DROP, sample
from tests.test_check_subagent_stop import report
from tests.test_check_task_verdict import REVIEWER
from tests.test_taskcmd import PLAN, plan_text
from tollgate_core import clock, paths, phases, sessions, tasks

RUN = ROOT / "hooks" / "run"
IMPL = "tollgate:implementer"
NO_TESTS_TOML = DEFAULT_TOML + "[project]\nallow_no_tests = true\n"


def hook(lab, event, payload):
    return subprocess.run([str(RUN), event], input=json.dumps(payload), capture_output=True,
                          text=True, env=lab.env(), timeout=60)


def tollgate(lab, *argv, cwd):
    """bin/tollgate senza scrivere il segnale: come lo lancia il modello dopo l'hook."""
    return subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), *argv], cwd=str(cwd),
                          env=lab.env(), capture_output=True, text=True, timeout=120)


class StartFromWrapperTest(test_start.StartCase):
    def test_start_from_wrapper_flow(self):                      # criterio 1
        fl = self.make()
        command = f"{paths.program_command(BIN / 'tollgate')} start 7 --level L1"
        r = hook(fl, "PreToolUse", sample("PreToolUse-Bash", session_id=SESSION,
                                          cwd=str(fl.main), tool_input={"command": command}))
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        found = sessions.cli_session(fl.ts.state, fl.main, "start", now=clock.now())
        self.assertEqual(found, SESSION)
        r = tollgate(fl, "start", "7", "--level", "L1", cwd=fl.main)
        self.assertEqual(r.returncode, 0, test_start.out(r))
        row = self.rows(fl)[0]
        self.assertEqual((row["issue"], row["phase"], json.loads(row["sessions"])),
                         (7, "plan", [SESSION]))
        self.assertTrue(Path(row["worktree"]).is_dir())
        self.assertIn("prossimo passo: EnterWorktree", r.stdout)


class TaskCycleEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.fl = FlowLab(issue=7, phase="plan", toml=NO_TESTS_TOML)
        self.addCleanup(self.fl.close)
        self.wt = self.fl.wt

    def event(self, event, name, **changes):
        base = dict(session_id=SESSION, cwd=str(self.wt))
        base.update(changes)
        return hook(self.fl, event, sample(name, **base))

    def subagent(self, aid, atype):
        r = self.event("SubagentStart", "SubagentStart-none", agent_id=aid, agent_type=atype)
        self.assertEqual((r.returncode, r.stderr), (0, ""))

    def stop(self, aid, atype, text):
        return self.event("SubagentStop", "SubagentStop-manual-normal", agent_id=aid,
                          agent_type=atype, last_assistant_message=text,
                          agent_transcript_path="/non/esiste.jsonl")

    def row(self):
        return tasks.get_task(self.fl.conn, self.fl.work, 1)

    def test_task_cycle_end_to_end(self):                        # criterio 4 (ramo generico, senza profili verticali)
        fl, wt = self.fl, self.wt
        plan = wt / PLAN
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(plan_text())
        r = self.event("PostToolUse", "PostToolUse-Write", tool_name="Write",
                       agent_id=DROP, agent_type=DROP,
                       tool_input={"file_path": str(plan), "content": plan_text()},
                       tool_response={"filePath": str(plan)})
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertEqual(phases.get_work(fl.conn, fl.work)["phase"], "execution")
        fl.git("add", PLAN, repo=wt)
        fl.git("commit", "-qm", "piano", repo=wt)

        r = tollgate(fl, "task", "start", "1", cwd=wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tg-7-t1", r.stdout)
        self.assertEqual(self.row()["state"], "running")

        launch = {"description": "d", "prompt": "p", "subagent_type": IMPL, "name": "tg-7-t1",
                  "run_in_background": False}
        r = self.event("PreToolUse", "PreToolUse-Agent", tool_input=launch)
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.subagent("ag-impl", IMPL)
        self.assertEqual(self.row()["pending"], None)

        (wt / "src" / "app.py").write_text("def somma(a, b):\n    return b + a\n")
        fl.git("commit", "-qam", "somma", repo=wt)
        r = self.event("PostToolUse", "PostToolUse-Bash", agent_id="ag-impl", agent_type=IMPL,
                       tool_input={"command": "git commit -qam somma", "description": "x"},
                       tool_response={"stdout": "", "stderr": "", "interrupted": False})
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        r = tollgate(fl, "verify", cwd=wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        r = self.stop("ag-impl", IMPL, report())
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertEqual(self.row()["state"], "review")

        r = tollgate(fl, "task", "review-prepare", "1", cwd=wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"revisore: {REVIEWER}", r.stdout)
        row = self.row()
        verdict = {"v": 1, "task": 1, "sha": row["review_sha"], "code": row["review_code"],
                   "outcome": "approved", "spec_compliance": [], "findings": []}
        text = "Verdetto.\n```json\n" + json.dumps(verdict) + "\n```"
        self.subagent("ag-rev", REVIEWER)
        r = self.stop("ag-rev", REVIEWER, text)
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        self.assertEqual((self.row()["verdict"], self.row()["state"]), ("approved", "review"))

        r = tollgate(fl, "task", "done", "1", cwd=wt)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "task 1: done"), r.stderr)
        self.assertEqual(self.row()["state"], "done")


if __name__ == "__main__":
    unittest.main()
