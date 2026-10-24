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
        self.assertTrue(any(f"repos/{SLUG}/commits/{c}/pulls" in a[-1] for a in self.calls()))

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
        # nessun rosso: solo l'ultimo commit lascia il segnale «controllato fino a qui»
        self.assertEqual([c for c in commits if self.sentinel_statuses(c)], [commits[-1]])
        self.assertEqual([r["state"] for r in self.sentinel_statuses(commits[-1])], ["success"])
        # un commit del push che non viene dalla PR è l'unico rosso: la risalita si ferma al
        # segnale e `direct` resta `failure`
        direct = self.commit("d")
        data = self.gh_data()       # niente `set_gh`: il segnale scritto dal codice deve restare
        data["commit_pulls"] = {c: [merged()] for c in commits}
        self.data.write_text(json.dumps(data))
        self.push(self.start, direct)
        self.assertEqual([c for c in (*commits, direct) if self.sentinel_statuses(c)],
                         [commits[-1], direct])
        self.assertEqual([r["state"] for r in self.sentinel_statuses(direct)], ["failure"])

    def test_first_install_ignored(self):
        before = self.start
        first = self.commit("a")
        install = self.lab.commit(WORKFLOW, "on: push\n", "installa sentinel")
        self.assertEqual(self.push(before, install), 0)
        self.assertEqual(self.issues(), [])
        self.assertEqual(self.pulls_calls(), [])
        later = self.commit("b")           # il commit dopo l'installazione conta
        self.push(before, later)
        # l'installazione lascia il segnale; `first` resta senza stati
        self.assertEqual([c for c in (first, install, later) if self.sentinel_statuses(c)],
                         [install, later])
        self.assertEqual([r["state"] for r in self.sentinel_statuses(install)], ["success"])
        self.assertEqual([r["state"] for r in self.sentinel_statuses(later)], ["failure"])

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
        after = self.commit("b")
        self.assertEqual([r["state"] for r in self.forced(before, after)], ["success"])
        self.assertEqual(self.issues(), [])

    def test_other_branch_push_ignored(self):
        c = self.commit()
        path = self.event(self.start, c, ref="refs/heads/feature")
        self.assertEqual(sentinel.run(path, publish=True, environ=os.environ,
                                      repo=self.lab.repo, sleep=self.sleeps.append), 0)
        self.assertEqual(self.pulls_calls(), [])


class SkipCiTest(SentinelBase):
    """Decisione 16, Review Focus 4: ogni push controllato lascia il segnale `success`
    «controllato fino a qui»; il push successivo risale fino a lui, così i commit di un push
    saltato con `[skip ci]` si controllano comunque."""

    def asked_since(self, n) -> list[str]:
        """Gli SHA di cui `commits/<sha>/pulls` è stato letto dopo la n-esima chiamata."""
        return list(dict.fromkeys(a[-1].split("/")[4] for a in self.calls()[n:]
                                  if "/pulls?" in a[-1]))

    def clean_push(self, before, after, *, head=PR_HEAD):
        self.set_gh(pulls={after: [merged(head=head)]}, statuses={head: GREEN})
        self.assertEqual(self.push(before, after), 0)

    def chain(self, count, parent) -> list[str]:
        """`count` commit vuoti in fila su `parent` (con `commit-tree`, senza muovere rami)."""
        tree = git(self.lab.repo, "rev-parse", f"{parent}^{{tree}}")
        out = []
        for i in range(count):
            parent = git(self.lab.repo, "commit-tree", tree, "-p", parent, "-m", f"c{i}")
            out.append(parent)
        return out

    def test_clean_push_writes_success_marker(self):
        c = self.commit()
        self.clean_push(self.start, c)
        [row] = self.sentinel_statuses(c)
        self.assertEqual((row["state"], row["description"]),
                         ("success", sentinel.CHECKED_DESCRIPTION))
        self.assertEqual(row["creator"]["login"], BOT)
        self.assertEqual(self.issues(), [])

    def test_dry_run_writes_no_marker(self):
        c = self.commit()
        self.set_gh(pulls={c: [merged()]}, statuses={PR_HEAD: GREEN})
        self.assertEqual(self.push(self.start, c, publish=False), 0)
        self.assertEqual(self.sentinel_statuses(c), [])

    def test_red_after_gets_failure_not_success(self):
        c = self.commit()
        self.push(self.start, c)
        self.assertEqual([r["state"] for r in self.sentinel_statuses(c)], ["failure"])

    def test_success_marker_on_after_even_if_an_earlier_commit_is_red(self):
        direct, via_pr = self.commit("d"), self.commit("p")
        self.set_gh(pulls={via_pr: [merged()]}, statuses={PR_HEAD: GREEN})
        self.push(self.start, via_pr)
        self.assertEqual([r["state"] for r in self.sentinel_statuses(direct)], ["failure"])
        self.assertEqual([r["state"] for r in self.sentinel_statuses(via_pr)], ["success"])
        self.assertEqual(len(self.issues()), 1)

    def test_skipped_push_checked_next_time(self):
        p0 = self.commit("p0")
        self.clean_push(self.start, p0)             # il codice scrive il segnale su p0
        skipped = self.commit("a")                  # push con `[skip ci]`: nessuna corsa
        after = self.commit("b")
        n = len(self.calls())
        self.assertEqual(self.push(skipped, after), 0)      # `before` del push B è `skipped`
        self.assertEqual(self.asked_since(n), [skipped, after])     # si ferma al segnale di p0
        self.assertEqual([r["state"] for r in self.sentinel_statuses(skipped)], ["failure"])
        self.assertEqual([r["state"] for r in self.sentinel_statuses(after)], ["failure"])
        self.assertEqual([r["state"] for r in self.sentinel_statuses(p0)], ["success"])
        [issue] = self.issues()
        self.assertIn(skipped, issue["body"])

    def test_walk_stops_at_a_failure_marker_too(self):
        direct = self.commit("d")
        self.push(self.start, direct)               # `failure` sul commit: è comunque controllato
        after = self.commit("e")
        n = len(self.calls())
        self.push(direct, after)
        self.assertEqual(self.asked_since(n), [after])
        self.assertEqual(len(self.sentinel_statuses(direct)), 1)

    def test_user_written_sentinel_status_ignored(self):
        p0, mid, after = self.commit("p0"), self.commit("m"), self.commit("z")
        self.clean_push(self.start, p0)
        data = self.gh_data()
        data["commit_statuses"].setdefault(mid, []).insert(0, {
            "context": "tollgate/sentinel", "state": "success", "description": "mio",
            "creator": {"login": "mario"}})
        self.data.write_text(json.dumps(data))
        n = len(self.calls())
        self.push(p0, after)
        self.assertEqual(self.asked_since(n), [mid, after])  # il segnale di `mid` non salta niente

    def test_user_marker_on_after_parent_does_not_skip_commits(self):
        """Lo stesso, con `github-actions` senza `[bot]` (un nome utente qualunque)."""
        p0, mid, after = self.commit("p0"), self.commit("m"), self.commit("z")
        self.clean_push(self.start, p0)
        data = self.gh_data()
        data["commit_statuses"].setdefault(mid, []).insert(0, {
            "context": "tollgate/sentinel", "state": "success",
            "creator": {"login": "github-actions"}})
        self.data.write_text(json.dumps(data))
        n = len(self.calls())
        self.push(p0, after)
        self.assertEqual(self.asked_since(n), [mid, after])

    def test_other_context_marker_does_not_stop_the_walk(self):
        after = self.commit("z")
        data = self.gh_data()
        data["commit_statuses"][self.start] = [
            {"context": "tollgate/verdict", "state": "success", "creator": {"login": BOT}}]
        self.data.write_text(json.dumps(data))
        self.assertIsNone(sentinel.last_checked(
            self.lab.repo, after, lambda sha: self.gh_data()["commit_statuses"].get(sha, [])))

    def test_last_checked_returns_the_first_marker_going_up(self):
        a, b, c = self.commit("a"), self.commit("b"), self.commit("c")
        rows = {a: [status("tollgate/sentinel", "failure")],
                b: [status("tollgate/sentinel", "success")]}
        got = sentinel.last_checked(self.lab.repo, c, lambda sha: rows.get(sha, []))
        self.assertEqual(got, b)
        self.assertIsNone(sentinel.last_checked(self.lab.repo, a, lambda sha: []))

    def test_last_checked_follows_first_parent_only(self):
        side_base = self.commit("s0")
        git(self.lab.repo, "checkout", "-q", "-b", "side", self.start)
        side = self.commit("s1")
        git(self.lab.repo, "checkout", "-q", "-")
        git(self.lab.repo, "merge", "-q", "--no-ff", "-m", "merge", "side")
        merge = git(self.lab.repo, "rev-parse", "HEAD")
        rows = {side: [status("tollgate/sentinel", "success")],
                self.start: [status("tollgate/sentinel", "success")]}
        asked = []
        got = sentinel.last_checked(self.lab.repo, merge,
                                    lambda sha: asked.append(sha) or rows.get(sha, []))
        self.assertEqual(got, self.start)           # `side` ha il segnale ma non è sul filo
        self.assertEqual(asked, [side_base, self.start])

    def test_no_marker_walk_bounded(self):
        commits = self.chain(sentinel.WALK_LIMIT + 10, self.start)
        before, after = commits[-5], commits[-1]
        asked = []
        got = sentinel.unverified(
            self.lab.repo, before=before, after=after, default_branch="main",
            prs_for_commit=lambda sha: [], statuses=lambda sha: asked.append(sha) or [],
            attempts=1, sleep=self.sleeps.append)
        self.assertEqual(sentinel.WALK_LIMIT, 200)
        self.assertEqual(len(asked), 200)                   # al più 200 GET, poi `before`
        self.assertEqual([sha for sha, _ in got], commits[-4:])

    def test_forced_push_still_uses_before(self):
        old = self.commit("old")
        git(self.lab.repo, "checkout", "-q", "-b", "alt", self.start)
        mid, new = self.commit("mid"), self.commit("new")
        data = self.gh_data()
        data["commit_statuses"][mid] = [status("tollgate/sentinel", "success")]
        data["commit_pulls"] = {new: [merged()]}
        data["commit_statuses"][PR_HEAD] = GREEN
        self.data.write_text(json.dumps(data))
        self.push(old, new)                         # un segnale su `mid` non accorcia l'intervallo
        self.assertEqual(self.pulls_calls(), [mid, new])
        self.assertIn("push forzato", self.sentinel_statuses(new)[0]["description"])

    def test_before_all_zeros_checks_only_after(self):
        c = self.commit()
        self.push(ZEROS, c)
        self.assertEqual(self.pulls_calls(), [c])
        self.assertFalse(any("/commits/" in a[-1] and "/statuses" in a[-1]
                             for a in self.calls()))

    def test_first_install_still_ignored(self):
        p0 = self.commit("p0")
        self.clean_push(self.start, p0)
        first = self.commit("a")
        install = self.lab.commit(WORKFLOW, "on: push\n", "installa sentinel")
        n = len(self.calls())
        self.assertEqual(self.push(p0, install), 0)
        self.assertEqual(self.asked_since(n), [])
        self.assertEqual(self.issues(), [])
        self.assertEqual([c for c in (first, install) if self.sentinel_statuses(c)], [install])

    def test_single_issue(self):
        skipped, b = self.commit("a"), self.commit("b")
        self.push(self.start, b)                    # a e b rossi: un'issue
        c = self.commit("c")
        self.push(b, c)                             # la risalita parte da `b`: solo `c`
        [issue] = self.issues()
        [note] = issue["comments"]
        self.assertIn(c, note["body"])
        self.assertNotIn(b, note["body"])
        self.assertIn(skipped, issue["body"])


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
        # il commit di merge è verificato: riceve il segnale «controllato fino a qui», non un rosso
        self.assertEqual([r["state"] for r in got["commit_statuses"].get(merge, [])
                          if r["context"] == "tollgate/sentinel"], ["success"])

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

    def publish(self, result) -> int:
        return baseids.publish(self.lab.repo, config_sha=self.lab.base, sha=self.lab.base,
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

    def test_red_suite_exits_1_after_status_and_issue(self):
        # I-1: il job `tollgate-base` è rosso se la suite della base è rossa
        self.assertEqual(self.publish(self.result("green", "red")), 1)
        self.assertEqual([r["state"] for r in self.base_statuses()], ["failure"])
        self.assertEqual(len(self.issues()), 1)

    def test_green_suite_exits_0(self):
        self.assertEqual(self.publish(self.result("green", "unverified")), 0)


class BaseProtectedTest(BasePublishBase):
    def test_protected_mode_publishes_nothing(self):
        # I-1: in `protected` non c'è uno stato, il segnale è il job rosso
        self.assertEqual(self.publish(self.result("red")), 1)
        self.assertEqual(self.calls(), [])

    def test_protected_green_exits_0_without_writing(self):
        self.assertEqual(self.publish(self.result("green", "unverified")), 0)
        self.assertEqual(self.calls(), [])


class BasePublishFromTest(BasePublishBase):
    """`gate base-publish` (C-1): pubblica dai dati dell'artefatto di `ids`, che non si fidano."""
    toml = GATE_TOML.replace("protected", "detect")

    def ids_dir(self, content=None, *, tree=None, commands=None, symlink=False) -> Path:
        d = self.tmp / "ids"
        d.mkdir(exist_ok=True)
        if content is None:
            content = json.dumps({
                "v": 1, "tree": tree or git(self.lab.repo, "rev-parse",
                                            f"{self.lab.base}^{{tree}}"),
                "sha": "f" * 40, "ids": {"verify": []},
                "commands": commands or {"verify": "green"}})
        if symlink:
            (d / "real.json").write_text(content)
            (d / "ids.json").symlink_to(d / "real.json")
        elif content is not False:
            (d / "ids.json").write_text(content)
        return d

    def publish_from(self, d, *, publish=True) -> int:
        return baseids.publish_from(self.lab.repo, config_sha=self.lab.base, sha=self.lab.base,
                                    ids_dir=d, environ=os.environ, publish=publish)

    def assert_error(self, d):
        self.data.write_text(json.dumps({"commit_pulls": {}, "commit_statuses": {},
                                         "open_issues": []}))
        self.assertEqual(self.publish_from(d), 1)
        [row] = self.base_statuses()
        self.assertEqual(row["state"], "error")
        self.assertEqual(self.issues(), [])

    def test_valid_data_publishes_the_status_even_from_a_cache_hit(self):
        # su un cache hit `sha` è quello del commit che ha riempito la cache: conta l'albero;
        # la suite rossa rende rosso anche il job (I-1)
        self.assertEqual(self.publish_from(self.ids_dir(commands={"verify": "red"})), 1)
        [row] = self.base_statuses()
        self.assertEqual(row["state"], "failure")
        self.assertIn("`verify`", self.issues()[0]["body"])

    def test_green_data_is_success(self):
        self.assertEqual(self.publish_from(self.ids_dir()), 0)
        self.assertEqual([r["state"] for r in self.base_statuses()], ["success"])

    def test_without_publish_nothing_is_written(self):
        self.assertEqual(self.publish_from(self.ids_dir(), publish=False), 0)
        self.assertEqual(self.publish_from(self.ids_dir(commands={"verify": "red"}),
                                           publish=False), 1)
        self.assertEqual(self.calls(), [])

    def test_missing_artifact_is_error(self):
        self.assert_error(self.ids_dir(False))
        self.assert_error(self.tmp / "nessuna")

    def test_other_tree_is_error(self):
        self.assert_error(self.ids_dir(tree="0" * 40))

    def test_hostile_json_is_error(self):
        tree = git(self.lab.repo, "rev-parse", f"{self.lab.base}^{{tree}}")
        for text in ("{", "[" * 100000, "[]", json.dumps({"v": 2, "tree": tree}),
                     json.dumps({"v": 1, "tree": tree, "commands": []}),
                     json.dumps({"v": 1, "tree": tree, "commands": {"verify": "verde"}}),
                     json.dumps({"v": 1, "tree": tree, "commands": {"verify": 1}}),
                     json.dumps({"v": 1, "tree": tree, "commands": {"x`\n# evil": "red"}})):
            with self.subTest(text=text[:40]):
                self.assert_error(self.ids_dir(text))
                self.data.write_text(json.dumps({"commit_pulls": {}, "commit_statuses": {},
                                                 "open_issues": []}))

    def test_symlink_and_oversize_are_error(self):
        self.assert_error(self.ids_dir(symlink=True, content="{}"))
        self.data.write_text(json.dumps({"commit_pulls": {}, "commit_statuses": {},
                                         "open_issues": []}))
        self.assert_error(self.ids_dir(" " * (baseids.MAX_IDS_FILE + 1)))

    def test_cli_handler_reads_the_push_event(self):
        event = self.event(self.start, self.lab.base)
        ns = cli.build_parser().parse_args(["base-publish", "--ids", str(self.ids_dir()),
                                            "--event", str(event), "--publish"])
        with mock.patch.object(Path, "cwd", return_value=self.lab.repo):
            self.assertEqual(cli.HANDLERS["base-publish"](ns), 0)
        self.assertEqual([r["state"] for r in self.base_statuses()], ["success"])


class BasePublishProtectedErrorTest(BasePublishBase):
    def test_protected_mode_writes_no_status_but_fails(self):
        tmp = self.tmp / "ids"
        tmp.mkdir()
        self.assertEqual(baseids.publish_from(
            self.lab.repo, config_sha=self.lab.base, sha=self.lab.base, ids_dir=tmp,
            environ=os.environ, publish=True), 1)
        self.assertEqual(self.calls(), [])

    def test_protected_red_suite_fails_without_writing(self):
        d = self.tmp / "ids"
        d.mkdir()
        tree = git(self.lab.repo, "rev-parse", f"{self.lab.base}^{{tree}}")
        for states, code in (({"verify": "red"}, 1), ({"verify": "green"}, 0)):
            with self.subTest(states=states):
                (d / "ids.json").write_text(json.dumps({
                    "v": 1, "tree": tree, "sha": self.lab.base, "ids": {"verify": []},
                    "commands": states}))
                self.assertEqual(baseids.publish_from(
                    self.lab.repo, config_sha=self.lab.base, sha=self.lab.base, ids_dir=d,
                    environ=os.environ, publish=True), code)
                self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
