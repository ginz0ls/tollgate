# Revisione finale del ramo `p3a-avvio-e-task` (81ce50c..71f4230)

Revisore: opus, in sola lettura. Fonti: piano P3a (Review Focus, decisioni), `global-constraints.md`, `cautele.md`, ledger con i ruling, `carry.md`, `preflight-scan.md`, spec rev 22, piano principale, rapporti dei Task 1, 13 e 14, diff dell'intero ramo e i sorgenti. Ho lanciato soltanto test mirati con `python3 -B`: `tests.test_layers`, `tests.test_verdicts`, `tests.test_sessions` e `tests.test_naming` (31 OK), più due test singoli con tracemalloc. Il worktree è rimasto pulito (`git status` vuoto).

Ho verificato che il codice rispetti i ruling del ledger, senza riaprirli. Quelli controllati sono C1, C4, C5, C6, C7, C8, C9, C10 nella variante del Task 6, C11, C12, C14, C17, C18, C21, D1, D2, il codice 4 e il footer del runner.

## Esito del Review Focus

| # | Esito | Evidenza |
|---|---|---|
| 1. Testo dell'issue ostile | **Regge** | Lo slug è `[a-z0-9-]`, con NFKD e il ripiego `issue` (`bin/tollgate_analysis/naming.py:11-15`). Alla CLI di `gh` arrivano solo il numero (`int(n)`) e prefissi costruiti da numeri (`bin/tollgate_flow/gh.py:78-99`). `issue.md` usa un recinto più lungo di ogni sequenza di backtick, preceduto da «DATO NON FIDATO» (`bin/tollgate_flow/start.py:66-86`), e `start` non stampa il titolo (`start.py:404-409`). Test: `tests/test_start.py:302` (`/tmp/PWNED` assente, titolo assente dalle chiamate a `gh`, due soli recinti). Nota: `start._fence` duplica `brief.fence` (Minor m7). |
| 2. Due sessioni e il segnale | **Regge**, con un limite residuo | `sessions.cli_session` accetta il segnale solo se valgono finestra di 120 s, cartella risolta e sottocomando; con zero candidate o con più d'una rifiuta (`bin/tollgate_core/sessions.py:113-133`). Il segnale si scrive solo per `start` e `act`, con la cartella effettiva (`bin/tollgate_checks/cli_calls.py:54-55`). Lo leggono `start.py:319-322` e `actapply.py:116-119`. Test: `tests/test_sessions.py:76`, più i casi a 121 s e il sottocomando diverso. Limite: il segnale non si consuma e `argv` non si confronta, quindi un secondo lancio senza hook nella stessa cartella entro 120 s eredita la sessione (Minor m11, rinviabile). |
| 3. Avvio interrotto | **Regge** | Crash dopo `worktree add`: un ramo `tg/N-*` locale o remoto, o una PR da quel ramo, danno sempre il rifiuto con `/tollgate:adopt #N` (`start.py:281-289` e `345-347`). Crash dopo la riga: la ripresa ricrea il worktree, con `--force` solo per un percorso registrato e sparito (`start.py:103-122` e `150-157`). Test: `tests/test_start.py:239`, `tests/test_start.py:455`, più le varianti con la registrazione tolta e con un altro worktree mancante. Residuo: un `sqlite3.Error` in `create_work` lascia ramo e worktree senza dirlo (Minor m10). |
| 4. Verdetto falsificato o vecchio | **Regge** | Nella matrice di `bin/tollgate_analysis/verdicts.py:46-83` un verdetto non valido non è mai `approved`. `task_verdict` accetta solo il revisore in attesa (`_common.awaiting_review`, `bin/tollgate_checks/_common.py:88`) e controlla l'impronta (`bin/tollgate_checks/task_verdict.py:30-32`). L'implementatore non passa di lì (`subagent_stop.py:63-70`). `task done` lega l'esito a `git.head(wt)` e al worktree pulito (`bin/tollgate_flow/taskcmd.py:322-327`). Test: `tests/test_verdicts.py:91`, `tests/test_check_task_verdict.py:116` e `:123`. |
| 5. Percorsi con spazi e titoli non ASCII | **Regge**, con un residuo | `gitw.worktree_dir` (`bin/tollgate_flow/gitw.py:119-121`), `add_excludes` nella cartella comune (`gitw.py:83-96`) e `paths.program_command`, cioè `python3` più `shlex.quote` (`bin/tollgate_core/paths.py:16-19`), usato da brief, messaggi dei veti, SubagentStart, riga «programma» e footer. Test: `tests/test_start.py:63`; la prova reale è stata ripetuta sul percorso con spazi (Task 13, giro 2). Residuo: il suggerimento di `rebase --abort` stampa il percorso senza virgolette (Minor m8). |

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

**m1. `delete_branch` può togliere un ramo in uso nel worktree di un'altra sessione.** È il rinviato del Task 3 (riga 66), con una conseguenza peggiore di quella annotata. Codice: `bin/tollgate_flow/start.py:377-383` e `gitw.py:73-80`.
- *Guasto.* Due `start 7` partono insieme. La sessione A crea `tg/7-x` alla base e il suo worktree. Il `worktree add -b` di B fallisce perché il ramo esiste, e B chiama `delete_branch(main, "tg/7-x", base_sha)`. `update-ref -d` è un comando plumbing e non controlla i worktree (a differenza di `git branch -d`), quindi il ramo di A sparisce. L'HEAD del worktree di A punta allora a un ref inesistente, e il primo commit di A diventa un commit radice senza la storia di `main`. È un'analisi sul comportamento di git: non l'ho provata dal vero, perché la sessione isolata nega git fuori dal worktree.
- *Correzione.* Prima di `delete_branch`, salta la rimozione se il ramo compare in `git.worktrees(main)`, oppure se esisteva già prima del `worktree_add` (rileggere `local_branches` subito prima). Serve un test che passi da `start()`, il che chiude anche il rinviato della riga 65.

**m2. Una connessione sqlite resta aperta in un test, e il piano principale dice «nessun `ResourceWarning`».** Codice: `tests/test_statusline.py:137-143` e `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md:6`. Dettagli più sotto, in «Origine dell'unclosed database».
- *Guasto.* Il messaggio compare a ogni suite, e a ogni corsa resta in `/tmp` una cartella `tollgate lab *`. La frase del piano è falsa.
- *Correzione.* Sostituire `self.addCleanup(lab.ts.cleanup)` con `self.addCleanup(lab.close)`. La frase del piano diventa vera così com'è.

**m3. `cli_calls` non riconosce tutte le forme del programma, e la decisione 22 si aggira.** Codice: `bin/tollgate_checks/cli_calls.py:18-29` e `:40-41`.
- *Guasto.* Ho provato le forme sul parser. `python3 -B "<bin>" task done 1`, `p="<bin>"; python3 "$p" task …` e `python3 "$(echo <bin>)" task …` danno `None`, e un errore di parsing dà `[]`. Un subagente che usa una di queste forme lancia `task done`, `review-prepare` o `status --checkpoint` senza diniego. Lato coordinatore il guasto è fail-closed: senza segnale `start` e `act` rifiutano.
- *Correzione.* In `_program_args` salta le opzioni dell'interprete (gli argomenti che cominciano con `-`) prima dello script. Con `agent_id` e un errore di parsing, nega se il testo grezzo contiene il nome del programma insieme a `task`, `act`, `start` o `--checkpoint`. Serve un test per le tre forme.

**m4. `agents/implementer.md:50` e `:65` scrivono `tollgate verify` e `tollgate block open` nudi**, con il ripiego «il percorso del programma indicato dal brief».
- *Guasto.* `tollgate` non è nel PATH. L'implementatore spreca un turno, oppure ricostruisce il percorso nudo, che è vietato dal vincolo (2) del piano principale e fallisce nel worktree con gli spazi. È un'incoerenza con D2 e con `program_command`.
- *Correzione.* Rimandare al «comando esatto del brief, nella forma `python3 '<bin>' verify`» e fare lo stesso per `block open`, che SubagentStart inietta già in quella forma.

**m5. Spec rev 22: due frasi non descrivono il codice.**
- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:459` dice: «Un revisore è in attesa solo se lanciato dopo l'ultimo `review-prepare`». `awaiting_review` non confronta i tempi (`_common.py:88-103`): basta che `review_sha` e `review_code` non siano nulli. Un revisore lanciato prima di un secondo `review-prepare` è quindi «in attesa» e riceve un veto per codice diverso. Il guasto è fail-closed, ma la frase va corretta in: «solo se esiste una revisione preparata (dopo un `--fix` serve un nuovo `review-prepare`)».
- `…design.md:333` dice: «I rifiuti si raccolgono tutti e si stampano insieme». In realtà si raccolgono solo i prerequisiti. I rifiuti di ambiente, sessione, rete, `gh` e ramo esistente escono uno alla volta (`start.py:295-347`). Va precisato.

**m6. Piano principale, riga 78: `write_checkpoint(state, cwd, *, note=None, now=None)`.** La firma reale è `note` obbligatorio per parola chiave, senza valore predefinito (`bin/tollgate_flow/checkpoint.py:90`). Si allinea il testo, oppure si aggiunge `=None` al codice.

**m7. `start._fence` (`start.py:66-69`) duplica `tollgate_analysis.brief.fence` (`brief.py:16-18`).** Va usata la funzione pubblica: è la stessa regola di sicurezza, e conviene una sola fonte.

**m8. Il suggerimento `git -C {wt} rebase --abort` in `start.py:164-165` non mette il percorso tra virgolette.** Con il repo in `…/Plugin IT workflow/` il comando da copiare è rotto. Correzione: `shlex.quote(str(wt))`.

**m9. I nomi `agent` e `reviewer` dei profili non sono convalidati.** Codice: `bin/tollgate_analysis/profiles.py:76-91`, `config.py:99`.
- *Guasto.* La spec (`…design.md:425`) impone `<plugin>:reviewer-<area>` e `<plugin>:implementer-<area>`, ma nessuno lo controlla. Prendiamo un profilo con `reviewer = "acme:code-review"`. Non è di sola lettura (`config.is_readonly`), quindi `pre_agent` lo tratta come scrittore senza `task start` e lo nega (`agents.py:59-69`). Il task resta in `review` per sempre. Un `agent` che invece combacia con `reviewer-*` sarebbe di sola lettura: `take_pending` non scatta e il task non parte.
- *Correzione.* `ConfigError` al caricamento, oppure il ripiego sui generici con un avviso, quando il nome non rispetta la forma. Spetta a **P3b**, che chiude il criterio 38.

**m10. `create_work` fallisce con un errore diverso da `WorkExists` dopo `worktree_add` (`start.py:384-390`).**
- *Guasto.* Con `sqlite3.Error` o `DbError` l'errore risale fino a `cli.main`, che stampa «errore del database» con uscita 1. Ramo e worktree restano, e nessuno li nomina. Il `start` successivo rifiuta con `/tollgate:adopt`, che in P3a non esiste.
- *Correzione.* Catturare anche `sqlite3.Error` e `db.DbError` con lo stesso messaggio di `WorkExists` («creati … rimuovili a mano»). Costa poche righe. La rimozione automatica resta a P3b, insieme al rinviato della riga 55.

**m11. Il segnale della CLI non si consuma e non confronta `argv`** (`sessions.py:113-133`).
- *Guasto.* Una seconda chiamata a `start` o `act` nella stessa cartella entro 120 s, senza hook (dal terminale, o da una sessione con tollgate spento), riceve la sessione dell'ultima chiamata con segnale. È raro e non viola la decisione 2, che fissa tre condizioni.
- *Correzione.* `cli_session` toglie la voce usata e confronta `argv` con `sys.argv`. Spetta a **P3b**, che aggiunge sottocomandi con segnale.

**m12. Dopo i 5 giri il ciclo si ripete** (`taskcmd.py:104-107`).
- *Guasto.* Il sesto `--fix` apre `needs_you`. Il `resolve` lo chiude, ma il task resta in `review` con `changes`. `next_step` indica di nuovo `--fix`, che riapre il blocco. In P3a non esiste un'uscita, salvo abbandonare il lavoro.
- *Correzione.* `approve rounds`, già previsto in P3b (piano principale, riga 77). Nel frattempo `next_step` dovrebbe dire che serve una decisione dell'utente.

**m13. Il revisore che esegue un test può risultare `tampered`.** `agents/task-reviewer.md:28` ammette «un test mirato». Se però il progetto non ignora `__pycache__` o `.pytest_cache`, l'impronta di 7.3 cambia e si apre `needs_you` (`_common.py:74-77`). Il guasto è fail-closed ma crea attrito. Correzione: escludere dall'impronta le cache note, oppure dire nel prompt di non eseguire test che scrivono file. Spetta a **P3b**, dove la stessa regola vale per il revisore finale.

## Origine dell'unclosed database

**Fonte: soltanto i test. Non è un difetto del prodotto.**

- La connessione è quella di `tests/hookkit.py:73` (`Lab.__init__`, `self.conn = db.open_db(...)`). Il test `tests/test_statusline.py:137` (`CtxTest.test_context_guard_reads_it`, Task 11, commit 7240ba8) crea `Lab()` e registra solo `lab.ts.cleanup`. `lab.close()` non si chiama mai, e così restano aperte sia la connessione sia la cartella temporanea `tollgate lab *`.
- Ho fatto due controlli mirati:
  1. `python3 -B -X tracemalloc=20 -W error::ResourceWarning -m unittest tests.test_statusline.CtxTest.test_context_guard_reads_it` stampa `OK` e poi `Exception ignored in: <sqlite3.Connection …> ResourceWarning: unclosed database`, all'uscita dell'interprete, come a fine suite.
  2. Controprova: lo stesso test, con un involucro esterno che chiude `lab.conn` dopo l'esecuzione, non stampa più nulla. Un test della stessa classe senza `Lab` (`test_null_when_missing`) è pulito.
- Nel prodotto ogni `db.open_db` ha la sua chiusura in `finally`: `start.py:324-357`, `taskcmd.py:75-86`, `taskcmd.py:241-247` e `:313-333`, `actapply.py:111-138`, `checkpoint.py:93-103`, `cli.py:252-273`, `runner.py:180` e `:326`. Anche `db.backup` e `integrity_ok` chiudono le loro connessioni.

## Triage dei minori rinviati

| Riga del ledger | Rilievo | Esito | Motivo |
|---|---|---|---|
| 14 | T1: controprova di `--strict` senza un log dedicato | c | È solo documentazione. V4 è stato riverificato nel giro 1 e passa dal Task 10. |
| 44 | T2: corsa sul merge di `cli/<session>.json` | c | Riguarda solo hook paralleli della stessa sessione. Il peggio è un segnale perso, cioè un rifiuto (fail-closed). |
| 45 | T2: test di `sessions` scritti dopo il codice | c | È storia del processo; i test ci sono e passano. |
| 46 | T2: `test_layers` non vede gli import dinamici | c | Né core né flow né analysis usano `importlib`. L'unico uso è `tollgate_hooks/registry.py`, legittimo. |
| 49 | T2: ordine degli import in `test_flowkit.py` | c | Estetico. |
| 55 | T3: `WorkExists` dopo `worktree_add` lascia orfani | b (P3b) | `adopt` e `cleanup` li gestiscono. Il messaggio c'è già; per il caso `sqlite3.Error` vedi m10. |
| 56 | T3: `--limit 200` e `--limit 100` filtrati lato client | b (P3b per le PR, P4 per sentinel) | Il ramo remoto esistente lo vede già `ls-remote`. Resta il caso di una PR vecchia con il ramo cancellato. |
| 57 | T3: `_checks` rilegge il ref invece di usare `base_sha` | c | Diverge solo con un `fetch` concorrente tra due letture, e l'effetto è un avviso. |
| 65 | T3: il test del ramo preesistente chiama `delete_branch` direttamente | a | Va insieme a m1: il test nuovo passa da `start()`. |
| 66 | T3: ramo preesistente alla base tolto in una corsa | a | Vedi m1: il ramo può essere in uso nell'altro worktree, e la storia si rompe. La correzione costa poche righe. |
| 74 | T4: `worktree add --force` con il ramo in uso altrove | b (P3b) | Richiede un percorso registrato e sparito più il ramo attivo altrove. Il posto giusto sono `cleanup` e `adopt`. |
| 75 | T4: test di `ResumeTest` senza RED | c | È storia del processo. |
| 82 | T5: apertura di un recinto con rientro qualsiasi | b (P3c) | Riguarda il parser del piano, che P3c riprende con `approve plan` e `plan-adversary`. |
| 83 | T5: `verify_cmd` e percorsi tra apici non recintati | c | Si rompe solo con un percorso che contiene un backtick. `program_command` quota per la shell. |
| 92 | T6: brief orfano in `.tollgate-run/` | c | La cartella è ignorata, e il `task start` successivo la riscrive. |
| 100 | T7: `awaiting_review` senza task prende il task più basso | c | È fail-closed, e il flusso è sequenziale. |
| 101 | T7: `task_reserve` applicato anche dopo un diniego | c | `agents.py` è l'unico controllo su `pre_agent`. Il costo (120 s) è dichiarato nella spec, in 6.3. |
| 102 | T7: `json_candidates` quadratica | b (P3b) | Revisore finale e verificatore avranno messaggi più lunghi; lì serve un tetto o una scansione lineare. |
| 103 | T7: report vecchio di un revisore ripreso | c | Con un codice vecchio il verdetto riceve il veto (fail-closed). |
| 105 | T7: configurazione caricata due volte; una riga lunga | c | Estetico. |
| 108 | T7: `approved` dichiarato con un blocker scartato resta `approved` | b (P3b) | Combacia con la lettera della spec rev 22, 8.6. Da rivedere con la distinzione delle regole `[blocca]` di P3b. |
| 115 | T8: `cap_paths` fuori dalla transazione | c | L'effetto è prudente: un percorso perso alza il livello. |
| 133 | T10: il checkpoint non distingue una revisione preparata da una non preparata | b (P3b) | Dopo `/clear` non c'è un revisore in primo piano vivo, quindi rilanciare `review-prepare` non fa danni. Va allineato alla tabella della skill `execute` quando P3b tocca `next_step`. |
| 134 | T10: la riga «revisore:» è testata solo con il tipo predefinito | c | È una riga di stampa su `tasks.reviewer_type`. `test_profile_agent_chosen` copre l'assegnazione. |
| 140 | T11: `.tmp` orfani di `ctx/` | c | Verificato: `Path.glob("*")` include i file nascosti, quindi `housekeeping` li toglie dopo `retention_days` (`housekeeping.py:15-23` e `:44-46`). |
| 142 | T11: «5.» scritto così com'è nel ramo `sed` | c | Succede solo senza `python3`. `context_pct` scarta il JSON non valido e restituisce `None`. |
| 149 | T12: `killpg` doppio, `PermissionError` non soppresso | c | Servirebbe il riuso del pgid nell'arco di millisecondi. Se si tocca `verify`, è una riga. |
| 150 | T12: `sleep(0.3)` fisso nel test del figlio in background | a | È la stessa classe del watchdog: il ruling del Task 14 non tollera test instabili. Uno zombie, o un carico alto, lo fanno fallire. Correzione: attesa a polling, come `wait_alive`. |
| 162 | T13: percorso nudo nel footer di `runner.py:50` | c (chiusa) | Corretto nel Task 14 (`runner._footer` usa `program_command`; test `FooterTest`). |
| 163 | T13: D6, il payload di `assign` non mostra `implementer` e `pending` | b (P5) | È osservabilità degli eventi e non tocca il comportamento. |

## Verdetto

**Da correggere, con un giro breve fatto solo di Minor.** Non ci sono Critical né Important. Su tutto il ramo l'architettura tiene:
- gli strati sono rispettati: `tests/test_layers.py` passa e un grep lo conferma;
- le transizioni di `task start` e `unblock_all` sono atomiche;
- la CLI e gli hook usano gli stessi nomi, codici d'uscita e forma del programma;
- gli hook di controllo sono fail-closed, salvo il riconoscimento del programma descritto in m3;
- le risorse si chiudono nel prodotto.

Prima del merge, a basso costo:
1. **m1** con le righe 65 e 66: niente `delete_branch` su un ramo in uso o preesistente, e un test che passa da `start()`.
2. **m2**: `addCleanup(lab.close)` in `tests/test_statusline.py:139`.
3. **Riga 150**: polling al posto di `sleep(0.3)` in `tests/test_verify.py:238`.
4. **m3**: opzioni dell'interprete ed errore di parsing in `cli_calls`.
5. **m4**: comandi del brief in `agents/implementer.md`.
6. **m5** e **m6**: tre frasi tra spec e piano principale.
7. **m7**, **m8** e **m10**: `brief.fence`, il percorso quotato nel suggerimento di rebase, il messaggio su ramo e worktree lasciati.

Da rinviare, già assegnati: m9, m11, m12 e m13 a P3b, più le righe «b» della tabella. Dopo il giro, `tests/run` verde con `python3.11` e `python3` e niente «unclosed database» a fine suite: a quel punto il ramo è pronto per il merge.
