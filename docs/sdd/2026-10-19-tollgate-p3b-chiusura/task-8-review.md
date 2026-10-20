# Revisione Task 8 (a336123..e7aef10)

Verificato: letto il pacchetto, `reviews.py`, `runner.py`, `task_verdict.py`, `_common.py`, `subagents.py`; eseguiti `python3 -B -m unittest tests.test_check_final_review tests.test_checkpoint` (29 test, OK) e `len(apply.OPS)` = 27.

### Aderenza
- ✅ `awaiting_final` (`_common.py:107-127`): running e interrupted, ruolo reviewer/verifier, specialisti L2 via `cycle["reviewers"]`; `subagent_stop.py:67-68` li salta.
- ✅ `final_review.py`: ordine 15, componente `final_review`, tampered con `readonly_check` (r.37-39), messaggio da `last_assistant_message` o `subagents.report` (r.43), JSON assente o non valido -> `subagent_finish(done)` + `needs_you` (r.20-24), nessun veto, nessuna scrittura diretta nel DB.
- ✅ Decisione 7: revisore `interrupted` per sola lettura conta (test), uno che ha cambiato file è `tampered` (stesso ramo di tampered; `finish` accetta ogni stato).
- ✅ Decisione 6 / carry (dalla revisione del Task 5): l'esito viene da `close_cycle`, non dall'`outcome` dichiarato; test `declared_outcome_does_not_decide_the_cycle` e `declared_needs_you`.
- ✅ Carry (dal Task 3): `close_cycle` chiamato solo con stadio `verify` e zero rilievi senza esito (`apply.py` `_review_report` e `_finding_verify`); `set_phase`/`open_block` fuori transazione (`close_cycle` e `verifier_incomplete` lo impongono con `in_transaction`).
- ✅ Ruling del Task 7: contatore dei riporti incompleti in `reported[VERIFIER]`, `needs_you` «verificatore senza esito su: <id>» dal secondo, mai `unverified` automatico (`reviews.py` `verifier_incomplete`; test `omits_ids_twice` e `completes_on_second_run`).
- ✅ Criterio 40 (rilievo senza regola `rejected`, non al verificatore), criterio 38 (specialisti allo stesso verificatore), `task_reviewer` invariato, `CAPS` con `reviews.CAP_REASON` -> «cicli di revisione», `OPS` = 27.
- ✅ Tutti i test del brief presenti e con asserzioni reali.
- ⚠️ Dubbio del report («apply non può iniettare avvisi»): impreciso. Il runner (`runner.py` righe ~284-289) cattura già `ValueError` dall'applier e produce un inject «registrazione non applicata»; a `subagent_stop` l'inject viene solo scritto nel log (`adapter.NO_INJECT_KINDS`, `runner.py:303`). Quindi sollevare sarebbe stato innocuo e avrebbe lasciato traccia nel log; l'`except ValueError: return` la perde. Non è un errore di correttezza (il carry chiedeva «ignorato», e il comportamento non fa cadere l'hook).

### Punti di forza
- Modulo piccolo, una responsabilità, riusa `_common` (tampered, impronta) e `reviews` senza duplicare le regole del ciclo.
- Fail-closed ovunque: `_final_rules` senza diff leggibile fa bloccare ogni `R-…`; riporti doppi o fuori stadio ignorati senza eccezioni.
- Test del verificatore completi (tampered, non atteso in `review`, secondo giro, riporto doppio).

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `final_review.py:13` / `subagent_stop.py:67-68`: `subagent_stop` salta sempre i revisori finali in attesa, ma `final_review` ha `component: "final_review"`. Con `final_review=false` impostato dopo l'apertura del ciclo, il revisore che si ferma resta `running` (nessuno lo chiude). Caso raro (`finalreview.py:89` rifiuta di aprire cicli a componente spento). Correzione: `component: None` e controllo dentro `decide`, oppure fare cadere `subagent_stop` su `awaiting_final` solo se il componente è acceso.
2. `apply.py` `_final_rules` (`files = [c.path …]`, base solo `work_base_sha`) ricalca `finalreview._profiles` (`finalreview.py:112-114`) ma senza il fallback `default_ref(main)` di r.87. Con `work_base_sha` nullo i file sono vuoti e nessun profilo è attivo (fail-closed, più severo del brief). Meglio un helper unico.
3. `apply.py` `_review_report`: `except ValueError: return` senza traccia (vedi ⚠️). Basterebbe lasciar salire l'eccezione (il runner la riporta) oppure un `events.record_event`.
4. Test mancanti: revisore `interrupted` che ha cambiato file (decisione 7, parte negativa); nessun test asserisce `len(apply.OPS) == 27`.
5. `_common.py` `awaiting_final`: lo stadio `verify` accetta qualsiasi riga `tollgate:finding-verifier` del lavoro, anche di un ciclo precedente; il `code` per ciclo nel parser lo protegge, quindi solo igiene.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti del brief, del carry (tre sezioni), della ruling del Task 7 e delle decisioni 5-8 soddisfatti, test verdi e significativi; restano solo minori (componente spento, helper dei profili duplicato, traccia del riporto scartato).
