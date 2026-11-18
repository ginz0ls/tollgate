## Letto nel progetto
- tests/test_migrations.py
- supabase/migrations/20261112000000_notes.sql
- supabase/config.toml
- supabase/functions/notes/index.ts
- docs/superpowers/plans/2026-11-12-prova-b7.md
- docs/superpowers/specs/2026-11-12-prova-b7.md

## Documentazione
- https://www.postgresql.org/docs/15/sql-createpolicy.html — sintassi CREATE POLICY (FOR SELECT, TO ruolo, USING con sottoquery); PostgreSQL 15 come da major_version = 15 in supabase/config.toml; senza policy applicabili vale il rifiuto; la sottoquery gira coi diritti di chi interroga.
- https://supabase.com/docs/guides/database/postgres/row-level-security — RLS su ogni tabella esposta, una policy per operazione con ruolo nominato, auth.uid() dentro (select ...), indice sulle colonne filtrate.

## Cosa ho trovato
La migrazione notes usa create table public.notes, enable row level security e una policy select to authenticated con auth.uid(). Seguo lo stesso schema per tags: tabella con FK on delete cascade verso public.notes, RLS attiva, una sola policy for select to authenticated con exists sulla nota del chiamante, scritta con (select auth.uid()) come chiede la documentazione (contiene ancora la stringa auth.uid() cercata dal test). Il test isola i blocchi con regex ancorate a [^;]*; come da piano. Nota: piano e spec decidono esplicitamente "nessun indice su note_id" (fuori scopo), in contrasto con la guida Supabase e R-DATABASE-10: seguo la decisione approvata e lo segnalo nei dubbi del report.
esito: valida
