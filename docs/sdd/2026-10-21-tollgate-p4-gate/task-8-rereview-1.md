# Ri-revisione Task 8, giro 1

### Verdetti sui rilievi
- **I-1 `shared_sha_prs` non filtra `head.sha == sha`**: INDIRIZZATO. `bin/tollgate_gate/github.py:185` aggiunge `(pr.get("head") or {}).get("sha") == sha`. `test_stacked_pr_does_not_make_sha_shared` (`tests/test_gate_guard.py:290`) con PR impilata A/B dà `success`. `test_shared_sha_is_error` (due PR con la stessa testa) dà ancora `error`. Unico chiamante: `guard.py:112`.
- **I-2 commento del guard rosso intitolato «in attesa»**: INDIRIZZATO. `comment.py:130` e docstring `comment.py:139` dicono «tollgate/guard: rosso». Test `test_guard_comment_says_red_not_waiting` e `test_red_comment_says_red_not_waiting`. Lo stato resta `failure`.
- **M ricontrollo della testa**: INDIRIZZATO. `guard.py:106-109` confronta `FETCH_HEAD` con `head` subito dopo il fetch, prima di ogni chiamata GitHub: se diverso, esce 0 senza stato né commento. `test_pr_advanced_since_the_event_writes_nothing` verifica `calls() == []` e nessun commento (percorso con sha dell'evento presente nel repo, quindi non è lo stale-head).
- **M WAIVERS**: INDIRIZZATO. `protected.WAIVER_FILES` (`protected.py:10`), usato da `REPO_PROTECTED` (stessi elementi e stesso ordine, comportamento invariato) e da `guard.py:31`. Nessun altro uso di `WAIVERS` nel repo.
- **M test spostamento / nomi ostili**: INDIRIZZATO. `test_tollgate_file_moved_is_red`, `test_hostile_file_names_stay_inert`.
- **M docstring ghcli entro 100 colonne**: INDIRIZZATO (`ghcli.py:117-120`).

### Verifiche richieste
- Test del token: `fake` chiama il vero `fetch_ref` senza token (`real(repo, ref)`): fetch verso l'origin nudo locale del banco, niente rete. Il token resta solo nel dict `seen`; l'asserzione sugli argomenti di `gh` resta.
- PR impilate e stessa testa: vedi I-1.
- `WAIVER_FILES`: nessun cambio di comportamento.
- Eseguiti `python3 -B -m unittest tests.test_gate_guard tests.test_gate_comment`: 69 test OK.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- Nessun test unitario diretto di `github.shared_sha_prs` (coperta via `guard`): non blocca.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
