## Da decidere tu

Su diciassette punti la fonte non diceva proprio quello che la regola chiede, o la scelta è tua, o la proposta ha un costo che devi conoscere. Per ognuno trovi la proposta; se non dici altro, resta quella.

1. **`**/migrations/**` è largo.** Il percorso `**/migrations/**` accende ogni cartella che si chiama `migrations/`, anche una che non è di database. Un componente in `src/components/migrations/` (per esempio `List.tsx`) va a `database` invece che a `frontend` (tre pezzi di percorso contro due). Lo stesso una rotta di Next.js che si chiama come la cartella, `app/migrations/` con la sua `page.tsx`, più probabile del primo caso. Sul tuo disco non ho trovato nessun componente così. Costo: un file d'interfaccia segue le regole del database e il lavoro sale a L2.
   Proposta: tenerlo largo, perché il catalogo lo chiede e copre le migrazioni di tutti gli strumenti. Chi ha un caso toglie la riga dal blocco a mano.

2. **Un documento dentro `docs/migrations/`.** Un file `.md` non accende da solo la cartella, ma se lì dentro c'è anche un `.sql` d'esempio la cartella `docs/migrations/` entra nel profilo e porta con sé anche i documenti. Costo: un documento segue le regole del database.
   Proposta: lasciare così.

3. **`**/schema.*` resta fuori.** Il catalogo lo elencava. Non lo metto perché sul tuo disco 18 file `schema.*` sono immagini, file `.graphql`, `.json` e `.ts` di validazione, e ognuno entrerebbe con il suo percorso esatto, che vince su ogni cartella. Gli schemi `.sql` sono già presi da `**/*.sql`, quelli di Prisma da `prisma/**`, quelli di Drizzle dalla riga di import. Costo: un `schema.ts` che non importa `drizzle-orm/pg-core` va all'agente generico.
   Proposta: lasciarlo fuori.

4. **`supabase/` e `prisma/` valgono solo alla radice.** In un monorepo la cartella `apps/web/supabase/` o `packages/db/prisma/` non entra per nome: le migrazioni dentro vanno comunque a `database` (per `**/migrations/**`), il resto no. Una edge function sotto `apps/api/supabase/` con `Deno.serve(` va a `backend`; sotto `web/supabase/` la funzione e il suo `config.toml` vanno a `frontend`; lo schema in `packages/db/prisma/` va all'agente generico; lo schema in `server/prisma/` va a `backend`. Costo: nessun monorepo con Supabase annidato tra i tuoi progetti, a parte uno con codice di terzi; ma se ne arriva uno, le sue funzioni e il suo schema non seguono le regole del database.
   Proposta: lasciare così; chi ha un monorepo aggiunge a mano la sua cartella al blocco.

5. **Uno schema di Drizzle trovato anche da `ai` o da `backend`.** Un file come `src/index.ts` che importa `drizzle-orm/pg-core` e anche un framework di server è trovato da due profili con lo stesso peso. Vince il primo blocco del `tollgate.toml`, e `init` scrive i blocchi in ordine alfabetico: `database` perde contro `ai` e `backend` e vince contro `frontend` e `infra`. Costo: lo schema segue le regole di `backend`.
   Proposta: lasciare così.

6. **Edge function e file di Prisma che vanno ad `ai`.** Una edge function che importa un programma per i modelli (`supabase/functions/chat/index.ts`) va ad `ai`, perché un percorso esatto di `ai` vince. Lo stesso una funzione in `supabase/functions/agents/`, che non ha nessuna riga particolare: `ai` accende ogni cartella che si chiama `agents/` per il nome e vince per tre pezzi di percorso contro uno; e un file in `supabase/functions/chat/prompts/`; e `prisma/seed.ts` che importa un programma per i modelli. Costo: va contro la tua scelta del progetto di B (le edge function stanno a `database`) in questi casi. Il rimedio sarebbe un `exclude` nel profilo `ai`, cioè una revisione di `rules-ai` con te.
   Proposta: lasciare così (è codice che parla con un modello, quindi difendibile) e rimandare il rimedio.

7. **`prisma/ai/` va ad `ai`.** Un file dentro `prisma/ai/`, per esempio un seme `seed.sql`, va ad `ai`: la cartella ha due pezzi di percorso contro uno di `prisma/**`. Costo: come il punto 6, un file di database segue le regole di `ai`.
   Proposta: lasciare così.

8. **Prisma 8 e il contratto.** Prisma 8 (ancora in versione di prova) scrive il contratto in `src/prisma/contract.prisma`, fuori dalla cartella `prisma/` alla radice, e `prisma/**` non lo copre. Va al profilo della sua cartella o all'agente generico. Costo: un cambio a quel file non segue le regole del database e non porta il lavoro in L2.
   Proposta: lasciare così e riprendere il caso quando Prisma 8 esce e un tuo progetto lo usa.

9. **Migrazioni di altri database.** `**/migrations/**` porta nel profilo anche le migrazioni di SQLite di Cloudflare D1 (`migrations/0001_init.sql` alla radice, accanto a `wrangler.toml`), di MySQL con Laravel (`database/migrations/`) e di Django (`blog/migrations/` dentro un server). Le regole che parlano di RLS, policy, `security definer`, `concurrently` e edge function sono di PostgreSQL e Supabase: per un altro database chi rivede risponde che non si applicano. Le altre (leggere prima schema e migrazioni, una migrazione nuova invece di modificarne una, come si annulla, i dati esistenti) valgono per tutti. Costo: il profilo propone anche regole che per quei progetti non servono.
   Proposta: tenere così, perché sono comunque schema.

10. **File di `infra` dentro `supabase/`.** `supabase/functions/Dockerfile` e `supabase/docker/docker-compose.yml` vanno a `infra`, perché sono nominati da quel profilo. Costo: nessuno di grave, sono configurazione di un contenitore.
    Proposta: lasciare così.

11. **I `.sql` nelle cartelle degli altri profili.** Un `.sql` dentro la cartella di un altro profilo resta a quel profilo: `server/db/schema.sql` resta a `backend`, `src/ai/queries.sql` ad `ai`, e lo stesso sotto `infra/`, `src/routes/` e `web/`. Costo: quel file non segue le regole del database; il lavoro però sale a L2 lo stesso, perché `database` è attivo.
    Proposta: lasciare così.

12. **Una fixture `.sql` o una cartella `tests/migrations/`.** `tests/fixtures/schema.sql` va a `database`, e una cartella di test che si chiama `tests/migrations/` pure. Costo: un lavoro sui soli test che le tocca sale a L2.
    Proposta: lasciare così; chi non lo vuole toglie il file o la cartella dal blocco.

13. **I comandi di Prisma e Drizzle che toccano il database chiedono il permesso.** Anche `prisma migrate dev`, che serve per lo sviluppo ma scrive sullo stesso database e può proporre di azzerarlo. Costo: ogni `migrate dev` o `db push` chiede il permesso, anche con un database locale; sul tuo disco ci sono due progetti con Prisma e uno con Drizzle.
    Proposta: tenerlo così, dalla parte sicura.

14. **`database-reviewer` non è una fonte.** È l'agente di un plugin che hai disattivato; i suoi punti stanno già nelle due skill e nelle pagine di Supabase. Costo: nessuno.
    Proposta: non citarlo.

15. **`dod` vuoto.** Il catalogo proponeva «migrazione applicata e annullata su un database vuoto», ma serve lo stack locale di Supabase o un PostgreSQL, e Supabase non ha file «down». Il profilo parte senza controlli in `dod`. Costo: nessun controllo automatico in più finché non lo aggiungi (l'esempio sta in «Cosa cambia»).
    Proposta: lasciarlo vuoto, come `infra`, `backend` e `frontend`.

16. **Alembic e Rails restano fuori.** Le migrazioni di Alembic (`alembic/versions/`) e di Rails (`db/migrate/`, `db/schema.rb`) non accendono il profilo. Sul tuo disco Alembic non c'è in nessun progetto. Costo: una migrazione di Alembic o di Rails non segue le regole del database e non porta il lavoro in L2.
    Proposta: lasciarle fuori; chi ne ha le aggiunge a mano.

17. **I temi «scelta nostra».** Sei regole hanno una parte che va oltre le fonti, scritta da noi: R-DATABASE-01 (i percorsi di schema e migrazioni nel report), R-DATABASE-02 (la via d'uscita per i progetti che non dichiarano la versione), R-DATABASE-04 (il report dice come si annulla la migrazione), R-DATABASE-05 (l'eccezione per una tabella creata nello stesso lavoro), R-DATABASE-06 (il report dichiara il blocco o la riscrittura di una tabella) e R-DATABASE-15 (il report motiva `verify_jwt = false`). Costo: qualche riga in più nel report; senza queste parti le regole non si potrebbero rispettare o giudicare.
    Proposta: tenerle tutte e sei.
