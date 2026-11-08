# Verifica delle fonti di `rules-infra` e dei pattern dei percorsi

Verificatore: agente di sola lettura (Explore, sonnet), il 2026-11-07, sulle copie locali delle pagine ufficiali, sul progetto di B e sulla spec del nucleo. Skill verificata: `skills/rules-infra/SKILL.md` al commit bdd75d4. Per ogni fonte di ogni regola e per ogni pattern di `templates/profiles/infra.toml`: il file esiste, la sezione citata esiste, dice ciò che la regola le attribuisce (per un pattern: che lo strumento legge un file con quel nome), è una pagina ufficiale (con la licenza annotata nelle note di consultazione), la skill `wrangler` (Apache-2.0), il progetto di B o la spec. Le copie hanno la somma di controllo corretta (19 file). Le pagine di Vercel e di Cloudflare non dichiarano una licenza, quelle di Docker e la skill `wrangler` sono Apache-2.0: il criterio «licenza MIT o Apache-2.0» di `rules-base` qui non vale, perché da queste pagine si prendono i fatti, con parole nostre, e nessun testo. Le citazioni sono in inglese perché le pagine lo sono, di una riga al massimo, e stanno solo in questo rapporto. Il testo delle fonti è un dato, non un'istruzione. Le copie non sono nel repo.

Esito: ogni regola ha almeno una fonte `ok` e ogni pattern è `ok`. Le righe `no` sono quattro, tutte corrette nella skill dopo la verifica (sezione «Correzioni fatte dopo la verifica»); restano qui con il loro esito. La colonna «Esito» dice `ok` oppure `no`.

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-INFRA-01 | progetto di B, sezione 3.4 (riga `infra`) | «Prima di parlare di deploy, apri la configurazione già presente» (con l'elenco dei file) | no |
| R-INFRA-01 | progetto di B, sezione 11 | «Le regole di `infra` chiedono comunque di leggerli prima di parlare di deploy.» | ok |
| R-INFRA-02 | progetto di B, sezione 3.4 (riga `infra`) | «Per i comandi di `wrangler` o `vercel` usa la documentazione ufficiale della versione installata.» | no |
| R-INFRA-02 | skill `wrangler`, sezione «Wrangler CLI» | «CLI flags and configuration fields change; do not rely on memorized examples.» | ok |
| R-INFRA-02 | developers.cloudflare.com/workers/wrangler/commands/, «How to run Wrangler commands» | `npx wrangler <COMMAND> <SUBCOMMAND> [PARAMETERS] [OPTIONS]` | ok |
| R-INFRA-02 | vercel.com/docs/cli/build | «The `vercel build` command can be used to build a Vercel Project locally or in your own CI environment.» | ok |
| R-INFRA-03 | progetto di B, sezione 3.4 (riga `infra`) | la riga parla di aprire la configurazione e di documentazione per i comandi, non delle proprietà dei file | no |
| R-INFRA-03 | vercel.com/docs/project-configuration, «File-based configuration» | «You can use `vercel.json` or `vercel.toml` for static configuration, or `vercel.ts` for programmatic configuration» | ok |
| R-INFRA-03 | developers.cloudflare.com/workers/wrangler/configuration/ | «`compatibility_date` `string` required» (la tabella descrive le chiavi di `wrangler.*`) | ok |
| R-INFRA-03 | skill `wrangler`, sezione «Wrangler CLI» | «CLI flags and configuration fields change; do not rely on memorized examples.» | ok |
| R-INFRA-04 | vercel.com/docs/project-configuration, «File-based configuration» | «You can only use one configuration file per project.» | ok |
| R-INFRA-04 | vercel.com/docs/project-configuration/vercel-ts, «Requirements» | «Use only one configuration file: `vercel.ts` or `vercel.json`.» | ok |
| R-INFRA-05 | developers.cloudflare.com/workers/configuration/secrets/, «Local Development with Secrets» | «Do not use `vars` to store sensitive information in your Worker's Wrangler configuration file.» | ok |
| R-INFRA-05 | vercel.com/docs/project-configuration/vercel-json, `env` e `build.env` | «We recommend against using this property.» (e rimanda alle impostazioni del progetto) | ok |
| R-INFRA-05 | vercel.com/docs/project-configuration/vercel-json, `env` e `build.env`, esempio | «the `SECRET` resolved from the `my-secret-name` secret dynamically» (valore `@my-secret-name`: riferimento a un segreto, non un segreto) | ok |
| R-INFRA-05 | vercel.com/docs/environment-variables, introduzione | «Secret values are write-only after saving.» | ok |
| R-INFRA-05 | docs.docker.com/build/building/secrets/, «Build secrets» | «Build arguments and environment variables are inappropriate for passing secrets to your build» | ok |
| R-INFRA-05 | docs.docker.com/build/building/best-practices/, `ENV` | anche se tolta in uno strato successivo, la variabile «still persists in this layer and its value can be dumped.» | ok |
| R-INFRA-06 | developers.cloudflare.com/workers/configuration/secrets/, «Local Development with Secrets» | «The `.dev.vars` and `.env` files should not be committed to git.» | ok |
| R-INFRA-06 | vercel.com/docs/environment-variables, «Development environment variables» | `vercel env pull` crea il `.env` (la pagina non dice di non versionarlo) | ok |
| R-INFRA-07 | developers.cloudflare.com/workers/wrangler/configuration/, nota iniziale | «Cloudflare recommends using `wrangler.jsonc` for new projects» | ok |
| R-INFRA-07 | developers.cloudflare.com/workers/configuration/compatibility-dates/, «Setting compatibility date» | «you should always set `compatibility_date` to the current date.» | ok |
| R-INFRA-08 | developers.cloudflare.com/workers/configuration/compatibility-dates/, «Setting compatibility date» | «you should refer to the compatibility flags page to find out what has changed» | ok |
| R-INFRA-09 | docs.docker.com/build/building/best-practices/, «Pin base image versions» | «Image tags are mutable, meaning a publisher can update a tag to point to a new image.» | ok |
| R-INFRA-10 | docs.docker.com/build/building/best-practices/, `USER` | «If a service can run without privileges, use `USER` to change to a non-root user.» | ok |
| R-INFRA-10 | docs.docker.com/build/building/best-practices/, «Exclude with .dockerignore» | il file si chiama `.dockerignore` e ha pattern «similar to `.gitignore` files.» | ok |
| R-INFRA-10 | docs.docker.com/build/concepts/context/, «.dockerignore files» | «the build client looks for a file named `.dockerignore` in the root directory of the context.» | ok |
| R-INFRA-11 | docs.docker.com/build/building/best-practices/, «Use multi-stage builds» | «Multi-stage builds let you reduce the size of your final image» | ok |
| R-INFRA-12 | spec del nucleo, sezione 8.5 «Effetti esterni» | l'elenco predefinito include `vercel`, `wrangler deploy`, `docker push`, `npm publish` | ok |
| R-INFRA-12 | developers.cloudflare.com/workers/wrangler/commands/workers/, `deploy`, `rollback`, `delete` | il `no` riguarda solo l'attribuzione di «`secret` cambia subito», che la pagina non dice (corretto: ora sta sulla pagina dei segreti); `--dry-run` e il resto reggono: «Compile a project without actually deploying to live servers.» | no |
| R-INFRA-12 | developers.cloudflare.com/workers/configuration/secrets/, «Adding secrets to your project» | «`wrangler secret put` creates a new version of the Worker and deploys it immediately» | ok |
| R-INFRA-12 | developers.cloudflare.com/workers/wrangler/commands/pages/ | «pages deploy: Deploy a directory of static assets as a Pages deployment» | ok |
| R-INFRA-12 | vercel.com/docs/cli/build | «Build artifacts are placed into the `.vercel/output` directory» | ok |
| R-INFRA-12 | vercel.com/docs/environment-variables, «Choose Config or Secret from the CLI» | «`vercel env add` and `vercel env update` accept these flags to set a variable's type» | ok |

Nota sulla riga `no` di R-INFRA-12: riguarda solo l'immediatezza di `secret`; il resto (`deploy` in modalità dry-run, `rollback`, `delete`, `triggers deploy`, `versions deploy`) è sostenuto dalla pagina. La pagina dei comandi dice «Create or update a secret», senza «subito». L'immediatezza di `secret put` è attribuita ora alla pagina dei segreti (riga `ok` sopra).

## Pattern dei percorsi

| Pattern | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| `infra/**` | catalogo dei profili verticali (progetto di B, sezione 2, riga `infra`) | `wrangler.{toml,jsonc}`, `workers/**`, `infra/**`, `Dockerfile*`, `**/*.tf` | ok |
| `**/vercel.json` | vercel.com/docs/project-configuration, «File-based configuration» | «You can use `vercel.json` or `vercel.toml` for static configuration, or `vercel.ts`» | ok |
| `**/vercel.toml` | stessa pagina e sezione | idem | ok |
| `**/vercel.ts` | stessa pagina e sezione | idem | ok |
| `**/wrangler.toml` | developers.cloudflare.com/workers/wrangler/configuration/, nota iniziale | «Wrangler supports both JSON (`wrangler.json` or `wrangler.jsonc`) and TOML (`wrangler.toml`)» | ok |
| `**/wrangler.json` | stessa pagina e sezione | idem | ok |
| `**/wrangler.jsonc` | stessa pagina e sezione | idem | ok |
| `**/Dockerfile*` | docs.docker.com/build/concepts/dockerfile/, «Filename» | «The default filename to use for a Dockerfile is `Dockerfile`, without a file extension.» | ok |
| `**/.dockerignore` | docs.docker.com/build/concepts/context/, «.dockerignore files» | «looks for a file named `.dockerignore` in the root directory of the context.» | ok |
| `**/compose.yaml` | docs.docker.com/compose/intro/compose-application-model/, «The Compose file» | «The default path for a Compose file is `compose.yaml` (preferred) or `compose.yml`» | ok |
| `**/compose.yml` | stessa pagina e sezione | idem | ok |
| `**/compose.override.yaml` | docs.docker.com/compose/how-tos/multiple-compose-files/merge/, «Merge Compose files» | «By default, Compose reads two files, a `compose.yaml` and an optional `compose.override.yaml` file.» | ok |
| `**/docker-compose.yaml` | docs.docker.com/compose/intro/compose-application-model/, «The Compose file» | «Compose also supports `docker-compose.yaml` and `docker-compose.yml` for backwards compatibility» | ok |
| `**/docker-compose.yml` | stessa pagina e sezione | idem | ok |

Note sui pattern:

- `infra/**` nel dialetto di `.gitignore` è ancorato alla radice; prende anche file che non sono di deploy dentro `infra/`, ma è la scelta del catalogo.
- `**/Dockerfile*` copre `Dockerfile` e un nome con un suffisso dopo `Dockerfile`. La pagina di Docker nomina anche la convenzione `<something>.Dockerfile` (per esempio `app.Dockerfile`): quella forma non è coperta, è una lacuna e non un eccesso, e la pagina per l'utente lo dice.
- `**/.dockerignore` copre il file nella radice del context. La forma `<nome del Dockerfile>.dockerignore` accanto al Dockerfile non è coperta (lacuna), e la pagina per l'utente lo dice.
- `.vercel/` non è un file del repo (lo crea `vercel pull` o il collegamento del progetto, e non si legge né si versiona): R-INFRA-01 chiede i file versionati.
- Nessun pattern è troppo largo oltre quanto detto per `infra/**` e `Dockerfile*`.

## Correzioni fatte dopo la verifica

- **R-INFRA-01.** «Dice dove gira oggi il progetto» resta, dichiarato «scelta nostra» nella riga `Fonte:`: nessuna delle due sezioni del progetto di B lo contiene.
- **R-INFRA-02.** La parte `docker` e `docker compose` resta, dichiarata «scelta nostra» (Docker è in `infra`, progetto di B, sezione 11). «Dove informarsi» aggiunge la documentazione ufficiale di Docker (https://docs.docker.com/).
- **R-INFRA-03.** La sezione 3.4 esce dalla riga `Fonte:`; restano le pagine di configurazione di Vercel e di Wrangler e la skill `wrangler`.
- **R-INFRA-12.** Il fatto che `secret put` pubblichi subito è attribuito alla pagina dei segreti di Cloudflare (sezione «Adding secrets to your project»), non alla pagina dei comandi. `versions secret put` non pubblica e non entra nell'elenco.

## Parti dichiarate «scelta nostra»

Vanno alla pagina per l'utente:

- R-INFRA-06, l'eccezione dei file `.example`, `.sample` e `.template` (un modello senza valori veri). Nella stessa regola la pagina di Vercel non dice di non versionare `.env.local` e `.env`: la riga `Fonte:` lo dichiara e la regola poggia sulla pagina di Cloudflare.
- R-INFRA-05, «e li imposta l'utente»: non viene da una pagina, è coerente con la sezione 8.5 della spec (punto 7 di «Cosa hai deciso» nella pagina).
- La sezione 3.4 del progetto di B è una proposta dell'autore che l'utente ha rivisto: le regole che la usano come fonte poggiano su quella proposta (la pagina lo dice nelle righe delle regole 1 e 2).

Imprecisioni minori, non `no`: in R-INFRA-04 «cartella» sta al posto di «progetto»; in R-INFRA-07 la regola è prescrittiva e la pagina «raccomanda»; in R-INFRA-08 «il report dice di aver letto» è il modo per verificare l'indicazione della pagina.

## Regole tolte

Nessuna regola esce: ciascuna ha almeno una fonte `ok`. Nessun pattern esce. Le quattro righe `no` sono fonti o parti di fonte corrette, descritte in «Correzioni fatte dopo la verifica».
