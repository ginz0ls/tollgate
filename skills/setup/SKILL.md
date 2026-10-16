---
name: setup
description: Propone la modifica di statusLine.command per avvolgere la statusline con statusline/ctx, che alimenta la guardia del contesto di tollgate. Solo l'utente.
disable-model-invocation: true
---

**Programma:** `"${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`, sempre tra virgolette (il percorso può contenere spazi). Se la variabile non risulta espansa nel testo, usa il percorso della riga `tollgate: programma` del contesto. Per `<radice>` ricava la radice del plugin da quel percorso (la cartella che contiene `bin/`).

`statusline/ctx` è un involucro: legge l'input JSON della statusline, scrive la percentuale di contesto usata per sessione e poi esegue il comando di statusline che gli passi, con lo stesso input. La guardia del contesto di tollgate (avviso e stop) ne dipende.

1. Leggi `~/.claude/settings.json` e non modificare il file: è protetto e la modifica la fa l'utente.
2. Guarda `statusLine.command`:
   - se esiste già un comando, proponi `"statusLine": {"type": "command", "command": "\"<radice>/statusline/ctx\" '<comando attuale>'"}`, con il comando attuale come **una stringa tra apici singoli**;
   - se non esiste una statusline, proponi `"command": "\"<radice>/statusline/ctx\" \"<radice>/statusline/statusline.sh\""`.
   La radice va **sempre tra virgolette**: il percorso può contenere spazi. Se il comando attuale contiene apici singoli, avvisa l'utente di doverli proteggere.
   La radice nella cache del plugin contiene la versione: la riga va riaggiornata a ogni aggiornamento del plugin.
3. Mostra la riga da incollare, indica dove va (`~/.claude/settings.json`, chiave `statusLine`) e di' che la modifica è sua. Se `statusLine.command` ha già `statusline/ctx`, di' che non serve fare nulla.

Non eseguire altri comandi e non scrivere in `~/.claude/`.
