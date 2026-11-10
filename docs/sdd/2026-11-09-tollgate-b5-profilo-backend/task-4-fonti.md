# Verifica delle fonti di `rules-backend` (Task 4, Step 1)

Uscita del verificatore `Explore` (sonnet, sola lettura), sulla bozza del commit 8e5574c, salvata dal controller (arrivata in due messaggi).

**Metodo.** Ho letto `skills/rules-backend/SKILL.md`, `templates/profiles/backend.toml`, `task-3-report.md`, tutte le copie in `fonti/backend/` con `FONTI.md`, e le sezioni citate del progetto di B (3.4, 12), del catalogo (2, 2.3, 4) e della spec del nucleo (8.5). `sha256sum -c SHA256SUMS` dentro `fonti/backend/` dà OK su tutti i 36 file. Le pagine ufficiali e `cloudflare-skills-workers-best-practices.md` sono estratti letterali parziali, non pagine intere. Ho confrontato solo con quegli estratti.

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-BACKEND-01 | progetto di B, 3.4 (riga `backend`) | «Leggi i contratti esistenti (tipi, schemi, rotte) prima di aggiungerne.» | ok |
| R-BACKEND-01 | agent-skills `api-and-interface-design`, «Contract First» | «Define the interface before implementing it. The contract is the spec — implementation follows.» | no: la sezione dice di definire il contratto prima di implementare, non di leggere quelli già presenti. È un'idea vicina, ma diversa |
| R-BACKEND-02 | progetto di B, 3.4 (riga `backend`) | «Per Supabase edge function e Cloudflare Worker, la documentazione del runtime.» | ok (vale per i Worker; la parte Supabase è di `database`, B 12) |
| R-BACKEND-02 | `workers-fetch-handler.md` | `async fetch(request, env, ctx) {`; env: «The bindings available to the Worker.» | ok |
| R-BACKEND-02 | `workers-bindings.md` | «Bindings are located on the `env` object, which can be accessed in several ways:» | ok |
| R-BACKEND-02 | `cloudflare-skills-workers-best-practices.md` (Apache-2.0) | «Prefer retrieval over pre-training» | ok |
| R-BACKEND-03 | agent-skills `api-and-interface-design`, «Validate at Boundaries» | «Trust internal code. Validate at system edges where external input enters:» (l'esempio risponde 422 all'input non valido) | ok |
| R-BACKEND-03 | `ecc-security-reviewer.md` | «Input Validation — Ensure all user inputs are properly sanitized» | ok |
| R-BACKEND-04 | agent-skills, «Consistent Error Semantics» | «Pick one error strategy and use it everywhere:»; «Every error response follows the same shape» | ok |
| R-BACKEND-05 | agent-skills, «Hyrum's Law» | «all observable behaviors of your system will be depended on by somebody» | ok |
| R-BACKEND-05 | agent-skills, «Prefer Addition Over Modification» | «Extend interfaces without breaking existing consumers:» (il «Bad» toglie un campo e cambia il tipo di `priority`) | ok |
| R-BACKEND-06 | `ecc-security-reviewer.md`, «Code Pattern Review» | «String-concatenated SQL \| CRITICAL \| Parameterized queries»; «Shell command with user input \| CRITICAL \| Use safe APIs or execFile» | ok |
| R-BACKEND-06 | `ecc-code-reviewer.md`, «Security (CRITICAL)» | «SQL injection — String concatenation in queries instead of parameterized queries» | ok (copre solo SQL, non i comandi di sistema) |
| R-BACKEND-07 | `workers-bindings.md` | «Bindings are located on the `env` object» | ok |
| R-BACKEND-07 | `workers-secrets.md` | «Do not use `vars` to store sensitive information in your Worker's Wrangler configuration file.» | ok |
| R-BACKEND-07 | `cloudflare-skills-workers-best-practices.md` | «Leaks credentials through version control; use Wrangler secrets.» | ok |
| R-BACKEND-07 | `ecc-security-reviewer.md` | «Hardcoded secrets \| CRITICAL \| Use `process.env`» | ok |
| R-BACKEND-08 | agent-skills `observability-and-instrumentation`, «Structured logging» | «Never log secrets, tokens, passwords, or full PII.» | ok |
| R-BACKEND-08 | `ecc-security-reviewer.md` | «Logging passwords/secrets \| MEDIUM \| Sanitize log output» | ok (la parte «corpo di una risposta d'errore» ha base in «Fail Securely — Errors should not expose data» dello stesso file, che la riga `Fonte:` non cita) |
| R-BACKEND-09 | catalogo 2.3 (riga `backend` del `dod`) | «\| `backend` \| test delle API, typecheck \|» | ok (regge i test delle API; il caso riuscito e quello d'errore per input e risorsa sono formulazione nostra) |
| R-BACKEND-09 | agent-skills `api-and-interface-design`, «Verification» | nessuna riga sui test nell'elenco; l'unico «test» del file è «Tests are not enough» in «Hyrum's Law» | no: la sezione non parla di test di endpoint. Correzione minima: togliere la sezione dalla `Fonte:` |
| R-BACKEND-10 | agent-skills, «Pagination» | «Paginate list endpoints:» | ok |
| R-BACKEND-11 | agent-skills, «Predictable Naming» | tabella delle convenzioni; la riga di «Verification» dice «Naming follows consistent conventions across all endpoints» | ok (la sezione fissa convenzioni sue, la regola chiede quella del progetto: l'idea della coerenza c'è) |
| R-BACKEND-12 | spec del nucleo 8.5 | «un elenco predefinito: … `wrangler deploy`, `npm publish`»; tra i buchi: «le scritture remote di `wrangler kv`, `d1` e `r2` (B5)» | ok |
| R-BACKEND-12 | progetto di B, 12 | «per D1 il permesso solo con `--remote` o `--preview`… perché le prove locali di D1 sono le più frequenti» | ok (l'obbligo di riportare la prova locale è nostro) |
| R-BACKEND-12 | `wrangler-kv.md` | «--local: "Interact with local storage"» (`kv key put`: --preview, --local, --remote) | ok |
| R-BACKEND-12 | `wrangler-d1.md` | «d1 execute: "Execute a command or SQL file" (--local, --remote, --preview)» | ok |
| R-BACKEND-12 | `wrangler-r2.md` | «r2 object put: "Create an object in an R2 bucket" (--local, --remote, --persist-to)» | ok |
| R-BACKEND-12 | `wrangler-v3-to-v4.md` | «All commands now run in local mode by default.» | ok |

## Pattern dei percorsi

| Pattern | Fonte | Citazione | Esito |
|---|---|---|---|
| `api/**` | `vercel-functions-api-reference.md` | «defining your function in a file under `/api` in your project. Vercel will deploy any file in the `/api` directory as a function.» | ok |
| `server/**` | catalogo 2, riga `backend` | «`api/**`, `server/**`, `**/routes/**`, `**/handlers/**`, `**/services/**`» | ok |
| `backend/**` | progetto di B, 12 | «Il codice dei server resta coperto da `api/`, `server/`, `backend/` alla radice» | ok (il catalogo non lo elenca: lo aggiunge B 12) |
| `functions/**` | `pages-functions-get-started.md` | «Make sure that the `/functions` directory is at the root of your Pages project» | ok |
| `**/routes/**` | catalogo 2, riga `backend`; progetto di B, 12 («da `routes/` e `handlers/`») | stessa riga del catalogo | no: il punto 1 regge, il punto 2 no. `routes/` a qualunque profondità prende anche le rotte di interfaccia (da conoscenza generale, non dalle fonti). La scelta è però del catalogo e confermata in B 12: da portare all'utente |
| `**/handlers/**` | catalogo 2, riga `backend`; progetto di B, 12 | idem | no: stesso rischio. `handlers/` può contenere gestori di eventi dell'interfaccia. Da portare all'utente |

## Marcatori di contenuto

Per i marcatori con virgolette conta il nome del modulo: la riga con apici singoli vale anche per la forma con le doppie.

| Marcatore | Fonte | Citazione | Esito |
|---|---|---|---|
| `cloudflare:workers` | `workers-bindings.md` | `import { env } from "cloudflare:workers";` | ok |
| `from workers import` | `workers-python.md` | `from workers import WorkerEntrypoint, Response` | ok |
| `ExportedHandler<` | `kv-get-started.md`, `d1-get-started.md` | `} satisfies ExportedHandler<Env>;` | ok |
| `require('express')` | `express-hello-world.md` | `const express = require('express')` | ok |
| `from 'express'` | `express-hello-world.md` | `import express from 'express';` | ok |
| `from 'fastify'` | `fastify-getting-started.md` | `import Fastify from 'fastify'` | ok |
| `require('fastify')` | `fastify-getting-started.md` | `const fastify = require('fastify')({` | ok |
| `from 'hono'` | `hono-cloudflare-workers.md` | `import { Hono } from 'hono'` | ok |
| `from 'node:http'` | `node-http.md` | `import http from 'node:http';` | ok (il modulo ha anche il client: costo piccolo) |
| `require('node:http')` | `node-http.md` | «can be imported via `require('node:http')` (CommonJS)» | ok |
| `from fastapi import` | `fastapi-first-steps.md` | `from fastapi import FastAPI` | ok |
| `from flask import` | `flask-quickstart.md` | `from flask import Flask` | ok |
| `Deno.serve(` | `deno-http-server.md` | `Deno.serve((_req) => {` | ok |
| `export function GET(` | `vercel-functions.md` | `export function GET(request: Request) {` | ok |
| `export async function GET(` | `vercel-functions-api-reference.md` | `export async function GET(request: Request) {` | ok |
| `export function POST(` | nessuna | | no: nessuna pagina la mostra |
| `export async function POST(` | `vercel-functions.md` | `export async function POST(request: Request) {` | ok |

## Esclusione

| Prefisso | Fonte | Citazione | Esito |
|---|---|---|---|
| `supabase/` | progetto di B, 12; `supabase-functions-quickstart.md` | «`backend` non le accende: il suo frammento esclude la cartella `supabase/`»; percorso «supabase/functions/hello-world/index.ts» | ok |

## Riepilogo

- Regole e fonti: 29 righe, 27 `ok` e 2 `no`. Nessuna regola resta senza una fonte `ok`.
- Regole con almeno una fonte `no`: R-BACKEND-01 («Contract First»: togliere dalla `Fonte:` o scrivere che ne viene solo il tema); R-BACKEND-09 («Verification»: togliere dalla `Fonte:`).
- Scelta nostra dichiarata: R-BACKEND-02 (libreria standard e framework).
- Obblighi non dichiarati scelta nostra: R-BACKEND-05 («chi li usa» e «che il task lo chiede»); R-BACKEND-09 (caso riuscito più un caso d'errore per ogni input e risorsa); R-BACKEND-12 (riportare la prova locale); R-BACKEND-07 ambigua («da `env`, non dai `vars`»: anche i `vars` stanno su `env`; la fonte dice solo di non metterci i segreti).
- Pattern `no`: `**/routes/**` e `**/handlers/**` per il punto 2 (troppo larghi); la scelta è del catalogo e di B 12, decide l'utente.
- Marcatori `no`: `export function POST(`. Gli altri 23 `ok`.
- Prefissi `no`: nessuno. Frasi copiate: nessuna.
- Licenze: per `cloudflare/skills` la copia non aveva un file `LICENSE` (nota di forma; il controller ha poi aggiunto `cloudflare-skills-LICENSE.md`).
