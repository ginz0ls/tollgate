 1. Task 1: minor (deferred): la riga SubagentHandback non cita handbackReport di PostToolUse Agent in primo piano (correzione di P0).
 2. Task 2: minor (deferred): check_l2 continua a cercare i report del piano anche con plan-approval superato (asimmetria con il ramo della spec).
 3. Task 2: minor (deferred): check_l2 non confronta il `path` di plan-approval.md con plan_path.
 4. Task 2: minor (deferred): i report della spec non sono legati allo spec_sha dell'approvazione (conforme a D15): da ricordare nel gate di P4.
 5. Task 2: minor (deferred): `slices` non intero nell'intestazione di spec-approval è ignorato in silenzio (lens non richiesto).
 6. Task 2: minor (deferred): chiavi duplicate in `counts` dell'intestazione: vince l'ultima.
 7. Task 2: minor (deferred): un test di check_l2 asserisce solo che esista un problema, non il messaggio; manca il caso di approvazione propria con `path` diverso.
 8. Task 3: minor (deferred): auditrules.py:76 `number` float 1.0 passa il confronto con 1.
 9. Task 3: minor (deferred): auditrules.py:80-83 con plan_sha=None o viewpoint=None passati dal chiamante per un giro che li richiede, un JSON senza quel campo è valido; il viewpoint atteso non è controllato contro VIEWPOINTS (il chiamante del Task 6 passa sempre i valori del giro).
10. Task 3: minor (deferred): un esito diverso da empty e superseded conta come findings senza segnalarlo.
11. Task 3: minor (deferred): campo `v` della riga JSON non richiesto (nessun controllo di versione futuro).
12. Task 4: minor (deferred): audits.close_round non valida outcome e counts; supersede ha `now` inutilizzato.
13. Task 4: minor (deferred): test_latest_version_is_5 sta nella classe MigrationV4Test.
14. Task 4: minor (deferred): git.ls_files_at non protegge un ref che inizia con `-`.
15. Task 4: minor (deferred): test_blob_at_directory_is_none non copre il prefisso comune (d/f con d/f.md presente; comportamento verificato corretto a mano).
16. Task 5: minor (deferred): i backtick nei percorsi non sono neutralizzati nel brief.
17. Task 5: minor (deferred): ⚠️ dimensioni.md citato nel brief delle lenti arriva col Task 13 (da verificare lì).
18. Task 6: minor (deferred): _write_atomic cattura solo OSError: con surrogati isolati nel messaggio resta un .tmp vuoto in reviews/<N>/ (il runner cattura il ValueError, nessun crash).
19. Task 6: minor (deferred): se il blob della spec non si legge, i rilievi meccanici del pitch spariscono in silenzio (audit_round._mechanical).
20. Task 6: minor (deferred): dopo «report non scritto» l'unico segnale è l'evento veto (D13); audit prepare ristampa il lancio del giro aperto.
21. Task 7: minor (deferred): resolve e approve nei test del Review Focus applicati dalla libreria (D20), il main() di act apply non esercitato lì.
22. Task 7: minor (deferred): non coperta la catena reale di un tetto del piano fino a approve plan.
23. Task 7: minor (deferred): con TOLLGATE_TEST_CONFIG impostato audit.work_config rifiuta comunque se manca la base (solo ambiente di test).
24. Task 7: minor (deferred): finalreview, openpr, taskcmd, finishcheck e sync ripetono ancora «base o ramo predefinito + load_config» (fuori ambito, preesistente).
25. Task 8: minor (deferred): testi di rifiuto per task e implementatore duplicati tra sync.py e l2acts.py, a parte il suffisso.
26. Task 8: minor (deferred): nessun test dell'interruzione fra reset_plan e set_phase (il codice regge: reset_plan ritorna [] con plan_sha già nullo).
27. Task 9: minor (deferred): nel test end-to-end close_tasks e fl.commit del banco sono scorciatoie dirette sul DB; la mutazione provata copre solo adopt.
28. Task 9: minor (deferred): righe oltre 100 colonne (finishcheck.py:187 nuova; start.py:199,347,462 e audit.py:485 preesistenti).
29. Task 10: minor (deferred): con NEEDS_CONFIRM peek dà il generico «lancia audit prepare» senza dire che serve la conferma.
30. Task 11: minor (deferred): violations.py:97 riga di docstring da 116 caratteri.
31. Task 11: minor (deferred): nel test di _review_report `cfg=lambda` ricarica la configurazione a ogni chiamata.
32. Task 11: minor (deferred): il lancio diretto dei file di test (riga 24) richiede PYTHONPATH=bin:. (preesistente).
33. Task 12: minor (deferred): un rilievo archiviato prima della creazione del task entra comunque nell'instradamento, senza test (conforme alla riga 71).
34. Task 12: minor (deferred): dopo il rifiuto del caso superseded (riga 50) blocco e atto restano aperti, senza test.
35. Task 13: minor (deferred): il test delle opzioni delle skill esclude `--force` (cleanup lo cita come comando git da non usare).
36. Task 13: minor (deferred): nessun test copre il testo della fase plan di start (fetta successiva e piano della sola fetta).
37. Task 14: minor (deferred): i log del primo tentativo sono stati spostati in /tmp/tollgate-p3c-keep, fuori dalla cartella della prova prescritta (/tmp/tollgate-p3c).
38. Task 14: minor (deferred): rapporto della prova: backtick rotti alla riga 5; righe 11, 14, 21 citano /tmp/tollgate-p3c/flow come se fosse la prova (ora è prova-1/flow); doppia parentesi nel non esercitato.
39. Task 14: minor (deferred): verifica_gh controlla il PATH dello script, non quello della shell del tool Bash di claude: da verificare alla prossima prova reale.
40. Task 15: minor (deferred): tabella P3a del piano principale (riga ~225) ha ancora «(P3c)» in «Resta a».
41. Task 15: minor (deferred): riferimenti «riga 49/71» e D2-D19 nella spec si risolvono solo nel registro (da portare in docs/sdd/ dopo il merge).
