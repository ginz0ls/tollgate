# Revisione Task 10 (90b2ebe)

### Aderenza
- ✅ Frontmatter agenti: implementer `Read, Edit, Write, Bash, Grep, Glob, Skill`, `model: inherit`, `maxTurns: 60` (agents/implementer.md:2-6); task-reviewer `Read, Grep, Glob, Bash`, `model: sonnet`, senza Edit/Write (agents/task-reviewer.md:2-6). Attribuzione presente in entrambi e in execute.
- ✅ Campi alla lettera: report dell'implementatore = `report.REQUIRED` + `must_have`, `size_reason` (bin/tollgate_analysis/report.py:8) e 18.5; verdetto del revisore = `parse_task_verdict` (verdicts.py:46-83) e 18.5.
- ✅ `approve`, `resolve`, `setup`, `off`, `on` con `disable-model-invocation: true`; `start`, `execute`, `status` senza.
- ✅ `setup` non scrive in `~/.claude`; propone solo la riga (C21).
- ✅ Licenze: `LICENSES/superpowers-MIT.txt` identica (diff) al LICENSE di Superpowers 7.0.0; `LICENSE` MIT sAInapse 2026.
- ✅ marketplace.json e plugin.json nella forma V4 (`--strict` riportato verde; non rilanciato, `claude plugin validate` ammesso ma non necessario).
- ✅ Opzioni e uscite citate nelle skill esistono: `start N [--level L1|L2] [--confirm]` (cli.py:62-68), codici 0/1/3/4 (start.py:3), righe `rifiuto:`/`avviso:`/`conferma:`/`prossimo passo: EnterWorktree` (start.py:59,144-146,210,409), `task start k [--fix]`, `review-prepare`, `done` (cli.py:69-77), `status --checkpoint --note` (cli.py:51-53), `stats --work N`, `act apply`, `block open test_spec_conflict --reason` (phases.py:19). Formato del riepilogo `task k: <tipo> name=<n> [model: inherit] launch|resume` (taskcmd.py:162-163). Giri 1-3 `resume`, 4-5 `launch` con `-r<giro>` e `model: inherit` (taskcmd.py:131-139, naming.py:8). `SendMessage` di ripresa e risposta a NEEDS_CONTEXT ammessi (send_message.py:36-42). `stop_pct` nega nuovi subagenti (agents.py:42).
- ❌ Vedi i rilievi sotto: revisore per area, ripresa dopo /clear, esito effettivo del verdetto, L1 non rientrante.
- ⚠️ `statusline/ctx` non esiste ancora (solo `statusline.sh`): è del Task 11, la skill `setup` lo anticipa. Da verificare al Task 11.

### Punti di forza
- Programma sempre tra virgolette con ripiego sulla riga `tollgate: programma` (V1), test dedicato.
- Divieto esplicito di subagenti nell'implementatore e nel revisore; gestione chiara di test/specifica in conflitto (R1), report e verdetto con il numero dei veti spiegato al modello.
- `start`: gestione corretta di 3 (conferme, mai `--confirm` di iniziativa) e 4, issue.md trattato come dato.
- Pre-condizione del worktree pulito per `review-prepare`/`task done` (carry) coperta al passo 0.

### Rilievi

**Important**

1. skills/execute/SKILL.md:29 (passo 4): il revisore è sempre `tollgate:task-reviewer`. `task start` salva `routing.reviewer` in `tasks.reviewer_type` (taskcmd.py:160; profiles.py:90) e `_common.awaiting_review` (bin/tollgate_checks/_common.py:98-100) riconosce il revisore solo se `tasks.reviewer_type = subagents.type`. Con un profilo che dichiara `reviewer` (decisione 15, criterio 38, es. `probe:reviewer-frontend`) il revisore lanciato dalla skill ha un tipo diverso: `task_verdict.decide` esce subito (task_verdict.py:26-28), `subagent_stop` lo tratta come sola lettura qualunque e lo chiude `done` senza verdetto (subagent_stop.py:65-69, `_readonly`), `tasks.verdict` resta vuoto e `task done` rifiuta (taskcmd.py:301). Il task si pianta e nessun messaggio dice perché. Il report lo ammette come «sotto-progetto B», ma il difetto è del contratto tra CLI e skill già in P3a (decisione 15 è di P3a). Correzione: far stampare a `task review-prepare` (e al riepilogo di `task start`) il tipo del revisore (`row["reviewer_type"]`, già nel DB) e far usare alla skill quel tipo; test CLI sulla riga stampata. Se si preferisce rinviare, almeno dichiararlo nella skill come limite noto (oggi la frase tra parentesi è l'unica traccia) e aprire un carry per P3b.

2. skills/execute/SKILL.md:30-37 (passo 5): la skill decide su `approved`/`changes` come li dichiara il revisore, ma il valore che conta è quello registrato (`tasks.verdict`): con `reviewer_standard` è ricalcolato da `spec_compliance` e dalle gravità (verdicts.py:75-82; decisione 10). Un `changes` dichiarato con soli rilievi minor/moderate vale `approved`: `task start k --fix` rifiuta («serve un verdetto changes», taskcmd.py:56-58) e la skill non dice cosa fare. Il caso inverso (dichiarato `approved` con `spec_compliance` non vuoto) fa rifiutare `task done` (taskcmd.py:301-303). Correzione: nella skill, «prova `task done k`; se rifiuta per verdetto `changes`, passa a `task start k --fix`; se `--fix` rifiuta per verdetto `approved`, esegui `task done k`», oppure far stampare l'esito effettivo. Aggiungere una riga sul perché.

3. skills/execute/SKILL.md:23-39 e :40-42: il ciclo parte sempre da `task start k` (che accetta solo `pending`, taskcmd.py:49-52) e dice che dopo `/clear` si riprende dal «primo task non chiuso» e che `status` lo mostra. Falso su due punti: `status` stampa solo i conteggi per stato (cli.py:_print_status, nessun numero di task), e un task in `review`, `running` o `blocked` non può ripartire da `task start k`. Dopo un `stop_pct` a metà task (caso previsto da 6.3) il modello si trova bloccato. La CLI conosce già il passo giusto (checkpoint.py:46-56: «task k in review: tollgate task review-prepare k», «approvato: task done», «da correggere: task start --fix», «running: attendi o riprendi»), e lo scrive nel checkpoint iniettato da SessionStart. Correzione: nella skill, tabella stato → passo di ingresso (pending → 1; running → ripresa/attesa; review senza verdetto → 4; review con verdetto → 5; blocked → `/tollgate:resolve`) e dire di leggere la riga «prossimo passo» del checkpoint (o rigenerarlo con `status --checkpoint`) invece di `status`.

4. skills/start/SKILL.md:35 (L1): non rientrante. Il modello scrive il checkpoint e chiede `/clear`; dopo il `/clear` il testo della skill non c'è più. Se l'utente rilancia `/tollgate:start #N`, `start` riprende il lavoro in fase `plan` e la skill, seguita alla lettera, chiede di nuovo checkpoint e `/clear`: ciclo. Se non lo rilancia, SessionStart inietta solo stato e checkpoint (session.py:38, nessun «invoca writing-plans»). Correzione: dire all'utente esplicitamente «dopo il /clear scrivi: invoca superpowers:writing-plans per #N» oppure «rilancia /tollgate:start #N» e, nel ramo L1, «se in questa sessione hai già fatto il checkpoint o il contesto è pulito (lavoro ripreso, nessuna fase persa), vai direttamente a writing-plans». Meglio se la CLI scrive nel checkpoint la riga «prossimo passo: superpowers:writing-plans».

**Minor**

5. skills/execute/SKILL.md:36: «Al quinto giro senza `approved` si apre `needs_you`» è impreciso. Il blocco si apre al primo `--fix` con `fix_rounds >= 5` (taskcmd.py:102-105), cioè dopo il quinto giro non approvato, al tentativo di un sesto. Scrivere «dopo il quinto giro non approvato, `task start --fix` apre il blocco e rifiuta».

6. skills/setup/SKILL.md:15-16: `<radice>/statusline/ctx` non è tra virgolette: con una radice con spazi (il repo di sviluppo ne ha) il comando si spezza. Citare la radice. Inoltre la cache del plugin contiene la versione nel percorso: avvertire che va riaggiornato a ogni aggiornamento del plugin.

7. agents/task-reviewer.md:58-60: l'esempio JSON usa `"approved" | "changes"` e `["missing" | "extra"]`, che non è JSON valido; se il modello lo copia il parser lo scarta (`json_candidates`, report.py:30-41) e prende il veto. Accompagnare l'esempio con un secondo esempio valido (`"outcome": "approved", "spec_compliance": []`). Lo stesso per `"task": 0`.

8. tests/test_manifest.py `test_brief_fields_match_agent_text`: cerca `"campo"` con virgolette in tutto il file e passa anche se il campo compare in prosa; è un controllo debole ma accettabile. Nessun test copre il punto 1 (tipo del revisore) né i punti 2-3.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** manifest, agenti, licenze e comandi citati sono corretti rispetto alla CLI, ma la skill `execute` (il programma del modello) ha tre punti che la portano in vicolo cieco: revisore per area non riconosciuto, esito effettivo del verdetto ignorato, ripresa dopo `/clear` non possibile da `review`/`running`; più il ciclo di `/clear` in `start` L1.
