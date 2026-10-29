# Ri-revisione giro 1, Task 1

### Verdetti sui rilievi
1. **Grep `content` anche su `src/app.py`, chiavi `grep_content` / `grep_content_dir`, passi e test**: INDIRIZZATO. Prompt a 12 passi con il passo 4 (path `src/app.py`, content) e il 6 (cartella, files_with_matches), "Dopo i dodici passi" (`run-b1-checks.sh` prompt); `raccogli.py` `classify`: content + path `.py` -> `grep_content`, content su altro path -> `grep_content_dir`; `SAMPLE_KEYS` aggiornato; test `test_checks_raccogli_anonymizes` verifica i path dei due campioni, `test_checks_allowed_tools` il testo del prompt.
2. **Grep su `src/app.py` senza `output_mode`, chiave `grep_default`**: INDIRIZZATO. Passo 5 del prompt ("non passare il parametro"); `classify`: `output_mode is None` + path `.py` -> `grep_default`; il Grep senza path e senza modo resta `grep_files`; il test usa l'evento `t3d` e verifica `assertNotIn("output_mode", ...)` e l'ordine delle chiavi.
3. **`TOLLGATE_STATE` isolato sotto `/tmp/tollgate-b1/` con sentinella, solo per `claude -p`**: INDIRIZZATO. `modo_sonda`: `mkdir -p "$TMP/state" && : > "$TMP/state/.tollgate-test"` ed `export` solo nella sottoshell del `claude -p` (`TOLLGATE_STATE="$TMP/state"`); il `claude` finto registra l'ambiente (`ENV`), il test controlla realpath e sentinella. Il `claude --version` non lo riceve (come richiesto, solo `-p`).
4. **`raccogli` rifiuta `--home` vuoto o assente**: INDIRIZZATO. Controllo sia in `run-b1-checks.sh` (modo_raccogli, `die`, messaggio su stderr, con `set -u` il ramo `${HOME:-}` non esplode) sia in `raccogli.py` `cmd_raccogli` (vuoto o `/`); `test_checks_raccogli_refuses_an_empty_home` prova `""` e `/`, verifica codice != 0, messaggio, nessuna scrittura.

Evidenza di verifica: ho rilanciato `python3 -B -m unittest tests.test_b1_scripts` sul codice finale (HEAD 39de853): 19 test OK; `bash -n` OK. Quindi l'evidenza copre il codice finale anche se la corsa completa di `tests/run` ha visto una versione intermedia: il file di test è stato rilanciato dopo l'ultima modifica (e l'ho confermato io).

### Danni nuovi nel diff della correzione
Nessuno.
(Minor non bloccante: in `classify` il ramo `grep_default` richiede path `.py`; un Grep senza output_mode su un file non `.py` cadrebbe in `grep_files`. Nella sonda il file è sempre `src/app.py`, quindi irrilevante.)

### Osservazioni fuori ambito
`docs/verifiche/evidenze/b1/` compare non tracciata (`valida-esito.txt`, creata mentre leggevo): è il lavoro del controller, non del diff.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
