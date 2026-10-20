---
name: approve
description: Approvazioni dell'utente (livello, rilievo, giri e cicli, revisione non verificata, rebase, deroga, effetto esterno). Solo l'utente.
disable-model-invocation: true
argument-hint: "level <L> <motivo> | finding <id> <gravità|dismiss> <motivo> | rounds <n> | unverified-review | rebase | waiver <id> | effect <id>"
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

L'atto è già registrato dal hook quando l'utente ha digitato il comando. Guarda il primo argomento:

- **`level <L> <motivo>`**, **`finding <id> <gravità|dismiss> <motivo>`**, **`rounds <n>`**, **`unverified-review`**, **`rebase`**: lancia dal worktree `<programma> act apply` e riferisci l'esito riga per riga. Se rifiuta, riporta il motivo così com'è. Cosa fa ciascuno:
  - `level`: fissa il tetto e dice il livello risultante (rifiuta, per esempio, se la fase corrente non esiste nella sequenza del livello di arrivo).
  - `finding`: declassa il rilievo a una gravità (`blocker|major|moderate|minor`) o lo scarta (`dismiss`); il motivo è obbligatorio. Dopo, `/tollgate:finish` rilancia la revisione se serve.
  - `rounds <n>`: concede `n` giri di correzione al task fermo (poi `task start k --fix`) oppure `n` cicli di revisione finale oltre i quattro (tetto assoluto 8), chiudendo il blocco del tetto; con più tetti insieme rifiuta e indica `/tollgate:resolve <id>`.
  - `unverified-review`: vale solo dopo il tetto dei cicli; il lavoro prosegue con la revisione dichiarata non verificata, e la PR lo riporta.
  - `rebase`: dopo un conflitto di `/tollgate:sync` risolto a mano nel worktree; riallinea la base, chiude il blocco e autorizza il push forzato del prossimo `finish open-pr`.
- **`waiver`**, **`effect`** e **`unverified-tests`**: l'approvazione vale già, perché dal DB. Dillo all'utente e **non lanciare nulla**.
- **`pr`**: non serve lanciare nulla; lo usa `finish open-pr` quando l'utente digita `/tollgate:finish`.
- **`spec`** e **`plan`**: arrivano con il percorso L2 (P3c): dillo e non lanciare nulla.
- **Ogni altro oggetto**: rispondi che non è un oggetto di `approve` e non lanciare nulla.

Non applicare nient'altro e non approvare nulla al posto dell'utente.
