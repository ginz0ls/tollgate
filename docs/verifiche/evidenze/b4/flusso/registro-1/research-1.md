## Letto nel progetto
- vercel.json
- Dockerfile
- tests/test_smoke.py
- .github/workflows/tollgate-run.yml

## Documentazione
- https://vercel.com/docs/project-configuration/vercel-json — la proprietà `headers` è un array di oggetti con `source` (pattern, es. "/(.*)") e `headers` (lista di coppie `key`/`value`); `cleanUrls` è una proprietà booleana separata.

## Cosa ho trovato
vercel.json contiene solo `cleanUrls: true`. Il Dockerfile (python:3.12-slim, app/) e i workflow in .github/workflows (solo tollgate-*, nessun deploy) non toccano l'intestazione. Aggiungo la chiave `headers` con una voce `/(.*)` e X-Content-Type-Options: nosniff, lasciando cleanUrls. Test unittest nello stile di test_smoke.py.
esito: valida
