 1. Task 1: minor (deferred): init.py:218 e :260 ricostruiscono `tuple(exclude)` a ogni file.
 2. Task 1: minor (deferred): `_drift` passa `exclude` a `_concrete_paths` su file già filtrati (ridondante, innocuo).
 3. Task 1: minor (deferred): il segmento di `_EXCLUDE` accetta il newline, come `_SEGMENT` (stesso minore di B4 Task 1).
 4. Task 1: minor (deferred): nessun test di `init` con due prefissi o con un prefisso a più segmenti (il parsing li copre).
 5. Task 1: minor (deferred): la chiave `exclude` non è ancora nella spec 11.4 (la scrive il Task 9, decisione 4).
 6. Task 2: minor (deferred): `wrangler kv namespace --help`, `wrangler r2 bucket` e `wrangler r2 bucket --help` diventano effetti (decisione 6 alla lettera; già nel costo, ruling D8).
 7. Task 2: minor (deferred): mancano test per `pnpm -w release`, `npm run-script deploy`, i valori di `-C`/`--dir`/`--prefix`, `yarn workspace deploy build` (le sonde passano).
 8. Task 2: minor (deferred): nessun test di `[external_effects] allow`/`commands` con le voci nuove di Wrangler.
 9. Task 2: minor (deferred): nessun test del ripiego `text_effect` per `kv:namespace` e per `--remote=false`.
10. Task 2: minor (deferred): buchi già scritti come costo (opzioni globali di Wrangler, `--loglevel info run deploy`, `yarn workspaces foreach run deploy`): li scrive il Task 9.
11. Task 3: minor (deferred): R-BACKEND-12 unisce due obblighi; la parte «il report non riporta comandi…» passa con un report che tace; «o un database» va oltre KV, D1, R2 (lo giudica anche il verificatore del Task 4).
12. Task 3: minor (deferred): la `Fonte:` di R-BACKEND-08 non cita `code-reviewer` («Error message leakage») per il corpo della risposta d'errore.
13. Task 3: minor (deferred): `USER_CHOICES` del test fissa solo R-BACKEND-01; R-BACKEND-02 e 12 (scelte dell'utente) no.
14. Task 3: minor (deferred): l'`if any(...)` finale di `test_endpoint_rules_say_how_to_recognize_an_endpoint` è tautologico.
15. Task 4: minor (deferred): `test_page_has_no_private_data` controlla solo `/home/`.
16. Task 4: minor (deferred): il metodo `sources_main` nei test non è usato.
17. Task 4: minor (deferred): alcune regex dei test della pagina sono deboli.
18. Task 4: minor (deferred): `docs/profili/infra.md` (approvata, non si tocca) dice ancora che le scritture remote di KV, D1 e R2 restano scoperte: lo scrive il Task 9 e il rapporto finale.
19. Task 4: minor (deferred): il test del rinvio normalizza gli spazi su tutta la sezione e può leggere anche il paragrafo dopo la voce.
20. Task 5: minor (deferred): nessun test asserisce che «Come rispondere» e «Rinvio» siano spariti dalla pagina approvata (infra non lo fa).
21. Task 5: minor (deferred): le docstring dei test saltati dicono ancora «col Task 5» (come infra).
22. Task 6: minor (deferred): agents/implementer-backend.md:115 elenca `psql` tra i comandi non coperti, ma `psql` è in `_DEFAULT_EFFECTS` (scoperto solo se il progetto lo mette in `allow`): la condizione del piano è caduta.
23. Task 6: minor (deferred): nella stessa frase `kv namespace` e `r2 bucket` sono presentati come sempre fermati, ma le letture (`list`, `get`, `info`) passano.
24. Task 6: minor (deferred): `assertIn("push", …)` in `test_real_infra_agent_names_uncovered_commands` è debole.
25. Task 7: minor (deferred): `SAVED_READERS` di flowreg.py è un elenco chiuso di lettori: un `Bash` con `python3 -c "open('…/tool-results/…')"` o `jq . …/tool-results/…` non viene ripulito né segnalato (per la prova del Task 8 vale la verifica a mano delle evidenze).
26. Task 7: minor (deferred): `tool_use_result.stderr` non viene sostituito.
27. Task 7: minor (deferred): `Handler` di `spikes/b5/flow/server/app.py` non ha test (vetrina del progetto di prova).
28. Task 8: minor (deferred): il rapporto dice che il brief del revisore contiene R-BASE-05, 07, 10, 11; nello stream c'è solo R-BASE-05 (le altre le cita il revisore): frase da correggere.
29. Task 8: minor (deferred): «riga con il testo della revisione» imprecisa (il prompt dell'Agent è il percorso di review-1.md, riga 208; il testo è alla riga 225).
30. Task 8: minor (deferred): registro-1/limiti.txt:1 dice «Task 9» (intestazione dello script ereditata da B4).
31. Task 9: minor (deferred): in 11.4 il perché del `dod` vuoto è solo un rimando a 8.7.
32. Task 9: minor (deferred): i due minori del Task 6 sul testo di `implementer-backend` (`psql`, letture di `kv namespace`/`r2 bucket`) non sono nel blocco «A B6-B8, da B5»: li tratta la revisione finale.
33. Task 9: minor (deferred): in 8.5 della spec la frase finale ha due parentesi consecutive.
