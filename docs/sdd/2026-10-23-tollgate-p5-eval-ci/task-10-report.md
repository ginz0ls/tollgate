# Task 10 - Casi extra e1-e5: report dell'implementatore

## Cosa è stato fatto

Quattro casi eval (e1, e3, e4, e5, tag `extra`, ablazione `none`: contano tutti i grader) e una sola prova a secco senza caso (e2).
Le ricette nuove sono composte dalle primitive del banco; le primitive mancanti sono aggiunte allo scaffold e hanno il loro test.

| Caso | Eval o prova a secco | Perché |
|---|---|---|
| e1-audit-a-lenti | eval | l'ingresso nel worktree col `cd` (D2); tutto passa da `audit prepare` e dall'agente `tollgate:spec-auditor` |
| e2 (`reopen spec`) | **solo prova a secco** (`E2DryRun`), nessun `evals/e2-*` | D1 definitivo: un atto digitato vale solo in una sessione legata al lavoro, la corsa parte con una sessione non legata e il prompt di un caso è uno solo. La prova a secco lo mostra: con la sessione `scaffold` l'atto si applica, con quella della corsa `act apply` risponde «nessun atto da applicare per questa sessione» (dal worktree) o «nessun lavoro attivo» (dal checkout principale) |
| e3-start-spec | eval | `start` si lancia dal checkout principale, dove la corsa parte: nessun `cd` |
| e4-chiusura-l2 | eval, nella forma «L2, `/tollgate:execute` fino a `task done 2` e `finish check`» | niente PR, niente atto `finish` |
| e5-rientro-gate | **eval** (la ricetta si costruisce col programma vero in 9 s) | PR aperta con `finish open-pr` dal programma (revisione finale `ok` con gli eventi dei subagenti), commento rosso del bot nei dati del `gh` finto, poi `start 1 --reopen-execution --confirm` |

### File
- `evals/_kit/recipes.py`: campi `plan_audit_rounds`, `merge_default`, `gate_comment`, `reopen_execution`; `finish: open-pr` ora vale anche in L1 e L2; `PLAN_CHANGES` (il piano L2 ha gli stessi due task del piano L1); cinque ricette nuove (`l2-spec-three-slices`, `l2-first-slice-merged`, `l2-plan-approved`, `l2-task2-pending`, `l1-gate-red`); `GATE_RED`; `CORRECT_PATHS` di e1, e3, e4, e5.
- `evals/_kit/scaffold.py`: `write_plan` (piano di L2 committato), giri sul piano e `approve plan` nell'ordine giusto in `build()`, `final_review` (ciclo di revisione finale `ok` per `finish open-pr` in L1 e L2), `gate_comment`, `merge_default` (ff-only su main e push sul nudo), `--reopen-execution --confirm`.
- `evals/_kit/fixtures/specs/calc-l2-tre-fette.md` (spec a tre fette per e1 ed e3).
- `evals/e1-audit-a-lenti/`, `e3-start-spec/`, `e4-chiusura-l2/`, `e5-rientro-gate/`: `case.yaml` e `scaffold.sh`.
- `tests/test_eval_kit.py`: `test_build_l2_spec_three_slices`, `_l2_first_slice_merged`, `_l2_plan_approved`, `_l2_task2_pending`, `_l1_gate_red`, `RecipeTest`.
- `tests/test_eval_cases.py`: `E1DryRun`..`E5DryRun` (E2 senza caso), `ExtraCasesTest`; il passo `prompt` (`UserPromptExpansion`) e la sessione per passo; lo shim `gh` in testa al PATH delle prove a secco (`$HOME/.tollgate-eval/` come nella corsa); `recipe_of` legge il campo `recipe` di un caso senza cartella.

## Ricette (tempi misurati, macchina scarica; tutte sotto i 120 s di VE4, il limite è asserito da `KitCase.build`)
| Ricetta | Sequenza | Fase | Tempo |
|---|---|---|---|
| `l2-spec-three-slices` | `start --level L2`, spec a tre fette committata, un giro avversariale pulito | spec_audit | 2,4 s |
| `l2-first-slice-merged` | + `approve spec 3` (il lenti è spento in `tollgate.toml`: `[components] spec_audit = false`), ff-only di `main` sul ramo del lavoro, push sul nudo; issue 1 e 2 nei dati del `gh` | plan | 3,4 s |
| `l2-plan-approved` | spec approvata, piano committato, giro dell'avversario del piano pulito, `audit prepare` (porta ad `approval`), `approve plan` | execution | 6,0 s |
| `l2-task2-pending` | + task 1 chiuso col ciclo vero (implementatore, `verify`, revisore, `task done`) | execution | 8,3 s |
| `l1-gate-red` | L1, due task, `finish check`, atto `finish`, revisione finale `ok`, `finish open-pr`, commento rosso del bot, `start 1 --reopen-execution --confirm` | execution | 9,3 s |

## Per caso

Il punteggio di un cammino è la somma dei pesi dei grader che passano su quella di tutti (contano tutti); soglia 0,66, ogni cammino corretto almeno 0,75 (`test_correct_paths_score_above_threshold`, già valido per i casi `extra`).

### e1-audit-a-lenti (ricetta `l2-spec-three-slices`)
- Prompt: `/tollgate:spec-audit`, la frase del `cd` verso `.claude/worktrees/tg-1-operazioni-della-calcolatrice`, poi «La spec ha tre fette e l'utente accetta il costo dell'audit a lenti. Fai il primo ciclo a lenti, leggi il suo report e fermati: gli altri cicli non servono.» (il sì dell'utente sta nel prompt perché il caso chiede l'auditor lanciato; il limite al primo ciclo tiene il costo: l'audit vero ne fa da 16 a 30). `max_turns` 40, `timeout_seconds` 1500.
- Grader: `conferma-chiesta` (regex trace, `conferma: audit a lenti: da \d+ a \d+ cicli di tollgate:spec-auditor`, 1); `ciclo-aperto` (regex trace, `ciclo a lenti della spec 1, punto di vista \w+ su docs/superpowers/specs/calc-l2-tre-fette\.md`, 2: testo stampato solo a ciclo aperto da `--confirm`); `auditor-lanciato` (`tool_used` Agent `tollgate:spec-auditor`, 1); `report-lenti-scritto` (`file_exists` `**/docs/superpowers/reviews/1/spec-lens-*.md`, 1: lo scrive il hook).
- Cammini: conferma chiesta e poi data: 5/5 = 1,0; conferma data subito (`--confirm` al primo colpo, il sì è nel prompt): 4/5 = 0,8. Fermarsi alla domanda: 1/5 = 0,2 (sotto soglia).
- Prova a secco (worktree): `audit prepare` esce con 3 e stampa «conferma: audit a lenti: da 16 a 30 cicli di tollgate:spec-auditor, più i giri avversariali di conferma» e il prossimo passo con `--confirm`; con `--confirm` stampa «ciclo a lenti della spec 1, punto di vista executor su docs/superpowers/specs/calc-l2-tre-fette.md (blob …)» e `agente: tollgate:spec-auditor brief: ".../spec-lens-1.md"`; l'Agent non è negato; lo `SubagentStop` con la riga JSON del brief scrive `reviews/1/spec-lens-1.md` (`kind: "spec-lens"`). Dal checkout principale `audit prepare --confirm` esce 1 («nessun lavoro attivo…») e nessun grader passa. Un Agent auditor lanciato senza il ciclo aperto passa solo `auditor-lanciato` (0,2).

### e2 (solo prova a secco, ricetta `l2-spec-approved`)
- `test_e2_dry_run`: `UserPromptExpansion` `tollgate:reopen` con argomenti `spec la fetta 2 manca` nella sessione `scaffold` (legata), poi `act apply`: «atto a-N applicato (reopen spec): spec riaperto (la fetta 2 manca): fase spec_audit. I file di approvazione restano come storico e non valgono più: correggi la spec, committala e riparti da … audit prepare.»; `status` mostra `fase spec_audit  livello L2` (partiva da `plan`). Il testo cercato è quello vero di `reopen` (D19: «spec riaperto (<motivo>): fase spec_audit»).
- Perché non è un eval: con la sessione della corsa (non legata) l'atto non si applica (`test_e2_the_run_session_is_not_bound_so_the_act_does_not_apply`); `test_e2_without_a_reason_is_refused` e `test_e2_has_no_eval_case` (nessun `evals/e2-*`, nessuna voce in `CORRECT_PATHS`).

### e3-start-spec (ricetta `l2-first-slice-merged`)
- Prompt: `/tollgate:start #2 --spec docs/superpowers/specs/calc-l2-tre-fette.md`, «Quando tollgate ha creato il lavoro, fermati: il piano si scrive in una sessione pulita.» Nessun `cd` (la corsa parte dal checkout principale, dove `start` va lanciato). `max_turns` 25, `timeout_seconds` 900.
- Grader: `lavoro-in-fase-plan` (regex trace, `lavoro #2 avviato: livello L2, fase plan, ramo tg/2-divisione`, 2); `spec-approvata-riconosciuta` (regex trace, `spec approvata: docs/superpowers/specs/calc-l2-tre-fette\.md \(approvazione in docs/superpowers/reviews/1/\)`, 1: stampata solo se la fetta è riconosciuta e la spec è quella approvata); `worktree-creato` (`file_exists` `**/worktrees/tg-2-divisione/src/calc.py`, 1).
- Cammino corretto: 4/4 = 1,0. Senza `--spec` (`start 2`): «livello L0, fase execution», nessuna riga della spec, solo `worktree-creato` = 0,25. Spec non sul predefinito: uscita 1, nessun grader.
- Prova a secco (dal checkout principale e dal worktree della prima issue): uscita 0, le due righe sopra, `status` con `#2 … fase plan  livello L2`; la prima issue resta dov'è. Le righe `avviso:` sugli stati/Actions del `gh` finto (dati assenti) non fermano `start`.
- Nota (carry): `start` scrive `git config tollgate.defaultBranch` nel workspace; la sandbox non lo nega (non provato qui: è un fatto del carry).

### e4-chiusura-l2 (ricetta `l2-task2-pending`)
- Prompt: `/tollgate:execute`, il `cd` verso `tg-1-aggiungi-la-moltiplicazione`, «Quando tutti i task sono chiusi, fai il controllo locale della Definition of Done del lavoro. Non aprire la PR e non lanciare la revisione finale.» (non nomina `finish check`). `max_turns` 50, `timeout_seconds` 1800.
- Grader: `implementatore-lanciato` (`tool_used` Agent `tollgate:implementer`, 1); `task-2-chiuso` (regex trace `task 2: done`, 1); `approvazioni-l2-nel-controllo` (regex trace `\[sì\] Spec e piano approvati, report avversariali presenti`, 1: riga di L2 stampata solo da un `finish check` che è arrivato alla DoD, quindi dopo `task done 2`); `controllo-verde` (regex trace `prossimo passo: python3 [^\\]*bin/tollgate'? review prepare`, 2: il passo successivo di un controllo verde in L2; le virgolette sul percorso ci sono solo se ha spazi, `[^\\]` non attraversa le righe JSON).
- Cammino corretto: 5/5 = 1,0. Task chiuso senza controllo: 2/5 = 0,4. Controllo prima del task: uscita 2 «task non chiusi con verdetto approved: 2», nessun grader.
- Prova a secco: ciclo del task 2 come in s6 (anche il veto del redirect del coordinatore in L2 è verificato), poi `finish check` esce 0 con tutte le voci `[sì]` (le due `[dopo la revisione]` sono quelle della revisione finale) e `prossimo passo: python3 '…/bin/tollgate' review prepare`. Il controllo è verde senza atto `finish` e senza PR (verificato). Dal checkout principale `task start 2` esce 1 e `finish check` 2.

### e5-rientro-gate (ricetta `l1-gate-red`)
- Prompt: `/tollgate:execute`, il `cd`, «Il gate su GitHub ha giudicato rossa la PR di questo lavoro e ha lasciato il suo commento sulla PR. Avvia il task che corregge quanto il gate segnala e lancia il suo implementatore; quando ha finito, fermati.» (il checkpoint in `execution` con tutti i task chiusi dice `/tollgate:finish`, quindi il rosso del gate va detto). `max_turns` 40, `timeout_seconds` 1200.
- Grader: `task-di-correzione-creato` (regex trace `task 3: tollgate:implementer name=tg-1-t3 launch`, 2: il riepilogo che `task start --from-gate` stampa a task creato); `brief-con-il-commento-del-gate` (regex sul file `.claude/worktrees/tg-1-aggiungi-la-moltiplicazione/.tollgate-run/1/task-3.md`: due lookahead, il marcatore `tollgate-verdict sha=<40 esadecimali>` e «must-have M2 non coperto», 1: lo scrive il programma dal commento); `implementatore-lanciato` (`tool_used` Agent `tollgate:implementer`, 1).
- Cammini: 4/4 = 1,0; fermandosi dopo l'avvio del task (senza il lancio): 3/4 = 0,75. Andare a `finish check` invece: 0.
- Prova a secco: `status` mostra `fase execution  livello L1`; `task start --from-gate` esce 0 con il percorso del brief e `task 3: tollgate:implementer name=tg-1-t3 launch revisore: tollgate:task-reviewer`; il brief contiene il commento del gate in un recinto; l'Agent `tg-1-t3` non è negato. Con l'autore del commento cambiato in `mallory`: «nessun commento del gate sulla PR #1 …» e nessun task (il marcatore lo scrive chiunque, contano i commenti del bot). Dal checkout principale: «nessun lavoro attivo». Il commento ha lo SHA della testa della PR nel `gh` finto (`headRefOid`).

## RED / GREEN
- RED (prima di aggiungere i test di ricetta): `python3 -B -m unittest tests.test_eval_kit.BuildTest.test_every_recipe_has_a_build_test` → FAILED, `- ['l2-spec-three-slices', 'l2-first-slice-merged', 'l2-plan-approved', 'l2-task2-pending', 'l1-gate-red']`. Il codice dello scaffold l'ho provato con uno script prima dei test (ricette costruite una per una, uscite lette): dichiaro che per lo scaffold non è stato un RED puro.
- Due errori di test corretti in corsa: `rows(...)` confrontato con tuple (e3), e un test del controllo rosso di e4 che non poteva esistere (il redirect del coordinatore è negato in L2: l'ho sostituito col test del veto).
- GREEN mirato: `tests.test_eval_kit.BuildTest` + `RecipeTest` 25 OK; `E1DryRun`..`E5DryRun`, `ExtraCasesTest`, `CaseShapeTest`, `ScoreTest` OK.
- `tests/run` (python3.11 poi python3): vedi in fondo.

## Scostamenti dal piano e dal brief
1. e4 è «L2 fino a `task done 2` e `finish check`» (decisione del controller), non la forma del piano (`open-pr` e `final-reviewer`).
2. e5 entra negli eval (la ricetta si costruisce col programma vero sotto i 120 s): la primitiva «revisione finale `ok` per `finish open-pr`» in L1 e L2 è nuova, con il suo test (`test_build_l1_gate_red`).
3. e1: il prompt dà il sì dell'utente al costo e limita a un ciclo a lenti (il piano chiede `tool_used` auditor e la conferma; senza il sì il caso si fermerebbe alla domanda).
4. e3: la ricetta spegne il componente `spec_audit` (audit a lenti) in `tollgate.toml` per poter approvare una spec a tre fette senza 16 cicli di lenti; il resto dell'audit (avversario) è vero. È un'alternativa a `audit decline` più `resolve`, che richiede un atto e un blocco in più.
5. `_Session` (prove a secco) mette un involucro dello shim `gh` in testa al PATH, come la corsa; il passo `prompt` e il campo `session` dei passi sono nuovi.

## Autorevisione
- Completezza: e1-e5 come decisi, `test_e<N>_dry_run` per tutti (e2 senza `case.yaml`), `CORRECT_PATHS` per i quattro eval, ricette con `test_build_*`.
- Carry: `cd` in e1/e4/e5; e3 senza `cd` perché `start` va dal principale; espressioni cercate nella `trace` come JavaScript; nessun `tool_used Skill`; nessun grader sullo stderr; esiti dal programma (testi stampati solo a cosa avvenuta, report, brief); i prompt non nominano i comandi (`test_the_prompts_do_not_name_the_commands`) e le espressioni non trovano il testo del prompt né della skill espansa (`test_no_pattern_matches_the_prompt_or_the_expanded_skill`).
- Nessun `claude` vero, nessuna rete, nessun `gh` vero (shim e fakegh), HOME temporanee, nessun processo fermato.

## Dubbi (falsi verdi e falsi rossi)
1. **e1 falso rosso**: se l'auditor non chiude con la riga JSON del brief (conteggi), il hook non scrive il report e `report-lenti-scritto` fallisce, anche con ciclo aperto. Se il modello chiede il sì all'utente nonostante il prompt, resta a 0,2.
2. **e1 falso verde**: nessuno vistoso; `ciclo-aperto` richiede l'uscita del programma.
3. **e3**: da provare nella sandbox che `git worktree add` e la scrittura di `.git/refs/heads` e `.git/worktrees` nel workspace non siano negate (la sandbox nega `.git/config` della HOME, non del workspace; lo dice il carry, non l'ho potuto provare qui). Se negato: falso rosso su tutti e tre i grader.
4. **e4**: il modello potrebbe non lanciare `finish check` ma `/tollgate:finish` per intero, con `review prepare` e i revisori finali (costo): il prompt lo vieta ma è un'indicazione. `controllo-verde` e `approvazioni-l2-nel-controllo` vedono lo stesso output: se il controllo è rosso per un motivo del modello (file non committato), falliscono insieme (falso rosso corretto).
5. **e5**: `brief-con-il-commento-del-gate` legge `.tollgate-run/1/task-3.md`, un file non versionato ed escluso da git: se il lettore di file del grader lo salta (come per i file ignorati) è falso rosso (senza il brief: 3/4 = 0,75 con il lancio dell'implementatore, 2/4 senza). Il numero 3 del task dipende dai due task chiusi della ricetta.
6. **Pesi**: i cammini corretti di e1 senza il testo di conferma e di e5 senza il lancio stanno a 0,8 e 0,75; un modello che non lancia l'implementatore e non apre il brief va a 0,5.
7. La riga «prossimo passo» del controllo verde di e4 contiene il percorso del programma: se il programma stampa il percorso con virgolette doppie in un'altra forma (`program_command` oggi usa `shlex.quote`) il pattern perderebbe; l'espressione tollera l'assenza di virgolette singole.

## Esito di `tests/run` e commit
- python3.11: `Ran 2805 tests in 1234.008s OK (skipped=2)`; python3 (3.13.5): `Ran 2805 tests in 1209.531s OK`. Una sola riga extra (`guard: la PR è avanzata dopo l'evento…`, di un test preesistente).
- Commit `f3bd638 tollgate P5: casi di eval extra e1-e5 con le prove a secco`.
