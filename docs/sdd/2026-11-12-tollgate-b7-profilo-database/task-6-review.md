# Revisione Task 6 (B7), pacchetto b2e773c..356ad9d

### Aderenza
- ✅ `agents/implementer-database.md` e `reviewer-database.md` derivano dai generici. Rispetto a `implementer-frontend` e `reviewer-frontend` cambia solo la sezione d'area (diff controllato). `skills: [rules-base, rules-database]`, `AREAS` con `database`. Il test di deriva copre tutti i paragrafi del generico.
- ✅ `final-database.md` (agents/final-database.md:1-65) ha gli stessi `tools` di `final-reviewer` (`Read, Grep, Glob, Bash`) e `model: inherit`. Ha `skills: [rules-base, rules-database]` e `FINAL_ATTRIBUTION`. La sua riga «regole di un'area che si giudicano sul report» è identica a quella di `final-reviewer` (diff 71 contro 110). Il caso `final` di `test_area_agents_derive_from_generic` (tests/test_manifest.py) taglia su `FINAL_ATTRIBUTION`, confronta i `tools`, le chiavi del frontmatter e `model`. Regge.
- ✅ Sezione d'area di `final-database` (righe 61-65): nomina 03, 05, 07-14 in una sola frase «si giudicano sul diff». Corrisponde alle righe «Si giudica su: diff» di `skills/rules-database/SKILL.md` (01, 02, 04, 06, 15, 16 sono report). Non nomina id di regole sul report, lascia quelle al revisore del task e cita la lista di controllo. `test_area_agents_name_area_rules` lo verifica con insiemi esatti, quindi non è una sola `assertIn`.
- ✅ Sezione dell'implementatore (agents/implementer-database.md:200-206): vieta `supabase`, `psql`, `docker`, `prisma`, `drizzle-kit` e `npx/npm/pnpm/yarn/bunx/bun`. Manda le prove a `<programma> verify` e `dod`. `implementer-frontend.md` non è nel diff, quindi il suo divieto resta com'è. `test_real_database_agent_names_forbidden_tools` controlla le parole.
- ✅ Elenchi di sola lettura: `hooks/run` e `config.py` hanno `reviewer-database` e `final-database`. `test_readonly_list_matches_config_and_agents` confronta wrapper, config e agenti senza Edit/Write, quindi copre i due agenti senza modifiche a `tests/test_wrapper.py` (scostamento dichiarato, giustificato).
- ✅ Virgole e `R-DATABASE-` in `final-reviewer.md:~27` e `finding-verifier.md:~136`: ora «`rules-backend`, le `R-FRONTEND-…` che `rules-frontend` e le `R-DATABASE-…` che `rules-database`». La virgola dopo `rules-backend` c'è e sono le uniche modifiche ai due file. `test_final_reviewers_leave_report_rules_of_areas` si estende da solo a `AREAS`.
- ✅ `test_real_database_specialist_in_l2` (tests/test_finalreview.py:~101): usa il frammento vero proposto da `init.profile_blocks` con i tre agenti veri copiati, una migrazione committata e L2. Asserisce `reviewers` = `[final-reviewer, final-database]`, il brief `final-1-database.md`, la sezione «Lista di controllo dell'area» e il testo vero della `checklist` (coincide con `templates/profiles/database.toml:48`). La prova è reale, perché il test passa solo se `final-database.md` esiste (`_agent_exists`). `test_real_database_specialist_not_in_l1` usa lo stesso lab in L1: coppia con controllo positivo, quindi vale.
- ✅ `init` propone `final_specialist` solo se l'agente esiste: `test_real_database_proposes_final_specialist` (tests/test_init.py) prima senza `final-database.md` (chiave assente e riga di avviso con `final-database.md`), poi con il file (chiave presente, `checklist` non vuota). Il codice `_agent_exists` (init.py:310) non è toccato.
- ✅ File approvati: `skills/rules-database`, `templates/`, `docs/profili/` non sono nel diff. Nessun altro file approvato toccato, `rules-backend`, `rules-frontend` e simili compresi.
- ✅ `docs/uso/comandi.md`: `execute` e `finish` aggiornati, coerenti con gli agenti.
- ✅ I test di `taskcmd` (routing e due aree uguale generico) e di `check_task_verdict` (solo `[blocca]` fermano, anche senza passo) seguono i pattern di `frontend`.
- ⚠️ Non verificabile dal pacchetto: la suite completa (4034 test, due interpreti) è affermazione del report. Non rilanciata, come da istruzioni. Nessun test mirato era necessario.

### Punti di forza
- Deriva tenuta da un test strutturale (paragrafi, chiavi del frontmatter, `tools`, `model`) anche per lo specialista.
- Test d'area per `final-database` con insiemi di id esatti e una sola frase per categoria, senza dipendere dal testo letterale.
- Test di instradamento con il frammento vero e un controllo positivo e uno negativo (L2/L1) sullo stesso lab. `FinalCase.lab(extra=)` è una modifica minima e retrocompatibile.
- Scostamenti e assenza di dubbi dichiarati onestamente nel report.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `docs/uso/comandi.md` (`/tollgate:finish`, riga ~37): «oggi `database`, con `tollgate:final-database`» invecchia al prossimo specialista. Meglio nominare l'area come esempio senza «oggi». Rifinitura.
2. tests/test_init.py (`DatabaseAgentsProposeTest`): il nome dice «real» ma le skill sono finte approvate di `_real_fragments_root`. I frammenti e gli agenti sono quelli veri, quindi l'intento è chiaro e la docstring lo dice. Nessuna azione necessaria.
3. `final-database.md` e `reviewer-database.md` ripetono nella sezione d'area l'elenco degli id. È voluto e vincolato dal test di allineamento con la skill (decisione 9), quindi non è duplicazione da correggere.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** I tre agenti rispettano le decisioni 10, 11 e 17, derivano dai generici con un test di deriva che regge. Lo specialista parte in L2 e non in L1, riceve la `checklist`, è di sola lettura ed è negli elenchi. Nessun file approvato è toccato. Restano solo rifiniture.
