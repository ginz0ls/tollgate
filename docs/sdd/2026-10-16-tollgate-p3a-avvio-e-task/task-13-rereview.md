# Ri-revisione Task 13, giro di correzione 2 (f7240d1..8ef5a59)

### Verdetti sui rilievi

1. **Important: D2 non esteso a brief e messaggi dei veti.** INDIRIZZATO. `bin/tollgate_core/paths.py` definisce `program_command` (`python3` + `shlex.quote`); è usato in `bin/tollgate_flow/taskcmd.py:147` (brief), `bin/tollgate_checks/subagent_start.py:34,38`, `bin/tollgate_checks/subagent_stop.py:127,135-137` e `bin/tollgate_checks/acts.py:29`. Un grep su `plugin_bin|BIN_PATH` in `bin/`, `agents/`, `skills/` non trova altre costruzioni di comando destinate al modello. Test sulla forma con percorso con spazi: `tests/test_taskcmd.py` (brief, con `assertIn(" ", str(BIN))`), `tests/test_check_agents.py` (verify e `block open`), `tests/test_check_subagent_stop.py` (veto), `tests/test_paths.py::ProgramCommandTest`, `tests/test_check_acts.py`. Il report mostra RED (3 fallimenti) e GREEN. La prova reale con `PLUGIN_REAL_PATH=1` esercita proprio il brief con percorso quotato con apici singoli: ricevuta `verify` registrata, task `done`, veti 0.
2. **Minor: test di cancellazione e rinomina del piano.** INDIRIZZATO. `tests/test_check_commit.py` (`test_deleted_registered_plan_is_denied`, `test_renamed_registered_plan_is_denied`): exit 2 e percorso nel messaggio.
3. **Minor: symlink in `_is_registered_plan`.** INDIRIZZATO. `bin/tollgate_checks/_common.py` aggiunge `(wt / path).is_symlink()` nella guardia iniziale; test `test_symlink_in_place_of_registered_plan_is_denied`.
4. **Minor: «questo percorso» nelle skill.** INDIRIZZATO. Tutte e sei le skill dicono «`<programma>` indica il comando intero…»; `tests/test_manifest.py` asserisce l'assenza della vecchia frase e la presenza della nuova (esclusa `setup`, che ha un'altra riga e usa `<radice>`).
5. **Minor: coerenza del rapporto.** INDIRIZZATO. `docs/verifiche/2026-10-16-p3a-prova-flusso.md:17` dichiara che «riuscito» vale per il codice di cfc07ae; D2 (`:40`), D4 (`:42`), D6 (`:44`) sono marcati SUPERATI dai giri.
6. **Minor: script sempre col link.** INDIRIZZATO. `spikes/run-p3a-flow.sh`: `PLUGIN_REAL_PATH=1` seleziona `$PLUGIN_REAL`, il `ln -s` viene saltato, `TG=(python3 "$PLUGIN/bin/tollgate")`.
7. **Minor: push al nudo e trascrizioni `~/.claude` non dichiarati.** INDIRIZZATO. Dichiarati in testa allo script e nel rapporto (sezione «Giro di correzione 2», «Dichiarazioni»).

### Verifica delle occorrenze lasciate
- `bin/tollgate_core/db.py:35` (`restore_hint`): usato in `db.py:224` («Ripristino dal terminale: …») e `bin/tollgate_hooks/runner.py:317`; testo per l'utente da terminale. Corretto lasciarlo.
- `bin/tollgate_hooks/runner.py:50` (`_footer`): «Programma: {BIN_PATH}. Per spegnere … dal terminale: touch …». Informazione, non un comando da eseguire. Accettabile, vedi osservazione.

### Strati
`paths.py` (tollgate_core) importa solo stdlib (`shlex` aggiunto). `tollgate_flow` e `tollgate_checks` importano da `tollgate_core`: direzione ammessa. Nessuna violazione.

### Danni nuovi nel diff della correzione
Nessuno. Nota senza gravità: il controllo symlink guarda il working tree anche quando `head_ref` è valorizzato (PostToolUse); l'unico effetto è negare in più, direzione sicura.

### Osservazioni fuori ambito
- `bin/tollgate_hooks/runner.py:50`: nel ramo `_fail` con `control=True` il footer finisce su stderr con exit 2, quindi è letto dal modello, e nomina il percorso nudo come «Programma». Non è un comando né quotato; se il modello lo copiasse ricadrebbe nel caso D2. Non blocca.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
