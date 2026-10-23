# Esecuzione del piano P5: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-23-tollgate-p5-eval-ci.md` con la skill `superpowers:subagent-driven-development`.

- **Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 25. La revisione 26 la scrive il Task 15.
- **Piano principale:** `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.
- **Registro di P4**, modello del metodo: `docs/sdd/2026-10-21-tollgate-p4-gate/`. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md`, dei `task-N-carry-extract.md` e di `preflight-scan.md`.
- **Documentazione di `claude plugin eval`:** `https://code.claude.com/docs/en/plugin-evals` e `claude plugin eval --help`. Il piano ne riporta i fatti che usa (decisioni 1-3); il Task 1 prova quelli non documentati.

## Dove lavorare

- Ramo `p5-eval-ci`, in un worktree isolato in `.claude/worktrees/p5`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`. Il worktree `.claude/worktrees/p4` e il ramo `p4-gate` esistono ancora: non toccarli.
- Il workspace SDD (ledger, brief, report) sta **nel worktree**: `.claude/worktrees/p5/.superpowers/sdd/<cartella stampata da sdd-workspace>`. Se esiste già, riprendi da dove si è fermato.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (2465 su `main` a P4).
- **Tempi della suite.** Con circa 2500 test una corsa di `tests/run` dura da 19 a 31 minuti quando la macchina è carica (due interpreti). Lanciala in background e aspetta l'esito con un ciclo `until` limitato sul file di uscita o con la notifica: non restare fermo ad aspettare. Lo stesso vale per i subagenti: il brief di ogni implementatore glielo dice, insieme al divieto di lanciare la suite completa più di una volta per giro quando basta il file di test del task (la suite completa va prima del commit).

## Scan pre-flight

Dopo il Task 1 e prima del Task 2, un analista sonnet in sola lettura scrive `preflight-scan.md`:
- una tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere);
- una tabella per task (test previsti contro codice previsto, file toccati da più task);
- i conflitti con la spec rev 25, con il codice reale di `main` e con gli esiti del Task 1.

Lo giudichi tu: per ogni conflitto una riga `Ruling:` nel ledger e una voce in `carry.md` (o nel `task-N-carry-extract.md`) per i task che ne dipendono, **prima** di lanciarli. Punti da far guardare apposta:
- gli esiti VE1-VE11 contro le decisioni 2, 3 e 9: (a) e (c) si applicano con una `Ruling:`; se scatta (b), fermati e chiedi all'utente prima di scrivere `local.py` e prima di ogni `claude -p`, e la `Ruling:` registra la sua risposta;
- `scaffold.build` (Task 7) contro `tests/flowkit.py` e `tests/hookkit.py`: segnale della sessione, forma degli eventi, cartella di stato; nessun accesso diretto al DB;
- le chiavi nuove di `attention.GROUPS` (Task 4) contro `CoverageTest` e contro il commento del gate;
- `guard` con `pending` (Task 5) contro la regola «nessuno stato sulle PR verso altri rami» (decisione 5 di P4) e contro `verdict._statuses`;
- `sentinel.last_checked` (Task 5) contro `_first_install` e contro i test di `test_gate_sentinel.py`;
- i test che cercano `@v4` o `actions/<x>@` (Task 3) contro il fissaggio: devono restare verdi;
- `VERSION` a `0.2.0` (Task 3) contro `prereq.GATE_FILES`, `.github/tollgate/VERSION` nei banchi (`tests/flowkit.py`, `tests/gatekit.py`) e l'avviso di `start` su una versione installata diversa.

## Ordine e modelli

1. **Task 1** per primo. Script, plugin sonda e test scritti da un implementatore sonnet **senza rete e senza `claude`**; esecuzione (GitHub, `claude plugin eval`) **del controller in prima persona**. Step 0: se `socat` manca, fermati e chiedi all'utente di installarlo.
2. **Task 2-12:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku. Il Task 12 usa la skill `humanizer` sui testi.
3. **Task 13:** script scritto da un implementatore sonnet senza rete; esecuzione su detect del controller, dopo il 12.
4. **Task 14:** del controller (eval e CI), dopo il 13. I giri di correzione che toccano il prodotto li scrive un implementatore sonnet, con un test.
5. **Task 15:** implementatore sonnet, dopo il 14.
6. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
7. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger e `carry.md`

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice la spec, vince la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. Una correzione che cambia la spec va nella revisione 26, scritta dal Task 15. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage.

**Le decisioni per un task possono stare in più posti**: `carry.md` (sezione del task, sezioni dello scan pre-flight, sezioni nate da un altro task) e i `task-N-carry-extract.md`. Prima di lanciare un task leggili **tutti** e copia nel brief ogni voce che lo nomina, non solo la sua sezione.

## Lezioni di P4 da applicare

- **GitHub vero non è deterministico.** Arrivano 500 a corpo vuoto anche sui POST (memoria `github-500-transitorio`), `gh pr edit` è rotto con gh 2.46 (si usa la PATCH REST), e con un controllo non obbligatorio rosso `mergeStateStatus` vale `UNSTABLE`. Ogni caso reale si scrive per essere ripetuto, con l'esito di ogni tentativo registrato; un esito ottenuto in più tentativi è «composito».
- **Il controller in prima persona** per GitHub vero, `claude plugin eval` e ogni `claude`: ogni `gh` passa dal wrapper con la guardia (`spikes/gh-p4/ghguard.py`, profilo `p5`), le evidenze si committano e il controllo dei comandi si fa alla fine. Un falso positivo del controllo fa fallire la suite: il controllo ha i suoi test.
- **Breaker.** Il Task 16 di P4 è arrivato al giro 5. Qui ogni prova reale è divisa: preparazione con test (Task 1 Step 1, Task 7-11, Task 13 Step 1) ed esecuzione del controller (Task 1 Step 2, Task 13 Step 2, Task 14). Le correzioni del prodotto scoperte in una prova sono giri del task della prova, ognuna con un test, e si ripete **solo** il caso interessato.
- **Aggiornare il codice installato su detect** si fa con la procedura di 9.4 (PR da `tollgate-config/*`, decisione 13 e Task 13): detect non ha protezione, quindi la procedura «togliere la protezione, push, attesa di `tollgate-base`, `protect.sh`» di P4 non serve.
- **Gli implementatori non eseguono mai** gli script contro GitHub, `claude plugin eval` né `claude -p`: il brief di ogni lancio e di ogni giro di correzione elenca i modi vietati (tutti tranne `bash -n` e `controlla`) e dice che l'esecuzione è del controller.
- **Workspace e registro.** Il workspace SDD sta nel worktree e si copia in `docs/sdd/` alla chiusura. La riga «Stato» del piano principale non cita `.superpowers/` (è ignorato da git).

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante). Sono quelle di `docs/sdd/2026-10-21-tollgate-p4-gate/cautele.md`, con i percorsi di P5 e con le **sole** eccezioni qui sotto, che valgono **solo per il controller** e non vanno mai a un subagente.

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`) e, per gli eval, una `HOME` temporanea (`evals/_kit/scaffold.py`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test: si usa una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`, `evals/_kit/`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` è ammesso.

**Esperimenti e rete (subagenti)**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete, nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py` (o lo shim `tests/evalbin/gh`). Mai `gh auth`, `gh api` o `gh pr create` col `gh` vero.
- Negli script dei Task 1 e 13 e in `evals/run.sh` i subagenti usano solo `bash -n` e il modo `controlla` con `gh` e `claude` finti.

**Eccezioni per il controller (decisioni 8, 20, 21 e 22 del piano)**
- Ogni `gh` del controller passa da `spikes/gh-p4/ghguard.py` con il profilo `p5`, scritto e testato nel Task 1 (Step 1) prima del primo uso.
- `ginz0ls/tollgate` (privato): `gh repo create ginz0ls/tollgate --private`, una volta, nel Task 1, **dopo** la ricerca di token in tutta la storia (`ghp_`, `gho_`, `ghs_`, `github_pat_`, `sk-ant-`, `AKIA`): se ne trovi, fermati e chiedi. Poi, nei Task 1, 13 e 14, nei giri di correzione della revisione finale e nella chiusura: `git push` di `main` (solo il `main` locale com'è, mai forzato; dopo il merge con l'OK dell'utente, il `main` nuovo), del ramo `p5-eval-ci` e dei rami `p5-probe-*`; `git push --delete` dei soli `p5-probe-*`; `gh run list|view|watch|download|rerun`; `gh api` in lettura.
- `ginz0ls/tollgate-p4-detect` (privato), solo nei Task 1 e 13: `git push` di rami e di `main` (mai forzato; il push diretto su `main` solo nel caso `skip-ci`); `gh pr create|close|merge|view|list|comment` e la PATCH REST del corpo; `gh issue close|comment|view|list`; `gh run list|view|watch|download|rerun`; `gh api` in lettura; `PUT repos/ginz0ls/tollgate-p4-detect/actions/permissions` per `sha_pinning_required`, rimesso al valore iniziale alla fine del Task 13.
- `git ls-remote` sui repo `actions/*` (Task 1, VC2). `gh auth status` (sola lettura).
- **Vietati**: ogni comando su `ginz0ls/tollgate-p4-protected` (lo cancella l'utente) e su altri repo; segreti; cambi di visibilità; cancellare repo; ogni `gh auth` diverso da `status`; `gh api user`.
- `claude plugin eval` solo dal controller, solo da `evals/run.sh` (Task 14) o dallo script della sonda (Task 1), sempre con `--no-publish`, `--trust-plugin`, `--model claude-sonnet-5-5` e `--max-cost-usd` uguale al residuo del tetto. **Tetto complessivo 80 USD** (`docs/verifiche/evidenze/eval-p5/budget.tsv`): al tetto ti fermi e chiedi all'utente. `claude -p` solo se scatta la decisione 9 (b) **e l'utente ha dato l'OK**, solo da `evals/_kit/local.py` (o dalla verifica VE11), con la `HOME` vera, `TOLLGATE_STATE` con la sentinella sotto `/tmp/tollgate-p5-eval/`, `--plugin-dir`, le esclusioni della configurazione dell'utente e i `--disallowedTools` della decisione 9 (b), e conta nello stesso tetto.
- `claude plugin validate --strict` è ammesso anche agli implementatori (non lancia il modello).
- I repo restano alla fine: `ginz0ls/tollgate` è il repo del plugin; detect lo cancella l'utente quando vuole.

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push verso remoti veri, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p5` (ramo `p5-eval-ci`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

## Quando fermarsi e chiedere

Solo in questi casi:
- `socat` assente (Task 1, Step 0), o una ricerca di token che trova qualcosa;
- il tetto di 80 USD raggiunto, o un costo ignoto dopo una corsa (`evals/run.sh` si ferma);
- la decisione 9 (b) che scatta: serve l'OK dell'utente per l'esecutore locale con `claude -p`;
- un'operazione distruttiva o irreversibile, o un'operazione su GitHub fuori dall'elenco qui sopra;
- un'azione fuori da questo worktree, come un merge su `main`;
- un piano rotto al punto che ogni strada è un'ipotesi (per esempio un esito del Task 1 che smentisce insieme le decisioni 3 e 9).

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: «Decisioni di questo piano», «Review Focus», la tabella «Copertura», le righe `minor (deferred)` del ledger da sottoporre a triage, i rapporti dei Task 1, 13 e 14, e le regole di cautela. Chiedigli in particolare di cercare i guasti che nascono dall'incontro di due comandi sugli stessi stati (`pending` di `guard` e verdetto, sentinella e stati, calcolo del gate in locale e su GitHub, scaffold e corsa vera) e di controllare che nessun testo non fidato entri in un argomento di `gh` o in una riga `run:`, e che gli eval non escano dal recinto (shim, `--no-publish`, tetto).
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano. Se una correzione tocca i workflow o il gate, ripeti nel Task 13 **solo** i casi interessati; se tocca un caso di eval o ciò che prova, ripeti **solo** quel caso, nel tetto.
3. **Suite tre volte**: `tests/run` (python3.11 e python3) e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`, tre corse verdi, nessun «unclosed database» a fine suite. E l'ultimo run della CI sul ramo verde.
4. **Niente merge su `main` senza l'OK dell'utente.** Riporta all'utente, in italiano e in breve: commit e numero di test, `Ruling:` prese, minori rinviati con il triage, esiti dei Task 1, 13 e 14 (casi di eval sopra e sotto soglia, Δ, costo totale e residuo; casi di detect riusciti, non riusciti, compositi; minuti di Actions; CI). Poi chiedi l'OK per il merge.
5. Dopo il merge (con l'OK):
   - push di `main` su `ginz0ls/tollgate` (non forzato) e attesa della CI verde su `main`;
   - copia il registro dal worktree (`.claude/worktrees/p5/.superpowers/sdd/…`) in `docs/sdd/2026-10-23-tollgate-p5-eval-ci/` con un `README.md`, come per P4, e committalo su `main` (e push);
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`): esito di P5, nucleo chiuso, repo `ginz0ls/tollgate`, detect lasciato all'utente da cancellare, prossimo passo (sotto-progetto B, C o D: lo sceglie l'utente);
   - **trascrizioni**: solo se questa sessione (o una delle sessioni del lavoro) è partita dalla cartella del worktree, le sue trascrizioni stanno in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow--claude-worktrees-p5/` e non compaiono in `/resume` dalla radice. Spostale con `mv -n` (i `.jsonl` e le eventuali cartelle `<id>/`) in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/`, mai il file della sessione attiva mentre è in uso. Se tutte le sessioni sono partite dalla radice, non c'è nulla da spostare: dillo. Non dire mai che le trascrizioni stanno dentro `.claude/worktrees/`;
   - chiedi all'utente se rimuovere i worktree e i rami `p4-gate` e `p5-eval-ci` ormai uniti.
