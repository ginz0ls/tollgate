import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

from tests.flowkit import FAKEGH, GATE_FILES, JUNIT_FILES, FlowLab
from tests.helpers import ROOT, git
from tests.hookkit import DEFAULT_FILES, DEFAULT_TOML
from tests.test_gate_workflows import PINNED, uses_of
from tests.test_protection import DETECT_MSG, PATH as PROTECTION_PATH, good
from tollgate_analysis import globs, profiles, research
from tollgate_core import VERSION, clock, config, fragments, phases, receipts
from tollgate_core import git as core_git
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

    def test_proposal_workflows_pinned(self):
        """Le azioni del gate (fissate per SHA) arrivano intatte nella proposta di `init`."""
        self.make(UNSET)
        self.proposal()
        for name in install.WORKFLOW_NAMES:
            rel = f"gate/workflows/tollgate-{name}.yml"
            proposed = (self.folder / f"files/.github/workflows/tollgate-{name}.yml").read_text()
            self.assertEqual(uses_of(proposed), uses_of((ROOT / rel).read_text()), name)
            for uses in uses_of(proposed):
                self.assertRegex(uses, PINNED)

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
                        "db=postgres:16,", "db", "=x", "db=x;rm", "db=$(x)", "db\n=x", "db=x\n",
                        "d_b=x"):
            r = self.run_init("--propose", "--service", service)
            self.assertNotEqual(r.returncode, 0, service)
            self.assertFalse(self.folder.exists(), service)

    def test_untrusted_names_through_the_api(self):
        fl = self.make(UNSET)
        with mock.patch.dict(os.environ, fl.env()):
            for services in ({"Bad Name": "x"}, {"db": "x y"}, {"db": "x\n  evil: 1"},
                             {"DB": "x"}, {"": "x"}, {"db\n": "x"}, {"db": "x\n"},
                             {"db": "x:"}, {"d_b": "x"}):
                got = init.propose(fl.ts.state, fl.main, update=False, merges_per_month=10,
                                   services=services)
                self.assertEqual(got.code, init.REFUSED, services)
                self.assertIsNone(got.folder)
        self.assertFalse(self.folder.exists())

    def test_one_rule_for_init_and_install(self):
        """La regola dei servizi sta in `install`: `files` rifiuta ciò che `init` rifiuta."""
        for services in ({"db\n": "x"}, {"db": "x\n"}, {"DB": "x"}, {"d_b": "x"}, {"-db": "x"}):
            with self.assertRaises(ValueError, msg=services):
                install.files(ROOT, default_branch="main", services=services)
            with self.assertRaises(ValueError, msg=services):
                install.validate_services(services)
        install.validate_services({"db": "postgres:16", "my-cache2": "redis"}, {"db": 5432})
        self.assertFalse(hasattr(init, "SERVICE_NAME"))

    def test_duplicate_service_is_refused(self):
        self.make(UNSET)
        r = self.run_init("--propose", "--service", "db=a", "--service", "db=b")
        self.assertNotEqual(r.returncode, 0)


class EstimateTest(InitCase):
    def make(self, *args, **kw):
        return super().make(*args, issue=7, **kw)

    def receipt(self, sha, command, duration, produced_by="finish", state="green", work=None):
        self.fl.lab.now += timedelta(seconds=1)
        receipts.add(self.fl.conn, work=work or self.fl.work, sha=sha, command=command,
                     resolved_command=None, exit_code=0, tests_run=1, tests_skipped=0,
                     duration=duration, log=None, produced_by=produced_by, state=state,
                     now=self.fl.lab.now)

    def other_repo_work(self):
        return phases.create_work(self.fl.conn, repo_key="github.com/altro/repo", issue=3,
                                  level="L1", now=self.fl.lab.now)

    def test_receipts_of_another_repo_do_not_count(self):
        self.make(UNSET)
        self.receipt("a" * 40, "verify", 3000.0, work=self.other_repo_work())
        self.proposal()
        self.assertIn("non misurata", self.readme())
        self.receipt("b" * 40, "verify", 90.0)
        self.proposal("--merges-per-month", "10")
        self.assertIn("40 minuti al mese", self.readme())

    def test_receipts_without_work_do_not_count(self):
        self.make(UNSET)
        self.fl.lab.now += timedelta(seconds=1)
        receipts.add(self.fl.conn, work=None, sha="a" * 40, command="verify",
                     resolved_command=None, exit_code=0, tests_run=1, tests_skipped=0,
                     duration=90.0, log=None, produced_by="finish", state="green",
                     now=self.fl.lab.now)
        self.proposal()
        self.assertIn("non misurata", self.readme())

    def test_only_green_receipts_count(self):
        self.make(UNSET)
        self.receipt("a" * 40, "verify", 90.0)
        self.receipt("b" * 40, "verify", 9000.0, state="red")      # più recente ma rossa
        self.receipt("c" * 40, "verify", 5.0, state="empty")
        self.proposal("--merges-per-month", "10")
        self.assertIn("40 minuti al mese", self.readme())

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

    def test_workflow_names_are_neutralized_in_the_readme(self):
        self.make(UNSET)
        evil = ".github/workflows/a`b\n## Falso.yml"
        real_ls, real_text = init.git.ls_files_at, init.git.text_at

        def ls(repo, ref, prefix):
            return [evil] if prefix == ".github/workflows/" else real_ls(repo, ref, prefix)

        def text(repo, ref, path):
            return "on: pull_request_target\n" if path == evil else real_text(repo, ref, path)

        with mock.patch.object(init.git, "ls_files_at", ls), \
                mock.patch.object(init.git, "text_at", text):
            fl = self.fl
            with mock.patch.dict(os.environ, fl.env()):
                got = init.propose(fl.ts.state, fl.main, update=False, merges_per_month=5,
                                   services={})
        self.assertEqual(got.code, init.OK)
        text = self.readme()
        self.assertLess(text.index("```"), text.index("## Falso"))      # dentro il recinto
        self.assertLess(text.index("## Falso"), text.rindex("```"))
        self.assertNotIn("\n## Falso", "\n".join(got.lines))

    def test_template_readme_says_to_fill_commands(self):
        fl = self.make(DETECT)
        git(fl.main, "rm", "-q", "tollgate.toml")
        git(fl.main, "commit", "-qm", "senza toml")
        git(fl.main, "push", "-q", "origin", "main")
        self.proposal()
        self.assertIn("compila `[commands]`", self.readme())

    def test_existing_toml_readme_does_not_ask_to_fill_commands(self):
        self.make(DETECT)
        self.proposal()
        self.assertNotIn("compila `[commands]`", self.readme())

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

    def test_update_with_nothing_changed_still_reports_missing_protection(self):
        self.make(UNSET)
        tree = self.install_tree()
        tree["tollgate.toml"] = DEFAULT_TOML
        self.push(tree)
        r = self.run_init("--update")
        self.assertIn("nulla da aggiornare", r.stdout)
        self.assertIn("senza protezione", r.stdout)
        self.assertIn("--propose", r.stdout)
        self.api(present())
        r = self.run_init("--update")
        self.assertNotIn("protezione", r.stdout)

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


    def test_with_mode_single_quoted_value(self):
        """Un valore tra apici singoli (TOML lo ammette) si sostituisce, non si duplica."""
        w = init.with_mode
        self.assertEqual(w("[gate]\nmode = 'protected'\n", "detect"), '[gate]\nmode = "detect"\n')
        self.assertEqual(w("[gate]\nmode='protected'  # x\n[a]\nmode = 'z'\n", "detect"),
                         '[gate]\nmode="detect"  # x\n[a]\nmode = \'z\'\n')
        for text in ("[gate]\nmode = 'protected'\n", "[gate]\nmode = \"protected\"\n"):
            out = w(text, "detect")
            self.assertEqual(out.count("mode"), 1, out)
            self.assertEqual(tomllib.loads(out)["gate"]["mode"], "detect")


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


FRAGMENT_X = """[profile]
paths = ["**/x/**"]
min_level = "L1"
agent = "tollgate:implementer-x"
reviewer = "tollgate:reviewer-x"
"""
SKILL_X = "---\nname: rules-x\napproved: 2026-11-01\n---\n# Regole x\n\n" \
          "R-X-01 [blocca] uno\n\nR-X-02 due\n"
BASE_TOML = 'schema_version = 1\n[gate]\nmode = "protected"\n'
DECLARED_X = ('[profiles.x]\npaths = ["src/x/**"]\nrules = ["R-X-01", "R-X-02"]\n'
              'blocking_rules = ["R-X-01"]\nagent = "tollgate:implementer-x"\n'
              'reviewer = "tollgate:reviewer-x"\n')


def _real_fragments_root(test, areas=None) -> Path:
    """Una radice temporanea con i frammenti veri di `templates/profiles/` (quelli di `areas`, o
    tutti) e, per ciascuno, una skill finta già approvata: `init.profile_blocks` li propone."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    root = Path(tmp.name)
    (root / "templates" / "profiles").mkdir(parents=True)
    for fr in fragments.load(ROOT):
        if areas is not None and fr.area not in areas:
            continue
        shutil.copy(fr.source, root / "templates" / "profiles" / fr.source.name)
        skill = root / "skills" / f"rules-{fr.area}"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\napproved: 2026-11-01\n---\nR-{fr.area.upper()}-01 [blocca] x\n",
            encoding="utf-8")
    return root


class PluginMixin:
    """Un plugin temporaneo con il frammento `x`, la sua skill e i suoi agenti."""

    def plugin(self, *, approved=True, agents=("implementer-x", "reviewer-x"),
               fragment=FRAGMENT_X, skill=SKILL_X) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "templates" / "profiles").mkdir(parents=True)
        (root / "templates" / "profiles" / "x.toml").write_text(fragment, encoding="utf-8")
        (root / "skills" / "rules-x").mkdir(parents=True)
        text = skill if approved else skill.replace("approved: 2026-11-01\n", "")
        (root / "skills" / "rules-x" / "SKILL.md").write_text(text, encoding="utf-8")
        (root / "agents").mkdir()
        for name in agents:
            (root / "agents" / f"{name}.md").write_text("---\nname: a\n---\n", encoding="utf-8")
        return root


class ProfileBlocksTest(PluginMixin, unittest.TestCase):
    def blocks(self, files, current=BASE_TOML, root=None, **kw):
        sizes = {f: 10 for f in files} if isinstance(files, (list, tuple)) else files
        return init.profile_blocks(sizes, current, root or self.plugin(), **kw)

    def profile(self, got, current=BASE_TOML):
        return tomllib.loads(current + got.text)["profiles"]["x"]

    def test_approved_profile_with_files_proposed(self):
        got = self.blocks({"src/x/a.py": 10, "README.md": 3})
        self.assertIn("[profiles.x]", got.text)
        self.assertIn("# profilo x da templates/profiles/x.toml", got.text)
        prof = self.profile(got)
        self.assertEqual(prof["paths"], ["src/x/**"])
        self.assertEqual(prof["rules"], ["R-X-01", "R-X-02"])
        self.assertEqual(prof["blocking_rules"], ["R-X-01"])
        self.assertEqual(prof["min_level"], "L1")
        shown = "\n".join(got.lines)
        self.assertIn("src/x/a.py", shown)
        self.assertIn("1 file", shown)

    def test_unapproved_profile_not_proposed(self):
        got = self.blocks(["src/x/a.py"], root=self.plugin(approved=False))
        self.assertEqual((got.text, got.lines), ("", []))

    def test_profile_without_files_not_proposed(self):
        got = self.blocks(["README.md", "src/y/a.py"])
        self.assertEqual(got.text, "")
        self.assertTrue(any("x" in line and "nessun file" in line for line in got.lines),
                        got.lines)

    def test_claude_agents_do_not_light_ai(self):
        self.assertEqual(self.blocks([".claude/x/a.md", ".claude/agents/x/b.md"]).text, "")

    def test_install_dir_does_not_light_profile(self):
        got = self.blocks([".github/tollgate/bin/x/a.py", "docs/superpowers/tollgate-init/x/b"])
        self.assertEqual(got.text, "")
        # Decisione 18: le cartelle di GitHub dei workflow e delle azioni non accendono profili.
        self.assertEqual(init.EXCLUDED_PREFIXES,
                         (".claude/", ".github/tollgate/", "docs/superpowers/tollgate-init/",
                          ".github/workflows/", ".github/actions/"))

    def test_concrete_paths_escaped(self):
        got = self.blocks(["app/[id]/x/p.ts"])
        pattern = self.profile(got)["paths"][0]
        self.assertEqual(pattern, "app/\\[id\\]/x/**")
        self.assertTrue(globs.match(pattern, "app/[id]/x/p.ts"))
        self.assertFalse(globs.match(pattern, "app/i/x/p.ts"))

    def test_root_folder_pattern_matches_like_the_folder(self):
        pattern = self.profile(self.blocks(["x/a.py"]))["paths"][0]
        self.assertTrue(globs.match(pattern, "x/a.py"))
        self.assertFalse(globs.match(pattern, "src/x/a.py"))

    def test_nested_dirs_first_match(self):
        got = self.blocks(["src/x/lib/x/a.py", "src/x/b.py"])
        self.assertEqual(self.profile(got)["paths"], ["src/x/**"])

    def test_file_named_like_the_folder_is_not_a_folder(self):
        self.assertEqual(self.blocks(["src/x"]).text, "")

    def test_declared_profile_rules_drift_reported(self):
        current = BASE_TOML + DECLARED_X.replace('"R-X-01", "R-X-02"', '"R-X-01"')
        got = self.blocks(["src/x/a.py"], current)
        self.assertEqual(got.text, "")
        self.assertEqual(len(got.lines), 1, got.lines)
        self.assertIn("R-X-02", got.lines[0])
        self.assertIn("aggiungi", got.lines[0])
        self.assertIn("rules", got.lines[0])

    def test_declared_profile_blocking_rules_drift_reported(self):
        current = BASE_TOML + DECLARED_X.replace('blocking_rules = ["R-X-01"]',
                                                 'blocking_rules = []')
        got = self.blocks(["src/x/a.py"], current)
        self.assertEqual(len(got.lines), 1, got.lines)
        self.assertIn("blocking_rules", got.lines[0])
        self.assertIn("R-X-01", got.lines[0])

    def test_declared_profile_stale_rule_removal_reported(self):
        current = BASE_TOML + DECLARED_X.replace(
            '"R-X-01", "R-X-02"]', '"R-X-01", "R-X-02", "R-X-09", "mia-regola"]')
        got = self.blocks(["src/x/a.py"], current)
        self.assertEqual(len(got.lines), 1, got.lines)
        self.assertIn("togli", got.lines[0])
        self.assertIn("R-X-09", got.lines[0])
        self.assertNotIn("mia-regola", got.lines[0])

    def test_declared_profile_new_paths_reported(self):
        current = BASE_TOML + DECLARED_X.replace(
            'paths = ["src/x/**"]', 'paths = ["src/x/**", "!src/x/gen/**"]')
        got = self.blocks(["src/x/a.py", "lib/x/a.py", "lib/x/b.py", "src/x/gen/c.py"], current)
        self.assertEqual(got.text, "")
        self.assertEqual(len(got.lines), 1, got.lines)
        self.assertIn("paths", got.lines[0])
        self.assertIn('"lib/x/**"', got.lines[0])
        self.assertIn("2 file", got.lines[0])
        self.assertNotIn("gen", got.lines[0])

    def test_declared_negation_respected_in_both_orders(self):
        for paths in ('["!lib/x/gen/**", "lib/x/**"]', '["lib/x/**", "!lib/x/gen/**"]'):
            with self.subTest(paths=paths):
                current = BASE_TOML + DECLARED_X.replace('["src/x/**"]', paths)
                self.assertEqual(self.blocks(["lib/x/gen/a.py", "lib/x/b.py"], current).lines, [])

    def test_declared_profile_agent_now_available(self):
        current = BASE_TOML + DECLARED_X.replace('agent = "tollgate:implementer-x"\n', "")
        got = self.blocks(["src/x/a.py"], current)
        self.assertEqual(len(got.lines), 1, got.lines)
        self.assertIn("agent", got.lines[0])
        self.assertIn("tollgate:implementer-x", got.lines[0])

    def test_declared_empty_agent_is_a_choice(self):
        current = BASE_TOML + DECLARED_X.replace('agent = "tollgate:implementer-x"', 'agent = ""')
        self.assertEqual(self.blocks(["src/x/a.py"], current).lines, [])

    def test_declared_agent_missing_in_plugin_is_silent(self):
        current = BASE_TOML + DECLARED_X.replace('agent = "tollgate:implementer-x"\n', "")
        got = self.blocks(["src/x/a.py"], current, root=self.plugin(agents=("reviewer-x",)))
        self.assertEqual(got.lines, [])

    def test_declared_profile_same_rules_silent_ok(self):
        got = self.blocks(["src/x/a.py"], BASE_TOML + DECLARED_X)
        self.assertEqual((got.text, got.lines), ("", []))

    def test_declared_unapproved_profile_is_silent(self):
        current = BASE_TOML + DECLARED_X.replace('"R-X-01", "R-X-02"', '"R-X-01"')
        got = self.blocks(["lib/x/a.py"], current, root=self.plugin(approved=False))
        self.assertEqual((got.text, got.lines), ("", []))

    def test_paths_shown_neutralized(self):
        got = self.blocks(["src/x/a\x1b[31mb.py"])
        self.assertNotIn("\x1b", "\n".join(got.lines))
        self.assertNotIn("\x1b", got.readme)
        self.assertIn("## Profili proposti", got.readme)
        self.assertIn("src/x/**", got.readme)

    def test_readme_keeps_one_line_per_note(self):
        current = BASE_TOML + '[profiles.web]\npaths = ["src/**"]\n'
        got = self.blocks(["src/x/a.py"], current,
                          root=self.plugin(agents=("reviewer-x",)))
        self.assertNotIn("?profilo", got.readme)
        self.assertIn("\nprofilo x: src/x/a.py corrisponde anche a «web»", got.readme)
        self.assertIn("implementer-x", got.readme)

    def test_readme_declared_drift_section(self):
        current = BASE_TOML + DECLARED_X.replace('"R-X-01", "R-X-02"', '"R-X-01"')
        got = self.blocks(["src/x/a.py"], current)
        self.assertIn("## Profili da controllare", got.readme)
        self.assertIn("\nprofilo x: [profiles.x] rules: aggiungi \"R-X-02\"", got.readme)

    def test_active_lists_new_area_warned(self):
        current = BASE_TOML + '[profiles]\nactive = ["x"]\n'
        got = self.blocks(["src/x/a.py"], current)
        self.assertIn("[profiles.x]", got.text)
        warned = [line for line in got.lines if "active" in line]
        self.assertEqual(len(warned), 1, got.lines)
        self.assertIn("ogni task", warned[0])

    def test_active_without_the_area_is_not_warned(self):
        current = BASE_TOML + '[profiles]\nactive = ["other"]\n'
        self.assertFalse([l for l in self.blocks(["src/x/a.py"], current).lines
                          if "active" in l])

    def test_overlap_with_declared_vertical_shown(self):
        current = BASE_TOML + '[profiles.web]\npaths = ["src/**"]\n'
        got = self.blocks(["src/x/a.py"], current)
        line = next(l for l in got.lines if "«web»" in l)
        self.assertIn("src/x/a.py", line)
        self.assertIn("vince x", line)
        tie = BASE_TOML + '[profiles.web]\npaths = ["src/x/a.*"]\n'
        line = next(l for l in self.blocks(["src/x/a.py"], tie).lines if "«web»" in l)
        self.assertIn("vince web", line)

    def test_missing_agent_dropped(self):
        got = self.blocks(["src/x/a.py"], root=self.plugin(agents=("reviewer-x",)))
        prof = self.profile(got)
        self.assertNotIn("agent", prof)
        self.assertEqual(prof["reviewer"], "tollgate:reviewer-x")
        self.assertTrue(any("implementer-x" in l for l in got.lines), got.lines)

    def test_proposed_rules_match_skill(self):
        skill = SKILL_X + "\nR-X-03 [blocca] tre\n\nR-X-10 dieci\n\nvedi R-X-04 a metà riga\n"
        got = self.blocks(["src/x/a.py"], root=self.plugin(skill=skill))
        known, blocking = research.area_rules(skill, "x")
        prof = self.profile(got)
        self.assertEqual(prof["rules"], sorted(known))
        self.assertEqual(prof["blocking_rules"], sorted(blocking))
        self.assertNotIn("R-X-04", prof["rules"])

    def test_proposal_validates(self):
        got = self.blocks({"src/x/a.py": 1, "lib/x/b.py": 1})
        cfg = config.load_config_text(BASE_TOML + got.text)
        self.assertEqual(cfg.warnings, [])
        self.assertEqual(cfg.profiles["x"]["paths"], ["lib/x/**", "src/x/**"])
        self.assertEqual(cfg.profiles["x"]["agent"], "tollgate:implementer-x")

    def test_text_appends_to_a_toml_without_final_newline(self):
        current = BASE_TOML.rstrip("\n")
        got = self.blocks(["src/x/a.py"], current)
        self.assertEqual(config.load_config_text(current + got.text).warnings, [])

    def test_detected_files_added_with_exact_path(self):
        got = self.blocks(["src/x/a.py"], detected={"x": ["edge/fn.ts", "src/x/a.py"]})
        self.assertEqual(self.profile(got)["paths"], ["edge/fn.ts", "src/x/**"])

    def test_detected_files_alone_light_the_profile(self):
        got = self.blocks(["README.md"], detected={"x": ["edge/fn.ts"]})
        self.assertEqual(self.profile(got)["paths"], ["edge/fn.ts"])

    def test_declared_detected_files_reported_unless_covered(self):
        current = BASE_TOML + DECLARED_X
        got = self.blocks(["src/x/a.py"], current,
                          detected={"x": ["edge/fn.ts", "src/x/gen.py"]})
        self.assertEqual(len(got.lines), 1, got.lines)
        self.assertIn('"edge/fn.ts"', got.lines[0])

    def test_no_fragments_no_output(self):
        root = self.plugin()
        (root / "templates" / "profiles" / "x.toml").unlink()
        got = self.blocks(["src/x/a.py"], root=root)
        self.assertEqual((got.text, got.lines, got.readme), ("", [], ""))

    def test_does_not_touch_git_or_network(self):
        with mock.patch("tollgate_core.git._proc", side_effect=AssertionError("git")):
            self.assertIn("[profiles.x]", self.blocks(["src/x/a.py"]).text)

    def paths_of(self, patterns, files, **kw):
        """I `paths` proposti dal frammento `x` con i `patterns` dati (lista di stringhe)."""
        toml = FRAGMENT_X.replace('["**/x/**"]', json.dumps(patterns))
        got = self.blocks(files, root=self.plugin(fragment=toml), **kw)
        return tomllib.loads(BASE_TOML + got.text)["profiles"]["x"]["paths"] if got.text else None

    def test_name_pattern_exact_paths(self):
        files = ["Dockerfile", "services/api/Dockerfile", "services/api/Dockerfile.prod"]
        paths = self.paths_of(["**/Dockerfile*"], files)
        self.assertEqual(paths, ["/Dockerfile", "services/api/Dockerfile",
                                 "services/api/Dockerfile.prod"])
        for f in files:
            self.assertEqual(len([p for p in paths if globs.match(p, f)]), 1, f)

    def test_concrete_for_exclude_default_is_b4(self):
        pats = fragments.load(self.plugin(fragment=FRAGMENT_X.replace(
            '["**/x/**"]', '["**/Dockerfile*", "**/x/**"]')))[0].patterns
        self.assertEqual(init.concrete_for("services/api/Dockerfile", pats),
                         "services/api/Dockerfile")
        self.assertEqual(init.concrete_for("src/x/a.py", pats), "src/x/**")
        self.assertEqual(init.concrete_for("src/x/a.py", pats, exclude=()), "src/x/**")

    def test_existing_forms_unchanged(self):
        pats = fragments.load(self.plugin(fragment=FRAGMENT_X.replace(
            '["**/x/**"]', '["**/Dockerfile*", "**/x/**"]')))[0].patterns
        self.assertEqual(init.concrete_for("services/api/Dockerfile", pats),
                         "services/api/Dockerfile")
        self.assertEqual(init.concrete_for("Dockerfile.prod", pats), "/Dockerfile.prod")
        self.assertEqual(init.concrete_for("src/x/a.py", pats), "src/x/**")
        self.assertEqual(init.concrete_for("src/x/a.py", pats, exclude=()), "src/x/**")
        self.assertIsNone(init.concrete_for("src/y/a.py", pats))

    def ext_patterns(self, patterns):
        return fragments.load(self.plugin(fragment=FRAGMENT_X.replace(
            '["**/x/**"]', json.dumps(patterns))))[0].patterns

    def test_concrete_for_ext(self):
        pats = self.ext_patterns(["**/components/**", "**/*.tsx"])
        self.assertEqual(init.concrete_for("src/main.tsx", pats), "**/*.tsx")
        self.assertEqual(init.concrete_for("src/components/a.tsx", pats), "src/components/**")
        self.assertIsNone(init.concrete_for("src/Foo.TSX", pats))
        self.assertIsNone(init.concrete_for(".github/tollgate/x.tsx", pats))
        self.assertIsNone(init.concrete_for("docs/a.md", self.ext_patterns(["**/*.md"])))
        self.assertIsNone(init.concrete_for("supabase/x.tsx", pats, exclude=("supabase/",)))

    def test_ext_proposed_once(self):
        paths = self.paths_of(["**/*.tsx"], ["src/a.tsx", "app/b/c.tsx", "web/d.tsx"])
        self.assertEqual(paths, ["**/*.tsx"])

    def test_ext_not_proposed_when_folder_covers_all(self):
        paths = self.paths_of(["**/components/**", "**/*.tsx"],
                              ["src/components/a.tsx", "src/components/b/c.tsx"])
        self.assertEqual(paths, ["src/components/**"])

    def test_ext_in_drift(self):
        toml = FRAGMENT_X.replace('["**/x/**"]', '["**/components/**", "**/*.css"]')
        current = BASE_TOML + DECLARED_X.replace("src/x/**", "src/components/**")
        got = self.blocks(["src/components/a.tsx", "src/main.css"], current=current,
                          root=self.plugin(fragment=toml))
        self.assertIn('profilo x: [profiles.x] paths: aggiungi "**/*.css" (1 file)', got.lines)

    def test_content_found_file_covered_by_ext(self):
        toml = FRAGMENT_X.replace('["**/x/**"]', '["**/*.tsx"]') \
            + '[detect]\ncontent = ["MARK"]\n'
        got = self.blocks(["src/a.tsx", "src/b.ts"], root=self.plugin(fragment=toml),
                          detected={"x": ["src/a.tsx", "src/b.ts"]})
        self.assertEqual(self.profile(got)["paths"], ["**/*.tsx", "src/b.ts"])

    def test_exclude_multi_segment_prefix(self):
        toml = FRAGMENT_X.replace('["**/x/**"]', '["**/*.tsx"]') \
            + '[detect]\nexclude = ["apps/api/"]\n'
        pats = fragments.load(self.plugin(fragment=toml))[0]
        self.assertIsNone(init.concrete_for("apps/api/x.tsx", pats.patterns, pats.exclude))
        self.assertEqual(init.concrete_for("apps/web/y.tsx", pats.patterns, pats.exclude),
                         "**/*.tsx")
        got = self.blocks(["apps/api/x.tsx"], root=self.plugin(fragment=toml))
        self.assertEqual(got.text, "")
        got = self.blocks(["apps/api/x.tsx", "apps/web/y.tsx"], root=self.plugin(fragment=toml))
        # `exclude` decide solo se il pattern si propone; a runtime `**/*.tsx` copre anche
        # `apps/api/` (decisione 2), e l'elenco dei file accesi lo mostra.
        self.assertEqual(self.profile(got)["paths"], ["**/*.tsx"])

    def test_concrete_for_with_exclude(self):
        pats = fragments.load(self.plugin(fragment=FRAGMENT_X.replace(
            '["**/x/**"]', '["**/handlers/**"]')))[0].patterns
        path = "supabase/functions/a/handlers/h.ts"
        self.assertEqual(init.concrete_for(path, pats), "supabase/functions/a/handlers/**")
        self.assertIsNone(init.concrete_for(path, pats, exclude=("supabase/",)))

    EXCL = FRAGMENT_X.replace('["**/x/**"]', '["**/handlers/**", "server/**"]') \
        + '[detect]\ncontent = ["MARK"]\nexclude = ["supabase/"]\n'

    def test_exclude_skips_paths_and_detect(self):
        files = ["supabase/functions/a/handlers/h.ts", "supabase/functions/b/index.ts",
                 "src/handlers/h.ts", "server/app.py"]
        got = self.blocks(files, root=self.plugin(fragment=self.EXCL),
                          detected={"x": ["supabase/functions/b/index.ts", "src/other.py"]})
        paths = self.profile(got)["paths"]
        self.assertEqual(paths, ["/server/**", "src/handlers/**", "src/other.py"])
        self.assertIn("3 file", "\n".join(got.lines))
        self.assertNotIn("supabase", got.text)

    def test_exclude_only_for_its_fragment(self):
        root = self.plugin(fragment=self.EXCL)
        (root / "templates" / "profiles" / "y.toml").write_text(
            '[profile]\npaths = ["**/handlers/**"]\n', encoding="utf-8")
        (root / "skills" / "rules-y").mkdir()
        (root / "skills" / "rules-y" / "SKILL.md").write_text(
            SKILL_X.replace("rules-x", "rules-y").replace("R-X-", "R-Y-"), encoding="utf-8")
        got = self.blocks(["supabase/functions/a/handlers/h.ts"], root=root)
        self.assertEqual(tomllib.loads(BASE_TOML + got.text)["profiles"]["y"]["paths"],
                         ["supabase/functions/a/handlers/**"])
        self.assertNotIn("profiles.x]", got.text)

    def test_exclude_respected_in_drift(self):
        root = self.plugin(fragment=self.EXCL)
        current = BASE_TOML + DECLARED_X
        got = self.blocks(["src/x/a.py", "supabase/functions/a/handlers/h.ts",
                           "supabase/functions/b/index.ts"], current=current, root=root,
                          detected={"x": ["supabase/functions/b/index.ts"]})
        self.assertFalse([l for l in got.lines if "paths: aggiungi" in l], got.lines)
        got = self.blocks(["src/handlers/h.ts"], current=current, root=root)
        self.assertTrue([l for l in got.lines if "paths: aggiungi" in l], got.lines)

    def two_profiles(self):
        """Il frammento `x` (`**/handlers/**`) e un frammento `y` (`**/ai/**`, con un marcatore)."""
        root = self.plugin(fragment=FRAGMENT_X.replace('["**/x/**"]', '["**/handlers/**"]'))
        (root / "templates" / "profiles" / "y.toml").write_text(
            '[profile]\npaths = ["**/ai/**"]\n[detect]\ncontent = ["import y_sdk"]\n',
            encoding="utf-8")
        (root / "skills" / "rules-y").mkdir()
        (root / "skills" / "rules-y" / "SKILL.md").write_text(
            SKILL_X.replace("rules-x", "rules-y").replace("R-X-", "R-Y-"), encoding="utf-8")
        return root

    def test_path_only_light_skipped_when_content_goes_to_another_profile(self):
        """I-1: `ai/handlers/tool.py` col marcatore di `y` resta a `y`, `x` non lo prende."""
        root = self.two_profiles()
        got = self.blocks(["ai/handlers/tool.py"], root=root,
                          detected={"y": ["ai/handlers/tool.py"]})
        self.assertNotIn("profiles.x]", got.text)
        self.assertEqual(tomllib.loads(BASE_TOML + got.text)["profiles"]["y"]["paths"],
                         ["/ai/**"])
        self.assertTrue([l for l in got.lines if "profilo x" in l and "nessun file" in l],
                        got.lines)

    def test_path_only_light_kept_without_the_marker(self):
        root = self.two_profiles()
        got = self.blocks(["ai/handlers/tool.py"], root=root)
        self.assertEqual(self.profile(got)["paths"], ["ai/handlers/**"])

    def test_file_found_by_content_in_both_profiles_stays_in_both(self):
        root = self.two_profiles()
        got = self.blocks(["ai/handlers/tool.py"], root=root,
                          detected={"x": ["ai/handlers/tool.py"], "y": ["ai/handlers/tool.py"]})
        self.assertEqual(self.profile(got)["paths"], ["ai/handlers/**"])

    def test_path_only_light_skipped_in_drift_too(self):
        root = self.two_profiles()
        got = self.blocks(["ai/handlers/tool.py"], current=BASE_TOML + DECLARED_X, root=root,
                          detected={"y": ["ai/handlers/tool.py"]})
        self.assertFalse([l for l in got.lines if "profiles.x" in l and "paths: aggiungi" in l],
                         got.lines)

    def test_real_content_match_of_ai_keeps_nested_routes_out_of_backend(self):
        """I-1 coi frammenti veri: un file in `ai/routes/` con un marcatore vero di `ai`
        non dà `src/ai/routes/**` a `backend`."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "templates" / "profiles").mkdir(parents=True)
        for fr in fragments.load(ROOT):
            shutil.copy(fr.source, root / "templates" / "profiles" / fr.source.name)
            skill = root / "skills" / f"rules-{fr.area}"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\napproved: 2026-11-01\n---\nR-{fr.area.upper()}-01 [blocca] x\n",
                encoding="utf-8")
        path = "src/ai/routes/chat.ts"
        got = init.profile_blocks({path: 10}, DEFAULT_TOML, root, detected={"ai": [path]})
        profiles = tomllib.loads(DEFAULT_TOML + got.text)["profiles"]
        self.assertEqual(profiles["ai"]["paths"], ["src/ai/**"])
        self.assertNotIn("backend", profiles)
        plain = init.profile_blocks({path: 10}, DEFAULT_TOML, root)
        self.assertIn("src/ai/routes/**",
                      tomllib.loads(DEFAULT_TOML + plain.text)["profiles"]["backend"]["paths"])

    def test_name_pattern_literal_is_exact_path(self):
        self.assertEqual(self.paths_of(["**/vercel.json"], ["vercel.json", "apps/web/vercel.json"]),
                         ["/vercel.json", "apps/web/vercel.json"])

    def test_name_pattern_dir_escaped(self):
        paths = self.paths_of(["**/vercel.json"], ["app/[id]/vercel.json"])
        self.assertEqual(paths, ["app/\\[id\\]/vercel.json"])
        self.assertTrue(globs.match(paths[0], "app/[id]/vercel.json"))

    def test_name_pattern_matches_files_not_folders(self):
        pat = ["**/Dockerfile*"]
        self.assertIsNone(self.paths_of(pat, ["docker/Dockerfiles/base.py",
                                              "docker/Dockerfiles/README.md"]))
        self.assertEqual(self.paths_of(pat, ["Dockerfiles/base/Dockerfile",
                                             "Dockerfiles/base/a.py"]),
                         ["Dockerfiles/base/Dockerfile"])

    def test_root_folder_pattern_only_root(self):
        self.assertEqual(self.paths_of(["infra/**"], ["infra/deploy.sh", "src/infra/db.py"]),
                         ["/infra/**"])
        self.assertIsNone(self.paths_of(["infra/**"], ["src/infra/db.py"]))

    def test_name_covered_by_folder_not_repeated(self):
        self.assertEqual(self.paths_of(["infra/**", "**/Dockerfile*"],
                                       ["infra/Dockerfile", "infra/a.sh"]), ["/infra/**"])

    def test_leftmost_folder_wins(self):
        self.assertEqual(self.paths_of(["infra/**", "**/x/**"], ["infra/a/x/b.py"]),
                         ["/infra/**"])
        self.assertEqual(self.paths_of(["**/x/**"], ["src/x/lib/x/a.py"]), ["src/x/**"])

    def test_name_pattern_skips_excluded_prefixes(self):
        files = [".github/tollgate/Dockerfile", ".github/actions/build/Dockerfile",
                 ".github/workflows/vercel.json",
                 "docs/superpowers/tollgate-init/files/vercel.json", ".claude/x/vercel.json"]
        self.assertIsNone(self.paths_of(["**/Dockerfile*", "**/vercel.json"], files))

    def test_doc_files_do_not_light_folders(self):
        docs = ["docs/x/guida.md", ".github/x/a.agent.md"]
        self.assertIsNone(self.paths_of(["**/x/**"], docs))
        self.assertEqual(self.paths_of(["**/x/**"], [*docs, "src/x/a.py"]), ["src/x/**"])
        self.assertIsNone(self.paths_of(["**/Dockerfile*"], ["docs/Dockerfile-note.md"]))
        self.assertEqual(self.paths_of(["**/README.md"], ["README.md"]), ["/README.md"])

    def test_doc_extension_case_insensitive(self):
        self.assertIsNone(self.paths_of(["**/x/**"], ["docs/x/README.MD"]))

    def test_concrete_for_none_without_a_form(self):
        pats = fragments.parse_pattern
        self.assertIsNone(init.concrete_for("src/a.py", [pats("**/x/**")]))
        self.assertEqual(init.concrete_for("src/x/a.py", [pats("**/x/**")]), "src/x/**")

    def test_concrete_name_path_wins_over_declared_folder(self):
        current = BASE_TOML + '[profiles.web]\npaths = ["web/**"]\n'
        root = self.plugin(fragment=FRAGMENT_X.replace('["**/x/**"]',
                                                       '["**/vercel.json", "**/Dockerfile*"]'))
        got = self.blocks(["web/vercel.json", "web/Dockerfile"], current, root=root)
        for f in ("web/vercel.json", "web/Dockerfile"):
            line = next(l for l in got.lines if f in l and "«web»" in l)
            self.assertIn("vince x", line)

    def test_overlap_between_two_new_profiles_reported(self):
        root = self.plugin()
        (root / "templates" / "profiles" / "y.toml").write_text(
            FRAGMENT_X.replace("**/x/**", "**/y/**").replace("-x", "-y"), encoding="utf-8")
        (root / "skills" / "rules-y").mkdir()
        (root / "skills" / "rules-y" / "SKILL.md").write_text(
            SKILL_X.replace("rules-x", "rules-y").replace("R-X-", "R-Y-"), encoding="utf-8")
        # `src/x/y/a.py` accende x e y: la riga di y nomina x; vince y (3 segmenti contro 2).
        got = self.blocks(["src/x/y/a.py", "lib/y/b.py"], root=root)
        tail = tomllib.loads(BASE_TOML + got.text)["profiles"]
        self.assertEqual(tail["x"]["paths"], ["src/x/**"])
        self.assertEqual(tail["y"]["paths"], ["lib/y/**", "src/x/y/**"])
        line = next(l for l in got.lines if "«x»" in l)
        self.assertIn("profilo y:", line)
        self.assertIn("src/x/y/a.py", line)
        self.assertIn("vince y", line)

    def test_declared_profile_new_name_file_reported(self):
        current = BASE_TOML + '[profiles.x]\npaths = ["/vercel.json"]\n'
        root = self.plugin(fragment=FRAGMENT_X.replace('["**/x/**"]', '["**/vercel.json"]'))
        got = self.blocks(["vercel.json", "apps/web/vercel.json"], current, root=root)
        self.assertTrue(any('aggiungi "apps/web/vercel.json" (1 file)' in l for l in got.lines),
                        got.lines)

    def test_declared_profile_negation_respected_for_names(self):
        current = BASE_TOML + '[profiles.x]\npaths = ["/vercel.json", "!apps/legacy/vercel.json"]\n'
        root = self.plugin(fragment=FRAGMENT_X.replace('["**/x/**"]', '["**/vercel.json"]'))
        got = self.blocks(["vercel.json", "apps/legacy/vercel.json"], current, root=root)
        self.assertFalse([l for l in got.lines if "legacy" in l], got.lines)

    def test_real_trees_light_no_profile(self):
        """I frammenti veri, con una skill finta approvata ciascuno, non accendono nessun profilo
        sull'albero che i test di init spingono né su quello installato (`bin/` copiato in
        `.github/tollgate/`)."""
        real = fragments.load(ROOT)
        if not real:
            self.skipTest("templates/profiles/ non ha ancora frammenti: il test si attiva "
                          "quando ce n'è uno")
        root = _real_fragments_root(self)
        installed = install.files(ROOT, default_branch="main", services={})
        cli_pushed = {*DEFAULT_FILES, *JUNIT_FILES, *GATE_FILES, ".github/tollgate/VERSION",
                      "package.json", ".github/workflows/ci.yml", "tollgate.toml"}
        trees = {"push": {*DEFAULT_FILES, "tollgate.toml"}, "file spinti dalla CLI": cli_pushed,
                 "installato": set(installed),
                 "installato + proposta": {*installed, *(f"{FOLDER}/files/{p}" for p in installed)}}
        for name, paths in trees.items():
            with self.subTest(name):
                got = init.profile_blocks({p: 1 for p in paths}, DEFAULT_TOML, root)
                self.assertEqual(got.text, "")
                self.assertFalse([l for l in got.lines if "proposto con" in l], got.lines)


class FrontendPrecedenceTest(unittest.TestCase):
    """La tabella delle precedenze di `frontend` (B6, decisione 4), con i frammenti veri: per ogni
    caso i `paths` che `init` propone per ogni profilo («Proposta»; un profilo non proposto non ha
    un blocco) e il profilo che `vertical_for` dà a ogni file dopo aver messo i blocchi proposti in
    un `tollgate.toml` («Runtime»). `detected` è ciò che il rilevamento per contenuto
    trova: lo dà il test, senza i file sotto un `exclude` (come farebbe `detect_files`)."""

    def check(self, files, proposal, runtime=None, detected=None):
        root = _real_fragments_root(self)
        got = init.profile_blocks({f: 10 for f in files}, DEFAULT_TOML, root, detected=detected)
        declared = tomllib.loads(DEFAULT_TOML + got.text).get("profiles", {})
        self.assertEqual({a: sorted(p["paths"]) for a, p in declared.items()},
                         {a: sorted(p) for a, p in proposal.items()}, "Proposta")
        if runtime is not None:
            got_runtime = {f: profiles.vertical_for(f, declared) for f in runtime}
            self.assertEqual(got_runtime, runtime, "Runtime")

    def test_real_precedence_p1(self):
        self.check(["src/components/Button.tsx"], {"frontend": ["src/components/**"]},
                   {"src/components/Button.tsx": "frontend"})

    def test_real_precedence_p2(self):
        self.check(["server/app.py", "server/components/Mail.tsx"], {"backend": ["/server/**"]},
                   {"server/app.py": "backend", "server/components/Mail.tsx": "backend"})

    def test_real_precedence_p3(self):
        self.check(["server/app.tsx", "src/main.tsx"],
                   {"backend": ["/server/**"], "frontend": ["**/*.tsx"]},
                   {"server/app.tsx": "backend", "src/main.tsx": "frontend"})

    def test_real_precedence_p4(self):
        self.check(["src/ai/agent.py", "src/ai/components/Chat.tsx"],
                   {"ai": ["src/ai/**"], "frontend": ["src/ai/components/**"]},
                   {"src/ai/components/Chat.tsx": "frontend"})

    def test_real_precedence_p5(self):
        self.check(["src/ai/agent.py", "src/ai/components/Chat.tsx"], {"ai": ["src/ai/**"]},
                   {"src/ai/components/Chat.tsx": "ai"},
                   detected={"ai": ["src/ai/components/Chat.tsx"]})

    def test_real_precedence_p6(self):
        self.check(["src/ai/agent.py", "src/ai/components/Chat.tsx",
                    "src/ai/components/Button.tsx"],
                   {"ai": ["src/ai/**"], "frontend": ["src/ai/components/**"]},
                   {"src/ai/components/Chat.tsx": "frontend",
                    "src/ai/components/Button.tsx": "frontend"},
                   detected={"ai": ["src/ai/components/Chat.tsx"]})

    def test_real_precedence_p7(self):
        self.check(["api/og.tsx"], {"backend": ["/api/**"]}, {"api/og.tsx": "backend"})

    def test_real_precedence_p8(self):
        self.check(["src/app/api/og/route.tsx", "src/app/page.tsx"],
                   {"backend": ["src/app/api/og/route.tsx"], "frontend": ["**/*.tsx"]},
                   {"src/app/api/og/route.tsx": "backend", "src/app/page.tsx": "frontend"},
                   detected={"backend": ["src/app/api/og/route.tsx"]})

    def test_real_precedence_p9(self):
        files = ["src/routes/index.tsx", "src/routes/about.tsx"]
        self.check(files, {"frontend": ["**/*.tsx"]}, {f: "frontend" for f in files},
                   detected={"frontend": files})

    def test_real_precedence_p10(self):
        files = ["src/routes/index.tsx", "src/routes/about.tsx", "src/routes/utils.ts"]
        self.check(files, {"backend": ["src/routes/**"], "frontend": ["**/*.tsx"]},
                   {f: "backend" for f in files}, detected={"frontend": files[:2]})

    def test_real_precedence_p11(self):
        self.check(["src/services/api.ts", "src/services/Widget.tsx"],
                   {"frontend": ["**/*.tsx"]},
                   {"src/services/api.ts": None, "src/services/Widget.tsx": "frontend"})

    def test_real_precedence_p12(self):
        self.check(["web/vercel.json", "web/index.css"],
                   {"infra": ["web/vercel.json"], "frontend": ["/web/**"]},
                   {"web/vercel.json": "infra", "web/index.css": "frontend"})

    def test_real_precedence_p13(self):
        self.check(["prompts/Card.tsx"], {"ai": ["/prompts/**"], "frontend": ["**/*.tsx"]},
                   {"prompts/Card.tsx": "ai"})

    def test_real_precedence_p14(self):
        self.check(["supabase/functions/og/index.tsx", "src/main.tsx"],
                   {"frontend": ["**/*.tsx"]},
                   {"supabase/functions/og/index.tsx": "frontend", "src/main.tsx": "frontend"})

    def test_real_precedence_p15(self):
        files = ["src/routes/+page.svelte", "src/routes/+page.server.ts"]
        self.check(files, {"backend": ["src/routes/**"], "frontend": ["**/*.svelte"]},
                   {f: "backend" for f in files})

    def test_real_precedence_p16(self):
        self.check([".github/tollgate/x.css", ".claude/x.tsx",
                    "docs/superpowers/tollgate-init/files/x.tsx"], {})

    def test_real_precedence_p17(self):
        self.check(["docs/components/guida.md", "src/components/README.md"], {})

    def test_real_precedence_p18(self):
        self.check(["src/Foo.TSX"], {}, {"src/Foo.TSX": None})

    def test_real_precedence_p19(self):
        self.check(["app/routes/home.tsx", "app/routes.ts"], {"frontend": ["**/*.tsx"]},
                   {"app/routes/home.tsx": "frontend"},
                   detected={"frontend": ["app/routes/home.tsx"]})

    def test_real_precedence_p20(self):
        self.check(["src/ai/agent.py", "src/ai/components/retriever.py"],
                   {"ai": ["src/ai/**"], "frontend": ["src/ai/components/**"]},
                   {"src/ai/components/retriever.py": "frontend"})

    def test_real_precedence_p21(self):
        files = ["infra/main.ts", "infra/components/vpc.ts"]
        self.check(files, {"infra": ["/infra/**"]}, {f: "infra" for f in files})

    def test_real_precedence_p22(self):
        """`server/entry.ts` sta anche nel `detected` di `frontend`: è `exclude` a tenerlo fuori,
        come fa `profile_blocks` con `skip`."""
        files = ["server/app.py", "server/entry.ts"]
        self.check(files, {"backend": ["/server/**"]}, {f: "backend" for f in files},
                   detected={"frontend": ["server/entry.ts"]})

    def test_real_precedence_p23(self):
        files = ["app/routes/home.tsx", "app/routes/api.users.ts"]
        self.check(files, {"frontend": ["**/*.tsx", "app/routes/api.users.ts"]},
                   {f: "frontend" for f in files}, detected={"frontend": files})

    def test_real_precedence_p24(self):
        self.check(["pages/api/hello.tsx", "src/main.tsx"], {"frontend": ["**/*.tsx"]},
                   {"pages/api/hello.tsx": "frontend"})

    def test_real_precedence_p25(self):
        self.check(["src/ai/agent.py", "src/ai/routes/chat.tsx"],
                   {"ai": ["src/ai/**"], "frontend": ["**/*.tsx"]},
                   {"src/ai/routes/chat.tsx": "ai"},
                   detected={"frontend": ["src/ai/routes/chat.tsx"]})

    def test_real_precedence_p26(self):
        self.check(["src/ai/agent.py", "src/ai/routes/chat.ts"],
                   {"ai": ["src/ai/**"], "frontend": ["src/ai/routes/chat.ts"]},
                   {"src/ai/routes/chat.ts": "frontend"},
                   detected={"frontend": ["src/ai/routes/chat.ts"]})

    def test_real_precedence_p27(self):
        self.check(["src/ai/agent.py", "src/ai/routes/chat.tsx"],
                   {"ai": ["src/ai/**"], "backend": ["src/ai/routes/**"],
                    "frontend": ["**/*.tsx"]},
                   {"src/ai/routes/chat.tsx": "backend"})

    def test_real_precedence_p28(self):
        self.check(["src/components/Button.tsx", "src/components/ai/ChatBubble.tsx"],
                   {"ai": ["src/components/ai/**"], "frontend": ["src/components/**"]},
                   {"src/components/ai/ChatBubble.tsx": "ai"})

    def test_real_precedence_p29(self):
        self.check(["src/components/Button.tsx", "src/components/routes/Nav.tsx"],
                   {"backend": ["src/components/routes/**"], "frontend": ["src/components/**"]},
                   {"src/components/routes/Nav.tsx": "backend"})

    def test_real_precedence_p30(self):
        self.check(["src/components/Button.tsx", "src/components/Chat.tsx"],
                   {"ai": ["src/components/Chat.tsx"], "frontend": ["src/components/**"]},
                   {"src/components/Chat.tsx": "ai", "src/components/Button.tsx": "frontend"},
                   detected={"ai": ["src/components/Chat.tsx"]})

    def test_real_precedence_p31(self):
        self.check(["src/app/page.tsx", "src/app/agents/page.tsx"],
                   {"ai": ["src/app/agents/**"], "frontend": ["**/*.tsx"]},
                   {"src/app/agents/page.tsx": "ai"})

    def test_real_precedence_p32(self):
        files = ["src/routes/index.tsx", "src/routes/index.test.tsx"]
        self.check(files, {"backend": ["src/routes/**"], "frontend": ["**/*.tsx"]},
                   {f: "backend" for f in files}, detected={"frontend": files[:1]})

    def test_real_precedence_p33(self):
        files = ["src/routes/index.tsx", "src/routes/index.module.css"]
        self.check(files, {"backend": ["src/routes/**"], "frontend": ["**/*.css", "**/*.tsx"]},
                   {f: "backend" for f in files}, detected={"frontend": files[:1]})

    def test_real_precedence_p34(self):
        self.check(["src/routes/index.tsx", "src/routes/api.ts"],
                   {"backend": ["src/routes/**"],
                    "frontend": ["**/*.tsx", "src/routes/api.ts"]},
                   {"src/routes/api.ts": "frontend", "src/routes/index.tsx": "backend"},
                   detected={"frontend": ["src/routes/index.tsx", "src/routes/api.ts"],
                             "backend": ["src/routes/api.ts"]})

    def test_real_precedence_p35(self):
        self.check(["web/index.html", "web/functions/api.ts"], {"frontend": ["/web/**"]},
                   {"web/functions/api.ts": "frontend"})

    def test_real_precedence_p36(self):
        files = ["src/main.tsx", "src/a.css", ".claude/skills/x/template.tsx",
                 ".github/tollgate/x.css", ".github/actions/a/index.css",
                 "docs/superpowers/tollgate-init/files/x.tsx"]
        self.check(files, {"frontend": ["**/*.css", "**/*.tsx"]}, {f: "frontend" for f in files})

    def test_real_precedence_p37(self):
        """A parità di segmenti vince il primo blocco dichiarato; in una sola corsa `init` li scrive
        in ordine alfabetico (`backend` prima di `frontend`), con `--update` li aggiunge in coda."""
        path = "src/lib/server.ts"
        self.check([path], {"backend": [path], "frontend": [path]}, {path: "backend"},
                   detected={"frontend": [path], "backend": [path]})

    def test_real_precedence_p38(self):
        files = ["src/components/Form/Form.tsx", "src/components/Form/handlers/onSubmit.ts"]
        self.check(files, {"backend": ["src/components/Form/handlers/**"],
                           "frontend": ["src/components/**"]},
                   {"src/components/Form/Form.tsx": "frontend",
                    "src/components/Form/handlers/onSubmit.ts": "backend"})

    def test_real_precedence_p39(self):
        """Con il blocco `backend` di B5 già dichiarato (`src/routes/**`), `init --update` propone
        `frontend` ma non toglie la cartella a `backend`: a runtime vince `backend`."""
        files = ["src/routes/index.tsx", "src/routes/about.tsx"]
        root = _real_fragments_root(self)
        current = DEFAULT_TOML + '[profiles.backend]\npaths = ["src/routes/**"]\n'
        got = init.profile_blocks({f: 10 for f in files}, current, root,
                                  detected={"frontend": files})
        declared = tomllib.loads(current + got.text)["profiles"]
        self.assertEqual(declared["frontend"]["paths"], ["**/*.tsx"])
        self.assertEqual(declared["backend"]["paths"], ["src/routes/**"])
        self.assertFalse(any("src/routes/**" in line and "togli" in line for line in got.lines),
                         "init non deve proporre di togliere la cartella a backend")
        self.assertEqual({f: profiles.vertical_for(f, declared) for f in files},
                         {f: "backend" for f in files}, "Runtime")

    def test_real_frontend_exclude_several_prefixes(self):
        """Sei prefissi di `exclude` (quelli di `backend`, di `infra` e `supabase/`) tengono fuori
        ogni file: `frontend` non è proposto; con un `.tsx` fuori da essi, sì."""
        files = ["server/components/a.tsx", "infra/components/b.ts", "api/c.tsx",
                 "functions/d.tsx", "backend/e.tsx", "supabase/functions/f/index.tsx"]
        root = _real_fragments_root(self)
        got = init.profile_blocks({f: 10 for f in files}, DEFAULT_TOML, root)
        self.assertNotIn("frontend", tomllib.loads(DEFAULT_TOML + got.text).get("profiles", {}))
        got = init.profile_blocks({f: 10 for f in [*files, "src/main.tsx"]}, DEFAULT_TOML, root)
        proposed = tomllib.loads(DEFAULT_TOML + got.text)["profiles"]["frontend"]
        self.assertEqual(proposed["paths"], ["**/*.tsx"])


class ProfilesProposeTest(PluginMixin, InitCase):
    def propose(self, root, *, update=False):
        with mock.patch.dict(os.environ, self.fl.env()):
            return init.propose(self.fl.ts.state, self.fl.main, update=update,
                                merges_per_month=10, services={}, profiles_root=root)

    def test_update_appends_and_keeps_user_text(self):
        text = "# la mia nota\n" + BASE_TOML.replace('mode = "protected"',
                                                      'mode = "protected"   # misurata')
        self.make(DETECT, toml=text)
        self.push({"src/x/a.py": "x\n"})
        got = self.propose(self.plugin(), update=True)
        self.assertEqual(got.code, init.OK, got.lines)
        expected = text.replace('"protected"   #', '"detect"   #')
        self.assertTrue(self.toml().startswith(expected), self.toml())
        tail = self.toml()[len(expected):]
        self.assertIn("# profilo x da templates/profiles/x.toml", tail)
        self.assertEqual(tomllib.loads(self.toml())["profiles"]["x"]["paths"], ["src/x/**"])
        self.assertTrue(any("src/x/a.py" in l for l in got.lines), got.lines)

    def test_update_twice_no_duplicate(self):
        self.make(UNSET, toml=BASE_TOML)
        self.push({"src/x/a.py": "x\n"})
        root = self.plugin()
        self.assertEqual(self.propose(root).code, init.OK)
        self.assertEqual(self.toml().count("[profiles.x]"), 1)
        self.push({"tollgate.toml": self.toml()})
        got = self.propose(root)
        self.assertEqual(got.code, init.OK, got.lines)
        self.assertEqual(self.toml().count("[profiles.x]"), 1)
        self.assertFalse([l for l in got.lines if l.startswith("profilo x")], got.lines)

    def test_drift_lines_survive_nothing_to_update(self):
        self.make(UNSET)
        tree = self.install_tree()
        tree["tollgate.toml"] = BASE_TOML + DECLARED_X.replace('"R-X-01", "R-X-02"', '"R-X-01"')
        tree["src/x/a.py"] = "x\n"
        tree["lib/x/b.py"] = "x\n"
        self.push(tree)
        got = self.propose(self.plugin(), update=True)
        text = "\n".join(got.lines)
        self.assertIn("nulla da aggiornare", text)
        self.assertIn("R-X-02", text)
        self.assertIn('"lib/x/**"', text)
        self.assertFalse((self.folder / "README.md").exists())

    def test_readme_lists_proposed_profiles(self):
        self.make(UNSET)
        self.push({"src/x/a.py": "x\n"})
        self.assertEqual(self.propose(self.plugin()).code, init.OK)
        readme = self.readme()
        self.assertIn("## Profili proposti", readme)
        self.assertIn("src/x/**", readme)
        self.assertIn("# profilo x da templates/profiles/x.toml", readme)
        self.assertIn("cancella", readme)

    def test_no_approved_profile_no_section(self):
        self.make(UNSET)
        self.push({"src/x/a.py": "x\n"})
        self.assertEqual(self.propose(self.plugin(approved=False)).code, init.OK)
        self.assertNotIn("Profili proposti", self.readme())
        self.assertNotIn("[profiles", self.toml())

    def test_bad_fragment_refuses_init(self):
        self.make(UNSET)
        root = self.plugin(fragment="[profile\nbroken")
        got = self.propose(root)
        self.assertNotEqual(got.code, init.OK)
        self.assertIn("x.toml", "\n".join(got.lines))
        self.assertFalse(self.folder.exists())

    def test_git_error_leaves_the_rest_of_the_proposal(self):
        self.make(UNSET)
        boom = core_git.GitError("git ls-tree: boom")
        for update in (False, True):
            with self.subTest(update=update), mock.patch(
                    "tollgate_core.git.tree_sizes_at", side_effect=boom):
                if update:
                    self.push({"tollgate.toml": BASE_TOML})
                got = self.propose(self.plugin(), update=update)
                self.assertEqual(got.code, init.OK, got.lines)
                self.assertTrue(any("profili non valutati" in l and "boom" in l
                                    for l in got.lines), got.lines)
                self.assertTrue((self.folder / "README.md").exists())
                self.assertIn("profili non valutati", self.readme())
                self.assertFalse(update and (self.folder / "files" / "tollgate.toml").exists())
                if not update:
                    self.assertNotIn("[profiles", self.toml())

    def test_real_default_root_is_the_plugin(self):
        self.assertEqual(init.PLUGIN_ROOT, ROOT)
        self.make(UNSET)
        seen = []
        real_load = fragments.load
        with mock.patch.dict(os.environ, self.fl.env()), mock.patch(
                "tollgate_core.fragments.load", side_effect=lambda r: (seen.append(r),
                                                                       real_load(r))[1]):
            got = init.propose(self.fl.ts.state, self.fl.main, update=False,
                               merges_per_month=10, services={})
        self.assertEqual(got.code, init.OK, got.lines)
        self.assertEqual({Path(r) for r in seen}, {ROOT})

    def test_blocks_failing_validation_are_dropped(self):
        self.make(UNSET)
        self.push({"src/x/a.py": "x\n"})
        bad = init.ProfileProposal("\n[profiles.x]\nrules = 3\n", ["profilo x: finto"], "r")
        with mock.patch("tollgate_flow.init.profile_blocks", return_value=bad):
            got = self.propose(self.plugin())
        self.assertEqual(got.code, init.OK, got.lines)
        self.assertTrue(any("profili non valutati" in l for l in got.lines), got.lines)
        self.assertNotIn("profilo x: finto", got.lines)
        self.assertNotIn("[profiles", self.toml())
        self.assertIn("profili non valutati", self.readme())

    def test_empty_tree_is_not_a_verdict_on_the_repo(self):
        self.make(UNSET)
        with mock.patch("tollgate_core.git.tree_sizes_at", return_value={}):
            got = self.propose(self.plugin())
        self.assertEqual(got.code, init.OK, got.lines)
        self.assertTrue(any("profili non valutati" in l for l in got.lines), got.lines)
        self.assertFalse(any("corrisponde ai suoi percorsi" in l for l in got.lines), got.lines)


FRAGMENT_XD = FRAGMENT_X + '[detect]\ncontent = ["import x_sdk", "npm:@x/sdk"]\n'
HIT = "import x_sdk\n"


class DetectTest(PluginMixin, InitCase):
    """Decisione 6: il codice che usa l'SDK fuori dalle cartelle tipiche, trovato per contenuto."""

    def setUp(self):
        self.make(UNSET, toml=BASE_TOML)
        self.root = self.plugin(fragment=FRAGMENT_XD)

    def detect(self, files: dict) -> list[str]:
        self.push(files)
        sizes = core_git.tree_sizes_at(self.fl.main, "origin/main")
        got = init.detect_files(self.fl.main, "origin/main", fragments.load(self.root), sizes)
        self.assertEqual(list(got), ["x"])
        return got["x"]

    def propose(self, *, update=False):
        with mock.patch.dict(os.environ, self.fl.env()):
            return init.propose(self.fl.ts.state, self.fl.main, update=update,
                                merges_per_month=10, services={}, profiles_root=self.root)

    def test_detect_adds_exact_paths(self):
        self.push({"supabase/functions/notify/index.ts":
                   'import X from "npm:@x/sdk"\n', "README.md": "x\n"})
        got = self.propose()
        self.assertEqual(got.code, init.OK, got.lines)
        paths = tomllib.loads(self.toml())["profiles"]["x"]["paths"]
        self.assertEqual(paths, ["supabase/functions/notify/index.ts"])
        self.assertTrue(any("supabase/functions/notify/index.ts" in l for l in got.lines))

    def test_detect_skips_manifests_docs_and_tests(self):
        found = self.detect({
            "package.json": '{"dependencies": {"npm:@x/sdk": "1"}}\n',
            "README.md": HIT, "tests/test_x.py": HIT, "src/x.test.ts": HIT,
            "src/x.spec.ts": HIT, "conftest.py": HIT, "pkg/__tests__/a.js": HIT,
            "pkg/b_test.go": HIT, "src/x.vue": HIT, "src/y.mts": HIT})
        self.assertEqual(found, ["src/x.vue", "src/y.mts"])

    def test_detect_skips_large_and_binary(self):
        found = self.detect({
            "src/big.py": HIT + "#" * (256 * 1024), "src/edge.py": HIT + "#" * (256 * 1024 - 13),
            "src/bin.py": b"\0" + HIT.encode(), "src/ok.py": HIT})
        self.assertEqual(found, ["src/edge.py", "src/ok.py"])

    def test_detect_skips_excluded_prefixes(self):
        found = self.detect({".claude/agents/a.py": HIT, ".github/tollgate/bin/a.py": HIT,
                             f"{FOLDER}/files/b.py": HIT, "src/ok.py": HIT})
        self.assertEqual(found, ["src/ok.py"])

    def test_detect_files_honours_exclude(self):
        self.push({"supabase/functions/n/index.ts": HIT, "src/ok.py": HIT})
        sizes = core_git.tree_sizes_at(self.fl.main, "origin/main")
        got = init.detect_files(self.fl.main, "origin/main", fragments.load(self.root), sizes)
        self.assertEqual(got["x"], ["src/ok.py", "supabase/functions/n/index.ts"])
        root = self.plugin(fragment=FRAGMENT_XD + 'exclude = ["supabase/"]\n')
        got = init.detect_files(self.fl.main, "origin/main", fragments.load(root), sizes)
        self.assertEqual(got["x"], ["src/ok.py"])

    def test_detect_odd_names(self):
        self.assertEqual(self.detect({"src/è à.py": HIT}), ["src/è à.py"])

    def test_detect_file_already_covered_not_repeated(self):
        self.push({"src/x/a.py": HIT, "edge/fn.ts": HIT})
        got = self.propose()
        self.assertEqual(got.code, init.OK, got.lines)
        paths = tomllib.loads(self.toml())["profiles"]["x"]["paths"]
        self.assertEqual(paths, ["edge/fn.ts", "src/x/**"])

    def test_declared_profile_new_detected_file_reported(self):
        self.make(UNSET, toml=BASE_TOML + DECLARED_X)
        self.push({"src/x/a.py": "x\n", "edge/fn.ts": HIT})
        got = self.propose()
        self.assertEqual(got.code, init.OK, got.lines)
        lines = [l for l in got.lines if l.startswith("profilo x")]
        self.assertEqual(len(lines), 1, got.lines)
        self.assertIn("paths: aggiungi", lines[0])
        self.assertIn('"edge/fn.ts"', lines[0])

    def test_declared_profile_negation_respected_in_both_orders(self):
        for paths in ('["!lib/x/gen/**", "lib/x/**"]', '["lib/x/**", "!lib/x/gen/**"]'):
            with self.subTest(paths=paths):
                self.make(UNSET, toml=BASE_TOML + DECLARED_X.replace('["src/x/**"]', paths))
                self.push({"lib/x/gen/a.py": HIT, "lib/x/b.py": HIT})
                got = self.propose()
                self.assertFalse([l for l in got.lines if "paths: aggiungi" in l], got.lines)

    def test_detect_timeout_warns(self):
        self.push({"src/x/a.py": "x\n", "edge/fn.ts": HIT})
        boom = core_git.GitError("git grep: timeout dopo 10 s")
        with mock.patch("tollgate_core.git.grep_files_at", side_effect=boom):
            got = self.propose()
        self.assertEqual(got.code, init.OK, got.lines)
        self.assertTrue(any("rilevamento" in l and "timeout" in l for l in got.lines), got.lines)
        self.assertIn("rilevamento", self.readme())
        self.assertEqual(tomllib.loads(self.toml())["profiles"]["x"]["paths"], ["src/x/**"])

    def test_failed_grep_of_one_fragment_does_not_stop_the_others(self):
        self.push({"src/ok.py": "import y_sdk\n"})
        sizes = core_git.tree_sizes_at(self.fl.main, "origin/main")
        root = self.plugin(fragment=FRAGMENT_XD)
        y = root / "templates" / "profiles" / "y.toml"
        y.write_text(FRAGMENT_XD.replace("import x_sdk", "import y_sdk"), encoding="utf-8")
        real = core_git.grep_files_at

        def grep(repo, ref, markers, specs):
            if "import x_sdk" in markers:
                raise core_git.GitError("git grep: timeout dopo 10 s")
            return real(repo, ref, markers, specs)

        warnings = []
        with mock.patch("tollgate_core.git.grep_files_at", side_effect=grep):
            got = init.detect_files(self.fl.main, "origin/main", fragments.load(root), sizes,
                                    warnings)
        self.assertEqual(got, {"x": [], "y": ["src/ok.py"]})
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("profilo x", warnings[0])

    def test_one_grep_per_fragment_with_markers(self):
        self.push({"src/ok.py": HIT})
        sizes = core_git.tree_sizes_at(self.fl.main, "origin/main")
        plain = self.plugin()
        with mock.patch("tollgate_core.git.grep_files_at", return_value=[]) as grep:
            init.detect_files(self.fl.main, "origin/main", fragments.load(plain), sizes)
            grep.assert_not_called()
            init.detect_files(self.fl.main, "origin/main", fragments.load(self.root), sizes)
            self.assertEqual(grep.call_count, 1)
            markers, specs = grep.call_args.args[2:]
            self.assertEqual(markers, ["import x_sdk", "npm:@x/sdk"])
            self.assertIn(":(glob)**/*.py", specs)
            self.assertNotIn(":(glob)**/*.md", specs)


if __name__ == "__main__":
    unittest.main()
