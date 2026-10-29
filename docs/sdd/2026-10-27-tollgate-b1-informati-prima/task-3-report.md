# Report Task 3: analisi pure (nota di ricerca, percorsi, URL, letture Bash)

## Implementato
- `bin/tollgate_analysis/research.py` (nuovo): `RULES_BASE`, `SECTION_*`, `MAX_NOTE_CHARS`, `HEREDOC_END`, `FILE_KINDS`/`URL_KIND`/`DOCS_KIND`, `ATTRIBUTE_UNNAMED_TOOLS = frozenset()`, `DOC_MCP_TOOLS`, `active`, `enforced`, `is_doc_tool`, `doc_library` (`libraryId` poi `context7CompatibleLibraryID`), `normalize_url`, `normalize_path`, `Source`, `Note`, `parse_note`, `check_note`, `submit_command`. Niente `APPROVAL_FILE` (B1-V7).
- `bin/tollgate_analysis/bash.py`: `read_targets(c)` con tabelle di opzioni con argomento per comando (D13).
- `tests/test_research.py` (30 test), `tests/test_bash.py::ReadTargetsTest` (4 test, 30 casi in subTest).

## TDD
- RED: `PYTHONPATH=bin python3 -B -m unittest tests.test_research tests.test_bash` prima del codice: `AttributeError: module 'tollgate_analysis.bash' has no attribute 'read_targets'`, `Ran 68 tests ... FAILED (errors=33)` (test_research falliva in import).
- GREEN: stessi file dopo il codice: `Ran 97 tests ... OK`; con `test_analysis_isolation` e `test_layers`: `Ran 106 tests ... OK`.
- Suite: `tests/run` background, python3.11: `Ran 2967 tests in 1381s OK (skipped=2)`; python3 (3.13.5): `Ran 2967 tests in 1371s OK`.

## Scelte e scostamenti dal piano
- `Source.ref`: per `context7` è il solo libraryId (senza prefisso `context7:`), per `url` l'URL come scritto (normalizzato in `check_note`). `lookups` di tipo `docs` hanno il libraryId come target.
- `Note.no_external`: `None` sezione assente, `""` presente senza motivo. Il controllo «motivo vuoto» sta in `check_note` (come dice il test del brief); i problemi di forma (sezioni mancanti o vuote, fonti non riconosciute, doppia sezione, lunghezza) sono in `parse_note.problems`, e `check_note` li riporta in testa, più i suoi (file/fonti non letti).
- `normalize_path`: `None` anche per percorso vuoto e per la radice del worktree stessa (non è un file). `~` rifiutato solo a inizio percorso. `normalize_url` toglie anche le credenziali (`user@`).
- `submit_command`: modello con le quattro intestazioni (Letto, Documentazione, Nessuna fonte esterna, Cosa ho trovato) e segnaposto `<...>`; il modello non compilato produce problemi in `parse_note` (testato). Nessun `TOLLGATE_`.
- `read_targets`, oltre al brief: `grep`/`rg` con `-l -L -c -q` (e lunghe equivalenti, `rg --files`) restituiscono `[]` perché non mostrano il contenuto (stessa logica della decisione 4 per Grep `files_with_matches`/`count`); `-` e le opzioni `+X` di `less` ignorate; `sed` senza `-n` o con `-i` → `[]`; `sed -f` non conta il file di script come lettura.
- **Reindirizzamento `<`**: NON arriva in `Cmd.redirects` (`bash.py` `flush()`: `_REDIR_SKIP` scarta `<` e il suo bersaglio; `redirects` contiene solo le uscite `>`, `>>`...). Quindi `read_targets` non li conta, e non usa `redirects` (conterebbe le uscite come letture: `cat < f > out` → `[]`). Parser non toccato; test `test_read_targets_stdin_redirect_not_in_redirects` fissa il comportamento. Se serve `cat < f`, va esteso il parser (decisione del controller).

## Autorevisione
Brief e carry.md coperti (D1, D2, B1-V2, B1-V7, D13); `tollgate_analysis` non importa tollgate (isolation/layers verdi); nessun `__pycache__` nel commit.

## Dubbi
- `read_targets` è best effort: `grep -r foo src` restituisce la cartella `src`, che non coincide con un `Read` di file (il confronto con le letture lo farà il chiamante).
- `less` ha molte opzioni con argomento: ne ho incluse le principali.

## Fix round 1
Modifiche:
1. `parse_note`: oltre `MAX_NOTE_CHARS` ritorna subito con il solo problema di lunghezza. Separatore senza regex (`str.find` di « — »/« - », lineare); anche l'intestazione `## ` senza regex.
2. `bash.py`: `--color`/`--colour` tolte dalle opzioni con argomento (`grep --color foo f` → `["f"]`).
3. `enforced`: `null`, `~`, `|`, `>`, `|-`, `>-`, `false`, virgolette vuote → non approvato.
4. «Letto nel progetto»: solo « — » separa la descrizione (`docs/A - B.md` intatto); « - » resta valido nelle fonti di «Documentazione».
Test nuovi: `test_enforced_not_a_real_value`, `test_parse_note_too_long_not_analyzed` (100.000 spazi, < 0.5 s), `test_parse_note_long_line_under_cap_is_fast` (< 0.5 s), `test_parse_note_file_with_dash_in_name`, casi `grep --color` in `test_read_targets`.
RED (nuovi test contro il codice del commit c4fb8dd, in una copia temporanea): `PYTHONPATH=bin python3 -B -m unittest tests.test_research tests.test_bash` → FAIL su enforced (null, ~, |, >, |-, false), file con trattino, riga lunga in Documentazione, nota troppo lunga, `grep --color`.
GREEN: stessi file, `Ran 101 tests OK`. `tests/run` in background: python3.11 `Ran 2971 tests in 1391s OK (skipped=2)`; python3 3.13.5 `Ran 2971 tests in 1375s OK`.
