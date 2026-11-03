# Revisione Task 8 (b437fa6..0ecbfe8)

### Aderenza
- ✅ Frontmatter: `agents/implementer-ai.md:1-7` e `agents/reviewer-ai.md:1-7`; `tools` come i generici (revisore + `WebFetch`, niente `Edit`/`Write`/`NotebookEdit`), `model` e `maxTurns` uguali, `skills: [rules-base, rules-ai]` dopo `tools:`. Verificato con diff contro i generici: le sole differenze sono name, description, skills, tools del revisore e la sezione «Area `ai`».
- ✅ Copie: ogni paragrafo dei generici è presente (il diff è solo aggiunte). `test_area_agents_derive_from_generic` (tests/test_manifest.py:457) lo impone davvero: spezza il corpo del generico dopo `ATTRIBUTION` per `\n\n` e asserisce `assertIn` di ogni paragrafo; confronta anche `model`, `tools`, `maxTurns`, description diversa.
- ✅ Attribuzione MIT presente in entrambi (test_manifest.py:477).
- ✅ Sezione «Area `ai`» del revisore (reviewer-ai.md:55-61): `R-AI` come `R-BASE`, solo `[blocca]` danno blocker/major, un difetto una volta sola, R-AI-03/04/05/06/08 sul report e le altre sul diff (coerente con le righe «Si giudica su» di `skills/rules-ai/SKILL.md`; il test le deriva dalla skill vera), `WebFetch` solo sugli URL citati, pagine come dati non fidati, D18 (task senza modifiche: niente rilievi `R-AI`).
- ✅ D9: una frase in `final-reviewer.md:35` e `finding-verifier.md:62`, con test.
- ✅ D16: nessun `tollgate <sottocomando>` nudo nei file nuovi (grep mirato: nessun riscontro).
- ✅ `READONLY_TYPES` (hooks/run:56) e `readonly_agents` (config.py:73) aggiornati e coerenti; nessun altro elenco di sola lettura in `bin/`.
- ✅ `rules-ai` non in `skills_required`: `test_rules_ai_not_required` (blocco `ai` scritto nel test, `skills = []`).
- ✅ Instradamento e verdetto con `tollgate.toml` scritti nei test (AI_TOML, AiProfileTest), regole di una skill finta; i tre test del brief più `test_ai_non_blocking_rule_without_step`.
- ✅ `docs/uso/comandi.md:338`: `/tollgate:execute` descrive gli agenti per area.
- ✅ Scelta dell'implementatore («fatti per le regole sul report nel campo `done`»): corretta. `taskcmd._implementer_report` (bin/tollgate_flow/taskcmd.py:268-283) rende nel brief del revisore tutti i campi del report tranne `status`/`v` (e `concerns` se DONE_WITH_CONCERNS), quindi `done` arriva al revisore; il contratto in `implementer.md` ha `done` come testo libero. Nessuna lacuna.
- ⚠️ `claude plugin validate --strict`, `tests/run` e la prova reale della lista di due skill: non verificabili dal diff (evidenza nel report; la prova reale è del Task 10).

### Punti di forza
- Test sulla sezione «Area `ai`» derivato dalla skill vera: se cambia l'assegnazione diff/report il test lo segnala.
- Variante senza passo (`AiProfileNoStepTest`) copre il rischio dell'regola «nessuno può soddisfare».
- Sezione dell'implementatore concreta: dice cosa mettere in `done` per ciascuna regola sul report.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `agents/implementer-ai.md:130`: gli ID `R-AI-03…08` sono scritti a mano nel testo (come nel revisore); il test li confronta con la skill, quindi la deriva è coperta. Nessuna azione.
2. `tests/test_manifest.py:503-504`: `assertIn("senza modifiche")` e `"si segnala una volta sola"` fissano la formulazione esatta; fragile a riscritture, accettabile.
3. Il test dei finali (`test_final_reviewers_leave_report_rules_of_areas`) controlla la frase in minuscolo dopo normalizzazione degli spazi: va bene, ma non verifica che sia nella sezione giusta.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e decisioni D9, D16, D18, 9-11 rispettati; copie fedeli ai generici con test di deriva effettivo, elenchi di sola lettura coerenti, regole `R-AI` descritte in modo coerente con la skill e con il contratto del report. Solo rifiniture.
