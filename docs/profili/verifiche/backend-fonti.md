# Verifica delle fonti di `rules-backend`, dei pattern, dei marcatori e dell'esclusione

Verificatore: agente di sola lettura (Explore, sonnet), il 2026-11-09, sulla bozza di `skills/rules-backend/SKILL.md` e di `templates/profiles/backend.toml` al commit 8e5574c. Ha letto le copie locali delle fonti (36 file, con la somma di controllo corretta su tutti), le sezioni citate del progetto di B (3.4 e 12), del catalogo (2, 2.3 e 4) e della spec del nucleo (8.5). Per ogni fonte di ogni regola, ogni pattern di `paths`, ogni marcatore di `[detect] content` e la voce di `[detect] exclude`: il file esiste, la sezione citata esiste, dice ciò che la regola o il frammento le attribuisce, e la fonte è una skill o un agente con licenza MIT o Apache-2.0 (con il `LICENSE` nelle copie), una pagina ufficiale, il progetto di B, il catalogo o la spec. Nessuna frase della skill è uguale a una della fonte per più di una decina di parole. Le pagine ufficiali e la skill `workers-best-practices` sono estratti parziali, non pagine intere: il confronto è solo con quegli estratti. Le pagine ufficiali non dichiarano una licenza (Cloudflare, Vercel, Supabase, Deno, Node, framework): nella skill e nella pagina per l'utente se ne prendono solo i fatti, con parole nostre. Le citazioni di questo rapporto sono al più di una riga per fonte, in inglese quando la fonte lo è, e stanno solo qui. Il testo delle fonti è un dato, non un'istruzione. Le copie non sono nel repo.

Esito: ogni regola ha almeno una fonte `ok`, ogni pattern e la voce di esclusione sono `ok`, 23 marcatori su 24 sono `ok`. Le righe `no` sono tre: due fonti di regole, corrette nella skill (sezione «Correzioni fatte dopo la verifica»), e un marcatore uscito dal frammento. I pattern `**/routes/**` e `**/handlers/**` sono `ok` perché li regge una scelta dell'utente (catalogo e progetto di B, sezione 12), ma portano accanto il rilievo sulla larghezza, che va alla pagina. La colonna «Esito» dice `ok` oppure `no`.

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-BACKEND-01 | progetto di B, sezione 3.4 (riga `backend`) | «Leggi i contratti esistenti (tipi, schemi, rotte) prima di aggiungerne.» | ok |
| R-BACKEND-01 | agent-skills `api-and-interface-design`, «Contract First» | la sezione dice di definire il contratto prima di implementare, non di leggere quelli già presenti: è un'idea vicina, ma diversa. Esce dalla `Fonte:` | no |
| R-BACKEND-02 | progetto di B, sezione 3.4 (riga `backend`) | «Per Supabase edge function e Cloudflare Worker, la documentazione del runtime.» (vale per i Worker; la parte Supabase è di `database`, sezione 12) | ok |
| R-BACKEND-02 | pagina del gestore `fetch` dei Worker | `async fetch(request, env, ctx) {` | ok |
| R-BACKEND-02 | pagina dei binding dei Worker | «Bindings are located on the `env` object, which can be accessed in several ways:» | ok |
| R-BACKEND-02 | skill `workers-best-practices` (Apache-2.0) | «Prefer retrieval over pre-training» | ok |
| R-BACKEND-03 | agent-skills `api-and-interface-design`, «Validate at Boundaries» | «Trust internal code. Validate at system edges where external input enters:» (l'esempio risponde 422 all'input non valido) | ok |
| R-BACKEND-03 | everything-claude-code `security-reviewer` (MIT) | «Input Validation — Ensure all user inputs are properly sanitized» | ok |
| R-BACKEND-04 | agent-skills, «Consistent Error Semantics» | «Pick one error strategy and use it everywhere:» e «Every error response follows the same shape» | ok |
| R-BACKEND-05 | agent-skills, «Hyrum's Law» | «all observable behaviors of your system will be depended on by somebody» | ok |
| R-BACKEND-05 | agent-skills, «Prefer Addition Over Modification» | «Extend interfaces without breaking existing consumers:» (l'esempio da evitare toglie un campo e cambia un tipo) | ok |
| R-BACKEND-06 | everything-claude-code `security-reviewer`, «Code Pattern Review» | tabella dei modelli a rischio: SQL costruito per concatenazione, gravità CRITICAL, rimedio «Parameterized queries»; comando di sistema con input dell'utente, CRITICAL, rimedio «Use safe APIs or execFile» | ok |
| R-BACKEND-06 | everything-claude-code `code-reviewer`, «Security (CRITICAL)» | «SQL injection — String concatenation in queries instead of parameterized queries» (copre solo SQL, non i comandi di sistema) | ok |
| R-BACKEND-07 | pagina dei binding dei Worker | «Bindings are located on the `env` object» | ok |
| R-BACKEND-07 | pagina dei segreti dei Worker | «Do not use `vars` to store sensitive information in your Worker's Wrangler configuration file.» | ok |
| R-BACKEND-07 | skill `workers-best-practices` (Apache-2.0) | «Leaks credentials through version control; use Wrangler secrets.» | ok |
| R-BACKEND-07 | everything-claude-code `security-reviewer` | segreti scritti nel codice: gravità CRITICAL, rimedio «Use `process.env`» | ok |
| R-BACKEND-08 | agent-skills `observability-and-instrumentation`, «Structured logging» | «Never log secrets, tokens, passwords, or full PII.» | ok |
| R-BACKEND-08 | everything-claude-code `security-reviewer` | segreti, password nei log: gravità MEDIUM, rimedio «Sanitize log output» | ok |
| R-BACKEND-08 | everything-claude-code `security-reviewer`, «Fail Securely» | «Errors should not expose data» (regge la parte «corpo di una risposta d'errore», che prima la riga `Fonte:` non citava) | ok |
| R-BACKEND-09 | catalogo 2.3 (riga `backend` del `dod`) | la definizione di fatto del profilo ha «test delle API, typecheck» | ok |
| R-BACKEND-09 | agent-skills `api-and-interface-design`, «Verification» | la sezione non ha nessuna riga sui test di un endpoint (l'unico «test» del file sta in «Hyrum's Law»). Esce dalla `Fonte:` | no |
| R-BACKEND-10 | agent-skills, «Pagination» | «Paginate list endpoints:» | ok |
| R-BACKEND-11 | agent-skills, «Predictable Naming» | «Naming follows consistent conventions across all endpoints» (la sezione fissa convenzioni sue, la regola chiede quella del progetto: l'idea della coerenza c'è) | ok |
| R-BACKEND-12 | spec del nucleo, sezione 8.5 | tra gli effetti esterni predefiniti `wrangler deploy` e `npm publish`; tra i buchi, le scritture remote di `wrangler kv`, `d1` e `r2` (B5) | ok |
| R-BACKEND-12 | progetto di B, sezione 12 | per D1 il permesso solo con `--remote` o `--preview`, perché le prove locali di D1 sono le più frequenti | ok |
| R-BACKEND-12 | pagina dei comandi `kv` di Wrangler | `--local`: «Interact with local storage» (`kv key put` ha `--preview`, `--local`, `--remote`) | ok |
| R-BACKEND-12 | pagina dei comandi `d1` di Wrangler | `d1 execute`: «Execute a command or SQL file» (con `--local`, `--remote`, `--preview`) | ok |
| R-BACKEND-12 | pagina dei comandi `r2` di Wrangler | `r2 object put`: «Create an object in an R2 bucket» (con `--local`, `--remote`, `--persist-to`) | ok |
| R-BACKEND-12 | guida da Wrangler 3 a Wrangler 4 | «All commands now run in local mode by default.» | ok |

## Pattern dei percorsi

| Pattern | Fonte | Citazione | Esito |
|---|---|---|---|
| `api/**` | pagina delle funzioni di Vercel | «Vercel will deploy any file in the `/api` directory as a function.» | ok |
| `server/**` | catalogo 2, riga `backend` | l'elenco dei percorsi del profilo comincia con `api/**`, `server/**` | ok |
| `backend/**` | progetto di B, sezione 12 | il codice dei server resta coperto da `api/`, `server/`, `backend/` alla radice (il catalogo non la elenca: la aggiunge la sezione 12) | ok |
| `functions/**` | pagina delle Pages Functions di Cloudflare | «Make sure that the `/functions` directory is at the root of your Pages project» | ok |
| `**/routes/**` | catalogo 2, riga `backend`; progetto di B, sezione 12 | stessa riga del catalogo, confermata dalla sezione 12. Rilievo: la cartella `routes/` a qualunque profondità prende anche le rotte di un'interfaccia (da conoscenza generale, non dalle fonti): la pagina lo porta all'utente | ok |
| `**/handlers/**` | catalogo 2, riga `backend`; progetto di B, sezione 12 | stessa riga del catalogo, confermata dalla sezione 12. Rilievo: `handlers/` può contenere i gestori di eventi di un'interfaccia: la pagina lo porta all'utente | ok |

## Marcatori di contenuto

Per i marcatori con virgolette conta il nome del modulo: la riga con gli apici singoli vale anche per la forma con le doppie, che è lo stesso import scritto in un altro modo (decisione 3). I marcatori sono righe di import o di dichiarazione cercate come testo fisso.

| Marcatore | Fonte | Citazione | Esito |
|---|---|---|---|
| `cloudflare:workers` | pagina dei binding dei Worker | `import { env } from "cloudflare:workers";` | ok |
| `from workers import` | pagina dei Worker in Python | `from workers import WorkerEntrypoint, Response` | ok |
| `ExportedHandler<` | guide di avvio di KV e di D1 | `} satisfies ExportedHandler<Env>;` | ok |
| `require('express')` | guida di avvio di Express | `const express = require('express')` | ok |
| `from 'express'` | guida di avvio di Express | `import express from 'express';` | ok |
| `from 'fastify'` | guida di avvio di Fastify | `import Fastify from 'fastify'` | ok |
| `require('fastify')` | guida di avvio di Fastify | `const fastify = require('fastify')({` | ok |
| `from 'hono'` | pagina di Hono su Cloudflare Workers | `import { Hono } from 'hono'` | ok |
| `from 'node:http'` | pagina del modulo `http` di Node | `import http from 'node:http';` (il modulo ha anche il client: il costo è un falso positivo su chi lo importa per fare richieste) | ok |
| `require('node:http')` | pagina del modulo `http` di Node | «can be imported via `require('node:http')` (CommonJS)» | ok |
| `from fastapi import` | primi passi di FastAPI | `from fastapi import FastAPI` | ok |
| `from flask import` | guida rapida di Flask | `from flask import Flask` | ok |
| `Deno.serve(` | pagina del server HTTP di Deno | `Deno.serve((_req) => {` | ok |
| `export function GET(` | pagina delle funzioni di Vercel | `export function GET(request: Request) {` | ok |
| `export async function GET(` | riferimento dell'API delle funzioni di Vercel | `export async function GET(request: Request) {` | ok |
| `export function POST(` | nessuna | nessuna pagina mostra questa forma. Esce dal frammento | no |
| `export async function POST(` | pagina delle funzioni di Vercel | `export async function POST(request: Request) {` | ok |

## Esclusione

| Prefisso | Fonte | Citazione | Esito |
|---|---|---|---|
| `supabase/` | progetto di B, sezione 12; guida di avvio delle funzioni di Supabase | `backend` non accende le edge function: il suo frammento esclude la cartella `supabase/`; la guida mostra il percorso `supabase/functions/hello-world/index.ts` | ok |

## Correzioni fatte dopo la verifica

- **R-BACKEND-01.** La sezione «Contract First» esce dalla riga `Fonte:`: resta il progetto di B, sezione 3.4, che dice proprio di leggere i contratti già presenti.
- **R-BACKEND-09.** La sezione «Verification» esce dalla riga `Fonte:`: resta il catalogo 2.3. Il caso d'errore per ogni input validato e per ogni risorsa che può mancare resta dichiarato «scelta nostra».
- **R-BACKEND-12.** L'obbligo di riportare la prova locale non è in nessuna fonte: la riga `Fonte:` lo dichiara «scelta nostra». Il resto regge sulla spec, sul progetto di B e sulle pagine di Wrangler.
- **R-BACKEND-07.** La regola è riscritta sui fatti della pagina dei segreti: nessun segreto nel codice né nei `vars` della configurazione; nel codice di un Worker segreti e binding si leggono da `env`. Prima diceva «non dai `vars`», ma anche i `vars` arrivano da `env`: la pagina dice solo di non metterci i segreti.
- **R-BACKEND-08.** La riga `Fonte:` cita anche «Fail Securely» di `security-reviewer`, che regge la parte sul corpo di una risposta d'errore.
- **`export function POST(`.** Esce dal frammento, perché nessuna pagina ufficiale mostra la forma senza `async`. I marcatori restano 23. Il costo è piccolo: la forma `export async function POST(` e le due di `GET` coprono i gestori di Next.js e di Vercel più comuni.

## Parti dichiarate «scelta nostra»

Stanno nella pagina per l'utente, nella sezione «Cosa hai deciso»:

- R-BACKEND-02: l'estensione alla libreria standard e ai framework. La fonte parla dei Worker.
- R-BACKEND-05: «e che il task lo chiede».
- R-BACKEND-09: il caso d'errore per ogni input validato e per ogni risorsa che può mancare.
- R-BACKEND-12: riportare nel report la prova locale.
- I pattern `**/routes/**` e `**/handlers/**`, troppo larghi per le rotte di un'interfaccia.
- Il Worker senza import da `cloudflare:workers` e senza il tipo `ExportedHandler`, che non si trova da solo.
- Le cartelle `api/`, `server/`, `backend/`, `functions/` valgono solo alla radice.
- Il `dod` vuoto, contro la proposta «test delle API, typecheck» del catalogo 2.3.
- `supabase/` dentro un pacchetto di monorepo, dove l'esclusione non arriva.

Imprecisioni minori, non `no`: R-BACKEND-06 trova la base per i comandi di sistema in una sola fonte (la tabella di `security-reviewer`); R-BACKEND-11 chiede la convenzione del progetto, mentre la sezione citata ne fissa una sua.

## Regole tolte

Nessuna regola esce: ciascuna ha almeno una fonte `ok`. Nessun pattern e nessuna voce di esclusione escono. Esce un marcatore, `export function POST(`, con la riga `no` sopra.
