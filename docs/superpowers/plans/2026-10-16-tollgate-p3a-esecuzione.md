# Esecuzione del piano P3a: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-16-tollgate-p3a-avvio-e-task.md` con la skill `superpowers:subagent-driven-development`.

- **Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 21. La revisione 22 la scrive il Task 14.
- **Piano principale:** `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.
- **Registro di P2**, da consultare per i precedenti: `docs/sdd/2026-10-09-tollgate-p2-guardrail/`. Le regole per implementatori e revisori lì sono il modello da riusare.

## Dove lavorare

- Lavora sul ramo `p3a-avvio-e-task`, in un worktree isolato in `.claude/worktrees/p3a`, creato con `superpowers:using-git-worktrees`. Mai su `main`.
- Il ledger sta nella cartella che stampa lo script `sdd-workspace` per questo piano. Se esiste già, riprendi da dove si è fermato.
- Prima del Task 2 fai lo scan pre-flight, come in P2: tabella per coppie di task e per task, `Ruling:` nel ledger, decisioni per task in `carry.md`.

## Ordine e modelli

1. **Il Task 1 va per primo, prima di qualunque codice.** Implementatore: sonnet. Gli esiti decidono:
   - il testo delle skill (V1, Task 10);
   - il segnale della CLI (V3, Task 2: con V3 «no» il Task 2 si ferma con BLOCKED e decidi tu la strada, con una `Ruling:`);
   - i campi di `marketplace.json` (V4, Task 10).

   Registra le conseguenze nel ledger come righe `Ruling:` **e** nel `carry.md` dei task che ne dipendono, prima di lanciarli.
2. **Task 2-12 e 14:** implementatore sonnet. Il piano dà firme e test, non il codice, quindi niente haiku.
3. **Task 13** (prova reale con `claude -p`): implementatore sonnet. Va dopo il 12 e prima del 14.
4. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; revisione finale dell'intero ramo opus.
5. Indica sempre il modello a ogni lancio di un subagente.

## Regole di cautela

Copiale nel brief di **ogni** subagente, al lancio.

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState`, cioè `TOLLGATE_STATE` con la sentinella `.tollgate-test`.
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/` nei test: si usa una `HOME` temporanea (`tests/flowkit.py`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` e niente `claude plugin marketplace add`. `claude plugin validate` è ammesso.

**Esperimenti e rete**
- `claude -p` si usa solo nei Task 1 e 13: solo da `/tmp/tollgate-p3a` e solo con `--plugin-dir`.
- Nessun repo su GitHub, nessun push, nessuna rete nei test. `gh` nei test è `tests/fakegh.py`.

**Git e segreti**
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati.
- Mai `npm run dev`.
- Non leggere né riportare `.env`, `auth.json` o segreti. V2 del Task 1 riporta solo i **nomi** delle variabili, mai i valori.

**Commit e lingua**
- Un commit dopo ogni task. Prima di ogni commit `tests/run` deve passare, con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`.
- Risposte e messaggi in italiano; identificatori in inglese.

## Decisioni durante l'esecuzione

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice la spec, vince la spec: decidi tu, scrivi la `Ruling:` nel ledger con il costo se sbagliata, e vai avanti.

Fermati e chiedi all'utente solo in tre casi:
- un'operazione distruttiva o irreversibile;
- un'azione fuori da questo worktree, come un merge su `main` o un push;
- un piano rotto al punto che ogni strada è un'ipotesi.

## Chiusura

1. Fai la revisione finale del ramo con opus. Passagli:
   - la sezione «Review Focus» del piano;
   - le righe `minor (deferred)` del ledger, da sottoporre a triage;
   - il rapporto del Task 13.
2. Correggi i rilievi `critical` e `important`. Per ognuno scrivi prima un test che fallisce, poi la correzione. Dopo ogni giro fai una ri-revisione mirata.
3. Lancia la suite completa tre volte, anche con `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`.
4. **Non fare il merge su `main`.** Riporta all'utente, in italiano:
   - i commit e il numero di test;
   - le `Ruling:` prese;
   - i minori rinviati, con il triage;
   - gli esiti dei Task 1 e 13.

   Poi chiedi l'OK per il merge.
5. Dopo il merge: copia il registro in `docs/sdd/2026-10-16-tollgate-p3a-avvio-e-task/`, come per P2, e aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`).
