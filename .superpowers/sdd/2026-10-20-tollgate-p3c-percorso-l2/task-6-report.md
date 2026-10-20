# Task 6: report dei giri a SubagentStop

## Implementato
- `bin/tollgate_checks/audit_round.py` (nuovo, ordine 15, `component: None`): legge la riga JSON con `auditrules.parse_round_json`; componente del tipo spento: solo `subagent_finish`; impronta cambiata con `readonly_check`: `tampered_records`; JSON non valido: due veti (`rule: audit_round`), poi `subagent_finish` e `needs_you` «report del giro non valido: <campi>» (mai valori grezzi), giro aperto; valido: `subagent_finish` poi `audit_report`. Rilievi meccanici (`spec_pitch`, solo `spec-adversarial`, sul blob del giro): un `major` per sezione mancante, sommato ai conteggi dal check, righe passate in `extra`.
- `_common.awaiting_audit(ctx, row)`: giro aperto, tipo `audits.AGENTS`, riga `running`/`interrupted`, `started` non nullo e `>= opened`; ripiego `governing_work` se `row["work"]` è nullo.
- `subagent_stop.py`: salta gli agenti per cui `awaiting_audit` dà un giro; docstring corretta.
- `apply.py`: `audit_report` (OPS = 28). Rilegge il giro (non più aperto: evento `veto` «giro non più aperto»); scrittura atomica (tmp + `os.replace`) di `reviews/<N>/<tipo>-<n>.md` con `approvals.render_report`, messaggio in recinto (`brief.fence`, `DATA_NOTE`) troncato a 60.000 caratteri; `OSError`: evento `veto` «report non scritto: <errore>», giro aperto (D13); `audits.close_round`; per `spec-lens` rigenera `spec-lens-stato.md` (un `OSError` lì dà il veto «stato delle lenti non scritto», il giro resta chiuso); blocchi dei tetti con `audits.cap_reason` (D19): spec avversariale >= `spec_rounds` e non pulito, piano >= `plan_rounds` e non pulito, lenti `==` `spec_audit_cycles` con audit non chiuso; `phases.open_block` fuori transazione.
- `tests/flowkit.py`: `round_message(row, counts, kind=)` (modulo) e `FlowLab.report_round` (D1, D20: a partenza `lab.now = opened + 1 s`, documentato nel docstring con la nota sul ritorno indietro).
- `tests/test_check_audit_round.py`: 34 test (tutti i nominati dal brief più: esito dichiarato ignorato, intestazione piano con `plan_sha`, `spec_pitch` non applicato alle lenti, messaggio lungo, `cut`, numero errato, manomissione senza `readonly_check`, componente spento, `awaiting_audit` (started/opened/nullo/ripiego), cartella occupata da un file, percorso occupato da una cartella, stato lenti non scritto, `audit_report` su giro non più aperto, tetto non raggiunto/superseded non contano/oltre il tetto non riapre).

## TDD
- RED: le stesse prove contro l'albero di HEAD (git archive in una cartella temporanea, con solo i due file di test): `python3.11 -B -m unittest tests.test_check_audit_round` -> `FAILED (failures=14, errors=12)` su 34.
- GREEN: `python3.11 -B -m unittest tests.test_check_audit_round` -> `Ran 34 tests ... OK`.
- Suite: `tests/run` con python3.11 (1585 test, OK) e python3 3.13.5 (1585 test, OK); nessun warning né traceback.

## Scostamenti e note
- `report_round` restituisce un `subprocess.CompletedProcess` costruito dall'esito dell'hook (`returncode` = uscita, `stdout`, `stderr`), per rispettare la firma del brief; `hookkit.Lab.hook` dà un `HookResult` con `.exit`, quindi i test usano `.returncode`.
- `cut=True` (non definito nel brief) = messaggio troncato a metà della riga JSON (invalido); `bad_json=True` = solo prosa. `report_round` fa `SubagentStart` solo se l'agente non è già partito: così più chiamate sono più `SubagentStop` della stessa riga (veti 1 e 2, poi blocco) e un test può far partire l'agente, manomettere un file e poi riportare.
- Il banco non ha `info/exclude` con `.tollgate-run/` (lo scrive `start`): senza, il brief del giro 2 scritto da `audit prepare` cambia l'impronta dell'agente 1 già partito (`tampered`). `RoundCase.lab` lo aggiunge, come in produzione. Nessun codice di produzione cambiato per questo.
- In `test_component_off...` il giro si apre dalla libreria: con `spec_adversary` spento `audit prepare` non ne apre.
- `_audit_report`: il conteggio dei rilievi meccanici è già sommato in `counts` da `audit_round` (l'op scrive i conteggi ricevuti e le righe `extra` nel corpo).

## Dubbi
- Nessuno bloccante. Il corpo del report usa un titolo breve («Report <tipo> <n>, lavoro #<N>») scelto da me.
