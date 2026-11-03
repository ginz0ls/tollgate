# Revisione Task 7 (dfc4835..f2a78b7)

### Aderenza
- ✅ `approved: 2026-11-02` senza apici dopo `version` (skills/rules-ai/SKILL.md:4); unica modifica alla skill, nessuna regola cambia testo o numero.
- ✅ `rules-base` non toccato (nessun file in diff).
- ✅ Pagina: riga «Approvata dall'utente il 2026-11-02.» (docs/profili/ai.md:5), testo al presente, «Da decidere tu» diventata «Cosa hai deciso» al passato. Le 4 decisioni coincidono con carry.md (R-AI-06 resta con l'indirizzo; R-AI-11 resta; lettura di «stabile» approvata; `from "openai"` resta fuori) senza aggiunte. Nella tabella cambiano solo i rimandi «Vedi «Cosa hai deciso»» (righe 6 e 11); il testo delle regole è identico.
- ✅ Test: `test_frontmatter` invertito (test_rules_ai.py:94-95), `test_page_approval_date_matches_skill` (regex ancorata, assert sulla lista: fallisce se la riga manca o è doppia), `test_real_ai_fragment_approved`. I due test di pagina saltano con motivo esplicito; `test_real_trees_light_no_profile` è attivo (non tra gli skip), i test di init non cambiano.
- ✅ docs/uso/comandi.md aggiornato (non era in elenco Files del brief, ma era una frase «bozza» ora falsa: correzione dovuta e coerente con la riga di rules-base).
- ⚠️ Non rilanciati i test (regola del ruolo); evidenza del report: 3363 OK su 3.11 e 3.13, validate --strict 0, `task-7-suite.out` non letto da me. Gli skip su 3.11 (4 contro 2) non indagati dall'implementatore: non dipendono dal diff, da controllare in revisione finale.

### Punti di forza
- Diff minimo e mirato; il test della data confronta pagina e skill, non una costante.
- Resoconto fedele alla decisione, senza aggiunte di merito.

### Rilievi
**Important**
- docs/profili/verifiche/ai-fonti.md:62: rimanda alla sezione «Da decidere tu» della pagina, che ora non esiste più (rinominata «Cosa hai deciso»), e dice «Va confermato dall'utente», ormai superato. Riferimento rotto nella coerenza pagina/rapporto fonti. Correzione: una riga, es. «L'utente l'ha confermato il 2026-11-02 (pagina `docs/profili/ai.md`, sezione «Cosa hai deciso»)». Nessun test lo intercetta (grep "Da decidere" in tests: nessun riferimento ad ai-fonti).

**Minor**
- docs/profili/ai.md:~72: la sezione «Come rispondere» è stata rinominata «Se vuoi cambiare qualcosa»: non richiesto, ma innocuo e coerente col tempo presente.
- Le docstring dei due test saltati dicono «col Task 7 ... si chiude»: ora sono codice morto in pratica (restano utili solo se `approved` sparisse); accettabile come in B2.

### Valutazione
**Qualità del task:** Da correggere (lieve)
**Motivo:** Implementazione fedele alla decisione dell'utente, regole intatte e test sensati; resta un riferimento rotto in `ai-fonti.md:62` verso la sezione rinominata, da sistemare con una riga prima di chiudere.
