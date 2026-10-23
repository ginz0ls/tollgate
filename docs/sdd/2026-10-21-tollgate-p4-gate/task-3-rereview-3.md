# Task 3: ri-revisione del giro di correzione 3

Verifiche con `python3 -B -c` su `bin/tollgate_analysis/workflows.py` (fcd85e1 e successivi) e PyYAML 6.0.1 per confermare la lettura di un parser.

### Verdetti sui rilievi
**I-2 (A): un tag YAML davanti alla stringa nasconde l'escape (`on: [push, !!str "pull_request_\x74arget"]`, voce di elenco, `!!str "\x73tatuses": write`, in flusso, tag verbatim `!<...>`)** — INDIRIZZATO. `_TAG` (`workflows.py:21`, uso a `:159`) dà rosso «tag YAML» su tutte le cinque forme; PyYAML conferma che sono evasioni reali (`pull_request_target`, `statuses: write` letti dal parser).
**I-2 (B): `statuses:<TAB>write` e `{checks:<TAB>write}` restano verdi** — INDIRIZZATO. `_SCOPE` (`:14-15`) accetta `[ \t]` e dà rosso su entrambe.

### Danni nuovi nel diff della correzione
**Important** — `workflows.py:90-94` (+ `_BLOCK_HEADER` `:25`). L'esenzione dei «blocchi» non è limitata agli scalari a blocco reali: `_BLOCK_HEADER` riconosce `[:-]\s+[|>]` a fine riga anche quando YAML non vede un blocco (qui `|` è parte di uno scalare semplice). Le righe seguenti più rientrate vengono saltate con `continue`, quindi non solo escono dalle regole su tag/àncore/alias, ma **non passano nemmeno per lo scanner degli escape** (`_escape_lines`). Evasione in contesto di flusso su più righe, verde e letta da PyYAML come `statuses: write`:

```
permissions: {contents: read, a: b - |
  , "\x73tatuses": write}
```
→ `problems()` = `[]`; `yaml.safe_load` = `{'permissions': {'contents': 'read', 'a': 'b - |', 'statuses': 'write'}}`.
Stesso schema, con tag davanti (`, !!str "\x73tatuses": write`) e per gli eventi (`on: {push: {}, a: b - |` / `  , !!str "pull_request_\x74arget": {}}`): verdi, e PyYAML legge `pull_request_target`. Quindi il guard lascia passare `statuses: write` e `pull_request_target`, cioè proprio ciò che la decisione 15 vuole bloccare. Il salto delle righe «a blocco» nello scanner degli escape c'è dal round 2 (`:92`); il round 3 lo estende a tag, àncore e alias, ma la falla è la stessa: il rilevamento del blocco è troppo largo. Il vincolo di fail-closed richiede che l'esenzione valga solo per uno scalare a blocco certo.
Indicazione di correzione: l'intestazione di blocco va accettata solo se la riga è una chiave/voce in contesto a blocchi (non dentro `[`/`{` aperti: tenere un contatore di profondità di flusso nello scanner, fuori dalle stringhe) e se `|`/`>` è preceduto da `:` o `-` come valore dell'intero nodo, non da testo (`b - |`); in alternativa, dentro i blocchi continuare comunque a segnalare gli escape quando la riga non è davvero un blocco, o mantenere rosso se compare un `|`/`>` finale in una riga con flusso aperto. Aggiungere test con `a: b - |` + riga di continuazione in flusso.

Varianti provate e **non** evasioni: blocco `run: |2` con contenuto `&x y` (blocco vero, PyYAML lo legge come testo); un `key: |` il cui blocco finisce prima (riga meno rientrata `&a b: 1` dopo il blocco: rosso); `! grep` e `cp *.txt` in un `run: |` vero (verdi, giusto). Un header in scalare semplice a blocchi (non flusso) non nasconde nulla perché la continuazione non può contenere `: `.

### Osservazioni fuori ambito
- PyYAML rifiuta la tabulazione dopo `:` (B1/B2): comunque rosso qui, nessun problema.
- Un job chiamato `checks`/`statuses` verde (già dichiarato nel report).

### Verdetto
**Giro di correzione:** Rilievi ancora aperti. A e B sono indirizzati, ma l'esenzione degli scalari a blocco apre un'evasione Important (scalare semplice che finisce con ` - |` in un flusso su più righe: le righe seguenti saltano escape, tag e àncore; evasione confermata per `statuses: write` e `pull_request_target`).
