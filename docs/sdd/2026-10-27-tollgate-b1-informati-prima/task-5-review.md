# Revisione Task 5 (bac69cd..e453b53)

### Aderenza
- ✅ `effects.decide` (`bin/tollgate_checks/effects.py:136-138`): per `pre_mcp` restituisce `[]` se `research.is_doc_tool(name)`, prima di `mcp_allow`; gli altri MCP seguono il percorso di oggi con «strumento MCP non in mcp_allow». Nessun altro chiamante toccato; `lookups.py:83` usa già `is_doc_tool`.
- ✅ `tests/test_check_effects.py` (`test_doc_mcp_not_an_effect`, `test_other_mcp_still_effect`) usano `mcp__plugin_context7_context7__query-docs` (carry B1-V3). Il TOML di test ha `mcp_allow = ["mcp__lettura__*"]`, quindi il primo test discrimina davvero: senza il nuovo ramo il nome sarebbe negato.
- ✅ `agents/implementer.md:4`: tools `Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch`, nessuna voce MCP, nessun `Agent` (carry B1-V2, decisione 7). `test_agents_frontmatter` aggiornato alla lettera; `test_implementer_tools` controlla WebFetch/WebSearch, assenza di `mcp__*` e di `Agent`.
- ✅ `implementer.md:19-46`: sezione «Informati prima di scrivere» dopo «Prima di cominciare» (riga 13); punti dello Step 3 presenti (file toccati e chiamanti, versioni dal file delle dipendenze, WebFetch sulla doc ufficiale, context7 solo «se ... è disponibile», consegna con `research submit` da stdin); frase sulle pagine scaricate identica a `agents/spec-auditor.md:14` (il test lo verifica confrontando i due file); L0/componente spento: nessuna nota (riga 45).
- ✅ `test_implementer_mentions_research_submit` prende le quattro sezioni e `HEREDOC_END` da `research.py`.
- ✅ `skills/setup/SKILL.md:20`: punto 4 con `permissions.allow`, `"WebFetch"`, `"WebSearch"`, «gratis», «non modificare il file: le regole le aggiunge l'utente da sé», domanda per dominio senza regole: coerente con la decisione 18. `description` aggiornata (carry D7).
- ✅ `tests/test_b1_scripts.py:442-446`: l'aggiornamento è corretto (denied False e niente «effetto esterno» in stderr) e non indebolisce il test: restano `tool_name`, la riga `read` registrata e l'assenza di `__pycache__`; il caso «MCP non di documentazione negato» è coperto da `test_other_mcp_still_effect`.
- ✅ Nessun `__pycache__` tracciato, working tree pulito.
- ⚠️ Il report dice che il 3.11 completo non è stato rilanciato dopo la correzione di `test_b1_scripts` (solo quel file, 19 OK); lo copre la suite del controller. `claude plugin validate --strict` rinviato al Task 9 per ruling.

### Punti di forza
- Modifica di `effects` minima e nel punto giusto (prima di `mcp_allow`, riuso di `research.is_doc_tool`, nessuna lista duplicata).
- Test di `effects` con configurazione che li rende significativi; test del manifest legati alle costanti di `research.py`, non a stringhe copiate.
- Testo dell'implementatore chiaro: ordine dei passi, rifiuto spiegato, caso L0.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `agents/implementer.md:29-42` duplica a mano il modello della nota di `research.submit_command` (`bin/tollgate_analysis/research.py:246-263`) e già diverge nell'ultima riga («<cosa hai capito, in poche righe>» contro «<cosa hai capito e come ne tieni conto>»). Scenario: se `research.py` cambia un'intestazione o il delimitatore, solo i titoli e `HEREDOC_END` sono coperti da test; segnaposto e ordine possono divergere senza che nulla fallisca. Correzione: allineare la riga o far verificare al test l'intero blocco contro `submit_command("<programma>", ...)` con i segnaposto normalizzati.
2. `tests/test_skill_contract.py:~131` (`test_setup_proposes_web_permissions`): la regex `lo aggiunge (?:lui|l'utente)|da sé|da lui` è larga; «da sé» basterebbe anche in una frase che dice il contrario. Correzione: ancorarla a «le aggiunge l'utente da sé» o alla negazione «Non modificare il file».
3. `skills/setup/SKILL.md:20`: il punto 4 è separato dal 3 da una riga vuota (lista spezzata in Markdown); inoffensivo, ma il resto della lista è compatto.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** i requisiti e le ruling del controller sono rispettati e verificabili dal diff; restano solo tre rifiniture minor (duplicazione del modello della nota, regex larga, riga vuota).
