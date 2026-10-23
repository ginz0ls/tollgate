# Task 5 — revisione (commit b02b53b, base fcd85e1)

Letti: regole, brief, report, diff, vincoli globali, cautele, decisioni 3, 6, 7, 8, 10, 11, 15, 21, 23. Sola lettura; nessun test rilanciato (le evidenze del report, 111 test e `tests/run` su due interpreti, sono coerenti con il diff). Controlli mirati fuori dal diff: `prref`, `model.PrFacts`, `l2tree`, `openpr.facts`/`_l2_dirs`, `git.blob_at`/`changes`, `protected`, `waivers.covers`, `attention.GROUPS`.

## Aderenza

- ✅ Famiglie `level`, `l2`, `issue`, `declared`, `notes`, `lockfiles`, `workflow_rules`, `guard_local` in `FAMILIES` (`evaluate.py:852`); `evaluate` resta l'unico punto di decisione.
- ✅ D13: `CoverageTest.test_every_group_key_is_produced` (`tests/test_gate_evaluate.py:1037`); nessun insieme di eccezioni, con motivo nel docstring.
- ✅ D17b (h): `tollgate_files_in_work` (`evaluate.py:822`) e `tollgate_files_changed` (`:828`) distinte, entrambe su `protected.is_tollgate_file`; nessun `TOLLGATE_FILE_GLOBS`; un test ciascuna (`TollgateFilesTest`). `git.changes` per il gate non applica `exclude` e usa `old_path`: i file spostati contano.
- ✅ `spec_reviews_dir` diverso dalla cartella trovata → `approval_stale` (`evaluate.py:560-565`, test `test_reviews_dir_other_than_the_found_one_is_stale`). Il confronto con `rstrip("/")` è giusto: `openpr._l2_dirs` scrive la cartella con la barra finale (`openpr.py:394`).
- ✅ Giudizio sulla spec da `approvals.judge_spec` (via `check_l2_detail` e `_stale_diffs`), componenti del predefinito passati (I-9, test dedicato).
- ✅ `ci_waived_workflow` e `review_unverified` prodotte, con test; il `Violation("ci_changed", ..., "ci")` coincide con quello di `testguard.py:224`.
- ✅ Blocco assente/non valido su `tg/*` → rosso `block_missing` con test; nomi dei must-have in `data`, `text` fisso.
- ✅ Decisione 8: ramo `tg/N-*` con `Closes` diverso o issue non aperta → rosso e nessuna deroga (la restrizione sulle deroghe sta in `Context.waiver_issue`, già esistente; il test copre il caso); altri rami senza `Closes` → `no_issue` + `not_tg_branch`, con `Closes #M` l'issue M deve essere aperta.
- ✅ Testo non fidato: ho letto ogni f-string dei nuovi `text`. Contengono solo conteggi, numeri di issue da regex `\d+`, livelli validati (`declared in LEVELS`, `minimum` calcolato), `warn`/`high` dalla configurazione. Blocco, corpo, rilievi, motivi, percorsi stanno in `data`. Nessun testo non fidato in un argomento di git: `_old_blob_text` valida lo sha con `_BLOB` prima di `cat-file`/`--find-object`; gli unici percorsi che vengono dal blocco (`spec`, `plan`) vanno in `git.blob_at` dopo `--` e con confronto esatto del nome (⚠️ già così dal Task 4 per `plan`; innocuo ma letteralmente «testo non fidato in un argomento di git»).
- ✅ Strati: nuovi import `tomllib`, `re`, `posixpath` e moduli di `tollgate_analysis`; nessun `db`/`sqlite3`.
- ✅ Le voci ricalcolate prevalgono: `RECOMPUTED_DOD` coincide con la decisione 11 (`receipt, guard_scope, must_have, approvals`).

### Le tre scelte dichiarate

1. `block_missing` nella famiglia `issue`: coerente con la decisione 23. Quella decisione dice che `definition_of_done = false` salta la famiglia `declared` (DoD dichiarata e rilievi); la decisione 6 elenca «blocco assente o non valido» come rosso autonomo della PR `tg/*`, indipendente dal componente. Spostarlo in `declared` lo farebbe sparire con la DoD spenta, e senza blocco `level`, `l2` e `must_have` non girano affatto: sarebbe un buco. ✅ Manca però un test che lo fissi con `definition_of_done = false` (Minor).
2. `level_cap` solo sotto il minimo: lettura difendibile di 9.2 (riga 302). ⚠️ La riga 868 e il criterio 1356 parlano di «tetto di livello dichiarato» tra le voci di `attenzione` senza condizione; se il tetto è presente ma il livello dichiarato è già ≥ minimo (diff rimpicciolito dopo `approve level`) il gate tace. Vedi Minor M-2.
3. `l2` sul livello dichiarato: voluto. `approve level` abbassa davvero `level` (6.x/spec 292-295, evento `level_change` con causa `cap`) e quel lavoro non ha mai percorso `spec_audit`/`plan`; pretendere i file L2 contraddirebbe lo scopo del tetto, che il gate riporta già come `level_cap` («da leggere»). Senza tetto il rosso `level_below_minimum` copre il caso. ✅

## Punti di forza

- Famiglie piccole e leggibili, `Context` esteso con proprietà cached (`diff_level`, `min_level`, `is_config_branch`) e `_over_l0` ridotto a una riga: nessun calcolo duplicato del livello.
- `min_level` ricalcolato come `openpr.facts` (stessi tre ingredienti, anche sui file cancellati e sui vecchi nomi).
- Gestione difensiva del blocco malformato (`_entries`, controlli `isinstance`) con test `test_malformed_block_fields_do_not_crash`.
- `approval_stale` con diff dal blob approvato solo se è nella storia della testa (`object_in_history`), altrimenti «diff non disponibile».
- Test di buona qualità: asseriscono anche che il testo non fidato non finisce in `text` (`assertNotIn(..., item.text)`).

## Rilievi

### Critical
Nessuno.

### Important

**I-1. `is_config_branch` ignora `PrFacts.cross_repo`: una PR da fork su un ramo chiamato `tollgate-config/*` salta test-guard e scope e non ha nessun rosso.**
`evaluate.py:117-121` (`Context.is_config_branch`), usata in `diff` (`:422`) e in `issue` (`:630`). `cross_repo` esiste in `model.PrFacts` (`model.py:40`) ma non è letto da nessuna parte in `bin/`. Il nome del ramo lo sceglie chi apre la PR: da un fork `tollgate-config/x` che cancella test o tocca `src/` ottiene solo `tollgate_config` («da leggere», non rosso) e `verdict` verde. `gate guard` (Task 8) non lo ferma: guarda i file di tollgate, e l'eccezione della decisione 15 vale solo per lo stesso repo (rilievo M-7), mentre qui non c'è nessun file di tollgate cambiato. Anche per un ramo dello stesso repo con file fuori dal perimetro di 9.4, la sola difesa è `guard`; ma per il fork il buco è completo. Correzione: `pr is not None and not pr.cross_repo and prref.is_config_branch(pr.head_ref)`; un ramo di fork così chiamato è trattato come ramo non `tg/*` (`not_tg_branch`, `no_issue`) e il test-guard gira. Aggiungere un test con `cross_repo=True` (rosso `diff` per un test cancellato, nessuna voce `tollgate_config`).

**I-2. `_findings` è fail-open quando `verdict` manca o `verdict.cycles` non è un intero: i rilievi bloccanti vengono ignorati.**
`evaluate.py:672-685`: `last` vale `None` se `verdict` non è un dizionario o `cycles` non è `int`, e la condizione `isinstance(last, int) and _finding_cycle(f) in (None, last)` scarta ogni rilievo confermato `blocker/major`, mentre un id non nel formato `f-<c>-<n>` conta come ultimo ciclo (fail-closed, report punto 5). Le due scelte sono incoerenti, e la decisione 11 dichiara fail-closed (`blocking` assente = bloccante). Il blocco è scritto dall'agente nel corpo della PR: togliere o rovinare `verdict` basta a far sparire `finding_blocking` (con `openpr.facts` il `verdict` può anche essere `None` legittimamente se il ciclo non sta su HEAD, caso in cui i rilievi di un ciclo precedente restano elencati). Correzione: se `last` non è un intero, contare tutti i bloccanti (o ricavare l'ultimo ciclo dal massimo `c` degli id); un test `test_blocking_finding_without_verdict_is_red` (e con `cycles` non intero) accanto a `test_old_cycle_finding_ignored`.

### Minor

- **M-1.** `tests/test_gate_evaluate.py:963` `test_deleted_and_moved_tollgate_files_count` prova solo la cancellazione; lo spostamento (rename `-M`, `old_path`) non è esercitato, anche se `tollgate_files_in_work` lo gestisce (`evaluate.py:822-825`). Aggiungere il caso di un file di tollgate rinominato fuori dal perimetro.
- **M-2.** `level` (`evaluate.py:468-485`): un tetto valido con livello ≥ minimo non produce `level_cap` (⚠️ vedi sopra); inoltre non si controlla che il tetto sia coerente con il dichiarato (`level_cap = L2` con `level = L0` e minimo L2 passa come semplice `attenzione`). Chiarire con la spec se il tetto va riportato sempre; costo di un'ulteriore riga.
- **M-3.** `CoverageTest` (`tests/test_gate_evaluate.py:1037`): in una corsa completa `unittest` esegue `CoverageTest` per prima (ordine alfabetico), `SEEN` è vuoto e il test rilancia tutte le altre classi del modulo (~14 s in più, risultati scartati). Accettabile, ma raddoppia il tempo del modulo e un errore nelle altre classi viene riportato due volte solo nei test normali. Alternativa: un `setUpModule`/`tearDownClass` che fissa l'ordine, oppure un `load_tests`.
- **M-4.** `_stale_diffs` (`evaluate.py:503-523`) rideriva a mano lo stato `stale` del piano (`parse_approval`, `is_current`) dopo che `check_l2_detail` lo ha già giudicato: due punti che potrebbero divergere (per esempio il piano con `spec_sha` non corrente). La spec è già giudicata da `judge_spec` in un punto solo, il piano no.
- **M-5.** `notes` non gira in locale (`evaluate.py:723-728`, scelta 4 del report). La decisione 3 esclude in locale solo `issue`, `declared` e `base_ids`; `off_periods`, `task_over_*` e `skills_absent` verrebbero dal blocco locale. È un'omissione prudente e dichiarata, ma non richiesta: confermare con il controller.
- **M-6.** `tests/test_gate_evaluate.py` è a 1080 righe e `evaluate.py` a 866: il report lo segnala (punto 7); da spacchettare nel task che segue (per esempio per famiglia).
- **M-7.** Manca un test che pinni `block_missing` con `definition_of_done = false` (la ragione per cui sta in `issue`).

## Valutazione

**Qualità del task: Da correggere.**
**Motivo:** requisiti e decisioni del controller sono coperti e il codice è pulito, ma due difetti di sicurezza vanno chiusi: la PR di fork su un ramo `tollgate-config/*` evita test-guard e scope (I-1) e i rilievi bloccanti spariscono se `verdict` manca o è malformato (I-2). Entrambe le correzioni sono di una o due righe più un test.
