# Task 10: report

Status: DONE. Commit `c72bcd0` (tollgate B4: prove, spec rev 31, piano principale di B, catalogo).

## Cosa ho fatto
Solo i quattro documenti indicati, nessun codice o test cambiato.
- Spec del nucleo, revisione 31: intestazione; 6.3 (task misti, derivazione degli agenti per area, paragrafo sugli agenti `-infra` e sul test d'area unico `AREAS`); 7.1 e 7.3 (`reviewer-infra` in `READONLY_TYPES` e `readonly_agents`, con `WebFetch`); 8.5 (14 voci di Wrangler più `pages publish`, `docker image push` e `docker compose push`, scansione dei lanciatori, testo di `-c` e `--call`, costi e buchi); 8.7 (i comandi del `dod` girano senza veto, riferimenti corretti: `runner.run_one`, `verify.dod_commands`); 11.2 (tre forme, `concrete_for`, documenti e cartelle di GitHub esclusi, `load_approved`, sovrapposizioni tra profili proposti nella stessa corsa, differenza per `ai`, conteggio dei file); 11.4 (tre forme, frammento di `infra` con 14 pattern, senza `[detect]`, `dod` vuoto e perché, `readonly_agents`); 16 (fatti verificati del 6 novembre, correzione su `compatibility_date`, riga della prova reale, elenco «ancora da verificare»); riga 31 della sezione 20 con le 18 decisioni e i ruling.
- Catalogo: sezione 2 (tre forme al posto di «fino a B4…», nota sulle graffe, riga `infra` con i 14 pattern), 2.1, 2.2, 2.3 (`dod` vuoto), 4 (fonti vere), 6.
- Piano principale di B: stato, riga B4 (sezione 2), sezione 3 (riga B3 e nuova riga B4 → B5-B7), sezione 9 (rinvii chiusi e aperti con il motivo, nuovo blocco «A B5-B8, da B4»), nuova sezione 13 «Prove di B4» con ogni riga della tabella «Copertura» e le prove oltre la tabella.
- Progetto di B: riga di avanzamento.

## Verifiche
- Tutti i nomi di test citati (`test_...`) esistono nei file di `tests/` (controllo con uno script).
- `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3667 test OK (skipped=7), python3.13 3667 test OK (skipped=5), uscita 0, nessun «unclosed». Nessuna ripetizione necessaria (il test del pty non è caduto). `tests.test_docs` verde.

## Scelte e dubbi
- Nel piano principale ho scritto che B4 è «sul ramo, revisione finale e unione in attesa»: da riallineare se l'unione avviene prima della consegna.
- Sezione 9: tra i «minor (deferred)» ho portato solo quelli per B5-B8 (buchi di scansione e Docker, `kv`/`d1`/`r2` a B5, Supabase locale a B7, profilo `ci`, copiatura di test e script di prova); gli altri (Task 1, 2, 4, 5, 7) restano al triage finale.
- Esempi di sovrapposizione e conteggi (12 regole, 7 `[blocca]`, 38 test di `test_rules_infra.py`, 31+14 righe del rapporto fonti) presi dai file veri e dal ledger; il numero di righe del rapporto fonti è quello del `progress.md`.
- Non ho toccato `docs/verifiche/`, `docs/profili/`, `skills/rules-*`.

## Fix round 1
- Tabella della sezione 3 del piano principale: `\|` nelle firme (righe B3 e B4); controllo con uno script su tutte le tabelle dei quattro documenti: nessuna riga fuori colonna nelle mie parti (restano due righe della sezione 20 della spec, già storte prima, 14 e 24).
- Riga B4 -> B5-B7: aggiunto `rules(text, area)`. Riga B3: «oggi `ai.toml` e `infra.toml`».
- Spec: `R-<AREA>-…` in 6.3; sezione 16 e riga «Progetto 1» del piano dicono che il report era già chiesto dal task (prova di esecuzione, non del precaricamento); riga 31 con le scelte dell'utente del 07/11 sui sette punti.
- Sezione 9: tolte le tre copie integrali del testo di B3.
- Test: `tests.test_docs` con python3.11 e python3, uscite in `task-10-fix1-docs.log` (in W).
