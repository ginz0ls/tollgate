# tollgate P3b: chiusura del lavoro

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portare un lavoro da «tutti i task `done`» alla PR aperta e seguirlo dopo: `finish check`, revisione finale con verificatore, `finish open-pr` con il blocco JSON 18.1, `task start --from-findings/--from-gate`, `sync`, `adopt`, `abandon`, `cleanup`, rilevamento di merge e chiusura, nuove voci di `act apply`, agenti `final-reviewer` e `finding-verifier`, skill `finish`, `sync`, `adopt`, `abandon`, `cleanup`.

**Architecture:** Il flusso nuovo sta in moduli nuovi di `bin/tollgate_flow` (`finishcheck`, `finalreview`, `openpr`, `prstate`, `fixtask`, `sync`, `adopt`, `closing`), che importano solo `tollgate_core` e `tollgate_analysis`. I dati nuovi (cicli di revisione, rilievi, intenti, PR del lavoro) entrano con la migrazione 4 e con due moduli di `tollgate_core` (`reviews`, `intents`). Le violazioni di test-guard e scope sull'intero diff si spostano da `tollgate_checks._common` in `tollgate_core.violations`, così `finish check` e gli hook usano lo stesso codice. Le funzioni pure (blocco JSON, corpo della PR, verdetti finali, must-have dal JUnit, file di approvazione) stanno in `tollgate_analysis`, perché P4 le riusa nel gate. Il verdetto del revisore finale e del verificatore lo chiude un modulo nuovo di `subagent_stop`, `final_review`.

**Tech Stack:** Python ≥ 3.11, solo libreria standard (`sqlite3`, `argparse`, `secrets`, `subprocess`, `unittest`), bash, git, `gh` 2.46. Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 22; la revisione 23 la scrive il Task 18): sezioni 3, 3.1, 4, 6.3 (`--from-findings`, `--from-gate`), 6.4, 6.5, 8.4, 8.6, 8.7, 10, 12.2, 12.3, 12.4, 13, 15, 18.1, 18.3, 18.5. Piano principale: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (sezione 3: contratti reali di P3a, «Vincoli per P3b e P3c», «Rinviati dalla revisione finale di P3a»; sezione 4: matrice dei criteri). Registro di P3a: `docs/sdd/2026-10-16-tollgate-p3a-avvio-e-task/`.

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11 (spec 2). Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- Strati (spec 3, `tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_flow` importa solo `tollgate_core` e `tollgate_analysis`; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`, tranne `tollgate_core/cli.py`; i moduli di `tollgate_checks` non scrivono nel DB, usano `record`.
- Scritture nel DB solo con le funzioni di `tollgate_core`. `set_phase`, `open_block` e `close_block` si chiamano fuori da una transazione. Errori da gestire: `db.DbError` all'apertura, `sqlite3.Error` durante le operazioni (vincoli 1-5 del piano principale). `compute_dod` riceve sempre `required_commands` (comandi del gate e `dod` dei profili) e `profile_items`.
- **Programma nei comandi per il modello:** ogni comando scritto in un messaggio della CLI, di un hook, di un brief o di una skill usa `tollgate_core.paths.program_command` (`python3 "<bin>"`); le skill scrivono `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`. Mai il percorso nudo (vincolo (2) di P3a per P3b).
- **Sessione della CLI:** ogni sottocomando che legge la sessione passa dal segnale di `cli_calls` (`sessions.cli_session`). Quelli di P3b sono `finish` (per `open-pr` con `approve pr`), `sync`, `adopt`, `cleanup`, `abandon` (vincolo (1)).
- La configurazione si legge dalla base del lavoro o dalla punta del ramo predefinito di `origin`, mai dal working tree (spec 3.2). `finish` e `sync` fanno prima `git fetch origin` (spec 3.2).
- Testo non fidato (issue, rilievi dei revisori, commento del gate): mai in un comando shell né in un argomento di `git` o `gh`. Va su file, in un recinto più lungo di ogni sequenza di backtick (`tollgate_analysis.brief.fence`), marcato come dato. Nel corpo della PR passa da `prbody.neutralize` (menzioni spente, lunghezza massima).
- Nessuna rete nei test. `gh` nei test è `tests/fakegh.py` con `TOLLGATE_GH` e la sentinella. I test spingono solo verso il repo nudo locale del banco (`FlowLab.origin`), dietro l'URL finto con `insteadOf`. **Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json` o `~/.claude/plugins/`.**
- I test non lanciano `claude`. Solo il Task 17 lancia `claude -p`, in `/tmp/tollgate-p3b`, con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

## Decisioni di questo piano

Scelte che la spec lascia aperte o che il codice reale impone, con il costo se sbagliate. Il Task 18 le riporta nella revisione 23 della spec.

1. **Migrazione 4** (solo in avanti, con la copia prima):
   - `work_items`: `pr_number INTEGER`, `pr_url TEXT`, `finish_sha TEXT` (SHA dell'ultimo `finish check` verde), `finish_report TEXT` (JSON delle voci calcolate da `finish check`), `extra_review_cycles INTEGER NOT NULL DEFAULT 0`, `review_unverified INTEGER NOT NULL DEFAULT 0`;
   - `review_cycles`: `code TEXT`, `stage TEXT` (`review`, `verify`, `closed`), `reviewers TEXT NOT NULL DEFAULT '[]'` (tipi attesi), `reported TEXT NOT NULL DEFAULT '{}'` (tipo → esito dichiarato), `opened TEXT`;
   - `findings`: `blocking INTEGER NOT NULL DEFAULT 1` (decisione 8);
   - `tasks`: `extra_fix_rounds INTEGER NOT NULL DEFAULT 0` (decisione 13).

   Costo: una migrazione.
2. **Segnale della CLI per P3b.** `cli_calls` registra il segnale anche per `finish`, `sync`, `adopt`, `cleanup` e `abandon`, e nega a un subagente anche `finish`, `review`, `sync`, `adopt`, `cleanup` e `abandon`. `sessions.cli_session` riceve `argv` e accetta la voce solo se `argv` coincide, poi la **toglie** (m11): un secondo lancio senza hook non eredita la sessione. Un parsing fallito con `agent_id` nega con lo stesso testo del diniego incerto (il messaggio breve rinviato da P3a). Costo: un comando ripetuto dal terminale senza hook rifiuta sempre.
3. **`abandon #N` non eredita il lavoro della sessione** (rinviato P2): come `adopt` e `cleanup`, l'atto ha `work` nullo e la CLI trova il lavoro attivo per (repo, N). Costo: nessuno.
4. **`finish check` è la copia locale minima del gate** (piano principale, rischio 2): esegue con `verify.run_gate` i comandi del gate e i `dod` dei profili attivi (ricevute `produced_by = "finish"`), calcola test-guard e scope su `work_base_sha..HEAD` con `violations.diff_violations`, i must-have dal JUnit della stessa esecuzione (`mustcheck`), i file di approvazione in L2 (`approvals`), e stampa la DoD voce per voce. Senza identificativi della base (P4). Verde: fase `review` (causa `finish_check_green`), `finish_sha = HEAD`, `finish_report`. Rosso: la fase resta `execution`. In `review` sullo stesso SHA è idempotente. Rifiuta se un task non è `done` con verdetto `approved` (legge `tasks.verdict`, vincolo (4)). Costo: P4 sostituisce i pezzi dietro la stessa interfaccia `finishcheck.check`.
5. **Ciclo di revisione** (10, 8.6). `review prepare` (sottocomando `tollgate review prepare`) guarda l'ultimo ciclo:
   - aperto sullo stesso SHA: lo riprende (stesso codice) e stampa i lanci mancanti (criterio 28: interruzione dopo `finish check`);
   - chiuso `ok` sullo stesso SHA o con lo stesso `patch-id`: nessun ciclo nuovo («revisione già superata»);
   - altrimenti apre il ciclo `n+1` con un codice `secrets.token_hex(4)`, uno per ciclo, valido per revisori e verificatore; i revisori attesi sono `tollgate:final-reviewer` più, solo in L2, i `final_specialist` dei profili attivi.

   Quando tutti i revisori attesi hanno riportato, lo stadio passa a `verify` e `review prepare` scrive il brief del verificatore con i rilievi senza esito, in ordine di gravità, fino a `max_findings`; gli altri diventano `unverified` («oltre max_findings»). Un rilievo senza `rule`, `file` o `line` intero si registra già `rejected` («senza prova», criterio 40). Senza rilievi da verificare il ciclo si chiude subito. Ogni riga di lancio è `agente: <tipo> brief: <percorso>[ model: <m>]`. Costo: un codice condiviso tra revisore e verificatore; li separa lo stadio.
6. **Esito del ciclo e tetti.** Alla chiusura: un revisore che ha dichiarato `needs_you` → blocco `needs_you`; altrimenti un rilievo confermato con `blocking = 1` e gravità effettiva `blocker` o `major` → `needs_fix`, fase `review → execution` (causa `needs_fix`); altrimenti `ok`. `counted = 1` se il ciclo ha rilievi confermati. Alla fine del ciclo contato numero `4 + extra_review_cycles` con `needs_fix` si apre `needs_you` con il motivo «cicli di revisione esauriti» (`checkpoint.CAPS`). `review prepare` rifiuta il nono ciclo: oltre serve `approve unverified-review`. Costo: nessuno, è la regola della spec.
7. **Revisore fermo per sola lettura.** Un revisore finale che legge per più di `stale_minutes` può essere segnato `interrupted` da `PreToolUse Agent` (vincolo (5)): `final_review` accetta anche le righe `interrupted` dei tipi attesi, con il controllo di sola lettura invariato. Costo: nessuno.
8. **Regole `[blocca]`** (8.6, vincolo (6), riga 108). Il profilo ha una chiave nuova `blocking_rules = []` (identificativi `R-…`). Un rilievo che cita una regola `R-…` dichiarata in `blocking_rules` di un profilo attivo, oppure un passo del piano (regola che non comincia con `R-`), è bloccante; una regola `R-…` presente solo nelle checklist e non in `blocking_rules` no; una regola `R-…` sconosciuta resta bloccante (fail-closed). Vale per il revisore del task (`verdicts.parse_task_verdict` riceve `blocking_rules`) e per la revisione finale (`findings.blocking`). Con lo standard acceso un `approved` dichiarato con un rilievo bloccante scartato per forma è non valido, come un `changes` (riga 108). Costo: un profilo senza `blocking_rules` ha tutte le sue regole non bloccanti: B le dichiara.
9. **Nomi degli agenti dei profili** (m9). Al caricamento, un `agent` che non ha la forma `<plugin>:implementer-<area>`, un `reviewer` fuori da `<plugin>:reviewer-<area>` o un `final_specialist` fuori da `<plugin>:final-<area>` diventano `""` con un avviso in `Config.warnings`: si usa l'agente generico. Costo: un profilo sbagliato lavora con i generici finché l'utente non legge l'avviso.
10. **`open-pr`** (6.4). Condizioni, raccolte e stampate insieme: fase `review`, `HEAD = finish_sha`; atto `finish` usabile su HEAD oppure `approve pr` della sessione su HEAD; in L1 e L2 con `final_review` acceso, ultimo ciclo `ok` su HEAD (o stesso `patch-id`) oppure `review_unverified`; nessun blocco aperto, nessuna deroga in attesa (`waivers.status`), nessun effetto `requested`; nessun rilievo senza esito; DoD verde (con `definition_of_done` spento si stampa e non ferma). Poi: intento `pr:<lavoro>:<sha>` → `git push origin <sha>:refs/heads/<ramo>` → `ls-remote` uguale a `<sha>` → PR esistente per il ramo (`gh pr list --head`)? `gh pr edit --body-file` : `gh pr create --head --base --title --body-file` → `pr_number`, `pr_url`, evento `pr_opened` o `pr_updated`, fase `pr_open`, intento `executed`, **atto consumato per ultimo** (un'interruzione lascia l'atto valido e la ripetizione non crea una seconda PR, criterio 12). Il push forzato (`--force-with-lease=refs/heads/<ramo>:<sha remoto letto prima>`) solo con un intento `force_push` autorizzato da `sync` o da `approve rebase`, consumato dal push. `--update` richiede una PR aperta. Titolo: `#<N> <slug del ramo con spazi>`, mai il titolo dell'issue (dato non fidato). Costo: un titolo meno leggibile; l'utente lo cambia su GitHub.
11. **Blocco JSON 18.1: contratto con P4.** `tollgate_analysis.prblock.build(PrFacts) -> dict` con tutti i campi di 18.1 nell'ordine della spec, `render(block) -> str` (`<!-- tollgate {...} -->`, con `<`, `>` e `&` scritti `<`, `>`, `&`: il testo non contiene mai `-->`) e `parse(text) -> dict | None` (l'ultimo blocco del testo; `None` se assente o non valido). Valori: `spec_audit` da `adversarial` e `lens` dei file di approvazione (o `null`); `acts` = atti `approve`, `resolve` e `reopen` del lavoro in qualunque stato, con `state` in più; `blocks` = blocchi aperti; `effects` = intenti `effect` eseguiti; `components_off` = chiavi di `[components]` a `false`; `off_periods` = intervalli `off`→`on` che toccano la vita del lavoro; `subagents` = conteggio e token del lavoro; `level_minimum` = massimo tra livello del diff, etichette e `min_level` dei profili attivi. P4 legge con `prblock.parse`. Costo: un campo nuovo non cambia `schema_version` (18).
12. **Merge e chiusura** (6.5, vincolo (8)). `prstate.detect` legge la PR di `work_items.pr_number`. `MERGED` → fase `closed` (causa `merged`) ed evento `merge_detected`, da qualunque fase. `CLOSED` senza merge: `start` esce con 3 e due strade (`/tollgate:abandon #N`, oppure `--confirm` che azzera `pr_number`: `open-pr` ne aprirà una nuova); `finish check`, `open-pr` e `sync` rifiutano con le stesse due strade. Lo chiamano `start` (ripresa), `finish check`, `finish open-pr` e `sync`. Costo: senza rete il rilevamento si salta con un avviso.
13. **`approve rounds <n>` e `resolve` ai tetti** (8.4, m12). Se è aperto il blocco «cicli di revisione esauriti»: `extra_review_cycles += n`, rifiutato se i cicli fatti più `n` superano 8; chiude il blocco. Se è aperto il blocco «giri di correzione esauriti sul task k»: `tasks.extra_fix_rounds += n` sul task k (tetto 8 giri in tutto) e chiude il blocco; `task start k --fix` ammette `5 + extra_fix_rounds` giri. Con entrambi aperti, rifiuta e chiede `resolve` su uno dei due. `resolve` sul blocco dei cicli concede **un** ciclo (`extra_review_cycles += 1`). Costo: `approve rounds` ha due usi, distinti dal blocco aperto.
14. **Altri atti applicabili** (`actapply.APPLIERS`):
    - `approve finding <id> <gravità|dismiss> <motivo>`: `user_decision = downgraded:<gravità>` o `dismissed` su un rilievo confermato del lavoro; ricalcola l'esito dell'ultimo ciclo su HEAD (`needs_fix` → `ok` se non resta nulla di bloccante) e chiude il blocco dei cicli se aperto;
    - `approve unverified-review`: solo con almeno 8 cicli; `review_unverified = 1`;
    - `approve rebase`: dopo il blocco del `sync`, `work_base_sha = merge-base(HEAD, origin/<predefinito>)` (evento `base_realigned`), chiude il blocco, fase `execution` (causa `sync`), un intento `force_push`;
    - `approve unverified-tests` non si applica: vale dal DB in ogni stato, come `approve waiver`; con l'atto `dod.receipt_verdict` conta `unverified` come verde (`allow_unverified`). Costo: nessuno.
15. **DoD dei rilievi** (rinviato P1). `dod._findings` blocca un rilievo confermato `blocking = 1` con gravità `blocker`/`major` se `user_decision` è nullo **o** `downgraded:blocker`/`downgraded:major`; passa con `dismissed` o con un declassamento a `moderate`/`minor`. La voce `specialists` (L2) è vera quando l'ultimo ciclo su HEAD ha il riporto di ogni specialista atteso. Costo: nessuno.
16. **`task start --from-findings <ciclo>`** (6.3, criteri 26 e 37): fase `execution`, ciclo `needs_fix`, nessun task con `source = "cycle:<n>"` già presente. Crea il task `max+1` con `kind = "fix"`, il brief scritto dai rilievi confermati bloccanti del ciclo (in un recinto), lo scope invariato (file dei rilievi dentro lo scope; uno fuori scope si dichiara nel brief come deroga da chiedere), l'instradamento da `task_routing` sui file dei rilievi. Il piano non si tocca. **`--from-gate`**: fase `execution`, PR nota; legge con `gh pr view <n> --json comments` l'ultimo commento che comincia con `<!-- tollgate-verdict` (contratto verso P4) e lo passa come dato; `source = "gate:<sha>"`. Costo: P4 deve scrivere quel marcatore.
17. **`sync`** (6.5, criterio 16). Dopo l'atto `sync` della sessione, fasi `execution` o `pr_open`: intento `sync:<lavoro>:<atto>` con gli SHA di partenza e di arrivo; `fetch`; se `origin/<ramo>` ha commit non in HEAD li integra con `merge --ff-only` (rami divergenti → `needs_you`); `rebase origin/<predefinito>`; conflitto → `rebase --abort`, base e fase invariate, `needs_you` con le due strade (risolvere fuori da Claude e `/tollgate:approve rebase`, oppure `/tollgate:abandon #N`). Riuscito: i commit riscritti diventano eventi `commit` (gli hook non li trattano come nuovi), `work_base_sha` = punta del predefinito (`base_realigned`), fase `pr_open → execution` (causa `sync`), intento `force_push`, poi `finish check` e, se il `patch-id` è lo stesso e l'ultimo ciclo era `ok`, `open-pr --update` autorizzato dall'atto `sync`. Con `patch-id` diverso si ferma con «serve una nuova revisione: /tollgate:finish». La ripresa (`start`) completa un `sync` interrotto con il rebase finito (`sync.complete_interrupted`). I commit riscritti non si riattribuiscono ai task: sono già `done`. Costo: dopo un rebase con contenuti diversi serve un nuovo ciclo.
18. **`adopt #N`** (12.4, criterio 17). Da una sessione qualunque, dopo l'atto; nessun lavoro attivo per (repo, N). Ramo: il `tg/<N>-*` locale, oppure quello remoto (ramo locale creato con `gitw.create_branch`); più di un candidato → rifiuto con l'elenco. Worktree: se il ramo è già in un worktree (`git.worktrees`) si riusa quello (riga 74, niente `--force`); altrimenti `worktree_add`. Base = `merge-base(origin/<predefinito>, ramo)`. Livello: diff più etichette dell'issue, tetto dal blocco JSON della PR aperta (`prblock.parse`). Fase, con la regola «senza prova la fase torna a quella che precede l'atto mancante»: L0 `execution`; L1 senza piano `plan`, con piano `execution`; L2 senza `spec-approval.md` `spec_audit`, senza `plan-approval.md` `approval`, con entrambi `execution`; PR aperta `pr_open`; PR unita → rifiuto. Il piano (primo file nuovo sotto `docs/superpowers/plans/` che passa `plan-check`) registra scope e task, tutti `pending`: rieseguiti, finiscono come «task già soddisfatto» (C11 di P3a). Deroghe dal file del ramo, nessuna approvata. `phases.create_work` riceve `phase` e `cause` (evento `phase_change` con causa `adopt`). Poi legame, segnalino, radici attive, `prossimo passo: EnterWorktree`. Costo: dopo un DB perso ogni task si rivede una volta.
19. **`cleanup`** (12.4). Dopo l'atto. Senza `--confirm` elenca ed esce con 3, senza consumare l'atto; con `--confirm` consuma e cancella. Elenco: rami e worktree dei lavori `closed` del repo; con `--orphans` anche i rami `tg/*` senza nessuna riga (riga 55), altrimenti solo indicati con «adottalo con /tollgate:adopt #N». Un worktree sporco non si rimuove (avviso). Il ramo si toglie con `gitw.delete_branch` sullo SHA letto in quel momento. Costo: un comando in due passi.
20. **`abandon #N`**: dopo l'atto, fase `closed` (causa `abandoned`); ramo, worktree e PR restano (si tolgono con `/tollgate:cleanup` e su GitHub). Costo: nessuno.
21. **`[review] models`** (spec 3, mai applicato in P3a): le righe di lancio di `review prepare` e il riepilogo di `task start` riportano `model: <m>` se `models` ha il tipo dell'agente; i giri 4-5 restano `inherit`. Costo: nessuno.
22. **Impronta senza cache** (m13): `git.fingerprint` salta i file sotto cartelle `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache` a qualunque profondità. Costo: un revisore che scrive lì non viene visto.
23. **`report.json_candidates` con un tetto** (riga 102): esamina solo gli ultimi `MAX_SCAN_CHARS = 65536` caratteri e al più `MAX_DECODES = 500` aperture di `{`. Costo: un JSON finale più lungo di 64 KiB non viene trovato (fail-closed: verdetto non valido).
24. **Prova reale senza rete** (Task 17): il solo push è verso il repo nudo in `/tmp/tollgate-p3b/flow/origin.git`, dietro l'URL finto con `insteadOf`; lo script verifica `git remote get-url --push origin` prima di lanciare `claude` e si ferma se non è quel percorso. Costo: nessuno.
25. **Eventi nuovi** (18.4, campi e tipi nuovi non cambiano la versione): `finish_check` {sha, ok}, `base_realigned` {from, to, cause}. Costo: nessuno.
26. **Criterio 41, seconda frase** («spec L2 senza `## Cosa non fare` → rilievo dell'avversario»): è dell'avversario della spec, quindi passa a P3c. Costo: nessuno.

## Rilievi ripresi qui

| Rilievo | Dove |
|---|---|
| Vincoli P3a→P3b (1) segnale, (2) programma, (3) worktree pulito, (4) `tasks.verdict`, (5) sessione viva, (6) `[blocca]`, (7) checkpoint ignorato, (8) merge e chiusura, (9) skill `finish` | (1) Task 2; (2) Global Constraints e Task 16; (3) Task 16; (4) Task 6 e 9; (5) Task 8 (decisione 7); (6) Task 5; (7) Task 6; (8) Task 13; (9) Task 16 |
| m9 nomi degli agenti dei profili | Task 5 |
| m11 segnale consumato e `argv` confrontato | Task 2 |
| m12 uscita dopo i 5 giri di correzione | Task 10 (`approve rounds`) e Task 15 (`next_step`) |
| m13 impronta e cache | Task 2 |
| Riga 55 ramo e worktree orfani dopo `WorkExists` | Task 12 (`adopt`) e Task 13 (`cleanup --orphans`) |
| Riga 56 PR vecchie filtrate lato client | Task 9 (`gh.prs_for_branch_prefix` con `--paginate`) |
| Riga 74 `worktree add --force` con il ramo in uso altrove | Task 12 |
| Riga 102 `json_candidates` quadratica | Task 2 |
| Riga 108 `approved` con un blocker scartato | Task 5 |
| Riga 133 checkpoint: revisione preparata o no | Task 15 |
| Messaggio breve di `cli_calls` al parsing fallito | Task 2 |
| P1/P2: `dod._findings` accetta ogni `user_decision` | Task 3 |
| P2: `abandon #N` eredita il lavoro della sessione | Task 2 |
| P2 T17: rebase e merge del predefinito portano commit estranei in `base..HEAD` | Task 11 (`sync` riallinea la base e registra i commit riscritti) |

Restano ad altri piani, non toccati qui: riga 82 (P3c), righe 56 di `sentinel_issues` e 163 (P4, P5), `from_approved_spec` senza `spec_path` (P3c).

## Review Focus

1. **`open-pr` interrotto** (push riuscito e `gh pr create` fallito; PR creata e processo morto prima dell'intento `executed`): la ripetizione non crea una seconda PR, aggiorna quella esistente, e l'atto `finish` resta valido fino alla fine. Test: Task 9 `test_interrupted_after_push_no_duplicate_pr`.
2. **Testo ostile dei revisori nella PR** (rilievo con ```` ``` ````, `@utente`, `-->`, `<!--`, testo di 10.000 caratteri): nessun markdown attivo né menzione, nessuna chiusura anticipata del commento, `prblock.parse(render(b)) == b`. Test: Task 9 `test_hostile_finding_text_neutralized_and_block_roundtrips`.
3. **Revisore finale fermo per sola lettura** (riga `interrupted` per `stale_minutes` mentre legge): il suo verdetto conta; uno che ha cambiato file no. Test: Task 8 `test_stale_interrupted_reviewer_verdict_counts`.
4. **`sync` con «Update branch» remoto e predefinito avanzato, poi conflitto o interruzione**: con il conflitto base e fase invariate e `needs_you`; interrotto dopo il rebase, la ripresa completa il riallineamento senza ripetere il rebase; mai un push forzato senza intento. Test: Task 11 `test_remote_merge_then_rebase`, `test_conflict_aborts_and_blocks`, `test_interrupted_sync_completed_by_start`.
5. **`adopt` con il ramo già in un worktree o solo remoto** (avvio interrotto, DB perso, altra macchina): nessun `--force`, nessun ramo duplicato, il worktree esistente si riusa. Test: Task 12 `test_branch_in_existing_worktree_reused`, `test_remote_only_branch`.

## Mappa dei file

| File | Responsabilità |
|---|---|
| `spikes/run-p3b-experiments.sh`, `docs/verifiche/2026-10-19-p3b-verifiche.md` | Verifiche del Task 1 |
| `bin/tollgate_core/db.py` | Migrazione 4 |
| `bin/tollgate_core/reviews.py` (nuovo) | Cicli di revisione e rilievi: apertura, riporti, verifica, chiusura con esito e tetti |
| `bin/tollgate_core/intents.py` (nuovo) | Intenti di PR, `sync` e push forzato |
| `bin/tollgate_core/violations.py` (nuovo) | Test-guard e scope su un intervallo di commit, per hook e `finish check` |
| `bin/tollgate_core/{phases,acts,dod,verify,sessions,git,config,events,stats,tasks}.py` | Funzioni nuove e correzioni elencate nei task |
| `bin/tollgate_core/cli.py` | Sottocomandi `finish`, `review`, `sync`, `adopt`, `cleanup`, `abandon`, `task start --from-*` |
| `bin/tollgate_flow/finishcheck.py` | `finish check` |
| `bin/tollgate_flow/finalreview.py` | `review prepare` |
| `bin/tollgate_flow/openpr.py`, `bin/tollgate_flow/prstate.py` | `finish open-pr`; merge e chiusura |
| `bin/tollgate_flow/fixtask.py` | `task start --from-findings` e `--from-gate` |
| `bin/tollgate_flow/sync.py`, `adopt.py`, `closing.py` | `sync`; `adopt`; `abandon` e `cleanup` |
| `bin/tollgate_flow/{actapply,checkpoint,start,taskcmd,gh,gitw}.py` | Voci nuove di `act apply`, prossimo passo, ripresa, `gh` e git in scrittura |
| `bin/tollgate_analysis/prblock.py`, `prbody.py` | Blocco JSON 18.1 e corpo della PR |
| `bin/tollgate_analysis/mustcheck.py`, `approvals.py` | Must-have dal JUnit; file di approvazione 18.3 |
| `bin/tollgate_analysis/{verdicts,report,brief,profiles}.py` | Verdetti finali, `[blocca]`, tetto di `json_candidates`, brief della revisione finale |
| `bin/tollgate_checks/final_review.py` (nuovo) | Verdetti del revisore finale, degli specialisti e del verificatore a `SubagentStop` |
| `bin/tollgate_checks/{cli_calls,acts,_common,subagent_stop,task_verdict}.py` | Segnale, atti, violazioni delegate a core, revisori finali saltati |
| `bin/tollgate_hooks/apply.py` | Operazioni nuove `review_report`, `finding_verify` |
| `agents/final-reviewer.md`, `agents/finding-verifier.md` | Agenti |
| `skills/{finish,sync,adopt,abandon,cleanup}/SKILL.md`; `skills/{approve,execute,start,resolve}/SKILL.md` | Skill nuove e aggiornate |
| `tests/fakegh.py`, `tests/flowkit.py` | `gh` finto con le PR; banco con piano registrato, task chiusi e JUnit finto |
| `tests/test_*.py` | Un file per modulo; `tests/test_criteria_p3b.py` per i criteri |

---

### Task 1: Verifiche dell'interfaccia di `gh`

Il codice di P3b chiama `gh` in forme non ancora provate (spec 16: «`gh` vero» non esercitato). La verifica è sul testo d'aiuto della versione installata, **senza rete**. Su Claude Code non servono fatti nuovi: i revisori finali usano gli stessi eventi provati in P0-P3a.

**Files:**
- Create: `spikes/run-p3b-experiments.sh`, `docs/verifiche/2026-10-19-p3b-verifiche.md`

**Interfaces:**
- Produces: esiti G1-G5, che decidono le forme di `gh.py` (Task 9) e di `fakegh.py`.

**Regole di cautela (vanno nel brief):** niente rete: solo `gh --version` e `gh <comando> --help`. Mai `gh auth`, `gh api` verso GitHub, `gh pr create`. Nessun repo su GitHub.

- [ ] **Step 1: Script** `spikes/run-p3b-experiments.sh`: scrive in `/tmp/tollgate-p3b/help/` l'uscita di `gh --version`, `gh api --help`, `gh pr create --help`, `gh pr edit --help`, `gh pr list --help`, `gh pr view --help`.
- [ ] **Step 2: Rapporto** `docs/verifiche/2026-10-19-p3b-verifiche.md`, tabella `Id | Voce | Esito | Evidenza | Conseguenza`:
  - G1 segnaposto `{owner}`/`{repo}` di `gh api` presi dal repo della cartella corrente (atteso sì; resta non provato con `insteadOf` verso un repo locale, coperto da `fakegh`);
  - G2 `gh pr create` con `--head`, `--base`, `--title`, `--body-file` (atteso sì); l'URL stampato su stdout non è nell'aiuto: il codice rilegge la PR con `pr list --head` (decisione 10);
  - G3 `gh pr edit <n> --body-file`; G4 `gh pr list --head --state all --json number,state,url,headRefOid,mergedAt`; `gh pr view <n> --json comments`;
  - G5 `--paginate` con `--jq` (atteso: una riga JSON per elemento, pagina dopo pagina); `--slurp` assente in 2.46 (decisione per `prs_for_branch_prefix`).
  
  Più la versione di `claude` (`claude --version`), solo annotata.
- [ ] **Step 3: Commit** «tollgate P3b: verifiche dell'interfaccia di gh».

---

### Task 2: Segnale per i sottocomandi di P3b, atti, tetto di `json_candidates`, impronta senza cache

**Files:**
- Modify: `bin/tollgate_core/sessions.py`, `bin/tollgate_checks/cli_calls.py`, `bin/tollgate_checks/acts.py`, `bin/tollgate_analysis/report.py`, `bin/tollgate_core/git.py`, `bin/tollgate_core/cli.py` (passa `argv` a `cli_session` per `start` e `act`), `bin/tollgate_flow/start.py`, `bin/tollgate_flow/actapply.py`, `tests/flowkit.py`
- Test: `tests/test_sessions.py`, `tests/test_check_cli_calls.py`, `tests/test_check_acts.py`, `tests/test_report.py`, `tests/test_git.py`

**Interfaces:**
- Produces: `sessions.cli_session(state, cwd, subcommand: str, *, now, argv: list[str] | None = None) -> str`. Con `argv` la voce vale solo se `entry["argv"] == argv`; la voce trovata si toglie dal file (scrittura atomica come `note_cli_call`). `start.start` e `actapply.apply_act` ricevono `argv: list[str] | None = None` per parola chiave e lo passano; `cli.main` passa `argv` (gli argomenti dal sottocomando in poi). `FlowLab.cli` resta compatibile.
- Produces: in `cli_calls`, `_SIGNALLED = ("start", "act", "finish", "sync", "adopt", "cleanup", "abandon")`, `_COORDINATOR_ONLY = ("start", "task", "act", "finish", "review", "sync", "adopt", "cleanup", "abandon")`. Il ramo `BashParseError` nega con il testo di `_deny_subagent(None, certain=False)`.
- Produces: in `checks/acts.py` `abandon` ha `work_id = None`, come `adopt` e `cleanup` (decisione 3).
- Produces: `report.MAX_SCAN_CHARS = 65536`, `report.MAX_DECODES = 500`; `json_candidates` esamina solo la coda e si ferma al tetto (decisione 23).
- Produces: `git.CACHE_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")`; `git.fingerprint` salta un file se un segmento del percorso è in `CACHE_DIRS` (decisione 22).

- [ ] **Step 1: Test che falliscono**
  - `test_sessions.py::CliSessionTest::test_signal_consumed_once` (seconda `cli_session` con lo stesso segnale → `CliSessionError`);
  - `test_sessions.py::CliSessionTest::test_argv_mismatch_refused` (segnale `["start", "7"]`, `argv=["start", "8"]` → errore);
  - `test_check_cli_calls.py::test_p3b_subcommands_signalled` (dalla sessione principale `finish open-pr`, `sync`, `adopt 7`, `cleanup --confirm`, `abandon 7` → voce nel file del segnale; anche `finish check` lascia la voce `finish`, innocua perché non la legge; `review prepare` → comando ammesso, nessuna voce);
  - `test_check_cli_calls.py::test_subagent_denied_p3b_commands` (con `agent_id`: `finish check`, `review prepare`, `sync` → 2);
  - `test_check_cli_calls.py::test_parse_failure_message_explains` (comando con virgolette aperte che nomina `tollgate task` da un subagente → 2 e il testo contiene «modo letterale»);
  - `test_check_acts.py::ActsTest::test_abandon_act_has_no_work` (sessione legata al lavoro 7, `/tollgate:abandon #9` → atto con `work` nullo e `target == "9"`);
  - `test_report.py::ReportTest::test_json_candidates_capped` (testo di 200.000 `{` seguito dal JSON valido → trovato in meno di 1 s; JSON valido seguito da 70.000 caratteri → non trovato);
  - `test_git.py::FingerprintTest::test_cache_dirs_ignored` (repo senza `.gitignore`, `tests/__pycache__/x.pyc` creato → impronta invariata; `src/a.py` cambiato → cambia).
- [ ] **Step 2: Verificare il fallimento**: `python3 -B -m unittest tests.test_sessions tests.test_check_cli_calls tests.test_check_acts tests.test_report tests.test_git`.
- [ ] **Step 3: Implementare** le firme sopra.
- [ ] **Step 4: Verificare**: stesso comando, poi `tests/run`.
- [ ] **Step 5: Commit** «tollgate P3b: segnale per i sottocomandi di chiusura, abandon senza lavoro, tetto di json_candidates, impronta senza cache».

---

### Task 3: Migrazione 4 e dati della chiusura

**Files:**
- Modify: `bin/tollgate_core/db.py`, `bin/tollgate_core/phases.py`, `bin/tollgate_core/acts.py`, `bin/tollgate_core/dod.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/stats.py`, `bin/tollgate_hooks/context.py` (`approved_waivers` delega a `acts`)
- Create: `bin/tollgate_core/reviews.py`, `bin/tollgate_core/intents.py`
- Modify: `tests/flowkit.py`
- Test: `tests/test_db.py`, `tests/test_reviews.py`, `tests/test_intents.py`, `tests/test_phases.py`, `tests/test_dod.py`, `tests/test_acts.py`, `tests/test_stats.py`

**Interfaces:**
- Produces in `db.py`: `SCHEMA_V4` (decisione 1), `MIGRATIONS` fino a 4.
- Produces in `events.py`: tipi `finish_check`, `base_realigned` (decisione 25).
- Produces in `phases.py`:
  - `create_work(..., phase: str | None = None, cause: str = "start")`: `phase` deve stare in `SEQUENCES[level]` ed essere diversa da `closed`, altrimenti `ValueError`;
  - `set_base(conn, work, sha, *, cause: str, now, session=None) -> None` (evento `base_realigned` {from, to, cause});
  - `set_pr(conn, work, number: int | None, url: str | None, *, now) -> None`;
  - `set_finish(conn, work, sha: str | None, report: dict | None, *, now) -> None`;
  - `add_extra_cycles(conn, work, n: int, *, now) -> int` (restituisce il nuovo totale);
  - `set_review_unverified(conn, work, *, now) -> None`.
- Produces in `acts.py`: `approved_waivers(conn, work: int) -> set[str]` (stessa query di `Ctx.approved_waivers`, che delega); `has_approval(conn, work: int, object_: str) -> bool` (un atto `approve` di quell'oggetto del lavoro in qualunque stato; serve a `unverified-tests`).
- Produces in `intents.py` (azioni `pr`, `sync`, `force_push`; stati `requested`, `executed`, `authorized`, `used`):
  - `request(conn, *, work, action, key, data: dict, now) -> int` (idempotente sulla chiave: una riga esistente torna `requested` e aggiorna `data`);
  - `complete(conn, key, *, outcome: str, now) -> None` (`executed`);
  - `authorize_force(conn, work, *, reason: str, now) -> str` (chiave `force:<work>:<n>`, stato `authorized`);
  - `take_force(conn, work, *, now) -> str | None` (consuma il più recente `authorized`: `used`; `None` se non ce n'è);
  - `pending(conn, work, action: str) -> list[sqlite3.Row]`.
- Produces in `reviews.py` (tabelle `review_cycles`, `findings`; ogni funzione apre la sua transazione, eventi `review_cycle` e `finding` di 18.4):
  - `SEVERITY_ORDER = ("blocker", "major", "moderate", "minor")`, `CAP_COUNTED = 4`, `MAX_CYCLES = 8`, `CAP_REASON = "cicli di revisione esauriti"`;
  - `latest(conn, work) -> sqlite3.Row | None`; `count(conn, work) -> int`; `counted(conn, work) -> int`;
  - `open_cycle(conn, work, *, sha, patch_id, code, reviewers: list[str], now) -> int` (numero del ciclo, stadio `review`);
  - `add_report(conn, work, cycle, *, source: str, outcome: str, findings: list[dict], rejected: list[dict], blocking_rules: set[str], now) -> str`: identificativi `f-<ciclo>-<n>` in ordine di arrivo; `rejected` registrati con `verification = 'rejected'` e motivo «senza prova (8.6)»; `blocking` per la decisione 8; segna `reported[source]`; restituisce lo stadio dopo il riporto (`verify` quando tutti i `reviewers` hanno riportato);
  - `to_verify(conn, work, cycle, *, max_findings: int, now) -> list[sqlite3.Row]`: rilievi con `verification` nullo in ordine di gravità; oltre `max_findings` diventano `unverified` («oltre max_findings»);
  - `apply_verification(conn, work, cycle, results: list[dict], *, now) -> int` (rilievi ancora senza esito);
  - `effective_severity(row) -> str` (gravità dopo `downgraded:<g>`);
  - `blocking_open(conn, work, cycle=None) -> list[sqlite3.Row]` (confermati, `blocking = 1`, gravità effettiva `blocker`/`major`, non `dismissed`);
  - `close_cycle(conn, state, work, cycle, *, now, session=None) -> str`: esito e passaggi della decisione 6 (`set_phase`, `open_block` fuori transazione); restituisce `ok`, `needs_fix` o `needs_you`;
  - `set_decision(conn, work, finding_id, decision: str, *, now, session=None) -> None` (`downgraded:<g>` o `dismissed`, solo su un rilievo `confirmed`).
- Produces in `dod.py`: `receipt_verdict(..., allow_unverified: bool = False)`; `compute_dod(..., allow_unverified: bool = False)`; `_findings` per la decisione 15; `_specialists(conn, work, head_sha, expected: list[str]) -> (bool, str)` usata da `compute_dod(..., specialists=None)` quando `specialists` è una lista (L2).
- Produces in `stats.py`: `off_periods(conn, start: datetime, end: datetime) -> list[dict]` (`{"from", "to"}`, `to` nullo se `OFF` è ancora attivo).
- Produces in `tests/flowkit.py`: `FlowLab.register_plan(tasks: int = 1) -> None` (piano L1 di `tests/test_taskcmd.PLAN` registrato come farebbe l'hook), `FlowLab.commit(path, text, msg) -> str` (commit nel worktree con l'evento `commit`), `FlowLab.close_tasks() -> None` (ogni task `done` con verdetto `approved`), `JUNIT_TOML` e il file `tools/junit_fake.py` (scrive `reports/junit.xml` con i test di `tests/ids.txt`: righe `id ok` o `id fail`) per i test dei must-have.

- [ ] **Step 1: Test** `test_db.py::MigrationV4Test` (DB v3 con righe → colonne nuove, dati intatti, copia `*migrazione-4*`; DB nuovo → nessuna copia; `test_latest_version_is_4`).
- [ ] **Step 2: Test** `test_phases.py::CreateWorkPhaseTest` (`phase="execution", cause="adopt"` in L2 → fase `execution`, evento `phase_change` con causa `adopt`; `phase="closed"` → `ValueError`; `phase="spec_audit"` in L1 → `ValueError`) e `SetBaseTest::test_set_base_records_event`.
- [ ] **Step 3: Test** `test_intents.py`: `test_request_is_idempotent`, `test_force_taken_once` (`authorize_force` poi due `take_force` → chiave, poi `None`), `test_pending_lists_requested`.
- [ ] **Step 4: Test** `test_reviews.py`:
  - `test_open_and_report_moves_to_verify` (due revisori attesi: dopo il primo stadio `review`, dopo il secondo `verify`; id `f-1-1`, `f-1-2`);
  - `test_rejected_without_proof` (rilievo senza `rule` → `rejected`, motivo con «senza prova»; criterio 40);
  - `test_beyond_max_findings_unverified` (17 rilievi, `max_findings=15` → 15 da verificare, 2 `unverified`, prima i `blocker`);
  - `test_close_needs_fix_goes_execution` (un `major` confermato → `needs_fix`, fase `execution`, `counted == 1`; criterio 26);
  - `test_cycle_without_confirmed_not_counted` (solo `rejected` → `ok`, `counted == 0`; criterio 9);
  - `test_fourth_counted_cycle_opens_needs_you` (quattro cicli con un `major` confermato → al quarto blocco `needs_you` con `CAP_REASON`; criterio 9);
  - `test_reviewer_needs_you_opens_block`;
  - `test_non_blocking_rule_is_note` (rilievo `major` con `rule` `R-WEB-2` fuori da `blocking_rules` → confermato ma `ok`);
  - `test_downgrade_and_dismiss` (`set_decision` su un `rejected` → `ValueError`; `downgraded:minor` → `blocking_open` vuoto).
- [ ] **Step 5: Test** `test_dod.py`: `test_downgraded_to_major_still_blocks` (rinviato P1), `test_dismissed_passes`, `test_unverified_receipt_counts_with_allow`, `test_specialists_item`. `test_acts.py::test_approved_waivers_any_state`. `test_stats.py::test_off_periods_overlap`.
- [ ] **Step 6: Fallimento, implementazione, verifica** (`python3 -B -m unittest tests.test_db tests.test_phases tests.test_intents tests.test_reviews tests.test_dod tests.test_acts tests.test_stats`), `tests/run`.
- [ ] **Step 7: Commit** «tollgate P3b: migrazione 4, cicli di revisione e rilievi, intenti, DoD dei rilievi».

---

### Task 4: Violazioni dell'intero diff in core, `verify.run_gate`

`finish check` vive in `tollgate_flow` e non può importare `tollgate_checks`. Le regole di scope e test-guard si spostano in `tollgate_core`, e gli hook le chiamano da lì: una sola fonte.

**Files:**
- Create: `bin/tollgate_core/violations.py`
- Modify: `bin/tollgate_checks/_common.py` (`commit_violations`, `scope_exempt`, `locked_docs`, `is_docs_md`, `_is_registered_plan` delegano), `bin/tollgate_hooks/context.py` (`guard_config` delega), `bin/tollgate_core/verify.py`
- Test: `tests/test_violations.py`, `tests/test_verify.py`; restano verdi senza modifiche `tests/test_check_commit.py`, `tests/test_check_post_bash.py`, `tests/test_check_writes.py`, `tests/test_check_common.py`

**Interfaces:**
- Produces in `violations.py` (nessuna dipendenza da `Ctx`):
  - `guard_config(cfg: Config, files) -> GuardConfig`;
  - `locked_docs(work) -> set[str]`; `is_docs_md(rel) -> bool`;
  - `scope_exempt(cfg, work, rel: str, scope: set[str]) -> bool`;
  - `is_registered_plan(work, wt: Path, path: str, head_ref: str | None) -> bool`;
  - `waiver_file(work) -> WaiverFile | None`;
  - `diff_violations(cfg, conn, work, wt: Path, base_ref: str, head_ref: str | None, changes, *, components: Mapping[str, bool]) -> list[Violation]` (stessa logica di `_common.commit_violations`, violazioni non coperte da una deroga).
- Produces in `verify.py`:
  - `dod_commands(cfg, files) -> list[CommandSpec]`: i `dod` dei profili attivi che non sono già nel gate, con nome `profile:<p>:<c>`;
  - `GateRun(ok: bool, lines: list[str], sha: str | None, states: dict[str, str], junits: dict[str, Junit | None])`;
  - `run_gate(state, cwd, *, produced_by: str, extra: list[CommandSpec] = (), now=None, environ=None) -> GateRun`: come `run_verify` senza `--related`, con le ricevute `produced_by` dato e i JUnit restituiti; `run_verify` usa gli stessi passi interni.

- [ ] **Step 1: Test** `test_violations.py`:
  - `test_same_result_as_hook` (un commit che cancella un test e uno fuori scope: `diff_violations` dà le due violazioni, come `commit_violations` del hook sullo stesso commit);
  - `test_waiver_resolves` (deroga `scope` nel file del lavoro → la violazione sparisce);
  - `test_registered_plan_committed_is_exempt`;
  - `test_components_off` (`scope_check` e `test_guard` a `false` → nessuna violazione).
- [ ] **Step 2: Test** `test_verify.py::RunGateTest`: `test_run_gate_returns_junit_and_produced_by` (comando che scrive un JUnit con due test → `junits["verify"].ids_run` ha i due id, ricevuta con `produced_by == "finish"`); `test_dod_command_of_profile_runs` (profilo con `dod = ["lint"]` e `commands.lint = "true"` → ricevuta `profile:web:lint`).
- [ ] **Step 3: Fallimento, implementazione** (sposta il codice, poi le funzioni di `_common` e `Ctx` chiamano `violations`), **verifica** con la suite degli hook invariata e `tests/run`.
- [ ] **Step 4: Commit** «tollgate P3b: violazioni del diff in tollgate_core, run_gate per finish check».

---

### Task 5: Regole `[blocca]`, nomi dei profili, verdetti finali

**Files:**
- Modify: `bin/tollgate_core/config.py` (chiave `blocking_rules`, nomi convalidati), `bin/tollgate_analysis/profiles.py`, `bin/tollgate_analysis/verdicts.py`, `bin/tollgate_checks/task_verdict.py`
- Test: `tests/test_config.py`, `tests/test_profiles.py`, `tests/test_verdicts.py`, `tests/test_check_task_verdict.py`

**Interfaces:**
- Produces in `config.py`: `PROFILE_DEFAULTS["blocking_rules"] = []`; `AGENT_FORMS = {"agent": "implementer", "reviewer": "reviewer", "final_specialist": "final"}`; un nome che non combacia con `^[^:\s]+:<forma>-[a-z0-9-]+$` diventa `""` con l'avviso «profilo <p>: <chiave> «<valore>» non ha la forma <plugin>:<forma>-<area>: uso l'agente generico» (decisione 9).
- Produces in `profiles.py`: `blocking_rules(names, profiles) -> set[str]`; `final_specialists(names, profiles) -> list[str]` (valori non vuoti, in ordine di dichiarazione, senza doppioni).
- Produces in `verdicts.py`:
  - `is_blocking(finding: dict, blocking_rules: set[str]) -> bool` (decisione 8);
  - `parse_task_verdict(..., blocking_rules: set[str] | None = None)`: con `None` vale la regola di P3a (ogni `R-…` bloccante); con un insieme vale `is_blocking`. Con lo standard, un `approved` dichiarato con un rilievo scartato che poteva bloccare → non valido («rilievo bloccante senza file, riga o regola: riscrivilo», riga 108);
  - `FinalVerdict(valid: bool, problems: list[str], outcome: str | None, findings: list[dict], rejected: list[dict])` e `parse_final_verdict(text, *, sha: str, code: str) -> FinalVerdict` (18.5 revisore finale; `outcome` in `ok|needs_fix|needs_you`; ultimo JSON con `outcome`; rilievi senza prova in `rejected`, non scartati in silenzio);
  - `VerifierResults(valid, problems, results: list[dict])` e `parse_verifier_results(text, *, sha, code, ids: set[str]) -> VerifierResults` (`verification` in `confirmed|rejected|unverified`; id fuori da `ids` ignorati e contati nei problemi solo se nessuno è valido).
- Produces: `task_verdict` passa `blocking_rules` dei profili attivi sul diff del task.

- [ ] **Step 1: Test** `test_config.py::ProfileNamesTest`: `test_bad_reviewer_name_falls_back_with_warning` (`reviewer = "acme:code-review"` → `""` e avviso; m9); `test_good_names_kept`; `test_blocking_rules_type` (stringa al posto di lista → `ConfigError`).
- [ ] **Step 2: Test** `test_verdicts.py`: `test_non_blocking_rule_major_is_approved` (standard acceso, `major` su `R-WEB-2` non in `blocking_rules` → `approved`); `test_blocking_rule_major_is_changes`; `test_plan_step_rule_blocks`; `test_unknown_rule_blocks`; `test_approved_with_dropped_blocker_invalid` (riga 108); `test_final_verdict_matrix` (SHA diverso, codice diverso, `outcome` sconosciuto, JSON assente → non valido; un rilievo senza `line` → in `rejected`); `test_verifier_results` (id sconosciuto ignorato, `verification` sconosciuta → non valido).
- [ ] **Step 3: Test** `test_check_task_verdict.py::BlockingRulesTest::test_profile_rule_not_blocking` (profilo `web` con `blocking_rules = ["R-WEB-1"]`, verdetto `changes` con un solo `major` su `R-WEB-2` → registrato `approved`).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: regole [blocca], nomi degli agenti dei profili convalidati, verdetti della revisione finale».

---

### Task 6: `finish check`

**Files:**
- Create: `bin/tollgate_flow/finishcheck.py`, `bin/tollgate_analysis/mustcheck.py`, `bin/tollgate_analysis/approvals.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `finish` con `check`; `open-pr` arriva nel Task 9)
- Test: `tests/test_mustcheck.py`, `tests/test_approvals.py`, `tests/test_finishcheck.py`

**Interfaces:**
- Consumes: `verify.run_gate`, `verify.dod_commands`, `violations.diff_violations`, `dod.compute_dod`, `acts.has_approval`, `phases.set_finish`, `phases.set_phase(..., "review", "finish_check_green")`, `reviews.latest`; `prstate.detect` arriva nel Task 9 e si aggancia lì.
- Produces in `mustcheck.py`: `MustHaveResult(ok: bool, missing: list[str], failed: list[str], manual: list[str])` e `check(must_haves: list[MustHave], ids_run: set[str], ids_failed: set[str]) -> MustHaveResult` (un id assente o fallito rende falsa la voce; `manuale` va in `manual` e non la rende falsa).
- Produces in `approvals.py`: `parse_approval(text: str) -> dict | None` (intestazione YAML di 18.3 per `spec-approval` e `plan-approval`: `kind`, `path`, `sha`, `spec_sha`, `slices`, `adversarial`, `lens`, `act_id`, `approved_at`; righe `chiave: valore`, valori tra virgolette o nudi, `null`); `approval_paths(issue: int) -> tuple[str, str]`.
- Produces in `finishcheck.py`:
  - `CheckResult(code: int, lines: list[str], items: list[DodItem])`, codici `OK = 0`, `RED = 1`, `REFUSED = 2`;
  - `check(state, cwd, *, now=None, environ=None) -> CheckResult`.
- Comportamento di `check` (decisione 4):
  - lavoro da `sessions.work_for_path(cwd)`; fase `execution`, oppure `review` (sullo stesso `finish_sha` restituisce l'esito salvato, su un altro SHA ricalcola); altrimenti rifiuto con la fase;
  - `gitw.fetch` (senza rete: avviso, si prosegue);
  - L1 e L2: ogni task `done` con `verdict == "approved"`, altrimenti rifiuto con i numeri (criterio 41);
  - `run_gate(produced_by="finish", extra=dod_commands(...))`; poi `diff_violations` da `work_base_sha` a HEAD; poi i must-have del piano a `plan_sha` contro l'unione di `ids_run` e `ids_failed` dei JUnit;
  - L2: `approvals` vera se `spec-approval.md` e `plan-approval.md` esistono in HEAD con `sha` uguale al blob di spec e piano in HEAD;
  - `compute_dod(..., required_commands=<gate + dod>, external={"guard_scope", "must_have", "approvals"}, profile_items={"profile:<p>:<c>": <ricevuta green>}, allow_unverified=has_approval(..., "unverified-tests"))`; le voci `findings` e `specialists` qui sono `None` («dopo la revisione»), e non contano per il verde di `finish check`;
  - verde: `set_finish(sha, {"items": {...}, "manual": [...]})`, evento `finish_check` {sha, ok: true}, fase `review`; rosso: evento con `ok: false`, fase invariata (criterio 31);
  - righe: una per voce, `[sì]`, `[no]` o `[dopo la revisione]` con l'etichetta e il dettaglio; ultima riga `prossimo passo: …` (`review prepare` in L1/L2, `finish open-pr` in L0).
- CLI: `tollgate finish check`, uscita con `code`.

- [ ] **Step 1: Test** `test_mustcheck.py` (presente e verde; assente; fallito; `manuale`) e `test_approvals.py` (intestazione valida; senza `---` → `None`; `sha` tra virgolette).
- [ ] **Step 2: Test** `test_finishcheck.py` (con `FlowLab`, `register_plan`, `commit`, `close_tasks`, `JUNIT_TOML`):
  - `test_green_moves_to_review_and_prints_dod` (uscita 0, fase `review`, `finish_sha == HEAD`, una riga per voce di L1; criterio 41);
  - `test_red_stays_in_execution` (un test fallito nel JUnit → uscita 1, fase `execution`; criterio 31);
  - `test_task_not_done_refused` (criterio 41);
  - `test_must_have_test_missing_is_red` (`M1 — test: tests.test_x::test_a` e quel test assente dal JUnit → voce `must_have` falsa; criterio 42);
  - `test_out_of_scope_commit_is_red` (commit fuori scope senza deroga → `guard_scope` falsa);
  - `test_checkpoint_present_is_ignored` (checkpoint scritto con `status --checkpoint` → verde; vincolo (7));
  - `test_rerun_in_review_same_sha_is_idempotent` (criterio 28: interruzione dopo `finish check`);
  - `test_l0_without_tasks`.
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: finish check, must-have dal JUnit, file di approvazione».

---

### Task 7: `review prepare`

**Files:**
- Create: `bin/tollgate_flow/finalreview.py`
- Modify: `bin/tollgate_analysis/brief.py`, `bin/tollgate_core/cli.py` (sottocomando `review prepare`), `bin/tollgate_flow/taskcmd.py` (modello da `[review] models` nel riepilogo, decisione 21)
- Test: `tests/test_brief.py`, `tests/test_finalreview.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Consumes: `reviews.*`, `profiles.final_specialists`, `profiles.active_profiles`, `git.changes`, `brief.fence`.
- Produces in `brief.py`:
  - `FinalBrief(issue, cycle, sha, code, base, head, diff_path, plan_path, plan_sha, must_haves, scope, checklists: list[str], severity: dict, issue_file, role: str)` e `final_review_brief(b) -> str`: contiene `sha` e `code` alla lettera, standard del revisore e disaccordo istruito (8.6: cercare difetti; ogni rilievo con `file`, `line` e `rule` `R-…` o passo del piano), asserzioni indebolite e casi speciali (R3), la definizione delle gravità di `[severity]`, il JSON di 18.5 del revisore finale e il divieto di modificare file e di eseguire test che scrivono file;
  - `VerifierBrief(issue, cycle, sha, code, diff_path, findings: list[dict])` e `verifier_brief(b) -> str`: i rilievi in un recinto, il JSON di 18.5 del verificatore, «conferma o scarta ogni rilievo, senza discutere con il revisore; un rilievo senza prova si scarta».
- Produces in `finalreview.py`:
  - `Launch(agent_type: str, brief: Path, model: str | None)`;
  - `PrepareResult(lines: list[str], launches: list[Launch], stage: str)`;
  - `ReviewError(Exception)`;
  - `prepare(state, cwd, *, now=None) -> PrepareResult` (decisione 5).
- Comportamento di `prepare`:
  - fase `review`, `HEAD == finish_sha` (altrimenti «rilancia /tollgate:finish»); L0 → «in L0 non c'è revisione finale»; componente `final_review` spento → «revisione finale spenta», nessun lancio;
  - `review_unverified` → nessun lancio («revisione non verificata»);
  - ultimo ciclo aperto su HEAD: stadio `review` → i lanci dei revisori non ancora riportati, stesso codice; stadio `verify` → `to_verify` e il lancio del verificatore, oppure `close_cycle` se non resta nulla;
  - ultimo ciclo chiuso `ok` su HEAD o con lo stesso `patch-id` (`git diff <base> HEAD | git patch-id --stable`) → «revisione già superata (ciclo n): prossimo passo: finish open-pr»;
  - cicli già fatti `>= MAX_CYCLES` → rifiuto con «/tollgate:approve unverified-review»;
  - altrimenti `open_cycle` e i brief in `.tollgate-run/<N>/final-<ciclo>.md`, `final-<ciclo>-<area>.md` per ogni specialista (solo L2), diff in `final-<ciclo>.diff`, verificatore in `verify-<ciclo>.md`;
  - una riga `agente: <tipo> brief: <percorso>` per lancio, con ` model: <m>` da `[review] models`; ultima riga `prossimo passo: …`.
- CLI: `tollgate review prepare` stampa `lines`; `ReviewError` → uscita 1.

- [ ] **Step 1: Test** `test_brief.py`: `test_final_brief_has_sha_code_rules_and_format`; `test_verifier_brief_fences_findings` (testo del rilievo con ```` ``` ```` → recinto più lungo).
- [ ] **Step 2: Test** `test_finalreview.py`:
  - `test_new_cycle_l1_one_reviewer` (un lancio `tollgate:final-reviewer`, ciclo 1 `review`);
  - `test_l2_adds_final_specialists` (profilo `security` con `final_specialist = "probe:final-security"` attivo sul diff → due lanci; criterio 38);
  - `test_resume_open_cycle_keeps_code` (criterio 28);
  - `test_verify_stage_launches_verifier`;
  - `test_same_patch_id_after_rebase_no_new_cycle` (criterio 16);
  - `test_ninth_cycle_refused`;
  - `test_head_differs_from_finish_sha_refused`;
  - `test_models_override_in_launch_line`.
- [ ] **Step 3: Test** `test_taskcmd.py::test_models_override_in_summary` (`models = {"tollgate:implementer" = "sonnet"}` → `model: sonnet` nel riepilogo; giro 4 resta `inherit`).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: review prepare (cicli, specialisti in L2, verificatore), modelli per agente».

---

### Task 8: Verdetti della revisione finale a `SubagentStop`

**Files:**
- Create: `bin/tollgate_checks/final_review.py`
- Modify: `bin/tollgate_checks/_common.py` (`awaiting_final`), `bin/tollgate_checks/subagent_stop.py` (salta i revisori finali in attesa), `bin/tollgate_hooks/apply.py`, `bin/tollgate_flow/checkpoint.py` (`CAPS` con `reviews.CAP_REASON` → «cicli di revisione»)
- Test: `tests/test_check_final_review.py`, `tests/test_checkpoint.py`

**Interfaces:**
- Produces in `_common.py`: `awaiting_final(ctx, row) -> tuple[work, cycle, role] | None`: `role = "reviewer"` se `row["type"]` è tra i `reviewers` dell'ultimo ciclo del lavoro in stadio `review` e non ha ancora riportato; `role = "verifier"` se è `tollgate:finding-verifier` e lo stadio è `verify`. Accetta righe `running` o `interrupted` (decisione 7).
- Produces: modulo `final_review` (evento `subagent_stop`, ordine 15, componente `final_review`):
  - impronta cambiata con `readonly_check` acceso → `tampered_records` (criterio 9);
  - revisore: `parse_final_verdict` valido → `record("review_report", work, cycle, source, outcome, findings, rejected)` più `subagent_finish(done)`; non valido o JSON assente → `subagent_finish(done)` e blocco `needs_you` «verdetto del revisore finale non valido: …» (8.6, criterio 9);
  - verificatore: `parse_verifier_results` valido → `record("finding_verify", work, cycle, results)` più `subagent_finish(done)`; non valido → `needs_you`;
  - messaggio da `last_assistant_message` o da `subagents.report` (auto mode, criterio 9).
- Produces in `apply.py`: `review_report` chiama `reviews.add_report` con `blocking_rules` dei profili attivi e, se lo stadio diventa `verify` senza rilievi da verificare, `reviews.close_cycle`; `finding_verify` chiama `reviews.apply_verification` e, a zero rilievi senza esito, `close_cycle`. `apply.OPS` passa a 27 voci.

- [ ] **Step 1: Test** `test_check_final_review.py` (`hookkit.Lab` in `review` con un ciclo aperto):
  - `test_valid_verdict_registers_findings_and_moves_to_verify`;
  - `test_verdict_without_code_needs_you` (criterio 9);
  - `test_malformed_json_needs_you` (criterio 9);
  - `test_reviewer_that_changed_files_tampered` (criterio 9);
  - `test_handback_report_used_in_auto_mode` (criterio 9);
  - `test_stale_interrupted_reviewer_verdict_counts` (Review Focus 3);
  - `test_verifier_confirms_and_closes_cycle_needs_fix` (fase `execution`; criterio 26);
  - `test_finding_without_rule_rejected_not_sent_to_verifier` (criterio 40);
  - `test_specialist_findings_go_to_same_verifier` (L2; criterio 38);
  - `test_task_reviewer_path_unchanged` (un `tollgate:task-reviewer` in attesa resta di `task_verdict`).
- [ ] **Step 2: Test** `test_checkpoint.py::test_stopped_by_review_cycles` (`status` dice «tetto: cicli di revisione»).
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: verdetti del revisore finale e del verificatore, chiusura del ciclo».

---

### Task 9: `finish open-pr`, blocco JSON 18.1, merge e chiusura

**Files:**
- Create: `bin/tollgate_analysis/prblock.py`, `bin/tollgate_analysis/prbody.py`, `bin/tollgate_flow/openpr.py`, `bin/tollgate_flow/prstate.py`
- Modify: `bin/tollgate_flow/gh.py`, `bin/tollgate_flow/gitw.py`, `bin/tollgate_flow/finishcheck.py` (chiama `prstate.detect`), `bin/tollgate_core/cli.py` (`finish open-pr [--update]`), `tests/fakegh.py`
- Test: `tests/test_prblock.py`, `tests/test_prbody.py`, `tests/test_gh.py`, `tests/test_openpr.py`, `tests/test_prstate.py`

**Interfaces:**
- Produces in `prblock.py` (decisione 11): `FIELDS` (le chiavi di 18.1 nell'ordine della spec), `SCHEMA_VERSION = 1`, `build(facts: dict) -> dict` (`KeyError` se manca un campo di `FIELDS`), `render(block: dict) -> str`, `parse(text: str) -> dict | None`.
- Produces in `prbody.py`: `MAX_TEXT = 2000`; `neutralize(text: str, max_len: int = MAX_TEXT) -> str` (recinto più lungo di ogni sequenza di backtick, `@` seguito da `​`, troncato con «… (troncato)»); `render(*, issue: int, level: str, dod_lines: list[str], notes: list[dict], waivers: list[str], warnings: list[str], block: dict) -> str` (prima riga `Closes #<issue>`, poi le sezioni; le note sono i rilievi confermati non bloccanti, 10; il blocco per ultimo).
- Produces in `gitw.py`: `push_sha(repo, sha, branch, *, lease: str | None) -> None` (`git push origin <sha>:refs/heads/<ramo>`, con `--force-with-lease=refs/heads/<ramo>:<lease>` se `lease`; `GitWriteError` se fallisce); `remote_sha(repo, branch) -> str | None` (`ls-remote --heads origin`); `patch_id(repo, base, head) -> str | None`.
- Produces in `gh.py`: `pr_for_branch(state, repo, branch) -> dict | None` (`pr list --head <ramo> --state all --json number,state,url,headRefOid,mergedAt`, la PR con il numero più alto); `pr_view(state, repo, number) -> dict` (`pr view <n> --json number,state,url,mergedAt`); `pr_create(state, repo, *, branch, base, title, body_file) -> None`; `pr_edit(state, repo, number, *, body_file) -> None`; `pr_comments(state, repo, number) -> list[dict]`; `prs_for_branch_prefix` passa a `api --paginate repos/{owner}/{repo}/pulls?state=all&per_page=100 --jq '.[] | {number, headRefName: .head.ref, state, url: .html_url}'` (una riga JSON per PR, riga 56; G5 del Task 1).
- Produces in `fakegh.py`: le PR stanno in `data["prs"]` con `number`, `headRefName`, `state`, `url`, `headRefOid`, `mergedAt`, `body`, `comments`; `pr create` aggiunge una PR e riscrive il file dei dati; `pr edit` riscrive `body`; `pr view`; `api --paginate …/pulls` stampa una riga per PR; `data["fail"]` (`["pr create"]`…) fa uscire con 1 quel comando, per simulare i guasti.
- Produces in `prstate.py` (decisione 12): `Detection(kind: str | None, pr: dict | None)` con `kind` in `merged`, `closed`, `open`, `None`; `detect(state, conn, work, repo, *, now, session=None) -> Detection` (con `merged` chiude il lavoro ed emette `merge_detected`; senza rete o con `GhError` restituisce `None` e la CLI avvisa); `CLOSED_HINT` (le due strade).
- Produces in `openpr.py`:
  - `OpenResult(code: int, lines: list[str], url: str | None)`;
  - `open_pr(state, cwd, *, update: bool, now=None, argv=None, via_sync: str | None = None) -> OpenResult`. `via_sync` è l'id dell'atto `sync` già consumato da `sync`: sostituisce l'atto `finish` (decisione 17).
  - `facts(conn, state, work, cfg, wt, head) -> dict`: i campi di 18.1 (decisione 11), usati da `open_pr` e da `adopt`.
- Comportamento: decisione 10, nell'ordine scritto lì; i rifiuti escono tutti insieme con le righe `rifiuto: …` e codice 1; con PR chiusa senza merge, `CLOSED_HINT`. Le note e il testo dei rilievi passano da `prbody.neutralize`.
- CLI: `tollgate finish open-pr [--update]`, sessione con `cli_session(state, cwd, "finish", argv=…)` (serve per `approve pr`).

- [ ] **Step 1: Test** `test_prblock.py`: `test_build_has_all_fields_in_order`; `test_render_never_contains_comment_close` (stringa con `-->` in `plan` → nessun `-->` dentro il commento); `test_parse_last_block_and_garbage` (due blocchi → l'ultimo; JSON rotto → `None`).
- [ ] **Step 2: Test** `test_prbody.py`: `test_hostile_finding_text_neutralized_and_block_roundtrips` (Review Focus 2); `test_closes_line_first`.
- [ ] **Step 3: Test** `test_gh.py` (con `fakegh`): `test_pr_for_branch_latest`; `test_prs_for_branch_prefix_paginated` (250 PR nei dati → trova la più vecchia); `test_pr_create_and_edit_roundtrip`.
- [ ] **Step 4: Test** `test_openpr.py` (`FlowLab` con lavoro L1 in `review`, ciclo `ok` su HEAD):
  - `test_refused_without_finish_or_approve_pr` (criterio 12);
  - `test_finish_act_after_long_review_opens_pr` (atto `finish` registrato 30 minuti prima → PR creata, fase `pr_open`, `pr_number`; criterio 12);
  - `test_commit_after_finish_invalidates` (criterio 12);
  - `test_finish_of_other_work_refused` (criterio 12);
  - `test_finish_survives_clear` (atto `finish` di una sessione, `open-pr` da un'altra sessione dello stesso lavoro → PR; criterio 12);
  - `test_interrupted_after_push_no_duplicate_pr` (`fail: ["pr create"]`, poi senza guasto → una sola PR; poi PR già creata e intento ancora `requested` → `pr edit`, non una seconda; criterio 12, Review Focus 1);
  - `test_refusals_collected` (deroga `test` in attesa, effetto `requested`, rilievo senza esito → tre righe `rifiuto:`; criterio 9);
  - `test_task_not_done_refused` (task rimesso `review` nel DB → rifiuto dalla DoD; criterio 41);
  - `test_dod_component_off_does_not_block` (criterio 18, `definition_of_done`);
  - `test_final_review_off_skips_cycle` (criterio 18, `final_review`);
  - `test_non_fast_forward_without_intent_refused` (ramo remoto avanzato a mano → rifiuto senza push; criterio 16);
  - `test_block_in_body_parses` (`prblock.parse(body)` ha `issue`, `head_sha`, `plan_sha`, `verdict.cycles`).
- [ ] **Step 5: Test** `test_prstate.py`: `test_merged_closes_work`; `test_closed_unmerged_returns_closed`; `test_offline_is_none`; `test_finish_check_refuses_on_closed_pr`.
- [ ] **Step 6: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: finish open-pr con il blocco JSON 18.1, rilevamento di merge e chiusura».

---

### Task 10: Voci nuove di `act apply`

**Files:**
- Modify: `bin/tollgate_flow/actapply.py`, `bin/tollgate_flow/taskcmd.py` (`MAX_FIX_ROUNDS + extra_fix_rounds`), `bin/tollgate_core/tasks.py` (`add_extra_rounds`)
- Test: `tests/test_actapply.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Produces in `tasks.py`: `add_extra_rounds(conn, work, number, n: int) -> int` (tetto 8 giri in tutto: `ValueError` oltre).
- Produces in `actapply.APPLIERS` (decisioni 13 e 14): `("approve", "finding")`, `("approve", "rounds")`, `("approve", "unverified-review")`, `("approve", "rebase")`. `_resolve` sul blocco con `reviews.CAP_REASON` aggiunge un ciclo (`phases.add_extra_cycles(…, 1)`).
- Produces: `approve finding` vuole `<id> <gravità|dismiss> <motivo>`; gravità in `blocker|major|moderate|minor`; motivo obbligatorio; id di un rilievo `confirmed` del lavoro.

- [ ] **Step 1: Test** `test_actapply.py`:
  - `test_approve_rounds_one_more_cycle` (quarto ciclo contato → blocco; `approve rounds 1` → blocco chiuso, `extra_review_cycles == 1`, il quinto ciclo si apre; criterio 9);
  - `test_approve_rounds_over_eight_refused`;
  - `test_approve_rounds_on_fix_rounds_cap` (blocco «giri di correzione esauriti sul task 1» → `approve rounds 2` → `task start 1 --fix` ammesso al sesto giro; m12);
  - `test_resolve_on_cycles_cap_grants_one`;
  - `test_approve_finding_dismiss_turns_cycle_ok` (ultimo ciclo `needs_fix` per un solo `major` → `dismiss` → esito `ok`);
  - `test_approve_finding_needs_reason_and_confirmed`;
  - `test_unverified_review_only_after_eight`;
  - `test_approve_rebase_realigns_base_and_authorizes_force` (blocco del `sync` → base = `merge-base`, fase `execution`, un intento `force_push`; criterio 16).
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: act apply per finding, rounds, unverified-review e rebase».

---

### Task 11: `sync`

**Files:**
- Create: `bin/tollgate_flow/sync.py`
- Modify: `bin/tollgate_flow/gitw.py` (`merge_ff_only`, `rebase`, `rebase_abort`, `merge_base`, `is_ancestor`), `bin/tollgate_flow/start.py` (ripresa: `sync.complete_interrupted`), `bin/tollgate_core/cli.py` (`sync`)
- Test: `tests/test_sync.py`, `tests/test_start.py`

**Interfaces:**
- Consumes: `acts.find_usable`/`consume` (`type_="sync"`), `intents.request/complete/authorize_force`, `phases.set_base`, `phases.set_phase(..., "execution", "sync")`, `finishcheck.check`, `openpr.open_pr(..., via_sync=<atto>)`, `prstate.detect`.
- Produces in `gitw.py`: `merge_ff_only(wt, ref) -> bool`; `rebase(wt, onto) -> bool` (falso con conflitto, rebase lasciato in corso); `rebase_abort(wt) -> None`; `merge_base(repo, a, b) -> str | None`; `is_ancestor(repo, a, b) -> bool`.
- Produces in `sync.py`:
  - `SyncResult(code: int, lines: list[str])`, codici `OK = 0`, `REFUSED = 1`, `BLOCKED = 2`, `REVIEW_NEEDED = 3`;
  - `sync(state, cwd, *, now=None, argv=None, environ=None) -> SyncResult` (decisione 17);
  - `complete_interrupted(conn, state, work, wt: Path, *, now, session=None) -> str | None`: con un intento `sync` `requested`, nessun rebase in corso e la punta di arrivo antenata di HEAD, completa base, commit ed eventi e restituisce la riga d'avviso; altrimenti `None`.
- CLI: `tollgate sync`, sessione con `cli_session(state, cwd, "sync", argv=…)`.

- [ ] **Step 1: Test** `test_sync.py` (`FlowLab` con lavoro in `pr_open`, PR nel finto `gh`, il predefinito avanzato con un commit che non tocca i file del lavoro):
  - `test_refused_without_sync_act` (criterio 16);
  - `test_rebase_realigns_base_and_updates_pr` (ramo rifatto sulla punta, `work_base_sha` = punta, eventi `commit` per gli SHA nuovi, `pr_updated`, push con lease; criterio 16);
  - `test_same_patch_id_no_cycle_consumed` (numero di cicli invariato; criterio 16);
  - `test_remote_merge_then_rebase` (un commit «Update branch» su `origin/<ramo>` → integrato con `--ff-only`, poi rebase; Review Focus 4; criterio 16);
  - `test_conflict_aborts_and_blocks` (conflitto → nessun rebase in corso, base e fase invariate, `needs_you` con le due strade; criterio 16);
  - `test_post_bash_ignores_rewritten_commits` (dopo `sync`, `PostToolUse Bash` sul worktree non apre blocchi);
  - `test_different_patch_id_asks_new_review` (codice 3, nessun push).
- [ ] **Step 2: Test** `test_start.py::ResumeTest::test_interrupted_sync_completed_by_start` (intento `sync` `requested` e rebase finito → `start` completa base ed eventi; Review Focus 4) e `test_interrupted_sync_with_rebase_in_progress_proposes_abort`.
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: sync (integrazione, rebase, base riallineata, PR aggiornata)».

---

### Task 12: `adopt`

**Files:**
- Create: `bin/tollgate_flow/adopt.py`
- Modify: `bin/tollgate_core/cli.py` (`adopt N`)
- Test: `tests/test_adopt.py`

**Interfaces:**
- Consumes: `acts.find_usable`/`consume` (`type_="adopt"`, `target=str(N)`, `work=None`), `phases.create_work(..., phase=, cause="adopt")`, `scope.register_plan(..., advance=False)`, `plan.check_plan`, `approvals.parse_approval`, `prblock.parse`, `gh.pr_for_branch`, `gh.issue`, `level.diff_level`, `labels_level`, `gitw.create_branch`, `gitw.worktree_add`, `git.worktrees`, `active.register`, `sessions.mark_bound`, `phases.set_level_cap`.
- Produces in `adopt.py`: `AdoptResult(code: int, lines: list[str], worktree: Path | None, work: int | None)` e `adopt(state, cwd, issue: int, *, now=None, argv=None) -> AdoptResult` (decisione 18). Ultima riga `prossimo passo: EnterWorktree <percorso>`.
- CLI: `tollgate adopt N`.

- [ ] **Step 1: Test** `test_adopt.py`:
  - `test_hooks_deny_on_orphan_branch_then_adopt` (DB cancellato, Edit su un file di codice nel worktree `tg/7-*` → `deny` con `/tollgate:adopt #7`; poi `adopt 7` → riga, fase, sessione legata; criteri 17 e 1);
  - `test_start_refusal_then_adopt` (ramo remoto `tg/7-x` → `start 7` rifiuta con l'adozione; `adopt 7` riesce; criterio 1);
  - `test_l2_with_plan_approval_stays_execution` (criterio 17);
  - `test_l2_without_plan_approval_goes_approval` (criterio 17);
  - `test_approved_waivers_back_pending` (deroga `test` nel file del ramo → `waivers.status` la dà `pending`; criterio 17);
  - `test_l1_without_plan_goes_plan`; `test_l1_with_plan_registers_scope_and_pending_tasks`;
  - `test_open_pr_gives_pr_open_and_cap_from_block` (corpo della PR con `level_cap: "L1"` → tetto L1);
  - `test_branch_in_existing_worktree_reused` (riga 74, Review Focus 5);
  - `test_remote_only_branch` (Review Focus 5);
  - `test_refused_with_active_work_or_merged_pr_or_two_branches`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: adopt (ricostruzione dal ramo, fase dalle prove, worktree riusato)».

---

### Task 13: `abandon`, `cleanup`, merge e chiusura in `start`

**Files:**
- Create: `bin/tollgate_flow/closing.py`
- Modify: `bin/tollgate_flow/start.py` (ripresa: `prstate.detect`, PR chiusa senza merge → conferma), `bin/tollgate_core/cli.py` (`abandon N`, `cleanup [--confirm] [--orphans]`)
- Test: `tests/test_closing.py`, `tests/test_start.py`

**Interfaces:**
- Produces in `closing.py`:
  - `abandon(state, cwd, issue: int, *, now=None, argv=None) -> tuple[int, list[str]]` (decisione 20);
  - `CleanupItem(kind: str, issue: int | None, branch: str, sha: str | None, worktree: Path | None, dirty: bool)` con `kind` in `closed`, `orphan`;
  - `cleanup(state, cwd, *, confirm: bool, orphans: bool, now=None, argv=None) -> tuple[int, list[str]]` (decisione 19: senza `confirm` codice 3 e l'elenco, atto non consumato).
- Produces in `start.py`: in ripresa, dopo il fetch, `prstate.detect`; `merged` → riga «lavoro #N chiuso: la PR è stata unita» e codice 0 senza `EnterWorktree`; `closed` → conferma (codice 3) con `CLOSED_HINT`; con `--confirm` `set_pr(None, None)`.

- [ ] **Step 1: Test** `test_closing.py`: `test_abandon_closes_and_keeps_branch`; `test_abandon_needs_act_and_matching_issue`; `test_cleanup_lists_then_deletes_with_confirm` (primo giro codice 3 e atto ancora `pending`; secondo giro ramo e worktree tolti); `test_cleanup_skips_dirty_worktree`; `test_cleanup_orphans_only_with_flag` (riga 55).
- [ ] **Step 2: Test** `test_start.py::ResumeTest`: `test_merged_pr_closes_work` (criterio 1, 6.5); `test_closed_pr_asks_and_confirm_clears_pr`.
- [ ] **Step 3: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: abandon, cleanup, merge e chiusura rilevati alla ripresa».

---

### Task 14: `task start --from-findings` e `--from-gate`

**Files:**
- Create: `bin/tollgate_flow/fixtask.py`
- Modify: `bin/tollgate_analysis/brief.py` (`findings_task_text`, `gate_task_text`), `bin/tollgate_flow/taskcmd.py` (`review_prepare` e `task_done` accettano i task `kind = "fix"` senza testo nel piano), `bin/tollgate_core/cli.py` (`task start --from-findings C`, `task start --from-gate`, esclusivi con `K`)
- Test: `tests/test_fixtask.py`

**Interfaces:**
- Consumes: `reviews.blocking_open(conn, work, cycle)`, `tasks.add_task(kind="fix", source=…)`, `tasks.assign`, `profiles.task_routing`, `brief.ImplBrief`, `gh.pr_comments`.
- Produces in `brief.py`: `findings_task_text(cycle: int, findings: list[dict], scope: list[str]) -> str` (i rilievi in un recinto; un file fuori scope è indicato come «serve una deroga»); `gate_task_text(sha: str, comment: str) -> str` (commento recintato, marcato come dato).
- Produces in `fixtask.py`: `GATE_MARKER = "<!-- tollgate-verdict"`; `from_findings(state, cwd, cycle: int, *, claude_dir, now=None) -> tuple[Path, str]`; `from_gate(state, cwd, *, claude_dir, now=None) -> tuple[Path, str]`. Stesso riepilogo di `task start` (tipo, `name`, `launch`, revisore). Errore `taskcmd.TaskError`. Decisione 16.

- [ ] **Step 1: Test** `test_fixtask.py`:
  - `test_from_findings_creates_fix_task_without_touching_plan` (ciclo `needs_fix` → task 2 `kind = "fix"`, `source = "cycle:1"`, brief con i rilievi, `plan_sha` e file del piano invariati; criteri 26 e 37);
  - `test_from_findings_twice_refused`;
  - `test_from_findings_ok_cycle_refused`;
  - `test_fix_task_review_and_done` (il task di correzione passa da `review-prepare` e `task done` come un task del piano);
  - `test_from_gate_reads_marked_comment_as_data` (due commenti, l'ultimo con il marcatore e ```` ``` ```` → brief con il recinto più lungo; `source = "gate:<sha>"`);
  - `test_from_gate_without_pr_refused`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: task di correzione dai rilievi e dal gate».

---

### Task 15: Prossimo passo nelle fasi di chiusura

**Files:**
- Modify: `bin/tollgate_flow/checkpoint.py`
- Test: `tests/test_checkpoint.py`

**Interfaces:**
- Produces: `next_step(conn, work) -> str` copre anche:
  - `review` con un task revisionato: «revisione preparata, lancia il revisore <tipo> con <brief>» se `review_sha` e `review_code` ci sono e il verdetto manca; «task review-prepare k» solo se la revisione non è preparata (riga 133);
  - blocco «giri di correzione esauriti sul task k»: «serve una decisione dell'utente: /tollgate:approve rounds <n>, /tollgate:resolve <id> o /tollgate:abandon #N» (m12);
  - tutti i task `done` in `execution`: `/tollgate:finish`; fase `review`: secondo lo stadio dell'ultimo ciclo (`review prepare`, lancio del verificatore, `finish open-pr`); fase `pr_open`: «PR #n aperta: attendi il gate; per correggere /tollgate:start #N --reopen-execution; se il predefinito è avanzato /tollgate:sync»;
  - ciclo `needs_fix`: `task start --from-findings <ciclo>`.

- [ ] **Step 1: Test** `test_checkpoint.py`: `test_prepared_review_not_reprepared` (riga 133); `test_fix_rounds_cap_asks_user` (m12); `test_review_phase_steps` (tre stadi); `test_pr_open_step`; `test_needs_fix_points_to_from_findings`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3b: prossimo passo per revisione finale, PR e tetti».

---

### Task 16: Agenti e skill della chiusura

**Files:**
- Create: `agents/final-reviewer.md`, `agents/finding-verifier.md`
- Create: `skills/finish/SKILL.md`, `skills/sync/SKILL.md`, `skills/adopt/SKILL.md`, `skills/abandon/SKILL.md`, `skills/cleanup/SKILL.md`
- Modify: `skills/approve/SKILL.md`, `skills/execute/SKILL.md`, `skills/start/SKILL.md`, `skills/resolve/SKILL.md`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: le uscite dei Task 6-15 (righe `agente: … brief: …`, `prossimo passo: …`, codici d'uscita).
- Produces: i nomi `tollgate:final-reviewer` e `tollgate:finding-verifier`, già in `readonly_agents`.

Contenuti (testo in italiano, identificatori in inglese, programma sempre `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` con il ripiego della riga «programma», come le skill di P3a):

**`agents/final-reviewer.md`**: frontmatter `name: final-reviewer`, `tools: Read, Grep, Glob, Bash`, `model: inherit`. Corpo derivato da `superpowers/skills/requesting-code-review/code-reviewer.md` di Superpowers 7.0.0, con la riga di attribuzione MIT come gli agenti di P3a: leggere il brief; sola lettura, mai subagenti, nessun test che scrive file (m13); cercare difetti, non confermare (8.6); confronto con piano, must-have e scope; asserzioni indebolite e casi speciali (R3); ogni rilievo con `file`, `line`, `rule`; chiusura con **un solo** JSON di 18.5 del revisore finale con `sha` e `code` del brief.

**`agents/finding-verifier.md`**: `name: finding-verifier`, `tools: Read, Grep, Glob, Bash`, `model: sonnet`. Testo proprio: per ogni rilievo del brief controlla la prova su file e riga, conferma o scarta, senza discutere con il revisore; un rilievo senza prova si scarta; chiusura con un solo JSON di 18.5 del verificatore.

**`skills/finish/SKILL.md`** (anche il modello): l'atto `finish` lo registra l'hook solo quando l'utente digita `/tollgate:finish`; poi, dal worktree:
1. `finish check`: uscita 1 → mostra le voci `[no]` e fermati; uscita 0 → avanti;
2. L1 e L2: `review prepare`, lancia **in primo piano** ogni riga `agente:` (le righe dello stesso stadio insieme, nello stesso messaggio), poi di nuovo `review prepare` finché la riga «prossimo passo» non è `finish open-pr`; con un ciclo `needs_fix` la fase torna `execution`: `task start --from-findings <ciclo>`, poi il ciclo di `/tollgate:execute`, poi chiedi all'utente di digitare di nuovo `/tollgate:finish`; con un blocco: fermati e indica `/tollgate:resolve`, `/tollgate:approve finding` o `/tollgate:approve rounds`;
3. `finish open-pr`: mostra l'URL; i rifiuti si riportano così come sono. Mai `git push` né `gh pr create` da Bash.

**`skills/sync/SKILL.md`**, **`adopt`**, **`abandon`**, **`cleanup`** (`disable-model-invocation: true`): l'atto è già registrato; lanciano il sottocomando e riferiscono. `adopt`: dal checkout principale, poi `EnterWorktree` come `start`. `cleanup`: prima senza `--confirm`, mostra l'elenco, chiede all'utente; solo con il suo sì rilancia con `--confirm` entro i 10 minuti dell'atto. `sync`: con codice 2 (conflitto) mostra le due strade; con 3 indica `/tollgate:finish`.

**Aggiornamenti:** `approve` (oggetti `finding`, `rounds`, `unverified-review`, `rebase` → `act apply`; `unverified-tests`, `waiver`, `effect` valgono dal DB; `pr` lo usa `finish open-pr`; `spec` e `plan` restano a P3c); `execute` (fine dei task: «di' all'utente di digitare `/tollgate:finish`»; task `fix` come gli altri); `start` (`/tollgate:adopt #N` esiste; PR chiusa senza merge: le due strade); `resolve` (al tetto dei cicli concede un ciclo).

- [ ] **Step 1: Test** `test_manifest.py`:
  - `test_final_agents_frontmatter` (strumenti senza `Edit`/`Write`; `final-reviewer` `inherit` con la riga di attribuzione; `finding-verifier` `sonnet`);
  - `test_closing_skills_user_only` (`sync`, `adopt`, `abandon`, `cleanup` con `disable-model-invocation: true`; `finish` senza);
  - `test_skills_use_program_command_form` (ogni skill che nomina `bin/tollgate` lo fa nella forma `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`; vincolo (2));
  - `test_finish_skill_never_pushes` (contiene «mai `git push`»);
  - `test_final_verdict_fields_in_agent_text` (i campi di 18.5 del revisore finale e del verificatore compaiono negli agenti).
- [ ] **Step 2: Fallimento, scrittura dei file, `tests/run`**; se `claude` è disponibile `claude plugin validate --strict .` deve riuscire (esito nel report).
- [ ] **Step 3: Commit** «tollgate P3b: agenti final-reviewer e finding-verifier, skill della chiusura».

---

### Task 17: Prova reale del flusso finish → open-pr con `claude -p`

Una sola esecuzione reale del percorso skill → CLI → hook → agenti per la chiusura, su un repo locale. Chiude i rischi che i test non vedono: frontmatter degli agenti nuovi, righe di lancio lette dal modello, atto `finish`, verdetti finali e del verificatore, PR nel finto `gh`.

**Files:**
- Create: `spikes/run-p3b-flow.sh`, `docs/verifiche/2026-10-19-p3b-prova-flusso.md`

**Regole di cautela (vanno nel brief):**
- tutto in `/tmp/tollgate-p3b/flow`, sul modello di `spikes/run-p3a-flow.sh`;
- `TOLLGATE_STATE=/tmp/tollgate-p3b/flow/state` con la sentinella; `TOLLGATE_GH=<worktree>/tests/fakegh.py` con dati che dichiarano l'issue 1 aperta, stato del predefinito `success` e nessuna PR;
- `claude -p --plugin-dir <worktree del ramo> --model sonnet`; mai `claude plugin install`; nessun comando scrive sotto `~/.claude`;
- **nessun push in rete** (decisione 24): `remote.origin.url = https://github.com/prova/flow.git` con `url.<repo nudo locale>.insteadOf`; prima di ogni passo lo script controlla che `git remote get-url --push origin` sia il repo nudo in `/tmp/tollgate-p3b/flow/origin.git`, altrimenti si ferma;
- mai `pkill`, `killall` o `kill` per pattern.

- [ ] **Step 1: Script** `spikes/run-p3b-flow.sh` (`prepara|passo1|passo2|passo3|tutto`). Prepara il repo L1 di P3a con un piano di un task già **eseguito**: lo script porta il lavoro fino a «task 1 `done`» con i comandi della CLI e gli eventi dell'hook, come `run-p3a-flow.sh` (oppure ripete i passi di P3a con `claude -p`). Poi, con `--continue`:
  1. `/tollgate:finish` (atto, `finish check`, `review prepare`, revisore finale, verificatore);
  2. se serve, «continua con /tollgate:finish» fino a `finish open-pr`;
  3. `bin/tollgate status` e `bin/tollgate events`.

  Registra stdout, `hooks.log`, eventi e il file dei dati del finto `gh`.
- [ ] **Step 2: Eseguire.** Esito atteso: un ciclo di revisione chiuso `ok` (o `needs_fix` seguito da un task di correzione e da un secondo ciclo), una PR nel finto `gh` con `Closes #1` e il blocco JSON leggibile con `prblock.parse`, fase `pr_open`, ramo spinto sul repo nudo allo SHA di HEAD. Un passo che si ferma si annota con l'evento o il messaggio. Si ripete una volta dopo una correzione **solo** se la causa è un difetto di questo piano, con un commit e un test che lo copre. Un esito non ottenuto si scrive «non riuscito», con la causa. Non si dichiara riuscito ciò che non lo è.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-19-p3b-prova-flusso.md`: versione di `claude`, passi, esito per passo, veti, token (`bin/tollgate stats`), difetti e correzioni, ciò che resta non esercitato (`sync`, `adopt`, L2).
- [ ] **Step 4: Commit** «tollgate P3b: prova reale del flusso di chiusura con claude -p».

---

### Task 18: Criteri, revisione 23 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p3b.py`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 23), `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «Prove dei criteri di P3b» nel piano principale; i contratti reali P3b → P3c e P4, compreso il blocco 18.1.

- [ ] **Step 1: Test dal programma vero** (`test_criteria_p3b.py`, `FlowLab` più `hooks/run` reale come in `test_criteria_p3a.py`):
  - `test_finish_to_pr_end_to_end` (criteri 9, 12, 40, 41): `UserPromptExpansion` di `/tollgate:finish` attraverso `hooks/run` → atto; `finish check` → 0; `review prepare`; `SubagentStart`/`SubagentStop` del revisore finale con un verdetto con un rilievo senza `rule`; `review prepare` → verificatore; `SubagentStop` del verificatore; `review prepare` → «finish open-pr»; `finish open-pr` (segnale scritto dal `PreToolUse Bash` vero) → PR nel finto `gh`, fase `pr_open`, blocco JSON con `verdict.outcome == "ok"`;
  - `test_needs_fix_then_from_findings_consumes_cycle` (criteri 26 e 37);
  - `test_sync_after_default_advanced` (criterio 16);
  - `test_adopt_after_db_lost` (criterio 17).
- [ ] **Step 2: Matrice.** Nel piano principale la tabella «Prove dei criteri di P3b» (formato `file::Classe.metodo`) per 1 (adozione eseguita), 9, 12, 16, 17 (`adopt`), 18 (`final_review`, `definition_of_done`), 26, 28 (interruzione dopo `finish check`), 31 (`finish check` rosso), 37 (`--from-findings`), 38 (`final_specialist`), 40 (verificatore), 41, 42 (DoD), con «Resta a» per P3c (41 seconda frase, decisione 26; 37 `plan_sha` di `approve plan`) e P4 (42 nel gate, 18 `definition_of_done` nel gate). Un criterio senza test è un buco: il test si aggiunge nel modulo che possiede il codice.
- [ ] **Step 3: Revisione 23 della spec**: le decisioni 1-26 nelle sezioni 3.1 (sottocomandi nuovi, segnale con `argv` consumato), 6.4 (`finish check`, revisione, `open-pr`), 6.5 (`sync`, merge e chiusura), 8.4 (atti applicabili, `approve rounds` sui giri di correzione, `abandon` senza lavoro), 8.6 (`[blocca]` con `blocking_rules`, nomi dei profili), 8.7 (DoD dei rilievi e `unverified-tests`), 10 (stadi del ciclo, codice per ciclo, tetti), 11.4 (`blocking_rules`), 12.2 (migrazione 4), 12.4 (`adopt`, `cleanup`), 15 (criterio 41 diviso), 16 (esiti G1-G5 del Task 1 e della prova reale), 18.1 (contratto di `prblock`, marcatore `<!-- tollgate-verdict` per P4), 18.4 (eventi nuovi), 20 (riga 23).
- [ ] **Step 4: Piano principale**: «Stato» (P3b chiuso sul ramo, merge in attesa dell'OK dell'utente, numero di test); sezione 3 con i moduli reali e i contratti P3b → P3c/P4 (`prblock.FIELDS/parse`, `reviews`, `intents`, `violations`, `finishcheck.check` come interfaccia che P4 sostituisce, `GATE_MARKER`), i vincoli per P3c e P4 emersi qui e i rinviati della revisione finale.
- [ ] **Step 5: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi, nessun «unclosed database».

```bash
git add tests/test_criteria_p3b.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git commit -m "tollgate P3b: prove dei criteri, spec rev 23, piano principale"
```

---

## Copertura: criteri, vincoli e rinviati → task

| Voce | Task |
|---|---|
| Criterio 1 (adozione proposta da `start` ed eseguita) | 12, 18 |
| Criterio 9 Revisori | 3, 8, 9, 10, 18 |
| Criterio 12 PR | 9, 18 |
| Criterio 16 Sync | 7, 9, 10, 11, 18 |
| Criterio 17 Adozione (`adopt`) | 12, 18 |
| Criterio 18 Componenti (`final_review`, `definition_of_done`) | 9 |
| Criterio 26 Da correggere | 3, 8, 14, 18 |
| Criterio 28 Ripresa (interruzione dopo `finish check`) | 6, 7 |
| Criterio 31 `finish check` rosso | 6 |
| Criterio 37 `--from-findings` | 14, 18 |
| Criterio 38 `final_specialist` in L2 | 7, 8 |
| Criterio 40 Revisione (verificatore) | 3, 8, 18 |
| Criterio 41 DoD (prima frase; seconda a P3c) | 6, 9, 18 |
| Criterio 42 Must-have nella DoD (gate a P4) | 6 |
| Blocco JSON 18.1 per P4 | 9 (decisione 11), 18 |
| Vincoli (1)-(9) di P3a per P3b | vedi «Rilievi ripresi qui» |
| m9, m11, m12, m13 | 5; 2; 10 e 15; 2 |
| Righe 55, 56, 74, 102, 108, 133 | 12 e 13; 9; 12; 2; 5; 15 |
| Messaggio breve di `cli_calls` | 2 |
| `dod._findings`, `abandon` della sessione, commit estranei del `sync` | 3; 2; 11 |
