"""Criteri di accettazione di P4 dal programma vero (spec 15): il gate e `finish check` sullo
stesso albero, il blocco scritto da `open-pr` letto da `gate evaluate`. Banchi `FlowLab` con HOME,
stato e gh finti; nessuna rete."""
import contextlib
import dataclasses
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import test_finishcheck, test_openpr
from tests.flowkit import PLAN, plan_text
from tests.helpers import git
from tollgate_analysis import prblock
from tollgate_core import git as core_git, phases, reviews, tasks
from tollgate_flow import finishcheck
from tollgate_gate import comment, evaluate, verdict
from tollgate_gate.model import GITHUB, PrFacts

COMPARED = ("diff", "l2", "must_have", "level")
SLUG = "o/r"
XML = ('<testsuite><testcase classname="tests.test_app" name="test_somma"/>'
       '<testcase classname="tests.test_app" name="test_zero"/></testsuite>')


class AgreementTest(test_finishcheck.FinishCheckCase):
    """Review Focus 1 (decisioni 3, 9, 10, 20): lo stesso albero dà le stesse voci rosse da
    `finish check` e da `gate evaluate` nelle famiglie condivise."""

    def bench(self, *, plan_changed=False):
        """L2 in execution con la spec approvata, un file fuori scope e un test cancellato."""
        fl = test_finishcheck.L2ApprovalsTest.l2_lab(self)
        fl.commit("src/extra.py", "x = 1\n", "fuori scope")
        fl.git("rm", "-q", "tests/test_app.py", repo=fl.wt)
        fl.git("commit", "-qm", "cancella un test", repo=fl.wt)
        if plan_changed:
            fl.commit(PLAN, plan_text(tasks=1) + "\nUna riga in più.\n", "piano ritoccato")
            fl.approve_plan_file()
        return fl

    def both(self, fl):
        """`finish check` dal programma vero (esito e uscita) e, sugli stessi ingressi, il
        calcolo con `where="github"`. Dà `(esito locale, voci locali, voci del gate)`."""
        real = fl.cli("finish", "check", cwd=fl.wt)
        self.assertEqual(real.returncode, 1, real.stdout + real.stderr)
        seen = []
        original = evaluate.evaluate

        def spy(inputs):
            result = original(inputs)
            seen.append((inputs, result))
            return result

        with mock.patch.object(evaluate, "evaluate", spy):
            local = self.check(fl)
        self.assertEqual(local.code, finishcheck.RED, local.lines)
        (inputs, local_ev), = seen
        body = f"Closes #7\n{prblock.render(inputs.block)}"
        branch = phases.get_work(fl.conn, fl.work)["branch"]
        pr = PrFacts(1, inputs.head_sha, branch, "main", "main", body, False)
        gate_ev = evaluate.evaluate(dataclasses.replace(
            inputs, where=GITHUB, pr=pr, base_ids={}, base_ids_source="cache"))
        return real, local_ev, gate_ev

    def keys(self, ev):
        return {i.key for i in ev.red if i.family in COMPARED}

    def test_finish_check_and_gate_agree(self):
        fl = self.bench()
        real, local, gate = self.both(fl)
        self.assertEqual(self.keys(local), self.keys(gate))
        self.assertTrue({"out_of_scope"} < self.keys(gate), self.keys(gate))
        self.assertGreater(len(self.keys(gate)), 1)       # anche il test cancellato
        self.assertIn("src/extra.py", real.stdout)
        self.assertEqual({i.key for i in gate.red if i.family == "l2"}, set())

    def test_plan_change_is_the_only_difference(self):
        """Decisione 9: il piano cambiato dopo la registrazione, senza file nuovi, è una
        violazione in locale e `plan_changed` («da leggere») nel gate."""
        fl = self.bench(plan_changed=True)
        _, local, gate = self.both(fl)

        def diff_items(ev):
            return {(i.key, i.data.partition("\n")[0]) for i in ev.red if i.family == "diff"}

        self.assertEqual(diff_items(local) - diff_items(gate), {("out_of_scope", PLAN)})
        self.assertEqual(diff_items(gate) - diff_items(local), set())
        for family in COMPARED[1:]:
            self.assertEqual({i.key for i in local.red if i.family == family},
                             {i.key for i in gate.red if i.family == family})
        self.assertIn("plan_changed", [i.key for i in gate.attention])
        self.assertNotIn("plan_changed", [i.key for i in local.attention])


class BlockFeedsGateTest(test_openpr.OpenCase):
    """Review Focus 2: i campi nuovi del blocco 18.1 scritto da `open-pr` arrivano a `gate
    evaluate`: lo stesso corpo, letto dal gate sulla stessa testa."""
    MAJOR = {"severity": "major", "confidence": 0.9, "file": "src/app.py", "line": 2,
             "rule": "R-1", "text": "nota"}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate block gate "))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def opened(self):
        toml = test_openpr.TOML + ("[tasks]\ntask_lines_warn = 1\ntask_lines_max = 1\n"
                                   "[components]\nbase_test_ids = false\n")
        fl = self.lab(toml=toml, cycle=None, finish_act=False)
        tasks.add_commit(fl.conn, fl.work, 1, test_openpr.head(fl))
        for kind, data in (("subagent_stop", {"id": "a1", "type": "tollgate:implementer",
                                             "task": 1, "declared_status": "DONE", "tokens": 1,
                                             "state": "done", "size_reason": "generato"}),
                           ("skills_absent", {"task": 1, "skills": ["ghost-skill"]})):
            test_openpr.events.record_event(fl.conn, kind, data, now=fl.now, work=fl.work)
        base = test_openpr.work(fl)["work_base_sha"]
        n = reviews.open_cycle(fl.conn, fl.work, sha=test_openpr.head(fl),
                               patch_id=core_git.patch_id(fl.wt, base, test_openpr.head(fl)),
                               code="c1", reviewers=[test_openpr.REVIEWER], now=fl.now)
        reviews.add_report(fl.conn, fl.work, n, source=test_openpr.REVIEWER, outcome="ok",
                           findings=[self.MAJOR], rejected=[], blocking_rules=set(),
                           known_rules={"R-1"}, now=fl.now)
        rows = reviews.to_verify(fl.conn, fl.work, n, max_findings=15, now=fl.now)
        reviews.apply_verification(fl.conn, fl.work, n, [
            {"id": r["id"], "verification": "confirmed", "reason": "ok"} for r in rows],
            now=fl.now)
        reviews.close_cycle(fl.conn, fl.ts.state, fl.work, n, now=fl.now)
        self.finish_act(fl, at=fl.now + test_openpr.timedelta(seconds=1))
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        return fl

    def judge(self, fl, body):
        """`gate evaluate` sulla PR 1 con `body`: dà gli stati e il commento scritti."""
        head, repo = test_openpr.head(fl), fl.wt
        git(repo, "push", "-q", "-f", "origin", f"{head}:refs/pull/1/head")
        branch = test_openpr.BRANCH
        data = json.loads(fl.gh_data.read_text())
        data["prs"][0]["comments"] = []
        data.update(
            pulls={"1": {"number": 1, "state": "open", "body": body,
                         "head": {"sha": head, "ref": branch, "repo": {"full_name": SLUG}},
                         "base": {"ref": "main"}}},
            issues={"7": {"number": 7, "state": "OPEN", "labels": []}},
            open_issues=[], commit_pulls={}, commit_statuses={})
        fl.gh_data.write_text(json.dumps(data))
        art = self.tmp / "art"
        shutil.rmtree(art, ignore_errors=True)
        (art / "junit").mkdir(parents=True)
        (art / "junit" / "0.xml").write_text(XML)
        (art / "results.json").write_text(json.dumps({
            "v": 1, "applicable": True, "sha": head, "config_sha": git(repo, "rev-parse",
                                                                      "origin/main"),
            "commands": [{"name": "verify", "state": "green", "exit": 0, "tests_run": 2,
                          "tests_skipped": 0, "report": "junit/0.xml"}]}))
        event = self.tmp / "event.json"
        event.write_text(json.dumps({
            "workflow_run": {
                "path": ".github/workflows/tollgate-run.yml", "event": "pull_request",
                "head_sha": head, "head_branch": branch, "conclusion": "success", "id": 99,
                "pull_requests": [{"number": 1, "base": {"ref": "main", "sha": fl.base},
                                   "head": {"ref": branch, "sha": head}}]},
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        with mock.patch.dict(os.environ, {"GITHUB_REPOSITORY": SLUG}), \
                contextlib.redirect_stdout(io.StringIO()):
            code = verdict.main(event, artifacts=art, base_ids_cache=None,
                                base_ids_artifact=None, publish=True, environ=os.environ,
                                repo=repo)
        self.assertEqual(code, 0)
        got = json.loads(fl.gh_data.read_text())
        statuses = {r["context"]: r["state"] for r in reversed(got["commit_statuses"][head])}
        [posted] = got["prs"][0]["comments"]
        self.assertEqual(comment.marker_sha(posted["body"]), head)
        return statuses, posted["body"]

    def test_open_pr_block_feeds_gate(self):
        fl = self.opened()
        body = self.prs(fl)[0]["body"]
        block = prblock.parse(body)
        self.assertEqual([f["blocking"] for f in block["findings"]], [False])
        self.assertEqual(block["tasks_over"], [{"task": 1, "lines": 2, "size_reason": "generato"}])
        self.assertEqual(block["skills_absent"], [{"task": 1, "skills": ["ghost-skill"]}])
        statuses, text = self.judge(fl, body)
        # il rilievo non bloccante non ferma la PR; il task oltre il tetto porta il suo motivo
        self.assertEqual(statuses["tollgate/verdict"], "success", text)
        self.assertIn("generato", text)
        self.assertIn("ghost-skill", text)
        self.assertNotIn("rilievi bloccanti", text)
        # senza il campo `blocking` il gate non lo sa: l'ultimo blocco del corpo vince
        for f in block["findings"]:
            del f["blocking"]
        statuses, text = self.judge(fl, body + "\n" + prblock.render(block))
        self.assertEqual(statuses["tollgate/verdict"], "failure", text)
        self.assertIn("rilievi bloccanti", text)


if __name__ == "__main__":
    unittest.main()
