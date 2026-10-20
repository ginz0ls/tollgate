import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from tests.flowkit import PLAN, SESSION, plan_text
from tests.helpers import BIN
from tests.hookkit import DEFAULT_TOML
from tests.test_openpr import BRANCH, SOMMA, pr
from tests.test_start import StartCase, out
from tollgate_analysis import prblock, waivers
from tollgate_flow import adopt
from tollgate_core import acts, clock, git as core_git, phases, scope, sessions
from tollgate_core.paths import repo_key

L0_FILES = {"src/app.py": SOMMA}
L1_FILES = {PLAN: plan_text(), "src/app.py": SOMMA, "docs/uso.md": "uso\n"}
L2_FILES = {**L1_FILES, "src/auth/login.py": "x = 1\n"}
SPEC_DOC = "docs/superpowers/specs/s.md"
SPEC_TEXT = "spec\n"


def blob(text):
    """Lo sha git del contenuto, come lo calcola `git hash-object`."""
    return subprocess.run(["git", "hash-object", "--stdin"], input=text, capture_output=True,
                          text=True, check=True).stdout.strip()


def spec_approval(sha=None, path=SPEC_DOC):
    return (f"---\nkind: spec-approval\npath: {path}\nsha: {sha or blob(SPEC_TEXT)}\n"
            "adversarial: true\nlens: sicurezza\n---\nOK\n")


def plan_approval(sha=None, path=PLAN, spec_sha=None):
    extra = f"spec_sha: {spec_sha}\n" if spec_sha else ""
    return (f"---\nkind: plan-approval\npath: {path}\nsha: {sha or blob(plan_text())}\n"
            f"{extra}---\nOK\n")


L2_DOCS = {**L2_FILES, SPEC_DOC: SPEC_TEXT}
SPEC_FILE = "docs/superpowers/reviews/7/spec-approval.md"
PLAN_FILE = "docs/superpowers/reviews/7/plan-approval.md"


class AdoptCase(StartCase):
    def branch_lab(self, files, *, push=False, remote_only=False, worktree=True, prs=(),
                   toml=None):
        """Repo attivo con il ramo `tg/7-demo` e nessuna riga nel DB (DB perso): i `files` sono
        un commit sul ramo. `remote_only`: il ramo esiste solo su origin (altra macchina)."""
        fl = self.make(**({"toml": toml} if toml else {}))
        self.gh(fl, prs=list(prs))
        fl.git("worktree", "add", "-q", "-b", BRANCH, str(fl.wt))
        for rel, text in files.items():
            target = fl.wt / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        if files:
            fl.git("add", "-A", repo=fl.wt)
            fl.git("commit", "-qm", "lavoro", repo=fl.wt)
        if push or remote_only:
            fl.git("push", "-q", "origin", BRANCH, repo=fl.wt)
        if remote_only or not worktree:
            fl.git("worktree", "remove", str(fl.wt))
        if remote_only:
            fl.git("branch", "-D", BRANCH)
        return fl

    def act(self, fl, n=7, session=SESSION):
        return acts.record_act(fl.conn, type_="adopt", target=str(n), session=session, work=None,
                               typed_text=f"/tollgate:adopt #{n}", now=clock.now(),
                               ttl_minutes=10)

    def adopt(self, fl, *, act=True, cwd=None):
        if act:
            self.act(fl)
        return fl.cli("adopt", "7", cwd=cwd)

    def adopted(self, fl, **kw):
        r = self.adopt(fl, **kw)
        self.assertEqual(r.returncode, 0, out(r))
        (row,) = self.rows(fl)
        return row

    def act_state(self, fl):
        return fl.conn.execute("SELECT state FROM acts WHERE type = 'adopt'").fetchone()[0]


class AdoptPhaseTest(AdoptCase):
    def test_hooks_deny_on_orphan_branch_then_adopt(self):
        fl = self.branch_lab(L0_FILES)
        denied = fl.pre_edit(fl.wt / "src/app.py")
        self.assertEqual(denied.exit, 2)
        self.assertIn("/tollgate:adopt #7", denied.stderr)
        r = self.adopt(fl, cwd=fl.wt)
        self.assertEqual(r.returncode, 0, out(r))
        (row,) = self.rows(fl)
        self.assertEqual((row["issue"], row["level"], row["phase"]), (7, "L0", "execution"))
        self.assertEqual(row["branch"], BRANCH)
        self.assertEqual(Path(row["worktree"]), fl.wt.resolve())
        self.assertEqual(row["work_base_sha"], fl.lab.base)
        self.assertEqual(json.loads(row["sessions"]), [SESSION])
        self.assertTrue((fl.ts.dir / "bound" / SESSION).is_file())
        self.assertEqual(r.stdout.strip().splitlines()[-1],
                         f"prossimo passo: EnterWorktree {fl.wt.resolve()}")
        self.assertEqual(self.act_state(fl), "consumed")
        self.assertEqual(fl.events("phase_change")[-1], {"from": None, "to": "execution",
                                                         "cause": "adopt"})
        self.assertEqual(fl.pre_edit(fl.wt / "src/app.py").exit, 0)

    def test_start_refusal_then_adopt(self):
        fl = self.branch_lab(L0_FILES, remote_only=True)
        refused = self.refused(fl, "/tollgate:adopt #7")
        self.assertIn(BRANCH, out(refused))
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"], row["branch"]), ("L0", "execution", BRANCH))

    def test_l1_without_plan_goes_plan(self):
        fl = self.branch_lab({"src/app.py": SOMMA, "docs/a.md": "a\n", "docs/b.md": "b\n"})
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L1", "plan"))
        self.assertIsNone(row["plan_sha"])
        self.assertEqual(scope.paths(fl.conn, row["id"]), set())

    def test_l1_with_plan_registers_scope_and_pending_tasks(self):
        fl = self.branch_lab(L1_FILES)
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L1", "execution"))
        self.assertEqual(row["plan_path"], PLAN)
        self.assertEqual(row["plan_sha"], fl.git("rev-parse", f"{BRANCH}:{PLAN}"))
        self.assertEqual(scope.paths(fl.conn, row["id"]),
                         {"src/app.py", "tests/test_app.py", "docs/uso.md"})
        tasks = fl.conn.execute("SELECT number, state, source FROM tasks WHERE work = ? "
                                "ORDER BY number", (row["id"],)).fetchall()
        self.assertEqual([(t["number"], t["state"], t["source"]) for t in tasks],
                         [(1, "pending", "plan"), (2, "pending", "plan")])

    def test_l2_with_plan_approval_stays_execution(self):
        fl = self.branch_lab({**L2_DOCS, SPEC_FILE: spec_approval(),
                              PLAN_FILE: plan_approval(spec_sha=blob(SPEC_TEXT))})
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L2", "execution"))
        self.assertEqual(row["spec_path"], SPEC_DOC)
        self.assertEqual(row["plan_path"], PLAN)
        self.assertEqual(len(scope.paths(fl.conn, row["id"])), 3)

    def test_l2_superseded_or_mismatched_approvals_go_back(self):
        old_plan = plan_text(task2="- Create: `docs/vecchio.md`")
        cases = {
            "piano modificato dopo l'approvazione": (
                {SPEC_FILE: spec_approval(), PLAN_FILE: plan_approval(sha=blob(old_plan))},
                "plan"),
            "approvazione del piano con un altro path": (
                {SPEC_FILE: spec_approval(), PLAN_FILE: plan_approval(path="docs/altro.md")},
                "plan"),
            "spec_sha diverso dalla spec": (
                {SPEC_FILE: spec_approval(), PLAN_FILE: plan_approval(spec_sha="0" * 40)},
                "plan"),
            "spec modificata dopo l'approvazione": (
                {SPEC_FILE: spec_approval(sha=blob("spec vecchia\n")), PLAN_FILE: plan_approval()},
                "spec_audit"),
            "spec approvata ma assente": (
                {SPEC_FILE: spec_approval(path="docs/superpowers/specs/manca.md"),
                 PLAN_FILE: plan_approval()}, "spec_audit"),
        }
        for name, (files, phase) in cases.items():
            with self.subTest(name):
                fl = self.branch_lab({**L2_DOCS, **files})
                r = self.adopt(fl)
                self.assertEqual(r.returncode, 0, out(r))
                row = self.rows(fl)[-1]
                self.assertEqual((row["level"], row["phase"]), ("L2", phase))
                self.assertIsNone(row["plan_sha"])
                self.assertEqual(scope.paths(fl.conn, row["id"]), set())

    def test_l2_without_spec_approval_goes_spec_audit(self):
        fl = self.branch_lab(L2_FILES)
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L2", "spec_audit"))

    def test_pr_and_cap_lines_only_when_step_succeeded(self):
        body = prblock.render({"issue": 7, "level_cap": "L1", "level_cap_reason": "x"})
        fl = self.branch_lab(L0_FILES, push=True, prs=[pr(3, "OPEN", body=body)])
        with mock.patch.object(phases, "set_pr", side_effect=ValueError("rotto")), \
                mock.patch.object(phases, "set_level_cap",
                                  side_effect=phases.TransitionError("no")), \
                mock.patch.dict(os.environ, fl.env()):
            self.act(fl)
            sessions.note_cli_call(fl.ts.state, SESSION, str(fl.main), ["adopt", "7"],
                                   now=clock.now())
            r = adopt.adopt(fl.ts.state, fl.main, 7, argv=["adopt", "7"])
        text = "\n".join(r.lines)
        self.assertEqual(r.code, adopt.INCOMPLETE, text)
        self.assertNotIn("aperta: fase pr_open", text)
        self.assertNotIn("ripristinato dalla PR", text)
        self.assertIn("registrazione incompleta: PR", text)

    def test_approved_waivers_back_pending(self):
        wf = waivers.WaiverFile(7, BRANCH, [waivers.Waiver(
            "w-7-1", "test", "tests/test_app.py", None, ["tests.test_app::test_somma"],
            "scelta", "motivo", "costo")])
        fl = self.branch_lab({**L0_FILES, waivers.path_for(7): waivers.dumps(wf)})
        row = self.adopted(fl)
        parsed = waivers.parse((Path(row["worktree"]) / waivers.path_for(7)).read_text())
        self.assertEqual(waivers.status(parsed, approved_ids=acts.approved_waivers(
            fl.conn, row["id"]), sensitive=lambda p: False), {"w-7-1": "pending"})


class AdoptIssueTest(AdoptCase):
    def test_external_issue_author_gives_at_least_l2(self):
        fl = self.branch_lab(L0_FILES)
        self.gh(fl, issues={"7": {"number": 7, "title": "Aggiungi export CSV", "body": "b",
                                  "state": "open", "labels": [], "author_association": "NONE"}})
        r = self.adopt(fl)
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn("autore dell'issue esterno al repo", r.stdout)
        (row,) = self.rows(fl)
        self.assertEqual(row["level"], "L2")

    def test_unreadable_issue_refuses(self):
        fl = self.branch_lab(L0_FILES)
        self.gh(fl, issues={"99": {"number": 99}})
        r = self.adopt(fl)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertEqual(self.rows(fl), [])


class AdoptPrTest(AdoptCase):
    def test_open_pr_gives_pr_open_and_cap_from_block(self):
        body = prblock.render({"issue": 7, "level": "L2", "level_cap": "L1",
                               "level_cap_reason": "solo documentazione"})
        fl = self.branch_lab(L2_FILES, push=True, prs=[pr(3, "OPEN", body=body)])
        row = self.adopted(fl)
        self.assertEqual(row["phase"], "pr_open")
        self.assertEqual((row["pr_number"], row["pr_url"]),
                         (3, "https://github.com/prova/flow/pull/3"))
        self.assertEqual((row["level_cap"], row["level_cap_reason"], row["level"]),
                         ("L1", "solo documentazione", "L1"))
        self.assertEqual(json.loads(row["level_cap_paths"]), ["src/auth/login.py"])
        self.assertEqual(row["plan_path"], PLAN)
        self.assertEqual(len(scope.paths(fl.conn, row["id"])), 3)       # livello L1 dopo il tetto

    def test_fork_pr_with_same_branch_is_not_ours(self):
        body = prblock.render({"issue": 7, "level": "L2", "level_cap": "L0",
                               "level_cap_reason": "di un altro"})
        fl = self.branch_lab(L2_FILES, push=True,
                             prs=[pr(3, "OPEN", body=body, isCrossRepository=True)])
        row = self.adopted(fl)
        self.assertEqual((row["pr_number"], row["level_cap"], row["level"]), (None, None, "L2"))

    def test_invalid_cap_in_block_is_ignored_with_warning(self):
        for name, block in {"livello": {"issue": 7, "level_cap": "L9"},
                            "issue": {"issue": 8, "level_cap": "L0", "level_cap_reason": "x"}
                            }.items():
            with self.subTest(name):
                fl = self.branch_lab(L0_FILES, push=True,
                                     prs=[pr(3, "OPEN", body=prblock.render(block))])
                r = self.adopt(fl)
                self.assertEqual(r.returncode, 0, out(r))
                self.assertIn("tetto di livello non valido", r.stdout)
                self.assertIsNone(self.rows(fl)[-1]["level_cap"])

    def test_open_pr_without_block_has_no_cap(self):
        fl = self.branch_lab(L0_FILES, push=True, prs=[pr(3, "OPEN", body="solo testo")])
        row = self.adopted(fl)
        self.assertEqual((row["phase"], row["level_cap"], row["pr_number"]), ("pr_open", None, 3))

    def test_closed_pr_is_ignored_with_warning(self):
        body = prblock.render({"issue": 7, "level_cap": "L0", "level_cap_reason": "x"})
        fl = self.branch_lab(L0_FILES, push=True, prs=[pr(3, "CLOSED", body=body)])
        r = self.adopt(fl)
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn("PR #3 chiusa senza merge: ignorata, finish open-pr ne aprirà una nuova",
                      r.stdout)
        (row,) = self.rows(fl)
        self.assertEqual((row["phase"], row["pr_number"], row["level_cap"]),
                         ("execution", None, None))


class AdoptWorktreeTest(AdoptCase):
    def worktrees(self, fl):
        return core_git.worktrees(fl.main)

    def test_branch_in_existing_worktree_reused(self):
        fl = self.branch_lab(L0_FILES)
        before = self.worktrees(fl)
        self.assertEqual(len(before), 2)
        r = self.adopt(fl, cwd=fl.main)
        self.assertEqual(r.returncode, 0, out(r))
        (row,) = self.rows(fl)
        self.assertEqual(Path(row["worktree"]), fl.wt.resolve())
        self.assertEqual(self.worktrees(fl), before)
        self.assertFalse((fl.main / ".claude" / "worktrees").exists())
        self.assertEqual(sorted(b for b in core_git.local_branches(fl.main) if b.startswith("tg/")),
                         [BRANCH])
        self.assertIn(f"worktree esistente riusato: {fl.wt.resolve()}", r.stdout)

    def test_remote_only_branch(self):
        fl = self.branch_lab(L0_FILES, remote_only=True)
        self.assertNotIn(BRANCH, core_git.local_branches(fl.main))
        row = self.adopted(fl)
        wt = Path(row["worktree"])
        self.assertEqual(wt, fl.main / ".claude" / "worktrees" / BRANCH.replace("/", "-"))
        self.assertTrue(wt.is_dir())
        self.assertEqual(core_git.branch(wt), BRANCH)
        self.assertEqual(sorted(b for b in core_git.local_branches(fl.main) if b.startswith("tg/")),
                         [BRANCH])
        self.assertEqual(fl.git("rev-parse", "HEAD", repo=wt),
                         fl.git("rev-parse", f"origin/{BRANCH}"))
        no_upstream = subprocess.run(
            ["git", "-C", str(fl.main), "config", "--get", f"branch.{BRANCH}.merge"],
            capture_output=True, text=True)
        self.assertNotEqual(no_upstream.returncode, 0)
        self.assertTrue((wt / ".tollgate-run" / "7" / "issue.md").is_file())

    def test_local_branch_without_worktree_gets_one(self):
        fl = self.branch_lab(L0_FILES, worktree=False)
        row = self.adopted(fl)
        wt = Path(row["worktree"])
        self.assertEqual(wt.parent, fl.main / ".claude" / "worktrees")
        self.assertEqual(core_git.branch(wt), BRANCH)

    def test_branch_in_main_checkout_refused(self):
        fl = self.branch_lab(L0_FILES, worktree=False)
        fl.git("switch", "-q", BRANCH)
        r = self.adopt(fl)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("checkout principale", out(r))
        self.assertEqual(self.rows(fl), [])

    def test_missing_registered_worktree_refused_without_force(self):
        fl = self.branch_lab(L0_FILES)
        subprocess.run(["rm", "-rf", str(fl.wt)], check=True)
        r = self.adopt(fl)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("git worktree prune", out(r))
        self.assertEqual(self.rows(fl), [])


class AdoptRefusalTest(AdoptCase):
    def active_work(self, fl):
        phases.create_work(fl.conn, repo_key=repo_key(core_git.origin_url(fl.main)), issue=7,
                           level="L0", now=clock.now(), branch=BRANCH, worktree=str(fl.wt))

    def second_branch(self, fl):
        fl.git("branch", "tg/7-altro")

    def test_refused_without_act(self):
        fl = self.branch_lab(L0_FILES)
        r = self.adopt(fl, act=False)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("/tollgate:adopt #7", out(r))
        self.assertEqual(self.rows(fl), [])

    def test_refused_with_active_work_or_merged_pr_or_two_branches(self):
        cases = {
            "lavoro attivo": (lambda fl: self.active_work(fl), {}, "lavoro attivo"),
            "PR unita": (lambda fl: None, {"prs": [pr(2, "MERGED", mergedAt="2026-10-19T00:00:00Z")]},
                         "PR #2"),
            "due rami": (lambda fl: self.second_branch(fl), {}, "tg/7-altro"),
        }
        for name, (prepare, gh, text) in cases.items():
            with self.subTest(name):
                fl = self.branch_lab(L0_FILES, push=bool(gh), **gh)
                prepare(fl)
                before = len(self.rows(fl))
                r = self.adopt(fl)
                self.assertEqual(r.returncode, 1, out(r))
                self.assertIn(text, out(r))
                self.assertEqual(len(self.rows(fl)), before)
                self.assertEqual(self.act_state(fl), "pending")
                if name == "PR unita":
                    self.assertEqual(self.rows(fl), [])

    def test_no_branch_refused(self):
        fl = self.make()
        r = self.adopt(fl)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("tg/7-", out(r))

    def test_act_of_another_issue_does_not_count(self):
        fl = self.branch_lab(L0_FILES)
        self.act(fl, n=8)
        r = fl.cli("adopt", "7")
        self.assertEqual(r.returncode, 1, out(r))
        self.assertEqual(self.rows(fl), [])

    def test_unreadable_pr_state_refuses(self):
        fl = self.branch_lab(L0_FILES)
        self.gh(fl, fail=["pr list"])
        r = self.adopt(fl)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertEqual(self.rows(fl), [])

    def test_cli_usage_without_signal_does_not_adopt(self):
        fl = self.branch_lab(L0_FILES)
        self.act(fl)
        r = subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), "adopt", "7"],
                           cwd=str(fl.main), env=fl.env(), capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertEqual(self.rows(fl), [])
        self.assertEqual(sessions.bound_work(fl.conn, SESSION), None)



class AdoptL2Test(AdoptCase):
    """`adopt` di L2 (12.4, decisione 16): fette successive e fase `plan` o `approval`."""
    OTHER_SPEC_FILE = "docs/superpowers/reviews/3/spec-approval.md"
    PLAN_ADV_OFF = DEFAULT_TOML + "[components]\nplan_adversary = false\n"

    def test_later_slice_with_plan_approval_goes_execution(self):
        fl = self.branch_lab({**L2_DOCS, self.OTHER_SPEC_FILE: spec_approval(),
                              PLAN_FILE: plan_approval(spec_sha=blob(SPEC_TEXT))})
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L2", "execution"))
        self.assertEqual(row["spec_path"], SPEC_DOC)
        self.assertEqual(row["plan_path"], PLAN)
        self.assertEqual(len(scope.paths(fl.conn, row["id"])), 3)

    def test_later_slice_without_plan_approval_goes_spec_audit(self):
        fl = self.branch_lab({**L2_DOCS, self.OTHER_SPEC_FILE: spec_approval()})
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L2", "spec_audit"))
        self.assertIsNone(row["plan_sha"])

    def test_later_slice_with_spec_changed_after_the_first_approval_goes_spec_audit(self):
        fl = self.branch_lab({**L2_DOCS, self.OTHER_SPEC_FILE: spec_approval(sha=blob("vecchia\n")),
                              PLAN_FILE: plan_approval(spec_sha=blob("vecchia\n"))})
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L2", "spec_audit"))

    def test_plan_without_approval_goes_plan_with_adversary_on(self):
        fl = self.branch_lab({**L2_DOCS, SPEC_FILE: spec_approval()})
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L2", "plan"))
        self.assertEqual(row["plan_path"], PLAN)
        self.assertIsNone(row["plan_sha"])
        self.assertEqual(scope.paths(fl.conn, row["id"]), set())

    def test_plan_without_approval_goes_approval_with_adversary_off(self):
        fl = self.branch_lab({**L2_DOCS, SPEC_FILE: spec_approval()}, toml=self.PLAN_ADV_OFF)
        row = self.adopted(fl)
        self.assertEqual((row["level"], row["phase"]), ("L2", "approval"))
        self.assertEqual(row["plan_path"], PLAN)
        self.assertIsNone(row["plan_sha"])
