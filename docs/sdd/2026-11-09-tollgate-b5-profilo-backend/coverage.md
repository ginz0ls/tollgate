## Copertura: punti del progetto e del piano principale destinati a B5 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: `backend` nel primo gruppo | 3, 4, 5, 6 |
| Progetto 2, obiettivo 3: `database` per le edge function (utente) | 1, 3 (`[detect] exclude`); decisione 4 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `backend` | 3 (sezione «Dove informarsi»), 4 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 6 |
| Progetto 2, anti-obiettivo «passo troppo pesante» | decisione 12 (L0) |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 4, 5; decisione 15 |
| Progetto 2, anti-obiettivo «fonti inventate» | 4 (verificatore di sola lettura, anche su pattern e marcatori); decisione 11 |
| Progetto 3.4, riga `backend`: contratti prima di aggiungerne; documentazione del runtime dei Worker | 3 (R-BACKEND-01, 02, «Dove informarsi») |
| Progetto 4, riga `backend`: L0; backend locale senza Supabase | 3 (frammento); decisioni 1, 12 |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 3, 4, 5 |
| Progetto 11: codice dei Worker in `backend` | 3 (marcatori); decisioni 1, 3, 5 |
| Progetto 12: `services/` fuori; KV e R2 salvo `--local`; edge function a `database` | decisioni 2, 4, 6; 1, 2, 3, 4 (`test_page_explains_what_changes`) |
| Piano principale, sezione 2, riga B5: `rules-backend`, agenti, percorsi, `dod` | 3, 6; decisione 8 |
| Piano principale, sezione 3, B4→B5-B7: `parse_pattern`, `concrete_for`, `DOC_EXTENSIONS`, `EXCLUDED_PREFIXES`, `load_approved`, `launcher_candidates`, `AREAS`, `rules(text, area)` | 1, 2, 3, 6 |
| Piano principale, sezione 9, «A B4-B7, da B3»: prefisso `R-BACKEND-`; rilevamento solo nei sorgenti; agenti nuovi; test da copiare | 3 (`test_rule_ids_consecutive`); decisione 3; 6; 3, 4 |
| Sezione 9, «A B4-B8, da B3-bis»: cartelle temporanee | Global Constraints |
| Sezione 9, «A B5-B8, da B4»: scritture remote di `wrangler kv`, `d1`, `r2` | 2; decisione 6 |
| Sezione 9, «A B5-B8, da B4»: script `deploy` nei monorepo | 2; decisione 7 |
| Sezione 9, «A B5-B8, da B4»: test da copiare con il prefisso `test_real_`; `.gitignore` di `spikes/b4/flow/` | 7, 9; decisione 16 |
| Sezione 9, «A B5-B8, da B4»: prove reali con `spikes/run-b1-flow.sh` (progetto senza credenziali, `togli-pagine`) | 7, 8; decisione 14 |
| Revisione finale di B4: `togli-pagine` e `Bash` sulle copie salvate; M-5 | 7; decisione 16 |
| Brief di scrittura: B5 da sola o unita a B6 | decisione 13 |
| Brief di scrittura: lezioni di B4 (copie salvate, piano scritto nel passo 1, implementatori fermi dopo la suite, ruling su elenchi d'eccezione) | decisione 14; Task 8; istruzioni d'esecuzione |
| Revisione della spec del nucleo | 9 |

