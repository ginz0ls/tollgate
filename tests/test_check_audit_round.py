import json
import types
from datetime import timedelta
from pathlib import Path

import tests.test_audit_prepare as tap
from tests.flowkit import SESSION, SPEC, round_message
from tests.hookkit import DEFAULT_TOML, sample
from tollgate_analysis import approvals, auditrules
from tollgate_core import audits, clock, subagents
from tollgate_flow import audit
from tollgate_hooks import apply

ADV, LENS, PLAN_ADV = "spec-adversarial", "spec-lens", "plan-adversarial"
MAJOR = {"major": 1}
CLEAN: dict = {}
REPORT = f"docs/superpowers/reviews/7/{ADV}-1.md"


class RoundCase(tap.AuditCase):
    def open_adv(self, **spec):
        """Una spec committata e il giro avversariale 1 aperto da `audit prepare`."""
        fl = self.lab(toml=spec.pop("toml", DEFAULT_TOML))
        fl.write_spec(**spec)
        self.assertEqual(self.prepare().code, audit.OK)
        return fl

    def open_off(self):
        """Un giro avversariale aperto dalla libreria con `spec_adversary` spento (`audit
        prepare` con il componente spento non ne apre: il giro è rimasto da prima)."""
        fl = self.lab(toml=self.off("spec_adversary"))
        blob = fl.write_spec()
        audits.open_round(fl.conn, fl.work, kind=ADV, sha=blob, spec_sha=blob, viewpoint=None,
                          code="c0de0000", now=fl.lab.now)
        return fl

    def open_row(self):
        return audits.open_round_row(self.fl.conn, self.fl.work)

    def row(self, kind=ADV, number=1):
        return self.fl.conn.execute("SELECT * FROM spec_audit WHERE work = ? AND kind = ? "
                                    "AND number = ?", (self.fl.work, kind, number)).fetchone()

    def agent_id(self, row=None):
        """L'agente del giro dato, del giro aperto o dell'ultimo giro."""
        row = row or self.open_row() or self.fl.conn.execute(
            "SELECT * FROM spec_audit WHERE work = ? ORDER BY id DESC LIMIT 1",
            (self.fl.work,)).fetchone()
        return f"a-{row['kind']}-{row['number']}"

    def start(self, row=None):
        """SubagentStart dell'agente del giro, un secondo dopo l'apertura (come report_round)."""
        row = row or self.open_row()
        self.fl.lab.now = clock.parse(row["opened"]) + timedelta(seconds=1)
        return self.fl.hook(sample("SubagentStart-none", session_id=SESSION,
                                   cwd=str(self.fl.wt), agent_id=self.agent_id(row),
                                   agent_type=audits.AGENTS[row["kind"]]))

    def stop(self, row, text, atype=None):
        p = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.fl.wt),
                   agent_id=self.agent_id(row), agent_type=atype or audits.AGENTS[row["kind"]],
                   last_assistant_message=text, agent_transcript_path="/non/esiste.jsonl")
        if text is None:
            p.pop("last_assistant_message")
        return self.fl.hook(p)

    def sub(self, row=None):
        return subagents.get(self.fl.conn, self.agent_id(row))

    def blocks(self):
        return [r["reason"] for r in self.fl.conn.execute(
            "SELECT reason FROM blocks WHERE work = ? AND closed IS NULL ORDER BY id",
            (self.fl.work,))]

    def vetoes(self):
        return [e for e in self.fl.events("veto") if e["rule"] == "audit_round"]

    def header(self, rel=REPORT):
        return approvals.parse_report_header((self.fl.wt / rel).read_text())


class ReportTest(RoundCase):
    def test_valid_report_written_and_round_closed(self):
        self.open_adv()
        r = self.fl.report_round(counts={"moderate": 2, "minor": 1})
        self.assertEqual(r.returncode, 0, r.stderr)
        head = self.header()
        self.assertEqual((head["kind"], head["number"], head["viewpoint"], head["outcome"]),
                         (ADV, 1, None, "findings"))
        self.assertEqual(head["counts"], {"blocker": 0, "major": 0, "moderate": 2, "minor": 1})
        row = self.row()
        self.assertEqual((row["stage"], row["outcome"], row["report_path"]),
                         ("closed", "findings", REPORT))
        self.assertEqual(head["spec_sha"], row["spec_sha"])
        self.assertEqual(self.fl.events("spec_audit_round"),
                         [{"kind": ADV, "number": 1, "viewpoint": None, "outcome": "findings"}])
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.blocks(), [])
        self.assertIn("Il contenuto dei recinti", (self.fl.wt / REPORT).read_text())

    def test_empty_counts_give_empty_outcome(self):
        self.open_adv()
        self.fl.report_round()
        self.assertEqual(self.header()["outcome"], "empty")
        self.assertEqual(self.row()["outcome"], "empty")

    def test_declared_outcome_is_ignored(self):
        self.open_adv()
        row = self.open_row()
        self.start(row)
        data = json.loads(round_message(row, MAJOR).splitlines()[1])
        data["outcome"] = "empty"
        r = self.stop(row, "Fine.\n" + json.dumps(data))
        self.assertEqual(r.exit, 0)
        self.assertEqual(self.row()["outcome"], "findings")

    def test_plan_report_header_has_plan_sha(self):
        fl = self.plan_lab()
        blob = fl.write_l2_plan()
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        head = self.header(f"docs/superpowers/reviews/7/{PLAN_ADV}-1.md")
        self.assertEqual((head["kind"], head["plan_sha"]), (PLAN_ADV, blob))

    def test_missing_cosa_non_fare_adds_major(self):
        fl = self.lab()
        fl.commit(SPEC, "# Prova\n\n## Obiettivo\nx\n\n## Fette previste\n1. Fetta 1\n\n"
                        "## Tane di coniglio\n- nessuna\n", "spec senza cosa non fare")
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        head = self.header()
        self.assertEqual(head["counts"]["major"], 1)
        self.assertEqual(head["outcome"], "findings")
        row = self.row()
        self.assertFalse(auditrules.is_clean(json.loads(row["counts"])))
        text = (fl.wt / REPORT).read_text()
        self.assertIn("rilievo meccanico: manca la sezione «## Cosa non fare»", text)
        self.assertNotIn("Tane di coniglio»", text)

    def test_spec_pitch_off_no_mechanical_finding(self):
        toml = DEFAULT_TOML + "[components]\nspec_pitch = false\n"
        fl = self.lab(toml=toml)
        fl.write_spec(pitch=False)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.header()["counts"]["major"], 0)
        self.assertNotIn("rilievo meccanico", (fl.wt / REPORT).read_text())

    def test_pitch_not_applied_to_lens_cycles(self):
        fl = self.lab()
        fl.write_spec(slices=2, pitch=False)
        fl.closed_round(ADV, CLEAN)
        self.assertEqual(self.prepare(confirm=True).code, audit.OK)
        fl.report_round(counts=CLEAN)
        self.assertEqual(self.header(f"docs/superpowers/reviews/7/{LENS}-1.md")["outcome"],
                         "empty")

    def test_long_message_is_truncated_and_fenced(self):
        self.open_adv()
        row = self.open_row()
        self.start(row)
        text = "```\n" + "x" * 70000 + "\n" + round_message(row, CLEAN).splitlines()[1]
        self.assertEqual(self.stop(row, text).exit, 0)
        body = (self.fl.wt / REPORT).read_text()
        self.assertIn("messaggio troncato", body)
        self.assertLess(len(body), 61500)
        self.assertIn("````", body)


class InvalidReportTest(RoundCase):
    def test_bad_json_vetoed_twice_then_needs_you(self):
        self.open_adv()
        for n in (1, 2):
            r = self.fl.report_round(bad_json=True)
            self.assertEqual(r.returncode, 2)
            self.assertIn("report del giro non valido", r.stderr)
            self.assertIn(f"veto {n} di 2", r.stderr)
            self.assertEqual(self.sub()["state"], "running")
        r = self.fl.report_round(bad_json=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(len(self.vetoes()), 2)
        [reason] = self.blocks()
        self.assertTrue(reason.startswith("report del giro non valido:"))
        self.assertEqual(self.open_row()["number"], 1)
        self.assertEqual(self.work()["phase"], "blocked")
        self.assertFalse((self.fl.wt / REPORT).exists())

    def test_cut_message_is_invalid(self):
        self.open_adv()
        r = self.fl.report_round(cut=True)
        self.assertEqual(r.returncode, 2)
        self.assertIsNotNone(self.open_row())

    def test_invalid_report_keeps_round_open_and_reason_has_no_raw_values(self):
        self.open_adv()
        row = self.open_row()
        self.start(row)
        data = json.loads(round_message(row, CLEAN).splitlines()[1])
        data.update(code="SEGRETO-CODE", spec_sha="SEGRETO-SHA", kind=LENS)
        text = "Fine.\n" + json.dumps(data)
        seen = [self.stop(row, text) for _ in range(3)]
        self.assertEqual([r.exit for r in seen], [2, 2, 0])
        for part in ("code", "spec_sha", "kind"):
            self.assertIn(part, seen[0].stderr)
        [reason] = self.blocks()
        for raw in ("SEGRETO-CODE", "SEGRETO-SHA"):
            self.assertNotIn(raw, reason)
            self.assertTrue(all(raw not in r.stderr for r in seen))
            self.assertTrue(all(raw not in v["reason"] for v in self.vetoes()))
        self.assertEqual((self.open_row()["number"], self.open_row()["code"]),
                         (1, row["code"]))
        self.assertEqual(self.prepare().code, audit.REFUSED)    # fase blocked: rifiuta
        self.assertIn("bloccato", self.text(self.prepare()))

    def test_wrong_number_or_viewpoint_invalid(self):
        self.open_adv()
        row = self.open_row()
        self.start(row)
        data = json.loads(round_message(row, CLEAN).splitlines()[1])
        data["number"] = 2
        r = self.stop(row, json.dumps(data))
        self.assertEqual(r.exit, 2)
        self.assertIn("number", r.stderr)

    def test_tampering_agent_needs_you(self):
        self.open_adv()
        self.start()
        (self.fl.wt / "src" / "app.py").write_text("manomesso\n")
        r = self.fl.report_round(counts=CLEAN)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.sub()["state"], "tampered")
        self.assertEqual(self.open_row()["number"], 1)
        self.assertFalse((self.fl.wt / REPORT).exists())
        [reason] = self.blocks()
        self.assertIn("ha cambiato file", reason)

    def test_tampering_ignored_without_readonly_check(self):
        self.open_adv(toml=DEFAULT_TOML + "[components]\nreadonly_check = false\n")
        self.start()
        (self.fl.wt / "src" / "app.py").write_text("manomesso\n")
        self.assertEqual(self.fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.row()["stage"], "closed")

    def test_handback_report_used_in_auto_mode(self):
        self.open_adv()
        row = self.open_row()
        self.start(row)
        subagents.set_report(self.fl.conn, self.agent_id(row), round_message(row, CLEAN))
        self.assertEqual(self.stop(row, None).exit, 0)
        self.assertEqual(self.row()["stage"], "closed")
        self.assertTrue((self.fl.wt / REPORT).is_file())

    def test_component_off_closes_only_the_agent_row(self):
        self.open_off()
        r = self.fl.report_round(counts=MAJOR)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.open_row()["number"], 1)
        self.assertEqual(self.fl.events("spec_audit_round"), [])
        self.assertFalse((self.fl.wt / REPORT).exists())
        self.assertEqual(self.blocks(), [])


class LateReportTest(RoundCase):
    def test_late_report_of_superseded_round_ignored(self):
        fl = self.lab()
        fl.write_spec()
        self.assertEqual(self.prepare().code, audit.OK)
        row1 = self.open_row()
        # il coordinatore corregge e committa la spec; POI parte l'agente 1
        fl.write_spec(note="correzione")
        self.start(row1)
        started = clock.parse(self.sub(row1)["started"])
        # POI si apre il giro 2 dalla libreria, dopo lo started dell'agente 1: il giro 1 è
        # superseded. Nessun file del worktree cambia da qui allo stop dell'agente 1 (D14): il
        # controllo di manomissione di subagent_stop resta attivo per lui.
        r = audit.prepare(fl.ts.state, fl.wt, confirm=False, now=started + timedelta(seconds=1))
        self.assertEqual(r.code, audit.OK, r.lines)
        self.assertEqual(self.row(number=1)["outcome"], "superseded")
        row2 = self.open_row()
        self.assertEqual(row2["number"], 2)
        fl.lab.now = started + timedelta(seconds=2)
        before = fl.conn.execute("SELECT count(*) FROM events WHERE type = 'veto'").fetchone()[0]
        r = self.stop(row1, round_message(row1, MAJOR))
        self.assertEqual(r.exit, 0, r.stderr)
        self.assertEqual(self.sub(row1)["state"], "done")
        self.assertEqual(fl.conn.execute("SELECT count(*) FROM events WHERE type = 'veto'")
                         .fetchone()[0], before)
        self.assertEqual(self.open_row()["number"], 2)
        self.assertEqual(self.row(number=2)["stage"], "open")
        self.assertFalse((fl.wt / REPORT).exists())
        self.assertEqual(self.blocks(), [])
        self.assertEqual(fl.events("spec_audit_round"), [])

    def test_agent_started_before_round_never_belongs_to_it(self):
        fl = self.lab()
        fl.write_spec()
        self.assertEqual(self.prepare().code, audit.OK)
        row = self.open_row()
        self.start(row)
        sub = subagents.get(fl.conn, self.agent_id(row))
        ctx = types.SimpleNamespace(db=fl.conn, event=types.SimpleNamespace(cwd=fl.wt),
                                    bound=False, work=None)
        from tollgate_checks import _common
        self.assertEqual(_common.awaiting_audit(ctx, sub)["number"], 1)
        fl.conn.execute("UPDATE spec_audit SET opened = ? WHERE id = ?",
                        (clock.fmt(clock.parse(sub["started"]) + timedelta(seconds=5)),
                         row["id"]))
        fl.conn.commit()
        self.assertIsNone(_common.awaiting_audit(ctx, sub))
        fl.conn.execute("UPDATE subagents SET started = NULL WHERE id = ?", (sub["id"],))
        fl.conn.commit()
        self.assertIsNone(_common.awaiting_audit(
            ctx, subagents.get(fl.conn, sub["id"])))

    def test_awaiting_audit_falls_back_to_governing_work(self):
        fl = self.lab()
        fl.write_spec()
        self.assertEqual(self.prepare().code, audit.OK)
        row = self.open_row()
        self.start(row)
        fl.conn.execute("UPDATE subagents SET work = NULL WHERE id = ?", (self.agent_id(row),))
        fl.conn.commit()
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.row()["stage"], "closed")


class WriteFailureTest(RoundCase):
    def check_not_written(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.row()["stage"], "open")
        [veto] = self.vetoes()
        self.assertTrue(veto["reason"].startswith("report non scritto:"))
        self.assertEqual(veto["event"], "subagent_stop")
        self.assertEqual(self.sub()["state"], "done")
        self.assertEqual(self.fl.events("spec_audit_round"), [])
        self.assertEqual(self.blocks(), [])

    def test_folder_occupied_by_a_file(self):
        fl = self.open_adv()
        reviews = fl.wt / "docs" / "superpowers" / "reviews"
        reviews.mkdir(parents=True, exist_ok=True)
        (reviews / "7").write_text("occupato\n")
        self.check_not_written(fl.report_round(counts=CLEAN))

    def test_report_path_occupied_by_a_folder(self):
        fl = self.open_adv()
        (fl.wt / REPORT).mkdir(parents=True)
        self.check_not_written(fl.report_round(counts=CLEAN))
        self.assertEqual([p.name for p in (fl.wt / REPORT).parent.iterdir()], [Path(REPORT).name])

    def test_lens_state_not_written_keeps_round_closed(self):
        fl = self.lab()
        fl.write_spec(slices=2)
        fl.closed_round(ADV, CLEAN)
        self.assertEqual(self.prepare(confirm=True).code, audit.OK)
        (fl.wt / "docs" / "superpowers" / "reviews" / "7").mkdir(parents=True)
        (fl.wt / "docs" / "superpowers" / "reviews" / "7" / "spec-lens-stato.md").mkdir()
        self.assertEqual(fl.report_round(counts=CLEAN).returncode, 0)
        self.assertEqual(self.row(LENS)["stage"], "closed")
        self.assertTrue(self.vetoes()[0]["reason"].startswith("stato delle lenti non scritto"))

    def test_unencodable_body_leaves_no_temporary_file(self):
        """Riga 18: un testo che non si codifica (surrogato) non lascia un `.tmp` nella cartella
        protetta e dà un veto, non un'eccezione."""
        fl = self.open_adv()
        ctx = types.SimpleNamespace(now=fl.lab.now, event=types.SimpleNamespace(session=SESSION),
                                    cfg=lambda k: 4)
        data = {"work": fl.work, "kind": ADV, "number": 1, "counts": dict(auditrules_zero()),
                "body": "rotto \udcff", "extra": []}
        apply._audit_report(fl.conn, fl.ts.state, ctx, data)
        self.assertTrue(self.vetoes()[0]["reason"].startswith("report non scritto:"))
        self.assertEqual(self.row()["stage"], "open")
        folder = (fl.wt / REPORT).parent
        self.assertEqual([p.name for p in folder.iterdir()] if folder.exists() else [], [])

    def test_write_atomic_removes_temporary_on_any_error(self):
        fl = self.open_adv()
        target = fl.wt / "docs" / "superpowers" / "reviews" / "7" / "x.md"
        with self.assertRaises(ValueError):
            apply._write_atomic(target, "\udcff")
        self.assertEqual([p.name for p in target.parent.iterdir()], [])
        apply._write_atomic(target, "ok\n")
        self.assertEqual([p.name for p in target.parent.iterdir()], ["x.md"])

    def test_audit_report_ignores_round_no_longer_open(self):
        fl = self.open_adv()
        ctx = types.SimpleNamespace(now=fl.lab.now, event=types.SimpleNamespace(session=SESSION),
                                    cfg=lambda k: 4)
        data = {"work": fl.work, "kind": ADV, "number": 1, "counts": dict(auditrules_zero()),
                "body": "x", "extra": []}
        audits.supersede(fl.conn, fl.work, (ADV, 1), now=fl.lab.now)
        apply._audit_report(fl.conn, fl.ts.state, ctx, data)
        data["number"] = 9
        apply._audit_report(fl.conn, fl.ts.state, ctx, data)
        self.assertEqual([v["reason"] for v in self.vetoes()], ["giro non più aperto"] * 2)
        self.assertFalse((fl.wt / REPORT).exists())
        self.assertEqual(self.row()["outcome"], "superseded")


def auditrules_zero():
    return {k: 0 for k in auditrules.SEVERITIES}


class CapTest(RoundCase):
    def test_fourth_dirty_adversarial_round_opens_cap_block(self):
        fl = self.lab()
        fl.write_spec()
        fl.closed_round(ADV, MAJOR)
        fl.closed_round(ADV, MAJOR)
        fl.write_spec(note="v3")
        self.assertEqual(self.prepare().code, audit.OK)
        fl.report_round(counts=MAJOR)
        self.assertEqual(self.blocks(), [])           # il terzo giro non è ancora il tetto
        self.assertEqual(self.work()["phase"], "spec_audit")
        fl.write_spec(note="v4")
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.open_row()["number"], 4)
        fl.report_round(counts=MAJOR)
        self.assertEqual(self.blocks(), [audits.cap_reason(ADV, 4)])
        self.assertEqual(self.work()["phase"], "blocked")
        self.assertEqual(self.work()["phase_before_block"], "spec_audit")

    def test_fourth_clean_round_opens_no_block(self):
        fl = self.lab()
        fl.write_spec()
        for _ in range(3):
            fl.closed_round(ADV, MAJOR)
        fl.write_spec(note="v4")
        self.assertEqual(self.prepare().code, audit.OK)
        fl.report_round(counts={"moderate": 3})
        self.assertEqual(self.blocks(), [])

    def test_superseded_rounds_do_not_count_toward_cap(self):
        fl = self.lab()
        fl.write_spec()
        fl.closed_round(ADV, MAJOR)
        fl.closed_round(ADV, MAJOR)
        fl.write_spec(note="v3")
        self.assertEqual(self.prepare().code, audit.OK)    # giro 3
        fl.write_spec(note="v4")
        self.assertEqual(self.prepare().code, audit.OK)    # il 3 è superseded, apre il 4
        self.assertEqual(self.open_row()["number"], 4)
        fl.report_round(counts=MAJOR)
        self.assertEqual(len(audits.rounds(fl.conn, fl.work, ADV)), 3)
        self.assertEqual(self.blocks(), [])

    def test_lens_cycle_regenerates_state_file(self):
        fl = self.lab()
        fl.write_spec(slices=2)
        fl.closed_round(ADV, CLEAN)
        self.assertEqual(self.prepare(confirm=True).code, audit.OK)
        fl.report_round(counts=CLEAN)
        state = fl.wt / "docs" / "superpowers" / "reviews" / "7" / "spec-lens-stato.md"
        self.assertIn("| executor (chi esegue) | 1 | 1 | empty |", state.read_text())
        head = self.header(f"docs/superpowers/reviews/7/{LENS}-1.md")
        self.assertEqual((head["kind"], head["viewpoint"]), (LENS, "executor"))
        self.assertEqual(self.prepare().code, audit.OK)
        fl.report_round(counts={"moderate": 1})
        text = state.read_text()
        self.assertIn("| executor (chi esegue) | 1 | 1 | empty |", text)
        self.assertIn("| user (chi usa) | 1 | 0 | findings |", text)
        self.assertIn("stato: aperto", text)
        self.assertIn("cicli fatti: 2 (tetto 30)", text)

    def test_lens_cap_opens_block(self):
        fl = self.lab()
        fl.write_spec(slices=2)
        fl.closed_round(ADV, CLEAN)
        for _ in range(29):
            fl.closed_round(LENS, {"moderate": 1}, viewpoint="executor")
        fl.write_spec(slices=2, note="v2")
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.open_row()["kind"], LENS)
        fl.report_round(counts={"moderate": 1})
        self.assertEqual(self.blocks(), [audits.cap_reason(LENS, 30)])
        self.assertEqual(self.blocks(), ["audit a lenti: tetto di cicli raggiunto"])

    def test_lens_cap_block_not_reopened_beyond_cap(self):
        fl = self.lab(toml=self.off("spec_adversary"))
        fl.write_spec(slices=2)
        for _ in range(30):
            fl.closed_round(LENS, {"moderate": 1}, viewpoint="executor")
        audits.suspend(fl.conn, fl.work, LENS, 30, now=fl.lab.now)
        fl.write_spec(slices=2, note="v2")
        self.assertEqual(self.prepare().code, audit.OK)     # ciclo di conferma
        self.assertEqual(self.open_row()["kind"], LENS)
        fl.report_round(counts={"moderate": 1})
        self.assertEqual(self.blocks(), [])

    def test_plan_round_cap_after_two(self):
        fl = self.plan_lab()
        fl.write_l2_plan()
        self.assertEqual(self.prepare().code, audit.OK)
        fl.report_round(counts=MAJOR)
        self.assertEqual(self.blocks(), [])
        fl.write_l2_plan(tasks=2)
        self.assertEqual(self.prepare().code, audit.OK)
        self.assertEqual(self.open_row()["number"], 2)
        fl.report_round(counts=MAJOR)
        self.assertEqual(self.blocks(), [audits.cap_reason(PLAN_ADV, 2)])
        self.assertEqual(self.blocks(), ["giri avversariali del piano esauriti (giro 2)"])


class OtherPathsTest(RoundCase):
    def test_task_reviewer_and_final_reviewer_paths_unchanged(self):
        self.open_adv()
        row = self.open_row()
        self.fl.lab.now = clock.parse(row["opened"]) + timedelta(seconds=1)
        for n, atype in enumerate(("tollgate:task-reviewer", "tollgate:final-reviewer")):
            aid = f"altro-{n}"
            self.fl.hook(sample("SubagentStart-none", session_id=SESSION, cwd=str(self.fl.wt),
                                agent_id=aid, agent_type=atype))
            p = sample("SubagentStop-manual-normal", session_id=SESSION, cwd=str(self.fl.wt),
                       agent_id=aid, agent_type=atype, last_assistant_message="niente JSON",
                       agent_transcript_path="/non/esiste.jsonl")
            self.assertEqual(self.fl.hook(p).exit, 0)
            self.assertEqual(subagents.get(self.fl.conn, aid)["state"], "done")
        self.assertEqual(self.open_row()["number"], 1)
        self.assertEqual(self.vetoes(), [])
        self.assertEqual(self.blocks(), [])

    def test_every_branch_emits_subagent_finish(self):
        cases = []

        def valid():
            self.fl.report_round(counts=CLEAN)

        def bad():
            for _ in range(3):
                self.fl.report_round(bad_json=True)

        def tamper():
            self.start()
            (self.fl.wt / "src" / "app.py").write_text("manomesso\n")
            self.fl.report_round(counts=CLEAN)

        for name, opener, act, want in (
                ("valido", self.open_adv, valid, "done"),
                ("non valido dopo due veti", self.open_adv, bad, "done"),
                ("manomesso", self.open_adv, tamper, "tampered"),
                ("componente spento", self.open_off, valid, "done")):
            with self.subTest(name):
                opener()
                act()
                cases.append(name)
                self.assertEqual(self.sub()["state"], want)
        self.assertEqual(len(cases), 4)

    def test_report_file_committable_and_protected(self):
        fl = self.open_adv()
        fl.report_round(counts=CLEAN)
        r = fl.bash(f"git add {REPORT}")
        self.assertEqual(r.exit, 0, r.stderr)
        r = fl.bash("git commit -m 'report del giro'")
        self.assertEqual(r.exit, 0, r.stderr)
        r = fl.pre_edit(fl.wt / REPORT)
        self.assertEqual(r.exit, 2)
        self.assertIn("protett", r.stderr)

    def test_ops_count_is_28(self):
        self.assertEqual(len(apply.OPS), 28)
        self.assertIn("audit_report", apply.OPS)


if __name__ == "__main__":
    import unittest
    unittest.main()
