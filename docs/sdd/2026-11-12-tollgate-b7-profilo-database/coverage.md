## Copertura: punti del progetto e del piano principale destinati a B7 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: `database` (Supabase e le edge function) nel primo gruppo | 3, 4, 5, 6 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `database` | 3 (sezione «Dove informarsi»), 4 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 6 |
| Progetto 2, non obiettivi: `security` fuori da B | decisione 9 (RLS solo per ciò che `database` scrive); 4 (la pagina lo dice) |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 4, 5 |
| Progetto 2, anti-obiettivo «fonti inventate» | 4 (verificatore di sola lettura su regole, pattern, marcatori); decisione 12 |
| Progetto 3.4, riga `database`: schema e migrazioni letti prima; documentazione di Supabase o PostgreSQL della versione | 3 (decisione 9, «Prima di scrivere») |
| Progetto 3.4, riga `backend` sul runtime delle edge function, che vale per `database` (progetto 12) | 3 (regola sulle edge function, «Dove informarsi») |
| Progetto 4, riga `database`: L2 con `final-database` | 3 (frammento), 6, 7, 8; decisioni 10, 13 |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 3, 4, 5 |
| Progetto 11: i comandi solo locali di Supabase dietro `npx` | 1; decisione 6 |
| Progetto 12: edge function a `database`; `exclude` di `backend` | 3 (Q3, Q11, Q30); decisione 3 |
| Progetto 14: scritture di Supabase salvo `--local`; prova reale fino alla revisione finale | 1; 7, 8; decisioni 6, 16 |
| Catalogo 2, riga `database`; nota sulle graffe | 3; decisioni 2, 4 |
| Catalogo 2.1, riga `database` (skill, specialista, modello `inherit`) | 3, 6; decisioni 10, 12 |
| Catalogo 2.3, `dod` «migrazione applicata e annullata» | decisione 14 |
| Catalogo 4, fonti di `rules-database`; prefisso `R-DATABASE-` | 3, 4; decisione 12 |
| Piano principale, sezione 2, riga B7: `rules-database`, agenti, `final-database`, percorsi, `dod` | 3, 6; decisioni 2, 10, 14 |
| Piano principale, sezione 3, B5 → B6-B7 e B6 → B7: `FLAG_EFFECTS`, forma `ext` per `**/*.sql`, `FrontendPrecedenceTest` come modello, `AREAS` | 1, 3, 6; decisioni 2, 5, 6 |
| Sezione 9, «A B4-B7, da B3»: prefisso; forma per `**/*.sql`; rilevamento solo nei sorgenti; agenti nuovi | 3, 6; decisioni 2, 4, 11 |
| Sezione 9, «A B5-B8, da B4»: comandi locali di Supabase dietro un lanciatore | 1 |
| Sezione 9, «A B6-B8, da B5»: `exclude` e le edge function (monorepo); scritture remote con lo schema di `FLAG_EFFECTS`; test di `bash`; test di `init` con più prefissi (non serve: nessun `exclude`) | 1, 3; decisioni 3, 6, 8, 17 |
| Sezione 9, «A B4-B7, da B3»: cosa si è perso nell'implementatore; «A B6-B8, da B5»: minori dei test di `rules-backend` da copiare | 3, 4, 5; decisione 17 |
| Sezione 9, «A B7-B8, da B6»: P14 e P36; divieto di `node` e `npm`; lookahead di `SAVED_PATH` e test; `_concrete_paths` e la f-string; virgole degli agenti finali; accoppiamento del test di `frontend`; minori dei test di `rules-frontend` | 2, 3, 6, 7; decisioni 11, 17 |
| Brief di scrittura: B7 da sola o divisa | decisione 15 |
| Brief di scrittura: prova reale senza `supabase` né rete | 7, 8; decisione 16 |
| Brief di scrittura: lezioni di B6 (notifiche dei subagenti, sonda a ogni giro, pagine che invecchiano, implementatori fermi, hook di Stop) | istruzioni d'esecuzione; decisione 5; Task 4 Step 1; Task 9 Step 3 |
| Revisione della spec del nucleo | 9 |
