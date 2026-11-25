# Piano di prova: scadenza dei token e lettura delle note

## Fatti verificati

- Il progetto ha `app/auth/tokens.py` (`sign` e `verify`, firma HMAC-SHA256 della libreria standard; `verify` non controlla ancora la scadenza), `app/notes.py` (`Note` e l'archivio in memoria, con `add_note`, `get_note` e `clear_notes`) e `tests/test_tokens.py`.
- Il progetto usa solo la libreria standard di Python e non è collegato a nessun servizio.
- La suite si lancia con `python3 tools/unittest_junit.py`, che scrive `reports/junit.xml`.

## Decisioni

- Un token con la scadenza uguale o precedente a `now` è scaduto (tana «token che scade nell'istante `now`» della spec).
- L'istante corrente arriva come argomento `now`, in secondi (tana «orologio» della spec).
- `read_note` verifica il token con la chiave di firma letta dalla variabile d'ambiente `C2_PROVA_SECRET`; nei test vale `PROVA-123`.
- Il permesso di lettura sta in una funzione sola, `can_read`, in `app/auth/access.py`.

## Interfacce

- `app/auth/tokens.py`: `verify(token: str, secret: bytes, *, now: int) -> str | None` controlla anche la scadenza.
- `app/auth/access.py`: `can_read(user: str, note: Note) -> bool`.
- `app/notes.py`: `read_note(token: str, note_id: int, *, now: int) -> Note | None`.

## Must-have

- M1. Un token scaduto non è valido: `verify` restituisce `None` — test: tests.test_tokens.TokensTest::test_expired_token_is_rejected
- M2. Il proprietario legge la propria nota con un token valido — test: tests.test_notes.NotesTest::test_owner_reads_own_note

## Scope

- `app/auth/tokens.py`, `app/auth/access.py`, `app/notes.py`, `tests/test_tokens.py`, `tests/test_notes.py`.

## Punti di arresto

- Nessuno: sono due passi piccoli. Nessun programma di servizi o di pacchetti.

## Rischi

- I test chiamano le funzioni: non provano un servizio di login vero. È un limite dichiarato della prova.

### Task 1: Scadenza dei token

- Modify: `app/auth/tokens.py`
- Test: `tests/test_tokens.py`
- Must-have: M1

In TDD: aggiungi in `tests/test_tokens.py` un `TokensTest.test_expired_token_is_rejected` che firma un token con una scadenza passata e controlla che `verify` restituisca `None`; poi aggiungi a `verify` il controllo della scadenza. Esegui `python3 tools/unittest_junit.py` e committa.

### Task 2: Lettura di una nota con il token

- Create: `app/auth/access.py`, `tests/test_notes.py`
- Modify: `app/notes.py`
- Must-have: M2

In TDD: crea `tests/test_notes.py` con un `NotesTest.test_owner_reads_own_note` che mette una nota nell'archivio, firma un token valido per il suo proprietario e controlla che `read_note` restituisca la nota; poi scrivi `can_read` in `app/auth/access.py` e `read_note` in `app/notes.py`, che verifica il token, cerca la nota e la restituisce se `can_read` lo permette, altrimenti `None`. Esegui `python3 tools/unittest_junit.py` e committa.
