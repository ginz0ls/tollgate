## Letto nel progetto
- config.toml
- src/__init__.py
- tests/test_smoke.py

## Documentazione
- https://docs.python.org/3/library/tomllib.html — tomllib.load vuole un file binario ("rb"); TOML invalido solleva TOMLDecodeError (sottoclasse di ValueError); disponibile da Python 3.11.

## Cosa ho trovato
config.toml contiene [app] nome = "prova-b1". Python 3.13. Test in unittest sotto tests/. CONFIG_PATH sarà la radice del repo/config.toml calcolata da __file__; open "rb" lascia propagare FileNotFoundError e TOMLDecodeError, e l'accesso a data["app"]["nome"] dà KeyError.
esito: valida
