# Task 5, ri-revisione del giro 1

### Verdetti sui rilievi
1. **Eccezione "@nome" in R-INFRA-05 con fonte, riga nel rapporto e test**: INDIRIZZATO. Skill `skills/rules-infra/SKILL.md:30` (regola) e `:32` (Fonte: pagina `vercel-json`, sezioni `env` e `build.env`). Rapporto `docs/profili/verifiche/infra-fonti.md:25`, riga `ok` con citazione di una riga, trovata alla lettera in `fonti/infra/vercel-json.md:1891` (tolto solo il markup del link). Test `test_secret_reference_exception_matches_skill` (`tests/test_rules_infra.py`) confronta pagina e skill e richiede la riga `ok`. `python3 -B -m unittest tests.test_rules_infra`: 36 OK (skipped=1, il test dell'approvazione).
2. **Parole spiegate, 3.4 come proposta, cella `no` di R-INFRA-12**: INDIRIZZATO. `docs/profili/infra.md:14-19` spiega `vars`/`ENV`/`ARG`, `npx` e i «lanciatori», CI, Terraform/nginx/systemd, `backend`, tutti prima del primo uso. La 3.4 è «una proposta del progetto di B che hai rivisto» (righe delle regole 1 e 2). La cella `no` di R-INFRA-12 (`infra-fonti.md:40`) dice che il `no` riguarda solo l'attribuzione di «`secret` cambia subito» ed è corretto.
3. **«li imposta l'utente» in «Da decidere tu», conteggio coerente**: INDIRIZZATO. Punto 7 in `infra.md` («Sette punti»; chiusura «Per i sette punti»); il rapporto lo rimanda al punto 7 (`infra-fonti.md:87`); `test_page_choices_count_matches_list` verifica il conteggio.

Coerenza pagina/skill: numero, «Blocca?» e «Si giudica su» invariati (i test di allineamento passano; le righe delle regole 1-12 non sono state toccate nel numero né nelle colonne). Nessun testo copiato da pagine di terzi nella skill o nella pagina; la sola citazione (una riga) è nel rapporto.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minor: nella riga della regola 5 della pagina l'eccezione nomina solo `env` di Vercel, mentre la skill dice `env` o `build.env`. Incoerenza lieve, non bloccante.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
