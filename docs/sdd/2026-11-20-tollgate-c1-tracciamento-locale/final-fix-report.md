# Giro di correzione finale di C1: report

Ramo `c1-tracciamento-locale`, worktree `c1`. Nessun subagente, nessun `claude`, nessuna rete, nessuna evidenza toccata, nessun profilo o agente toccato.

## Rilievi nuovi (F1-F6)

| Voce | Cosa ho fatto | Test | Esito |
|---|---|---|---|
| F1 | `task_verdict` passa `cost_task` (il task rivisto) nei tre rami che chiudono il revisore (verdetto valido, veti esauriti, manomissione); `tampered_records` prende `cost_task`; l'operazione `subagent_finish` di `apply` lo passa a `subagents.finish`, che lo usa solo per `data.task` dell'evento `cost` (riga del subagente e `subagent_stop` invariati). Spec 18.4 e `gestionale.md` (che cosa conta `by_task`) aggiornati | `tests/test_subagents.py` (`test_cost_task_overrides_only_the_cost_event`, `test_cost_task_defaults_to_the_row_task`), `tests/test_check_task_verdict.py` (`test_cost_carries_the_reviewed_task`, e il task dei `cost` nel caso tampered/veti). RED: `TypeError` su `cost_task` e `[None, None] != [1, 1]` | verde |
| F2 | `perch[eèé]`, `"perchè": "why"` in `_FIELD`, `unicodedata.normalize("NFC", …)` sul testo prima di `splitlines`; docstring aggiornata | `test_perche_with_grave_accent_or_decomposed_e` (`perchè`, `Perchè`, `PERCHÈ`, NFD con acuto e con grave). RED: 6 fallimenti (`manca il campo «perché:»`) | verde |
| F3 | `_common._size_line` compone la riga con `worksize.preview` (segnali di `apply._level`: livello nuovo, task registrati, 0 aree, `slices or 1`, causa `level`) e `level_records` la aggiunge all'iniezione, sia nel ramo generico sia nel caso L0 → L2 (dove c'è il `level`). Spec 6.1 (quando e la riga) aggiornata | `tests/test_check_post_edit.py`: `test_level_rise_says_the_new_size` e l'asserzione nuova in `test_l0_with_sensitive_path_goes_l2_in_plan` (la riga iniettata coincide con `applied` e `reason` dell'evento). RED: `'taglia: medio — livello L2' not found` | verde |
| F4 | Spec 11.4 e `gestionale.md`: 0 = «mai» solo per `events_days`, «subito» per le altre due; il limite di un repo vale per gli eventi di tutti i repo dello stato della macchina (l'archivio li tiene) | n/a (documenti, `tests.test_docs` verde) | fatto |
| F5 | Spec 12.2 e decisione 1 del piano C1: «con `size` nullo» al posto di «non calcolata» | n/a | fatto |
| F6 | `gestionale.md`, «Limiti noti»: `repo_key` con un remoto locale è un percorso della macchina; la frase «si può mostrare ovunque» rimanda al limite | n/a | fatto |

## Righe «da correggere» del triage

| Riga | Cosa ho fatto | Test | Esito |
|---|---|---|---|
| 2 | `events._fsync_path` (file e cartella `archive/`) in `archive_and_prune`, dopo `write_atomic` e prima del `DELETE`; `fsutil.write_atomic` non cambia | `test_archive_is_fsynced_before_the_delete` (mock di `os.fsync`: una chiamata su un file e una su una cartella, a eventi ancora tutti nel DB) e `test_write_atomic_itself_does_not_fsync` | verde |
| 3 | Tolto `fsutil` dall'import del sottoprocesso di `ConcurrencyTest.test_three_writers` | test esistente | verde |
| 7 | In `adopt` la taglia «start» si decide dopo il passo del tetto, con il livello letto dal DB (`phases.get_work`); anche `approve_spec` usa quel livello | `AdoptSizeTest.test_size_at_start_is_decided_after_the_level_cap`. RED: `('start', 'L2')` invece di `('start', 'L1')` | verde |
| 8 | `approve_plan`: la riga della taglia sta prima di «Committa … poi /tollgate:execute.», come in `approve_spec` | `test_approve_plan_says_size_before_the_commit_hint` | verde |
| 9 | Test diretto dell'operazione `level` con livello uguale (nessuna taglia) e più basso (`TransitionError`, nessuna taglia) | `LevelSizeTest.test_level_op_with_same_or_lower_level_does_not_decide_size` | verde |
| 12 | Riga spezzata in `test_refused_forms_are_not_recorded` | test esistente | verde |
| 13 | Test: `approve size grande` lascia `slices` nullo e non propone le issue | `test_approve_size_large_leaves_slices_and_proposes_no_issues` | verde |
| 16 | Tolta la condizione morta `name != "-"` in `cli_calls.py:69` (il numero di riga 95 della tabella non corrisponde più al file; la condizione era quella) | `tests.test_check_cli_calls` | verde |
| 17 | Chiusa con F2 (NFC) | stesso test di F2 | verde |
| 19 | Casi nuovi in `test_ask_user_question_never_denied_by_runner_failure`: `Bash` con un `tool_name` annidato (e con il testo citato) e input troncato resta un controllo (uscita 2) | quel test | verde |
| 20 | `session._source`: `source` solo se stringa, tagliata a 32 caratteri (`SOURCE_MAX`), altrimenti `None` | `test_session_start_source_is_a_trimmed_string_or_none` | verde |
| 22 | Riga lunga spezzata in `tests/test_ruling_cmd.py` (la riga 1, docstring di 102 caratteri, non è del caso nuovo e non l'ho toccata) | `tests.test_ruling_cmd` | verde |
| 23 | `report.new_tokens(usage)`, usata da `transcript_tokens` e da `_common.transcript_cost` | `test_new_tokens_leaves_cache_read_out` | verde |
| 24 | `_readonly` e il ramo dell'implementatore senza lavoro passano `tokens=None` quando l'uso è `None`; il ramo del tetto resta con 0 | `test_no_transcript_means_unknown_tokens_not_zero` | verde |
| 25 | La guardia di decisione 6 usa una regex `SET\s+(colonne,)*user_decision\s*=` (anche su più righe e dopo un'altra colonna), con tre testi di controllo | `test_user_decision_written_only_by_set_decision` | verde |
| 27 | `snapshot._answered` si calcola una volta in `build` e si passa a `_work` e `waiting_items(conn, work, answered=None)` | `test_answers_are_scanned_once_per_snapshot` (traccia SQL: una sola scansione con due lavori) | verde |
| 28 | `gestionale.md`, limiti noti: con `events_days > 0` `cost.tokens`, `by_task` e `last_event_at` possono scendere o diventare nulli | n/a | fatto |
| 29 | `gestionale.md`: percorso `docs/verifiche/evidenze/eval-b8/`, 88 file `tollgate.db` di schema 6, come ripetere la misura (primo, mezzo, ultimo per percorso ordinato: ho riverificato 11, 26 e 46 eventi su copie in `tollgate-*` temporanee, poi cancellate) | n/a | fatto |
| 31 | Intestazione di `spikes/run-b1-flow.sh` e riga di `registra` nel modo `controlla`: `eventi-c1.jsonl` e `snapshot.json` | `bash -n`, `tests.test_b1_scripts` (139 OK) | verde |
| 33 | Rapporto della prova: i due `veto` del passo1 (seq 4 `coordinator`, seq 5 `plan_check`) sono voluti | n/a | fatto |
| 34 | Rapporto: «restano solo i token…» vale per `eventi-c1.jsonl`; `events.jsonl` ha il dettaglio | n/a | fatto |
| 35 | Rapporto: «8 file modificati dall'anonimizzazione su 41 nella cartella» | n/a | fatto |
| 36 | Rapporto: esito di `claude plugin validate --strict` letto da `validate/validate-1.txt` (passa, un solo avviso sul README della copia) | n/a | fatto |
| 37 | Spec: l'intestazione della rev 36 cita D19 | n/a | fatto |
| 38 | Spec 7.2 (`PreToolUse` di `AskUserQuestion`): senza domande leggibili `stop_asked` non si registra | n/a | fatto |
| 39 | Spec 6.1: `adopt` decide con le tre cause `start` (dopo il tetto), `approve_spec` e `plan` | n/a | fatto |

Sezione 20 della spec (riga 36): una frase che dice che la revisione finale ha corretto F1-F6 e i minori del triage.

## Sezione 8 del piano principale di C

Al posto della riga che rimandava al triage: riga 6 (operazione `plan` in due transazioni, per C5), riga 18 (`_asks_user` e `json_str` dipendono dall'ordine delle chiavi, per C6) con i loro motivi, e la voce di F6 per C4 (filtrare `repo_key` con la lista «non va mai» del progetto 7). La riga C1 della sezione 2 resta «eseguita sul ramo `c1-tracciamento-locale`, in attesa del merge».

## Scostamenti e dubbi

- F1 vale per i `cost` nuovi: quelli già scritti (come i due della prova reale) non portano il task del revisore. L'ho scritto in `gestionale.md` e nel rapporto della prova.
- F3: nel caso L0 → L1 (causa `l0_grew`) non c'è una decisione di taglia (la fase cambia, ma l'operazione `level` non viene emessa), quindi la riga si aggiunge solo dove l'evento `size_decided` esiste davvero (livello che sale con l'operazione `level`, anche L0 → L2).
- Riga 22: il testo della tabella parla di una riga lunga nel «caso nuovo»; ho spezzato la riga di 134 caratteri di `test_missing_repeated_or_leading_text_are_problems`.
- Il RED di F2, F3, F1, riga 7 è stato osservato; per le righe 2, 20, 23, 24, 27 il test è scritto insieme al codice (RED non registrato per le righe 23 e 24, che cambiano la forma di un valore già coperto).

## Suite

`PYTHONWARNINGS=error::ResourceWarning tests/run` (log `suite-final-fix.log`): `exit 0`. Python 3.11: 4349 test OK (13 saltati); Python 3.13: 4349 test OK (11 saltati); nessun «unclosed». Commit: 48d5a72 (codice e test), 4cf5824 (documenti).
