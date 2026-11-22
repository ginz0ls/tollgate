# Report Task 5: comando `ruling add`

Stato: DONE. Commit: vedi `git log -1` (oggetto: "tollgate C1: comando ruling add per le decisioni prese al posto dell'utente").

## Implementato
- `bin/tollgate_flow/ruling_cmd.py`: `parse_text`, `add`, `command`, `RulingResult`, `OK, REFUSED = 0, 2`, `RULING_TEXT_MAX = 1000`, `HEREDOC_END`, `BY`. Etichette senza distinzione di maiuscole (D20); altre righe continuano il campo aperto; campi su più righe uniti con uno spazio; campo vuoto, mancante, ripetuto o testo prima del primo campo sono problemi. Evento `ruling` con `data = {what, why, cost, by, task}` e `work`. Messaggi senza il programma nudo (D17).
- `bin/tollgate_core/cli.py`: sottocomando `ruling add [--task K] [--by agent|user]`, stdin limitato a `4*3*RULING_TEXT_MAX+1`, righe su stdout con 0 e su stderr con 2.
- `bin/tollgate_analysis/brief.py`: `ImplBrief.ruling_cmd` e una riga nel brief con il heredoc e l'avviso su `TOLLGATE_…=`; `taskcmd.py` lo riempie con `ruling_cmd.command(program_command(db.BIN_PATH), number)` (sempre, non dipende dal passo di ricerca).
- `bin/tollgate_checks/cli_calls.py` (D4): un subagente non può `ruling add --by user` (anche `--by=user`, `--b user`); `--by agent` o senza `--by` passano; la sessione principale può tutto.
- `skills/execute/SKILL.md`: un paragrafo per il coordinatore dopo il punto 6; `docs/uso/comandi.md`: voce nella sezione CLI.

## Test
Nuovo `tests/test_ruling_cmd.py` (11) e aggiunte in `test_cli` (RulingCliTest), `test_check_cli_calls` (RulingCallsTest, con D11: programma di `program_command(PROGRAM)`, corpo con apostrofi, `$`, backtick, `task`, `review`, `start`; controllo negativo `task start 1` negato al subagente), `test_brief`, `test_taskcmd`.
- Mirati: 174 test OK (poi `test_check_cli_calls` 32 OK dopo una correzione di un'asserzione tautologica).
- Suite completa: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> `exit 0`; Python 3.11.16: 4266 test OK (13 skipped); Python 3.13.5: 4266 test OK (11 skipped). Log: `suite-task-5.log`. File nuovi aggiunti con `git add` prima della suite (lezione del Task 3).

## Evidenza TDD
Scostamento: ho scritto il codice prima dei test, quindi non ho un RED registrato. I test sono stati poi scritti sui comportamenti del brief e lanciati verdi.

## Scostamenti dal piano
- Toccato anche `bin/tollgate_checks/cli_calls.py` (D4, richiesto dal controller).
- `--by user` negato anche in forma abbreviata (`--b`), perché argparse accetta i prefissi.

## Dubbi
Nessuno bloccante. Il comando non limita fase o livello del lavoro (il brief non lo chiedeva).

## Fix round 1
- **I1** (`ruling_cmd.parse_text`): un testo di più righe prima del primo campo dava `KeyError('')` (CLI: traceback, uscita 1). Ora un flag `leading` segnala il problema una sola volta e `current` resta `None`: rifiuto con uscita 2.
  - RED (prima della correzione): `python3 -B -m unittest tests.test_ruling_cmd tests.test_check_cli_calls tests.test_cli.RulingCliTest` -> `FAILED (failures=1, errors=1)`: `KeyError: ''` in `test_missing_repeated_or_leading_text_are_problems` (caso `"intro\naltra riga\ncosa: a..."`) e `AssertionError: (1, '') != (2, '')` in `test_cli_ruling_multiline_text_before_the_first_field`.
  - GREEN: stesso comando con `tests.test_cli` intero -> `Ran 84 tests ... OK`.
- **M1** (`tests/test_check_cli_calls.py`): il controllo negativo (`test_same_body_with_task_start_is_denied_to_a_subagent`) usa lo stesso heredoc e corpo con testa `<programma> task start 1 <<'RULING_FINE'`, verifica uscita 2, `rule == "coordinator_only"` (dagli eventi `veto`) e il testo «comando del coordinatore». Passava già: è un controllo rafforzato, senza RED.
- Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> `exit 0`; Python 3.11.16: 4285 test OK (13 skipped); Python 3.13.5: 4285 test OK (11 skipped). Log: `suite-task-5-fix1.log`.
