# Esecuzione del piano P3c: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-20-tollgate-p3c-percorso-l2.md` con la skill `superpowers:subagent-driven-development`.

- **Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 23. La revisione 24 la scrive il Task 15.
- **Piano principale:** `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.
- **Registro di P3b**, modello del metodo: `docs/sdd/2026-10-19-tollgate-p3b-chiusura/`. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md` e `preflight-scan.md`.

## Dove lavorare

- Ramo `p3c-percorso-l2`, in un worktree isolato in `.claude/worktrees/p3c`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`.
- Il ledger sta nella cartella che stampa lo script `sdd-workspace` per questo piano. Se esiste già, riprendi da dove si è fermato.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (1417 su `main` a P3b).

## Scan pre-flight

Prima del Task 2, come in P2, P3a e P3b, un analista sonnet in sola lettura scrive `preflight-scan.md`:
- una tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere);
- una tabella per task (test previsti contro codice previsto, file toccati da più task);
- i conflitti con la spec rev 23 e con il codice reale di `main`.

Lo giudichi tu: per ogni conflitto una riga `Ruling:` nel ledger e una voce in `carry.md` per i task che ne dipendono, **prima** di lanciarli. In P3b lo scan trovò 25 conflitti. Punti da far guardare apposta:
- le cause nuove di `_FORWARD_CONDITION` (Task 4) contro ogni chiamante che oggi porta avanti una fase L2 con `advance` (test, `hookkit`, `flowkit`, `adopt`, `scope.register_plan`);
- l'uso di `finalreview.Launch` e del formato delle righe `agente:` in `audit prepare` (Task 5) rispetto a `review prepare`;
- `awaiting_audit` e `subagent_stop` (Task 6) contro `awaiting_review` e `awaiting_final`: un agente non deve essere chiuso da due moduli;
- `approvals.locate_spec_approval` usata da sei moduli (Task 2, 7, 9): stessa firma e stesso significato di `files` ovunque;
- l'ordine dei Task 11-12 (rinviati) rispetto ai Task 5-10 che toccano gli stessi file (`finalreview.py`, `actapply.py`, `brief.py`).

## Ordine e modelli

1. **Task 1** per primo. Implementatore sonnet. Non lancia `claude -p` né la rete.
2. **Task 2-13 e 15:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku.
3. **Task 14** (prova reale con `claude -p`): implementatore sonnet, dopo il 13 e prima del 15.
4. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
5. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger e `carry.md`

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice la spec, vince la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. Una correzione che cambia la spec va nella revisione 24, scritta dal Task 15. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage.

**Le decisioni per un task possono stare in più sezioni di `carry.md`** (quella del task, quelle dello scan pre-flight, quelle nate da un altro task). Prima di lanciare un task leggi `carry.md` per intero e copia nel brief **tutte** le voci che lo nominano, non solo la sua sezione. In P3b una decisione rimasta in una sezione diversa da quella del task è stata persa una volta.

## Lezioni di P3b da applicare

- **Interazioni tra comandi.** I quattro Important della revisione finale di P3b nascevano dall'incontro di task diversi. Il piano ha un Review Focus per ogni stato toccato da più comandi, con il suo test: controlla che ogni test del Review Focus esista e attraversi davvero i comandi (non solo la libreria).
- **Skill contro codice.** Il Task 13 scrive le skill dopo i sottocomandi, e `tests/test_skill_contract.py` confronta codici d'uscita, passi e sottocomandi citati con il codice. Un revisore del Task 13 deve leggere ogni skill accanto al sottocomando che cita.
- **Prova reale e sessione legata.** Nel Task 14, dal passo 2 ogni `claude -p` parte dalla cartella del worktree; lo script lo controlla. Un atto digitato in una sessione non legata viene rifiutato: non è un difetto del codice.
- **`gh`.** P3c non usa campi JSON nuovi di `gh`. Se un task ne introduce uno, va segnalato nel ledger come i campi di G4 di P3b (non verificati sull'aiuto di `gh` 2.46).

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante). Sono quelle di `docs/sdd/2026-10-19-tollgate-p3b-chiusura/cautele.md`, con i percorsi di P3c:

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test: si usa una `HOME` temporanea (`tests/flowkit.py`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` è ammesso.

**Esperimenti e rete**
- `claude -p` solo nel Task 14: solo da `/tmp/tollgate-p3c` e solo con `--plugin-dir`.
- Nel Task 1 solo `claude --version` e `gh --version`: nessuna chiamata di rete.
- Nessun repo su GitHub, nessun push verso la rete, nessuna rete nei test. Il solo push ammesso è verso il repo nudo locale del banco (`FlowLab.origin`) o di `/tmp/tollgate-p3c/flow/origin.git`. `gh` nei test è `tests/fakegh.py`. Mai `gh auth`, `gh api` verso GitHub o `gh pr create` col `gh` vero.

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione (incidente del Task 8 di P3a).
- Mai force push (verso remoti veri), `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p3c` (ramo `p3c-percorso-l2`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

## Quando fermarsi e chiedere

Solo in tre casi:
- un'operazione distruttiva o irreversibile;
- un'azione fuori da questo worktree, come un merge su `main` o un push in rete;
- un piano rotto al punto che ogni strada è un'ipotesi.

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: la sezione «Review Focus» del piano, la tabella «Copertura» del piano, le «Decisioni di questo piano», le righe `minor (deferred)` del ledger da sottoporre a triage, i rapporti dei Task 1 e 14, e le regole di cautela. Chiedigli in particolare di cercare i guasti che nascono dall'incontro di due comandi sugli stessi stati (righe dei giri, file di approvazione, registrazione del piano, fasi e blocchi).
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano.
3. **Suite tre volte**: `tests/run` (python3.11 e python3) e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`, tre corse verdi, nessun «unclosed database» a fine suite.
4. **Niente merge su `main` senza l'OK dell'utente.** Riporta all'utente, in italiano e in breve: commit e numero di test, `Ruling:` prese, minori rinviati con il triage, esiti dei Task 1 e 14. Poi chiedi l'OK per il merge.
5. Dopo il merge (con l'OK):
   - copia il registro in `docs/sdd/2026-10-20-tollgate-p3c-percorso-l2/` con un `README.md`, come per P3b, e committalo su `main`;
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`);
   - **trascrizioni**: solo se questa sessione (o una delle sessioni del lavoro) è partita dalla cartella del worktree, le sue trascrizioni stanno in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow--claude-worktrees-p3c/` e non compaiono in `/resume` dalla radice. Spostale con `mv -n` (i `.jsonl` e le eventuali cartelle `<id>/`) in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/`, mai il file della sessione attiva mentre è in uso. Se tutte le sessioni sono partite dalla radice, non c'è nulla da spostare: dillo. Non dire mai che le trascrizioni stanno dentro `.claude/worktrees/`.
