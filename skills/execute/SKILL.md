---
name: execute
description: Esegue il piano del lavoro task per task con gli agenti tollgate:implementer e tollgate:task-reviewer, fino a quando tutti i task sono chiusi.
---

Derivato da superpowers/skills/subagent-driven-development (MIT, © 2025 Jesse Vincent); vedi LICENSES/superpowers-MIT.txt

Sei il coordinatore: scegli, lanci, leggi i verdetti. Non scrivi codice dei task tu.

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa la forma `python3 "<percorso>"` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica questo percorso. Lancia i comandi dal worktree del lavoro.

**Regole ferme:** mai subagent-driven-development, mai implementatori `general-purpose`: l'unico che scrive in `execution` è l'agente scelto da `task start`, e i hook negano il resto. I subagenti non lanciano né comandi `task` né `status --checkpoint`: li lanci tu.

## Passo 0: ingresso e ripresa

Vale all'inizio e dopo ogni `/clear`. Lancia `<programma> status --checkpoint` (non `status` da solo: stampa solo i conteggi) e segui la riga **«prossimo passo»**, l'ultima del checkpoint, che SessionStart inietta anche a sessione pulita. Il passo di ingresso dipende dallo stato del primo task non `done`:

| Stato del task k | Dove entri |
|---|---|
| `pending` | ciclo, punto 1 (`task start k`) |
| `running` | attendi, oppure riprendi l'implementatore con `SendMessage` al suo `name` (punto 3) |
| `review`, revisione non preparata | punto 4 (`task review-prepare k`) |
| `review`, revisione preparata, senza verdetto | lancia il revisore (punto 4, secondo capoverso) |
| `review` con verdetto `changes` | punto 5, `task start k --fix` |
| `review` con verdetto `approved` | punto 5, `task done k` |
| `blocked` | fermati: `/tollgate:resolve` |

Prima del **primo** task (nessun task ancora avviato):
1. Controlla il piano (il file indicato dal lavoro): task che si contraddicono, file condivisi tra task, dipendenze nascoste. Annota le decisioni con `<programma> status --checkpoint --note "<testo>"`.
2. Il worktree deve essere **pulito**: `task review-prepare` e `task done` rifiutano un albero con modifiche non committate. Se il piano o altri file del coordinatore non sono committati, committali ora, prima del primo `task start`. Tra un task e l'altro non lasciare modifiche non committate, e non modificare codice tra `review-prepare` e `task done`.

## Per ogni task non `done`, in ordine

1. **Avvio.** `<programma> task start k` (solo da `pending`). Stampa il percorso del brief e un riepilogo del tipo `task k: <tipo agente> name=<nome> [model: inherit] launch|resume revisore: <tipo revisore>`.
2. **Implementatore.** Con lo strumento `Agent`, **in primo piano** (mai `run_in_background`): `subagent_type` = il tipo del riepilogo, `name` = il `name` del riepilogo, `prompt` = il percorso del brief. Passa `model` solo se il riepilogo lo indica. Un solo `Agent` per volta.
3. **Risposta dell'implementatore.**
   - DONE o DONE_WITH_CONCERNS: vai alla revisione.
   - NEEDS_CONTEXT: rispondi riprendendo **lo stesso** implementatore (`SendMessage` al suo `name`) con le informazioni richieste; non consuma un giro.
   - BLOCKED, oppure un veto di budget (taglio di `maxTurns` o token oltre il tetto): fermati, riferisci all'utente il motivo e indica `/tollgate:resolve`. Non rilanciare da solo.
4. **Revisione.** `<programma> task review-prepare k` stampa due righe: il percorso del brief del revisore e `revisore: <tipo>`. Lancia `Agent` con `subagent_type` = **quel tipo** (mai un tipo fisso: un revisore di tipo diverso da quello assegnato non viene riconosciuto e il task si pianta), in primo piano, con `prompt` = il percorso del brief.
5. **Verdetto: conta quello registrato, non quello dichiarato.** Con lo standard del revisore (8.6) l'esito effettivo è ricalcolato da `spec_compliance` e dalle gravità: un `changes` con soli rilievi `moderate`/`minor` vale `approved`, e viceversa. Quindi, finito il revisore, lancia sempre `<programma> task done k`:
   - se chiude il task, passa al successivo;
   - se rifiuta perché il verdetto è `changes`, lancia `<programma> task start k --fix`, che scrive il file dei rilievi e un riepilogo:
     - giri 1-3 (riepilogo con `resume`): `SendMessage` al `name` dell'implementatore con il percorso del file dei rilievi;
     - giri 4-5 (riepilogo con `launch` e nome `-r<giro>`): un nuovo `Agent` con quel `name`, `model: inherit` e il percorso del brief;
     - dopo il quinto giro non approvato, il `task start k --fix` successivo apre un blocco `needs_you` e rifiuta: fermati, riferisci e indica `/tollgate:resolve`;
   - se `--fix` rifiuta perché il verdetto è `approved`, lancia `task done k`;
   - se `task done` rifiuta per altro (verdetto assente, worktree sporco, SHA non coperto), leggi il messaggio: serve una nuova `review-prepare` o un commit dei file del coordinatore.
   - Verdetto rifiutato dal hook (veto): il revisore riscrive; dopo due veti si apre `needs_you`.
6. Torna al punto 1 per il task successivo.

## Guardia del contesto

All'avviso del hook (`warn_pct`) scrivi il checkpoint con `<programma> status --checkpoint`. A `stop_pct` il hook nega nuovi subagenti: scrivi il checkpoint, chiedi all'utente `/clear`, e dopo il `/clear` riprendi da questa skill, dal passo 0 (ingresso dalla riga «prossimo passo»).

## Fine

Quando ogni task è `done`, di' all'utente di lanciare `/tollgate:finish` (arriva con P3b).
