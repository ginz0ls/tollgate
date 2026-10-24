import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from tests import test_gate_github
from tests.flowkit import FAKEGH
from tests.gatekit import BRANCH, GateLab
from tests.helpers import BIN, TempState, git
from tests.hookkit import DEFAULT_FILES
from tollgate_core import ghcli
from tollgate_core.git import GitError
from tollgate_gate import cli, comment, github, guard
from tollgate_gate.model import IssueFacts, PrFacts

SLUG = "o/r"
OK_WF = "on: pull_request\npermissions:\n  contents: read\njobs:\n  t:\n    runs-on: ubuntu-latest\n"
WF_BODY = "jobs:\n  t:\n    runs-on: ubuntu-latest\n"
HOSTILE_BODY = "CORPO-OSTILE closes #7"
HOSTILE_REF = "tg/7-ramo-ostile"
CONFIG_BRANCH = "tollgate-config/x"


class GuardBase(unittest.TestCase):
    files = None

    def setUp(self):
        self.lab = GateLab(files=self.files)
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate guard "))
        self.data, self.log = self.tmp / "gh data.json", self.tmp / "gh.log"
        self.addCleanup(self.lab.close)
        self.addCleanup(self.ts.cleanup)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.set_gh()
        env = mock.patch.dict(os.environ, {
            "TOLLGATE_STATE": str(self.ts.dir), "TOLLGATE_GH": str(FAKEGH),
            "TOLLGATE_FAKEGH_DATA": str(self.data), "TOLLGATE_FAKEGH_LOG": str(self.log),
            "GITHUB_REPOSITORY": SLUG, "GITHUB_ACTIONS": "true"})
        env.start()
        self.addCleanup(env.stop)

    def set_gh(self, **data):
        data.setdefault("prs", [{"number": 1, "headRefName": BRANCH, "state": "OPEN",
                                 "comments": []}])
        self.data.write_text(json.dumps(data))

    def gh_data(self) -> dict:
        return json.loads(self.data.read_text())

    def calls(self) -> list[list[str]]:
        return [json.loads(x)["argv"] for x in self.log.read_text().splitlines()] \
            if self.log.exists() else []

    def posted_statuses(self, sha=None) -> list[dict]:
        by_sha = self.gh_data().get("commit_statuses", {})
        return by_sha.get(sha or self.lab.head, [])

    def comments(self) -> list[dict]:
        return self.gh_data()["prs"][0]["comments"]

    def event(self, *, head_ref=BRANCH, base="main", head_repo=SLUG, number=1, sha=None,
              body=HOSTILE_BODY, action="synchronize") -> Path:
        path = self.tmp / "event.json"
        path.write_text(json.dumps({
            "action": action, "number": number,
            "pull_request": {"number": number, "body": body,
                             "head": {"sha": sha or self.lab.head, "ref": head_ref,
                                      "repo": {"full_name": head_repo}},
                             "base": {"ref": base}},
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        return path

    def push_pr_head(self, number=1):
        git(self.lab.repo, "push", "-q", "origin", f"HEAD:refs/pull/{number}/head")

    def config_branch(self):
        git(self.lab.repo, "checkout", "-q", "-b", CONFIG_BRANCH, self.lab.base)

    def check(self, head_ref=BRANCH, cross_repo=False):
        return guard.check(self.lab.repo, base_tip=self.lab.base, head=self.lab.head,
                           head_ref=head_ref, cross_repo=cross_repo)

    def run_guard(self, event=None, *, publish=True):
        return guard.run(event or self.event(), publish=publish, environ=os.environ,
                         repo=self.lab.repo)


class CheckTest(GuardBase):
    files = {**DEFAULT_FILES, ".github/workflows/ci.yml": OK_WF}

    def test_clean_branch_is_green(self):
        self.lab.commit("src/new.py", "x = 1\n")
        self.assertEqual(self.check(), [])

    def test_tollgate_toml_changed(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        problems = self.check()
        self.assertEqual(len(problems), 1)
        self.assertIn("tollgate.toml", problems[0])

    def test_verdict_workflow_changed_outside_config_branch(self):
        self.lab.commit(".github/workflows/tollgate-verdict.yml", "on: x\n")
        for ref in (BRANCH, "feature/y"):
            with self.subTest(ref):
                self.assertTrue(any("tollgate-verdict.yml" in p for p in self.check(ref)))

    def test_tollgate_file_deleted_or_moved_is_red(self):
        self.lab.commit(".github/tollgate/VERSION", "1\n")
        base = self.lab.head
        self.lab.delete(".github/tollgate/VERSION")
        problems = guard.check(self.lab.repo, base_tip=base, head=self.lab.head,
                               head_ref=BRANCH, cross_repo=False)
        self.assertTrue(any("VERSION" in p for p in problems))

    def test_tollgate_file_moved_is_red(self):
        self.lab.commit(".github/tollgate/VERSION", "1\n")
        base = self.lab.head
        git(self.lab.repo, "mv", ".github/tollgate/VERSION", "docs/VERSION")
        git(self.lab.repo, "commit", "-qm", "sposta")
        problems = guard.check(self.lab.repo, base_tip=base, head=self.lab.head,
                               head_ref=BRANCH, cross_repo=False)
        self.assertTrue(any(".github/tollgate/VERSION" in p for p in problems), problems)

    def test_config_branch_only_tollgate_files_passes(self):
        self.config_branch()
        self.lab.commit("tollgate.toml", self.lab.toml + "\n# nota\n")
        self.lab.commit(".github/workflows/tollgate-run.yml", "on: x\n")
        self.lab.commit(".tollgate/waivers/7.toml", "schema_version = 1\n")
        self.assertEqual(self.check(CONFIG_BRANCH), [])

    def test_config_branch_with_code_is_red(self):
        self.config_branch()
        self.lab.commit("tollgate.toml", self.lab.toml + "\n# nota\n")
        self.lab.commit("src/new.py", "x = 1\n")
        problems = self.check(CONFIG_BRANCH)
        self.assertEqual(len(problems), 1)
        self.assertIn("src/new.py", problems[0])
        self.assertNotIn("tollgate.toml", problems[0])

    def test_config_branch_with_only_code_is_red(self):
        self.config_branch()
        self.lab.commit("src/new.py", "x = 1\n")
        self.assertTrue(any("src/new.py" in p for p in self.check(CONFIG_BRANCH)))

    def test_project_workflow_rules(self):
        wfs = {
            "statuses": "on: pull_request\npermissions:\n  statuses: write\n" + WF_BODY,
            "checks": "on: pull_request\npermissions:\n  checks: write\n" + WF_BODY,
            "target": "on: pull_request_target\npermissions:\n  contents: read\n" + WF_BODY,
            "run": "on:\n  workflow_run:\n    workflows: [x]\npermissions:\n"
                   "  contents: read\n" + WF_BODY,
            "none": "on: pull_request\n" + WF_BODY,
        }
        for name, text in wfs.items():
            path = f".github/workflows/{name}.yml"
            self.lab.commit(path, text, f"workflow {name}")
        problems = self.check()
        for name, needle in (("statuses", "statuses: write"), ("checks", "checks: write"),
                             ("target", "pull_request_target"), ("run", "workflow_run"),
                             ("none", "permissions")):
            with self.subTest(name):
                mine = [p for p in problems if f"{name}.yml" in p]
                self.assertEqual(len(mine), 1, mine)
                self.assertIn(needle, mine[0])
        self.assertEqual(len(set(problems)), 5)

    def test_project_workflow_modified_ok_passes(self):
        self.lab.commit(".github/workflows/ci.yml", OK_WF + "      - run: make\n")
        self.assertEqual(self.check(), [])

    def test_yaml_extension_checked(self):
        self.lab.commit(".github/workflows/x.yaml",
                        "on: pull_request\npermissions:\n  statuses: write\n" + WF_BODY)
        self.assertTrue(any("x.yaml" in p and "statuses" in p for p in self.check()))

    def test_workflow_deleted_is_not_checked(self):
        self.lab.delete(".github/workflows/ci.yml")
        self.assertEqual(self.check(), [])

    def test_fork_pr(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.lab.commit(".github/workflows/w.yml", "on: pull_request_target\n" + WF_BODY)
        problems = self.check(cross_repo=True)
        self.assertTrue(any("tollgate.toml" in p for p in problems))
        self.assertTrue(any("w.yml" in p and "pull_request_target" in p for p in problems))

    def test_fork_config_branch_gets_no_exception(self):
        self.config_branch()
        self.lab.commit("tollgate.toml", self.lab.toml + "\n# nota\n")
        self.assertEqual(self.check(CONFIG_BRANCH, cross_repo=False), [])
        problems = self.check(CONFIG_BRANCH, cross_repo=True)
        self.assertTrue(any("tollgate.toml" in p for p in problems))


class RunTest(GuardBase):
    def test_green_publishes_success_without_comment(self):
        self.push_pr_head()
        self.assertEqual(self.run_guard(), 0)
        [status] = self.posted_statuses()
        self.assertEqual((status["context"], status["state"]), ("tollgate/guard", "success"))
        self.assertLessEqual(len(status["description"]), 140)
        self.assertEqual(self.comments(), [])

    def test_red_publishes_failure_and_comment(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        self.assertEqual(self.run_guard(), 0)
        [status] = self.posted_statuses()
        self.assertEqual((status["context"], status["state"]), ("tollgate/guard", "failure"))
        [c] = self.comments()
        self.assertTrue(c["body"].startswith(f"{comment.GUARD_PREFIX} sha={self.lab.head} -->"))
        self.assertIn("tollgate.toml", c["body"])

    def test_red_comment_is_updated_not_duplicated(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        self.run_guard()
        self.lab.commit("tollgate.toml", "schema_version = 2\n")
        self.push_pr_head()
        self.run_guard(self.event(sha=self.lab.head))
        [c] = self.comments()
        self.assertIn(self.lab.head, c["body"])

    def test_publish_uses_files_not_args(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        self.assertEqual(self.run_guard(self.event(head_ref=HOSTILE_REF)), 0)
        calls = self.calls()
        self.assertTrue(calls)
        for argv in calls:
            line = " ".join(argv)
            for secret in ("CORPO-OSTILE", "ostile", "tollgate.toml", "schema_version"):
                self.assertNotIn(secret, line)
        self.assertTrue(any(a.startswith("body=@") for argv in calls for a in argv))
        self.assertTrue(any("--input" in argv for argv in calls))

    def test_not_default_base_writes_no_status(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        event = self.event(base="other", head_ref="tollgate-config/z")
        self.assertEqual(self.run_guard(event), 0)
        self.assertEqual(self.posted_statuses(), [])
        self.assertNotIn("commit_statuses", self.gh_data())
        [c] = self.comments()
        self.assertIn("non applicabile", c["body"])
        self.assertTrue(c["body"].startswith(comment.GUARD_PREFIX))

    def test_shared_sha_is_error(self):
        self.push_pr_head()
        sha = self.lab.head
        pulls = [{"number": n, "state": "open", "merged_at": None,
                  "base": {"ref": "main"}, "head": {"sha": sha}} for n in (1, 2)]
        self.set_gh(commit_pulls={sha: pulls})
        self.assertEqual(self.run_guard(), 0)
        [status] = self.posted_statuses()
        self.assertEqual((status["context"], status["state"]), ("tollgate/guard", "error"))
        self.assertIn("SHA condiviso", status["description"])

    def test_shared_sha_ignores_other_bases_and_closed(self):
        self.push_pr_head()
        sha = self.lab.head
        pulls = [
            {"number": 1, "state": "open", "base": {"ref": "main"}, "head": {"sha": sha}},
            {"number": 2, "state": "open", "base": {"ref": "other"}, "head": {"sha": sha}},
            {"number": 3, "state": "closed", "base": {"ref": "main"}, "head": {"sha": sha}}]
        self.set_gh(commit_pulls={sha: pulls})
        self.assertEqual(self.run_guard(), 0)
        self.assertEqual(self.posted_statuses()[0]["state"], "success")

    def test_other_base_on_shared_sha_does_not_overwrite_guard(self):
        """Una PR verso `other` sulla stessa testa di una PR verso il predefinito: nessuno stato."""
        self.push_pr_head()
        sha = self.lab.head
        pulls = [{"number": n, "state": "open", "base": {"ref": b}, "head": {"sha": sha}}
                 for n, b in ((1, "main"), (2, "other"))]
        self.set_gh(commit_pulls={sha: pulls},
                    prs=[{"number": 2, "headRefName": "tollgate-config/z", "state": "OPEN",
                          "comments": []}])
        self.assertEqual(self.run_guard(self.event(base="other", number=2,
                                                   head_ref="tollgate-config/z")), 0)
        self.assertEqual(self.posted_statuses(), [])

    def test_stacked_pr_does_not_make_sha_shared(self):
        """`commits/<sha>/pulls` elenca anche la PR B impilata su A (V5b): non è testa di A."""
        self.push_pr_head()
        sha = self.lab.head
        pulls = [{"number": 1, "state": "open", "base": {"ref": "main"}, "head": {"sha": sha}},
                 {"number": 2, "state": "open", "base": {"ref": "main"},
                  "head": {"sha": "b" * 40}}]
        self.set_gh(commit_pulls={sha: pulls})
        self.assertEqual(self.run_guard(), 0)
        self.assertEqual(self.posted_statuses()[0]["state"], "success")

    def test_transient_500_on_commit_pulls_is_retried(self):
        """Prova P4: `commits/<sha>/pulls` risponde a volte 500 a corpo vuoto, che gh con
        `--paginate` riporta come `unexpected end of JSON input`; la richiesta dopo va."""
        self.push_pr_head()
        sha = self.lab.head
        pulls = [{"number": 1, "state": "open", "base": {"ref": "main"}, "head": {"sha": sha}}]
        self.set_gh(commit_pulls={sha: pulls},
                    api_flaky={f"repos/{SLUG}/commits/{sha}/pulls": ["unexpected end of JSON input"]})
        with mock.patch.object(ghcli, "_sleep") as sleep:
            self.assertEqual(self.run_guard(), 0)
        sleep.assert_called_once_with(2)
        [status] = self.posted_statuses()
        self.assertEqual((status["context"], status["state"]), ("tollgate/guard", "success"))

    def test_transient_500_on_guard_status_post_is_retried(self):
        """Prova P4 (giro 5): il POST di `tollgate/guard` ha avuto un 500 a corpo vuoto."""
        self.push_pr_head()
        sha = self.lab.head
        self.set_gh(api_flaky={f"POST repos/{SLUG}/statuses/{sha}": ["unexpected end of JSON input"]})
        with mock.patch.object(ghcli, "_sleep") as sleep:
            self.assertEqual(self.run_guard(), 0)
        sleep.assert_called_once_with(2)
        [status] = self.posted_statuses()
        self.assertEqual((status["context"], status["state"]), ("tollgate/guard", "success"))

    def test_red_comment_says_red_not_waiting(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        self.run_guard()
        [c] = self.comments()
        self.assertNotIn("in attesa", c["body"])
        self.assertIn("tollgate/guard", c["body"])
        self.assertIn("rosso", c["body"])

    def test_pr_advanced_since_the_event_writes_nothing(self):
        old = self.lab.head
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        self.assertEqual(self.run_guard(self.event(sha=old)), 0)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.comments(), [])

    def test_hostile_file_names_stay_inert(self):
        name = "a`b``` --> @x ::error::.txt"
        self.config_branch()
        self.lab.commit(name, "x\n")
        self.push_pr_head()
        out = io.StringIO()
        with redirect_stdout(out):
            self.run_guard(self.event(head_ref=CONFIG_BRANCH), publish=False)
        for line in out.getvalue().splitlines():
            self.assertFalse(line.startswith("::"), line)
        self.assertEqual(self.run_guard(self.event(head_ref=CONFIG_BRANCH)), 0)
        [c] = self.comments()
        outside = c["body"].split("\n````", 1)
        self.assertEqual(len(outside), 2, c["body"])
        self.assertNotIn("@x", outside[0])
        self.assertEqual(outside[0].count("-->"), 1)

    def test_edit_to_other_base_after_green_guard_keeps_green_status(self):
        self.push_pr_head()
        self.run_guard()
        self.run_guard(self.event(base="other"))
        self.assertEqual([s["state"] for s in self.posted_statuses()], ["success"])

    def test_dry_run_publishes_nothing_and_returns_1_when_red(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(self.run_guard(publish=False), 1)
        self.assertEqual(self.calls(), [])
        self.assertIn("tollgate.toml", out.getvalue())

    def test_stale_head_is_an_error(self):
        self.push_pr_head()
        with self.assertRaises(GitError):
            self.run_guard(self.event(sha="1" * 40))
        self.assertEqual(self.posted_statuses(), [])

    def test_green_guard_updates_previous_red_comment(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        self.run_guard()
        [red] = self.comments()
        self.assertIn("rosso", red["body"])
        # lo stesso SHA diventa verde: il predefinito ha raggiunto la stessa configurazione
        git(self.lab.repo, "push", "-q", "origin", "HEAD:refs/heads/main")
        self.assertEqual(self.run_guard(), 0)
        [note] = self.comments()
        self.assertEqual(note["id"], red["id"])
        self.assertTrue(note["body"].startswith(f"{comment.GUARD_PREFIX} sha={self.lab.head} -->"))
        self.assertIn("risolto", note["body"])
        self.assertNotIn("tollgate.toml", note["body"])
        self.assertNotIn("rosso", note["body"])
        self.assertEqual([s["state"] for s in self.posted_statuses()], ["success", "failure"])

    def test_green_guard_keeps_red_comment_of_another_sha(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        red_sha = self.lab.head
        self.push_pr_head()
        self.run_guard()
        [red] = self.comments()
        git(self.lab.repo, "push", "-q", "origin", "HEAD:refs/heads/main")
        other = self.lab.commit("src/new.py", "x = 1\n")       # un altro SHA, verde
        self.push_pr_head()
        self.assertEqual(self.run_guard(self.event(sha=other)), 0)
        self.assertEqual(self.comments(), [red])
        self.assertTrue(self.comments()[0]["body"].startswith(
            f"{comment.GUARD_PREFIX} sha={red_sha} -->"))
        self.assertEqual(self.posted_statuses(other)[0]["state"], "success")

    def test_edit_comment_failure_after_green_status_is_a_message(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        self.run_guard()
        git(self.lab.repo, "push", "-q", "origin", "HEAD:refs/heads/main")
        err = io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.lab.repo)
        self.addCleanup(os.chdir, cwd)
        with mock.patch.object(github, "edit_comment", side_effect=ghcli.GhError("HTTP 502")), \
                redirect_stderr(err):
            code = cli.main(["guard", "--event", str(self.event()), "--publish"])
        self.assertEqual(code, 1)
        self.assertIn("HTTP 502", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self.posted_statuses()[0]["state"], "success")

    def test_green_guard_without_comment_creates_none(self):
        self.push_pr_head()
        self.run_guard()
        self.assertEqual(self.comments(), [])
        self.assertFalse(any("--method" in a and a[-1].endswith("/comments") for a in self.calls()))

    def test_green_guard_leaves_not_applicable_comment_alone(self):
        self.push_pr_head()
        self.run_guard(self.event(base="other"))
        [before] = self.comments()
        self.run_guard()
        self.assertEqual(self.comments(), [before])

    def test_missing_repository_is_a_value_error(self):
        env = {k: v for k, v in os.environ.items() if k != "GITHUB_REPOSITORY"}
        with self.assertRaises(ValueError):
            guard.run(self.event(), publish=True, environ=env, repo=self.lab.repo)

    def test_token_reaches_fetch_only_as_token(self):
        self.push_pr_head()
        seen = {}

        real = guard.git.fetch_ref

        def fake(repo, ref, *, token=None):
            seen.update(ref=ref, token=token)
            real(repo, ref)

        with mock.patch.object(guard.git, "fetch_ref", fake), \
                mock.patch.dict(os.environ, {"GH_TOKEN": "tkn-123"}):
            self.run_guard()
        self.assertEqual(seen, {"ref": "refs/pull/1/head", "token": "tkn-123"})
        self.assertFalse(any("tkn-123" in " ".join(a) for a in self.calls()))


class PendingTest(test_gate_github.VerdictBase):
    """Decisione 15, Review Focus 3: su `opened`, `edited` e `reopened` `guard` scrive
    `tollgate/verdict` `pending` prima dei controlli; `gate evaluate` lo sostituisce."""

    def guard_event(self, action, *, base="main", sha=None) -> Path:
        path = self.tmp / "guard event.json"
        path.write_text(json.dumps({
            "action": action, "number": 1,
            "pull_request": {"number": 1, "body": "", "head": {
                "sha": sha or self.sha, "ref": BRANCH, "repo": {"full_name": SLUG}},
                "base": {"ref": base}},
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        return path

    def guard(self, action, *, publish=True, **kw) -> int:
        return guard.run(self.guard_event(action, **kw), publish=publish, environ=os.environ,
                         repo=self.lab.repo)

    def verdict_states(self, sha=None) -> list[str]:
        """Gli stati di `tollgate/verdict` del commit, dal più recente."""
        rows = self.gh_data().get("commit_statuses", {}).get(sha or self.sha, [])
        return [r["state"] for r in rows if r["context"] == "tollgate/verdict"]

    def test_edited_publishes_pending_then_verdict_replaces(self):
        self.assertEqual(self.guard("edited"), 0)
        self.assertEqual(self.verdict_states(), ["pending"])
        [row] = [r for r in self.gh_data()["commit_statuses"][self.sha]
                 if r["context"] == "tollgate/verdict"]
        self.assertEqual(row["description"], guard.PENDING_DESCRIPTION)
        self.assertEqual(self.statuses()["tollgate/guard"]["state"], "success")
        self.assertEqual(self.run_verdict(), 0)
        self.assertEqual(self.verdict_states(), ["success", "pending"])
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "success")

    def test_reopened_publishes_pending(self):
        self.guard("reopened")
        self.assertEqual(self.verdict_states(), ["pending"])

    def test_opened_publishes_pending(self):
        # una PR nuova con la testa di una PR chiusa che aveva `success`: non lo eredita
        self.assertEqual(self.run_verdict(), 0)
        self.assertEqual(self.verdict_states(), ["success"])
        self.guard("opened")
        self.assertEqual(self.verdict_states(), ["pending", "success"])
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "pending")

    def test_synchronize_no_pending(self):
        self.guard("synchronize")
        self.assertEqual(self.verdict_states(), [])
        self.assertEqual(self.statuses()["tollgate/guard"]["state"], "success")

    def test_no_pending_for_other_base(self):
        self.guard("edited", base="other")
        self.assertNotIn("commit_statuses", self.gh_data())

    def test_other_base_keeps_the_previous_verdict(self):
        self.assertEqual(self.run_verdict(), 0)
        self.guard("edited", base="other")
        self.assertEqual(self.verdict_states(), ["success"])

    def test_dry_run_publishes_no_pending(self):
        with redirect_stdout(io.StringIO()):
            self.guard("edited", publish=False)
        self.assertNotIn("commit_statuses", self.gh_data())

    def test_pending_is_written_before_the_checks(self):
        stale = "1" * 40            # la testa dell'evento non esiste: i controlli falliscono
        with self.assertRaises(GitError):
            self.guard("edited", sha=stale)
        self.assertEqual(self.verdict_states(stale), ["pending"])
        self.assertEqual([r["context"] for r in self.gh_data()["commit_statuses"][stale]],
                         ["tollgate/verdict"])

    def test_pending_actions(self):
        self.assertEqual(guard.PENDING_ACTIONS, ("opened", "edited", "reopened"))


class GithubTest(GuardBase):
    def api_state(self):
        return self.ts.state

    def call(self, fn, *args, **kw):
        return fn(self.ts.state, self.lab.repo, SLUG, *args, **kw)

    def test_pr_from_event(self):
        pr = github.pr_from_event(github.read_event(self.event(head_repo="x/fork")))
        self.assertEqual(pr, PrFacts(1, self.lab.head, BRANCH, "main", "main", HOSTILE_BODY,
                                     True))
        pr = github.pr_from_event(github.read_event(self.event()))
        self.assertFalse(pr.cross_repo)

    def test_pr_from_event_deleted_fork_is_cross_repo(self):
        data = github.read_event(self.event())
        data["pull_request"]["head"]["repo"] = None
        self.assertTrue(github.pr_from_event(data).cross_repo)

    def test_pr_from_event_without_pr_is_none(self):
        self.assertIsNone(github.pr_from_event({"repository": {}}))

    def test_pr_from_event_rejects_bad_sha(self):
        data = github.read_event(self.event())
        data["pull_request"]["head"]["sha"] = "--upload-pack=x"
        with self.assertRaises(ValueError):
            github.pr_from_event(data)

    def test_read_event_rejects_non_object(self):
        path = self.tmp / "e.json"
        path.write_text("[1]")
        with self.assertRaises(ValueError):
            github.read_event(path)

    def test_set_status_goes_through_input_file(self):
        sha = self.lab.head
        self.call(github.set_status, sha, context="tollgate/guard", status="failure",
                  description="x" * 300)
        [status] = self.posted_statuses()
        self.assertEqual(len(status["description"]), 140)
        [argv] = [a for a in self.calls() if "--method" in a]
        self.assertIn("--input", argv)
        self.assertNotIn("failure", " ".join(argv))

    def test_set_status_retries_transient_500(self):
        sha = self.lab.head
        self.set_gh(api_flaky={f"POST repos/{SLUG}/statuses/{sha}": ["unexpected end of JSON input"]})
        with mock.patch.object(ghcli, "_sleep") as sleep:
            self.call(github.set_status, sha, context="tollgate/guard", status="success",
                      description="d")
        sleep.assert_called_once_with(2)
        [status] = self.posted_statuses()
        self.assertEqual(status["state"], "success")
        self.assertEqual(len([a for a in self.calls() if "--method" in a]), 2)

    def test_new_comment_and_issue_are_not_retried(self):
        self.set_gh(issues={"12": {"number": 12, "state": "open", "labels": [], "comments": []}},
                    api_flaky={f"POST repos/{SLUG}/issues/12/comments": ["gh: boom (HTTP 500)"],
                               f"POST repos/{SLUG}/issues": ["gh: boom (HTTP 500)"]})
        with mock.patch.object(ghcli, "_sleep") as sleep:
            with self.assertRaises(ghcli.GhError):
                self.call(github.comment_issue, 12, body_file=self.body_file("ciao"))
            with self.assertRaises(ghcli.GhError):
                self.call(github.create_issue, title=ghcli.SENTINEL_TITLE,
                          body_file=self.body_file("corpo"))
        sleep.assert_not_called()
        self.assertEqual(len(self.calls()), 2)
        self.assertEqual(self.gh_data()["issues"]["12"]["comments"], [])

    def test_upsert_patch_is_retried_but_new_comment_post_is_not(self):
        prefix = comment.GUARD_PREFIX
        self.set_gh(prs=[{"number": 1, "comments": [
            {"id": 5, "body": prefix + " a", "author": {"login": "github-actions"}}]}],
            api_flaky={f"PATCH repos/{SLUG}/issues/comments/5": ["unexpected end of JSON input"]})
        with mock.patch.object(ghcli, "_sleep") as sleep:
            self.call(github.upsert_comment, 1, prefix=prefix,
                      body_file=self.body_file(prefix + " b"))
        sleep.assert_called_once_with(2)
        self.assertEqual([c["body"] for c in self.comments()], [prefix + " b"])
        self.set_gh(api_flaky={f"POST repos/{SLUG}/issues/1/comments": ["gh: boom (HTTP 500)"]})
        with mock.patch.object(ghcli, "_sleep") as sleep:
            with self.assertRaises(ghcli.GhError):
                self.call(github.upsert_comment, 1, prefix=prefix,
                          body_file=self.body_file(prefix + " c"))
        sleep.assert_not_called()
        self.assertEqual(self.comments(), [])

    def test_set_status_validates(self):
        good = {"context": "tollgate/guard", "status": "success"}
        for sha, kw in (("abc", {}), (self.lab.head, {"context": "altro/guard"}),
                        (self.lab.head, {"status": "boh"})):
            with self.subTest(sha=sha, kw=kw), self.assertRaises(ValueError):
                self.call(github.set_status, sha, description="d", **{**good, **kw})
        self.assertEqual(self.calls(), [])

    def test_statuses_newest_first_with_creator(self):
        sha = self.lab.head
        self.set_gh(commit_statuses={sha: [
            {"context": "tollgate/guard", "state": "failure", "creator": {"login": "mario"}},
            {"context": "tollgate/guard", "state": "success",
             "creator": {"login": "github-actions[bot]"}}]})
        got = self.call(github.statuses, sha)
        self.assertEqual([s["state"] for s in got], ["failure", "success"])
        self.assertEqual(got[0]["creator"]["login"], "mario")

    def test_issue(self):
        self.set_gh(issues={"7": {"number": 7, "state": "OPEN", "labels": [{"name": "security"}]}},
                    api_status={"repos/o/r/issues/9": {"status": 404, "message": "Not Found",
                                                       "body": {"message": "Not Found"}}})
        self.assertEqual(self.call(github.issue, 7), IssueFacts(7, "open", ("security",)))
        self.assertIsNone(self.call(github.issue, 9))

    def test_issue_that_is_a_pr_is_flagged(self):
        self.set_gh(issues={"7": {"number": 7, "state": "OPEN", "labels": [],
                                  "pull_request": {"url": "u"}}})
        self.assertEqual(self.call(github.issue, 7), IssueFacts(7, "open", (), is_pr=True))

    def test_pr_comments_are_rest_with_ids(self):
        self.set_gh(prs=[{"number": 1, "comments": [
            {"id": 5, "body": "b", "author": {"login": "github-actions"}}]}])
        [c] = self.call(github.pr_comments, 1)
        self.assertEqual((c["id"], c["user"]["login"], c["body"]),
                         (5, "github-actions[bot]", "b"))

    def body_file(self, text):
        path = self.tmp / "body.md"
        path.write_text(text)
        return path

    def test_upsert_creates_then_updates_bot_comment(self):
        prefix = comment.GUARD_PREFIX
        self.call(github.upsert_comment, 1, prefix=prefix, body_file=self.body_file(prefix + " a"))
        self.call(github.upsert_comment, 1, prefix=prefix, body_file=self.body_file(prefix + " b"))
        [c] = self.comments()
        self.assertEqual(c["body"], prefix + " b")

    def test_upsert_ignores_user_comment_with_same_prefix(self):
        prefix = comment.GUARD_PREFIX
        self.set_gh(prs=[{"number": 1, "comments": [
            {"id": 5, "body": prefix + " finto", "author": {"login": "mario"}}]}])
        self.call(github.upsert_comment, 1, prefix=prefix, body_file=self.body_file(prefix + " v"))
        bodies = [c["body"] for c in self.comments()]
        self.assertEqual(bodies, [prefix + " finto", prefix + " v"])

    def test_prs_for_commit_and_open_sentinel_issues(self):
        sha = self.lab.head
        pulls = [{"number": 4, "state": "open", "merged_at": None, "base": {"ref": "main"},
                  "head": {"sha": sha}}]
        sentinel = {"number": 12, "title": ghcli.SENTINEL_TITLE, "url": "https://x/12"}
        other = {"number": 13, "title": "altro", "url": "https://x/13"}
        self.set_gh(commit_pulls={sha: pulls}, open_issues=[sentinel, other])
        self.assertEqual(self.call(github.prs_for_commit, sha), pulls)
        self.assertEqual(self.call(github.open_sentinel_issues), [sentinel])
        [argv] = [a for a in self.calls() if a[-1].startswith("repos/o/r/issues?")]
        self.assertIn("--paginate", argv)
        self.assertNotIn("--limit", argv)

    def test_comment_and_create_issue_use_body_files(self):
        self.set_gh(issues={"12": {"number": 12, "state": "open", "labels": [], "comments": []}})
        self.call(github.comment_issue, 12, body_file=self.body_file("ciao"))
        self.assertEqual(self.gh_data()["issues"]["12"]["comments"][0]["body"], "ciao")
        made = self.call(github.create_issue, title=ghcli.SENTINEL_TITLE,
                         body_file=self.body_file("corpo"))
        self.assertEqual(made["title"], ghcli.SENTINEL_TITLE)
        self.assertTrue(any(a.startswith("body=@") for argv in self.calls() for a in argv))

    def test_repo_slug_validated(self):
        self.assertEqual(github.repo_slug({"GITHUB_REPOSITORY": "o/r"}), "o/r")
        for bad in (None, "", "o", "o/r/x", "o/r;x", "-o/r", "o/../r"):
            with self.subTest(bad), self.assertRaises(ValueError):
                github.repo_slug({} if bad is None else {"GITHUB_REPOSITORY": bad})


class CliTest(GuardBase):
    def tollgate(self, *args, **env):
        e = {**self.ts.env(), "HOME": str(self.tmp)}
        e.update(env)
        e.pop("GITHUB_ACTIONS", None) if "GITHUB_ACTIONS" not in env else None
        return subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), "gate", "guard",
                               *args], cwd=self.lab.repo, env=e, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=120)

    def test_publish_refused_outside_actions(self):
        for env in ({}, {"GITHUB_ACTIONS": "false"}, {"GITHUB_ACTIONS": "1"}):
            with self.subTest(env=env):
                r = self.tollgate("--event", str(self.event()), "--publish", **env)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("GitHub Actions", r.stderr)
                self.assertEqual(self.calls(), [])

    def test_abbreviated_option_is_an_argument_error(self):
        for opt in ("--pub", "--publ", "--ev"):
            with self.subTest(opt=opt):
                r = self.tollgate("--event", str(self.event()), opt, GITHUB_ACTIONS="true")
                self.assertEqual(r.returncode, 2)

    def test_end_to_end_publish_in_actions(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        r = self.tollgate("--event", str(self.event()), "--publish", GITHUB_ACTIONS="true",
                          GITHUB_REPOSITORY=SLUG, TOLLGATE_GH=str(FAKEGH),
                          TOLLGATE_FAKEGH_DATA=str(self.data),
                          TOLLGATE_FAKEGH_LOG=str(self.log))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.posted_statuses()[0]["state"], "failure")

    def test_dry_run_prints_problems_as_json_strings(self):
        self.lab.commit("tollgate.toml", "schema_version = 1\n")
        self.push_pr_head()
        r = self.tollgate("--event", str(self.event()), GITHUB_REPOSITORY=SLUG)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn('"', r.stdout)
        self.assertEqual(self.calls(), [])

    def test_event_error_is_a_message_not_a_traceback(self):
        bad = self.tmp / "bad.json"
        bad.write_text("{")
        r = self.tollgate("--event", str(bad), GITHUB_REPOSITORY=SLUG)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("gate guard", r.stderr)


if __name__ == "__main__":
    unittest.main()
