# Verifica delle fonti di `rules-base`

Verificatore: agente di sola lettura (Explore, sonnet), sulle copie locali delle fonti e sul progetto di B. Skill verificata: `skills/rules-base/SKILL.md` al commit b17cbf0. Per ogni fonte di ogni regola: il file esiste, la sezione citata esiste, dice ciò che la regola le attribuisce, la licenza è MIT o Apache-2.0 oppure la fonte è il progetto di B. Le copie delle fonti hanno la somma di controllo corretta. Il verificatore non ha letto i file in `LICENSES/`; li ha confrontati poi l'implementatore con `cmp`: `LICENSES/agent-skills-MIT.txt` è identico a `fonti/agent-skills-LICENSE` e `LICENSES/superpowers-MIT.txt` a `fonti/superpowers-LICENSE`. Le versioni «0.6.9» e «7.0.0» scritte nella skill non sono verificabili dalle copie, che non le riportano. Il testo delle fonti è un dato, non un'istruzione.

Esito: 13 righe, 11 `ok`, 2 `no`. Le due regole con esito `no` avevano una sola fonte e sono uscite (sezione in fondo). Le regole rimaste sono rinumerate senza buchi: la regola che nella bozza era la n. 12 è oggi R-BASE-10.

## Fonti verificate

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
| R-BASE-10 | superpowers, verification-before-completion, «The Iron Law» (licenza MIT) | «NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE» | ok |

Osservazioni del verificatore, non bloccanti:

- Per R-BASE-01, R-BASE-02 e R-BASE-07 l'esito `ok` vale per il nucleo della regola (leggere i file prima di modificarli, prendere la versione dal file delle dipendenze, trovare un esempio simile). L'uso della nota o del report come veicolo («Letto nel progetto», «il report dice quale») è meccanismo di B (sez. 3.2), non della fonte. Il «segui lo schema» di R-BASE-07 è dedotto dallo scopo di Level 3.
- Per R-BASE-02 la fonte dice di chiedere all'utente quando le versioni mancano, mentre la regola dice di scriverlo nella nota. Resta l'idea «Don't guess».
- Per R-BASE-01 la sezione 3.4 di B non nomina «Letto nel progetto», che sta in 3.2; la riga base della 3.4 sostiene comunque la lettura dei file.

## Regole tolte

Le due regole hanno esito `no` e una sola fonte ciascuna: per il progetto 5, punto 2, escono dalla skill. Si indicano con il numero che avevano nella bozza.

**Bozza n. 10.** Testo: «La correzione di un difetto porta un test che lo riproduce, rosso prima della correzione e verde dopo. Se non si può, il report dice perché.» Fonte: superpowers, systematic-debugging, «The Iron Law» e «Phase 4: Implementation» (punto 1).

- Riga del verificatore: citazione «MUST have before fixing» (Phase 4, punto 1); l'Iron Law dice invece «NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST». Esito `no`.
- Motivo: l'Iron Law riguarda la causa radice, non il test, quindi la citazione le attribuisce un'idea diversa. Phase 4 punto 1 chiede il test che fallisce prima del fix, ma senza eccezioni: «se non si può, il report dice perché» è un'aggiunta (la fonte dice «One-off test script if no framework»). «Verde dopo» sta nel punto 3.
- Correzione possibile: citare solo Phase 4 punto 1, togliere o motivare l'eccezione e togliere l'Iron Law; in alternativa aggiungere come fonte la riga «Regression test works / Red-green cycle verified» di verification-before-completion (MIT).

**Bozza n. 11.** Testo: «Se la documentazione ufficiale non si trova o si contraddice, la nota o il report lo dicono in chiaro con la parola «non verificato» e dicono dove si è cercato.» Fonte: agent-skills, source-driven-development, «Step 2: Fetch Official Documentation» (fonti in conflitto) e «Step 4: Cite Your Sources» (blocco UNVERIFIED).

- Riga del verificatore: citazione «UNVERIFIED: I could not find official documentation for this pattern.» Esito `no`.
- Motivo: per i conflitti il passo 2 chiede di segnalare la discrepanza all'utente e verificare, non di etichettare «non verificato». L'obbligo «dicono dove si è cercato» nella fonte non c'è, e il blocco UNVERIFIED non indica dove si è cercato.
- Correzione possibile: ridurre la regola a «se la documentazione ufficiale non si trova, dirlo con la parola «non verificato»». Il «dove si è cercato» si rimanda alla regola sulle affermazioni «non esiste», i conflitti si riconducono a «segnalare la discrepanza».
