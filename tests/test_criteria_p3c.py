"""Criteri di accettazione di P3c dal programma vero (spec 15): hooks/run e bin/tollgate come li
lancia Claude Code, su un repo temporaneo con HOME, stato e gh finti (FlowLab). I subagenti non
si lanciano: i loro eventi (SubagentStart, SubagentStop) e i loro messaggi li scrive il test."""
import json
import os
import shlex
import shutil
import subprocess
import unittest
from pathlib import Path

from tests.flowkit import PLAN, SESSION, SPEC, FlowLab, plan_text, round_message, spec_text
from tests.hookkit import sample
from tests.test_adopt import blob
from tests.test_criteria_p3b import MINOR, NO_RULE, FinishCase, hook
from tests.test_openpr import BOTH_OK, ISSUES, SOMMA, TOML
from tollgate_analysis import approvals, auditrules, prblock, specdoc
from tollgate_core import audits, db, dod, scope

FIRST_ISSUE, LATER_ISSUE = 3, 9
LOGIN = "src/auth/login.py"
ZERO = {k: 0 for k in approvals.SEVERITIES}


def first_slice_files() -> dict:
    """Ciò che la prima fetta (issue 3) ha unito sul predefinito: la spec con tre fette, la sua
    approvazione e i report dell'avversario e delle lenti."""
    text = spec_text(3)
    folder = f"{approvals.REVIEWS_DIR}/{FIRST_ISSUE}"
    files = {SPEC: text, approvals.approval_paths(FIRST_ISSUE)[0]: approvals.render_approval({
        "kind": "spec-approval", "path": SPEC, "sha": blob(text), "slices": 3,
        "adversarial": "closed", "lens": "closed", "act_id": "a-1",
        "approved_at": "2026-10-19T10:00:00Z"})}
    for kind in ("spec-adversarial", "spec-lens"):
        files[f"{folder}/{kind}-1.md"] = approvals.render_report(
            {"kind": kind, "number": 1, "spec_sha": blob(text), "counts": ZERO,
             "outcome": "empty"}, "Nessun rilievo.\n")
    return files


class L2Helpers(FinishCase):
    """I passi del coordinatore e dell'utente in un lavoro L2, attraverso `hooks/run` e
    `bin/tollgate`. Non ha `setUp` né test: lo scrivono le sottoclassi (un banco `FlowLab` senza
    lavoro, `self.n_agents = 0`)."""

    def make_lab(self, *, toml=TOML, files=None, issues=None):
        """Il banco senza lavoro (lo crea `start`), con il finto `gh` e i due stati verdi."""
        fl = FlowLab(issue=None, toml=toml, files=files)
        self.addCleanup(fl.close)
        self.fl, self.n_agents = fl, 0
        tip = fl.git("rev-parse", "origin/main")
        fl.set_gh(auth=True, issues=issues or ISSUES, prs=[], issue_list=[],
                  statuses={tip: {"statuses": [{"context": "tollgate/guard", "state": "success"},
                                               {"context": "tollgate/verdict",
                                                "state": "success"}]}})
        return fl

    def rows(self, kind):
        return audits.rounds(self.fl.conn, self.fl.work, kind)

    def enter_worktree(self):
        """Il lavoro creato da `start` è l'ultimo: il banco e gli hook usano il suo worktree."""
        row = db_row(self.fl.conn)
        self.wt = Path(row["worktree"])
        self.fl.lab.wt = self.fl.wt = self.wt
        self.fl.lab.work = self.fl.work = row["id"]
        return row

    # --- come lo farebbe il coordinatore -------------------------------------------------
    def commit(self, paths, message):
        """`git add` e `git commit` da Bash: PreToolUse Bash non deve vietarli, PostToolUse Bash
        registra il commit."""
        command = ("git add -- " + " ".join(shlex.quote(p) for p in paths)
                   + " && git commit -q -m " + shlex.quote(message))
        self.event("PreToolUse", "PreToolUse-Bash", tool_input={"command": command})
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com",
                   GIT_CONFIG_GLOBAL="/dev/null")
        done = subprocess.run(["bash", "-c", command], cwd=self.wt, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.event("PostToolUse", "PostToolUse-Bash", tool_input={"command": command},
                   tool_response={"stdout": "", "stderr": "", "interrupted": False})

    def write(self, rel, text):
        """Write di Claude Code: PreToolUse, il file, PostToolUse."""
        path = self.wt / rel
        self.event("PreToolUse", "PreToolUse-Write", tool_name="Write",
                   tool_input={"file_path": str(path), "content": text})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.event("PostToolUse", "PostToolUse-Write", tool_name="Write",
                   tool_input={"file_path": str(path), "content": text},
                   tool_response={"filePath": str(path)})

    def edit_spec(self):
        return hook(self.fl, "PreToolUse", sample(
            "PreToolUse-Edit", session_id=SESSION, cwd=str(self.wt), tool_name="Edit",
            tool_input={"file_path": str(self.wt / SPEC), "old_string": "a", "new_string": "b"}))

    def round(self, kind, counts=None, *args):
        """`audit prepare` apre il giro e l'agente riporta il suo messaggio con i conteggi
        `counts` (default: nessun rilievo). Restituisce la riga del giro chiuso."""
        r = self.cli("audit", "prepare", *args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        row = audits.open_round_row(self.fl.conn, self.fl.work)
        self.assertEqual(row["kind"], kind)
        self.agent(audits.AGENTS[kind], round_message(row, counts or {}))
        self.assertIsNone(audits.open_round_row(self.fl.conn, self.fl.work))
        return audits.last_closed(self.fl.conn, self.fl.work, (kind,))

    def act(self, name, args):
        """L'utente digita `/tollgate:<name> <args>` e la skill lancia `act apply` (gli atti si
        registrano con `UserPromptExpansion` e scadono dopo 10 minuti reali: i test sono più
        brevi, quindi non serve applicarli dalla libreria con `now=fl.now`)."""
        self.slash(name, args)
        return self.cli("act", "apply")

    def approve(self, what):
        r = self.act("approve", what)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def refused(self, name, args):
        """L'atto è rifiutato: uscita 1 e il messaggio (su stdout o stderr)."""
        r = self.act(name, args)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def deny(self, tool, rel, **fields):
        """PreToolUse di `Write` o `Edit` sul file `rel`: dev'essere negato (uscita 2)."""
        r = hook(self.fl, "PreToolUse", sample(
            f"PreToolUse-{tool}", session_id=SESSION, cwd=str(self.wt), tool_name=tool,
            tool_input={"file_path": str(self.wt / rel), **fields}))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        return r

    def prepare_step(self):
        """L'ultima riga di `audit prepare` (rc 0): il passo che la CLI indica."""
        r = self.cli("audit", "prepare")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout.strip().splitlines()[-1]

    def commit_reviews(self, issue, message):
        self.commit([f"{approvals.REVIEWS_DIR}/{issue}"], message)

    def header(self, rel):
        return approvals.parse_approval((self.wt / rel).read_text())

    def blob_at_head(self, rel):
        return self.fl.git("rev-parse", f"HEAD:{rel}", repo=self.wt)

    def run_tasks(self):
        """Dal piano registrato ai task chiusi e al codice committato (due task, il secondo
        crea `LOGIN`)."""
        for k in (1, 2):
            r = self.cli("task", "start", str(k))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.fl.close_tasks()
        self.fl.commit("tests/ids.txt", BOTH_OK, "ids")
        self.fl.commit("src/app.py", SOMMA, "somma")
        self.fl.commit(LOGIN, "x = 1\n", "login")

    # --- il flusso di un lavoro L2 con una fetta, dall'avvio all'esecuzione -------------------
    def start_l2(self, issue=7):
        r = self.cli("start", str(issue), "--level", "L2", cwd=self.fl.main)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        row = self.enter_worktree()
        self.assertEqual((row["issue"], row["level"], row["phase"]), (issue, "L2", "spec_audit"))

    def spec_to_plan(self, slices=1):
        """Spec scritta, un giro pulito, `approve spec`, approvazione committata: fase `plan`."""
        self.write(SPEC, spec_text(slices))
        self.commit([SPEC], "spec")
        self.round("spec-adversarial")
        self.approve(f"spec {slices}")
        self.commit_reviews(7, "approvazione della spec e report")
        self.assertEqual(self.work()["phase"], "plan")

    def plan_to_execution(self, plan):
        """Il piano scritto, un giro pulito, `audit prepare` porta ad `approval`, `approve plan`:
        fase `execution`, approvazione committata."""
        self.write(PLAN, plan)
        self.commit([PLAN], "piano")
        self.round("plan-adversarial")
        self.prepare_step()
        self.assertEqual(self.work()["phase"], "approval")
        self.approve("plan")
        self.assertEqual(self.work()["phase"], "execution")
        self.commit_reviews(7, "approvazione del piano e report")


class LaterSliceTest(L2Helpers):
    """Fetta successiva (Review Focus 5): una spec approvata dall'issue 3 e unita sul predefinito,
    poi `start 9 --spec`, piano, task, `finish check`, `open-pr` e `adopt` dopo un DB perso."""

    def setUp(self):
        self.make_lab(files=first_slice_files(),
                      issues={"9": {**ISSUES["7"], "number": 9, "title": "Seconda fetta"}})

    # --- il flusso --------------------------------------------------------------------------
    def start_later_slice(self):
        r = self.cli("start", str(LATER_ISSUE), "--spec", SPEC, cwd=self.fl.main)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f"spec approvata: {SPEC} (approvazione in "
                      f"docs/superpowers/reviews/{FIRST_ISSUE}/)", r.stdout)
        row = self.enter_worktree()
        self.assertEqual((row["issue"], row["level"], row["phase"], row["spec_path"]),
                         (LATER_ISSUE, "L2", "plan", SPEC))
        self.assertTrue((self.wt / SPEC).is_file())

    def to_execution(self):
        self.start_later_slice()
        denied = self.edit_spec()                            # la spec approvata è bloccata
        self.assertEqual(denied.returncode, 2, denied.stdout + denied.stderr)
        self.write(PLAN, plan_text(tasks=2, task2=f"- Create: `{LOGIN}`"))
        self.commit([PLAN], "piano")
        self.round("plan-adversarial")
        self.cli("audit", "prepare")
        self.assertEqual(self.work()["phase"], "approval")
        self.approve("plan")
        work = self.work()
        self.assertEqual(work["phase"], "execution")
        plan_approval = approvals.approval_paths(LATER_ISSUE)[1]
        header = approvals.parse_approval((self.wt / plan_approval).read_text())
        self.assertEqual((header["sha"], header["spec_sha"]),
                         (work["plan_sha"], blob(spec_text(3))))
        self.commit_reviews(LATER_ISSUE, "approvazione del piano e report")
        self.run_tasks()

    def test_later_slice_end_to_end(self):                      # criterio 24, Review Focus 5
        self.to_execution()
        self.assertIn(LOGIN, scope.paths(self.fl.conn, self.fl.work))
        r = self.finish_check()
        self.assertNotIn("out_of_scope", r.stdout)
        self.assertIn("[sì] " + dod.LABELS["approvals"], r.stdout)
        self.assertNotIn("[no]", r.stdout)

        self.review([MINOR, NO_RULE], outcome="ok")
        self.open_pr()
        (opened,) = json.loads(self.fl.gh_data.read_text())["prs"]
        block = prblock.parse(opened["body"])
        self.assertEqual((block["issue"], block["level"], block["spec"]),
                         (LATER_ISSUE, "L2", SPEC))
        self.assertEqual(block["spec_reviews_dir"], f"docs/superpowers/reviews/{FIRST_ISSUE}/")
        self.assertEqual(block["plan_reviews_dir"], f"docs/superpowers/reviews/{LATER_ISSUE}/")
        self.assertEqual(block["spec_audit"], {"adversarial": "closed", "lens": "closed"})
        self.assertEqual(self.work()["phase"], "pr_open")

        # DB perso, PR chiusa senza merge: `adopt` ritrova la fase dal ramo
        head = self.fl.git("rev-parse", "HEAD", repo=self.wt)
        data = json.loads(self.fl.gh_data.read_text())
        data["prs"][0]["state"] = "CLOSED"
        self.fl.set_gh(**data)
        self.fl.conn.close()
        state = self.fl.ts.state
        shutil.move(str(state.db_path), str(state.db_path) + ".perso")
        for extra in ("-wal", "-shm"):
            Path(str(state.db_path) + extra).unlink(missing_ok=True)
        self.fl.lab.conn = self.fl.conn = db.open_db(state)
        self.slash("adopt", f"#{LATER_ISSUE}")
        r = self.cli("adopt", str(LATER_ISSUE))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        row = db_row(self.fl.conn)
        self.assertEqual((row["issue"], row["level"], row["phase"], row["spec_path"]),
                         (LATER_ISSUE, "L2", "execution", SPEC))
        self.assertIsNotNone(row["plan_sha"])
        self.assertEqual(self.fl.git("rev-parse", "HEAD", repo=self.wt), head)
        denied = self.edit_spec()                            # e la spec è di nuovo bloccata
        self.assertEqual(denied.returncode, 2, denied.stdout + denied.stderr)


class L2FlowTest(L2Helpers):
    """Il percorso L2 dal programma vero (criteri 18, 24, 35 parte locale, 37 e 41 seconda frase):
    `start --level L2`, giri, atti dell'utente e fasi. I subagenti non si lanciano: il test
    scrive i loro eventi (`L2Helpers.round`)."""

    def setUp(self):
        self.make_lab()
        self.start_l2()

    def test_l2_spec_to_execution_end_to_end(self):          # criteri 18, 24, 37, 41
        # in spec_audit un piano non si scrive (criterio 37)
        self.deny("Write", PLAN, content=plan_text(tasks=2))
        self.assertFalse((self.wt / PLAN).exists())

        # spec senza «Tane di coniglio» e «Cosa non fare», committata: l'avversario non dichiara
        # rilievi, ma `spec_pitch` aggiunge un `major` per sezione mancante (criterio 41)
        bad = spec_text(pitch=False)
        self.write(SPEC, bad)
        self.commit([SPEC], "spec")
        row = self.round("spec-adversarial")
        counts = json.loads(row["counts"])
        self.assertEqual(counts["major"], len(specdoc.pitch_problems(bad)))
        self.assertEqual(counts["major"], 2)
        self.assertEqual((row["outcome"], auditrules.is_clean(counts)), ("findings", False))
        self.assertIn("rilievo meccanico", (self.wt / row["report_path"]).read_text())
        r = self.cli("audit", "prepare")                     # stessa spec: serve correggerla
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("correggi la spec", r.stdout)

        # approve spec e act apply dopo un giro non pulito: rifiuto, fase invariata (criterio 24)
        self.assertIn("blocker o major", self.refused("approve", "spec 1"))
        self.assertEqual(self.work()["phase"], "spec_audit")
        self.assertFalse((self.wt / approvals.approval_paths(7)[0]).exists())

        # spec corretta, nuovo giro pulito, approve spec: file di approvazione e fase plan
        good = spec_text(note="corretta")
        self.write(SPEC, good)
        self.commit([SPEC], "spec corretta")
        clean = self.round("spec-adversarial")
        self.assertEqual((clean["outcome"], clean["sha"]), ("empty", self.blob_at_head(SPEC)))
        self.approve("spec 1")
        header = self.header(approvals.approval_paths(7)[0])
        self.assertEqual((header["sha"], header["adversarial"], header["slices"]),
                         (self.blob_at_head(SPEC), "closed", 1))
        self.assertEqual(self.work()["phase"], "plan")
        self.deny("Edit", SPEC, old_string="a", new_string="b")      # la spec approvata è bloccata
        self.commit_reviews(7, "approvazione della spec e report")

        # piano: giro non pulito, piano corretto, giro pulito, la CLI porta la fase ad approval
        self.write(PLAN, plan_text(tasks=2))
        self.commit([PLAN], "piano")
        dirty = self.round("plan-adversarial", {"major": 1})
        self.assertEqual(dirty["outcome"], "findings")
        self.assertEqual(self.work()["phase"], "plan")
        first_plan = self.blob_at_head(PLAN)
        self.write(PLAN, plan_text(tasks=3))
        self.commit([PLAN], "piano corretto")
        corrected = self.blob_at_head(PLAN)
        self.assertNotEqual(corrected, first_plan)
        self.round("plan-adversarial")
        self.assertIsNone(self.work()["plan_sha"])           # in L2 il piano non si registra da solo
        self.prepare_step()
        self.assertEqual(self.work()["phase"], "approval")

        # approve plan: plan_sha è il blob del piano corretto, che l'avversario ha approvato
        self.approve("plan")
        work = self.work()
        self.assertEqual((work["phase"], work["plan_sha"]), ("execution", corrected))
        plan_header = self.header(approvals.approval_paths(7)[1])
        self.assertEqual((plan_header["sha"], plan_header["spec_sha"]),
                         (corrected, self.blob_at_head(SPEC)))
        self.assertEqual(scope.paths(self.fl.conn, self.fl.work),
                         {"src/app.py", "tests/test_app.py", "docs/uso.md", "docs/extra-3.md"})
        self.assertEqual([e["cause"] for e in self.fl.events("phase_change")][-3:],
                         ["approve_spec", "audit_clean", "approve_plan"])

    def test_cap_and_suspension_in_pr_block(self):           # criterio 24
        self.write(SPEC, spec_text())
        self.commit([SPEC], "spec")
        for n in range(4):                                   # quattro giri con un major
            if n:
                self.write(SPEC, spec_text(note=f"correzione {n}"))
                self.commit([SPEC], f"spec {n}")
            self.round("spec-adversarial", {"major": 1})
        ((block, reason),) = [(r["id"], r["reason"]) for r in self.fl.conn.execute(
            "SELECT id, reason FROM blocks WHERE work = ? AND closed IS NULL", (self.fl.work,))]
        self.assertEqual((reason, self.work()["phase"]),
                         (audits.cap_reason("spec-adversarial", 4), "blocked"))
        self.assertIn("giri avversariali della spec", reason)
        r = self.cli("audit", "prepare")                     # bloccato: si passa da resolve
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("/tollgate:resolve", r.stdout)
        self.assertIn("/tollgate:resolve", self.refused("approve", "spec 1"))

        r = self.act("resolve", f"{block} deciso")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("avversariale sospeso", r.stdout)
        self.assertEqual(self.work()["phase"], "spec_audit")
        self.assertEqual(audits.suspended(self.fl.conn, self.fl.work), {"spec-adversarial": 4})
        self.assertIn("/tollgate:approve spec", self.prepare_step())
        self.approve("spec 1")
        self.assertEqual(self.header(approvals.approval_paths(7)[0])["adversarial"], "suspended")
        self.commit_reviews(7, "approvazione della spec e report")

        # dal piano alla PR: la sospensione arriva nel blocco 18.1
        self.plan_to_execution(plan_text(tasks=2, task2=f"- Create: `{LOGIN}`"))
        self.run_tasks()
        r = self.finish_check()
        self.assertIn("[sì] " + dod.LABELS["approvals"], r.stdout)
        self.assertNotIn("[no]", r.stdout)
        self.review([MINOR, NO_RULE], outcome="ok")
        self.open_pr()
        (opened,) = json.loads(self.fl.gh_data.read_text())["prs"]
        block_json = prblock.parse(opened["body"])
        self.assertEqual(block_json["spec_audit"], {"adversarial": "suspended", "lens": None})
        self.assertEqual(block_json["spec_reviews_dir"], f"{approvals.REVIEWS_DIR}/7/")
        self.assertEqual(block_json["plan_reviews_dir"], f"{approvals.REVIEWS_DIR}/7/")
        self.assertEqual((block_json["level"], block_json["spec"]), ("L2", SPEC))
        self.assertEqual(self.work()["phase"], "pr_open")

    def test_three_slices_lens_audit_and_component_off(self):    # criteri 24 e 35 (parte locale)
        self.write(SPEC, spec_text(3))
        self.commit([SPEC], "spec")
        self.round("spec-adversarial")
        self.assertIn("prevede 3 fette", self.refused("approve", "spec 1"))
        r = self.cli("audit", "prepare")                     # il costo si conferma (uscita 3)
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("audit a lenti", r.stdout)
        self.assertEqual(self.rows("spec-lens"), [])
        first = self.round("spec-lens", None, "--confirm")
        self.assertEqual((first["number"], first["viewpoint"]), (1, "executor"))
        self.assertIn("audit a lenti non è chiuso", self.refused("approve", "spec 3"))
        self.assertEqual(self.work()["phase"], "spec_audit")
        for _ in range(len(auditrules.VIEWPOINTS) * auditrules.EMPTY_NEEDED - 1):      # ogni punto di vista, due cicli vuoti
            self.round("spec-lens")
        self.assertIn("/tollgate:approve spec", self.prepare_step())
        r = self.approve("spec 3")
        self.assertIn("Fette successive", r.stdout)
        header = self.header(approvals.approval_paths(7)[0])
        self.assertEqual((header["slices"], header["adversarial"], header["lens"]),
                         (3, "closed", "closed"))

    def test_reopen_spec_from_execution(self):                   # criterio 37
        self.spec_to_plan()
        self.plan_to_execution(plan_text(tasks=2))
        spec_approval, plan_approval = approvals.approval_paths(7)
        first = (self.header(spec_approval)["sha"], self.work()["plan_sha"])
        self.assertTrue(scope.paths(self.fl.conn, self.fl.work))
        self.deny("Edit", SPEC, old_string="a", new_string="b")

        self.assertIn("motivo", self.refused("reopen", "spec"))      # il motivo è obbligatorio
        r = self.act("reopen", "spec la spec dimentica un caso")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        work = self.work()
        self.assertEqual((work["phase"], work["plan_sha"]), ("spec_audit", None))
        self.assertEqual(scope.paths(self.fl.conn, self.fl.work), set())
        self.assertEqual(self.fl.conn.execute("SELECT COUNT(*) FROM tasks WHERE work = ?",
                                              (self.fl.work,)).fetchone()[0], 0)
        (reset,) = self.fl.events("plan_reset")
        self.assertEqual(reset["plan_sha"], first[1])
        self.assertEqual(hook(self.fl, "PreToolUse", sample(
            "PreToolUse-Edit", session_id=SESSION, cwd=str(self.wt), tool_name="Edit",
            tool_input={"file_path": str(self.wt / SPEC), "old_string": "a",
                        "new_string": "b"})).returncode, 0)     # la spec è di nuovo modificabile

        # nuova approvazione richiesta: spec corretta, nuovo giro, approve spec
        self.write(SPEC, spec_text(note="corretta"))
        self.commit([SPEC], "spec corretta")
        self.round("spec-adversarial")
        self.approve("spec 1")
        second = self.header(spec_approval)["sha"]
        self.assertEqual((second, self.work()["phase"]), (self.blob_at_head(SPEC), "plan"))
        self.assertNotEqual(second, first[0])
        self.deny("Edit", SPEC, old_string="a", new_string="b")      # bloccata di nuovo
        self.commit_reviews(7, "nuova approvazione della spec")

        # il piano si approva di nuovo: nuovo giro sulla spec nuova, scope e task di nuovo pending
        self.round("plan-adversarial")
        self.prepare_step()
        self.approve("plan")
        work = self.work()
        self.assertEqual((work["phase"], work["plan_sha"]), ("execution", self.blob_at_head(PLAN)))
        self.assertEqual(self.header(plan_approval)["spec_sha"], second)
        self.assertEqual([t["state"] for t in self.fl.conn.execute(
            "SELECT state FROM tasks WHERE work = ? ORDER BY number", (self.fl.work,))],
            ["pending", "pending"])


class SpecAuditOffTest(L2Helpers):
    """Criterio 35, parte locale: `spec_audit = false` (un banco con un'altra configurazione)."""

    def setUp(self):
        self.make_lab(toml=TOML + "[components]\nspec_audit = false\n")
        self.start_l2()

    def test_three_slices_with_spec_audit_off(self):             # criterio 35 (parte locale)
        self.write(SPEC, spec_text(3))
        self.commit([SPEC], "spec")
        self.round("spec-adversarial")
        self.assertIn("/tollgate:approve spec", self.prepare_step())
        self.assertEqual(self.rows("spec-lens"), [])
        self.approve("spec 3")
        header = self.header(approvals.approval_paths(7)[0])
        self.assertEqual((header["slices"], header["adversarial"], header["lens"]),
                         (3, "closed", "off"))
        self.assertEqual(self.work()["phase"], "plan")


def db_row(conn):
    return conn.execute("SELECT * FROM work_items ORDER BY id DESC LIMIT 1").fetchone()


if __name__ == "__main__":
    unittest.main()
