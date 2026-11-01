# Report del giro di correzione della revisione finale di B2

Commit: 03a0a2e (I-1, I-2, codice e test), il commit dei minori (test, rapporto delle fonti, docstring, implementer), il commit dei documenti (spec rev 28, piano principale). Vedi `git log`.

## I-1: R-BASE `[blocca]` bloccanti solo con il passo attivo
- Cambiato: `lookups.base_rules(root, active)` (`bin/tollgate_core/lookups.py`): le `[blocca]` bloccano solo con `active` e interruttore acceso; le note restano sempre note. Chiamanti: `task_verdict.py` e `apply._final_rules` con `research.active(work["research"], ctx.component("research_note"))`. Una sola funzione per la condizione.
- Test: `tests/test_check_task_verdict.py` (`Base.research`, `BaseRulesTest` con `research = True`, `BaseRulesNoStepTest`, `BaseRulesComponentOffTest`), `tests/test_check_final_review.py` (stesso schema). `test_rejected_report_leaves_trace` ha ora `component` nel contesto finto (serve a `_final_rules`).
- RED: `python3 -B -m unittest tests.test_check_task_verdict tests.test_check_final_review`: 2 fallimenti per file (`'changes' != 'approved'`, `1 != 0`) nelle classi senza passo e con componente spento. GREEN: 37 e 34 test OK.
- Documenti: spec 8.6 e piano principale sezione 3 («solo nei lavori con il passo»).

## I-2: report dell'implementatore nel brief del revisore (strada a)
- `ReviewBrief.implementer_report` e sezione «Report dell'implementatore» in `review_brief` (`brief.py`): frase sulle regole sul report, `DATA_NOTE`, poi `_block`. `taskcmd._implementer_report` rende in chiaro i campi del report (senza `concerns`, che ha la sua sezione e il cui test esistente `test_done_report_without_concerns_adds_none` richiede che non compaia con `DONE`); se il report non si legge, la coda del testo registrato (tetto `report.MAX_SCAN_CHARS`). Sempre quando c'è un report.
- Agenti: `task-reviewer.md` (report nel brief, in un recinto, dato per le regole sul report), `final-reviewer.md` e `finding-verifier.md` (R-BASE solo sul diff; regole su nota e report del revisore del task; frase condizionata di D6 mantenuta).
- Test: `tests/test_brief.py::ReviewReportTest`, `tests/test_taskcmd.py` (`test_report_reaches_review_brief_even_when_done`, `test_no_report_no_report_section`), `tests/test_manifest.py::test_reviewers_know_where_report_and_note_rules_are_judged`. RED dei primi due: `AssertionError` per la sezione assente (e `TypeError` sul campo non esistente). Gli agenti: solo la correzione, più il test (verde).

## Minori
3. `test_unreadable_switch_warns_and_logs_once`: `assertLess` sull'ordine, `assertNotIn("non si legge")` alla seconda modifica (già verde: guardia, non RED).
4. `tests/test_rules_base.py`: `test_page_approval_date_matches_skill`, `test_base_rules_of_research_match_rules` (guardie, verdi).
5. `docs/profili/verifiche/base-fonti.md`: riga 3 cita 3c4697a (il commit con cui la R-BASE-10 attuale, verificata il 2026-11-01, è entrata nella skill); la riga `no` di systematic-debugging esce dalla tabella e sta sotto come «Fonte scartata». `test_sources_report_covers_every_rule` invariato e verde.
6. Spec del nucleo: 6.3 (paragrafo `rules-base` dopo `SubagentStop` e «Una skill non installata…»), 16/18.4 (`research_switch_unreadable` in «Tipi:»; `tests/test_docs.py::test_spec_event_types_match_registry`, RED verificato sulla spec di HEAD: manca `research_switch_unreadable`), `rules_switch`/`rules_enforced` (spec 8.1, piano sezione 3, docstring in `lookups.py`), frasi su I-1 e I-2, «bozza n. 11».
7. Piano principale: sezione 3 (`no`, `off` e `n`, confronto dopo gli apici; grammatica «si precarica»; `base_rules(root, active)`), sezione 10 («I primi due», prove nuove, «bozza n. 11»), rinvii a B3: rinvio 37 di B1 (letture con glob) e una nota sul giudicare le regole su ciò che il revisore vede. Gli altri minori «rinviabili a B3» erano già annotati.
8. Docstring di `research_gate.py`: interruttore illeggibile ed evento `research_switch_unreadable`.
9. `agents/implementer.md` punto 1: leggere comunque i file che si modificano se le regole di base non sono nel contesto. `test_manifest` verde.

## Verifica
- Test mirati: tutti i file toccati verdi (test_check_task_verdict, test_check_final_review, test_brief, test_taskcmd, test_manifest, test_rules_base, test_docs, test_check_research_gate, test_check_agents, test_lookups).
- `claude plugin validate --strict .`: uscita 0 («Validation passed»; un avviso preesistente sul README).
- Suite completa: vedi la riga finale in fondo a questo report.

## Scostamenti e dubbi
- Prima corsa della suite lanciata per errore con `&` dentro il comando (contro le cautele): fermata subito, per PID dei miei soli processi, e rilanciata con `run_in_background`; nessun risultato di quella corsa è stato usato.
- Il «commit della seconda verifica» in `base-fonti.md`: ho citato 3c4697a (la skill con la R-BASE-10 attuale entra lì); se si intendeva un altro commit, è una riga.
- Il brief nomina gli id R-BASE-05, 07, 10, 11 nel testo della sezione del report: sono stabili dopo l'approvazione, ma se l'elenco cambia va aggiornato anche lì.
- La prova reale va ripetuta dopo questo giro (ruling del controller): non fatta qui (vietata).

## Esito della suite completa
Comando: `PYTHONWARNINGS=error::ResourceWarning tests/run` (background, una sola corsa valida, lanciata dopo il commit 7c8deb4: copre tutti e tre i commit). python3.11.16: 3238 test, OK (skipped=2), 1443 s. python3 3.13.5: 3238 test, OK, 1434 s. Uscita 0, nessun «unclosed database» né ResourceWarning. `claude plugin validate --strict .`: uscita 0.

## Ultimo giro (documenti)
Commit «rinvii a B3 dal secondo verdetto della revisione finale»: spec 8.6 (frase finale sulle R-BASE) e tre rinvii a B3 nel piano principale. Solo documenti; `tests.test_docs` verde; `tests/run` non rilanciato (lo fa il controller).
