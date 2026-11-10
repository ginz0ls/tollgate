### Task 8: Prova reale: esecuzione e rapporto (controller)

**Files:**
- Create: `docs/verifiche/2026-11-09-b5-prova-flusso.md`, `docs/verifiche/evidenze/b5/flusso/`

- [ ] **Step 1 (controller): esecuzione.** `B1_FLOW_CASE=backend B1_FLOW_RULES=vere`: `prepara`, `passo1`, `passo2`, `registra`, solo sotto `/tmp/tollgate-b1/`. Atteso: `init` propone `backend` con `/server/**` e `edge/index.ts`, niente sotto `supabase/`; task 1 `done` con verdetto `approved`; `agent_type` `tollgate:implementer-backend`, `reviewer_type` `tollgate:reviewer-backend`; il titolo di `rules-backend` nelle trascrizioni di entrambi; nota valida prima della prima modifica; `comandi-rischiosi.txt` vuoto. Si annota se il modello ha scritto il piano già nel passo 1 (lezione di B4) e, in quel caso, se il piano elenca le righe del report che le regole chiedono. Un esito in più tentativi è «composito»; al più 3 tentativi per passo. Un difetto del prodotto scoperto qui è un giro del task che possiede il codice (test che fallisce, correzione, `tests/run`), poi si ripete solo il passo interessato.
- [ ] **Step 2: Evidenze e rapporto.** `flowreg togli-pagine` sulle evidenze; poi, **prima di scrivere il rapporto**, la verifica a mano: `grep` dei risultati di `Read`, `Grep` e `Bash` che toccano `tool-results/` (per un `Bash` sia il blocco sia `tool_use_result.stdout`) e di ogni testo di pagine o skill di terzi rimasto sotto il tetto del test (lezione I-1 di B4), più il controllo di nome utente, host, `/home/<utente>`, id di sessione e forme di token. Rapporto, con in testa la riga `Esito: riuscita`, `Esito: riuscita (composita)` oppure `Esito: non riuscita: <motivo>`: passi, tentativi, proposta di `init` (percorsi, file trovati per contenuto, esclusione di `supabase/`), agenti lanciati, precaricamento visto e come lo si distingue dal piano scritto dal modello (decisione 14), letture, nota, verdetto e rilievi `R-BACKEND-…`, consumo stimato, limiti.
- [ ] **Step 3: Verifica e commit.** `python3 -B -m unittest tests.test_b1_scripts` (compreso `test_committed_evidence_has_no_long_web_results`): PASS. Commit «tollgate B5: prova reale corta con il profilo backend».

---

