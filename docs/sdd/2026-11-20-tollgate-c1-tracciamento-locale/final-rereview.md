# Ri-revisione del giro di correzione finale di C1 (d03fc33..4cf5824)

Letti: regole, brief, rilievi e triage, report, diff completo (codice, test, documenti). Eseguiti solo test mirati (`python3 -B`, `PYTHONWARNINGS=error::ResourceWarning`): test_ruling_cmd, test_subagents, test_check_task_verdict, test_check_post_edit, test_snapshot, test_events, test_adopt, test_check_session: 201 test, OK. Il diff non tocca `docs/verifiche/evidenze/`, profili, regole approvate, agenti, gate (verificato con `git diff --stat` sui percorsi). Working tree pulito.

## Verdetti sui rilievi

**F1 (task del revisore nel `cost`)**: INDIRIZZATO. `task_verdict.py:49-50, 66-72` passa `cost_task` nei tre rami (manomissione, verdetto valido, veti esauriti); `_common.py:86-90` (`tampered_records`); `apply.py:266` lo passa; `subagents.py:100-103` lo usa solo per `data.task` del `cost` (riga e `subagent_stop` invariati). Test: `test_check_task_verdict` (`test_cost_carries_the_reviewed_task`), `test_subagents` (`test_cost_task_overrides_only_the_cost_event`, `..._defaults_to_the_row_task`). Spec 18.4 e `gestionale.md:46` aggiornati, con il limite per i `cost` già scritti.

**F2 (`perchè:`)**: INDIRIZZATO. `ruling_cmd.py:22-26` (`perch[eèé]`, chiave `perchè`), `:41` NFC prima di `splitlines`. Test con `perchè`, `Perchè`, `PERCHÈ` e tre forme NFD (`test_ruling_cmd`).

**F3 (riga della taglia quando il livello sale)**: INDIRIZZATO. `_common.py:302-309` (`_size_line`, stessi segnali di `apply._level:36-44`, stessa `worksize.preview`), `:337-345` (caso L0 con L2 e ramo generico). Test `test_level_rise_says_the_new_size` e asserzione in `test_l0_with_sensitive_path_goes_l2_in_plan`: la riga iniettata coincide con l'evento. Spec 6.1 aggiornata. Il caso L0 -> L1 non emette `level`, quindi non c'è decisione: scelta coerente col codice.

**F4 (significato dello 0 in `[retention]`, portata del limite)**: INDIRIZZATO. Spec 11.4 (riga 1417) e `gestionale.md:70` dicono: 0 = «mai» solo per `events_days`, «subito» per le altre due; il limite del repo vale per tutto lo stato della macchina.

**F5 («non calcolata»)**: INDIRIZZATO. Spec 12.2 (riga 1532) e piano C1 decisione 1 (riga 79): «con `size` nullo».

**F6 (`repo_key` nella fotografia)**: INDIRIZZATO. `gestionale.md:48` rimanda al limite, `:65` lo scrive; sezione 8 del piano principale ha la voce per C4.

**Triage 2 (fsync prima del DELETE)**: INDIRIZZATO. `events.py:82-87, 107-111`; `fsutil.write_atomic` invariato. Test con spia su `os.fsync` (file e cartella, eventi ancora tutti nel DB) e controllo che `write_atomic` non faccia fsync.
**3 (import `fsutil`)**: INDIRIZZATO (`tests/test_events.py`, import tolto).
**7 (taglia «start» in `adopt` dopo il tetto)**: INDIRIZZATO. `adopt.py:376-386` (passo spostato dopo il tetto), `:425-436` (livello dal DB). Test `test_size_at_start_is_decided_after_the_level_cap`. Spec 6.1 allineata.
**8 (riga della taglia in `approve_plan`)**: INDIRIZZATO. `l2acts.py:265-272`; test sull'ordine.
**9 (test di `level` uguale/più basso)**: INDIRIZZATO (`test_check_post_edit`, `test_level_op_with_same_or_lower_level_does_not_decide_size`).
**12 (riga lunga in `test_check_acts`)**: INDIRIZZATO.
**13 (`approve size grande`: slices invariato, niente issue)**: INDIRIZZATO (`tests/test_l2acts.py`, `test_approve_size_large_leaves_slices_and_proposes_no_issues`).
**16 (`name != "-"`)**: INDIRIZZATO (`cli_calls.py:69`).
**17 (NFD)**: INDIRIZZATO con F2.
**19 (`Bash` con `tool_name` annidato)**: INDIRIZZATO (`tests/test_hook_engine.py`, due casi, uscita 2).
**20 (`source` di `session_start`)**: INDIRIZZATO (`session.py:12-19, 30`; test con stringa lunga, lista, intero).
**22 (riga lunga in `test_ruling_cmd`)**: INDIRIZZATO (righe spezzate; la riga di docstring di 102 caratteri alla riga 1 non era del caso nuovo).
**23 (formula duplicata)**: INDIRIZZATO. `report.new_tokens` (`report.py:116-118`) usata da `transcript_tokens` e `_common.transcript_cost`; nessuna terza copia.
**24 (`None` e non 0)**: INDIRIZZATO nei due rami nominati (`subagent_stop.py:28-31, 91-93`), ramo del tetto invariato; test `test_no_transcript_means_unknown_tokens_not_zero`.
**25 (regex di `SET user_decision`)**: INDIRIZZATO (`tests/test_reviews.py`, regex `SET\s+(...)*user_decision\s*=` con tre testi di controllo).
**27 (`_questions` una scansione)**: INDIRIZZATO (`snapshot.py:27-33, 53-59, 101`); test con traccia SQL: una sola scansione con due lavori.
**28 (limiti noti con `events_days > 0`)**: INDIRIZZATO (`gestionale.md:66`).
**29 (misura ripetibile)**: INDIRIZZATO (`gestionale.md:76`: percorso, 88 `tollgate.db`, schema 6, procedura).
**31 (intestazione di `run-b1-flow.sh`)**: INDIRIZZATO (`spikes/run-b1-flow.sh:41-42, 275`).
**33 (due `veto` voluti)**: INDIRIZZATO; ho confrontato con `evidenze/c1/flusso/registro-1/events.jsonl`: seq 4 `coordinator` (`pre_bash`), seq 5 `plan_check` (`post_edit`, nessun task).
**34 (frase su `eventi-c1.jsonl`/`events.jsonl`)**: INDIRIZZATO (rapporto riga 45).
**35 (8 file)**: INDIRIZZATO (rapporto riga 68).
**36 (esito di `plugin validate`)**: INDIRIZZATO (rapporto riga 70); `validate-1.txt` ha «Validation passed» e un avviso («1 plugin directory warning»), come scritto.
**37 (D19 nell'intestazione rev 36)**: INDIRIZZATO (spec riga 4).
**38 (7.2: `stop_asked` senza domande leggibili)**: INDIRIZZATO (spec riga 741); coerente con `stops.py:55-57`.
**39 (6.1: tre cause di `adopt`)**: INDIRIZZATO (spec 6.1); coerente con `adopt.py:427, 434, 460` (`start`, `approve_spec`, `plan`).

**Sezione 8 del piano principale**: INDIRIZZATO. Righe 6 (per C5) e 18 (per C6) con il motivo e la voce F6 per C4; la riga C1 della sezione 2 non è stata toccata e non contiene «unita» (dice «in attesa del merge»).

## Danni nuovi nel diff della correzione

Nessuno Critical o Important. Minor:
- Minor: righe sopra i 100 caratteri introdotte da questo giro, proprio il tipo di difetto delle righe 12 e 22: `bin/tollgate_core/events.py:93` (docstring di `archive_and_prune`, 134 caratteri) e `bin/tollgate_flow/ruling_cmd.py:4` (109 caratteri).
- Minor: la riga 24 lascia `tokens = 0` nel ramo di manomissione di `_readonly` (`subagent_stop.py:25-27`) e in `task_verdict` (`task_verdict.py:47-49, 66-72`) quando l'uso è `None`: «non so» e «zero» restano confusi lì. Coerente con la lettera della riga 24 (due rami), quindi non è un rilievo aperto.

## Osservazioni fuori ambito

- La riga C1 della sezione 2 del piano principale dice ancora «revisione finale ancora da fare» (riga 27), non toccata da questo giro; da aggiornare con il merge.
- La frase del rapporto della prova sul revisore (`:53`) e la pagina d'uso descrivono correttamente che i `cost` già scritti non portano il task: nessuna azione.

## Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
