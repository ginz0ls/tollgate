# tollgate P3a: avvio, ripresa e task

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portare un lavoro dall'issue a «tutti i task `done`» in locale: `start` (nuovo lavoro e ripresa), `task start/review-prepare/done` con gli agenti `tollgate:implementer` e `tollgate:task-reviewer` scelti per profilo, il verdetto del revisore del task a `SubagentStop`, `act apply` per `resolve` e `approve level`, `status --checkpoint`, statusline e skill `start`, `execute`, `status`, `approve`, `resolve`, `setup`.

**Architecture:** Un pacchetto nuovo, `bin/tollgate_flow`, contiene le operazioni con git in scrittura e `gh`. Può importare `tollgate_core` e `tollgate_analysis`, mai `tollgate_hooks` né `tollgate_checks`. Le funzioni pure nuove stanno in `tollgate_analysis`: testo del task, brief, nomi, instradamento per profilo, dimensione del task, verdetto. `tollgate_core` riceve la migrazione 3 e poche funzioni di scrittura. `tollgate_checks` riceve due moduli nuovi, `cli_calls` e `task_verdict`, e piccole modifiche. La CLI non conosce la sessione di Claude Code: la ricava da un **segnale** scritto dall'hook `PreToolUse Bash` (decisione 2). Skill e agenti sono file Markdown del plugin.

**Tech Stack:** Python ≥ 3.11, solo libreria standard (`sqlite3`, `argparse`, `secrets`, `subprocess`, `unittest`), bash, git, `gh`. Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 21; la revisione 22 la scrive il Task 14): sezioni 3 (skill, agenti, `marketplace.json`), 3.1 (`start`, `task`, `act apply`, `status --checkpoint`), 4, 5 (tetto), 6.1, 6.3, 8.4, 8.6 (revisore del task), 11.1, 11.3, 12.4 (ripresa), 18.5 (verdetto del revisore del task). Piano principale: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (sezione 3: contratti P1/P2 e i **vincoli per P3**; sezione 4: criteri). Registro di P2: `docs/sdd/2026-10-09-tollgate-p2-guardrail/` (`final-review.md` con il triage, `progress.md` con i minori rinviati). Rinviati di P1: memoria del progetto `p1-rilievi-rinviati.md`, riportati nella sezione «Rilievi ripresi qui».

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11 (spec 2). Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- Strati: `tollgate_analysis` non importa nulla di tollgate. `tollgate_flow` importa solo `tollgate_core` e `tollgate_analysis`. `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`. I moduli di `tollgate_checks` non scrivono nel DB: usano `record` (spec 3.2). Un test lo controlla (Task 2).
- Scritture nel DB solo con le funzioni di `tollgate_core`. `set_phase`, `open_block` e `close_block` si chiamano fuori da una transazione. Gli errori da gestire sono `db.DbError` all'apertura e `sqlite3.Error` durante le operazioni (vincoli 1-5 del piano principale).
- Vincoli per P3 del piano principale, tutti in questo piano:
  - (1) `name` del brief = `tasks.implementer` (Task 6);
  - (2) la statusline scrive `ctx/<session_id>.json` (Task 11);
  - (3) `start` pulisce `bound/` (Task 3);
  - (5) `approve level` scrive `level_cap_paths` (Task 8);
  - (6) i verdetti sono moduli nuovi di `subagent_stop` che controllano `tampered` (Task 7);
  - (7) `task start` chiama `tasks.assign` con `pending` (Task 6);
  - `start` registra le radici attive con `active.register` (Task 3).
  - Il vincolo (4), `open-pr`, è di P3b.
- La configurazione si legge dalla base del lavoro o dalla punta del ramo predefinito di `origin`, mai dal working tree (spec 3.2). `start` fa `git fetch origin` prima di leggerla.
- Il testo dell'issue non è fidato: non entra mai in un comando shell né negli argomenti di `git`. Va su file, in un recinto più lungo di ogni sequenza di backtick che contiene, marcato come dato (spec 6.1).
- Nessuna rete nei test. `gh` nei test è il finto `tests/fakegh.py`, attivato da `TOLLGATE_GH` con la sentinella (spec 3.1). **Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json` o `~/.claude/plugins/`**: si passano cartelle temporanee (`TempState`, `HOME` temporanea).
- I test non lanciano `claude`. Solo i Task 1 e 13 lanciano `claude -p`, sempre in `/tmp/tollgate-p3a`, con `--plugin-dir`, mai nel repo e mai con il plugin installato nella configurazione dell'utente.
- Identificatori in inglese, testi per l'utente in italiano (spec 0). Nessun `__pycache__` nel repo (`-B`).
- Commit dopo ogni task.

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

## Review Focus

1. **Testo dell'issue ostile** (titolo con `$(rm -rf ~)`, backtick, `"; touch /tmp/x`, emoji, recinti ```` ``` ````): lo slug resta `[a-z0-9-]`, nessun comando riceve il testo, `issue.md` lo racchiude in un recinto più lungo. Test: Task 3 `test_hostile_issue_title_and_body`.
2. **Due sessioni e il segnale della CLI** (due sessioni nella stessa cartella entro 120 s; segnale vecchio; sottocomando diverso): mai la sessione sbagliata. Si rifiuta con un messaggio. Test: Task 2 `test_cli_session_ambiguous_or_stale_refuses`.
3. **Avvio interrotto** (crash dopo `worktree add` e prima della riga; crash dopo la riga e prima del worktree): il secondo `start` propone l'adozione invece di creare `-2`, oppure ricrea il worktree in ripresa. Test: Task 3 `test_branch_without_row_proposes_adopt`, Task 4 `test_resume_recreates_missing_worktree`.
4. **Verdetto falsificato o vecchio** (SHA superato, codice sbagliato, verdetto scritto da un implementatore, revisore che ha cambiato file, JSON in mezzo al testo): mai `approved`. Test: Task 7 `test_verdict_validity_matrix`.
5. **Percorsi con spazi e titoli non ASCII** (il repo stesso è in `.../Plugin IT workflow/`): worktree, brief ed `exclude` funzionano. `FlowLab` crea repo con spazi nel percorso. Test: Task 3 `test_start_creates_work_in_path_with_spaces`.

## Mappa dei file

| File | Responsabilità |
|---|---|
| `spikes/hookprobe/skills/probe-root/SKILL.md`, `spikes/run-p3a-experiments.sh`, `docs/verifiche/2026-10-16-p3a-verifiche.md` | Verifiche del Task 1 |
| `bin/tollgate_core/db.py` | Migrazione 3 |
| `bin/tollgate_core/sessions.py` | Segnale della CLI (`note_cli_call`, `cli_session`), pulizia di `bound/` |
| `bin/tollgate_core/tasks.py` | `assign` senza azzerare, `take_pending` per numero, prenotazione, verdetto, `review-prepare`, skill richieste |
| `bin/tollgate_core/phases.py` | `set_level_cap`; nessuna scrittura su lavori chiusi |
| `bin/tollgate_core/git.py` | `blob_text` |
| `bin/tollgate_core/cli.py` | Sottocomandi `start`, `task`, `act apply`, `status --checkpoint` |
| `bin/tollgate_flow/gitw.py` | Git in scrittura: fetch, worktree, exclude, config |
| `bin/tollgate_flow/gh.py` | `gh` reale o finto: issue, PR, stati, issue di `sentinel` |
| `bin/tollgate_flow/prereq.py` | Prerequisiti di `start`: Superpowers, gate, GitHub, skill installate |
| `bin/tollgate_flow/start.py` | `start`: nuovo lavoro e ripresa |
| `bin/tollgate_flow/housekeeping.py` | Pulizie di `start` |
| `bin/tollgate_flow/taskcmd.py` | `task start`, `task review-prepare`, `task done` |
| `bin/tollgate_flow/actapply.py` | `act apply` |
| `bin/tollgate_flow/checkpoint.py` | `status --checkpoint`, tetto che ha fermato il lavoro |
| `bin/tollgate_analysis/plan.py` | `task_text`, correzioni del parser |
| `bin/tollgate_analysis/naming.py` | Slug, ramo, nome dell'implementatore |
| `bin/tollgate_analysis/profiles.py` | `task_routing` |
| `bin/tollgate_analysis/size.py` | Righe di un task (6.3), condivise da `review-prepare` e `SubagentStop` |
| `bin/tollgate_analysis/brief.py` | Testo dei brief di implementatore e revisore |
| `bin/tollgate_analysis/verdicts.py` | Verdetto del revisore del task (18.5) |
| `bin/tollgate_checks/cli_calls.py` | Segnale della CLI; comandi del coordinatore negati ai subagenti |
| `bin/tollgate_checks/task_verdict.py` | Verdetto del revisore del task a `SubagentStop` |
| `bin/tollgate_checks/{_common,agents,subagent_stop,acts,bash_rules}.py` | Revisore in attesa, prenotazione, report salvato, riga del programma, messaggio di `rm -rf` |
| `bin/tollgate_hooks/apply.py` | Operazioni nuove: `cli_call`, `task_reserve`, `task_verdict` |
| `agents/implementer.md`, `agents/task-reviewer.md` | Agenti (derivati da subagent-driven-development, MIT) |
| `skills/{start,execute,status,approve,resolve,setup}/SKILL.md` | Skill di P3a |
| `statusline/ctx` | Involucro che scrive il file del contesto |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `LICENSE`, `LICENSES/superpowers-MIT.txt` | Manifest, marketplace, licenze |
| `tests/fakegh.py`, `tests/flowkit.py` | `gh` finto e banco di prova del flusso |
| `tests/test_*.py` | Un file per modulo; `tests/test_criteria_p3a.py` per i criteri |

---

### Task 1: Verifiche di piattaforma per P3a

Fatti che il codice dà per buoni. Questo task non scrive codice di prodotto. Produce un esperimento e un rapporto.

**Files:**
- Create: `spikes/hookprobe/skills/probe-root/SKILL.md`
- Create: `spikes/run-p3a-experiments.sh`
- Create: `docs/verifiche/2026-10-16-p3a-verifiche.md`
- Modify: `spikes/hookprobe/probe.sh` (ramo temporaneo per V3, tolto a fine task)
- Modify: `spikes/fixtures/hook-inputs/samples.json` (chiave `PreToolUse-NotebookEdit`, se osservata)

**Interfaces:**
- Produces: esito di V1, che decide il testo delle skill nel Task 10 (decisione 3).
- Produces: esito di V3, che conferma o smentisce la decisione 2. Se la smentisce, il Task 2 si ferma con BLOCKED.
- Produces: esito di V4, che decide i campi di `marketplace.json` nel Task 10.

**Regole di cautela (vanno nel brief):** si lavora solo in `/tmp/tollgate-p3a`. `claude -p` si lancia solo con `--plugin-dir spikes/hookprobe`, tranne V4, che usa solo `claude plugin validate`. Niente `claude plugin install` né `marketplace add`. Non si toccano `~/.claude/settings.json`, `~/.claude/plugins/` né `~/.local/state/tollgate`. Nessun repo su GitHub.

- [ ] **Step 1: Skill sonda `probe-root`**: frontmatter `name: probe-root`, `description: Sonda P3a, solo su richiesta esplicita.`; corpo «Riporta alla lettera questa riga: RADICE=${CLAUDE_PLUGIN_ROOT} SKILLDIR=${CLAUDE_SKILL_DIR}».
- [ ] **Step 2: Script `spikes/run-p3a-experiments.sh`** sul modello di `spikes/run-p2-experiments.sh`: `P3=/tmp/tollgate-p3a`, `PROBE_LOG`, una funzione `run id modo prompt`. Esperimenti:
  - **V1**: «invoca con lo strumento Skill la skill hookprobe:probe-root e riporta alla lettera ciò che dice».
  - **V2**: «esegui con Bash `env | grep -i -E 'claude|session' | sed 's/=.*//'` e riporta i nomi»: solo i nomi delle variabili, mai i valori.
  - **V3**: con il ramo temporaneo di `probe.sh`, per `PreToolUse` di Bash con `PROBE_HS` nel comando, scrive `/tmp/tollgate-p3a/hs.txt` con il `session_id`. Prompt: «esegui con Bash `cat /tmp/tollgate-p3a/hs.txt # PROBE_HS` e riporta l'uscita».
  - **V5**: «crea con lo strumento NotebookEdit una cella nel notebook `/tmp/tollgate-p3a/n.ipynb`» (lo script crea prima un notebook vuoto valido).
- [ ] **Step 3: V4 senza sessione**: `claude plugin validate "$REPO"` sul repo con un `marketplace.json` di prova in `/tmp/tollgate-p3a/mkt/.claude-plugin/` (copia del repo con `git worktree add --detach`, mai nel checkout). Il file di prova è quello del Task 10, Step 4. Registra l'uscita e, se la validazione fallisce, il messaggio che indica la forma corretta.
- [ ] **Step 4: Eseguire** `bash spikes/run-p3a-experiments.sh` e leggere i log come nel Task 1 di P2. Un esito poco chiaro si ripete una volta, poi si scrive «non determinato».
- [ ] **Step 5: Rapporto** `docs/verifiche/2026-10-16-p3a-verifiche.md`, nella forma dei rapporti precedenti: versione di `claude`, tabella `Id | Voce | Esito | Evidenza | Conseguenza` per V1-V5, e la sezione «Conseguenze per il piano P3a»:
  - V1 sì: le skill usano `${CLAUDE_PLUGIN_ROOT}`; no: usano la riga «programma» (decisione 3).
  - V3 sì: decisione 2 confermata. V3 no: il Task 2 si ferma con BLOCKED e chiede al controller una strada alternativa.
  - V2: solo informativo, per la revisione 22.
  - V4: i campi validi di `marketplace.json` per il Task 10.
  - V5: campione `PreToolUse-NotebookEdit` in `samples.json` (anonimizzato come in P2) e la voce della sezione 16 chiusa.
- [ ] **Step 6: Togliere il ramo temporaneo di `probe.sh`**, poi commit:

```bash
git add spikes/hookprobe/skills/probe-root/SKILL.md spikes/run-p3a-experiments.sh docs/verifiche/2026-10-16-p3a-verifiche.md spikes/fixtures/hook-inputs/samples.json
git commit -m "tollgate P3a: verifiche (radice del plugin nelle skill, segnale della CLI, marketplace, NotebookEdit)"
```

---

### Task 2: Segnale della sessione, strati, banco di prova del flusso

**Files:**
- Modify: `bin/tollgate_core/sessions.py`
- Create: `bin/tollgate_checks/cli_calls.py`
- Modify: `bin/tollgate_hooks/apply.py` (operazione `cli_call`)
- Modify: `bin/tollgate_checks/acts.py` (riga «programma» per ogni `/tollgate:*`)
- Create: `bin/tollgate_flow/__init__.py`
- Create: `tests/fakegh.py`, `tests/flowkit.py`
- Test: `tests/test_sessions.py`, `tests/test_check_cli_calls.py`, `tests/test_check_acts.py`, `tests/test_layers.py`

**Interfaces:**
- Consumes: `bash.parse`, `bash.uses_tollgate_bin(cmd, plugin_bin)`, `bash.effective_dir`, `Ctx.plugin_bin`.
- Produces:
  - `sessions.CLI_DIR = "cli"`;
  - `sessions.CLI_WINDOW_S = 120`;
  - `sessions.note_cli_call(state, session: str, cwd: str, argv: list[str], *, now) -> None`: scrittura atomica (tmp più `os.replace`) di `<stato>/cli/<session>.json`. Ignora le sessioni che non passano `_SAFE`;
  - `sessions.cli_session(state, cwd, subcommand: str, *, now) -> str`, che solleva `sessions.CliSessionError` con il messaggio di decisione 2;
  - `sessions.CliSessionError(Exception)`.
- Produces: modulo `cli_calls` (evento `pre_bash`, ordine 5). Per ogni `Cmd` che usa il programma (`uses_tollgate_bin` o `argv[0]` con basename `tollgate`):
  - con `agent_id` e sottocomando `start`, `task`, `act`, o `status` con `--checkpoint`: `deny(..., rule="coordinator_only")` (decisione 22);
  - altrimenti, senza `agent_id`: `record("cli_call", cwd=<effective_dir>, argv=<argv[1:]>)`.
- Produces: `apply` registra `cli_call`, che chiama `sessions.note_cli_call` con `ctx.event.session`. `apply.OPS` passa a 23 voci.
- Produces: in `acts.py`, per ogni `command_name` che comincia con `tollgate:`, compresi quelli che non sono atti (`start`, `execute`, `status`, `setup`, `finish`, `init`), un `inject` con la riga `tollgate: programma <ctx.plugin_bin>`. Per gli atti la riga si aggiunge a «atto ricevuto».
- Produces: `tests/fakegh.py`, un eseguibile Python che legge `$TOLLGATE_FAKEGH_DATA` (JSON). Risponde a `issue view N --json …`, `pr list …`, `api repos/{o}/{r}/commits/{sha}/status`, `issue list …` e `auth status`, registra ogni chiamata in `$TOLLGATE_FAKEGH_LOG` ed esce con 1 se la risposta manca dai dati.
- Produces: `tests/flowkit.FlowLab(*, toml=DEFAULT_TOML, files=None, gate=True, issue=None)`, con:
  - `.ts` (TempState), `.main`, `.origin`, `.home` (HOME temporanea con `.claude/plugins/installed_plugins.json` che dichiara Superpowers 7.0.0);
  - `.env()`, con `TOLLGATE_STATE`, `TOLLGATE_GH=tests/fakegh.py`, i dati del finto e `HOME`;
  - `.cli(*argv, cwd=None, session="sess-flow") -> CompletedProcess`: scrive prima il segnale con `sessions.note_cli_call`, poi esegue `bin/tollgate`;
  - `.hook(payload)`, come `hookkit.Lab.hook`;
  - `.conn`, `.close()`.

  Con `gate=True` l'origin contiene i file della decisione 8. Le cartelle temporanee hanno uno spazio nel nome. `remote.origin.url` vale `https://github.com/prova/flow.git`, con `url.<origin nudo>.insteadOf` impostato su quell'URL: il fetch va al repo nudo locale e il controllo GitHub di `prereq.is_github` passa.

- [ ] **Step 1: Test che falliscono**
  - `test_sessions.py::CliSessionTest`:
    - `test_cli_session_found` (segnale di 5 s prima, stessa cartella e sottocomando → restituisce la sessione);
    - `test_cli_session_ambiguous_or_stale_refuses`: (a) due sessioni con segnali validi → `CliSessionError` con «più sessioni»; (b) segnale di 121 s prima → errore «sessione non riconosciuta»; (c) sottocomando diverso → errore; (d) cartella diversa → errore;
    - `test_note_cli_call_rejects_unsafe_session` (`"../x"` non crea file).
  - `test_check_cli_calls.py`:
    - `test_coordinator_call_records_signal`: `hookkit.Lab`, `bash(f"'{BIN}' start 7")` dalla sessione principale → uscita 0 e file `cli/sess-lab.json` con `argv[0] == "start"`;
    - `test_subagent_cannot_run_coordinator_commands`: con `agent_id`, `task start 1`, `act apply` e `status --checkpoint` → 2; `verify` e `block open needs_you --reason x` → 0;
    - `test_cd_then_call_records_effective_dir`.
  - `test_check_acts.py::ProgramLineTest::test_every_tollgate_command_gets_program_line` (`tollgate:start` e `tollgate:resolve` → l'iniezione contiene `programma` e il percorso di `bin/tollgate`).
  - `test_layers.py::LayersTest::test_imports`: con `ast`, `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`, e `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`.
- [ ] **Step 2: Verificare il fallimento**: `python3 -B -m unittest tests.test_sessions tests.test_check_cli_calls tests.test_check_acts tests.test_layers` → errori di import e asserzioni.
- [ ] **Step 3: Implementare** le firme sopra, più `fakegh.py` e `flowkit.py`. `cli_session` legge i file di `cli/` e confronta le cartelle con `Path.resolve()`.
- [ ] **Step 4: Verificare**: stesso comando verde, poi `tests/run`.
- [ ] **Step 5: Commit** «tollgate P3a: segnale della sessione per la CLI, riga del programma, strati, banco di prova del flusso».

---

### Task 3: `start` su un lavoro nuovo

**Files:**
- Create: `bin/tollgate_flow/gitw.py`, `bin/tollgate_flow/gh.py`, `bin/tollgate_flow/prereq.py`, `bin/tollgate_flow/housekeeping.py`, `bin/tollgate_flow/start.py`
- Create: `bin/tollgate_analysis/naming.py`
- Modify: `bin/tollgate_core/sessions.py` (`prune_bound`), `bin/tollgate_core/cli.py` (sottocomando `start`)
- Test: `tests/test_naming.py`, `tests/test_prereq.py`, `tests/test_start.py`

**Interfaces:**
- Consumes:
  - core: `phases.create_work`, `phases.find_active`, `db.backup`, `active.register(state, repo, extra=[wt])`, `sessions.mark_bound`, `sessions.cli_session`, `events.prune_events`, `config.load_config`, `git.default_branch`, `git.resolve_ref`, `git.local_branches`, `git.exists_at`;
  - analysis: `level.labels_level`, `level.max_level`.
- Produces in `naming.py` (puro):
  - `slug(title: str) -> str`;
  - `branch_name(issue: int, title: str, taken: set[str]) -> str`;
  - `implementer_name(issue: int, task: int, round_: int = 0) -> str`, che dà `tg-<N>-t<k>`, oppure `tg-<N>-t<k>-r<round>` per `round_ >= 4`.
- Produces in `gitw.py` (scrittura, con `subprocess` e timeout di 120 s per `fetch`):
  - `fetch(repo) -> bool`: falso senza rete, mai un'eccezione;
  - `worktree_add(repo, path, *, branch, start_point, new_branch: bool)`;
  - `add_excludes(repo, lines: list[str])`: righe nuove in `info/exclude` della cartella comune, senza duplicati;
  - `set_config(repo, key, value)`;
  - `remote_branches(repo, pattern) -> list[str]` (con `ls-remote --heads origin`, falso senza rete).

  Errore: `gitw.GitWriteError`.
- Produces in `gh.py`:
  - `GH_ENV = "TOLLGATE_GH"`;
  - `gh_cmd(state) -> list[str]`: `[TOLLGATE_GH]` se `paths.test_env` lo dà, altrimenti `["gh"]`;
  - `run_json(state, repo, args) -> object`;
  - `Issue(number, title, body, state, labels, author_association)`;
  - `issue(state, repo, n) -> Issue`;
  - `prs_for_branch_prefix(state, repo, prefix) -> list[dict]`;
  - `commit_state(state, repo, sha) -> str | None`;
  - `sentinel_issues(state, repo) -> list[dict]`.

  Errore `gh.GhError` (gh assente, uscita diversa da 0, JSON non valido).
- Produces in `prereq.py`:
  - `SUPERPOWERS_RANGE = ((6, 4, 1), (8, 0, 0))`;
  - `GATE_FILES` (decisione 8);
  - `superpowers_version(claude_dir: Path) -> tuple[int, int, int] | None`;
  - `gate_status(repo, ref) -> tuple[list[str], str | None]`: file mancanti e versione;
  - `is_github(repo) -> bool`: legge `git config --get remote.origin.url` **grezzo**, perché `git remote get-url` espande `insteadOf`. La chiave del repo resta ovunque `repo_key(git.origin_url(repo))`, la stessa che usano gli hook;
  - `skill_installed(name: str, *, claude_dir: Path, worktree: Path | None) -> bool` (decisione 16; la usa il Task 6).
- Produces in `housekeeping.py`: `run(conn, state, cfg, *, now) -> list[str]`, che restituisce righe di avviso. Fa:
  - `events.prune_events(events_days)`;
  - `sessions.prune_bound(conn, state, now=now, stale_minutes=...)`: toglie i segnalini delle sessioni non vive e non presenti tra le `sessions` di un lavoro attivo;
  - `backup/.tmp-*` più vecchi di un'ora;
  - `logs/*` e `ctx/*` più vecchi di `retention_days`;
  - `cli/*` più vecchi di un giorno.
- Produces in `start.py`:
  - `StartResult(code: int, lines: list[str], worktree: Path | None, work: int | None)`;
  - `start(state, cwd: Path, issue: int, *, level: str | None, confirm: bool, reopen_execution: bool, claude_dir: Path, now=None) -> StartResult`.

  Codici: 0 = fatto, 1 = rifiuto, 3 = serve conferma (decisione 6). L'ultima riga con codice 0 è `prossimo passo: EnterWorktree <percorso>`.
- CLI: `tollgate start N [--level L1|L2] [--confirm] [--reopen-execution]`. Stampa `lines` ed esce con `code`. La sessione arriva da `cli_session(state, cwd, "start")`.

Ordine dei passi di `start` per un lavoro nuovo (spec 6.1). Ogni rifiuto riporta il motivo:
1. `git.toplevel(cwd)` e il checkout principale (`git.main_worktree`). Se `cwd` non è in un repo git, rifiuto.
2. `gitw.fetch`. Senza rete, al primo avvio, il rifiuto è «senza rete non si avvia un lavoro nuovo».
3. Ramo predefinito (`git.default_branch`). Senza commit, rifiuto. `set_config tollgate.defaultBranch`.
4. `tollgate.toml` su `origin/<predefinito>`: se manca, rifiuto («repo non attivo»). Poi `load_config`.
5. Prerequisiti, ognuno con il suo rifiuto:
   - Superpowers nell'intervallo (decisione 7);
   - `origin` su `github.com`;
   - `gh auth status` con uscita 0;
   - gate installato: un file mancante dà il rifiuto, una versione diversa un avviso.
6. Controlli:
   - checkout principale sporco: avviso;
   - stato del commit predefinito diverso da `success`: chiede conferma;
   - issue chiusa: chiede conferma;
   - `[gate] mode = "detect"`: avviso «modalità rilevazione: il merge non è impedito» più le issue di `sentinel` aperte.
7. Lavoro attivo per (repo, N): si passa alla ripresa (Task 4). Ramo locale `tg/<N>-*`, ramo remoto `tg/<N>-*` o PR da `tg/<N>-*`: rifiuto con `/tollgate:adopt #<N>`.
8. Livello: il massimo tra `--level`, `labels_level(labels, sensitive_labels)` e `L2` se `author_association` non è `OWNER`, `MEMBER` o `COLLABORATOR`.
9. Ramo con `naming.branch_name` (prende i rami locali e remoti). `worktree_add` con `new_branch=True` da `origin/<predefinito>`. Poi `create_work` con `session`, `branch`, `worktree`, `work_base_sha` (SHA di `origin/<predefinito>`) e `gate_mode`, seguito da `db.backup(conn, state, "start")`.
10. Registrazioni:
    - `active.register(state, main, extra=[wt])`;
    - `sessions.mark_bound`;
    - `gitw.add_excludes` (decisione 4);
    - `.tollgate-run/<N>/issue.md` con titolo, etichette e corpo come dato non fidato (spec 6.1);
    - `housekeeping.run`.

- [ ] **Step 1: Test di `naming`** (`tests/test_naming.py::NamingTest`):
  - `slug("Aggiungi l'export CSV!")` == `"aggiungi-l-export-csv"`;
  - `slug("Città più veloce 🚀")` == `"citta-piu-veloce"`;
  - `slug("$(rm -rf ~)")` == `"rm-rf"`;
  - `slug("")` == `"issue"`;
  - `len(slug("a" * 80)) == 40`;
  - `branch_name(7, "Demo", {"tg/7-demo"})` == `"tg/7-demo-2"`;
  - `implementer_name(7, 3)` == `"tg-7-t3"`;
  - `implementer_name(7, 3, 4)` == `"tg-7-t3-r4"`;
  - `implementer_name(7, 3, 2)` == `"tg-7-t3"`.
- [ ] **Step 2: Test di `prereq`** (`tests/test_prereq.py`):
  - `test_superpowers_version_from_registry` (7.0.0 → `(7, 0, 0)`);
  - `test_superpowers_missing_or_malformed` (registro assente o JSON rotto → `None`);
  - `test_gate_status` (repo con i 5 workflow e `VERSION` `0.1.0` → `([], "0.1.0")`; senza `tollgate-run.yml` → quel file è tra i mancanti);
  - `test_skill_installed` (plugin con `skills/x/SKILL.md` → vero; `~/.claude/skills/y/SKILL.md` → vero; skill inesistente → falso).
- [ ] **Step 3: Test di `start`** (`tests/test_start.py::StartNewTest`, con `FlowLab`):
  - `test_start_creates_work_in_path_with_spaces`: `cli("start", "7")` dal checkout principale. Si verificano:
    - uscita 0 e l'ultima riga comincia con `prossimo passo: EnterWorktree`;
    - il ramo `tg/7-<slug>` esiste;
    - il worktree sta sotto `.claude/worktrees/`;
    - senza `--level` e senza etichette sensibili la riga ha `level == "L0"` e `phase == "execution"`; con `start 8 --level L1` su un'altra issue, `level == "L1"` e `phase == "plan"`;
    - `work_base_sha` uguale a `origin/main` e la sessione tra le `sessions`;
    - `bound/sess-flow` esiste;
    - `active/` contiene il worktree;
    - `info/exclude` contiene le tre righe una sola volta anche dopo un secondo `start` su un'altra issue;
    - in `backup/` c'è una copia `*-start.db`.
  - `test_refusals`, uno per sottocaso con il motivo nell'uscita:
    - senza `tollgate.toml` su origin → 1 «non attivo»;
    - senza gate (`FlowLab(gate=False)`) → 1 con il nome del file mancante;
    - Superpowers 6.3.0 → 1;
    - Superpowers 8.0.0 → 1;
    - `gh auth status` che fallisce → 1;
    - origin non GitHub → 1.
  - `test_confirmations`: issue chiusa → 3 con «conferma» e nessuna riga creata; con `--confirm` → 0. Stato del predefinito `failure` → 3.
  - `test_branch_without_row_proposes_adopt`: ramo locale `tg/7-x` → 1 con `/tollgate:adopt #7` e nessun `tg/7-*-2`. Ramo remoto `tg/7-y` → stesso esito.
  - `test_level_from_labels_and_author`: etichetta `security` → L2 (`spec_audit`); `author_association: "NONE"` → L2; `--level L2` → L2.
  - `test_detect_mode_warning`: `mode = "detect"` → la riga «modalità rilevazione» e il titolo dell'issue di `sentinel`.
  - `test_hostile_issue_title_and_body`: titolo `` `$(touch /tmp/PWNED)` ";rm -rf ~" `` e corpo con ```` ``` ```` e `@utente`. Si verificano:
    - ramo `[a-z0-9-]`;
    - `/tmp/PWNED` non esiste;
    - in `issue.md` il recinto è più lungo di ogni sequenza di backtick del corpo;
    - la riga «DATO NON FIDATO» precede il corpo;
    - nessuna chiamata a `fakegh` contiene il titolo.
  - `test_no_session_signal_refuses`: `bin/tollgate start 7` senza segnale → 1 «sessione non riconosciuta».
  - `test_housekeeping`: segnalino `bound/` di una sessione morta tolto, quello di una sessione legata tenuto; `backup/.tmp-x` di 2 ore fa tolto; `ctx/` oltre `retention_days` tolto.
- [ ] **Step 4: Verificare il fallimento**, **Step 5: implementare**, **Step 6: verificare** con `python3 -B -m unittest tests.test_naming tests.test_prereq tests.test_start`, poi `tests/run`.
- [ ] **Step 7: Commit** «tollgate P3a: start su un lavoro nuovo (prerequisiti, worktree, riga, registri, pulizie)».

---

### Task 4: `start` in ripresa

**Files:**
- Modify: `bin/tollgate_flow/start.py`, `bin/tollgate_flow/gitw.py` (`rebase_in_progress(wt) -> bool`, `is_dirty(wt) -> bool`)
- Test: `tests/test_start.py::ResumeTest`

**Interfaces:**
- Consumes: `phases.find_active`, `phases.bind_session`, `phases.set_phase(..., "execution", "start")`, `subagents.running`, `subagents.interrupt`, `sessions.alive`, `sessions.mark_bound`, `effects.get` / tabella `intents` (`state = 'requested'`).
- Produces: un ramo di `start.start` per il lavoro attivo (12.4). Rifiuti ammessi solo per «repo attivo» e «Python». Rete assente, `gh` non raggiungibile, stati non verdi e checkout principale sporco diventano avvisi.

Comportamento:
- **Worktree assente:**
  - con il ramo locale presente, `worktree_add(new_branch=False)`;
  - senza ramo, `worktree_add(new_branch=True, start_point=work_base_sha)`;
  - aggiorna `work_items.worktree` se il percorso è cambiato, con una funzione nuova `phases.set_worktree(conn, work, path, *, now)`.
- **Rebase in corso:** avviso con «`git -C <wt> rebase --abort`» proposto, senza eseguirlo.
- **Worktree sporco:** avviso e proposta di un commit di lavoro in corso.
- **Subagenti `running` di sessioni non vive:** `interrupt`.
- **Intenti `requested`:** codice 3 con l'elenco; si procede solo con `--confirm`.
- **Un'altra sessione viva tra le `sessions`:** codice 3, si procede con `--confirm` (12.4).
- **Legame:** `bind_session`, `mark_bound`, `active.register`.
- **Fase `review` o `pr_open`:** riga «fase X: per correggere rilancia con `--reopen-execution`» (decisione 19). Con il flag, `set_phase(execution, start)`.

- [ ] **Step 1: Test** (`ResumeTest`):
  - `test_resume_recreates_missing_worktree`: rimosso con `git worktree remove --force` → ricreato sullo stesso ramo, uscita 0;
  - `test_resume_without_branch_starts_from_base`: ramo e worktree assenti → ramo ricreato su `work_base_sha`;
  - `test_resume_dirty_worktree_proposes_commit` (criterio 28);
  - `test_resume_offline_and_dirty_main_are_warnings` (origin rinominato: `fetch` falso → uscita 0 con due avvisi; criterio 28);
  - `test_two_live_sessions_need_confirmation` (sessione B toccata 1 minuto fa, `start` da A → 3; con `--confirm` → 0, ed entrambe in `sessions`);
  - `test_second_session_does_not_interrupt_live_implementer` (implementatore `running` di B viva → resta `running`; criterio 28);
  - `test_dead_session_implementer_interrupted_task_pending`;
  - `test_pending_intent_needs_confirmation`;
  - `test_reopen_execution_from_review`;
  - `test_rebase_in_progress_warns`, con un rebase in conflitto preparato a mano nel worktree.
- [ ] **Steps 2-5**: fallimento, implementazione, verifica (`python3 -B -m unittest tests.test_start`), `tests/run`, commit «tollgate P3a: start in ripresa (12.4)».

---

### Task 5: Analisi pura: testo del task, brief, instradamento, dimensione

**Files:**
- Modify: `bin/tollgate_analysis/plan.py`, `bin/tollgate_analysis/profiles.py`
- Create: `bin/tollgate_analysis/brief.py`, `bin/tollgate_analysis/size.py`
- Modify: `bin/tollgate_checks/subagent_stop.py` (usa `size.task_lines`; `_GENERATED` si sposta in `size.GENERATED`)
- Test: `tests/test_plan.py`, `tests/test_profiles.py`, `tests/test_brief.py`, `tests/test_size.py`

**Interfaces:**
- Produces in `plan.py`:
  - `task_text(text: str, number: int) -> str | None`: il testo da `### Task <number>` all'intestazione `###` o `##` successiva, esclusa. I recinti si rispettano: un `###` dentro un blocco di codice non chiude il task.
  - Correzioni del parser:
    - una riga `- Create: a.py, b.py` o `` - Modify: `a.py`, `b.py` `` porta tutti i file;
    - recinti `~~~` e di 4 o più backtick, chiusi solo dallo stesso marcatore di lunghezza ≥;
    - `**M1.** testo — test: id` riconosciuto;
    - ID di must-have duplicati → problema «M1 duplicato»;
    - numeri di task duplicati → problema.
- Produces in `profiles.py`: `Routing(implementer: str, reviewer: str, skills: list[str], reviewer_skills: list[str], split_candidate: bool)` e `task_routing(files, profiles: dict[str, dict]) -> Routing` (decisione 15). Costanti `DEFAULT_IMPLEMENTER = "tollgate:implementer"` e `DEFAULT_REVIEWER = "tollgate:task-reviewer"`.
- Produces in `size.py`: `GENERATED` (i quattro pattern oggi in `subagent_stop`) e `task_lines(changes, lockfiles) -> int`.
- Produces in `brief.py`:
  - `fence(text) -> str`: un recinto più lungo di ogni sequenza di backtick del testo;
  - `ImplBrief(issue, task, name, agent_type, model_hint, task_text, scope, related_tests, must_haves, skills, absent_skills, verify_cmd, fix_findings, fix_round)`;
  - `implementer_brief(b: ImplBrief) -> str`. Il testo contiene nell'ordine: intestazione con lavoro, task e `name`; il testo del task in un recinto; scope; test correlati (R2); must-have collegati; skill da usare con `(assente)`; per un giro di correzione, i rilievi da correggere in un recinto; istruzioni fisse (TDD, commit, `<verify_cmd>` prima di DONE, `block open test_spec_conflict`, report JSON di 18.5).
  - `ReviewBrief(issue, task, sha, code, base, head, brief_path, diff_path, lines, lines_warn, lines_max, concerns, reviewer_skills, standard: bool)`;
  - `review_brief(b: ReviewBrief) -> str`. Contiene la riga del verdetto con `sha` e `code` alla lettera, l'avviso di dimensione oltre `lines_warn`, i dubbi di DONE_WITH_CONCERNS in un recinto e, con `standard`, lo standard di 8.6.

- [ ] **Step 1: Test** (`test_plan.py::TaskTextTest`):
  - `test_task_text_stops_at_next_task`;
  - `test_task_text_ignores_headings_in_fences`;
  - `test_multiple_files_on_one_line`;
  - `test_tilde_and_long_fences`;
  - `test_bold_must_have`;
  - `test_duplicate_must_have_and_task_ids`;
  - `test_existing_cases_unchanged` (rilanciare la suite `PlanCheckTest` esistente: deve restare verde).
- [ ] **Step 2: Test** (`test_profiles.py::RoutingTest`):
  - profilo `web` (`paths=["web/**"]`, `agent="probe:implementer-frontend"`, `reviewer="probe:reviewer-frontend"`, `skills=["ui-ux-pro-max"]`): task su `web/a.tsx` → quei due agenti e `skills == ["ui-ux-pro-max"]` (criterio 38);
  - task su `web/a.tsx` e `api/b.py`, con `api` che ha `agent="probe:implementer-backend"` → `tollgate:implementer`, `tollgate:task-reviewer`, unione delle skill e `split_candidate`;
  - profilo `cross` `a11y` (`reviewer_skills=["axe"]`) elencato in `web.cross` → `"axe" in reviewer_skills`;
  - quattro skill → tre e `split_candidate`;
  - nessun profilo → generici.
- [ ] **Step 3: Test** (`test_brief.py`):
  - `test_fence_longer_than_content`;
  - `test_implementer_brief_has_name_verify_and_report_fields` (contiene `tg-7-t2`, il comando di verifica, «18.5» e ognuno dei campi `REQUIRED` di `report.py`);
  - `test_absent_skill_marked`;
  - `test_fix_brief_includes_findings_in_fence`;
  - `test_review_brief_has_sha_code_and_size_warning` (righe 250 con warn 200 → l'avviso c'è; righe 50 → non c'è).
- [ ] **Step 4: Test** (`test_size.py`): lockfile e `dist/` esclusi; somma `added + removed`. `tests.test_check_subagent_stop` resta verde.
- [ ] **Steps 5-7**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: analisi del task (testo, brief, instradamento, dimensione), plan.py corretto».

---

### Task 6: `task start` e i giri di correzione

**Files:**
- Modify: `bin/tollgate_core/db.py` (migrazione 3, decisione 9), `bin/tollgate_core/tasks.py`, `bin/tollgate_core/git.py` (`blob_text`)
- Modify: `bin/tollgate_hooks/apply.py` (`_subagent_start` passa il numero alla ripresa)
- Create: `bin/tollgate_flow/taskcmd.py`
- Modify: `bin/tollgate_core/cli.py` (sottocomando `task`)
- Test: `tests/test_db.py`, `tests/test_tasks.py`, `tests/test_taskcmd.py`, `tests/test_check_agents.py`

**Interfaces:**
- Produces in `tasks.py`:
  - `assign(..., reviewer_type=None, ...)`: un `reviewer_type` `None` non sovrascrive il valore esistente (`coalesce`);
  - `take_pending(conn, work, *, agent_type, resume, number=None) -> int | None`: con `number` cerca solo quel task;
  - `reserve(conn, work, number, *, now) -> None` e `clear_reservation(conn, work, number)`;
  - `set_skills_required(conn, work, number, skills: list[str]) -> None`;
  - `set_review_prep(conn, work, number, *, sha, code) -> None`;
  - `set_verdict(conn, work, number, *, outcome: str, findings: list[dict], now, session=None) -> None`: `outcome` ∈ (`approved`, `changes`), stato invariato, evento `task_change`.
- Produces in `git.py`: `blob_text(repo, sha) -> str | None` (decisione 20).
- Produces in `taskcmd.py`:
  - `TaskError(Exception)`;
  - `task_start(state, cwd, number: int, *, fix: bool, claude_dir: Path, now=None) -> tuple[Path, str]`: restituisce il percorso del brief e un riepilogo di una riga, con il tipo di agente, il `name`, l'eventuale `model: inherit` e se si lancia o si riprende.
- Comportamento di `task_start`:
  - Lavoro: `sessions.work_for_path(cwd)`. Fase `execution`, livello L1 o L2: in L0 rifiuto «in L0 lavora la sessione principale».
  - Senza `--fix` il task deve essere `pending`. Con `--fix`, `review` con verdetto `changes`; al quinto giro rifiuto e `needs_you` (decisione 18).
  - Piano a `plan_sha` (decisione 20), poi `plan.task_text`, i file del task da `check_plan` e il `Routing`.
  - Skill assenti tolte con `set_skills_required` (decisione 16).
  - Brief scritto in `.tollgate-run/<N>/task-<k>.md`, oppure `task-<k>-fix-<giro>.md` per `--fix`.
  - `tasks.task_event(start)` per `pending`, oppure `fix` per `--fix`.
  - `tasks.assign(implementer=<nome>, agent_type=<routing>, pending=launch|resume, reviewer_type=<routing>)`.
  - Test correlati: le voci `Test:` del task e i test dei must-have collegati (riga `Must-have:`, altrimenti tutti).
- CLI: `tollgate task start <k> [--fix]`. Stampa il percorso del brief e il riepilogo, esce con 0. `TaskError` esce con 1.

- [ ] **Step 1: Test** (`test_db.py::MigrationV3Test`):
  - DB v2 con righe in `tasks` → dopo `open_db` le colonne nuove esistono, i dati restano, la copia `*migrazione-3*` c'è;
  - DB nuovo → nessuna copia.
- [ ] **Step 2: Test** (`test_tasks.py`):
  - `test_assign_keeps_reviewer_type`;
  - `test_take_pending_by_number` (due task `resume` dello stesso tipo → `number=2` prende il 2);
  - `test_set_verdict_keeps_state`;
  - `test_reserve_and_clear`.
- [ ] **Step 3: Test** (`test_taskcmd.py`, con `FlowLab` dopo `start` e un piano L1 registrato tramite il hook `post_edit`, come in `test_check_post_edit`):
  - `test_task_start_writes_brief_and_assigns`: brief con `tg-7-t1`; `tasks` con `state running`, `pending launch`, `implementer tg-7-t1`, `agent_type tollgate:implementer`;
  - `test_task_start_only_from_pending`;
  - `test_profile_agent_chosen` (profilo `web`; criterio 38);
  - `test_fix_rounds_counted` (tre volte verdetto `changes` e `--fix` → `fix_rounds == 3` e `pending resume` con lo stesso nome; criterio 4);
  - `test_rounds_four_five_new_implementer` (giro 4 → `tg-7-t1-r4`, `pending launch`, riepilogo con `model: inherit`);
  - `test_sixth_fix_opens_needs_you`;
  - `test_absent_skill_removed_from_required`;
  - `test_plan_changed_after_registration_refuses`;
  - `test_l0_refuses`.
- [ ] **Step 4: Test** (`test_check_agents.py::ResumeTaskTest`):
  - `test_resume_takes_its_own_task`: due task in `resume` dello stesso tipo; `SubagentStart` di ripresa per l'agente del task 2 → resta associato al 2;
  - `test_resumed_implementer_keeps_fingerprint`: il rinviato del Task 19 di P2.
- [ ] **Steps 5-7**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: task start e giri di correzione; migrazione 3».

---

### Task 7: `task review-prepare`, verdetto del revisore, `task done`, prenotazione

**Files:**
- Create: `bin/tollgate_analysis/verdicts.py`, `bin/tollgate_checks/task_verdict.py`
- Modify:
  - `bin/tollgate_flow/taskcmd.py`;
  - `bin/tollgate_checks/_common.py` (`awaiting_review`, `fingerprint_changed` spostata da `subagent_stop`);
  - `bin/tollgate_checks/subagent_stop.py` (salta i revisori in attesa; registra il report del messaggio finale);
  - `bin/tollgate_checks/agents.py` (prenotazione);
  - `bin/tollgate_hooks/apply.py` (`task_reserve`, `task_verdict`);
  - `bin/tollgate_core/cli.py`.
- Test: `tests/test_verdicts.py`, `tests/test_check_task_verdict.py`, `tests/test_taskcmd.py`, `tests/test_check_agents.py`

**Interfaces:**
- Produces in `verdicts.py`:
  - `TaskVerdict(valid: bool, problems: list[str], outcome: str | None, declared: str | None, findings: list[dict], dropped: int)`;
  - `parse_task_verdict(text: str | None, *, task: int, sha: str, code: str, standard: bool) -> TaskVerdict`: cerca l'ultimo oggetto JSON con `outcome`, come `report._candidates`, e applica la decisione 10.
- Produces in `taskcmd.py`:
  - `review_prepare(state, cwd, number, *, now=None) -> Path`. Il task deve essere in `review`. Range: dal genitore del primo SHA di `tasks.commits` all'ultimo. Senza commit, rifiuto. Scrive:
    - `.tollgate-run/<N>/review-<k>.diff`, con `git log --oneline`, `--stat` e `diff -U10` del range;
    - `.tollgate-run/<N>/review-<k>.md`, con `brief.review_brief`, il codice da `secrets.token_hex(4)` e lo SHA uguale all'ultimo commit;
    - `set_review_prep`.

    Il report dell'implementatore viene da `subagents.report` dell'ultimo implementatore del task e passa come dubbi se dice `DONE_WITH_CONCERNS`.
  - `task_done(state, cwd, number, *, now=None) -> str`: rifiuta senza `verdict == approved` e senza `review_sha == tasks.commits[-1]`. Con un commit dopo la revisione rifiuta con «serve una nuova revisione». Altrimenti `task_event(approved)`.
- Produces in `_common.py`:
  - `awaiting_review(ctx, row) -> tuple | None` restituisce `(work, task)` se `row["type"]` è il `reviewer_type` di un task del lavoro in `review` con `review_code` non nullo; il lavoro si trova da `row["work"]`, oppure da `governing_work(ctx, ctx.event.cwd)`;
  - `fingerprint_changed(ctx, row, wt) -> bool`.
- Produces: modulo `task_verdict` (evento `subagent_stop`, ordine 15, componente `None`). Per un revisore in attesa:
  - con `readonly_check` acceso e l'impronta cambiata: `subagent_finish(tampered)` più `needs_you`;
  - con il verdetto valido: `task_verdict(work, number, outcome, findings)` più `subagent_finish(done)`;
  - con il verdetto non valido: veto con i problemi (uscita 2), e dopo 2 veti `subagent_finish(done)` più `needs_you` «verdetto del revisore non valido».

  Il messaggio viene da `last_assistant_message`, o da `subagents.report` (auto mode).
- Produces: in `subagent_stop.decide`:
  - prima del ramo di sola lettura, `if _common.awaiting_review(ctx, row): return []`;
  - per gli implementatori, quando c'è `last_assistant_message`, un `record("subagent_report", ...)` in testa alle decisioni, così `review-prepare` ha i dubbi anche in modalità manuale.
- Produces: in `agents.decide`, quando ammette l'implementatore: con `reserved_at` del task più recente di 120 s → `deny("lancio già in corso per il task k", rule="writer")`; altrimenti `record("task_reserve", work=..., number=...)`. `apply._subagent_start` chiama `tasks.clear_reservation` sul task preso.
- CLI: `tollgate task review-prepare <k>` stampa il percorso del brief del revisore. `tollgate task done <k>`.

- [ ] **Step 1: Test** (`test_verdicts.py`):
  - `test_valid_approved`;
  - `test_minor_only_changes_becomes_approved_with_standard` (criterio 40);
  - `test_minor_only_changes_kept_without_standard`;
  - `test_finding_without_rule_dropped` (criterio 40);
  - `test_spec_compliance_forces_changes`;
  - `test_verdict_validity_matrix`, un sottocaso per: SHA diverso, codice diverso, task diverso, JSON assente, JSON malformato, `outcome` sconosciuto. Tutti danno `valid` falso.
- [ ] **Step 2: Test** (`test_check_task_verdict.py`, `hookkit.Lab` con il task in `review` e la preparazione fatta):
  - `test_approved_recorded_and_row_closed`;
  - `test_invalid_verdict_vetoes_twice_then_needs_you`;
  - `test_tampering_reviewer_verdict_ignored` (file cambiato durante la revisione → `tampered`, `needs_you`, verdetto non registrato);
  - `test_implementer_cannot_deliver_verdict` (stesso JSON da `tollgate:implementer` → nessun `task_verdict`);
  - `test_handback_report_used_in_auto_mode`;
  - `test_reviewer_standard_component_off` (criterio 18).
- [ ] **Step 3: Test** (`test_taskcmd.py::ReviewDoneTest`):
  - `test_review_prepare_writes_diff_and_code`;
  - `test_done_requires_approved_on_last_sha` (senza verdetto → rifiuto, criterio 4; con verdetto `approved` → `done`; commit dopo il verdetto → rifiuto);
  - `test_concerns_reach_review_brief`.
- [ ] **Step 4: Test** (`test_check_agents.py::ReservationTest`): `test_second_launch_in_same_message_denied` (due `PreToolUse Agent` di fila → il secondo 2); `test_reservation_expires_after_120s`.
- [ ] **Steps 5-7**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: review-prepare, verdetto del revisore del task, task done, prenotazione del lancio».

---

### Task 8: `act apply` per `resolve` e `approve level`

**Files:**
- Create: `bin/tollgate_flow/actapply.py`
- Modify: `bin/tollgate_core/phases.py` (`set_level_cap`), `bin/tollgate_core/cli.py` (sottocomando `act apply`)
- Test: `tests/test_phases.py`, `tests/test_actapply.py`

**Interfaces:**
- Produces in `phases.py`: `set_level_cap(conn, work, cap: str, reason: str, cap_paths: list[str], *, now, session=None) -> None` (decisione 14). Solleva `TransitionError` se la fase corrente, o `phase_before_block` per `blocked`, non è nella sequenza di `cap`. Abbassa `level` a `cap` se è più alto (evento `level_change` con `{"from", "to", "cause": "cap"}`) e scrive `level_cap`, `level_cap_reason` e `level_cap_paths` (JSON).
- Produces in `actapply.py`:
  - `APPLIERS: dict[tuple[str, str | None], Callable]`, con chiavi `("resolve", None)` e `("approve", "level")`;
  - `ActApplyError(Exception)`;
  - `apply_act(state, cwd, act_id: str | None, *, now=None) -> str`.
- Comportamento di `apply_act`:
  - Sessione con `cli_session(state, cwd, "act")`. Lavoro con `sessions.work_for_path(cwd)`.
  - Atto: quello indicato, oppure l'ultimo `pending` della sessione con chiave in `APPLIERS`. Deve essere della sessione, del lavoro, non scaduto e con chiave applicabile.
  - `acts.consume(...)` nella stessa sequenza, poi l'applicatore.
  - `resolve <id>`: `close_block` con la nota (`args[1:]` unite); se l'id non è un blocco aperto del lavoro, rifiuto. Quando la fase esce da `blocked`, ogni task `blocked` riceve `unblocked`.
  - `resolve writer`: `interrupt` sugli implementatori `running` del lavoro.
  - `approve level <L> <motivo>`: `cap_paths = level.sensitive_in(<percorsi del diff dalla base, compresi old_path>, sensitive_paths)`, poi `set_level_cap`.
- CLI: `tollgate act apply [<id>]`.

- [ ] **Step 1: Test** (`test_phases.py::LevelCapTest`):
  - `test_cap_lowers_level_and_records_paths`;
  - `test_cap_refused_when_phase_not_in_target_sequence` (L2 in `spec_audit` → L1 rifiutato);
  - `test_cap_in_blocked_uses_phase_before_block`.
- [ ] **Step 2: Test** (`test_actapply.py`, `FlowLab` più `hookkit` per registrare l'atto con `UserPromptExpansion`):
  - `test_resolve_closes_block_and_unblocks_tasks`;
  - `test_resolve_writer_interrupts`;
  - `test_approve_level_cap_holds_until_new_sensitive_path` (dopo il tetto il ricalcolo di `post_edit` non rialza per un file non sensibile, e rialza per `src/auth/x.py`; criterio 22);
  - `test_act_of_other_session_or_expired_refused`;
  - `test_act_consumed_once` (secondo `act apply` sullo stesso id → rifiuto);
  - `test_unknown_act_type_refused` (`approve waiver` → «non si applica con act apply»).
- [ ] **Steps 3-5**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: act apply (resolve, resolve writer, approve level)».

---

### Task 9: `status --checkpoint`, tetto che ha fermato il lavoro, sola lettura di `status`

**Files:**
- Create: `bin/tollgate_flow/checkpoint.py`
- Modify: `bin/tollgate_core/cli.py` (`status --checkpoint [--note TESTO]`; `status` senza DB non lo crea), `bin/tollgate_core/stats.py` (eventi senza lavoro nei conteggi globali)
- Test: `tests/test_checkpoint.py`, `tests/test_cli.py`, `tests/test_stats.py`

**Interfaces:**
- Produces in `checkpoint.py`:
  - `CAPS`: prefissi dei motivi dei blocchi, `"budget superato"` → `"budget del task"` e `"giri di correzione esauriti"` → `"giri di correzione"`; P3b aggiunge i cicli di revisione;
  - `stopped_by(conn, work) -> list[str]`: per i blocchi aperti che corrispondono a un prefisso, «tetto: <nome> (blocco <id>)»;
  - `next_step(conn, work) -> str`: il primo task non `done` con il suo stato e il comando successivo (`task start k`, `task review-prepare k`, `task done k`); con tutti i task `done`, «`/tollgate:finish`»;
  - `write_checkpoint(state, cwd, *, note: str | None, now=None) -> Path`. Scrive `docs/superpowers/reviews/<N>/checkpoint.md` nel worktree con fase, livello, piano e `plan_sha`, task per stato, `stopped_by`, prossimo passo e note. Le note precedenti si conservano, le ultime 5. Scrittura con tmp più `os.replace`.
- Produces in `cli.py`: `status` stampa anche `stopped_by`, nel JSON (chiave `stopped_by`) e nel testo. Se `state.db_path` non esiste stampa «nessun lavoro attivo» senza creare nulla.
- Produces in `stats.py`: i conteggi globali (`work=None`) comprendono anche gli eventi con `work` nullo (veti, blocchi); `phase_hours` resta per lavoro.

- [ ] **Step 1: Test**:
  - `test_checkpoint.py`:
    - `test_checkpoint_written_and_ignored_by_git` (`git status --porcelain` nel worktree vuoto dopo la scrittura, grazie all'exclude);
    - `test_next_step_sequence`;
    - `test_notes_kept_last_five`;
    - `test_stopped_by_budget_and_rounds` (criterio 39: «`status` dice quale tetto»);
    - `test_session_start_injects_checkpoint` (con `hookkit`: dopo `write_checkpoint`, `SessionStart` contiene «prossimo passo»).
  - `test_cli.py::StatusReadOnlyTest::test_status_without_db_creates_nothing`.
  - `test_stats.py::GlobalTest::test_vetoes_without_work_counted`.
- [ ] **Steps 2-4**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: checkpoint, tetto che ha fermato il lavoro, status in sola lettura».

---

### Task 10: Agenti, skill, manifest e licenze

**Files:**
- Create: `agents/implementer.md`, `agents/task-reviewer.md`
- Create: `skills/start/SKILL.md`, `skills/execute/SKILL.md`, `skills/status/SKILL.md`, `skills/approve/SKILL.md`, `skills/resolve/SKILL.md`, `skills/setup/SKILL.md`
- Create: `.claude-plugin/marketplace.json`, `LICENSE`, `LICENSES/superpowers-MIT.txt`
- Modify: `.claude-plugin/plugin.json`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: gli esiti V1 e V4 del Task 1; i sottocomandi dei Task 3-9.
- Produces: i nomi `tollgate:implementer` e `tollgate:task-reviewer`, che `profiles.DEFAULT_*` già usa.

Contenuti (testo in italiano, identificatori in inglese):

**`agents/implementer.md`**
- Frontmatter: `name: implementer`, `description` (implementatore di un task del piano lanciato da `tollgate:execute`), `tools: Read, Edit, Write, Bash, Grep, Glob, Skill`, `model: inherit`, `maxTurns: 60`.
- Corpo derivato da `implementer-prompt.md` di Superpowers 7.0.0, con in testa la riga di attribuzione «Derivato da superpowers/skills/subagent-driven-development (MIT, © 2025 Jesse Vincent); vedi LICENSES/superpowers-MIT.txt». Le sezioni:
  - leggere prima il brief indicato nel prompt;
  - fare domande prima di cominciare;
  - lavoro in TDD;
  - mai lanciare subagenti;
  - organizzazione del codice e quando fermarsi;
  - autorevisione;
  - le skill del brief da invocare con lo strumento Skill, più `superpowers:test-driven-development` e `superpowers:systematic-debugging` quando servono;
  - prima di DONE: commit e `tollgate verify` green;
  - conflitto tra test e specifica: `tollgate block open test_spec_conflict --reason …` e BLOCKED;
  - messaggio finale con **un solo** blocco JSON di 18.5, con i campi alla lettera, e `size_reason` oltre `task_lines_max`.

**`agents/task-reviewer.md`**
- Frontmatter: `name: task-reviewer`, `tools: Read, Grep, Glob, Bash`, `model: sonnet`.
- Corpo derivato da `task-reviewer-prompt.md`, con la stessa riga di attribuzione:
  - leggere il brief del revisore, il brief del task e il file del diff indicati;
  - sola lettura, mai lanciare subagenti;
  - non fidarsi del report;
  - parte 1, aderenza; parte 2, qualità;
  - standard del revisore (8.6): approvare se il cambiamento migliora la salute del codice; solo `blocker` e `major` chiedono modifiche; ogni rilievo con `file`, `line` e `rule` (`R-…` o il passo del piano), altrimenti non vale; cercare difetti, non confermare;
  - chiusura con **un solo** blocco JSON del revisore del task di 18.5, con `sha` e `code` copiati dal brief.

**`skills/start/SKILL.md`** (anche il modello)
- Frontmatter: `name: start`, `description`, `argument-hint: "#N [L1|L2]"`.
- Corpo:
  - lanciare `<programma> start <N> [--level L]` dal checkout principale;
  - uscita 3: mostrare all'utente gli avvisi e chiedere; solo con il suo sì rilanciare con `--confirm`;
  - uscita 0: `EnterWorktree` con il percorso dell'ultima riga; se non riesce, dire «cd <percorso> && claude» e fermarsi;
  - poi, per livello:
    - L0: implementa la sessione;
    - L1: checkpoint (`status --checkpoint`), `/clear` e writing-plans con le intestazioni di 7.5;
    - L2: brainstorming, fermarsi dopo la spec (P3c);
  - writing-plans chiude con un rimando a subagent-driven-development: si usa invece `/tollgate:execute` (6.3).

**`skills/execute/SKILL.md`** (anche il modello). Il ciclo di 6.3, derivato dal processo di subagent-driven-development con la riga di attribuzione:
- Passo 0: controllo del piano (task che si contraddicono, file condivisi) annotato con `status --checkpoint --note`.
- Per ogni task non `done`, in ordine:
  - `task start k`;
  - `Agent` con `subagent_type` = tipo del riepilogo, `name` = quello del riepilogo, in primo piano, prompt = percorso del brief; `model` solo se il riepilogo lo indica;
  - alla risposta, `task review-prepare k`;
  - `Agent` del revisore con il percorso del brief del revisore;
  - con `approved`: `task done k`;
  - con `changes`: `task start k --fix`. Giri 1-3: `SendMessage` al `name` con il percorso del file dei rilievi. Giri 4-5: un nuovo `Agent` con il nome `-r<giro>` e `model: inherit`.
  - Con NEEDS_CONTEXT si risponde riprendendo lo stesso implementatore.
  - Con BLOCKED, o un veto di budget, ci si ferma, si riferisce all'utente e si indica `/tollgate:resolve`.
- Guardia del contesto: all'avviso di `warn_pct` si scrive il checkpoint; a `stop_pct`, checkpoint, `/clear` e ripresa dal primo task non chiuso.
- Fine dei task: `/tollgate:finish`.
- Mai subagent-driven-development, mai implementatori `general-purpose`.

**Altre skill**
- **`skills/status/SKILL.md`**: `<programma> status` (sola lettura) e `stats --work N` su richiesta.
- **`skills/approve/SKILL.md`** (`disable-model-invocation: true`): l'atto è già registrato dal hook.
  - Per `level`, lanciare `<programma> act apply` e riferire.
  - Per `waiver` ed `effect`, dire che l'approvazione vale già e non lanciare nulla.
  - Per gli altri oggetti: «arriva con /tollgate:finish (P3b) o con il percorso L2 (P3c)».
- **`skills/resolve/SKILL.md`** (`disable-model-invocation: true`): `<programma> act apply` e riferire la fase.
- **`skills/setup/SKILL.md`** (`disable-model-invocation: true`): leggere `~/.claude/settings.json` senza modificarlo e mostrare la modifica di `statusLine.command` (decisione 21). Se c'è già una statusline, proporre `"<radice>/statusline/ctx <comando attuale>"`, altrimenti `"<radice>/statusline/ctx <radice>/statusline/statusline.sh"`. La modifica la fa l'utente: il file è protetto.

Ogni skill indica il programma come `${CLAUDE_PLUGIN_ROOT}/bin/tollgate` oppure con la riga «programma» (esito V1).

**Manifest e licenze**
- `plugin.json`: aggiungere `"author": {"name": "sAInapse"}` e `"license": "MIT"`. `dependencies` resta senza `version`.
- `marketplace.json`: `name: "sainapse"`, `owner: {"name": "sAInapse"}`, `plugins: [{"name": "tollgate", "source": "./", "description": …}]`, `allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]`, oppure i campi che V4 ha indicato come validi.
- `LICENSE`: MIT, «Copyright (c) 2026 sAInapse».
- `LICENSES/superpowers-MIT.txt`: copia del LICENSE di Superpowers 7.0.0.

- [ ] **Step 1: Test** (`test_manifest.py`, aggiunte):
  - `test_agents_frontmatter`: parser minimo del frontmatter YAML, solo `chiave: valore`. `implementer` ha `maxTurns: 60`, `model: inherit` e i 7 strumenti; `task-reviewer` ha `model: sonnet` e non ha `Edit` né `Write`; entrambi hanno la riga di attribuzione.
  - `test_user_only_skills` (`approve`, `resolve`, `setup`, `off`, `on` → `disable-model-invocation: true`; `start`, `execute`, `status` → no).
  - `test_skills_never_mention_sdd_as_executor` (`execute` contiene `/tollgate:finish` e «mai subagent-driven-development»).
  - `test_plugin_and_marketplace_json` (author, license, nessun `version` nelle dipendenze, `allowCrossMarketplaceDependenciesOn`).
  - `test_license_files`.
  - `test_brief_fields_match_agent_text`: ogni campo `REQUIRED` di `report.py` compare in `implementer.md`; i campi del revisore di 18.5 compaiono in `task-reviewer.md`.
- [ ] **Step 2: Fallimento**, **Step 3: scrivere i file**, **Step 4: verificare** con `tests/run`. Se `claude` è disponibile, `claude plugin validate .` deve dare successo (passo manuale, esito nel report).
- [ ] **Step 5: Commit** «tollgate P3a: agenti implementer e task-reviewer, skill del flusso, marketplace e licenze».

---

### Task 11: Statusline e file del contesto

**Files:**
- Create: `statusline/ctx` (eseguibile, bash)
- Test: `tests/test_statusline.py`

**Interfaces:**
- Produces: `statusline/ctx [comando…]` (decisione 21):
  - legge tutto stdin;
  - ricava `session_id` e `context_window.used_percentage` con `python3 -c`, perché `jq` può mancare. Se non c'è Python cerca solo le due chiavi con `sed`, senza mai fallire;
  - scrive in modo atomico `<stato>/ctx/<session_id>.json` = `{"used_pct": <numero o null>}`. `<stato>` è `$TOLLGATE_STATE` solo se contiene `.tollgate-test`, altrimenti `~/.local/state/tollgate`;
  - esegue il comando passato con lo stesso stdin e ne restituisce l'uscita; senza comando non stampa nulla;
  - un `session_id` che non rispetta `^[A-Za-z0-9_-]+$` non scrive nulla.

- [ ] **Step 1: Test** (`test_statusline.py`):
  - `test_writes_used_pct` (input con `session_id: "s1"` e `used_percentage: 42` → `{"used_pct": 42}`);
  - `test_null_when_missing`;
  - `test_passes_stdin_to_wrapped_command` (comando `cat` → stdout uguale all'input);
  - `test_unsafe_session_ignored`;
  - `test_state_without_sentinel_not_used` (HOME temporanea);
  - `test_context_guard_reads_it` (con `hookkit.Lab`: dopo `ctx` con 60%, `PreToolUse Agent` → 2 con «contesto»; criterio 8).
- [ ] **Steps 2-4**: fallimento, implementazione, `tests/run`, commit «tollgate P3a: statusline/ctx scrive il file del contesto».

---

### Task 12: Minori rinviati del motore

**Files:**
- Modify: `bin/tollgate_core/phases.py`, `bin/tollgate_core/verify.py`, `bin/tollgate_checks/_common.py`, `bin/tollgate_checks/bash_rules.py`
- Test: `tests/test_phases.py`, `tests/test_verify.py`, `tests/test_check_bash.py`, `tests/test_check_common.py`

**Interfaces:**
- `phases.bind_session` e `phases.set_level` su un lavoro `closed` → `TransitionError("il lavoro è chiuso")`. Il runner già trasforma questo errore in un avviso.
- `verify._run_one`: `os.killpg` del gruppo anche a fine normale, ignorando `ProcessLookupError`, così nessun figlio in background sopravvive.
- `_common.waiver_hint(v)` ed `explain(violations)` senza il parametro `issue`, con i chiamanti aggiornati.
- `bash_rules`: il messaggio di `rm -rf` fuori dal repo aggiunge «usa `rm -r` senza `-f`, oppure un percorso dentro il worktree».

- [ ] **Step 1: Test**:
  - `test_phases.py::ClosedWorkTest::test_bind_and_set_level_refuse_closed`;
  - `test_verify.py::VerifyRunTest::test_background_child_killed_after_success` (comando `sleep 30 & echo ok` con report vuoto → dopo `verify` il pid del figlio non esiste);
  - `test_check_bash.py::test_rm_rf_outside_message_suggests_alternative`.
- [ ] **Steps 2-4**: fallimento, correzioni, `tests/run`, commit «tollgate P3a: minori rinviati (lavori chiusi, killpg, messaggi)».

---

### Task 13: Prova reale del flusso con `claude -p`

Una sola esecuzione reale del percorso skill → CLI → hook → agenti, su un repo locale. Non si usano repo GitHub. Chiude i rischi che i test unitari non vedono: frontmatter, nomi degli agenti, `EnterWorktree`, iniezioni, segnale della CLI.

**Files:**
- Create: `spikes/run-p3a-flow.sh`, `docs/verifiche/2026-10-16-p3a-prova-flusso.md`

**Regole di cautela (vanno nel brief):**
- tutto in `/tmp/tollgate-p3a/flow`;
- `TOLLGATE_STATE=/tmp/tollgate-p3a/flow/state` con la sentinella;
- `TOLLGATE_GH=<repo>/tests/fakegh.py` con dati che dichiarano l'issue 1 aperta e lo stato del predefinito `success`;
- `HOME` resta quella vera (serve l'autenticazione di `claude`), ma nessun comando scrive sotto `~/.claude`;
- `claude -p --plugin-dir <worktree del ramo> --model sonnet`;
- mai `claude plugin install`;
- il repo di prova ha `remote.origin.url = https://github.com/prova/flow.git` e `url.<repo nudo locale>.insteadOf` su quell'URL, come `FlowLab`: il fetch va al repo nudo e `prereq.is_github` legge l'URL grezzo. Nessun push.

- [ ] **Step 1: Script** `spikes/run-p3a-flow.sh`. Prepara:
  - il repo con `tollgate.toml` (L1, `verify = "python3 -m unittest"` con un report JUnit finto, oppure `allow_no_tests` come serve);
  - i 5 workflow vuoti e `.github/tollgate/VERSION`;
  - un piano L1 di un task già scritto in un file fuori dal repo.

  Poi lancia in sequenza, con `--continue`:
  1. `/tollgate:start #1 L1`;
  2. «scrivi il piano copiando <file> in docs/superpowers/plans/2026-10-16-prova.md»;
  3. `/tollgate:execute`.

  Registra stdout e log degli hook (`hooks.log`, eventi del DB con `bin/tollgate events`).
- [ ] **Step 2: Eseguire.** Esito atteso: task 1 `done` e un verdetto `approved` nei `task_change`. Ogni passo che si ferma si annota con l'evento o il messaggio che l'ha fermato. Si ripete una volta dopo una correzione **solo** se la causa è un difetto di questo piano, con un commit di correzione e un test che lo copre. Un esito non ottenuto si scrive «non riuscito», con la causa, e diventa un rilievo per il controller. Non si dichiara riuscito ciò che non lo è.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-16-p3a-prova-flusso.md`: versione, passi, esito per passo, numero di veti e di token (`bin/tollgate stats`), difetti trovati e correzioni.
- [ ] **Step 4: Commit** «tollgate P3a: prova reale del flusso con claude -p».

---

### Task 14: Criteri, revisione 22 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p3a.py`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 22), `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «criteri di P3a → test» nel piano principale; i contratti reali P3a → P3b/P3c/P4.

- [ ] **Step 1: Test dal programma vero** (`test_criteria_p3a.py`, `FlowLab` più `hooks/run` reale come in `test_criteria_p2.py`):
  - `test_start_from_wrapper_flow` (criterio 1): `PreToolUse Bash` di `start 7` attraverso `hooks/run` registra il segnale, poi `bin/tollgate start 7` → 0;
  - `test_task_cycle_end_to_end` (criteri 4 e 38): `task start 1`, `PreToolUse Agent` con il nome del brief → 0, `SubagentStart`, commit, `verify`, `SubagentStop` con il report → task in `review`, `review-prepare`, `SubagentStop` del revisore con il verdetto → `approved`, `task done` → `done`.
- [ ] **Step 2: Matrice.** Per i criteri di P3a scrivere nel piano principale la tabella «Prove dei criteri di P3a» (formato `file::Classe.metodo`), con «Resta a» per le parti di P3b, P3c e P4:
  - 1: senza la proposta d'adozione eseguita (P3b `adopt`);
  - 4: parte `task`;
  - 18: `reviewer_standard`;
  - 22: tetto;
  - 28: senza «interruzione dopo `finish check`» (P3b);
  - 38: `task start` e unione; `final_specialist` a P3b;
  - 39: `status`;
  - 40: revisore del task; verificatore a P3b.

  Un criterio senza test è un buco: si aggiunge il test nel modulo che possiede il codice.
- [ ] **Step 3: Revisione 22 della spec**:
  - le decisioni 2-22 di questo piano nelle sezioni pertinenti: 3.1 (segnale della CLI, `act apply` senza id, `start` con `--confirm` e `--reopen-execution`), 6.1 (passi e codici d'uscita, percorso del worktree, `exclude`), 6.3 (instradamento, skill assenti, prenotazione, verdetto effettivo), 8.4 (`act apply`, riga «programma»), 5 (tetto e fase), 11.1 (intervallo di Superpowers), 11.3 (involucro della statusline), 12.2 (migrazione 3), 0 (checkpoint non committato);
  - nota M3 in 0 («sessione viva»): `Read`, `Grep` e `Glob` non aggiornano la vita, per non lanciare Python a ogni lettura; un implementatore che legge per più di `stale_minutes` senza altri strumenti risulta fermo;
  - sezione 16: esiti V1-V5;
  - riga 22 nella sezione 20.
- [ ] **Step 4: Piano principale**:
  - «Stato»: P3a chiuso sul ramo, merge in attesa dell'OK dell'utente, con il numero di test;
  - sezione 3: pacchetto `tollgate_flow` con i moduli reali, e i contratti P3a → P3b/P3c/P4 con i nomi reali, tra cui `APPLIERS`, `checkpoint.CAPS`, `prereq.GATE_FILES` e `.github/tollgate/VERSION` per P4;
  - i vincoli per P3b e P3c emersi qui.
- [ ] **Step 5: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi.

```bash
git add tests/test_criteria_p3a.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git commit -m "tollgate P3a: prove dei criteri, spec rev 22, piano principale"
```
