# Revisione Task 13 (c63f8a0): `finish check` sul gate, campi del blocco, `--from-gate`

### Aderenza
- ✅ Contratto di `finishcheck.check`: firma, `OK/RED/REFUSED`, `CheckResult`, chiavi di `items` e di `finish_report` (`gate` è solo aggiunto; `open-pr` legge solo `items`, `openpr.py:322`). `_saved` legge `report.get("gate", {})`: un report vecchio funziona. Fissato da `test_contract_unchanged`.
- ✅ Decisione 3: in `finishcheck.py` non resta logica di scope, must-have o approvazioni (spariti `_approved_spec_blob`, `_must_have`, `_approvals`); `_check` chiama `evaluate.evaluate` e fa solo la proiezione sulle voci della DoD (`FOLDED`). Verde = DoD verde e `ev.red` vuoto (`finishcheck.py` dopo `compute_dod`).
- ✅ Decisione 9: l'unica differenza è `plan_changed`, asserita a parte da `test_plan_change_is_the_only_difference`. Lo scope locale ora viene dal blob di `plan_sha` e non dal DB: equivalente, perché il DB lo riempie `register_plan` dallo stesso piano.
- ✅ Strati: `_gate_inputs` è in `tollgate_flow`; `tollgate_gate` non importa `db`/`sqlite3`; l'import di `openpr` dentro la funzione evita il ciclo.
- ✅ `--from-gate` (`fixtask.py:_gate`): solo commenti con `author.login` in `BOT_LOGINS`, prefisso `GATE_MARKER`, SHA da `comment.marker_sha` (40 esadecimali, `comment.py:34`), rifiuto senza SHA. Il testo del commento resta dato (recinto invariato). I test coprono SHA del marcatore diverso da HEAD, autore diverso, entrambe le forme di login, marcatore senza SHA.
- ✅ Blocco: `FIELDS` con le due voci in coda, `prblock.DEFAULTS` (Task 4) fa leggere un blocco vecchio; `test_fields_order_with_new_fields`. `test_facts_keys_match_block_fields` è tornato al confronto esatto. `findings[].blocking`, `tasks_over`, `skills_absent` in `openpr.facts`; `size_reason` = ultimo non nullo (`_size_reasons`, `openpr.py`); evento `skills_absent` in `events.EVENT_TYPES` e registrato in `taskcmd` nella stessa transazione di `assign`; `size_reason` percorre `subagent_stop` → `record` → `apply` → `subagents.finish` e arriva nell'evento (troncato a 500).
- ✅ D17d: `openpr.issue_labels` pubblica, usata da `finishcheck`.
- ✅ Scelte dichiarate: `IssueFacts(..., "open", ...)` è corretto, perché `Context.waiver_issue` (`evaluate.py:78-90`) con issue valida e `open` dà `n`, e con `issue=None` in locale dà `n` (non `None`), quindi le deroghe valgono in entrambi i casi. `finish check` con `gh` assente/offline: `ghcli.run` trasforma `FileNotFoundError` e timeout in `GhError` (`ghcli.py:55-58`), e `issue_labels` avvisa e continua (test `test_issue_unreadable_warns_and_continues`). `_tasks_over` salta i commit spariti: accettabile, il campo è informativo.
- ✅ Riscrittura di `test_level_minimum_from_issue_labels`: giustificata dal costo dichiarato della decisione 20 e dal brief (D11); il test continua a provare che il blocco porta `level_minimum` L2.
- ⚠️ La suite completa non è stata rilanciata (regola del revisore); mi fido dell'evidenza del report (2308 test, due interpreti).

### Punti di forza
- La proiezione sulla DoD è piccola e leggibile; le voci non nella DoD (livello, file di tollgate) si stampano come `rosso:` e non si perdono; le voci di `attenzione` sono raggruppate come nel gate (`attention.group`).
- I rossi della famiglia `diff` sono sempre piegati in `guard_scope`; `must_have` ed `l2` non possono dare rossi non stampati (`must_have` esce a L0, `l2` solo L2), quindi non esiste il caso «rosso senza motivo».
- `test_stale_approval_still_fails_dod_locally` fissa il rilievo I-4; `test_open_pr_block_feeds_gate` usa il programma vero di `open-pr` e `verdict.main`, con la prova a contrario del blocco senza `blocking`.
- `_size_reason` taglia il testo del subagente; `fixtask` rifiuta con messaggio chiaro invece di ripiegare su HEAD.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `tests/test_criteria_p4.py:46-62` (`AgreementTest.both`): il test è solo in parte non tautologico. Intercetta `evaluate.evaluate` e rilancia lo stesso oggetto `inputs` con `where=GITHUB`, `pr` e `base_ids` sostituiti. Prova che il ramo `where` di `evaluate` non altera le famiglie condivise (utile: è il cuore della decisione 9), ma non prova che gli ingressi costruiti dal gate vero (configurazione della punta del predefinito, blocco letto dal corpo, base = merge-base, comandi dagli artefatti) diano lo stesso albero giudicato. Quel pezzo è coperto solo in parte da `BlockFeedsGateTest.judge` (verdetto verde, non confronto di chiavi). Correzione possibile: nel banco `bench()` far girare `verdict.main` come in `judge` e confrontare le chiavi rosse del commento con quelle di `finish check`. Il piano chiede il confronto con `evaluate(where="github")`, quindi non blocca.
   Inoltre l'uscita del programma vero è asserita solo per `returncode == 1` e per la presenza di `src/extra.py`; il test cancellato non compare nelle righe stampate (non asserito).
2. `finishcheck.py:_gate_inputs`: il parametro `environ` è nella firma ma inutilizzato (dichiarato nel report; la firma è quella del brief). Il parametro `warnings` aggiunto è un secondo canale di uscita per un avviso: un ritorno `(inputs, warning)` sarebbe più pulito, ma il contratto del brief è il tipo `GateInputs`. Nessuna azione richiesta.
3. `finishcheck.py` `details["approvals"]` per `approval_stale`: le prime 5 righe di ogni voce possono includere righe di diff dei documenti (dichiarato nel report). Solo rumore nell'uscita.
4. Ogni `finish check` ora costa una chiamata `gh` (fino a 60 s di timeout offline, `ghcli.py:17`) e un `git` per task in `_tasks_over`. Accettato dalla decisione 20; vale la pena citarlo nella documentazione dell'uso offline.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** i requisiti e le voci di `carry.md` sono tutti soddisfatti sul diff e il contratto di `finish check` è invariato; `finishcheck` non duplica logica del gate e gli strati sono rispettati. Restano solo rilievi Minor, il principale è che `AgreementTest` confronta il calcolo sugli stessi ingressi invece degli ingressi costruiti dal gate vero.
