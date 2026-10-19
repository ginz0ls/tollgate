# Ri-revisione giro 1 del Task 10 (90b2ebe..f246234)

### Verdetti sui rilievi

1. **Tipo del revisore stampato e usato dalla skill** — INDIRIZZATO. `task start` aggiunge `revisore: <routing.reviewer>` al riepilogo (taskcmd.py, fine di `_task_start`), lo stesso valore salvato in `tasks.reviewer_type` da `assign(... reviewer_type=routing.reviewer)`; `review-prepare` stampa `revisore: <row["reviewer_type"]>` (cli.py:66, taskcmd.reviewer_type, ripiego `prof.DEFAULT_REVIEWER` esistente in profiles.py:10). `_common.awaiting_review` confronta `tasks.reviewer_type = subagents.type`: il tipo lanciato è quindi quello atteso. La skill (execute, punto 4) dice di usare «quel tipo». Test: `test_profile_agent_chosen` (summary con `probe:web-reviewer`), `test_cli_review_prepare_and_done` (due righe), `test_reviewer_type_is_read_from_db`. Lacuna minore: la riga di `review-prepare` non ha un test con un profilo non predefinito.
2. **Decisione sul verdetto registrato** — INDIRIZZATO. execute punto 5: prima `task done k`, poi `--fix` se rifiuta per `changes`, poi `done` se `--fix` rifiuta per `approved`, con il perché (8.6). Rifiuti con comando giusto: taskcmd.py `_check_state` (hint `task done N`) e `task_done` (hint `task start N --fix`, solo in review con `changes`). Test: `test_done_refusal_with_changes_points_to_fix`, `test_fix_refusal_with_approved_points_to_done`, e l'ordine nel manifest (`index("task done k`:") < index("task start k --fix`, che")`).
3. **Ripresa da `status --checkpoint`** — INDIRIZZATO. Passo 0 con checkpoint e riga «prossimo passo», tabella stato → comando. Coerente con `checkpoint.next_step`: pending → `task start`; running → attendi/riprendi; blocked → resolve; approved → `task done`; changes con review_sha → `--fix`; altrimenti `review-prepare`. Ogni comando è accettato dallo stato indicato (`start` solo pending, `--fix` solo review+changes, `done` review+approved). La riga «review, preparata, senza verdetto → lancia il revisore» non è distinguibile dal checkpoint (che stampa `review-prepare` in entrambi i casi); è innocua perché `review-prepare` è rilanciabile e la tabella lo copre in parte, quindi la annoto come minore.
4. **next_step per plan e spec_audit/approval; start L1 rientrante** — INDIRIZZATO. checkpoint.py:41-47 (`plan` → writing-plans/committalo/`/tollgate:execute`; `spec_audit`/`approval` → P3c); test `test_next_step_in_phases_without_tasks`. start L1: contesto già pulito → va direttamente a writing-plans, niente secondo `/clear`, l'utente è istruito sul post-`/clear`; test del manifest sul testo.
5. **Minori** — INDIRIZZATI. Sesto `--fix`: «dopo il quinto giro non approvato, il `task start k --fix` successivo apre un blocco» (execute); radice quotata + avviso di riaggiornamento in setup; esempi JSON del revisore validi, uno per esito, con test che li parsa (`json.loads`) e verifica `{"approved","changes"}`; test del manifest sui punti 1-3. Eseguiti `tests.test_manifest tests.test_checkpoint tests.test_taskcmd`: 62 OK.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minori:
- Minor, skills/execute/SKILL.md (tabella passo 0): la riga «revisione preparata, senza verdetto» non ha un segnale nel checkpoint; chi riprende vede `review-prepare` e lo rilancia, che azzera la preparazione ma è sicuro. Nessun errore, solo ridondanza.
- Minor, tests/test_taskcmd.py: la riga `revisore:` di `review-prepare` è provata solo con il tipo predefinito.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
