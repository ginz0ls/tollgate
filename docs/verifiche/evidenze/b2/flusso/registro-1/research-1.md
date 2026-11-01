## Letto nel progetto
- config.toml
- src/__init__.py
- tests/test_smoke.py
- tests/__init__.py

## Documentazione
- https://docs.python.org/3/library/tomllib.html — tomllib.load vuole un file binario (open "rb"), restituisce dict; TOMLDecodeError sottoclasse di ValueError; modulo aggiunto in Python 3.11 (qui Python 3.13.5, solo libreria standard).

## Cosa ho trovato
config.toml ha [app] nome = "prova-b1". I test usano unittest con package tests/ e src/. Creo src/config.py con DEFAULT_CONFIG_PATH calcolato da __file__ (indipendente dalla cwd) e app_name(path) che apre in "rb", tomllib.load, restituisce data["app"]["nome"]; KeyError, FileNotFoundError e TOMLDecodeError si propagano. Nuovo modulo: nessun modulo simile esistente da imitare.
esito: valida
