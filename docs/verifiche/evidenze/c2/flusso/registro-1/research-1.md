## Letto nel progetto
- app/auth/tokens.py
- tests/test_tokens.py
- app/notes.py
- docs/superpowers/plans/2026-11-22-prova-c2.md
- docs/superpowers/specs/2026-11-22-prova-c2.md
- tollgate.toml
- tools/unittest_junit.py

## Documentazione
- https://docs.python.org/3/library/hmac.html — compare_digest accetta due str solo ASCII o due bytes-like dello stesso tipo, confronta senza uscire al primo byte diverso; la doc consiglia di codificare il testo in bytes prima.
- https://docs.python.org/3/library/stdtypes.html#str.isdigit — isdigit() è vero anche per cifre non ASCII (arabo-indiane, apici come ²), isascii() è vero solo per U+0000-U+007F: servono tutte e due per ammettere solo cifre ASCII.

## Cosa ho trovato
Il progetto usa solo la libreria standard (nessun file di dipendenze: niente requirements/pyproject; spec, «Cosa non fare»). verify oggi confronta la firma con != e non controlla la scadenza. Applico l'ordine della spec: secret vuoto -> None; token.encode("utf-8") con UnicodeEncodeError -> None; rsplit(".", 2) in tre parti; hmac.compare_digest sui byte UTF-8 delle due firme (la firma ricevuta può contenere non ASCII, quindi codifico: il token è già codificabile al passo 2); utente non vuoto; scadenza isascii() e isdigit() e len <= 20, poi int, valida solo se now < expires_at. signing_key() legge os.environ a ogni chiamata, codifica UTF-8 senza strip, RuntimeError(...) from None per assente/vuota/non codificabile, messaggio che nomina C2_PROVA_SECRET e mai il valore. sign non cambia. La suite non registra subTest: niente subTest, cicli con msg=.
esito: valida
