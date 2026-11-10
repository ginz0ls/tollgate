# Report Task 7 (implementatore sonnet)

Commit: 161882a "tollgate B5: prova reale con il profilo backend, script e progetto di prova; togli-pagine per Bash; prefisso test_real_".

## Implementato
- `spikes/b5/flow/` (tollgate.toml identico a quello di b4, config.toml, server/app.py con `ROUTES`/`dispatch`/funzione pura `hello`, edge/index.ts con import da `cloudflare:workers`, supabase/functions/hello/index.ts con `Deno.serve(`, tests, issue-1.md, piano-L1.md, .gitignore). Nessuna credenziale; i `.ts` sono solo testo.
- `spikes/run-b1-flow.sh`: `B1_FLOW_CASE=backend` (PROJ, PROJ_FILES, PLAN_REL=docs/superpowers/plans/2026-11-09-prova-b5.md, ISSUE_TITLE, OUT=b5/flusso, valori ammessi, regole vere obbligatorie, scrivi_dati_gh, proponi_profilo backend/server/app.py, controlla, trascrizioni e tipi, limiti.txt); `DEPLOY_CLIS` + `supabase deno node` (quattro forme); grep dei comandi rischiosi su infra e backend. `bash -n` ok; nessun `--force`, `--no-verify`, `kill `.
- `spikes/b1/flowreg.py`: titolo `# Regole backend (versione 1)` in `AREA_TITLES`; `Bash` in `SAVED_TOOLS` (`_saved_copy` cerca `tool-results/` nel testo del comando, solo se c'è un lettore cat/sed/head/tail/grep/rg/awk/less/more/nl); `_swap_saved` sostituisce anche `tool_use_result.stdout`; il rilevamento guarda anche `stdout` (blocco già segnaposto ma stdout col testo: segnalato e riscritto).
- `tests/test_b1_scripts.py`: `src_repo(case="backend", backend_approved=...)` con `skills/rules-backend/`; 13 test nuovi (i 13 del brief); import `tomllib`.

## Test rinominati (solo il nome, prefisso test_real_)
test_flow_case_infra_project_verifies, test_flow_case_infra_prepara_refuses_without_profile, test_registra_flags_deploy_clis, test_registra_reads_infra_title, test_registra_infra_refuses_an_empty_home, test_flow_case_infra_project_has_no_credentials, test_flow_case_infra_task_forbids_publishing; gemelli ai: test_flow_case_ai_prepara_refuses_without_profile, test_flow_case_ai_project_verifies, test_registra_ai_refuses_an_empty_home, test_registra_reads_only_matching_lines. Non rinominati: test_flow_case_backend_out_dir, test_flow_disallows_service_clis_backend, test_registra_deploy_clis_only_for_infra.

## Verifica
- `python3 -B -m unittest tests.test_b1_scripts`: 91 test OK con python3 (3.13) e python3.11, compreso `test_committed_evidence_has_no_long_web_results` (evidenze di B1-B4 non toccate: nessun blocco di terzi).
- Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run`: 3755 test, OK (skipped=8), exit 0, nessun «unclosed» (`task-7-suite.txt`).
- RED: il progetto e i test sono stati scritti insieme prima di lanciare il modulo; la prima corsa ha mostrato due rossi veri nel mio codice (bug: `stdout` considerato anche senza copia salvata, che segnalava 271 blocchi nelle evidenze di B1-B4 e un `cat app.py`), corretti subito. Non ho una corsa rossa dei test contro il codice vecchio.

## Scostamenti e dubbi
- Il piano del lavoro non nomina «contratti», «indirizzo», «prova locale», «pagina ufficiale», «chi li usa» (verificato dal test).
- `ls` o altri comandi su `tool-results/` senza lettore non vengono riscritti (scelta mia: il loro stdout sono nomi di file).
- Nessuno script vero eseguito (`prepara`/`passo*`/`registra` solo nei test con HOME finta e `B1_FLOW_CHECK=1`).
