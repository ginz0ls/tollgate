# Task 16 — giro 5: ritentativi per le scritture idempotenti (cautele invariate: task-16-fix4.md e cautele.md)

## Esito reale (22/10/2026, protected aggiornato al giro 4, commit e75adcb del repo di prova)
Ripetuti 5 casi: 4 riusciti; `verde-config` (PR 92) fallito: il job guard esce con `gate guard: gh api --method: unexpected end of JSON input` (uscita 1) senza pubblicare `tollgate/guard`. La lettura `commits/<sha>/pulls` è passata; è fallita una scrittura (GitHub 500 a corpo vuoto, come sulle letture), che dal giro 4 giustamente non si ritenta.

## Ruling del controller
Si ritentano anche le scritture **idempotenti**, dichiarate esplicitamente da chi chiama, mai dedotte dagli argomenti:
- `ghcli.api(..., retry=True)` (nuovo parametro, default `False`): con `retry=True` una chiamata non GET si ritenta alle stesse condizioni del giro 4 (stessi transitori, stessi 3 tentativi, stesse attese, stesso errore finale). Le GET restano ritentate come oggi a prescindere dal parametro. `run_json*` invariati.
- Lo usano solo:
  - `github.set_status` (POST `statuses/<sha>`: per lo stesso SHA e contesto vale l'ultimo stato; ripubblicare lo stesso stato non cambia l'esito);
  - il PATCH di un commento esistente in `github.upsert_comment` (`issues/comments/<id>`: riscrive lo stesso testo).
- Restano senza ritentativo: POST di un commento nuovo (`comment_issue`), `create_issue`, e tutto il resto (un doppio commento o una doppia issue non sono innocui). Commento nel codice di una riga sul perché.
- Un solo punto che decide (lo stesso helper del giro 4, con il parametro in più).

## Test (prima rossi)
- `api(method="POST", retry=True)` con 500 poi ok → ritorna, 2 chiamate; sempre 500 → `GhError` di oggi, 3 chiamate; `retry=False` (default) con 500 → 1 chiamata.
- `set_status` con un 500 a corpo vuoto (`unexpected end of JSON input`) poi ok → stato pubblicato; `comment_issue`/`create_issue` con 500 → 1 chiamata, `GhError`.
- `upsert_comment` su commento esistente: PATCH 500 poi ok → aggiornato; senza commento esistente: POST 500 → nessun ritentativo.
- Guard (`tests/test_gate_guard.py`): POST di `tollgate/guard` 500 una volta poi ok → `success` pubblicato.

Suite verde con `tests/run` su python3.11 e python3. Commit nuovo «tollgate P4: ritentativi anche per stati e modifiche di commenti, scritture idempotenti (Task 16, giro 5)» con la riga esatta «Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>». Sezione «Giro 5» nel report; rispondi solo con stato, commit, una riga sui test, dubbi.
