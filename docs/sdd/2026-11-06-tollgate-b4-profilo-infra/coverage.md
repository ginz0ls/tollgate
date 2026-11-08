## Copertura: punti del progetto e del piano principale destinati a B4 → task

| Punto | Task |
|---|---|
| Progetto 1: «è su Vercel, leggi le cose prima» | 4 (R-INFRA-01) |
| Progetto 2, obiettivo 3: `infra` nel primo gruppo | 4, 5, 6, 7 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `infra` | 4 (sezione «Dove informarsi»), 5 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 7 |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 5, 6; decisione 15 |
| Progetto 2, anti-obiettivo «fonti inventate» | 5 (verificatore di sola lettura, anche sui pattern); decisione 12 |
| Progetto 3.4, riga `infra`: aprire la configurazione presente, documentazione della versione installata | 4 (R-INFRA-01, 02, 03, «Dove informarsi») |
| Progetto 4, riga `infra`: L1, Vercel | 4 (frammento); decisioni 1, 13 |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 4, 5, 6 |
| Progetto 11: workflow al gate; Worker in `backend`; Docker sì | decisioni 1, 5, 6, 18; 2 (`test_name_pattern_skips_excluded_prefixes`); 4 (`test_fragment_leaves_out_ci_and_workers`); 5 (`test_page_explains_what_changes`) |
| Piano principale, sezione 2, riga B4: `rules-infra` con Vercel, agenti, percorsi (anche `vercel.json`), `dod` | 1, 2, 4, 7; decisione 7 |
| Piano principale, sezione 3, B3→B4-B7: frammenti, `init`, agenti derivati, elenchi di sola lettura | 1, 2, 7 |
| Piano principale, sezione 9, «A B4-B7, da B3»: prefisso `R-INFRA-` | 4 (`test_rule_ids_consecutive`, `test_area_rules_of_research_match_rules`) |
| Sezione 9: forma dei pattern (`_PATTERN`, `_FOLDER_PATTERN`, percorsi concreti) | 1, 2; decisioni 2, 3 |
| Sezione 9: rilevamento per contenuto solo nei sorgenti | decisione 5 |
| Sezione 9: cartelle `agents/` e `prompts/` e file che non sono codice | 2; decisione 4 |
| Sezione 9: agenti nuovi (tupla, `rules-base`, elenchi, id a mano) | 7; decisione 9 |
| Sezione 9: test esistenti sulla radice vera | 2; decisione 16 |
| Sezione 9: test da copiare | 4, 5 |
| Sezione 9: piccole cose rimaste aperte nel codice di B3 | 1; decisione 10 |
| Sezione 9, «A B4-B8, da B3-bis»: cartelle temporanee, test che toccano `start` | Global Constraints |
| Sezione 9, «A B3-B7»: `rules-base` negli agenti nuovi; regole giudicate sul visibile | 7; 4 (`test_blocking_rules_judged_on_diff_or_report`) |
| Spec 8.5: un deploy è un effetto esterno da approvare, anche con `npx` | 3; decisione 17 |
| Brief di scrittura: B4 da sola o unita | decisione 11 |
| Revisione della spec del nucleo | 10 |
