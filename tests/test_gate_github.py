import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.flowkit import FAKEGH
from tests.gatekit import BRANCH, DEFAULT_IDS, GATE_TOML, ISSUE, GateLab
from tests.helpers import TempState, git
from tollgate_analysis import prblock
from tollgate_core import ghcli
from tollgate_gate import baseids, cli, comment, github, verdict

SLUG = "o/r"
RUN_PATH = ".github/workflows/tollgate-run.yml"
XML = ('<testsuite><testcase classname="tests.test_app" name="test_somma"/>'
       '<testcase classname="tests.test_app" name="test_zero"/></testsuite>')
SENTINEL = {"number": 12, "title": ghcli.SENTINEL_TITLE, "url": "https://x/12"}


class VerdictBase(unittest.TestCase):
    def setUp(self):
        self.lab = GateLab()
        self.ts = TempState()
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate verdict "))
        self.data, self.log = self.tmp / "gh data.json", self.tmp / "gh.log"
        self.art = self.tmp / "art"
        self.addCleanup(self.lab.close)
        self.addCleanup(self.ts.cleanup)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        env = mock.patch.dict(os.environ, {
            "TOLLGATE_STATE": str(self.ts.dir), "TOLLGATE_GH": str(FAKEGH),
            "TOLLGATE_FAKEGH_DATA": str(self.data), "TOLLGATE_FAKEGH_LOG": str(self.log),
            "GITHUB_REPOSITORY": SLUG, "GITHUB_ACTIONS": "true"})
        env.start()
        self.addCleanup(env.stop)
        self.sha = self.lab.head
        self.push_pr_head()
        self.write_artifacts()
        self.set_gh()

    # --- banco ---------------------------------------------------------------------------

    def push_pr_head(self, number=1):
        git(self.lab.repo, "push", "-q", "-f", "origin", f"HEAD:refs/pull/{number}/head")

    def pr_body(self, **block):
        return f"Closes #{ISSUE}\n" + prblock.render(self.lab.block(**block))

    def rest_pull(self, **override) -> dict:
        pull = {"number": 1, "state": "open", "body": self.pr_body(),
                "head": {"sha": self.sha, "ref": BRANCH, "repo": {"full_name": SLUG}},
                "base": {"ref": "main"}}
        pull.update(override)
        return pull

    def set_gh(self, *, pull=None, issue=None, comments=None, **extra):
        data = {"prs": [{"number": 1, "comments": comments or []}],
                "pulls": {"1": pull or self.rest_pull()},
                "issues": {str(ISSUE): issue or {"number": ISSUE, "state": "OPEN", "labels": []}},
                "open_issues": [], "commit_pulls": {}}
        data.update(extra)
        self.data.write_text(json.dumps(data))

    def gh_data(self) -> dict:
        return json.loads(self.data.read_text())

    def calls(self) -> list[list[str]]:
        return [json.loads(x)["argv"] for x in self.log.read_text().splitlines()] \
            if self.log.exists() else []

    def statuses(self, sha=None) -> dict:
        """L'ultimo stato per contesto del commit."""
        rows = self.gh_data().get("commit_statuses", {}).get(sha or self.sha, [])
        return {r["context"]: r for r in reversed(rows)}

    def comments(self) -> list[dict]:
        return self.gh_data()["prs"][0]["comments"]

    def write_artifacts(self, *, sha=None, config_sha=None, commands=None, applicable=True,
                        xml=XML, report="junit/0.xml"):
        shutil.rmtree(self.art, ignore_errors=True)
        (self.art / "junit").mkdir(parents=True)
        (self.art / "junit" / "0.xml").write_text(xml)
        entry = {"name": "verify", "state": "green", "exit": 0, "tests_run": 2,
                 "tests_skipped": 0, "report": report}
        (self.art / "results.json").write_text(json.dumps({
            "v": 1, "applicable": applicable, "sha": sha or self.sha,
            "config_sha": config_sha or self.lab.base,
            "commands": [entry] if commands is None else commands}))

    def ids_file(self, directory: Path, *, tree=None, ids=DEFAULT_IDS) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        tree = tree or git(self.lab.repo, "rev-parse", f"{self.lab.base}^{{tree}}")
        path = directory / "ids.json"
        path.write_text(json.dumps({"v": baseids.IDS_VERSION, "tree": tree, "sha": self.lab.base,
                                    "ids": {"verify": list(ids)},
                                    "commands": {"verify": "green"}}))
        return path

    def event(self, *, path=RUN_PATH, event="pull_request", sha=None, pull_requests=None) -> Path:
        sha = sha or self.sha
        listed = [{"number": 1, "base": {"ref": "main", "sha": self.lab.base},
                   "head": {"ref": BRANCH, "sha": sha}}] if pull_requests is None \
            else pull_requests
        out = self.tmp / "event.json"
        out.write_text(json.dumps({
            "workflow_run": {"path": path, "event": event, "head_sha": sha,
                             "head_branch": BRANCH, "conclusion": "success", "id": 99,
                             "pull_requests": listed},
            "repository": {"full_name": SLUG, "default_branch": "main"}}))
        return out

    def run_verdict(self, event=None, *, publish=True, cache=None, artifact=None) -> int:
        if cache is None and artifact is None:
            cache = self.ids_file(self.tmp / "cache")
        return verdict.main(event or self.event(), artifacts=self.art, base_ids_cache=cache,
                            base_ids_artifact=artifact, publish=publish, environ=os.environ,
                            repo=self.lab.repo)

    def assert_error(self, reason=None, *, sha=None):
        got = self.statuses(sha)
        self.assertEqual({k: v["state"] for k, v in got.items()},
                         {"tollgate/verdict": "error", "tollgate/attention": "error"})
        if reason:
            self.assertIn(reason, got["tollgate/verdict"]["description"])
        return got


class OutcomeTest(VerdictBase):
    def test_clean_pr_green(self):
        self.assertEqual(self.run_verdict(), 0)
        got = self.statuses()
        self.assertEqual(got["tollgate/verdict"]["state"], "success")
        self.assertEqual(got["tollgate/attention"]["state"], "success")
        [c] = self.comments()
        self.assertEqual(comment.marker_sha(c["body"]), self.sha)
        self.assertTrue(c["body"].startswith(comment.marker(self.sha)))

    def test_red_pr_is_failure_with_comment(self):
        self.write_artifacts(xml='<testsuite><testcase classname="tests.test_app" '
                                 'name="test_somma"/></testsuite>')
        self.run_verdict()
        got = self.statuses()
        self.assertEqual(got["tollgate/verdict"]["state"], "failure")
        self.assertIn("voci da correggere", got["tollgate/verdict"]["description"])
        self.assertIn("tests.test_app::test_zero", self.comments()[0]["body"])

    def test_sentinel_issue_open_in_attention(self):
        self.set_gh(open_issues=[SENTINEL, {"number": 13, "title": "altra", "url": "u"}])
        self.run_verdict()
        got = self.statuses()
        self.assertEqual(got["tollgate/verdict"]["state"], "success")
        self.assertEqual(got["tollgate/attention"]["state"], "failure")
        self.assertIn("sentinel", self.comments()[0]["body"])

    def test_closes_a_pr_number_is_red(self):
        self.set_gh(issue={"number": ISSUE, "state": "OPEN", "labels": [],
                           "pull_request": {"url": "u"}})
        self.run_verdict()
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "failure")
        self.assertIn(f"#{ISSUE} è una PR, non un'issue", self.comments()[0]["body"])

    def test_fork_pr_treated_as_manual(self):
        """Un ramo `tg/*` da un fork non è un lavoro di tollgate (decisione 4): nessun blocco
        richiesto, solo `not_tg_branch`."""
        body = f"Closes #{ISSUE}\n"
        pull = self.rest_pull(body=body, head={"sha": self.sha, "ref": BRANCH,
                                               "repo": {"full_name": "altro/r"}})
        self.set_gh(pull=pull)
        self.run_verdict()
        got = self.statuses()
        self.assertEqual(got["tollgate/verdict"]["state"], "success")
        self.assertEqual(got["tollgate/attention"]["state"], "failure")
        text = self.comments()[0]["body"]
        self.assertIn("fuori dai rami tg/*", text)
        self.assertNotIn("blocco JSON", text)

    def test_deleted_fork_repo_is_a_fork(self):
        pull = self.rest_pull(body="", head={"sha": self.sha, "ref": BRANCH, "repo": None})
        self.set_gh(pull=pull)
        self.run_verdict()
        self.assertIn("fuori dai rami tg/*", self.comments()[0]["body"])

    def test_no_publish_prints_and_writes_nothing(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.run_verdict(publish=False), 0)
        self.assertIn("verdict: success", out.getvalue())
        self.assertNotIn("commit_statuses", self.gh_data())
        self.assertEqual(self.comments(), [])
        self.assertFalse(any("POST" in a or "PATCH" in a for argv in self.calls()
                             for a in argv))

    def test_no_publish_red_exits_1(self):
        self.set_gh(issue={"number": ISSUE, "state": "CLOSED", "labels": []})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.run_verdict(publish=False), 1)


class PrechecksTest(VerdictBase):
    def pre(self, event=None, pr="default", shared=()):
        ev = json.loads((event or self.event()).read_text())
        pr = self.rest_pull() if pr == "default" else pr
        return verdict.prechecks(ev, pr, default_branch="main", open_prs_for_sha=list(shared))

    def test_prechecks(self):
        self.assertEqual(self.pre(), ("ok", ""))
        self.assertEqual(self.pre(shared=[{"number": 1}])[0], "ok")
        for kw in ({"path": ".github/workflows/altro.yml"}, {"event": "push"},
                   {"event": "pull_request_target"}):
            with self.subTest(kw):
                self.assertEqual(self.pre(self.event(**kw))[0], "error")
        self.assertEqual(self.pre(pr=None)[0], "error")
        self.assertEqual(self.pre(shared=[{"number": 1}, {"number": 2}]),
                         ("error", "SHA condiviso da più PR: chiudine una"))
        self.assertEqual(self.pre(pr=self.rest_pull(head={"sha": "b" * 40, "ref": BRANCH}))[0],
                         "error")

    def test_other_base_is_not_applicable_not_error(self):
        outcome, reason = self.pre(pr=self.rest_pull(base={"ref": "other"}))
        self.assertEqual(outcome, "not_applicable")
        self.assertIn("non applicabile", reason)

    def test_wrong_workflow_path_writes_error_status(self):
        self.run_verdict(self.event(path=".github/workflows/tollgate-run.yml.evil"))
        self.assert_error("tollgate-run.yml")
        self.assertEqual(self.comments(), [])

    def test_wrong_event_writes_error_status(self):
        self.run_verdict(self.event(event="pull_request_target"))
        self.assert_error()
        self.assertEqual(self.comments(), [])

    def test_not_applicable_writes_no_status(self):
        """Una PR verso `other` sulla stessa testa: gli stati sono per SHA, vincerebbe l'ultimo
        scritto (rilievo C-1). Solo il commento «non applicabile»."""
        self.set_gh(pull=self.rest_pull(base={"ref": "other"}))
        self.assertEqual(self.run_verdict(), 0)
        self.assertNotIn("commit_statuses", self.gh_data())
        [c] = self.comments()
        self.assertIn("non applicabile", c["body"])
        self.assertTrue(c["body"].startswith(verdict.NA_PREFIX))
        self.assertNotIn("<!-- tollgate-verdict", c["body"])
        self.run_verdict()                       # una seconda corsa lo aggiorna
        self.assertEqual(len(self.comments()), 1)

    def test_other_base_next_to_default_base_pr(self):
        """Due PR sulla stessa testa, una verso `other`: la prima è giudicata, la seconda
        riceve solo il commento."""
        self.set_gh(pulls={"1": self.rest_pull(), "2": self.rest_pull(number=2,
                                                                      base={"ref": "other"})},
                    prs=[{"number": 1, "comments": []}, {"number": 2, "comments": []}])
        both = [{"number": n} for n in (1, 2)]
        self.run_verdict(self.event(pull_requests=both))
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "success")
        prs = {p["number"]: p["comments"] for p in self.gh_data()["prs"]}
        self.assertTrue(prs[2][0]["body"].startswith(verdict.NA_PREFIX))
        self.assertTrue(prs[1][0]["body"].startswith("<!-- tollgate-verdict"))

    def test_sha_shared_by_two_prs_is_error(self):
        pulls = [{"number": n, "state": "open", "merged_at": None, "base": {"ref": "main"},
                  "head": {"sha": self.sha}} for n in (1, 2)]
        self.set_gh(commit_pulls={self.sha: pulls})
        self.assertEqual(self.run_verdict(), 0)
        self.assert_error("SHA condiviso")
        self.assertEqual(self.comments(), [])

    def test_pr_found_from_commit_when_event_has_none(self):
        """Per una PR da fork `workflow_run.pull_requests` è vuoto: si cerca dal commit."""
        pulls = [{"number": 1, "state": "open", "merged_at": None, "base": {"ref": "main"},
                  "head": {"sha": self.sha}}]
        self.set_gh(commit_pulls={self.sha: pulls})
        self.run_verdict(self.event(pull_requests=[]))
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "success")

    def test_no_pr_at_all_is_error(self):
        self.run_verdict(self.event(pull_requests=[]))
        self.assert_error("nessuna PR")

    def test_superseded_sha_is_error(self):
        """La PR ha una testa nuova: `error` sullo SHA vecchio, nessun commento."""
        self.set_gh(pull=self.rest_pull(head={"sha": "b" * 40, "ref": BRANCH,
                                              "repo": {"full_name": SLUG}}))
        self.assertEqual(self.run_verdict(), 0)
        self.assert_error("SHA superato")
        self.assertEqual(self.comments(), [])
        self.assertEqual(self.statuses("b" * 40), {})

    def test_head_rechecked_just_before_writing(self):
        """Se la PR avanza mentre `verdict` lavora, di quello SHA non si scrive nulla."""
        real, seen = github.pull, []

        def advancing(state, cwd, slug, n):
            seen.append(n)
            pull = real(state, cwd, slug, n)
            if len(seen) > 1:       # dalla seconda lettura (il ricontrollo) la testa è nuova
                pull["head"]["sha"] = "c" * 40
            return pull

        out = io.StringIO()
        with mock.patch.object(github, "pull", advancing), contextlib.redirect_stdout(out):
            self.assertEqual(self.run_verdict(), 0)
        self.assertIn("nessuna scrittura", out.getvalue())
        self.assertGreaterEqual(len(seen), 2)
        self.assertNotIn("commit_statuses", self.gh_data())
        self.assertEqual(self.comments(), [])


class ArtifactsTest(VerdictBase):
    def test_missing_or_invalid_artifact_is_error(self):
        entity = ('<!DOCTYPE x [<!ENTITY e "boom">]><testsuite><testcase classname="a" '
                  'name="&e;"/></testsuite>')
        cases = {
            "assente": lambda: shutil.rmtree(self.art),
            "report con ../": lambda: self.write_artifacts(report="../outside.xml"),
            "report assoluto": lambda: self.write_artifacts(report="/etc/passwd"),
            "xml con entità": lambda: self.write_artifacts(xml=entity),
            "collegamento": lambda: (self.art / "junit" / "1.xml").symlink_to("/etc/passwd"),
        }
        for name, setup in cases.items():
            with self.subTest(name):
                self.write_artifacts()
                setup()
                self.set_gh()
                self.assertEqual(self.run_verdict(), 0)
                got = self.assert_error()
                self.assertEqual(got["tollgate/verdict"]["description"], verdict.DESC_ARTIFACTS)
                self.assertTrue(self.comments()[0]["body"].startswith(
                    comment.marker(self.sha)))

    def test_config_changed_after_run_is_error(self):
        self.write_artifacts(config_sha="d" * 40)
        self.run_verdict()
        got = self.assert_error("configurazione del gate cambiata")
        self.assertIn("rilancia i controlli", got["tollgate/verdict"]["description"])
        self.assertIn("rilancia i controlli", self.comments()[0]["body"])

    def test_results_of_another_sha_is_error(self):
        self.write_artifacts(sha="e" * 40)
        self.run_verdict()
        self.assert_error()
        self.assertIn("non è dello SHA giudicato", self.comments()[0]["body"])

    def test_results_not_applicable_for_a_default_pr_is_error(self):
        self.write_artifacts(applicable=False, commands=[])
        self.run_verdict()
        self.assert_error()

    def test_invalid_default_config_is_error(self):
        git(self.lab.repo, "checkout", "-q", "main")
        self.lab.commit("tollgate.toml", "schema_version = 99\n", "config rotta")
        git(self.lab.repo, "push", "-q", "origin", "main")
        git(self.lab.repo, "checkout", "-q", BRANCH)
        self.assertEqual(self.run_verdict(), 0)       # nessun traceback, nessuna eccezione
        got = self.assert_error()
        self.assertIn("schema_version", got["tollgate/verdict"]["description"])
        self.assertIn("schema_version", self.comments()[0]["body"])

    def test_read_results_fills_meta_from_the_same_read(self):
        from tollgate_gate import artifacts
        meta = {}
        _, applicable, problems = artifacts.read_results(self.art, meta=meta)
        self.assertEqual((applicable, problems), (True, []))
        self.assertEqual(meta, {"sha": self.sha, "config_sha": self.lab.base})


class BaseIdsTest(VerdictBase):
    EXTRA = (*DEFAULT_IDS, "tests.test_app::test_gone")

    def keys_in_comment(self) -> str:
        return self.comments()[0]["body"]

    def test_base_ids_source_order(self):
        """Cache dell'albero di `merge-base`, poi artefatto, poi errore (Review Focus 7)."""
        cache = self.ids_file(self.tmp / "cache", ids=self.EXTRA)      # chiede un test in più
        artifact = self.ids_file(self.tmp / "artifact", ids=DEFAULT_IDS).parent
        # 1. cache valida: vince, l'artefatto si ignora
        self.run_verdict(cache=cache, artifact=artifact)
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "failure")
        self.assertIn("test_gone", self.keys_in_comment())
        self.assertNotIn("run della PR", self.keys_in_comment())
        for label, stale in (("albero diverso", self.ids_file(self.tmp / "c2", tree="f" * 40,
                                                              ids=self.EXTRA)),
                             ("assente", self.tmp / "nessuna" / "ids.json")):
            with self.subTest(label):
                self.set_gh()
                # 2. senza cache valida si usa l'artefatto e compare `base_ids_from_run`
                self.run_verdict(cache=stale, artifact=artifact)
                got = self.statuses()
                self.assertEqual(got["tollgate/verdict"]["state"], "success")
                self.assertEqual(got["tollgate/attention"]["state"], "failure")
                self.assertIn("run della PR", self.keys_in_comment())
        # 3. nessuna delle due: errore
        self.set_gh()
        self.run_verdict(cache=self.tmp / "nessuna" / "ids.json",
                         artifact=self.tmp / "nessuno")
        self.assert_error()
        self.assertIn("identificativi della base non disponibili", self.keys_in_comment())

    def test_artifact_ids_of_another_tree_or_symlink_are_ignored(self):
        artifact = self.ids_file(self.tmp / "artifact", tree="f" * 40).parent
        self.run_verdict(cache=self.tmp / "nessuna" / "ids.json", artifact=artifact)
        self.assert_error()
        good = self.ids_file(self.tmp / "real")
        link = self.tmp / "link"
        link.mkdir()
        (link / "ids.json").symlink_to(good)
        self.set_gh()
        self.run_verdict(cache=self.tmp / "nessuna" / "ids.json", artifact=link)
        self.assert_error()

    def test_ids_are_per_command(self):
        """Gli identificativi di un altro comando non rendono rosso `verify`."""
        cache = self.ids_file(self.tmp / "cache")
        data = json.loads(cache.read_text())
        data["ids"]["profile:web:test"] = ["web/a.test.js::x"]
        cache.write_text(json.dumps(data))
        self.run_verdict(cache=cache)
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "success")

    def test_base_test_ids_off_needs_no_ids(self):
        lab = GateLab(toml=GATE_TOML + "[components]\nbase_test_ids = false\n")
        self.addCleanup(lab.close)
        git(self.lab.repo, "checkout", "-q", "main")
        self.lab.commit("tollgate.toml", lab.toml, "senza base ids")
        git(self.lab.repo, "push", "-q", "origin", "main")
        git(self.lab.repo, "checkout", "-q", BRANCH)
        self.write_artifacts(config_sha=git(self.lab.repo, "rev-parse", "origin/main"))
        self.run_verdict(cache=self.tmp / "nessuna" / "ids.json")
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "success")


class CommentTest(VerdictBase):
    def test_comment_updated_not_duplicated(self):
        self.run_verdict()
        self.run_verdict()
        self.assertEqual(len(self.comments()), 1)
        self.assertTrue(any("PATCH" in argv for argv in self.calls()))

    def test_other_authors_comment_with_same_marker_is_left_alone(self):
        fake = {"id": 5, "author": {"login": "mario"},
                "body": comment.marker(self.sha) + "\nfinto"}
        self.set_gh(comments=[fake])
        self.run_verdict()
        by_author = {c["author"]["login"]: c for c in self.comments()}
        self.assertEqual(by_author["mario"]["body"], fake["body"])
        self.assertEqual(len(self.comments()), 2)
        self.assertIn("verdetto sullo SHA", by_author["github-actions"]["body"])

    def test_more_than_100_comments_are_paginated(self):
        filler = [{"id": 100 + n, "author": {"login": "utente"}, "body": f"c{n}"}
                  for n in range(120)]
        mine = {"id": 900, "author": {"login": "github-actions"},
                "body": comment.marker(self.sha) + "\nvecchio"}
        self.set_gh(comments=[*filler, mine])
        self.run_verdict()
        self.assertEqual(len(self.comments()), 121)
        self.assertIn("verdetto sullo SHA", self.comments()[-1]["body"])
        listing = next(a for a in self.calls() if a[-1].endswith("/comments?per_page=100"))
        self.assertIn("--paginate", listing)

    def test_text_goes_through_files_not_arguments(self):
        self.set_gh(pull=self.rest_pull(body=self.pr_body() + "\nCORPO-OSTILE"))
        self.run_verdict()
        for argv in self.calls():
            self.assertNotIn("CORPO-OSTILE", " ".join(argv))
        self.assertTrue(any(a.startswith("body=@") for argv in self.calls() for a in argv))


class NoCacheWriteTest(VerdictBase):
    def snapshot(self):
        return sorted(p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*")
                      if "gh" not in p.name and p.name != "event.json")

    def test_verdict_never_writes_cache(self):
        """Un job `workflow_run` ha la cache in sola lettura: con nessun esito `verdict` scrive
        file di cache o identificativi della testa."""
        cache = self.ids_file(self.tmp / "cache")
        before_text = cache.read_text()
        outcomes = {
            "verde": lambda: None,
            "rosso": lambda: self.set_gh(issue={"number": ISSUE, "state": "CLOSED",
                                                "labels": []}),
            "errore": lambda: shutil.rmtree(self.art),
        }
        for name, setup in outcomes.items():
            with self.subTest(name):
                self.write_artifacts()
                self.set_gh()
                setup()
                before = self.snapshot()
                self.run_verdict(cache=cache)
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(cache.read_text(), before_text)
        self.assertEqual(sorted(p.name for p in cache.parent.iterdir()), ["ids.json"])

    def test_no_head_ids_option(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cli.build_parser().parse_args(["evaluate", "--event", "e", "--artifacts", "a",
                                           "--head-ids-out", "x"])


class CliTest(VerdictBase):
    def test_evaluate_parses(self):
        ns = cli.build_parser().parse_args([
            "evaluate", "--event", "e.json", "--artifacts", "art", "--base-ids-cache", "c.json",
            "--base-ids-artifact", "b", "--publish"])
        self.assertEqual((ns.gate_cmd, ns.event, ns.artifacts, ns.base_ids_cache,
                          ns.base_ids_artifact, ns.publish),
                         ("evaluate", "e.json", "art", "c.json", "b", True))

    def test_publish_refused_outside_actions(self):
        env = {k: v for k, v in os.environ.items() if k != "GITHUB_ACTIONS"}
        err = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), contextlib.redirect_stderr(err):
            code = cli.main(["evaluate", "--event", str(self.event()), "--artifacts",
                             str(self.art), "--publish"])
        self.assertEqual(code, 1)
        self.assertIn("GitHub Actions", err.getvalue())
        self.assertNotIn("commit_statuses", self.gh_data())

    def test_end_to_end_through_cli(self):
        cache = self.ids_file(self.tmp / "cache")
        cwd = os.getcwd()
        os.chdir(self.lab.repo)
        self.addCleanup(os.chdir, cwd)
        code = cli.main(["evaluate", "--event", str(self.event()), "--artifacts", str(self.art),
                         "--base-ids-cache", str(cache), "--publish"])
        self.assertEqual(code, 0)
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "success")

    def chdir_repo(self):
        cwd = os.getcwd()
        os.chdir(self.lab.repo)
        self.addCleanup(os.chdir, cwd)

    def test_read_failure_writes_explicit_error_through_cli(self):
        """`pulls/<n>` assente: gh esce con 1, ma gli stati si possono scrivere."""
        self.set_gh(pulls={})
        self.chdir_repo()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = cli.main(["evaluate", "--event", str(self.event()), "--artifacts",
                             str(self.art), "--publish"])
        self.assertEqual(code, 0)
        self.assert_error(verdict.DESC_ERROR)
        self.assertNotIn("Traceback", err.getvalue())

    def test_status_write_failure_is_a_clean_refusal(self):
        """Se nemmeno lo stato si scrive l'uscita è 1, senza traceback."""
        self.set_gh(pulls={}, api_status={f"repos/{SLUG}/statuses/{self.sha}": {
            "status": 403, "message": "Forbidden", "body": {"message": "Forbidden"}}})
        self.chdir_repo()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = cli.main(["evaluate", "--event", str(self.event()), "--artifacts",
                             str(self.art), "--publish"])
        self.assertEqual(code, 1)
        self.assertIn("gate evaluate:", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertNotIn("commit_statuses", self.gh_data())


class BoundaryTest(VerdictBase):
    """Con `--publish`, noto lo SHA, ogni esito scrive `error` espliciti (decisione 5)."""

    def assert_explicit_error(self):
        got = self.assert_error(verdict.DESC_ERROR)
        self.assertLessEqual(len(got["tollgate/verdict"]["description"]), 140)

    def test_unexpected_failures_write_explicit_error(self):
        real_pull = github.pull
        calls = []

        def pull_fails_on_recheck(state, cwd, slug, n):
            calls.append(n)
            if len(calls) > 1:
                raise ghcli.GhError("rate limit")
            return real_pull(state, cwd, slug, n)

        bad_head = self.rest_pull(head={"sha": self.sha, "repo": {"full_name": SLUG}})
        cases = {
            "shared": lambda: mock.patch.object(github, "shared_sha_prs",
                                                side_effect=ghcli.GhError("HTTP 502")),
            "pull": lambda: mock.patch.object(github, "pull",
                                              side_effect=ghcli.GhError("HTTP 500")),
            "recheck": lambda: mock.patch.object(github, "pull", pull_fails_on_recheck),
            "pr_from_rest": lambda: _set(self, pull=bad_head),
            "evaluate": lambda: mock.patch.object(verdict.evaluate, "evaluate",
                                                  side_effect=RuntimeError("boom")),
        }
        for name, setup in cases.items():
            with self.subTest(name):
                self.set_gh()
                calls.clear()
                with setup(), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(self.run_verdict(), 0)
                self.assert_explicit_error()
                self.assertEqual(self.comments(), [])

    def test_unwritable_status_exits_1(self):
        err = io.StringIO()
        with mock.patch.object(github, "shared_sha_prs", side_effect=ghcli.GhError("x")), \
                mock.patch.object(github, "set_status", side_effect=ghcli.GhError("403")), \
                contextlib.redirect_stderr(err):
            self.assertEqual(self.run_verdict(), 1)
        self.assertIn("403", err.getvalue())

    def test_no_publish_prints_reason_and_exits_nonzero(self):
        err = io.StringIO()
        with mock.patch.object(github, "shared_sha_prs", side_effect=ghcli.GhError("HTTP 502")), \
                contextlib.redirect_stderr(err):
            self.assertNotEqual(self.run_verdict(publish=False), 0)
        self.assertIn("HTTP 502", err.getvalue())
        self.assertNotIn("commit_statuses", self.gh_data())

    def test_not_applicable_and_superseded_still_write_no_error(self):
        self.set_gh(pull=self.rest_pull(base={"ref": "other"}))
        self.run_verdict()
        self.assertNotIn("commit_statuses", self.gh_data())


@contextlib.contextmanager
def _set(case, **kw):
    case.set_gh(**kw)
    yield


class MinorsTest(VerdictBase):
    def test_not_applicable_comment_skips_pr_with_another_head(self):
        other = self.rest_pull(number=2, base={"ref": "other"},
                               head={"sha": "b" * 40, "ref": "x", "repo": {"full_name": SLUG}})
        self.set_gh(pulls={"1": self.rest_pull(), "2": other},
                    prs=[{"number": 1, "comments": []}, {"number": 2, "comments": []}])
        self.run_verdict(self.event(pull_requests=[{"number": 1}, {"number": 2}]))
        prs = {p["number"]: p["comments"] for p in self.gh_data()["prs"]}
        self.assertEqual(prs[2], [])
        self.assertEqual(len(prs[1]), 1)

    def test_not_applicable_comment_rechecks_head(self):
        real, calls = github.pull, []

        def advancing(state, cwd, slug, n):
            calls.append(n)
            pull = real(state, cwd, slug, n)
            if len(calls) > 1:
                pull["head"]["sha"] = "c" * 40
            return pull

        self.set_gh(pull=self.rest_pull(base={"ref": "other"}))
        with mock.patch.object(github, "pull", advancing):
            self.run_verdict()
        self.assertEqual(self.comments(), [])

    def test_closed_pr_from_payload_is_ignored(self):
        self.set_gh(pull=self.rest_pull(state="closed"))
        self.run_verdict()
        self.assert_error("nessuna PR")

    def test_closed_pr_with_same_head_is_not_chosen(self):
        self.set_gh(pulls={"1": self.rest_pull(state="closed"), "2": self.rest_pull(number=2)},
                    prs=[{"number": 1, "comments": []}, {"number": 2, "comments": []}])
        self.run_verdict(self.event(pull_requests=[{"number": 1}, {"number": 2}]))
        prs = {p["number"]: p["comments"] for p in self.gh_data()["prs"]}
        self.assertEqual((len(prs[1]), len(prs[2])), (0, 1))

    def test_malformed_recheck_response_writes_nothing(self):
        real, calls = github.pull, []

        def malformed(state, cwd, slug, n):
            calls.append(n)
            pull = real(state, cwd, slug, n)
            if len(calls) > 1:
                pull.pop("head")
            return pull

        with mock.patch.object(github, "pull", malformed), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.run_verdict(), 0)
        self.assertNotIn("commit_statuses", self.gh_data())

    def test_fork_pr_with_closed_issue_is_red(self):
        pull = self.rest_pull(body=f"Closes #{ISSUE}\n",
                              head={"sha": self.sha, "ref": BRANCH,
                                    "repo": {"full_name": "altro/r"}})
        self.set_gh(pull=pull, issue={"number": ISSUE, "state": "CLOSED", "labels": []})
        self.run_verdict()
        self.assertEqual(self.statuses()["tollgate/verdict"]["state"], "failure")
        self.assertIn("non è aperta", self.comments()[0]["body"])


class IssueRuleTest(unittest.TestCase):
    """La regola «issue della PR» sta in `evaluate.pr_issue_number`, usata anche da `verdict`."""

    def pr(self, ref, body="", cross=False):
        from tollgate_gate.model import PrFacts
        return PrFacts(1, "a" * 40, ref, "main", "main", body, cross)

    def test_rule(self):
        from tollgate_gate import evaluate
        cases = [(self.pr("tg/7-x", "Closes #9"), 7), (self.pr("tg/7-x"), 7),
                 (self.pr("tg/7-x", "Closes #9", cross=True), 9),
                 (self.pr("tg/7-x", cross=True), None), (self.pr("fix/x", "Fixes #4"), 4),
                 (self.pr("fix/x"), None)]
        for pr, want in cases:
            with self.subTest(pr=pr):
                self.assertEqual(evaluate.pr_issue_number(pr), want)

    def test_verdict_has_no_copy(self):
        self.assertFalse(hasattr(verdict, "_issue_number"))


class SharedShaPrsTest(VerdictBase):
    """`github.shared_sha_prs`, riusata da `prechecks`: coperta qui direttamente."""

    def shared(self, pulls) -> list[int]:
        self.set_gh(commit_pulls={self.sha: pulls})
        got = github.shared_sha_prs(self.ts.state, self.lab.repo, SLUG, self.sha, "main")
        return [p["number"] for p in got]

    def row(self, number, *, state="open", base="main", sha=None):
        return {"number": number, "state": state, "merged_at": None, "base": {"ref": base},
                "head": {"sha": sha or self.sha}}

    def test_two_open_prs_with_same_head(self):
        self.assertEqual(self.shared([self.row(1), self.row(2)]), [1, 2])

    def test_stacked_pr_has_another_head(self):
        self.assertEqual(self.shared([self.row(1), self.row(2, sha="b" * 40)]), [1])

    def test_closed_pr_does_not_count(self):
        self.assertEqual(self.shared([self.row(1), self.row(2, state="closed")]), [1])

    def test_other_base_does_not_count(self):
        self.assertEqual(self.shared([self.row(1), self.row(2, base="other")]), [1])

    def test_a_number_counts_once(self):
        self.assertEqual(self.shared([self.row(1), self.row(1)]), [1])


if __name__ == "__main__":
    unittest.main()
