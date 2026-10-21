# Task 5: `audit prepare` e `audit decline` — report

## Implementato
- `bin/tollgate_flow/audit.py` (nuovo): `OK/REFUSED/NEEDS_CONFIRM`, `STEPS` (otto chiavi, parte fissa
  senza segnaposto; `<programma>`, `<id>`, `<fette>` li sostituisce chi stampa), `PrepareResult`,
  `AuditError`, `prepare`, `decline`, `adversarial_ok`, `peek`. La decisione è una funzione senza
  scritture (`_decide_spec`, `_decide_plan` -> `_Act`): `prepare` la esegue, `peek` la legge,
  `decline` ne riusa le precondizioni.
- `spec_audit`: i sei rami nell'ordine esatto di D2 (giro aperto; avversariale non passato;
  ciclo a lenti con conferma del costo; avversariale di conferma; ciclo a lenti di conferma con
  avversariale spento; `approve spec`). «Passato» = ultimo giro avversariale chiuso pulito (qualunque
  SHA) o sospeso (numero del giro in `audit_suspended`). Un giro aperto di un componente spento o
  su un altro SHA si chiude `superseded`.
- `plan` (L2): D3 (approvazione della spec letta in HEAD con `git.ls_files_at`/`text_at`;
  «committa …/spec-approval.md prima del giro del piano» se è solo su disco; spec cambiata dopo
  l'approvazione -> `reopen spec`), piano da `plan_path` o da `adopt.find_plan` (registrato con
  `scope.set_plan_path`), piano letto a HEAD, `plan-check` rieseguito sul blob in HEAD, giro del
  piano finché uno è pulito o sospeso su (blob del piano, blob della spec), poi
  `set_phase(..., "approval", "audit_clean")`. Con `plan_adversary` spento il passaggio è immediato
  (con le stesse precondizioni di `approve plan`: spec approvata, piano valido e committato).
- D12 (`_check_path`: a capo, `"`, controllo), D15 (`finalreview.launch_line`, `adopt.find_plan`
  pubbliche, `git.blob_at`), D19 (`paths.program_command` per ogni comando nei testi; nessun
  `tollgate audit` nudo), D1 (`closed_round` nel banco, niente `report_round`).
- `brief.py`: `AuditBrief` e `audit_brief` (codice, blob, riga JSON della decisione 5 come esempio
  esatto costruita con `json.dumps`, sola lettura, sezione e gravità, controlli per tipo, tabella dei
  task del piano con «candidato a essere diviso»).
- CLI: gruppo `audit` (`prepare [--confirm]`, `decline`), `AuditError` -> uscita 1;
  `cli_calls._COORDINATOR_ONLY` con `audit` (nessun segnale: non legge la sessione).
- `tests/flowkit.py`: `SPEC`, `spec_text(slices, pitch, note)`, `FlowLab.write_spec`,
  `write_l2_plan`, `closed_round` (D1), più `approve_spec_file` (spec-approval.md committato).

## Scostamenti dal piano / scelte
- I rifiuti con un passo (`fix_spec`, `write_spec`, `resolve`, …) tornano come
  `PrepareResult(REFUSED, ["rifiuto: …", "prossimo passo: …"])` e uscita 1; `AuditError` solo per
  errori d'ambiente (nessun lavoro, DB, git, config).
- `peek(conn, work)` restituisce il testo del passo senza «prossimo passo:»; per `open`/`reprint`/
  `confirm`/`advance` vale «lancia <programma> audit prepare» (come il ripiego della decisione 20).
- `decline` controlla le quattro condizioni del brief più «audit a lenti non già sospeso».
- Il costo (exit 3) stampa `conferma: audit a lenti: da 16 a <tetto> cicli di
  tollgate:spec-auditor, più i giri avversariali di conferma` e un passo con `--confirm` / `decline`
  (costante `CONFIRM_STEP`, non una chiave di `STEPS`, per non cambiarne l'insieme).
- Test in più di D2: `test_lens_corrections_do_not_trigger_adversarial_until_lens_closed`,
  `test_adversarial_confirmation_after_lens_closed`; più D3, D12, rami di rifiuto, peek, CLI.
- Il ciclo successivo a lenti dopo uno con rilievi passa al punto di vista seguente (regola della
  decisione 6: primo con contatore < 2 dopo l'ultimo usato), non allo stesso.

## TDD
- RED: `python3 -B -m unittest tests.test_audit_prepare` senza `audit.py` -> `FAILED (errors=1)`
  (ImportError). `tests.test_brief.AuditBriefTest` scritto prima del codice del brief; i test di
  `audit prepare` e `test_audit_is_coordinator_only` sono stati scritti dopo il codice
  (onestà: per questi non ho un RED di singolo test, solo quello dell'import mancante).
- GREEN: `python3 -B -m unittest tests.test_audit_prepare` -> `Ran 58 tests ... OK`;
  `tests.test_brief` 15 OK; `tests.test_check_cli_calls` 16 OK; manifest, layers, cli,
  finalreview, adopt, flowkit OK (113 test).

## Esito finale
`tests/run`: python3.11 `Ran 1546 tests ... OK`; python3 (3.13.5) `Ran 1546 tests ... OK`.
Nessun `__pycache__` nel commit (`git status` controllato).

## Fix round 1
Modifiche:
1. `_decide_plan`: con `plan_adversary` spento `_Act("advance", supersede=row)`: il giro del piano aperto si chiude `superseded`.
2. `brief._task_line`: la tabella dei task del brief del piano va in un recinto (`_block`, più lungo dei backtick del titolo); `DATA_NOTE` era già nel brief.
3. Un rifiuto (`fix_spec`, `fix_plan`) porta con sé il giro aperto su un altro SHA (`_Refuse.supersede`): `prepare` lo chiude `superseded` anche rifiutando. `_decide_spec` ora delega a `_spec_branches`.
4. `ValueError` di `audits.open_round` -> `AuditError` (uscita 1 con messaggio).
Test nuovi: `test_plan_adversary_off_supersedes_open_plan_round`, `test_fix_plan_refusal_supersedes_stale_open_round`, `test_fix_spec_refusal_supersedes_open_round_on_other_sha`, `test_open_round_value_error_is_an_audit_error`, `AuditBriefTest.test_plan_task_titles_stay_inside_a_fence`.
RED: `python3 -B -m unittest tests.test_brief tests.test_audit_prepare` -> `FAILED (failures=4, errors=1)` (i cinque nuovi).
GREEN: stesso comando -> `Ran 78 tests ... OK`.
Suite: `tests/run` python3.11 `Ran 1551 tests ... OK`; python3 (3.13.5) `Ran 1551 tests ... OK`.
