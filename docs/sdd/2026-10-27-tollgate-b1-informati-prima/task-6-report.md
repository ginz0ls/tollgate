# Task 6 report: comando `research`

Stato: DONE_WITH_CONCERNS. Commit: vedi `git log -1` sul ramo b1-informati-prima ("tollgate B1: comando research per la nota di ricerca").

## Implementato
- `bin/tollgate_flow/research_cmd.py`: `submit`, `show`, `note_path` (D17), `SubmitResult`, codici OK 0 / INVALID 1 / REFUSED 2. Rifiuti: nessun lavoro, L0, fase diversa da execution, `research = 0` («lavoro iniziato prima del passo informati prima»), componente spento via `config.load_config(...).get("components.research_note")` («componente research_note spento»; configurazione illeggibile = REFUSED), task inesistente o non `running`. Nota salvata sempre (anche non valida) in `tasks.research_note/research_ok` e nel file con riga finale `esito: valida|non valida`; evento `research_note` {task, ok, problems}. Le letture sono `lookups.for_task` (tutte quelle del task, qualunque agent_id).
- `bin/tollgate_core/cli.py`: sottocomando `research submit K` (stdin) e `research show K`; niente `--file` (B1-V5). Uscita su stdout se OK (e per `show` anche INVALID), altrimenti stderr.
- `bin/tollgate_checks/cli_calls.py`: nega alla sessione principale (senza agent_id) in L1/L2 solo `research submit` («la nota la scrive l'implementatore del task», rule `research_main_session`), anche con programma incerto e nel ripiego testuale (parole `research`, `submit` e `tollgate`). `show` ammesso; L0 ammesso. Livello da `_common.governing_work`.

## Test
- `tests/test_research_cmd.py` (15), `tests/test_check_cli_calls.py::ResearchSubcommandTest` (8, incluso `test_heredoc_research_passes_bash_rules` con hooks/run vero, nota con backtick, `$(...)` e riga `EOF`, e esecuzione reale con `bash -c`: la nota arriva intera in `tasks.research_note`), `tests/test_cli.py::ResearchCliTest` (2).
- RED osservato per i test di `cli_calls` (7 fallimenti prima della regola). Per `research_cmd` i test e il modulo sono stati scritti in sequenza e il RED non è stato osservato separatamente (ImportError implicito).
- GREEN: `tests/run` intero, python3.11: 3055 test OK (skipped=2); python3 (3.13.5): 3055 OK. `test_layers` verde.

## Scostamenti / dubbi
- Il controllo lavoro/research/worktree duplicato in `runner._record_lookup` e `lookup_rec.decide` NON riusabile qui: vive in `tollgate_hooks`/`tollgate_checks`, che `tollgate_flow` non può importare (FLOW_FORBIDDEN); inoltre qui servono messaggi di rifiuto distinti. Non ho aggiunto una terza copia di quel controllo, ma `research_cmd` ha il proprio ordine di rifiuti. Una futura estrazione in `tollgate_core` (es. `sessions`/`lookups`) toglierebbe la duplicazione.
- Per lo stesso vincolo di strato `_write_atomic` è copiato (stesso schema di `apply._write_atomic`) in `research_cmd`: seconda copia, da unificare in core se si vuole.
- `submit` salva il testo intero in DB anche se supera 8.000 caratteri (la nota è dichiarata non valida da `parse_note`); nessun taglio.

## Giro 1
- Important 1: nuovo `bin/tollgate_core/fsutil.py` con `write_atomic`; `apply.py` e `research_cmd.py` la usano, le due copie sono tolte (tolto anche `import os` inutile in `apply.py`). Il test `test_write_atomic_removes_temporary_on_any_error` ora chiama `fsutil.write_atomic` (stessa asserzione).
- Minor 1: `submit` rifiuta con «componente research_note spento» tramite `research.active(work["research"], on)` (il controllo `research = 0` resta prima, con il suo messaggio).
- Minor 2: test `test_unreadable_config_refused` e `test_note_file_write_failure_refused` (nessuna nota in DB, nessun evento).
- Minor 4: `ResearchSubcommandTest` spostata prima del blocco `__main__`.
- Minor 6: `test_submit_valid_note` asserisce il testo del messaggio.
- Minor 3 e 5 rinviate, non toccate.
- Test: `tests/run` intero, python3.11 3057 OK (2 skipped), python3 3.13.5 3057 OK.
