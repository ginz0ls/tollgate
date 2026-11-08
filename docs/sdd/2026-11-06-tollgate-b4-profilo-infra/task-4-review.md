# Revisione Task 4 (ef3a317..bdd75d4)

### Aderenza
- ✅ Frammento `templates/profiles/infra.toml`: 14 pattern nell'ordine di D4 (con `**/compose.override.yaml` dopo `**/compose.yml`), `kind=vertical`, `min_level=L1`, `skills=[]`, `reviewer_skills=[]`, `commands={}`, `dod=[]`, agent/reviewer giusti, nessun `[detect]`, nessuna chiave `rules`/`blocking_rules`; un commento per gruppo con la pagina. `test_fragment_matches_decisions` lo asserisce (tests/test_rules_infra.py).
- ✅ Skill: frontmatter come da brief, senza `approved`, 79 righe, sezioni «Prima di scrivere», «Mentre lavori», «Dove informarsi», «Fonti». Nessun `R-INFRA-NN [blocca]` senza testo (`test_blocca_lines_have_text`). Bloccanti 01-06 e 12, tutte su diff o report; nessuna regola bloccante si regge sulla nota.
- ✅ Divisione di R-INFRA-07 (07 diff / 08 report) e rinumerazione (Docker 09-11, «non pubblicare» = 12): corretta. Le due metà hanno ciascuna un solo oggetto del giudizio (SKILL.md, R-INFRA-07/08). Date e «required» verificati sulle copie: `cf-wrangler-configuration.md` (`compatibility_date` required; wrangler.jsonc raccomandato) e `cf-compatibility-dates.md` («set to the current date», «no need to update»); la Fonte di 07 lo dice e la regola non blocca.
- ✅ R-INFRA-05 senza compose (nessuna fonte), con `env`/`build.env` di Vercel: `vercel-json.md` «We recommend against using this property». Corretto togliere l'obbligo sui compose.
- ✅ R-INFRA-06: poggia sulla pagina dei segreti Cloudflare (`.dev.vars*`, `.env*`, `.gitignore`), la riga Fonte ammette che Vercel non lo dice e che l'eccezione `.example/.sample/.template` è scelta nostra. `test_secret_rules_allow_example_files`.
- ✅ Fatti controllati sulle copie: R-INFRA-04 (`vercel-ts.md` «Use only one configuration file», `vercel-project-configuration.md` «only use one configuration file per project», `vercel.toml` citato), R-INFRA-05 (Docker ENV persiste nello strato, build arg non per segreti), R-INFRA-10 (`USER`, `.dockerignore` nella radice del context o `<Dockerfile>.dockerignore`), R-INFRA-12 (dry-run compila senza pubblicare; secret/rollback/delete/triggers deploy/versions deploy; `vercel build` scrive in `.vercel/output`; `env add`).
- ✅ Nessun obbligo senza fonte: tutti i contenuti sono nella bozza o nelle pagine. Controllo di n-grammi (5 e 6 parole) tra la skill e le 19 copie: coincidono solo gli URL. Le «» sono titoli di sezione (≤ 4 parole). Nessuna citazione.
- ✅ Test: `rules(text, area="ai")` costruisce la regex da `area.upper()`; i test di `ai` la chiamano senza area (tests/test_rules_ai.py diff). `test_real_fragments_load` legge anche `infra` (nessun detect). Tutti i test del brief presenti in `RulesInfraTest`.
- ✅ Non toccati: `skills/rules-ai`, `skills/rules-base`, `docs/profili/` (diff stat vuoto). Nessun nome utente, host o progetto privato (grep). Nessun `workers-best-practices` in «Dove informarsi».
- ✅ `docs/uso/comandi.md`: sezione `/tollgate:rules-infra` senza «solo l'utente» né «Argomenti:», dichiara la bozza non approvata.
- ✅ Evidenze: RED/GREEN descritti; suite completa verde con `python3.11` (3626) e `python3` (3626). Non rilanciata. Un tentativo di rilancio mirato dalla cartella sbagliata non vale come esito.
- ⚠️ La suite e `claude plugin validate --strict` si leggono solo dal report (log `task-4-suite.log` non riletto).

### Punti di forza
- Ogni regola ha un solo oggetto del giudizio e una Fonte con sezione; i dubbi di fonte (Vercel su `.env`, `compatibility_date` required) sono dichiarati nella Fonte stessa, non nascosti.
- Il frammento ha un commento per ogni gruppo con la pagina da cui viene il nome; `Dockerfile*` e `app.Dockerfile` sono trattati onestamente (rinvio alla pagina del Task 5).
- Correzione del test alla causa giusta (descrivere a parole le opzioni dei servizi) invece di allargare `test_skill_contract`.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor:**
1. SKILL.md, R-INFRA-05: un valore come `"SECRET": "@nome"` in `env` di Vercel è un riferimento a un segreto, non un segreto; la regola dice «nessun segreto (chiave, token, password)» quindi si giudica bene, ma conviene dirlo alla pagina del Task 5 o con mezza frase, per evitare falsi blocchi.
2. SKILL.md, R-INFRA-02: per `docker` e `docker compose` non c'è una pagina di comandi tra le fonti né in «Dove informarsi» (solo buone pratiche, segreti, compose). La regola regge sulla scelta di B 3.4, ma l'agente non ha un indirizzo dove cercare la sintassi di `docker`. Aggiungere al Task 5/6 l'indirizzo della documentazione dei comandi, se il controller ne raccoglie la copia.
3. SKILL.md, R-INFRA-01: la bozza citava anche «progetto 1»; la Fonte nomina 3.4 e 11, come chiede il test. Nessun danno.
4. SKILL.md, R-INFRA-07: «la data del giorno» si giudica sul diff solo se il revisore conosce la data del commit; accettabile perché non blocca.
5. tests/test_rules_infra.py `test_no_long_quotations`: controlla solo le «» (≤ 12 parole); è dichiarato che la verifica del testo copiato è del Task 5.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e ruling del controller rispettati, ogni regola bloccante si giudica con un sì o un no su diff o report, i fatti coincidono con le copie delle fonti senza testo copiato, e il frammento segue le decisioni 1, 5, 7, 8, 13 e D4. Restano solo rifiniture.
