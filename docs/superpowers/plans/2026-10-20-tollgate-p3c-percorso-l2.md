# tollgate P3c: percorso L2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portare un lavoro L2 da «spec scritta» a «task del piano in esecuzione»: giri avversariali sulla spec, audit a lenti quando le fette sono più di una, `approve spec <fette>` con `spec-approval.md`, avversario del piano, `approve plan` con `plan-approval.md` e registrazione dello scope alla versione approvata, `reopen spec|plan`, `start #M --spec <percorso>` per le fette successive, la voce `approvals` della DoD con i report, agenti `spec-adversary`, `spec-auditor`, `plan-adversary`, skill `spec-audit` e `reopen`.

**Architecture:** I giri di audit vivono nella tabella `spec_audit` (già nello schema 1, mai usata), estesa dalla migrazione 5 con codice, SHA e stadio, e gestita da un modulo nuovo di `tollgate_core` (`audits`). Le regole pure (esito dai conteggi, matrice dei punti di vista, forma della spec, file di approvazione e di report) stanno in `tollgate_analysis`, perché P4 le riusa nel gate. Il coordinatore apre ogni giro con un sottocomando nuovo, `tollgate audit prepare` (`tollgate_flow.audit`), che stampa le righe di lancio come `review prepare`; il report lo chiude un modulo nuovo di `subagent_stop` (`audit_round`) con un'operazione `record` nuova che scrive il report in `docs/superpowers/reviews/<N>/`. Le approvazioni e le riaperture sono voci nuove di `actapply.APPLIERS`, in un modulo a parte (`tollgate_flow.l2acts`).

**Tech Stack:** Python ≥ 3.11, solo libreria standard (`sqlite3`, `argparse`, `secrets`, `subprocess`, `unittest`), bash, git, `gh` 2.46 (nessun campo nuovo). Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 23; la revisione 24 la scrive il Task 15): sezioni 0 (ciclo vuoto, lenti e punti di vista), 3, 3.1, 4, 5 (fette), 6.1 (`--spec`), 6.2, 7.2, 8.4, 8.7, 11.4 (`[spec_audit]`, `[components]`), 12.2, 12.3, 12.4, 15 (criteri 18, 24, 35, 37, 41), 18.1, 18.3, 18.4. Piano principale: `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md` (sezione 3: contratti reali di P3a e P3b, «Vincoli per P3b e P3c», «Vincoli per P3c», rinviato della riga 83; sezione 4: matrice dei criteri). Registro di P3b: `docs/sdd/2026-10-19-tollgate-p3b-chiusura/` (triage in `final-review.md`, righe in `deferred-minors.md`).

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- Strati (spec 3, `tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_flow` importa solo `tollgate_core` e `tollgate_analysis`; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks` né `tollgate_checks`, tranne `tollgate_core/cli.py`; i moduli di `tollgate_checks` non scrivono nel DB né su file: usano `record`.
- Scritture nel DB solo con le funzioni di `tollgate_core`. `set_phase`, `open_block` e `close_block` fuori da una transazione. `db.DbError` all'apertura e `sqlite3.Error` durante le operazioni diventano rifiuti, mai traceback (vincoli 1-5 del piano principale).
- **Programma nei comandi per il modello:** ogni comando scritto in un messaggio della CLI, di un hook, di un brief, di una skill o di un agente usa `tollgate_core.paths.program_command` (`python3 "<bin>"`); le skill scrivono `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`. Mai il percorso nudo.
- **Sottocomandi del coordinatore:** ogni sottocomando nuovo va in `cli_calls._COORDINATOR_ONLY`; se legge la sessione anche in `_SIGNALLED`, e passa `argv` a `sessions.cli_session` (vincolo (5) di P3b). In P3c nessun sottocomando nuovo legge la sessione: `audit` va solo in `_COORDINATOR_ONLY`; `approve spec`, `approve plan` e `reopen` passano da `act apply`, già segnalato.
- La configurazione si legge dalla base del lavoro o dalla punta del ramo predefinito di `origin`, mai dal working tree (spec 3.2). Gli hook non usano la rete.
- **Testo non fidato** (issue, spec e piano scritti dal modello, messaggi degli avversari e degli auditor): mai in un comando shell né in un argomento di `git` o `gh`. Va su file, in un recinto più lungo di ogni sequenza di backtick (`tollgate_analysis.brief.fence`), marcato come dato (`brief.DATA_NOTE`).
- `docs/superpowers/reviews/**` lo scrivono solo la CLI e gli hook (spec 0, file protetti): report e file di approvazione non si scrivono mai con Edit o Write, e il coordinatore li committa con `git add`/`git commit`.
- Nessuna rete nei test. `gh` nei test è `tests/fakegh.py` con `TOLLGATE_GH` e la sentinella. **Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json` o `~/.claude/plugins/`.** I test non lanciano `claude`; solo il Task 14 lancia `claude -p`, in `/tmp/tollgate-p3c`, con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

## Decisioni di questo piano

Scelte che la spec lascia aperte o che il codice reale impone, con il costo se sbagliate. Il Task 15 le riporta nella revisione 24 della spec.

1. **Migrazione 5** (solo in avanti, con la copia prima):
   - `spec_audit`: `code TEXT` (codice del giro, `secrets.token_hex(4)`), `sha TEXT` (blob del documento esaminato: la spec per `spec-adversarial` e `spec-lens`, il piano per `plan-adversarial`), `spec_sha TEXT` (blob della spec; per i giri sulla spec coincide con `sha`), `stage TEXT NOT NULL DEFAULT 'closed'` (`open`, `closed`), `opened TEXT`;
   - `work_items`: `audit_suspended TEXT NOT NULL DEFAULT '{}'`, JSON `{tipo: numero del giro}` dei tetti sciolti con `resolve` (decisione 7).

   `outcome` vale `findings`, `empty` (18.3) o `superseded` (giro aperto su un documento poi cambiato, decisione 4). Costo: una migrazione.
2. **Tipi di giro e agenti.** `audits.KINDS = ("spec-adversarial", "spec-lens", "plan-adversarial")`; `audits.AGENTS = {"spec-adversarial": "tollgate:spec-adversary", "spec-lens": "tollgate:spec-auditor", "plan-adversarial": "tollgate:plan-adversary"}`; componenti `spec_adversary`, `spec_audit`, `plan_adversary`. Il report del giro `n` è `docs/superpowers/reviews/<N>/<tipo>-<n>.md`; il numero è per tipo, da 1. Costo: nessuno.
3. **`tollgate audit prepare [--confirm]`** (sottocomando nuovo, del coordinatore, senza sessione) decide il passo dallo stato, come `review prepare`, e lo stampa. Codici `OK` 0, `REFUSED` 1, `NEEDS_CONFIRM` 3. Ogni lancio è una riga `agente: <tipo> brief: "<percorso>"[ model: <m>]` (`[review] models`), l'ultima riga è `prossimo passo: …`. Il documento si legge **a HEAD**: se il file del worktree è diverso dal blob in HEAD, rifiuta con «committa <percorso> prima del giro» (i report non committati non contano). Fasi:
   - `spec_audit`: spec = `work_items.spec_path`, altrimenti il primo file nuovo sotto `docs/superpowers/specs/` in `work_base_sha..HEAD` (lo registra `phases.set_spec_path`); nessuna spec → rifiuto «scrivi e committa la spec». Una sola condizione, **avversariale soddisfatto** (`audit.adversarial_ok`), vale in tutti i rami e in `approve spec`: `spec_adversary` spento, oppure l'ultimo giro `spec-adversarial` chiuso ha `sha` uguale al blob attuale ed è pulito o sospeso (decisione 7). Poi, nell'ordine: giro aperto sullo stesso SHA → ristampa il lancio (stesso codice); giro aperto su un altro SHA → `superseded` e si prosegue; avversariale non soddisfatto → se l'ultimo giro avversariale è non pulito sullo stesso SHA e non sospeso, rifiuto «correggi la spec e committala, poi rilancia» (`STEPS["fix_spec"]`), altrimenti nuovo giro avversariale; avversariale soddisfatto e fette > 1 con `spec_audit` acceso e audit a lenti né chiuso né sospeso → ciclo a lenti (decisione 6; se l'ultimo ciclo a lenti chiuso è sullo stesso SHA e non vuoto, rifiuto «correggi la spec»); con l'audit a lenti chiuso **o sospeso** e `spec_adversary` spento, se l'ultimo ciclo a lenti chiuso non sta sul blob attuale → un ciclo a lenti **di conferma** (punto di vista dato da `next_viewpoint`, anche ad audit chiuso o sospeso: la spec cambiata va rivista; un ciclo di conferma non riapre il tetto dei cicli e non toglie la sospensione; con l'audit sospeso, un ciclo di conferma con rilievi lascia comunque la strada a «approve spec»: è il senso di «sospeso», e il report resta tra i file della PR); altrimenti «prossimo passo: chiedi all'utente /tollgate:approve spec <fette>». Così, dopo correzioni portate dalle lenti, lo SHA cambia e l'avversariale torna non soddisfatto: il giro di conferma di 6.2 è automatico.
   - `plan` in L2: piano = `work_items.plan_path` (lo registra l'hook `post_edit` quando passa `plan-check`), altrimenti il primo file nuovo sotto `docs/superpowers/plans/` in `work_base_sha..HEAD` che passa `plan-check`, come `adopt._find_plan`, registrato con `scope.set_plan_path` (un piano scritto da Bash non passa da `post_edit`); nessun piano → rifiuto «scrivi il piano con superpowers:writing-plans; deve passare plan-check». Con `plan_adversary` acceso: giro avversariale del piano finché uno è pulito su (SHA del piano, SHA della spec approvata); pulito o sospeso → **la CLI porta la fase `plan → approval`** (causa `audit_clean`, 6.2) e stampa «chiedi all'utente /tollgate:approve plan». Con `plan_adversary` spento il passaggio è immediato.
   - `approval`: stampa «chiedi all'utente /tollgate:approve plan». Altre fasi, L0 e L1: rifiuto con la fase. In `blocked` rifiuta e indica `/tollgate:resolve`.

   Costo: un sottocomando in più nella skill; è rientrante dopo `/clear`.
4. **Giri e chiusura.** `audits.open_round` scrive una riga `stage = 'open'` con `opened`; un solo giro aperto per lavoro. Un agente appartiene al giro aperto solo se è del tipo del giro **e** la sua riga di `subagents` ha `started` non nullo e non precedente a `opened` (`started >= opened`; entrambi scritti con `clock.fmt`, quindi confrontabili come testo; una riga con `started` nullo non appartiene a nessun giro): il report tardivo dell'agente di un giro superato non tocca il giro nuovo, e `subagent_stop` lo chiude come un qualunque agente di sola lettura. Il giro si chiude a `SubagentStop` (decisione 5). Un giro aperto su uno SHA che non è più quello in HEAD si chiude `superseded` (non conta nei tetti né nella matrice). Esito di un giro chiuso: `empty` se `blocker + major + moderate == 0` (glossario: ciclo vuoto), altrimenti `findings`. Un giro avversariale è **pulito** se `blocker + major == 0` (6.2: «finché un giro non trova né blocker né major»). Costo: nessuno.
5. **Report dei giri a `SubagentStop`** (modulo `tollgate_checks.audit_round`, ordine 15). Il messaggio finale dell'agente (da `last_assistant_message` o da `subagents.report`, auto mode) deve chiudere con una riga JSON:
   `{"v": 1, "kind": "<tipo>", "number": <n>, "viewpoint": <punto di vista o null>, "spec_sha": "<blob>", "plan_sha": "<blob, solo plan-adversarial>", "code": "<codice>", "counts": {"blocker": 0, "major": 1, "moderate": 3, "minor": 2}}`.
   Vale solo con `kind`, `number`, `code`, `spec_sha` (e `plan_sha`) del giro, `viewpoint` del giro per `spec-lens` (`null` altrimenti) e `counts` con i quattro interi ≥ 0; `outcome` dichiarato si ignora (6.2: lo calcola l'hook). Non valido → veto (uscita 2) con l'elenco dei problemi, al più 2 (`subagent_veto`), poi `subagent_finish` (riga del subagente `done`), `needs_you` «report del giro non valido: <nomi dei problemi>» (mai i valori grezzi del JSON) e il **giro resta aperto**: `audit prepare` lo ristampa con lo stesso codice. Impronta cambiata con `readonly_check` acceso → `tampered_records` (riga `tampered`), `needs_you`, giro aperto. Con il componente del tipo spento il modulo chiude solo la riga del subagente (`subagent_finish`); il giro resta aperto e lo chiude `superseded` il successivo `audit prepare`, che con il componente spento non apre giri di quel tipo (nessuna operazione `record` in più: `OPS` passa a 28). In ogni ramo `audit_round` emette `subagent_finish`, perché `subagent_stop` salta gli agenti in attesa di un giro. Valido → `record("audit_report", …)`: l'operazione aggiorna la riga (conteggi, esito, `report_path`, `stage = 'closed'`), scrive il report nel worktree (intestazione 18.3 più il messaggio in un recinto, troncato a 60.000 caratteri), per `spec-lens` rigenera `spec-lens-stato.md`, emette `spec_audit_round` {kind, number, viewpoint, outcome} e apre i blocchi dei tetti (decisione 7). Costo: un agente che scrive solo prosa riceve due veti.
6. **Audit a lenti** (6.2, glossario). Punti di vista, nell'ordine: `audits.VIEWPOINTS = ("executor", "user", "attacker", "payer", "successor", "skeptic", "edge_case", "integrator")` con le etichette italiane di 0 (chi esegue, chi usa, chi attacca, chi paga, chi arriva dopo, lo scettico, il caso limite, chi integra). Il contatore di un punto di vista è il numero di cicli vuoti **consecutivi** dei suoi cicli chiusi; un ciclo non vuoto lo azzera (criterio 24: «una correzione `major` azzera il contatore del punto di vista che l'ha trovata»). L'audit è **chiuso** quando ogni contatore è ≥ 2 (almeno 16 cicli). Il prossimo punto di vista è il primo, in ordine circolare dopo l'ultimo usato, con contatore < 2; il ciclo 1 è `executor` (prd-audit). Tetto `spec_audit_cycles` (30) contando i cicli chiusi non `superseded`. **Costo e conferma:** se il lavoro non ha nessuna riga `spec-lens` (superate comprese), `audit prepare` esce con 3 e le righe `conferma: audit a lenti: da 16 a <tetto> cicli di tollgate:spec-auditor, più i giri avversariali di conferma`; la skill chiede all'utente e rilancia con `--confirm`; al no lancia `tollgate audit decline`, che apre `needs_you` «audit a lenti rifiutato dall'utente». Costo: la scelta del punto di vista è meccanica, non «il più lontano» di prd-audit.
7. **Tetti e sospensione** (6.2, 8.4). I tetti contano i giri chiusi non `superseded` del tipo (`len(audits.rounds(...))`), non il numero del giro. Alla chiusura di un giro: giro avversariale della spec che è almeno il `spec_rounds`-esimo (4) e non è pulito → `needs_you` «giri avversariali della spec esauriti (giro <n>)»; avversario del piano, almeno il `plan_rounds`-esimo (2) → «giri avversariali del piano esauriti (giro <n>)»; ciclo a lenti che è **esattamente** il `spec_audit_cycles`-esimo (30, confronto per uguaglianza: i cicli di conferma oltre il tetto non lo riaprono) con l'audit non chiuso → «audit a lenti: tetto di cicli raggiunto». I prefissi stanno in `audits.CAP_REASONS` (tipo → prefisso) e `audits.DECLINE_REASON`. `resolve` su uno di questi blocchi, oltre a chiuderlo, scrive in `work_items.audit_suspended` il tipo con il numero del giro (0 per il rifiuto): «avversariale sospeso», «avversario del piano sospeso», «audit a lenti sospeso». Una sospensione avversariale vale solo finché l'ultimo giro di quel tipo è quello sospeso: un giro successivo non pulito sopra il tetto riapre il blocco. La sospensione dell'audit a lenti è definitiva per il lavoro. `reopen` non tocca le sospensioni. Costo: dopo una riapertura il primo giro non pulito è già sopra il tetto e riapre subito il blocco.
8. **Forma della spec** (`tollgate_analysis.specdoc`). `slices(text) -> int`: le voci `^\d+\.\s+\S` della sezione `## Fette previste` (fino alla prossima intestazione di secondo livello, fuori dai recinti); senza sezione o senza voci 1. `pitch_problems(text) -> list[str]`: mancano `## Tane di coniglio` o `## Cosa non fare`. Con `spec_pitch` acceso, `audit_round` aggiunge a ogni giro `spec-adversarial` un `major` per ogni sezione mancante (conteggi e riga «rilievo meccanico: …» nel report): è la seconda frase del criterio 41, deterministica. Costo: un avversario che segnala lo stesso difetto lo conta due volte.
9. **`approve spec <fette>`** (`l2acts.approve_spec`). Fase `spec_audit`; `spec_path` registrato; spec in HEAD uguale al worktree; `<fette>` intero uguale a `specdoc.slices` della spec in HEAD (altrimenti rifiuto con il numero atteso); nessun giro aperto (altrimenti «giro <tipo> <n> ancora aperto: aspetta il report o rilancia audit prepare»); avversariale soddisfatto (`audit.adversarial_ok`, decisione 3: con `spec_adversary` acceso l'ultimo giro avversariale sta sul blob attuale ed è pulito o sospeso; spento, la condizione non si applica, 6.2); con fette > 1 e `spec_audit` acceso, audit a lenti chiuso o sospeso. Si guardano solo i giri della spec (`spec-adversarial`, `spec-lens`), mai quelli del piano; se ne esiste almeno uno chiuso, l'ultimo chiuso tra questi deve stare sul blob attuale (6.2, punto 4), anche con `spec_adversary` spento. Scrive `docs/superpowers/reviews/<N>/spec-approval.md` (`approvals.render_approval`: `kind`, `path`, `sha`, `slices`, `adversarial`, `lens`, `act_id`, `approved_at`; `adversarial` e `lens` in `closed`, `suspended`, `off`, `null` (lenti con una fetta sola)), poi fase `spec_audit → plan` (causa `approve_spec`). Con fette > 1 le righe propongono un'issue per le fette 2..n, con il titolo `fetta <k>/<n> di <nome del file della spec>` (i titoli scritti nella spec sono testo non fidato: compaiono solo in un recinto, marcati come dato, e non vanno in un argomento di `gh`), «da creare tu, oppure dall'agente dopo /tollgate:approve effect», e il comando `/tollgate:start #M --spec <percorso>` da usare dopo il merge di questa (5). Ultima riga: «committa <spec-approval> con i report, poi scrivi il piano». Costo: la proposta delle issue è testo, non un'azione.
10. **`approve plan`** (`l2acts.approve_plan`). Fase `approval`; nessun giro aperto; piano registrato come percorso; piano in HEAD uguale al worktree e valido per `plan-check`; spec in HEAD con lo `sha` dell'approvazione della spec (decisione 13), altrimenti rifiuto «spec cambiata dopo approve spec: /tollgate:reopen spec»; con `plan_adversary` acceso, ultimo giro `plan-adversarial` pulito o sospeso con `sha` = blob del piano e `spec_sha` = blob della spec. Poi, nell'ordine: `scope.register_plan(..., plan_sha=<blob in HEAD>, advance=False)` (saltato se `plan_sha` è già quello: ripetizione dopo un'interruzione), `plan-approval.md` (`kind`, `path`, `sha`, `spec_sha`, `adversarial`, `act_id`, `approved_at`), fase `approval → execution` (causa `approve_plan`). Criterio 37: `plan_sha` è quello di `approve plan`. Costo: nessuno.
11. **Passaggi in avanti di L2 con una causa propria** (12.3): `phases._FORWARD_CONDITION` riceve `("spec_audit", "plan"): "approve_spec"`, `("plan", "approval"): "audit_clean"`, `("approval", "execution"): "approve_plan"`. Così la fase non avanza senza l'atto o il giro pulito. `hookkit.Lab.goto` legge già quella tabella; i casi L2 di `tests/test_phases.py` cambiano di conseguenza. Costo: tre righe di test riscritte.
12. **`reopen spec|plan <motivo>`** (`l2acts.reopen`). Motivo obbligatorio (`args[1:]`). `reopen spec` da `plan`, `approval`, `execution` (L2) → `spec_audit` (causa `reopen_spec`); `reopen plan` da `approval`, `execution` (L1 e L2) → `plan` (causa `reopen_plan`). Rifiuta in altre fasi, con un task `running` o `review`, o con un implementatore `running` (stessa regola di `sync`, ruling I-2). Un giro di audit aperto diventa `superseded`. Se il piano è registrato, `scope.reset_plan` toglie scope, `plan_sha` e i task del lavoro (evento nuovo `plan_reset` {plan_sha, tasks}); `plan_path` resta, così `post_edit` riconosce lo stesso file. I file di approvazione restano come storico: la fase precedente all'approvazione li rende modificabili (`violations.locked_docs`) e superati (lo `sha` non coincide più). Dopo la nuova registrazione i task tornano tutti `pending`: quelli già fatti finiscono come «task già soddisfatto», come dopo `adopt`. Costo: un task già chiuso si rivede una volta.
13. **Approvazione della spec di un lavoro** (`approvals.locate_spec_approval(files, *, issue, spec_path, spec_blob)`): il file `reviews/<N>/spec-approval.md` del lavoro se esiste con `path == spec_path` (qualunque `sha`: chi chiama controlla `is_current`); altrimenti, per una fetta successiva, il `reviews/<M>/spec-approval.md` con `path == spec_path` e `sha == spec_blob`; con `spec_blob = None` basta `path == spec_path` (lo usa `locked_docs`, a cui serve sapere solo se la spec è stata approvata); con più candidati vince il numero di issue più basso (la prima fetta). `files` è `{percorso: testo}` dei file di approvazione presenti nell'albero (HEAD, ramo predefinito o disco). La usano `start --spec`, `approve plan`, `violations.locked_docs`, `finish check`, `openpr.facts` e `adopt`. Costo: un elenco dei file sotto `docs/superpowers/reviews/` (`git.ls_files_at`).
14. **`start #M --spec <percorso>`** (5, 6.1). Solo per un lavoro nuovo (in ripresa si ignora con un avviso). Il percorso è relativo, sotto `docs/superpowers/specs/`, senza `..`, e deve esistere sul ramo predefinito; se non c'è un `spec-approval.md` per quel percorso sul ramo predefinito → rifiuto (criterio 24). Approvazione con `sha` uguale al blob attuale → livello L2, `create_work(spec_path=..., from_approved_spec=True)`, fase `plan`. Approvazione con `sha` diverso → uscita 3, «la spec è cambiata dopo l'approvazione: con --confirm il lavoro parte da spec_audit, con un nuovo giro e una nuova approve spec»; con `--confirm` livello L2, `spec_path` registrato, fase `spec_audit`. Il testo dell'issue non decide mai la fase. `create_work` con `from_approved_spec` senza `spec_path` → `ValueError` (rinviato di P1). Costo: nessuno.
15. **Voce `approvals` della DoD in L2** (8.7: «spec e piano approvati, report avversariali presenti»). `approvals.check_l2(files, *, issue, spec_path, spec_blob, plan_path, plan_blob) -> list[str]` (vuota = vera), funzione pura che P4 riusa nel gate: approvazione della spec trovata con `locate_spec_approval` e `sha == spec_blob`; `plan-approval.md` del lavoro con `sha == plan_blob` e `spec_sha == spec_blob`; nella cartella dell'approvazione della spec almeno un `spec-adversarial-<n>.md` con intestazione valida, salvo `adversarial: off`; `spec-lens-<n>.md` se `slices > 1` e `lens: closed`; nella cartella del lavoro almeno un `plan-adversarial-<n>.md`, salvo `adversarial: off` nel piano. `finish check` la usa al posto del controllo di P3b; `openpr.facts` valorizza `spec_reviews_dir` con la cartella dell'approvazione trovata (anche di un'altra issue), `plan_reviews_dir` con quella del lavoro se `plan-approval.md` esiste, e `spec_audit` dall'approvazione trovata (18.1). Lo scope L2 di `finish check` esenta la spec se il suo blob è lo `sha` dell'approvazione trovata. Costo: per una fetta successiva i report della spec sono nella cartella di un'altra issue, come vuole 18.1.
16. **`adopt` di L2** (12.4, vincolo (2) di P3b). Senza `spec-approval.md` proprio, ma con un `plan-approval.md` corrente il cui `spec_sha` è lo `sha` di un'approvazione trovata nell'albero per una spec ancora con quel blob → spec approvata (fetta successiva). Senza nessuno dei due → `spec_audit`, come oggi. Con la spec approvata, il piano e **senza** `plan-approval.md`, la fase è `plan` se `plan_adversary` è acceso (i giri del piano sono persi con il DB, e `approve plan` li richiede: in `plan` `audit prepare` li rifà), `approval` se è spento; oggi `adopt` dà sempre `approval`. Costo: una fetta successiva adottata senza piano approvato riparte da `spec_audit` e va abbandonata e riavviata con `--spec`.
17. **Parser del piano: recinti** (rinviato della riga 83 del piano principale). `_FENCE_OPEN` ammette al più 3 spazi di rientro (CommonMark): una riga con 4 o più spazi seguiti da ```` ``` ```` è codice indentato, non apre un recinto. Vale per `check_plan` e `task_text`. Costo: un piano con un recinto rientrato di 4 spazi dentro un elenco ora è letto come testo.
18. **File di approvazione e intestazioni dei report** (18.3). `approvals.parse_header(text) -> dict | None` è il lettore comune (intestazione tra `---`); `parse_approval` lo usa e accetta solo i due `kind` di approvazione; `parse_report_header` accetta i tre tipi di giro con `number` intero e `counts` valido. `_value` toglie un commento ` #…` anche dopo un valore tra virgolette (triage 30). `render_approval(fields: dict) -> str` e `render_report(fields: dict, body: str) -> str` scrivono le intestazioni con i valori stringa tra virgolette doppie e `counts` in forma `{blocker: 0, major: 1, moderate: 0, minor: 2}`; `parse_*(render_*(x))` restituisce gli stessi campi. Costo: nessuno.
19. **Blocco della spec** (`violations.locked_docs`): la spec è bloccata dopo `spec_audit` se esiste su disco un'approvazione per `spec_path` trovata con `locate_spec_approval(..., spec_blob=None)` (anche di un'altra issue, per le fette successive). Una modifica della spec fatta da Bash in una fetta successiva resta visibile a `finish check`, perché la spec non è più esente dallo scope (decisione 15). Costo: una lettura della cartella `reviews/` del worktree per ogni scrittura in L2.
20. **Prossimo passo** (`checkpoint.next_step`) in `spec_audit`, `plan` di L2 e `approval`: il passo di `audit prepare` calcolato senza aprire giri (`audit.peek(conn, work) -> str`, che carica la configurazione con `config.load_config_at(<checkout principale>, <base del lavoro>)`, senza cartella di stato; base = `work_base_sha` o, se nullo, `git.default_ref`; con `ConfigError`, `git.GitError` o worktree assente restituisce «lancia <programma> audit prepare», mai un'eccezione; come le altre letture senza stato, ignora `TOLLGATE_TEST_CONFIG`, quindi i test di `next_step` scrivono `tollgate.toml` nella base). `CAPS` riceve i tre prefissi dei tetti dell'audit e il rifiuto del costo («giri avversariali della spec», «giri avversariali del piano», «audit a lenti»), così `status` dice quale tetto ha fermato il lavoro; **non** entrano in `CAP_PREFIXES`, che porta a `approve rounds`: per i blocchi dell'audit `_cap_step` dice `audit.STEPS["resolve"]` («serve una decisione dell'utente: /tollgate:resolve <id> <nota> sospende; oppure correggi e rilancia audit prepare dopo il resolve»). Costo: nessuno.
21. **Agenti** (spec 3, 4): `spec-adversary` (`tools: Read, Grep, Glob, WebFetch`, `model: inherit`), `spec-auditor` (`Read, Grep, Glob, WebFetch`, `sonnet`), `plan-adversary` (`Read, Grep, Glob`, `inherit`); niente scrittura né Bash, già in `readonly_agents`. I brief li scrive `audit prepare` in `.tollgate-run/<N>/<tipo>-<n>.md`: percorso e SHA del documento, cartella dei report precedenti, testo dell'issue (`issue.md`, solo se esiste), gravità da `[severity]`, il JSON finale della decisione 5 con `code` e SHA alla lettera; per `spec-lens` anche il punto di vista e il percorso assoluto di `skills/spec-audit/references/dimensioni.md`; per `plan-adversary` anche il percorso della spec approvata e, per ogni task, numero di file e instradamento (`profiles.task_routing`: agenti diversi o più di 3 skill → candidato a essere diviso; più di `task_files_warn` file → segnalato, 6.3). Il metodo delle lenti è la skill `spec-audit`, «versione di prd-audit incorporata, con l'accordo dell'autore» (spec 3). Costo: nessuno.
22. **Nessuna verifica preliminare su Claude Code** (Task 1). I giri sono in sequenza (il metodo corregge il documento tra un giro e l'altro), quindi non serve provare subagenti avversari in parallelo; i fatti usati sono già provati: `SubagentStop` con `last_assistant_message` e `SubagentHandback` (P0), `agent_type` dei plugin (P0), `UserPromptExpansion` con `command_args` per le skill con `disable-model-invocation` (P0), `${CLAUDE_PLUGIN_ROOT}` espansa nelle skill (P3a, V1), `EnterWorktree` (P0), `Agent` lanciato da una riga `agente:` (P3b, prova reale). `gh`: nessun campo JSON nuovo; le issue delle fette le crea l'agente con il proprio comando dopo `approve effect`, non il codice. Costo: se la prova reale (Task 14) smentisce un fatto, il difetto si corregge lì.
23. **Prova reale senza rete** (Task 14), come la decisione 24 di P3b: tutto in `/tmp/tollgate-p3c/flow`, repo nudo locale dietro l'URL finto con `insteadOf`, `gh` finto, `claude -p --plugin-dir`; dal passo dopo `start` ogni `claude -p` parte dalla cartella del worktree (sessione nuova, legata da `SessionStart`) e lo script lo controlla prima di lanciare. Costo: nessuno.
24. **Eventi nuovi** (18.4): `plan_reset` {plan_sha, tasks}; `spec_audit_round` (già nell'elenco) con {kind, number, viewpoint, outcome}. Le cause nuove di `phase_change`: `approve_spec`, `audit_clean`, `approve_plan`. Costo: nessuno.
25. **Rinviati di P3b** (triage di `final-review.md`, destinazione P3c): tutti nei Task 11 e 12, con test; il dettaglio è nella tabella «Rilievi ripresi qui». Per la riga 49 (`approve finding` su un rilievo di un ciclo non ultimo) il blocco dei cicli si chiude comunque, come stabilito dalla ruling «dubbio 1 del Task 10» di P3b; per la riga 71 il task di correzione instrada sui file dei rilievi del ciclo **qualunque sia** la decisione successiva dell'utente (instradamento stabile). Costo: nessuno.

26. **File di `reviews/<N>/` esenti dallo scope dei commit** (spec 6.2: «il coordinatore committa i report insieme a spec e piano»). `violations.scope_exempt` esenta ogni file sotto `docs/superpowers/reviews/<issue del lavoro>/`: li scrivono solo la CLI e gli hook (file protetti, mai Edit o Write) e senza esenzione, dopo `approve plan`, `plan-approval.md` non si potrebbe committare e renderebbe negato ogni commit del lavoro (il file non tracciato entra nelle modifiche del worktree). È la stessa esenzione che `finish check` dava già con `_own_document`, ora nel calcolo condiviso. Costo: un file scritto lì a mano da Bash non è visto dallo scope; resta protetto dalle regole di 7.4.
27. **Fasi, blocchi e sospensioni** (`work_items.phase`, `phase_before_block`, blocchi dei tetti, `audit_suspended`), toccati da `audit prepare`, `audit decline`, `SubagentStop`, `resolve`, `approve`, `reopen` e `adopt`: in `blocked` `audit prepare` e gli atti di L2 rifiutano (`approve spec|plan` e `reopen` indicano `/tollgate:resolve`); `resolve` dell'ultimo blocco riporta la fase di prima e scrive la sospensione nella stessa chiamata. Costo: nessuno.

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

## Mappa dei file

| File | Responsabilità |
|---|---|
| `docs/verifiche/2026-10-20-p3c-verifiche.md` | Task 1: fatti riusati e versioni |
| `bin/tollgate_analysis/specdoc.py` (nuovo) | Fette previste e sezioni del pitch |
| `bin/tollgate_analysis/auditrules.py` (nuovo) | Esito dai conteggi, giro pulito, matrice dei punti di vista, JSON del giro, testo del report e dello stato delle lenti |
| `bin/tollgate_analysis/approvals.py` | Lettore comune delle intestazioni, scrittura, ricerca dell'approvazione della spec, `check_l2` |
| `bin/tollgate_analysis/plan.py` | Recinti con al più 3 spazi |
| `bin/tollgate_analysis/brief.py` | Brief dei giri |
| `bin/tollgate_core/db.py` | Migrazione 5 |
| `bin/tollgate_core/audits.py` (nuovo) | Righe dei giri, sospensioni, prefissi dei tetti |
| `bin/tollgate_core/{phases,scope,events,git,violations}.py` | Cause L2, `set_spec_path`, `reset_plan`, `plan_reset`, `ls_files_at`, blocco della spec |
| `bin/tollgate_core/cli.py` | `audit prepare [--confirm]`, `audit decline`, `start --spec` |
| `bin/tollgate_flow/audit.py` (nuovo) | `prepare`, `decline`, `peek` |
| `bin/tollgate_flow/l2acts.py` (nuovo) | `approve spec`, `approve plan`, `reopen`, sospensioni da `resolve` |
| `bin/tollgate_flow/{actapply,start,finishcheck,openpr,adopt,checkpoint}.py` | Voci di `APPLIERS`, `--spec`, `approvals`, cartelle 18.1, adozione L2, prossimo passo |
| `bin/tollgate_checks/audit_round.py` (nuovo) | Report dei giri a `SubagentStop` |
| `bin/tollgate_checks/{_common,subagent_stop,cli_calls}.py` | `awaiting_audit`, giri saltati, `audit` del coordinatore |
| `bin/tollgate_hooks/apply.py` | Operazione `audit_report` |
| `agents/{spec-adversary,spec-auditor,plan-adversary}.md` | Agenti |
| `skills/{spec-audit,reopen}/SKILL.md`, `skills/spec-audit/references/dimensioni.md` | Skill nuove |
| `skills/{approve,start,resolve,finish,status}/SKILL.md`, `agents/implementer.md` | Skill aggiornate; forma del programma |
| `tests/flowkit.py` | Banco L2: spec e piano scritti e committati, report di giro simulato |
| `tests/test_*.py` | Un file per modulo; `tests/test_skill_contract.py`; `tests/test_criteria_p3c.py` |
| `spikes/run-p3c-flow.sh`, `docs/verifiche/2026-10-20-p3c-prova-flusso.md` | Prova reale |

---

### Task 1: Nessuna verifica preliminare su Claude Code

Il piano non usa fatti nuovi di Claude Code né campi nuovi di `gh` (decisione 22). Il task lo registra, con le versioni, e il piano parte dal codice.

**Files:**
- Create: `docs/verifiche/2026-10-20-p3c-verifiche.md`

**Regole di cautela (vanno nel brief):** nessun `claude -p`, nessuna chiamata di rete: solo `claude --version` e `gh --version`.

- [ ] **Step 1: Rapporto** con la tabella `Fatto | Dove è provato | Dove incide in P3c` per le voci della decisione 22, più `claude --version` e `gh --version`, e la riga «verifiche nuove: nessuna; la prova reale del Task 14 è il controllo».
- [ ] **Step 2: Commit** «tollgate P3c: nessuna verifica preliminare, fatti riusati».

---

### Task 2: Analisi pura: forma della spec, file di approvazione e di report, recinti del piano

**Files:**
- Create: `bin/tollgate_analysis/specdoc.py`
- Modify: `bin/tollgate_analysis/approvals.py`, `bin/tollgate_analysis/plan.py`
- Test: `tests/test_specdoc.py`, `tests/test_approvals.py`, `tests/test_plan.py`

**Interfaces:**
- Produces in `specdoc.py`: `SLICES_SECTION = "Fette previste"`, `PITCH_SECTIONS = ("Tane di coniglio", "Cosa non fare")`; `slices(text: str) -> int`; `slice_titles(text: str) -> list[str]`; `pitch_problems(text: str) -> list[str]` (testo: «manca la sezione «## Cosa non fare» (spec L2, 6.2)»). Recinti saltati come in `plan.py`.
- Produces in `approvals.py`:
  - `REPORT_KINDS = ("spec-adversarial", "spec-lens", "plan-adversarial")`, `SEVERITIES = ("blocker", "major", "moderate", "minor")`;
  - `parse_header(text: str) -> dict | None` (lettore comune; `counts` in forma `{chiave: intero, …}` diventa un dizionario);
  - `parse_approval(text)` invariata nel contratto, sopra `parse_header`;
  - `parse_report_header(text) -> dict | None` (tipo in `REPORT_KINDS`, `number` intero ≥ 1, `counts` con le quattro chiavi intere ≥ 0);
  - `render_approval(fields: dict) -> str`, `render_report(fields: dict, body: str) -> str` (decisione 18);
  - `approval_listing(paths: list[str]) -> list[str]`: i percorsi `docs/superpowers/reviews/<n>/spec-approval.md` di un elenco;
  - `locate_spec_approval(files: Mapping[str, str], *, issue: int, spec_path: str, spec_blob: str | None) -> tuple[str, dict] | None` (decisione 13; restituisce percorso e intestazione);
  - `check_l2(files: Mapping[str, str], *, issue: int, spec_path: str | None, spec_blob: str | None, plan_path: str | None, plan_blob: str | None) -> list[str]` (decisione 15; `files` contiene **tutti** i file sotto `docs/superpowers/reviews/` dell'albero, con il testo).
- Produces in `plan.py`: `_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")` (decisione 17).

- [ ] **Step 1: Test** `test_specdoc.py`: `test_slices_counts_numbered_items` (tre voci → 3); `test_no_section_is_one`; `test_section_without_items_is_one`; `test_items_inside_fence_ignored`; `test_slice_titles`; `test_pitch_problems` (manca solo «Cosa non fare» → una riga che lo nomina; entrambe presenti → `[]`).
- [ ] **Step 2: Test** `test_approvals.py`:
  - `test_quoted_value_with_comment` (`sha: "abc" # nota` → `"abc"`; triage 30);
  - `test_render_parse_roundtrip_approval` e `test_render_parse_roundtrip_report` (stessi campi, `counts` compreso);
  - `test_report_header_rejects_bad_counts` (chiave mancante, intero negativo, `number` 0 → `None`);
  - `test_locate_own_then_other_issue` (approvazione propria con `path` uguale → la propria; senza, quella dell'issue 3 con `sha` uguale al blob; due candidati 3 e 5 → 3; `sha` diverso → `None`);
  - `test_check_l2_matrix` (tutto presente → `[]`; `plan-approval` con `spec_sha` vecchio → un problema; nessun `spec-adversarial-*.md` con `adversarial: closed` → un problema, con `adversarial: off` nessuno; `slices: 3` e `lens: closed` senza `spec-lens-*.md` → un problema; `lens: suspended` senza report → nessuno; report con intestazione non valida → non conta).
- [ ] **Step 3: Test** `test_plan.py::FenceIndentTest`: `test_fence_with_four_spaces_does_not_open` (un `### Task 9` dopo una riga `    ```` ` è un task vero; con 3 spazi resta dentro il recinto); `test_task_text_same_rule`.
- [ ] **Step 4: Fallimento** (`python3 -B -m unittest tests.test_specdoc tests.test_approvals tests.test_plan`), **implementazione, verifica, `tests/run`**.
- [ ] **Step 5: Commit** «tollgate P3c: forma della spec, intestazioni di approvazioni e report, recinti del piano».

---

### Task 3: Analisi pura dell'audit

**Files:**
- Create: `bin/tollgate_analysis/auditrules.py`
- Test: `tests/test_auditrules.py`

**Interfaces:**
- Produces in `auditrules.py` (nessuna dipendenza da tollgate):
  - `VIEWPOINTS` e `VIEWPOINT_LABELS` (decisione 6); `SEVERITIES = ("blocker", "major", "moderate", "minor")`;
  - `outcome(counts: dict) -> str` (`empty` o `findings`, decisione 4); `is_clean(counts: dict) -> bool` (`blocker + major == 0`);
  - `RoundJson(valid: bool, problems: list[str], counts: dict | None)` e `parse_round_json(text: str, *, kind: str, number: int, code: str, spec_sha: str, plan_sha: str | None, viewpoint: str | None) -> RoundJson` (decisione 5; cerca l'ultimo JSON con la chiave `counts` con `report.json_candidates`, che sta in `tollgate_analysis`);
  - `LensState(cycles: dict[str, list[str]], streak: dict[str, int], closed: bool, total: int)` e `lens_state(rows: list[tuple[str, str]]) -> LensState` (righe `(viewpoint, outcome)` dei cicli chiusi non `superseded`, in ordine);
  - `next_viewpoint(state: LensState, last: str | None) -> str` (ad audit aperto il primo con contatore < 2 dopo `last`, in ordine circolare; ad audit chiuso semplicemente il successivo di `last`: serve ai cicli di conferma, decisione 3);
  - `render_lens_status(state: LensState, *, issue: int, cap: int, suspended: bool) -> str` (tabella `Punto di vista | Cicli | Vuoti di fila | Ultimo esito`, più «stato: aperto|chiuso|sospeso», cicli fatti e tetto).

- [ ] **Step 1: Test** `test_auditrules.py`:
  - `test_outcome_and_clean` (`moderate: 1` → `findings` ma pulito; `major: 1` → non pulito; solo `minor` → `empty`);
  - `test_round_json_valid_and_matrix` (codice, numero, tipo, SHA, `viewpoint` sbagliati → non valido con il problema; `counts` con stringa o negativo → non valido; JSON assente → «manca la riga JSON del giro (18.3)»; `outcome` dichiarato ignorato; `plan_sha` richiesto solo per `plan-adversarial`; ultimo JSON vince);
  - `test_major_resets_viewpoint_counter` (criterio 24: `executor` vuoto, vuoto, poi `major` → contatore 0);
  - `test_closed_needs_two_empty_each` (16 cicli vuoti, due per punto di vista → chiuso; 15 → aperto);
  - `test_next_viewpoint_rotates_and_repeats_findings` (primo `executor`; dopo `executor` con rilievi e gli altri a 2, torna `executor`; ad audit chiuso dopo `integrator` dà `executor`);
  - `test_render_lens_status_has_all_viewpoints`.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: regole pure dell'audit (esiti, punti di vista, riga JSON del giro)».

---

### Task 4: Migrazione 5, giri nel DB, cause L2, reset del piano

**Files:**
- Create: `bin/tollgate_core/audits.py`
- Modify: `bin/tollgate_core/db.py`, `bin/tollgate_core/phases.py`, `bin/tollgate_core/scope.py`, `bin/tollgate_core/events.py`, `bin/tollgate_core/git.py`, `bin/tollgate_core/violations.py` (`scope_exempt`, decisione 26)
- Test: `tests/test_db.py`, `tests/test_audits.py`, `tests/test_phases.py`, `tests/test_scope.py`, `tests/test_git.py`, `tests/test_violations.py`

**Interfaces:**
- Produces in `db.py`: `SCHEMA_V5` (decisione 1), `MIGRATIONS` fino a 5.
- Produces in `events.py`: tipo `plan_reset` (decisione 24).
- Produces in `phases.py`: le tre cause della decisione 11 in `_FORWARD_CONDITION`; `set_spec_path(conn, work: int, path: str, *, now) -> None` (solo se nullo); `create_work(..., from_approved_spec=True)` senza `spec_path` → `ValueError("from_approved_spec richiede spec_path")`.
- Produces in `scope.py`: `reset_plan(conn, work: int, *, now, session=None) -> list[int]` (toglie le righe di `scope` con `origin = 'plan'`, azzera `plan_sha`, cancella i task del lavoro e restituisce i loro numeri; evento `plan_reset`; una transazione).
- Produces in `git.py`: `ls_files_at(repo, ref: str, prefix: str) -> list[str]` (`git ls-tree -r --name-only <ref> -- <prefix>`, `[]` se il riferimento non c'è).
- Produces in `audits.py` (ogni funzione apre la sua transazione):
  - `KINDS`, `AGENTS`, `COMPONENTS = {"spec-adversarial": "spec_adversary", "spec-lens": "spec_audit", "plan-adversarial": "plan_adversary"}`, `CAP_REASONS` (tipo → prefisso, decisione 7), `DECLINE_REASON = "audit a lenti rifiutato dall'utente"`, `SUSPENDED_LABELS` (tipo → «avversariale sospeso», «audit a lenti sospeso», «avversario del piano sospeso»);
  - `open_round(conn, work, *, kind, sha, spec_sha, viewpoint, code, now) -> int` (numero; `ValueError` se c'è già un giro aperto);
  - `open_round_row(conn, work) -> sqlite3.Row | None`;
  - `supersede(conn, work, number_kind: tuple[str, int], *, now) -> None`;
  - `close_round(conn, work, *, kind, number, counts: dict, outcome: str, report_path: str, now) -> None` (evento `spec_audit_round`);
  - `rounds(conn, work, kind) -> list[sqlite3.Row]` (chiusi, non `superseded`, in ordine);
  - `any_rows(conn, work, kind) -> bool` (anche superate e aperte: serve alla conferma del costo, decisione 6);
  - `last_closed(conn, work, kind=None) -> sqlite3.Row | None` (con `kind=None` di qualunque tipo);
  - `suspend(conn, work, kind, number: int, *, now) -> None`; `suspended(conn, work) -> dict[str, int]`;
  - `cap_kind(reason: str) -> str | None` (tipo dal motivo di un blocco, anche `DECLINE_REASON` → `spec-lens`).

- [ ] **Step 1: Test** `test_db.py::MigrationV5Test` (DB v4 con righe → colonne nuove, dati intatti, copia `*migrazione-5*`; `test_latest_version_is_5`; il test v4 asserisce `str(db.latest_version())` se ancora asserisce `"4"`).
- [ ] **Step 2: Test** `test_phases.py`: la tabella `ALLOWED` di L2 usa `approve_spec`, `audit_clean`, `approve_plan`; `test_l2_forward_needs_its_cause` (`spec_audit → plan` con `advance` → `TransitionError`); `test_from_approved_spec_requires_spec_path`; `test_create_work_phase_and_from_approved_spec_exclusive` (già coperto: verificare che esista); `test_set_spec_path_only_once`.
- [ ] **Step 3: Test** `test_scope.py::ResetPlanTest`: `test_reset_then_register_again` (registrato, `reset_plan`, nuova `register_plan` con un altro `plan_sha` → riuscita; task vecchi spariti; evento `plan_reset` con i numeri). `test_git.py::LsFilesAtTest`.
- [ ] **Step 3b: Test** `test_violations.py::ReviewsExemptTest::test_own_reviews_dir_exempt_other_issue_not` (decisione 26: con lo scope registrato un file nuovo sotto `docs/superpowers/reviews/7/` non dà violazioni; sotto `reviews/8/` sì).
- [ ] **Step 4: Test** `test_audits.py`: `test_open_one_at_a_time`; `test_close_and_last_closed_any_kind`; `test_superseded_not_in_rounds`; `test_suspend_roundtrip`; `test_cap_kind_from_reasons`; `test_numbers_per_kind` (giro avversariale 1, ciclo a lenti 1, avversariale 2).
- [ ] **Step 5: Fallimento, implementazione, verifica** (`python3 -B -m unittest tests.test_db tests.test_phases tests.test_scope tests.test_audits tests.test_git`), `tests/run`.
- [ ] **Step 6: Commit** «tollgate P3c: migrazione 5, giri di audit nel DB, cause dei passaggi L2, reset del piano».

---

### Task 5: `audit prepare` e `audit decline`

**Files:**
- Create: `bin/tollgate_flow/audit.py`
- Modify: `bin/tollgate_analysis/brief.py`, `bin/tollgate_core/cli.py` (gruppo `audit`), `bin/tollgate_checks/cli_calls.py` (`audit` in `_COORDINATOR_ONLY`), `tests/flowkit.py`
- Test: `tests/test_brief.py`, `tests/test_audit_prepare.py`, `tests/test_check_cli_calls.py`

**Interfaces:**
- Consumes: `audits.*`, `specdoc.slices`, `auditrules.lens_state`, `auditrules.next_viewpoint`, `plan.check_plan`, `profiles.task_routing`, `approvals.locate_spec_approval`, `git.ls_files_at`, `git.blob_sha`, `git.text_at`, `phases.set_spec_path`, `phases.set_phase(..., "approval", "audit_clean")`, `phases.open_block`.
- Produces in `brief.py`: `AuditBrief(issue: int, kind: str, number: int, code: str, doc_path: str, doc_sha: str, spec_path: str, spec_sha: str, reviews_dir: str, issue_file: str | None, severity: dict, viewpoint: str | None, method_path: str | None, tasks: list[dict])` e `audit_brief(b: AuditBrief) -> str`: contiene `code`, `spec_sha` (e per il piano `plan_sha`) alla lettera e la riga JSON della decisione 5 come esempio esatto; vieta di modificare file; chiede ogni rilievo con sezione e gravità; per `spec-adversarial` chiede di controllare «Fette previste», «Tane di coniglio» (una tana senza scelta è `major`) e «Cosa non fare»; per `spec-lens` il punto di vista e il file del metodo; per `plan-adversarial` la tabella dei task.
- Produces in `audit.py`:
  - `OK = 0`, `REFUSED = 1`, `NEEDS_CONFIRM = 3`;
  - `STEPS: dict[str, str]`, i testi fissi delle righe `prossimo passo:` (chiavi `launch`, `fix_spec`, `fix_plan`, `approve_spec`, `approve_plan`, `write_spec`, `write_plan`, `resolve`); la skill e il Task 13 li citano;
  - `PrepareResult(code: int, lines: list[str], launches: list[finalreview.Launch])` (riusa `Launch` di `finalreview`);
  - `AuditError(Exception)`;
  - `prepare(state, cwd, *, confirm: bool, now=None) -> PrepareResult` (decisioni 3, 4, 6, 21; i brief in `.tollgate-run/<N>/<tipo>-<n>.md`);
  - `decline(state, cwd, *, now=None) -> tuple[int, list[str]]` (solo in `spec_audit`, con fette > 1, `spec_audit` acceso e nessun ciclo a lenti; apre il blocco `DECLINE_REASON`);
  - `adversarial_ok(conn, work: sqlite3.Row, cfg, spec_blob: str) -> bool` (decisione 3, usata anche da `l2acts.approve_spec`);
  - `peek(conn, work) -> str` (lo stesso calcolo senza scritture, per `next_step`, decisione 20).
  - I testi di `STEPS` cominciano con una parte fissa senza segnaposto (`<…>`); i segnaposto, se ci sono, vengono dopo. Il Task 13 confronta la parte fissa.
- CLI: `tollgate audit prepare [--confirm]` e `tollgate audit decline`, uscita con il codice; `AuditError` → uscita 1 con il messaggio.
- Produces in `tests/flowkit.py`: `SPEC = "docs/superpowers/specs/2026-10-20-prova.md"`, `spec_text(slices: int = 1, pitch: bool = True) -> str`; `FlowLab.write_spec(slices=1, pitch=True) -> str` (scrive e committa la spec, restituisce il blob); `FlowLab.write_l2_plan(tasks=1) -> str` (scrive il piano, `post_edit`, commit); `FlowLab.report_round(kind: str | None = None, counts: dict | None = None, *, bad_json=False, cut=False) -> subprocess.CompletedProcess` (legge il giro aperto, porta l'orologio del banco a `opened` più un secondo (`lab.now`), poi scrive `SubagentStart` e `SubagentStop` dell'agente del giro con il JSON corretto, attraverso `hookkit.Lab.hook`). **Orologi:** `audit prepare` lanciato dalla CLI usa l'ora reale, mentre gli hook del banco usano l'ora di `hookkit` (dal 9 ottobre 2026): senza questo allineamento nessun agente simulato apparterrebbe al giro. I test non tolgono mai la condizione `started >= opened` per farli passare.

- [ ] **Step 1: Test** `test_brief.py::AuditBriefTest`: `test_brief_has_code_sha_and_json_line`; `test_issue_file_only_when_present`; `test_lens_brief_has_viewpoint_and_method`; `test_plan_brief_lists_split_candidates` (task a cavallo di due profili con agenti diversi → «candidato a essere diviso»).
- [ ] **Step 2: Test** `test_audit_prepare.py` (`FlowLab(issue=7, level="L2", phase="spec_audit")`: senza `issue=` il banco non crea il lavoro):
  - `test_no_spec_refused`;
  - `test_first_round_registers_spec_path_and_launches_adversary` (una riga `agente: tollgate:spec-adversary brief: "…"`, `spec_path` registrato, giro 1 aperto);
  - `test_uncommitted_spec_refused` (worktree diverso da HEAD → «committa»);
  - `test_open_round_same_sha_reprinted_same_code`;
  - `test_open_round_other_sha_superseded`;
  - `test_dirty_round_same_sha_asks_fix` (codice 1, `STEPS["fix_spec"]`);
  - `test_clean_round_one_slice_asks_approve_spec`;
  - `test_three_slices_lens_needs_confirm_then_executor` (codice 3 con il costo; con `--confirm` lancio di `tollgate:spec-auditor` con `executor`);
  - `test_lens_closed_then_confirmation_round_if_spec_changed`;
  - `test_suspended_adversarial_goes_to_lens_or_approve` (dopo «avversariale sospeso» sulla spec attuale: con una fetta «approve spec», con tre il ciclo a lenti; I-2 della revisione del piano);
  - `test_adversary_off_three_slices_reaches_lens`;
  - `test_superseded_first_lens_cycle_does_not_ask_confirm_again`;
  - `test_plan_written_by_bash_is_found` (piano committato senza `post_edit` → `plan_path` registrato e giro del piano);
  - `test_decline_opens_block` (`audit decline` → blocco `DECLINE_REASON`, fase `blocked`; poi `prepare` rifiuta con `STEPS["resolve"]`);
  - `test_components_off` (`spec_adversary = false` e una fetta → subito `approve_spec`; `plan_adversary = false` in `plan` → fase `approval` senza giri);
  - `test_plan_round_then_clean_moves_to_approval` (giro del piano pulito → `plan → approval`, causa `audit_clean`);
  - `test_l1_refused`; `test_models_override_in_launch_line`.
- [ ] **Step 3: Test** `test_check_cli_calls.py::test_audit_is_coordinator_only` (con `agent_id`: `audit prepare` → 2; dalla sessione principale ammesso, nessuna voce di segnale).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: audit prepare e audit decline (giri, lenti, passaggio plan → approval)».

---

### Task 6: Report dei giri a `SubagentStop`

**Files:**
- Create: `bin/tollgate_checks/audit_round.py`
- Modify: `bin/tollgate_checks/_common.py` (`awaiting_audit`), `bin/tollgate_checks/subagent_stop.py` (salta i giri in attesa; docstring «gli avversari sono di P3b» corretta), `bin/tollgate_hooks/apply.py` (`audit_report`)
- Test: `tests/test_check_audit_round.py`

**Interfaces:**
- Produces in `_common.py`: `awaiting_audit(ctx, row) -> sqlite3.Row | None`: il giro aperto del lavoro del subagente se `row["type"] == audits.AGENTS[giro.kind]`, la riga è `running` o `interrupted` e `row["started"]` non è nullo né precedente a `giro.opened` (decisione 4).
- Produces: modulo `audit_round` (`CHECK = {"api": 1, "events": ["subagent_stop"], "component": None, "order": 15}`; il componente del tipo si controlla dentro con `audits.COMPONENTS`): decisione 5; con il componente del tipo spento il giro si chiude come se l'agente non contasse (`subagent_finish` e nessun report).
- Produces in `apply.py`: `audit_report` (dati: `work`, `kind`, `number`, `counts`, `body`, `extra`: righe dei rilievi meccanici). Rilegge il giro: se non è più aperto con quel numero (superato, chiuso) ignora e registra l'evento `veto` {event: "subagent_stop", rule: "audit_round", reason: "giro non più aperto"}, mai un'eccezione. Scrive il report con `approvals.render_report` in scrittura atomica (file temporaneo e `os.replace`), chiude il giro, rigenera `spec-lens-stato.md` per le lenti, poi i blocchi dei tetti con `phases.open_block` fuori transazione. `apply.OPS` passa a 28 voci.

- [ ] **Step 1: Test** `test_check_audit_round.py` (`FlowLab` L2 con un giro aperto):
  - `test_valid_report_written_and_round_closed` (file `spec-adversarial-1.md` con intestazione valida per `parse_report_header`, `outcome` calcolato, evento `spec_audit_round`);
  - `test_missing_cosa_non_fare_adds_major` (criterio 41, seconda frase: spec senza `## Cosa non fare`, l'agente dichiara zero rilievi → `major: 1`, giro non pulito, riga «rilievo meccanico» nel report);
  - `test_spec_pitch_off_no_mechanical_finding` (criterio 18, `spec_pitch`);
  - `test_bad_json_vetoed_twice_then_needs_you`;
  - `test_tampering_agent_needs_you` (impronta cambiata);
  - `test_handback_report_used_in_auto_mode`;
  - `test_late_report_of_superseded_round_ignored` (Review Focus 3: l'agente del giro 1, partito prima che il giro 2 dello stesso tipo si aprisse, non riceve veti né tocca il giro 2; `subagent_stop` lo chiude `done`; il giro 2 si apre chiamando `audit.prepare(..., now=<dopo lo started dell'agente 1>)` dalla libreria, non dalla CLI, perché l'orologio del banco è avanti rispetto all'ora reale);
  - `test_invalid_report_keeps_round_open_and_reason_has_no_raw_values`;
  - `test_fourth_dirty_adversarial_round_opens_cap_block` (criterio 24: quarto giro con `major` → `needs_you` con `CAP_REASONS["spec-adversarial"]`);
  - `test_lens_cycle_regenerates_state_file`;
  - `test_lens_cap_opens_block` (30 cicli con l'audit aperto);
  - `test_plan_round_cap_after_two`;
  - `test_task_reviewer_and_final_reviewer_paths_unchanged`;
  - `test_report_file_committable_and_protected` (Review Focus 4: `git add docs/superpowers/reviews/7/spec-adversarial-1.md` e `git commit` dal coordinatore in `spec_audit` attraverso `PreToolUse Bash` → ammessi; `PreToolUse Write` sullo stesso file → `deny`);
  - `test_every_branch_emits_subagent_finish`;
  - `test_ops_count_is_28` (triage 40).
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: report dei giri di audit a SubagentStop, tetti dei giri».

---

### Task 7: `approve spec`, `approve plan` e sospensioni da `resolve`

**Files:**
- Create: `bin/tollgate_flow/l2acts.py`
- Modify: `bin/tollgate_flow/actapply.py` (voci di `APPLIERS`, `_resolve` sui tetti dell'audit, testo di `_pick`), `bin/tollgate_core/violations.py` (`locked_docs`, decisione 19)
- Test: `tests/test_l2acts.py`, `tests/test_check_common.py`

**Interfaces:**
- Consumes: `audit.adversarial_ok` (Task 5), `audits.*`, `auditrules.is_clean`, `specdoc.slices`, `specdoc.slice_titles`, `approvals.render_approval`, `approvals.locate_spec_approval`, `scope.register_plan`, `plan.check_plan`, `phases.set_phase` con le cause della decisione 11.
- Produces in `l2acts.py` (firma degli applicatori di P3a: `(conn, state, work, act, args, now, session) -> str`, i rifiuti sollevano `l2acts.Refused(Exception)`, che `actapply.apply_act` converte in `ActApplyError`; `l2acts` non importa `actapply`):
  - `approve_spec(...)` (decisione 9);
  - `approve_plan(...)` (decisione 10);
  - `suspend_on_resolve(conn, work, block_reason: str, *, now) -> str | None` (decisione 7: restituisce l'etichetta della sospensione o `None`). Gira prima di `close_block`, in una transazione sua: se il processo muore tra le due, il blocco resta aperto e un nuovo `resolve` riscrive la stessa sospensione (idempotente).
- Produces in `actapply.APPLIERS`: `("approve", "spec")`, `("approve", "plan")`; `_resolve` chiama `suspend_on_resolve` prima di chiudere il blocco e aggiunge l'etichetta al messaggio; il messaggio di `_pick` senza atto elenca anche `spec`, `plan` e `reopen`.
- Produces in `violations.locked_docs`: la spec bloccata con l'approvazione trovata da `locate_spec_approval` sui file del worktree (decisione 19).

- [ ] **Step 1: Test** `test_l2acts.py::ApproveSpecTest` (`FlowLab` L2, spec scritta, giri simulati con `report_round`):
  - `test_refused_after_dirty_round_accepted_after_clean` (criterio 24);
  - `test_cap_resolve_suspended_then_approve` (criterio 24 e Review Focus 6: quarto giro con `major` → blocco, fase `blocked`, `audit prepare` e `approve spec 1` rifiutano; `resolve` → «avversariale sospeso», fase `spec_audit`; `audit prepare` → «approve spec»; `approve spec 1` → `adversarial: suspended` nel file);
  - `test_suspended_round_then_dirty_round_reblocks` (Review Focus 3);
  - `test_wrong_slice_count_refused` (criterio 24: `approve spec 1` su tre fette → rifiuto con «3»);
  - `test_three_slices_refused_until_lens_closed_or_suspended` (criterio 24);
  - `test_spec_changed_after_last_round_refused` (criterio 24);
  - `test_reopen_without_changes_then_approve_again` (dopo `reopen spec` senza modifiche alla spec l'ultimo giro avversariale sta ancora sul blob: `approve spec` accettato; i giri del piano non contano);
  - `test_open_round_refuses_approve`;
  - `test_adversary_off_lens_closed_then_spec_changed_refused` (tre fette, `spec_adversary = false`, audit a lenti chiuso, spec corretta dopo l'ultimo ciclo → `approve spec 3` rifiutato, `audit prepare` lancia un ciclo di conferma; dopo il ciclo `approve spec 3` accettato);
  - `test_adversary_off_lens_suspended_then_spec_changed` (stesso caso con l'audit sospeso al tetto: ciclo di conferma senza nuovo blocco, poi `approve spec 3` con `lens: suspended`);
  - `test_spec_audit_off_three_slices_accepted` (criterio 35: `lens: off`);
  - `test_spec_adversary_off_accepted_without_rounds` (criterio 18);
  - `test_writes_file_and_moves_to_plan` (`parse_approval` ha `kind`, `path`, `sha` = blob, `slices`, `act_id`; fase `plan`, causa `approve_spec`);
  - `test_three_slices_propose_issues_and_start_spec`.
- [ ] **Step 2: Test** `test_l2acts.py::ApprovePlanTest`:
  - `test_plan_sha_is_the_approved_version` (criterio 37: piano corretto dopo un giro avversariale non pulito, nuovo giro pulito, `approve plan` → `plan_sha` = blob approvato, scope e task registrati, `plan-approval.md` con `spec_sha`, fase `execution`, causa `approve_plan`);
  - `test_refused_outside_approval`;
  - `test_refused_when_spec_changed_after_approval`;
  - `test_refused_when_last_plan_round_on_other_spec_sha`;
  - `test_plan_adversary_off` (criterio 18);
  - `test_repeat_after_interruption_does_not_register_twice`;
  - `test_plan_approval_committable_in_execution` (Review Focus 4: dopo `approve plan`, `git add` di `plan-approval.md` e `git commit` dal coordinatore attraverso `PreToolUse Bash` → ammessi; poi un commit dell'implementatore su un file dello scope → ammesso).
- [ ] **Step 3: Test** `test_check_common.py::LockedDocsTest::test_spec_locked_by_real_approve_spec` (criterio 24 e 37: dopo `approve spec` reale, `PreToolUse Edit` sulla spec in `plan` → `deny`; su `spec-approval.md` → `deny`).
- [ ] **Step 4: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: approve spec, approve plan, sospensioni dei tetti dell'audit».

---

### Task 8: `reopen spec|plan`

**Files:**
- Modify: `bin/tollgate_flow/l2acts.py` (`reopen`), `bin/tollgate_flow/actapply.py` (voci `("reopen", "spec")`, `("reopen", "plan")`)
- Test: `tests/test_l2acts.py`

**Interfaces:**
- Consumes: `scope.reset_plan`, `phases.set_phase(..., "reopen_spec"|"reopen_plan")`, `subagents.running`, `config.is_readonly`.
- Produces in `l2acts.py`: `reopen(conn, state, work, act, args, now, session) -> str` (decisione 12).

- [ ] **Step 1: Test** `test_l2acts.py::ReopenTest`:
  - `test_reopen_spec_from_plan_unlocks_and_requires_new_approval` (criterio 37);
  - `test_reopen_needs_reason`;
  - `test_reopen_refused_with_running_task_or_writer`;
  - `test_reopen_plan_l1_from_execution` (fase `plan`, scope tolto, `post_edit` del piano corretto registra di nuovo);
  - `test_reopen_spec_then_new_approval_end_to_end` (Review Focus 1: `approve spec`, commit, `reopen spec`, spec corretta e committata, nuovo giro pulito, `approve spec` → `sha` nuovo nel file, spec bloccata in `plan`; poi piano, giro, `approve plan`, task chiuso, `finish check` → voce `approvals` vera e nessun `out_of_scope`);
  - `test_reopen_plan_then_reapprove_registers_new_scope` (Review Focus 2: L2 in `execution`, `reopen plan`, piano con un file in più, giro pulito, `approve plan` → scope con il file nuovo, task `pending`, `task start 1` legge il nuovo `plan_sha`).
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: reopen spec e reopen plan».

---

### Task 9: Fette successive, `approvals` nella DoD, cartelle 18.1, `adopt` di L2

**Files:**
- Modify: `bin/tollgate_flow/start.py` (`spec`), `bin/tollgate_core/cli.py` (`start --spec PERCORSO`), `bin/tollgate_flow/finishcheck.py` (`_approvals` con `check_l2`, `_own_document` con `locate_spec_approval`), `bin/tollgate_flow/openpr.py` (`facts`), `bin/tollgate_flow/adopt.py` (`_gather`, decisione 16)
- Test: `tests/test_start.py`, `tests/test_finishcheck.py`, `tests/test_openpr.py`, `tests/test_adopt.py`, `tests/test_criteria_p3c.py` (classe `LaterSliceTest`). Test esistenti da riscrivere, perché il comportamento cambia per decisione: `tests/test_finishcheck.py` (i test L2 delle approvazioni intorno a `test_l2_approvals_follow_the_files`, che oggi non hanno `spec_sha` né report) e `tests/test_adopt.py` (il caso L2 con piano e senza `plan-approval.md`: la fase attesa passa da `approval` a `plan`, decisione 16).

**Interfaces:**
- Produces in `start.py`: `start(..., spec: str | None = None)` (decisione 14); il riepilogo di un lavoro nuovo con `--spec` dice «spec approvata: <percorso> (approvazione in <cartella>)».
- Produces in `finishcheck.py`: `_approvals(wt, work) -> tuple[bool, str]` calcolato con `approvals.check_l2` sui file di `git.ls_files_at(wt, "HEAD", REVIEWS_DIR)`.
- Produces in `openpr.facts`: `spec_reviews_dir`, `plan_reviews_dir`, `spec_audit` della decisione 15.
- Produces in `adopt.py`: fase L2 della decisione 16.

- [ ] **Step 1: Test** `test_start.py::StartSpecTest`:
  - `test_approved_spec_starts_in_plan` (criterio 24: spec e approvazione dell'issue 3 sul predefinito, `start 9 --spec <percorso>` → L2, fase `plan`, `spec_path`);
  - `test_without_approval_refused` (criterio 24);
  - `test_changed_spec_needs_confirm_then_spec_audit`;
  - `test_bad_path_refused` (assoluto, `..`, fuori da `docs/superpowers/specs/`, assente sul predefinito);
  - `test_spec_ignored_on_resume_with_warning`;
  - `test_cli_passes_spec` (argomento della CLI fino a `start.start`).
- [ ] **Step 2: Test** `test_finishcheck.py::L2ApprovalsTest`: `test_reports_required` (senza `spec-adversarial-*.md` → `approvals` falsa con il problema); `test_complete_l2_is_green`; `test_kind_mismatch_is_false` e `test_must_have_tests_off` (triage 31: con `must_have_tests = false` la voce `must_have` non blocca).
- [ ] **Step 3: Test** `test_openpr.py::L2FactsTest::test_dirs_and_spec_audit_from_located_approval` (lavoro con la propria approvazione → la propria cartella; fetta successiva → cartella dell'issue della prima fetta, `spec_audit` da quell'approvazione).
- [ ] **Step 4: Test** `test_adopt.py::AdoptL2Test`: `test_later_slice_with_plan_approval_goes_execution`, `test_later_slice_without_plan_approval_goes_spec_audit`, `test_plan_without_approval_goes_plan_with_adversary_on` e `test_plan_without_approval_goes_approval_with_adversary_off` (decisione 16).
- [ ] **Step 5: Test** `test_criteria_p3c.py::LaterSliceTest::test_later_slice_end_to_end` (Review Focus 5: issue 3 approvata e unita sul predefinito; `start 9 --spec` attraverso `hooks/run` e `bin/tollgate`; Edit sulla spec → `deny`; piano, giro del piano, `approve plan`; un task chiuso; `finish check` verde con `approvals`; `open-pr` con `spec_reviews_dir` dell'issue 3; DB cancellato e `adopt 9` → fase `execution`).
- [ ] **Step 6: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: start --spec, voce approvals con i report, cartelle 18.1 e adopt delle fette successive».

---

### Task 10: Prossimo passo e tetti dell'audit in `status`

**Files:**
- Modify: `bin/tollgate_flow/checkpoint.py`
- Test: `tests/test_checkpoint.py`

**Interfaces:**
- Consumes: `audit.peek`, `audits.CAP_REASONS`, `audits.DECLINE_REASON`.
- Produces: `next_step` per `spec_audit`, `plan` di L2 senza task e `approval` (decisione 20); `CAPS` con i tre tetti dell'audit e il rifiuto del costo (non `CAP_PREFIXES`); `_cap_step` dice `audit.STEPS["resolve"]` per quei blocchi.

- [ ] **Step 1: Test** `test_checkpoint.py`: `test_l2_phases_point_to_audit_prepare` (sostituisce il test che cercava «P3c»); `test_approval_points_to_approve_plan`; `test_audit_caps_in_stopped_by` (`status` dice «tetto: giri avversariali della spec»); `test_audit_cap_step_is_resolve_not_rounds` (decisione 20); `test_steps_use_program_command` esteso alle fasi L2.
- [ ] **Step 2: Fallimento, implementazione, verifica, `tests/run`, commit** «tollgate P3c: prossimo passo nelle fasi L2 e tetti dell'audit».

---

### Task 11: Rinviati di P3b in core, analisi e hook

**Files:**
- Modify: `bin/tollgate_core/config.py` (riga 21), `bin/tollgate_checks/task_verdict.py`, `bin/tollgate_flow/taskcmd.py`, `bin/tollgate_checks/post_bash.py`, `bin/tollgate_core/git.py` (riga 23), `bin/tollgate_analysis/verdicts.py` (riga 25), `bin/tollgate_flow/finishcheck.py` (riga 32), `bin/tollgate_core/violations.py`, `bin/tollgate_hooks/apply.py` e `bin/tollgate_flow/finalreview.py` (righe 38, 39)
- Test: `tests/test_cli.py`, `tests/test_config.py`, `tests/test_check_task_verdict.py`, `tests/test_verdicts.py`, `tests/test_profiles.py`, `tests/test_check_final_review.py`, `tests/test_finishcheck.py`

**Interfaces:**
- Produces in `git.py`: `range_base(repo, first_commit: str) -> str` (`resolve_ref(<c>^)` o l'albero vuoto), usata da `taskcmd._range`, `task_verdict._task_files` e `post_bash` (riga 23).
- Produces in `violations.py` (`tollgate_core`, perché né `tollgate_hooks` né `tollgate_checks` importano `tollgate_flow`): `active_profile_names(cfg, wt, work) -> list[str]` (profili attivi sul diff del lavoro, con il ripiego `default_ref` per la base), usata da `finalreview` e da `apply._final_rules` (riga 38).

Ogni riga del triage, con il suo test (righe di `docs/sdd/2026-10-19-tollgate-p3b-chiusura/deferred-minors.md`):

- [ ] **Step 1 (riga 5):** `test_cli.py::ArgvSignalTest`: `test_second_start_without_new_signal_refused` (stessa voce consumata) e `test_level_option_in_argv_matches` (`start 7 --level L1` col segnale `["start", "7", "--level", "L1"]` → accettato), con `FlowLab` e `hooks/run`.
- [ ] **Step 2 (riga 21):** `config.py` usa `re.fullmatch`; `test_config.py::ProfileNamesTest::test_trailing_newline_name_falls_back`.
- [ ] **Step 3 (righe 22, 23):** `test_check_task_verdict.py::TaskFilesTest`: profilo attivato solo da `paths` sul diff del task (regole `[blocca]` di quel profilo applicate) e diff illeggibile (nessun profilo, fail-closed come oggi: ogni `R-…` bloccante); `range_base` con un test in `test_git.py`; `import json` nel gruppo della libreria standard.
- [ ] **Step 4 (riga 24):** in `test_verdicts.py` e `test_profiles.py` le classi dopo `unittest.main()` vanno sopra il blocco `if __name__ == "__main__"`; `python3 -B tests/test_verdicts.py` le esegue (stesso numero di test della scoperta).
- [ ] **Step 5 (riga 25):** `parse_verifier_results` riporta «ogni risultato ha un id» una volta sola; `test_verdicts.py::VerifierResultsTest::test_missing_id_problem_once`.
- [ ] **Step 6 (riga 32):** docstring di `finishcheck._own_document`: l'esenzione di `reviews/<N>/` vale a ogni livello (testo, nessun test).
- [ ] **Step 7 (righe 38, 39, 40):** `apply._final_rules` e `finalreview` usano `violations.active_profile_names` (stesso risultato con `default_ref` come ripiego: `test_check_final_review.py::RulesTest::test_rules_with_default_ref_fallback`); `apply._review_report` con `ValueError` registra l'evento `veto` {rule: "final_review", reason} invece di un `return` muto (`test_rejected_report_leaves_trace`); `test_check_final_review.py::ReviewerTest::test_interrupted_reviewer_that_changed_files_tampered`.
- [ ] **Step 8: Verifica** dei moduli toccati e `tests/run`; **commit** «tollgate P3c: rinviati di P3b in core, analisi e hook (righe 5, 21-25, 32, 38-40)».

---

### Task 12: Rinviati di P3b nel flusso e nei test

**Files:**
- Modify: `bin/tollgate_analysis/brief.py` (righe 34, 36, 72), `bin/tollgate_flow/finalreview.py` (34, 36), `bin/tollgate_flow/actapply.py` (49, 50), `bin/tollgate_flow/taskcmd.py` (71), `bin/tollgate_flow/adopt.py` (60, 62)
- Test: `tests/test_brief.py`, `tests/test_finalreview.py`, `tests/test_actapply.py`, `tests/test_taskcmd.py`, `tests/test_sync.py`, `tests/test_adopt.py`, `tests/test_closing.py`, `tests/test_fixtask.py`, `tests/test_criteria_p3b.py`

- [ ] **Step 1 (righe 34, 36):** `FinalBrief` dice, quando `sha` del ciclo e HEAD differiscono per un rebase con lo stesso `patch-id`, «il ciclo è stato aperto su <sha>; HEAD è <head> dopo un rebase senza modifiche di contenuto: rivedi il diff di HEAD»; `issue_file` è `None` se `.tollgate-run/<N>/issue.md` non esiste e il brief non lo nomina. Test in `test_brief.py` e `test_finalreview.py`.
- [ ] **Step 2 (righe 49, 50):** `approve finding` su un rilievo confermato di un ciclo non ultimo chiude il blocco dei cicli se aperto (decisione 25); `recompute_outcome` che solleva `ValueError` (ultimo ciclo `superseded`) diventa un rifiuto con il messaggio, dopo che la decisione è scritta. Test `test_actapply.py::ApproveFindingTest::test_old_cycle_finding_closes_cycles_block` e `test_superseded_last_cycle_is_a_refusal`.
- [ ] **Step 3 (riga 51):** `test_taskcmd.py::FixRoundsTest::test_sixth_round_name_launch_inherit` (dopo `approve rounds 1`: nome `tg-7-t1-r6`, `pending = launch`, `model: inherit` nel brief).
- [ ] **Step 4 (riga 55):** `test_sync.py::SyncEdgeTest`: `test_intent_recorded_before_rebase`; `test_rebase_in_progress_at_start_refused`; `test_ff_only_failure_blocks`; `test_finish_check_red_after_rebase` (il messaggio è il rosso, non il rifiuto, m4).
- [ ] **Step 5 (righe 60, 62):** `adopt` con ramo locale e remoto su punte diverse avvisa «ramo locale e remoto diversi: uso la punta locale <sha>»; `sqlite3.Error` in `acts.consume` dopo `create_work` dà codice 4 «lavoro creato, atto non consumato: …», come `start`. Test in `test_adopt.py`.
- [ ] **Step 6 (riga 67):** `test_closing.py`: `test_cleanup_from_inside_worktree`; `test_cleanup_with_missing_worktree_dir`; `test_start_confirm_closed_pr_with_other_confirmations`.
- [ ] **Step 7 (righe 71, 72, 73):** `taskcmd._fix_files` instrada sui file di tutti i rilievi del ciclo usati per creare il task, senza filtrare per decisione dell'utente; `brief._finding` stampa la gravità effettiva (`reviews.effective_severity` se la riga la ha, altrimenti quella dichiarata) con l'originale tra parentesi se diversa. Test in `test_fixtask.py`: `test_routing_stable_after_dismiss`, `test_brief_shows_effective_severity`, `test_from_findings_rollback_on_error`, `test_l0_refused`, `test_cli_from_gate`, `test_gate_fence_longer_than_any_backtick_run` (asserzione esatta sul recinto).
- [ ] **Step 8 (riga 82):** in `test_criteria_p3b.py` il test del criterio 26 asserisce il codice e la riga «rifiuto:» di `open-pr`, l'helper si chiama `prepare_needs_fix_cycle`, e un test nuovo `test_second_finish_is_new_cycle` porta dal programma vero il ciclo 2 a `ok` e `open-pr` a 0.
- [ ] **Step 9: Verifica, `tests/run`, commit** «tollgate P3c: rinviati di P3b nel flusso e nei test (righe 34-82)».

---

### Task 13: Agenti, skill e contratto skill-codice

Le skill si scrivono **dopo** i sottocomandi (lezione del Task 16 di P3b): ogni codice d'uscita e ogni riga «prossimo passo» citati vengono dalle costanti dei Task 5-10, e un test lo controlla.

**Files:**
- Create: `agents/spec-adversary.md`, `agents/spec-auditor.md`, `agents/plan-adversary.md`, `skills/spec-audit/SKILL.md`, `skills/spec-audit/references/dimensioni.md`, `skills/reopen/SKILL.md`, `tests/test_skill_contract.py`
- Modify: `skills/approve/SKILL.md`, `skills/start/SKILL.md` (anche riga 78: testo morto sulla PR chiusa sotto «1, rifiuto»), `skills/resolve/SKILL.md`, `skills/finish/SKILL.md` (voce `approvals` in L2), `skills/status/SKILL.md` (tetti dell'audit), `agents/implementer.md` e gli altri agenti che citano il programma (riga 79), `tests/test_manifest.py` (righe 77 e 79)

**Interfaces:**
- Consumes: `audit.OK/REFUSED/NEEDS_CONFIRM`, `audit.STEPS`, `start.OK/REFUSED/NEEDS_CONFIRM/INCOMPLETE`, `finishcheck.OK/RED/REFUSED`, `sync.OK/REFUSED/BLOCKED/REVIEW_NEEDED`, i testi delle righe `agente:` di `audit prepare`, i campi della riga JSON della decisione 5.
- Produces: i nomi `tollgate:spec-adversary`, `tollgate:spec-auditor`, `tollgate:plan-adversary`, già in `readonly_agents`; la skill `tollgate:spec-audit`.

Contenuti (testo in italiano, identificatori in inglese, programma sempre `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` con il ripiego della riga «programma», come le skill di P3a e P3b):

**`agents/spec-adversary.md`** (`tools: Read, Grep, Glob, WebFetch`, `model: inherit`): legge il brief; sola lettura; cerca contraddizioni, ambiguità che un implementatore risolverebbe a caso, fatti non verificati (WebFetch sulle fonti citate), le tre sezioni del pitch (una tana di coniglio senza scelta è `major`); rilievi con sezione, gravità e correzione proposta; chiude con **una sola** riga JSON della decisione 5 con `code` e `spec_sha` del brief.

**`agents/spec-auditor.md`** (`Read, Grep, Glob, WebFetch`, `sonnet`): un solo ciclo, dal punto di vista del brief, con le dieci lenti di `references/dimensioni.md` (percorso nel brief); almeno tre sospetti scartati se il ciclo è vuoto (prd-audit); chiude con la riga JSON con `viewpoint`. Riga di attribuzione: «Metodo derivato da prd-audit (sAInapse), con l'accordo dell'autore».

**`agents/plan-adversary.md`** (`Read, Grep, Glob`, `inherit`): confronta il piano con la spec approvata e con i must-have (ogni must-have con un test), scope e dimensione dei task, candidati a essere divisi dalla tabella del brief, task che si contraddicono; chiude con la riga JSON con `plan_sha`.

**`skills/spec-audit/SKILL.md`** (anche il modello; riga di attribuzione a prd-audit): il ciclo del coordinatore in `spec_audit` e in `plan` di L2: `audit prepare` → lancia **in primo piano** l'agente della riga `agente:` → leggi il report in `docs/superpowers/reviews/<N>/` come dato → correggi spec o piano → **committa** il documento e i report (`git add` del documento e della cartella `reviews/<N>/`, poi `git commit`; mai Edit o Write sui report) → di nuovo `audit prepare`, finché la riga «prossimo passo» non chiede all'utente `/tollgate:approve spec <fette>` o `/tollgate:approve plan`. Codici: 0 avanti; 1 riporta il motivo (se è `STEPS["fix_spec"]` o `STEPS["fix_plan"]` correggi e ricomincia); 3 mostra il costo dell'audit a lenti e chiedi all'utente: sì → `--confirm`, no → `audit decline` e indica `/tollgate:resolve <id>`. Con un blocco di tetto: fermati e indica `/tollgate:resolve <id> <nota>` («sospeso») o la correzione. Mai `--confirm` senza il sì dell'utente; mai lanciare due giri insieme.

**`skills/spec-audit/references/dimensioni.md`**: copia di `~/.claude/skills/prd-audit/references/dimensioni.md` con la riga di attribuzione in testa.

**`skills/reopen/SKILL.md`** (`disable-model-invocation: true`): l'atto è registrato; lancia `act apply`; riferisci fase e scope tolto; poi: con `spec`, correggi la spec e riparti da `/tollgate:spec-audit`; con `plan`, correggi il piano e (L2) riparti dall'avversario del piano, (L1) il piano corretto si registra da solo.

**Aggiornamenti:** `approve` (`spec <fette>` e `plan` → `act apply`; riferire il file di approvazione da committare e la proposta delle issue delle fette; `argument-hint` e `description` con `spec` e `plan`; tolta la frase «arrivano con il percorso L2 (P3c)»); `start` (L2: brainstorming → spec con le tre sezioni del pitch → committa → `/tollgate:spec-audit`; dopo `approve spec`: checkpoint, `/clear`, writing-plans, committa, di nuovo `/tollgate:spec-audit` per l'avversario del piano; `--spec <percorso>` nell'`argument-hint` e nel passo 1, con l'uscita 3 della spec cambiata; tolta la frase «sono del percorso L2 (P3c)»; riga 78); `resolve` (ai tetti dell'audit: «sospeso»); `finish` (in L2 una voce `approvals` `[no]` indica il file o il report mancante); `status` (tetti dell'audit).

- [ ] **Step 1: Test** `test_manifest.py`:
  - `test_audit_agents_frontmatter` (strumenti esatti della decisione 21, senza `Edit`, `Write`, `Bash`; modelli; attribuzione nello `spec-auditor`);
  - `test_audit_json_fields_in_agent_text` (i campi della riga JSON della decisione 5 in ogni agente);
  - `test_reopen_user_only` e `test_spec_audit_model_invocable`;
  - `test_agents_use_program_command_form` (riga 79: ogni agente che nomina `bin/tollgate` usa `python3 "…/bin/tollgate"`, mai apici singoli);
  - `test_dimensioni_copied_with_attribution` (solo la copia nel repo: il test non legge `~/.claude/skills`);
  - i test esistenti che cercano sottostringhe nelle skill (riga 77) passano al contratto qui sotto quando la frase è un codice d'uscita o un passo.
- [ ] **Step 2: Test** `test_skill_contract.py`: una tabella `(skill, sezione, modulo, costanti)`: per `start` (`OK`, `REFUSED`, `NEEDS_CONFIRM`, `INCOMPLETE`), `finish` (`finishcheck`), `sync`, `spec-audit` (`audit`): l'insieme dei codici delle righe `- **<n>, …**` della sezione della skill è **uguale** all'insieme delle costanti (le skill `finish` e `sync` passano a questa forma di riga, oggi `finish` scrive «Uscita 0, verde»); la parte fissa di ogni testo di `audit.STEPS` (fino al primo `<`) compare nella skill `spec-audit`; ogni sottocomando nominato nelle skill (`<programma> <sub> …`) esiste nel parser di `cli.build_parser()`; nessuna skill contiene «P3c».
- [ ] **Step 3: Fallimento, scrittura dei file, `tests/run`**; se `claude` è disponibile `claude plugin validate --strict .` deve riuscire (esito nel report).
- [ ] **Step 4: Commit** «tollgate P3c: agenti dell'audit, skill spec-audit e reopen, contratto tra skill e codice».

---

### Task 14: Prova reale del percorso L2 con `claude -p`

Una sola esecuzione reale del percorso skill → CLI → hook → agenti in L2, fino all'esecuzione del primo task. Chiude i rischi che i test non vedono: frontmatter degli agenti nuovi, righe di lancio lette dal modello, riga JSON dei giri, atti `approve spec` e `approve plan` digitati in una sessione legata.

**Files:**
- Create: `spikes/run-p3c-flow.sh`, `docs/verifiche/2026-10-20-p3c-prova-flusso.md`

**Regole di cautela (vanno nel brief):**
- tutto in `/tmp/tollgate-p3c/flow`, sul modello di `spikes/run-p3b-flow.sh` (lo script rifiuta un `FLOW` diverso prima di ogni `rm -rf`);
- `TOLLGATE_STATE=/tmp/tollgate-p3c/flow/state` con la sentinella; `TOLLGATE_GH=<worktree>/tests/fakegh.py` con l'issue 1 aperta (`author_association OWNER`), stati del predefinito `success`, nessuna PR;
- `claude -p --plugin-dir <worktree del ramo> --model sonnet`; mai `claude plugin install`; nessun comando scrive sotto `~/.claude`;
- **nessun push in rete** (decisione 23): `remote.origin.url = https://github.com/prova/flow.git` con `url.<repo nudo locale>.insteadOf`; prima di ogni passo lo script controlla `git remote get-url --push origin`;
- **dal passo 2 ogni `claude -p` parte dalla cartella del worktree del lavoro** (sessione nuova, legata da `SessionStart`); lo script verifica che la cartella sia il worktree `tg/1-*` sotto `/tmp/tollgate-p3c/flow` e si ferma altrimenti; mai `--continue` dalla radice;
- mai `pkill`, `killall` o `kill` per pattern.

- [ ] **Step 1: Script** `spikes/run-p3c-flow.sh` (`prepara|passo1|…|libero "<prompt>"|registra|tutto`). `prepara`: repo come P3b (stdlib, `tools/unittest_junit.py`, gate installato) più una spec di prova `spec-L2.md` con una fetta, «Tane di coniglio» con le scelte e «Cosa non fare», e un piano di prova `piano-L2.md` che passa `plan-check` (verificato dallo script). Passi:
  1. dal checkout: `/tollgate:start #1 L2`; dopo il passo lo script controlla che nel ramo non ci sia ancora nessun file sotto `docs/superpowers/specs/` (il modello potrebbe aver avviato il brainstorming e scritto una spec sua: in quel caso si ferma con la nota «rifare il passo 1», perché il «primo file nuovo» sarebbe quella spec);
  2. dal worktree: «la spec è in <file>: copiala in `docs/superpowers/specs/2026-10-20-prova.md` senza cambiarla, committala, poi segui `/tollgate:spec-audit` finché audit prepare non chiede `/tollgate:approve spec 1`»;
  3. dal worktree: `/tollgate:approve spec 1`;
  4. dal worktree: «il piano è in <file>: scrivilo con lo strumento Write in `docs/superpowers/plans/2026-10-20-prova.md` (così passa da plan-check), committalo, poi segui `/tollgate:spec-audit` per l'avversario del piano finché non chiede `/tollgate:approve plan`»;
  5. dal worktree: `/tollgate:approve plan`;
  6. dal worktree: `/tollgate:execute`, fino a «task 1 `done`»;
  7. `registra`: `status`, `events`, `stats`, report in `reviews/1/`, `hooks.log`, dati del finto `gh`.

  `libero "<prompt>"` lancia un prompt dal worktree (per esempio `/tollgate:resolve <id> <nota>` a un tetto, o «continua con /tollgate:spec-audit»).
- [ ] **Step 2: Eseguire.** Esito atteso: almeno un giro `spec-adversarial` chiuso con report in `reviews/1/`, `spec-approval.md` con lo `sha` della spec, fase `plan`, almeno un giro `plan-adversarial`, fase `approval` poi `execution` con `plan_sha` = blob del piano approvato, `plan-approval.md` con `spec_sha`, task 1 `done`. Un passo che si ferma si annota con l'evento o il messaggio. Si ripete una volta dopo una correzione **solo** se la causa è un difetto di questo piano, con un commit e un test che la copre. Un esito non ottenuto si scrive «non riuscito», con la causa; un esito ottenuto in più tentativi si dichiara composito. Non si dichiara riuscito ciò che non lo è.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-20-p3c-prova-flusso.md`: versione di `claude`, sessioni reali (id e cartella di ogni passo), passi ed esiti, veti, giri e loro esiti, token (`bin/tollgate stats`), difetti e correzioni, ciò che resta non esercitato (audit a lenti, `reopen`, `--spec`, tetti, uso interattivo).
- [ ] **Step 4: Commit** «tollgate P3c: prova reale del percorso L2 con claude -p».

---

### Task 15: Criteri, revisione 24 della spec, piano principale

**Files:**
- Create: `tests/test_criteria_p3c.py` (la classe `LaterSliceTest` c'è già dal Task 9)
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 24), `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`

**Interfaces:**
- Consumes: tutto il piano.
- Produces: la tabella «Prove dei criteri di P3c» nel piano principale; i contratti reali di P3c verso P4 e P5.

- [ ] **Step 1: Test dal programma vero** (`test_criteria_p3c.py`, `FlowLab` più `hooks/run` reale come in `test_criteria_p3b.py`; i subagenti non si lanciano, i loro eventi li scrive il test):
  - `test_l2_spec_to_execution_end_to_end` (criteri 24, 37, 41): `start` L2; Write di un piano in `spec_audit` → `deny`; spec senza `## Cosa non fare` committata; `audit prepare`; `SubagentStop` dell'avversario con zero rilievi → `major` meccanico, giro non pulito; `UserPromptExpansion` di `/tollgate:approve spec 1` e `act apply` → rifiuto; spec corretta, nuovo giro pulito, `approve spec 1` → `spec-approval.md`, fase `plan`; Edit sulla spec → `deny`; piano, giro del piano non pulito, piano corretto, giro pulito → `approval`; `/tollgate:approve plan` → `plan_sha` = blob del piano corretto, fase `execution`;
  - `test_cap_and_suspension_in_pr_block` (criterio 24: quarto giro non pulito → `needs_you`; `resolve` → «avversariale sospeso»; fino a `open-pr` → blocco 18.1 con `spec_audit.adversarial == "suspended"`);
  - `test_three_slices_lens_audit_and_component_off` (criteri 24 e 35: tre fette, `approve spec 3` rifiutato finché l'audit a lenti è aperto; con `spec_audit = false` accettato e `lens: off`);
  - `test_reopen_spec_from_execution` (criterio 37).
- [ ] **Step 2: Matrice.** Nel piano principale la tabella «Prove dei criteri di P3c» (formato `file::Classe.metodo`) per 18 (`spec_adversary`, `spec_audit`, `plan_adversary`, `spec_pitch`), 24, 35 (parte locale), 37 (`plan_sha` di `approve plan`, `reopen`), 41 (seconda frase), con «Resta a» per P4 (35 nel gate: `attenzione` rosso; report e approvazioni L2 ricalcolati nel gate con `approvals.check_l2`). Un criterio senza test è un buco: il test si aggiunge nel modulo che possiede il codice.
- [ ] **Step 3: Revisione 24 della spec**: le decisioni 1-27 nelle sezioni 0 (`superseded`), 3 (agenti, skill `spec-audit` e `reopen`), 3.1 (`audit prepare|decline`, `start --spec`, `audit` del coordinatore), 5 (proposta delle issue delle fette in `approve spec`, livello L2 con `--spec`), 6.1, 6.2 (giri, codice, lettura a HEAD, punti di vista meccanici, conferma e rifiuto del costo, pitch meccanico, passaggio `plan → approval` della CLI), 8.4 (atti applicabili `approve spec`, `approve plan`, `reopen`, sospensioni da `resolve`), 7.4 e 8.3 (file di `reviews/<N>/` esenti dallo scope dei commit, decisione 26), 8.7 (voce `approvals` con `check_l2`), 12.2 (migrazione 5), 12.3 (cause `approve_spec`, `audit_clean`, `approve_plan`; `reopen` toglie la registrazione), 12.4 (`adopt` delle fette successive), 15 (criterio 41 intero a P3c), 16 (esiti del Task 1 e della prova reale), 18.1 (`spec_reviews_dir` di una fetta successiva), 18.3 (riga JSON dei giri con `code` e `plan_sha`, `render_*`), 18.4 (`plan_reset`, cause nuove), 20 (riga 24).
- [ ] **Step 4: Piano principale**: «Stato» (P3c chiuso sul ramo, merge in attesa dell'OK dell'utente, numero di test); sezione 2 (P3c); sezione 3 con i moduli reali (`audits`, `audit`, `l2acts`, `auditrules`, `specdoc`, `audit_round`), i contratti P3c → P4 (`approvals.check_l2`, `locate_spec_approval`, `parse_report_header`, prefissi dei tetti e sospensioni nel blocco 18.1), i vincoli per P4 emersi qui e i rinviati della revisione finale.
- [ ] **Step 5: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi, nessun «unclosed database».

```bash
git add tests/test_criteria_p3c.py docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md
git commit -m "tollgate P3c: prove dei criteri, spec rev 24, piano principale"
```

---

## Copertura: criteri, vincoli e rinviati → task

| Voce | Task |
|---|---|
| Criterio 18 Componenti (`spec_adversary`, `spec_audit`, `plan_adversary`, `spec_pitch`) | 5, 6, 7, 15 |
| Criterio 24 Audit della spec (sei punti) | 3 (contatore), 6 (tetto), 7 (approvazione, fette, spec cambiata, blocco), 9 (`--spec`), 15 |
| Criterio 35 Componenti spenti (parte locale; gate a P4) | 7, 15 |
| Criterio 37 Flusso dopo l'approvazione (`plan_sha` di `approve plan`, `reopen spec`) | 7, 8, 15 |
| Criterio 41, seconda frase (spec senza `## Cosa non fare` → rilievo dell'avversario) | 6, 15 |
| Parti «Resta a P3c» della matrice (18: chiavi L2; 37: `plan_sha`; 41: seconda frase) | come sopra |
| Vincoli per P3c (1)-(6) del piano principale | vedi «Rilievi ripresi qui» |
| Vincoli per P3b e P3c (1) segnale, (2) programma | Global Constraints, 5, 13 |
| Rinviato della riga 83 (recinti del piano) | 2 |
| P1: `from_approved_spec` senza `spec_path` | 4 |
| Triage P3b, righe 5, 21-25, 30-32, 38-40 | 11 (30 e 31 nei Task 2 e 9) |
| Triage P3b, righe 34, 36, 49-51, 55, 60, 62, 67, 71-73, 82 | 12 |
| Triage P3b, righe 77-79 | 13 |
| Sezioni 6.2, 8.4 (`approve spec`, `approve plan`, `reopen`), 18.3 della spec | 2-10 |
| Review Focus 1-6 | 8, 8, 6 e 7, 6 e 7, 9, 7 |
| Decisioni 26-27 (esenzione di `reviews/<N>/`, fasi e blocchi) | 4, 6, 7 |
