import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

from tests.flowkit import FAKEGH, FlowLab
from tests.helpers import ROOT, git
from tests.hookkit import DEFAULT_TOML
from tests.test_protection import DETECT_MSG, PATH as PROTECTION_PATH, good
from tollgate_core import VERSION, clock, config, receipts
from tollgate_flow import init
from tollgate_gate import install, protection

FOLDER = "docs/superpowers/tollgate-init"
UNSET = {"status": 404, "message": "Branch not protected",
         "body": {"message": "Branch not protected"}}
DETECT = {"status": 403, "message": DETECT_MSG, "body": {"message": DETECT_MSG}}
NO_ADMIN = {"status": 403, "message": "Must have admin rights to Repository.",
            "body": {"message": "Must have admin rights to Repository."}}


def present(data=None):
    return {"status": 200, "body": data or good()}


class InitCase(unittest.TestCase):
    def make(self, protection_entry=None, **kw):
        fl = FlowLab(**kw)
        self.addCleanup(fl.close)
        self.fl = fl
        self.api(protection_entry if protection_entry is not None else UNSET)
        return fl

    def api(self, entry, **extra):
        self.fl.set_gh(api_status={PROTECTION_PATH: entry}, **extra)

    def run_init(self, *args, cwd=None):
        return self.fl.cli("init", *args, cwd=cwd)

    @property
    def folder(self) -> Path:
        return self.fl.main / FOLDER

    def proposal(self, *args) -> subprocess.CompletedProcess:
        r = self.run_init("--propose", *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def readme(self) -> str:
        return (self.folder / "README.md").read_text(encoding="utf-8")

    def toml(self) -> str:
        return (self.folder / "files" / "tollgate.toml").read_text(encoding="utf-8")

    def push(self, files: dict, message="cambio"):
        """Scrive i file nel checkout, li committa e li spinge sul predefinito (origin è locale)."""
        for rel, data in files.items():
            target = self.fl.main / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data if isinstance(data, bytes) else data.encode())
        self.fl.git("add", "-A")
        self.fl.git("commit", "-qm", message)
        self.fl.git("push", "-q", "origin", "main")

    def install_tree(self, **kw) -> dict:
        return install.files(ROOT, default_branch="main", services={}, **kw)


class ModeTest(InitCase):
    def test_detect_proposal(self):
        fl = self.make(DETECT)
        r = self.proposal()
        self.assertIn("detect", r.stdout)
        self.assertIn('mode = "detect"', self.toml())
        self.assertFalse((self.folder / "protect.sh").exists())
        self.assertFalse((self.folder / "protection.json").exists())
        self.assertIn("detect", self.readme())
        # il file è una configurazione valida
        self.assertEqual(config.load_config_text(self.toml()).get("gate.mode"), "detect")
        self.assertEqual(fl.git("status", "--porcelain", "--", "tollgate.toml"), "")

    def test_template_used_when_toml_is_missing(self):
        fl = self.make(DETECT)
        git(fl.main, "rm", "-q", "tollgate.toml")
        git(fl.main, "commit", "-qm", "senza toml")
        git(fl.main, "push", "-q", "origin", "main")
        self.proposal()
        cfg = config.load_config_text(self.toml())
        self.assertEqual(cfg.get("gate.mode"), "detect")
        self.assertNotIn("__MODE__", self.toml())
        self.assertIn("Da compilare", self.toml())

    def test_existing_toml_keeps_its_content_and_changes_only_the_mode(self):
        text = DEFAULT_TOML.replace('mode = "protected"', 'mode = "protected"   # misurata')
        text += '\n[levels]\nl0_max_files = 5\n'
        self.make(DETECT, toml=text)
        self.proposal()
        self.assertEqual(self.toml(), text.replace('"protected"   #', '"detect"   #'))

    def test_protected_unset_proposes_command(self):
        self.make(UNSET)
        r = self.proposal()
        self.assertIn('mode = "protected"', self.toml())
        script = (self.folder / "protect.sh").read_text(encoding="utf-8")
        self.assertIn(protection.BASE_JOB, script)
        self.assertIn(".app.id", script)
        self.assertIn("app.slug", script)
        self.assertNotIn("app_id: -1", script)
        self.assertNotIn('"app_id": -1', script)
        self.assertTrue(os.stat(self.folder / "protect.sh").st_mode & stat.S_IXUSR)
        self.assertIn("protect.sh", self.readme())
        body = json.loads((self.folder / "protection.json").read_text())
        self.assertEqual([c["app_id"] for c in body["required_status_checks"]["checks"]],
                         [protection.APP_ID_PLACEHOLDER] * 2)
        self.assertEqual(subprocess.run(["bash", "-n", str(self.folder / "protect.sh")]
                                        ).returncode, 0)
        self.assertIn("protected", r.stdout)

    def test_protected_with_missing_fields_lists_them(self):
        data = good()
        data["enforce_admins"] = {"enabled": False}
        self.make(present(data))
        r = self.proposal()
        self.assertIn("enforce_admins", self.readme())
        self.assertIn("enforce_admins", r.stdout)
        self.assertTrue((self.folder / "protect.sh").exists())

    def test_complete_protection_needs_no_script(self):
        self.make(present())
        self.proposal()
        self.assertIn('mode = "protected"', self.toml())
        self.assertFalse((self.folder / "protect.sh").exists())
        self.assertIn("protezione già completa", self.readme())

    def test_token_without_admin_undetermined(self):
        self.make(NO_ADMIN)
        r = self.run_init("--propose")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        text = r.stdout + r.stderr
        self.assertIn("non determinata", text)
        self.assertIn("tue credenziali", text)
        self.assertFalse(self.folder.exists())
        for entry in (None, {"status": 500, "message": "boom"}):
            self.fl.set_gh(**({"api_status": {PROTECTION_PATH: entry}} if entry else {}))
            r = self.run_init("--propose")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertFalse(self.folder.exists())

    def test_undetermined_also_refuses_update(self):
        fl = self.make(NO_ADMIN)
        self.push(self.install_tree())
        r = self.run_init("--update")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(self.folder.exists())

    def test_outside_a_repo_refuses(self):
        self.make(UNSET)
        with tempfile.TemporaryDirectory(prefix="tollgate fuori ") as outside:
            r = self.run_init("--propose", cwd=outside)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("repo git", r.stdout + r.stderr)

    def test_no_write_call_to_github(self):
        fl = self.make(UNSET)
        self.proposal()
        for call in fl.gh_calls():
            argv = call["argv"]
            self.assertEqual(argv[0], "api", argv)
            self.assertNotIn("--method", argv)
            self.assertNotIn("-f", argv)


class FilesTest(InitCase):
    def test_files_tree(self):
        self.make(UNSET)
        self.proposal()
        want = self.install_tree()
        got = {p.relative_to(self.folder / "files").as_posix(): p.read_bytes()
               for p in (self.folder / "files").rglob("*") if p.is_file()}
        self.assertEqual(set(got), set(want) | {"tollgate.toml"})
        for rel in want:
            self.assertEqual(got[rel], want[rel], rel)
        readme = self.readme()
        copy = readme.index("1. Copia")
        commit = readme.index("2. Fai un commit sul ramo predefinito")
        script = readme.index("3. ", commit)
        self.assertLess(copy, commit)
        self.assertLess(commit, script)
        self.assertIn("protect.sh", readme[script:script + 400])
        self.assertIn(f"{FOLDER}/files", readme)

    def test_default_branch_in_push_workflows(self):
        self.make(UNSET)
        self.proposal()
        base = (self.folder / "files/.github/workflows/tollgate-base.yml").read_text()
        self.assertIn("- 'main'", base)
        self.assertNotIn(install.BRANCH_PLACEHOLDER, base)

    def test_rerun_replaces_the_previous_proposal(self):
        self.make(UNSET)
        self.proposal()
        (self.folder / "files" / "vecchio.txt").write_text("x")
        (self.folder / "altro.md").write_text("tienimi")
        self.api(DETECT)
        self.proposal()
        self.assertFalse((self.folder / "files" / "vecchio.txt").exists())
        self.assertFalse((self.folder / "protect.sh").exists())
        self.assertEqual((self.folder / "altro.md").read_text(), "tienimi")

    def test_workflow_job_name_is_the_one_protect_reads(self):
        text = (ROOT / "gate/workflows/tollgate-base.yml").read_text()
        self.assertRegex(text, rf"(?m)^  {protection.BASE_JOB}:")
        for name in install.WORKFLOW_NAMES:
            if name != "base":
                other = (ROOT / f"gate/workflows/tollgate-{name}.yml").read_text()
                self.assertNotRegex(other, rf"(?m)^  {protection.BASE_JOB}:")
                self.assertNotIn(f"name: {protection.BASE_JOB}\n    runs", other)


class ServicesTest(InitCase):
    def test_services_reach_the_run_workflow(self):
        self.make(UNSET)
        self.proposal("--service", "db=postgres:16", "--service", "cache=redis:7,6379")
        run = (self.folder / "files/.github/workflows/tollgate-run.yml").read_text()
        self.assertIn("        image: 'postgres:16'", run)
        self.assertIn("        image: 'redis:7'\n        ports:\n          - \"6379:6379\"", run)
        # db non ha porta: nessuna se non richiesta; i job `head` e `base` hanno gli stessi servizi
        self.assertEqual(run.count("ports:"), 2)
        base = (self.folder / "files/.github/workflows/tollgate-base.yml").read_text()
        self.assertIn("        image: 'redis:7'", base)
        self.assertIn("db", self.readme())

    def test_untrusted_names(self):
        self.make(UNSET)
        for service in ("DB=x", "a b=x", "d:b=x", "-db=x", "db=x y", "db=x\ny", "db=",
                        "db=postgres:16,0", "db=postgres:16,70000", "db=postgres:16,54x2",
                        "db=postgres:16,", "db", "=x", "db=x;rm", "db=$(x)"):
            r = self.run_init("--propose", "--service", service)
            self.assertNotEqual(r.returncode, 0, service)
            self.assertFalse(self.folder.exists(), service)

    def test_untrusted_names_through_the_api(self):
        fl = self.make(UNSET)
        with mock.patch.dict(os.environ, fl.env()):
            for services in ({"Bad Name": "x"}, {"db": "x y"}, {"db": "x\n  evil: 1"},
                             {"DB": "x"}, {"": "x"}):
                got = init.propose(fl.ts.state, fl.main, update=False, merges_per_month=10,
                                   services=services)
                self.assertEqual(got.code, init.REFUSED, services)
                self.assertIsNone(got.folder)
        self.assertFalse(self.folder.exists())

    def test_duplicate_service_is_refused(self):
        self.make(UNSET)
        r = self.run_init("--propose", "--service", "db=a", "--service", "db=b")
        self.assertNotEqual(r.returncode, 0)


class EstimateTest(InitCase):
    def receipt(self, sha, command, duration, produced_by="finish"):
        self.fl.lab.now += timedelta(seconds=1)
        receipts.add(self.fl.conn, work=None, sha=sha, command=command, resolved_command=None,
                     exit_code=0, tests_run=1, tests_skipped=0, duration=duration, log=None,
                     produced_by=produced_by, state="green", now=self.fl.lab.now)

    def test_minutes_estimate(self):
        self.make(UNSET)
        self.receipt("a" * 40, "verify", 90.0)
        self.proposal("--merges-per-month", "10")
        text = self.readme()
        # 90 s → 2 minuti fatturati; base + gate = 4 minuti a merge; 10 merge → 40 minuti
        self.assertIn("40 minuti al mese", text)
        self.assertIn("2.000", text)
        self.assertNotIn("non misurata", text)

    def test_no_receipts_is_not_measured(self):
        self.make(UNSET)
        self.proposal()
        self.assertIn("non misurata", self.readme())
        self.assertIn("2.000", self.readme())

    def test_sha_must_have_a_receipt_for_every_gate_command(self):
        toml = DEFAULT_TOML.replace('gate = ["verify"]', 'lint = "true"\ngate = ["verify", "lint"]')
        self.make(UNSET, toml=toml)
        old, new = "a" * 40, "b" * 40
        self.receipt(old, "verify", 600.0)
        self.receipt(old, "verify", 60.0)         # vale l'ultima ricevuta del comando
        self.receipt(old, "lint", 30.0)
        self.receipt(new, "verify", 3000.0)       # più recente ma senza lint: non vale
        self.proposal("--merges-per-month", "5")
        self.assertIn("20 minuti al mese", self.readme())     # 90 s → 2 min, ×2, ×5

    def test_only_finish_and_verify_receipts_count(self):
        self.make(UNSET)
        self.receipt("a" * 40, "verify", 90.0, produced_by="gate")
        self.proposal()
        self.assertIn("non misurata", self.readme())

    def test_missing_duration_is_not_measured(self):
        self.make(UNSET)
        self.receipt("a" * 40, "verify", None)
        self.proposal()
        self.assertIn("non misurata", self.readme())

    def test_invalid_merges_per_month(self):
        self.make(UNSET)
        for value in ("0", "-3", "x"):
            r = self.run_init("--propose", "--merges-per-month", value)
            self.assertNotEqual(r.returncode, 0, value)


class HintsTest(InitCase):
    def test_jest_junit_hint(self):
        self.make(UNSET)
        self.push({"package.json": json.dumps({"devDependencies": {"jest": "^29.0.0"}})})
        self.proposal()
        text = self.readme()
        self.assertIn("jest-junit", text)
        self.assertIn('"classNameTemplate": "{filepath}"', text)
        self.assertIn('"titleTemplate": "{classname} {title}"', text)

    def test_no_jest_no_hint(self):
        self.make(UNSET)
        self.push({"package.json": json.dumps({"devDependencies": {"vitest": "^1.0.0"}})})
        self.proposal()
        self.assertNotIn("classNameTemplate", self.readme())

    def test_unreadable_package_json_is_no_hint(self):
        self.make(UNSET)
        self.push({"package.json": "{ non json"})
        self.proposal()
        self.assertNotIn("classNameTemplate", self.readme())

    def test_separate_agent_token_paragraph(self):
        self.make(UNSET)
        self.proposal()
        text = self.readme()
        self.assertIn("token", text)
        self.assertIn("amministrazione", text)

    def test_existing_workflow_violations_listed(self):
        self.make(UNSET)
        self.push({".github/workflows/ci.yml": "name: ci\non: pull_request\n"
                                               "permissions:\n  statuses: write\n"
                                               "jobs:\n  t:\n    runs-on: ubuntu-latest\n"
                                               "    steps:\n      - run: echo ok\n",
                   ".github/workflows/lint.yaml": "name: lint\non: pull_request\n"
                                                  "permissions:\n  contents: read\n"
                                                  "jobs:\n  t:\n    runs-on: ubuntu-latest\n"
                                                  "    steps:\n      - run: echo ok\n",
                   ".github/workflows/tollgate-extra.yml": "name: x\non: push\n"})
        r = self.proposal()
        text = self.readme()
        self.assertIn(".github/workflows/ci.yml", text)
        self.assertIn("statuses: write", text)
        self.assertNotIn("lint.yaml", text)
        self.assertNotIn("tollgate-extra", text)
        self.assertIn("ci.yml", r.stdout)

    def test_no_violations_no_section(self):
        self.make(UNSET)
        self.proposal()
        self.assertNotIn("Workflow già presenti", self.readme())


class UpdateTest(InitCase):
    def test_update_only_changed_files(self):
        self.make(UNSET)
        tree = self.install_tree()
        tree["tollgate.toml"] = DEFAULT_TOML
        old = dict(tree)
        old[".github/tollgate/VERSION"] = b"0.0.1\n"
        old[".github/workflows/tollgate-guard.yml"] = tree[
            ".github/workflows/tollgate-guard.yml"] + b"# vecchio\n"
        old[".github/tollgate/bin/tollgate_gate/morto.py"] = b"x = 1\n"
        self.push(old)
        r = self.run_init("--update")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        got = {p.relative_to(self.folder / "files").as_posix()
               for p in (self.folder / "files").rglob("*") if p.is_file()}
        self.assertEqual(got, {".github/tollgate/VERSION", ".github/workflows/tollgate-guard.yml"})
        text = self.readme()
        self.assertIn(f"tollgate-config/{VERSION}", text)
        self.assertIn(".github/tollgate/bin/tollgate_gate/morto.py", text)
        self.assertIn("da cancellare", text)
        self.assertIn(f"tollgate-config/{VERSION}", r.stdout)

    def test_update_with_nothing_changed(self):
        self.make(UNSET)
        tree = self.install_tree()
        tree["tollgate.toml"] = DEFAULT_TOML
        self.push(tree)
        r = self.run_init("--update")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nulla da aggiornare", r.stdout)
        self.assertFalse(self.folder.exists())

    def test_update_new_mode_rewrites_toml(self):
        self.make(DETECT)
        tree = self.install_tree()
        tree["tollgate.toml"] = DEFAULT_TOML           # `protected` sul predefinito
        self.push(tree)
        self.run_init("--update")
        files = {p.relative_to(self.folder / "files").as_posix()
                 for p in (self.folder / "files").rglob("*") if p.is_file()}
        self.assertEqual(files, {"tollgate.toml"})
        self.assertIn('mode = "detect"', self.toml())

    def test_update_without_toml_refuses(self):
        fl = self.make(UNSET)
        git(fl.main, "rm", "-q", "tollgate.toml")
        git(fl.main, "commit", "-qm", "senza toml")
        git(fl.main, "push", "-q", "origin", "main")
        r = self.run_init("--update")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--propose", r.stdout + r.stderr)


class ModeRewriteTest(unittest.TestCase):
    def test_with_mode(self):
        w = init.with_mode
        self.assertEqual(w('[gate]\nmode = "protected"\n', "detect"), '[gate]\nmode = "detect"\n')
        self.assertEqual(w('[gate]\nmode="protected"  # x\n[a]\nmode = "z"\n', "detect"),
                         '[gate]\nmode="detect"  # x\n[a]\nmode = "z"\n')
        self.assertEqual(w('[a]\nmode = "z"\n[gate]\n[b]\nx = 1\n', "detect"),
                         '[a]\nmode = "z"\n[gate]\nmode = "detect"\n[b]\nx = 1\n')
        self.assertEqual(w("schema_version = 1\n", "detect"),
                         'schema_version = 1\n\n[gate]\nmode = "detect"\n')
        self.assertEqual(w("schema_version = 1", "detect"),
                         'schema_version = 1\n\n[gate]\nmode = "detect"\n')


class ProtectScriptTest(InitCase):
    """`protect.sh` con il `gh` finto nel PATH: legge `app.id` dal check-run di `tollgate-base`."""

    SHA = "c" * 40

    def setUp(self):
        self.fl = None

    def script(self):
        self.make(UNSET)
        self.proposal()
        return self.folder / "protect.sh"

    def run_script(self, script, check_runs, *args, cwd=None):
        fl = self.fl
        fake = fl.tmp / "fakebin"
        fake.mkdir(exist_ok=True)
        wrapper = fake / "gh"
        wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKEGH}" "$@"\n')
        wrapper.chmod(0o755)
        fl.set_gh(check_runs=check_runs)
        env = {"PATH": f"{fake}:/usr/bin:/bin", "HOME": str(fl.home),
               "TOLLGATE_FAKEGH_DATA": str(fl.gh_data), "TOLLGATE_FAKEGH_LOG": str(fl.gh_log)}
        which = subprocess.run(["sh", "-c", "command -v gh"], env=env, capture_output=True,
                               text=True).stdout.strip()
        self.assertEqual(which, str(wrapper))       # mai il gh vero
        return subprocess.run(["bash", str(script), *args], cwd=str(cwd or fl.main), env=env,
                              capture_output=True, text=True, timeout=60)

    def puts(self):
        return json.loads(self.fl.gh_data.read_text()).get("protection_puts", [])

    @staticmethod
    def run_row(name="tollgate-base", status="completed", conclusion="success", app_id=15368,
                slug="github-actions"):
        return {"name": name, "status": status, "conclusion": conclusion,
                "app": {"id": app_id, "slug": slug}}

    def test_reads_app_id_and_puts_the_body(self):
        script = self.script()
        runs = {self.SHA: [self.run_row("altro-job", app_id=999),
                           self.run_row(app_id=15368),
                           self.run_row(app_id=15368, conclusion="failure")]}
        r = self.run_script(script, runs, self.SHA)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        body = self.puts()[0]
        self.assertEqual([c["app_id"] for c in body["required_status_checks"]["checks"]],
                         [15368, 15368])
        self.assertTrue(body["required_status_checks"]["strict"])
        self.assertEqual(len(self.puts()), 1)
        path = [c["argv"] for c in self.fl.gh_calls() if "--method" in c["argv"]][0][-1]
        self.assertEqual(path, "repos/{owner}/{repo}/branches/main/protection")

    def test_default_sha_is_the_tip_of_origin(self):
        script = self.script()
        tip = self.fl.git("rev-parse", "origin/main")
        r = self.run_script(script, {tip: [self.run_row(app_id=15368)]})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.puts()), 1)

    def test_stops_without_the_check_run(self):
        script = self.script()
        for runs in ({}, {self.SHA: []},
                     {self.SHA: [self.run_row("altro-job")]},
                     {self.SHA: [self.run_row(slug="altra-app", app_id=7)]}):
            r = self.run_script(script, runs, self.SHA)
            self.assertNotEqual(r.returncode, 0, runs)
            self.assertEqual(self.puts(), [], runs)
            self.assertIn(protection.BASE_JOB, r.stdout + r.stderr)

    def test_stops_when_base_is_not_finished(self):
        script = self.script()
        r = self.run_script(script, {self.SHA: [self.run_row(status="in_progress",
                                                             conclusion=None)]}, self.SHA)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("finito", r.stdout + r.stderr)
        self.assertEqual(self.puts(), [])

    def test_stops_on_ambiguous_or_odd_app_ids(self):
        script = self.script()
        for rows in ([self.run_row(app_id=1), self.run_row(app_id=2)],
                     [self.run_row(app_id=-1)], [self.run_row(app_id=0)],
                     [self.run_row(app_id="1; rm -rf /")]):
            r = self.run_script(script, {self.SHA: rows}, self.SHA)
            self.assertNotEqual(r.returncode, 0, rows)
            self.assertEqual(self.puts(), [], rows)

    def test_rejects_a_malformed_sha_argument(self):
        script = self.script()
        for arg in ("main", "abc", "--help", self.SHA + "x", "$(id)"):
            r = self.run_script(script, {self.SHA: [self.run_row()]}, arg)
            self.assertNotEqual(r.returncode, 0, arg)
        self.assertEqual(self.puts(), [])

    def test_script_text_quotes_names_and_never_uses_minus_one(self):
        script = self.script().read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", script)
        self.assertNotRegex(script, r"app_id\W+-1")
        self.assertIn("BRANCH='main'", script)
        self.assertIn("JOB='tollgate-base'", script)


if __name__ == "__main__":
    unittest.main()
