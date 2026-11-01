# Verifica delle fonti di `rules-base` (Task 4, Step 1)

Verificatore: Explore, sonnet, sola lettura (secondo lancio: il primo si è interrotto per un errore di rete dell'API prima di rispondere). Skill verificata: `skills/rules-base/SKILL.md` al commit b17cbf0. Uscita riportata testualmente dal controller.

**Metodo.** Ho letto per intero il brief, `skills/rules-base/SKILL.md`, le quattro copie di SKILL.md in `W/fonti/`, i due file di licenza (intestazione) e la spec di B `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`. `sha256sum -c SHA256SUMS` in `W/fonti/` dà OK per tutti e 6 i file. Le versioni «0.6.9» e «7.0.0» scritte nella skill non sono verificabili dalle copie, che non le riportano. Le licenze `LICENSES/*-MIT.txt` citate nella skill non erano nel mio perimetro e non le ho controllate.

| Regola | Fonte | Citazione | Esito |
|---|---|---|---|
| R-BASE-01 | agent-skills, context-engineering, «Level 3: Relevant Source Files» (licenza MIT) | «Before editing a file, read it.» | ok |
| R-BASE-01 | progetto di B, sez. 3.4 (riga base) | «Leggi i file che modifichi e quelli che li chiamano.» | ok |
| R-BASE-02 | agent-skills, source-driven-development, «Step 1: Detect Stack and Versions» (licenza MIT) | «Read the project's dependency file to identify exact versions:» | ok |
| R-BASE-03 | agent-skills, source-driven-development, «Step 2: Fetch Official Documentation» (licenza MIT) | «Blog posts or tutorials (even popular ones)» (elenco «Not authoritative», contro «Official documentation / Official blog / changelog») | ok |
| R-BASE-04 | progetto di B, sez. 1 e 3.6 | «il nome di un modello si scrive solo dopo averlo letto sulla pagina ufficiale» (3.6) | ok |
| R-BASE-05 | progetto di B, sez. 1 (schema 2) | «dichiara che una cosa «non esiste» senza controllare;» | ok |
| R-BASE-06 | progetto di B, sez. 1 (schema 3) | «cita fonti, link o numeri senza averli aperti;» | ok |
| R-BASE-07 | agent-skills, context-engineering, «Level 3», punto 3 (licenza MIT) | «Find one example of a similar pattern already in the codebase» | ok |
| R-BASE-08 | progetto di B, sez. 1 (esempio del deploy) | «deploy dedotto senza guardare il progetto: «è su Vercel, leggi le cose prima»;» | ok |
| R-BASE-09 | progetto di B, sez. 2 (anti-obiettivo) e 3.2 | «è ammessa solo con un motivo» (3.2); anti-obiettivo: «Un passo così pesante che anche cambiare un colore richiede un giro di ricerca» | ok |
| R-BASE-10 | superpowers, systematic-debugging, «The Iron Law» e «Phase 4: Implementation» punto 1 (licenza MIT) | «MUST have before fixing» (Phase 4, punto 1); l'Iron Law dice invece «NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST» | no: l'Iron Law riguarda la causa radice, non il test, quindi la citazione le attribuisce un'idea diversa. Phase 4 punto 1 chiede il test che fallisce prima del fix, ma senza eccezioni: «se non si può, il report dice perché» è un'aggiunta (la fonte dice «One-off test script if no framework»). «Verde dopo» sta nel punto 3. |
| R-BASE-11 | agent-skills, source-driven-development, «Step 2» (fonti in conflitto) e «Step 4: Cite Your Sources» (licenza MIT) | «UNVERIFIED: I could not find official documentation for this pattern.» | no: per i conflitti il passo 2 chiede di segnalare la discrepanza all'utente e verificare, non di etichettare «non verificato». L'obbligo «dicono dove si è cercato» nella fonte non c'è, e il blocco UNVERIFIED non indica dove si è cercato. |
| R-BASE-12 | superpowers, verification-before-completion, «The Iron Law» (licenza MIT) | «NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE» | ok |

**Riepilogo.** Le righe sono 13: 11 `ok`, 2 `no` (R-BASE-10 e R-BASE-11). Restano senza nessuna fonte `ok` R-BASE-10 e R-BASE-11, perché ognuna ha una sola fonte (un file, citato con due sezioni).

Osservazioni, tutte da leggere come non bloccanti:
- Per R-BASE-01, R-BASE-02 e R-BASE-07 ho dato `ok` al nucleo di ciascuna regola: leggere i file prima di modificarli, prendere la versione dal file delle dipendenze senza indovinarla, trovare un esempio simile. Non ho contato come obbligo estraneo l'uso della nota o del report come veicolo («Letto nel progetto», «il report dice quale»), che è meccanismo di B (sez. 3.2). Il «segui lo schema» di R-BASE-07 è dedotto dallo scopo di Level 3, non scritto lì.
- Per R-BASE-02 la fonte dice «ask the user» quando le versioni mancano, mentre la regola dice di scriverlo nella nota. Resta l'idea «Don't guess».
- Per R-BASE-01 la sezione B 3.4 non nomina «Letto nel progetto», che sta in 3.2. La riga base della 3.4 sostiene però la lettura dei file.
- Per sistemare R-BASE-10, citare solo Phase 4 punto 1, togliere o motivare l'eccezione «se non si può» e togliere l'Iron Law. In alternativa, aggiungere come fonte la riga «Regression test works / Red-green cycle verified» di verification-before-completion (anch'essa MIT), che sostiene il rosso-poi-verde.
- Per R-BASE-11, ridurre la regola a «se non si trova la documentazione ufficiale, dirlo con la parola «non verificato»». Il «dove si è cercato» si può rimandare a B sez. 1 (schema 2), e i conflitti si possono ricondurre a «segnalare la discrepanza».
