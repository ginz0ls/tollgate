# Ri-revisione giro 1 del Task 8

### Verdetti sui rilievi
1. **Sblocco dei task atomico** — INDIRIZZATO. `tasks.unblock_all` (tasks.py, nuova funzione dopo `task_event`) apre `db.tx`, legge i `blocked` e chiama `task_event` per ciascuno; `db.tx` si unisce alla transazione già aperta (db.py:146-148), quindi tutti o nessuno. `_resolve` (actapply.py) la chiama subito dopo `close_block`, che resta fuori da transazione, solo se la fase esce da `blocked`. Test `UnblockAllTest.test_failure_midway_leaves_no_mixed_state` (`_log` che fallisce al secondo task): stati tornano `["blocked","pending","blocked"]` (originali) e `in_transaction` falso; il rollback è reale perché l'UPDATE del primo task è annullato.
2. **Id di resolve solo cifre ASCII** — INDIRIZZATO. actapply.py: `re.fullmatch(r"[0-9]+", act["target"])` al posto di `isdigit()`; `²` non raggiunge `int()`. Test `test_resolve_refuses_non_ascii_digits`: `ActApplyError` «non è un blocco aperto», atto `consumed`, fase `blocked`.
3. **`output_excludes` unico (Minor)** — INDIRIZZATO. `config.output_excludes` (config.py:276-278) = `output_dirs + [".tollgate-run/"]`, identico alla vecchia espressione; usato in verify.py:~157 e taskcmd.py:~207.

### Danni nuovi nel diff della correzione
Nessuno. Nota non bloccante: `unblock_all` annidata in una transazione esterna dipende dal chiamante per il rollback, comportamento standard di `db.tx`.

### Osservazioni fuori ambito
Restano i due Minor non toccati della revisione precedente (atto consumato per errori di sola forma; `cap_paths` fuori dalla transazione di `set_level_cap`), già classificati come non bloccanti.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
