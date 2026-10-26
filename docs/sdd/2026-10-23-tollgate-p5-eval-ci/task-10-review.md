# Revisione Task 10 - casi extra e1-e5 (a63b6db..f3bd638)

## Aderenza

- ✅ e1: `test_e1_dry_run` copre uscita 3 con il testo di conferma, `--confirm` con il ciclo aperto e il lancio di `tollgate:spec-auditor`, report scritto dal hook (`tests/test_eval_cases.py`, classe `E1DryRun`). Il `cd` nel prompt c'è (D2). Il testo di conferma e il ciclo escono da `print` su stdout (`bin/tollgate_core/cli.py:388-390`, `bin/tollgate_flow/audit.py:522,479-486`), quindi nessun grader dipende dallo stderr (I1).
- ✅ e2: solo prova a secco (`E2DryRun`), nessun `evals/e2-*` e nessuna voce in `CORRECT_PATHS` (D1), con test che lo asseriscono. Il testo cercato è quello vero di `reopen` (D19). Il test `test_e2_the_run_session_is_not_bound_so_the_act_does_not_apply` documenta il motivo.
- ✅ e3: `start 2 --spec` produce la fase `plan` sia dal checkout principale sia dal worktree. I tre grader leggono testi stampati da `start` solo a lavoro creato (`bin/tollgate_flow/start.py:513-516`) e il worktree creato nella corsa (`file_exists` conta i file creati nella corsa, `plugin-evals-doc.md:580`).
- ✅ e4 nella forma decisa (L2, `/tollgate:execute` fino a `task done 2` e `finish check`, senza PR né atto `finish`). La riga `prossimo passo: ... review prepare` esce solo dal `finish check` verde in L2 (`bin/tollgate_flow/finishcheck.py:56-57`) e `Spec e piano approvati...` solo dalla DoD (`bin/tollgate_core/dod.py:27`). I grader guardano quindi l'esito del programma, non il solo comando lanciato. `test_e4_the_check_before_the_task_is_closed_is_refused` mostra che il comando lanciato presto non dà verde.
- ✅ e5 è eval, con la ricetta costruita dal programma vero (9 s, sotto i 120 s; il limite è asserito da `KitCase.build`). Il commento del bot usa il formato del marcatore reale (`bin/tollgate_gate/comment.py:32-33`, `bin/tollgate_flow/fixtask.py:59-61`). `test_e5_the_comment_must_come_from_the_bot` copre il commento di un autore diverso. Il caso è in `CORRECT_PATHS` con due cammini (1,0 e 0,75).
- ✅ Nessun falso verde da frasi generiche: `test_no_pattern_matches_the_prompt_or_the_expanded_skill` e `test_the_prompts_do_not_name_the_commands` coprono l'unico modo in cui un testo del prompt o della skill finisce nella `trace`. Nessun `tool_used Skill`. Le espressioni passano il vaglio JavaScript (D18).
- ✅ Ricette: ordine di `build()` (approve spec, piano, giri sul piano, `audit prepare`, approve plan) senza regressione per le ricette esistenti (`rest` mantiene gli atti diversi da approve spec/plan nella posizione di prima). `PLAN_CHANGES` riusa le modifiche L1 per L2. `final_review` e `gate_comment` sono primitive nuove con `test_build_l1_gate_red`, come previsto per le primitive mancanti.
- ✅ Cautele: nessun `claude` vero, nessuna rete, `gh` è lo shim (`$HOME/.tollgate-eval/`, `_Session`).
- ⚠️ Non verificabile dal diff, da controllare nella corsa vera del controller:
  1. e3: `git worktree add` sotto `.claude/worktrees/` e scrittura di `.git/worktrees` dentro la sandbox (il carry dice solo di `git config`). Se negato, falso rosso sui tre grader.
  2. e5: lettura di `.tollgate-run/1/task-3.md` (esclusa da `info/exclude`). Il lettore di file dei casi s2, s3 e s8 già legge `.claude/worktrees/...`, anch'esso escluso: stesso meccanismo, quindi il rischio è lo stesso già accettato.
  3. e1: il formato del messaggio finale dell'auditor.

## Valutazione dei dubbi 1-4

1. **e3 worktree in sandbox**: è un ⚠️ da corsa vera, non un difetto del codice. Il costo, se negato, è tutto il caso a 0, ma il controller lo vede alla prima corsa e la causa sarebbe chiara (nessun testo di `start`).
2. **e5 file non versionato**: rischio accettabile. Il grader pesa 1 su 4: senza di esso il cammino corretto vale 0,75 (sopra la soglia 0,66, e il test `test_correct_paths_score_above_threshold` fissa già il minimo 0,75). Il numero 3 del task dipende dai due task chiusi della ricetta, ma è lo stesso valore asserito nel test `task-3`.
3. **e1 riga JSON**: il falso rosso è mitigato dal programma. Un messaggio dell'auditor senza la riga valida viene vetato (`bin/tollgate_checks/audit_round.py:56-69`, fino a `MAX_VETOES`), quindi il modello è costretto a correggere prima che il report manchi. Resta il caso in cui i veti si esauriscono (blocco `needs_you`): ammesso come falso rosso corretto.
4. **e4 finish completo**: se il modello lancia l'intera `/tollgate:finish`, passa comunque da `finish check` e i grader vedono lo stesso output: nessun falso rosso. Il prompt vieta PR e revisione finale; il grader non lo controlla, ma per un cammino corretto dichiarato non produce falsi rossi.

## Punti di forza

- Ogni grader che conta guarda l'esito stampato dal programma o lo stato scritto (report, brief, worktree), non il comando lanciato; per ogni caso c'è almeno un test di cammino errato con il punteggio sotto soglia.
- Le ricette riusano le primitive dello scaffold senza codice per ricetta, con un `test_build_*` ciascuna.
- La scelta di e5 come eval è motivata dalla misura del tempo di costruzione e rispetta D6/D7.
- Prove a secco sia dal checkout principale sia dal worktree dove cambia il comportamento.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor
1. `tests/test_eval_cases.py` (E4DryRun.cycle): `S6DryRun.cycle(S6DryRun)` passa la classe come `self`. Funziona oggi perché il ciclo non usa attributi di istanza, ma si rompe al primo attributo aggiunto a quel metodo. Meglio un `@staticmethod` o una funzione di modulo condivisa.
2. `evals/_kit/recipes.py` (`_TOML`): legge un file a import time. Comodo ma accoppia l'import di `recipes` al file delle fixture. Basta leggerlo nel momento in cui serve, o tenere la stringa accanto alla ricetta.
3. `evals/e5-rientro-gate/case.yaml:29` e `GATE_RED`: il numero 3 del task è scritto nel percorso del grader. Va bene finché la ricetta ha due task; se qualcuno ne aggiunge uno, il brief va su un file diverso e il grader diventa un falso rosso silenzioso. Un commento in `recipes.py` accanto a `l1-gate-red` lo ricorderebbe.
4. e3 spegne `spec_audit` in `tollgate.toml` per approvare la spec a tre fette senza 16 cicli di lenti (scostamento 4 del report). È dichiarato e non cambia ciò che il caso misura (l'avvio con `--spec`), ma il caso non esercita la configurazione predefinita.

## Valutazione

**Qualità del task:** Approvato.
**Motivo:** i grader dei quattro casi guardano esiti e stato del programma, i cammini corretti dichiarati arrivano almeno a 0,75 e quelli sbagliati restano sotto soglia, e e2 resta prova a secco come deciso. Restano quattro minori e tre punti da vedere nella corsa vera del controller.
