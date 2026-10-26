# Ri-revisione Task 6, giro di correzione 1 (e1a9e97..fe5d070)

### Verdetti sui rilievi
- **Important 1: chiusura del ciclo, evento, fase e blocchi nella stessa transazione, idempotenza, test di atomicità.** INDIRIZZATO.
  `reviews.py` `close_cycle`: `_cycle`, UPDATE, `record_event` e `_consequences` stanno tutti nel solo `with db.tx(conn)`; `_consequences` usa `phases.set_phase_in_tx` e `open_block_in_tx`, senza transazioni proprie (`db.tx` e `record_event` si uniscono comunque a quella aperta, `db.py:192-195`). Le copie (`db.backup`) sono dopo il commit, nell'ordine di prima (execution, poi blocked). La seconda chiusura rientra dal ramo `stage == 'closed'` e torna l'esito senza toccare nulla. `test_close_is_atomic_with_phase_and_blocks` inietta l'errore in `phases._change_phase` e verifica ciclo ancora `verify`/outcome None/counted 0, fase `review`, nessun evento in più, nessuna transazione aperta, e che la ripetizione chiude e porta a `execution`. `test_close_leaves_a_db_copy_per_phase_change` copre la copia. Il recupero non serve più: il difetto (ciclo chiuso senza conseguenze) non può più esistere. Docstring aggiornato.
- **Minor 1: `openpr` con `data["task"]`/`data["skills"]` di forma sbagliata.** INDIRIZZATO.
  `openpr.py` `_skills_absent`: controllo `task` intero e `skills` elenco con `DbError` che nomina `events.data`; `_size_reasons` ignora un `size_reason` non stringa. Tre casi nuovi (`{}`, task stringa, skills stringa) più `subagent_stop` `[1]` in `OpenCorruptTest`; il report dichiara il RED (KeyError, `0 != 1`). Residuo trascurabile: `True` passa come intero.
- **Minor 2: `events.known_commits` con `json.loads` nudo.** INDIRIZZATO.
  `events.py:45` ora `load_json(..., "events.data", dict)`; `test_known_commits_corrupt_data_is_dberror` (RED dichiarato: JSONDecodeError).

### Danni nuovi nel diff della correzione
Nessuno. Verifiche:
- `set_phase_in_tx` e `open_block_in_tx` sono lo stesso corpo delle pubbliche spostato; `_change_phase` registra l'evento `phase_change`, `block_opened` e `block_closed` e `level_change` restano nel corpo; le pubbliche mantengono guardia `in_transaction`, `db.tx` e la copia dopo il commit (`fase-{to}`, `fase-blocked` solo se la fase è cambiata). Gli effetti (eventi, UPDATE, copie) sono gli stessi. Nell'indentazione l'`if cause == "l0_grew"` resta al livello di prima.
- Copie del DB solo dopo il commit, mai dentro la transazione. Un solo `BEGIN IMMEDIATE`, nessun lucchetto annidato né transazione aperta due volte.
- Il vincolo `ValueError` sul tipo di blocco è ora in `open_block_in_tx`, prima di qualsiasi scrittura.

### Osservazioni fuori ambito
- Restano i minori 3, 4, 5 della revisione (sottostringa nel brief, `kind=None`, `_saved` silenzioso): non toccati, non bloccanti.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
