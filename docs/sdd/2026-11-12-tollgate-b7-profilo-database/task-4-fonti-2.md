# Task 4, secondo passaggio: fonti di `rules-database` (cinque parti cambiate)

**Metodo.** Letti: brief del primo passaggio, `task-4-fonti.md`, `skills/rules-database/SKILL.md`, `docs/profili/verifiche/database-fonti.md`, le copie in `fonti/database/` (supabase-local-dev.md, supabase-edge-functions.md, supabase-cli.md, prisma.md, drizzle.md, postgresql-18.md, skill/deprecation-and-migration). `sha256sum -c SHA256SUMS` in `fonti/database/`: nessuna riga diversa da `OK`. Nessuna rete. Nessuna traccia della richiesta di rapporto a Supabase nelle copie, salvo la nota che dice che è stata tolta (e la parola `feedback` in un elenco di gruppi della CLI, supabase-cli.md riga 15, che non è un'istruzione).

## Voci

| Parte | Voce | Citazione (copia) | Ambito / giudizio | Esito |
|---|---|---|---|---|
| Introduzione | `schema.prisma` | «It is typically a single file called `schema.prisma`» (prisma.md) | nessuna `Fonte:` nell'introduzione | ok |
| Introduzione | tabella Drizzle, import di `drizzle-orm/pg-core` | `import { integer, pgTable, varchar } from "drizzle-orm/pg-core";` (drizzle.md) | idem | ok |
| Introduzione | `create table` in un file `.sql` | nessuna copia lo dice: `create table` compare solo come esempio SQL nelle skill di Supabase, non come criterio per riconoscere lo schema | l'introduzione non lo dichiara «scelta nostra»; `database-fonti.md` non ha nessuna riga per l'introduzione | no |
| R-DATABASE-02 | progetto di B, 3.4 | «Per RLS e funzioni Postgres, la documentazione di Supabase o di Postgres della versione del progetto.» | report; ambito dichiarato nella regola e nell'introduzione | ok |
| R-DATABASE-02 | postgresql.org/docs/current/ | `postgresql-18.md` è la documentazione 18.6 con l'indirizzo `/docs/current/` | idem | ok |
| R-DATABASE-02 | supabase.com .../cli/getting-started | «a `supabase` directory and a `config.toml`» (supabase-local-dev.md) | idem | ok |
| R-DATABASE-02 | supabase.com .../cli/config (`major_version`) | «The database major version to use. This has to be the same as your remote database's.» (supabase-local-dev.md, aggiunta del 16/11; `[db] major_version`, default 15) | la copia dice «del database locale» come riassunto, la citazione dice «uguale al remoto»: regge la voce | ok |
| R-DATABASE-02 | via d'uscita senza versione dichiarata | scelta nostra, dichiarata nella `Fonte:` | non si verifica | scelta nostra |
| R-DATABASE-03 | supabase.com .../database-migrations | «never change the remote database directly.» (supabase-local-dev.md) | diff; supporto indiretto (non dice «migrazione esistente»), come nel primo passaggio | ok |
| R-DATABASE-03 | prisma.io .../migration-histories | «you should not edit or delete a migration that has already been applied» (prisma.md) | regge: «già applicata» e «sul ramo di partenza» sono vicine, la regola è più larga (vale per ogni migrazione precedente) | ok |
| R-DATABASE-03 | deprecation-and-migration 0.6.9, «Database Schema Migrations» | «The fix is to **never change a column in place**.» (LICENSE MIT presente) | supporto indiretto (parla di colonne, non di file) | ok |
| R-DATABASE-06 | postgresql.org .../sql-createindex.html | «a standard index build locks out writes (but not reads) on the table until it's done.» (postgresql-18.md) | report; «Vale solo per PostgreSQL» dichiarato | ok |
| R-DATABASE-06 | postgresql.org .../sql-altertable.html | «An `ACCESS EXCLUSIVE` lock is acquired unless explicitly noted.»; «Adding a column with a volatile `DEFAULT` ... will cause the entire table and its indexes to be rewritten.»; «Changing the type of an existing column will normally cause the entire table and its indexes to be rewritten.»; «if a valid `CHECK` constraint exists ... the table scan is skipped.» (postgresql-18.md) | idem; copre tutte e quattro le condizioni | ok |
| R-DATABASE-06 | deprecation-and-migration 0.6.9 | «**Build large indexes without blocking writes** (e.g. Postgres `CREATE INDEX CONCURRENTLY`).» | idem | ok |
| R-DATABASE-06 | che il report lo dichiari | scelta nostra | non si verifica | scelta nostra |
| R-DATABASE-16 | progetto di B, 14 | «Le scritture della CLI di Supabase che possono andare sul progetto vero chiedono il permesso salvo --local (utente).» | report; ambito: Supabase, Prisma, Drizzle nominati | ok |
| R-DATABASE-16 | spec del nucleo, 8.5 | `supabase` in scrittura tra gli effetti esterni negati finché l'utente non li approva | idem | ok |
| R-DATABASE-16 | supabase.com/docs/reference/cli (`db push`) | «Pushes to the local database by default.» (supabase-cli.md) | idem | ok |
| R-DATABASE-16 | supabase.com .../functions/deploy | «Deploy your Edge Functions to your remote Supabase Project.» (supabase-edge-functions.md, aggiunta 16/11); «collegato» con `supabase link --project-ref` è riassunto della copia, senza citazione | idem | ok |
| R-DATABASE-16 | supabase.com .../functions/secrets | solo un riassunto nella copia: «I segreti di produzione si impostano dalla Dashboard o con `supabase secrets set`»; nessuna riga testuale | il fatto c'è, la citazione testuale no | ok (da rilevare: citazione non testuale) |
| R-DATABASE-16 | prisma.io .../prisma-cli-reference | riassunto in prisma.md: scrivono migrate dev/reset/deploy/resolve, db push, db execute; `DATABASE_URL` non compare, la regola dice «il database configurato» | nessuna citazione testuale | ok (da rilevare: citazione non testuale) |
| R-DATABASE-16 | orm.drizzle.team .../kit-overview | riassunto in drizzle.md: «migrate e push scrivono» | nessuna citazione testuale | ok (da rilevare: citazione non testuale) |

Frasi copiate (oltre una decina di parole identiche alle fonti): nessuna nelle cinque parti.

## `docs/profili/verifiche/database-fonti.md`

Righe per voce: R-DATABASE-02 quattro (le tre di prima più `major_version`; la via d'uscita non ha riga, è scelta nostra), R-DATABASE-03 tre, R-DATABASE-06 tre, R-DATABASE-16 nove (due `no` storici del primo passaggio, sette `ok`). Tutte le citazioni di queste righe stanno nelle copie (controllate una per una: «never change the remote database directly.», «you should not edit or delete...», «Pushes to the local database by default.», «Deploy your Edge Functions to your remote Supabase Project.», «The database major version to use...», le righe di postgresql-18.md e di deprecation-and-migration). Mancanza: **nessuna riga per l'introduzione** (come si riconosce uno schema nel diff), nemmeno per `schema.prisma` e `pg-core` che si potrebbero provare.

## Riepilogo

- ok: 19 voci; scelta nostra: 2 (R-DATABASE-02 via d'uscita, R-DATABASE-06 dichiarazione nel report); no: 1.
- **no: introduzione, `create table` in un file `.sql`**: nessuna fonte nelle copie e nessuna riga in `database-fonti.md`. Correzione minima: dichiarare nell'introduzione (o nella verifica) che il criterio `create table` in `.sql` è una scelta nostra, oppure togliere il criterio; aggiungere in `database-fonti.md` una riga per l'introduzione (`schema.prisma` e `pg-core` hanno citazioni nelle copie).
- Da rilevare, non `no`: tre voci di R-DATABASE-16 (secrets, Prisma, Drizzle) poggiano su riassunti della copia senza riga testuale.
- Regole di PostgreSQL o Supabase senza ambito dichiarato: nessuna tra le cinque parti.
- Istruzioni di terzi: nessuna da eseguire; non eseguita alcuna richiesta di rapporto a Supabase.
