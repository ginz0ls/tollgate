# Piano di prova: nome dell'app da config.toml

## Fatti verificati

- Il progetto ha `src/__init__.py`, `tests/test_smoke.py` e `config.toml` con `[app]` e `nome = "prova-b1"`.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- `leggi_nome(percorso="config.toml")` apre il file in modalità binaria e usa `tomllib.load`, come dice la documentazione ufficiale di Python.

## Interfacce

- `src.conf.leggi_nome(percorso="config.toml")` restituisce il valore di `[app] nome` come stringa.

## Must-have

- M1. `leggi_nome` restituisce il valore di `[app] nome` — test: tests.test_conf.ConfTest::test_leggi_nome

## Scope

- `src/conf.py`, `tests/test_conf.py`.

## Punti di arresto

- Nessuno: il task è una sola funzione.

## Rischi

- Nessuno di rilievo.

### Task 1: Funzione leggi_nome

- Create: `src/conf.py`
- Test: `tests/test_conf.py`
- Must-have: M1

In TDD: scrivi in `tests/test_conf.py` un `ConfTest.test_leggi_nome` che verifica `leggi_nome("config.toml") == "prova-b1"`, poi crea `src/conf.py` con `leggi_nome`. Esegui `python3 -m unittest discover -s tests -t .` e committa.
