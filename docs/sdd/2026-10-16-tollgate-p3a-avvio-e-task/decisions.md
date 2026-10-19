## Decisioni di questo piano

Scelte che la spec lascia aperte o che i fatti impongono. Per ognuna è indicato il costo se sbagliata. Il Task 14 le riporta nella revisione 22 della spec.

1. **P3 diviso in tre piani** (decisione dell'utente del 16/10/2026): P3a (questo), P3b (chiusura: `finish`, revisione finale, `open-pr` con il blocco 18.1, `sync`, `adopt`, `cleanup`, `abandon`), P3c (percorso L2: audit della spec, avversari, `approve spec/plan`, `reopen`, `start --spec`). Le skill di P3a nominano già `/tollgate:finish`, che arriva con P3b. Costo: nessuno, P3a non si pubblica da solo.
2. **Sessione della CLI tramite segnale.** La CLI gira dentro Bash e non riceve il `session_id`. Per i comandi del coordinatore che devono conoscere la sessione (`start`, `act apply`), il modulo `cli_calls` su `pre_bash` registra l'operazione `cli_call`. L'operazione scrive `<cartella di stato>/cli/<session_id>.json` con `{"cwd": <directory effettiva>, "argv": [...], "at": <ora>}`. La CLI chiama `sessions.cli_session(state, cwd, subcommand, now)`, che accetta un segnale solo se valgono tutte e tre le condizioni:
   - è più recente di 120 s;
   - ha la stessa directory, risolta;
   - riguarda lo stesso sottocomando.

   Con zero segnali la CLI rifiuta («sessione non riconosciuta: lancia il comando da Claude Code con tollgate acceso»). Con più sessioni candidate rifiuta e chiede di ripetere. Il Task 1 verifica che il segnale scritto dall'hook sia visibile al comando che segue. Costo: con tollgate spento, `start` e `act apply` non funzionano. Va bene, perché con `OFF` gli atti non si registrano comunque.
3. **Percorso del programma.** Ogni `/tollgate:*` digitato riceve da `UserPromptExpansion` la riga `tollgate: programma <percorso assoluto di bin/tollgate>`. Le skill usano `${CLAUDE_PLUGIN_ROOT}/bin/tollgate` e, se la variabile non è espansa, il percorso di quella riga. Il Task 1 verifica l'espansione. Costo: una riga in più nel contesto per comando.
4. **Worktree in `<checkout principale>/.claude/worktrees/tg-<N>-<slug>`**, la posizione di `EnterWorktree`, già gestita come worktree annidato da `_common.in_main_checkout`. `start` scrive in `$(git rev-parse --git-common-dir)/info/exclude` tre righe, senza duplicarle: `.claude/worktrees/`, `.tollgate-run/` e `docs/superpowers/reviews/*/checkpoint.md`. Costo: un checkout principale con `.claude/` tracciato vede i worktree come file ignorati, non come modifiche.
5. **Il checkpoint non si committa.** `docs/superpowers/reviews/<N>/checkpoint.md` è ignorato (decisione 4). Così `verify` non trova il worktree sporco a ogni checkpoint, e `SessionStart` lo legge come oggi. Costo: si perde se si cancella il worktree; la ripresa riparte da `tasks`.
6. **Conferme di `start`.** La CLI non è interattiva. Gli avvisi che chiedono conferma (issue chiusa, stati del predefinito non verdi, intenti in sospeso, altra sessione viva) fanno uscire `start` con codice 3 e l'elenco. La skill li mostra all'utente e, se lui conferma, rilancia con `--confirm`. Ramo o PR remoti già esistenti, oppure un ramo locale `tg/<N>-*` senza riga, rifiutano sempre e indicano `/tollgate:adopt #N` (P3b). Costo: il modello potrebbe passare `--confirm` da solo. Sono avvisi, non obblighi (1.1).
7. **Versione di Superpowers: `>= 6.4.1` e `< 8.0.0`**, letta da `~/.claude/plugins/installed_plugins.json` (versione 2: `plugins["superpowers@claude-plugins-official"][*].version`). Fuori intervallo, o non installato: rifiuto. Il limite superiore protegge il formato del piano (`### Task N`, `Create:/Modify:/Test:`). Costo: Superpowers 8 richiede un aggiornamento di tollgate.
8. **Gate installato** = sul riferimento predefinito ci sono i cinque workflow di 9.1 (`.github/workflows/tollgate-{guard,run,verdict,base,sentinel}.yml`) e `.github/tollgate/VERSION`. Un file mancante dà il rifiuto. Una versione diversa da `tollgate_core.VERSION` dà un avviso e `init --update`. È un **contratto verso P4**, che deve scrivere quei file con quei nomi. Costo: se P4 cambia i nomi, si aggiorna una costante (`prereq.GATE_FILES`).
9. **Migrazione 3** (solo in avanti):
   - `tasks.review_sha`: lo SHA dato al revisore da `review-prepare`;
   - `tasks.review_findings`: JSON, default `'[]'`;
   - `tasks.reserved_at`: la prenotazione del lancio (decisione 12).

   Il verdetto sta in `tasks.verdict`, già presente. Costo: una migrazione.
10. **Verdetto del revisore del task.** È valido solo se valgono tutte queste condizioni:
    - è JSON di 18.5;
    - `sha` = `tasks.review_sha` e `code` = `tasks.review_code`;
    - `task` è il numero del task;
    - il revisore non ha cambiato file (7.3).

    Un rilievo senza `rule`, `file` o `line` non vale e si scarta.

    Con `reviewer_standard` acceso l'esito **effettivo** è `changes` solo se `spec_compliance` non è vuoto o c'è almeno un rilievo valido `blocker` o `major`; altrimenti `approved` (8.6). Con il componente spento vale l'esito dichiarato.

    Un verdetto non valido riceve un veto (uscita 2: il revisore riscrive). Dopo 2 veti si apre `needs_you`, come in 8.1. Costo: un revisore che non sa scrivere il JSON costa due giri.
11. **Il modulo `task_verdict` possiede l'intera chiusura del revisore in attesa**: sola lettura, verdetto e riga del subagente. `subagent_stop` non tocca i subagenti di sola lettura che `task_verdict` riconosce come revisori in attesa (`_common.awaiting_review`). Altrimenti la riga si chiuderebbe come `done` anche dopo un veto, perché i `record` si applicano anche dopo un `deny` (3.2). Costo: nessuno.
12. **Prenotazione del lancio** (rinviato del Task 18 di P2: due `Agent` nello stesso messaggio). `pre_agent`, quando ammette l'implementatore, registra `task_reserve`, che scrive `tasks.reserved_at`. Un secondo `Agent` sullo stesso task con una prenotazione di meno di 120 s è negato. `SubagentStart` (`take_pending`) azzera la prenotazione. Costo: se il lancio fallisce dopo il `PreToolUse`, si aspettano 120 s.
13. **`act apply [<id>]`.** Senza id applica l'ultimo atto `pending` della sessione (decisione 2) tra quelli applicabili. In P3a sono applicabili:
    - `resolve <id> <nota>`: chiude il blocco con la nota. Quando si chiude l'ultimo blocco, ogni task `blocked` torna `pending` (evento `unblocked`, tabella di 6.3);
    - `resolve writer`: `subagents.interrupt` sugli implementatori `running` del lavoro;
    - `approve level <L> <motivo>`: `phases.set_level_cap`.

    L'atto si consuma sempre, così non si applica due volte. P3b e P3c aggiungono voci alla tabella `APPLIERS`. `approve waiver` e `approve effect` non si applicano con `act apply`: valgono già dal DB (8.4, 8.5). Costo: nessuno.
14. **`approve level` è ammesso solo se la fase corrente esiste nella sequenza del livello di arrivo** (12.3). Per esempio L2 in `spec_audit` → L1 è rifiutato, perché L1 non ha `spec_audit`. Il tetto abbassa `level` (`level_change` con causa `cap`), scrive `level_cap`, `level_cap_reason` e `level_cap_paths` (i percorsi sensibili del diff attuale) e non tocca la fase. Costo: chi vuole abbassare in `spec_audit` deve prima arrivare a `plan`.
15. **Scelta dell'agente per un task** (6.3): `profiles.task_routing(files, profiles)`.
    - I verticali del task sono quelli di `vertical_for` sui file `Create/Modify/Test`.
    - Implementatore e revisore: se i verticali dichiarano **un solo** valore non vuoto di `agent`, si usa quello, e allo stesso modo per `reviewer`; altrimenti `tollgate:implementer` e `tollgate:task-reviewer`.
    - Skill dell'implementatore: unione dei `skills` dei verticali.
    - Skill del revisore: unione dei `reviewer_skills` dei verticali e dei profili `cross` che quei verticali elencano.
    - Entrambe le liste hanno un tetto di 3, nell'ordine di dichiarazione; `split_candidate` indica che l'unione superava 3 o che gli agenti erano diversi.

    Costo: nessuno, è la regola della spec.
16. **Skill non installate** (6.3: «non blocca»). Si cercano in quest'ordine:
    - `<installPath>/skills/<nome>/SKILL.md` del plugin, per i nomi `plugin:nome`;
    - `~/.claude/skills/<nome>/SKILL.md`;
    - `<worktree>/.claude/skills/<nome>/SKILL.md`.

    `task start` toglie le skill assenti da `tasks.skills_required` e le segna «assente» nel brief, così `SubagentStop` non mette il veto su una skill impossibile. Costo: una skill di plugin in una posizione diversa risulta assente; il gate la riporta in `attenzione` (P4).
17. **Nomi.** Ramo `tg/<N>-<slug>`: lo slug viene dal titolo, minuscolo, traslitterato con `unicodedata` NFKD, con `[a-z0-9-]`, trattini compressi, al massimo 40 caratteri, mai vuoto (`issue`). Se il ramo esiste in locale o su `origin` si aggiunge `-2`, `-3`… Implementatore `tg-<N>-t<k>`; giri 4-5 `tg-<N>-t<k>-r<giro>` (6.3). Costo: nessuno.
18. **Giri di correzione.** `task start k --fix` è ammesso da `review` con verdetto `changes`. Al primo `--fix` con `fix_rounds` già a 5, `task start` apre `needs_you` («giri di correzione esauriti sul task k») e rifiuta. Giri 1-3: `pending = resume`, stesso nome. Giri 4-5: `pending = launch`, nome `-r<giro>`, e il brief chiede `model: inherit`. Costo: nessuno.
19. **Ripresa in `review` o `pr_open`.** `start` su un lavoro in quelle fasi non cambia fase. Con `--reopen-execution` porta la fase a `execution` (causa `start`, 12.3). Il rilevamento di merge e chiusura della PR è di P3b. Costo: un flag in più.
20. **Il brief legge il piano a `plan_sha`.** `plan_sha` è il blob del file (`hash-object`, non scritto nel DB degli oggetti). `git.blob_text(repo, sha)` prova `cat-file`. Se il blob non c'è, usa il file del worktree solo se il suo `hash-object` coincide. Altrimenti `task start` rifiuta («piano diverso dalla versione registrata»). Costo: nessuno, il piano è bloccato dopo la registrazione.
21. **Statusline: un involucro, non una sostituzione.** `statusline/ctx` legge l'input JSON, scrive `ctx/<session_id>.json` (`{"used_pct": context_window.used_percentage o null}`) e poi esegue il comando di statusline passato come argomenti, con lo stesso input. `/tollgate:setup` propone di avvolgere la statusline dell'utente, o `statusline/statusline.sh` se non ne ha una. Costo: un processo in più per aggiornamento della statusline.
22. **Comandi del coordinatore negati ai subagenti.** `cli_calls` nega a un input con `agent_id` (un subagente) le chiamate al programma `tollgate` con `start`, `task`, `act` e `status --checkpoint`. `verify`, `waiver add` e `block open` restano permessi. Costo: nessuno.

## Rilievi ripresi qui

| Rilievo | Dove |
|---|---|
| P1: `bind_session` e `set_level` agiscono su lavori `closed` | Task 12 |
| P1: `level_cap` mai consultato | Task 8 (`set_level_cap`) |
| P1: pulizia dei `.tmp-*` orfani in `backup/` da `start` | Task 3 |
| P1: `create_work` non fa la copia del DB | Task 3 (`start` chiama `db.backup` dopo la creazione) |
| P1: `tollgate status` crea DB e cartella pur essendo in sola lettura | Task 9 |
| P1: `stats` globale ignora gli eventi senza lavoro | Task 9 |
| P2 T2: `tasks.assign` senza `reviewer_type` lo azzera | Task 6 |
| P2 T4: `plan.py`: più file su una riga, recinti `~~~` e da 4 backtick, ID duplicati, must-have in grassetto («prima dell'uso reale») | Task 5 |
| P2 T10: figli in background vivi dopo `verify`; `killpg` anche a fine normale | Task 12 |
| P2 T14: `waiver_hint`/`explain` con parametro `issue` inutilizzato | Task 12 |
| P2 T18: due `Agent` nello stesso messaggio | Task 7 (decisione 12) |
| P2 T18: `take_pending(resume=True)` fragile con più task dello stesso tipo | Task 6 |
| P2 T19: manca il test che l'implementatore ripreso non rinnova l'impronta | Task 6 |
| P2 finale M3: sessione viva e subagente fermo solo con strumenti intercettati | Task 14 (nota nella spec: nessun matcher su `Read/Grep/Glob`, per non lanciare Python a ogni lettura) |
| P2 finale M7: `rm -rf` fuori dal repo negato anche in `/tmp`, messaggio poco utile | Task 12 (il messaggio suggerisce `rm -r` o un percorso nel worktree) |
| Spec 16: forma dell'input di `NotebookEdit` | Task 1 |

Restano ad altri piani, e non sono toccati qui:
- P3b: `dod._findings` che accetta ogni `user_decision`, `abandon #N` che eredita il lavoro della sessione, rebase e merge in `sync` (P2 T17);
- P3c: `from_approved_spec` senza `spec_path`;
- P4: criterio 34 in `protected`.
