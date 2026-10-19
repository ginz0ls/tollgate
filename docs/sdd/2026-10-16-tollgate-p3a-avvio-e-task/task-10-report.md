# Task 10: report

Commit: 90b2ebe «tollgate P3a: agenti implementer e task-reviewer, skill del flusso, marketplace e licenze».

## Implementato
- `agents/implementer.md`, `agents/task-reviewer.md` (frontmatter e attribuzione come da brief; corpi derivati da implementer-prompt.md e task-reviewer-prompt.md di Superpowers 7.0.0, letti in sola lettura).
- `skills/{start,execute,status,approve,resolve,setup}/SKILL.md`, con programma `"${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` tra virgolette e ripiego sulla riga `tollgate: programma`.
- `.claude-plugin/marketplace.json` (forma V4), `.claude-plugin/plugin.json` (author, license), `LICENSE`, `LICENSES/superpowers-MIT.txt` (copia del LICENSE 7.0.0).
- `start`: uscite 1/3/0/4, EnterWorktree con ripiego `cd <percorso> && claude`, L0/L1/L2, commit del piano dopo writing-plans, rimando a `/tollgate:execute`.
- `execute`: passo 0 con worktree pulito e piano committato, ciclo di 6.3, riprese 1-3 con SendMessage e 4-5 con nuovo Agent `-r<giro>` e `model: inherit`, guardia del contesto, `/tollgate:finish`, riga «mai subagent-driven-development» (minuscolo, C13).
- `setup`: propone `<radice>/statusline/ctx '<comando attuale>'` (C21), non scrive in `~/.claude`.

## TDD
RED (prima dei file): `python3 -B -m unittest tests.test_manifest` -> `Ran 13 tests ... FAILED (errors=9)`, tutti FileNotFoundError su skills/agents/LICENSE/marketplace.json.
Un secondo RED durante la scrittura: `test_execute_forbids_sdd_as_executor` falliva per la maiuscola di «Mai»; corretto il testo della skill.
GREEN: `python3 -B -m unittest tests.test_manifest` -> `Ran 13 tests ... OK`.
`tests/run`: `== Python 3.11.16 Ran 949 tests OK`; `== Python 3.13.5 Ran 949 tests OK`.
`claude plugin validate --strict .` -> `Validating marketplace manifest: .../.claude-plugin/marketplace.json` / `✔ Validation passed`.

## Test aggiunti (tests/test_manifest.py)
test_agents_frontmatter, test_user_only_skills, test_skills_use_quoted_program, test_execute_forbids_sdd_as_executor, test_start_skill_covers_exit_codes_and_levels, test_setup_skill_does_not_write_settings, test_plugin_and_marketplace_json, test_license_files, test_brief_fields_match_agent_text. Il vecchio `test_off_on_skills_user_only` resta.

## Scostamenti e dubbi
- Il revisore: `task start`/`review-prepare` non stampano il tipo del revisore (la CLI non lo espone: solo `tasks.reviewer_type` nel DB). La skill `execute` usa sempre `tollgate:task-reviewer`; il revisore per area (profili verticali) richiede che la CLI stampi il tipo, da fare con il sotto-progetto B. Segnalato nella skill.
- `skills/status` indica `/tollgate:finish` (P3b) come passo finale, come le altre skill.
- Il report dell'implementatore non ha un file: il brief (brief.py) chiede il solo blocco JSON nel messaggio finale, quindi l'agente non scrive `REPORT_FILE` come in Superpowers.
- `tests/run` si ferma al primo interprete se fallisce (set -e): il secondo giro con python3 è stato eseguito dopo il fix, entrambi verdi.

## Fix round 1
Rilievi 1-8 con le decisioni del controller.
- Revisore: `task start` stampa `revisore: <tipo>`; `task review-prepare` stampa percorso e `revisore: <tipo>` (taskcmd.reviewer_type, cli.py); la skill execute lancia quel tipo.
- Verdetto registrato: la skill lancia `task done k` e, se rifiuta per changes, `task start k --fix`; i messaggi di rifiuto indicano il comando giusto.
- Ripresa: passo 0 con `status --checkpoint`, riga prossimo passo e tabella stato -> comando; `checkpoint.next_step` copre plan e spec_audit/approval.
- start L1 rientrante; needs_you al --fix successivo al quinto giro; radice quotata in setup; esempi JSON del revisore validi.
- Test: test_taskcmd, test_checkpoint, test_manifest (JSON parsabili, punti 1-3 nel testo di execute, start rientrante).
- RED: unittest test_taskcmd test_checkpoint -> FAILED (failures=4, errors=3) prima del codice.
- GREEN: tests/run -> 3.11.16 Ran 955 OK; 3.13.5 Ran 955 OK; claude plugin validate --strict . -> Validation passed.
