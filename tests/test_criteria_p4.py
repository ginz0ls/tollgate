"""Criteri di accettazione di P4 dal programma vero (spec 15): il gate e `finish check` sullo
stesso albero, il blocco scritto da `open-pr` letto da `gate evaluate`, e i casi del criterio 10
con `bin/tollgate gate …` lanciato come processo su `GateLab`. Banchi con HOME, stato e gh finti;
nessuna rete."""
import contextlib
import dataclasses
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import (test_finishcheck, test_gate_evaluate, test_gate_github, test_gate_sentinel,
                   test_openpr)
from tests.flowkit import PLAN, plan_text
from tests.gatekit import BRANCH, DEFAULT_IDS, GATE_TOML, GateLab
from tests.helpers import BIN, git
from tests.hookkit import DEFAULT_FILES
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


PROGRAM = BIN / "tollgate"
SOMMA, ZERO = test_gate_evaluate.SOMMA, test_gate_evaluate.ZERO
DETECT_TOML = GATE_TOML.replace('mode = "protected"', 'mode = "detect"')
NEW_WF = ".github/workflows/nuovo.yml"
CI_WF = ".github/workflows/ci.yml"
ONLY_ZERO = '<testsuite><testcase classname="tests.test_app" name="test_zero"/></testsuite>'
ZERO_FAILS = ('<testsuite><testcase classname="tests.test_app" name="test_somma"/>'
              '<testcase classname="tests.test_app" name="test_zero"><failure/></testcase>'
              '</testsuite>')
ENTITY = ('<!DOCTYPE t [<!ENTITY e "x">]><testsuite><testcase classname="tests.test_app" '
          'name="test_somma"/>&e;</testsuite>')
MANUAL_PLAN = plan_text().replace("test: tests.test_app::test_somma", "test: manuale").replace(
    "test: tests.test_app::test_zero", "test: manuale")
GREEN, RED, ERROR = "success", "failure", "error"


class ProgramCase(test_gate_github.VerdictBase):
    """`bin/tollgate gate <sottocomando> … --publish` come processo, con `GITHUB_ACTIONS=true` e il
    `gh` finto dell'ambiente di `VerdictBase`; ogni caso ha il suo `GateLab` (`fresh`)."""

    def fresh(self, *, toml=GATE_TOML, files=None, plan=None, branch=None):
        self.lab = GateLab(toml=toml, files=files, plan=plan)
        self.addCleanup(self.lab.close)
        if branch:
            git(self.lab.repo, "checkout", "-q", "-b", branch, self.lab.base)
        return self.lab

    def program(self, *argv) -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": str(self.tmp)}
        return subprocess.run([sys.executable, "-B", str(PROGRAM), "gate", *argv],
                              cwd=self.lab.repo, env=env, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=120)

    def ready(self, *, ref=BRANCH, body=None, block=None, base="main", head_sha=None,
              issue=None, **artifacts):
        """La testa del ramo diventa la PR 1: spinta in `refs/pull/1/head`, artefatti di
        `tollgate-run` (`artifacts` va a `write_artifacts`) e risposte del `gh` finto."""
        self.sha = self.lab.head
        self.push_pr_head()
        self.write_artifacts(**artifacts)
        if body is None:
            body = f"Closes #7\n{prblock.render(block or self.lab.block())}"
        self.set_gh(pull=self.rest_pull(
            body=body, base={"ref": base},
            head={"sha": head_sha or self.sha, "ref": ref, "repo": {"full_name": SLUG}}),
            issue=issue)

    def evaluate(self, *, ids=DEFAULT_IDS, base="main") -> tuple[dict, str]:
        """`gate evaluate --publish` con gli identificativi `ids` della base in cache (`None`:
        né cache né artefatto). Dà `(contesto → stato, commento del verdetto o "")`."""
        args = ["evaluate", "--event", str(self.event(pull_requests=[
            {"number": 1, "base": {"ref": base, "sha": self.lab.base},
             "head": {"ref": BRANCH, "sha": self.sha}}])), "--artifacts", str(self.art)]
        if ids is not None:
            args += ["--base-ids-cache", str(self.ids_file(self.tmp / "cache", ids=ids))]
        r = self.program(*args, "--publish")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        bodies = [c["body"] for c in self.comments()]
        return ({k: v["state"] for k, v in self.statuses().items()},
                next((b for b in bodies if comment.marker_sha(b) == self.sha), ""))

    def guard(self, *, ref=BRANCH) -> tuple[str | None, str]:
        """`gate guard --publish` sull'evento `pull_request`: dà `(stato, commento di guard)`."""
        path = self.tmp / "pr-event.json"
        path.write_text(json.dumps({
            "action": "synchronize", "number": 1,
            "pull_request": {"number": 1, "body": "",
                             "head": {"sha": self.sha, "ref": ref, "repo": {"full_name": SLUG}},
                             "base": {"ref": "main"}},
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        r = self.program("guard", "--event", str(path), "--publish")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        state = self.statuses().get("tollgate/guard", {}).get("state")
        bodies = [c["body"] for c in self.comments() if c["body"].startswith(comment.GUARD_PREFIX)]
        return state, "".join(bodies)

    def sentinel(self, before: str, after: str) -> subprocess.CompletedProcess:
        path = self.tmp / "push-event.json"
        path.write_text(json.dumps({
            "ref": "refs/heads/main", "before": before, "after": after,
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        r = self.program("sentinel", "--event", str(path), "--publish")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def commit_waiver(self, *items, issue=7):
        self.lab.commit(f".tollgate/waivers/{issue}.toml",
                        test_gate_evaluate.wtext(*items, issue=issue), "deroga")

    def assert_judged(self, got, verdict_state, attention_state, *texts):
        (states, body) = got
        self.assertEqual((states.get(verdict.VERDICT), states.get(verdict.ATTENTION)),
                         (verdict_state, attention_state), body)
        for text in texts:
            self.assertIn(text, body)


class Criterion10Test(ProgramCase):
    """Criterio 10 dal programma vero: una sottoprova per riga che i test non coprono già da
    `bin/tollgate` (`tollgate.toml` cambiato → `guard` rosso è
    `test_gate_guard.CliTest.test_end_to_end_publish_in_actions`; lo stato pubblicato con un
    token personale in `protected` lo prova solo GitHub, nel rapporto del Task 16)."""

    def test_criterion_10_matrix(self):
        for name in [n for n in dir(self) if n.startswith("case_")]:
            with self.subTest(name[len("case_"):]):
                getattr(self, name)()

    # --- verdi ---------------------------------------------------------------------------

    def case_01_clean_pr(self):
        self.fresh().commit("src/app.py", "def somma(a, b):\n    return b + a\n")
        self.ready()
        self.assertEqual(self.guard()[0], GREEN)
        self.assert_judged(self.evaluate(), GREEN, GREEN, "Nessuna voce.")

    def case_02_config_branch(self):
        self.fresh(branch="tollgate-config/1").commit(
            "tollgate.toml", GATE_TOML + "[tasks]\ntask_lines_warn = 300\n")
        self.ready(ref="tollgate-config/1", body="")
        self.assertEqual(self.guard(ref="tollgate-config/1")[0], GREEN)
        self.assert_judged(self.evaluate(), GREEN, RED,
                           "PR di aggiornamento della configurazione di tollgate")

    def case_03_manual_branch(self):
        self.fresh(branch="fix/a-mano").commit("src/app.py", "x = 1\n")
        self.ready(ref="fix/a-mano", body="Una correzione fatta a mano.\n")
        self.assertEqual(self.guard(ref="fix/a-mano")[0], GREEN)
        self.assert_judged(self.evaluate(), GREEN, RED, "PR fuori dai rami tg/*")

    # --- verdict rosso -------------------------------------------------------------------

    def case_04_test_removed(self):
        self.fresh().delete("tests/test_app.py")
        self.ready()
        self.assert_judged(self.evaluate(), RED, GREEN, "file di test cancellato (test)")

    def case_05_skip_added(self):
        self.fresh().commit("tests/test_app.py", DEFAULT_FILES["tests/test_app.py"]
                            + "\n\nimport pytest\n\n\n@pytest.mark.skip\ndef test_tre():\n"
                              "    assert somma(1, 1) == 2\n")
        self.ready()
        self.assert_judged(self.evaluate(), RED, GREEN, "marcatori di salto aggiunti (test)")

    def case_06_out_of_scope(self):
        self.fresh().commit("src/stray.py", "x = 1\n")
        self.ready()
        self.assert_judged(self.evaluate(), RED, GREEN, "file fuori dallo scope del piano")

    def case_07_base_id_missing(self):
        self.fresh()
        self.ready(xml=ONLY_ZERO)
        self.assert_judged(self.evaluate(), RED, GREEN,
                           "1 test della base non sono eseguiti nella testa")

    def case_08_or_true_with_failing_test(self):
        """`"check": "vitest run || true"`: uscita 0 dichiarata verde, un test fallito nel
        report; il gate ricalcola dal JUnit."""
        self.fresh()
        self.ready(xml=ZERO_FAILS)
        self.assert_judged(self.evaluate(), RED, GREEN,
                           "il comando «verify» è rosso, 1 test falliti nel report")

    def case_09_level_below_minimum(self):
        self.fresh()
        self.ready(issue={"number": 7, "state": "OPEN", "labels": [{"name": "security"}]})
        self.assert_judged(self.evaluate(), RED, GREEN, "livello dichiarato L1 sotto il minimo L2")

    def case_10_l2_report_missing(self):
        lab = self.fresh()
        test_gate_evaluate.set_up_l2(lab, spec_reports=())
        self.ready(block=test_gate_evaluate.l2_block(lab))
        self.assert_judged(self.evaluate(), RED, GREEN,
                           "1 problema nei file di approvazione e nei report di L2")

    # --- deroghe -------------------------------------------------------------------------

    def case_11_waiver_of_another_issue(self):
        self.fresh().commit("src/stray.py", "x = 1\n")
        self.commit_waiver(("scope", "src/stray.py", None, []), issue=3)
        self.ready()
        self.assert_judged(self.evaluate(), RED, GREEN, "file fuori dallo scope del piano")

    def case_12_same_waiver_in_own_file(self):
        """Controprova dell'11: la stessa deroga nel file dell'issue della PR scioglie."""
        self.fresh().commit("src/stray.py", "x = 1\n")
        self.commit_waiver(("scope", "src/stray.py", None, []))
        self.ready()
        self.assert_judged(self.evaluate(), GREEN, GREEN, "deroga w-7-1 (scope)")

    # --- tollgate/sentinel rosso e issue aperta ------------------------------------------

    def case_13_direct_push(self):
        lab = self.fresh()
        start, pushed = lab.head, lab.commit("src/diretto.py", "x = 1\n")
        self.data.write_text(json.dumps({"commit_pulls": {}, "commit_statuses": {},
                                         "open_issues": []}))
        self.sentinel(start, pushed)
        self.assert_sentinel_red(pushed)

    def case_14_merge_of_red_verdict_in_detect(self):
        lab = self.fresh(toml=DETECT_TOML)
        start, merge = lab.head, lab.commit("src/merge.py", "x = 1\n")
        status = test_gate_sentinel.status
        self.data.write_text(json.dumps({
            "commit_pulls": {merge: [test_gate_sentinel.merged()]},
            "commit_statuses": {test_gate_sentinel.PR_HEAD: [
                status("tollgate/verdict", "failure"), status("tollgate/guard", "success")]},
            "open_issues": []}))
        self.sentinel(start, merge)
        self.assert_sentinel_red(merge)

    def assert_sentinel_red(self, sha):
        got = self.gh_data()
        self.assertEqual([r["state"] for r in got["commit_statuses"][sha]
                          if r["context"] == "tollgate/sentinel"], [RED])
        [issue] = got["open_issues"]
        self.assertEqual(issue["title"], test_gate_sentinel.ghcli.SENTINEL_TITLE)
        self.assertIn(sha, issue["body"])

    # --- guard rosso ---------------------------------------------------------------------

    def case_15_verdict_workflow_outside_config_branch(self):
        self.fresh().commit(".github/workflows/tollgate-verdict.yml", "on: push\n")
        self.ready()
        state, body = self.guard()
        self.assertEqual(state, RED)
        self.assertIn("tollgate-verdict.yml", body)

    def case_16_project_workflows(self):
        cases = {
            "statuses: write": "on: pull_request\npermissions:\n  statuses: write\njobs: {}\n",
            "checks: write": "on: pull_request\npermissions:\n  checks: write\njobs: {}\n",
            "pull_request_target": "on: pull_request_target\npermissions:\n  contents: read\n"
                                   "jobs: {}\n",
            "workflow_run": "on:\n  workflow_run:\n    workflows: [ci]\npermissions:\n"
                            "  contents: read\njobs: {}\n",
            "senza permissions": "on: pull_request\njobs: {}\n"}
        for name, text in cases.items():
            with self.subTest(name):
                self.fresh().commit(NEW_WF, text)
                self.ready()
                state, body = self.guard()
                self.assertEqual(state, RED, name)
                self.assertIn(NEW_WF, body)

    # --- verde con attenzione ------------------------------------------------------------

    def case_17_project_workflow_with_ci_waiver(self):
        ok = "on: pull_request\npermissions:\n  contents: read\njobs: {}\n"
        lab = self.fresh(files={**DEFAULT_FILES, CI_WF: ok},
                         plan=plan_text(task2=f"- Modify: `{CI_WF}`"))
        lab.commit(CI_WF, ok.replace("jobs: {}", "jobs:\n  t:\n    runs-on: ubuntu-latest"))
        self.commit_waiver(("ci", CI_WF, None, []))
        self.ready()
        self.assertEqual(self.guard()[0], GREEN)
        self.assert_judged(self.evaluate(), GREEN, RED,
                           "workflow del progetto modificati con una deroga ci: 1")

    # --- attenzione rosso ----------------------------------------------------------------

    def case_18_test_waiver(self):
        self.fresh()
        self.commit_waiver(("test", "tests/test_app.py", None, [SOMMA]))
        self.ready()
        self.assert_judged(self.evaluate(), GREEN, RED, "deroga w-7-1 (test)")

    def case_19_plan_changed(self):
        self.fresh().commit(PLAN, plan_text() + "\nUna riga in più.\n", "piano ritoccato")
        self.ready()
        self.assert_judged(self.evaluate(), GREEN, RED,
                           "il piano in testa è diverso da quello registrato",
                           "+Una riga in più.")

    def case_20_level_cap(self):
        lab = self.fresh()
        self.ready(block=lab.block(level_cap="L1", level_cap_reason="solo documenti"))
        self.assert_judged(self.evaluate(), GREEN, RED, "tetto di livello dichiarato (L1)")

    def case_21_allow_no_tests_with_zero_tests(self):
        self.fresh(toml=test_gate_evaluate.ALLOW_NO_TESTS_TOML, plan=MANUAL_PLAN)
        self.ready(xml="<testsuite/>", commands=[
            {"name": "verify", "state": "empty", "exit": 0, "tests_run": 0, "tests_skipped": 0,
             "report": "junit/0.xml"}])
        self.assert_judged(self.evaluate(ids=()), GREEN, RED,
                           "il comando «verify» (empty) vale verde solo per allow_no_tests")

    # --- error ---------------------------------------------------------------------------

    def case_22_dotdot_in_artifact(self):
        self.fresh()
        self.ready(report="../fuori.xml")
        self.assert_judged(self.evaluate(), ERROR, ERROR)
        self.assertEqual(self.statuses()[verdict.VERDICT]["description"],
                         verdict.DESC_ARTIFACTS)

    def case_23_xml_entity(self):
        self.fresh()
        self.ready(xml=ENTITY)
        self.assert_judged(self.evaluate(), ERROR, ERROR)
        self.assertEqual(self.statuses()[verdict.VERDICT]["description"],
                         verdict.DESC_ARTIFACTS)

    def case_24_superseded_sha(self):
        self.fresh()
        self.ready(head_sha="f" * 40)
        self.assert_judged(self.evaluate(), ERROR, ERROR)
        self.assertIn("SHA superato", self.statuses()[verdict.VERDICT]["description"])

    # --- non applicabile -----------------------------------------------------------------

    def case_25_pr_to_another_branch(self):
        self.fresh()
        self.ready(base="release")
        states, _ = self.evaluate(base="release")
        self.assertEqual(states, {})
        [body] = [c["body"] for c in self.comments()]
        self.assertTrue(body.startswith(verdict.NA_PREFIX))
        self.assertIn("La PR non punta al ramo predefinito: non applicabile.", body)


class GroupsTest(ProgramCase):
    def test_criterion_44_groups_end_to_end(self):
        """Criterio 44: sola deroga `scope` entro la seconda → `attenzione` verde con la nota;
        con una deroga `test` → rosso, e la deroga `test` in cima al gruppo «da leggere»."""
        self.fresh().commit("src/stray.py", "x = 1\n")
        self.commit_waiver(("scope", "src/stray.py", None, []))
        self.ready()
        states, body = self.evaluate()
        self.assert_judged((states, body), GREEN, GREEN, "Informative (1)", "deroga w-7-1 (scope)")
        self.assertEqual(self.statuses()[verdict.ATTENTION]["description"],
                         verdict.DESC_ATTENTION_OK)
        self.assertNotIn("### Da leggere", body)

        self.fresh().commit("src/stray.py", "x = 1\n")
        self.commit_waiver(("scope", "src/stray.py", None, []),
                           ("test", "tests/test_app.py", None, [SOMMA]))
        self.ready()
        states, body = self.evaluate()
        self.assert_judged((states, body), GREEN, RED)
        read = body.split("### Da leggere\n\n", 1)[1]
        self.assertTrue(read.startswith("- deroga w-7-2 (test)"), body)
        self.assertLess(body.index("deroga w-7-2 (test)"), body.index("<details>"))
        self.assertGreater(body.index("deroga w-7-1 (scope)"), body.index("<details>"))


class ComponentsInGateTest(ProgramCase):
    def test_criterion_35_gate(self):
        """Criterio 35 nel gate: `spec_audit = false` e tre fette, approvazione con `lens: off`
        → `attenzione` rosso, non `verdict` rosso."""
        lab = self.fresh(toml=GATE_TOML + "[components]\nspec_audit = false\n")
        test_gate_evaluate.set_up_l2(lab, slices=3, lens="off")
        self.ready(block=test_gate_evaluate.l2_block(
            lab, spec_audit={"adversarial": "closed", "lens": "off"}))
        self.assert_judged(self.evaluate(), GREEN, RED, "audit della spec spento: lenti",
                           "componenti spenti sul ramo predefinito: spec_audit")

    def test_components_in_gate(self):
        """Criterio 18 nel gate: `definition_of_done`, `base_test_ids` e `sentinel` a `false`
        spengono il loro controllo, con `components_off` («da leggere»)."""
        dod = {"dod": {"L": "L1", "items": {"receipt": True, "tasks_approved": False}},
               "findings": [test_gate_evaluate.finding()]}
        with self.subTest("definition_of_done acceso"):
            lab = self.fresh()
            self.ready(block=lab.block(**dod))
            self.assert_judged(self.evaluate(), RED, GREEN, "1 voci della DoD dichiarate false")
        with self.subTest("definition_of_done spento"):
            lab = self.fresh(toml=GATE_TOML + "[components]\ndefinition_of_done = false\n")
            self.ready(block=lab.block(**dod))
            self.assert_judged(self.evaluate(), GREEN, RED,
                               "componenti spenti sul ramo predefinito: definition_of_done")
        with self.subTest("base_test_ids acceso, senza identificativi"):
            self.fresh()
            self.ready()
            self.assert_judged(self.evaluate(ids=None), ERROR, ERROR)
        with self.subTest("base_test_ids spento"):
            self.fresh(toml=GATE_TOML + "[components]\nbase_test_ids = false\n")
            self.ready()
            self.assert_judged(self.evaluate(ids=None), GREEN, RED,
                               "componenti spenti sul ramo predefinito: base_test_ids")
        with self.subTest("sentinel spento"):
            lab = self.fresh(toml=GATE_TOML + "[components]\nsentinel = false\n")
            start, pushed = lab.head, lab.commit("src/diretto.py", "x = 1\n")
            self.data.write_text(json.dumps({"commit_pulls": {}, "commit_statuses": {},
                                             "open_issues": []}))
            self.log.unlink(missing_ok=True)
            r = self.sentinel(start, pushed)
            self.assertIn("components.sentinel = false", r.stdout)
            self.assertEqual(self.calls(), [])
            self.assertEqual(self.gh_data()["open_issues"], [])


if __name__ == "__main__":
    unittest.main()
