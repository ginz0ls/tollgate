---
name: approve
description: Approvazioni dell'utente (livello, deroga, effetto esterno). Solo l'utente.
disable-model-invocation: true
argument-hint: "level <L> <motivo> | waiver <id> | effect <id>"
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

L'atto è già registrato dal hook quando l'utente ha digitato il comando. Guarda il primo argomento:

- **`level <L> <motivo>`**: lancia dal worktree `<programma> act apply` e riferisci l'esito (tetto fissato, livello risultante). Se rifiuta (per esempio la fase corrente non esiste nella sequenza del livello di arrivo), riporta il motivo così com'è.
- **`waiver`** e **`effect`**: l'approvazione vale già, perché dal DB. Dillo all'utente e **non lanciare nulla**.
- **Ogni altro oggetto** (`spec`, `plan`, `finding`, `rebase`…): rispondi «arriva con /tollgate:finish (P3b) o con il percorso L2 (P3c)» e non lanciare nulla.

Non applicare nient'altro e non approvare nulla al posto dell'utente.
