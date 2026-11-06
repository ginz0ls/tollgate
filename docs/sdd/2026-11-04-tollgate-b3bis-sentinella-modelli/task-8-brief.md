### Task 8: Revisione 30 della spec, progetto, piano principale

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`

- [ ] **Step 1: Revisione 30 della spec del nucleo.** 3 (albero: `templates/models.toml`); 3.1 (riga di `models check`); 3.2 (la rete della sentinella sta nella CLI, mai negli hook); 6.1 (avvisi dei modelli a un lavoro nuovo, decisione 6); 11.4 (`[models] files`, `[components] models_check`, variabili, scadenza e cache, decisioni 1, 4, 5, 7, 13); 16 (i fatti verificati di questo piano e dello Step 0 del Task 1, con gli URL e la data, e l'esito della prova vera); riga 30 della sezione 20; intestazione.
- [ ] **Step 2: Piano principale di B.** Stato in testa (corregge anche la frase di B3 «merge in attesa dell'OK», superata dall'unione del 03/11/2026); una riga B3-bis nella sezione 2; nella sezione 3 una riga B3-bis → B8 (righe `modelli:` dell'uscita di `start` per gli eval; nessun evento); sezione 9: chiusi i due rinvii «A B3-bis» (forma del punto unico: decisione 1; `test_real_markers_not_in_tollgate_bin`: invariato, host in `templates/models.toml`), più i minori rinviati che riguardano B4-B8; una sezione «Prove di B3-bis» con ogni riga della tabella «Copertura» e il test o l'evidenza che la prova.
- [ ] **Step 3: Progetto di B.** Riga di avanzamento: «B1, B2, B3 e B3-bis eseguite».
- [ ] **Step 4: Suite e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi (`tests/test_docs.py` compreso); commit «tollgate B3-bis: spec rev 30, progetto e piano principale di B».

---

## Copertura: punti del progetto e del piano principale destinati a B3-bis → task

| Punto | Task |
|---|---|
| Progetto 9: sentinella sul computer dell'utente, all'avvio di un lavoro, chiave nell'ambiente, niente segreti su GitHub né job programmati, hook senza rete | 2, 3, 4; decisioni 4, 6; Global Constraints |
| Progetto 9: fornitori Anthropic (`GET /v1/models`) e Gemini (`models.list`) | 1, 2; «Fatti verificati» |
| Progetto 9 (scelta del 1° novembre ripresa nel brief): OpenAI e OpenRouter se le loro pagine danno un elenco | 1, 2; «Fatti verificati» (entrambi lo danno) |
| Progetto 9: avviso per un modello stabile più nuovo della stessa famiglia | 1 (decisione 3), 3 |
| Progetto 9: avviso per un modello in uso che sta per essere ritirato | 1 (decisione 3), 3 |
| Progetto 9, «solo modelli stabili» | 1 (`test_gemini_newer_stable_only`, `test_anthropic_deprecated_newer_not_from_deprecated`) |
| Progetto 10: ciò che l'elenco non dà si salta e si dice | 1 (`test_gemini_retirement_not_checked_line`, `test_openai_shutdown_and_not_checked`, `test_openrouter_expiration_and_not_checked`); 3 (`test_some_keys_missing_lines`) |
| Progetto 10: una prova vera | 7 |
| Progetto 10: pulizia di `/tmp` | 5; 7, Step 1 |
| Piano principale, sezione 9, «A B3-bis»: forma del punto unico | 3; decisione 1 |
| Piano principale, sezione 9, «A B3-bis»: `test_real_markers_not_in_tollgate_bin` | 2 (`test_real_hosts_not_in_bin`); decisione 9 |
| Memoria, lezione del 03/11/2026: evidenze di B2 e gh-p4 con testo di terzi | 6; decisione 11 |
| Memoria, lezione del 03/11/2026: cartelle `tollgate-test-*` in `/tmp` | 5; decisione 10 |
| Revisione della spec del nucleo | 8 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B (sezioni 9 e 10), il brief di scrittura, il piano principale, la spec rev 29, il codice di `main` e il modello di B3.

| Giro | Rilievi | Esito |
|---|---|---|
| 1 | 0 critical; 7 important (I-1 hook `SessionStart` di terzi nelle evidenze non visti dal test, e un test esistente da estendere invece di duplicare; I-2 `test_wrong_host_refused` non scrivibile; I-3 nessuna scadenza complessiva della rete; I-4 un test poteva arrivare alla rete vera con la chiave della macchina; I-5 affermazione falsa sul guardrail `TOLLGATE_`; I-6 falsi allarmi su alias senza data e ID di Vertex; I-7 caso «nessuna chiave» non decidibile); 14 minor | «Non pronto». Corretti tutti: decisioni 1-5, 8, 10, 11 riscritte, decisione 13 nuova (forma delle righe); Step 0 del Task 1 (alias di Anthropic, variabile di OpenRouter); `Deadline`, `build_opener`, `no_network()`; test nuovi o rinominati nei Task 1-4, 6, 7; regola stretta per la pulizia di `/tmp` |
| 2 | I-2 e I-5 del giro 1 chiusi, I-3, I-6, I-7 chiusi, I-1 e I-4 in parte; 2 important nuovi (N-1 i test con processo figlio sfuggono a `no_network()` e alla radice finta; N-2 lo script della prova vuole `python3.11`, che il job 3.13 della CI non ha); 14 minor | «Non pronto». Corretti tutti: test del Task 4 nello stesso processo e regola sui processi figli nei Global Constraints; `B3BIS_PY`, `B3BIS_TOLLGATE`, cartelle `/tmp/tollgate-run-*` nei test del Task 7; decisione 11 (radici note di tollgate, ogni uscita `SessionStart` oltre il tetto, un solo iteratore); decisioni 1, 2, 4, 5, 6, 10, 13 precisate (caratteri dei percorsi, `MAX_FILES`, `git.object_info_at`, nomi vecchi di Claude, `hint` per la riga «manca la chiave», `ProxyHandler({})`, `FetchError` fuori da `except`, ordine delle righe, `-name 'tollgate*'`, righe come dati); `test_hook_run_does_not_load_models_net` |
| 3 | N-1 e N-2 del giro 2 in parte; 3 important nuovi (R3-1 `tollgate_skill` sbagliava sul worktree `p4` e dipendeva da `ROOT.name` in CI; R3-2 le uscite `SessionStart` corte di terzi restavano; R3-3 i test dello script della prova lanciano un figlio con una chiave e `[models] files`); 10 minor | «Non pronto». Corretti tutti: radici di tollgate scritte come letterali, con il caso `p4`; ogni uscita `SessionStart` che non comincia con `tollgate:`; eccezione scritta nei Global Constraints per i test dello script (ambiente senza chiavi vere, `B3BIS_TOLLGATE` obbligatorio, file segnale, cartelle `tollgate-b3bis-test-*`, `B3BIS_PY` in ogni test); riga «forma inattesa» e cache scritta dopo la convalida; cache con data futura; `hint` con `fullmatch`; avvisi di configurazione in `models check`; `os.chdir` nei test del Task 4; `grep` dei prefissi e `tollgate-run-*` vecchie |
| 4 | R3-1 e R3-3 chiusi, R3-2 chiuso nel merito; 1 important nuovo (R4-1 il segnaposto degli hook risultava a sua volta di terzi: test rosso dopo la pulizia e `togli_pagine` non idempotente); 10 minor | «Non pronto». Corretti tutti: forma fissa del segnaposto esclusa dal tipo «hook», test di idempotenza; prefisso `claude-(?:[a-z0-9]+-)?[0-9]` in decisione 2 e in `hint`; avviso dei percorsi con `repr`; riga «non è un file»; timeout ridotto a `deadline.left()` e DNS dichiarato; iteratore interno nelle Interfaces del Task 6 con il controllo `codeText`; `test_model_key_vars_match_providers_file`; regola sui figli limitata a `bin/tollgate`; `prova` dalla cartella del repo, confronto delle chiavi in bash; `paths.program_command` nelle righe |
| 5 | R4-1 chiuso (verificato anche sulle evidenze vere: uscite degli hook, percorsi delle skill); 8 minor (righe di cache a ogni `start`; chiave vuota nello script; `components_off` del gate con `models_check = false`; `mock.patch` di `parse_pages` e delle funzioni git; apostrofi nei commenti; cache per fornitore e non per chiave; `grep` dei prefissi incompleto; `hint` di OpenAI troppo largo) | **«Pronto». Critical aperti: 0. Important aperti: 0.** Corretti comunque tutti i minor: `show_cache=False` in `start`, variabili vuote saltate, costi scritti nelle decisioni 1 e 7, chiamate attraverso il modulo, test sugli apostrofi, nota nel ledger, vincolo sull'`hint` di OpenAI |
