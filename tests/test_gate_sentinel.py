import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import test_gate_github
from tests.flowkit import FAKEGH
from tests.gatekit import GATE_TOML, GateLab
from tests.helpers import TempState, git
from tollgate_core import ghcli, paths
from tollgate_gate import baseids, cli, github, sentinel

SLUG = "o/r"
BOT = "github-actions[bot]"
WORKFLOW = ".github/workflows/tollgate-sentinel.yml"
ZEROS = "0" * 40
PR_HEAD = "a" * 40


def merged(number=4, head=PR_HEAD, base="main", merged_at="2026-10-21T10:00:00Z") -> dict:
    """Una riga di `commits/<sha>/pulls` come la dà `github.prs_for_commit`."""
    return {"number": number, "state": "closed", "merged_at": merged_at,
            "base": {"ref": base}, "head": {"sha": head}}


def status(context, state, login=BOT) -> dict:
    return {"context": context, "state": state, "creator": {"login": login}}


GREEN = [status("tollgate/verdict", "success"), status("tollgate/guard", "success")]


class SentinelBase(unittest.TestCase):
    toml = GATE_TOML

    def setUp(self):
        self.lab = GateLab(toml=self.toml)
        self.start = self.lab.head      # il commit del piano: i push cominciano dopo
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate sentinel "))
        self.data, self.log = self.tmp / "gh data.json", self.tmp / "gh.log"
        self.addCleanup(self.lab.close)
        self.addCleanup(self.ts.cleanup)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        env = mock.patch.dict(os.environ, {
            "TOLLGATE_STATE": str(self.ts.dir), "TOLLGATE_GH": str(FAKEGH),
            "TOLLGATE_FAKEGH_DATA": str(self.data), "TOLLGATE_FAKEGH_LOG": str(self.log),
            "GITHUB_REPOSITORY": SLUG, "GITHUB_ACTIONS": "true"})
        env.start()
        self.addCleanup(env.stop)
        self.stdout, self.stderr = io.StringIO(), io.StringIO()
        self.enterContext(contextlib.redirect_stdout(self.stdout))
        self.enterContext(contextlib.redirect_stderr(self.stderr))
        self.sleeps: list[float] = []
        self.set_gh()

    def set_gh(self, *, pulls=None, statuses=None, open_issues=None):
        self.data.write_text(json.dumps({
            "commit_pulls": pulls or {}, "commit_statuses": statuses or {},
            "open_issues": open_issues or []}))

    def gh_data(self) -> dict:
        return json.loads(self.data.read_text())

    def calls(self) -> list[list[str]]:
        return [json.loads(x)["argv"] for x in self.log.read_text().splitlines()] \
            if self.log.exists() else []

    def pulls_calls(self) -> list[str]:
        """Gli SHA interrogati, ciascuno una volta (le riletture non contano)."""
        return list(dict.fromkeys(a[-1].split("/")[4] for a in self.calls() if "/pulls?" in a[-1]))

    def sentinel_statuses(self, sha) -> list[dict]:
        rows = self.gh_data().get("commit_statuses", {}).get(sha, [])
        return [r for r in rows if r["context"] == "tollgate/sentinel"]

    def issues(self) -> list[dict]:
        return self.gh_data()["open_issues"]

    def event(self, before, after, *, ref="refs/heads/main") -> Path:
        path = self.tmp / "event.json"
        path.write_text(json.dumps({
            "ref": ref, "before": before, "after": after,
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        return path

    def push(self, before, after, *, publish=True, **kw) -> int:
        return sentinel.run(self.event(before, after), publish=publish, environ=os.environ,
                            repo=self.lab.repo, sleep=self.sleeps.append, **kw)

    def commit(self, name="x") -> str:
        return self.lab.commit(f"src/{name}.py", f"{name} = 1\n", f"commit {name}")


class UnverifiedTest(SentinelBase):
    def unverified(self, before, after, pulls, statuses, **kw):
        return sentinel.unverified(
            self.lab.repo, before=before, after=after,
            prs_for_commit=lambda sha: pulls.get(sha, []),
            statuses=lambda sha: statuses.get(sha, []), sleep=self.sleeps.append, **kw)

    def test_green_commit_is_verified(self):
        c = self.commit()
        got = self.unverified(self.start, c, {c: [merged()]}, {PR_HEAD: GREEN})
        self.assertEqual(got, [])
        self.assertEqual(self.sleeps, [])

    def test_empty_list_retries_then_unverified(self):
        c = self.commit()
        calls = []
        got = sentinel.unverified(
            self.lab.repo, before=self.start, after=c, attempts=3, wait=5.0,
            prs_for_commit=lambda sha: calls.append(sha) or [], statuses=lambda sha: [],
            sleep=self.sleeps.append)
        self.assertEqual([sha for sha, _ in got], [c])
        self.assertEqual(calls, [c, c, c])
        self.assertEqual(self.sleeps, [5.0, 5.0])

    def test_pr_appearing_on_retry_is_accepted(self):
        c = self.commit()
        answers = iter([[], [merged()]])
        got = sentinel.unverified(
            self.lab.repo, before=self.start, after=c, prs_for_commit=lambda sha: next(answers),
            statuses=lambda sha: GREEN, sleep=self.sleeps.append)
        self.assertEqual(got, [])
        self.assertEqual(len(self.sleeps), 1)

    def test_open_or_other_base_pr_does_not_count(self):
        c = self.commit()
        pulls = {c: [merged(4, merged_at=None), merged(5, base="release")]}
        got = self.unverified(self.start, c, pulls, {PR_HEAD: GREEN})
        self.assertEqual([sha for sha, _ in got], [c])

    def test_reasons_name_the_missing_context(self):
        c = self.commit()
        got = self.unverified(self.start, c, {c: [merged()]},
                              {PR_HEAD: [status("tollgate/guard", "success")]})
        [(_, reason)] = got
        self.assertIn("tollgate/verdict", reason)
        self.assertIn("#4", reason)

    def test_any_verified_pr_is_enough(self):
        c = self.commit()
        pulls = {c: [merged(4, head="b" * 40), merged(5)]}
        got = self.unverified(self.start, c, pulls, {PR_HEAD: GREEN})
        self.assertEqual(got, [])


class RunTest(SentinelBase):
    def test_direct_push_red_and_issue(self):
        c = self.commit()
        self.assertEqual(self.push(self.start, c), 0)
        [row] = self.sentinel_statuses(c)
        self.assertEqual(row["state"], "failure")
        [issue] = self.issues()
        self.assertEqual(issue["title"], ghcli.SENTINEL_TITLE)
        self.assertIn(c, issue["body"])
        self.assertEqual(self.sleeps, [5.0, 5.0])

    def test_dry_run_prints_and_writes_nothing(self):
        c = self.commit()
        self.assertEqual(self.push(self.start, c, publish=False), 1)
        self.assertIn(c, self.stdout.getvalue())
        self.assertEqual(self.sentinel_statuses(c), [])
        self.assertEqual(self.issues(), [])

    def test_dry_run_does_not_need_github_repository(self):
        c = self.commit()
        with mock.patch.dict(os.environ):
            del os.environ["GITHUB_REPOSITORY"]
            self.assertEqual(self.push(self.start, c, publish=False), 1)
        self.assertIn(f"repos/{SLUG}/commits/{c}/pulls", self.calls()[0][-1])

    def test_merge_of_red_verdict(self):
        c = self.commit()
        self.set_gh(pulls={c: [merged()]}, statuses={PR_HEAD: [
            status("tollgate/verdict", "failure"), status("tollgate/guard", "success")]})
        self.push(self.start, c)
        self.assertEqual([r["state"] for r in self.sentinel_statuses(c)], ["failure"])
        self.assertEqual(len(self.issues()), 1)
        self.assertEqual(self.sleeps, [])

    def test_status_from_user_token_not_trusted(self):
        c = self.commit()
        self.set_gh(pulls={c: [merged()]}, statuses={PR_HEAD: [
            status("tollgate/verdict", "success", login="mario"),
            status("tollgate/guard", "success")]})
        self.push(self.start, c)
        self.assertEqual(len(self.sentinel_statuses(c)), 1)
        self.assertEqual(len(self.issues()), 1)

    def test_bot_login_without_suffix_not_trusted_for_statuses(self):
        c = self.commit()
        self.set_gh(pulls={c: [merged()]}, statuses={PR_HEAD: [
            status("tollgate/verdict", "success", login="github-actions"),
            status("tollgate/guard", "success")]})
        self.push(self.start, c)
        self.assertEqual(len(self.sentinel_statuses(c)), 1)

    def test_statuses_written_before_the_issue(self):
        c = self.commit()
        self.push(self.start, c)
        writes = [a[-1] for a in self.calls() if "--method" in a]
        self.assertEqual(writes[0].split("/")[3], "statuses")
        self.assertTrue(writes[1].endswith("/issues"), writes)

    def test_latest_status_wins(self):
        c = self.commit()
        self.set_gh(pulls={c: [merged()]}, statuses={PR_HEAD: [      # dal più recente
            status("tollgate/verdict", "failure"), status("tollgate/guard", "success"),
            status("tollgate/verdict", "success")]})
        self.push(self.start, c)
        self.assertEqual(len(self.sentinel_statuses(c)), 1)
        self.set_gh(pulls={c: [merged()]}, statuses={PR_HEAD: [      # il rosso è il più vecchio
            status("tollgate/verdict", "success"), status("tollgate/guard", "success"),
            status("tollgate/verdict", "failure")]})
        self.assertEqual(self.push(self.start, c), 0)
        self.assertEqual(self.issues(), [])

    def test_rebase_merge_commits(self):
        commits = [self.commit(n) for n in ("a", "b", "c")]
        self.set_gh(pulls={c: [merged()] for c in commits}, statuses={PR_HEAD: GREEN})
        self.assertEqual(self.push(self.start, commits[-1]), 0)
        self.assertEqual(self.pulls_calls(), commits)
        self.assertEqual(self.issues(), [])
        self.assertTrue(all(self.sentinel_statuses(c) == [] for c in commits))
        # un commit del push che non viene dalla PR è l'unico rosso
        direct = self.commit("d")
        self.set_gh(pulls={c: [merged()] for c in commits}, statuses={PR_HEAD: GREEN})
        self.push(self.start, direct)
        self.assertEqual([c for c in (*commits, direct) if self.sentinel_statuses(c)], [direct])

    def test_first_install_ignored(self):
        before = self.start
        first = self.commit("a")
        install = self.lab.commit(WORKFLOW, "on: push\n", "installa sentinel")
        self.assertEqual(self.push(before, install), 0)
        self.assertEqual(self.issues(), [])
        self.assertEqual(self.pulls_calls(), [])
        later = self.commit("b")           # il commit dopo l'installazione conta
        self.push(before, later)
        self.assertEqual([c for c in (first, install, later) if self.sentinel_statuses(c)],
                         [later])

    def test_installed_workflow_is_not_a_first_install(self):
        install = self.lab.commit(WORKFLOW, "on: push\n", "installa sentinel")
        c = self.commit()
        self.push(install, c)
        self.assertEqual(len(self.sentinel_statuses(c)), 1)

    def test_single_issue_reused(self):
        c1 = self.commit("a")
        self.push(self.start, c1)
        [issue] = self.issues()
        c2 = self.commit("b")
        self.push(c1, c2)
        [again] = self.issues()
        self.assertEqual(again["number"], issue["number"])
        [note] = again["comments"]
        self.assertIn(c2, note["body"])
        self.assertNotIn(c1, note["body"])

    def test_existing_issue_found_beyond_first_page(self):
        rows = [{"number": n, "title": f"altro {n}"} for n in range(1, 111)]
        rows[105] = {"number": 106, "title": ghcli.SENTINEL_TITLE, "url": "https://x/106"}
        self.set_gh(open_issues=rows)
        self.push(self.start, self.commit())
        self.assertEqual(len(self.issues()), 110)
        self.assertEqual(len(self.issues()[105]["comments"]), 1)

    def test_before_all_zeros(self):
        c = self.commit()
        self.push(ZEROS, c)
        self.assertEqual(self.pulls_calls(), [c])
        self.assertEqual(len(self.sentinel_statuses(c)), 1)

    def forced(self, before, after, **kw):
        """Il push `before` → `after` con `after` in una PR verificata: solo la riscrittura
        della storia può renderlo rosso."""
        self.set_gh(pulls={after: [merged()]}, statuses={PR_HEAD: GREEN})
        self.push(before, after, **kw)
        return self.sentinel_statuses(after)

    def test_unknown_before_is_forced_push(self):
        c = self.commit()
        [row] = self.forced("1" * 40, c)
        self.assertEqual(row["state"], "failure")
        self.assertIn("push forzato", row["description"])
        self.assertIn("push forzato: intervallo non calcolabile", self.issues()[0]["body"])
        self.assertEqual(self.pulls_calls(), [c])

    def test_rewritten_history_is_forced_push(self):
        old = self.commit("old")
        git(self.lab.repo, "checkout", "-q", "-b", "alt", self.start)
        new = self.commit("new")
        [row] = self.forced(old, new)
        self.assertIn("push forzato", row["description"])
        self.assertEqual(self.pulls_calls(), [new])        # `old..new` è calcolabile: solo `new`

    def test_rewind_is_forced_push(self):
        first = self.commit("a")
        second = self.commit("b")
        self.assertEqual(len(self.forced(second, first)), 1)

    def test_forced_push_adds_to_the_range_checks(self):
        old = self.commit("old")
        git(self.lab.repo, "checkout", "-q", "-b", "alt", self.start)
        mid, new = self.commit("mid"), self.commit("new")
        self.set_gh(pulls={new: [merged()]}, statuses={PR_HEAD: GREEN})
        self.push(old, new)
        self.assertEqual([c for c in (mid, new) if self.sentinel_statuses(c)], [mid, new])
        self.assertIn("push forzato", self.sentinel_statuses(new)[0]["description"])

    def test_fast_forward_is_not_forced(self):
        before = self.commit("a")
        self.assertEqual(self.forced(before, self.commit("b")), [])
        self.assertEqual(self.issues(), [])

    def test_other_branch_push_ignored(self):
        c = self.commit()
        path = self.event(self.start, c, ref="refs/heads/feature")
        self.assertEqual(sentinel.run(path, publish=True, environ=os.environ,
                                      repo=self.lab.repo, sleep=self.sleeps.append), 0)
        self.assertEqual(self.pulls_calls(), [])


class CrossCommandTest(test_gate_github.VerdictBase):
    """`gate evaluate` e `gate guard` scrivono gli stati nel `gh` finto; `gate sentinel` sul
    commit di merge li legge (Review Focus 4)."""

    def test_evaluate_then_sentinel_cross_command(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.assertEqual(self.run_verdict(), 0)
        state = paths.resolve_state(os.environ)
        github.set_status(state, self.lab.repo, SLUG, self.sha, context="tollgate/guard",
                          status="success", description="in regola")
        merge = self.lab.commit("src/merge.py", "m = 1\n", "merge")
        data = self.gh_data()
        data["commit_pulls"][merge] = [merged(1, head=self.sha)]
        self.data.write_text(json.dumps(data))
        path = self.tmp / "push.json"
        path.write_text(json.dumps({
            "ref": "refs/heads/main", "before": self.sha, "after": merge,
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        self.assertEqual(sentinel.run(path, publish=True, environ=os.environ,
                                      repo=self.lab.repo, sleep=lambda s: None), 0)
        got = self.gh_data()
        self.assertEqual(got["open_issues"], [])
        self.assertNotIn("tollgate/sentinel",
                         [r["context"] for r in got["commit_statuses"].get(merge, [])])

    def test_user_status_after_evaluate_is_not_trusted(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.assertEqual(self.run_verdict(), 0)
        state = paths.resolve_state(os.environ)
        github.set_status(state, self.lab.repo, SLUG, self.sha, context="tollgate/guard",
                          status="success", description="in regola")
        data = self.gh_data()
        for row in data["commit_statuses"][self.sha]:
            if row["context"] == "tollgate/verdict":
                row["creator"] = {"login": "mario"}
        merge = self.lab.commit("src/merge.py", "m = 1\n", "merge")
        data["commit_pulls"][merge] = [merged(1, head=self.sha)]
        self.data.write_text(json.dumps(data))
        path = self.tmp / "push.json"
        path.write_text(json.dumps({
            "ref": "refs/heads/main", "before": self.sha, "after": merge,
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        sentinel.run(path, publish=True, environ=os.environ, repo=self.lab.repo,
                     sleep=lambda s: None)
        self.assertEqual(len(self.gh_data()["open_issues"]), 1)


class ComponentOffTest(SentinelBase):
    toml = GATE_TOML + "[components]\nsentinel = false\n"

    def test_component_off_exits(self):
        c = self.commit()
        self.assertEqual(self.push(self.start, c), 0)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.sleeps, [])


class CliTest(SentinelBase):
    def test_publish_outside_actions_refused(self):
        c = self.commit()
        path = self.event(self.start, c)
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
            self.assertEqual(cli.main(["sentinel", "--event", str(path), "--publish"]), 1)
        self.assertIn("GitHub Actions", self.stderr.getvalue())
        self.assertEqual(self.calls(), [])

    def test_abbreviation_refused(self):
        with self.assertRaises(SystemExit):
            cli.build_parser().parse_args(["sentinel", "--event", "e", "--pub"])

    def test_sentinel_is_dispatched(self):
        ns = cli.build_parser().parse_args(["sentinel", "--event", "e", "--publish"])
        with mock.patch.object(sentinel, "run", return_value=0) as run:
            self.assertEqual(cli.HANDLERS["sentinel"](ns), 0)
        run.assert_called_once()
        self.assertEqual(run.call_args.args, (Path("e"),))
        self.assertTrue(run.call_args.kwargs["publish"])


class BasePublishBase(SentinelBase):
    def result(self, *states) -> dict:
        return {"v": 1, "tree": "t", "sha": self.lab.base,
                "ids": {f"c{i}": [] for i, _ in enumerate(states)},
                "commands": {f"c{i}": s for i, s in enumerate(states)}}

    def publish(self, result):
        baseids.publish(self.lab.repo, config_sha=self.lab.base, sha=self.lab.base,
                        result=result, environ=os.environ)

    def base_statuses(self) -> list[dict]:
        rows = self.gh_data().get("commit_statuses", {}).get(self.lab.base, [])
        return [r for r in rows if r["context"] == "tollgate/base"]


class BaseDetectTest(BasePublishBase):
    toml = GATE_TOML.replace("protected", "detect")

    def test_base_failure_comments_issue_in_detect(self):
        self.set_gh(open_issues=[{"number": 12, "title": ghcli.SENTINEL_TITLE,
                                  "url": "https://x/12"}])
        self.publish(self.result("green", "red"))
        [row] = self.base_statuses()
        self.assertEqual(row["state"], "failure")
        [note] = self.issues()[0]["comments"]
        self.assertIn(self.lab.base, note["body"])
        self.assertIn("`c1`", note["body"])
        self.assertNotIn("`c0`", note["body"])

    def test_base_failure_creates_the_issue_if_missing(self):
        self.publish(self.result("red"))
        [issue] = self.issues()
        self.assertEqual(issue["title"], ghcli.SENTINEL_TITLE)
        self.assertIn(self.lab.base, issue["body"])

    def test_unverified_commands_are_in_the_description(self):
        self.publish(self.result("red", "unverified", "unverified"))
        [row] = self.base_statuses()
        self.assertIn("non verificati", row["description"])
        self.assertLessEqual(len(row["description"]), 140)
        self.publish(self.result("green", "unverified"))
        self.assertIn("non verificati", self.base_statuses()[0]["description"])
        self.assertEqual(self.base_statuses()[0]["state"], "success")

    def test_base_status_written_before_the_issue(self):
        self.publish(self.result("red"))
        writes = [a[-1] for a in self.calls() if "--method" in a]
        self.assertEqual(writes[0].split("/")[3], "statuses")

    def test_base_green_in_detect_is_success_without_comment(self):
        self.publish(self.result("green", "green"))
        self.assertEqual([r["state"] for r in self.base_statuses()], ["success"])
        self.assertEqual(self.issues(), [])


class BaseProtectedTest(BasePublishBase):
    def test_protected_mode_publishes_nothing(self):
        self.publish(self.result("red"))
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
