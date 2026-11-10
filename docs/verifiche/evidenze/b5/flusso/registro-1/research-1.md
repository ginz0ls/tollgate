## Letto nel progetto
- server/app.py
- tests/test_smoke.py

## Documentazione
- https://docs.python.org/3/library/http.server.html — BaseHTTPRequestHandler: i do_*() sono scritti a mano nelle sottoclassi; send_response, send_header, end_headers. Il task non tocca Handler, usa solo la libreria standard (json).

## Cosa ho trovato
Il progetto non ha contratti formali (tipi o schemi): solo la tabella ROUTES in server/app.py con funzioni pure che restituiscono (stato, tipo, corpo), e dispatch che dà 404 per rotte o metodi sconosciuti. health() segue lo schema di hello(). Nessun campo o rotta esistente cambia, nessun input da validare, nessun dato toccato. Il test segue lo stile di test_smoke.py (unittest).
esito: valida
