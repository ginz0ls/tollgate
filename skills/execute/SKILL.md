---
name: execute
description: Esegue il piano del lavoro task per task con gli agenti tollgate:implementer e tollgate:task-reviewer, fino a quando tutti i task sono chiusi.
---

Derivato da superpowers/skills/subagent-driven-development (MIT, © 2025 Jesse Vincent); vedi LICENSES/superpowers-MIT.txt

Sei il coordinatore: scegli, lanci, leggi i verdetti. Non scrivi codice dei task tu.

**Programma:** `"${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`, sempre tra virgolette (il percorso può contenere spazi). Se la variabile non risulta espansa nel testo, usa il percorso della riga `tollgate: programma` del contesto. Nel seguito `<programma>` indica questo percorso. Lancia i comandi dal worktree del lavoro.

**Regole ferme:** mai subagent-driven-development, mai implementatori `general-purpose`: l'unico che scrive in `execution` è l'agente scelto da `task start`, e i hook negano il resto. I subagenti non lanciano né comandi `task` né `status --checkpoint`: li lanci tu.

## Passo 0: prima del task 1

1. Controlla il piano (il file indicato dal lavoro): task che si contraddicono, file condivisi tra task, dipendenze nascoste. Annota le decisioni con `"<programma>" status --checkpoint --note "<testo>"`.
2. Il worktree deve essere **pulito**: `task review-prepare` e `task done` rifiutano un albero con modifiche non committate. Se il piano o altri file del coordinatore non sono committati, committali ora, prima del primo `task start`. Tra un task e l'altro non lasciare modifiche non committate, e non modificare codice tra `review-prepare` e `task done`.

## Per ogni task non `done`, in ordine

1. **Avvio.** `"<programma>" task start k`. Stampa il percorso del brief e un riepilogo del tipo `task k: <tipo agente> name=<nome> [model: inherit] launch|resume`.
2. **Implementatore.** Con lo strumento `Agent`, **in primo piano** (mai `run_in_background`): `subagent_type` = il tipo del riepilogo, `name` = il `name` del riepilogo, `prompt` = il percorso del brief. Passa `model` solo se il riepilogo lo indica. Un solo `Agent` per volta.
3. **Risposta dell'implementatore.**
   - DONE o DONE_WITH_CONCERNS: vai alla revisione.
   - NEEDS_CONTEXT: rispondi riprendendo **lo stesso** implementatore (`SendMessage` al suo `name`) con le informazioni richieste; non consuma un giro.
   - BLOCKED, oppure un veto di budget (taglio di `maxTurns` o token oltre il tetto): fermati, riferisci all'utente il motivo e indica `/tollgate:resolve`. Non rilanciare da solo.
4. **Revisione.** `"<programma>" task review-prepare k` stampa il percorso del brief del revisore. Lancia `Agent` con `subagent_type` = `tollgate:task-reviewer`, in primo piano, con `prompt` = quel percorso (il revisore per area dei profili verticali arriva con il sotto-progetto B).
5. **Verdetto.**
   - `approved`: `"<programma>" task done k`.
   - `changes`: `"<programma>" task start k --fix` scrive il file dei rilievi e un riepilogo.
     - Giri 1-3 (riepilogo con `resume`): `SendMessage` al `name` dell'implementatore con il percorso del file dei rilievi.
     - Giri 4-5 (riepilogo con `launch` e nome `-r<giro>`): un nuovo `Agent` con quel `name`, `model: inherit` e il percorso del brief.
     - Al quinto giro senza `approved` si apre un blocco `needs_you`: fermati, riferisci e indica `/tollgate:resolve`.
   - Verdetto rifiutato dal hook (veto): il revisore riscrive; dopo due veti si apre `needs_you`.
6. Torna al passo 1 per il task successivo.

## Guardia del contesto

All'avviso del hook (`warn_pct`) scrivi il checkpoint con `"<programma>" status --checkpoint`. A `stop_pct` il hook nega nuovi subagenti: scrivi il checkpoint, chiedi all'utente `/clear`, e dopo il `/clear` riprendi da questa skill, dal primo task non chiuso (`"<programma>" status` lo mostra).

## Fine

Quando ogni task è `done`, di' all'utente di lanciare `/tollgate:finish` (arriva con P3b).
