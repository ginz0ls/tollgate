---
name: rules-database
description: Regole di tollgate per il database (migrazioni, schema, RLS, funzioni del database, edge function di Supabase): le caricano in automatico gli agenti dell'area database, non serve invocarla.
version: 1
approved: 2026-11-17
---
# Regole database (versione 1)

Sono le regole per il codice che cambia il database: migrazioni, schema, policy di accesso, funzioni del database e edge function di Supabase. Valgono in aggiunta a quelle di base. Chi scrive le segue prima di toccare un file. Chi rivede le applica guardando ciò che ha davanti, e per ognuna risponde sì o no: sotto ogni regola la riga «Si giudica su» dice se la risposta sta nel diff o nel report. Le regole segnate `[blocca]` si giudicano sul diff o sul report, perché nei lavori senza il passo «informati prima» la nota non c'è. Un difetto si segnala una volta sola, con la regola che viola.

Uno schema si riconosce da un file `schema.prisma`, da una tabella di Drizzle (un file che importa `drizzle-orm/pg-core`) o da un `create table` in un file `.sql` (questo criterio è una scelta nostra). Serve a R-DATABASE-01.

Nel diff si riconosce una migrazione da un file nuovo o cambiato sotto `supabase/migrations/` o sotto un'altra cartella `migrations/` (anche `prisma/migrations/`), oppure da un file `.sql` con `create`, `alter` o `drop`. Una policy è un'istruzione `create policy` o `alter policy` in un file `.sql`. Una edge function è un file sotto `supabase/functions/<nome>/`.

Le regole su RLS, policy, funzioni `security definer`, `concurrently` e edge function valgono solo per PostgreSQL e Supabase, che si riconoscono da `supabase/`, da `prisma/schema.prisma` con `provider = "postgresql"` o dal SQL stesso. Una cartella `migrations/` può essere di un'altra base dati (SQLite di D1, MySQL di Laravel, Django): lì il revisore risponde «non si applica» a quelle regole, e le altre valgono lo stesso.

## Prima di scrivere

R-DATABASE-01 [blocca] Se il diff aggiunge o cambia una migrazione o uno schema, il report nomina lo schema e le migrazioni già presenti che ha letto prima di scrivere (percorsi), o dice che non ce ne sono.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `database`: si leggono lo schema e le migrazioni esistenti prima di scriverne una); i percorsi nel report sono una scelta nostra, per poter controllare che la lettura ci sia stata

R-DATABASE-02 [blocca] Se il diff usa per la prima volta nel file un'istruzione, una funzione o un'opzione specifica di PostgreSQL o di Supabase, il report ha l'indirizzo della pagina ufficiale della versione del progetto (`major_version` in `supabase/config.toml`, o la versione di PostgreSQL che il progetto dichiara), con la versione; se il progetto non la dichiara, il report lo dice e dà l'indirizzo della documentazione corrente.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `database`: per RLS e funzioni la documentazione di Supabase o di PostgreSQL della versione del progetto); https://www.postgresql.org/docs/current/ e https://supabase.com/docs/guides/local-development/cli/getting-started (la cartella `supabase/` ha il `config.toml` del progetto) e https://supabase.com/docs/guides/local-development/cli/config (`major_version` è la versione principale di PostgreSQL del database locale, uguale a quella remota); la via d'uscita per i progetti senza versione dichiarata è una scelta nostra

## Mentre lavori

R-DATABASE-03 [blocca] Una migrazione che esisteva prima del lavoro (sul ramo di partenza) non si modifica e non si cancella: ogni cambiamento allo schema è un file di migrazione nuovo.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/deployment/database-migrations (lo schema cambia solo con migrazioni nuove) e https://www.prisma.io/docs/orm/prisma-migrate/understanding-prisma-migrate/migration-histories (una migrazione già applicata non si cambia né si toglie); deprecation-and-migration 0.6.9 (Addy Osmani, MIT), «Database Schema Migrations»

R-DATABASE-04 [blocca] Per ogni migrazione nuova il report dice come si annulla: il file o i passi che riportano lo stato indietro, oppure che non si può annullare e perché.
Si giudica su: report
Fonte: catalogo 2.1 (riga `database`: migrazioni reversibili) e 2.3 (riga `database`: migrazione applicata e annullata su un database vuoto); deprecation-and-migration 0.6.9 (Addy Osmani, MIT), «Database Schema Migrations» (ogni migrazione ha un percorso di ritorno provato); che il report lo scriva è una scelta nostra

R-DATABASE-05 [blocca] Il diff non rinomina e non toglie in un solo passo una colonna o una tabella che può avere dati: prima si aggiunge il nuovo e si copiano i dati, poi, in una migrazione successiva, si toglie il vecchio. Fa eccezione una tabella creata nello stesso diff.
Si giudica su: diff
Fonte: deprecation-and-migration 0.6.9 (Addy Osmani, MIT), «Database Schema Migrations» (espandi, copia, contrai: un cambio sul posto rompe il codice che gira durante il rilascio); l'eccezione per la tabella appena creata è una scelta nostra

R-DATABASE-06 [blocca] Se il diff, su una tabella che il diff non crea, crea un indice senza `concurrently`, aggiunge una colonna con un valore predefinito volatile, cambia il tipo di una colonna o imposta `not null` senza un vincolo `check` già valido, il report lo dichiara e dice perché il blocco o la riscrittura è accettabile, o come l'ha evitato. Vale solo per PostgreSQL.
Si giudica su: report
Fonte: https://www.postgresql.org/docs/current/sql-createindex.html (senza `concurrently` le scritture si fermano finché l'indice non è pronto) e https://www.postgresql.org/docs/current/sql-altertable.html (blocco esclusivo, riscrittura con default volatile o cambio di tipo, `not null` senza scansione con un `check` valido); deprecation-and-migration 0.6.9 (Addy Osmani, MIT), «Database Schema Migrations» (indici grandi senza bloccare le scritture); che il report lo dichiari è una scelta nostra

R-DATABASE-07 [blocca] Una tabella nuova in uno schema esposto dall'API (in Supabase, come `public`) ha `enable row level security` nella stessa migrazione e le policy per i ruoli che devono accedervi. Vale solo per PostgreSQL e Supabase.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/database/postgres/row-level-security (RLS su ogni tabella di uno schema esposto; senza policy l'API non dà dati) e https://supabase.com/docs/guides/database/database-advisors (avviso 0013, tabella in `public` senza RLS); https://www.postgresql.org/docs/current/ddl-rowsecurity.html (senza policy applicabili vale il rifiuto; il proprietario della tabella salta RLS salvo `force row level security`)

R-DATABASE-08 Ogni policy nomina il ruolo con `to` e riguarda una sola operazione (`select`, `insert`, `update` o `delete`), non `for all`; `to anon` con `using (true)` solo per dati pubblici. Vale solo per PostgreSQL e Supabase.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/database/postgres/row-level-security (una policy per operazione, il ruolo sempre nominato, `anon` solo per dati pubblici); https://www.postgresql.org/docs/current/sql-createpolicy.html (senza `to` la policy vale per tutti i ruoli)

R-DATABASE-09 [blocca] In una policy `auth.uid()` e le altre funzioni `auth.*` stanno dentro `(select …)`, così si valutano una volta per istruzione e non per ogni riga. Vale solo per PostgreSQL e Supabase.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/database/postgres/row-level-security (sezione sulle funzioni chiamate con `select`) e https://supabase.com/docs/guides/database/database-advisors (avviso 0003); supabase-postgres-best-practices 1.1.0 (Supabase, MIT), references/security-rls-performance.md

R-DATABASE-10 [blocca] Una policy nuova ha un indice sulle colonne che filtra, e una chiave esterna nuova ha un indice sulla sua colonna: PostgreSQL non lo crea da sé. Vale solo per PostgreSQL e Supabase.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/database/postgres/row-level-security (un indice sulle colonne filtrate dalle policy) e https://supabase.com/docs/guides/database/database-advisors (avviso 0001, chiave esterna senza indice); supabase-postgres-best-practices 1.1.0 (Supabase, MIT), references/schema-foreign-key-indexes.md e references/security-rls-performance.md

R-DATABASE-11 [blocca] Una funzione `security definer` fissa `search_path` (a `''`, o a un elenco senza schemi scrivibili da altri) e scrive lo schema davanti a ogni tabella che usa; dove basta si sceglie `security invoker`, che è il predefinito. Vale solo per PostgreSQL e Supabase.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/database/functions (preferire `security invoker`; con `security definer` il `search_path` si fissa e i nomi si qualificano) e https://supabase.com/docs/guides/database/database-advisors (avviso 0011); https://www.postgresql.org/docs/current/sql-createfunction.html (un `search_path` sicuro esclude gli schemi scrivibili da utenti non fidati)

R-DATABASE-12 [blocca] Una vista in uno schema esposto dall'API si crea con `security_invoker = true`, altrimenti ignora le policy di chi la interroga. Vale solo per PostgreSQL (dalla 15) e Supabase.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/database/postgres/row-level-security (le viste saltano RLS per default; `security_invoker` da PostgreSQL 15) e https://supabase.com/docs/guides/database/database-advisors (avviso 0010)

R-DATABASE-13 [blocca] Nessuna chiave segreta, password del database o chiave `service_role` di Supabase in un file versionato né nel codice che gira nel browser: stanno nelle variabili d'ambiente o nei segreti del servizio.
Si giudica su: diff
Fonte: https://supabase.com/docs/guides/database/postgres/row-level-security (la chiave segreta non va mai nel browser; il ruolo `service_role` salta RLS) e https://supabase.com/docs/guides/functions/secrets (un file di segreti versionato li espone a chiunque legga il repo)

R-DATABASE-14 [blocca] Una edge function di Supabase legge i segreti con `Deno.env.get` e non li scrive nel codice; il diff non aggiunge `supabase/functions/.env`. Vale solo per Supabase.
Si giudica su: diff
Fonte: progetto di B, sezione 12 (le edge function di Supabase restano all'area `database`); https://supabase.com/docs/guides/functions/secrets (segreti letti con `Deno.env.get`, in locale da `supabase/functions/.env`, che non si versiona)

R-DATABASE-15 [blocca] Se il diff mette `verify_jwt = false` in `[functions.<nome>]` di `supabase/config.toml`, il report dice perché la funzione deve poter essere chiamata da chiunque e come si protegge in altro modo. Vale solo per le edge function di Supabase.
Si giudica su: report
Fonte: https://supabase.com/docs/guides/functions/function-configuration (il controllo del JWT è attivo per default; con `verify_jwt = false` la chiama chiunque); che il report lo motivi è una scelta nostra

R-DATABASE-16 [blocca] Il task non scrive sul progetto collegato né su un database vero. Il report non riporta comandi lanciati da lui che lo facciano (`supabase db push` verso il progetto remoto, `supabase functions deploy`, `supabase secrets set`, `supabase link`, `prisma migrate deploy`, `prisma db push`, `drizzle-kit push`, `drizzle-kit migrate`) e dice quale prova ha fatto, o perché non l'ha fatta.
Si giudica su: report
Fonte: progetto di B, sezione 14 (le scritture della CLI di Supabase che possono andare sul progetto vero chiedono il permesso) e spec del nucleo, sezione 8.5 (gli effetti esterni sono negati finché l'utente non li approva); https://supabase.com/docs/reference/cli (con la CLI 3 `db push` scrive in locale se manca l'opzione remote) e https://supabase.com/docs/guides/functions/deploy (`functions deploy` porta le funzioni sul progetto remoto collegato) e https://supabase.com/docs/guides/functions/secrets (`secrets set` imposta i segreti di produzione); https://www.prisma.io/docs/orm/reference/prisma-cli-reference (i comandi di migrazione e `db push` scrivono sul database configurato) e https://orm.drizzle.team/docs/kit-overview (`push` e `migrate` scrivono)

## Dove informarsi

Prima di scrivere si aprono le migrazioni e lo schema già presenti (R-DATABASE-01). Per ogni istruzione o opzione si cerca la pagina ufficiale della versione di PostgreSQL o di Supabase del progetto; se la versione non si trova o la pagina non c'è, il report lo dice e non si inventa la sintassi.

- Le skill `supabase-postgres-best-practices` (RLS, indici, schema, blocchi; plugin `postgres-best-practices`) e `deprecation-and-migration` (migrazioni in più tempi, percorso di ritorno; plugin `agent-skills`), se i plugin sono installati.
- Supabase: https://supabase.com/docs/guides/database/postgres/row-level-security, https://supabase.com/docs/guides/database/functions, https://supabase.com/docs/guides/database/database-advisors, https://supabase.com/docs/guides/deployment/database-migrations, https://supabase.com/docs/guides/functions, https://supabase.com/docs/reference/cli.
- PostgreSQL, la pagina della versione in uso (la corrente è https://www.postgresql.org/docs/current/): `ddl-rowsecurity`, `sql-createpolicy`, `sql-createindex`, `sql-altertable`, `sql-createfunction`.
- Prisma https://www.prisma.io/docs/orm/prisma-migrate/understanding-prisma-migrate/migration-histories e Drizzle https://orm.drizzle.team/docs/kit-overview, per la versione scritta nel file delle dipendenze del progetto.

## Fonti

Le regole sono scritte con parole nostre. Da `supabase-postgres-best-practices` 1.1.0 (Supabase, licenza MIT) e da `deprecation-and-migration` di agent-skills 0.6.9 (Addy Osmani, licenza MIT) vengono i temi e i nomi delle sezioni, senza testo copiato. Le pagine ufficiali di Supabase, PostgreSQL, Prisma e Drizzle riportano i fatti, non il testo. Le scelte dell'utente stanno nel progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md, sezioni 3.4, 12 e 14) e nel catalogo (sezioni 2.1 e 2.3). I nomi dei file e i marcatori con cui `init` riconosce il profilo (`templates/profiles/database.toml`) vengono dalle stesse pagine: un commento del frammento dice quale per ogni gruppo.
