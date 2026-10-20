import shutil
from pathlib import Path

from tests.flowkit import SESSION
from tests.test_start import StartCase, out
from tollgate_core import acts, clock, effects, git as core_git, phases
from tollgate_flow import gitw

BRANCH = "tg/7-demo"


class ClosingCase(StartCase):
    def lab(self, *, closed=None):
        """Lavoro #7 attivo (ramo `tg/7-demo` nel suo worktree), chiuso con la causa `closed`."""
        fl = self.make(issue=7)
        if closed:
            phases.set_phase(fl.conn, fl.ts.state, fl.work, "closed", closed, now=clock.now())
        return fl

    def act(self, fl, type_, target=None, session=SESSION):
        return acts.record_act(fl.conn, type_=type_, target=target, session=session, work=None,
                               typed_text=f"/tollgate:{type_} {target or ''}".strip(),
                               now=clock.now(), ttl_minutes=10)

    def act_state(self, fl, type_):
        return fl.conn.execute("SELECT state FROM acts WHERE type = ? ORDER BY n DESC",
                               (type_,)).fetchone()[0]

    def branches(self, fl):
        return core_git.local_branches(fl.main)

    def orphan(self, fl, name="tg/7-altro"):
        """Un ramo `tg/*` senza riga nel DB, con il suo worktree."""
        wt = fl.tmp / "wt orfano"
        fl.git("worktree", "add", "-q", "-b", name, str(wt))
        return wt


class GitwWorktreeRemoveTest(ClosingCase):
    def test_removes_clean_worktree_without_force(self):
        fl = self.lab()
        gitw.worktree_remove(fl.main, fl.wt)
        self.assertFalse(fl.wt.exists())
        self.assertIn(BRANCH, self.branches(fl))

    def test_dirty_worktree_raises(self):
        fl = self.lab()
        (fl.wt / "src/app.py").write_text("modificato\n")
        with self.assertRaises(gitw.GitWriteError):
            gitw.worktree_remove(fl.main, fl.wt)
        self.assertTrue(fl.wt.exists())


class AbandonTest(ClosingCase):
    def test_abandon_closes_and_keeps_branch(self):
        fl = self.lab()
        self.act(fl, "abandon", "7")
        r = fl.cli("abandon", "7")
        self.assertEqual(r.returncode, 0, out(r))
        row = phases.get_work(fl.conn, fl.work)
        self.assertEqual((row["phase"], row["closed_reason"]), ("closed", "abandoned"))
        self.assertIn(BRANCH, self.branches(fl))
        self.assertTrue(fl.wt.is_dir())
        self.assertEqual(self.act_state(fl, "abandon"), "consumed")
        self.assertIn("/tollgate:cleanup", out(r))
        self.assertEqual(fl.events("phase_change")[-1]["cause"], "abandoned")

    def test_abandon_needs_act_and_matching_issue(self):
        fl = self.lab()
        r = fl.cli("abandon", "7")
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("serve un atto dell'utente: /tollgate:abandon #7", out(r))
        self.act(fl, "abandon", "8")
        r = fl.cli("abandon", "7")
        self.assertEqual(r.returncode, 1, out(r))
        self.assertEqual(phases.get_work(fl.conn, fl.work)["phase"], "execution")
        self.assertEqual(self.act_state(fl, "abandon"), "pending")

    def test_abandon_without_active_work_refuses(self):
        fl = self.lab(closed="merged")
        self.act(fl, "abandon", "7")
        r = fl.cli("abandon", "7")
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("nessun lavoro attivo per #7", out(r))
        self.assertEqual(self.act_state(fl, "abandon"), "pending")


class CleanupTest(ClosingCase):
    def test_cleanup_needs_act(self):
        fl = self.lab(closed="merged")
        r = fl.cli("cleanup", "--confirm")
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("serve un atto dell'utente: /tollgate:cleanup", out(r))
        self.assertIn(BRANCH, self.branches(fl))

    def test_cleanup_lists_then_deletes_with_confirm(self):
        fl = self.lab(closed="merged")
        self.act(fl, "cleanup")
        first = fl.cli("cleanup")
        self.assertEqual(first.returncode, 3, out(first))
        self.assertIn(BRANCH, out(first))
        self.assertIn(str(fl.wt.resolve()), out(first))
        self.assertIn("--confirm", out(first))
        self.assertEqual(self.act_state(fl, "cleanup"), "pending")
        self.assertIn(BRANCH, self.branches(fl))
        sha = fl.git("rev-parse", BRANCH)
        second = fl.cli("cleanup", "--confirm")
        self.assertEqual(second.returncode, 0, out(second))
        self.assertNotIn(BRANCH, self.branches(fl))
        self.assertFalse(fl.wt.exists())
        self.assertIn(sha, out(second))
        self.assertEqual(self.act_state(fl, "cleanup"), "consumed")
        # un atto consumato non basta a un secondo giro
        self.assertEqual(fl.cli("cleanup", "--confirm").returncode, 1)

    def test_cleanup_from_inside_worktree(self):
        """Da dentro il worktree del ramo chiuso né il worktree né il ramo si toccano."""
        fl = self.lab(closed="merged")
        self.act(fl, "cleanup")
        r = fl.cli("cleanup", "--confirm", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn("sei dentro il worktree", out(r))
        self.assertIn("niente da ripulire", out(r))
        self.assertTrue(fl.wt.is_dir())
        self.assertIn(BRANCH, self.branches(fl))
        self.assertEqual(self.act_state(fl, "cleanup"), "pending")

    def test_cleanup_with_missing_worktree_dir(self):
        """La cartella è sparita ma git la ricorda: si toglie il ramo, senza errori."""
        fl = self.lab(closed="merged")
        sha = fl.git("rev-parse", BRANCH)
        shutil.rmtree(fl.wt)
        self.act(fl, "cleanup")
        listing = fl.cli("cleanup")
        self.assertEqual(listing.returncode, 3, out(listing))
        self.assertIn(f"ramo {BRANCH}", out(listing))
        self.assertNotIn("worktree " + str(fl.wt), out(listing))
        r = fl.cli("cleanup", "--confirm")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertNotIn(BRANCH, self.branches(fl))
        self.assertIn(f"ramo {BRANCH} tolto (puntava a {sha}", out(r))
        self.assertNotIn("Traceback", out(r))
        self.assertEqual(self.act_state(fl, "cleanup"), "consumed")

    def test_cleanup_keeps_active_work(self):
        fl = self.lab()
        self.act(fl, "cleanup")
        r = fl.cli("cleanup", "--confirm")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn(BRANCH, self.branches(fl))
        self.assertTrue(fl.wt.is_dir())
        self.assertEqual(self.act_state(fl, "cleanup"), "pending")

    def test_cleanup_skips_dirty_worktree(self):
        fl = self.lab(closed="abandoned")
        (fl.wt / "src/app.py").write_text("lavoro non committato\n")
        self.act(fl, "cleanup")
        listing = fl.cli("cleanup")
        self.assertIn("modifiche non committate", out(listing))
        r = fl.cli("cleanup", "--confirm")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn("modifiche non committate", out(r))
        self.assertTrue(fl.wt.is_dir())
        self.assertEqual((fl.wt / "src/app.py").read_text(), "lavoro non committato\n")
        self.assertIn(BRANCH, self.branches(fl))

    def test_cleanup_never_touches_branch_of_main_checkout(self):
        fl = self.lab(closed="merged")
        fl.git("worktree", "remove", str(fl.wt))
        fl.git("switch", "-q", BRANCH)
        self.act(fl, "cleanup")
        r = fl.cli("cleanup", "--confirm")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn(BRANCH, self.branches(fl))
        self.assertIn("checkout principale", out(r))

    def test_cleanup_orphans_only_with_flag(self):
        """Riga 55: `WorkExists` dopo `worktree_add` lascia un ramo `tg/7-*` e il suo worktree,
        mentre una riga attiva per lo stesso N punta a un altro ramo."""
        fl = self.lab()
        wt = self.orphan(fl)
        self.act(fl, "cleanup")
        plain = fl.cli("cleanup", "--confirm")
        self.assertEqual(plain.returncode, 0, out(plain))
        self.assertIn("/tollgate:adopt #7", out(plain))
        self.assertIn("tg/7-altro", self.branches(fl))
        self.assertTrue(wt.is_dir())
        self.assertEqual(self.act_state(fl, "cleanup"), "pending")
        listing = fl.cli("cleanup", "--orphans")
        self.assertEqual(listing.returncode, 3, out(listing))
        self.assertIn("tg/7-altro", out(listing))
        self.assertIn("tg/7-altro", self.branches(fl))
        done = fl.cli("cleanup", "--orphans", "--confirm")
        self.assertEqual(done.returncode, 0, out(done))
        self.assertNotIn("tg/7-altro", self.branches(fl))
        self.assertFalse(wt.exists())
        self.assertIn(BRANCH, self.branches(fl))
        self.assertTrue(fl.wt.is_dir())
        self.assertEqual(self.act_state(fl, "cleanup"), "consumed")

    def test_cleanup_does_not_list_branch_of_other_repo_work(self):
        fl = self.lab(closed="merged")
        fl.conn.execute("UPDATE work_items SET repo_key = 'altro/repo'")
        fl.conn.commit()
        self.act(fl, "cleanup")
        r = fl.cli("cleanup", "--confirm")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn(BRANCH, self.branches(fl))     # ora è un orfano: serve --orphans
        self.assertIn("/tollgate:adopt #7", out(r))


class ClosedBranchHintTest(ClosingCase):
    def test_orphan_hint_on_closed_work_points_to_cleanup(self):
        fl = self.lab(closed="merged")
        denied = fl.pre_edit(fl.wt / "src/app.py")
        self.assertEqual(denied.exit, 2)
        self.assertIn("/tollgate:cleanup", denied.stderr)
        self.assertNotIn("/tollgate:adopt", denied.stderr)
        sh = fl.bash(f"echo x > '{fl.wt / 'src/app.py'}'")
        self.assertEqual(sh.exit, 2)
        self.assertIn("/tollgate:cleanup", sh.stderr)
        start = fl.hook({"hook_event_name": "SessionStart", "session_id": "nuova",
                         "cwd": str(fl.wt), "source": "startup"})
        self.assertIn("/tollgate:cleanup", start.stdout)
        self.assertNotIn("/tollgate:adopt", start.stdout)

    def test_orphan_hint_without_closed_work_still_points_to_adopt(self):
        fl = self.lab()
        fl.conn.execute("DELETE FROM work_items")
        fl.conn.commit()
        denied = fl.pre_edit(fl.wt / "src/app.py")
        self.assertEqual(denied.exit, 2)
        self.assertIn("/tollgate:adopt #7", denied.stderr)


class StartConfirmTest(ClosingCase):
    def test_start_confirm_closed_pr_with_other_confirmations(self):
        """PR chiusa e intento pendente chiedono conferma insieme; con --confirm la PR si
        scollega e le conferme restano scritte come «confermato»."""
        fl = self.lab()
        phases.set_pr(fl.conn, fl.work, 1, "https://github.com/prova/flow/pull/1",
                      now=clock.now())
        self.gh(fl, prs=[{"number": 1, "headRefName": BRANCH, "state": "CLOSED",
                          "url": "https://github.com/prova/flow/pull/1", "headRefOid": "x",
                          "mergedAt": None, "body": "", "comments": []}])
        effects.request(fl.conn, key=effects.effect_key("gh issue comment 7", fl.work, None),
                        command="gh issue comment 7", work=fl.work, sha=None, now=clock.now())
        asked = fl.cli("start", "7")
        self.assertEqual(asked.returncode, 3, out(asked))
        confirms = [l for l in out(asked).splitlines() if l.startswith("conferma:")]
        self.assertEqual(len(confirms), 2, out(asked))
        self.assertTrue(any("PR #1 chiusa senza merge" in l for l in confirms))
        self.assertTrue(any("intento e-" in l for l in confirms))
        self.assertEqual(phases.get_work(fl.conn, fl.work)["pr_number"], 1)
        done = fl.cli("start", "7", "--confirm")
        self.assertEqual(done.returncode, 0, out(done))
        row = phases.get_work(fl.conn, fl.work)
        self.assertEqual((row["pr_number"], row["pr_url"]), (None, None))
        self.assertIn("confermato: PR #1 chiusa senza merge", out(done))
        self.assertIn("confermato: intento e-", out(done))
        self.assertEqual(fl.conn.execute("SELECT state FROM intents").fetchone()[0], "requested")
        self.assertEqual(done.stdout.strip().splitlines()[-1],
                         f"prossimo passo: EnterWorktree {fl.wt.resolve()}")
