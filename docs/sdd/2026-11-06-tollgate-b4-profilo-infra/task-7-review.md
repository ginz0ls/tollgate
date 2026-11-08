# Revisione Task 7 (8fd55e0..6b35ada)

### Aderenza
- ✅ Frontmatter: `agents/implementer-infra.md:1-7` e `agents/reviewer-infra.md:1-7` differiscono dagli `-ai` solo in `name`, `description` (contiene «infra»), `skills: [rules-base, rules-infra]`; `tools` del revisore `Read, Grep, Glob, Bash, WebFetch`, `model`/`maxTurns` come i generici. Verificato con `diff` contro `-ai` e contro i generici: nessun'altra divergenza oltre alla sezione «Area `infra`».
- ✅ Attribuzione MIT presente in entrambi (riga 9).
- ✅ Insieme di id: la sezione del revisore nomina 01-12 (report: 01, 02, 03, 08, 12; diff: 04, 05, 06, 07, 09, 10, 11), uguale alla skill (`skills/rules-infra/SKILL.md`: «Si giudica su: report» solo su 01, 02, 03, 08, 12). Le frasi «si giudicano sul report» / «sul diff» e «sul tuo report» (implementatore) coincidono.
- ✅ R-INFRA-12 trattata come «non pubblicare» (implementer-infra.md:53, in `done` il motivo/prova). Comandi non coperti nominati: `wrangler kv`, `d1`, `r2`, `docker build`/`docker buildx build` con «l'opzione push» (a parole, senza `--`).
- ✅ `tollgate:reviewer-infra` in `hooks/run:56` e `config.py:77`; `test_readonly_list_matches_config_and_agents` (invariato) lo copre.
- ✅ final-reviewer e finding-verifier: esempio con `R-INFRA-…`; `docs/uso/comandi.md:32` aggiornato, senza trappole di testo.
- ✅ Nessuna modifica a `skills/rules-ai`, `skills/rules-base`, `docs/profili/*` (stat del diff).
- ✅ Test d'area: `tests/test_manifest.py` `test_area_agents_name_area_rules` usa regex `R-<AREA>-\d\d`, niente `b[:7]`; confronta insiemi esatti per ogni area, quindi fallirebbe se un id mancasse o ne comparisse uno in più (e il revisore deve avere l'insieme completo `== ids`). Test di B3 non indeboliti: deriva, preload, attribuzione e final-reviewers ora girano su `AREAS`; i due `assertIn` di frasi esatte restano.
- ✅ Test di instradamento e verdetto (taskcmd, profiles, check_task_verdict) come da brief, con skill finta nel `tollgate.toml` di test.
- ⚠️ Non verificabile dal diff: l'esito delle suite (3653 test, `claude plugin validate --strict`) è dichiarato nel report, non rilanciato.

### Punti di forza
- Derivazione fedele: i paragrafi dei generici sono intatti; unica aggiunta la sezione d'area.
- Test d'area generalizzato davvero (non regge solo su `ai`): prefisso, skill e sezione derivati dall'area.
- La sezione dell'implementatore distingue effetti coperti da tollgate e comandi non coperti, come chiesto dalle voci D3/D13.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `tests/test_manifest.py` (test d'area): nessuna asserzione fissa che l'implementatore nomini `wrangler kv`/`d1`/`r2` e le build Docker con push (requisito di carry D3/D13). Il testo c'è (`agents/implementer-infra.md:53`) ma una regressione non sarebbe vista. Aggiungere `assertIn` mirati per `implementer-infra`.
2. `agents/implementer-infra.md:53`: «la sua configurazione elenca» è approssimativo (l'elenco degli effetti sta in parte nei default del codice); inoltre non dice che anche la prova di R-INFRA-12 (`wrangler deploy` in dry-run, `vercel build`) è un comando di servizio che tollgate ferma finché l'utente non approva. Il rimando «quella che le regole indicano» lo copre, ma una mezza frase lo renderebbe esplicito.
3. Report: il rosso di `test_readonly_list_matches_config_and_agents` non è stato osservato (agenti ed elenchi scritti insieme), dichiarato onestamente; il brief lo prevedeva (Step 2). Nessun effetto sul risultato.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** gli agenti derivano dai generici senza divergenze fuori da frontmatter e sezione d'area, gli id e le frasi report/diff coincidono con la skill, gli elenchi di sola lettura sono aggiornati e i test d'area sono davvero generali; restano solo rifiniture minori.
