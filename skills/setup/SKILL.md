---
name: setup
description: Propone la modifica di statusLine.command per avvolgere la statusline con statusline/ctx, che alimenta la guardia del contesto di tollgate, e le regole permissions.allow per WebFetch (per dominio) e WebSearch. Solo l'utente.
disable-model-invocation: true
---

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Per `<radice>` ricava la radice del plugin da quel percorso (la cartella che contiene `bin/`).

`statusline/ctx` è un involucro: legge l'input JSON della statusline, scrive la percentuale di contesto usata per sessione e poi esegue il comando di statusline che gli passi, con lo stesso input. La guardia del contesto di tollgate (avviso e stop) ne dipende.

1. Leggi `~/.claude/settings.json` e non modificare il file: è protetto e la modifica la fa l'utente.
2. Guarda `statusLine.command`:
   - se esiste già un comando, proponi `"statusLine": {"type": "command", "command": "\"<radice>/statusline/ctx\" '<comando attuale>'"}`, con il comando attuale come **una stringa tra apici singoli**;
   - se non esiste una statusline, proponi `"command": "\"<radice>/statusline/ctx\" \"<radice>/statusline/statusline.sh\""`.
   La radice va **sempre tra virgolette**: il percorso può contenere spazi. Se il comando attuale contiene apici singoli, avvisa l'utente di doverli proteggere.
   La radice nella cache del plugin contiene la versione: la riga va riaggiornata a ogni aggiornamento del plugin.
3. Mostra la riga da incollare, indica dove va (`~/.claude/settings.json`, chiave `statusLine`) e di' che la modifica è sua. Se `statusLine.command` ha già `statusline/ctx`, di' che non serve fare nulla.

4. **Permessi per leggere la documentazione.** Gli implementatori aprono pagine pubbliche con `WebFetch` e cercano con `WebSearch`. Senza una regola Claude Code chiede un permesso la prima volta che si apre un dominio nuovo, e il lavoro si ferma su quella domanda. Proponi per prime le regole per dominio, una per ogni sito di documentazione che il progetto usa davvero, da mettere in `permissions.allow` del `.claude/settings.json` del progetto (per esempio `"WebFetch(domain:docs.python.org)"`): valgono solo per quel progetto, non costano niente e il lavoro non si ferma per quei siti. Poi di' in una frase il rischio di un `WebFetch` libero: un `WebFetch` libero può portare dati fuori nell'URL, una pagina scaricata può contenere istruzioni ostili, e tollgate non controlla `WebFetch`. Le voci senza dominio, `"WebFetch"` e `"WebSearch"`, in `~/.claude/settings.json` valgono per ogni progetto e ogni sessione: sono una scelta dell'utente, a suo rischio, e vanno proposte solo se le chiede. Non modificare nessun file: le regole le aggiunge l'utente da sé, e se non le aggiunge risponde a una domanda per ogni dominio nuovo.

Non eseguire altri comandi e non scrivere in `~/.claude/`.
