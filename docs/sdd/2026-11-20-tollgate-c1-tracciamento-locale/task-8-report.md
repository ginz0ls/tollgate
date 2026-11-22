# Report Task 8: la fotografia per il gestionale

## Implementato
- `bin/tollgate_analysis/turn.py`: `TurnFacts`, `waiting_on`, `USER_PHASES`.
- `bin/tollgate_core/snapshot.py`: `SNAPSHOT_VERSION = 1`, `build`, `waiting_items` (blocchi, effetti, domande in quest'ordine), `dumps`. Solo SELECT; nessun testo libero.
- `bin/tollgate_core/cli.py`: sottocomando `snapshot`; il ramo senza DB sta accanto a quello di `status`, prima di `db.open_db`, e non crea niente (D15). `import socket`.
- `docs/uso/gestionale.md` (nuova) e voce di `snapshot` in `docs/uso/comandi.md`; `tests/test_docs.py` riceve `gestionale`.
- Test: `tests/test_turn.py`, `tests/test_snapshot.py` (shape, costo per agente, domande che scadono, nessun testo libero controllato sulle chiavi, lavoro pre-C1, chiusi, pr_open, CLI senza DB), `tests/test_cli.py::test_snapshot_cli_process`.

## TDD
RED: `python3 -B -m unittest tests.test_turn tests.test_snapshot` -> `ImportError: cannot import name 'snapshot' from 'tollgate_core'` (errors=2).
GREEN: stesso comando, 17 test OK (un errore iniziale era nel mio test: un L1 parte da `plan`, corretto). Poi `tests.test_docs tests.test_turn tests.test_snapshot tests.test_layers tests.test_cli`: 73 OK.

## Misura
Da copie in `mkdtemp(prefix="tollgate-")` di tre stati di `eval-b8` (prima, centrale, ultima), cartella cancellata: 11, 26, 46 eventi = 83 eventi, 27787 byte JSONL, 334,8 byte/evento. Nella pagina anche la misura dello scan su tutte e 88 (1002 eventi, 334672 byte, 334/evento), con la provenienza. Nel repo nessun `-wal`/`-shm`.

## Scostamenti e note
- Una domanda conta come «ultima della sua sessione» su tutti gli eventi `stop_asked` della sessione (anche senza lavoro); una `stop_answered` chiude per `tool_use_id` su tutto il DB.
- La pagina non contiene percorsi locali; `by_task` ha chiavi intere in Python, stringhe nel JSON.
- Nessun test di `by_task` su `reopen plan` (documentato come limite).

## Suite
`suite-task-8.log` (esito in coda al commit).

Suite: python3.11 4329 OK (skipped 13), python3 (3.13) 4329 OK (skipped 11), exit 0, nessun unclosed.
