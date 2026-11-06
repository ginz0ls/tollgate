# Task 8: report dell'implementatore

## Cosa ho scritto

Solo documentazione: nessun codice. File toccati (4 oltre ai due documenti del brief; il quarto è imposto dalle carte del controller):

- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 30)
- `docs/uso/limiti.md` (stessa voce di 1.2, richiesta da D15 e da `test_limits_match_spec_1_2`)
- `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento)
- `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`

### Spec del nucleo, revisione 30, sezione per sezione

- Intestazione: «Revisione: **30**» con gli esiti (prova vera «nessuna chiave», fatti dei fornitori) e le sezioni toccate; la rev 29 resta in coda.
- 1.2: voce nuova «La chiave del controllo dei modelli sta nell'ambiente della sessione, leggibile da qualunque comando» (D15), sotto «Limite nuovo in B3-bis (rev 30)»; stessa voce come `###` in `docs/uso/limiti.md` sotto un `##` nuovo «Il controllo dei modelli».
- 3: albero con `templates/models.toml`; paragrafo «Rete del controllo dei modelli» dopo gli strati (analisi pura, rete solo in `modelsfetch`, import dentro la funzione, hook senza rete, host solo nel file di dati).
- 3.1: riga `models check [--refresh]` (D4, D7: tre messaggi, codici 0/1, `rifiuto: configurazione non valida: …`, non apre il DB, non negato ai subagenti, si lancia dal plugin).
- 3.2: bullet «la rete del controllo sta solo nella CLI».
- 6.1: bullet «Modelli» (solo lavoro nuovo, dopo `housekeeping.run`, mai la ripresa, mai l'esito di `start`, righe come dati, cache fresca non stampata).
- 11.4: `[models]` e `models_check` nella tabella; paragrafi nuovi: visione d'insieme, `[models] files` (decisione 1 con D2 e D9), lettura da git con `object_info_at`, dati dei fornitori (9), chiavi (4), nomi e confronto con i quattro fornitori (2, 3), client stretto con `OpenerDirector` minimo e `UnknownHandler` (5, D21), cache/ordine/forma delle righe (6, 7, 13, D10), costi accettati.
- 14 (non nell'elenco del brief): paragrafo su `tests/run` (D1: trap con `chmod` poi `rm`, entrambi `|| true`; cartella di corsa; tre perdite chiuse) e sulla rete nei test (Global Constraints). Serviva una sede per D1.
- 16: blocco «Verificato in B3-bis, il 4-5/11/2026» con una tabella (Anthropic, Step 0 a, Gemini, OpenAI con Step 0 c, OpenRouter con Step 0 b, costo e chiave di Claude Code, prova vera con esito «nessuna chiave», nessuna rete, parte di rete NON provata dal vivo), un paragrafo «Evidenze senza testo di terzi» (decisione 11, storia di git non riscritta) e la riga «Ancora da verificare» estesa a B3-bis. Fatti con parole mie, URL e data; nessun testo copiato.
- 20: riga 30 (05/11/2026) con le 13 decisioni e i ruling.

### Progetto di B

Riga di avanzamento: «B1, B2, B3 e B3-bis eseguite. B1, B2 e B3 sono unite su `main` …; B3-bis è sul ramo `b3bis-sentinella-modelli`, unione in attesa dell'OK dell'utente».

### Piano principale di B

- Riga 3 (revisione 30) e «Stato (5 novembre 2026)»: la frase di B3 «merge in attesa dell'OK» corretta in «unita su `main` il 03/11/2026»; paragrafo di stato di B3-bis (suite 3559 test su 3.11 skipped=5 e 3.13 skipped=3, dal log del Task 7; esito della prova vera detto senza abbellire).
- Sezione 2: righe di stato di B2 e B3 corrette (stesso errore, «merge in attesa» superato); nuova riga B3-bis.
- Sezione 3: riga B3-bis → B8 (righe `modelli:` di `start` per gli eval, nessun evento).
- Sezione 4: righe per i punti 9 e 10 del progetto (mancavano).
- Sezione 9: i due rinvii «A B3-bis» marcati chiusi (forma del punto unico, decisione 1; `test_real_markers_not_in_tollgate_bin` invariato, host in `templates/models.toml`); nuovo blocco «A B4-B8, da B3-bis».
- Sezione 12 «Prove di B3-bis»: le 13 righe della tabella «Copertura» con test o evidenza, più «Prove oltre la tabella». Tutti i nomi di test citati esistono (verificato con uno script sui `def test_…` di `tests/`).

## Test ed esiti

- `python3.11 -B -m unittest tests.test_docs` e `python3 -B -m unittest tests.test_docs`: 7 test, OK, dopo le modifiche (compreso `test_limits_match_spec_1_2`).
- Suite completa: vedi in fondo (sezione «Suite»).

## Scostamenti dal piano e perché

1. Ho aggiunto un paragrafo alla sezione 14 della spec (non nell'elenco del brief) perché D1 e la regola dei test senza rete non avevano una sede. Una sola sezione in più, tutta nuova.
2. Ho corretto anche la riga di stato di B2 nella sezione 2 del piano principale («merge in attesa dell'OK»): stesso errore di quello di B3, già falso dal 01/11.
3. Nella sezione 9 del piano principale non ho riportato nessun minore del ledger come «che riguarda B4-B8»: ho riletto tutte le righe `minor (deferred)` e nessuna tocca B4-B8 (riguardano il codice di B3-bis o cartelle di `/tmp`). Ho scritto due convenzioni per i test delle fette successive invece di inventare rinvii.
4. La voce di 1.2 contiene anche il dettaglio che `runner.clean_env` toglie le `TOLLGATE_…` ai comandi del progetto: verificato in `bin/tollgate_core/runner.py:87-89`.

## Autorevisione

- Brief rispettato punto per punto (Step 1-3; Step 4 in corso al momento della scrittura). Le 13 decisioni sono tutte in rev 30: 1-9 e 13 in 11.4 (e 3.1, 6.1), 10 in 14, 11 e 12 in 16; D1, D2, D4, D9, D15, D21 e l'esito dello Step 0 con gli URL sono riportati.
- «sentinella» nella spec compare una volta in 11.4 («è la "sentinella dei modelli" del progetto di B») e nella riga 30/16 solo come richiamo al progetto; nessun nome di codice. Nei testi per l'utente (`limiti.md`) uso «controllo dei modelli».
- Repo pubblico: nessun nome utente, host o percorso locale, nessun nome di progetto privato (grep sul diff: nessuna corrispondenza). Nessuna chiave letta o stampata.
- Non toccati `skills/rules-base/SKILL.md`, `skills/rules-ai/SKILL.md`, `docs/profili/`. Nessuna rete, nessun `claude`.

## Dubbi

- `docs/uso/comandi.md` dice che la copia del gate in `.github/tollgate/` «non lo contiene» (il comando `models check`). Leggendo `bin/tollgate_gate/install.py:83-100` e `_sources` risulta invece che `install.files` copia tutto `bin/` (quindi il codice di `models check` c'è) ma non `templates/`, quindi il comando lanciato da lì darebbe «controllo non riuscito» per mancanza di `templates/models.toml`. Nella spec ho scritto la forma precisa («ha il codice ma non il file dei fornitori»). Non l'ho verificato eseguendo il comando dalla copia; la frase di `comandi.md` (Task 4) va allineata dal controller o dalla revisione finale: non l'ho toccata perché fuori dai file del task.
- La spec dice, per l'esito della prova vera, «un tentativo su tre»: il ledger dice «2 tentativi rimasti» dopo il primo, coerente.
- Il numero dei test della suite (3559) viene dal log del Task 7; lo confermo o correggo con la corsa del Task 8 (sezione «Suite»).

## Suite

`PYTHONWARNINGS=error::ResourceWarning tests/run` (uscita in `task-8-suite.out`, RC=0): Python 3.11.16, 3561 test, OK (skipped=5); Python 3.13.5, 3561 test, OK (skipped=3). Nessun «unclosed». `test_db_restore_interactive_eof_and_ctrl_c` verde al primo colpo. Il numero 3561 sostituisce il 3559 del log del Task 7 (i commit a00a417 e 34ce2c9 hanno aggiunto test); il piano principale dice 3561.
