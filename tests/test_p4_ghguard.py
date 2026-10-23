"""La lista degli ammessi dei gh della prova reale (`spikes/gh-p4/ghguard.py`, decisione 25), il gh con guardia
(`ghwrap.py`) e i controlli del flusso (`flowcheck.py`). Nessuna rete: il gh «vero» è uno script che registra gli argomenti."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers import ROOT

GH4 = ROOT / "spikes" / "gh-p4"
sys.path.insert(0, str(GH4))


def load(name):
    spec = importlib.util.spec_from_file_location(name, GH4 / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ghguard = load("ghguard")
flowcheck = load("flowcheck")

PROT, DET = ghguard.PROT, ghguard.DET


def quiet(fn, *args):
    """Il valore di `fn` senza il testo che stampa."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)
SHA = "a" * 40


class GuardBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate p4 guard "))
        (self.tmp / "out").mkdir()
        (self.tmp / "work").mkdir()
        patcher = mock.patch.dict(os.environ, {"P4_OUT": str(self.tmp / "out"), "P4_WORK": str(self.tmp / "work"),
                                               "P4_TMP": str(self.tmp / "flow"), "TMPDIR": ""})
        patcher.start()
        os.environ.pop("TMPDIR")
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def ok(self, *args, profile="script"):
        self.assertIsNone(ghguard.violation(list(args), profile=profile), " ".join(args))

    def no(self, *args, profile="script"):
        self.assertIsNotNone(ghguard.violation(list(args), profile=profile), " ".join(args))


class WriteFormsTest(GuardBase):
    def status(self, repo=PROT, sha=SHA, **over):
        fields = {"state": "success", "context": "tollgate/verdict", "description": "prova-token-personale-p4"}
        fields.update(over)
        args = ["api", "--method", "POST", f"repos/{repo}/statuses/{sha}"]
        for k, v in fields.items():
            args += ["-f", f"{k}={v}"]
        return args

    def test_post_status_of_the_personal_token_case(self):
        self.ok(*self.status())
        self.ok(*self.status(repo=DET))
        self.ok(*self.status(state="failure"))
        args = self.status()
        args[1:3] = ["-X", "POST"]
        self.ok(*args)

    def test_post_status_rejects_everything_else(self):
        self.no(*self.status(context="tollgate/guard"))
        self.no(*self.status(state="boh"))
        self.no(*self.status(description="altro"))
        self.no(*self.status(sha="abc"))
        self.no(*self.status(repo=f"{ghguard.OWNER}/altro"))
        self.no(*self.status(), "-f", "target_url=x")
        self.no(*self.status()[:-2])                                   # manca il campo description
        self.no("api", "--method", "POST", f"repos/{PROT}/issues", "-f", "title=x")
        self.no("api", "--method", "POST", f"repos/{PROT}/statuses/{SHA}", "-F", "state=success")
        self.no("api", "--method=POST", f"repos/{PROT}/statuses/{SHA}")
        self.no("api", "-XPOST", f"repos/{PROT}/issues")
        self.no("api", "--method", "PATCH", f"repos/{PROT}/issues/1", "-f", "state=closed")

    def test_protection_put_and_delete_only_on_protected(self):
        body = "/tmp/tmp.abc123"
        self.ok("api", "--method", "PUT", "--input", body, f"repos/{PROT}/branches/main/protection")
        self.ok("api", "--method", "DELETE", f"repos/{PROT}/branches/main/protection")
        self.no("api", "--method", "PUT", "--input", body, f"repos/{DET}/branches/main/protection")
        self.no("api", "--method", "DELETE", f"repos/{DET}/branches/main/protection")
        self.no("api", "--method", "PUT", "--input", body, f"repos/{PROT}/branches/dev/protection")
        self.no("api", "--method", "PUT", "--input", "/etc/passwd", f"repos/{PROT}/branches/main/protection")
        self.no("api", "--method", "PUT", "--input", "relativo.json", f"repos/{PROT}/branches/main/protection")
        self.no("api", "--method", "PUT", "--input", f"{self.tmp}/out/../x", f"repos/{PROT}/branches/main/protection")
        self.no("api", "--method", "PUT", f"repos/{PROT}/branches/main/protection")        # senza --input
        self.no("api", "--method", "PUT", "--input", body, "-f", "a=b", f"repos/{PROT}/branches/main/protection")
        self.no("api", "--method", "DELETE", "--input", body, f"repos/{PROT}/branches/main/protection")
        self.no("api", "--method", "PUT", "--input", body, f"repos/{PROT}/branches/main/protection/required_status_checks")

    def test_the_flow_profile_allows_no_api_writes(self):
        self.no(*self.status(), profile="flow")
        self.no("api", "--method", "DELETE", f"repos/{PROT}/branches/main/protection", profile="flow")
        self.no("api", "--method", "PUT", "--input", "/tmp/x", f"repos/{PROT}/branches/main/protection", profile="flow")


class FlowCloneTest(GuardBase):
    """Il clone del flusso (imposto dal brief) è ammesso solo per protected e solo nella cartella esatta."""

    FLOW_DIR = "/tmp/tollgate-p4/flow/protected"

    def test_the_flow_clone_of_protected_is_allowed(self):
        self.ok("repo", "clone", PROT, self.FLOW_DIR, "--", "-q")
        self.ok("repo", "clone", PROT, self.FLOW_DIR)

    def test_other_repo_or_folder_is_refused(self):
        self.no("repo", "clone", DET, self.FLOW_DIR, "--", "-q")
        self.no("repo", "clone", PROT, "/tmp/tollgate-p4/flow/altro", "--", "-q")
        self.no("repo", "clone", PROT, "/tmp/tollgate-p4/flow/protected/../x", "--", "-q")
        self.no("repo", "clone", PROT, "/tmp/tollgate-p4/flow/protected/sotto", "--", "-q")
        self.no("repo", "clone", PROT, "/tmp/tollgate-p4/flow", "--", "-q")

    def test_the_flow_profile_still_refuses_repo_clone(self):
        self.no("repo", "clone", PROT, self.FLOW_DIR, "--", "-q", profile="flow")


class PullBodyPatchTest(GuardBase):
    """L'unica scrittura nuova (scelta dell'utente del 22/10/2026): `api --method PATCH repos/<protected>/pulls/<n> -F body=@<file>`,
    perché `gh pr edit` non funziona con gh 2.46."""

    def patch(self, repo=PROT, number="3", body=None, extra=()):
        body = body or f"{self.tmp}/out/body.md"
        return ["api", "--method", "PATCH", f"repos/{repo}/pulls/{number}", "-F", f"body=@{body}", *extra]

    def test_the_exact_form_is_allowed_in_both_profiles(self):
        self.ok(*self.patch())
        self.ok(*self.patch(body="/tmp/tollgate-body/b.md"))
        self.ok(*self.patch(body=f"{self.tmp}/flow/wt/.tollgate-run/7/pr-body.md"), profile="flow")
        args = self.patch()
        args = [args[0], args[3], args[4], args[5], args[1], args[2]]       # altro ordine
        self.ok(*args)

    def test_everything_else_is_refused(self):
        self.no(*self.patch(repo=DET))
        self.no(*self.patch(repo=f"{ghguard.OWNER}/altro"))
        self.no(*self.patch(number="3/merge"))
        self.no(*self.patch(number="x"))
        self.no("api", "--method", "PATCH", f"repos/{PROT}/pulls/3/merge", "-F", f"body=@{self.tmp}/out/b.md")
        self.no("api", "--method", "PATCH", f"repos/{PROT}/issues/3", "-F", f"body=@{self.tmp}/out/b.md")
        self.no(*self.patch(extra=["-f", "title=x"]))
        self.no(*self.patch(extra=["-F", "title=@/tmp/x"]))
        self.no(*self.patch(extra=["--input", "/tmp/x"]))
        self.no("api", "--method", "PATCH", f"repos/{PROT}/pulls/3", "-f", "body=testo")
        self.no("api", "--method", "PATCH", f"repos/{PROT}/pulls/3", "-F", "body=testo")
        self.no("api", "--method", "PATCH", f"repos/{PROT}/pulls/3", "-F", "state=@/tmp/x")
        self.no("api", "-X", "PATCH", f"repos/{ghguard.OWNER}/altro/pulls/3", "-F", "body=@/tmp/x")
        self.no(*self.patch(body="/etc/passwd"))
        self.no(*self.patch(body="relativo.md"))
        self.no(*self.patch(body="/tmp/tollgate-body/b.md"), profile="flow")      # nel flusso solo sotto $FLOW
        self.no("api", "--method", "DELETE", f"repos/{PROT}/pulls/3")

    def test_comandi_log_accepts_the_patch(self):
        log = self.tmp / "out" / "comandi.log"
        log.write_text(f"2026-10-22T00:00:00Z gh api --method PATCH repos/{PROT}/pulls/3 -F body=@{self.tmp}/out/b.md\n")
        r = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghguard.py"), "comandi", str(log)], capture_output=True,
                           text=True, env={**os.environ, "P4_OUT": str(self.tmp / "out"), "P4_WORK": str(self.tmp / "work")})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class ReadFormsTest(GuardBase):
    def test_reads_that_the_scripts_use(self):
        self.ok("api", "--paginate", f"repos/{PROT}/commits/{SHA}/statuses?per_page=100", "--jq",
                ".[] | {context, state, creator: .creator.login}")
        self.ok("api", f"repos/{PROT}/pulls/3")
        self.ok("api", "--include", f"repos/{DET}/branches/main/protection")
        self.ok("api", "--paginate", "--jq", ".check_runs[] | [.status] | @tsv", f"repos/{PROT}/commits/{SHA}/check-runs?per_page=100")
        self.ok("pr", "list", "--repo", PROT, "--head", "tg/7-x", "--state", "all", "--limit", "100", "--json",
                "number,state,url,headRefOid")
        self.ok("issue", "list", "--repo", DET, "--state", "open", "--limit", "100", "--json", "number,title")
        self.ok("issue", "view", "5", "--repo", DET, "--json", "number,title,comments")
        self.ok("issue", "create", "--repo", PROT, "--title", "prova", "--body", "testo con spazi")
        self.ok("issue", "close", "5", "--repo", PROT)
        self.ok("run", "watch", "9", "--repo", PROT)

    def test_body_file_only_from_known_folders(self):
        f = self.tmp / "out" / "body.md"
        self.ok("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t", "--body-file", str(f))
        self.ok("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t",
                "--body-file", "/tmp/tollgate-body/body.md")
        self.ok("pr", "edit", "3", "--repo", PROT, "--body-file", "/tmp/tollgate-body/body.md")
        self.no("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t", "--body-file", "/etc/passwd")
        self.no("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t", "--body-file", "body.md")
        self.no("pr", "comment", "1", "--repo", PROT, "--body-file", "/home/utente/.ssh/id_rsa")
        self.no("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t",
                "--body-file", str(self.tmp / "out" / ".." / "x"))

    def test_still_forbidden_as_before(self):
        for args in (["api", "user"], ["api", "graphql"], ["api", "-X", "POST", f"repos/{PROT}/issues"],
                     ["api", "-fstate=x", f"repos/{PROT}/statuses/{SHA}"], ["api", "--input=x", f"repos/{PROT}/issues"],
                     ["api", "-F", "a=b", f"repos/{PROT}/issues"], ["api", "--raw-field=a=b", f"repos/{PROT}/issues"],
                     ["repo", "delete", PROT], ["repo", "edit", PROT, "--visibility", "public"], ["auth", "refresh"],
                     ["pr", "merge", "1", "--repo", PROT], ["pr", "list", "--repo", "altro/x"],
                     ["run", "delete", "1", "--repo", PROT], ["secret", "set", "X"]):
            self.no(*args)

    def test_flow_profile_forbids_what_the_flow_never_does(self):
        self.ok("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t",
                "--body-file", f"{self.tmp}/flow/wt/.tollgate-run/7/pr-body.md", profile="flow")
        for args in (["issue", "create", "--repo", PROT, "--title", "x"], ["pr", "merge", "1", "--repo", PROT, "--squash"],
                     ["pr", "close", "1", "--repo", PROT], ["repo", "clone", PROT], ["run", "download", "1", "--repo", PROT]):
            self.no(*args, profile="flow")

    def test_check_cli_reads_the_profile_from_the_environment(self):
        cmd = [sys.executable, "-B", "-I", str(GH4 / "ghguard.py"), "check", "--", "issue", "create", "--repo", PROT,
               "--title", "x"]
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        r = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "P4_PROFILE": "flow"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("flusso", r.stderr)

    def test_comandi_log_accepts_the_new_write_forms(self):
        log = self.tmp / "out" / "comandi.log"
        log.write_text(
            f"2026-10-22T00:00:00Z gh api --method POST repos/{PROT}/statuses/{SHA} -f state=success "
            "-f context=tollgate/verdict -f description=prova-token-personale-p4\n"
            f"2026-10-22T00:00:01Z gh api --paginate --jq .[] | {{context, state}} repos/{PROT}/commits/{SHA}/statuses?per_page=100\n"
            f"2026-10-22T00:00:02Z gh pr create --repo {PROT} --base main --head tg/7-x --title prova: caso --body-file "
            f"{self.tmp}/out/body.md\n")
        r = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghguard.py"), "comandi", str(log)], capture_output=True,
                           text=True, env={**os.environ, "P4_OUT": str(self.tmp / "out"), "P4_WORK": str(self.tmp / "work")})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        log.write_text(log.read_text() + f"2026-10-22T00:00:03Z gh api --method POST repos/{PROT}/issues -f title=x\n")
        r = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghguard.py"), "comandi", str(log)], capture_output=True,
                           text=True, env={**os.environ, "P4_OUT": str(self.tmp / "out"), "P4_WORK": str(self.tmp / "work")})
        self.assertEqual(r.returncode, 1)


class TighteningTest(GuardBase):
    """Giro 1: M-2 (repo create e segreti), M-4 (profilo flow solo le forme del flusso), file di ingresso del flusso."""

    def test_repo_create_visibility_matches_the_repo(self):
        self.ok("repo", "create", PROT, "--public", "--add-readme")
        self.ok("repo", "create", DET, "--private", "--add-readme")
        self.no("repo", "create", DET, "--public", "--add-readme")
        self.no("repo", "create", PROT, "--private")

    def test_secrets_endpoints_are_refused(self):
        self.no("api", f"repos/{PROT}/actions/secrets")
        self.no("api", f"repos/{DET}/actions/secrets/NOME")
        self.no("api", "--paginate", f"repos/{DET}/dependabot/secrets?per_page=100")
        self.ok("api", f"repos/{PROT}/actions/permissions")

    def test_flow_profile_has_only_the_flow_forms(self):
        body = f"{self.tmp}/flow/wt/.tollgate-run/7/pr-body.md"
        for args in (["pr", "edit", "3", "--repo", PROT, "--body-file", body],["issue", "close", "5", "--repo", PROT], ["issue", "comment", "5", "--repo", PROT, "--body", "x"],
                     ["pr", "comment", "3", "--repo", PROT, "--body", "x"],
                     ["pr", "edit", "3", "--repo", PROT, "--base", "dev"],
                     ["pr", "edit", "3", "--repo", PROT, "--title", "x"],
                     ["pr", "edit", "3", "--repo", PROT, "--body", "x"]):
            self.no(*args, profile="flow")
            if args[:2] in (["issue", "close"], ["pr", "comment"]):
                self.ok(*args)          # lo script del gate li usa

    def test_flow_body_files_only_under_the_flow_folder(self):
        for path in ("/tmp/x.md", "/etc/passwd", f"{self.tmp}/out/x.md", f"{self.tmp}/flow/../x.md"):
            self.no("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t",
                    "--body-file", path, profile="flow")
        self.ok("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t",
                "--body-file", f"{self.tmp}/flow/a/b.md", profile="flow")

    def test_tmpdir_of_the_environment_does_not_widen_the_flow_profile(self):
        with mock.patch.dict(os.environ, {"TMPDIR": "/etc"}):
            self.no("pr", "create", "--repo", PROT, "--base", "main", "--head", "tg/7-x", "--title", "t",
                    "--body-file", "/etc/passwd", profile="flow")


class MinorsOfP4Test(GuardBase):
    """Minori di P4 corretti con il profilo p5: regex con fullmatch (un a-capo finale non passa), cifre solo ASCII."""

    def test_trailing_newline_is_refused_everywhere(self):
        self.no("pr", "view", "3\n", "--repo", PROT)
        self.no("pr", "list", "--repo", PROT, "--head", "ramo\n")
        self.no("pr", "list", "--repo", PROT, "--json", "number\n")
        self.no("run", "list", "--repo", PROT, "--workflow", "probe-run.yml\n")
        self.no("run", "download", "1", "--repo", PROT, "-n", "nome\n")
        self.no("api", f"repos/{PROT}/pulls/3\n")
        self.no("api", "--method", "PATCH", f"repos/{PROT}/pulls/3\n", "-F", f"body=@{self.tmp}/out/b.md")
        self.no("api", "--method", "POST", f"repos/{PROT}/statuses/{SHA}\n", "-f", "state=success", "-f",
                "context=tollgate/verdict", "-f", "description=prova-token-personale-p4")

    def test_unicode_digits_are_not_numbers(self):
        for fake in ("٣", "３", "²"):                     # arabo-indico, a larghezza intera, apice
            self.no("issue", "close", fake, "--repo", PROT)
            self.no("pr", "view", fake, "--repo", PROT)
            self.no("pr", "list", "--repo", PROT, "--limit", fake)
            self.no("api", "--method", "PATCH", f"repos/{PROT}/pulls/{fake}", "-F", f"body=@{self.tmp}/out/b.md")
        self.ok("issue", "close", "3", "--repo", PROT)

    def test_p5_refuses_them_too(self):
        self.no("pr", "view", "3\n", "--repo", DET, profile="p5")
        self.no("run", "view", "٣", "--repo", ghguard.TOL, profile="p5")
        self.no("run", "list", "--repo", ghguard.TOL, "--workflow", "ci-probe.yml\n", profile="p5")


class P5ProfileTest(GuardBase):
    """Profilo `p5` (decisioni 20-22 di P5): due soli repo, operazioni per repo, scritture `gh api` in due forme."""

    TOL = ghguard.TOL

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ, {"P5_PR_REGISTRY": str(self.tmp / "prs.txt")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def p5(self, *args):
        return self.ok(*args, profile="p5")

    def not_p5(self, *args):
        return self.no(*args, profile="p5")

    def test_repo_create_only_the_private_tollgate(self):
        self.p5("repo", "create", self.TOL, "--private")
        for args in (["repo", "create", self.TOL, "--public"], ["repo", "create", self.TOL],
                     ["repo", "create", self.TOL, "--private", "--add-readme"],
                     ["repo", "create", self.TOL, "--private", "--public"], ["repo", "create", DET, "--private"],
                     ["repo", "create", PROT, "--private"], ["repo", "create", f"{ghguard.OWNER}/altro", "--private"],
                     ["repo", "create", self.TOL, "--private", "--source=."],
                     ["repo", "delete", self.TOL], ["repo", "clone", DET], ["repo", "view", self.TOL],
                     ["repo", "edit", self.TOL, "--visibility", "public"], ["repo", "archive", self.TOL]):
            self.not_p5(*args)

    def test_auth_status_and_version_only(self):
        self.p5("auth", "status")
        self.p5("--version")
        for args in (["auth", "login"], ["auth", "refresh"], ["auth", "status", "--show-token"], ["auth", "token"],
                     ["--version", "x"]):
            self.not_p5(*args)

    def test_tollgate_allows_only_run_operations_and_reads(self):
        for sub in ("list", "view", "watch", "download", "rerun"):
            extra = {"list": ["--workflow", "ci-probe.yml", "--limit", "5", "--json", "databaseId"],
                     "download": ["-D", f"{self.tmp}/out/x"]}.get(sub, [])
            number = [] if sub == "list" else ["12"]
            self.p5("run", sub, *number, "--repo", self.TOL, *extra)
        self.p5("run", "view", "12", "--repo", self.TOL, "--log")
        self.p5("run", "view", "12", "--repo", self.TOL, "--log-failed")
        self.p5("run", "rerun", "12", "--repo", self.TOL, "--failed")
        self.p5("api", f"repos/{self.TOL}/actions/runs/12/timing")
        self.p5("api", "--paginate", f"repos/{self.TOL}/actions/runs?per_page=100", "--jq", ".total_count")
        self.p5("api", "--include", f"repos/{self.TOL}")
        for args in (["pr", "list", "--repo", self.TOL], ["pr", "create", "--repo", self.TOL, "--head", "x"],
                     ["pr", "view", "1", "--repo", self.TOL], ["issue", "list", "--repo", self.TOL],
                     ["issue", "comment", "1", "--repo", self.TOL, "--body", "x"],
                     ["run", "delete", "1", "--repo", self.TOL], ["run", "cancel", "1", "--repo", self.TOL],
                     ["run", "rerun", "1", "--repo", self.TOL, "--debug"], ["run", "list"],
                     ["workflow", "run", "ci.yml", "--repo", self.TOL], ["release", "create", "v1", "--repo", self.TOL]):
            self.not_p5(*args)

    def test_detect_allows_pr_issue_and_run_operations(self):
        body = f"{self.tmp}/out/body.md"
        self.p5("pr", "create", "--repo", DET, "--base", "main", "--head", "p5-probe-cache", "--title", "sonda",
                "--body", "testo con spazi")
        self.p5("pr", "create", "--repo", DET, "--base", "main", "--head", "p5-probe-cache", "--title", "t",
                "--body-file", body)
        self.p5("pr", "close", "5", "--repo", DET)
        self.p5("pr", "merge", "5", "--repo", DET, "--squash")
        self.p5("pr", "view", "5", "--repo", DET, "--json", "state,mergeStateStatus")
        self.p5("pr", "list", "--repo", DET, "--state", "all", "--limit", "20", "--json", "number,headRefName")
        self.p5("pr", "comment", "5", "--repo", DET, "--body", "x")
        self.p5("issue", "close", "2", "--repo", DET)
        self.p5("issue", "comment", "2", "--repo", DET, "--body", "x")
        self.p5("issue", "view", "2", "--repo", DET, "--json", "number,title")
        self.p5("issue", "list", "--repo", DET, "--state", "open", "--limit", "10", "--json", "number")
        self.p5("run", "watch", "9", "--repo", DET, "--exit-status")
        self.p5("run", "rerun", "9", "--repo", DET)
        self.p5("api", f"repos/{DET}/actions/permissions")
        self.p5("api", f"repos/{DET}/actions/runs/9/timing")
        for args in (["pr", "merge", "5", "--repo", DET], ["pr", "merge", "5", "--repo", DET, "--squash", "--admin"],
                     ["pr", "edit", "5", "--repo", DET, "--body", "x"], ["issue", "create", "--repo", DET, "--title", "x"],
                     ["pr", "create", "--repo", DET, "--head", "x", "--body-file", "/etc/passwd"],
                     ["pr", "ready", "5", "--repo", DET], ["pr", "checkout", "5", "--repo", DET],
                     ["issue", "delete", "2", "--repo", DET], ["issue", "transfer", "2", "--repo", DET],
                     ["run", "delete", "9", "--repo", DET], ["secret", "set", "X"], ["gist", "create"]):
            self.not_p5(*args)

    def test_protected_and_other_repos_are_refused_everywhere(self):
        other = f"{ghguard.OWNER}/altro"
        for repo in (PROT, other, "altro/tollgate", f"{ghguard.OWNER}/tollgate-p4-protected-x", f"{self.TOL}x"):
            self.not_p5("run", "list", "--repo", repo)
            self.not_p5("pr", "list", "--repo", repo)
            self.not_p5("issue", "list", "--repo", repo)
            self.not_p5("api", f"repos/{repo}/actions/permissions")
            self.not_p5("api", "--method", "PUT", f"repos/{repo}/actions/permissions", "-F", "enabled=true",
                        "-F", "sha_pinning_required=true")
        self.not_p5("run", "list", "--repo", self.TOL, "-R", PROT)
        self.not_p5("pr", "list", "--repo", DET, "--repo", PROT)
        self.not_p5("pr", "list", f"-R{PROT}")

    def test_a_command_that_names_a_foreign_repo_anywhere_is_refused(self):
        self.not_p5("pr", "comment", "5", "--repo", DET, "--body", f"vedi {PROT}")
        self.not_p5("pr", "comment", "5", "--repo", DET, "--body", f"vedi {ghguard.OWNER}/altro.")
        self.not_p5("issue", "comment", "2", "--repo", DET, "--body", "vedi ginz0ls/tollgate-p4-protected/pull/1")
        self.p5("issue", "comment", "2", "--repo", DET, "--body", f"vedi {DET} e {self.TOL}.")

    def test_secrets_and_user_endpoints_are_refused(self):
        for ep in ("user", "/user", "graphql", f"repos/{DET}/actions/secrets", f"repos/{self.TOL}/actions/secrets/X",
                   f"repos/{self.TOL}/dependabot/secrets", f"repos/{DET}/../{PROT}", f"repos/{DET}//x",
                   f"repos/{DET}/%2e%2e/x", "orgs/ginz0ls", "users/ginz0ls", "notifications"):
            self.not_p5("api", ep)

    def test_visibility_changes_and_deletions_are_refused(self):
        for args in (["api", "--method", "PATCH", f"repos/{self.TOL}", "-F", "private=false"],
                     ["api", "--method", "PATCH", f"repos/{DET}", "-f", "visibility=public"],
                     ["api", "--method", "DELETE", f"repos/{DET}"], ["api", "--method", "DELETE", f"repos/{self.TOL}"],
                     ["api", "--method", "PUT", f"repos/{self.TOL}/actions/secrets/X", "-f", "encrypted_value=x"],
                     ["api", "--method", "POST", f"repos/{DET}/issues", "-f", "title=x"],
                     ["api", "--method", "POST", f"repos/{DET}/statuses/{SHA}", "-f", "state=success"],
                     ["api", "--method", "PUT", f"repos/{DET}/branches/main/protection", "--input", "/tmp/x"],
                     ["api", "--method", "DELETE", f"repos/{DET}/git/refs/heads/p5-probe-pin"],
                     ["api", "-XPOST", f"repos/{DET}/issues"]):
            self.not_p5(*args)


class P5ApiWritesTest(GuardBase):
    """Le due scritture `gh api` del profilo p5, il registro delle PR e i comandi git registrati."""

    def setUp(self):
        super().setUp()
        self.registry = self.tmp / "prs-aperte.txt"
        patcher = mock.patch.dict(os.environ, {"P5_PR_REGISTRY": str(self.registry)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.body = f"{self.tmp}/out/body.md"

    def put(self, **over):
        fields = {"enabled": "true", "sha_pinning_required": "true"}
        fields.update(over)
        args = ["api", "--method", "PUT", f"repos/{DET}/actions/permissions"]
        for key, value in fields.items():
            if value is not None:
                args += ["-F", f"{key}={value}"]
        return args

    def patch(self, number="3", repo=DET):
        return ["api", "--method", "PATCH", f"repos/{repo}/pulls/{number}", "-F", f"body=@{self.body}"]

    def test_put_actions_permissions_exact_form(self):
        self.ok(*self.put(), profile="p5")
        self.ok(*self.put(sha_pinning_required="false"), profile="p5")
        self.ok(*self.put(allowed_actions="all"), profile="p5")
        self.ok(*self.put(allowed_actions="selected"), profile="p5")
        args = self.put()
        args[1:3] = ["-X", "PUT"]
        self.ok(*args, profile="p5")

    def test_put_actions_permissions_everything_else_is_refused(self):
        self.no(*self.put(enabled="false"), profile="p5")
        self.no(*self.put(enabled=None), profile="p5")
        self.no(*self.put(sha_pinning_required=None), profile="p5")
        self.no(*self.put(sha_pinning_required="boh"), profile="p5")
        self.no(*self.put(allowed_actions="tutto"), profile="p5")
        self.no(*self.put(extra="x"), profile="p5")
        self.no(*self.put(), "-f", "allowed_actions=all", profile="p5")
        self.no(*self.put(), "--input", "/tmp/x", profile="p5")
        self.no(*self.put(), profile="script")
        self.no(*self.put(), profile="flow")
        for repo in (ghguard.TOL, PROT):
            args = self.put()
            args[3] = f"repos/{repo}/actions/permissions"
            self.no(*args, profile="p5")
        args = self.put()
        args[3] = f"repos/{DET}/actions/permissions/selected-actions"
        self.no(*args, profile="p5")
        args[3] = f"repos/{DET}/actions/permissions/workflow"
        self.no(*args, profile="p5")

    def test_patch_body_only_for_prs_opened_in_this_trial(self):
        self.no(*self.patch(), profile="p5")                               # nessun registro
        self.registry.write_text("create\n")
        self.no(*self.patch(), profile="p5")                               # creata ma non registrata
        self.registry.write_text("create\npr 3\n")
        self.ok(*self.patch("3"), profile="p5")
        self.no(*self.patch("4"), profile="p5")
        self.no(*self.patch("33"), profile="p5")
        self.no(*self.patch("3", repo=ghguard.TOL), profile="p5")
        self.no(*self.patch("3", repo=PROT), profile="p5")
        self.registry.write_text("create\npr 3\ncreate\npr 4\n")
        self.ok(*self.patch("4"), profile="p5")

    def test_patch_body_refuses_any_other_shape(self):
        self.registry.write_text("create\npr 3\n")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3", "-f", "body=testo", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3", "-F", "body=testo", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3", "-F", f"body=@{self.body}", "-F", "title=x", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3", "-F", f"body=@{self.body}", "-f", "state=closed", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3", "-F", "state=@/tmp/x", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3/merge", "-F", f"body=@{self.body}", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/issues/3", "-F", f"body=@{self.body}", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3", "-F", "body=@/etc/passwd", profile="p5")
        self.no("api", "--method", "PATCH", f"repos/{DET}/pulls/3", "--input", "/tmp/x", profile="p5")

    def test_p4_profiles_still_patch_any_pr_of_protected_only(self):
        self.ok(*self.patch("3", repo=PROT), profile="script")
        flow = self.patch("999", repo=PROT)
        flow[-1] = f"body=@{self.tmp}/flow/pr-body.md"
        self.ok(*flow, profile="flow")
        self.no(*self.patch("3", repo=DET), profile="script")

    def run_guard(self, *args, env=None):
        full = {**os.environ, "P4_PROFILE": "p5", "P4_OUT": str(self.tmp / "out"), "P4_WORK": str(self.tmp / "work")}
        full.update(env or {})
        return subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghguard.py"), *args], capture_output=True,
                              text=True, env=full)

    def test_pr_create_through_check_registers_and_register_pr_consumes(self):
        create = ["check", "--", "pr", "create", "--repo", DET, "--base", "main", "--head", "p5-probe-cache",
                  "--title", "t", "--body", "x"]
        self.assertEqual(self.run_guard("register-pr", "7").returncode, 1)          # nessun create in attesa
        self.assertEqual(self.run_guard(*create).returncode, 0)
        self.assertEqual(self.registry.read_text(), "create\n")
        self.assertEqual(self.run_guard("register-pr", "x7").returncode, 1)
        self.assertEqual(self.run_guard("register-pr", "٧").returncode, 1)
        self.assertEqual(self.run_guard("register-pr", "7").returncode, 0)
        self.assertEqual(self.run_guard("register-pr", "8").returncode, 1)          # il create è già consumato
        self.assertEqual(self.registry.read_text(), "create\npr 7\n")
        self.assertEqual(self.run_guard("check", "--", *self.patch("7")).returncode, 0)
        self.assertEqual(self.run_guard("check", "--", *self.patch("8")).returncode, 1)

    def test_pr_create_without_a_registry_is_refused_by_check(self):
        cmd = ["check", "--", "pr", "create", "--repo", DET, "--base", "main", "--head", "x", "--title", "t"]
        r = self.run_guard(*cmd, env={"P5_PR_REGISTRY": ""})
        self.assertEqual(r.returncode, 1)
        self.assertIn("P5_PR_REGISTRY", r.stderr)
        self.assertEqual(self.run_guard(*cmd, env={"P5_PR_REGISTRY": "relativo.txt"}).returncode, 1)

    def test_a_refused_pr_create_leaves_the_registry_alone(self):
        r = self.run_guard("check", "--", "pr", "create", "--repo", PROT, "--base", "main", "--head", "x", "--title", "t")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(self.registry.exists())

    def test_comandi_log_checks_gh_and_git_net_lines_with_the_p5_profile(self):
        log = self.tmp / "out" / "comandi.log"
        self.registry.write_text("create\npr 3\n")
        lines = [
            "2026-10-23T00:00:00Z gh run list --repo ginz0ls/tollgate --workflow ci-probe.yml --limit 30 --json databaseId",
            f"2026-10-23T00:00:01Z gh api --method PATCH repos/{DET}/pulls/3 -F body=@{self.tmp}/out/b.md",
            f"2026-10-23T00:00:02Z git-net dir=/tmp/tollgate-p5/ci push {ghguard.TOL_URL} main",
        ]
        env = {"P5_PR_REGISTRY": str(self.registry)}
        log.write_text("\n".join(lines) + "\n")
        r = self.run_guard("comandi", str(log), env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("git push", r.stdout)
        for bad in (f"2026-10-23T00:00:03Z gh run list --repo {PROT}",
                    f"2026-10-23T00:00:04Z git-net dir=/tmp/tollgate-p5/ci push --force {ghguard.TOL_URL} main",
                    f"2026-10-23T00:00:05Z gh api --method PATCH repos/{DET}/pulls/9 -F body=@{self.tmp}/out/b.md"):
            log.write_text("\n".join(lines + [bad]) + "\n")
            self.assertEqual(self.run_guard("comandi", str(log), env=env).returncode, 1, bad)

    def test_log_uses_the_profile_of_the_environment(self):
        log = self.tmp / "gh.log"
        log.write_text("run\tlist\t--repo\tginz0ls/tollgate\t\n")
        self.assertEqual(self.run_guard("log", str(log)).returncode, 0)
        self.assertEqual(self.run_guard("log", str(log), env={"P4_PROFILE": "script"}).returncode, 1)
        log.write_text(f"run\tlist\t--repo\t{PROT}\t\n")
        self.assertEqual(self.run_guard("log", str(log)).returncode, 1)


class P5GitNetTest(GuardBase):
    """`git_violation`: i comandi git con la rete del profilo p5 (decisioni 20 e 21, scelta del controller)."""

    TOL_URL, DET_URL = ghguard.TOL_URL, ghguard.DET_URL

    def setUp(self):
        super().setUp()
        self.pins = self.tmp / "pins"
        patcher = mock.patch.dict(os.environ, {"P5_PINS": str(self.pins)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def git_ok(self, *args, directory=""):
        self.assertIsNone(ghguard.git_violation(list(args), directory), " ".join(args))

    def git_no(self, *args, directory=""):
        self.assertIsNotNone(ghguard.git_violation(list(args), directory), " ".join(args))

    def test_push_to_tollgate_only_main_the_branch_and_probe_branches(self):
        for ref in ("main", "p5-eval-ci", "p5-probe-ci", "p5-probe-ci-20261023-1", "p5-probe-a/b"):
            self.git_ok("push", self.TOL_URL, ref)
        for ref in ("p5-probe-", "p5-probe", "altro", "p4-gate", "master", "p5-eval-ci2", "tg/7-x"):
            self.git_no("push", self.TOL_URL, ref)

    def test_push_to_detect_any_plain_branch_and_main(self):
        for ref in ("main", "p5-probe-cache", "p5-probe-pin", "tg/7-x", "altro"):
            self.git_ok("push", self.DET_URL, ref)

    def test_push_is_never_forced_and_takes_no_refspec_tricks(self):
        for args in (["push", "--force", self.TOL_URL, "main"], ["push", "-f", self.TOL_URL, "main"],
                     ["push", self.TOL_URL, "+main"], ["push", self.TOL_URL, "main:main"],
                     ["push", self.TOL_URL, "HEAD:main"], ["push", self.TOL_URL, ":main"],
                     ["push", "--force-with-lease", self.TOL_URL, "main"], ["push", "--mirror", self.TOL_URL],
                     ["push", "--all", self.TOL_URL], ["push", "--tags", self.TOL_URL], ["push", self.TOL_URL],
                     ["push", self.TOL_URL, "main", "p5-eval-ci"], ["push", "-u", self.TOL_URL, "main"],
                     ["push", "--no-verify", self.TOL_URL, "main"], ["push", "origin", "main"],
                     ["push", "--delete", "--force", self.TOL_URL, "p5-probe-ci"], ["push", self.TOL_URL, "-main"],
                     ["push", self.TOL_URL, "a..b"], ["push", self.TOL_URL, "main\n"]):
            self.git_no(*args)

    def test_delete_only_probe_branches_of_tollgate_never_on_detect(self):
        self.git_ok("push", "--delete", self.TOL_URL, "p5-probe-ci")
        for args in (["push", "--delete", self.TOL_URL, "main"], ["push", "--delete", self.TOL_URL, "p5-eval-ci"],
                     ["push", "--delete", self.DET_URL, "p5-probe-cache"], ["push", "--delete", self.DET_URL, "main"],
                     ["push", "-d", self.TOL_URL, "p5-probe-ci"], ["push", self.TOL_URL, "--delete", "p5-probe-ci"]):
            self.git_no(*args)

    def test_push_only_to_the_two_urls(self):
        for url in (f"https://github.com/{PROT}.git", "https://github.com/ginz0ls/altro.git", "origin",
                    "https://github.com/ginz0ls/tollgate", f"git@github.com:{ghguard.TOL}.git",
                    "https://example.com/ginz0ls/tollgate.git", "https://github.com/actions/checkout", "/tmp/bare.git",
                    "https://github.com/ginz0ls/tollgate.git?x", "https://github.com/ginz0ls/tollgate.git/"):
            self.git_no("push", url, "main")

    def test_ls_remote_only_tags_of_the_five_actions(self):
        for action in ghguard.ACTIONS:
            self.git_ok("ls-remote", "--tags", f"https://github.com/actions/{action}")
        for args in (["ls-remote", "https://github.com/actions/checkout"], ["ls-remote", "--tags", self.TOL_URL],
                     ["ls-remote", "--tags", "https://github.com/actions/runner"],
                     ["ls-remote", "--tags", "https://github.com/altro/checkout"],
                     ["ls-remote", "--tags", "https://github.com/actions/checkout.git"],
                     ["ls-remote", "--heads", "https://github.com/actions/checkout"],
                     ["ls-remote", "--tags", "origin"], ["ls-remote"]):
            self.git_no(*args)

    def test_fetch_of_action_tags_only_in_the_pins_folder(self):
        url = "https://github.com/actions/checkout"
        folder = str(self.pins / "checkout")
        self.git_ok("fetch", "--depth", "1", url, "tag", "v4.2.2", directory=folder)
        self.git_ok("fetch", "--depth", "1", url, "tag", "v5", directory=folder)
        self.git_no("fetch", "--depth", "1", url, "tag", "v4.2.2", directory=str(self.pins))
        self.git_no("fetch", "--depth", "1", url, "tag", "v4.2.2", directory="/tmp/altro/checkout")
        self.git_no("fetch", "--depth", "1", url, "tag", "v4.2.2", directory=f"{self.pins}/../x")
        self.git_no("fetch", "--depth", "1", url, "tag", "v4.2.2")
        for args in (["fetch", "--depth", "1", url, "tag", "main"], ["fetch", "--depth", "1", url, "tag", "v4.2.2\n"],
                     ["fetch", "--depth", "1", url, "tag", "../v4"], ["fetch", url, "tag", "v4.2.2"],
                     ["fetch", "--depth", "1", url, "refs/tags/v4:refs/tags/v4"], ["fetch", "--depth", "1", url, "tag"],
                     ["fetch", "--depth", "1", self.TOL_URL, "tag", "v4"], ["fetch", "--depth", "1", "origin", "tag", "v4"],
                     ["fetch", "--all"], ["fetch", "--depth", "1", url, "tag", "v4.2.2", "--force"]):
            self.git_no(*args, directory=folder)

    def test_detect_clone_only_below_the_work_folder(self):
        work = str(self.tmp / "work")
        dest = f"{work}/detect"
        self.git_ok("clone", "-q", self.DET_URL, dest, directory=dest)
        self.git_no("clone", "-q", self.DET_URL, dest, directory="/tmp/altro")
        self.git_no("clone", "-q", self.DET_URL, "/tmp/altro", directory="/tmp/altro")
        self.git_no("clone", "-q", self.DET_URL, dest, directory=work)
        self.git_no("clone", "-q", self.TOL_URL, dest, directory=dest)
        self.git_no("clone", "-q", f"https://github.com/{PROT}.git", dest, directory=dest)
        self.git_no("clone", self.DET_URL, dest, directory=dest)
        self.git_no("clone", "-q", "--mirror", self.DET_URL, dest, directory=dest)
        self.git_no("fetch", self.DET_URL, "main", directory=dest)       # detect si clona, non si aggiorna
        self.git_no("fetch", self.TOL_URL, "main", directory=dest)

    def test_other_git_verbs_with_the_network_are_refused(self):
        for args in (["pull"], ["pull", self.TOL_URL], ["remote", "add", "x", self.TOL_URL], ["submodule", "update"],
                     ["archive", f"--remote={self.TOL_URL}", "main"], ["send-pack", self.TOL_URL], [], ["config", "x"]):
            self.git_no(*args)

    def test_gitcheck_cli(self):
        base = [sys.executable, "-B", "-I", str(GH4 / "ghguard.py"), "gitcheck"]
        env = {**os.environ, "P5_PINS": str(self.pins), "P4_WORK": str(self.tmp / "work")}
        r = subprocess.run([*base, "--", "push", self.TOL_URL, "main"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run([*base, "--", "push", "--force", self.TOL_URL, "main"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stderr.strip())
        r = subprocess.run([*base, "--dir", str(self.pins / "cache"), "--", "fetch", "--depth", "1",
                            "https://github.com/actions/cache", "tag", "v4.2.0"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run([*base, "push", self.TOL_URL, "main"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 2)


class ReplayOfCommittedEvidenceTest(GuardBase):
    """`comandi` rigioca i registri committati, che portano i percorsi del worktree di allora: si riportano alla cartella
    corrente del registro (solo prefissi `…/.claude/worktrees/<nome>/docs/verifiche/evidenze/<cartella>`)."""

    def replay(self, root_name, lines):
        evid = self.tmp / root_name / "docs" / "verifiche" / "evidenze" / "gh-p4"
        evid.mkdir(parents=True, exist_ok=True)
        log = evid / "comandi.log"
        log.write_text("".join(f"2026-10-21T15:56:04Z gh {line}\n" for line in lines))
        env = {k: v for k, v in os.environ.items() if k not in ("P4_OUT", "P4_WORK", "P4_PROFILE")}
        return subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghguard.py"), "comandi", str(log)], capture_output=True,
                              text=True, env=env)

    OLD = "/home/utente/MEGA/Plugin IT workflow/.claude/worktrees/p4/docs/verifiche/evidenze/gh-p4"

    def lines(self, old=None):
        old = old or self.OLD
        return [f"run download 39630136045 --repo {PROT} -D {old}/v1-target-artifacts-39630136045",
                f"api --method PATCH repos/{PROT}/pulls/3 -F body=@{old}/b.md",
                f"pr create --repo {PROT} --base main --head tg/7-x --title t --body-file {old}/body.md"]

    def test_paths_of_an_old_worktree_pass_from_any_checkout_path(self):
        for name in ("senza-spazi", "con spazi qui", ".claude/worktrees/p5"):
            r = self.replay(name, self.lines())
            self.assertEqual(r.returncode, 0, name + r.stdout + r.stderr)

    def test_other_prefixes_and_traversals_are_still_refused(self):
        for old in ("/etc/passwd-dir/docs/verifiche/evidenze/gh-p4", "/home/u/docs/verifiche/evidenze/gh-p4",
                    "/home/u/.claude/worktrees/p4/docs/verifiche/evidenze/altra"):
            r = self.replay("x", self.lines(old)[:1])
            self.assertEqual(r.returncode, 1, old)
        r = self.replay("y", [f"run download 1 --repo {PROT} -D /etc"])
        self.assertEqual(r.returncode, 1)
        r = self.replay("z", [f"run download 1 --repo {PROT} -D {self.OLD}/../../x"])
        self.assertEqual(r.returncode, 1)


class WrapperTest(unittest.TestCase):
    """`ghwrap.py`: espande i segnaposto, aggiunge --repo, controlla, registra e passa al gh vero."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate p4 wrap "))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real = self.tmp / "gh-vero"
        self.real.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{self.tmp}/argv.txt"\necho eseguito\n')
        self.real.chmod(self.real.stat().st_mode | stat.S_IEXEC)
        self.log = self.tmp / "comandi.log"

    def run_gh(self, *args, repo=PROT, profile="script"):
        env = {"PATH": os.environ["PATH"], "P4_REAL_GH": str(self.real), "P4_REPO": repo, "P4_LOG": str(self.log),
               "P4_PROFILE": profile, "P4_OUT": str(self.tmp), "P4_WORK": str(self.tmp)}
        (self.tmp / "argv.txt").unlink(missing_ok=True)
        r = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghwrap.py"), *args], capture_output=True, text=True,
                           env=env, cwd=self.tmp)
        argv = (self.tmp / "argv.txt").read_text().split("\n")[:-1] if (self.tmp / "argv.txt").exists() else None
        return r, argv

    def test_expands_placeholders_and_runs_the_real_gh(self):
        r, argv = self.run_gh("api", "repos/{owner}/{repo}/issues/7")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(argv, ["api", f"repos/{PROT}/issues/7"])
        self.assertIn(f"gh api repos/{PROT}/issues/7", self.log.read_text())

    def test_adds_the_repo_to_pr_issue_and_run(self):
        r, argv = self.run_gh("pr", "list", "--head", "tg/7-x", "--state", "all", "--limit", "100", "--json", "number")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(argv[-2:], ["--repo", PROT])

    def test_refused_commands_never_reach_the_real_gh(self):
        r, argv = self.run_gh("issue", "create", "--title", "x", profile="flow")
        self.assertEqual(r.returncode, 126)
        self.assertIsNone(argv)
        self.assertIn("RIFIUTATO", self.log.read_text())
        r, argv = self.run_gh("api", "--method", "POST", "repos/{owner}/{repo}/issues", "-f", "title=x")
        self.assertEqual((r.returncode, argv), (126, None))

    def test_a_repo_that_is_not_allowed_stops_everything(self):
        r, argv = self.run_gh("api", "repos/{owner}/{repo}/issues/7", repo=f"{ghguard.OWNER}/altro")
        self.assertEqual((r.returncode, argv), (126, None))
        self.assertIn("non è uno dei due ammessi", r.stderr)

    def test_protect_sh_shapes_pass_only_on_protected(self):
        body = tempfile.NamedTemporaryFile(prefix="tmp.", delete=False)
        body.close()
        self.addCleanup(os.unlink, body.name)
        jq = '.check_runs[] | select(.name == "tollgate-base" and .app.slug == "github-actions") | [.status, (.conclusion // ""), (.app.id | tostring)] | @tsv'
        r, argv = self.run_gh("api", "--paginate", "--jq", jq, f"repos/{{owner}}/{{repo}}/commits/{SHA}/check-runs?per_page=100")
        self.assertEqual(r.returncode, 0, r.stderr)
        r, argv = self.run_gh("api", "--method", "PUT", "--input", body.name, "repos/{owner}/{repo}/branches/main/protection")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(argv[:3], ["api", "--method", "PUT"])
        r, argv = self.run_gh("api", "--method", "PUT", "--input", body.name, "repos/{owner}/{repo}/branches/main/protection",
                              repo=DET)
        self.assertEqual((r.returncode, argv), (126, None))

    def test_without_the_real_gh_it_refuses(self):
        r = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghwrap.py"), "auth", "status"], capture_output=True,
                           text=True, env={"PATH": os.environ["PATH"]})
        self.assertEqual(r.returncode, 126)


class GeneratedWrapperTest(unittest.TestCase):
    """Il gh del flusso fissa profilo, repo, gh vero e registro al momento della generazione: l'ambiente del modello non li cambia."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate p4 gen "))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.real = self.tmp / "gh-vero"
        self.real.write_text(f'#!/bin/sh\nprintf "%s\\n" "$@" > "{self.tmp}/argv.txt"\n')
        self.real.chmod(0o755)
        self.dest = self.tmp / "ghbin" / "gh"
        self.dest.parent.mkdir()
        self.log = self.tmp / "gh-wrap.log"
        r = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghwrap.py"), "make-wrapper", str(self.dest),
                            "--real", str(self.real), "--repo", PROT, "--profile", "flow", "--log", str(self.log),
                            "--tmp", str(self.tmp / "flow")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def call(self, *args, **env):
        (self.tmp / "argv.txt").unlink(missing_ok=True)
        e = {"PATH": os.environ["PATH"], **env}
        r = subprocess.run([str(self.dest), *args], capture_output=True, text=True, env=e, cwd=self.tmp)
        return r, (self.tmp / "argv.txt").exists()

    def test_hostile_environment_changes_nothing(self):
        for env in ({"P4_PROFILE": "script"}, {"P4_REPO": DET}, {"P4_REAL_GH": "/bin/true"}, {"P4_LOG": "/dev/null"},
                    {"P4_OUT": str(self.tmp), "P4_WORK": str(self.tmp), "P4_TMP": "/"}, {"GH_REPO": DET},
                    {"GH_HOST": "altro.example"}, {"GH_CONFIG_DIR": str(self.tmp)}, {"BASH_ENV": str(self.tmp / "evil.sh")},
                    {"ENV": str(self.tmp / "evil.sh")}):
            r, ran = self.call("pr", "merge", "5", "--squash", **env)
            self.assertEqual(r.returncode, 126, env)
            self.assertFalse(ran, env)
        self.assertIn("RIFIUTATO", self.log.read_text())

    def test_credentials_and_host_variables_are_dropped_without_reading_them(self):
        probe = self.tmp / "gh-sonda"
        probe.write_text(f'#!/bin/sh\nenv | cut -d= -f1 | sort > "{self.tmp}/nomi.txt"\n')
        probe.chmod(0o755)
        dest = self.tmp / "ghbin" / "gh2"
        subprocess.run([sys.executable, "-B", "-I", str(GH4 / "ghwrap.py"), "make-wrapper", str(dest), "--real", str(probe),
                        "--repo", PROT, "--profile", "flow", "--log", str(self.log), "--tmp", str(self.tmp / "flow")],
                       check=True)
        env = {"PATH": os.environ["PATH"]}
        dropped = ("GH_HOST", "GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
                   "GH_CONFIG_DIR", "BASH_ENV", "ENV", "GH_REPO", "TMPDIR")
        env.update({name: "valore-finto" for name in dropped})
        r = subprocess.run([str(dest), "pr", "list", "--head", "tg/7-x", "--state", "all", "--limit", "100", "--json",
                            "number"], capture_output=True, text=True, env=env, cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        names = (self.tmp / "nomi.txt").read_text().split()
        for name in dropped:
            self.assertNotIn(name, names)

    def test_body_file_roots_are_not_taken_from_the_environment(self):
        r, ran = self.call("pr", "create", "--base", "main", "--head", "tg/7-x", "--title", "t", "--body-file",
                           "/etc/passwd", TMPDIR="/etc", P4_TMP="/etc")
        self.assertEqual((r.returncode, ran), (126, False))

    def test_allowed_call_goes_to_the_pinned_real_gh_and_the_pinned_repo(self):
        r, ran = self.call("pr", "list", "--head", "tg/7-x", "--state", "all", "--limit", "100", "--json", "number",
                           P4_REPO=DET, P4_REAL_GH="/bin/false", GH_REPO=DET)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(ran)
        self.assertEqual((self.tmp / "argv.txt").read_text().split("\n")[-3:-1], ["--repo", PROT])
        self.assertIn(f"gh pr list", self.log.read_text())

    def test_the_generated_file_is_not_writable(self):
        self.assertFalse(os.access(self.dest, os.W_OK) and (self.dest.stat().st_mode & 0o222))


def stream(*blocks):
    """Un'uscita stream-json di esempio: `system/init` e, per ogni `(comando, uscita)`, un uso di Bash con il suo risultato."""
    lines = [{"type": "system", "subtype": "init", "session_id": "s-1", "cwd": "/tmp/tollgate-p4/flow/protected"}]
    for i, (command, result) in enumerate(blocks):
        lines.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"t{i}", "name": "Bash",
                                                                     "input": {"command": command}}]}})
        lines.append({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}",
                                                                "content": [{"type": "text", "text": result}]}]}})
    return "".join(json.dumps(x) + "\n" for x in lines)


class FlowCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate p4 flow "))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, name, text):
        path = self.tmp / name
        path.write_text(text)
        return path

    def test_gh_invocations_are_found_in_pipelines_and_after_assignments(self):
        found = flowcheck.gh_invocations('cd x && GH_PROMPT_DISABLED=1 gh pr list --head tg/7-a | cat; echo "gh issue create"')
        self.assertEqual(found, [["pr", "list", "--head", "tg/7-a"]])
        self.assertEqual(flowcheck.gh_invocations("echo gh; ls"), [])

    def test_gh_invocations_through_prefixes_paths_and_substitutions(self):
        cases = {
            "P4_PROFILE=script gh pr merge 5 --squash": [["pr", "merge", "5", "--squash"]],
            "/usr/bin/gh pr merge 5": [["pr", "merge", "5"]],
            "command gh pr merge 5": [["pr", "merge", "5"]],
            "env gh pr merge 5": [["pr", "merge", "5"]],
            "env -i FOO=1 /opt/bin/gh pr merge 5": [["pr", "merge", "5"]],
            "exec gh pr merge 5": [["pr", "merge", "5"]],
            "echo 5 | xargs gh pr merge": [["pr", "merge"]],
            "bash -c 'gh pr merge 5 && echo ok'": [["pr", "merge", "5"]],
            'sh -c "cd x; gh issue create --title a"': [["issue", "create", "--title", "a"]],
            "echo $(gh pr merge 5)": [["pr", "merge", "5"]],
            "echo `gh pr merge 5`": [["pr", "merge", "5"]],
            "cd /tmp && gh pr view 3 | cat": [["pr", "view", "3"]],
        }
        for command, want in cases.items():
            with self.subTest(command):
                self.assertEqual(flowcheck.gh_invocations(command), want)

    def test_dangerous_commands_are_listed(self):
        bad = ["git push --force origin main", "git push -f origin tg/7-x", "git push origin +HEAD:tg/7-x",
               "git push origin HEAD:main", "git push origin main", "git -C x push --force-with-lease",
               "git push origin tg/7-x:refs/heads/main", "P4_PROFILE=script true", "export P4_REAL_GH=/usr/bin/gh",
               "git push --mirror", "git push origin --delete tg/7-x"]
        for command in bad:
            with self.subTest(command):
                self.assertTrue(flowcheck.risky(command), command)
        for command in ("git status", 'echo "main"', "git log --oneline"):
            with self.subTest(command):
                self.assertEqual(flowcheck.risky(command), [], command)

    def audit(self, transcript_commands, wrap_lines=()):
        self.write("passo1.jsonl", stream(*[(c, "") for c in transcript_commands]))
        log = self.write("gh-wrap.log", "".join(wrap_lines))
        with mock.patch.dict(os.environ, {"P4_TMP": "/tmp/tollgate-p4/flow"}):
            return quiet(flowcheck.cmd_audit, self.tmp, log)

    def test_audit_passes_a_clean_run(self):
        ok = self.audit(["gh pr view 3 --json state", "git status"],
                        [f"2026-10-22T00:00:00Z gh pr view 3 --json state --repo {PROT}\n",
                         f"2026-10-22T00:00:01Z gh api repos/{PROT}/issues/7\n"])
        self.assertEqual(ok, 0)

    def test_audit_catches_each_bypass_in_the_transcript(self):
        for command in ("P4_PROFILE=script gh pr merge 5 --squash", "/usr/bin/gh pr merge 5", "command gh pr merge 5",
                        "env gh pr merge 5", "bash -c 'gh pr merge 5'", "echo $(gh pr merge 5)",
                        "git push --force origin main", "git push origin HEAD:main", "git push origin +tg/7-x"):
            with self.subTest(command):
                self.assertEqual(self.audit([command]), 1)

    def test_audit_catches_a_transcript_gh_that_never_went_through_the_wrapper(self):
        self.assertEqual(self.audit(["gh pr view 3 --json state"], []), 1)

    def test_audit_catches_out_of_list_and_refused_wrapper_calls(self):
        self.assertEqual(self.audit([], [f"2026-10-22T00:00:00Z gh pr merge 5 --squash --repo {PROT}\n"]), 1)
        self.assertEqual(self.audit([], ["2026-10-22T00:00:00Z RIFIUTATO gh issue create --title x\n"]), 1)
        self.assertEqual(self.audit([], [f"2026-10-22T00:00:00Z gh api repos/{PROT}/issues/7\n"]), 0)

    def test_audit_catches_writes_to_the_wrapper(self):
        path = self.write("passo2.jsonl", json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "w", "name": "Write", "input": {"file_path": "/tmp/tollgate-p4/flow/ghbin/gh"}}]}}) + "\n")
        log = self.write("gh-wrap.log", "")
        with mock.patch.dict(os.environ, {"P4_TMP": "/tmp/tollgate-p4/flow"}):
            self.assertEqual(quiet(flowcheck.cmd_audit, self.tmp, log), 1)
        path.unlink()

    def test_judge_gh(self):
        self.assertIsNone(flowcheck.judge_gh(["pr", "view", "3", "--json", "comments"]))
        self.assertIsNone(flowcheck.judge_gh(["api", "repos/{owner}/{repo}/issues/7"]))
        self.assertIn("flusso", flowcheck.judge_gh(["issue", "create", "--title", "x"]))
        self.assertIn("non ammesso", flowcheck.judge_gh(["pr", "list", "--repo", f"{ghguard.OWNER}/altro"]))
        self.assertIn("repo", flowcheck.judge_gh(["pr", "list", "--repo", DET]))

    def test_gh_command_reports_a_foreign_target_with_a_nonzero_code(self):
        good = self.write("a.jsonl", stream(("gh pr view 3 --json state", "{}")))
        bad = self.write("b.jsonl", stream(("gh pr view 3 --json state", "{}"), (f"gh pr list --repo {DET}", "[]")))
        self.assertEqual(quiet(flowcheck.cmd_gh, good), 0)
        self.assertEqual(quiet(flowcheck.cmd_gh, bad), 1)

    def test_shim_compares_the_tool_output_with_the_shim(self):
        shim = "/tmp/tollgate-p4/flow/shim/gh"
        same = self.write("a.jsonl", stream(("command -v gh", shim + "\n"), ('echo "$PATH"', "/usr/bin")))
        other = self.write("b.jsonl", stream(("command -v gh", "/usr/bin/gh\n")))
        none = self.write("c.jsonl", stream(("ls", "x")))
        self.assertEqual(quiet(flowcheck.cmd_shim, same, shim), 0)
        self.assertEqual(quiet(flowcheck.cmd_shim, other, shim), 1)
        self.assertEqual(quiet(flowcheck.cmd_shim, none, shim), 1)

    def test_events_are_compared_with_the_expectation(self):
        rows = [{"seq": 1, "type": "veto", "work": 1, "data": {"rule": "x"}},
                {"seq": 2, "type": "effect_requested", "work": 1, "data": {}},
                {"seq": 3, "type": "effect_executed", "work": 1, "data": {}}]
        path = self.write("e.jsonl", "".join(json.dumps(r) + "\n" for r in rows))
        self.assertEqual(quiet(flowcheck.cmd_events, path, "open-pr"), 0)
        self.assertEqual(quiet(flowcheck.cmd_events, path, "nessuno"), 1)

    def test_shapes_all_pass_and_the_forbidden_ones_do_not(self):
        with mock.patch.dict(os.environ, {"P4_TMP": "/tmp/tollgate-p4/flow"}):
            self.assertEqual(quiet(flowcheck.cmd_shapes), 0)
            body = [a for shape in flowcheck.SHAPES for a in shape if a.endswith("pr-body.md")]
            body = [b.removeprefix("body=@") for b in body]
            self.assertTrue(body and all(".tollgate-run/" in b and b.startswith("/tmp/tollgate-p4/flow/") for b in body))
            self.assertIn(["api", "--method", "PATCH", "repos/{owner}/{repo}/pulls/3", "-F", f"body=@{flowcheck.BODY}"],
                          flowcheck.SHAPES)
            self.assertFalse([sh for sh in flowcheck.SHAPES if sh[:2] == ["pr", "edit"]])
            self.assertIn(["pr", "edit", "3", "--body-file", flowcheck.BODY], flowcheck.FORBIDDEN_SHAPES)

    def test_sessions_are_listed(self):
        self.write("passo1.jsonl", stream(("ls", "x")))
        self.write("events-passo1.jsonl", "")
        out = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "flowcheck.py"), "sessions", str(self.tmp)],
                             capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.strip().split("\t"), ["passo1", "s-1", "/tmp/tollgate-p4/flow/protected"])


if __name__ == "__main__":
    unittest.main()
