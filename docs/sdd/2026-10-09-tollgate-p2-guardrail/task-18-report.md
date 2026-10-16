# Task 18 - Report

## Implementato
- `agents.py` (pre_agent), `send_message.py`, `subagent_start.py`, `post_agent.py`, `skills.py`, `handback.py` come da brief.
- Nuovo `prompt_submit.py` (carry): ordine 20, componente `task_budget`; senza `<task-notification>` o senza `stopped at its N-turn limit` esce vuoto; altrimenti `<task-id>` = `agent_id`.
- Helper condiviso `_common.budget_cut_records` (taglio: riga `cut`, task `budget_exceeded`, blocco `needs_you`, inject). Lo usano `post_agent` (primo piano) e `prompt_submit` (background e ripresa): una sola logica.
- Nessuna nuova operazione `record`: `apply.py` aveva già tutto.

## Scostamenti dal piano
- Il taglio passa da `budget_cut_records`, che legge task e lavoro dalla riga del subagente (non da `governing_work`); registra anche `tokens` (K2: `totalTokens` in primo piano, `<subagent_tokens>` nella notifica).
- `send_message` restituisce anche i record di interruzione dei subagenti fermi (il piano li scartava).
- `subagent_finish cut` solo se la riga è `running` (come nel piano): Task 19 non deve chiudere come `done` un subagente tagliato in primo piano prima di `PostToolUse Agent` (non c'è `SubagentStop` al taglio, E6).

## Test
- `tests/test_check_agents.py`: test del brief + `PromptSubmitCutTest` (testo di E7/E8 su busta `UserPromptSubmit-none`: nessun effetto su prompt normali/altre notifiche, taglio in background, dopo ripresa, agente ignoto/riga chiusa, task non running, componente spento), `PostAgentExtraTest` (async_launched, handback auto, token del taglio), `SendMessageExtraTest` (subagente mittente, sola lettura, altro scrittore vivo, scrittore fermo).
- `tests/test_subagents.py`: `is_stale` (last_seen, started, assenza di last_seen), `interrupt` no-op (non running, sconosciuto, task non running).
- RED: `python3 -B -m unittest tests.test_check_agents` prima dei moduli: `FAILED (failures=9, errors=13)`.
- GREEN: `PYTHONWARNINGS=error::ResourceWarning tests/run`: 587 test OK con python3.11 e python3 (3.13.5), output pulito.

## Dubbi
Nessuno bloccante.

## Dubbi aperti (per la revisione finale, non corretti)
- Race del lancio in parallelo: la riga entra in `subagents` solo a `SubagentStart`, quindi due `Agent` nello stesso messaggio passano entrambi `PreToolUse` (scrittore unico aggirabile).
- `take_pending(resume=True)` è fragile con più task dello stesso tipo: prende il primo `pending='resume'` per numero, non quello del subagente che riprende.

## Fix round 1
1. `prompt_submit`: il prompt (senza spazi iniziali) deve cominciare con `<task-notification>`; si spezza in blocchi; per ogni blocco `<task-id>` e `<summary>`, la frase `stopped at its N-turn limit` si cerca solo nel `<summary>`; un taglio per blocco. Test: due notifiche (normale + tagliata, e due tagliate), citazione a metà testo, frase solo in `<result>`, spazi iniziali.
2. Chiusura `cut` (con token) sempre; `budget_exceeded` e blocco `needs_you` solo con `task_budget` (dentro `budget_cut_records`). `prompt_submit` senza componente nel `CHECK`; `post_agent` non lo controlla più. Test: primo piano e background con `task_budget` spento -> `cut`, task `running`, nessun blocco.
3. `send_message`: il deny «un subagente non riprende un subagente che scrive» vale solo in `execution` L1/L2 (scostamento dal piano: fuori da execution non c'è scrittore unico da proteggere). Test.
4. `live_writers` esclude il target prima di calcolare i fermi: non viene interrotto subito prima della ripresa. Test.
- Test: `python3 -B -m unittest tests.test_check_agents` RED con 8 fallimenti prima dei fix, poi 30 OK. `PYTHONWARNINGS=error::ResourceWarning tests/run`: 595 test OK con python3.11 e python3; `python3.11 -B -W error::ResourceWarning -m unittest discover -s tests -t .` OK.
