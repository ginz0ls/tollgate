## Letto nel progetto
- config.toml
- tests/test_smoke.py
- src/__init__.py
- tollgate.toml

## Documentazione
- https://docs.python.org/3/library/tomllib.html — tomllib.load(fp, /, *, parse_float=float) richiede un file binario (modo "rb"); TOMLDecodeError per TOML non valido; modulo aggiunto in Python 3.11. Il progetto non ha file delle dipendenze: la libreria è della stdlib, versione minima 3.11.

## Cosa ho trovato
config.toml contiene [app] nome = "prova-b1". I test usano unittest con discover -s tests -t . (tollgate.toml). Il pacchetto src esiste già. Implemento src/config.py con CONFIG_PREDEFINITO ancorato a __file__ (indipendente dalla directory corrente), open(..., "rb") e tomllib.load. Lo schema dei test segue tests/test_smoke.py. Nessun file di build/CI toccato.
esito: valida
