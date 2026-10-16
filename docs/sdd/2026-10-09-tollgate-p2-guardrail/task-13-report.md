# Task 13 — report

**Commit:** `f79ed8d` tollgate P2: wrapper hooks/run, hooks.json, plugin.json, interruttore off/on
**Ramo:** p2-guardrail (worktree p2-guardrail)

## Implementato

- `hooks/run` (eseguibile, 755): wrapper di ogni hook. Ordine: UserPromptSubmit senza `<task-notification>` esce 0 subito; `UserPromptExpansion` con `tollgate:off` / `tollgate:on` (senza Python né DB); OFF attivo con scadenza passata (riaccensione e riga `off.log`); repo non attivo (`tollgate.toml` su `origin/<defaultBranch>`, `origin/HEAD`, `origin/main`, `origin/master`, oppure segnalino `bound/<sessione>`); Python >= 3.11 (`python3`, `python3.13`, `python3.12`, `python3.11`); esecuzione di `bin/tollgate hook <evento>` con cane da guardia a `timeout_s + 2` (lettura da `tollgate.toml` sul riferimento remoto con `awk`, default 20); uscite: 0 e 2 passano, errori di PreToolUse diventano 2, errori degli altri eventi diventano 0 con avviso; log in `hook-errors.log`.
- `hooks/hooks.json`: sette eventi, `timeout: 90`. `PreToolUse` e `PostToolUse` con i matcher del brief. `UserPromptSubmit` senza matcher (carry).
- `.claude-plugin/plugin.json`: `version` 0.1.0 (uguale a `tollgate_core.VERSION`); dipendenza superpowers senza `version` e senza `license`/`author` (carry).
- `skills/off/SKILL.md`, `skills/on/SKILL.md`: `disable-model-invocation: true`.
- `tests/test_wrapper.py` (14 test), `tests/test_manifest.py` (4 test). Solo `TempState` (`TOLLGATE_STATE` con sentinella), nessun `claude`, nessuna rete.

## TDD

RED: `python3 -B -m unittest tests.test_wrapper tests.test_manifest` prima dell'implementazione:

```
Ran 18 tests in 0.018s
FAILED (failures=1, errors=17)
```

Gli errori sono i file mancanti (`hooks/run` copiato in `setUp`, `hooks.json`, `plugin.json`); il fallimento è `test_wrapper_executable`.

GREEN: stesso comando dopo l'implementazione:

```
Ran 18 tests in 5.243s
OK
```

Suite completa, `tests/run`:

```
== Python 3.11.16   Ran 396 tests in 17.957s   OK
== Python 3.13.5    Ran 396 tests in 17.980s   OK
```

378 precedenti più 18 nuovi.

## Scostamenti dal brief e da carry.md

1. `json_str`: la `sed` del brief usa `.*` iniziale, quindi prende l'**ultima** occorrenza sulla riga. Sostituita con `awk` (`match()` restituisce la prima occorrenza). Test `test_json_str_takes_first_occurrence`: `cwd` di primo livello non attivo, `cwd` annidato in `tool_input` attivo; deve vincere il primo. `awk` è in `TOOLS` del test, `grep` no.
2. `off <ore>`: `^[0-9]+$` su `command_args`, poi `10#$ARGS`. Test con `08` (8 ore, tolleranza 60 s, messaggio «spento per 08 ore») e `0.5` (nessuna scadenza, `OFF` vuoto, avviso «non è un numero intero di ore»).
3. Decisione mia: `off` senza argomenti spegne senza avviso (non è un errore); l'avviso compare solo con argomento non valido. Il brief non lo specificava: da confermare.
4. `off 0` è accettato come intero valido: scade subito (`until` = adesso). Non l'ho bloccato perché il carry non lo prevede. Da confermare.
5. `off.log`: una `printf >>` per riga, senza `sed` né descrittori aperti. Formato `<ISO> off[ <until>]` / `<ISO> on`, compatibile con la regex di `offlog._LINE`.

## Concern

- Il cane da guardia (decisione 4) lascia un `sleep` orfano per al massimo `timeout_s + 2` secondi anche quando il hook è finito prima, perché `kill` colpisce solo la subshell. Ha `stdin`/`stdout`/`stderr` su `/dev/null`, quindi non tiene aperta la pipe di Claude Code, ma è un processo residuo. Ho seguito il brief; una versione che chiude anche il `sleep` richiederebbe più shell per un beneficio piccolo.
- Il percorso con il timeout reale (`mode=sleep`) richiede circa 3 s di attesa nei test: il tempo totale della suite cresce di poco.

## Non fatto

- `claude plugin validate` non è stato lanciato (vincolo di cautela: nessun `claude` nei test né contro la configurazione dell'utente).
- Nessun test del wrapper contro `~/.local/state/tollgate`: tutti i test usano `TempState`.

## Fix round 1

**Commit:** `1697e59` tollgate P2: wrapper, fix round 1 (messaggi off/on su stdout JSON, ore 1-9999, timeout_s, cane da guardia)

Cambiamenti in `hooks/run`:

1. **Messaggi off/on su stdout JSON** (rami `tollgate:off` e `tollgate:on` di UserPromptExpansion): un solo oggetto `{"systemMessage", "hookSpecificOutput": {"hookEventName", "additionalContext"}}`, uscita 0. Escape di `\` e `"` in `expansion_json`, più rimozione dei caratteri di controllo. Lo stderr resta solo per il messaggio di salto con OFF attivo (come chiesto). `on` risponde anche quando tollgate era già acceso.
2. **Ore**: `^[0-9]{1,4}$` e valore >= 1. `0`, `0000`, `99999999999999999999`, `2h`, `-1`, `0.5` danno «non è un numero intero di ore (1-9999)» senza scadenza; `1` e `9999` sono accettati.
3. **`timeout_s`**: `match()` su `=[[:space:]]*[0-9]+`, quindi `timeout_s = 5 # max 30` dà 5. Tetto a 85 (`TIMEOUT`).
4. **Sleep orfano**: il guardiano installa il `trap TERM` prima di `sleep N & SP=$!`; quando il wrapper lo ferma a fine hook, il trap uccide `SP`.
5. **Pipe chiuse in fretta**: test di regressione con `timeout_s = 1` e hook veloce, sotto 2 s.

Cambiamento aggiuntivo, non nell'elenco: `json_str` decodifica le sequenze `\"` e `\\`. Il test del messaggio con virgolette e backslash falliva per il motivo sbagliato (il valore veniva troncato alla prima `\"`).

### TDD

RED (`python3 -B -m unittest tests.test_wrapper`, prima del fix): `FAILED (failures=5, errors=8)` su 22 test. Falliscono: i messaggi su stdout (errori JSON), le ore `0`, `0000`, `99999999999999999999`, `2h`, `-1`, il timeout con commento (errore), il tetto a 85 e lo sleep orfano (`sleep 39`). Passano già, e restano come regressione: i bordi `1` e `9999` e la chiusura rapida delle pipe.

Nota sul RED: il test del tetto a 85 ha lasciato un `sleep 902` orfano (il codice vecchio non lo uccideva); l'ho terminato a mano prima del GREEN. Nessun orfano dopo il fix.

Bug del test trovato durante il GREEN: il payload era inviato solo in `communicate()`, mentre il wrapper aspetta lo stdin con `cat`. Il test ora scrive lo stdin e lo chiude prima di controllare `pgrep`.

GREEN (`tests.test_wrapper tests.test_manifest`): `Ran 26 tests ... OK`.

`tests/run`:

```
== Python 3.11.16   Ran 404 tests in 27.299s   OK
== Python 3.13.5    Ran 404 tests in 27.750s   OK
```

404 = 396 precedenti più 8 nuovi test del wrapper.

`skills/off/SKILL.md` non è cambiata: la skill può continuare a chiedere di riferire il messaggio, che ora arriva come `additionalContext`.
