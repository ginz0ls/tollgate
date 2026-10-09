# Esecuzione del piano P2: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-09-tollgate-p2-guardrail.md` con la skill `superpowers:subagent-driven-development`.

- **Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`. Oggi è alla revisione 20; la revisione 21 la scrivono i Task 1 e 20.
- **Piano principale:** `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`.

## Dove lavorare

- Lavora sul ramo `p2-guardrail`, in un worktree isolato creato con `superpowers:using-git-worktrees`. Mai su `main`.
- Il ledger è `.superpowers/sdd/2026-10-09-tollgate-p2-guardrail/progress.md`. Se esiste già, riprendi dal punto in cui si è fermato.

## Ordine e modelli

1. **Il Task 1 va per primo, prima di qualunque codice.** Implementatore: sonnet.
   - I suoi esiti decidono `INJECT_MODE` (Task 12) e il campo `version` di `dependencies` (Task 13).
   - Registra le conseguenze nel ledger come righe `Ruling:`.
2. **Task 12, 15, 16, 17, 18, 19** (integrazione tra moduli): implementatore sonnet.
3. **Tutti gli altri task**, che hanno il codice completo nel piano: implementatore haiku.
4. **Revisioni:** revisore di ogni task sonnet; revisione finale dell'intero ramo opus.
5. Indica sempre il modello a ogni lancio di un subagente.

## Regole di cautela

Copiale nel brief di **ogni** subagente.

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState`, cioè `TOLLGATE_STATE` con la sentinella `.tollgate-test`.
- Mai installare, abilitare o disinstallare plugin nella configurazione dell'utente: niente `claude plugin install`, niente `claude plugin marketplace add`.
- Mai modificare `~/.claude/settings.json`.

**Esperimenti e rete**
- `claude -p` si usa solo nel Task 1: solo con `--plugin-dir spikes/hookprobe` e solo da `/tmp/tollgate-p2`.
- Nessun repo su GitHub, nessun push, nessuna rete nei test.

**Git e segreti**
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati.
- Mai `npm run dev`.
- Non leggere né riportare `.env`, `auth.json` o segreti.

**Commit e lingua**
- Un commit dopo ogni task. Prima di ogni commit `tests/run` deve passare, con `python3.11` e con `python3`.
- Risposte e messaggi in italiano; identificatori in inglese.

## Decisioni durante l'esecuzione

Se il codice del piano contraddice la spec, vince la spec: decidi tu, scrivi la `Ruling:` nel ledger e vai avanti.

Fermati e chiedi all'utente solo in tre casi:
- un'operazione distruttiva o irreversibile;
- un'azione fuori da questo worktree, come un merge su `main` o un push;
- un piano rotto al punto che ogni strada è un'ipotesi.

## Chiusura

1. Fai la revisione finale del ramo con opus, passandogli la sezione «Review Focus» del piano.
2. Correggi i rilievi `critical` e `important`. Per ognuno scrivi prima un test che fallisce, poi la correzione.
3. Lancia la suite completa, anche con `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`.
4. **Non fare il merge su `main`.** Riporta all'utente, in italiano:
   - i commit e il numero di test;
   - le `Ruling:` prese;
   - i rilievi minori rinviati;
   - gli esiti del Task 1.

   Poi chiedi l'OK per il merge.
5. Aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`) con lo stato di P2.
