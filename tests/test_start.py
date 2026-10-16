import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from tests.flowkit import ORIGIN_URL, SESSION, FlowLab
from tests.helpers import BIN
from tests.hookkit import DEFAULT_TOML
from tollgate_core import VERSION, clock, events, phases, sessions
from tollgate_flow import housekeeping

SENTINEL_TITLE = "tollgate: merge non verificato"


def issue(n=7, title="Aggiungi export CSV", **kw):
    data = {"number": n, "title": title, "body": "corpo dell'issue", "state": "open",
            "labels": [], "author_association": "OWNER"}
    data.update(kw)
    return data


def out(r):
    return r.stdout + r.stderr


class StartCase(unittest.TestCase):
    def make(self, **kw):
        fl = FlowLab(**kw)
        self.addCleanup(fl.close)
        self.gh(fl)
        return fl

    def gh(self, fl, issues=None, ctx_state="success", **extra):
        sha = fl.git("rev-parse", "origin/main")
        data = {"auth": True,
                "issues": issues or {"7": issue(7), "8": issue(8, "Altro lavoro"),
                                     "9": issue(9, "Terzo")},
                "prs": [], "issue_list": [],
                "statuses": {sha: {"statuses": [
                    {"context": "tollgate/guard", "state": ctx_state},
                    {"context": "tollgate/verdict", "state": "success"}]}}}
        data.update(extra)
        fl.set_gh(**data)

    def rows(self, fl):
        return fl.conn.execute("SELECT * FROM work_items ORDER BY id").fetchall()

    def refused(self, fl, text, *args):
        r = fl.cli("start", *(args or ("7",)))
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn(text, out(r))
        self.assertEqual(self.rows(fl), [])
        return r


class StartNewTest(StartCase):
    def test_start_creates_work_in_path_with_spaces(self):
        fl = self.make()
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 0, out(r))
        last = r.stdout.strip().splitlines()[-1]
        self.assertTrue(last.startswith("prossimo passo: EnterWorktree "), last)
        (row,) = self.rows(fl)
        self.assertRegex(row["branch"], r"^tg/7-aggiungi-export-csv$")
        wt = Path(row["worktree"])
        self.assertEqual(last, f"prossimo passo: EnterWorktree {wt}")
        self.assertEqual(wt.parent, fl.main / ".claude" / "worktrees")
        self.assertIn(" ", str(wt.parent.parent.parent))
        self.assertEqual(fl.git("rev-parse", "--abbrev-ref", "HEAD", repo=wt), row["branch"])
        self.assertEqual((row["level"], row["phase"]), ("L0", "execution"))
        self.assertEqual(row["work_base_sha"], fl.git("rev-parse", "origin/main"))
        self.assertEqual(row["gate_mode"], "protected")
        self.assertEqual(json.loads(row["sessions"]), [SESSION])
        self.assertTrue((fl.ts.dir / "bound" / SESSION).is_file())
        active = "\n".join(p.read_text() for p in (fl.ts.dir / "active").iterdir())
        self.assertIn(str(wt), active.splitlines())
        self.assertTrue(list((fl.ts.dir / "backup").glob("*-start.db")))
        self.assertEqual(fl.git("config", "--get", "tollgate.defaultBranch"), "main")

    def test_worktree_branch_has_no_upstream(self):
        fl = self.make()
        self.assertEqual(fl.cli("start", "7").returncode, 0)
        (row,) = self.rows(fl)
        r = subprocess.run(["git", "-C", str(fl.main), "config", "--get",
                            f"branch.{row['branch']}.merge"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_second_start_keeps_excludes_once_and_level_l1(self):
        fl = self.make()
        self.assertEqual(fl.cli("start", "7").returncode, 0)
        r = fl.cli("start", "#8", "--level", "L1")
        self.assertEqual(r.returncode, 0, out(r))
        row = self.rows(fl)[1]
        self.assertEqual((row["issue"], row["level"], row["phase"]), (8, "L1", "plan"))
        exclude = Path(fl.git("rev-parse", "--git-common-dir"))
        exclude = (fl.main / exclude if not exclude.is_absolute() else exclude) / "info" / "exclude"
        lines = exclude.read_text().splitlines()
        for want in (".claude/worktrees/", ".tollgate-run/",
                     "docs/superpowers/reviews/*/checkpoint.md"):
            self.assertEqual(lines.count(want), 1, lines)
        self.assertEqual(fl.git("status", "--porcelain"), "")

    def test_start_from_a_linked_worktree_uses_main_checkout(self):
        fl = self.make()
        self.assertEqual(fl.cli("start", "7").returncode, 0)
        wt = Path(self.rows(fl)[0]["worktree"])
        r = fl.cli("start", "8", cwd=wt)
        self.assertEqual(r.returncode, 0, out(r))
        self.assertEqual(Path(self.rows(fl)[1]["worktree"]).parent, fl.main / ".claude" / "worktrees")

    def test_outside_a_git_repo_refuses(self):
        fl = self.make()
        with tempfile.TemporaryDirectory() as d:
            r = fl.cli("start", "7", cwd=d)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("repo git", out(r))

    def test_refusals(self):
        def not_active(fl):
            fl.git("rm", "-q", "tollgate.toml")
            fl.git("commit", "-qm", "senza toml")
            fl.git("push", "-q", "origin", "main")

        def superpowers(version):
            def f(fl):
                reg = fl.home / ".claude/plugins/installed_plugins.json"
                data = json.loads(reg.read_text())
                data["plugins"]["superpowers@claude-plugins-official"][0]["version"] = version
                reg.write_text(json.dumps(data))
            return f

        def no_auth(fl):
            self.gh(fl, auth=False)

        def not_github(fl):
            fl.git("config", "remote.origin.url", "https://gitlab.com/prova/flow.git")
            fl.git("config", f"url.{fl.origin}.insteadOf", "https://gitlab.com/prova/flow.git")

        def offline(fl):
            fl.git("config", "remote.origin.url", str(fl.tmp / "non-esiste.git"))

        cases = [
            ("non attivo", dict(), not_active),
            ("tollgate-run.yml", dict(gate=False), None),
            ("6.3.0", dict(), superpowers("6.3.0")),
            ("8.0.0", dict(), superpowers("8.0.0")),
            ("gh", dict(), no_auth),
            ("github.com", dict(), not_github),
            ("senza rete non si avvia un lavoro nuovo", dict(), offline),
        ]
        for text, kw, setup in cases:
            with self.subTest(text):
                fl = self.make(**kw)
                if setup:
                    setup(fl)
                self.refused(fl, text)
                self.assertFalse((fl.main / ".claude" / "worktrees").exists())
                self.assertEqual([b for b in fl.git("branch", "--list", "tg/*").split()], [])

    def test_superpowers_missing_refuses(self):
        fl = self.make()
        (fl.home / ".claude/plugins/installed_plugins.json").unlink()
        self.refused(fl, "Superpowers")

    def test_refusals_are_collected(self):
        fl = self.make(gate=False)
        reg = fl.home / ".claude/plugins/installed_plugins.json"
        data = json.loads(reg.read_text())
        data["plugins"]["superpowers@claude-plugins-official"][0]["version"] = "6.3.0"
        reg.write_text(json.dumps(data))
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("6.3.0", out(r))
        self.assertIn("tollgate-run.yml", out(r))

    def test_confirmations(self):
        fl = self.make()
        self.gh(fl, issues={"7": issue(7, state="closed")})
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 3, out(r))
        self.assertIn("conferma", out(r))
        self.assertIn("--confirm", out(r))
        self.assertEqual(self.rows(fl), [])
        self.assertFalse((fl.main / ".claude" / "worktrees").exists())
        self.assertEqual(fl.git("branch", "--list", "tg/*"), "")
        r = fl.cli("start", "7", "--confirm")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertEqual(len(self.rows(fl)), 1)

    def test_default_branch_status_not_green_asks_confirmation(self):
        for bad in ("failure", "pending", "error"):
            with self.subTest(bad):
                fl = self.make()
                self.gh(fl, ctx_state=bad)
                r = fl.cli("start", "7")
                self.assertEqual(r.returncode, 3, out(r))
                self.assertIn("tollgate/guard", out(r))
                self.assertEqual(self.rows(fl), [])
                self.assertEqual(fl.cli("start", "7", "--confirm").returncode, 0)

    def test_warnings_do_not_block(self):
        fl = self.make()
        (fl.main / ".github/tollgate/VERSION").write_text("0.0.9\n")
        fl.git("add", "-A")
        fl.git("commit", "-qm", "versione vecchia")
        fl.git("push", "-q", "origin", "main")
        (fl.main / "sporco.txt").write_text("x")
        self.gh(fl, statuses={fl.git("rev-parse", "origin/main"): {"statuses": []}})
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 0, out(r))
        o = out(r)
        self.assertIn("0.0.9", o)
        self.assertIn(VERSION, o)
        self.assertIn("modifiche non committate", o)
        self.assertIn("stati di tollgate assenti", o)

    def test_unreadable_statuses_are_a_warning(self):
        fl = self.make()
        self.gh(fl, statuses={})
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn("non leggibili", out(r))

    def test_status_other_contexts_only_is_a_warning(self):
        fl = self.make()
        sha = fl.git("rev-parse", "origin/main")
        self.gh(fl, statuses={sha: {"statuses": [{"context": "ci/altro", "state": "failure"}]}})
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn("stati di tollgate assenti", out(r))

    def test_branch_without_row_proposes_adopt(self):
        fl = self.make()
        fl.git("branch", "tg/7-x")
        r = self.refused(fl, "/tollgate:adopt #7")
        self.assertEqual(fl.git("branch", "--list", "tg/7-*").split(), ["tg/7-x"])
        fl = self.make()
        fl.git("push", "-q", "origin", "main:refs/heads/tg/7-y")
        self.refused(fl, "/tollgate:adopt #7")
        self.assertEqual(fl.git("branch", "--list", "tg/7-*"), "")
        fl = self.make()
        self.gh(fl, prs=[{"headRefName": "tg/7-z", "number": 3, "state": "OPEN"},
                         {"headRefName": "tg/70-altro", "number": 4, "state": "OPEN"}])
        self.refused(fl, "/tollgate:adopt #7")
        fl = self.make()
        self.gh(fl, prs=[{"headRefName": "tg/70-altro", "number": 4, "state": "OPEN"}])
        self.assertEqual(fl.cli("start", "7").returncode, 0)

    def test_branch_refusal_comes_before_confirmation(self):
        fl = self.make()
        self.gh(fl, issues={"7": issue(7, state="closed")})
        fl.git("branch", "tg/7-x")
        self.refused(fl, "/tollgate:adopt #7")

    def test_level_from_labels_and_author(self):
        fl = self.make()
        self.gh(fl, issues={"7": issue(7, labels=[{"name": "security"}]),
                            "8": issue(8, author_association="NONE"),
                            "9": issue(9, labels=[{"name": "ui"}]),
                            "10": issue(10, author_association="CONTRIBUTOR")})
        levels = {}
        for n, extra in ((7, ()), (8, ()), (9, ("--level", "L2")), (10, ())):
            r = fl.cli("start", str(n), *extra)
            self.assertEqual(r.returncode, 0, out(r))
        for row in self.rows(fl):
            levels[row["issue"]] = (row["level"], row["phase"])
        self.assertEqual(levels, {7: ("L2", "spec_audit"), 8: ("L2", "spec_audit"),
                                  9: ("L2", "spec_audit"), 10: ("L2", "spec_audit")})

    def test_level_trusted_authors_keep_l0(self):
        fl = self.make()
        self.gh(fl, issues={"7": issue(7, author_association="MEMBER"),
                            "8": issue(8, author_association="COLLABORATOR"),
                            "9": issue(9, labels=[{"name": "ui"}])})
        for n in (7, 8, 9):
            self.assertEqual(fl.cli("start", str(n)).returncode, 0)
        self.assertEqual({r["level"] for r in self.rows(fl)}, {"L0"})

    def test_detect_mode_warning(self):
        fl = self.make(toml=DEFAULT_TOML.replace("protected", "detect"))
        self.gh(fl, issue_list=[{"number": 3, "title": SENTINEL_TITLE},
                                {"number": 4, "title": "Altra issue qualunque"}])
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertIn("modalità rilevazione: il merge non è impedito", out(r))
        self.assertIn(SENTINEL_TITLE, out(r))
        self.assertNotIn("Altra issue qualunque", out(r))
        self.assertEqual(self.rows(fl)[0]["gate_mode"], "detect")

    def test_protected_mode_has_no_detect_warning(self):
        fl = self.make()
        r = fl.cli("start", "7")
        self.assertNotIn("rilevazione", out(r))

    def test_hostile_issue_title_and_body(self):
        pwned = Path("/tmp/PWNED")
        if pwned.exists():
            self.skipTest("/tmp/PWNED esiste già")
        fl = self.make()
        title = "`$(touch /tmp/PWNED)` \";rm -rf ~\""
        body = "testo\n```\nrm -rf ~\n````\n@utente\n"
        self.gh(fl, issues={"7": issue(7, title, body=body, labels=[{"name": "ui`x"}])})
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 0, out(r))
        self.assertFalse(pwned.exists())
        (row,) = self.rows(fl)
        self.assertRegex(row["branch"], r"^tg/7-[a-z0-9-]+$")
        self.assertRegex(Path(row["worktree"]).name, r"^tg-7-[a-z0-9-]+$")
        text = (Path(row["worktree"]) / ".tollgate-run" / "7" / "issue.md").read_text()
        longest = max(len(x) for x in re.findall(r"`+", body + title + "ui`x"))
        fences = [m for m in re.finditer(r"^(`{3,})\s*$", text, re.M)]
        self.assertGreater(len(fences[0].group(1)), longest)
        fences = [m for m in fences if m.group(1) == fences[0].group(1)]
        self.assertEqual(len(fences), 2, text)
        self.assertLess(text.index("DATO NON FIDATO"), fences[0].start())
        between = text[fences[0].end():fences[1].start()]
        self.assertIn("@utente", between)
        self.assertIn("rm -rf ~", between)
        self.assertIn(title, between)
        for call in fl.gh_calls():
            self.assertNotIn("touch", json.dumps(call))
            self.assertNotIn(title, json.dumps(call))
        self.assertFalse(pwned.exists())

    def test_no_session_signal_refuses(self):
        fl = self.make()
        r = subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), "start", "7"],
                           cwd=fl.main, env=fl.env(), capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("sessione non riconosciuta", out(r))
        self.assertEqual(self.rows(fl), [])

    def test_stale_signal_refuses(self):
        fl = self.make()
        sessions.note_cli_call(fl.ts.state, SESSION, str(fl.main), ["start", "7"],
                               now=clock.now() - timedelta(seconds=300))
        r = subprocess.run([sys.executable, "-B", str(BIN / "tollgate"), "start", "7"],
                           cwd=fl.main, env=fl.env(), capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("sessione non riconosciuta", out(r))

    def test_invalid_issue_number(self):
        fl = self.make()
        r = fl.cli("start", "sette")
        self.assertEqual(r.returncode, 2)

    def test_resume_is_not_available_yet(self):
        fl = self.make(issue=7)
        r = fl.cli("start", "7")
        self.assertEqual(r.returncode, 1, out(r))
        self.assertIn("ripresa", out(r))
        self.assertEqual(len(self.rows(fl)), 1)


class HousekeepingTest(StartCase):
    def age(self, path, hours):
        t = (clock.now() - timedelta(hours=hours)).timestamp()
        os.utime(path, (t, t))

    def test_housekeeping(self):
        fl = self.make(issue=9)
        state = fl.ts.state
        now = clock.now()
        sessions.mark_bound(state, SESSION)
        sessions.mark_bound(state, "morta")
        sessions.mark_bound(state, "viva")
        sessions.touch(fl.conn, "viva", now=now)
        old_event = events.record_event(fl.conn, "off", {}, now=now - timedelta(days=200))
        new_event = events.record_event(fl.conn, "on", {}, now=now)
        d = fl.ts.dir
        for rel, hours in (("backup/.tmp-x", 2), ("backup/.tmp-fresco", 0),
                           ("backup/tollgate-vecchia.db", 5000),
                           ("ctx/vecchio.json", 24 * 40), ("ctx/nuovo.json", 1),
                           ("logs/vecchio.log", 24 * 40), ("logs/nuovo.log", 1),
                           ("cli/vecchio.json", 30), ("cli/nuovo.json", 1)):
            p = d / rel
            p.parent.mkdir(exist_ok=True)
            p.write_text("x")
            self.age(p, hours)
        cfg = self.cfg(fl)
        warnings = housekeeping.run(fl.conn, state, cfg, now=now)
        self.assertEqual(warnings, [])
        bound = sorted(p.name for p in (d / "bound").iterdir())
        self.assertEqual(bound, sorted([SESSION, "viva"]))
        self.assertFalse((d / "backup/.tmp-x").exists())
        self.assertTrue((d / "backup/.tmp-fresco").exists())
        self.assertTrue((d / "backup/tollgate-vecchia.db").exists())
        self.assertFalse((d / "ctx/vecchio.json").exists())
        self.assertTrue((d / "ctx/nuovo.json").exists())
        self.assertFalse((d / "logs/vecchio.log").exists())
        self.assertTrue((d / "logs/nuovo.log").exists())
        self.assertFalse((d / "cli/vecchio.json").exists())
        self.assertTrue((d / "cli/nuovo.json").exists())
        seqs = [r[0] for r in fl.conn.execute("SELECT seq FROM events")]
        self.assertNotIn(old_event, seqs)
        self.assertIn(new_event, seqs)

    def test_housekeeping_without_directories(self):
        fl = self.make(issue=9)
        self.assertEqual(housekeeping.run(fl.conn, fl.ts.state, self.cfg(fl), now=clock.now()),
                         [])

    def cfg(self, fl):
        from tollgate_core import config
        return config.load_config(fl.ts.state, fl.main, "origin/main")

    def test_prune_bound_keeps_sessions_of_active_work_only(self):
        fl = self.make(issue=9)
        state = fl.ts.state
        sessions.mark_bound(state, SESSION)
        w = phases.get_work(fl.conn, fl.work)
        phases.set_phase(fl.conn, state, w["id"], "closed", "abandoned", now=clock.now())
        sessions.prune_bound(fl.conn, state, now=clock.now(), stale_minutes=30)
        self.assertFalse((fl.ts.dir / "bound" / SESSION).exists())


if __name__ == "__main__":
    unittest.main()
