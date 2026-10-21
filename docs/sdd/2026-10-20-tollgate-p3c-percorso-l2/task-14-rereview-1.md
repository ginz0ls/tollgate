# Ri-revisione Task 14, giro di correzione 1 (4142e88..214913e)

Letti: regole, brief, revisione, report, diff. In sola lettura ho controllato `bash -n` (ok), l'awk di `worktree_lavoro` su un percorso con spazio (ok) e le evidenze sotto `/tmp/tollgate-p3c/prova-1/flow` e `/tmp/tollgate-p3c/prova-accidentale`. Nessuno script e nessun `claude -p` lanciati.

### Verdetti sui rilievi

**I-1 (il rapporto negava l'uso del piano di prova): INDIRIZZATO.** Riga della tabella del passo 4 e frase sotto la tabella: il modello ha letto `piano-L2.md` e lo ha copiato con Write senza modifiche (`486c3ab`, blob `6ad777ba`), il giro 1 ha trovato un minor, il modello ha corretto (`4aca8f5`, blob `f7340037`, approvato). `piano-L2.md` e' tolto dal non esercitato (resta solo `spec-L2.md`). Coerente con la revisione.

**I-2 (versione dello script del passo 1 non dichiarata): INDIRIZZATO.** Nuova voce D5, richiamo nell'«Esito» e nella riga del passo 1: passo 1 con la forma precedente, accettato per giudizio, ramo committato di `passo1` e `tutto` end to end non eseguiti, solo `spec_nel_ramo` di `passo2` girato. Riscontro: `prova-1/flow/logs/exit-codes.txt` chiude il passo 1 con «rifare il passo 1».

**I-3 (gh vero raggiungibile): INDIRIZZATO nel codice, non esercitato, dichiarato tale.** `prepara` crea `$SHIM/gh` che esegue `tests/fakegh.py` (`run-p3c-flow.sh`, blocco di `prepara`); `claude_step` mette `PATH="$SHIM:$PATH"` davanti a `timeout ... claude` e chiama `verifica_gh` prima del passo. Le variabili `TOLLGATE_FAKEGH_*` sono esportate, quindi lo shim le eredita. Il rapporto («Correzioni dopo la prova») dice che non e' stato esercitato da una prova pianificata. Limite (vedi Osservazioni): `verifica_gh` controlla il PATH dello script, non quello della shell del tool Bash di claude.

**I-4 (esito non propagato): INDIRIZZATO.** `claude_step` termina con `return "$rc"` (e `return 1` se `verifica_push` post-passo fallisce); `passo` registra e ritorna l'esito; `passo2..6` e `libero` usano `passo`; `passo1` fa `passo ... || return 1`; `tutto` e' una catena `&&`. Si ferma al primo fallimento, con i log registrati. Non esercitato, dichiarato.

**Minori: INDIRIZZATI.** `--add-dir "$INPUT"` con `spec-L2.md` e `piano-L2.md` spostati in `$FLOW/input` (variabili `SPEC_SRC`/`PLAN_SRC`, usate coerentemente in `prepara`, nel controllo Python e nei prompt dei passi 2 e 4); `worktree_lavoro` con `substr($0,10)` (provato con spazio); `verifica_push` anche dopo il passo.

**Incidente (esecuzione accidentale): INDIRIZZATO.** Il rapporto lo dichiara in chiaro (ultimo punto di «Correzioni dopo la prova»): cosa e' girato (passi 1-3 e parte del 4), che e' contrario all'indicazione del giro, dove stanno i log e che non e' evidenza. Verifiche: i log citati come evidenza dal rapporto puntano a `/tmp/tollgate-p3c/prova-1/flow/logs` (riga 5; contenuto con mtime fino a 23:22:39, anteriore all'esecuzione accidentale, che ha mtime 23:52-23:54 e vive in `prova-accidentale`); `prova-accidentale/logs/exit-codes.txt` si ferma al passo 3 (passo4 senza esito, fermato), coerente col testo. Nessun numero, sha o esito del rapporto e' preso dai log accidentali.

### Danni nuovi nel diff della correzione
Nessun Critical/Important.
- Minor, rapporto riga 5: backtick rotti. Il percorso e la parentesi esplicativa stanno dentro un unico codice (`/tmp/.../logs (copia conservata; `/tmp/tollgate-p3c/flow` ...)`), il rendering si spezza. Solo di forma.
- Minor, rapporto «Impianto» (righe 11, 14) e tabella sessioni (riga 21): citano ancora `/tmp/tollgate-p3c/flow/...` come luogo del worktree, del repo e dei log nel presente. Il percorso e' quello visto in esecuzione, ma oggi `flow` e' rigenerato; manca una riga unica che dica «leggere `flow` come `prova-1/flow`». Il rimando c'e' solo alla riga 5.
- Minor, rapporto, voce «Ciò che resta non esercitato»: frase con doppia parentesi poco leggibile.

### Osservazioni fuori ambito
- `verifica_gh` non prova che nella shell Bash di `claude -p` il `gh` sia lo shim (un profilo di shell potrebbe riordinare il PATH). Da guardare alla prossima prova reale.
- Tra le voci del rapporto, la frase «Nessun difetto di P3c emerso... nessun passo ripetuto» convive con il passo 1 ripetuto (spiegato in D1/D5); non blocca.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. I minori sopra sono di forma.
