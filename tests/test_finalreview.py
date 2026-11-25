import json
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from unittest import mock

from tests.flowkit import PLAN, FlowLab, plan_text
from tests.helpers import ROOT, git
from tests.hookkit import DEFAULT_TOML
from tollgate_core import git as core_git, phases, reviews
from tollgate_flow import finalreview, init

REVIEWER = "tollgate:final-reviewer"
SPEC = "probe:final-security"
SEC_TOML = DEFAULT_TOML + """
[profiles.security]
paths = ["src/**"]
final_specialist = "probe:final-security"
checklist = "nessun segreto nel codice"
"""


class FinalCase(unittest.TestCase):
    def lab(self, toml=DEFAULT_TOML, level="L1", extra=None):
        """Lavoro in fase review: piano registrato, un commit, finish_sha = HEAD."""
        fl = FlowLab(issue=7, phase="plan", toml=toml)
        self.addCleanup(fl.close)
        self.fl = fl
        fl.register_plan(tasks=1)
        fl.commit(PLAN, plan_text(tasks=1), "piano")
        fl.commit("src/app.py", "def somma(a, b):\n    return b + a\n", "somma")
        for path, text in (extra or {}).items():
            fl.commit(path, text, f"aggiunge {path}")
        fl.close_tasks()
        self.advance("review")
        if level == "L0":       # un lavoro L0 non ha piano né task: solo il livello conta qui
            fl.conn.execute("UPDATE work_items SET level = 'L0' WHERE id = ?", (fl.work,))
            fl.conn.commit()
        elif level != "L1":
            phases.set_level(fl.conn, fl.work, level, now=fl.now)
        return fl

    def advance(self, to):
        fl = self.fl
        phases.set_phase(fl.conn, fl.ts.state, fl.work, to, "finish_check_green", now=fl.now)
        phases.set_finish(fl.conn, fl.work, core_git.head(fl.wt),
                          {"items": {}, "manual": []}, now=fl.now)

    def prepare(self):
        return finalreview.prepare(self.fl.ts.state, self.fl.wt, now=self.fl.now)

    def cycle(self, n=None):
        fl = self.fl
        return reviews.latest(fl.conn, fl.work) if n is None else fl.conn.execute(
            "SELECT * FROM review_cycles WHERE work = ? AND number = ?",
            (fl.work, n)).fetchone()

    def run_dir(self):
        return self.fl.wt / ".tollgate-run" / "7"


class PrepareNewCycleTest(FinalCase):
    def test_new_cycle_l1_one_reviewer(self):
        fl = self.lab()
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [REVIEWER])
        self.assertEqual(r.stage, "review")
        c = self.cycle()
        self.assertEqual((c["number"], c["stage"], c["sha"], c["counted"]),
                         (1, "review", core_git.head(fl.wt), 0))
        self.assertEqual(json.loads(c["reviewers"]), [REVIEWER])
        brief = self.run_dir() / "final-1.md"
        self.assertEqual(r.launches[0].brief, brief)
        text = brief.read_text()
        self.assertIn(c["code"], text)
        self.assertIn(c["sha"], text)
        self.assertTrue((self.run_dir() / "final-1.diff").exists())
        self.assertIn(f'agente: {REVIEWER} brief: "{brief}"', r.lines)
        self.assertTrue(r.lines[-1].startswith("prossimo passo:"))
        self.assertIn(" ", str(brief))      # il banco ha spazi nel percorso

    def test_l2_adds_final_specialists(self):
        self.lab(toml=SEC_TOML, level="L2")
        r = self.prepare()
        self.assertEqual([x.agent_type for x in r.launches], [REVIEWER, SPEC])
        self.assertEqual(json.loads(self.cycle()["reviewers"]), [REVIEWER, SPEC])
        spec_brief = self.run_dir() / "final-1-security.md"
        self.assertEqual(r.launches[1].brief, spec_brief)
        text = spec_brief.read_text()
        self.assertIn(SPEC, text)
        self.assertIn("nessun segreto nel codice", text)
        self.assertIn(self.cycle()["code"], text)

    MIGRATION = {"supabase/migrations/20260101000000_init.sql": "create table t (id int);\n"}

    def real_database_toml(self):
        """Il frammento vero di `database`, come lo propone `init` in un repo temporaneo con una
        migrazione e gli agenti veri del plugin (decisione 10 di B7)."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "templates" / "profiles").mkdir(parents=True)
        shutil.copy(ROOT / "templates" / "profiles" / "database.toml",
                    root / "templates" / "profiles" / "database.toml")
        (root / "skills" / "rules-database").mkdir(parents=True)
        shutil.copy(ROOT / "skills" / "rules-database" / "SKILL.md",
                    root / "skills" / "rules-database" / "SKILL.md")
        (root / "agents").mkdir()
        for name in ("implementer-database", "reviewer-database", "final-database"):
            shutil.copy(ROOT / "agents" / f"{name}.md", root / "agents" / f"{name}.md")
        got = init.profile_blocks({"supabase/migrations/20260101000000_init.sql": 10},
                                  DEFAULT_TOML, root)
        self.assertIn("[profiles.database]", got.text)
        return DEFAULT_TOML + got.text

    def test_real_database_specialist_in_l2(self):
        self.lab(toml=self.real_database_toml(), level="L2", extra=self.MIGRATION)
        r = self.prepare()
        specialist = "tollgate:final-database"
        self.assertEqual([x.agent_type for x in r.launches], [REVIEWER, specialist])
        self.assertEqual(json.loads(self.cycle()["reviewers"]), [REVIEWER, specialist])
        brief = self.run_dir() / "final-1-database.md"
        self.assertEqual(r.launches[1].brief, brief)
        text = brief.read_text()
        self.assertIn("Lista di controllo dell'area", text)
        self.assertIn("migrazioni reversibili e dati esistenti", text)
        self.assertIn(specialist, text)

    def test_real_database_specialist_not_in_l1(self):
        self.lab(toml=self.real_database_toml(), extra=self.MIGRATION)
        self.assertEqual([x.agent_type for x in self.prepare().launches], [REVIEWER])

    AUTH = {"app/auth/x.py": "def consentito(utente):\n    return utente is not None\n"}

    def real_toml(self, areas, files):
        """I frammenti veri di `areas`, come li propone `init` in un repo temporaneo con i file
        `files` e le skill e gli agenti veri del plugin (decisione 10 di C2)."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "templates" / "profiles").mkdir(parents=True)
        (root / "agents").mkdir()
        for area in areas:
            shutil.copy(ROOT / "templates" / "profiles" / f"{area}.toml",
                        root / "templates" / "profiles" / f"{area}.toml")
            (root / "skills" / f"rules-{area}").mkdir(parents=True)
            shutil.copy(ROOT / "skills" / f"rules-{area}" / "SKILL.md",
                        root / "skills" / f"rules-{area}" / "SKILL.md")
            for kind in ("implementer", "reviewer", "final"):
                shutil.copy(ROOT / "agents" / f"{kind}-{area}.md",
                            root / "agents" / f"{kind}-{area}.md")
        got = init.profile_blocks({f: 10 for f in files}, DEFAULT_TOML, root)
        for area in areas:
            self.assertIn(f"[profiles.{area}]", got.text)
        return DEFAULT_TOML + got.text

    def test_real_security_specialist_in_l2(self):
        self.lab(toml=self.real_toml(("security",), self.AUTH), level="L2", extra=self.AUTH)
        r = self.prepare()
        specialist = "tollgate:final-security"
        self.assertEqual([x.agent_type for x in r.launches], [REVIEWER, specialist])
        self.assertEqual(json.loads(self.cycle()["reviewers"]), [REVIEWER, specialist])
        brief = self.run_dir() / "final-1-security.md"
        self.assertEqual(r.launches[1].brief, brief)
        text = brief.read_text()
        self.assertIn("Lista di controllo dell'area", text)
        self.assertIn("accesso negato provato da un test", text)
        self.assertIn(specialist, text)

    def test_real_security_specialist_not_in_l1(self):
        self.lab(toml=self.real_toml(("security",), self.AUTH), extra=self.AUTH)
        self.assertEqual([x.agent_type for x in self.prepare().launches], [REVIEWER])

    def test_real_security_and_database_specialists_together(self):
        """Un lavoro L2 che tocca un file di `security` e una migrazione lancia tutti e due gli
        specialisti, ognuno con il suo brief e la sua lista di controllo."""
        files = {**self.AUTH, **self.MIGRATION}
        self.lab(toml=self.real_toml(("database", "security"), files), level="L2", extra=files)
        r = self.prepare()
        db, sec = "tollgate:final-database", "tollgate:final-security"
        self.assertEqual(sorted(x.agent_type for x in r.launches[1:]), [db, sec])
        self.assertEqual(r.launches[0].agent_type, REVIEWER)
        self.assertEqual(sorted(json.loads(self.cycle()["reviewers"])), sorted([REVIEWER, db, sec]))
        db_text = (self.run_dir() / "final-1-database.md").read_text()
        sec_text = (self.run_dir() / "final-1-security.md").read_text()
        self.assertIn("migrazioni reversibili e dati esistenti", db_text)
        self.assertNotIn("accesso negato provato da un test", db_text)
        self.assertIn("accesso negato provato da un test", sec_text)
        self.assertNotIn("migrazioni reversibili e dati esistenti", sec_text)
        general = (self.run_dir() / "final-1.md").read_text()
        self.assertIn("migrazioni reversibili e dati esistenti", general)
        self.assertIn("accesso negato provato da un test", general)

    def test_l1_has_no_specialists(self):
        self.lab(toml=SEC_TOML)
        self.assertEqual([x.agent_type for x in self.prepare().launches], [REVIEWER])

    def test_models_override_in_launch_line(self):
        self.lab(toml=DEFAULT_TOML + '[review]\nmodels = {"tollgate:final-reviewer" = "opus"}\n')
        r = self.prepare()
        self.assertEqual(r.launches[0].model, "opus")
        self.assertTrue(any(x.startswith("agente: ") and x.endswith(' model: opus')
                            for x in r.lines))

    def test_l0_and_component_off_launch_nothing(self):
        self.lab(level="L0")
        r = self.prepare()
        self.assertEqual(r.launches, [])
        self.assertIn("in L0 non c'è revisione finale", "\n".join(r.lines))
        self.assertIsNone(self.cycle())
        self.lab(toml=DEFAULT_TOML + "[components]\nfinal_review = false\n")
        r = self.prepare()
        self.assertEqual(r.launches, [])
        self.assertIn("revisione finale spenta", "\n".join(r.lines))
        self.assertIsNone(self.cycle())

    def test_review_unverified_launches_nothing(self):
        fl = self.lab()
        phases.set_review_unverified(fl.conn, fl.work, now=fl.now)
        r = self.prepare()
        self.assertEqual(r.launches, [])
        self.assertIn("revisione non verificata", "\n".join(r.lines))
        self.assertIn("finish open-pr", r.lines[-1])
        self.assertIsNone(self.cycle())

    def test_head_differs_from_finish_sha_refused(self):
        fl = self.lab()
        fl.commit("src/app.py", "x = 1\n", "altro")
        with self.assertRaises(finalreview.ReviewError) as cm:
            self.prepare()
        self.assertIn("/tollgate:finish", str(cm.exception))
        self.assertIsNone(self.cycle())

    def test_unreadable_plan_refused_before_opening_cycle(self):
        fl = self.lab()
        fl.conn.execute("UPDATE work_items SET plan_sha = ? WHERE id = ?", ("0" * 40, fl.work))
        fl.conn.commit()
        with self.assertRaises(finalreview.ReviewError):
            self.prepare()
        self.assertEqual(reviews.count(fl.conn, fl.work), 0)

    def test_wrong_phase_refused(self):
        fl = self.lab()
        phases.set_phase(fl.conn, fl.ts.state, fl.work, "execution", "needs_fix", now=fl.now)
        with self.assertRaises(finalreview.ReviewError):
            self.prepare()


class PrepareBriefTest(FinalCase):
    def test_issue_file_named_only_if_start_wrote_it(self):
        self.lab()
        self.assertFalse((self.run_dir() / "issue.md").exists())     # il banco non lo scrive
        self.prepare()
        self.assertNotIn("issue.md", (self.run_dir() / "final-1.md").read_text())
        (self.run_dir() / "issue.md").write_text("testo dell'issue\n")
        self.prepare()                  # riprende il ciclo e riscrive il brief
        self.assertIn("Issue: `" + str(self.run_dir() / "issue.md") + "`",
                      (self.run_dir() / "final-1.md").read_text())

    def test_rebase_explained_in_brief(self):
        fl = self.lab()
        self.prepare()
        old = self.cycle()["sha"]
        git(fl.main, "checkout", "-q", "-b", "avanti", fl.base)
        (fl.main / "altro.txt").write_text("x\n")
        git(fl.main, "add", "altro.txt")
        git(fl.main, "commit", "-q", "-m", "avanti")
        new_base = git(fl.main, "rev-parse", "HEAD")
        git(fl.wt, "rebase", "-q", "--onto", new_base, fl.base)
        new_head = core_git.head(fl.wt)
        phases.set_base(fl.conn, fl.work, new_base, cause="rebase", now=fl.now)
        phases.set_finish(fl.conn, fl.work, new_head, {"items": {}, "manual": []}, now=fl.now)
        r = self.prepare()
        self.assertEqual(self.cycle()["number"], 1)             # stesso ciclo, stesso patch-id
        self.assertEqual(len(r.launches), 1)
        self.assertIn(f"Il ciclo è stato aperto su `{old}`; HEAD è `{new_head}` dopo un rebase "
                      "senza modifiche di contenuto: rivedi il diff di HEAD.",
                      (self.run_dir() / "final-1.md").read_text())


class PrepareResumeTest(FinalCase):
    def test_resume_open_cycle_keeps_code(self):
        self.lab(toml=SEC_TOML, level="L2")
        first = self.prepare()
        code = self.cycle()["code"]
        again = self.prepare()
        self.assertEqual(reviews.count(self.fl.conn, self.fl.work), 1)
        self.assertEqual(self.cycle()["code"], code)
        self.assertEqual([x.agent_type for x in again.launches],
                         [x.agent_type for x in first.launches])
        reviews.add_report(self.fl.conn, self.fl.work, 1, source=REVIEWER, outcome="ok",
                           findings=[], rejected=[], blocking_rules=set(), known_rules=set(),
                           now=self.fl.now)
        third = self.prepare()
        self.assertEqual([x.agent_type for x in third.launches], [SPEC])
        self.assertTrue((self.run_dir() / "final-1-security.md").exists())

    def test_verify_stage_launches_verifier(self):
        fl = self.lab()
        self.prepare()
        c = self.cycle()
        f = {"severity": "major", "confidence": 0.9, "file": "src/app.py", "line": 2,
             "rule": "R-1", "text": "manca lo zero ``` qui"}
        reviews.add_report(fl.conn, fl.work, 1, source=REVIEWER, outcome="needs_fix",
                           findings=[f], rejected=[], blocking_rules=set(), known_rules=set(),
                           now=fl.now)
        r = self.prepare()
        self.assertEqual(r.stage, "verify")
        self.assertEqual([x.agent_type for x in r.launches], ["tollgate:finding-verifier"])
        brief = self.run_dir() / "verify-1.md"
        self.assertEqual(r.launches[0].brief, brief)
        text = brief.read_text()
        self.assertIn(c["code"], text)
        self.assertIn("f-1-1", text)
        self.assertIn("manca lo zero ``` qui", text)
        self.assertEqual(self.cycle()["stage"], "verify")

    def test_verify_stage_without_findings_closes_cycle(self):
        fl = self.lab()
        self.prepare()
        reviews.add_report(fl.conn, fl.work, 1, source=REVIEWER, outcome="ok", findings=[],
                           rejected=[], blocking_rules=set(), known_rules=set(), now=fl.now)
        r = self.prepare()
        self.assertEqual(r.launches, [])
        self.assertEqual((self.cycle()["stage"], self.cycle()["outcome"]), ("closed", "ok"))
        self.assertIn("finish open-pr", r.lines[-1])

    def test_open_cycle_on_other_sha_superseded(self):
        fl = self.lab()
        self.prepare()
        fl.commit("src/app.py", "def somma(a, b):\n    return a + b + 0\n", "altro")
        phases.set_finish(fl.conn, fl.work, core_git.head(fl.wt), {"items": {}, "manual": []},
                          now=fl.now)
        r = self.prepare()
        old, new = self.cycle(1), self.cycle(2)
        self.assertEqual((old["outcome"], old["stage"], old["counted"]),
                         ("superseded", "closed", 0))
        self.assertEqual((new["stage"], new["sha"]), ("review", core_git.head(fl.wt)))
        self.assertNotEqual(old["code"], new["code"])
        self.assertEqual(len(r.launches), 1)


class PrepareClosedTest(FinalCase):
    def close_ok(self):
        fl = self.fl
        self.prepare()
        reviews.add_report(fl.conn, fl.work, 1, source=REVIEWER, outcome="ok", findings=[],
                           rejected=[], blocking_rules=set(), known_rules=set(), now=fl.now)
        reviews.close_cycle(fl.conn, fl.ts.state, fl.work, 1, now=fl.now)

    def test_already_passed_same_sha(self):
        self.lab()
        self.close_ok()
        r = self.prepare()
        self.assertEqual(r.launches, [])
        self.assertIn("revisione già superata (ciclo 1)", "\n".join(r.lines))
        self.assertIn("finish open-pr", r.lines[-1])
        self.assertEqual(reviews.count(self.fl.conn, self.fl.work), 1)

    def test_same_patch_id_after_rebase_no_new_cycle(self):
        fl = self.lab()
        self.close_ok()
        # il lavoro viene riscritto su una base avanzata: SHA nuovo, stesso contenuto
        git(fl.main, "checkout", "-q", "-b", "avanti", fl.base)
        (fl.main / "altro.txt").write_text("x\n")
        git(fl.main, "add", "altro.txt")
        git(fl.main, "commit", "-q", "-m", "avanti")
        new_base = git(fl.main, "rev-parse", "HEAD")
        git(fl.wt, "rebase", "-q", "--onto", new_base, fl.base)
        new_head = core_git.head(fl.wt)
        self.assertNotEqual(new_head, self.cycle()["sha"])
        phases.set_base(fl.conn, fl.work, new_base, cause="rebase", now=fl.now)
        phases.set_finish(fl.conn, fl.work, new_head, {"items": {}, "manual": []}, now=fl.now)
        r = self.prepare()
        self.assertEqual(r.launches, [])
        self.assertIn("revisione già superata (ciclo 1)", "\n".join(r.lines))
        self.assertEqual(reviews.count(fl.conn, fl.work), 1)

    def test_closed_needs_fix_opens_next_cycle(self):
        fl = self.lab()
        self.prepare()
        f = {"severity": "major", "confidence": 0.9, "file": "src/app.py", "line": 2,
             "rule": "R-1", "text": "x"}
        reviews.add_report(fl.conn, fl.work, 1, source=REVIEWER, outcome="needs_fix",
                           findings=[f], rejected=[], blocking_rules=set(), known_rules=set(),
                           now=fl.now)
        rows = reviews.to_verify(fl.conn, fl.work, 1, max_findings=15, now=fl.now)
        reviews.apply_verification(fl.conn, fl.work, 1,
                                   [{"id": rows[0]["id"], "verification": "confirmed",
                                     "reason": "ok"}], now=fl.now)
        self.assertEqual(reviews.close_cycle(fl.conn, fl.ts.state, fl.work, 1, now=fl.now),
                         "needs_fix")
        fl.commit("src/app.py", "def somma(a, b):\n    return a + b\n", "fix")
        self.advance("review")
        r = self.prepare()
        self.assertEqual(len(r.launches), 1)
        self.assertEqual(self.cycle()["number"], 2)

    def test_ninth_cycle_refused(self):
        fl = self.lab()
        for n in range(1, 9):
            reviews.open_cycle(fl.conn, fl.work, sha=f"s{n}", patch_id=f"p{n}", code="c",
                               reviewers=[REVIEWER], now=fl.now)
            reviews.supersede(fl.conn, fl.work, n, now=fl.now)
        with self.assertRaises(finalreview.ReviewError) as cm:
            self.prepare()
        self.assertIn("/tollgate:approve unverified-review", str(cm.exception))
        self.assertEqual(reviews.count(fl.conn, fl.work), 8)


class CliTest(FinalCase):
    def test_cli_prints_launch_lines_and_refuses_with_exit_1(self):
        fl = self.lab()
        r = fl.cli("review", "prepare", cwd=fl.wt)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f'agente: {REVIEWER} brief: "', r.stdout)
        fl.commit("src/app.py", "x = 1\n", "altro")
        r = fl.cli("review", "prepare", cwd=fl.wt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("/tollgate:finish", r.stderr)


if __name__ == "__main__":
    unittest.main()
