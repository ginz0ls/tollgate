# Report Task 8 (brief dell'implementatore e del revisore)

## Implementato
- `bin/tollgate_analysis/brief.py`: `ImplBrief.research_cmd`, `.research_note_path`; `ReviewBrief.research`, `.research_enforced`, `.research_note`, `.research_note_path`, `.first_diff_file` (tutti con predefinito). Sezione «Nota di ricerca» dell'implementatore prima di «Istruzioni» (sezioni dalle costanti di `research`, comando in `_block`, nei giri `--fix` la frase sul percorso della nota). Sezione del revisore solo con `research` vero: nota in `_block` dopo `DATA_NOTE`, oppure «(nessuna nota consegnata)»; gravità `major` + `missing` (acceso) o `moderate` senza `missing` (spento); `file` = percorso della nota, o primo file del diff se manca; `line` 1. Il modulo resta puro (importa solo `research`, sorella).
- `bin/tollgate_flow/taskcmd.py`: `_research_on` (`research.active` con il componente `research_note`, D2), `_rules_enforced` (legge `db.BIN_PATH.parents[1] / research.RULES_BASE`), percorso della nota da `research_cmd.note_path` (D17), nota letta con `lookups.note`; `first_diff_file` = primo `Change.path` del diff.
- `bin/tollgate_checks/subagent_start.py`: frase «Prima di modificare file consegna la nota di ricerca (vedi il brief).» solo se `research.active(...)`; non importa `tollgate_flow`.
- `agents/task-reviewer.md`: punto nella Parte 1 sulla sezione «Nota di ricerca» (regola `nota di ricerca`, «Nessuna fonte esterna», gravità e `file`/`line` dal brief).

## Test
Aggiunti: `test_brief.py` (ImplementerResearchTest, ReviewResearchTest: i sei del brief più il caso nota esistente), `test_taskcmd.py` (research_cmd, legacy, componente spento sia brief sia revisione, fix, review con nota/senza nota/interruttore acceso con radice del plugin temporanea), `test_check_agents.py` (promemoria, legacy, componente spento), `test_manifest.py::test_task_reviewer_checks_note`.
Nessun test esistente modificato (solo aggiunte e import).

## Evidenza TDD
Scritti i test di `test_brief.py` prima del codice; poi il codice di brief.py e il resto. Non ho conservato l'output del RED per ogni file: dichiaro che il RED è stato osservato solo indirettamente (primo giro di `test_brief` con 2 fallimenti di formulazione, corretti). GREEN: `python3 -B -m unittest tests.test_brief tests.test_taskcmd tests.test_check_agents tests.test_manifest tests.test_layers` verde.

## Scostamenti
- Frase del giro `--fix` preceduta da «Giro di correzione:» (il brief la cita in minuscolo dopo i due punti).
- `skills/rules-base/SKILL.md` non esiste ancora: l'interruttore è spento nel repo (come previsto, Task 10/B2); il test dell'interruttore acceso usa una radice del plugin temporanea.

## Suite
tests/run: python3.11 3104 test OK (2 skipped), python3 3104 test OK, exit 0 entrambi.
