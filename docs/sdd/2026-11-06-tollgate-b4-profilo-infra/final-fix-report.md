# Report del giro di correzione finale B4

Commit: vedi `git log -1` sul ramo b4-profilo-infra.

1. I-1: `spikes/b1/flowreg.py` (`_saved_copy`, `_swap_saved`, ramo "copia salvata" in `_third_party`): ogni risultato di Read/Grep con percorso sotto `tool-results/` e' sostituito col segnaposto `[pagina di terzi tolta dalle evidenze: copia salvata da Claude Code (<file>), N caratteri]`, a qualunque lunghezza, idempotente. Test nuovo `test_flowreg_togli_pagine_replaces_reads_and_greps_of_saved_copies` (stream finto; verde dopo, rosso prima per assenza di blocchi). `test_committed_evidence_has_no_long_web_results` (gia' su tutte le evidenze, B3 e B3-bis comprese) con lo scanner allargato era ROSSO su passo1 riga 153 e passo2 riga 128; dopo `togli-pagine` sui soli .jsonl di `evidenze/b4/flusso/` (2 righe sostituite) e' VERDE. Nessun altro rilievo su B3/B3-bis. Riga 146 del rapporto della prova corretta. Grep di controllo (nome utente, host, sk-ant, ghp_, github_pat_, /home/ diverso da /home/USER): tutti 0. Nota: il tipo e' conservativo, anche un Read di un output salvato non di terzi verrebbe tolto.
2. M-1: `("docker-compose", "push")` in `bin/tollgate_analysis/bash.py`; test in `test_docker_push_forms` (rosso prima, verde dopo).
3. M-2: frase nei buchi noti in spec nucleo 8.5 (rev 31) e piano principale sezione 9.
4. M-3: `docs/uso/comandi.md` "Le caricano".
5. `len()` in `tests/test_init.py`; `spikes/b4/flow/.gitignore` con `.vercel/`, `.env*`, `.dev.vars*`, `.wrangler/` (nessuna eccezione preesistente, nessun test rotto).
6-7. M-4 e M-5 non toccati.

Verifica: unittest dei 4 moduli: 289 OK con python3.11 e python3. `PYTHONWARNINGS=error::ResourceWarning tests/run`: 3668 test OK (skipped=5), exit 0.
