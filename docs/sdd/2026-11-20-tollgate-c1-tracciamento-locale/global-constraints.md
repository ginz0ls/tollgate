## Global Constraints

- **Codice e test.**
  - Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11.
  - Ogni task chiude con `tests/run` verde (`python3.11` e `python3`). Verifica finale come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`, senza «unclosed».
  - **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate fuori da sé; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`; il gate non importa i moduli nuovi.
  - Nessun modello di linguaggio nel codice (progetto 14): la presa della taglia sono regole.
- **Niente GitHub.** C1 non scrive né legge niente di nuovo su GitHub. Il testo delle ruling, delle domande e delle risposte resta nello stato locale (progetto 6, «Tutto locale»).
- **Cosa non cambia.**
  - La busta degli eventi resta alla versione 1: i tipi nuovi e i campi nuovi in `data` non la cambiano (spec 18.4).
  - Profili e regole approvati non si toccano: `skills/rules-*/SKILL.md`, `templates/profiles/*.toml`, `docs/profili/**`, `agents/*.md`.
  - Il gate (`tollgate_gate`) non cambia.
  - Un hook su `AskUserQuestion` non nega mai, nemmeno quando fallisce: il controllo delle fermate non sta in `CONTROL_EVENTS`, e il wrapper e `runner` non trattano quel `PreToolUse` come un controllo (decisione 4).
- **Prova reale** (Task 9): solo il controller, con `spikes/run-b1-flow.sh`, senza GitHub vero; circa 1-2 USD equivalenti sull'abbonamento, nessun addebito.
- **Cartelle temporanee dei test.** Ogni `mkdtemp` si chiude con `addCleanup`. Una cartella creata in `/tmp` ha un prefisso che comincia con `tollgate`. Nessuna asserzione che, se fallisce, stampi `os.environ`.
- **Il repo è pubblico.** Nei test e nei documenti niente nomi di progetti privati, nome utente, host, token. Nei test i nomi delle macchine sono finti (`macchina-prova`).
- **Stile.** Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.
