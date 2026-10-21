### Task 6: Report dei giri a `SubagentStop`

**Files:**
- Create: `bin/tollgate_checks/audit_round.py`
- Modify: `bin/tollgate_checks/_common.py` (`awaiting_audit`), `bin/tollgate_checks/subagent_stop.py` (salta i giri in attesa; docstring «gli avversari sono di P3b» corretta), `bin/tollgate_hooks/apply.py` (`audit_report`)
- Test: `tests/test_check_audit_round.py`

**Interfaces:**
- Produces in `_common.py`: `awaiting_audit(ctx, row) -> sqlite3.Row | None`: il giro aperto del lavoro del subagente se `row["type"] == audits.AGENTS[giro.kind]`, la riga è `running` o `interrupted` e `row["started"]` non è nullo né precedente a `giro.opened` (decisione 4).
- Produces: modulo `audit_round` (`CHECK = {"api": 1, "events": ["subagent_stop"], "component": None, "order": 15}`; il componente del tipo si controlla dentro con `audits.COMPONENTS`): decisione 5; con il componente del tipo spento il giro si chiude come se l'agente non contasse (`subagent_finish` e nessun report).
- Produces in `apply.py`: `audit_report` (dati: `work`, `kind`, `number`, `counts`, `body`, `extra`: righe dei rilievi meccanici). Rilegge il giro: se non è più aperto con quel numero (superato, chiuso) ignora e registra l'evento `veto` {event: "subagent_stop", rule: "audit_round", reason: "giro non più aperto"}, mai un'eccezione. Scrive il report con `approvals.render_report` in scrittura atomica (file temporaneo e `os.replace`), chiude il giro, rigenera `spec-lens-stato.md` per le lenti, poi i blocchi dei tetti con `phases.open_block` fuori transazione. `apply.OPS` passa a 28 voci.

- [ ] **Step 1: Test** `test_check_audit_round.py` (`FlowLab` L2 con un giro aperto):
  - `test_valid_report_written_and_round_closed` (file `spec-adversarial-1.md` con intestazione valida per `parse_report_header`, `outcome` calcolato, evento `spec_audit_round`);
  - `test_missing_cosa_non_fare_adds_major` (criterio 41, seconda frase: spec senza `## Cosa non fare`, l'agente dichiara zero rilievi → `major: 1`, giro non pulito, riga «rilievo meccanico» nel report);
  - `test_spec_pitch_off_no_mechanical_finding` (criterio 18, `spec_pitch`);
  - `test_bad_json_vetoed_twice_then_needs_you`;
  - `test_tampering_agent_needs_you` (impronta cambiata);
  - `test_handback_report_used_in_auto_mode`;
  - `test_late_report_of_superseded_round_ignored` (Review Focus 3: l'agente del giro 1, partito prima che il giro 2 dello stesso tipo si aprisse, non riceve veti né tocca il giro 2; `subagent_stop` lo chiude `done`; il giro 2 si apre chiamando `audit.prepare(..., now=<dopo lo started dell'agente 1>)` dalla libreria, non dalla CLI, perché l'orologio del banco è avanti rispetto all'ora reale);
  - `test_invalid_report_keeps_round_open_and_reason_has_no_raw_values`;
  - `test_fourth_dirty_adversarial_round_opens_cap_block` (criterio 24: quarto giro con `major` → `needs_you` con `CAP_REASONS["spec-adversarial"]`);
  - `test_lens_cycle_regenerates_state_file`;
  - `test_lens_cap_opens_block` (30 cicli con l'audit aperto);
  - `test_plan_round_cap_after_two`;
  - `test_task_reviewer_and_final_reviewer_paths_unchanged`;
  - `test_report_file_committable_and_protected` (Review Focus 4: `git add docs/superpowers/reviews/7/spec-adversarial-1.md` e `git commit` dal coordinatore in `spec_audit` attraverso `PreToolUse Bash` → ammessi; `PreToolUse Write` sullo stesso file → `deny`);
  - `test_every_branch_emits_subagent_finish`;
  - `test_ops_count_is_28` (triage 40).
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: report dei giri di audit a SubagentStop, tetti dei giri».

---


**Dal Task 5 (spostato qui dalla ruling D1):**
- Produces in `tests/flowkit.py`: `FlowLab.report_round(kind: str | None = None, counts: dict | None = None, *, bad_json=False, cut=False) -> subprocess.CompletedProcess` (legge il giro aperto, porta l'orologio del banco a `opened` più un secondo (`lab.now`), poi scrive `SubagentStart` e `SubagentStop` dell'agente del giro con il JSON corretto, attraverso `hookkit.Lab.hook`). **Orologi:** `audit prepare` lanciato dalla CLI usa l'ora reale, mentre gli hook del banco usano l'ora di `hookkit` (dal 9 ottobre 2026): senza questo allineamento nessun agente simulato apparterrebbe al giro. I test non tolgono mai la condizione `started >= opened` per farli passare.
