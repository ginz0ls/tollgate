# Report Task 11 B3

Status: DONE. Commit: "tollgate B3: prove, spec rev 29, piano principale di B, catalogo" (solo i quattro documenti).

## Fatto
- Spec del nucleo rev 29: intestazione, 6.3 (rules-<area> precaricata, task misti, derivazione degli agenti), 7.1 (READONLY_TYPES, due punti da aggiornare), 7.3 (revisori per area con WebFetch), 11.2 (profili: percorsi concreti, un git grep per frammento, GitError non fatale, tollgate.toml esistente, agente che manca), 11.4 (readonly_agents, frammenti di profilo, area_rules), 16 (riga della prova reale), riga 29 della sezione 20.
- Catalogo: principi 6 e 7, intro sezione 2 (percorsi concreti, rilevamento per contenuto, nota graffe per B4/B6), riga ai di 2.1, strumenti in 2.2, fonti di rules-ai, nota sul prefisso R-<AREA>-, sezione 6.
- Piano principale: stato in testa, riga B3, sezione 3 (nomi reali), sezione 9 (stato di ogni rinvio, blocchi B3-bis / B4-B7 / B8 con i minor rinviati), nuova sezione 11 «Prove di B3» (tabella Copertura + prove oltre la tabella).
- Progetto: «B1, B2 e B3 eseguite».

## Verifiche
- Tutti i 131 nomi di test citati nella sezione 11 esistono in tests/ (controllo con script).
- test_docs verde; suite completa `PYTHONWARNINGS=error::ResourceWarning tests/run`: 3387 test OK su 3.11 (skipped=4) e 3.13 (skipped=2), nessun «unclosed» (task-11-suite.out).
- Nessun nome utente/host/percorso /home nei testi aggiunti.

## Scostamenti / dubbi
- La prova reale è del 02/11/2026 ma il file ha la data 2026-11-01 (nome fissato dal piano): detto così.
- L'attribuzione dei test ai file nella sezione 11 è stata controllata per esistenza del nome, non file per file.
