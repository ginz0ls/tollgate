# Task 10: report

Solo documenti. Nessun codice toccato, `docs/verifiche/` non toccato.

## Spec del nucleo, revisione 36 (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`)
- **Intestazione**: riga «Revisione: **36**» con la prova reale (0,93 USD equivalenti), le decisioni 1-12 e le ruling.
- **3.1**: due righe nuove in tabella, `snapshot` e `ruling add` (campi, limiti, uscite); la frase di `cli_calls` ora nega ai subagenti `ruling add --by user` (D4; la decisione 5 diceva «`cli_calls` non cambia»); `snapshot` è «sola lettura dei dati», il primo avvio dopo un aggiornamento può migrare con copia in `backup/` (D7).
- **3.2**: elenco chiuso degli eventi d'ingresso con `pre_question` e `post_question`, fuori da `CONTROL_EVENTS`.
- **6.1**: nuovo paragrafo «La taglia del lavoro»: `worksize.propose`, soglie 4 task / 2 aree, quando gira `sizes.decide`, `preview` e le forme della riga, mai giù, `large` solo con `approve spec <n>`, atto dell'utente, D12.
- **7.1**: eccezione al punto 6: `PreToolUse` di `AskUserQuestion` non è un controllo (wrapper `CONTROL=no`, `runner._asks_user`).
- **7.2**: `SessionStart` registra `session_start`; due righe nuove per `AskUserQuestion` (`stop_asked`, `stop_answered`, D16); `SubagentStop` registra `cost`.
- **8.4**: target `size`; riga `approve size`; `approve spec` scrive anche `slices` e taglia prima del cambio di fase, `approve plan` decide la taglia dopo `register_plan` (D10, D19); elenco degli atti applicabili.
- **11.4**: esempio `[retention]` con `events_days = 0` e `lookups_days = 180`; paragrafo con archivio, `archive_and_prune` come sola potatura (D21), limiti 0-36500 con `ConfigError` (D5).
- **12.2**: colonne `size`, `size_by`, `slices`; vincolo di `events`; le letture dei `lookups` si potano con `lookups_days`; nuova «Migrazione 7».
- **18.4**: `data` dei cinque tipi nuovi (`size_decided`, `ruling`, `stop_asked`, `stop_answered`, `cost`), `cost` cumulativo per agente, nessun `cost` senza uso (D3), `tokens` senza `cache_read` (D21), decisioni sui rilievi nell'evento `finding`. La riga `**Tipi:**` non è toccata (l'ha fatta il Task 1).
- **20**: riga 36 con le dodici decisioni, le ruling che cambiano la spec (D3, D4, D5, D7, D10, D19, D12, D16, D20, D21) e i limiti scritti (forma di `tool_response` da provare in C6; domanda in attesa; `reopen plan` e `by_task`; sessione principale fuori dal costo).

## Progetto e piano principale di C
- Progetto (`...-c-tracciamento-design.md`): riga «Avanzamento» (C1 eseguita sul ramo, in attesa del merge; rapporto della prova).
- Piano principale (`...-c-piano-principale.md`): riga «Stato» in testa; riga C1 della sezione 2 con «**Stato:** eseguita sul ramo `c1-tracciamento-locale`, in attesa del merge» (mai «unita»); sezione 3 con i nomi reali (`Signals`, `Proposal`, `preview`, `sizes.decide`, `set_by_user`, `snapshot.build`, `archive_and_prune`, `events_days` a 0); riferimento alla spec «36 dopo C1»; sezione 8: una riga che dice che il triage dei minori di C1 arriva con la revisione finale (nessun minore elencato).

## Controllo della tabella «Copertura» del piano C1
`grep -n "def <nome>" tests/*` per tutti i 41 nomi. 38 esistono come scritti. Corretti con una nota sotto la tabella:
- `test_adopt_decides_size` → `test_adopt_decides_size_at_start` (`tests/test_adopt.py:509`), più i tre test sulle fette (`:526`, `:533`, `:543`).
- `test_events_days_default_is_never` → `test_minimal_gets_defaults` (`tests/test_config.py:16`) e `test_housekeeping_never_prunes_with_zero` (`tests/test_start.py:1249`).
- `test_approve_finding_emits_finding_event` sta in `tests/test_actapply.py:412` (non `tests/test_reviews.py`); `test_user_decision_written_only_by_set_decision` è in `tests/test_reviews.py:426`.

## Verifiche
- `python3 -B -m unittest tests.test_docs`: 7 test OK (prima della suite).
- Suite `PYTHONWARNINGS=error::ResourceWarning tests/run`: Python 3.11.16 4334 test OK (13 saltati), Python 3.13.5 4334 test OK (11 saltati), `exit 0` (`suite-task-10.log`).
