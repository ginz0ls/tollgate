# Ri-revisione giro 5 — Task 16 (c178f03)

### Verdetti sul ruling
**retry=True solo su set_status e PATCH di commento esistente** — INDIRIZZATO. `grep retry=True bin`: solo `github.py` in `set_status` (POST `statuses/<sha>`) e nel PATCH di `upsert_comment`; `comment_issue` (anche via `upsert_comment` per un commento nuovo) e `create_issue` restano senza.
**Un solo punto di decisione** — INDIRIZZATO. `ghcli._run_retrying(..., idempotent=)`; `api(retry=)` lo passa; `run_json*` invariati; GET ritentate a prescindere.
**Errore finale e condizioni invariati** — INDIRIZZATO. Stesse condizioni transitorie, 3 tentativi, attese (2, 4); un 4xx con `retry=True` non ritenta; errore finale testato («gh api --method: gh: Server Error (HTTP 500)», testo di sempre).
**Test richiesti** — INDIRIZZATI: `test_write_declared_idempotent_is_retried`, `test_retry_true_keeps_4xx_final`, `test_set_status_retries_transient_500`, `test_new_comment_and_issue_are_not_retried`, `test_upsert_patch_is_retried_but_new_comment_post_is_not`, `test_transient_500_on_guard_status_post_is_retried`. Estensione `api_flaky` con chiave `"<METODO> <percorso>"` minima e documentata. `tests.test_ghcli tests.test_gate_guard` eseguiti con -B: OK.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
