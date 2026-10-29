# Task 9, Step 1: report

Commit db7cd80 «tollgate B1: script della prova reale di un lavoro L1 (Task 9, Step 1)».

## Cosa ho fatto
- `spikes/run-b1-flow.sh`: modi `controlla`, `prepara`, `passo1`, `passo2`, `registra`.
- `spikes/b1/flowreg.py`: aiuti di sola lettura per `registra` (comandi Bash e conto strumenti, lookups e nota salvata, eventi research_note/research_reminder/veto, conto Grep vs letture).
- `spikes/b1/flow/`: progetto di prova (tollgate.toml, config.toml, src/, tests/test_smoke.py, .gitignore), `issue-1.md` (testo dell'issue #1), `piano-L1.md` (piano L1 con un task: Create `src/conf.py`, Test `tests/test_conf.py`, must-have `tests.test_conf.ConfTest::test_leggi_nome`).
- 14 test in `tests/test_b1_scripts.py` (classe `FlowScriptTest`, radici finte e `claude` finto; nelle evidenze del repo non scrive niente, controllato da un cleanup del test).
- NON fatti (del controller): rapporto `docs/verifiche/2026-10-27-b1-prova-flusso.md`, Step 2-4. Non ho creato `docs/verifiche/evidenze/b1/flusso/`: la crea lo script.

## Ruling applicati
- B1-V2: `--allowedTools` = `Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob,WebFetch,WebSearch`.
- B1-V7: `prepara` scrive solo nella copia `skills/rules-base/SKILL.md` con `approved: prova-b1`; niente `APPROVED`; test `test_flow_rules_base_only_in_copy`.
- B1-V6: `registra` scrive `grep-non-registrati.txt` ("Grep del modello: N; letture registrate (read): M" e la frase che i Grep non sono registrati); `comandi-modello.txt` ha il conto per strumento (totale, di cui da subagenti) e le righe dei Grep.
- Task 5: prima del primo `claude -p`, `passo1` lancia `claude plugin validate --strict .` con cwd la copia (esito in `validate/validate-N.txt`); se fallisce il passo si ferma senza `claude -p` e senza consumare un tentativo. Test `test_flow_passo1_validates_the_copy_first_and_stops_on_failure`.

## Come funziona
- Radice `/tmp/tollgate-b1` (o una sottocartella, senza `..`); altrimenti rifiuto "non è sotto /tmp/tollgate-b1/". Sotto: `plugin/` (copia), `flow/` (repo di prova), `origin.git` (nudo locale, URL GitHub finto con insteadOf come in p3a), `state/` (sentinella `.tollgate-test`), `ghbin/gh` (shim sul finto `tests/fakegh.py`, in testa al PATH), `fakegh-data.json`, `fakegh.log`.
- `prepara` non cancella: rinomina in `<nome>.prev-<tempo>` anche `passo1/` e `passo2/` delle evidenze. Controlla il piano con plan-check.
- Ogni passo: `claude -p --plugin-dir ... --model sonnet --permission-mode acceptEdits --allowedTools ... --disallowedTools ... --output-format stream-json --verbose --include-hook-events`, dentro `timeout` (predefinito 2400 s, `B1_FLOW_TIMEOUT`). Divieti: `Bash(*/gh:*)`, `command gh`, `gh repo|api|auth|secret`, `git push` verso https/http/ssh/git@, `--force`, `-f`, `--mirror`, `--delete`, `curl`, `wget` (anche per percorso).
- Tentativi: `docs/verifiche/evidenze/b1/flusso/<passo>/tentativo-N/` con `argv.txt`, `claude.jsonl`, `claude.err`, `uscita.txt`, `esito.txt` (inizio, fine, uscita, "tetto di tempo superato" se 124). Al quarto tentativo per passo: rifiuto. Registro in `exit-codes.txt`.
- `passo2`: serve il worktree `tg/1-*` creato da `passo1`; il prompt chiede Write del piano in `docs/superpowers/plans/2026-10-27-prova-b1.md` (testo del piano nel prompt tra `<<<PIANO` e `PIANO>>>`), il commit con git, poi `/tollgate:execute`, senza `/tollgate:finish`.
- `registra`: cartella nuova `registro-N/` con versione di claude, events/stats/`status --json`, `eventi-ricerca.jsonl`, `lookups.txt` (righe, conto per tipo, stato dei task, nota salvata), `comandi-modello.txt`, `grep-non-registrati.txt`, `comandi-rischiosi.txt` (bash con git push/gh/curl/wget), log git del worktree, `research-*.md`, `fakegh.log`, log degli hook.

## Test ed esiti
- `python3 -B -m unittest tests.test_b1_scripts`: 32 test OK.
- `tests/run` completa: python3.11 3117 test OK (skipped=2), python3 (3.13.5) 3117 test OK. Nessun `__pycache__` nel commit.
- TDD: scritti script e test insieme; il primo giro ha dato 6 rossi (passo2 senza `verifica_radice`, regex statica sul `--force` dei divieti, conteggio di `plugin validate` anche nell'eco di `controlla`), corretti.

## Scostamenti e dubbi
- Esclusi dalla copia del plugin `docs`, `evals`, `tests`, `spikes`, `.superpowers`: copiati solo `.claude-plugin agents bin gate hooks skills templates statusline LICENSE`.
- `registra` e `passo` leggono `hook-errors.log` e `skipped.log` solo se esistono.
- Non verificato con `claude` vero (vietato): in particolare se `plugin validate --strict .` con cwd la copia accetta il frontmatter nuovo, e che `parent_tool_use_id` nel flusso stream-json distingua i subagenti (se il campo manca, "di cui da subagenti" risulta 0).
- `registra` dipende da `status --json`, `events`, `stats` sullo stato di prova; senza `tollgate.db` (nessun passo eseguito) `lookups.txt` resta con l'errore in `lookups.err`.

## Comandi per il controller (dalla radice del worktree b1)
```
bash "spikes/run-b1-flow.sh" controlla
bash "spikes/run-b1-flow.sh" prepara
bash "spikes/run-b1-flow.sh" passo1
bash "spikes/run-b1-flow.sh" passo2
bash "spikes/run-b1-flow.sh" registra
```
Esito di ogni tentativo in `docs/verifiche/evidenze/b1/flusso/<passo>/tentativo-N/esito.txt`; più di 3 tentativi per passo sono rifiutati.

## Giro 1
Commit: vedi `git log` («tollgate B1: script della prova reale (Task 9, giro 1)»).
- I1: `tentativi_fatti` conta i `tentativo-*` di `<passo>/` e di `<passo>.prev-*/`; oltre 3 in tutta la prova rifiuto, e la numerazione prosegue. Test del tetto corretto (dopo `prepara` il quarto è rifiutato) e nuovo `test_flow_attempt_cap_counts_moved_attempts_in_two_folders` (2 + 1 tra due cartelle).
- I2: `registra` chiama `flowreg comandi` una sola volta con tutti i flussi dei due passi; `_count` somma le righe. Test `test_flow_registra_sums_greps_over_attempts_and_steps` (2+0+7 Grep = 9, letture registrate sommate).
- I3: copia del plugin con lista di esclusione (`.git .github .claude .superpowers docs spikes tests __pycache__`); `evals` e `LICENSES` ci sono. Il test verifica che il percorso `experimental.evals` di `plugin.json` esista nella copia.
- Minor: test che il `claude` finto riceve il `PATH` con `ghbin` per primo, `TOLLGATE_GH` e `TOLLGATE_FAKEGH_DATA`; `timeout -k` (60 s, `B1_FLOW_KILL`); `registra` scrive `fallimenti.txt` e esce 1 se `events`/`stats`/`status`/`lookups`/`eventi` falliscono, dopo aver raccolto il resto (test con DB corrotto); `limiti.txt` in ogni `registro-N/` con scappatoie dei divieti a prefisso, Write/Edit nudi, eventi non separati per passo, `parent_tool_use_id` non verificato, tetto e `registra` sulla preparazione corrente. La regex di `comandi-rischiosi.txt` ora prende `git ... push`.
- Test: `tests.test_b1_scripts` 36 OK; `tests/run`: python3.11 3121 OK (skipped=2), python3 3.13.5 3121 OK.
