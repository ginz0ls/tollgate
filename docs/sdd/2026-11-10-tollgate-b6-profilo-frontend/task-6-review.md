# Revisione Task 6 (21244ff, intervallo 3b2a258..21244ff)

### Aderenza
- ✅ Frontmatter (diff di `implementer-backend`/`reviewer-backend` e dei generici): stessi campi dei generici (`model`, `maxTurns`, chiavi), cambiano solo `name`, `description`, `skills: [rules-base, rules-frontend]` e, per il revisore, `tools: Read, Grep, Glob, Bash, WebFetch` (`agents/reviewer-frontend.md:5`). Attribuzione MIT presente (riga 8 di entrambi). Corpo del generico conservato alla lettera, con in più la sola sezione «Area `frontend`» (`implementer-frontend.md:108-114`, `reviewer-frontend.md:239-245`).
- ✅ D7: `description` con la parola intera `frontend` in entrambi (riga 3 / riga 3).
- ✅ Revisore, sezione «Area `frontend`»: una sola frase con «si giudicano sul report» (`:243`, nomina 01 e 02) e una sola con «si giudicano sul diff» (nomina 03-12, esattamente le «Si giudica su: diff» della skill, verificato su `rules-frontend/SKILL.md`); presenti «WebFetch», «dati non fidati», «senza modifiche», «si segnala una volta sola».
- ✅ Implementatore: una sola occorrenza di «sul tuo report» (`:112`), con 01 e 02; il campo `done` riceve indirizzo e versione della documentazione, o la mancata dichiarazione con l'indirizzo della documentazione corrente (ramo di R-FRONTEND-01 della skill), più i componenti simili (R-FRONTEND-02).
- ✅ Divieti (`implementer-frontend.md:114`): `node`, `npm`, `npx`, `pnpm`, `yarn`, `bun`, `vite`, `next dev`, `python3 -m http.server`, browser; verifica con i test del progetto e, senza test d'interfaccia, lo dice nel report.
- ✅ `tollgate:reviewer-frontend` in `hooks/run:56` e in `config.py:77`; `implementer-frontend` no (corretto: ha Edit/Write). Nessun altro elenco di tipi o aree nel repo da aggiornare (controllato con `git grep` su `reviewer-infra`/`implementer-infra` fuori da `tests` e `docs/sdd`: restano solo i template dei profili e `comandi.md`, già a posto).
- ✅ `final-reviewer.md:37` e `finding-verifier.md:13` nominano `R-FRONTEND-…`; `docs/uso/comandi.md:32` aggiunge l'area `frontend` senza toccare altro.
- ✅ Report: RED dei test di manifest (11 casi), RED degli elenchi (`test_readonly_list_matches_config_and_agents`), GREEN dei file mirati, `plugin validate --strict` e suite su 3.11 e 3.13 con `exit 0` (`suite-task-6.log`). Evidenza completa.
- ⚠️ `suite-task-6.log` non riletto (regola: non rilanciare la suite; il report dichiara 3882 test).

### Guardie di smistamento (richiesta specifica)
- `test_frontend_task_routed_to_area_agents` (`test_taskcmd.py`): asserisce i due tipi nella riga del task e nel riepilogo. Il default sarebbe `tollgate:implementer`, quindi la guardia distingue davvero. ✅
- `test_rules_frontend_not_required`: asserisce `skills_required == []`, assenza di «rules-frontend» e della lista «Skill da usare» nel brief. Identica a quella di `backend`. Vedi Minor 2.
- `test_frontend_and_backend_task_goes_generic`: due blocchi, un task con `server/app.py` e `src/components/Button.tsx`, asserisce i tipi generici. Asserisce ciò che dice il nome. ✅
- `test_frontend_and_backend_routing_is_split_candidate` (`test_profiles.py`): asserisce generico e `split_candidate`. ✅
- `test_frontend_profile_blocking_rule_changes` / `_non_blocking_rule_approves` / `test_frontend_blocking_rule_without_step`: un `major` (da `GOOD`) su una `[blocca]` dà `changes`, su una non bloccante `approved`, anche con `research=False`. Il caso "approva" è significativo perché il rilievo è `major`. ✅ (Come per `backend`, non provano nulla di specifico di `frontend`: stesso codice dei blocchi `infra` e `backend`; sono guardie di regressione, non test di funzionalità.)
- `test_real_frontend_agent_names_forbidden_tools`: vedi Minor 3.

### Punti di forza
- Derivazione fedele: il test di deriva (`test_area_agents_derive_from_generic`) copre ora anche le due copie, e il diff con i generici conferma che l'unica differenza è la sezione d'area.
- Le liste di regole nelle frasi coincidono con la skill approvata (01 e 02 sul report; 03-12 sul diff).
- Il rosso intermedio del test degli elenchi è stato visto e documentato, come chiedeva il brief.

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor**
1. `agents/implementer-frontend.md:114` contro `:119-121` (imposto dal piano, da decidere al controller). Il divieto di `node`, `npm`, `npx`, `pnpm`, `yarn`, `bun` vale per ogni utente del plugin, non solo per la prova reale. In un progetto JavaScript i test dell'interfaccia (`vitest`, `jest`, `npm test`) passano per quei programmi: l'implementatore non potrebbe fare il RED/GREEN mirato del passo 4 e del report, ma solo `<programma> verify`. La frase "Verifichi con i test del progetto" è quindi vera solo per progetti con test non basati su `node` (Python, come la prova). Il brief lo impone alla lettera e le cautele lo giustificano per la sessione di B6, quindi non è un difetto del task. Se si vuole attenuare: limitare il divieto a installazioni, server di sviluppo e browser, e lasciare i test del progetto al comando di `verify`. Da riportare come costo nella revisione finale.
2. `tests/test_taskcmd.py` (`test_rules_frontend_not_required`): il blocco ha `skills = []`, quindi `skills_required == []` è vero a prescindere; l'asserzione utile è solo l'assenza di «rules-frontend» nel brief. È lo stesso schema di `test_rules_backend_not_required`, coerente col codebase; nessuna correzione richiesta.
3. `tests/test_manifest.py` (`test_real_frontend_agent_names_forbidden_tools`): `assertIn(word, section)` controlla la presenza delle parole come sottostringhe (per esempio «node», «bun»), non che siano dentro il divieto. Una riscrittura che le nominasse come permesse passerebbe. Basterebbe asserire la frase `Non lanci …` fino al punto, o cercare i nomi dentro quella frase. Stesso livello di rigore del test di `infra`.
4. `agents/final-reviewer.md:37` e `agents/finding-verifier.md:13`: l'elenco ha ora due «e» di fila («…che `rules-backend` e le `R-FRONTEND-…` che `rules-frontend` segnano…») dopo «le `R-INFRA-…` che `rules-infra` e le `R-BACKEND-…`». Si legge, ma una virgola prima dell'ultima voce lo chiarirebbe. Il test cerca solo la frase fissa e `r-frontend-`, quindi la modifica è sicura.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** i due agenti sono copie fedeli dei generici con la sola sezione d'area richiesta, i vincoli di `carry.md` e di D7/D11 sono tutti soddisfatti, gli elenchi sono aggiornati e le guardie asseriscono ciò che dicono i nomi. Restano quattro minori, il più rilevante (divieto di `node` e gestori di pacchetti per tutti gli utenti) è imposto dal brief.
