import json
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

from tests.flowkit import SESSION
from tests.helpers import git as run_git
from tests.test_openpr import BRANCH, OpenCase, head, pr, work
from tollgate_core import (acts, clock, events, git as core_git, intents, phases, reviews, sessions,
                           subagents)
from tollgate_flow import gitw, prstate, sync

TWELVE = "".join(f"x{i} = {i}\n" for i in range(1, 13))
TWELVE_WORK = TWELVE.replace("x2 = 2\n", "x2 = 20\n")
TWELVE_MAIN = TWELVE.replace("x5 = 5\n", "x5 = 50\n")


class SyncCase(OpenCase):
    def pr_open_lab(self, **kw):
        """Lavoro in `pr_open`: PR aperta (la numero 1), ramo spinto su origin, identità per i
        rebase e il predefinito ancora fermo."""
        fl = self.lab(**kw)
        fl.git("config", "user.name", "t")
        fl.git("config", "user.email", "t@example.com")
        r = self.go(fl)
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(work(fl)["phase"], "pr_open")
        self.at = fl.now + timedelta(hours=2)
        return fl

    def advance_main(self, fl, path="docs/nuovo.md", text="nuovo\n", msg="avanza"):
        """Un commit sul predefinito di origin, spinto dal checkout principale."""
        target = fl.main / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        fl.git("add", "--", path)
        fl.git("commit", "-qm", msg)
        fl.git("push", "-q", "origin", "main")
        return fl.git("rev-parse", "HEAD")

    def update_branch_remote(self, fl):
        """«Update branch» su origin/<ramo>: il predefinito (avanzato prima) unito con un merge."""
        clone = fl.tmp / "clone"
        run_git(fl.tmp, "clone", "-q", str(fl.origin), str(clone))
        run_git(clone, "checkout", "-q", "-b", BRANCH, f"origin/{BRANCH}")
        run_git(clone, "merge", "-q", "--no-ff", "-m", "Update branch", "origin/main")
        run_git(clone, "push", "-q", "origin", BRANCH)
        return clone, run_git(clone, "rev-parse", "HEAD")

    def sync_act(self, fl, *, session=SESSION):
        return acts.record_act(fl.conn, type_="sync", typed_text="/tollgate:sync",
                               session=session, work=fl.work, now=self.at, ttl_minutes=10)

    def run_sync(self, fl, *, act=True, **kw):
        if act:
            self.sync_act(fl)
        sessions.note_cli_call(fl.ts.state, SESSION, str(fl.wt), ["sync"], now=self.at)
        return sync.sync(fl.ts.state, fl.wt, now=self.at, environ=fl.env(), **kw)

    def intent_states(self, fl, action):
        return [r[0] for r in fl.conn.execute(
            "SELECT state FROM intents WHERE work = ? AND action = ? ORDER BY id",
            (fl.work, action))]


class SyncOpenWorkTest(SyncCase):
    """I-2: `sync` non riscrive i commit mentre un task o un implementatore li sta usando."""

    def execution_lab(self):
        fl = self.lab()
        fl.git("config", "user.name", "t")
        fl.git("config", "user.email", "t@example.com")
        phases.set_phase(fl.conn, fl.ts.state, fl.work, "execution", "needs_fix", now=fl.now)
        self.at = fl.now + timedelta(hours=2)
        self.advance_main(fl)
        return fl

    def assert_refused_untouched(self, fl, pattern):
        before = head(fl)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertRegex(" ".join(r.lines), pattern)
        self.assertEqual(head(fl), before)
        self.assertEqual(self.intent_states(fl, "sync"), [])
        self.assertEqual(work(fl)["phase"], "execution")

    def test_task_in_review_with_commits_refuses(self):
        fl = self.execution_lab()
        fl.conn.execute("UPDATE tasks SET state = 'review', commits = ? WHERE work = ? "
                        "AND number = 1", (json.dumps([head(fl)]), fl.work))
        self.assert_refused_untouched(fl, r"chiudi o riporta in attesa il task 1, poi "
                                          r"/tollgate:sync")

    def test_running_task_refuses(self):
        fl = self.execution_lab()
        fl.conn.execute("UPDATE tasks SET state = 'running' WHERE work = ? AND number = 1",
                        (fl.work,))
        self.assert_refused_untouched(fl, r"task 1")

    def test_writer_subagent_running_refuses(self):
        fl = self.execution_lab()
        subagents.start(fl.conn, agent_id="a-1", type_="tollgate:implementer", session=SESSION,
                        work=fl.work, task=1, base_sha=None, fingerprint=None, now=self.at)
        self.assert_refused_untouched(fl, r"implementatore")

    def test_finish_check_refusal_is_not_reported_as_red(self):
        fl = self.execution_lab()
        fl.conn.execute("UPDATE tasks SET state = 'pending' WHERE work = ? AND number = 1",
                        (fl.work,))
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        text = " ".join(r.lines)
        self.assertIn("finish check ha rifiutato", text)
        self.assertNotIn("non è verde", text)

    def test_finish_check_red_is_reported_as_red(self):
        fl = self.execution_lab()
        with mock.patch.object(sync.finishcheck, "check",
                               return_value=sync.finishcheck.CheckResult(1, ["[no] x"])):
            r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertIn("finish check non è verde dopo il rebase", " ".join(r.lines))

    def test_readonly_subagent_does_not_refuse(self):
        fl = self.execution_lab()
        subagents.start(fl.conn, agent_id="a-2", type_="tollgate:final-reviewer", session=SESSION,
                        work=fl.work, task=None, base_sha=None, fingerprint=None, now=self.at)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)


class SyncRefusalTest(SyncCase):
    def test_refused_without_sync_act(self):
        fl = self.pr_open_lab()
        self.advance_main(fl)
        before = head(fl)
        r = self.run_sync(fl, act=False)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertIn("/tollgate:sync", " ".join(r.lines))
        self.assertEqual(head(fl), before)
        self.assertEqual(self.intent_states(fl, "sync"), [])
        self.assertEqual(work(fl)["phase"], "pr_open")

    def test_closed_pr_not_cleared_refused_with_hint(self):
        fl = self.pr_open_lab()
        self.advance_main(fl)
        fl.set_gh(prs=[pr(1, "CLOSED")])
        before = head(fl)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertIn(prstate.CLOSED_HINT, "\n".join(r.lines))
        self.assertEqual(head(fl), before)

    def test_merged_pr_closes_work_and_refuses(self):
        fl = self.pr_open_lab()
        fl.set_gh(prs=[pr(1, "MERGED", mergedAt="2026-10-19T00:00:00Z")])
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertEqual(work(fl)["phase"], "closed")

    def test_wrong_phase_refused(self):
        fl = self.lab()
        fl.git("config", "user.name", "t")
        self.at = fl.now + timedelta(hours=2)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertIn("review", " ".join(r.lines))


class SyncRebaseTest(SyncCase):
    def test_rebase_realigns_base_and_updates_pr(self):
        fl = self.pr_open_lab()
        old_head = head(fl)
        tip = self.advance_main(fl)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)
        new_head = head(fl)
        self.assertNotEqual(new_head, old_head)
        self.assertEqual(fl.git("merge-base", "HEAD", "origin/main", repo=fl.wt), tip)
        w = work(fl)
        self.assertEqual(w["work_base_sha"], tip)
        self.assertEqual(w["phase"], "pr_open")
        self.assertEqual(fl.events("base_realigned")[-1]["to"], tip)
        self.assertEqual(fl.events("base_realigned")[-1]["cause"], "sync")
        recorded = {e["sha"] for e in fl.events("commit")}
        self.assertTrue(set(core_git.rev_list(fl.wt, tip, new_head)) <= recorded)
        self.assertEqual(fl.events("pr_updated")[-1], {"pr": 1, "sha": new_head})
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), new_head)
        self.assertEqual(len(self.calls(fl, "pr", "edit")), 1)
        self.assertEqual(self.calls(fl, "pr", "create")[1:], [])
        self.assertEqual(self.intent_states(fl, "sync"), ["executed"])
        self.assertEqual(self.intent_states(fl, "force_push"), ["used"])
        self.assertEqual(fl.conn.execute("SELECT state FROM acts WHERE type = 'sync'")
                         .fetchone()[0], "consumed")
        phases_seen = [json.loads(e["data"]) for e in fl.conn.execute(
            "SELECT data FROM events WHERE type = 'phase_change' ORDER BY seq")]
        self.assertIn({"from": "pr_open", "to": "execution", "cause": "sync"}, phases_seen)

    def test_same_patch_id_no_cycle_consumed(self):
        fl = self.pr_open_lab()
        cycles = reviews.count(fl.conn, fl.work)
        self.assertEqual(cycles, 1)
        self.advance_main(fl)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)
        self.assertEqual(reviews.count(fl.conn, fl.work), cycles)
        last = reviews.latest(fl.conn, fl.work)
        self.assertEqual(last["patch_id"],
                         core_git.patch_id(fl.wt, work(fl)["work_base_sha"], head(fl)))

    def test_nothing_to_rebase_updates_nothing_rewritten(self):
        fl = self.pr_open_lab()
        before = head(fl)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)
        self.assertEqual(head(fl), before)
        self.assertEqual(self.intent_states(fl, "force_push"), [])
        self.assertEqual(self.intent_states(fl, "sync"), ["executed"])

    def test_stale_pending_sync_intent_completed(self):
        fl = self.pr_open_lab()
        self.advance_main(fl)
        intents.request(fl.conn, work=fl.work, action="sync", key=f"sync:{fl.work}:a-0",
                        data={}, now=fl.now)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)
        self.assertEqual(intents.pending(fl.conn, fl.work, "sync"), [])

    def test_remote_merge_then_rebase(self):
        """«Update branch» su GitHub: un merge del predefinito su origin/<ramo>. Si integra con
        --ff-only, poi il rebase sul predefinito avanzato lo toglie dalla storia."""
        fl = self.pr_open_lab()
        self.advance_main(fl, msg="primo")
        clone = fl.tmp / "clone"
        run_git(fl.tmp, "clone", "-q", str(fl.origin), str(clone))
        run_git(clone, "checkout", "-q", "-b", BRANCH, f"origin/{BRANCH}")
        run_git(clone, "merge", "-q", "--no-ff", "-m", "Update branch", "origin/main")
        merge = run_git(clone, "rev-parse", "HEAD")
        run_git(clone, "push", "-q", "origin", BRANCH)
        tip = self.advance_main(fl, path="docs/altro.md", msg="secondo")
        self.sync_act(fl)
        sessions.note_cli_call(fl.ts.state, SESSION, str(fl.wt), ["sync"], now=self.at)
        with mock.patch.object(gitw, "merge_ff_only", wraps=gitw.merge_ff_only) as ff:
            r = sync.sync(fl.ts.state, fl.wt, now=self.at, environ=fl.env())
        self.assertEqual(r.code, sync.OK, r.lines)
        ff.assert_called_once_with(fl.wt, merge)
        self.assertFalse(gitw.is_ancestor(fl.wt, merge, head(fl)))
        self.assertEqual(fl.git("merge-base", "HEAD", "origin/main", repo=fl.wt), tip)
        self.assertEqual(work(fl)["work_base_sha"], tip)
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), head(fl))
        self.assertEqual(self.intent_states(fl, "force_push"), ["used"])

    def test_integrated_commits_recorded_when_rebase_conflicts(self):
        """Review Focus 4: dopo l'integrazione --ff-only HEAD sta sulla punta remota; con il
        conflitto nel rebase quei commit sono comunque noti, e PostToolUse Bash non apre nulla."""
        fl = self.pr_open_lab()
        self.advance_main(fl, msg="primo")
        clone, merge = self.update_branch_remote(fl)
        self.advance_main(fl, path="src/app.py",
                          text="def somma(a, b):\n    return a + b + 0\n", msg="conflitto")
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.BLOCKED, r.lines)
        self.assertEqual(head(fl), merge)                     # l'integrazione è rimasta
        recorded = {e["sha"] for e in fl.events("commit")}
        unknown = set(core_git.rev_list(fl.wt, work(fl)["work_base_sha"], head(fl))) - recorded
        self.assertEqual(unknown, set())
        commits = len(fl.events("commit"))
        out = fl.bash("git status", post=True, cwd=fl.wt)
        self.assertEqual(out.exit, 0, out.stderr)
        self.assertEqual(len(fl.events("commit")), commits)
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM blocks WHERE closed IS NULL AND "
                                         "reason NOT LIKE 'sync:%'").fetchone()[0], 0)

    def test_repeat_after_integrated_merge_is_not_divergent(self):
        fl = self.pr_open_lab_twelve()
        self.advance_main(fl, path="docs/uno.md", msg="primo")
        self.update_branch_remote(fl)
        self.advance_main(fl, path="src/app.py", text=TWELVE_MAIN, msg="secondo")
        self.assertEqual(self.run_sync(fl).code, sync.REVIEW_NEEDED)
        self.at += timedelta(minutes=30)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REVIEW_NEEDED, r.lines)
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM blocks").fetchone()[0], 0)

    def test_diverged_remote_needs_you(self):
        fl = self.pr_open_lab()
        self.advance_main(fl)
        clone = fl.tmp / "clone"
        run_git(fl.tmp, "clone", "-q", str(fl.origin), str(clone))
        run_git(clone, "checkout", "-q", "-b", BRANCH, f"origin/{BRANCH}")
        run_git(clone, "commit", "-q", "--allow-empty", "-m", "di un altro")
        run_git(clone, "push", "-q", "origin", BRANCH)
        fl.git("commit", "-q", "--allow-empty", "-m", "mio", repo=fl.wt)
        before, remote = head(fl), gitw.remote_sha(fl.wt, BRANCH)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.BLOCKED, r.lines)
        self.assertEqual(head(fl), before)
        self.assertNotEqual(remote, before)
        self.assertFalse(gitw.rebase_in_progress(fl.wt))
        (block,) = fl.conn.execute("SELECT * FROM blocks WHERE closed IS NULL").fetchall()
        self.assertEqual(block["type"], "needs_you")
        self.assertIn("diverg", block["reason"])
        self.assertEqual(self.intent_states(fl, "force_push"), [])

    def test_conflict_aborts_and_blocks(self):
        fl = self.pr_open_lab()
        old_base = work(fl)["work_base_sha"]
        before = head(fl)
        self.advance_main(fl, path="src/app.py", text="def somma(a, b):\n    return a + b + 0\n")
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.BLOCKED, r.lines)
        self.assertFalse(gitw.rebase_in_progress(fl.wt))
        self.assertEqual(head(fl), before)
        self.assertEqual(fl.git("status", "--porcelain", "--untracked-files=no", repo=fl.wt), "")
        w = work(fl)
        self.assertEqual(w["work_base_sha"], old_base)
        self.assertEqual((w["phase"], w["phase_before_block"]), ("blocked", "pr_open"))
        (block,) = fl.conn.execute("SELECT * FROM blocks WHERE closed IS NULL").fetchall()
        self.assertEqual(block["type"], "needs_you")
        self.assertTrue(block["reason"].startswith(intents.SYNC_CONFLICT_REASON))
        self.assertIn("/tollgate:approve rebase", block["reason"])
        self.assertIn("/tollgate:abandon #7", block["reason"])
        self.assertIn("/tollgate:approve rebase", "\n".join(r.lines))
        self.assertEqual(self.intent_states(fl, "force_push"), [])
        self.assertEqual(self.intent_states(fl, "sync"), ["executed"])
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), before)
        self.assertEqual(fl.events("base_realigned"), [])

    def test_different_patch_id_asks_new_review(self):
        fl = self.pr_open_lab_twelve()
        old_head = head(fl)
        self.advance_main(fl, path="src/app.py", text=TWELVE_MAIN)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REVIEW_NEEDED, r.lines)
        self.assertIn("serve una nuova revisione: /tollgate:finish", "\n".join(r.lines))
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), old_head)       # nessun push
        self.assertEqual(self.calls(fl, "pr", "edit"), [])
        self.assertEqual(work(fl)["phase"], "review")
        self.assertEqual(fl.events("pr_updated"), [])
        self.assertEqual(reviews.count(fl.conn, fl.work), 1)
        self.assertTrue(intents.force_authorized(fl.conn, fl.work))      # per il finish che segue

    def test_repeat_after_review_needed_is_not_divergent(self):
        """Il remoto ha ancora il vecchio push (nostro, poi riscritto): non è una divergenza."""
        fl = self.pr_open_lab_twelve()
        self.advance_main(fl, path="src/app.py", text=TWELVE_MAIN)
        self.assertEqual(self.run_sync(fl).code, sync.REVIEW_NEEDED)
        self.at += timedelta(minutes=30)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REVIEW_NEEDED, r.lines)
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM blocks").fetchone()[0], 0)
        self.assertEqual(self.intent_states(fl, "force_push"), ["authorized"])

    def test_force_lease_is_remote_tip_at_sync_and_rejects_newer_remote(self):
        fl = self.pr_open_lab_twelve()
        old_head = head(fl)
        self.advance_main(fl, path="src/app.py", text=TWELVE_MAIN)
        self.assertEqual(self.run_sync(fl).code, sync.REVIEW_NEEDED)
        self.assertEqual(intents.force_lease(fl.conn, fl.work), old_head)
        clone = fl.tmp / "clone"
        run_git(fl.tmp, "clone", "-q", str(fl.origin), str(clone))
        run_git(clone, "checkout", "-q", "-b", BRANCH, f"origin/{BRANCH}")
        run_git(clone, "commit", "-q", "--allow-empty", "-m", "a mano")
        run_git(clone, "push", "-q", "origin", BRANCH)
        manual = run_git(clone, "rev-parse", "HEAD")
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        r = self.go(fl, update=True, via_sync="a-99")
        self.assertEqual(r.code, 1, r.lines)
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), manual)         # commit remoto intatto
        self.assertEqual(self.intent_states(fl, "force_push"), ["authorized"])
        self.assertEqual(self.calls(fl, "pr", "edit"), [])

    def test_stale_lease_is_renewed_and_open_pr_pushes(self):
        """I-4: il remoto è avanzato dopo l'autorizzazione e i suoi commit sono integrati."""
        fl = self.pr_open_lab_twelve()
        old_head = head(fl)
        self.advance_main(fl, path="src/app.py", text=TWELVE_MAIN)
        self.assertEqual(self.run_sync(fl).code, sync.REVIEW_NEEDED)
        self.assertEqual(intents.force_lease(fl.conn, fl.work), old_head)
        clone = fl.tmp / "clone"
        run_git(fl.tmp, "clone", "-q", str(fl.origin), str(clone))
        run_git(clone, "checkout", "-q", "-b", BRANCH, f"origin/{BRANCH}")
        run_git(clone, "commit", "-q", "--allow-empty", "-m", "Update branch")
        run_git(clone, "push", "-q", "origin", BRANCH)
        advanced = run_git(clone, "rev-parse", "HEAD")
        events.record_event(fl.conn, "commit", {"sha": advanced}, now=self.at, work=fl.work)
        self.at += timedelta(minutes=30)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REVIEW_NEEDED, r.lines)
        self.assertEqual(intents.force_lease(fl.conn, fl.work), advanced)
        self.assertEqual(self.intent_states(fl, "force_push"), ["authorized"])
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        r = self.go(fl, update=True, via_sync="a-99")
        self.assertEqual(r.code, 0, r.lines)
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), head(fl))
        self.assertEqual(self.intent_states(fl, "force_push"), ["used"])

    def test_failed_lease_push_points_to_sync(self):
        fl = self.pr_open_lab_twelve()
        self.advance_main(fl, path="src/app.py", text=TWELVE_MAIN)
        self.assertEqual(self.run_sync(fl).code, sync.REVIEW_NEEDED)
        clone = fl.tmp / "clone"
        run_git(fl.tmp, "clone", "-q", str(fl.origin), str(clone))
        run_git(clone, "checkout", "-q", "-b", BRANCH, f"origin/{BRANCH}")
        run_git(clone, "commit", "-q", "--allow-empty", "-m", "a mano")
        run_git(clone, "push", "-q", "origin", BRANCH)
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        r = self.go(fl, update=True, via_sync="a-99")
        self.assertEqual(r.code, 1, r.lines)
        self.assertIn("il ramo remoto è avanzato: /tollgate:sync", " ".join(r.lines))

    def pr_open_lab_twelve(self):
        return self.pr_open_lab(files={"src/app.py": TWELVE}, app=TWELVE_WORK)

    def test_execution_without_open_pr_stops_after_finish_check(self):
        fl = self.lab()
        fl.git("config", "user.name", "t")
        fl.git("config", "user.email", "t@example.com")
        phases.set_phase(fl.conn, fl.ts.state, fl.work, "execution", "needs_fix", now=fl.now)
        self.at = fl.now + timedelta(hours=2)
        self.advance_main(fl)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)
        self.assertIn("PR non ancora aperta: /tollgate:finish", "\n".join(r.lines))
        self.assertEqual(work(fl)["phase"], "review")
        self.assertEqual(self.calls(fl, "pr", "create"), [])
        self.assertIsNone(gitw.remote_sha(fl.wt, BRANCH))
        self.assertEqual(self.intent_states(fl, "force_push"), [])

    def test_post_bash_ignores_rewritten_commits(self):
        fl = self.pr_open_lab()
        self.advance_main(fl)
        r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)
        commits = len(fl.events("commit"))
        out = fl.bash("git status", post=True, cwd=fl.wt)
        self.assertEqual(out.exit, 0, out.stderr)
        self.assertEqual(len(fl.events("commit")), commits)
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM blocks WHERE closed IS NULL")
                         .fetchone()[0], 0)
        # controllo: un commit che nessuno ha registrato, invece, lo vede
        fl.git("commit", "-q", "--allow-empty", "-m", "nuovo", repo=fl.wt)
        fl.bash("git commit --allow-empty -m nuovo", post=True, cwd=fl.wt)
        self.assertEqual(len(fl.events("commit")), commits + 1)


class SyncEdgeTest(SyncCase):
    """Riga 55 di P3b: l'ordine dell'intento, il rebase già in corso, `--ff-only` che fallisce e
    `finish check` rosso dopo il rebase."""

    def test_intent_recorded_before_rebase(self):
        fl = self.pr_open_lab()
        old_head = head(fl)
        tip = self.advance_main(fl)
        seen = []
        real = gitw.rebase

        def spy(wt, onto):
            seen.append([(r["state"], json.loads(r["data"])) for r in
                         intents.pending(fl.conn, fl.work, "sync")])
            return real(wt, onto)

        with mock.patch.object(gitw, "rebase", side_effect=spy):
            r = self.run_sync(fl)
        self.assertEqual(r.code, sync.OK, r.lines)
        self.assertEqual(len(seen), 1)
        (state, data), = seen[0]            # al momento del rebase l'intento è già richiesto
        self.assertEqual(state, "requested")
        self.assertEqual((data["from"], data["to"], data["branch"]), (old_head, tip, BRANCH))
        self.assertEqual(self.intent_states(fl, "sync"), ["executed"])

    def test_rebase_in_progress_at_start_refused(self):
        fl = self.pr_open_lab()
        before = head(fl)
        self.advance_main(fl)
        gitdir = fl.git("rev-parse", "--absolute-git-dir", repo=fl.wt)
        (Path(gitdir) / "rebase-merge").mkdir()        # un rebase lasciato a metà
        with mock.patch.object(gitw, "fetch") as fetch, mock.patch.object(gitw, "rebase") as rb:
            r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertIn("rebase in corso", " ".join(r.lines))
        self.assertIn("rebase --abort", " ".join(r.lines))
        fetch.assert_not_called()
        rb.assert_not_called()
        self.assertEqual(head(fl), before)
        self.assertEqual(self.intent_states(fl, "sync"), [])
        self.assertEqual(fl.conn.execute("SELECT state FROM acts WHERE type = 'sync'")
                         .fetchone()[0], "pending")

    def test_ff_only_failure_refuses(self):
        """`merge --ff-only` dei commit remoti che fallisce è un rifiuto (spec 6.5), non un
        blocco: HEAD intatto, intento chiuso con l'errore, atto non consumato, nessun rebase né
        push forzato, nessun blocco aperto."""
        fl = self.pr_open_lab()
        self.advance_main(fl, msg="primo")
        self.update_branch_remote(fl)
        before = head(fl)
        with mock.patch.object(gitw, "merge_ff_only", return_value=False), \
                mock.patch.object(gitw, "rebase") as rb:
            r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        self.assertRegex(" ".join(r.lines), r"merge --ff-only [0-9a-f]{7} non riuscito")
        rb.assert_not_called()
        self.assertEqual(head(fl), before)
        self.assertEqual(self.intent_states(fl, "sync"), ["executed"])
        outcome = fl.conn.execute("SELECT outcome FROM intents WHERE action = 'sync'").fetchone()[0]
        self.assertIn("non riuscito", outcome)
        self.assertEqual(self.intent_states(fl, "force_push"), [])
        self.assertEqual(fl.conn.execute("SELECT state FROM acts WHERE type = 'sync'")
                         .fetchone()[0], "pending")
        self.assertEqual(work(fl)["phase"], "pr_open")
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM blocks WHERE closed IS NULL")
                         .fetchone()[0], 0)

    def test_finish_check_red_after_rebase(self):
        """Dopo un rebase riuscito, un `finish check` rosso dà il messaggio del rosso (m4), non
        quello del rifiuto; il rebase resta fatto e la PR non si aggiorna."""
        fl = self.pr_open_lab()
        tip = self.advance_main(fl)
        with mock.patch.object(sync.finishcheck, "check",
                               return_value=sync.finishcheck.CheckResult(1, ["[no] x"])):
            r = self.run_sync(fl)
        self.assertEqual(r.code, sync.REFUSED, r.lines)
        text = " ".join(r.lines)
        self.assertIn("finish check non è verde dopo il rebase", text)
        self.assertNotIn("ha rifiutato", text)
        self.assertIn("[no] x", text)
        self.assertEqual(work(fl)["work_base_sha"], tip)         # il rebase è stato fatto
        self.assertEqual(work(fl)["phase"], "execution")
        self.assertEqual(self.intent_states(fl, "sync"), ["executed"])
        self.assertEqual(self.calls(fl, "pr", "edit"), [])


class SyncCliTest(SyncCase):
    def test_cli_sync_end_to_end(self):
        fl = self.pr_open_lab()
        tip = self.advance_main(fl)
        acts.record_act(fl.conn, type_="sync", typed_text="/tollgate:sync", session=SESSION,
                        work=fl.work, now=clock.now(), ttl_minutes=10)
        r = fl.cli("sync", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(work(fl)["work_base_sha"], tip)
        self.assertEqual(gitw.remote_sha(fl.wt, BRANCH), head(fl))
        again = fl.cli("sync", cwd=fl.wt)         # senza un nuovo atto: rifiuto
        self.assertEqual(again.returncode, 1, again.stdout + again.stderr)


if __name__ == "__main__":
    unittest.main()
