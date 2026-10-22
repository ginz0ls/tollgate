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
        self.ok("pr", "edit", "3", "--repo", PROT, "--body-file", body, profile="flow")
        for args in (["issue", "close", "5", "--repo", PROT], ["issue", "comment", "5", "--repo", PROT, "--body", "x"],
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
            self.assertTrue(body and all(".tollgate-run/" in b and b.startswith("/tmp/tollgate-p4/flow/") for b in body))

    def test_sessions_are_listed(self):
        self.write("passo1.jsonl", stream(("ls", "x")))
        self.write("events-passo1.jsonl", "")
        out = subprocess.run([sys.executable, "-B", "-I", str(GH4 / "flowcheck.py"), "sessions", str(self.tmp)],
                             capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.strip().split("\t"), ["passo1", "s-1", "/tmp/tollgate-p4/flow/protected"])


if __name__ == "__main__":
    unittest.main()
