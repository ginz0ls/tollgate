import io
import json
import os
import unittest
from contextlib import redirect_stderr
from unittest import mock

from tests.flowkit import JUNIT_TOML, PLAN, FlowLab, plan_text
from tests.helpers import git
from tollgate_core import acts, cli, dod, git as core_git, phases
from tollgate_flow import finishcheck, gh, gitw

BOTH_OK = "tests.test_app::test_somma ok\ntests.test_app::test_zero ok\n"
SOMMA = "def somma(a, b):\n    return b + a\n"
# gli identificativi del finto JUnit stanno in tests/ids.txt: non sono lavoro del piano
TOML = JUNIT_TOML + '[scope]\nalways = ["tests/ids.txt"]\n'
PROFILE_TOML = TOML + '[profiles.p]\npaths = ["src/**"]\ndod = ["lint"]\n'


def phase(fl):
    return phases.get_work(fl.conn, fl.work)["phase"]


def head(fl):
    return core_git.head(fl.wt)


def receipts(fl):
    return fl.conn.execute("SELECT count(*) FROM receipts").fetchone()[0]


def item_lines(r):
    return [x for x in r.lines if x.startswith(("[sì]", "[no]", "[dopo la revisione]"))]


class FinishCheckCase(unittest.TestCase):
    def lab(self, *, ids=BOTH_OK, toml=TOML, close=True, level="L1", plan=None):
        """Lavoro L1 in execution: piano registrato e committato, un commit sul file dello
        scope, task chiusi, report JUnit dagli identificativi."""
        fl = FlowLab(issue=7, phase="plan" if level != "L0" else "execution", toml=toml,
                     level=level)
        self.addCleanup(fl.close)
        if level != "L0":
            if plan is None:
                fl.register_plan(tasks=1)
            else:
                (fl.wt / PLAN).parent.mkdir(parents=True, exist_ok=True)
                (fl.wt / PLAN).write_text(plan)
                self.assertEqual(fl.post_edit(fl.wt / PLAN).exit, 0)
            fl.commit(PLAN, plan or plan_text(tasks=1), "piano")
        fl.commit("tests/ids.txt", ids, "ids")
        fl.commit("src/app.py", SOMMA, "somma")
        if close and level != "L0":
            fl.close_tasks()
        return fl

    def check(self, fl, **kw):
        return finishcheck.check(fl.ts.state, fl.wt, environ=fl.env(), **kw)

    def item(self, r, key):
        return next(i for i in r.items if i.key == key)


class GreenRedTest(FinishCheckCase):
    def test_green_moves_to_review_and_prints_dod(self):
        fl = self.lab()
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        work = phases.get_work(fl.conn, fl.work)
        self.assertEqual((work["phase"], work["finish_sha"]), ("review", head(fl)))
        keys = dod.ITEMS_BY_LEVEL["L1"]
        self.assertEqual([i.key for i in r.items], list(keys))
        self.assertEqual(len(item_lines(r)), len(keys))
        self.assertEqual([x[:4] for x in item_lines(r) if "Nessun rilievo" in x], ["[dop"])
        self.assertEqual(sum(x.startswith("[sì]") for x in r.lines), len(keys) - 1)
        report = json.loads(work["finish_report"])
        self.assertEqual(report["items"], {"receipt": True, "guard_scope": True,
                                           "tasks_approved": True, "findings": None,
                                           "must_have": True, "skills": True})
        self.assertEqual(report["manual"], [])
        self.assertEqual(fl.events("finish_check"), [{"sha": head(fl), "ok": True}])
        self.assertTrue(r.lines[-1].startswith("prossimo passo: python3 "))
        self.assertTrue(r.lines[-1].endswith(" review prepare"))
        self.assertGreater(receipts(fl), 0)

    def test_red_stays_in_execution(self):
        fl = self.lab(ids="tests.test_app::test_somma ok\ntests.test_app::test_zero fail\n")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED, r.lines)
        self.assertEqual(phase(fl), "execution")
        self.assertFalse(self.item(r, "receipt").ok)
        self.assertFalse(self.item(r, "must_have").ok)
        self.assertTrue(any(x.startswith("[no]") for x in r.lines))
        self.assertEqual(fl.events("finish_check"), [{"sha": head(fl), "ok": False}])
        self.assertIsNone(phases.get_work(fl.conn, fl.work)["finish_sha"])
        self.assertIn("rilancia", r.lines[-1])

    def test_task_not_done_refused(self):
        fl = self.lab(close=False)
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.REFUSED)
        self.assertIn("1", r.lines[-1])
        self.assertTrue(r.lines[-1].startswith("rifiuto:"))
        self.assertEqual((phase(fl), receipts(fl)), ("execution", 0))
        self.assertEqual(fl.events("finish_check"), [])

    def test_must_have_test_missing_is_red(self):
        fl = self.lab(ids="tests.test_app::test_zero ok\n")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED, r.lines)
        mh = self.item(r, "must_have")
        self.assertFalse(mh.ok)
        self.assertIn("tests.test_app::test_somma", " ".join(r.lines))
        self.assertTrue(self.item(r, "receipt").ok)
        self.assertEqual(phase(fl), "execution")

    def test_out_of_scope_commit_is_red(self):
        fl = self.lab()
        fl.commit("src/extra.py", "x = 1\n", "fuori scope")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED, r.lines)
        self.assertFalse(self.item(r, "guard_scope").ok)
        self.assertIn("src/extra.py", " ".join(r.lines))
        self.assertTrue(self.item(r, "receipt").ok)
        self.assertEqual(phase(fl), "execution")

    def test_checkpoint_present_is_ignored(self):
        fl = self.lab()
        p = fl.cli("status", "--checkpoint", cwd=fl.wt)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue((fl.wt / "docs/superpowers/reviews/7/checkpoint.md").exists())
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        self.assertEqual(phase(fl), "review")

    def test_dirty_worktree_refused_phase_unchanged(self):
        fl = self.lab()
        (fl.wt / "src" / "dirty.py").write_text("x = 1\n")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.REFUSED, r.lines)
        self.assertIn("non pulito", " ".join(r.lines))
        self.assertEqual(phase(fl), "execution")
        self.assertEqual(fl.events("finish_check"), [])

    def test_wrong_phase_refused(self):
        fl = FlowLab(issue=7, phase="plan")
        self.addCleanup(fl.close)
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.REFUSED)
        self.assertIn("plan", r.lines[-1])

    def test_no_work_refused(self):
        fl = FlowLab(issue=None)
        self.addCleanup(fl.close)
        r = finishcheck.check(fl.ts.state, fl.main, environ=fl.env())
        self.assertEqual(r.code, finishcheck.REFUSED)

    def test_git_and_os_errors_are_refusals_not_tracebacks(self):
        fl = self.lab()
        for exc in (core_git.GitError("git: rotto"), OSError("disco")):
            with self.subTest(exc=type(exc).__name__):
                with mock.patch.object(finishcheck.git, "head", side_effect=exc):
                    r = self.check(fl)
                self.assertEqual(r.code, finishcheck.REFUSED, r.lines)
                self.assertIn(str(exc), " ".join(r.lines))

    def test_fetch_failure_warns_and_goes_on(self):
        fl = self.lab()
        with mock.patch.object(gitw, "fetch", return_value=False):
            r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        self.assertTrue(r.lines[0].startswith("avviso:"))


class RerunTest(FinishCheckCase):
    def test_rerun_in_review_same_sha_is_idempotent(self):
        fl = self.lab()
        first = self.check(fl)
        n_receipts = receipts(fl)
        n_phase = len(fl.events("phase_change"))
        second = self.check(fl)
        self.assertEqual(second.code, finishcheck.OK, second.lines)
        self.assertEqual(item_lines(second), item_lines(first))
        self.assertEqual([(i.key, i.ok) for i in second.items],
                         [(i.key, i.ok) for i in first.items])
        self.assertEqual(second.lines[-1], first.lines[-1])
        self.assertEqual((receipts(fl), len(fl.events("phase_change")),
                          len(fl.events("finish_check"))), (n_receipts, n_phase, 1))
        self.assertEqual(phase(fl), "review")

    def test_rerun_in_review_other_sha(self):
        fl = self.lab()
        self.check(fl)
        phase_events = len(fl.events("phase_change"))
        sha = fl.commit("src/app.py", SOMMA + "\n", "ritocco")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        work = phases.get_work(fl.conn, fl.work)
        self.assertEqual((work["phase"], work["finish_sha"]), ("review", sha))
        self.assertEqual(len(fl.events("phase_change")), phase_events)
        self.assertEqual([e["ok"] for e in fl.events("finish_check")], [True, True])

    def test_red_in_review_other_sha_keeps_phase(self):
        fl = self.lab()
        self.check(fl)
        fl.commit("tests/ids.txt", "tests.test_app::test_somma fail\n", "rosso")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED)
        self.assertEqual(phase(fl), "review")


class LevelsTest(FinishCheckCase):
    def test_l0_without_tasks(self):
        fl = self.lab(level="L0")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        self.assertEqual([i.key for i in r.items], ["receipt", "guard_scope"])
        self.assertEqual(phase(fl), "review")
        self.assertTrue(r.lines[-1].endswith(" finish open-pr"))
        report = json.loads(phases.get_work(fl.conn, fl.work)["finish_report"])
        self.assertEqual(report["items"], {"receipt": True, "guard_scope": True})

    def test_l2_approvals_follow_the_files(self):
        fl = self.lab()
        spec = "docs/superpowers/specs/2026-10-16-somma-design.md"
        fl.conn.execute("UPDATE work_items SET level = 'L2', spec_path = ? WHERE id = ?",
                        (spec, fl.work))
        fl.commit(spec, "# spec\n", "spec")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED, r.lines)
        self.assertFalse(self.item(r, "approvals").ok)
        self.assertEqual(phase(fl), "execution")
        sha_spec = git(fl.wt, "rev-parse", f"HEAD:{spec}")
        sha_plan = git(fl.wt, "rev-parse", f"HEAD:{PLAN}")
        header = "---\nschema_version: 1\nkind: {}\npath: {}\nsha: \"{}\"\n---\n"
        fl.commit("docs/superpowers/reviews/7/spec-approval.md",
                  header.format("spec-approval", spec, sha_spec), "approvazione spec")
        fl.commit("docs/superpowers/reviews/7/plan-approval.md",
                  header.format("plan-approval", PLAN, "0" * 40), "approvazione piano")
        r = self.check(fl)
        self.assertFalse(self.item(r, "approvals").ok, "sha del piano diverso dal blob")
        fl.commit("docs/superpowers/reviews/7/plan-approval.md",
                  header.format("plan-approval", PLAN, sha_plan), "approvazione piano")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        self.assertTrue(self.item(r, "approvals").ok)
        self.assertEqual([i.key for i in r.items], list(dod.ITEMS_BY_LEVEL["L2"]))
        self.assertEqual(self.item(r, "specialists").ok, None)

    SPEC = "docs/superpowers/specs/2026-10-16-somma-design.md"
    HEADER = "---\nschema_version: 1\nkind: {}\npath: {}\nsha: \"{}\"\n---\n"

    def l2_lab(self):
        """L2 in execution con spec e approvazioni committate e coerenti con HEAD."""
        fl = self.lab()
        fl.conn.execute("UPDATE work_items SET level = 'L2', spec_path = ? WHERE id = ?",
                        (self.SPEC, fl.work))
        fl.commit(self.SPEC, "# spec\n", "spec")
        self.approve(fl)
        return fl

    def approve(self, fl):
        """Riscrive i due file di approvazione con gli sha di HEAD."""
        for kind, doc in (("spec-approval", self.SPEC), ("plan-approval", PLAN)):
            path = f"docs/superpowers/reviews/7/{kind}.md"
            text = self.HEADER.format(kind, doc, git(fl.wt, "rev-parse", f"HEAD:{doc}"))
            if not (fl.wt / path).exists() or (fl.wt / path).read_text() != text:
                fl.commit(path, text, kind)

    def test_l2_approved_spec_and_reviews_files_exempt(self):
        fl = self.l2_lab()
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        self.assertTrue(self.item(r, "guard_scope").ok)

    def test_l2_modified_plan_after_registration_is_out_of_scope(self):
        fl = self.l2_lab()
        fl.commit(PLAN, plan_text(tasks=1) + "\n- Create: `src/extra.py`\n", "piano ritoccato")
        self.approve(fl)
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED, r.lines)
        self.assertFalse(self.item(r, "guard_scope").ok)
        self.assertIn(PLAN, " ".join(r.lines))

    def test_l2_spec_changed_after_approval_is_out_of_scope(self):
        fl = self.l2_lab()
        fl.commit(self.SPEC, "# spec cambiata\n", "spec ritoccata")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED, r.lines)
        self.assertFalse(self.item(r, "guard_scope").ok)
        self.assertIn(self.SPEC, " ".join(r.lines))

    def test_must_have_manual_listed_in_report(self):
        text = plan_text(tasks=1).replace("M2. Zero — test: tests.test_app::test_zero",
                                          "M2. Colore — test: manuale")
        fl = self.lab(plan=text, ids="tests.test_app::test_somma ok\n")
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        report = json.loads(phases.get_work(fl.conn, fl.work)["finish_report"])
        self.assertEqual(report["manual"], ["M2"])
        self.assertIn("M2", " ".join(r.lines))


class ProfileDodTest(FinishCheckCase):
    def test_dod_without_command_is_red_and_names_it(self):
        fl = self.lab(toml=PROFILE_TOML)
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.RED, r.lines)
        line = next(x for x in item_lines(r) if x.startswith("[no] Voce del profilo"))
        self.assertTrue(line.startswith("[no]"))
        self.assertIn("lint", line)
        self.assertIn("[commands]", line)
        self.assertEqual(phase(fl), "execution")

    def test_unverified_tests_approval_passes(self):
        fl = self.lab(toml=PROFILE_TOML)
        acts.record_act(fl.conn, type_="approve", object_="unverified-tests",
                        typed_text="/tollgate:approve unverified-tests", session="sess-flow",
                        work=fl.work, now=fl.now, ttl_minutes=30)
        r = self.check(fl)
        self.assertEqual(r.code, finishcheck.OK, r.lines)
        self.assertTrue(self.item(r, "profile:p:lint").ok)
        self.assertEqual(phase(fl), "review")


class CliTest(FinishCheckCase):
    def test_finish_check_subcommand_exit_code_and_output(self):
        fl = self.lab()
        p = fl.cli("finish", "check", cwd=fl.wt)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("prossimo passo:", p.stdout.splitlines()[-1])
        self.assertEqual(phase(fl), "review")

    def test_finish_check_red_exits_one(self):
        fl = self.lab(ids="tests.test_app::test_somma fail\n")
        p = fl.cli("finish", "check", cwd=fl.wt)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)

    def test_external_errors_become_a_message_and_exit_one(self):
        fl = self.lab()
        errors = (gh.GhError("gh ko"), core_git.GitError("git ko"), gitw.GitWriteError("w ko"))
        for err in errors:
            with self.subTest(err=type(err).__name__), \
                    mock.patch.dict(os.environ, fl.ts.env()), \
                    mock.patch.object(finishcheck, "check", side_effect=err), \
                    redirect_stderr(io.StringIO()) as buf:
                self.assertEqual(cli.main(["finish", "check"]), 1)
                self.assertIn(str(err), buf.getvalue())

    def test_unknown_errors_still_propagate(self):
        fl = self.lab()
        with mock.patch.dict(os.environ, fl.ts.env()), \
                mock.patch.object(finishcheck, "check", side_effect=RuntimeError("bug")):
            with self.assertRaises(RuntimeError):
                cli.main(["finish", "check"])


if __name__ == "__main__":
    unittest.main()
