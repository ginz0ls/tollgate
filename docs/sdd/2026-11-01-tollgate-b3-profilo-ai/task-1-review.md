### Aderenza
- ✅ D12 (`bin/tollgate_flow/taskcmd.py` `_implementer_report`/`_render`): `None` -> `null` (anche negli elenchi); `concerns` saltato se vuoto o di soli spazi; escluso solo con `DONE_WITH_CONCERNS` (sezione dei dubbi propria); mostrato con `DONE` se non vuoto; altri campi invariati. Test: `tests/test_taskcmd.py` (4 test in `ReviewDoneTest`, D19 rispettata).
- ✅ D13 (`bin/tollgate_analysis/brief.py`, `review_brief`): frase quando `not (research and research_enforced)`; tre combinazioni in `tests/test_brief.py` `ReviewBaseRulesTest`.
- ✅ Rinvio 184 e 186 in `agents/implementer.md` (sezione «Informati prima di scrivere» e punto `tests`), test in `tests/test_manifest.py` con asserzioni sulla sezione giusta.
- ✅ `agents/task-reviewer.md` riga 53: indicazione per il revisore, coerente con la frase del brief; test extra.
- ✅ Test vecchio `test_done_report_without_concerns_adds_none` sostituito, motivo scritto nel report.
- ⚠️ Esito di `tests/run` (due interpreti, avvisi come errori) non verificabile dal diff: si fida del report (`task-1-suite.out`).

### Punti di forza
- Modifica chirurgica; `_render` piccolo, riusato per elenchi; i test asseriscono il comportamento reale (sezione del report isolata, `assertNotIn("None")`, conteggio unico del dubbio con `DONE_WITH_CONCERNS`).

### Rilievi
- Critical: nessuno. Important: nessuno.
- Minor: `taskcmd.py` `_implementer_report`: un `concerns` non stringa (es. lista vuota `[]`) viene reso via `str(...)`; `[]` darebbe stringa vuota e verrebbe saltato, ma `["a"]` passerebbe il controllo e sarebbe reso correttamente: nessun difetto reale, solo da sapere.
- Minor: la frase del brief aggiunge un inciso sul passo «informati prima» non richiesto; innocuo, ma il Task 8 copierà nei generici solo la frase del piano.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** D12, D13, D19 e i rinvii 184-187 sono implementati e testati sul comportamento reale, senza scostamenti né difetti rilevanti.
