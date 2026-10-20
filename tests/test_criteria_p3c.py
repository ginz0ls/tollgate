"""Criteri di accettazione di P3c dal programma vero (spec 15): hooks/run e bin/tollgate come li
lancia Claude Code, su un repo temporaneo con HOME, stato e gh finti (FlowLab). I subagenti non
si lanciano: i loro eventi (SubagentStart, SubagentStop) e i loro messaggi li scrive il test."""
import json
import os
import shlex
import shutil
import subprocess
import unittest
from pathlib import Path

from tests.flowkit import PLAN, SESSION, SPEC, FlowLab, plan_text, round_message, spec_text
from tests.hookkit import sample
from tests.test_adopt import blob
from tests.test_criteria_p3b import MINOR, NO_RULE, FinishCase, hook
from tests.test_openpr import BOTH_OK, ISSUES, SOMMA, TOML
from tollgate_analysis import approvals, prblock
from tollgate_core import audits, db, dod, scope

FIRST_ISSUE, LATER_ISSUE = 3, 9
LOGIN = "src/auth/login.py"
ZERO = {k: 0 for k in approvals.SEVERITIES}


def first_slice_files() -> dict:
    """Ciò che la prima fetta (issue 3) ha unito sul predefinito: la spec con tre fette, la sua
    approvazione e i report dell'avversario e delle lenti."""
    text = spec_text(3)
    folder = f"{approvals.REVIEWS_DIR}/{FIRST_ISSUE}"
    files = {SPEC: text, approvals.approval_paths(FIRST_ISSUE)[0]: approvals.render_approval({
        "kind": "spec-approval", "path": SPEC, "sha": blob(text), "slices": 3,
        "adversarial": "closed", "lens": "closed", "act_id": "a-1",
        "approved_at": "2026-10-19T10:00:00Z"})}
    for kind in ("spec-adversarial", "spec-lens"):
        files[f"{folder}/{kind}-1.md"] = approvals.render_report(
            {"kind": kind, "number": 1, "counts": ZERO, "outcome": "empty"}, "Nessun rilievo.\n")
    return files


class LaterSliceTest(FinishCase):
    """Fetta successiva (Review Focus 5): una spec approvata dall'issue 3 e unita sul predefinito,
    poi `start 9 --spec`, piano, task, `finish check`, `open-pr` e `adopt` dopo un DB perso."""

    def setUp(self):
        fl = FlowLab(issue=None, toml=TOML, files=first_slice_files())
        self.addCleanup(fl.close)
        self.fl, self.n_agents = fl, 0
        tip = fl.git("rev-parse", "origin/main")
        fl.set_gh(auth=True, issues={"9": {**ISSUES["7"], "number": 9, "title": "Seconda fetta"}},
                  prs=[], issue_list=[],
                  statuses={tip: {"statuses": [{"context": "tollgate/guard", "state": "success"},
                                               {"context": "tollgate/verdict",
                                                "state": "success"}]}})

    # --- come lo farebbe il coordinatore -------------------------------------------------
    def commit(self, paths, message):
        """`git add` e `git commit` da Bash: PreToolUse Bash non deve vietarli, PostToolUse Bash
        registra il commit."""
        command = ("git add -- " + " ".join(shlex.quote(p) for p in paths)
                   + " && git commit -q -m " + shlex.quote(message))
        self.event("PreToolUse", "PreToolUse-Bash", tool_input={"command": command})
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com",
                   GIT_CONFIG_GLOBAL="/dev/null")
        done = subprocess.run(["bash", "-c", command], cwd=self.wt, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.event("PostToolUse", "PostToolUse-Bash", tool_input={"command": command},
                   tool_response={"stdout": "", "stderr": "", "interrupted": False})

    def write(self, rel, text):
        """Write di Claude Code: PreToolUse, il file, PostToolUse."""
        path = self.wt / rel
        self.event("PreToolUse", "PreToolUse-Write", tool_name="Write",
                   tool_input={"file_path": str(path), "content": text})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.event("PostToolUse", "PostToolUse-Write", tool_name="Write",
                   tool_input={"file_path": str(path), "content": text},
                   tool_response={"filePath": str(path)})

    def edit_spec(self):
        return hook(self.fl, "PreToolUse", sample(
            "PreToolUse-Edit", session_id=SESSION, cwd=str(self.wt), tool_name="Edit",
            tool_input={"file_path": str(self.wt / SPEC), "old_string": "a", "new_string": "b"}))

    def round(self, kind):
        """`audit prepare` apre il giro e l'agente riporta il suo messaggio senza rilievi."""
        r = self.cli("audit", "prepare")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        row = audits.open_round_row(self.fl.conn, self.fl.work)
        self.assertEqual(row["kind"], kind)
        self.agent(audits.AGENTS[kind], round_message(row, {}))
        self.assertIsNone(audits.open_round_row(self.fl.conn, self.fl.work))

    def approve(self, what):
        self.slash("approve", what)
        r = self.cli("act", "apply")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    # --- il flusso --------------------------------------------------------------------------
    def start_later_slice(self):
        r = self.cli("start", str(LATER_ISSUE), "--spec", SPEC, cwd=self.fl.main)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"spec approvata: {SPEC} (approvazione in "
                      f"docs/superpowers/reviews/{FIRST_ISSUE}/)", r.stdout)
        row = db_row(self.fl.conn)
        self.assertEqual((row["issue"], row["level"], row["phase"], row["spec_path"]),
                         (LATER_ISSUE, "L2", "plan", SPEC))
        self.wt = Path(row["worktree"])
        self.fl.lab.wt = self.fl.wt = self.wt              # il banco usa il worktree di `start`
        self.fl.lab.work = self.fl.work = row["id"]
        self.assertTrue((self.wt / SPEC).is_file())

    def to_execution(self):
        self.start_later_slice()
        denied = self.edit_spec()                            # la spec approvata è bloccata
        self.assertEqual(denied.returncode, 2, denied.stdout + denied.stderr)
        self.write(PLAN, plan_text(tasks=2, task2=f"- Create: `{LOGIN}`"))
        self.commit([PLAN], "piano")
        self.round("plan-adversarial")
        self.cli("audit", "prepare")
        self.assertEqual(self.work()["phase"], "approval")
        self.approve("plan")
        work = self.work()
        self.assertEqual(work["phase"], "execution")
        plan_approval = approvals.approval_paths(LATER_ISSUE)[1]
        header = approvals.parse_approval((self.wt / plan_approval).read_text())
        self.assertEqual((header["sha"], header["spec_sha"]),
                         (work["plan_sha"], blob(spec_text(3))))
        self.commit([f"{approvals.REVIEWS_DIR}/{LATER_ISSUE}"], "approvazione del piano e report")
        for k in (1, 2):
            r = self.cli("task", "start", str(k))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.fl.close_tasks()
        self.fl.commit("tests/ids.txt", BOTH_OK, "ids")
        self.fl.commit("src/app.py", SOMMA, "somma")
        self.fl.commit(LOGIN, "x = 1\n", "login")

    def test_later_slice_end_to_end(self):                      # criterio 24, Review Focus 5
        self.to_execution()
        self.assertIn(LOGIN, scope.paths(self.fl.conn, self.fl.work))
        r = self.finish_check()
        self.assertNotIn("out_of_scope", r.stdout)
        self.assertIn("[sì] " + dod.LABELS["approvals"], r.stdout)
        self.assertNotIn("[no]", r.stdout)

        self.review([MINOR, NO_RULE], outcome="ok")
        self.open_pr()
        (opened,) = json.loads(self.fl.gh_data.read_text())["prs"]
        block = prblock.parse(opened["body"])
        self.assertEqual((block["issue"], block["level"], block["spec"]),
                         (LATER_ISSUE, "L2", SPEC))
        self.assertEqual(block["spec_reviews_dir"], f"docs/superpowers/reviews/{FIRST_ISSUE}/")
        self.assertEqual(block["plan_reviews_dir"], f"docs/superpowers/reviews/{LATER_ISSUE}/")
        self.assertEqual(block["spec_audit"], {"adversarial": "closed", "lens": "closed"})
        self.assertEqual(self.work()["phase"], "pr_open")

        # DB perso, PR chiusa senza merge: `adopt` ritrova la fase dal ramo
        head = self.fl.git("rev-parse", "HEAD", repo=self.wt)
        data = json.loads(self.fl.gh_data.read_text())
        data["prs"][0]["state"] = "CLOSED"
        self.fl.set_gh(**data)
        self.fl.conn.close()
        state = self.fl.ts.state
        shutil.move(str(state.db_path), str(state.db_path) + ".perso")
        for extra in ("-wal", "-shm"):
            Path(str(state.db_path) + extra).unlink(missing_ok=True)
        self.fl.lab.conn = self.fl.conn = db.open_db(state)
        self.slash("adopt", f"#{LATER_ISSUE}")
        r = self.cli("adopt", str(LATER_ISSUE))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        row = db_row(self.fl.conn)
        self.assertEqual((row["issue"], row["level"], row["phase"], row["spec_path"]),
                         (LATER_ISSUE, "L2", "execution", SPEC))
        self.assertIsNotNone(row["plan_sha"])
        self.assertEqual(self.fl.git("rev-parse", "HEAD", repo=self.wt), head)
        denied = self.edit_spec()                            # e la spec è di nuovo bloccata
        self.assertEqual(denied.returncode, 2, denied.stdout + denied.stderr)


def db_row(conn):
    return conn.execute("SELECT * FROM work_items ORDER BY id DESC LIMIT 1").fetchone()


if __name__ == "__main__":
    unittest.main()
