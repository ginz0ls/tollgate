# Esecuzione del piano B1: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-27-tollgate-b1-informati-prima.md` con la skill `superpowers:subagent-driven-development`.

- **Progetto di B** (l'autorità): `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`. Le scelte marcate «utente» non si discutono; quelle marcate «mia scelta» si correggono solo con una `Ruling:` che dice il motivo.
- **Spec del nucleo:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 26. La revisione 27 la scrive il Task 10.
- **Piano principale di B:** `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`.
- **Registro di P5**, modello del metodo: `docs/sdd/2026-10-23-tollgate-p5-eval-ci/`. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md`, dei `task-N-carry-extract.md` e di `preflight-scan.md`.

## Dove lavorare

- Ramo `b1-informati-prima`, in un worktree isolato in `.claude/worktrees/b1`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`.
- Avvia la sessione dalla **radice del repo**, non dal worktree: così la trascrizione resta visibile in `/resume` dalla radice (memoria `sessioni-nei-worktree`).
- Il workspace SDD (ledger, brief, report) sta **nel worktree**: `.claude/worktrees/b1/.superpowers/sdd/<cartella stampata da sdd-workspace>`. Se esiste già, riprendi da dove si è fermato.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (2897 su `main` a P5).
- **Tempi della suite.** Con circa 2900 test una corsa di `tests/run` dura da 20 a 35 minuti quando la macchina è carica (due interpreti). Lanciala in background e aspetta l'esito sul file d'uscita, senza restare fermo. Il brief di ogni implementatore lo dice, insieme al divieto di lanciare la suite completa più di una volta per giro quando basta il file di test del task.

## Scan pre-flight

Dopo il Task 1 e prima del Task 2, un analista sonnet in sola lettura scrive `preflight-scan.md`:
- una tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere);
- una tabella per task (test previsti contro codice previsto, file toccati da più task);
- i conflitti con il progetto di B, con la spec rev 26, con il codice reale di `main` e con gli esiti del Task 1.

Lo giudichi tu: per ogni conflitto una riga `Ruling:` nel ledger e una voce in `carry.md` (o nel `task-N-carry-extract.md`) per i task che ne dipendono, **prima** di lanciarli. Punti da far guardare apposta:
- gli esiti B1-V1..V7 contro le decisioni 4, 5, 6, 7, 8 e 15 e contro i ripieghi dello Step 4 del Task 1: ognuno si applica con una `Ruling:`;
- `ATTRIBUTE_UNNAMED` (Task 3) contro `lookup_owner` (Task 4) e contro la regola dello scrittore unico (`bin/tollgate_checks/agents.py`);
- l'ordine dei moduli in `pre_edit` (`writes` 20, `research_gate` 25) e in `post_bash` (`post_bash` 20, `lookup_rec` 40): il primo `deny` vince, i `record` si applicano tutti (spec 3.2);
- `research` contro `cli_calls._COORDINATOR_ONLY` e `_SIGNALLED` (nessuno dei due: è un sottocomando dell'implementatore, decisione 12);
- la migrazione 6 contro `tests/test_db.py` (copie `migrazione-*`, `BackupRaceTest`) e contro `evals/_kit/scaffold.py` (lo scaffold costruisce lavori col programma vero: avranno `research = 1`, e i casi di eval di P5 non devono cambiare esito; la prova a secco `tests/test_eval_cases.py` lo controlla);
- i test esistenti che contano `apply.OPS` (28, in `tests/test_check_audit_round.py`), `latest_version()` (5, in `tests/test_db.py`), gli eventi d'ingresso (`INPUT_EVENTS`), il matcher di `hooks.json` e l'elenco esatto degli strumenti di `implementer.md` (`tests/test_manifest.py`);
- `Lab(plugin_root=…)` di `tests/hookkit.py` (Task 7) contro i test che oggi contano su `plugin_root=ROOT`.

## Ordine e modelli

1. **Task 1** per primo. Script, plugin sonda e test scritti da un implementatore sonnet **senza rete e senza `claude`**; esecuzione (`claude -p`) **del controller in prima persona**.
2. **Task 2-8:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku.
3. **Task 9:** script scritto da un implementatore sonnet senza rete e senza `claude`; esecuzione del controller, dopo il Task 8.
4. **Task 10:** implementatore sonnet, dopo il Task 9.
5. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
6. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger e `carry.md`

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice il progetto o la spec, vince il progetto, poi la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. Una correzione che cambia la spec va nella revisione 27, scritta dal Task 10. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage, e quelli che riguardano B2 e oltre finiscono nel piano principale di B.

**Le decisioni per un task possono stare in più posti**: `carry.md` (sezione del task, sezioni dello scan pre-flight, sezioni nate da un altro task) e i `task-N-carry-extract.md`. Prima di lanciare un task leggili **tutti** e copia nel brief ogni voce che lo nomina.

## Lezioni dei piani precedenti

- **Le prove reali si dividono** (P4, P5): preparazione con test (Task 1 Step 1, Task 9 Step 1) ed esecuzione del controller (Task 1 Step 2, Task 9 Step 2). Le correzioni del prodotto scoperte in una prova sono giri del task della prova, ognuna con un test, e si ripete **solo** il passo interessato.
- **Gli implementatori non eseguono mai** gli script delle prove fuori dai modi `controlla` e `bash -n`, né `claude -p`: il brief di ogni lancio e di ogni giro di correzione elenca i modi vietati e dice che l'esecuzione è del controller (incidente del Task 14 di P3c).
- **Un esito ottenuto in più tentativi è «composito»**, e il rapporto lo dice.
- **Workspace e registro.** Il workspace SDD sta nel worktree e si copia in `docs/sdd/` alla chiusura. La riga «Stato» del piano principale non cita `.superpowers/` (è ignorato da git).

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante). Sono quelle di `docs/sdd/2026-10-23-tollgate-p5-eval-ci/cautele.md`, con i percorsi di B1, e con le **sole** eccezioni elencate dopo, che valgono **solo per il controller** e non vanno mai a un subagente.

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`) e una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`, `evals/_kit/`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test.
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Esperimenti e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete, nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py`. Mai `gh auth`, `gh api`, `gh pr create` né alcun altro comando col `gh` vero.
- Negli script dei Task 1 e 9 (`spikes/b1/run-b1-checks.sh`, `spikes/run-b1-flow.sh`) usi solo `bash -n` e il modo `controlla` (o una corsa con un `claude` finto nel `PATH`). Non li esegui mai in nessun altro modo, nemmeno per prova, nemmeno durante un giro di correzione: l'esecuzione è del controller.
- `evals/run.sh` di P5: solo `bash -n` e il modo `controlla`, mai un'altra forma (gli eval sono di B8).

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push verso remoti veri, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b1` (ramo `b1-informati-prima`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Tempi della suite**
- Con circa 2900 test una corsa di `tests/run` dura da 20 a 35 minuti quando la macchina è carica. Lanciala in background e aspetta l'esito sul file d'uscita, senza restare fermo. Mentre lavori lancia solo i file di test del task; la suite completa al più una volta per giro, prima del commit.

**Eccezioni per il controller, una per una**
1. **`claude -p` nel Task 1** (verifiche B1-V1..V5): solo da `spikes/b1/run-b1-checks.sh sonda`, solo con la cartella di lavoro sotto `/tmp/tollgate-b1/probe/`, sempre con `--plugin-dir spikes/b1/probe-plugin`, `--model sonnet`, `--permission-mode acceptEdits` e l'`--allowedTools` dello Step 1 (senza, `WebFetch` e gli altri strumenti verrebbero negati e la sonda misurerebbe i flag). `claude plugin validate --strict` (B1-V7) non lancia il modello e non conta. Al più **3 esecuzioni** della sonda: oltre ti fermi e chiedi all'utente. Motivo: il progetto 3.5 vuole i fatti provati prima del codice, e solo una sessione vera li dà.
2. **`claude -p` nel Task 9** (prova reale): solo da `spikes/run-b1-flow.sh`, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir /tmp/tollgate-b1/plugin` (la copia con la `rules-base` di prova), `--model sonnet`, `--permission-mode acceptEdits` e l'`--allowedTools` del Task 9, con il `gh` finto nel `PATH` e lo stato con la sentinella. Al più **3 tentativi per passo**: oltre ti fermi e chiedi. Motivo: progetto 7, prova reale di un lavoro L1.
3. **Rete del modello in quelle esecuzioni:** `WebFetch` e `WebSearch` verso la documentazione pubblica sono lo scopo della prova e sono ammessi; `curl`, `wget`, `gh` vero e `git push` verso remoti non locali restano vietati al modello con `--disallowedTools`.
4. **Push di `main` su `https://github.com/ginz0ls/tollgate.git`**, solo dopo il merge con l'OK dell'utente e solo dopo `spikes/gh-p4/ghguard.py gitcheck -- push https://github.com/ginz0ls/tollgate.git main` con `P4_PROFILE=p5` uscito con 0; mai forzato. Poi `gh run list|view|watch` della CI di `main`, dalla guardia con lo stesso profilo. Nessun altro comando verso GitHub.
5. Le esecuzioni con `claude -p` consumano l'abbonamento dell'utente: nessun denaro in più, ma il consumo va riportato (token da `tollgate stats` e dalle trascrizioni) nel rapporto e all'utente.

Vietati anche al controller: ogni operazione sui repo di prova di P4 (`ginz0ls/tollgate-p4-protected`, `ginz0ls/tollgate-p4-detect`) e su altri repo; segreti; cambi di visibilità; cancellare repo o rami remoti; `claude plugin eval` (gli eval sono di B8).

## Quando fermarsi e chiedere

Solo in questi casi:
- un esito del Task 1 che non rientra in nessuno dei ripieghi dello Step 4 (per esempio le letture non si registrano e nemmeno la sola forma della nota ha senso);
- più di 3 esecuzioni della sonda, o più di 3 tentativi di un passo della prova reale;
- un'operazione distruttiva o irreversibile, o un'operazione su GitHub fuori dall'eccezione 4;
- un'azione fuori da questo worktree, come un merge su `main`;
- un piano rotto al punto che ogni strada è un'ipotesi.

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: «Decisioni di questo piano», «Review Focus», la tabella «Copertura», le righe `minor (deferred)` del ledger da sottoporre a triage, i rapporti dei Task 1 e 9, le regole di cautela. Chiedigli in particolare di cercare i guasti che nascono dall'incontro di due eventi sugli stessi stati (una lettura registrata e la nota consegnata nello stesso task; un giro di correzione con un implementatore nuovo; L0 che cresce; un lavoro nato prima della migrazione), di controllare che nessuna lettura di un altro task o della sessione principale renda valida una nota, e che il testo della nota e delle pagine scaricate non entri mai come istruzione in un brief.
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano. Se una correzione tocca ciò che la prova reale ha provato, ripeti **solo** il passo interessato, nelle eccezioni 2 e 3.
3. **Suite tre volte**: `tests/run` (python3.11 e python3) e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`, tre corse verdi, nessun «unclosed database» a fine suite.
4. **Niente merge su `main` senza l'OK dell'utente.** Riporta all'utente, in italiano, in breve e in parole semplici: commit e numero di test, `Ruling:` prese, minori rinviati con il triage, esiti del Task 1 (quali ripieghi sono scattati) e della prova reale (letture registrate, nota, avvisi e rifiuti, consumo). Poi chiedi l'OK per il merge.
5. Dopo il merge (con l'OK):
   - push di `main` (eccezione 4) e attesa della CI verde su `main`;
   - copia il registro dal worktree in `docs/sdd/2026-10-27-tollgate-b1-informati-prima/` con un `README.md`, come per P5, e committalo su `main` (e push);
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`): esito di B1, ripieghi scattati, prossimo passo (scrivere il piano di B2);
   - **trascrizioni**: se una sessione del lavoro è partita dalla cartella del worktree, spostane i `.jsonl` (e le cartelle `<id>/`) con `mv -n` da `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow--claude-worktrees-b1/` a `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/`, mai il file della sessione attiva mentre è in uso. Se tutte le sessioni sono partite dalla radice, non c'è nulla da spostare: dillo. Non dire mai che le trascrizioni stanno dentro `.claude/worktrees/`;
   - chiedi all'utente se rimuovere il worktree e il ramo `b1-informati-prima` ormai uniti.
