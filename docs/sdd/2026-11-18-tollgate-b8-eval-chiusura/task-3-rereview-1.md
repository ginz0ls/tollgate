# Ri-revisione Task 3, giro di correzione 1 (7618110..a1906b8)

### Verdetti sui rilievi
**I1 — `strip_bash_web` non vedeva `python3`/`node` con lo script su stdin:** INDIRIZZATO.
`evals/scrub.py` `_names_domain` cerca il dominio (parola intera, senza distinzione di maiuscole) nel testo grezzo del comando, heredoc e here-string compresi; `_fetches_domain` esenta solo se `_is_exempt` (ogni comando letto da `bash.parse` è `sed` o `research submit`; un comando illeggibile non è esente). Test in `tests/test_eval_run.py` (`StripBashWebTest`): heredoc, here-string, `xargs curl`, `perl -e` sostituiti (7 in tutto); nota, `sed`, `altro-dominio`, `dominio-simile` invariati.
Prove mie con `python3 -B` (script nello scratchpad, non nel repo), tutte sostituite come richiesto:
- `curl https://vercel.com/docs; … research submit <<N`
- `research submit <<N … N` seguito da `curl …`
- `sed -i … && curl …`
- `sed -n 1,5p <(curl …)`, `sed -n p $(curl …)`
- `research submit "$(curl …)"` e con backtick
- `(curl …); tollgate research submit`
- `bash -c 'curl …'; tollgate research submit`
Un `submit` con heredoc che nomina il dominio resta esente.

**⚠️ Test di `anonymize` con lo schema vero:** INDIRIZZATO.
`AnonymizeTest.test_anonymize_real_tollgate_schema` usa `core_db.open_db` e `core_events.record_event`. Controlla host e `data` ripuliti, `integrity_check` ok, niente `-wal`/`-shm`, valori assenti dai byte del file (`tests/test_eval_run.py`, nuovo test dopo `test_anonymize_...` del diff).

### Danni nuovi nel diff della correzione
- **Minor** — `evals/scrub.py` `_is_exempt`: `"research" in c.argv and "submit" in c.argv` cerca le due parole in qualunque posizione di argv, non come sottocomando. Un comando unico come `curl -s https://vercel.com/docs research submit` o `python3 -c "…urlopen('https://vercel.com')…" research submit` risulta esente e il suo risultato resta nella trace (provato: `_fetches_domain` → `None`). Non è la forma composta richiesta (quella è coperta) e richiede argomenti finali innaturali; si chiude esigendo che `argv[0]` o il secondo elemento sia `tollgate`/`*/tollgate` seguito da `research submit` contigui. Non blocca.
- **Minor** — `sed` è esente per nome: `sed -n '1e curl -s https://vercel.com/docs' /dev/null` (comando `e` di GNU sed) legge la pagina e resta esente (provato). Contrivato; stessa soglia, non blocca.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important (due Minor sull'esenzione, sopra).
