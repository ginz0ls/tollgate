# Report Task 15: prove dei criteri, spec rev 24, piano principale

Commit: vedi `git log -1` («tollgate P3c: prove dei criteri, spec rev 24, piano principale»).

## Cosa ho fatto

- `tests/test_criteria_p3c.py` esteso (D18b). Le funzioni di `LaterSliceTest` sono passate in una base `L2Helpers(FinishCase)` (nessun `setUp`, nessun test) usata da `LaterSliceTest` (stesso comportamento, stesso test verde) e dalla classe nuova `L2FlowTest`. `round(kind, counts, *args)` ora riceve i conteggi e `--confirm`; nuovi helper `act`, `refused`, `deny`, `prepare_step`, `commit_reviews`, `run_tasks`, `start_l2`, `spec_to_plan`, `plan_to_execution`, `make_lab`, `enter_worktree`.
- Quattro test nuovi in `L2FlowTest` (più uno: il ramo `spec_audit = false` sta in un test a parte, perché ha un banco con un'altra configurazione):
  - `test_l2_spec_to_execution_end_to_end` (18, 24, 37, 41): `start --level L2`; Write di un piano in `spec_audit` negato; spec senza le due sezioni, avversario con zero rilievi, due `major` meccanici, `audit prepare` rifiuta («correggi la spec»); `approve spec 1` rifiutato; spec corretta, giro pulito, `approve spec 1` → `spec-approval.md` e fase `plan`; Edit sulla spec negato; piano, giro con `major`, piano corretto, giro pulito, `audit prepare` porta `approval`; `approve plan` → `plan_sha` = blob del piano corretto = `sha` e `spec_sha` di `plan-approval.md`, scope del piano corretto, ultime tre cause `approve_spec`, `audit_clean`, `approve_plan`.
  - `test_cap_and_suspension_in_pr_block` (24): quattro giri con `major` (spec corretta tra l'uno e l'altro), blocco `giri avversariali della spec esauriti (giro 4)`, fase `blocked`, `audit prepare` e `approve spec` rifiutano e indicano `/tollgate:resolve`; `resolve` → «avversariale sospeso», `audit_suspended == {spec-adversarial: 4}`, `approve spec 1` con `adversarial: suspended`; piano, `approve plan`, task, `finish check` (voce `approvals` vera), revisore, `open-pr`; blocco 18.1 con `spec_audit == {adversarial: suspended, lens: null}` e le due cartelle `reviews/7/`.
  - `test_three_slices_lens_audit_and_component_off` (24): `approve spec 1` su tre fette rifiutato; `audit prepare` esce con 3, `--confirm` apre il ciclo 1 (`executor`); `approve spec 3` rifiutato con l'audit aperto; 16 cicli vuoti in tutto, `approve spec 3` accettato con `adversarial: closed`, `lens: closed` e la proposta delle issue.
  - `test_three_slices_with_spec_audit_off` (35, parte locale): stessa spec, `[components] spec_audit = false`: nessun giro `spec-lens`, passo «approve spec», `approve spec 3` accettato con `lens: off`.
  - `test_reopen_spec_from_execution` (37): dall'esecuzione, motivo obbligatorio, `reopen spec` → `spec_audit`, `plan_sha` e scope tolti, task cancellati, evento `plan_reset`, spec di nuovo modificabile; spec corretta, nuovo giro, nuova approvazione con `sha` diverso, spec di nuovo bloccata; giro del piano sulla spec nuova, `approve plan` → `execution`, `spec_sha` del piano = nuovo `sha` della spec, task di nuovo `pending`.
- Spec rev 24 (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`): intestazione, 0 (giro superato), 3 (agenti e skill), 3.1 (`audit`, `start --spec`, comandi negati ai subagenti, nessun segnale), 5 (proposta delle issue in `approve spec`, `--spec` e `locate_spec_approval`), 6.1 (`--spec`), 6.2 riscritta (forma e pitch meccanico, giri e tetti, lenti e punti di vista meccanici, report e giro superato, ordine dei passi di `audit prepare` con D2, approvazione, blocco, sospensioni, piano, `approve plan`), 7.4 e 8.3 (esenzione di `reviews/<N>/`, `locked_docs` una volta), 8.4 (`approve spec|plan`, `reopen`, `resolve` e sospensioni, D5, D6), 8.7 (`check_l2`), 12.2 (colonne, migrazione 5), 12.3 (cause di L2, ritorni), 12.4 (`adopt` di L2), 15 (24 e 41), 16 (esiti di P3c), 18.1, 18.3 (riga JSON, `render_*`, D12), 18.4 (`plan_reset`, cause), 20 (riga 24).
- Piano principale: spec rev 24, stato (P3c chiuso sul ramo, merge in attesa dell'OK dell'utente, 1736 test), sezione 2, sezione 3 (moduli reali, contratti verso il gate, vincoli per P4 e rinviati dei task), tabella «Prove dei criteri di P3c».

## TDD

I quattro test (cinque con quello a componente spento) sono passati subito: il codice dei Task 2-14 esiste già e questi test lo attraversano da `hooks/run` e `bin/tollgate`. Non c'è stato un RED: lo dichiaro. Un solo errore mio nel primo giro, corretto nel test e non nel codice: dopo `reopen spec` la spec è invariata e l'ultimo giro avversariale (pulito, stesso blob) vale ancora, quindi `approve spec` è accettato subito (comportamento voluto, già provato da `test_reopen_without_changes_then_approve_again`); avevo asserito un rifiuto per errore. Gli atti passano per la CLI con l'ora reale: i test durano meno dei 10 minuti di scadenza, quindi non serve applicarli dalla libreria con `now=fl.now` (lo dice il docstring di `L2Helpers.act`).

## Matrice

Ogni `file::Classe.metodo` della tabella (44) è stato controllato con un parsing AST dei file di test: nessuno manca. Nessun buco da riempire: i criteri avevano già test nei moduli che possiedono il codice; il Task 15 ha aggiunto i test dal programma vero.

## Suite

- `tests/run`: Python 3.11.16, 1736 test, OK (445,8 s); Python 3.13.5, 1736 test, OK (451,1 s).
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 1736 test, OK (442,1 s), nessun «unclosed database» (grep: 0 occorrenze). Coda dell'output:

```
----------------------------------------------------------------------
Ran 1736 tests in 442.072s

OK
```

I tempi dei quattro test nuovi sono di 12-25 secondi ciascuno (sono flussi interi con processi veri).

## Scostamenti e dubbi

- Registro dell'esecuzione: nel piano principale ho scritto `.superpowers/sdd/2026-10-20-tollgate-p3c-percorso-l2/` «da portare in `docs/sdd/` a cura del controller» (come ha fatto P3b): non esiste ancora `docs/sdd/2026-10-20-…` e non ho inventato il percorso.
- «Rinviati della revisione finale»: la revisione finale del ramo non è ancora fatta, quindi nella sezione 3 ci sono i rinviati delle revisioni dei task (righe «deferred» di `progress.md`, selezione) e la nota che quelli della revisione finale si aggiungono dopo.
- La riga di Stato dice «riuscita ma composita» per la prova reale (passo 1 rifatto, spec scritta dal modello), come nel suo rapporto.
- La spec 6.2 è stata riscritta in modo ampio (era la sezione che le decisioni cambiavano di più): l'ho riletta contro il codice (`audit.py`, `l2acts.py`) ma una lettura critica del controller su 6.2 è consigliata.

## Fix round 1

- I-1: spec 16 corretta («dei due agenti lanciati, `spec-auditor` non provato»); in 16 e nello Stato del piano: passo 1 con la forma precedente dello script (D5) e l'esecuzione accidentale di `claude -p`, fermata per PID e non usata come evidenza.
- I-2: decisione 17 in 7.5 (recinto con al più 3 spazi, `check_plan` e `task_text`); decisione 25 in 6.3 (instradamento sulla gravità dichiarata blocker/major, riga 49, `HEAD` nullo senza profili); riga 24 di sezione 20 e intestazione aggiornate con 6.3 e 7.5; D15 spiegato con `git.blob_at` nel punto 4 della 6.2.
- I-3: le tre asserzioni diventano `assertIn("/tollgate:approve spec", self.prepare_step())`.
- Minori: 6.2 passo 4 con `spec_audit` spento; «decisione 15» al posto di «D15» nel piano; riga `reopen` di 8.4 con il task non `done` con commit; colonne «Resta a» di P3b annotate come chiuse in P3c; `test_check_writes.py::ExecutionL1Test.test_protected_files` in matrice; il test a componente spento è in `SpecAuditOffTest` con banco proprio (`rows` passa alla base).
- Matrice: 45 riferimenti, controllati con AST, nessuno manca.
- Suite: `tests/run` python3.11 1736 test OK (444,0 s) e python3 3.13.5 1736 test OK (440,9 s). Non ho rilanciato il comando con `-W error::ResourceWarning`: la modifica tocca solo la struttura delle classi di test, già verde con lo stesso comando prima del fix.
