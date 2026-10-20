# Esiti delle verifiche P3c

Versioni: Claude Code 2.1.304 (`claude --version`), gh 2.46.0 (2025-01-13, Debian 2.46.0-3, `gh --version`). Data: 20 ottobre 2026.

Piano: `docs/superpowers/plans/2026-10-20-tollgate-p3c-percorso-l2.md` (Task 1, decisione 22). Spec: revisione 23. Nessuna rete e nessun `claude -p`: solo `claude --version` e `gh --version`.

Verifiche nuove: nessuna; la prova reale del Task 14 è il controllo. I giri dell'audit sono in sequenza (il metodo corregge il documento tra un giro e l'altro), quindi non serve provare subagenti avversari in parallelo. I fatti usati sono già provati in P0, P3a e P3b; se la prova reale (Task 14) ne smentisce uno, il difetto si corregge lì.

| Fatto | Dove è provato | Dove incide in P3c |
|---|---|---|
| `SubagentStop` con `last_assistant_message` | `docs/verifiche/2026-10-08-p0-esiti.md`, sezione «Hook (claude -p)», E1 (secondo `SubagentStop` con `last_assistant_message: "due"`, ripresa con `SendMessage`) e E2 (controprova in `manual`, primo piano: `last_assistant_message` presente). Limite: in auto mode manca (E2) | Task 6 (report dei giri a `SubagentStop`): il testo dell'auditor si legge da `last_assistant_message` quando c'è |
| `SubagentHandback` | `2026-10-08-p0-esiti.md`, sezione «Hook (claude -p)», E2: in `--permission-mode auto` il subagente chiude con `SubagentHandback` (`tool_input: {"message": ...}`, visto da `PreToolUse`/`PostToolUse` con `agent_id` e `agent_type`) | Task 6: fonte del report in auto mode, dove `last_assistant_message` manca |
| `agent_type` dei plugin | `2026-10-08-p0-esiti.md`, sezione «Hook (claude -p)», E5 e E6 (agenti `hookprobe:probe-agent` e `hookprobe:probe-turns`); evidenza grezza in `docs/verifiche/evidenze/hook/e5.jsonl` e `e6.jsonl` (`"agent_type":"hookprobe:probe-agent"`, `"hookprobe:probe-turns"`). Nelle sessioni interattive compaiono anche `SubagentStop` con `agent_type: ""` (sezione «Interattivi», «Fatto in più») | Task 6 e Task 13: l'hook riconosce gli agenti auditor di `tollgate` da `agent_type` e ignora quelli con tipo vuoto |
| `UserPromptExpansion` con `command_args` per le skill con `disable-model-invocation` | `2026-10-08-p0-esiti.md`, sezione «Hook (claude -p)», E4 (forma lunga e breve, con `command_name` e `command_args`); sezione «Interattivi», I2 (stesso esito in sessione interattiva) | Task 7 e Task 8 (`approve spec`, `approve plan`, `reopen`): l'atto dell'utente si legge da `command_name` e `command_args` |
| `${CLAUDE_PLUGIN_ROOT}` espansa nelle skill | `docs/verifiche/2026-10-16-p3a-verifiche.md`, V1 (esito sì; conseguenze, riga V1) | Task 13: le skill nuove scrivono `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` |
| `EnterWorktree` | `2026-10-08-p0-esiti.md`, sezione «Interattivi», I3 (accetta un worktree esistente, `tool_input: {"path": ...}`) | Task 13 e Task 14: le skill del percorso L2 entrano nel worktree del lavoro |
| `Agent` lanciato da una riga `agente:` | `docs/verifiche/2026-10-19-p3b-prova-flusso.md`, sezione «Passi ed esiti» (revisore finale `tollgate:final-reviewer` lanciato in primo piano da una riga `agente:` di `review prepare`, brief letto dal percorso) | Task 5 (`audit prepare` stampa la riga `agente:`) e Task 13 (agenti auditor) |
| `gh`: nessun campo JSON nuovo | `docs/verifiche/2026-10-19-p3b-verifiche.md`, G2-G5 (opzioni e campi già usati da `gh.py`; nomi dei campi JSON non verificabili dall'aiuto di 2.46.0, controllo reale al primo uso) | P3c non aggiunge chiamate a `gh` con campi nuovi. Le issue delle fette le crea l'agente con il proprio comando dopo `approve effect`, non il codice (decisione 22) |

Annotazione: le versioni di Claude Code sono diverse tra le prove (P0: 2.1.294; P3b: 2.1.304; oggi: 2.1.304). I fatti di P0 sono stati ritrovati in uso reale in P3b (agenti del plugin, hook a `SubagentStop`), ma non rieseguiti su 2.1.304 uno per uno: il Task 14 è il controllo.

Fatti non trovati: nessuno. Ogni voce della decisione 22 ha una prova citata sopra.
