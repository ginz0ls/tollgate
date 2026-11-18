# Spec di prova: tag per le note

## Obiettivo

Aggiungere i tag alle note del progetto di prova: una tabella `tags` collegata a `notes`, e la lettura dei tag di ogni nota nella edge function `supabase/functions/notes/index.ts`. Ogni passo ha il suo test in `tests/`, che legge solo il testo dei file.

## Fette previste

1. Tabella `tags` con la sua riga di sicurezza per le righe, e lettura dei tag nella edge function, con un test per ciascuno.

## Must-have

- M1. Esiste la tabella `tags`, collegata a `notes`, e ha la riga che attiva la sicurezza per le righe, come `notes` — test: tests.test_migrations.MigrationsTest::test_tags_table
- M2. La edge function `notes` legge la tabella `tags` — test: tests.test_function.FunctionTest::test_reads_tags

## Tane di coniglio

- Ordine dei tag di una nota: scelta fatta, nessun ordine garantito.
- Più tag con lo stesso testo sulla stessa nota: scelta fatta, ammessi; nessun vincolo di unicità.
- Un tag senza nota: scelta fatta, non esiste; ogni tag appartiene a una nota.
- Tag nelle risposte già esistenti della funzione: scelta fatta, la funzione aggiunge i tag a ciò che già restituisce, senza togliere campi.

## Cosa non fare

- Nessun programma di database, di servizi o di pacchetti: i file `.sql`, `.ts` e `.toml` sono solo testo.
- Nessuna credenziale né file `.env` nel progetto.
- Nessuna modifica a `supabase/config.toml` né a `tools/unittest_junit.py` né al test già presente `tests/test_migrations.py::test_every_table_has_row_level_security`.
