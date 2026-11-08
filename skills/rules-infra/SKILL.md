---
name: rules-infra
description: Regole di tollgate per la configurazione e il deploy (Vercel, Cloudflare, Docker): le caricano in automatico gli agenti dell'area infra, non serve invocarla.
version: 1
approved: 2026-11-07
---
# Regole infra (versione 1)

Sono le regole per la configurazione e il deploy su Vercel, su Cloudflare (Wrangler) e con Docker, in aggiunta a quelle di base. Chi scrive la configurazione le segue prima di toccare un file. Chi rivede le applica guardando ciò che ha davanti, e per ognuna risponde sì o no: sotto ogni regola la riga «Si giudica su» dice se la risposta sta nel diff, nel report o nella nota di ricerca. Le regole segnate `[blocca]` si giudicano sul diff o sul report, perché nei lavori senza il passo «informati prima» la nota non c'è. Un difetto si segnala una volta sola, con la regola che viola.

## Prima di scrivere

R-INFRA-01 [blocca] Se il diff tocca la configurazione o i comandi di deploy, il report nomina i file di deploy versionati che ha letto prima di scrivere (la configurazione di Vercel e quella di Wrangler, i Dockerfile e i file compose, i workflow di deploy in `.github/workflows/`) e dice dove gira oggi il progetto.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `infra`: prima di parlare di deploy si apre la configurazione già presente) e sezione 11 (i workflow di GitHub non accendono `infra`, ma le regole chiedono di leggerli prima di parlare di deploy); dire dove gira oggi il progetto è una scelta nostra, che nessuna delle due sezioni contiene

R-INFRA-02 [blocca] Un comando o un'opzione di `vercel`, `wrangler`, `docker` o `docker compose` che il diff scrive (in uno script, in `package.json`, nella documentazione) o che il report dà per un fatto ha nel report l'indirizzo della pagina ufficiale che lo descrive.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `infra`: per `wrangler` e `vercel` vale la documentazione ufficiale, non la memoria); l'estensione a `docker` e `docker compose` è una scelta nostra, perché Docker è in `infra` (progetto di B, sezione 11); la skill `wrangler` (Apache-2.0) https://github.com/cloudflare/skills/blob/main/skills/wrangler/SKILL.md (opzioni e campi cambiano, quindi non ci si fida di esempi ricordati; se la documentazione non si raggiunge si dice, senza inventare la sintassi); le pagine dei comandi https://developers.cloudflare.com/workers/wrangler/commands/ e https://vercel.com/docs/cli/build

R-INFRA-03 [blocca] Una proprietà che il diff scrive in un file di configurazione di Vercel (`vercel.json`, `vercel.toml`, `vercel.ts`) o di Wrangler (`wrangler.toml`, `wrangler.json`, `wrangler.jsonc`) ha nel report l'indirizzo della pagina ufficiale che la descrive.
Si giudica su: report
Fonte: le pagine della configurazione https://vercel.com/docs/project-configuration (con le pagine di `vercel.json` e `vercel.ts` che da lì partono) e https://developers.cloudflare.com/workers/wrangler/configuration/; la skill `wrangler` https://github.com/cloudflare/skills/blob/main/skills/wrangler/SKILL.md (i campi di configurazione cambiano da una versione all'altra)

## Mentre lavori

R-INFRA-04 [blocca] Un progetto Vercel ha un solo file di configurazione: il diff non aggiunge `vercel.json`, `vercel.toml` o `vercel.ts` in una cartella che ne ha già uno degli altri due (chi rivede guarda la cartella nel repo).
Si giudica su: diff
Fonte: https://vercel.com/docs/project-configuration (sezione «File-based configuration»: un solo file per progetto) e https://vercel.com/docs/project-configuration/vercel-ts (sezione «Requirements»: si usa `vercel.ts` oppure `vercel.json`, non entrambi)

R-INFRA-05 [blocca] Nessun segreto (chiave, token, password) nei file versionati: non in `vars` di Wrangler, non nella configurazione di Vercel (nemmeno in `env` o `build.env`), non in `ENV` o `ARG` di un Dockerfile. I segreti passano dalle impostazioni dei servizi (i segreti dei Worker, le variabili `Secret` di Vercel) o, nella build di Docker, dall'opzione `secret` di `docker build` letta da un `RUN` con montaggio di tipo `secret`, e li imposta l'utente. Un valore `"@nome"` in `env` o `build.env` di Vercel è il riferimento a un segreto già salvato su Vercel, non un segreto.
Si giudica su: diff
Fonte: https://developers.cloudflare.com/workers/configuration/secrets/ (sezione «Local Development with Secrets»: `vars` non è per le informazioni riservate); https://vercel.com/docs/project-configuration/vercel-json (sezioni `env` e `build.env`: la pagina li sconsiglia e manda alle impostazioni del progetto; un valore `@<nome>` è risolto da un segreto salvato su Vercel, come mostra il suo esempio) e https://vercel.com/docs/environment-variables (le variabili stanno fuori dal codice; un valore `Secret` si può solo scrivere); https://docs.docker.com/build/building/secrets/ (argomenti di build e variabili d'ambiente restano nell'immagine, i segreti passano con l'opzione `secret` di `docker build` e con il montaggio di tipo `secret`) e https://docs.docker.com/build/building/best-practices/ (sezione `ENV`: un valore messo con `ENV` resta nello strato anche se poi lo si toglie)

R-INFRA-06 [blocca] I file dei segreti locali (`.dev.vars*`, `.env`, `.env.*`) non entrano nel diff, salvo quelli che finiscono in `.example`, `.sample` o `.template`, che sono modelli senza valori veri. Se il diff aggiunge codice, uno script o documentazione che li usa, `.gitignore` li esclude (nel diff o già nel repo).
Si giudica su: diff
Fonte: https://developers.cloudflare.com/workers/configuration/secrets/ (sezione «Local Development with Secrets»: `.dev.vars` e `.env` non si versionano e `.dev.vars*` e `.env*` vanno nel `.gitignore`); https://vercel.com/docs/environment-variables (sezione sulle variabili di sviluppo: `.env.local` e il `.env` creato da `vercel env pull` contengono le variabili del progetto; la pagina non dice di non versionarli, la regola poggia sulla pagina di Cloudflare); l'eccezione dei file modello è una nostra scelta, perché un modello non porta valori da proteggere

R-INFRA-07 Una configurazione di Wrangler nuova usa `wrangler.jsonc` e, in `compatibility_date`, la data del giorno in cui nasce.
Si giudica su: diff
Fonte: https://developers.cloudflare.com/workers/wrangler/configuration/ (nota iniziale: per i progetti nuovi si consiglia `wrangler.jsonc`, e alcune funzioni nuove ci sono solo con il formato JSON; la tabella delle chiavi segna `compatibility_date` come richiesta); https://developers.cloudflare.com/workers/configuration/compatibility-dates/ (sezione «Setting compatibility date»: a inizio progetto si mette la data del giorno; le date vecchie restano valide per sempre, perciò la regola non blocca)

R-INFRA-08 Se il diff cambia una `compatibility_date` già presente, il report dice di aver letto la pagina dei flag di compatibilità per vedere che cosa cambia con la data nuova.
Si giudica su: report
Fonte: https://developers.cloudflare.com/workers/configuration/compatibility-dates/ (sezione «Setting compatibility date»: la data si aggiorna ogni tanto, dopo aver letto i flag e provato il Worker)

R-INFRA-09 L'immagine di base di un Dockerfile ha una versione fissata (un tag preciso o un digest), non `latest` né il solo nome.
Si giudica su: diff
Fonte: https://docs.docker.com/build/building/best-practices/ (sezione «Pin base image versions»: un tag può essere spostato dal suo autore, il digest fissa l'immagine)

R-INFRA-10 Un Dockerfile nuovo per un servizio che non ha bisogno di privilegi passa a un utente non root con `USER`, e ha un `.dockerignore` nella radice del context di build, oppure un file `<nome del Dockerfile>.dockerignore` accanto al Dockerfile.
Si giudica su: diff
Fonte: https://docs.docker.com/build/building/best-practices/ (sezioni `USER` e «Exclude with .dockerignore»); https://docs.docker.com/build/concepts/context/ (sezione sui file `.dockerignore`: nome e posizione, compresa la forma con il nome del Dockerfile)

R-INFRA-11 Un Dockerfile che compila separa la build dall'immagine finale con una build a stadi.
Si giudica su: diff
Fonte: https://docs.docker.com/build/building/best-practices/ (sezione «Use multi-stage builds»: gli stadi distinti riducono l'immagine finale)

R-INFRA-12 [blocca] Il task non pubblica e non cambia un servizio. Il report dice quale prova senza pubblicazione ha eseguito (per esempio `npx wrangler deploy` in modalità di prova, cioè con l'opzione dry-run, oppure `vercel build` in un progetto collegato), dopo l'approvazione dell'utente che tollgate chiede per quei comandi, oppure perché non l'ha fatta. Non riporta comandi che pubblicano o cambiano un servizio (deploy, pubblicazione in produzione, `secret`, `env add`) lanciati da lui.
Si giudica su: report
Fonte: spec del nucleo, sezione 8.5 (gli effetti esterni sono negati finché l'utente non li approva); https://developers.cloudflare.com/workers/wrangler/commands/workers/ (il deploy in modalità dry-run compila senza pubblicare; `rollback`, `delete`, `triggers deploy` e `versions deploy` cambiano ciò che è in linea), https://developers.cloudflare.com/workers/configuration/secrets/ (sezione «Adding secrets to your project»: `secret put` pubblica subito una nuova versione) e https://developers.cloudflare.com/workers/wrangler/commands/pages/ (lo stesso per `pages deploy` e per i comandi `pages` che creano, cancellano o impostano segreti); https://vercel.com/docs/cli/build (la build locale scrive in `.vercel/output`, e conviene un `vercel pull` prima); https://vercel.com/docs/environment-variables (`env add` imposta le variabili del progetto sul servizio)

## Dove informarsi

Prima di parlare di deploy si aprono i file di deploy già presenti nel repo (R-INFRA-01). Per `wrangler` e `vercel` si legge la versione installata nel file delle dipendenze del progetto e si cerca la documentazione di quella versione; se la versione non si trova o la pagina non c'è, il report lo dice e non si inventa la sintassi.

- La skill `wrangler`: comandi e configurazione di Wrangler, con la regola di non fidarsi di esempi ricordati. La skill `cloudflare`: la piattaforma Cloudflare in generale.
- Cloudflare: configurazione https://developers.cloudflare.com/workers/wrangler/configuration/, comandi https://developers.cloudflare.com/workers/wrangler/commands/, segreti https://developers.cloudflare.com/workers/configuration/secrets/, date di compatibilità https://developers.cloudflare.com/workers/configuration/compatibility-dates/
- Vercel: configurazione https://vercel.com/docs/project-configuration, collegamento del progetto https://vercel.com/docs/cli/project-linking, build in locale https://vercel.com/docs/cli/build, variabili https://vercel.com/docs/environment-variables
- Docker: documentazione ufficiale https://docs.docker.com/, buone pratiche dei Dockerfile https://docs.docker.com/build/building/best-practices/, segreti di build https://docs.docker.com/build/building/secrets/, file compose https://docs.docker.com/compose/intro/compose-application-model/

## Fonti

Le regole sono scritte con parole nostre a partire dalle pagine ufficiali di Vercel, Cloudflare e Docker consultate il 2026-11-06, dalla skill `wrangler` e dalle scelte dell'utente raccolte nel progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md, sezioni 3.4 e 11) e nella spec del nucleo (sezione 8.5). Delle pagine riportano i fatti, senza testo copiato: ogni regola dice da quale pagina e da quale sezione viene.

- Vercel: https://vercel.com/docs/ (configurazione, `vercel.json` e `vercel.ts`, collegamento, build in locale, variabili). Le pagine non dichiarano una licenza.
- Cloudflare: https://developers.cloudflare.com/workers/ (Wrangler: configurazione, comandi, segreti, date di compatibilità). Le pagine non dichiarano una licenza. La skill `wrangler` è nel repository https://github.com/cloudflare/skills, con licenza Apache-2.0.
- Docker: https://docs.docker.com/ (Dockerfile, contesto di build, segreti, buone pratiche, file compose). La documentazione è nel repository https://github.com/docker/docs, con licenza Apache-2.0.

I nomi dei file con cui `init` riconosce il profilo (`templates/profiles/infra.toml`) vengono dalle stesse pagine: un commento del frammento dice quale per ogni gruppo.
