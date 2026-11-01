# Revisione Task 5 (1a0b6d9..3c4697a)

### Aderenza
- ✅ Regola 10 rimessa: `skills/rules-base/SKILL.md:42-43` identica al testo verificato in `task-5-fonti.md` e a `carry.md:26`, con la sola fonte `ok` (verification-before-completion, «Key Patterns»); la fonte `no` (systematic-debugging) non compare nella skill, solo nel rapporto.
- ✅ Vecchia 10 diventata R-BASE-11 senza altri cambi (`SKILL.md:45-46`). 11 regole, id consecutivi 01-11 (verificato con grep su skill, tabella pagina `base.md:36-46`, rapporto `base-fonti.md:21-23`).
- ✅ «Blocca?» uguale a `[blocca]`: la 10 è «sì» in pagina e `[blocca]` in skill; la 11 «no». `test_page_blocca_matches_skill` passa.
- ✅ `approved: 2026-11-01` (`SKILL.md:5`) dopo `version`, forma AAAA-MM-GG; unica occorrenza nel repo fuori da docs/sdd e test (grep).
- ✅ Frase «bozza» sostituita in «Fonti» (`SKILL.md:50`) e in `docs/uso/comandi.md:~152` (carry righe 23-24). Nessun'altra occorrenza di «bozza» in skills/agents/docs/uso.
- ✅ Pagina: «Approvata dall'utente il 2026-11-01.» (`base.md:5`), «undici regole», testo al presente («approvate e bloccano»), contenuto coerente con la decisione 10 (L1/L2 rifiuto, L0 avviso, anche nei lavori in corso, da quando la versione unita arriva al plugin installato; `test_page_explains_what_changes` lo fissa). Parole semplici, nessun gergo nuovo. Sezione tolte: bozza 10 rimessa, 11 resta tolta, coerente con carry.
- ✅ Rapporto fonti: due righe nuove (no e ok) con le citazioni di `task-5-fonti.md`, riga R-BASE-11, sezione tolte senza id `R-BASE-` (richiesto da `test_sources_report_covers_every_rule`). La riga `no` non rompe il test perché il test chiede almeno un `ok` per regola.
- ✅ D9: nessuna `--opzione`, sigla P+cifra o nome di comando nel nuovo testo della skill. D8: `validate --strict` uscita 0 con data senza apici, riportata nel report (non rieseguita: ⚠️ solo dal report). D16: non rosso.
- ✅ Test: `test_frontmatter` invertito, `test_real_rules_base_is_approved`, `RealRulesBaseTest` L1/L2. Rieseguito `python3 -B -m unittest tests.test_rules_base tests.test_check_research_gate`: 52 OK.
- ✅ Asserzione di `test_real_rules_base_blocks_l1/l2` (`tests/test_check_research_gate.py:360-377`): exit 2 più `REFUSAL + " 1"` in stderr. Il testo «nota di ricerca mancante o non valida per il task» esiste una sola volta in `bin/` (`bin/tollgate_checks/research_gate.py:113`), quindi identifica il modulo che nega quanto `rule == research_gate`; lo scostamento dal piano è giustificato e innocuo. I test usano `plugin_root=ROOT` (skill vera), quindi provano davvero la regola vera e non una copia.
- ✅ Nessun test dipende in silenzio dall'interruttore acceso: i test pre-esistenti usano `make_root(...)`; solo i due nuovi leggono il repo vero, e dichiarano di volerlo (docstring). La suite completa (3189 OK su 3.11 e 3.13) è dal report: ⚠️ non rieseguita.

### Punti di forza
Diff chirurgico, testi della regola e delle fonti identici a quelli verificati, report onesto sullo scostamento (campo `rule`), rapporto e pagina aggiornati insieme.

### Rilievi
- Critical: nessuno.
- Important: nessuno.
- Minor 1 (`tests/test_rules_base.py:48-54`): nessun test fissa che la riga «Approvata dall'utente il …» della pagina esista e coincida con `approved` della skill; la divergenza fra data in pagina e data in skill passerebbe. Aggiungere un'asserzione che estrae la data dalla pagina e la confronta.
- Minor 2 (`docs/profili/base.md:50-54`): «Nella bozza erano dodici. Due non hanno passato il controllo ... sono state tolte» è storicamente vero ma convive con il primo punto che dice che una è stata rimessa; per chi legge è un po' contorto. Opzionale: «Due erano state tolte; una è rientrata».
- Minor 3 (`docs/profili/verifiche/base-fonti.md:3`): «Skill verificata ... al commit b17cbf0» è la prima verifica; la nuova verifica (R-BASE-10) è dichiarata in riga 5, ma l'intestazione non dice che la skill attuale è diversa. Trascurabile.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** i requisiti di brief e carry sono tutti soddisfatti, skill, pagina e rapporto coincidono, l'accensione è provata da test che colpiscono la regola vera, e lo scostamento sull'asserzione `rule` è equivalente; restano solo rifiniture.
