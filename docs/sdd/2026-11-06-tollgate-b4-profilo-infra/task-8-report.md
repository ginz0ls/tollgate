# Task 8 - report

Status: DONE. Commit 6af06c5 «tollgate B4: prova reale con il profilo infra, script e progetto di prova».

## Fatto
- `spikes/run-b1-flow.sh`: `B1_FLOW_CASE=infra` (PROJ `spikes/b4/flow`, OUT `b4/flusso`, PLAN_REL e ISSUE_TITLE del brief, regole vere obbligatorie, gh finto con la risposta sulla protezione, `proponi_profilo <area> <file>` con `infra`/`vercel.json`, HOME, trascrizioni e tipi in `registra`). `DISALLOWED` ha per i 10 programmi le forme `p`, `*/p`, `command p`, `env p`. `registra` (D5) cerca i programmi in posizione di comando; `limiti.txt` ha la riga D9.
- `spikes/b1/flowreg.py`: titolo `# Regole infra (versione 1)` (costante rinominata `AREA_TITLES`).
- `spikes/b4/flow/`: progetto di prova senza credenziali; `vercel.json` con la sola `cleanUrls`.
- `tests/test_b1_scripts.py`: i test del brief (D6 con `shlex.split` di `controlla`; D8 `src_repo` con `infra_approved`) più `test_registra_deploy_clis_only_for_infra` e `test_registra_infra_refuses_an_empty_home`.

## Verifica
`bash -n` ok; `tests.test_b1_scripts` 77 ok; `tests/run` con ResourceWarning=error: 3667 test OK (skipped=5), verificato dal controller su entrambi gli interpreti.

## Note
- Ho scritto codice e test insieme: il passo RED non è stato osservato separatamente.
- Limite noto della grep di `registra`: `env VAR=x yarn` non è segnato (documentato in `limiti.txt`); `cat dir/npm foo` darebbe un falso positivo.
- Mai lanciati `claude`, `prepara`, `passo1`/`passo2` fuori dai test.
