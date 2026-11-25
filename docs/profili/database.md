# Regole del profilo database di tollgate

Questa pagina è per te: dice quali sono le regole per il codice che cambia il database (migrazioni, schema, policy di accesso, funzioni del database, edge function di Supabase), cosa cambia nei tuoi progetti e cosa hai deciso su diciassette punti dubbi. Le regole sono approvate e il profilo si può accendere.

Approvata dall'utente il 2026-11-17.

Il 2026-11-24, con il tuo OK, è stata corretta una frase su `verify` e `dod`.

## Cosa sono

Sono sedici regole in più rispetto a quelle di base. Quindici di queste bloccano il lavoro se non sono rispettate. Dicono, per esempio, di leggere prima le migrazioni che ci sono già, di non modificare una migrazione già scritta, di accendere la protezione delle righe (RLS) su ogni tabella nuova e di non mandare nessuna scrittura al database vero senza il tuo permesso.

Qualche parola, la prima volta che serve:

- **Schema**: la forma del database, cioè quali tabelle e quali colonne ha. Nel codice sta in un file `.sql`, in `schema.prisma` o in un file di Drizzle.
- **Migrazione**: un file che cambia lo schema di un passo (aggiunge una tabella, una colonna, un indice). Le migrazioni si applicano una dopo l'altra, e una già applicata non si deve cambiare: se ne scrive una nuova.
- **RLS** (protezione delle righe): un interruttore di PostgreSQL per ogni tabella. Se è acceso, nessuno vede o cambia le righe se non c'è una policy che lo permette. Se è spento su una tabella che l'API espone, chiunque conosca l'indirizzo del progetto può leggere e cambiare tutto.
- **Policy**: la regola che dice chi può leggere, inserire, cambiare o cancellare le righe di una tabella con RLS accesa.
- **Edge function**: un piccolo programma che gira sui server di Supabase, scritto in TypeScript. Sta in `supabase/functions/<nome>/`.
- **Specialista finale**: un revisore in più che guarda il lavoro intero alla fine, e solo per un tipo di codice. Quello del database è `final-database` e lavora quando il lavoro è di livello L2.
- **Livello L2**: i lavori grandi. Chiedono una specifica (spec) e un piano che tu approvi prima di scrivere codice. Un lavoro L1 è medio, L0 è piccolo.
- **CLI**: il programma da riga di comando di un servizio, qui `supabase`, `prisma` o `drizzle-kit`: si usa scrivendo comandi nel terminale.
- **Supabase**: il servizio che ospita il database PostgreSQL e le edge function di molti tuoi progetti. Ha una cartella `supabase/` nel repo e un programma da riga di comando, `supabase`.
- **PostgreSQL**: il database che sta sotto Supabase. Altri database (SQLite di Cloudflare D1, MySQL di Laravel) hanno altre regole.
- **Prisma** e **Drizzle**: due librerie per descrivere lo schema e le migrazioni nel codice; hanno i loro programmi da riga di comando (`prisma`, `drizzle-kit`).
- **Progetto collegato**: il progetto Supabase vero a cui la cartella locale è legata con `supabase link`. Un comando che lo scrive cambia i dati e le funzioni di produzione.
- **Indice**: una scorciatoia che rende veloce cercare nelle righe di una colonna. PostgreSQL non lo crea da sé per una chiave esterna.
- **Chiave esterna**: la colonna che punta a una riga di un'altra tabella.
- **Vista**: una tabella finta, il risultato salvato di una domanda al database. In uno schema esposto dall'API può saltare le policy se non è scritta con cura.
- **Profilo**: un gruppo di regole, di agenti e di file che tollgate usa per un tipo di lavoro (qui il database; ce ne sono altri, come `backend` o `frontend`).
- **Percorso esatto**: il nome completo di un solo file, scritto nel `tollgate.toml`. Vince su ogni cartella.
- **Percorso per estensione**: un percorso che vale per tutti i file con una certa estensione, scritto come `**/*.sql`.
- **Marcatore**: una riga di codice che `init` cerca nei file per riconoscere un tipo di lavoro (qui, la riga che importa le tabelle di Drizzle).
- **`tollgate.toml`**: il file di impostazioni di tollgate nella radice del progetto.
- **`dod`**: la lista dei controlli che devono essere verdi a fine lavoro.

Le regole valgono per chi scrive il codice e per chi lo rivede. Chi rivede guarda tre cose. Il «diff» è l'elenco delle righe cambiate. Il «report» è il resoconto che l'agente scrive alla fine. La «nota di ricerca» è l'elenco di cosa ha letto prima di scrivere. Per ogni regola chi rivede risponde sì o no. La colonna «Si giudica su» dice su quale delle tre guarda: nessuna regola di questo profilo si giudica sulla sola nota.

Nove regole su sedici riguardano solo PostgreSQL e Supabase, e lo dicono nel loro testo: dove il database è un altro (SQLite, MySQL, Django) chi rivede risponde che non si applicano, e le altre valgono lo stesso.

## Quando si accende

Il profilo non si accende da solo. Si accende solo in un progetto dove il comando `/tollgate:init` lo propone e tu copi il blocco proposto nel `tollgate.toml` del progetto. `init` lo propone solo dopo che le regole sono approvate. Un progetto nuovo riceve la proposta con `/tollgate:init --propose`; uno che ha già tollgate con `/tollgate:init --update`. Conta nei lavori dei livelli L1 e L2, cioè medi e grandi; un lavoro piccolo (L0) lo scrive la sessione principale, senza task e senza agenti per area.

`init` lo propone in quattro casi.

1. Se nel progetto c'è la cartella `supabase/` alla radice (migrazioni, `config.toml`, `seed.sql`, test, edge function).
2. Se nel progetto c'è una cartella `migrations/` a qualunque profondità, anche dentro `server/`, `api/` o `infra/`; oppure la cartella `prisma/` alla radice.
3. Se nel progetto ci sono file `.sql`. `init` scrive un solo percorso, `**/*.sql`.
4. Se un file di codice contiene la riga che importa le tabelle o la configurazione di Drizzle, nelle due forme di virgolette (`'` e `"`): `from 'drizzle-orm/pg-core'` e `from 'drizzle-kit'`. Il file entra nel profilo con il suo percorso esatto, anche dentro `server/`.

Cosa non lo accende, e perché:

- Il codice che **usa** il database: un client di Supabase in `src/lib/supabase.ts`, le query di un server, `@prisma/client`, `pg`. Va al profilo della sua cartella o all'agente generico.
- Le migrazioni di Alembic e di Rails, e i file `drizzle/meta/*.json` che scrive `drizzle-kit` da solo (i suoi `.sql` sì).
- Una cartella `supabase/` o `prisma/` dentro un'altra cartella (un monorepo): vale solo la radice (punto 4 di «Cosa hai deciso»).

**Le precedenze.** I percorsi per estensione (qui `**/*.sql`) perdono contro ogni cartella di un altro profilo e contro ogni file nominato da un altro profilo. Esempi, tutti provati sul codice di `init`:

- `supabase/functions/og/index.tsx` va a `database` (la cartella `supabase/` ha un pezzo di percorso, `**/*.tsx` nessuno), mentre `src/main.tsx` resta a `frontend`.
- `server/migrations/001.sql` va a `database` (due pezzi di percorso contro uno), mentre `server/db/schema.sql` resta a `backend`.
- `src/ai/migrations/1.sql` va a `database` (tre pezzi contro due); `src/ai/queries.sql` resta ad `ai`.
- Lo schema di Drizzle `server/db/schema.ts`, con il suo import, va a `database` anche dentro `server/`: un percorso esatto vince sulla cartella.
- `prisma/schema.prisma` e `prisma/migrations/…` vanno a `database` (nessun altro profilo li nomina).

## Le regole

| N. | In parole semplici | Blocca? | Si giudica su | Da dove viene |
|---|---|---|---|---|
| 1 (R-DATABASE-01) | Se il lavoro aggiunge o cambia una migrazione o uno schema, il report elenca (con i percorsi) lo schema e le migrazioni che c'erano già e che ha letto prima di scrivere, oppure dice che non ce n'erano. | sì | il report | Una proposta del progetto di B che hai rivisto (sezione 3.4). I percorsi nel report sono una scelta nostra. |
| 2 (R-DATABASE-02) | La prima volta che un file usa un'istruzione, una funzione o un'opzione tipica di PostgreSQL o di Supabase, il report ha l'indirizzo della pagina ufficiale per la versione del progetto (`major_version` in `supabase/config.toml`, o la versione di PostgreSQL che il progetto dichiara), con la versione. Se il progetto non la dichiara, il report lo dice e dà l'indirizzo della documentazione corrente. | sì | il report | Il progetto di B (sezione 3.4) e le pagine di PostgreSQL e di Supabase sulla cartella `supabase/` e sulla sua configurazione. Il caso senza versione è una scelta nostra. |
| 3 (R-DATABASE-03) | Una migrazione che esisteva prima del lavoro (sul ramo di partenza) non si modifica e non si cancella: ogni cambio allo schema è un file di migrazione nuovo. | sì | il diff | Le pagine di Supabase e di Prisma sulle migrazioni e la skill `deprecation-and-migration` (MIT). |
| 4 (R-DATABASE-04) | Per ogni migrazione nuova il report dice come si annulla: il file o i passi che riportano lo stato indietro, oppure che non si può annullare e perché. | sì | il report | Il catalogo dei profili (sezioni 2.1 e 2.3) e la skill `deprecation-and-migration` (MIT). Che lo scriva il report è una scelta nostra. |
| 5 (R-DATABASE-05) | Il lavoro non rinomina e non toglie in un solo passo una colonna o una tabella che può avere dati: prima si aggiunge il nuovo e si copiano i dati, poi, in una migrazione successiva, si toglie il vecchio. Fa eccezione una tabella creata nello stesso lavoro. | sì | il diff | La skill `deprecation-and-migration` (MIT). L'eccezione è una scelta nostra. |
| 6 (R-DATABASE-06) | Se il lavoro, su una tabella che non crea lui, crea un indice senza `concurrently`, aggiunge una colonna con un valore predefinito che cambia a ogni riga, cambia il tipo di una colonna o imposta `not null` senza un vincolo `check` già valido, il report lo dice e spiega perché il blocco è accettabile o come l'ha evitato. Solo PostgreSQL. | sì | il report | Le pagine di PostgreSQL sul comando che crea un indice e su quello che cambia una tabella, e la skill `deprecation-and-migration` (MIT). Che lo dichiari il report è una scelta nostra. |
| 7 (R-DATABASE-07) | Una tabella nuova in uno schema che l'API espone (in Supabase, `public`) ha RLS accesa nella stessa migrazione e le policy per i ruoli che devono accedervi. Solo PostgreSQL e Supabase. | sì | il diff | Le pagine di Supabase sulla RLS e sull'Advisor (l'avviso sulle tabelle senza RLS) e la pagina di PostgreSQL sulla sicurezza per riga. |
| 8 (R-DATABASE-08) | Ogni policy nomina il ruolo e riguarda una sola operazione (lettura, inserimento, modifica o cancellazione), non tutte insieme; `anon` con `using (true)` solo per dati pubblici. Solo PostgreSQL e Supabase. | no | il diff | Le pagine di Supabase sulla RLS e di PostgreSQL sulle policy. |
| 9 (R-DATABASE-09) | In una policy `auth.uid()` e le altre funzioni `auth.*` stanno dentro `(select …)`, così si calcolano una volta per istruzione e non per ogni riga. Solo PostgreSQL e Supabase. | sì | il diff | Le pagine di Supabase sulla RLS e sull'Advisor, e la skill `supabase-postgres-best-practices` (MIT). |
| 10 (R-DATABASE-10) | Una policy nuova ha un indice sulle colonne che filtra, e una chiave esterna nuova ha un indice sulla sua colonna. Solo PostgreSQL e Supabase. | sì | il diff | Le pagine di Supabase sulla RLS e sull'Advisor, e la skill `supabase-postgres-best-practices` (MIT). |
| 11 (R-DATABASE-11) | Una funzione `security definer` (che gira con i permessi di chi l'ha scritta) fissa `search_path` e scrive lo schema davanti a ogni tabella che usa; dove basta si sceglie `security invoker`, che è il predefinito. Solo PostgreSQL e Supabase. | sì | il diff | Le pagine di Supabase sulle funzioni del database e sull'Advisor, e la pagina di PostgreSQL sulle funzioni. |
| 12 (R-DATABASE-12) | Una vista in uno schema esposto dall'API si crea con `security_invoker = true`, altrimenti ignora le policy di chi la interroga. Solo PostgreSQL (dalla 15) e Supabase. | sì | il diff | Le pagine di Supabase sulla RLS e sull'Advisor. |
| 13 (R-DATABASE-13) | Nessuna chiave segreta, password del database o chiave `service_role` di Supabase in un file versionato né nel codice che gira nel browser: stanno nelle variabili d'ambiente o nei segreti del servizio. | sì | il diff | Le pagine di Supabase sulla RLS e sui segreti delle funzioni. |
| 14 (R-DATABASE-14) | Una edge function di Supabase legge i segreti con `Deno.env.get` e non li scrive nel codice; il lavoro non aggiunge `supabase/functions/.env`. Solo Supabase. | sì | il diff | Il progetto di B (sezione 12) e la pagina di Supabase sui segreti delle funzioni. |
| 15 (R-DATABASE-15) | Se il lavoro mette `verify_jwt = false` in `[functions.<nome>]` di `supabase/config.toml`, il report dice perché la funzione deve poter essere chiamata da chiunque e come si protegge in altro modo. Solo Supabase. | sì | il report | La pagina di Supabase sulla configurazione delle funzioni. Che il report lo motivi è una scelta nostra. |
| 16 (R-DATABASE-16) | Il lavoro non scrive sul progetto collegato né su un database vero. Il report non riporta comandi lanciati da lui che lo facciano (`supabase db push` verso il progetto remoto, `supabase functions deploy`, `supabase secrets set`, `supabase link`, `prisma migrate deploy`, `prisma db push`, `drizzle-kit push`, `drizzle-kit migrate`) e dice quale prova ha fatto, o perché non l'ha fatta. | sì | il report | Il progetto di B (sezione 14), la spec del nucleo (sezione 8.5) e le pagine di Supabase, Prisma e Drizzle sui loro comandi. |

La colonna «Blocca?» dice quali regole sono le più serie. Se una di queste non è rispettata, chi rivede ferma il task. L'altra (la regola 8) è segnalata ma non lo ferma. Un difetto viene segnalato una sola volta.

Le fonti sono state controllate una per una. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/database-fonti.md`. Anche ogni cartella, ogni estensione e ogni riga di codice che accende il profilo ha una fonte: le pagine ufficiali di Supabase, Prisma e Drizzle per le cartelle e le righe di codice; il catalogo (cioè una tua scelta) per `**/migrations/**` e `**/*.sql`.

## Cosa cambia nei tuoi progetti

**Il lavoro sale a L2.** Il profilo ha `min_level = "L2"`: un cambio di schema è delicato, e il progetto di B lo voleva così. Un lavoro avviato in L1 che tocca una migrazione, un file di `supabase/` o di `prisma/` o un file SQL sale a L2 al primo ricalcolo e torna a chiedere spec e piano approvati. Un cambio piccolo a un `.sql` fuori da `migrations/` porta tutto il lavoro in L2: è il costo. Consiglio: un lavoro che tocca il database avvialo direttamente in L2. Il profilo resta attivo anche quando il file va a un altro profilo (un file SQL sotto `server/`): il lavoro sale a L2 lo stesso.

**Il gate della PR lo controlla.** Il gate è il controllo prima di aprire la pull request. Ferma un lavoro dichiarato sotto L2 che tocca file del profilo, con l'esito `level_below_minimum`.

**Revisione finale.** Lo specialista finale lavora nei lavori L2: con il profilo attivo la revisione finale ha un revisore in più, `final-database`, che guarda solo il diff e la lista di controllo del profilo (migrazioni reversibili e dati esistenti; con PostgreSQL anche RLS sulle tabelle nuove e indici delle policy e delle chiavi esterne). Parte con `/tollgate:finish`. Costo: un agente in più, con qualche migliaio di parole di istruzioni in più da leggere, più il diff. I tre agenti del profilo (`implementer-database`, `reviewer-database` e questo) arrivano dopo la tua approvazione; fino ad allora la proposta di `init` non ha lo specialista.

**Chi ha già dichiarato il blocco a mano.** Se nel `tollgate.toml` c'è già un `[profiles.database]` scritto da te, `init --update` non gli propone niente di nuovo: aggiungi tu `min_level = "L2"` e `checklist` (la frase per la lista di controllo dello specialista).

**`dod` e comandi restano vuoti.** Applicare e annullare una migrazione vuole lo stack locale di Supabase (Docker) o un PostgreSQL, che cambiano da progetto a progetto, e un comando scritto da `init` fallirebbe dove il programma manca. Se vuoi un controllo in più lo scrivi tu nel `tollgate.toml`, per esempio così:

```
[profiles.database]
commands = { db_reset = "supabase db reset --local", db_test = "supabase test db" }
dod = ["db_reset", "db_test"]
```

Attenzione: i comandi di `dod` li lancia tollgate stesso a fine lavoro, senza chiedere e senza nessun controllo sugli effetti, con le credenziali che hai salvato sul computer. Un comando lì dentro non deve mai avere `--remote`, `--linked` né `--db-url`: scriverebbe sul progetto vero. L'agente `implementer-database` non lancia mai `supabase`, `psql`, `docker`, `prisma`, `drizzle-kit` né un lanciatore di pacchetti: le prove del database passano da `verify`, che esegue i controlli del progetto e i comandi che scrivi nella riga `gate` del blocco del profilo. I comandi di `dod` girano solo a fine lavoro: se vuoi un comando anche durante il task, aggiungi anche a `gate` i comandi, nello stesso ordine (per esempio `gate = ["db_reset", "db_test"]`); i comandi di `gate` girano anche nel controllo prima della pull request.

**Permessi della CLI di Supabase.** Da B7 tollgate guarda ogni comando `supabase` (anche dietro `npx`) e chiede il permesso prima di quelli che possono scrivere sul progetto vero. È la scelta che hai fatto il 12 novembre, e vale in tutti i progetti, non solo con il profilo database. La regola è chiusa: un comando passa senza chiedere solo se sta in una lista; tutto il resto chiede, compresi i comandi che la CLI aggiungerà.

- Passano sempre: i comandi locali (`init`, `start`, `stop`, `status`, `migration new`, `functions new`, `functions serve`, `test new` e simili, e `--help` o `--version`) e le letture del progetto collegato (`functions list`, `functions download`, `secrets list`, `projects list`, `orgs list`, `branches list`, `snippets list`).
- Chiedono solo se c'è un'opzione che punta al progetto vero (`--remote`, `--linked`, `--db-url`, `--project-ref`, `--project-id`): `db reset`, `db lint`, `db query`, `db advisors`, `db diff`, `db dump`, `migration list`, `migration squash`, `gen types`, `test db`, `inspect db`, `inspect report`, `seed buckets`.
- Chiedono salvo `--local`: `db push`, `db pull`, `migration up`, `migration down`, `migration repair`, `migration fetch`. Costo: con la CLI 3 un `db push` in locale senza `--local` chiede il permesso. L'opzione `--local` è deprecata nella CLI 3 e sparisce nella 4: allora questa lista andrà rivista.
- Chiedono sempre: `functions deploy`, `secrets set`, `link`, `unlink`, `config push`, `storage ls` e gli altri comandi `storage`, `bootstrap`, `login`, `logout`, `branches get` e tutto ciò che non è nelle liste sopra. Anche `login` e `logout` chiedono, perché cambiano l'accesso al servizio.
- Un lint o una formattazione della cartella `supabase` dietro un lanciatore chiede il permesso: per esempio `npx eslint supabase --fix`, perché la parola `supabase` dopo il lanciatore sembra un comando della CLI. Costo: un permesso in più, nessun rischio.
- Con la CLI 2 i comandi `db dump`, `migration list` e `inspect db` senza opzioni potevano leggere il progetto collegato, e qui passano senza chiedere: chi ha ancora la CLI 2 fa una lettura del progetto vero senza permesso. Con la CLI 3 leggono il database locale.

**Permessi di Prisma e Drizzle.** Chiede il permesso ogni comando che scrive sul database configurato, anche quelli pensati per lo sviluppo: `prisma migrate dev`, `prisma migrate deploy`, `prisma migrate reset`, `prisma migrate resolve`, `prisma db push`, `prisma db execute`, `prisma db seed`, `prisma studio`; con Prisma 8 (ancora in versione di prova) anche `prisma db init`, `prisma db update`, `prisma db migrate` e `prisma db sign`; con Drizzle `drizzle-kit push`, `drizzle-kit migrate`, `drizzle-kit studio` e le forme vecchie `push:pg`, `push:mysql`, `push:sqlite`. Passano liberi i comandi che non toccano il database (`prisma generate`, `prisma format`, `prisma validate`, `drizzle-kit generate`, `drizzle-kit check`) e le letture (`prisma db pull`, `prisma migrate status`, `drizzle-kit pull`). Due costi. Primo: un'opzione di `prisma` prima del sottocomando (per esempio `prisma --config x migrate deploy`) non è guardata, e quella scrittura passa senza chiedere. Secondo: anche lo sviluppo con un database locale chiede il permesso a ogni `migrate dev` o `db push`.

**Un `.tsx` dentro `supabase/` cambia profilo.** La pagina approvata di `frontend` dice che `supabase/functions/og/index.tsx` va a `frontend` finché non arriva il profilo del database: da qui in poi va a `database`. La pagina di `frontend` non si tocca; la differenza sta nel piano e nella spec.

**Un `.sql` dentro la cartella di un altro profilo resta a quel profilo.** Vale per `server/`, `src/ai/`, `infra/`, `src/routes/` e `web/` (punto 11 di «Cosa hai deciso»).

## Cosa hai deciso

Su diciassette punti la fonte non diceva proprio quello che la regola chiede, o la scelta era tua, o la proposta aveva un costo che dovevi conoscere. Hai approvato la proposta in tutti e diciassette: resta quella scritta sotto, e i numeri delle regole non cambiano più.

1. **`**/migrations/**` è largo.** Il percorso `**/migrations/**` accende ogni cartella che si chiama `migrations/`, anche una che non è di database. Un componente in `src/components/migrations/` (per esempio `List.tsx`) va a `database` invece che a `frontend` (tre pezzi di percorso contro due). Lo stesso una rotta di Next.js che si chiama come la cartella, `app/migrations/` con la sua `page.tsx`, più probabile del primo caso. Sul tuo disco non ho trovato nessun componente così. Costo: un file d'interfaccia segue le regole del database e il lavoro sale a L2.
   Proposta: tenerlo largo, perché il catalogo lo chiede e copre le migrazioni di tutti gli strumenti. Chi ha un caso toglie la riga dal blocco a mano.
   Hai approvato la proposta.

2. **Un documento dentro `docs/migrations/`.** Un file `.md` non accende da solo la cartella, ma se lì dentro c'è anche un `.sql` d'esempio la cartella `docs/migrations/` entra nel profilo e porta con sé anche i documenti. Costo: un documento segue le regole del database.
   Proposta: lasciare così.
   Hai approvato la proposta.

3. **`**/schema.*` resta fuori.** Il catalogo lo elencava. Non lo metto perché sul tuo disco 18 file `schema.*` sono immagini, file `.graphql`, `.json` e `.ts` di validazione, e ognuno entrerebbe con il suo percorso esatto, che vince su ogni cartella. Gli schemi `.sql` sono già presi da `**/*.sql`, quelli di Prisma da `prisma/**`, quelli di Drizzle dalla riga di import. Costo: un `schema.ts` che non importa `drizzle-orm/pg-core` va all'agente generico.
   Proposta: lasciarlo fuori.
   Hai approvato la proposta.

4. **`supabase/` e `prisma/` valgono solo alla radice.** In un monorepo la cartella `apps/web/supabase/` o `packages/db/prisma/` non entra per nome: le migrazioni dentro vanno comunque a `database` (per `**/migrations/**`), il resto no. Una edge function sotto `apps/api/supabase/` con `Deno.serve(` va a `backend`; sotto `web/supabase/` la funzione e il suo `config.toml` vanno a `frontend`; lo schema in `packages/db/prisma/` va all'agente generico; lo schema in `server/prisma/` va a `backend`. Costo: nessun monorepo con Supabase annidato tra i tuoi progetti, a parte uno con codice di terzi; ma se ne arriva uno, le sue funzioni e il suo schema non seguono le regole del database.
   Proposta: lasciare così; chi ha un monorepo aggiunge a mano la sua cartella al blocco.
   Hai approvato la proposta.

5. **Uno schema di Drizzle trovato anche da `ai` o da `backend`.** Un file come `src/index.ts` che importa `drizzle-orm/pg-core` e anche un framework di server è trovato da due profili con lo stesso peso. Vince il primo blocco del `tollgate.toml`, e `init` scrive i blocchi in ordine alfabetico: `database` perde contro `ai` e `backend` e vince contro `frontend` e `infra`. Costo: lo schema segue le regole di `backend`.
   Proposta: lasciare così.
   Hai approvato la proposta.

6. **Edge function e file di Prisma che vanno ad `ai`.** Una edge function che importa un programma per i modelli (`supabase/functions/chat/index.ts`) va ad `ai`, perché un percorso esatto di `ai` vince. Lo stesso una funzione in `supabase/functions/agents/`, che non ha nessuna riga particolare: `ai` accende ogni cartella che si chiama `agents/` per il nome e vince per tre pezzi di percorso contro uno; e un file in `supabase/functions/chat/prompts/`; e `prisma/seed.ts` che importa un programma per i modelli. Costo: va contro la tua scelta del progetto di B (le edge function stanno a `database`) in questi casi. Il rimedio sarebbe un `exclude` nel profilo `ai`, cioè una revisione di `rules-ai` con te.
   Proposta: lasciare così (è codice che parla con un modello, quindi difendibile) e rimandare il rimedio.
   Hai approvato la proposta.

7. **`prisma/ai/` va ad `ai`.** Un file dentro `prisma/ai/`, per esempio un seme `seed.sql`, va ad `ai`: la cartella ha due pezzi di percorso contro uno di `prisma/**`. Costo: come il punto 6, un file di database segue le regole di `ai`.
   Proposta: lasciare così.
   Hai approvato la proposta.

8. **Prisma 8 e il contratto.** Prisma 8 (ancora in versione di prova) scrive il contratto in `src/prisma/contract.prisma`, fuori dalla cartella `prisma/` alla radice, e `prisma/**` non lo copre. Va al profilo della sua cartella o all'agente generico. Costo: un cambio a quel file non segue le regole del database e non porta il lavoro in L2.
   Proposta: lasciare così e riprendere il caso quando Prisma 8 esce e un tuo progetto lo usa.
   Hai approvato la proposta.

9. **Migrazioni di altri database.** `**/migrations/**` porta nel profilo anche le migrazioni di SQLite di Cloudflare D1 (`migrations/0001_init.sql` alla radice, accanto a `wrangler.toml`), di MySQL con Laravel (`database/migrations/`) e di Django (`blog/migrations/` dentro un server). Le regole che parlano di RLS, policy, `security definer`, `concurrently` e edge function sono di PostgreSQL e Supabase: per un altro database chi rivede risponde che non si applicano. Le altre (leggere prima schema e migrazioni, una migrazione nuova invece di modificarne una, come si annulla, i dati esistenti) valgono per tutti. Costo: il profilo propone anche regole che per quei progetti non servono.
   Proposta: tenere così, perché sono comunque schema.
   Hai approvato la proposta.

10. **File di `infra` dentro `supabase/`.** `supabase/functions/Dockerfile` e `supabase/docker/docker-compose.yml` vanno a `infra`, perché sono nominati da quel profilo. Costo: nessuno di grave, sono configurazione di un contenitore.
    Proposta: lasciare così.
    Hai approvato la proposta.

11. **I `.sql` nelle cartelle degli altri profili.** Un `.sql` dentro la cartella di un altro profilo resta a quel profilo: `server/db/schema.sql` resta a `backend`, `src/ai/queries.sql` ad `ai`, e lo stesso sotto `infra/`, `src/routes/` e `web/`. Costo: quel file non segue le regole del database; il lavoro però sale a L2 lo stesso, perché `database` è attivo.
    Proposta: lasciare così.
    Hai approvato la proposta.

12. **Una fixture `.sql` o una cartella `tests/migrations/`.** `tests/fixtures/schema.sql` va a `database`, e una cartella di test che si chiama `tests/migrations/` pure. Costo: un lavoro sui soli test che le tocca sale a L2.
    Proposta: lasciare così; chi non lo vuole toglie il file o la cartella dal blocco.
    Hai approvato la proposta.

13. **I comandi di Prisma e Drizzle che toccano il database chiedono il permesso.** Anche `prisma migrate dev`, che serve per lo sviluppo ma scrive sullo stesso database e può proporre di azzerarlo. Costo: ogni `migrate dev` o `db push` chiede il permesso, anche con un database locale; sul tuo disco ci sono due progetti con Prisma e uno con Drizzle.
    Proposta: tenerlo così, dalla parte sicura.
    Hai approvato la proposta.

14. **`database-reviewer` non è una fonte.** È l'agente di un plugin che hai disattivato; i suoi punti stanno già nelle due skill e nelle pagine di Supabase. Costo: nessuno.
    Proposta: non citarlo.
    Hai approvato la proposta.

15. **`dod` vuoto.** Il catalogo proponeva «migrazione applicata e annullata su un database vuoto», ma serve lo stack locale di Supabase o un PostgreSQL, e Supabase non ha file «down». Il profilo parte senza controlli in `dod`. Costo: nessun controllo automatico in più finché non lo aggiungi (l'esempio sta in «Cosa cambia»).
    Proposta: lasciarlo vuoto, come `infra`, `backend` e `frontend`.
    Hai approvato la proposta.

16. **Alembic e Rails restano fuori.** Le migrazioni di Alembic (`alembic/versions/`) e di Rails (`db/migrate/`, `db/schema.rb`) non accendono il profilo. Sul tuo disco Alembic non c'è in nessun progetto. Costo: una migrazione di Alembic o di Rails non segue le regole del database e non porta il lavoro in L2.
    Proposta: lasciarle fuori; chi ne ha le aggiunge a mano.
    Hai approvato la proposta.

17. **I temi «scelta nostra».** Sei regole hanno una parte che va oltre le fonti, scritta da noi: R-DATABASE-01 (i percorsi di schema e migrazioni nel report), R-DATABASE-02 (la via d'uscita per i progetti che non dichiarano la versione), R-DATABASE-04 (il report dice come si annulla la migrazione), R-DATABASE-05 (l'eccezione per una tabella creata nello stesso lavoro), R-DATABASE-06 (il report dichiara il blocco o la riscrittura di una tabella) e R-DATABASE-15 (il report motiva `verify_jwt = false`). Costo: qualche riga in più nel report; senza queste parti le regole non si potrebbero rispettare o giudicare.
    Proposta: tenerle tutte e sei.
    Oltre alle sei regole, hai approvato anche l'introduzione della skill: riconoscere uno schema SQL da un `create table` in un file `.sql` è una scelta nostra, non delle fonti. È il modo in cui chi rivede trova uno schema nel diff; senza, un file `.sql` con una tabella nuova non sarebbe riconosciuto come schema.
    Hai approvato la proposta.

## Regole tolte dalla verifica

Nessuna regola è uscita: ciascuna ha almeno una fonte che regge per ogni voce, e i numeri restano. Rispetto alla bozza verificata sono cambiate tre regole, senza aggiungere o togliere fonti che reggevano:

- La regola 16 citava due cose che le pagine non dicevano: che `functions deploy` e `secrets set` lavorano sul progetto collegato, e che i comandi di Prisma scrivono sul database di `DATABASE_URL`. Ora cita le due pagine di Supabase che lo dicono, e per Prisma dice «il database configurato».
- La regola 3 parlava di una migrazione «già presente nel repo»: ora dice una migrazione che esisteva prima del lavoro, sul ramo di partenza, così il revisore la riconosce nel diff.
- La regola 6 parlava di una tabella «che ha già dati»: ora una tabella che il diff non crea, perché il revisore non vede i dati.

La regola 2 ha una fonte in più, la pagina della configurazione di Supabase, per `major_version`. Nessun percorso e nessuna riga di codice è uscito.
