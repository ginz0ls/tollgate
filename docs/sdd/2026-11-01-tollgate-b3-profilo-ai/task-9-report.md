# Report Task 9 (B3): prova reale con il profilo ai, script e progetto di prova

Status: DONE

## Cosa c'è
- `spikes/b3/flow/`: `tollgate.toml` (identico a quello di b1), `config.toml`, `issue-1.md`, `piano-L1.md`, `ai/__init__.py`, `ai/summary.py` (`riassumi(client, testo, model)`, nessun nome di modello), `services/notify.py` (`from anthropic import Anthropic`), `tests/__init__.py`, `tests/test_smoke.py` (non importa `services/`), `.gitignore`.
- `spikes/run-b1-flow.sh`: `B1_FLOW_CASE` (`b1` predefinito, `ai`). Con `ai`: richiede `B1_FLOW_RULES=vere`; OUT `docs/verifiche/evidenze/b3/flusso`; progetto, `PLAN_SRC`, `PLAN_REL` (`docs/superpowers/plans/2026-11-02-prova-b3.md`), titolo dell'issue e file di `controlla` dipendono dal caso. Il caso `b1`/B2 non cambia (stampa solo la riga `B1_FLOW_CASE: b1`).
- `prepara` (ai): gh finto con `api_status` e chiave `repos/{owner}/{repo}/branches/main/protection` (403 col messaggio Free: modalità `detect`) senza `statuses` -> commit con il `tollgate.toml` di base -> push -> url/insteadOf come oggi -> `init --propose` sulla copia del plugin (gh finto nel PATH, stato con sentinella; uscita in `$TMP/init-propose.txt` e a video) -> copia di `docs/superpowers/tollgate-init/files/tollgate.toml` nel repo, verifica che `[profiles.ai]` copra `services/notify.py` (altrimenti si ferma con «profiles.ai») -> secondo commit e push -> la cartella della proposta è spostata (mai cancellata) in `$TMP/tollgate-init.proposta-<tempo>-<pid>` -> `sha`, `statuses`, `plan-check`.
- `registra` (ai): rifiuta `HOME` vuota prima di creare il registro; `flowreg.py trascrizioni <home> <stream>...` ricava `cwd` e `session_id` dal primo messaggio `system` di ogni flusso (passo1/passo2), guarda solo `<home>/.claude/projects/<cwd con non-alfanumerici -> ->/<session_id>/subagents/agent-*.jsonl` e stampa solo i titoli `# Regole ai (versione 1)` e `# Regole di base (versione 1)` con `isMeta` (file `trascrizioni.txt`); `flowreg.py tipi <db>` -> `tipi-task.txt` con `agent_type` e `reviewer_type`. In b1/b2 niente di tutto questo.
- `flowreg.py`: `project_dir_name`, `trascrizioni`, `tipi`.

## Test (tests/test_b1_scripts.py)
Nuovi: `test_flow_case_ai_out_dir`, `test_flow_case_ai_requires_real_rules`, `test_flow_case_unknown_value`, `test_real_flow_case_ai_prepara_proposes_profile`, `test_flow_case_ai_prepara_refuses_without_profile`, `test_flow_case_ai_project_verifies`, `test_flowreg_project_dir_name`, `test_registra_reads_only_matching_lines` (cwd con punto e spazio, HOME finta, sessione e cartella estranee, righe del compito non salvate), `test_registra_ai_refuses_an_empty_home`, `test_registra_b1_does_not_look_at_transcripts`. `FlowBench.src_repo(case="ai", ai_approved=...)` copia i file veri tracciati (bin, templates, gate, agents, skills/rules-base, skills/rules-ai, .claude-plugin).

## TDD
RED: `python3 -B -m unittest tests.test_b1_scripts.FlowScriptTest` dopo aver scritto i soli test: `FAILED (failures=21, errors=2)` (es. `'[profiles.ai]' not found in 'schema_version = 1 ...'`).
GREEN: `python3 -B -m unittest tests.test_b1_scripts`: `Ran 54 tests ... OK`. `bash -n spikes/run-b1-flow.sh`: ok.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` (uscita in `task-9-suite.out`): python3.11 `Ran 3386 tests ... OK (skipped=4)`, python3.13 `Ran 3386 tests ... OK (skipped=2)`, rc=0.

## Istruzioni per il controller (Task 10)
Variabili per tutti i modi: `export B1_FLOW_CASE=ai B1_FLOW_RULES=vere` (HOME vera: `registra` legge solo le due cartelle di sessione). Ordine: `spikes/run-b1-flow.sh controlla` -> `prepara` (guarda `init-propose.txt` in `/tmp/tollgate-b1/` e il blocco `[profiles.ai]` nel `tollgate.toml` del repo di prova) -> `passo1` -> `passo2` -> `registra`. Uscite in `docs/verifiche/evidenze/b3/flusso/` (`registro-N/trascrizioni.txt`, `tipi-task.txt`, `precarico.txt`). Il tetto di 3 tentativi per passo resta. Il lavoro chiede a `implementer-ai` la costante `SUMMARY_MODEL` in `ai/models.py` (nome scelto dall'agente).

## Scostamenti e dubbi
- Nessuno scostamento di sostanza. `init --propose` in modalità `detect`: ho scelto la risposta Free perché il piano dice «detect su Free»; con `protected` servirebbe una protezione completa nel finto.
- `registra` con `ai` esegue anche `precarico` (già attivo con `vere`): le trascrizioni dei subagenti non hanno `agent_transcript_path` nello stream finto, quindi quel file potrebbe dire «indizio»; la prova vera è `trascrizioni.txt`.
- Non verificato dal vivo (vietato): il formato reale di `system init` (`cwd`, `session_id`) e la posizione `subagents/` sono presi dalla decisione D15; se il `claude` vero differisce, `trascrizioni.txt` dirà «nessuna trascrizione di subagente».

## Fix round 1
- `flowreg.py trascrizioni`: la riga d'intestazione stampa «sessione N» (numero d'ordine) e la cartella solo se il `cwd` è sotto `/tmp/tollgate-b1/`; il `session_id` reale non compare mai nell'uscita. Un `session_id` che non fa `fullmatch(r"[A-Za-z0-9_-]+")` salta la sessione con «session_id non valido: sessione saltata», senza il valore.
- Test: `test_registra_reads_only_matching_lines` ora verifica che `sess-uno`/`sess-due` e i percorsi fuori da `/tmp/tollgate-b1/` non compaiano e che ci siano «sessione 1» e «sessione 2» (tolti commento e `assertTrue(wt.is_dir())`); nuovo `test_flowreg_trascrizioni_skips_an_unsafe_session_id` (`sid` = `../../estranea`, la cartella estranea non si legge).
- Esito: `python3.11 -B -m unittest tests.test_b1_scripts` e `python3 -B -m unittest tests.test_b1_scripts`: 55 test, OK.
