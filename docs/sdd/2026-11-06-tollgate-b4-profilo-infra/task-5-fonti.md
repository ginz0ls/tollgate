# Verifica delle fonti di rules-infra (Task 5, Step 1, verificatore Explore sonnet, 2026-11-07)

**Metodo.** Ho letto il brief, `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml`, `task-4-report.md`, `FONTI.md` e tutte le copie in `fonti/infra/`. Per `vercel-json.md` e `vercel-ts.md` ho usato `grep` e `sed -n`. Ho letto anche le sezioni 3.4 e 11 del progetto di B, la riga `infra` del catalogo (sezione 2, riga 41), la sezione 8.5 della spec del nucleo e il testo di `rules-infra`. `sha256sum -c SHA256SUMS`, eseguito in `.superpowers/sdd/2026-11-06-tollgate-b4-profilo-infra/fonti/infra/`, dà OK per tutti i 19 file. Nessuna rete, nessuno strumento di servizio, nessun file scritto.

Il punto 4 del brief vale per tutte le righe: ogni fonte è una pagina ufficiale con licenza annotata in `FONTI.md` («non dichiarata» per Vercel e Cloudflare, Apache-2.0 per Docker e per la skill `wrangler`), oppure il progetto di B o la spec del nucleo. Nessuna riga cade per questo punto.

Il punto 3 sul testo copiato: nessuna regola ha una frase identica di più di una decina di parole. Non c'è nessun `no` di forma.

### Tabella delle regole

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-INFRA-01 | progetto di B, 3.4 (riga `infra`) | «Prima di parlare di deploy, apri la configurazione già presente (`.vercel/`, `vercel.json`, `wrangler.toml`, `Dockerfile`, workflow).» | **no**: la regola aggiunge «e dice dove gira oggi il progetto», che la sezione 3.4 non contiene. |
| R-INFRA-01 | progetto di B, sezione 11 | «I file in `.github/workflows/` non accendono `infra` ... Le regole di `infra` chiedono comunque di leggerli prima di parlare di deploy.» | ok |
| R-INFRA-02 | progetto di B, 3.4 (riga `infra`) | «Per i comandi di `wrangler` o `vercel` usa la documentazione ufficiale della versione installata.» | **no** per la parte `docker` / `docker compose`: la riga nomina solo `wrangler` e `vercel`. Per Wrangler e Vercel la sezione regge. |
| R-INFRA-02 | skill `wrangler`, sezione «Wrangler CLI» | «CLI flags and configuration fields change; do not rely on memorized examples.» (e «state the gap ... rather than inventing syntax», sezione «Retrieve What the Task Needs») | ok |
| R-INFRA-02 | `cf-wrangler-commands.md`, «How to run Wrangler commands» | «`npx wrangler <COMMAND> <SUBCOMMAND> [PARAMETERS] [OPTIONS]`» | ok (la pagina descrive i comandi) |
| R-INFRA-02 | `vercel-cli-build.md`, pagina `cli/build` | «The `vercel build` command can be used to build a Vercel Project locally or in your own CI environment.» | ok |
| R-INFRA-03 | progetto di B, 3.4 (riga `infra`) | La riga parla di aprire la configurazione e di documentazione per i comandi. | **no**: non dice nulla sulle proprietà dei file di configurazione. |
| R-INFRA-03 | `vercel-project-configuration.md`, «File-based configuration» | «You can use `vercel.json` or `vercel.toml` for static configuration, or `vercel.ts` for programmatic configuration» (più la tabella delle proprietà) | ok |
| R-INFRA-03 | `cf-wrangler-configuration.md`, pagina della configurazione | «`compatibility_date` `string` required» (la pagina descrive le chiavi di `wrangler.*`) | ok |
| R-INFRA-03 | skill `wrangler`, «Wrangler CLI» | «CLI flags and configuration fields change; do not rely on memorized examples.» | ok |
| R-INFRA-04 | `vercel-project-configuration.md`, «File-based configuration» | «You can only use one configuration file per project.» | ok. «Cartella» è la traduzione operativa di «progetto». |
| R-INFRA-04 | `vercel-ts.md`, «Requirements» | «Use only one configuration file: `vercel.ts` or `vercel.json`.» | ok |
| R-INFRA-05 | `cf-workers-secrets.md`, «Local Development with Secrets» | «Do not use `vars` to store sensitive information in your Worker's Wrangler configuration file. Use secrets instead.» | ok |
| R-INFRA-05 | `vercel-json.md`, `env` e `build.env` | «We recommend against using this property. To add custom environment variables to your project define them in the Project Settings.» | ok |
| R-INFRA-05 | `vercel-environment-variables.md`, introduzione | «Environment variables are key-value pairs configured outside your source code ... Secret values are write-only after saving.» | ok |
| R-INFRA-05 | `docker-build-secrets.md`, «Build secrets» | «Build arguments and environment variables are inappropriate for passing secrets to your build, because they persist in the final image.» (più `docker build --secret` e `--mount=type=secret`) | ok |
| R-INFRA-05 | `docker-best-practices.md`, `ENV` | Anche se tolta in uno strato successivo, la variabile «still persists in this layer and its value can be dumped.» | ok |
| R-INFRA-06 | `cf-workers-secrets.md`, «Local Development with Secrets» | «The `.dev.vars` and `.env` files should not be committed to git.» e «Add `.dev.vars*` and `.env*` to your project's `.gitignore` file.» | ok |
| R-INFRA-06 | `vercel-environment-variables.md`, «Development environment variables» | «`vercel env pull` ... create and populate the `.env` file (which serves the same purpose as `.env.local`)» | ok. La riga `Fonte:` dichiara onestamente che la pagina non dice di non versionarli. |
| R-INFRA-07 | `cf-wrangler-configuration.md`, nota iniziale e «Inheritable keys» | «Cloudflare recommends using `wrangler.jsonc` for new projects» e «`compatibility_date` `string` required» | ok |
| R-INFRA-07 | `cf-compatibility-dates.md`, «Setting compatibility date» | «When you start your project, you should always set `compatibility_date` to the current date.» | ok |
| R-INFRA-08 | `cf-compatibility-dates.md`, «Setting compatibility date» | «When updating, you should refer to the compatibility flags page to find out what has changed» | ok. «Il report dice di averla letta» è il modo di verificare l'indicazione. |
| R-INFRA-09 | `docker-best-practices.md`, «Pin base image versions» | «Image tags are mutable, meaning a publisher can update a tag to point to a new image.» | ok. La copia non nomina `latest`; il titolo della sezione regge la regola. |
| R-INFRA-10 | `docker-best-practices.md`, `USER` | «If a service can run without privileges, use `USER` to change to a non-root user.» | ok |
| R-INFRA-10 | `docker-best-practices.md`, «Exclude with .dockerignore» | Il file si chiama `.dockerignore` e supporta pattern «similar to `.gitignore` files.» | ok |
| R-INFRA-10 | `docker-build-context.md`, «.dockerignore files» (nome e posizione) | «the build client looks for a file named `.dockerignore` in the root directory of the context.»; la forma «prefix the ignore-file with the name of the Dockerfile» | ok |
| R-INFRA-11 | `docker-best-practices.md`, «Use multi-stage builds» | «Multi-stage builds let you reduce the size of your final image» | ok |
| R-INFRA-12 | spec del nucleo, 8.5 «Effetti esterni» | L'elenco predefinito include `vercel`, `wrangler deploy`, `docker push`, `npm publish`. La tabella del nucleo (riga 163) dice «Negati finché non c'è un atto». | ok |
| R-INFRA-12 | `cf-wrangler-commands-workers.md`, `deploy`, `secret`, `rollback` ecc. | «`--dry-run`: Compile a project without actually deploying to live servers.» | **no** solo per «`secret` ... cambiano subito»: la pagina dei comandi dice «Create or update a secret for a Worker», senza «subito». L'immediatezza sta in `cf-workers-secrets.md` («`wrangler secret put` creates a new version of the Worker and deploys it immediately»), e `versions secret put` non pubblica. Tutto il resto (`deploy --dry-run`, `rollback`, `delete`, `triggers deploy`, `versions deploy`) è sostenuto dalla pagina. |
| R-INFRA-12 | `cf-wrangler-commands-pages.md`, sezione «Pages» | «pages deploy: Deploy a directory of static assets as a Pages deployment»; «pages secret put: Create or update a secret variable for a Pages project» | ok |
| R-INFRA-12 | `vercel-cli-build.md`, pagina `cli/build` | «Build artifacts are placed into the `.vercel/output` directory» e «It is recommended to run the `vercel pull` command before invoking `vercel build`» | ok |
| R-INFRA-12 | `vercel-environment-variables.md`, «Choose Config or Secret from the CLI» | «`vercel env add` and `vercel env update` accept these flags to set a variable's type» | ok |

### Tabella dei pattern

| Pattern | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| `infra/**` | Catalogo dei profili verticali, sezione 2, riga `infra` | `wrangler.{toml,jsonc}`, `workers/**`, `infra/**`, `Dockerfile*`, `**/*.tf` | ok. Nel dialetto di `.gitignore` il pattern è ancorato alla radice, come dice il commento. Prende anche file non di deploy dentro `infra/`, ma è la scelta del catalogo. |
| `**/vercel.json` | `vercel-project-configuration.md`, «File-based configuration» | «You can use `vercel.json` or `vercel.toml` for static configuration, or `vercel.ts`» | ok |
| `**/vercel.toml` | stessa pagina e sezione | idem | ok |
| `**/vercel.ts` | stessa pagina e sezione | idem | ok |
| `**/wrangler.toml` | `cf-wrangler-configuration.md`, nota iniziale | «Wrangler supports both JSON (`wrangler.json` or `wrangler.jsonc`) and TOML (`wrangler.toml`)» | ok |
| `**/wrangler.json` | idem | idem | ok |
| `**/wrangler.jsonc` | idem | idem | ok |
| `**/Dockerfile*` | `docker-dockerfile-concepts.md`, «Filename» | «The default filename to use for a Dockerfile is `Dockerfile`, without a file extension.» | ok. Il `*` può prendere un `Dockerfile.md` o simili, ma è lo schema del catalogo. La convenzione `<something>.Dockerfile` della pagina non è coperta: è una lacuna, non un eccesso. |
| `**/.dockerignore` | `docker-build-context.md`, «.dockerignore files» | «looks for a file named `.dockerignore` in the root directory of the context.» | ok. La forma `<nome>.dockerignore` accanto al Dockerfile non è coperta (lacuna). |
| `**/compose.yaml` | `docker-compose-application-model.md`, «The Compose file» | «The default path for a Compose file is `compose.yaml` (preferred) or `compose.yml`» | ok |
| `**/compose.yml` | stessa pagina e sezione | idem | ok |
| `**/compose.override.yaml` | `docker-compose-merge.md`, «Merge Compose files» | «By default, Compose reads two files, a `compose.yaml` and an optional `compose.override.yaml` file.» | ok |
| `**/docker-compose.yaml` | `docker-compose-application-model.md`, «The Compose file» | «Compose also supports `docker-compose.yaml` and `docker-compose.yml` for backwards compatibility» | ok |
| `**/docker-compose.yml` | stessa pagina e sezione | idem | ok |

### Riepilogo

- **Tabella delle regole:** 31 righe, 27 `ok` e 4 `no`.
- **Tabella dei pattern:** 14 righe, 14 `ok`, 0 `no`. Nessun pattern è troppo largo oltre quanto già detto per `infra/**` e `Dockerfile*`.
- **Regole senza nessuna fonte `ok`:** nessuna. Ogni regola ha almeno una fonte `ok`.
- **Regole con almeno una fonte `no`, con la correzione minima:**
  - **R-INFRA-01 (progetto di B, 3.4).** Togliere «e dice dove gira oggi il progetto», oppure dichiararlo «scelta nostra» nella riga `Fonte:`.
  - **R-INFRA-02 (progetto di B, 3.4).** La parte `docker` / `docker compose` non ha fonte: la sezione 3.4 nomina solo `wrangler` e `vercel`. O si limita la regola ai due strumenti, o si dichiara l'estensione a Docker «scelta nostra» (la sezione 11 copre Docker per `infra`, ma non dice di citare pagine di comandi).
  - **R-INFRA-03 (progetto di B, 3.4).** La riga parla di documentazione per i comandi, non per le proprietà dei file di configurazione. Togliere 3.4 da questa `Fonte:`, o dichiarare «scelta nostra» l'obbligo per le proprietà. Le altre tre fonti reggono la regola.
  - **R-INFRA-12 (`cf-wrangler-commands-workers.md`).** Spostare «`secret` ... cambiano subito» sulla pagina dei segreti (`https://developers.cloudflare.com/workers/configuration/secrets/`, sezione «Adding secrets to your project»), oppure togliere `secret` dall'elenco di ciò che cambia subito. `versions secret put` non pubblica.
- **Parti dichiarate «scelta nostra» (da portare all'utente):**
  - R-INFRA-06, l'eccezione dei file `.example`, `.sample` e `.template`. Nella stessa regola, il fatto che la pagina di Vercel non dica di non versionare `.env.local` e `.env` è già dichiarato nella riga `Fonte:`.
  - La sezione 3.4 del progetto di B è una proposta «(mia scelta)» che l'utente rivede con la sezione 5. Le righe che la usano come fonte poggiano su quella scelta.
- **Imprecisioni minori, non `no`:**
  - R-INFRA-05: «e li imposta l'utente» non viene da nessuna pagina, ma è coerente con 8.5.
  - R-INFRA-04: «cartella» sta al posto di «progetto» (le pagine non parlano di cartelle).
  - R-INFRA-08: la pagina dice «should refer»; «il report dice di aver letto» è il modo per verificarlo.
  - R-INFRA-07: la regola è prescrittiva, la pagina «raccomanda».
- **Pattern `no`:** nessuno.
