## Rilievi ripresi qui

| Rilievo | Dove |
|---|---|
| Vincoli P3b→P3c (1) seconda frase del criterio 41, (2) `approve spec`/`plan` in `APPLIERS` con i campi letti da P3b, (3) `plan_sha` di `approve plan`, (4) `spec_reviews_dir`, `plan_reviews_dir`, `spec_audit` e fette successive, (5) sottocomandi nuovi in `cli_calls`, (6) `create_work` con `phase` e `from_approved_spec` | (1) Task 6 (decisione 8); (2) Task 7; (3) Task 7 e 15; (4) Task 9; (5) Task 5 (Global Constraints); (6) già in `phases.create_work:91`, test ripreso nel Task 4 |
| Vincoli P3a→P3b e P3c (1) segnale, (2) programma | (1) Global Constraints e Task 5; (2) Global Constraints, Task 13 |
| Riga 83 del piano principale (P3a riga 82): recinto con rientro qualsiasi | Task 2 (decisione 17) |
| P1: `from_approved_spec` senza `spec_path` | Task 4 |
| P3b righe 5, 21, 22, 23, 24, 25, 30, 31, 32, 38, 39, 40 (core, analisi, hook) | Task 11 (30 nel Task 2, 31 nel Task 9) |
| P3b righe 34, 36, 49, 50, 51, 55, 60, 62, 67, 71, 72, 73, 82 (flusso e test) | Task 12 |
| P3b righe 77, 78, 79 (skill e agenti) | Task 13 |
| Lezioni di P3b: stati toccati da più comandi; skill contro codice; prova reale in sessione legata; campi di `gh`; carry per task | Review Focus e test che attraversano i comandi (Task 7, 8, 9, 15); Task 13 (skill dopo i sottocomandi, test del contratto); Task 14; decisione 22; istruzioni di esecuzione |

Restano ad altri piani, non toccati qui: le voci di P3b destinate a P4 (righe 4, 47, 68, 69; `prs_for_branch_prefix` e le PR da fork) e a P5; il gate (`attenzione` per componenti spenti e audit sospesi, criterio 35 nel gate).

## Review Focus

Ogni voce è uno stato che due o più comandi toccano (lezione della revisione finale di P3b). Sono sei: la sesta copre fasi e blocchi, toccati da quasi ogni comando di P3c.

1. **Spec, blob e approvazione** (toccati da `approve spec`, `reopen spec`, `locked_docs`, `finish check`, `open-pr`, `start --spec`, `adopt`): dopo `approve spec`, commit, `reopen spec`, spec corretta, nuovo giro e nuova `approve spec`, il file di approvazione ha il nuovo `sha`, la spec è di nuovo bloccata, `finish check` dà `approvals` vera e la spec non è fuori scope. Test: Task 8 `test_reopen_spec_then_new_approval_end_to_end`.
2. **Registrazione del piano** (toccata da `post_edit` in L2, `approve plan`, `reopen plan`, `task start`, `adopt`): in L2 `post_edit` non registra mai lo scope; `approve plan` registra il blob approvato; `reopen plan` lo toglie e la nuova `approve plan` registra il piano corretto, con i task di nuovo `pending` e `task start` che legge il nuovo `plan_sha`. Test: Task 8 `test_reopen_plan_then_reapprove_registers_new_scope`.
3. **Righe dei giri** (scritte da `audit prepare`, chiuse da `SubagentStop`, lette da `resolve` e `approve spec`): un giro aperto quando la spec cambia diventa `superseded` e il report tardivo del suo agente è ignorato senza eccezioni; un giro sospeso seguito da un giro non pulito riapre il blocco; `approve spec` legge sempre l'ultimo giro chiuso. Test: Task 6 `test_late_report_of_superseded_round_ignored`, Task 7 `test_suspended_round_then_dirty_round_reblocks`.
4. **File sotto `docs/superpowers/reviews/<N>/`** (scritti dall'hook e da `act apply`, committati dal coordinatore, esenti dallo scope, protetti da Edit e Write): il coordinatore li committa con `git add`/`git commit` attraverso `PreToolUse Bash` in `spec_audit`, `plan`, `approval` **ed `execution`** (dopo `approve plan`, con lo scope registrato) senza veti; un Edit su un report è negato; `finish check` non li conta fuori scope. Test: Task 6 `test_report_file_committable_and_protected`, Task 7 `test_plan_approval_committable_in_execution`.
5. **Fetta successiva** (toccata da `start --spec`, `locked_docs`, `approve plan`, `finish check`, `open-pr`, `adopt`): un lavoro avviato con `--spec` su una spec approvata da un'altra issue arriva a `finish check` con `approvals` vera, la spec bloccata, `spec_reviews_dir` nella cartella dell'altra issue, e `adopt` dopo un DB perso ritrova la fase. Test: Task 9 `test_later_slice_end_to_end`.
6. **Fasi, blocchi e sospensioni** (decisione 27): un tetto dell'audit porta a `blocked`; `audit prepare`, `approve spec` e `reopen` rifiutano lì; `resolve` riporta la fase e scrive la sospensione; dopo, `audit prepare` arriva a «approve spec» senza chiedere correzioni. Test: Task 7 `test_cap_resolve_suspended_then_approve` (con il passaggio da `audit prepare` prima e dopo il `resolve`).

