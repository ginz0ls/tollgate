# Minori rinviati del ramo B6 (da sottoporre a triage)

1. Task 1: minor (deferred): `docs/uso/comandi.md:124` dice ancora «tre forme» accanto alla frase nuova sull'estensione (portato nel Task 3, che tocca la stessa sezione).
2. Task 1: minor (deferred): messaggio di `_parse` in `fragments.py` con una f-string spezzata in due senza motivo.
3. Task 1: minor (deferred): `_concrete_paths` tiene un percorso esatto acceso da `name` anche se un `**/*.<ext>` proposto lo copre (`**/vercel.json` con `**/*.json`); innocuo, ridondante.
4. Task 2: minor (deferred): il lookahead di `SAVED_PATH` (`flowreg.py:33`) non riconosce la sola cartella seguita da `,`, `}`, `]`, `:` o `\` (`ls {/x/tool-results,/y}`, `${D:-/x/tool-results}`); con un file dentro sì. Raro, ma contro «dalla parte sicura».
5. Task 2: minor (deferred): `test_togli_pagine_bash_any_reader` prova solo il prefisso `<` dei sei di D1; mancano i negativi del lookahead (`tool-results.txt`, `tool-results-old/x`) e un `Bash` con `stdout` e `stderr` pieni insieme.
6. Task 2: minor (deferred): un percorso tra virgolette con spazi (`"/x/tool-results/a b"`) dà il nome `a` nel segnaposto (solo estetico).
7. Task 2: minor (deferred): il report del Task 2 non riporta l'output dei comandi RED/GREEN, solo l'esito.
8. Task 3: minor (deferred): R-FRONTEND-12 ha esempi («gradiente viola su bianco», «carattere di sistema») che le fonti non dicono così (FUE: «Purple/indigo everything», «Excessive gradients»); portato nel Task 4, che corregge la skill dove una fonte non passa.
9. Task 3: minor (deferred): `test_a11y_rules_name_a_wcag_criterion` controlla numero e livello del criterio, non il nome.
10. Task 3: minor (deferred): R-FRONTEND-07 ammette `aria-label` come etichetta (voce «Screen Readers» della lista) mentre la voce «Forms» chiede un'etichetta visibile: da dire nel rapporto delle fonti e nella pagina (portato nel Task 4).
11. Task 3: minor (deferred): R-FRONTEND-11 cita «Component Architecture» e non «Verification» della bozza: confermato, nessuna azione.
12. Task 4: minor (deferred): `test_removed_sources_are_not_in_the_skill` ha il ciclo sulle righe `no` vuoto (nessuna riga `no` nel rapporto): resta valido per i quattro `assertNotIn`, la docstring promette di più.
13. Task 4: minor (deferred): la pagina usa «l'utente» sia per chi usa il sito sia per chi legge («tu»).
14. Task 4: minor (deferred): restano `assertIn`/`assertNotIn` sul testo della skill nei test del Task 3 (`tests/test_rules_frontend.py:234-252`, `:313`), che in caso di errore stampano una sezione della skill (file pubblico, senza dati privati).
15. Task 4: minor (deferred): righe nuove oltre i 100 caratteri e rientri non allineati nelle `re.search` multilinea (`tests/test_rules_frontend.py:408-412`, `:536-543`).
16. Task 5: minor (deferred): i test «prima dell'approvazione» di `tests/test_rules_frontend.py` (circa righe 574-663, `skip_if_approved`) restano e ora si saltano sempre (come in B5, `test_rules_backend.py:459`).
17. Task 5: minor (deferred): `test_page_records_the_choices` conta le frasi «Hai approvato: resta la proposta» ma non confronta il testo delle proposte con la versione prima dell'approvazione (coperto solo dal diff).
18. Task 6: minor (deferred): `test_rules_frontend_not_required` (`tests/test_taskcmd.py`) asserisce `skills_required == []` su un blocco con `skills = []` (vero comunque); stesso schema di `test_rules_backend_not_required`.
19. Task 6: minor (deferred): `test_real_frontend_agent_names_forbidden_tools` controlla che i nomi dei programmi compaiano nella sezione, non che stiano dentro la frase del divieto.
20. Task 6: minor (deferred): `agents/final-reviewer.md:37` e `agents/finding-verifier.md:13` hanno due «e» di fila nell'elenco delle regole d'area (manca una virgola).
21. Task 7: minor (deferred): `test_real_flow_case_frontend_project_verifies` confronta il `tollgate.toml` di `spikes/b6/flow` con quello di `spikes/b1/flow` (accoppiamento senza ragione di prova).
22. Task 7: minor (deferred): due righe vuote in più dentro la classe in `tests/test_b1_scripts.py` (circa riga 1819).
23. Task 7: minor (deferred): `test_scrivi_limiti_heading_is_generic_backend` (Task 2, circa riga 1952) legge anch'esso i file veri senza il prefisso `test_real_`.
24. Task 9: minor (deferred): piano principale, sezione 9 (circa riga 207): il corpo della voce «Chiuso da B4 per `infra` e da B6 per `**/*.{tsx,jsx}`» dice ancora che «la forma con `*` iniziale resta rifiutata», falso da B6.
25. Task 9: minor (deferred): catalogo, sezione 2 «Percorsi predefiniti»: la frase «`init` non li copia così come sono» resta intatta, con la deroga per `ext` solo più avanti nel paragrafo (D10 chiedeva coerenza).
26. Task 9: minor (deferred): spec 16 e piano principale sezione 15 non citano il `tollgate plan-check` inesistente lanciato dal modello nel passo 1 né che il task 1 non prova il precaricamento (dipende dal giro 1 del Task 8); lo «Stato (10 novembre 2026)» in testa al piano principale non ha la data dell'11.
27. Task 9: minor (deferred): sezione 9 del piano principale, voce «A B6-B8, da B5»: due voci portano lo «Stato dopo B6» a metà o in fondo invece che in testa.
