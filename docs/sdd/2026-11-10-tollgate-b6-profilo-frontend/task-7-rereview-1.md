# Ri-revisione giro 1, Task 7 (d61f7e6)

### Verdetti sui rilievi
1. **Test che legge i file veri senza prefisso `test_real_`**: INDIRIZZATO. `tests/test_b1_scripts.py:1819` (`test_real_scrivi_limiti_heading_is_generic_frontend`) e `:1953` (`test_real_scrivi_limiti_heading_is_generic_backend`, gemello che usa `backend_prepara()` e i file veri). Il test `test_scrivi_limiti_heading_is_generic` (caso b1, senza `_real_`) resta com'era, fuori dal diff.
2. **Commento dello script sui `.ts` e sulla rotta solo per `backend`**: INDIRIZZATO. `spikes/run-b1-flow.sh` ora ha il bullet comune `(backend, frontend)` senza la frase, e un blocco `if [ "$CASE" = backend ]` con la frase sui `.ts` e sulla rotta.
3. **`registra` cerca `http.server` ovunque, con i casi in `test_real_registra_flags_ui_tools_frontend`, e `limiti.txt` che dichiara il limite di `--disallowedTools`**: INDIRIZZATO. Regex `^bash( \(subagente\))?: .*http\.server` (`spikes/run-b1-flow.sh`, riga del commento «B6 (decisione 15)»); i quattro casi richiesti (`-mhttp.server`, `python3 -B -m http.server`, `python3.11 -m http.server 8000`, `python3 -c "import http.server..."`) sono nell'elenco `flagged` del test, che verifica `bash: {cmd}\n` in `comandi-rischiosi.txt`. Il bullet `(frontend)` di `limiti.txt` cita le forme non coperte e dice che `registra` le cerca; il test asserisce `python3.11 -m http.server` nei limiti (stessa riga del bullet, quindi la sottostringa c'è).

Falsi positivi sui comandi innocui: nessuno. La regex richiede la sottostringa letterale `http.server`; `python3 -m unittest discover`, `cat web/index.html`, `git add web/styles.css`, `ls web/vite.config.txt` non la contengono, e il test li esclude con `assertNotIn` (`python3 -m unittest` incluso). Solo un percorso che contenga davvero `http.server` verrebbe segnalato, e per un elenco di controllo manuale è accettabile.

### Danni nuovi nel diff della correzione
Nessuno. Nota minore non bloccante: nel diff resta la doppia riga vuota prima di `bash_saved_stream` (rilievo minor 4 della prima revisione, non incluso nei rilievi da giudicare).

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
