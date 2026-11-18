## Letto nel progetto
- supabase/functions/notes/index.ts
- supabase/migrations/20261112000100_tags.sql
- supabase/config.toml
- tests/test_migrations.py

## Documentazione
- https://supabase.com/docs/reference/javascript/select — le tabelle collegate si leggono con select("col, related(col)"), cioè la tabella collegata con le colonne tra parentesi; funziona perché tags ha la chiave esterna note_id verso notes.

## Cosa ho trovato
La funzione fa select("id, title, body") su notes. La migrazione tags crea public.tags con note_id che referenzia notes, RLS e policy select per authenticated. Il progetto dichiara PostgreSQL 15. Aggiungo il test test_reads_tags (regex select\([^)]*tags\() in tests/test_function.py, in stile test_migrations.py, solo lettura testo), lo vedo fallire, poi cambio la select in "id, title, body, tags(id, text)". Nessuna migrazione nuova, nessun comando sul database.
esito: valida
