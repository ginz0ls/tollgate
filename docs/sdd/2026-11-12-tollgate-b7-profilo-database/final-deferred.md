1. Task 1: minor (deferred): M2 `--help`/`-h` come valore di un'opzione non globale fa passare un comando (D1 lo limita alle opzioni globali; il comando di solito fallisce).
2. Task 1: minor (deferred): M3 comandi locali dietro `npx --package supabase supabase start`, `npm exec supabase -- start`, `npm run supabase -- start` ora chiedono (candidato di `launcher_candidates` con `--` o un doppio `supabase`).
3. Task 1: minor (deferred): M4 il ripiego testuale non vede `npx supabase@2 db push` né `/usr/bin/supabase db push` (già così prima; vale anche per Wrangler).
4. Task 1: minor (deferred): M5 Prisma e Drizzle con un'opzione prima del sottocomando passano (`prisma --schema x migrate dev`, `drizzle-kit --config x push`): limite della regola aperta, già in D13.
5. Task 1: minor (deferred): M7 motivo del veto poco leggibile con `--package` o `--` (`supabase supabase db`, spazio finale).
6. Task 1: minor (deferred): M8 tre scorrimenti di `FLAG_EFFECTS` per la stessa voce di Supabase (`_supabase_reason`, `_flag_data_reason`, `_supabase_text_effect`).
7. Task 2: minor (deferred): riga del docstring di `_concrete_paths` (init.py:254) di 103 caratteri.
8. Task 2: minor (deferred): `tool-results:` scritto in un comando ora conta come cartella e fa togliere l'uscita (toglie di più, mai di meno).
9. Task 3: minor (deferred): `tests/test_rules_database.py:317` di 101 caratteri (limite 100).
10. Task 3: minor (deferred): Q46 sono due controlli di fila senza `subTest`.
11. Task 3: minor (deferred): `test_draft_is_not_approved_before_task_5` resterà un test sempre saltato dopo il Task 5.
12. Task 4: minor (deferred): il test delle scelte aperte cerca le parole nell'intera sezione «Da decidere tu», non nel punto che le spetta.
13. Task 4: minor (deferred): alcune voci di R-DATABASE-04 poggiano su un riassunto della copia senza citazione testuale.
14. Task 4: minor (deferred): ⚠️ la frase della pagina sulla CLI 2 viene dalla memoria del controller (Ruling dello Step 0 del Task 1), non da una pagina.
15. Task 4: minor (deferred): la citazione dei segreti di R-DATABASE-16 dice «with the Supabase CLI», l'etichetta `secrets set` (sostegno un po' più largo, accettato dal verificatore).
16. Task 5: minor (deferred): `test_page_records_the_choices` confronta le proposte sull'intera sezione e non nel loro punto (cinque proposte identiche «lasciare così.»), e non confronta i «Costo:».
17. Task 5: minor (deferred): la pagina approvata dice che gli agenti del profilo «arrivano dopo la tua approvazione» (vero, ma suona sfasato dopo il Task 6); la pagina approvata si tocca solo con l'utente.
18. Task 5: minor (deferred): nel punto 17 la proposta dice «tutte e sei» e l'introduzione è un settimo elemento.
19. Task 6: minor (deferred): «oggi `database`» in `docs/uso/comandi.md` invecchierà con un secondo specialista.
20. Task 6: minor (deferred): il nome «real» in `DatabaseAgentsProposeTest` è approssimativo (le skill sono finte).
21. Task 7: minor (deferred): `approve spec $ISSUE` usa il numero dell'issue al posto del numero di fette (oggi coincidono: issue 1, una fetta).
22. Task 7: minor (deferred): `test_real_flow_case_database_prepara_checks_l2_plan` non distingue L1 da L2 (plan.py tratta i due livelli allo stesso modo su quel controllo).
23. Task 7: minor (deferred): variabile `STEPS` in `spikes/run-b1-flow.sh:132-133` assegnata e mai usata.
24. Task 7: minor (deferred): nessun test sul salto delle cartelle `libero-*.prev-*` in `registra` e nella numerazione di `libero`.
25. Task 7: minor (deferred): due righe vuote prima della sezione `database` nella classe di `tests/test_b1_scripts.py`.
26. Task 7: minor (deferred): `FRONTEND_PROJECT` forse senza uso dopo la rimozione del confronto (non verificato).
27. Task 7: minor (deferred): `spikes/b7/flow/tools/unittest_junit.py` esce 1 se non gira nessun test (non succede: il progetto ha test).
28. Task 7: minor (deferred): nel rapporto junit i failure/error hanno solo `message="x"` (il dettaglio resta su stderr).
29. Task 8: minor (deferred): con due task in `resume` dello stesso tipo l'hook sceglie per `name` ma il `SubagentStart` lega al numero più basso (si potrebbe preferire il task con `reserved_at`); nessun test.
30. Task 8: minor (deferred): con un task `launch` e uno `resume` dello stesso tipo il `SubagentStart` prende prima il `launch`, l'hook sceglie per `name`.
31. Task 8: minor (deferred): la scelta per `name` in `agents.py:88` cambia anche il caso dei soli task `launch` (non richiesto, innocuo).
32. Task 8: minor (deferred): il ripiego di `apply.py` vale anche fuori da execution L1/L2, dove l'hook non filtra (rischio già presente per i task `launch`).
33. Task 8: minor (deferred): il rapporto (riga 151) riporta le lunghezze 1.129, 3.604 e 10.170 caratteri dei SessionStart tolti senza una fonte nelle evidenze.
34. Task 8: minor (deferred): il rapporto (riga 42) parla di eventi spec_audit_round per i 5 giri della spec, ma nel file sono 9 (5 della spec e 4 del piano).
35. Task 9: minor (deferred): il report del Task 9 dice che la spec 16 riporta «4061 test», ma il numero sta solo nello stato del piano principale.
36. Task 9: minor (deferred): il log della suite del Task 9 non mostra la variabile PYTHONWARNINGS con cui è girata.
37. Task 9: minor (deferred): il blocco «A B8, da B7» del piano principale mescola due rinvii di processo (minor del Task 8 sul rapporto) con quelli di prodotto.
