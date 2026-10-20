"""Criteri di accettazione di P3b dal programma vero (spec 15): hooks/run e bin/tollgate come li
lancia Claude Code, su un repo temporaneo con HOME, stato e gh finti (FlowLab). I subagenti non
si lanciano: i loro eventi (SubagentStart, SubagentStop) e i loro verdetti li scrive il test."""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from tests.flowkit import PLAN, SESSION, FlowLab, plan_text
from tests.helpers import BIN, ROOT
from tests.hookkit import sample
from tests.test_openpr import BOTH_OK, BRANCH, ISSUES, SOMMA, TOML
from tollgate_analysis import prblock
from tollgate_core import clock, db, paths, phases, reviews, sessions, tasks

RUN = ROOT / "hooks" / "run"
REVIEWER = "tollgate:final-reviewer"
VERIFIER = "tollgate:finding-verifier"
MINOR = {"rule": "R-1", "file": "src/app.py", "line": 2, "severity": "minor",
         "text": "nome poco chiaro"}
MAJOR = {"rule": "R-1", "file": "src/app.py", "line": 2, "severity": "major",
         "text": "manca il caso zero"}
NO_RULE = {"file": "src/app.py", "line": 1, "severity": "major", "text": "sensazione"}


def hook(lab, event, payload):
    return subprocess.run([str(RUN), event], input=json.dumps(payload), capture_output=True,
                          text=True, env=lab.env(), timeout=60)


class FinishCase(unittest.TestCase):
    """Lavoro L1 in `execution` con il piano registrato, i task chiusi, il codice committato e
    il finto gh senza PR: tutto ciò che precede `/tollgate:finish`."""

    def setUp(self):
        fl = FlowLab(issue=7, phase="plan", toml=TOML)
        self.addCleanup(fl.close)
        self.fl, self.wt = fl, fl.wt
        fl.register_plan(tasks=1)
        fl.commit(PLAN, plan_text(tasks=1), "piano")
        fl.commit("tests/ids.txt", BOTH_OK, "ids")
        fl.commit("src/app.py", SOMMA, "somma")
        fl.close_tasks()
        fl.set_gh(prs=[], issues=ISSUES)
        self.n_agents = 0

    # --- eventi di Claude Code, attraverso hooks/run -------------------------------------
    def event(self, event, name, **changes):
        base = dict(session_id=SESSION, cwd=str(self.wt))
        base.update(changes)
        r = hook(self.fl, event, sample(name, **base))
        self.assertEqual((r.returncode, r.stderr), (0, ""), r.stdout)
        return r

    def slash(self, name, args=""):
        return self.event("UserPromptExpansion", "UserPromptExpansion-none",
                          command_name=f"tollgate:{name}", command_args=args,
                          prompt=f"/tollgate:{name} {args}".strip())

    def cli(self, *argv, cwd=None):
        """Come lo lancia il modello: prima PreToolUse Bash (che scrive il segnale), poi il
        programma, senza riscrivere il segnale."""
        cwd = cwd or self.wt
        command = f"{paths.program_command(BIN / 'tollgate')} {' '.join(argv)}"
        r = hook(self.fl, "PreToolUse", sample("PreToolUse-Bash", session_id=SESSION,
                                               cwd=str(cwd), tool_input={"command": command}))
        self.assertEqual((r.returncode, r.stderr), (0, ""), r.stdout)
        return subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), *argv], cwd=str(cwd),
                              env=self.fl.env(), capture_output=True, text=True, timeout=120)

    def agent(self, atype, text):
        """Il subagente parte e si ferma con `text` come ultimo messaggio."""
        self.n_agents += 1
        aid = f"ag-{self.n_agents}"
        self.event("SubagentStart", "SubagentStart-none", agent_id=aid, agent_type=atype)
        self.event("SubagentStop", "SubagentStop-manual-normal", agent_id=aid, agent_type=atype,
                   last_assistant_message=text, agent_transcript_path="/non/esiste.jsonl")
        return aid

    # --- lettura dello stato -------------------------------------------------------------
    def work(self):
        return phases.get_work(self.fl.conn, self.fl.work)

    def cycle(self, number=None):
        if number is None:
            return reviews.latest(self.fl.conn, self.fl.work)
        return self.fl.conn.execute("SELECT * FROM review_cycles WHERE work = ? AND number = ?",
                                    (self.fl.work, number)).fetchone()

    def acts(self, type_):
        return [r["state"] for r in self.fl.conn.execute(
            "SELECT state FROM acts WHERE type = ? ORDER BY n", (type_,))]

    # --- i passi della chiusura ----------------------------------------------------------
    def finish_check(self):
        self.slash("finish")
        self.assertEqual(self.acts("finish"), ["pending"])
        r = self.cli("finish", "check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.work()["phase"], "review")
        return r

    def prepare(self):
        r = self.cli("review", "prepare")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def review(self, findings, outcome="needs_fix"):
        """Il revisore finale riporta `findings`; poi il verificatore li conferma tutti."""
        r = self.prepare()
        self.assertIn(f"agente: {REVIEWER} brief:", r.stdout)
        c = self.cycle()
        verdict = {"v": 1, "sha": c["sha"], "code": c["code"], "outcome": outcome,
                   "findings": findings}
        self.agent(REVIEWER, "Verdetto.\n```json\n" + json.dumps(verdict) + "\n```")
        self.assertEqual(self.cycle()["stage"], "verify")
        r = self.prepare()
        self.assertIn(f"agente: {VERIFIER} brief:", r.stdout)
        ids = reviews.unjudged_ids(self.fl.conn, self.fl.work, c["number"])
        results = {"v": 1, "sha": c["sha"], "code": c["code"],
                   "results": [{"id": i, "verification": "confirmed", "reason": "visto"}
                               for i in ids]}
        self.agent(VERIFIER, "Esiti.\n```json\n" + json.dumps(results) + "\n```")
        return c["number"]

    def open_pr(self):
        r = self.cli("finish", "open-pr")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def to_pr_open(self):
        """Dalla fase `execution` alla PR aperta, con un ciclo `ok` (un rilievo minore)."""
        self.finish_check()
        self.review([MINOR, NO_RULE], outcome="ok")
        self.assertEqual(self.cycle()["outcome"], "ok")
        self.open_pr()
        self.assertEqual(self.work()["phase"], "pr_open")


class FinishToPrEndToEndTest(FinishCase):
    def test_finish_to_pr_end_to_end(self):                      # criteri 9, 12, 40, 41
        self.finish_check()
        wt_head = self.fl.git("rev-parse", "HEAD", repo=self.wt)
        self.assertEqual(self.work()["finish_sha"], wt_head)

        r = self.prepare()                                       # revisore finale
        c = self.cycle()
        self.assertEqual((c["number"], c["stage"], c["sha"]), (1, "review", wt_head))
        self.assertIn(f'agente: {REVIEWER} brief: "{self.wt / ".tollgate-run" / "7"}', r.stdout)
        self.assertIn(c["code"], (self.wt / ".tollgate-run" / "7" / "final-1.md").read_text())
        verdict = {"v": 1, "sha": c["sha"], "code": c["code"], "outcome": "ok",
                   "findings": [MINOR, NO_RULE]}
        self.agent(REVIEWER, "Verdetto.\n```json\n" + json.dumps(verdict) + "\n```")

        self.assertEqual(self.cycle()["stage"], "verify")        # criterio 40: lo scarto per forma
        by_id = {x["id"]: x for x in self.fl.conn.execute(
            "SELECT * FROM findings WHERE work = ? ORDER BY rowid", (self.fl.work,))}
        self.assertEqual(sorted(x["verification"] or "-" for x in by_id.values()),
                         ["-", "rejected"])
        rejected = next(x for x in by_id.values() if x["verification"] == "rejected")
        self.assertEqual(rejected["text"], NO_RULE["text"])

        r = self.prepare()                                       # verificatore
        self.assertIn(f"agente: {VERIFIER} brief:", r.stdout)
        ids = reviews.unjudged_ids(self.fl.conn, self.fl.work, 1)
        self.assertEqual(len(ids), 1)
        results = {"v": 1, "sha": c["sha"], "code": c["code"],
                   "results": [{"id": ids[0], "verification": "confirmed", "reason": "visto"}]}
        self.agent(VERIFIER, "Esiti.\n```json\n" + json.dumps(results) + "\n```")
        self.assertEqual((self.cycle()["stage"], self.cycle()["outcome"]), ("closed", "ok"))
        self.assertEqual(self.work()["phase"], "review")

        r = self.prepare()
        self.assertIn("finish open-pr", r.stdout.strip().splitlines()[-1])

        r = self.open_pr()                                       # criterio 12
        self.assertEqual(self.acts("finish"), ["consumed"])
        with self.assertRaises(sessions.CliSessionError):        # il segnale è stato consumato
            sessions.cli_session(self.fl.ts.state, self.wt, "finish", argv=["finish", "open-pr"],
                                 now=clock.now())
        w = self.work()
        self.assertEqual((w["phase"], w["pr_number"]), ("pr_open", 1))
        (opened,) = json.loads(self.fl.gh_data.read_text())["prs"]
        self.assertEqual((opened["headRefName"], opened["state"]), (BRANCH, "OPEN"))
        self.assertEqual(self.fl.git("rev-parse", f"refs/heads/{BRANCH}", repo=self.fl.origin),
                         wt_head)
        block = prblock.parse(opened["body"])
        self.assertEqual(block["verdict"]["outcome"], "ok")
        self.assertEqual((block["issue"], block["head_sha"]), (7, wt_head))
        self.assertEqual(block["verdict"]["cycles"], 1)
        self.assertEqual(self.fl.events("pr_opened")[-1]["pr"], 1)


class NeedsFixTest(FinishCase):
    def prepare_needs_fix_cycle(self):
        """Dal lavoro in `execution` al ciclo 1 chiuso `needs_fix` con un rilievo maggiore
        confermato (fase di nuovo `execution`). Dà il numero del ciclo."""
        self.finish_check()
        n = self.review([MAJOR])
        c = self.cycle(n)
        self.assertEqual((c["stage"], c["outcome"], c["counted"]), ("closed", "needs_fix", 1))
        self.assertEqual(self.work()["phase"], "execution")
        return n

    def test_needs_fix_then_from_findings_consumes_cycle(self):  # criteri 26 e 37
        n = self.prepare_needs_fix_cycle()
        self.assertEqual(reviews.counted(self.fl.conn, self.fl.work), 1)
        self.slash("finish")
        r = self.cli("finish", "open-pr")                        # criterio 26: rifiuto, non errore
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        lines = (r.stdout + r.stderr).splitlines()
        self.assertTrue(lines[0].startswith("rifiuto: la fase è execution"), lines)
        self.assertTrue(all(l.startswith("rifiuto:") for l in lines), lines)
        self.assertIn("Nessun rilievo blocker o major confermato", r.stdout + r.stderr)
        self.assertEqual(self.work()["phase"], "execution")

        r = self.cli("task", "start", "--from-findings", str(n))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        row = tasks.get_task(self.fl.conn, self.fl.work, 2)
        self.assertEqual((row["kind"], row["source"], row["state"]), ("fix", "cycle:1", "running"))
        self.assertIn("manca il caso zero", (self.wt / ".tollgate-run" / "7" / "task-2.md")
                      .read_text())
        self.assertEqual(self.work()["phase"], "execution")
        again = self.cli("task", "start", "--from-findings", str(n))      # un solo task per ciclo
        self.assertEqual(again.returncode, 1, again.stdout)
        self.assertEqual(reviews.counted(self.fl.conn, self.fl.work), 1)
        self.assertEqual(reviews.count(self.fl.conn, self.fl.work), 1)

    def test_second_finish_is_new_cycle(self):                   # criteri 26 e 28, dal programma
        n = self.prepare_needs_fix_cycle()
        r = self.cli("task", "start", "--from-findings", str(n))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        old_head = self.fl.git("rev-parse", "HEAD", repo=self.wt)
        self.fl.commit("src/app.py", SOMMA + "# corretto il caso zero\n", "correzione")
        self.fl.close_tasks()                                    # il task di correzione è chiuso
        self.slash("finish")                                     # il secondo `finish`
        r = self.cli("finish", "check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.work()["phase"], "review")
        self.assertNotEqual(self.work()["finish_sha"], old_head)

        self.review([MINOR, NO_RULE], outcome="ok")              # ciclo 2: nuovo, non il 1
        c = self.cycle()
        self.assertEqual((c["number"], c["stage"], c["outcome"]), (2, "closed", "ok"))
        self.assertEqual(self.cycle(1)["outcome"], "needs_fix")
        self.assertEqual(reviews.count(self.fl.conn, self.fl.work), 2)
        self.open_pr()                                           # open-pr dà 0
        w = self.work()
        self.assertEqual((w["phase"], w["pr_number"]), ("pr_open", 1))
        (opened,) = json.loads(self.fl.gh_data.read_text())["prs"]
        self.assertEqual(prblock.parse(opened["body"])["verdict"]["outcome"], "ok")


class SyncTest(FinishCase):
    def test_sync_after_default_advanced(self):                  # criterio 16
        self.to_pr_open()
        self.fl.git("config", "user.name", "t")
        self.fl.git("config", "user.email", "t@example.com")
        old_head = self.fl.git("rev-parse", "HEAD", repo=self.wt)
        (self.fl.main / "docs").mkdir(exist_ok=True)
        (self.fl.main / "docs" / "nuovo.md").write_text("nuovo\n")
        self.fl.git("add", "--", "docs/nuovo.md")
        self.fl.git("commit", "-qm", "avanza")
        self.fl.git("push", "-q", "origin", "main")
        tip = self.fl.git("rev-parse", "HEAD")

        self.slash("sync")
        self.assertEqual(self.acts("sync"), ["pending"])
        r = self.cli("sync")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        new_head = self.fl.git("rev-parse", "HEAD", repo=self.wt)
        self.assertNotEqual(new_head, old_head)
        self.assertEqual(self.fl.git("merge-base", "HEAD", "origin/main", repo=self.wt), tip)
        w = self.work()
        self.assertEqual((w["phase"], w["work_base_sha"]), ("pr_open", tip))
        self.assertEqual(self.fl.git("rev-parse", f"refs/heads/{BRANCH}", repo=self.fl.origin),
                         new_head)
        (pr,) = json.loads(self.fl.gh_data.read_text())["prs"]
        self.assertEqual(prblock.parse(pr["body"])["head_sha"], new_head)
        self.assertEqual(self.acts("sync"), ["consumed"])
        self.assertEqual(reviews.count(self.fl.conn, self.fl.work), 1)   # stesso patch-id
        self.assertEqual(self.fl.events("base_realigned")[-1]["to"], tip)
        self.assertEqual(self.fl.events("pr_updated")[-1]["sha"], new_head)


class AdoptTest(FinishCase):
    def test_adopt_after_db_lost(self):                          # criterio 17
        self.to_pr_open()
        head = self.fl.git("rev-parse", "HEAD", repo=self.wt)
        self.fl.conn.close()
        state = self.fl.ts.state
        shutil.move(str(state.db_path), str(state.db_path) + ".perso")
        for extra in ("-wal", "-shm"):
            Path(str(state.db_path) + extra).unlink(missing_ok=True)
        self.fl.lab.conn = self.fl.conn = db.open_db(state)      # DB nuovo e vuoto (lo chiude Lab.close)
        self.assertEqual(self.fl.conn.execute("SELECT count(*) FROM work_items")
                         .fetchone()[0], 0)

        self.slash("adopt", "#7")
        self.assertEqual(self.acts("adopt"), ["pending"])
        r = self.cli("adopt", "7")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (row,) = [dict(x) for x in self.fl.conn.execute("SELECT * FROM work_items")]
        self.assertEqual((row["issue"], row["level"], row["phase"], row["branch"]),
                         (7, "L1", "pr_open", BRANCH))
        self.assertEqual(row["pr_number"], 1)
        self.assertEqual(Path(row["worktree"]), self.wt.resolve())
        self.assertEqual(self.acts("adopt"), ["consumed"])
        self.assertIn("prossimo passo: EnterWorktree", r.stdout)
        self.assertEqual(self.fl.git("rev-parse", "HEAD", repo=self.wt), head)


if __name__ == "__main__":
    unittest.main()
