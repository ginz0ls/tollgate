# Task 13 — Report

## Implementato
- Agenti: `agents/spec-adversary.md`, `agents/spec-auditor.md` (attribuzione a prd-audit), `agents/plan-adversary.md`; strumenti e modelli della decisione 21; una sola riga JSON della decisione 5 per agente.
- Skill nuove: `skills/spec-audit/SKILL.md` (ciclo, codici 0/1/3, righe «prossimo passo» con la parte fissa di `audit.STEPS` e `CONFIRM_STEP`, tetti e sospensione), `skills/spec-audit/references/dimensioni.md` (copia di prd-audit con riga di attribuzione in testa; il percorso scritto da `audit._write_brief` e `Path(BIN_PATH).parent.parent/skills/spec-audit/references/dimensioni.md` coincide con questo file), `skills/reopen/SKILL.md` (solo utente, `act apply`).
- Aggiornate: `approve` (spec/plan, argument-hint, description, tolta la frase P3c), `start` (`--spec`, L2 a tre fasi, uscita 3 per spec cambiata, tolta la frase P3c e il testo morto sulla PR chiusa sotto «1, rifiuto»), `resolve` (sospensioni dei tetti), `finish` (forma `- **n, …**`, voce `approvals` L2), `status` (tetti dell'audit, tolto «arriva con P3b»), `sync` (riga `- **0, riallineato**`), `agents/implementer.md` (apici singoli -> virgolette doppie, riga 79).
- Test: `tests/test_skill_contract.py` (codici = costanti per start/finish/sync/spec-audit; parte fissa di `audit.STEPS`; sottocomandi nel parser, anche annidati; nessun «P3c»); `tests/test_manifest.py`: argument-hint di start con `--spec` (D10), `test_audit_agents_frontmatter`, `test_audit_json_fields_in_agent_text`, `test_reopen_user_only_and_spec_audit_model_invocable`, `test_agents_use_program_command_form`, `test_dimensioni_copied_with_attribution`, reopen/spec-audit nelle liste esistenti.

## TDD
RED: `python3 -B -m unittest tests.test_skill_contract tests.test_manifest` -> `Ran 33 tests ... FAILED (failures=5, errors=8)` (file reopen/spec-audit/agenti assenti, `finish` senza righe `- **n,`, «P3c» in approve e start, apici singoli in implementer, argument-hint senza `--spec`).
GREEN: stesso comando -> `Ran 33 tests ... OK`. Suite completa `tests/run`: python3.11 e python3 (3.13.5) `Ran 1725 tests ... OK`.
`claude plugin validate --strict .` -> `Validation passed`.

## Scostamenti / note
- Riga 77 del triage: i test di sola sottostringa su finish/start restano (non erano codici d'uscita); i codici sono ora nel contratto.
- `argument-hint` di start: `"#N [L1|L2] [--spec <percorso>]"`.
- Non ho letto `prd-audit/SKILL.md`: il modello del ciclo viene dalle decisioni 3, 4, 6, 7 e dal brief; letto solo `references/dimensioni.md`.
- Nel contratto la sezione di `spec-audit` è `## Codici d'uscita`; la lista «Righe prossimo passo» è fuori dalla sezione per non confondere i codici.

## Dubbi
Nessuno bloccante. Il testo di `spec-audit` fa riferimento ai tetti senza numeri fissi (letti dalla config).

## Fix round 1
Modifiche:
- I-1: `skills/spec-audit/references/verifica-fatti.md` (copia con attribuzione in testa, il rimando di L8 non è più morto). `agents/spec-auditor.md` riscritto nelle sezioni «Il ciclo» e «Quando il ciclo è vuoto»: punto di vista dichiarato in cima, inventario = sezioni della spec (L10), `verifica-fatti.md` per L8, «cerca la regola, non il caso», stati `[VERIFICATO]`/`[RAGIONATO]`/`[SCARTATO]`, vuoto = nessun blocker/major/moderate (come `auditrules.outcome`), tre scartati anche con soli minor. Contenuto di WebFetch dichiarato non fidato in `spec-adversary` e `spec-auditor`.
- I-2: `skills/start/SKILL.md`, L2 `spec_audit` rientrante (spec già sul ramo, anche con `--spec` e spec cambiata -> commit se serve e `/tollgate:spec-audit`; brainstorming solo senza spec); fase `plan` anche per lavori nati con `--spec`, piano della sola fetta.
- Minori: test D19 su `fisso + " `<id>`"`; `test_options_exist_in_parser` (opzioni delle skill contro `build_parser()`, escluso `--force` di git); `test_lens_brief_method_file_exists`; `test_exit_codes_keep_their_meaning` (significato abbinato a ogni codice); `spec-audit` cita i messaggi stderr del codice 1 e la fase `approval`; `finish` chiarisce chi committa; `reopen` (nuovo giro solo se la spec cambia); test del brief diviso in `test_reopen_user_only` e `test_spec_audit_model_invocable`; `test_dimensioni_copied_with_attribution` verifica che ogni `.md` nominato esista con attribuzione; nuovi `test_spec_auditor_carries_the_method`, `test_start_l2_spec_audit_is_reentrant`.

RED (nuovi test contro i file del commit f6b5fc4, copia in scratchpad): `Ran 38 tests ... FAILED (failures=3)`: `test_lens_brief_method_file_exists`, `test_dimensioni_copied_with_attribution`, `test_spec_auditor_carries_the_method`.
GREEN: `python3 -B -m unittest tests.test_skill_contract tests.test_manifest` OK; `tests/run`: python3.11 e python3 `Ran 1731 tests ... OK`; `claude plugin validate --strict .` -> `Validation passed`.
