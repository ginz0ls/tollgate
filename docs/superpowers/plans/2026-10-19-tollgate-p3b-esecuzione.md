# Esecuzione del piano P3b: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-19-tollgate-p3b-chiusura.md` con la skill `superpowers:subagent-driven-development`.

- **Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 22. La revisione 23 la scrive il Task 18.
- **Piano principale:** `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.
- **Registro di P3a**, modello del metodo: `docs/sdd/2026-10-16-tollgate-p3a-avvio-e-task/`. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md` e `preflight-scan.md`.

## Dove lavorare

- Ramo `p3b-chiusura`, in un worktree isolato in `.claude/worktrees/p3b`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`.
- Il ledger sta nella cartella che stampa lo script `sdd-workspace` per questo piano. Se esiste già, riprendi da dove si è fermato.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (997 su `main` a P3a).

## Scan pre-flight

Prima del Task 2, come in P2 e P3a, un analista sonnet in sola lettura scrive `preflight-scan.md`:
- una tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere);
- una tabella per task (test previsti contro codice previsto, file toccati da più task);
- i conflitti con la spec rev 22 e con il codice reale di `main`.

Lo giudichi tu: per ogni conflitto una riga `Ruling:` nel ledger e una voce in `carry.md` per i task che ne dipendono, **prima** di lanciarli. In P3a lo scan trovò 21 conflitti, due bloccanti. Punti da far guardare apposta: l'ordine tra Task 6 e 9 (`prstate` agganciato a `finish check` nel Task 9), la firma di `cli_session` con `argv` (Task 2) usata dai Task 9, 11, 12, 13, e lo spostamento di `_common` in `violations` (Task 4) rispetto ai test degli hook.

## Ordine e modelli

1. **Il Task 1 va per primo**, prima di qualunque codice. Implementatore sonnet. Gli esiti G1-G5 vanno subito nel ledger come `Ruling:` e nel `carry.md` del Task 9 (forme di `gh` e di `fakegh`).
2. **Task 2-16 e 18:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku.
3. **Task 17** (prova reale con `claude -p`): implementatore sonnet, dopo il 16 e prima del 18.
4. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
5. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice la spec, vince la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. Una correzione che cambia la spec va nella revisione 23, scritta dal Task 18. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage.

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante), insieme a quelle di `cautele.md` di P3a:

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test: si usa una `HOME` temporanea (`tests/flowkit.py`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` è ammesso.

**Esperimenti e rete**
- `claude -p` solo nel Task 17: solo da `/tmp/tollgate-p3b` e solo con `--plugin-dir`.
- Nel Task 1 solo `gh --version` e `gh … --help`: nessuna chiamata di rete.
- Nessun repo su GitHub, nessun push verso la rete, nessuna rete nei test. Il solo push ammesso è verso il repo nudo locale del banco o di `/tmp/tollgate-p3b/flow/origin.git`. `gh` nei test è `tests/fakegh.py`.

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione (incidente del Task 8 di P3a).
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Risposte e messaggi in italiano; identificatori in inglese.

## Quando fermarsi e chiedere

Solo in tre casi:
- un'operazione distruttiva o irreversibile;
- un'azione fuori da questo worktree, come un merge su `main` o un push in rete;
- un piano rotto al punto che ogni strada è un'ipotesi.

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: la sezione «Review Focus» del piano, la tabella «Copertura» del piano, le righe `minor (deferred)` del ledger da sottoporre a triage, i rapporti dei Task 1 e 17, e le regole di cautela.
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano.
3. **Suite tre volte**: `tests/run` (python3.11 e python3) e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`, tre corse verdi, nessun «unclosed database» a fine suite.
4. **Niente merge su `main` senza l'OK dell'utente.** Riporta all'utente, in italiano e in breve: commit e numero di test, `Ruling:` prese, minori rinviati con il triage, esiti dei Task 1 e 17. Poi chiedi l'OK per il merge.
5. Dopo il merge (con l'OK):
   - copia il registro in `docs/sdd/2026-10-19-tollgate-p3b-chiusura/` con un `README.md`, come per P3a, e committalo su `main`;
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`);
   - **sposta le trascrizioni**: le sessioni avviate nel worktree stanno in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow--claude-worktrees-p3b/` e non compaiono in `/resume` dalla radice. Spostale con `mv -n` (i `.jsonl` e le eventuali cartelle `<id>/`) in `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/`, mai il file della sessione attiva mentre è in uso. Non dire mai che le trascrizioni stanno dentro `.claude/worktrees/`.
