# Ri-revisione giro 1 del Task 9 (`6beebe8..80e9f47`)

### Verdetti sui rilievi
1. **I-1, manca il rinvio «R-INFRA-06 ambigua» nella sezione 9**: INDIRIZZATO. Nuova voce nel blocco «A B6-B8, da B5» del piano principale, subito dopo la decisione 7: fatto (seconda frase ambigua su «codice che li usa», con rimando a `final-review.md:38`), motivo (skill e pagina approvate, non si toccano senza l'utente), destinatario (la prossima revisione di `rules-infra` la porta all'utente).
2. **M-1, riga B4 della sezione 2 falsa su `workers/**`**: INDIRIZZATO. Ora dice che non è un pattern né di `infra` né di `backend` e che il codice dei Worker è `backend` per contenuto (B5), coerente con la riga B5 e il catalogo.
3. **M-2, `script_name` e `nx`/`lerna`**: INDIRIZZATO, frase nuova verificata su `bin/tollgate_analysis/bash.py`. `script_name` è chiamato solo per `npm|pnpm|yarn|bun` (`bash.py:1209-1210`); `yarn workspaces foreach` dà `workspaces` (`:1228-1230`), `pnpm turbo run` dà `turbo`; `turbo run`, `nx run`, `lerna run` hanno come base un programma fuori dall'elenco e non passano da `script_name`. Corretti i due punti della sezione 9 e il punto di 8.5 della spec.

### Danni nuovi nel diff della correzione
Nessuno. Solo documentazione (2 file, +5 -4). Nota stilistica minore, non bloccante: in 8.5 della spec la frase finale ha due parentesi consecutive ("(…) (`yarn workspaces foreach` …)"). «Non vengono guardati affatto» riguarda solo `script_name`; i comandi possono comunque incontrare altre regole di effetto. Suite del report: exit 0, 3755 OK su 3.11 e 3.13, nessun «unclosed».

### Osservazioni fuori ambito
M-3 e M-4 della revisione (minori) non erano nei rilievi da giudicare e restano come stavano.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
