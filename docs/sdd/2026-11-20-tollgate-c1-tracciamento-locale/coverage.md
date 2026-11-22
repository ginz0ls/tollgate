## Copertura: punti del progetto destinati a C1 → task

| Punto del progetto (e del piano principale) | Task | Prova |
|---|---|---|
| 2 Obiettivo 1, 6: gli eventi nuovi escono da `tollgate events` | 1 | `test_new_event_types_recorded` |
| 2 Obiettivo 4, 3.1, 3.2 «Chi decide» (proposta e riga, piccolo e medio senza aspettare) | 3 | `test_start_new_work_has_size_line`, `test_plan_registration_decides_size` |
| 3.2 «Quando diventa grande, e qual è il sì» (`approve spec <n>` con n > 1; `size_decided` all'avvio e ad `approve spec`) | 4 | `test_approve_spec_records_slices_and_large` |
| 3.2 «Segnali» (fette, task, aree, L2; soglie con test) | 3 | `test_medium_thresholds`, `test_large_with_slices`, `test_areas_counts_verticals_only` |
| 3.2 «Crescita» (il livello sale, il piano aggiunge fette; grande solo con un sì; mai giù da sola) | 3 | `test_never_goes_down`, `test_large_needs_a_yes`, `test_level_rise_raises_size`, `test_l1_plan_with_three_slices_stays_medium`, `test_plan_after_reopen_does_not_shrink` |
| 3.2 «Scelta dell'utente» (l'atto fissa la taglia) | 3, 4 | `test_approve_size_act`, `test_user_size_is_fixed` |
| 8 «La macchina che l'ha avviato o adottato» (un lavoro adottato ha taglia e fette) | 3 | `test_adopt_decides_size` |
| 3.3 La presa: punto unico, segnali in ingresso, taglia e motivo in uscita, ogni proposta e correzione registrata | 3 | `test_reason_names_the_signals`, `test_decide_records_event_and_sets_size` |
| 6 `size_decided` | 3, 4 | come sopra |
| 6 `ruling` e «Come si registrano le ruling» (comando sul modello di `research submit`, quattro campi, la skill e il brief lo citano) | 5 | `test_parse_text`, `test_add_records_event`, `test_subagent_may_add_ruling`, `test_implementer_brief_mentions_ruling` |
| 6 `stop_asked`, `stop_answered` (con la risposta, anche rifiutata) | 6, 8 | `test_stop_asked_recorded`, `test_stop_answered_from_tool_response`, `test_stop_answered_on_failure`, `test_unanswered_question_expires` |
| 6 `cost` e «Dove sta il costo» (token per ogni subagente; dollari solo negli eval, nel loro registro) | 7 | `test_cost_event_on_finish`, `test_transcript_usage_by_model`, `test_reviewers_pass_usage` |
| 6 Decisioni sui rilievi come evento (accettato, declassato, archiviato), con confidenza e verifica | 7 | `test_approve_finding_emits_finding_event`, `test_user_decision_written_only_by_set_decision`; «accettato» = evento `finding` confermato senza `user_decision` (decisione 6) |
| 6 `sync` | rinviato a C4 (decisione 10; piano principale, decisione 2) | — |
| 6 «Tutto locale» | 5, 6, 8 | nessuna scrittura su GitHub nei task; `test_snapshot_has_no_free_text` |
| 6 «La storia non si cancella» («mai» per difetto, archivio JSONL, spazio misurato) | 2, 8 | `test_events_days_default_is_never`, `test_archive_then_prune`, `test_archive_write_failure_deletes_nothing`; pagina d'uso |
| 10 Fotografia con versione, sola lettura, documentata in `docs/uso/` | 8 | `test_snapshot_shape`, `test_cli_snapshot_without_db`; `docs/uso/gestionale.md` |
| 4.3 «A chi tocca» (il calcolo locale; la scheda è di C4) | 8 | `test_decision_wins`, `test_user_phases`, `test_agent_otherwise` |
| 2 Anti-obiettivo «una cosa piccola con la cerimonia di una grande» | 3 | `test_small_by_default` (un lavoro piccolo non chiede niente all'utente) |
| 13 Test senza rete | tutti | nessun test nuovo usa `gh` |
| 14 Vincoli (stdlib, strati, suite, niente modelli, profili intatti, repo pubblico) | tutti | `tests/test_layers.py`; suite tre volte; revisione finale |
| Piano principale, decisione 6: prova reale corta | 9 | rapporto `docs/verifiche/2026-11-20-c1-prova-flusso.md` |
| Spec del nucleo: revisione 36 | 1 (riga `**Tipi:**`), 10 | `test_spec_event_types_match_registry` |
