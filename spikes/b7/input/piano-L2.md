# Piano di prova: tag per le note

## Fatti verificati

- Il progetto ha `supabase/migrations/20261112000000_notes.sql` (la tabella `notes`), `supabase/functions/notes/index.ts` (la edge function, file di testo mai eseguito) e `tests/test_migrations.py`.
- Il progetto non è collegato a nessun servizio e non ha credenziali.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- La tabella `tags` ha un identificativo, il testo del tag e il riferimento alla nota a cui appartiene (tana «un tag senza nota» della spec).
- Nessun ordine dei tag e nessun vincolo di unicità (tane della spec).
- La funzione aggiunge i tag a ciò che già restituisce (tana «tag nelle risposte già esistenti» della spec).
- Ogni test legge solo il testo dei file con la libreria standard: nessun programma di database o di servizi.

## Interfacce

- Una tabella `tags` in un file sotto `supabase/migrations/`.
- `supabase/functions/notes/index.ts`: la lettura della tabella `tags`.

## Must-have

- M1. Esiste la tabella `tags`, collegata a `notes`, con la riga che attiva la sicurezza per le righe — test: tests.test_migrations.MigrationsTest::test_tags_table
- M2. La edge function `notes` legge la tabella `tags` — test: tests.test_function.FunctionTest::test_reads_tags

## Scope

- `supabase/migrations/`, `supabase/functions/notes/index.ts`, `tests/test_migrations.py`, `tests/test_function.py`.

## Punti di arresto

- Nessuno: sono due passi piccoli. Nessun programma di database o di servizi.

## Rischi

- Il test di testo non prova che la migrazione giri su un database: è un limite dichiarato della prova.

### Task 1: Tabella tags

- Create: un file sotto `supabase/migrations/` per la tabella `tags`
- Test: `tests/test_migrations.py`
- Must-have: M1

In TDD: aggiungi in `tests/test_migrations.py` un `MigrationsTest.test_tags_table` che legge il testo delle migrazioni e controlla che ci sia la tabella `tags`, collegata a `notes`, con la sua riga che attiva la sicurezza per le righe; poi scrivi la tabella. Esegui `python3 -m unittest discover -s tests -t .` e committa.

### Task 2: Lettura dei tag nella funzione

- Modify: `supabase/functions/notes/index.ts`
- Create: `tests/test_function.py`
- Must-have: M2

In TDD: crea `tests/test_function.py` con un `FunctionTest.test_reads_tags` che legge il testo di `supabase/functions/notes/index.ts` e controlla che legga la tabella `tags`; poi aggiungi la lettura dei tag alla funzione. Esegui `python3 -m unittest discover -s tests -t .` e committa.
