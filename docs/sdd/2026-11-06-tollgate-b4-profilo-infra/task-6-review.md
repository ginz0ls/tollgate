# Revisione Task 6 (67bb9e1..8fd55e0)

### Aderenza
- ✅ `approved: 2026-11-07` dopo `version` (skills/rules-infra/SKILL.md:5); unica riga cambiata nella skill: regole, «Blocca?», «Si giudica su» invariati.
- ✅ «Approvata dall'utente il 2026-11-07.» in docs/profili/infra.md:5.
- ✅ «Cosa hai deciso»: sette punti, ognuno «tenuto» come proposto (1 resta, 2 estesa a Docker, 3 senza compose, 4 eccezioni .example/.sample/.template, 5 workflow e azioni escluse, 6 `prompts/` senza più `ai` e `txt` tra i documenti, 7 «li imposta l'utente»). Nulla aggiunto o cambiato nel contenuto.
- ✅ Nessun «Da decidere tu» né «va confermato» residuo in pagina, skill, rapporto (grep). infra-fonti.md rimanda a «Cosa hai deciso».
- ✅ docs/uso/comandi.md: sezione `/tollgate:rules-infra` con la data 2026-11-07; non contiene «solo l'utente» né «Argomenti:» (le occorrenze altrove sono di altri comandi / intestazione generale).
- ✅ Nessun file di `ai` o `base` toccato (stat del diff).
- ✅ `test_frontmatter` invertito; `test_page_approval_date_matches_skill` già presente e ora attivo (non più skippato); `test_real_infra_fragment_approved` aggiunto; `test_page_records_the_choices` in più (utile).
- ✅ Nessun test indebolito: `test_page_choices_count_matches_list` riadattato alla nuova sezione, con la stessa asserzione sul conteggio; i due test «proposta» si saltano a skill approvata, come nel modello di `ai`.
- ❌ Manca `test_approved_skill_leaves_no_pending_decisions` in tests/test_rules_infra.py (richiesto dal brief, Step 2; esiste per `ai` in tests/test_rules_ai.py:381). Il report non ne parla. Il contenuto oggi è corretto (grep pulito) ma nulla lo protegge.
- ⚠️ Esiti della suite (3644 OK, validate 0) dal report, non rieseguiti.

### Punti di forza
Cambio chirurgico, testo della pagina coerente con le scelte, riga delle fonti riallineata, introduzione e coda della pagina adeguate (i numeri non cambiano più).

### Rilievi
- **Important** — tests/test_rules_infra.py (classe RulesInfraPageTest, dopo riga ~415): aggiungere `test_approved_skill_leaves_no_pending_decisions` sul modello di tests/test_rules_ai.py:381-391, per PAGE e SOURCES: nessun «Da decidere tu», nessun `[Vv]a confermat[ao] dall'utente`; skip se la skill non è approvata. Requisito esplicito del brief.
- **Minor** — tests/test_rules_infra.py:~391: `test_page_is_a_proposal` e `test_page_brings_the_open_choices_to_the_user` restano come test sempre saltati (stesso schema di `ai`, accettabile).

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** Contenuto e approvazione corretti e fedeli alla risposta dell'utente, ma manca uno dei quattro test richiesti dal brief (`test_approved_skill_leaves_no_pending_decisions`).
