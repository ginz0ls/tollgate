## Letto nel progetto
- config.toml
- tests/test_smoke.py
- src/__init__.py

## Documentazione
- https://docs.python.org/3/library/tomllib.html — tomllib.load(fp) vuole un file binario ("rb"); TOMLDecodeError sottoclasse di ValueError; restituisce dict.

## Cosa ho trovato
config.toml contiene [app] nome = "prova-b1". Uso open(percorso, "rb") + tomllib.load e dati["app"]["nome"]; KeyError e FileNotFoundError si propagano naturalmente. Il default è ancorato a __file__ per non dipendere dalla cwd. Python 3.13, tomllib in stdlib.
esito: valida
