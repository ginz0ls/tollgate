---
name: status
description: Mostra lo stato dei lavori tollgate attivi (fase, livello, task, blocchi) in sola lettura, e le statistiche di un lavoro su richiesta.
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

Lancia `<programma> status` e riferisci l'output all'utente: per ogni lavoro attivo la fase, il livello, i task per stato, i blocchi aperti e l'eventuale tetto che ha fermato il lavoro, compresi i tetti dell'audit di L2 (`tetto: giri avversariali della spec`, `giri avversariali del piano`, `audit a lenti`): per questi il passo è `/tollgate:resolve <id> <nota>` (sospende l'audit) oppure correggere e rilanciare `/tollgate:spec-audit`. È di sola lettura: non crea nulla e non cambia fase. Con `--json` l'uscita è strutturata.

Se l'utente chiede le statistiche di un lavoro, lancia `<programma> stats --work N` dal repo (N è il numero dell'issue) e riassumi il JSON.

`status` non legge GitHub: le issue di `sentinel` («tollgate: merge non verificato», aperte quando un commit entra sul ramo predefinito senza i controlli verdi) le mostra `/tollgate:start` tra gli avvisi, in modalità `detect`. Se l'utente chiede dei merge non verificati, rimandalo a quelle issue su GitHub: le chiude lui dopo averle lette, mai tu. Un'installazione assente o incompleta del gate si propone con `/tollgate:init`.

Dopo lo stato, indica il passo successivo in base alla fase: task `pending` o in corso, `/tollgate:execute`; blocco aperto, `/tollgate:resolve`; in `spec_audit` e `plan` di L2, `/tollgate:spec-audit`; tutti i task `done`, `/tollgate:finish`.
