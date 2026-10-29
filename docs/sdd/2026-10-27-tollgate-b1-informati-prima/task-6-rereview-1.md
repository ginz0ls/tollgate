### Verdetti sui rilievi
1. **Important 1: un solo `write_atomic` in `tollgate_core`**: INDIRIZZATO. `bin/tollgate_core/fsutil.py:9-21` è identica alle due copie rimosse (stesso temporaneo `.<nome>.tmp`, `except (OSError, ValueError)`, pulizia, raise). `apply.py:11` e `research_cmd.py:14` la importano; `grep` non trova più `_write_atomic` in `bin/`. In `apply.py` i due chiamanti (`:187`, `:203`) catturano ancora `(OSError, ValueError)` e danno veto: comportamento invariato. `fsutil` importa solo `os` e `pathlib`, quindi `tests/test_layers.py` resta verde. Il test `test_write_atomic_removes_temporary_on_any_error` (`tests/test_check_audit_round.py:392`) chiama `fsutil.write_atomic` con la stessa asserzione.
2. **Minor 1: componente spento tramite `research.active`**: INDIRIZZATO. `research_cmd.py:80-82` usa `research.active(work["research"], on)` dopo il controllo `research = 0` con il suo messaggio. `test_component_off_submit_refused` lo copre.
3. **Minor 2: test per configurazione illeggibile e scrittura fallita**: INDIRIZZATO. `tests/test_research_cmd.py` ha `test_unreadable_config_refused` (patch di `config.load_config` con `ConfigError`, asserisce REFUSED, messaggio e nessuna nota) e `test_note_file_write_failure_refused` (patch di `research_cmd.write_atomic` con `OSError`, asserisce REFUSED, messaggio, nessuna nota e nessun evento). Il patch cade sul nome importato nel modulo, quindi il ramo `:106` è raggiunto davvero.
4. **Minor 4: `ResearchSubcommandTest` prima di `unittest.main()`**: INDIRIZZATO. `tests/test_check_cli_calls.py`: il blocco `__main__` è ora in fondo al file, dopo la classe.
5. **Minor 6: asserzione del testo in `test_submit_valid_note`**: NON INDIRIZZATO. `tests/test_research_cmd.py:63` è ancora `assertEqual((r.code, r.lines), (research_cmd.OK, [r.lines[0]]), r.lines)`: verifica solo che ci sia una riga, non il testo. Il diff `64cbcf9..d2c6a23` non contiene nessun hunk per questa riga e `git grep "nota di ricerca valida"` sui test a `d2c6a23` non trova nulla. Il report dichiara una correzione che non c'è.

### Danni nuovi nel diff della correzione
Nessuno. Verificato con `python3 -B -m unittest tests.test_layers tests.test_research_cmd tests.test_check_cli_calls tests.test_check_audit_round`: 88 test OK.
Minor estetico: `apply.py` (chiamata a `write_atomic` per `spec-lens-stato.md`) ha la riga di continuazione `text)` allineata a due colonne in più dopo il rinomino. Non blocca.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti: Minor 6 (`tests/test_research_cmd.py:63`).
