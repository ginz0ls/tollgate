# Task 5: report dell'implementatore

## Fatto
- `skills/rules-infra/SKILL.md`: correzioni del controller. R-INFRA-01 «dove gira oggi» dichiarato scelta nostra; R-INFRA-02 estensione a Docker dichiarata scelta nostra e «Dove informarsi» con https://docs.docker.com/; R-INFRA-03 senza la sezione 3.4; R-INFRA-12 con l'immediatezza di `secret put` attribuita alla pagina dei segreti di Cloudflare. Nessuna regola esce (01-12). Non c'è `approved`.
- `docs/profili/verifiche/infra-fonti.md`: due tabelle («Regole e fonti», 33 righe, 4 `no` tenute; «Pattern dei percorsi», 14 `ok`), correzioni, parti «scelta nostra», `.vercel/` non è un file del repo.
- `docs/profili/infra.md`: pagina in parole semplici (tabella a cinque colonne, quando si accende, cosa cambia per i comandi con `dod`, `allow_no_tests`, decisione 17, «Da decidere tu» con sei punti compreso il cambio per `ai`, regole tolte senza id, come rispondere).
- `tests/test_rules_infra.py`: `RulesInfraPageTest` (14 test). RED prima (13 errori/fallimenti), poi GREEN.

## Suite
`PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3640 OK (skipped=6), python3 3640 OK (skipped=4). Log: `task-5-suite.log`. Nessun fallimento di `test_db_restore_interactive_eof_and_ctrl_c`.

## Skipped in più (6 e 4 contro 5 e 3)
Uno per interprete: `test_page_approval_date_matches_skill`, che salta finché la skill non ha `approved` (lo scrive il Task 6). Gli altri skip sono quelli della baseline.

## Dubbi
- Il punto 5 di «Da decidere tu» (cartelle `.github/actions/` fuori da ogni profilo) non era nel dispatch: l'ho aggiunto perché è una scelta del piano (decisione 18) che l'utente non ha visto. Il controller può toglierlo.

## Fix round 1
Modifiche:
- R-INFRA-05 della skill ammette `"@nome"` in `env`/`build.env` di Vercel (riferimento a un segreto), con la fonte nella `Fonte:`; riga `ok` nel rapporto (esempio `@my-secret-name` della pagina `vercel-json`); test `test_secret_reference_exception_matches_skill` (pagina e skill) e `test_page_choices_count_matches_list` (conteggio dei punti di «Da decidere tu»).
- Pagina: glossario con `vars`/`ENV`/`ARG`, `npx` e lanciatori, CI, Terraform/nginx/systemd, `backend`; la 3.4 è «proposta del progetto di B che hai rivisto»; nuovo punto 7 (R-INFRA-05, «li imposta l'utente»), «Sette punti».
- Rapporto: cella `no` di R-INFRA-12 dice che riguarda solo l'attribuzione di «secret cambia subito» ed è corretta; riga sui punti di «Da decidere tu» allineata.
Non fatti (minor 5 e 6 della revisione, non richiesti): numeri «dodici»/«quattro fonti» non testati; controllo dati privati solo `/home/`.
Test: `python3 -B -m unittest tests.test_rules_infra tests.test_rules_ai tests.test_docs tests.test_skill_contract`: 94 OK (skipped=3).
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` (log `task-5-suite-2.log`): python3.11 3642 OK (skipped=6), python3 (3.13.5) 3642 OK (skipped=4). Nessun fallimento del test pty.
