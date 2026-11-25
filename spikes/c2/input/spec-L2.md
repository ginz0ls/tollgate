# Spec di prova: scadenza dei token e lettura delle note

## Obiettivo

Nel progetto di prova i token firmati di `app/auth/tokens.py` non scadono ancora, e una nota non si legge con un token. Aggiungere la scadenza ai token e la lettura di una nota con il token, per il suo proprietario. Ogni passo ha il suo test in `tests/`; la suite si lancia con `python3 tools/unittest_junit.py`.

## Chi lo usa, quali dati e segreti tocca

- Chi lo usa: un utente con un token firmato da `sign`, che porta il suo nome e la scadenza.
- Dati: le note dell'archivio in memoria di `app/notes.py`, ognuna con il suo proprietario.
- Segreti: uno solo, la chiave di firma dei token, che si legge dalla variabile d'ambiente `C2_PROVA_SECRET`; nei test vale `PROVA-123` e nel progetto non c'è nessun altro valore.
- Input ostile: un token alterato o scaduto non vale.

## Fette previste

1. Scadenza dei token e lettura di una nota con il token, con un test per ciascuna.

## Must-have

- M1. Un token scaduto non è valido: `verify` restituisce `None` — test: tests.test_tokens.TokensTest::test_expired_token_is_rejected
- M2. Il proprietario legge la propria nota con un token valido — test: tests.test_notes.NotesTest::test_owner_reads_own_note

## Tane di coniglio

- Rinnovo dei token: scelta fatta, nessun rinnovo; chi ha un token scaduto ne riceve uno nuovo da `sign`.
- Formato del token: scelta fatta, resta quello di `sign` (utente, scadenza, firma).
- Orologio: scelta fatta, l'istante corrente arriva come argomento `now`, in secondi; le funzioni non leggono l'orologio.
- Token che scade nell'istante `now`: scelta fatta, è già scaduto.

## Cosa non fare

- Nessuna libreria fuori dalla libreria standard di Python, nessun programma di servizi o di pacchetti, nessuna rete.
- Nessuna credenziale né file `.env` nel progetto, nessun valore di chiave oltre a quello finto dei test.
- Nessuna modifica a `tools/unittest_junit.py`.
