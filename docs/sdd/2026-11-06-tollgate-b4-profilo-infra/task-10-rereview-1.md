# Task 10: ri-revisione del giro di correzione 1 (c81fa1e, base 16fdcd8)

### Verdetti sui rilievi

1. **(Important) Tabella della sezione 3 del piano principale con `|` non escapati.** INDIRIZZATO. Le righe B3 e B4 (piano principale, righe 52 e 53) hanno ora `Pattern \| None` e `str \| None`. Script sui separatori non escapati (anche dentro i backtick, come fa GFM) su tutte le tabelle dei documenti `.md` di `docs/` toccati dal ramo (`git diff --name-only main...HEAD`): nel piano principale nessuna riga fuori colonna. Due righe fuori colonna restano nella spec, righe 1950 (revisione 14) e 1960 (revisione 24) della sezione 20: sono preesistenti (`git blame`: commit bcaaf85 «revisione 14» e 3aa47c2 «P3c», già su `main`), non del ramo. Non bloccano.
2. **(Important) `rules(text, area)` nella riga B4 → B5-B7.** INDIRIZZATO. Piano principale riga 53: «L'helper dei test di regole è `rules(text, area)` di `tests/test_rules_ai.py` … un'area nuova lo importa, non lo riscrive».
3. **(Minor) Quattro punti.**
   - Riga «Progetto 1» della sezione 13 e sezione 16 della spec (riga 1779): INDIRIZZATO. Entrambe dicono che il testo del task, scritto dal modello nel passo 1, chiedeva già quelle righe (prova di esecuzione, non del precaricamento) e che il precaricamento lo provano i titoli `isMeta` e il revisore che cita da sé R-INFRA-04 e 05.
   - Spec 6.3 (riga 489): INDIRIZZATO, ora «rilievi `R-<AREA>-…`», nessun `R-AI-` residuo nel paragrafo.
   - Riga B3 del piano principale: INDIRIZZATO, «oggi `ai.toml` e `infra.toml`».
   - Revisione 31 (spec riga 1967): INDIRIZZATO. Le sette scelte del 07/11/2026 coincidono, una a una e nello stesso ordine, con «Cosa hai deciso» di `docs/profili/infra.md` (righe 102-108): R-INFRA-01 «dove gira oggi», R-INFRA-02 estesa a docker, R-INFRA-05 senza compose, eccezioni `.example`/`.sample`/`.template` di R-INFRA-06, cartelle di GitHub, cambio per `ai`, «li imposta l'utente».
4. **(Minor) Sezione 9, tre rinvii chiusi con la copia integrale del testo di B3.** INDIRIZZATO. `grep "Testo di B3"` nel piano: zero occorrenze. Le tre voci (radice vera, `agents/`+`prompts/`, piccole cose di B3) tengono solo lo stato nuovo in una riga. Nessuna informazione ancora necessaria è andata persa (le voci aperte restano).

### Danni nuovi nel diff della correzione
Nessuno. Il diff tocca solo le 4 righe di tabella (due della sezione 3, la riga «Progetto 1»), le voci della sezione 9, 6.3, sezione 16 e riga 31 della spec; conteggio colonne invariato; nessun nome utente, host o token nel testo aggiunto.

### Osservazioni fuori ambito
- Righe 1950 e 1960 della spec (sezione 20) con una colonna in più, preesistenti.
- Il report cita `task-10-fix1-docs.log` per `tests.test_docs`: non l'ho aperto né rieseguito (commit solo documentale).

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
