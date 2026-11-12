## Copertura: punti del progetto e del piano principale destinati a B6 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: `frontend` nel primo gruppo | 3, 4, 5, 6 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `frontend` | 3 (sezione «Dove informarsi»), 4 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 6 |
| Progetto 2, non obiettivi: trasversali `a11y` e `performance` fuori da B | decisione 9 (nessuna skill `rules-a11y`, nessun `cross`, `rules-performance` fuori) |
| Progetto 2, anti-obiettivo «passo troppo pesante» (cambiare un colore) | decisione 13 (L0) |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 4, 5; decisione 14 |
| Progetto 2, anti-obiettivo «fonti inventate» | 4 (verificatore di sola lettura, anche su pattern e marcatori); decisione 12 |
| Progetto 3.4, riga `frontend`: documentazione della versione in `package.json`; cercare un componente simile | 3 (R-FRONTEND-01, 02, «Dove informarsi») |
| Progetto 4, riga `frontend`: L0 | 3 (frammento); decisione 13 |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 3, 4, 5 |
| Progetto 12: `services/` fuori da `backend` («fino a B6 al generico») | decisione 6; 4 («Da decidere tu») |
| Progetto 13: accessibilità dentro `rules-frontend` | 3 (R-FRONTEND-05…10, `test_a11y_rules_name_a_wcag_criterion`); decisione 9 |
| Progetto 13: rimedio per `routes/` d'interfaccia | 3 (marcatori, `test_real_precedence_p9`, `p10`, `p19`); 7, 8 (P9 dal vivo); decisione 5 |
| Catalogo 2, riga `frontend`; nota sulle graffe | 1 (forma `ext`), 3; decisioni 2, 3 |
| Catalogo 2.1, riga `frontend` (skill e revisore) | 3; decisioni 9, 10 |
| Catalogo 2.3, `dod` «lint, typecheck, test dei componenti» | decisione 8; R-FRONTEND-11 |
| Catalogo 3, `a11y` e `performance` | decisione 9; 9 (catalogo 3) |
| Catalogo 4, fonti di `rules-frontend` e `rules-a11y`; prefisso `R-FRONTEND-` | 3 (`test_rule_ids_consecutive`); decisioni 10, 12 |
| Piano principale, sezione 2, riga B6: `rules-frontend` (e `rules-a11y` da decidere), agenti, percorsi, `dod` | 3, 6; decisioni 3, 8, 9 |
| Piano principale, sezione 3, B4→B5-B7 e B5→B6-B7: `parse_pattern`, `concrete_for(..., exclude=)`, `Fragment.exclude`, regola di I-1, `AREAS`, `rules(text, area)`, test da copiare | 1, 3, 6; decisioni 2, 5, 7, 16 |
| Sezione 9, «A B4-B7, da B3»: prefisso `R-FRONTEND-`; forma per `**/*.{tsx,jsx}`; rilevamento solo nei sorgenti; agenti nuovi | 3; 1; decisione 5; 6 |
| Sezione 9, «A B6-B8, da B5»: `routes/` e `handlers/` contro i pattern per estensione | decisioni 4, 5; 3 |
| Sezione 9, «A B6-B8, da B5»: limite di I-1 in cartelle annidate | decisione 4 (P4-P6, P13, P20, P25-P31); 3 |
| Sezione 9, «A B6-B8, da B5»: nessun test di `init` con più prefissi di `exclude` | 3 (`test_real_frontend_exclude_several_prefixes`); decisione 7 |
| Sezione 9, «A B6-B8, da B5»: test di `rules-backend` da copiare con le correzioni | 3, 4, 5; decisione 16 |
| Sezione 9, «A B6-B8, da B5»: `SAVED_READERS` e `stderr` di `togli-pagine` | 2; decisione 16 |
| Triage di B5, voce 30: intestazione «Task 9» di `limiti.txt` | 2; decisione 16 |
| Sezione 9, «A B4-B8, da B3-bis»: cartelle temporanee | Global Constraints |
| Brief di scrittura: B6 da sola o divisa | decisione 14 |
| Brief di scrittura: prova reale senza `node` né browser | 7, 8; decisione 15 |
| Brief di scrittura: lezioni di B5 (implementatori fermi dopo la suite, sentinelle del controller, paralleli, fonti, evidenze, brief corto, revisione finale sulle precedenze) | istruzioni d'esecuzione; Review Focus 1-2; Task 8 |
| Revisione della spec del nucleo | 9 |
