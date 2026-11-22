# Revisione Task 7 (d455093..415ad58)

Metodo: pacchetto di revisione letto per intero; un solo controllo mirato su una copia `git archive 415ad58` in cartella temporanea (poi cancellata): ricerca di `user_decision` e di `record("subagent_finish"` in `bin/`. Nessun test rilanciato (evidenze dell'implementatore: suite 4311 verde con python3.11 e python3).

### Aderenza
- ✅ `report.transcript_usage` (`report.py:80-89`): per modello `input/cache_creation/cache_read/output`, un id una volta (ultima riga), modello assente o non stringa -> `"sconosciuto"`, `{}` senza file o senza righe `usage`. `transcript_tokens` (`:92-95`) ora riusa lo stesso lettore `_messages`: comportamento invariato.
- ✅ D3/D21: `_common.transcript_cost` (`_common.py:134-141`) fa una sola lettura; `tokens` = input+cache_creation+output su tutti i modelli (0 senza uso), `usage` `None` per vuoto. Tre casi di D3 + lettura unica coperti in `test_check_common.py` (`TranscriptCostTest`).
- ✅ I 15 `record("subagent_finish")` (contati nell'archivio: 15): 14 portano `tokens` e `usage` (`subagent_stop` 5 diretti + `_readonly`; `task_verdict` 2; `final_review` `_invalid`, revisore, verificatore; `audit_round` 3; `tampered_records` chiamata dai quattro moduli, tutti aggiornati). `budget_cut_records` resta senza (test `BudgetCutCostTest`).
- ✅ `subagents.finish` (`subagents.py:96-101`): `cost` subito dopo `subagent_stop`, solo con `usage` non vuoto; `data` esatto `{agent, type, task, tokens, by_model, usd: None, source: "transcript"}`; `tokens` è lo stesso valore di `subagent_stop`. `apply.py` passa `usage=d.get("usage")`. L'interruzione (`interrupt`) non emette `cost` (test).
- ✅ Ramo del budget invariato: `tokens > cap and running` (`subagent_stop.py:~108`); ora `tokens` è calcolato prima del ramo "senza lavoro" ma il valore è lo stesso.
- ✅ Decisione 6: nessun file di `bin/` fuori da `reviews.py` scrive `user_decision` (verificato: le altre occorrenze in `evaluate.py`, `openpr.py`, `brief.py`, `db.py` sono letture o schema; `reviews.py:283` è l'unico UPDATE). `cost` è già tra i tipi ammessi (`events.py:22`).
- ⚠️ Scostamento dichiarato: `test_approve_finding_emits_finding_event` in `tests/test_actapply.py` invece di `test_reviews.py`: giustificato (lì vive il flusso `approve finding`), ma il brief lo elencava in `test_reviews.py`. Accettabile. Il RED registrato dopo il codice (su una copia) non è verificabile dal diff: ⚠️.

### Punti di forza
- Un solo lettore tollerante per token e uso: i due numeri non possono divergere (il test somma `by_model` e lo confronta con `transcript_tokens`).
- Calcolo spostato prima di `tampered_records` in tutti i moduli: nessun ramo perde l'uso.
- Test per ramo con eventi `cost` asseriti nel valore (non solo nella presenza), compresi i veti che non chiudono (nessun `cost` finché la riga non chiude) e l'assenza di trascrizione in ogni ramo.
- Le trascrizioni finte stanno in `TemporaryDirectory(prefix="tollgate-")` con `addCleanup`; nessuna dipendenza da variabili della macchina (solo `TMPDIR`, che `tempfile` gestisce).

### Rilievi

**Critical**: nessuno.

**Important**
1. Duplicazione letterale di un helper di test: la stessa funzione che scrive la trascrizione finta (stesso JSON, 12/5/700/3) è copiata quattro volte: `tests/test_check_audit_round.py:641`, `tests/test_check_final_review.py:875`, `tests/test_check_task_verdict.py:1111` (nel diff), `tests/test_check_subagent_stop.py:995` (`write_transcript`), con `MODEL` e il dizionario atteso ripetuti. Come correggere: una sola `fake_transcript(case, ...)` in `tests/hookkit.py` (o `tests/helpers.py`) e un `USAGE`/`MODEL` condivisi; i quattro moduli la importano.

**Minor**
1. `tokens = sum(input+cache_creation+output)` è scritto due volte, in `report.transcript_tokens` (`report.py:95`) e in `_common.transcript_cost` (`_common.py:140`): stessa formula in due posti. Un helper `report.new_tokens(usage)` (o lasciare `transcript_cost` chiamare `transcript_tokens`... no, sarebbe una seconda lettura) la renderebbe unica. Il test `test_transcript_usage_by_model` la tiene allineata, quindi non è un bug.
2. Cambio di comportamento minimo: `_readonly` e l'implementatore senza lavoro prima passavano `tokens=None` (colonna invariata via `coalesce`, evento `subagent_stop` con `tokens: null`); ora passano `0` senza trascrizione, quindi scrivono 0 nella colonna e nell'evento. Innocuo (`cut` chiude prima, e quelle righe non portavano un valore), ma `tokens` falsy nel test «senza trascrizione» (`test_check_subagent_stop.py` `assertTrue(all(not s["tokens"]...))`) non distingue `None` da `0`. Se si vuole mantenere `None` senza trascrizione: `tokens if usage else None` nei due punti.
3. `test_user_decision_written_only_by_set_decision` cerca il testo `"SET user_decision"`: una riga SQL spezzata in due stringhe o con spazi doppi sfuggirebbe. Per una guardia basta, ma si potrebbe cercare con regex `SET\s+user_decision` anche su `UPDATE findings` spezzati.
4. `test_unreadable_path_has_no_usage` usa una directory (IsADirectoryError): copre l'`OSError` all'apertura, non un errore a metà lettura (che `_messages` non cattura: preesistente, non introdotto qui).

### Valutazione
**Qualità del task:** Da correggere (lieve).
**Motivo:** i requisiti di D3, D21, dei 14 punti e della decisione 6 sono rispettati e verificati sul diff, senza conteggi doppi né punti rimasti senza `usage`; resta solo la duplicazione dell'helper di test in quattro file (Important per rubrica, correzione meccanica) e rifiniture minori.
