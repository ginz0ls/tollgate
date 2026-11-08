# Piano di prova: intestazione nosniff in vercel.json

## Fatti verificati

- Il progetto ha `vercel.json` (con la sola proprietà `cleanUrls`), un `Dockerfile` di poche righe, `app/__init__.py`, `app/main.py` e `tests/test_smoke.py`.
- Il progetto non è collegato a nessun servizio: nessun progetto Vercel, nessun account, nessuna credenziale. La prova senza pubblicazione non si fa e il report dice perché.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- `vercel.json` ottiene la proprietà `headers` con una regola per tutti i percorsi che imposta `X-Content-Type-Options: nosniff`; `cleanUrls` resta com'è.
- Il test legge `vercel.json` con il modulo `json` e controlla l'intestazione, senza lanciare alcun programma di Vercel.

## Interfacce

- `vercel.json`: la proprietà `headers`, una lista di regole con `source` e `headers` (coppie `key` e `value`).

## Must-have

- M1. `vercel.json` ha una regola che vale per ogni percorso con l'intestazione `X-Content-Type-Options: nosniff` — test: tests.test_headers.HeadersTest::test_nosniff

## Scope

- `vercel.json`, `tests/test_headers.py`.

## Punti di arresto

- Nessuno: il task è una sola intestazione. Non si pubblica e non si collega il progetto.

## Rischi

- Nessuno di rilievo: nessun comando di servizio viene lanciato.

### Task 1: Intestazione nosniff

- Modify: `vercel.json`
- Test: `tests/test_headers.py`
- Must-have: M1

In TDD: scrivi in `tests/test_headers.py` un `HeadersTest.test_nosniff` che legge `vercel.json` e verifica che una regola con `source` `/(.*)` abbia l'intestazione `X-Content-Type-Options` con valore `nosniff`, poi aggiungi la proprietà `headers` a `vercel.json`. Nel report scrivi l'indirizzo della pagina ufficiale di Vercel che descrive `headers`, e che la prova senza pubblicazione non si è fatta perché il progetto non è collegato a nessun servizio. Esegui `python3 -m unittest discover -s tests -t .` e committa.
