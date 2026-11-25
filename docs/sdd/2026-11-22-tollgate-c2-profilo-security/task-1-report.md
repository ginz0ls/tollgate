# Task 1: report dell'implementatore (opus)

**Status:** DONE
**Commit:** `0ae01de` «tollgate C2: revisori su Fable, implementatori su opus, mai sonnet» (ramo `c2-profilo-security`)

## Cosa ho fatto

- **Agenti (solo la riga `model:`)**: `model: fable` per `task-reviewer`, `reviewer-{ai,infra,backend,frontend,database}`, `final-reviewer`, `final-database`, `finding-verifier`, `spec-auditor`, `spec-adversary`, `plan-adversary` (12); `model: opus` per `implementer` e `implementer-{ai,infra,backend,frontend,database}` (6). `git diff --stat agents/`: 18 file, una riga ciascuno.
- **`bin/tollgate_flow/taskcmd.py`**: `MODEL_HINT = "opus"`; il suggerimento è `cfg.get("review.models").get(routing.implementer)`, e dal giro 4 (`renamed`) diventa `hint or MODEL_HINT`. Primo avvio e giri 1-3 invariati. Commento aggiornato (decisione 21 + decisione 14 di C2: la chiamata vuole un alias).
- **`skills/execute/SKILL.md:34`**: il riepilogo è `[model: <modello>]`, e la riga dice quando compare (`[review] models`, e sempre dal giro 4 con `opus` di base). **`:46`**: giri 4-5 con «il `model` del riepilogo (`opus`, o il valore di `[review] models`)». Nessun `model: inherit` resta nelle skill.
- **Script**: `spikes/run-b1-flow.sh:83` `MODEL=opus`; `spikes/b1/run-b1-checks.sh:34` `B1_MODEL:-opus`; `evals/run.sh:47` `MODEL=claude-opus-5-5` (ID completo, come prima). `bash -n` ok su tutti e tre.
- **`docs/uso/eval-e-ci.md:42`** (D11): modello `claude-opus-5-5` (scelta dell'utente del 22/11/2026); nella stessa riga: i punteggi e i costi di `p5` e `b8` sono su `claude-sonnet-5-5` e non si confrontano, la prossima corsa va aperta come campagna nuova (registro e tetto in `CAMPAIGNS` di `evals/cost.py`) scelta con `--campagna`, perché la predefinita di `run.sh` è ancora `b8`.
- **`docs/uso/comandi.md`**: sezione nuova `## Modelli degli agenti`, prima di `## La CLI`: i ruoli (`fable` / `opus` con i tipi), la scelta dell'utente, gli alias, `[review] models` con esempio TOML (alias, «per esempio `fable` o `opus`»; non accetta ID completo né `inherit` nella chiamata; tollgate non valida il valore), dove vale (implementatore, revisione finale, audit; dal giro 4 sempre un modello; il revisore del task usa la definizione: verificato, `review-prepare` non legge `[review] models`, lo leggono solo `taskcmd.py:176`, `finalreview.py:127`, `audit.py:478`), cosa fa Claude Code se l'account non ha il modello (`availableModels`: versione più recente permessa della famiglia, poi `CLAUDE_CODE_SUBAGENT_MODEL`, poi la sessione, avviso solo interattivo; catena di riserva) e `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (ignora riga `model:` e parametro della chiamata; resta `CLAUDE_CODE_SUBAGENT_MODEL` o la sessione). I fatti vengono dalla riga della pagina dei subagenti in `fatti-verificati.md`; «resta `CLAUDE_CODE_SUBAGENT_MODEL` o la sessione» con FORCE è la mia deduzione dall'ordine delle precedenze lì riportato.

## Test

- `tests/test_manifest.py`: costanti `REVIEW_MODEL = "fable"`, `WRITER_MODEL = "opus"` e `SONNET_PIN` (la regex della decisione 14: `model: (sonnet|haiku)`, `--model (sonnet|haiku)`, `MODEL=(sonnet|haiku|claude-sonnet|claude-haiku)`, `:-(sonnet|haiku)`). Aggiornati `test_agents_frontmatter`, `test_final_agents_frontmatter`, `AUDIT_AGENTS`. Nuovi:
  - `test_no_agent_on_sonnet`: nessun `agents/*.md` con `sonnet` o `haiku` nel `model`.
  - `test_agent_models_by_role`: `readonly_agents` senza `Explore` → `fable`; `implementer` e `implementer-*` → `opus`; in più ogni `agents/*.md` deve stare in uno dei due gruppi («un agente senza un ruolo»): il Task 7 dovrà quindi aggiungere `reviewer-security`/`final-security` a `readonly_agents` (cosa già prevista dallo scan 4-bis punto 7) e chiamare `implementer-security` così.
  - `test_no_sonnet_in_skills_and_scripts`: nessuna riga di `skills/*/SKILL.md`, `spikes/run-b1-flow.sh`, `spikes/b1/run-b1-checks.sh`, `evals/run.sh` che corrisponda a `SONNET_PIN`; nessun `model: inherit` nelle `SKILL.md` (D6 c). L'indirizzo della `Fonte:` di `rules-ai:35` non scatta (verificato: test verde, file non toccato).
- `tests/test_taskcmd.py`: `:142` e `:475` → `assertNotIn("model:", summary)` (D6 a); `test_models_override_in_summary` con dato `fable`, solo il primo avvio (righe 248-251), tolte le righe del giro 4 che ripetevano il test nuovo (D6 b); `test_rounds_four_five_new_implementer` → `model: opus`; `test_sixth_round_name_launch_inherit` → `test_sixth_round_name_launch_opus`; nuovi `test_fix_round_4_hints_opus` (senza `[review] models`, giro 4 `model: opus`, `MODEL_HINT == "opus"`, niente `inherit`) e `test_fix_round_4_uses_review_models` (`{"tollgate:implementer" = "fable"}`: primo avvio `model: fable` come in `:248-251`, giro 4 con nome `-r4` e `model: fable`, niente `opus` né `inherit`).
- `tests/test_brief.py:65-70`: `model_hint="opus"`, `model: opus`.
- `tests/test_b1_scripts.py:190`, `:753` → `"opus"`; `:569` → `"--model opus"`.
- `tests/test_eval_run.py:250` → `claude-opus-5-5`.

### RED

`python3 -B -m unittest tests.test_manifest tests.test_taskcmd tests.test_brief tests.test_b1_scripts tests.test_eval_run`, prima del codice:

```
FAIL: test_agent_models_by_role (...) (agent='final-database') ... 18 subtest, uno per agente
FAIL: test_agents_frontmatter
FAIL: test_audit_agents_frontmatter
FAIL: test_final_agents_frontmatter
FAIL: test_no_agent_on_sonnet (...) 8 subtest (i sonnet)
FAIL: test_no_sonnet_in_skills_and_scripts (...) skills/execute/SKILL.md, spikes/run-b1-flow.sh, spikes/b1/run-b1-checks.sh, evals/run.sh
FAIL: test_fix_round_4_hints_opus
FAIL: test_fix_round_4_uses_review_models
FAIL: test_rounds_four_five_new_implementer
FAIL: test_sixth_round_name_launch_opus
FAIL: test_checks_allowed_tools
FAIL: test_flow_allowed_tools
FAIL: test_flow_controlla_lists_steps
FAIL: test_always_no_publish
Ran 406 tests in 181.934s
FAILED (failures=41)
```

Unica eccezione: `test_fix_brief_includes_findings_in_fence` di `tests/test_brief.py` era già verde, perché `brief.implementer_brief` ripete il `model_hint` che riceve (è un dato del test, non un comportamento che cambia).

### GREEN

Stessi file più `tests.test_docs` (per la sezione nuova di `comandi.md`):

```
Ran 413 tests in 289.371s
OK
```

`claude plugin validate --strict .`: `✔ Validation passed`, `exit 0` (un avviso «plugin directory» sull'icona mancante e un consiglio sul README, già presenti prima e che non cambiano l'esito).

Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` in background, log `W/suite-task-1.log`:

```
== Python 3.11.16
Ran 4354 tests in 2682.299s
OK (skipped=13)
== Python 3.13.5
Ran 4354 tests in 1943.002s
OK (skipped=11)
exit 0
```

Nessun «unclosed» nel log (`/usr/bin/grep -c -i unclosed` = 0).

## File cambiati

`agents/` (18 file, riga `model:`), `bin/tollgate_flow/taskcmd.py`, `skills/execute/SKILL.md`, `spikes/run-b1-flow.sh`, `spikes/b1/run-b1-checks.sh`, `evals/run.sh`, `docs/uso/comandi.md`, `docs/uso/eval-e-ci.md`, `tests/test_manifest.py`, `tests/test_taskcmd.py`, `tests/test_brief.py`, `tests/test_b1_scripts.py`, `tests/test_eval_run.py`. Nessun file nuovo, nessun `__pycache__`, nessun file approvato toccato.

## Scostamenti dal piano

- Nessuno di sostanza. Forma del giro 4: due righe (`hint = …get(…)`; `if renamed: hint = hint or MODEL_HINT`) invece della riga unica proposta dallo scan, stesso comportamento dell'interfaccia del brief.
- `test_agent_models_by_role` controlla in più che ogni agente abbia un ruolo (copertura completa invece di sole due liste): costa nulla, e fa scattare il test se un agente nuovo nasce fuori da `readonly_agents` e dal nome `implementer-*`.
- In `comandi.md` gli esempi di alias sono solo `fable` e `opus`, per non riproporre sonnet nella documentazione.

## Autorevisione

- Completezza: tutte le righe dei «Fatti verificati» e dello scan (4-bis punto 2, «Task 1, giro 4», D5, D6, D11) coperte; `grep -rn "inherit\|sonnet"` su `docs/uso`, `README.md`, `bin`, `skills`, `hooks`, `templates`, `evals/*.sh`, `evals/*.py`: restano solo `rules-ai:35` (approvata, non fissa un modello), la frase storica sui punteggi sonnet in `eval-e-ci.md:42` e due menzioni volute in `comandi.md` («mai sonnet né haiku», «né `inherit`»).
- Fuori (decisione 14, «Fuori»): script e agenti storici di P3/P4/P5 e sonde, dati dei test (`hookkit.py`, `test_models*.py`, ecc.), `budget.tsv`: non toccati.
- Nessun `claude` vero oltre a `plugin validate --strict`; nessuna rete; nessun subagente.

## Dubbi

- Il valore di `[review] models` non è validato (`config.py:119`, mappa di stringhe): un progetto che scrive un ID completo o `inherit` lo vedrà proposto anche dal giro 4. La pagina d'uso lo dice; validarlo sarebbe fuori dal task.
- La frase su `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` in `comandi.md` («resta `CLAUDE_CODE_SUBAGENT_MODEL`, o quello della sessione») è dedotta dall'ordine delle precedenze della pagina, non letta testualmente: se il controller ha la pagina, conviene un controllo.
