# Regole del profilo backend di tollgate

Questa pagina è per te: dice quali sono le regole per il codice dei server e delle API (anche i Worker di Cloudflare) e cosa hai deciso su nove punti dubbi. Le regole sono approvate e il profilo si può accendere.

Approvata dall'utente il 2026-11-10.

## Cosa sono

Sono dodici regole in più rispetto a quelle di base. Valgono solo per il codice che risponde alle richieste: un server, un'API, una funzione di Vercel o di Cloudflare Pages, una rotta di Next.js, un Worker di Cloudflare. Dicono, per esempio, di leggere i contratti già presenti prima di scrivere una rotta nuova, di controllare l'input prima di usarlo e di non scrivere mai un segreto nel codice.

Qualche parola, la prima volta che serve:

- **Server e API**: un server è un programma che resta in ascolto e risponde alle richieste. L'API è l'elenco di cose che gli si può chiedere.
- **Gestore**: la funzione che riceve una richiesta e prepara la risposta.
- **Rotta o endpoint**: uno di quegli indirizzi, per esempio `GET /health`. Nel codice è una funzione registrata come rotta di un server, un gestore esportato da un file di rotte (come `GET` o `POST` in un `route.ts`, o `onRequest` in `functions/`) oppure il gestore `fetch` di un Worker.
- **Edge function**: una funzione che gira sui server di un servizio (qui Supabase) invece che sul tuo.
- **`tollgate.toml`**: il file di impostazioni di tollgate nella radice del progetto.
- **Worker**: codice che gira sulla rete di Cloudflare e risponde alle richieste. Il suo punto d'ingresso non sta in una cartella fissa.
- **Wrangler**: il programma da riga di comando di Cloudflare. Con Wrangler si lavora anche sui dati di un Worker: **KV** (coppie chiave e valore, raccolte in «namespace», cioè in contenitori con un nome), **D1** (un database) e **R2** (file, raccolti in «bucket», cioè in contenitori con un nome).
- **`env` e `vars`**: `env` è l'oggetto da cui un Worker legge i suoi segreti e i suoi collegamenti ai servizi (i «binding»). `vars` è la parte della configurazione di Wrangler dove si scrivono variabili in chiaro: lì non vanno i segreti.
- **Segreto**: una chiave, un token o una password. Chi legge il repo o il log la vedrebbe.
- **Framework**: una libreria che organizza un server (Express, Fastify, Hono, FastAPI, Flask).
- **Validare l'input**: controllare che ciò che arriva dalla richiesta abbia la forma attesa prima di usarlo.
- **Query con parametri**: una richiesta al database che tiene separati il comando e i dati, così un dato non può diventare un comando.
- **Paginare**: restituire una lista a pezzi, un po' per volta, invece che tutta insieme.
- **`dod`**: la lista dei controlli che devono essere verdi a fine lavoro. Un **typecheck** è il controllo dei tipi del codice.
- **Monorepo**: un unico repository con più pacchetti, ognuno nella sua cartella.

Valgono per chi scrive il codice e per chi lo rivede. Chi scrive può essere un agente a cui è affidato un task, cioè un pezzo del lavoro. Può essere anche Claude Code che lavora direttamente con te.

Chi rivede guarda tre cose. Il «diff» è l'elenco delle righe cambiate. Il «report» è il resoconto che l'agente scrive alla fine. La «nota di ricerca» è l'elenco di cosa ha letto prima di scrivere. Per ogni regola chi rivede risponde sì o no. La colonna «Si giudica su» dice su quale delle tre guarda: la regola 3, per esempio, si giudica sul solo diff.

## Quando si accende

Il profilo non si accende da solo. Si accende solo in un progetto dove il comando `/tollgate:init` lo propone e tu copi il blocco proposto nel `tollgate.toml` del progetto. Un progetto nuovo riceve la proposta con `/tollgate:init --propose`; uno che ha già tollgate la riceve con `/tollgate:init --update`. In tutti e due i casi la copia la fai tu. Conta nei lavori dei livelli L1 e L2, cioè medi e grandi. Un lavoro piccolo (L0) lo scrive la sessione principale, senza task e senza agenti per area.

`init` lo propone in tre casi.

1. Se nel progetto c'è una di queste cartelle, **alla radice**:
   - `api/` (le funzioni di Vercel),
   - `server/` e `backend/`,
   - `functions/` (le funzioni di Cloudflare Pages).

2. Se c'è una cartella `routes/` o `handlers/`, a qualunque profondità.

3. Se un file di codice contiene una di queste righe, con cui un server si riconosce:
   - Worker di Cloudflare: `cloudflare:workers`, `from workers import` (Python) e `ExportedHandler<` (il tipo che il modello di base di Cloudflare usa per il gestore `fetch`).
   - Framework e moduli di Node, nelle due forme di virgolette (`'` e `"`): `express` e `fastify` (con `require` o con `from`), `hono` e `node:http` (con `from`, e `node:http` anche con `require`).
   - Python e Deno: `from fastapi import`, `from flask import`, `Deno.serve(`.
   - Gestori di rotta di Next.js e di Vercel: `export function GET(`, `export async function GET(` e `export async function POST(`.

Cosa non lo accende, e perché:

- La cartella `services/` non lo accende. Sul tuo disco le cartelle `services/` stanno accanto a cartelle di interfaccia: sono codice che chiama le API, non un server. Finché non arriva il profilo dell'interfaccia (B6) i loro file vanno all'agente generico.
- Le edge function di Supabase e la cartella `supabase/` sono del profilo `database`. Il frammento di `backend` esclude `supabase/`: nessun file lì sotto lo accende, né per la cartella né per le righe di codice (`Deno.serve(`, per esempio).
- La configurazione di Wrangler e di Vercel e i file di Docker sono del profilo `infra`. Un task che tocca `wrangler.jsonc` e il codice del Worker è misto: va all'agente generico.
- Un Worker senza import da `cloudflare:workers` e senza il tipo `ExportedHandler`, o scritto in JavaScript senza tipi, non si trova da solo. Per quel caso c'è un punto in «Cosa hai deciso».
- La riga `export function POST(` non lo accende: nessuna pagina ufficiale la mostra (vedi «Regole tolte dalla verifica»). Un gestore `POST` senza `async` si trova solo se il file ha un'altra delle righe sopra o sta in una delle cartelle.

Un file trovato per le sue righe entra nel profilo con il suo percorso esatto. Gli altri file della stessa cartella (per esempio gli altri file di un Worker) non entrano e vanno all'agente generico; un task che tocca insieme un file trovato e uno no va comunque all'agente di `backend`. Un file nuovo con una di quelle righe entra con la riga che `/tollgate:init --update` ti propone. Un file senza quelle righe e fuori dalle cartelle non entra mai da solo: lo aggiungi a mano nel `tollgate.toml`.

## Le regole

| N. | In parole semplici | Blocca? | Si giudica su | Da dove viene |
|---|---|---|---|---|
| 1 (R-BACKEND-01) | Se il lavoro aggiunge o cambia una rotta, il report dice quali contratti già presenti ha letto (i tipi o gli schemi delle richieste e delle risposte, il file dove le rotte sono registrate), oppure che il progetto non ne ha. | sì | il report | Una proposta del progetto di B che hai rivisto (sezione 3.4). |
| 2 (R-BACKEND-02) | La prima volta che un file usa una parte del programma che serve le richieste (il gestore e i binding di un Worker, `Deno.serve`, il modulo `http` di Node, `http.server` di Python, un framework), il report ha l'indirizzo della pagina ufficiale della versione in uso. | sì | il report | La proposta del progetto di B che hai rivisto, per i Worker, le pagine di Cloudflare e la skill `workers-best-practices`. Libreria standard e framework sono una scelta nostra. |
| 3 (R-BACKEND-03) | Una rotta nuova o cambiata controlla corpo, parametri e query prima di usarli, e risponde con un errore del client (input sbagliato) quando non sono validi. | sì | il diff | La skill `api-and-interface-design` e i prompt di revisione di everything-claude-code, entrambi MIT. |
| 4 (R-BACKEND-04) | Gli errori di una rotta nuova hanno la stessa forma e gli stessi codici di stato già usati nel progetto o, se non ce ne sono, una forma sola. | sì | il diff | La skill `api-and-interface-design` (MIT). |
| 5 (R-BACKEND-05) | Se il lavoro toglie o rinomina un campo di una risposta, una rotta o un parametro già pubblici, o ne cambia il tipo, il report dice chi li usa e che il task chiedeva proprio quel cambiamento. | sì | il report | La skill `api-and-interface-design` (MIT). «Che il task lo chiede» è una scelta nostra. |
| 6 (R-BACKEND-06) | Le query al database e i comandi del sistema si scrivono con parametri, mai attaccando l'input della richiesta al testo. | sì | il diff | I prompt di revisione di everything-claude-code (MIT). |
| 7 (R-BACKEND-07) | Nessun segreto scritto nel codice né nei `vars` della configurazione di Wrangler. Nel codice di un Worker segreti e binding si leggono da `env`. | sì | il diff | Le pagine di Cloudflare sui binding e sui segreti, la skill `workers-best-practices` (Apache-2.0) e everything-claude-code (MIT). |
| 8 (R-BACKEND-08) | Un segreto, un token o una password non finisce in una riga di log né nel corpo di una risposta d'errore. | sì | il diff | La skill `observability-and-instrumentation` e everything-claude-code (MIT). |
| 9 (R-BACKEND-09) | Una rotta nuova o cambiata ha un test che la chiama con un caso riuscito, più un caso d'errore per ogni input che controlla e per ogni risorsa che può mancare. Senza input e senza risorse basta il caso riuscito. | sì | il diff | Il catalogo dei profili (i test delle API nella definizione di fatto). Il caso d'errore è una scelta nostra. |
| 10 (R-BACKEND-10) | Una rotta nuova che restituisce una lista la pagina. | no | il diff | La skill `api-and-interface-design` (MIT). |
| 11 (R-BACKEND-11) | Nomi di rotte, campi e parametri seguono la convenzione già usata nel progetto. | no | il diff | La skill `api-and-interface-design` (MIT). |
| 12 (R-BACKEND-12) | Se il lavoro tocca codice che legge o scrive KV, D1, R2 o un database, il report dice quale prova locale ha eseguito (per esempio una scrittura di Wrangler con `--local`) oppure perché non l'ha fatta. In ogni task il report non riporta comandi lanciati dall'agente che scrivono sui dati di un servizio in linea o che pubblicano. | sì | il report | La spec di tollgate sugli effetti esterni, il progetto di B (sezione 12) e le pagine di Wrangler. Riportare la prova locale è una scelta nostra. |

La colonna «Blocca?» dice quali regole sono le più serie. Se una di queste non è rispettata, chi rivede ferma il task. Le altre sono segnalate ma non lo fermano. Un difetto viene segnalato una sola volta.

Le fonti sono state controllate una per una. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/backend-fonti.md`. Anche ogni cartella e ogni riga di codice che accende il profilo ha una fonte: una pagina ufficiale per le righe di codice, per `api/` e per `functions/`; il catalogo e il progetto di B (cioè scelte tue) per `server/`, `backend/`, `routes/` e `handlers/`.

## Cosa cambia per i comandi

Tre cose da sapere, perché toccano il tuo modo di lavorare.

**Le scritture di Wrangler su KV, R2 e D1 chiedono la tua approvazione, salvo in locale.** Lo hai deciso tu per i dati di Cloudflare. Le scritture su KV e R2 chiedono l'approvazione a meno che il comando abbia `--local`. Quelle su D1 (`d1 execute`, `d1 migrations apply`) la chiedono solo con `--remote` o `--preview`, perché le prove locali di D1 sono le più frequenti. Anche creare o cancellare un namespace di KV, un bucket di R2 o un database D1 chiede l'approvazione. Le letture non la chiedono. Costo: con Wrangler 4 una scrittura locale di KV o R2 scritta senza `--local` chiede l'approvazione senza che serva. Per questo la regola 12 dice di scrivere `--local` nelle prove. C'è un secondo costo, ereditato dal profilo `infra`: dietro un lanciatore (un programma come `npx` che ne avvia un altro), una chiave o un valore che coincide col nome di un programma noto (per esempio `az`) fa chiedere l'approvazione.

**Un typecheck o i test delle API li aggiungi tu, a mano.** Il profilo parte senza un controllo nella definizione di «fatto» (la lista `dod`). Il comando dei test delle API e il typecheck cambiano da progetto a progetto (`pytest`, `vitest`, `tsc --noEmit`, `mypy`), e un comando scritto da tollgate fallirebbe dove il programma manca. Se vuoi un controllo in più, lo scrivi nel `tollgate.toml`, per esempio così:

```
[profiles.backend]
commands = { typecheck = "npx tsc --noEmit" }
dod = ["typecheck"]
```

Attenzione: i comandi di `dod` li lancia tollgate stesso a fine lavoro, senza chiedere e senza nessun controllo sugli effetti, con le credenziali che hai salvato sul computer. Un comando lì dentro non deve scrivere su un servizio. Un comando aggiunto a mano in `dod` che non produce un report dei test conta verde solo se nel `tollgate.toml` c'è `[project] allow_no_tests = true`, oppure se approvi con `/tollgate:approve unverified-tests`.

**Gli script `deploy` e `release` nei monorepo.** Da questa versione tollgate riconosce anche le forme con l'opzione del pacchetto, come `pnpm -F web run deploy` o `npm -w web run deploy`, e chiede l'approvazione come per lo script nudo. Restano scoperti i giri rari: gli script lanciati da un orchestratore di monorepo (un programma che lancia lo stesso script in più pacchetti, come `turbo run deploy` o `nx run web:deploy`) e le opzioni di Wrangler scritte prima del sottocomando.

## Cosa hai deciso

Su nove punti la fonte non diceva proprio quello che la regola chiede, o la scelta era tua. Hai approvato la proposta in tutti e nove: resta com'era scritta.

1. **Regola 2 (R-BACKEND-02), libreria standard e framework.** Le pagine che reggono la regola parlano dei Worker. Estenderla a `Deno.serve`, al modulo `http` di Node, a Python e ai framework è una scelta nostra, per avere sempre un indirizzo da controllare. Hai approvato: resta la proposta, cioè tenerla.
2. **Regola 5 (R-BACKEND-05), «e che il task lo chiede».** Le fonti dicono che cambiare ciò che è pubblico rompe chi lo usa. Chiedere che il report dica anche che il task voleva quel cambiamento è una scelta nostra: serve a chi rivede per capire se il cambio è voluto. Hai approvato: resta la proposta, cioè tenerla.
3. **Regola 9 (R-BACKEND-09), i casi d'errore.** Il catalogo chiede i test delle API. Un caso d'errore per ogni input controllato e per ogni risorsa che può mancare è una scelta nostra: è un obbligo più pesante. Hai approvato: resta la proposta, cioè tenerlo.
4. **Regola 12 (R-BACKEND-12), la prova locale nel report.** Nessuna fonte chiede di riportare la prova locale: è una scelta nostra, perché chi rivede possa vedere che i dati veri non sono stati toccati. Hai approvato: resta la proposta, cioè tenerla.
5. **`routes/` e `handlers/` sono troppo larghe.** Il catalogo e il progetto di B le mettono tra i percorsi del profilo, a qualunque profondità. Ma una cartella `routes/` può contenere anche le rotte di un'interfaccia (React Router, Remix, SvelteKit), e `handlers/` i gestori di eventi di un'interfaccia: quei file andrebbero all'agente `backend` per errore, e ci resterebbero. Hai approvato: resta la proposta, cioè tenerle, e togliere a mano la cartella dal `tollgate.toml` dove non serve.
6. **Il Worker senza import e senza tipo.** Un Worker che non importa da `cloudflare:workers` e non usa il tipo `ExportedHandler` (il caso più comune: il gestore `fetch` del modello di base) non si trova da solo, e il suo codice va all'agente generico. Anche un Worker in JavaScript senza tipi non si trova. Hai approvato: resta la proposta, cioè lasciare così; chi ne ha uno aggiunge a mano la sua cartella, per esempio `workers/`, nel `tollgate.toml`. Non la metto nel profilo perché `workers/` non è un nome che indichi sempre un Worker.
7. **Le cartelle valgono solo alla radice.** `api/`, `server/`, `backend/` e `functions/` valgono alla radice del progetto. In un monorepo il server di un pacchetto (per esempio `apps/api/`) non è coperto e va all'agente generico, a meno che un file abbia una delle righe che lo riconoscono. Hai approvato: resta la proposta, cioè lasciare così; chi ha un monorepo aggiunge la cartella a mano.
8. **`dod` vuoto.** Il catalogo proponeva «test delle API, typecheck» come definizione di fatto del profilo. Ho lasciato la lista vuota, perché il comando dipende dal progetto e uno scritto da `init` fallirebbe dove il programma manca. Hai approvato: resta la proposta, cioè lasciare vuota la lista e aggiungere il comando a mano, come nel profilo `infra`.
9. **`supabase/` dentro un pacchetto di monorepo.** L'esclusione vale per la cartella `supabase/` alla radice. Una cartella come `apps/api/supabase/functions/` non è esclusa, e il percorso proposto da `backend` lì vincerebbe su quello che il profilo del database (B7) proporrà per quel pacchetto. Hai approvato: resta la proposta, cioè lasciare così e riprendere il caso in B7.

## Regole tolte dalla verifica

Nessuna regola è uscita: ciascuna ha almeno una fonte che regge. Rispetto alla bozza che è stata verificata è cambiato questo:

- Due fonti sono state tolte dalle righe «Da dove viene»: la sezione della skill sulle API che parla di definire un contratto prima di scrivere (la regola 1 chiede di leggere quelli già presenti) e quella che non parla dei test di una rotta (regola 9).
- La regola 12 dichiara ora che riportare la prova locale è una scelta nostra. Le regole 5 e 9 lo dicevano già.
- La regola 7 è riscritta sui fatti della pagina dei segreti: niente segreti nel codice né nei `vars`, e nel Worker segreti e binding si leggono da `env`.
- La regola 8 cita una fonte in più, per la parte sul corpo delle risposte d'errore.
- Un riconoscimento del codice è uscito: la riga `export function POST(`, perché nessuna pagina ufficiale mostra quella forma senza `async`.

## Se vuoi cambiare qualcosa

Per ogni regola puoi dirmi una di queste tre cose.

- **Va bene così.** La regola resta com'è.
- **Cambiala.** Dimmi cosa cambiare. Una regola cambiata nel senso o con una fonte nuova passa di nuovo dal controllo delle fonti.
- **Toglila.** La regola esce e il suo numero non si riusa: le altre tengono il loro.

I numeri delle regole, ora che sono approvate, non cambiano più. Se vorrai cambiare, aggiungere o togliere una regola, me lo dici e la sistemo.
