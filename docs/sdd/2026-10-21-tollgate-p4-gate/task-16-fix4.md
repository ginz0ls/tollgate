# Task 16 — giro 4: errori transitori 5xx di GitHub nelle letture di `gh api`

Cautele invariate (leggi anche `cautele.md` in questa cartella): solo `bash -n`, `controlla`, test offline con gh finto; mai rete, mai gh vero, mai `claude`, mai ~/.claude/settings.json o ~/.claude/plugins/, mai ~/.local/state/tollgate. Le evidenze in docs/verifiche/evidenze/gh-p4/ NON si toccano. Niente subagenti. Niente `git add -f`, niente commit dei report, niente amend, niente stash, niente reset. tests/run in primo piano con un ciclo `until` se serve attendere: non restare fermo in attesa di notifiche.

## Che cosa è successo (esito reale, prova del 22/10/2026 sul repo protected)
Su 7 casi ripetuti, 5 sono falliti perché il job `tollgate-guard` è uscito con
`gate guard: gh api --paginate: unexpected end of JSON input` (uscita 1) prima di pubblicare `tollgate/guard`; in 2 casi anche `tollgate/verdict` è finito `error`. La chiamata è `github.shared_sha_prs` → `prs_for_commit` → `gh api --paginate --jq … repos/<slug>/commits/<sha>/pulls?per_page=100` (`bin/tollgate_gate/github.py:201`). Il controller l'ha riprodotto in sola lettura: lo stesso endpoint risponde a volte `HTTP/2.0 500 Internal Server Error` con `Content-Length: 0` e, alla richiesta subito dopo, `200` con il corpo atteso. Con `--paginate --jq` gh 2.46 riporta il 500 a corpo vuoto come `unexpected end of JSON input`; senza `--paginate` lo riporta come `HTTP 500` nello stderr. Il gate così resta chiuso (direzione sicura) ma la PR non si sblocca da sola: è un difetto di robustezza del prodotto.

## Ruling del controller (da applicare)
In `bin/tollgate_core/ghcli.py` le **letture** ritentano sugli errori transitori del server; le scritture no.
- Lettura = `api(...)` con `method == "GET"`, e `run_json_lines`/`run_json` quando gli argomenti cominciano con `api` e non contengono `--method`/`-X` (le usa `bin/tollgate_flow/gh.py`). Non si ritenta nient'altro (`pr create`, `pr merge`, POST/PATCH/PUT/DELETE: non idempotenti).
- Transitorio = uscita non zero di gh con stderr che contiene `HTTP 5` seguito da due cifre (500, 502, 503, 504…) oppure `unexpected end of JSON input`; con `include=True`, anche una riga di stato con codice >= 500. Un 4xx (403, 404, 422…) non è transitorio: comportamento invariato (con `include` resta un risultato). Il timeout (`TimeoutExpired`) non si ritenta.
- Tentativi: 3 in tutto, attese `RETRY_DELAYS_S = (2, 4)` secondi tra un tentativo e il successivo, con il sonno preso da un nome del modulo sostituibile nei test (es. `_sleep = time.sleep`) così che i test non dormano. Dopo l'ultimo tentativo fallito l'errore è esattamente quello di oggi (stesso `GhError`, stesso testo).
- Un solo punto che decide «ritenta o no» (helper unico usato da `api` e dalle due `run_json*`), niente logica duplicata.
- Docstring del modulo/funzione aggiornate in una riga (perché: 500 a corpo vuoto osservato su `commits/<sha>/pulls` nella prova P4).

## Test (TDD: prima ROSSI, poi verdi)
In `tests/test_ghcli.py` (o dove stanno i test di `ghcli`), con il gh finto (`tests/fakegh.py`; se non sa rispondere «prima un errore poi un successo», estendilo in modo minimo e testato) o con un `run` sostituito:
1. GET con un 500 (stderr `HTTP 500`) e poi successo → ritorna i dati; 2 chiamate; un'attesa di 2 s.
2. GET `paginate` con `unexpected end of JSON input` e poi successo → ritorna la lista.
3. GET sempre 500 → `GhError` col testo di oggi; 3 chiamate; attese (2, 4).
4. POST/PATCH con 500 → nessun ritentativo (1 chiamata), `GhError`.
5. GET `include=True` con 404 e con 403 → nessun ritentativo, risultato come oggi; con riga di stato 502 → ritenta.
6. GET con 422/404 senza include → nessun ritentativo.
7. `run_json_lines(["api","--paginate",...])` transitorio poi ok → ritenta; `run_json_lines` con `--method POST` → no.
8. Un test di guard (`tests/test_gate_guard.py`) in cui `commits/<sha>/pulls` risponde una volta 500 a corpo vuoto e poi bene → `tollgate/guard` pubblicato `success` (oggi il job uscirebbe con 1).

Suite verde con `tests/run` su python3.11 e python3 prima del commit; nessun `__pycache__` committato.

Commit nuovo «tollgate P4: le letture di gh api ritentano sui 5xx transitori di GitHub (Task 16, giro 4)» con la riga esatta «Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>». Aggiungi una sezione «Giro 4» al report `task-16-report.md` (cosa, file, test, esito della suite) e rispondimi solo con stato, commit, una riga sui test e dubbi.
