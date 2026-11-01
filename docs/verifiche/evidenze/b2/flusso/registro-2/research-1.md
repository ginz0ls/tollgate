## Letto nel progetto
- config.toml
- tests/test_smoke.py
- src/__init__.py
- tollgate.toml

## Documentazione
- https://docs.python.org/3/library/tomllib.html — tomllib.load(fp) vuole un file binario ("rb"); TOMLDecodeError su TOML invalido; modulo dalla 3.11. Libreria standard, Python 3.13.5 locale.

## Cosa ho trovato
config.toml in radice contiene [app] nome = "prova-b1". Il percorso predefinito va calcolato da __file__ (Path(__file__).resolve().parent.parent / "config.toml") per funzionare con cwd diversa. Open in "rb"; KeyError e FileNotFoundError si propagano naturalmente. Schema test: unittest come test_smoke.py; comando test in tollgate.toml.
esito: valida
