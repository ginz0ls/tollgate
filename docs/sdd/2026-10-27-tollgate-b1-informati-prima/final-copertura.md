## Copertura: punti del progetto destinati a B1 → task

| Punto del progetto | Task |
|---|---|
| 1, causa tecnica: implementatore senza `WebFetch`, `WebSearch`, context7 | 5 |
| 2, obiettivo 1: passo comune prima di modificare file | 4, 6, 7, 8 |
| 2, obiettivo 2: controllo delle fonti sulle letture registrate | 2, 3, 4, 6 |
| 2, anti-obiettivo «frase vuota senza lettura registrata» | 3 (`check_note`), 6, 7 |
| 2, obiettivi 3 e 5 (primo gruppo di profili, agenti per area) | **B2-B7** (piano principale di B, sezione 4) |
| 2, anti-obiettivo «passo troppo pesante»: L0 solo avviso, una volta per lavoro; permessi di `WebFetch` | 7 (`test_l0_warns_once`); 5 (decisione 18) |
| 2, anti-obiettivo «regole mai lette da una persona» | **B2-B7** (pagine approvate) |
| 2, anti-obiettivo «fonti inventate» nella nota | 3 (`test_check_note_source_not_read`), 6 |
| 3.1 L0 avvisa, L1 e L2 bloccano; L0 che cresce | 7; interruttore: decisione 8 (accensione in B2) |
| 3.2 contenuto della nota, «nessuna fonte esterna» con motivo | 3, 6, 8 (revisore) |
| 3.3 punti 1-4 | 3 (`check_note`), 4 (letture), 6 |
| 3.3 pertinenza dal revisore del task | 8 |
| 3.4 «Dove informarsi» | **B2-B7**: sono le regole dei profili; B1 consegna il formato delle fonti (decisione 2) |
| 3.5 strumenti, pagine come dati non fidati | 5 |
| 3.5 le tre verifiche e i ripieghi | 1 (Step 2 e 4); conseguenze nei Task 3-7 |
| 3.5 context7 assente → solo `WebFetch` | 1 (Step 4), 5 |
| 3.6 giri di correzione, nota del task; `reopen plan` | 2 (`for_task`, `reset_plan`), 6, 7, 8 |
| 3.6 L0 senza task: un avviso per lavoro | 7 |
| 3.6 nomi dei modelli in `rules-base` | **B2** (è una regola) |
| 4 i profili; `base` caricata da ogni agente | **B2-B7** |
| 5 regole approvate; il blocco acceso dopo `rules-base` | interruttore nel Task 3 e 7 (decisione 8); approvazione in **B2** |
| 6 dove sta la nota e in che formato | decisioni 1, 2; Task 3, 6 |
| 6 come gli hook registrano le letture | decisioni 4, 5, 15; Task 2, 4 |
| 6 normalizzazione degli URL, libreria e context7 | decisione 4; Task 3 |
| 6 come `rules-base` arriva agli agenti | **B2** |
| 6 testo dell'avviso e del rifiuto | Task 7 |
| 6 ordine e dimensione delle fette | piano principale di B |
| 6 revisione della spec del nucleo | 10 |
| 7 test della suite (quattro casi) | 7 (`test_l1_without_note_denied_when_enforced`, `test_l0_warns_once`, `test_invalid_note_denied_with_problems`, `test_valid_note_passes`) e 3 |
| 7 prova reale L1 | 9 |
| 7 eval minimi | **B8** |
| 8 vincoli del nucleo | Global Constraints |
| 8 lavori iniziati prima di B; deroga per `adopt` | 2, 6, 7 (decisione 10) |

