# Ri-revisione Task 3, giro di correzione 2 (61d2d9c)

### Verdetti sui rilievi

**I-2 — `workflows.problems` fail-closed su escape in stringhe a doppie virgolette (forme su più righe, chiave con `:` a capo, continuazione `\`)**: NON INDIRIZZATO per una evasione residua (tag YAML); le quattro varianti del giro 1 sono invece chiuse.

Provato con `python3 -B` su `problems()`:
- Rossi, correttamente: `on: [` con la stringa su righe separate; `on:` + a capo + `[push, "pull_request_\x74arget"]`; `permissions: {` con `"\x73tatuses"` e `:` sulla riga dopo; `"stat\` + `  uses": write`. Rossi anche CRLF, CR soli, `'` dentro `"…"` e `"` dentro `'…'`, `#` dentro una stringa, escape dopo tabulazione, stringhe a virgolette doppie dopo `!!str`+a capo.
- Scalari a blocco: `on: |` / `on: >` con `pull_request_target` sotto sono rossi (`_EVENT` guarda ogni riga, scalari a blocco compresi); `statuses: |`, `|-`, `>` sono rossi (il valore `|`/`>` non è in `SAFE_VALUES`). Non è evasione. Costo: un `statuses: |` con `read` sotto è rosso (fail-closed, accettabile).
- `''` raddoppiato (`'stat''uses'`, `'pull_request_''target'`): verde ma corretto, la chiave letta è `stat'uses`, non `statuses`.

**Evasione residua A (Important): tag YAML davanti alla stringa.** Il testo è YAML valido; PyYAML lo legge come evento o permesso vietato; `problems()` restituisce `[]`:
1. `on: [push, !!str "pull_request_\x74arget"]` -> `{on: [push, pull_request_target]}`.
2. `on:` / `  - !!str "pull_request_\x74arget"` -> idem.
3. `permissions:` / `  !!str "\x73tatuses": write` -> `{statuses: write}`; vale anche in flusso `{!!str "\x73tatuses": write}` e col tag verbatim `!<tag:yaml.org,2002:str> "…"`; e come chiave di `on` (`!!str "pull_request_\x74arget":`).
Causa: `_escape_lines` apre le virgolette solo se il carattere prima è in `_NODE_START` (`-:[{,?`) o a inizio riga (`bin/tollgate_analysis/workflows.py:96-103`); con un tag davanti il carattere precedente è la fine del tag (`r`, `>`) e la stringa non si apre, quindi l'escape non si vede. `_ANCHOR` (`workflows.py:21`) copre `&` e `*` ma non `!`. Correzione semplice: rosso per qualunque tag (`!` a inizio nodo, stessa regola di `_ANCHOR`), oppure aprire la stringa dopo un tag.

**Possibile evasione B (da confermare, Important se confermata): tabulazione dopo i due punti.** `permissions:` / `  statuses:<TAB>write`, `permissions: {statuses:<TAB>write}`, `checks:<TAB>write` restano verdi: `_SCOPE` vuole `[ ]+` dopo i due punti (`workflows.py:15`), `_TAB_INDENT` guarda solo il rientro. PyYAML (YAML 1.1) rifiuta il file, quindi non l'ho potuto confermare come lettura di GitHub; il parser YAML 1.2 (go-yaml) ammette la tabulazione come spazio di separazione dopo `:`, quindi è probabile che GitHub lo legga come `statuses: write`. Il caso `on:<TAB>pull_request_target` è rosso (`_EVENT`), solo i permessi sono scoperti. Fix a basso costo: `[ \t]+` in `_SCOPE`, oppure rosso per qualunque tabulazione fuori da stringhe.

Casi verdi legittimi controllati (non sono evasioni): `\x73tatuses` in uno scalare semplice (nessun escape in YAML), scalari semplici/virgolettati su più righe senza `\` (si ripiegano con uno spazio), NBSP, larghezza zero, form feed.

### Danni nuovi nel diff della correzione
Nessuno. Falsi positivi: `\` in un valore ordinario `name: "a\tb"` è rosso per scelta del ruling; `run:` non è rosso.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti: I-2 (evasione A, tag YAML `!!str`/`!<…>` davanti a una stringa con escape; evasione B da confermare, tabulazione dopo `:` in `statuses`/`checks`). Le quattro varianti del giro 1 e gli scalari a blocco sono chiusi.
