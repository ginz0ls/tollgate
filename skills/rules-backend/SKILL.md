---
name: rules-backend
description: Regole di tollgate per il codice dei server e delle API (anche i Worker di Cloudflare): le caricano in automatico gli agenti dell'area backend, non serve invocarla.
version: 1
approved: 2026-11-10
---
# Regole backend (versione 1)

Sono le regole per il codice che risponde alle richieste: server HTTP, API, funzioni di Vercel e di Cloudflare Pages, rotte di Next.js, Worker di Cloudflare. Valgono in aggiunta a quelle di base. Chi scrive le segue prima di toccare un file. Chi rivede le applica guardando ciò che ha davanti, e per ognuna risponde sì o no: sotto ogni regola la riga «Si giudica su» dice se la risposta sta nel diff o nel report. Le regole segnate `[blocca]` si giudicano sul diff o sul report, perché nei lavori senza il passo «informati prima» la nota non c'è. Un difetto si segnala una volta sola, con la regola che viola.

Un endpoint è una funzione registrata come rotta di un server, un gestore esportato da un file di rotte (come `GET` o `POST` in un `route.ts`, o `onRequest` in `functions/`) o il gestore `fetch` di un Worker: nel diff si riconosce da una di queste tre forme, nuova o cambiata.

## Prima di scrivere

R-BACKEND-01 [blocca] Se il diff aggiunge o cambia un endpoint, il report nomina i contratti già presenti che ha letto (tipi o schemi delle richieste e delle risposte, il file dove sono registrate le rotte), o dice che il progetto non ne ha.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `backend`: prima di scrivere un endpoint si leggono i contratti già presenti)

R-BACKEND-02 [blocca] Se il diff usa per la prima volta nel file un'API del runtime o della libreria standard per servire richieste (il gestore e i binding di un Worker, `Deno.serve`, il modulo `http` di Node, `http.server` di Python) o di un framework di server, il report ha l'indirizzo della pagina ufficiale della versione in uso.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `backend`: per i Worker vale la documentazione del runtime); la pagina del gestore `fetch` https://developers.cloudflare.com/workers/runtime-apis/handlers/fetch/ e quella dei binding https://developers.cloudflare.com/workers/runtime-apis/bindings/; la skill `workers-best-practices` (Apache-2.0) https://github.com/cloudflare/skills/blob/main/skills/workers-best-practices/SKILL.md (meglio la documentazione ufficiale della memoria); l'estensione alla libreria standard e ai framework è una scelta nostra

## Mentre lavori

R-BACKEND-03 [blocca] Un endpoint nuovo o cambiato valida corpo, parametri e query prima di usarli, e risponde con un errore del client a un input non valido.
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/api-and-interface-design/SKILL.md, «Validate at Boundaries»; everything-claude-code 1.4.1 (Affaan Mustafa, MIT), agents/security-reviewer.md (input dell'utente tra i punti da controllare)

R-BACKEND-04 [blocca] Gli errori di un endpoint nuovo hanno la stessa forma e gli stessi codici di stato già usati nel progetto o, se il progetto non ne ha ancora, una forma sola per tutti gli errori dell'endpoint.
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/api-and-interface-design/SKILL.md, «Consistent Error Semantics»

R-BACKEND-05 [blocca] Se il diff toglie o rinomina un campo di una risposta, una rotta o un parametro già pubblici, o ne cambia il tipo, il report dice chi li usa (le chiamate trovate nel repo) e che il task lo chiede.
Si giudica su: report
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/api-and-interface-design/SKILL.md, «Hyrum's Law» e «Prefer Addition Over Modification» (cambiare ciò che è pubblico rompe chi lo usa); che il task chieda il cambiamento è una scelta nostra

R-BACKEND-06 [blocca] Le query al database e i comandi del sistema si costruiscono con parametri, mai concatenando l'input della richiesta.
Si giudica su: diff
Fonte: everything-claude-code 1.4.1 (Affaan Mustafa, MIT), agents/security-reviewer.md (tabella dei modelli di codice a rischio) e agents/code-reviewer.md (elenco della sicurezza)

R-BACKEND-07 [blocca] Nessun segreto scritto nel codice né nei `vars` della configurazione di Wrangler. Nel codice di un Worker i segreti e i binding si leggono da `env`.
Si giudica su: diff
Fonte: le pagine dei Worker sui binding https://developers.cloudflare.com/workers/runtime-apis/bindings/ e sui segreti https://developers.cloudflare.com/workers/configuration/secrets/; la skill `workers-best-practices` (Apache-2.0) https://github.com/cloudflare/skills/blob/main/skills/workers-best-practices/SKILL.md (i segreti nel codice passano dal controllo di versione; `vars` non è il posto dei dati sensibili); everything-claude-code 1.4.1 (Affaan Mustafa, MIT), agents/security-reviewer.md (segreti scritti nel codice)

R-BACKEND-08 [blocca] Un segreto, un token o una password non finisce in una riga di log né nel corpo di una risposta d'errore.
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/observability-and-instrumentation/SKILL.md, «Structured logging»; everything-claude-code 1.4.1 (Affaan Mustafa, MIT), agents/security-reviewer.md (segreti nei log e «Fail Securely» per le risposte d'errore)

R-BACKEND-09 [blocca] Un endpoint nuovo o cambiato ha un test che lo chiama con un caso riuscito, e un caso d'errore per ogni input che l'endpoint valida e per ogni risorsa che può mancare (un endpoint senza input e senza risorse ha solo il caso riuscito).
Si giudica su: diff
Fonte: catalogo 2.3 (riga `backend`: nella definizione di fatto, i test delle API); il caso d'errore per ogni input validato e per ogni risorsa che può mancare è una scelta nostra

R-BACKEND-10 Un endpoint nuovo che restituisce una lista la pagina.
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/api-and-interface-design/SKILL.md, «Pagination»

R-BACKEND-11 Nomi di rotte, campi e parametri seguono la convenzione già usata nel progetto.
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/api-and-interface-design/SKILL.md, «Predictable Naming»

R-BACKEND-12 [blocca] Se il diff tocca codice che legge o scrive KV, D1, R2 o un database, il report dice quale prova locale ha eseguito (per esempio una scrittura di Wrangler con l'opzione della modalità locale) oppure perché non l'ha fatta; in ogni task il report non riporta comandi lanciati dall'implementatore che scrivono sui dati di un servizio in linea o pubblicano.
Si giudica su: report
Fonte: spec del nucleo 8.5 (gli effetti esterni); progetto di B, sezione 12 (le prove sono locali); le pagine dei comandi di Wrangler https://developers.cloudflare.com/workers/wrangler/commands/kv/, https://developers.cloudflare.com/workers/wrangler/commands/d1/ e https://developers.cloudflare.com/workers/wrangler/commands/r2/, e la guida a Wrangler 4 https://developers.cloudflare.com/workers/wrangler/migration/update-v3-to-v4/ (i comandi che possono girare in locale o in remoto girano in locale per impostazione predefinita); riportare nel report la prova locale è una scelta nostra

## Dove informarsi

Prima di scrivere un endpoint si aprono i contratti già presenti (R-BACKEND-01). Per il runtime o il framework si legge la versione installata nel file delle dipendenze del progetto e si cerca la pagina ufficiale di quella versione; se la versione non si trova o la pagina non c'è, il report lo dice e non si inventa la sintassi.

- Le skill `api-and-interface-design` (contratti, errori, validazione, compatibilità) e `observability-and-instrumentation` (log, metriche, tracce), se i plugin sono installati.
- Per i Worker: le skill `workers-best-practices` e `cloudflare`; il runtime https://developers.cloudflare.com/workers/runtime-apis/, la configurazione https://developers.cloudflare.com/workers/wrangler/configuration/, i tipi https://developers.cloudflare.com/workers/languages/typescript/. Le versioni di `wrangler` e di `@cloudflare/workers-types` stanno nel file delle dipendenze del progetto.
- Per un framework: la pagina ufficiale della versione in uso, per esempio https://expressjs.com/, https://fastify.dev/, https://hono.dev/, https://fastapi.tiangolo.com/, https://flask.palletsprojects.com/, https://docs.deno.com/runtime/fundamentals/http_server/, https://nodejs.org/api/http.html.
- Per Vercel https://vercel.com/docs/functions e per Cloudflare Pages https://developers.cloudflare.com/pages/functions/.

## Fonti

Le regole sono scritte con parole nostre. Dalle skill `api-and-interface-design` e `observability-and-instrumentation` di agent-skills 0.6.9 (Addy Osmani, licenza MIT) e dal repository https://github.com/cloudflare/skills (`workers-best-practices`, licenza Apache-2.0) vengono i temi e i nomi delle sezioni; da everything-claude-code 1.4.1 (Affaan Mustafa, licenza MIT) si prendono solo i temi di revisione (input, query, segreti, log), senza testo copiato. Delle pagine ufficiali di Cloudflare (https://developers.cloudflare.com/workers/, che non dichiara una licenza), di Vercel, di Deno, di Node e dei framework riportano i fatti, non il testo. Le scelte dell'utente stanno nel progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md, sezioni 3.4 e 12) e nella spec del nucleo (sezione 8.5). I nomi dei file e i marcatori con cui `init` riconosce il profilo (`templates/profiles/backend.toml`) vengono dalle stesse pagine: un commento del frammento dice quale per ogni gruppo.
