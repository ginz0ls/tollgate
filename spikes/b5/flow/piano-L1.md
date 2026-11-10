# Piano di prova: rotta GET /health

## Fatti verificati

- Il progetto ha `server/app.py` (una tabella `ROUTES` e una funzione pura per ogni rotta, che restituisce stato, tipo e corpo), `edge/index.ts` e `supabase/functions/hello/index.ts` (file di testo, mai eseguiti) e `tests/test_smoke.py`.
- Il progetto non è collegato a nessun servizio e non ha credenziali.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- `server/app.py` ottiene la funzione `health()`, che restituisce `(200, "application/json", '{"status": "ok"}')`, e la voce `("GET", "/health")` in `ROUTES`.
- Il test chiama `health()` e `dispatch("GET", "/health")` e legge il corpo con il modulo `json`; non si avvia nessun server.

## Interfacce

- `server/app.py`: `health()` e la voce di `ROUTES` per `GET /health`.

## Must-have

- M1. `GET /health` risponde `{"status": "ok"}` con il tipo `application/json` — test: tests.test_health.HealthTest::test_health

## Scope

- `server/app.py`, `tests/test_health.py`.

## Punti di arresto

- Nessuno: il task è una sola rotta. Non si avvia un server su una porta.

## Rischi

- Nessuno di rilievo: nessun programma di servizio viene lanciato.

### Task 1: Rotta GET /health

- Modify: `server/app.py`
- Test: `tests/test_health.py`
- Must-have: M1

In TDD: scrivi in `tests/test_health.py` un `HealthTest.test_health` che chiama `health()` e `dispatch("GET", "/health")` e verifica stato 200, tipo `application/json` e corpo `{"status": "ok"}`, poi aggiungi `health()` e la voce in `ROUTES`. Esegui `python3 -m unittest discover -s tests -t .` e committa.
