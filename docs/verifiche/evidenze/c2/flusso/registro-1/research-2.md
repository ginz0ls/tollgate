## Letto nel progetto
- app/notes.py
- app/auth/tokens.py
- app/auth/__init__.py
- tests/test_tokens.py
- tools/unittest_junit.py
- tollgate.toml
- docs/superpowers/plans/2026-11-22-prova-c2.md

## Nessuna fonte esterna
Il progetto usa solo la libreria standard di Python (piano, «Fatti verificati»): il diff usa unittest, unittest.mock e os, e le funzioni gia' presenti signing_key, verify, sign, get_note, add_note, clear_notes. Nessuna libreria di token, password o sessioni e nessun servizio esterno.

## Cosa ho trovato
verify(token, secret, *, now) di Task 1 e' completo e non solleva mai; signing_key() solleva RuntimeError se C2_PROVA_SECRET manca. read_note(token, note_id, *, now) chiamera' signing_key() come prima istruzione senza try (M11), poi verify, get_note e can_read(user, note.owner); stesso None per token invalido, nota assente e nota altrui. can_read in app/auth/access.py confronta due nomi utente (non segreti) e non importa app/notes.py. I test seguono lo schema di tests/test_tokens.py (setUp con mock.patch.dict fermato da addCleanup, valore finto PROVA-123); NotesTest chiama clear_notes() nel setUp perche' _NOTES e' globale.
esito: valida
