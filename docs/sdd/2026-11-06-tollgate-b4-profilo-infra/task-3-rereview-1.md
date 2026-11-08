# Ri-revisione giro 1, Task 3

### Verdetti sui rilievi
1. **PACKAGE_COMMANDS senza `docs`, `config`, `help`, `repo`, `home`, `patch`; restano `search`, `explain`, `bugs`, `rebuild`, `dedupe`, `prune`, `fund`; tre nuovi casi con effetto; guardie `npm search/explain vercel` → None.** INDIRIZZATO. `bin/tollgate_analysis/bash.py:1007-1010` (diff) ha esattamente la lista richiesta; `tests/test_bash.py` (test_launcher_wrapped_effects) aggiunge `pnpm --filter docs exec wrangler deploy`, `pnpm -C docs wrangler deploy`, `yarn workspace docs wrangler deploy` con esito True; le guardie `npm search vercel`, `npm explain vercel` → False restano a `tests/test_bash.py:218`.
2. **Due test di guardia, codice di produzione invariato.** INDIRIZZATO. `test_commands_config_matches_launcher_text` (`commands=["npx mytool"]` su `npx mytool run` non None; `bash.py:1145` confronta `cfg.commands` col testo) e `test_curl_and_gh_stay_on_original_argv` (`npx curl …`, `npx gh pr list` → False). Il diff di `bash.py` tocca solo la tupla.

Controllo mirato: `python3 -B -m unittest tests.test_bash` → 81 test OK.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
