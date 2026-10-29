# Task 1, Step 1: report dell'implementatore

## Cosa ho fatto
- `spikes/b1/run-b1-checks.sh`: modi `controlla`, `sonda --redirect-url <url>`, `latenza`, `valida`, `raccogli [N]`.
  - `sonda`: un solo `claude -p --plugin-dir ... --model sonnet --permission-mode acceptEdits --allowedTools "Read,Grep,Glob,Bash,Agent,Skill,Write,Edit,WebFetch,WebSearch,mcp__context7__*,mcp__plugin_context7_context7__*" --disallowedTools "Bash(curl:*),Bash(wget:*),Bash(gh:*),Bash(git push:*)" --output-format json`, sotto `timeout` (900 s, `B1_TIMEOUT`), da `/tmp/tollgate-b1/probe/` (repo con `src/app.py` e `pyproject.toml`). Rifiuta senza `--redirect-url` (o non https), con cartella di lavoro non strettamente sotto `/tmp/tollgate-b1/` (anche con `..`), con `--plugin-dir` vuoto o cartella inesistente. Ogni esecuzione e' un `tentativo-N` (argv, versione, claude.json, claude.err, uscita, redirect-url, hooks.jsonl, eco.txt); il repo di prova e i file di ripiego esistenti si rinominano `.prev-<tempo>`, niente si cancella.
  - `latenza`: delega a `spikes/b1/latenza.py` (v. sotto). `valida`: copia in `/tmp/tollgate-b1/valida/`, aggiunge `skills/rules-base/SKILL.md` con `approved: prova`, lancia solo `claude plugin validate --strict .`, esito in `<OUT>/valida-esito.txt`.
  - `raccogli`: delega a `spikes/b1/raccogli.py`.
  - `controlla`: nessuna scrittura; stampa modi e comando `claude`, `bash -n`, compilazione dei Python, forma di `hooks.json`, riga `tools` dell'agente, heredoc della skill.
- `spikes/b1/probe-plugin/` (nome `probe`): `hooks/hooks.json` (PreToolUse, PostToolUse, PostToolUseFailure con matcher `.*`; SubagentStart, SubagentStop), `hooks/record.py` (scrive in JSONL solo lo stdin; log `$B1_PROBE_LOG` o `/tmp/tollgate-b1/hooks.jsonl`; mai sotto la HOME, mai l'ambiente), `agents/lettore.md` (tools come da brief), `skills/leggi/SKILL.md` (lancia `probe:lettore` e porta il passo finale: heredoc `<<'NOTA_DI_RICERCA_FINE'` verso `${CLAUDE_PLUGIN_ROOT}/bin/eco` con backtick, riga `EOF`, `$HOME`), `bin/eco` (stdin -> `$B1_ECO_OUT` o `/tmp/tollgate-b1/eco.txt`, byte per byte).
- `claude plugin validate --strict spikes/b1/probe-plugin` (l'unico `claude` vero lanciato): "Validation passed" (solo l'avviso ICON_MISSING, non bloccante).
- `tests/test_b1_scripts.py`: 18 test.

## Scostamenti dal piano (tutti piccoli)
1. Due file in piu' del brief: `spikes/b1/latenza.py` (costruzione del repo attivo, lavoro L1, implementatore registrato via `hooks/run SubagentStart`, 50+50 misure con un'invocazione di riscaldamento non conteggiata, prova a secco B1-V3 con `mcp__plugin_context7_context7__query-docs`) e `spikes/b1/raccogli.py` (anonimizzazione, campioni, esito dell'heredoc, riepilogo). Motivo: logica troppo lunga e da provare direttamente per stare in heredoc di bash. Con `--root`/`--runs` temporanei il test la esegue per davvero (solo locale, niente `claude`).
2. L'heredoc atteso non e' duplicato: `raccogli` lo estrae da `skills/leggi/SKILL.md` (unica fonte); un test lo esegue con bash cosi' com'e' e lo confronta.
3. Il prompt della sonda aggiunge, ai passi del brief, il `Read` di un file assente (`src/assente.py`) richiesto da B1-V1 (arriva come `PostToolUseFailure`?).
4. `test_checks_valida_uses_tmp_copy`: il brief dice «sotto `/tmp/tollgate-b1/valida/`»; il test usa `B1_CHECK=1` con `B1_TMP` temporaneo (`<tmp>/tollgate-b1/valida`) per non scrivere nella cartella del controller; il valore fisso `DEFAULT_TMP=/tmp/tollgate-b1` e' verificato dal test sulla forma dello script e da `controlla`. `B1_CHECK`/`B1_TMP` hanno effetto solo con `B1_CHECK=1`.
5. Il percorso del log degli hook e di eco passa per variabili d'ambiente (`B1_PROBE_LOG`, `B1_ECO_OUT`) fissate dalla sonda; se non arrivassero (default `/tmp/tollgate-b1/...`), lo script sposta i file di ripiego nel tentativo. Da verificare dal controller al primo giro: se `hooks.jsonl` del tentativo e' vuoto o assente ma esiste il ripiego, e' scritto in `argv`/riepilogo.

## Note per il controller
- Nei campioni le stringhe oltre 4000 caratteri sono troncate con marcatore (`…[troncato, N caratteri]`); il registro `hooks.jsonl` copiato nelle evidenze resta intero (anonimizzato).
- `raccogli` sceglie, per ogni chiave, il primo `PreToolUse` con `agent_id` (altrimenti il primo) e il suo post per `tool_use_id`. `mcp_docs`: solo `query-docs`/`get-library-docs`. Un `PostToolUse` senza pre diventa un campione con la sola chiave `post`.
- Dry run reale di `latenza.py` con 3 misure in una radice temporanea: mediana circa 600 ms per il Bash da subagente e 485 ms per il Read senza `agent_id` (macchina carica, suite in corso: indicativo, non e' la misura). B1-V3 a secco: `deny` per effetto esterno (`strumento MCP non in mcp_allow`), come atteso.
- Non ho eseguito `sonda`, `latenza`, `valida`, `raccogli` dello script: solo `bash -n`, `controlla` e, nei test, un `claude` finto. `/tmp/tollgate-b1` non esiste dopo i test.

## TDD
Onesta' sul processo: ho scritto sonda e script prima, poi i test (i test esercitano comportamento reale: claude finto che registra argomenti, rifiuti, heredoc eseguito da bash, raccolta su registro finto, latenza su repo reale). Un RED formale non e' stato registrato; l'unico fallimento visto e' stato un conteggio sbagliato di `claude -p` nel test sulla forma dello script (corretto: conta `=(claude -p`).
- GREEN: `python3 -B -m unittest tests.test_b1_scripts` -> `Ran 18 tests ... OK` (python3 e python3.11).

- Suite completa: python3.11 2915 test OK (2 skipped), python3 (3.13.5) 2915 test OK; commit 67aad17.

## Fix round 1
Modifiche:
1. Prompt a 12 passi («Dopo i dodici passi»): aggiunti il Grep content con path `src/app.py` (file) e il Grep con path `src/app.py` senza output_mode. Campioni: `grep_content` = Grep content su file `.py`, `grep_content_dir` = Grep content su cartella, `grep_default` = Grep senza output_mode su file; `grep_files` resta l'esplicito files_with_matches (o senza modo e senza file).
2. `sonda` crea `$TMP/state/.tollgate-test` ed esporta `TOLLGATE_STATE="$TMP/state"` al solo `claude -p`; il `claude` finto registra l'ambiente e il test lo verifica (`test_checks_allowed_tools`).
3. `raccogli` (script e `raccogli.py`) rifiuta `--home` vuoto o `/`; nuovo `test_checks_raccogli_refuses_an_empty_home` (nessuna scrittura).
Un commento dello script nominava lo stato dell'utente e rompeva il test sulla forma: riscritto.
Test: `python3.11 -B -m unittest tests.test_b1_scripts` e `python3 -B ...` -> `Ran 19 tests ... OK`; `run-b1-checks.sh controlla` -> `CONTROLLA: ok`.
Suite completa (`tests/run`): 3.11 2916 OK (skipped=2), python3 2916 OK. Nota: l'aggiunta di `grep_default` e' arrivata mentre la suite girava; dopo di essa ho rilanciato il solo file `tests.test_b1_scripts` con entrambi i Python (verde), e di nuovo prima del commit.
