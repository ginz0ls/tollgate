# Decisioni del controller da portare nei task (prevalgono sul testo del piano)

## Task 1
- D2: in `tests/test_db.py:333` (`MigrationV6Test.test_migration_keeps_existing_works_outside`) `"6"` diventa `str(db.latest_version())`; le asserzioni sulle copie `migrazione-6` (`:341`, `:345`) restano. Il test che il piano chiama `test_latest_version_is_6` è a `tests/test_db.py:198` (classe `MigrationV4Test`).
- D17: la riga `**Tipi:**` di 18.4 (spec del nucleo, circa riga 2140) ha tra backtick **solo** i nomi dei tipi: `test_spec_event_types_match_registry` (`tests/test_docs.py:138-142`) prende ogni parola minuscola con underscore tra backtick della riga.

## Task 2
- D1: anche `HousekeepingTest.test_housekeeping` (`tests/test_start.py:1127-1163`, asserzione a `:1162`) diventa rosso con «0 = mai»: si tratta come `test_malformed_sessions_do_not_skip_other_cleanups` (`:1190-1207`): `tollgate.toml` del repo di prova con `[retention] events_days = 180` (`StartCase.make(toml=…)`, `:350`) e l'evento di 200 giorni nell'archivio invece che sparito. `test_prune_events_error_does_not_skip_prune_bound` è a `:1209-1219`.
- D5: la validazione di `config` rifiuta `retention.events_days`, `retention.lookups_days` e `retention.retention_days` negativi **e** sopra 36500 giorni (`ConfigError` con la chiave nel messaggio); test per il negativo e per 36501.
- D8: `archive/` si crea con `mkdir(mode=0o700, exist_ok=True)` sotto `state.root`; `events.py` chiama `fsutil.write_atomic(...)` attraverso il modulo (`from . import fsutil` o equivalente), così i test che lo sostituiscono lo intercettano.
- D21: `events.prune_events` si toglie (dopo il Task 2 non ha chiamanti in `bin/`); il suo test `tests/test_events.py:73` passa su `archive_and_prune`. Una primitiva che cancella senza archiviare non resta.

## Task 3
- D9: in `adopt._register_plan` il testo del piano L1 per `specdoc.slices` si legge dal commit con `git.text_at(...)` (`_Evidence.plan` ha solo `(percorso, check)`).
- D10: in `approve_plan` `sizes.decide` subito dopo `register_plan` e prima di `phases.set_phase`.
- D19: in `approve_plan` `decide` sta dentro l'`if work["plan_sha"] != plan_blob` (`l2acts.py:230-239`) con `register_plan`; `test_approve_plan_decides_size` fissa anche che una ripetizione dopo un'interruzione (come `test_repeat_after_interruption_does_not_register_twice`, `tests/test_l2acts.py:476`) dà un solo `size_decided` con causa `plan`.
- D12: `sizes.decide` (e `set_by_user`) scrive `size` e `size_by` se cambia la taglia applicata **o** chi decide (`by`): dopo `approve spec <n>` con `n > 1` su una taglia dell'utente già `large`, `size_by` torna `rules`. Un test lo fissa in `tests/test_sizes.py`.
- D17: i messaggi di `sizes` e `worksize` non scrivono mai `tollgate <sottocomando>` nudo (`BareProgramInMessagesTest`, `tests/test_manifest.py:655-690`): usano `/tollgate:approve spec <n>`, `/tollgate:start …` (con i due punti passa).
- Fatti dello scan: `ctx.config.profiles` è `dict[str, dict]` senza la chiave `active` (`config.py:139-141`); `profiles.vertical_for` dà `None` per i file del generico e dei profili `cross`. I test di `start`/`adopt` guardano solo `splitlines()[-1]` o la riga dopo `avviso: modelli`: la riga della taglia va prima di `prossimo passo:`. `apply._OPS` resta a 29 (`tests/test_check_audit_round.py:576`).

## Task 4
- D10: in `approve_spec` la `UPDATE work_items SET slices` e `sizes.decide` stanno in un solo `db.tx` **prima** di `phases.set_phase` (`set_phase` vuole stare fuori da una transazione e fa la copia del DB dopo il commit, `phases.py:203-211`). La riga della taglia va nell'uscita prima di «Committa …» e fuori dal recinto dei titoli delle fette (`tests/test_l2acts.py:297-309`).
- `APPLIERS` è a `actapply.py:238-249`, il messaggio di `_pick` a `:267` (il piano dice `:240-251` e `:268-269`).
- D17: la skill `approve` e la pagina `docs/uso/comandi.md` cambiano insieme (`argument-hint`, `tests/test_docs.py:79-98`, `tests/test_skill_contract.py`); nelle skill niente nome nudo del programma (`tests/test_manifest.py:440-447`).

## Task 5
- Lezione del Task 3: `tests/test_b1_scripts.py` copia il plugin dai soli file tracciati da git; un file nuovo di `bin/` non ancora aggiunto con `git add` fa fallire una ventina di quei test. Prima di lanciare la suite completa, `git add` dei file nuovi del task (senza `__pycache__`).
- D4: `cli_calls` nega a un input con `agent_id` (subagente) un `ruling add` con `--by user` (anche `--by=user`), con un motivo in italiano che dice che solo il coordinatore registra una scelta dell'utente; `--by agent` o senza `--by` restano permessi al subagente e tutto resta permesso alla sessione principale. Test in `tests/test_check_cli_calls.py`.
- D11: `test_subagent_may_add_ruling` usa il programma di `paths.program_command(<plugin_bin del contesto di prova>)`, il corpo con apostrofi, `$`, un backtick e le parole `task`, `review`, `start`, e ha anche il controllo negativo: lo stesso corpo con `task start 1` → `deny` `coordinator_only` per il subagente.
- D20: le etichette `cosa:`, `perché:`/`perche:`, `costo:` si riconoscono senza distinguere le maiuscole (test con «Cosa:»); la riga del brief dell'implementatore e quella della skill `execute` avvisano che nel testo non si scrive un'assegnazione `TOLLGATE_…=` (la nega `bash_rules`).
- D17: i messaggi di `ruling_cmd` non scrivono `tollgate ruling` nudo (`BareProgramInMessagesTest`): il heredoc si compone con il programma dato.
- Sonda dello scan (§4.1): oggi `cli_calls.decide` non nega `ruling add` a nessuno (sottocomando sconosciuto); il heredoc con apostrofo, `$` e backtick si analizza con `bash.parse`.

## Task 6
- Lezione del Task 3: `tests/test_b1_scripts.py` copia il plugin dai soli file tracciati da git; un file nuovo di `bin/` non ancora aggiunto con `git add` fa fallire una ventina di quei test. Prima di lanciare la suite completa, `git add` dei file nuovi del task (senza `__pycache__`).
- D16: `stops` legge `tool_input`, `tool_response` e `tool_use_id` da `event.raw` (l'adattatore mette `tool_response = None` se non è un dizionario, `adapter.py:66`), tollerante a ogni forma (stringa, lista, assente). Nessun campione di `AskUserQuestion` né di `PostToolUseFailure` in `spikes/fixtures/hook-inputs/`.
- Fatti dello scan: nessun test del registro va cambiato; si cambiano insieme `model.INPUT_EVENTS` (non `CONTROL_EVENTS`), `adapter._PRE`/`_POST` e il ramo `PostToolUseFailure` di `adapter._kind` (`adapter.py:44-49`). `tests/test_modelsfetch.py:775-815` vieta «modelsfetch»/«models_check» nei testi dei moduli di `tollgate_checks`. Nel wrapper `CONTROL` è a `hooks/run:15` (prima della lettura dell'input a `:16`): il `CONTROL=no` va dopo `INPUT="$(cat)"`. Nel runner la riga è `runner.py:203`.

## Task 7
- D3: `_common.transcript_cost(event) -> tuple[int, dict | None]`: `usage` è `None` per file mancante, illeggibile o senza nessuna riga `usage`; altrimenti un dizionario non vuoto. `subagents.finish` registra `cost` solo con un dizionario non vuoto. Un test per ciascuno dei tre casi.
- D21: `transcript_cost` legge la trascrizione una volta con `report.transcript_usage`; `tokens` = somma di `input + cache_creation + output` di tutti i modelli (0 senza uso), uguale a `transcript_tokens` sullo stesso file (`test_transcript_usage_by_model` lo fissa). `final_review._invalid(row, work, tokens, what, problems)` (`final_review.py:23`, chiamata a `:47` e `:55`) riceve anche `usage`. `_readonly(ctx, row, work)` (`subagent_stop.py:27`) riceve l'evento.
- Elenco dei 15 `record("subagent_finish")` in `preflight-scan.md` §5.2 (14 con trascrizione; `budget_cut_records`, `_common.py:343`, resta senza). Righe esatte: `subagent_stop.py:27`, `:88`, `:98`, `:107`, `:153`; `_common.py:78`; `task_verdict.py:65`, `:69`; `final_review.py:23`, `:50`, `:57`; `audit_round.py:48`, `:61`, `:71`.
- I test dei revisori di oggi usano `agent_transcript_path="/non/esiste.jsonl"`: per `test_reviewers_pass_usage` serve una trascrizione finta in una cartella temporanea.

## Task 8
- Lezione del Task 3: `tests/test_b1_scripts.py` copia il plugin dai soli file tracciati da git; un file nuovo di `bin/` non ancora aggiunto con `git add` fa fallire una ventina di quei test. Prima di lanciare la suite completa, `git add` dei file nuovi del task (senza `__pycache__`).
- D15: il ramo di `snapshot` in `cli.py` sta prima di `db.open_db` (`cli.py:515`), accanto a quello di `status` che controlla `state.db_path.exists()` (`:495`): senza DB stampa `{"v": 1, "at", "host", "works": []}` e non crea niente.
- D7: `gestionale.md` dice «sola lettura dei dati; il primo avvio dopo un aggiornamento può migrare lo schema, con una copia in `backup/`».
- D13 e D14: `gestionale.md` scrive come limiti: `reopen plan` rinumera i task (`cost.by_task` può unire i due piani); `slices` nullo per L1, per le fette dalla 2 in poi e per i lavori nati prima di C1; chiavi di `cost.by_task` stringhe nel JSON; avanzamento, dipendenze e coda arrivano con C4 e C5; un profilo `vertical` senza `paths` conta come area per ogni file.
- Misura (sonda dello scan, §4.4): le 88 copie di `eval-b8` sono allo schema 6 (quelle di `eval-p5` allo schema 5, senza `lookups`): la misura si fa sulle copie di `eval-b8`, sempre da una copia in `mkdtemp(prefix="tollgate-")`. Lo scan ha contato su tutte e 88: 1002 eventi, 334672 byte di JSONL, 334 byte per evento; la pagina può usare la misura su tre copie che chiede il piano e citare anche quella su tutte e 88, dicendo da dove viene.
- D17: `test_docs_exist` (`tests/test_docs.py:74-76`) riceve `gestionale.md`; `test_no_local_paths` (`:108`) vieta `/home/` e `MEGA` nella pagina; i messaggi di `snapshot` non scrivono `tollgate snapshot` nudo.

## Task 9
- Lezione del Task 3: `tests/test_b1_scripts.py` copia il plugin dai soli file tracciati da git; un file nuovo di `bin/` non ancora aggiunto con `git add` fa fallire una ventina di quei test. Prima di lanciare la suite completa, `git add` dei file nuovi del task (senza `__pycache__`).
- D6: `B1_FLOW_EVIDENCE` si applica dopo le righe `OUT=` (`run-b1-flow.sh:60-66`) e **prima** della riga del banco di prova (`:68`, così `B1_FLOW_OUT` dei test vince ancora e i test non scrivono nelle evidenze vere), validata con `^[a-z0-9-]+$` come `B1_FLOW_RULES`/`B1_FLOW_CASE` (`:162-163`); test sul modo `controlla` con `c1` (`cartella delle uscite: …/evidenze/c1/flusso`, riga stampata a `:247`) e con `../x` (rifiuto). `test_flow_registra_collects_the_evidence` (`tests/test_b1_scripts.py:854`) pretende `fallimenti.txt` vuoto: `snapshot` nel banco deve uscire con 0.

## Revisioni in parallelo (tutti i revisori che girano mentre lavora l'implementatore del task dopo)
- D18: leggi il codice del task dal pacchetto di revisione o con `git show <commit>`; se devi lanciare un test, fallo su una copia esportata con `git archive <commit>` in una cartella `mkdtemp(prefix="tollgate-")` che cancelli alla fine, mai nel worktree vivo.

## Task 10
- Le ruling del ledger che cambiano la spec o il piano principale (vanno nella rev 36 e nella sezione 20 con le dodici decisioni): D4 (`cli_calls` nega a un subagente `ruling add --by user`, anche `--by=user` e il prefisso `--b`: la decisione 5 diceva «`cli_calls` non cambia»); D5 (`retention_days`, `events_days`, `lookups_days` tra 0 e 36500, `ConfigError` fuori); D7 (`snapshot` «sola lettura dei dati»: il primo avvio dopo un aggiornamento può migrare lo schema con una copia in `backup/`, in 3.1); D21 (`events.prune_events` tolta: la sola potatura è `archive_and_prune`); D3 (`cost` solo con un uso non vuoto: una trascrizione senza righe `usage` resta senza `cost`); D10 (in `approve spec` slices e taglia prima del cambio di fase; in `approve plan` taglia subito dopo `register_plan`); D12 (`size_by` si riscrive anche quando cambia solo chi decide); D20 (etichette delle ruling senza distinzione di maiuscole); D16 (`stops` legge da `event.raw`). Il ledger completo è in `W/progress.md` (righe `Ruling:`): leggile tutte e riporta in 20 quelle che toccano la spec.
- Il Task 7 ha messo `test_approve_finding_emits_finding_event` in `tests/test_actapply.py` (non `tests/test_reviews.py`): nella tabella «Copertura» del piano C1 si corregge il file con una nota.
- La prova reale è riuscita (`docs/verifiche/2026-11-20-c1-prova-flusso.md`, `Esito: riuscita`): la riga «Avanzamento» del progetto di C la cita.
- La sezione 8 del piano principale di C («Rinvii dalle fette chiuse») riceve i minori rinviati **solo dopo** il triage della revisione finale: nel Task 10 la sezione 8 riceve una riga che dice che il triage dei minori di C1 arriva con la revisione finale, senza elencarli ora.
- La riga C1 della sezione 2 del piano principale: «**Stato:** eseguita sul ramo `c1-tracciamento-locale`, in attesa del merge» (mai «unita»).
- Lezione del Task 3: `git add` dei file nuovi prima della suite.
