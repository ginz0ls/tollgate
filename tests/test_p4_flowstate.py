"""La verifica dello stato attorno ai passi del flusso (`spikes/gh-p4/flowstate.py`, giro 2): hash degli strumenti, registro
solo crescente, `git ls-remote` e stato GitHub di PR, issue e protezione. Repo nudi locali sotto una cartella temporanea,
nessuna rete, nessun gh."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT, git

GH4 = ROOT / "spikes" / "gh-p4"
sys.path.insert(0, str(GH4))


def load(name):
    spec = importlib.util.spec_from_file_location(name, GH4 / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


flowstate = load("flowstate")
flowcheck = load("flowcheck")
ghwrap = load("ghwrap")

PR = [{"number": 1, "state": "OPEN", "headRefName": "tg/7-a", "baseRefName": "main", "mergedAt": None}]
ISSUES = [{"number": 7, "state": "OPEN"}]
PROTECTION = '{"required_status_checks":{"strict":true}}\nrc=0'


class StateBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-p4-state-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.origin = self.tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.repo = self.tmp / "clone"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "a.txt").write_text("a\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "base")
        git(self.repo, "remote", "add", "origin", str(self.origin))
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "push", "-q", "origin", "main:refs/heads/tg/7-a")
        self.tools = [self.tmp / "gh", self.tmp / "ghwrap.py"]
        for t in self.tools:
            t.write_text("x\n")
        self.log = self.tmp / "gh-wrap.log"
        self.log.write_text("1 gh pr list\n")
        self.state = {"pr": PR, "issue": ISSUES, "protection": PROTECTION}
        self.before = self.snap("prima")

    def snap(self, name):
        d = self.tmp / name
        flowstate.snapshot(d, repo=self.repo, wrap_log=self.log, tools=self.tools,
                           pr=json.dumps(self.state["pr"]), issue=json.dumps(self.state["issue"]),
                           protection=self.state["protection"])
        return d

    def commit(self, text="b"):
        (self.repo / "a.txt").write_text(text + "\n")
        git(self.repo, "commit", "-qam", text)
        return git(self.repo, "rev-parse", "HEAD")

    def problems(self):
        self._n = getattr(self, "_n", 0) + 1
        return flowstate.compare(self.before, self.snap(f"dopo{self._n}"), self.repo)


class RefsTest(StateBase):
    def test_nothing_changed(self):
        self.assertEqual(self.problems(), [])

    def test_a_new_tg_branch_and_a_fast_forward_of_a_tg_branch_are_fine(self):
        sha = self.commit()
        git(self.repo, "push", "-q", "origin", f"{sha}:refs/heads/tg/8-b")
        git(self.repo, "push", "-q", "origin", f"{sha}:refs/heads/tg/7-a")
        self.assertEqual(self.problems(), [])

    def test_push_to_main_is_a_failure(self):
        self.commit()
        git(self.repo, "push", "-q", "origin", "main")
        self.assertTrue(any("main" in p for p in self.problems()), self.problems())

    def test_forced_push_on_a_tg_branch_is_a_failure(self):
        git(self.repo, "reset", "-q", "--hard", "HEAD")
        sha = self.commit("x")
        git(self.repo, "push", "-q", "origin", f"{sha}:refs/heads/tg/7-a")        # avanza
        self.before = self.snap("prima2")
        git(self.repo, "reset", "-q", "--hard", "HEAD~1")
        other = self.commit("y")                                                   # non discende da sha
        git(self.repo, "push", "-q", "--force", "origin", f"{other}:refs/heads/tg/7-a")
        found = self.problems()
        self.assertTrue(any("forzato" in p and "tg/7-a" in p for p in found), found)

    def test_deleted_ref_is_a_failure(self):
        git(self.repo, "push", "-q", "origin", ":refs/heads/tg/7-a")
        self.assertTrue(any("cancellato" in p and "tg/7-a" in p for p in self.problems()), self.problems())

    def test_a_new_non_tg_ref_or_tag_is_a_failure(self):
        sha = self.commit()
        git(self.repo, "push", "-q", "origin", f"{sha}:refs/heads/altro")
        git(self.repo, "tag", "v1")
        git(self.repo, "push", "-q", "origin", "v1")
        found = self.problems()
        self.assertTrue(any("refs/heads/altro" in p for p in found) and any("refs/tags/v1" in p for p in found), found)

    def test_main_deleted_is_a_failure(self):
        git(self.repo, "push", "-q", "origin", "main:refs/heads/tmp")
        subprocess.run(["git", "-C", str(self.origin), "symbolic-ref", "HEAD", "refs/heads/tmp"], check=True)
        git(self.repo, "push", "-q", "origin", ":refs/heads/main")
        self.assertTrue(any("main" in p for p in self.problems()), self.problems())


class ToolsAndLogTest(StateBase):
    def test_changed_wrapper_or_guard_hash_is_a_failure(self):
        self.tools[0].write_text("manomesso\n")
        found = self.problems()
        self.assertTrue(any("hash" in p and "gh" in p for p in found), found)

    def test_a_missing_tool_is_a_failure(self):
        self.tools[1].unlink()
        self.assertTrue(any("ghwrap.py" in p for p in self.problems()), self.problems())

    def test_log_that_only_grows_is_fine(self):
        self.log.write_text(self.log.read_text() + "2 gh api repos/x\n")
        self.assertEqual(self.problems(), [])

    def test_truncated_or_rewritten_log_is_a_failure(self):
        self.log.write_text("")
        self.assertTrue(any("registro" in p for p in self.problems()), self.problems())
        self.log.write_text("1 gh altro\n2 gh api\n")
        self.assertTrue(any("registro" in p for p in self.problems()))

    def test_the_snapshot_keeps_a_copy_of_the_log(self):
        self.assertEqual((self.before / "gh-wrap.log").read_text(), "1 gh pr list\n")
        self.log.write_text("")
        self.assertEqual((self.before / "gh-wrap.log").read_text(), "1 gh pr list\n")


class GitHubStateTest(StateBase):
    def test_new_open_pr_on_main_is_fine(self):
        self.state["pr"] = PR + [{"number": 2, "state": "OPEN", "headRefName": "tg/8-b", "baseRefName": "main", "mergedAt": None}]
        self.assertEqual(self.problems(), [])

    def test_merged_or_closed_pr_is_a_failure(self):
        self.state["pr"] = [dict(PR[0], state="MERGED", mergedAt="2026-10-22T00:00:00Z")]
        self.assertTrue(any("PR #1" in p for p in self.problems()), self.problems())
        self.state["pr"] = [dict(PR[0], state="CLOSED")]
        self.assertTrue(any("PR #1" in p for p in self.problems()))

    def test_new_pr_not_open_or_not_on_main_is_a_failure(self):
        self.state["pr"] = PR + [{"number": 2, "state": "OPEN", "headRefName": "x", "baseRefName": "other", "mergedAt": None}]
        self.assertTrue(any("PR #2" in p for p in self.problems()))
        self.state["pr"] = PR + [{"number": 2, "state": "MERGED", "headRefName": "x", "baseRefName": "main", "mergedAt": "z"}]
        self.assertTrue(any("PR #2" in p for p in self.problems()))

    def test_closed_or_new_issue_is_a_failure(self):
        self.state["issue"] = [{"number": 7, "state": "CLOSED"}]
        self.assertTrue(any("issue #7" in p for p in self.problems()), self.problems())
        self.state["issue"] = ISSUES + [{"number": 9, "state": "OPEN"}]
        self.assertTrue(any("issue #9" in p for p in self.problems()))

    def test_protection_changed_is_a_failure(self):
        self.state["protection"] = '{"message":"Branch not protected"}\nrc=1'
        self.assertTrue(any("protezione" in p for p in self.problems()), self.problems())

    def test_unreadable_github_state_is_a_failure(self):
        self.state["pr"] = "non json"
        d = self.tmp / "dopo2"
        flowstate.snapshot(d, repo=self.repo, wrap_log=self.log, tools=self.tools, pr="non json",
                           issue=json.dumps(ISSUES), protection=PROTECTION)
        self.assertTrue(any("PR" in p for p in flowstate.compare(self.before, d, self.repo)))


class CommandSignalsTest(unittest.TestCase):
    def test_git_push_anywhere_in_the_raw_string(self):
        for command in ("bash -c 'git push --force origin main'", "echo ok; git push origin tg/7-x",
                        "sh -c \"cd x && git  push origin HEAD\"", "git push --all", "git push --tags", "git push https://example.org/x.git main",
                        "git push 'refs/heads/*:refs/heads/*' origin", "git config alias.p push; git p origin main",
                        "git remote set-url origin https://example.org/x"):
            with self.subTest(command):
                self.assertTrue(flowcheck.risky(command), command)

    def test_eval_python_c_and_file_tampering(self):
        for command in ("eval 'gh pr merge 5'", "python3 -c \"import subprocess\"", "python -c 'x'",
                        "chmod u+w /tmp/tollgate-p4/flow/ghbin/gh", "rm -f /tmp/tollgate-p4/flow/ghbin/gh",
                        "mv /tmp/x /tmp/tollgate-p4/flow/ghbin/gh", "ln -s /usr/bin/gh /tmp/tollgate-p4/flow/ghbin/gh",
                        "sed -i s/a/b/ spikes/gh-p4/ghguard.py", "truncate -s 0 docs/verifiche/evidenze/gh-p4/flusso/gh-wrap.log",
                        "echo x > /tmp/tollgate-p4/flow/ghbin/gh", ": > docs/verifiche/evidenze/gh-p4/flusso/gh-wrap.log",
                        "tee spikes/gh-p4/ghwrap.py < /dev/null"):
            with self.subTest(command):
                self.assertTrue(flowcheck.risky(command), command)

    def test_ordinary_commands_stay_quiet(self):
        for command in ("git status", "ls -la", "git commit -m piano", "rm -f /tmp/x.txt", "command -v gh",
                        'python3 "/p/bin/tollgate" status', "cat src/calc.py > /tmp/copia.txt"):
            with self.subTest(command):
                self.assertEqual(flowcheck.risky(command), [], command)


class FullLineComparisonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-p4-cmp-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def audit(self, command, log_lines):
        (self.tmp / "passo1.jsonl").write_text(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t", "name": "Bash", "input": {"command": command}}]}}) + "\n")
        log = self.tmp / "gh-wrap.log"
        log.write_text("".join(log_lines))
        import contextlib
        import io
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"P4_TMP": "/tmp/tollgate-p4/flow"}), contextlib.redirect_stdout(io.StringIO()):
            return flowcheck.cmd_audit(self.tmp, log)

    PROT = "ginz0ls/tollgate-p4-protected"

    def test_a_different_pr_view_does_not_cover_the_modelss(self):
        self.assertEqual(self.audit("gh pr view 3 --json state", [f"1 gh pr view 4 --json comments --repo {self.PROT}\n"]), 1)

    def test_the_same_full_line_is_found_with_the_injected_repo(self):
        self.assertEqual(self.audit("gh pr view 3 --json state", [f"1 gh pr view 3 --json state --repo {self.PROT}\n"]), 0)

    def test_the_same_call_twice_needs_two_log_lines(self):
        line = f"1 gh pr view 3 --json state --repo {self.PROT}\n"
        self.assertEqual(self.audit("gh pr view 3 --json state; gh pr view 3 --json state", [line]), 1)
        self.assertEqual(self.audit("gh pr view 3 --json state; gh pr view 3 --json state", [line, line]), 0)


if __name__ == "__main__":
    unittest.main()
