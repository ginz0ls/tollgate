# Esecuzione del piano P4: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-21-tollgate-p4-gate.md` con la skill `superpowers:subagent-driven-development`.

- **Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 24. La revisione 25 la scrive il Task 17.
- **Piano principale:** `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.
- **Registro di P3c**, modello del metodo: `docs/sdd/2026-10-20-tollgate-p3c-percorso-l2/`. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md`, dei `task-N-carry.md` e di `preflight-scan.md`.

## Dove lavorare

- Ramo `p4-gate`, in un worktree isolato in `.claude/worktrees/p4`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`.
- Il workspace SDD (ledger, brief, report) sta **nel worktree**: `.claude/worktrees/p4/.superpowers/sdd/<cartella stampata da sdd-workspace>`, non nella radice. Se esiste già, riprendi da dove si è fermato.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (1753 su `main` a P3c).

## Scan pre-flight

Prima del Task 2, come in P2, P3a, P3b e P3c, un analista sonnet in sola lettura scrive `preflight-scan.md`:
- una tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere);
- una tabella per task (test previsti contro codice previsto, file toccati da più task);
- i conflitti con la spec rev 24, con il codice reale di `main` e con gli esiti del Task 1.

Lo giudichi tu: per ogni conflitto una riga `Ruling:` nel ledger e una voce in `carry.md` (o nel `task-N-carry.md`) per i task che ne dipendono, **prima** di lanciarli. Punti da far guardare apposta:
- l'estrazione del Task 2 (`runner`, `ghcli`, `diffcheck`, `l2tree`) contro ogni chiamante e ogni test che fa `patch` su un nome di `verify`, `violations`, `gh` o `l2tree`: i nomi devono restare importabili dal modulo di origine;
- `GateInputs`, `Item` ed `Evaluation` (Task 4) contro chi li costruisce e li legge (Task 5, 6, 9, 13): stessi campi e stesso significato di `where`;
- l'ordine nuovo di `locate_spec_approval` (Task 3) contro `l2tree.spec_approval`, `violations.locked_docs`, `audit`, `l2acts`, `start --spec`, `adopt`, `openpr.facts` e i loro test;
- `openpr.facts` chiamato da `finish check` (Task 13): import nella funzione, nessun ciclo, comportamento senza cicli di revisione;
- i campi nuovi di `prblock.FIELDS` (Task 13) contro i test che costruiscono blocchi a mano e contro `adopt`;
- le forme reali di V1-V6 (Task 1) contro le decisioni 5, 12, 14, 16 e 18: una forma diversa diventa una `Ruling:` prima dei Task 8-12.

## Ordine e modelli

1. **Task 1** per primo. Script scritti da un implementatore sonnet **senza rete**; esecuzione su GitHub **del controller in prima persona** (decisione 25 del piano).
2. **Task 2-15 e 17:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku.
3. **Task 16:** script scritti da un implementatore sonnet senza rete e senza `claude -p`; esecuzione (GitHub e `claude -p`) del controller, dopo il 15 e prima del 17.
4. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
5. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger e `carry.md`

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice la spec, vince la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. Una correzione che cambia la spec va nella revisione 25, scritta dal Task 17. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage.

**Le decisioni per un task possono stare in più posti**: `carry.md` (sezione del task, sezioni dello scan pre-flight, sezioni nate da un altro task) e i `task-N-carry.md`. Prima di lanciare un task leggili **tutti** e copia nel brief ogni voce che lo nomina, non solo la sua sezione.

## Lezioni di P3b e P3c da applicare

- **Interazioni tra comandi.** Le revisioni finali di P3b (4 Important) e P3c (I-1) hanno trovato difetti nati dall'incontro di task diversi o da due funzioni che ricalcolavano lo stesso fatto in modo diverso. In P4 il fatto condiviso è il calcolo del gate (decisione 3): `finish check` e `gate evaluate` passano dalla stessa `evaluate`. Il piano ha un Review Focus per ogni stato toccato da due comandi, con il suo test: controlla che ogni test del Review Focus esista e attraversi davvero i comandi.
- **Skill contro codice.** Il Task 15 scrive le skill dopo i sottocomandi, e `tests/test_skill_contract.py` confronta codici, passi e sottocomandi citati con il codice. Il revisore del Task 15 legge ogni skill accanto al sottocomando che cita.
- **Prova reale.** In P3c un implementatore, durante un giro di correzione, ha lanciato un `claude -p` contro le istruzioni. Nel Task 16 **gli implementatori non eseguono mai** gli script contro GitHub né `claude -p`: il brief di ogni lancio e di ogni giro di correzione elenca i modi vietati (tutti tranne `bash -n` e `controlla`) e dice che l'esecuzione è del controller.
- **`gh`.** I campi JSON usati sono quelli verificati nel Task 1. Un campo nuovo introdotto da un task si segnala nel ledger e si controlla nel Task 16.

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante). Sono quelle di `docs/sdd/2026-10-20-tollgate-p3c-percorso-l2/cautele.md`, con i percorsi di P4 e con le **sole** eccezioni per GitHub qui sotto, che valgono **solo per il controller**:

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test: si usa una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` è ammesso.

**Esperimenti e rete (subagenti)**
- Nessun `claude -p`, nessuna chiamata di rete, nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py`. Mai `gh auth`, `gh api` o `gh pr create` col `gh` vero.
- Negli script del Task 1 e del Task 16 i subagenti usano solo `bash -n` e il modo `controlla` con un `gh` finto.

**Eccezioni per GitHub (solo il controller, solo nei Task 1 e 16, decisione 25 del piano)**
- Repo ammessi: `ginz0ls/tollgate-p4-protected` (pubblico) e `ginz0ls/tollgate-p4-detect` (privato). Nessun comando su altri repo.
- `gh repo create` dei due nomi, una volta (Task 1).
- `git push` di rami e di `main` verso i due repo; mai push forzato su `main`.
- `gh pr create|edit|close|merge|view|list|comment`, `gh issue create|close|comment|view|list`, `gh run list|view|download|watch` sui due repo.
- `gh api` in lettura sui due repo; `POST repos/<o>/<r>/statuses/<sha>` (prova del token personale); `PUT` e `DELETE` di `branches/main/protection` **solo** su `tollgate-p4-protected`.
- `gh auth status` (sola lettura). Vietati: ogni altro `gh auth`, `gh api user`, cancellare i repo, cambiarne la visibilità, i segreti.
- `claude -p` solo nel Task 16, solo da `/tmp/tollgate-p4/flow`, solo con `--plugin-dir`.
- I repo restano alla fine: **li cancella l'utente**.

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push verso remoti veri, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p4` (ramo `p4-gate`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

## Quando fermarsi e chiedere

Solo in tre casi:
- un'operazione distruttiva o irreversibile, o un'operazione su GitHub fuori dall'elenco qui sopra;
- un'azione fuori da questo worktree, come un merge su `main`;
- un piano rotto al punto che ogni strada è un'ipotesi (per esempio un esito del Task 1 che smentisce più decisioni insieme).

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: la sezione «Review Focus», la tabella «Copertura», le «Decisioni di questo piano», le righe `minor (deferred)` del ledger da sottoporre a triage, i rapporti dei Task 1 e 16, e le regole di cautela. Chiedigli in particolare di cercare i guasti che nascono dall'incontro di due comandi sugli stessi stati (calcolo del gate in locale e su GitHub, blocco 18.1, commento e marcatore, stati e sentinella, cache degli identificativi, approvazioni tra fette) e di controllare che nessun testo non fidato entri in un argomento di `gh` o in una riga `run:`.
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano. Se una correzione tocca i workflow o il calcolo del gate, ripeti nel Task 16 **solo** i casi interessati, dal controller.
3. **Suite tre volte**: `tests/run` (python3.11 e python3) e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`, tre corse verdi, nessun «unclosed database» a fine suite.
4. **Niente merge su `main` senza l'OK dell'utente.** Riporta all'utente, in italiano e in breve: commit e numero di test, `Ruling:` prese, minori rinviati con il triage, esiti dei Task 1 e 16 (casi riusciti, non riusciti, compositi, minuti di Actions). Poi chiedi l'OK per il merge.
5. Dopo il merge (con l'OK):
   - copia il registro dal worktree (`.claude/worktrees/p4/.superpowers/sdd/…`) in `docs/sdd/2026-10-21-tollgate-p4-gate/` con un `README.md`, come per P3c, e committalo su `main`;
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`): esito di P4, repo di prova lasciati all'utente da cancellare (`ginz0ls/tollgate-p4-protected`, `ginz0ls/tollgate-p4-detect`), prossimo passo (P5);
   - **trascrizioni**: solo se questa sessione (o una delle sessioni del lavoro) è partita dalla cartella del worktree, le sue trascrizioni stanno in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow--claude-worktrees-p4/` e non compaiono in `/resume` dalla radice. Spostale con `mv -n` (i `.jsonl` e le eventuali cartelle `<id>/`) in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/`, mai il file della sessione attiva mentre è in uso. Se tutte le sessioni sono partite dalla radice, non c'è nulla da spostare: dillo. Non dire mai che le trascrizioni stanno dentro `.claude/worktrees/`;
   - i repo di prova restano su GitHub: ricorda all'utente che li cancella lui.
