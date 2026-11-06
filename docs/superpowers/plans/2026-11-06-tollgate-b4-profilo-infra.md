# tollgate B4: profilo `infra`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il secondo profilo verticale, `infra` (configurazione e deploy su Vercel, Cloudflare e Docker), con le regole `rules-infra` scritte dalle pagine ufficiali, verificate e approvate dall'utente, gli agenti `implementer-infra` e `reviewer-infra`, e ciò che manca perché il profilo funzioni: frammenti che nominano file e cartelle alla radice, non solo cartelle a qualunque profondità, e i comandi di deploy lanciati con `npx` riconosciuti come effetti esterni.

**Architecture:** Il frammento `templates/profiles/infra.toml` usa tre forme di pattern: `**/<cartella>/**` (già di B3), `<cartella>/**` (una cartella alla radice) e `**/<nome>` (un file con quel nome, a qualunque profondità). Le forme si riconoscono in un solo punto, `fragments.parse_pattern`; `init` lo usa per i percorsi concreti: per una cartella il prefisso fino alla cartella, come in B3, per un nome di file il percorso esatto del file. I file di documentazione non accendono più un profilo per cartella. `infra` non ha marcatori di contenuto: i suoi file si riconoscono dal nome. `bash.effect_reason` guarda anche il comando lanciato da `npx` e simili, così `npx wrangler deploy` è un effetto da approvare come `wrangler deploy`. A runtime il resto del nucleo non cambia: il profilo vive nel `tollgate.toml` del progetto. Gli agenti per area sono copie dichiarate dei generici, come `-ai`.

**Tech Stack:** Python ≥ 3.11, solo libreria standard; bash; git; Claude Code (`claude plugin validate --strict`; la prova reale con `claude -p --plugin-dir` solo dal controller). Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** il progetto approvato `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (l'autorità: «utente» non si discute, «mia scelta» si corregge solo con un motivo scritto qui), soprattutto le sezioni 1 («è su Vercel, leggi le cose prima»), 2, 3.4 (righe `infra` e `backend`), 4 (riga `infra`: L1, va aggiunto Vercel), 5 e **11 (scelte dell'utente del 6 novembre 2026: workflow al gate, codice dei Worker in `backend`, Docker sì)**; la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 30 (la 31 la scrive il Task 10): 6.3, 7.1, 7.3, 8.5, 9.2, 11.2, 11.4, 16, 18.4; il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, sezioni 1 (principi 6 e 7), 2 (riga `infra` e nota sulle graffe), 2.1, 2.2, 2.3 e 4. Piano principale di B: `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, riga B4 della sezione 2, righe B1→B3-B7, B2→B3-B7 e B3→B4-B7 della sezione 3, rinvii «A B3-B7» e «A B4-B7, da B3» della sezione 9.

## Fatti verificati (6 novembre 2026, pagine ufficiali aperte con WebFetch, e codice di `main`)

| Fatto | Fonte | Conseguenza qui |
|---|---|---|
| Wrangler legge `wrangler.toml`, `wrangler.json` e `wrangler.jsonc` (JSON da Wrangler 3.91.0); Cloudflare consiglia `wrangler.jsonc` per i progetti nuovi; la pagina non dice dove deve stare il file, ma i file locali dei segreti stanno «nella stessa cartella» | https://developers.cloudflare.com/workers/wrangler/configuration/ | tre nomi di file nel frammento, a qualunque profondità; una regola non bloccante sul formato dei progetti nuovi |
| Cloudflare consiglia Wrangler installato nel progetto, lanciato con `npx wrangler …` | https://developers.cloudflare.com/workers/wrangler/commands/ | «Dove informarsi»: la versione installata; Task 3 (`npx`) |
| `wrangler deploy --dry-run` compila senza pubblicare (`--outdir` per vedere il risultato); la pagina non dice se servono credenziali; `wrangler types --check` confronta solo i tipi generati con la configurazione | https://developers.cloudflare.com/workers/wrangler/commands/workers/ | `dod` vuoto (decisione 7) |
| I segreti di un Worker non vanno in `vars` della configurazione; si mettono con `wrangler secret put` (o `wrangler versions secret put` con i rilasci graduali); in locale stanno in `.dev.vars` o `.env` accanto alla configurazione, file che non si committano | https://developers.cloudflare.com/workers/configuration/secrets/ | regole sui segreti |
| Pubblicano o cambiano subito ciò che è in linea: `wrangler secret put`, `secret delete`, `secret bulk` (creano una versione e la pubblicano), `wrangler rollback`, `wrangler delete`, `wrangler triggers deploy`, `wrangler versions deploy`, `wrangler pages deploy`. Creano solo una versione non pubblicata: `wrangler versions upload`, `wrangler versions secret put`. Leggono soltanto: `wrangler versions list`, `versions view`, `secret list`. `wrangler pages publish` non compare nella pagina di Pages | https://developers.cloudflare.com/workers/wrangler/commands/workers/, https://developers.cloudflare.com/workers/wrangler/commands/pages/ | voci nuove degli effetti (decisione 17) |
| `compatibility_date` non è obbligatoria (le date vecchie restano valide per sempre); si consiglia la data del giorno a inizio progetto e aggiornamenti occasionali dopo aver letto i flag | https://developers.cloudflare.com/workers/configuration/compatibility-dates/ | regola non bloccante |
| Vercel legge `vercel.json`, `vercel.toml` o `vercel.ts`, **uno solo per progetto**; il supporto di `now.json` finisce il 31 marzo 2026 | https://vercel.com/docs/project-configuration | tre nomi di file nel frammento; regola «un solo file» |
| `vercel link` crea `.vercel/` con `project.json` (`orgId`, `projectId`) | https://vercel.com/docs/cli/project-linking | `.vercel/` non è un pattern: di solito non è tracciata |
| `vercel build` costruisce in locale in `.vercel/output`; prima si consiglia `vercel pull` (impostazioni e variabili del progetto collegato) | https://vercel.com/docs/cli/build | `dod` vuoto (decisione 7) |
| Le variabili di Vercel sono `Config` o `Secret` (queste ultime solo in scrittura); in locale stanno in `.env.local` o nel `.env` di `vercel env pull` | https://vercel.com/docs/environment-variables | regole sui segreti |
| Compose legge `compose.yaml` (preferito), `compose.yml`, e per compatibilità `docker-compose.yaml` e `docker-compose.yml` | https://docs.docker.com/compose/intro/compose-application-model/ | quattro nomi di file |
| Buone pratiche dei Dockerfile: build a stadi, `.dockerignore`, versione dell'immagine di base fissata, utente non root quando non servono privilegi; un valore messo con `ENV` resta nello strato anche dopo averlo tolto | https://docs.docker.com/build/building/best-practices/ | regole non bloccanti su Dockerfile; segreti |
| I segreti di una build passano con `docker build --secret` e `RUN --mount=type=secret`, non con argomenti di build né variabili d'ambiente, che restano nell'immagine | https://docs.docker.com/build/building/secrets/ | regola sui segreti |
| Licenze: il repository delle skill di Cloudflare (`cloudflare`, `wrangler`, `workers-best-practices` e altre) è Apache-2.0; il repository della documentazione di Docker è Apache-2.0; le pagine di Vercel e Cloudflare non dichiarano una licenza nella pagina | https://github.com/cloudflare/skills, https://github.com/docker/docs | si prendono i fatti con parole nostre, come per `rules-ai` (catalogo 1.7) |
| `globs` (dialetto di `.gitignore`) fa corrispondere un pattern anche a tutto ciò che sta sotto (suffisso `(?:/.*)?` in `globs.compile`): `globs.match("**/Dockerfile*", "docker/Dockerfiles/README.md")` è vero; `literal_segments("web/Dockerfile*")` vale 1, come `web/**` | `bin/tollgate_analysis/globs.py` | la forma `name` si confronta sul solo nome del file e propone percorsi esatti (decisioni 2 e 3) |
| `bash.effect_reason` confronta con `_DEFAULT_EFFECTS` il solo nome del programma (`basename(argv[0])`): `vercel` (ogni sottocomando), `wrangler deploy` e `wrangler publish` sono effetti; `npx wrangler deploy`, `npx vercel --prod`, `npx supabase db push`, `wrangler secret put`, `wrangler pages deploy` no; il ramo `supabase` guarda anch'esso `a[0]`. `bash.is_claude` (`bash.py:903-911`) ha un suo elenco di lanciatori | `bin/tollgate_analysis/bash.py:903-1103` | Task 3 (decisione 17) |
| `spikes/run-b1-flow.sh` vieta al modello solo `gh` per percorso, `git push` verso la rete, `curl` e `wget` (`DISALLOWED`) | `spikes/run-b1-flow.sh:76-79` | Task 8 (decisione 14) |
| Nei progetti dell'utente sul disco (contati per nome di file, senza aprirli né nominarli): `Dockerfile*` in 6 cartelle, `docker-compose.y*ml` in 4, `vercel.json` in 10, `vercel.ts` in 1, file di Wrangler in 3, `*.tf` in 1 | `find` locale del 6 novembre | progetto 11: Docker sì, Terraform no |

**Da verificare prima del codice** (controller, Task 4, Step 0): (a) la pagina di Docker che dà il nome predefinito `Dockerfile` e le forme con suffisso (`Dockerfile.<x>`); (b) la pagina di Docker sul file `.dockerignore` (nome e posizione); (c) le pagine di `vercel.json` e `vercel.ts` per le proprietà citate dalle regole. Se un fatto della tabella sopra risulta smentito al punto da cambiare una decisione, il controller si ferma e chiede. Una forma con prefisso (`<x>.Dockerfile`) non entra, anche se la pagina la mostra: la forma `name` non ammette un `*` iniziale (decisione 2), e il costo (un `app.Dockerfile` non accende `infra`) si scrive in una `Ruling:`.

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`); verifica finale come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`.
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`.
- **Nessuna operazione nuova in `apply._OPS`** (29) e **nessun tipo nuovo in `events.EVENT_TYPES`** (33).
- **Nessuna rete**, né nei test né per i subagenti: le fonti delle regole sono copie locali messe dal controller nel workspace (Task 4, Step 0), che **non entrano mai in git** né nella copia del registro in `docs/sdd/`. Nessun `claude` vero nei test; `gh` è `tests/fakegh.py`. **Nessun `vercel`, `wrangler`, `docker`, `npx`, `npm`, `pnpm`, `yarn` o `bunx` vero** nei test, negli script e nei comandi dei subagenti: nei test sono solo testo dato a `bash.parse`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`, `~/.claude/projects/`.
- **Test con la radice del plugin esplicita**: ogni test nuovo che legge frammenti, skill o agenti usa una radice temporanea, salvo i `test_real_…` e i file `tests/test_rules_*.py`, che sono sui file veri della loro area.
- **Cartelle temporanee dei test** (piano principale, sezione 9, «A B4-B8, da B3-bis»): ogni `mkdtemp` si chiude con `addCleanup`; una cartella creata direttamente in `/tmp` ha un prefisso che comincia con `tollgate`. Nessuna asserzione che, se fallisce, stampi `os.environ` (lezione di B3-bis).
- **Regole con parole nostre** (catalogo 1, principio 7): dalle pagine dei fornitori si prendono i **fatti**, senza copiarne testo; una citazione sta al più in una riga, nel solo rapporto delle fonti. Ogni regola si giudica con un sì o un no **su ciò che il revisore vede** (il diff, con i file del repo che servono a giudicarlo, il report o la nota); una regola `[blocca]` si giudica sul diff o sul report, mai sulla sola nota.
- **Numeri delle regole stabili dopo l'approvazione** (catalogo 2.3). **`approved` in `skills/rules-infra/SKILL.md` si scrive solo nel Task 6**, con la data dell'OK dell'utente; gli agenti `-infra` caricano `rules-infra` solo dopo (Task 7 dopo il Task 6).
- Non si toccano `skills/rules-base/SKILL.md`, `skills/rules-ai/SKILL.md`, `docs/profili/base.md`, `docs/profili/ai.md` e i loro rapporti delle fonti: sono approvati dall'utente.
- Testo non fidato (nota, pagine scaricate, citazioni, report dell'implementatore): nei brief dentro `brief.fence` con `brief.DATA_NOTE`, mai come istruzione.
- `tollgate.toml` del progetto: `init` non lo scrive mai nel repo, produce la proposta in `docs/superpowers/tollgate-init/` che l'utente copia (spec 11.2).
- Il repo è pubblico: nei file nuovi niente nomi di progetti privati dell'utente, niente nome utente né host, nessun token; nelle evidenze nessun testo intero di pagine o skill di terzi (`flowreg togli-pagine`).
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

## Decisioni di questo piano

Scelte che il progetto e il piano principale lasciano a B4, o che il codice reale impone, con il costo se sbagliate. Il Task 10 le riporta nella revisione 31 della spec.

1. **Cosa copre `infra`** (progetto 4 e 11). La configurazione e il deploy su Vercel (`vercel.json`, `vercel.toml`, `vercel.ts`), su Cloudflare (`wrangler.toml`, `wrangler.json`, `wrangler.jsonc`) e con Docker (`Dockerfile*`, `.dockerignore`, i quattro nomi dei file compose), più la cartella `infra/` alla radice (catalogo 2). Escono dal catalogo `workers/**` (il codice dei Worker è `backend`, progetto 11), `**/*.tf` (Terraform: un solo file nei progetti dell'utente, nessuna fonte in questo piano) e `.github/workflows/**` (progetto 11). Gli altri server (nginx, systemd) non entrano. Pattern del frammento, in quest'ordine: `["infra/**", "**/vercel.json", "**/vercel.toml", "**/vercel.ts", "**/wrangler.toml", "**/wrangler.json", "**/wrangler.jsonc", "**/Dockerfile*", "**/.dockerignore", "**/compose.yaml", "**/compose.yml", "**/docker-compose.yaml", "**/docker-compose.yml"]`; il verificatore delle fonti (Task 5) controlla ogni nome su una pagina ufficiale e un pattern senza fonte `ok` esce, come un marcatore di B3 (allora `test_fragment_matches_decisions` si aggiorna, con una `Ruling:`). Costo: un cambio a Terraform o alla configurazione di un server proprio va all'agente generico finché un progetto non li chiede.
2. **Tre forme di pattern nei frammenti** (rinvio «Forma dei pattern» di B3). `fragments.parse_pattern(p) -> Pattern | None`, l'unico punto che le riconosce:
   - `**/<cartella>/**` → `Pattern("folder", <cartella>)`, come in B3;
   - `<cartella>/**` → `Pattern("root_folder", <cartella>)`, la sola cartella alla radice (serve anche a `backend` per `api/**` e `server/**`);
   - `**/<nome>` → `Pattern("name", <nome>)`: un **file** con quel nome, a qualunque profondità.
   `<cartella>` è un segmento senza `*`, `?`, `[`, `]`, `!`, `\` e diverso da `.` e `..` (la regex di B3). `<nome>` è un tratto letterale di lettere ASCII, cifre, `.`, `_`, `-`, lungo almeno 2 caratteri, con almeno una lettera, diverso da `.` e `..`, seguito al più da **un solo `*` finale** (`Dockerfile*`). Sono quindi rifiutati `**/*.sql`, `**/*.json`, `**/*.Dockerfile` (un `*` iniziale accenderebbe ogni file di un tipo: la forma giusta per `database` la decide B7). Ogni altra forma è una `FragmentError` (graffe comprese: `globs` non le espande, catalogo 2). `fragments.load` usa `parse_pattern` al posto di `_PATTERN`; `init` lo usa al posto di `_FOLDER_PATTERN` (che sparisce). Costo: nessuno; una forma nuova si aggiunge in quel solo punto.
3. **Percorsi concreti per le forme nuove** (decisione 5 di B3, estesa). Per ogni file tracciato fuori da `init.EXCLUDED_PREFIXES` (decisione 18), `init.concrete_for(path, patterns)`:
   - **prima le forme a cartella**, come in B3: la prima cartella del percorso (da sinistra) che ha il nome di un pattern `folder` dà `<percorso fino a quella cartella, compresa>/**` passato da `globs.escape`; se il primo segmento è il nome di un pattern `root_folder`, dà `/<cartella>/**`. Tra le due vale la cartella più a sinistra (`infra/x/ai/y.py` con `infra/**` e `**/ai/**` dà `/infra/**`);
   - **poi la forma `name`**, solo se nessuna forma a cartella ha acceso il file: il **nome del file** (l'ultimo segmento) si confronta con il nome del pattern con `fnmatch.fnmatchcase` (mai `globs.match`, che accenderebbe anche le cartelle con quel nome), e il percorso concreto è il **percorso esatto** del file passato da `globs.escape` (`/vercel.json` alla radice, `services/api/Dockerfile.prod`).
   Un percorso esatto già coperto da un percorso a cartella proposto si toglie; tra i percorsi a cartella si toglie quello coperto da uno più corto, come in B3. I percorsi esatti hanno tutti i segmenti letterali, quindi vincono per specificità (spec 6.3) su un `web/**` o su un `services/api/**` già dichiarati (`web/Dockerfile` vale 2 segmenti, `web/**` 1). Fa eccezione un percorso con un segmento escapato, che `globs.literal_segments` non conta (`app/\[id\]/vercel.json` vale 2, non 3: piano principale, sezione 9): a parità vince il profilo dichiarato per primo, e `infra`, aggiunto in coda, perde; la riga di sovrapposizione della proposta lo mostra. Costo: un `Dockerfile` o un `vercel.json` nuovo, anche nella stessa cartella, non è coperto finché l'utente non applica la riga di `init --update` (decisione 7 di B3).
4. **I documenti non accendono un profilo per cartella** (rinvio «Cartelle `agents/` e `prompts/` e file che non sono codice» di B3). Un file la cui estensione, confrontata in minuscolo (`README.MD` conta), è in `init.DOC_EXTENSIONS = ("md", "mdx", "markdown", "rst", "txt", "adoc")` non accende le forme `folder` e `root_folder` e passa alle forme `name`; lì un nome con `*` non accende un documento (`docs/Dockerfile-note.md` resta fuori), un nome letterale sì (è esplicito). Vale per tutte le aree: `docs/ai/guida.md` o `.github/agents/x.agent.md` non propongono più `ai`. Una volta proposto `src/ai/**`, un markdown lì dentro va comunque all'agente dell'area (`vertical_for` guarda i percorsi): l'esclusione decide solo la proposta. La pagina approvata `docs/profili/ai.md` («Quando si accende») resta com'è: il Task 10 scrive la differenza nella spec e nel piano principale, e il rapporto finale la dice all'utente. Costo: una cartella che contiene solo documenti non riceve più la proposta; un file senza estensione (`README`, `LICENSE`, `CHANGELOG`) accende ancora le cartelle.
5. **Nessun rilevamento per contenuto per `infra`** (brief, «Da decidere»). I file di `infra` si riconoscono dal nome; i file non sorgente (`.toml`, `.json`, `.yaml`, `Dockerfile`) non hanno righe di import da cercare. Il frammento non ha `[detect]`; `init.SOURCE_EXTENSIONS` resta com'è. Il codice che usa le librerie di runtime (`cloudflare:workers`, `@vercel/functions`) è `backend` (progetto 11) e lo rileverà B5, se serve. Costo: nessuno per `infra`.
6. **CI del progetto** (progetto 11, utente). `.github/workflows/**` non è nei percorsi di `infra`: un workflow del progetto resta del gate (`guard` lo rifiuta se potrebbe pubblicare stati falsi, la deroga `ci` di test-guard per ogni modifica, spec 9.2 e 8.3) e, dopo B, del profilo `ci`. `rules-infra` chiede di leggere i workflow di deploy prima di parlare di deploy (R-INFRA-01). Costo: un task che cambia solo un workflow di deploy va all'agente generico.
7. **`dod` e comandi di `infra` vuoti** (catalogo 2.3: «`wrangler deploy --dry-run` o equivalente», proposta da confermare). Il comando dipende dal progetto: per Vercel la prova in locale vuole un progetto collegato e `vercel pull` (Fatti verificati), e ogni comando `vercel` è un effetto esterno da approvare (spec 8.5); per Cloudflare `wrangler deploy --dry-run` compila senza pubblicare, ma vuole Wrangler installato, la pagina non dice se servono credenziali, ed è anch'esso un effetto (`wrangler deploy`). Un `dod` scritto da `init` fallirebbe o chiederebbe un'approvazione in ogni progetto che non lo regge. Quindi il frammento ha `commands = {}` e `dod = []`; la pagina per l'utente (Task 5) dice come aggiungere a mano un comando del profilo (per esempio `deploy-check = "npx wrangler deploy --dry-run"`), metterlo in `dod`, e approvarlo una volta con `/tollgate:approve effect <id>` o metterlo in `[external_effects] allow`. R-INFRA-11 chiede al report quale prova senza pubblicazione è stata fatta o perché no. Costo: nessun controllo automatico del deploy finché l'utente non lo aggiunge.
8. **`rules-infra` precaricata, non nel brief** (decisione 9 di B3, modello per B4-B7). `implementer-infra` e `reviewer-infra` hanno `skills: [rules-base, rules-infra]`; il frammento ha `skills = []` e `reviewer_skills = []`. Le skill del catalogo 2.1 restano fuori dal frammento: «Dove informarsi» di `rules-infra` nomina `wrangler` e `cloudflare` (Cloudflare, Apache-2.0); `workers-best-practices` riguarda il codice dei Worker, che è `backend` (progetto 11), e non si nomina qui. Costo: come in B3, circa 2.000-3.000 token in più per lancio; nei task misti le regole dell'area non arrivano all'agente.
9. **Agenti per area derivati dai generici** (decisioni 10 e 11 di B3). `agents/implementer-infra.md` e `agents/reviewer-infra.md`: il testo di `implementer.md` e `task-reviewer.md`, lo stesso frontmatter tranne `name`, `description`, `skills` e, per il revisore, `tools` (`Read, Grep, Glob, Bash, WebFetch`), la riga di attribuzione MIT e una sezione «Area `infra`». `tollgate:reviewer-infra` entra in `READONLY_TYPES` di `hooks/run` e in `config.DEFAULTS["review"]["readonly_agents"]`. Gli id `R-<AREA>-…` della sezione d'area si confrontano con la skill in un solo test per tutte le aree (`AREAS = ("ai", "infra")`, rinvio T8-1 di B3), con questa regola: nella sezione «Area `<area>`» del revisore l'insieme degli id nominati è uguale a quello della skill; la frase (il testo tra due punti fermi) che contiene «si giudicano sul report» nomina esattamente le regole che la skill segna «Si giudica su: report», e quella che contiene «si giudicano sul diff» esattamente le altre; nella sezione dell'implementatore la frase che contiene «sul tuo report» nomina esattamente le regole sul report. Il testo di `agents/*-ai.md` soddisfa già questa regola. I due `assertIn` di `tests/test_manifest.py` che fissano frasi esatte restano: il test d'area nuovo cerca gli id, non le frasi. Costo: due file in più, tenuti allineati dal test di deriva.
10. **Piccole cose rimaste aperte nel codice di B3** (piano principale, sezione 9). Si chiudono: `fragments.load_approved(plugin_root)`, l'unico punto con `load` e il filtro `approved`, usato da `init.propose` e da `init.profile_blocks`; `fragments.rules(fragment)` con la skill che non si legge è una `FragmentError` con il nome del file, non più `([], [])`; ogni `tests/test_rules_<area>.py` nuovo ha `test_blocca_lines_have_text` (una riga `R-<AREA>-NN [blocca]` senza testo dopo sarebbe una regola nota ma non bloccante); `tests/test_fragments.py` usa `tomlout` al posto dell'helper `tomlout_str`. Restano aperte, con il motivo: `tomlout.table` che divide `name` sui punti (i nomi d'area sono `[a-z0-9-]+`) e «profili non valutati» per un repo senza file (messaggio esplicito, ramo testato). Costo: nessuno.
11. **B4 non si unisce a un'altra fetta** (piano principale, sezione 2). Porta le forme nuove dei pattern e gli effetti dietro `npx`, che servono a B5-B7, più un profilo con la sua pagina da approvare: non è piccola. Costo: un giro di piano in più per B5.
12. **Fonti di `rules-infra`** (catalogo 4: «skill Cloudflare (Apache-2.0)», più Vercel per il progetto 4). Le pagine ufficiali della tabella «Fatti verificati» più quelle dello Step 0 del Task 4; la skill `wrangler` del repository di Cloudflare (Apache-2.0) per l'idea «documentazione della versione installata»; le scelte dell'utente con `Fonte: progetto di B, sezione 3.4` o `sezione 11`; la spec del nucleo 8.5 per gli effetti esterni. Le copie locali le fa il controller (Task 4, Step 0) con `SHA256SUMS` e `FONTI.md`. Costo: le pagine cambiano; il rapporto delle fonti ha la data.
13. **Livello e tipo** (progetto 4): `kind = "vertical"`, `min_level = "L1"`, `agent = "tollgate:implementer-infra"`, `reviewer = "tollgate:reviewer-infra"`, nessuno specialista finale.
14. **Prova reale corta** (Task 8 e 9), come in B3: un progetto di prova `spikes/b4/flow/` con `vercel.json`, un `Dockerfile` e un po' di codice, un lavoro L1 che chiede di aggiungere un'intestazione di sicurezza in `vercel.json`. Si prova: `init` propone `infra` con i percorsi esatti, `implementer-infra` e `reviewer-infra` lanciati, `rules-infra` precaricata, nota valida, nessun comando di servizio eseguito. Le credenziali dell'utente per Vercel e Cloudflare possono stare in file della sua cartella (dopo `vercel login` o `wrangler login`), non solo in variabili: per questo, con `B1_FLOW_CASE=infra`, `DISALLOWED` vieta al modello anche `vercel`, `wrangler`, `docker`, `npx`, `bunx`, `pnpx`, `bun`, `npm`, `pnpm`, `yarn` (da soli, con un percorso, dopo `command` e dopo `env`), `registra` cerca quei comandi nello stream, e il piano del lavoro dice che la prova senza pubblicazione non si fa e che il report dice perché. Costo: circa 1-1,5 USD stimati sull'abbonamento (B3: 1,32), nessuna spesa in denaro; R-INFRA-11 si vede dal vivo solo nel ramo «perché no».
15. **Fermata per l'approvazione e unione anticipata.** La sessione d'esecuzione si ferma per l'utente nel Task 6, dopo la verifica delle fonti e la pagina. Se l'utente rinvia, su `main` si possono unire solo i commit dei Task 1-3 (forme dei pattern, percorsi concreti, documenti esclusi, effetti dietro `npx`), con la parte della revisione 31 che li riguarda (decisioni 2-4, 10, 16-18), scritta come un Task 10 ridotto; bozza, pagina e frammento di `infra` restano sul ramo, e il rapporto lo dice. Costo: B4 resta aperta.
16. **Test di `init` sulla radice vera** (rinvio «Test esistenti che girano sulla radice vera» di B3). `test_real_trees_light_no_profile` si estende all'albero che spingono le classi di `tests/test_init.py` che lanciano la CLI: `DEFAULT_FILES` (da `tests.hookkit`), `JUNIT_FILES` e `GATE_FILES` con `.github/tollgate/VERSION` (da `tests.flowkit`), `package.json` e `.github/workflows/ci.yml` (spinti da `HintsTest`), l'albero installato e la proposta. Così il frammento vero di `infra` non cambia in silenzio l'uscita di quei test. Costo: nessuno.
17. **Comandi di servizio dietro un lanciatore** (spec 8.5; Fatti verificati). `bash.unwrap_launcher(argv)` dà l'`argv` del programma lanciato; `effect_reason` la calcola una volta (`u`) e la usa per `_DEFAULT_EFFECTS` **e per il ramo `supabase`**, mentre `project_scripts`, `curl`, `wget` e `gh` restano sull'`argv` originale, e `[external_effects] commands` e `allow` sul testo di tutto il comando, come oggi. Regole di `unwrap_launcher`:
   - lanciatori: `npx`, `bunx`, `pnpx`, `npm exec`, `npm x`, `bun x`, `pnpm exec`, `pnpm dlx`, `yarn dlx`, `yarn exec`; inoltre `pnpm <p>` e `yarn <p>` quando `<p>` è il nome di un programma di `_DEFAULT_EFFECTS` o `supabase` (gli altri sottocomandi di `pnpm` e `yarn` non cambiano);
   - opzioni prima del programma: senza valore `--yes`, `-y`, `--no`, `--quiet`, `-q`, `--silent`, `--ignore-existing`; con valore (nella forma `--x v` o `--x=v`) `--package`/`-p`, `--registry`, `--cache`, `--workspace`/`-w`, `--prefix`, `--userconfig`; il separatore `--` si salta;
   - `-c <testo>` e `--call <testo>`: il testo si analizza con `bash.parse` e ogni comando che contiene passa da `effect_reason`;
   - un'opzione sconosciuta prima del programma: si provano tutte e due le letture (opzione senza valore, o con il valore dopo) e vince quella che dà un effetto (fail-closed);
   - il nome del pacchetto: tolto il suffisso `@<versione>` (non la `@` iniziale di uno scope), se ne prende l'ultimo pezzo dopo `/` (`@scope/wrangler@3` → `wrangler`), poi `PACKAGE_PROGRAMS = {"firebase-tools": "firebase", "netlify-cli": "netlify"}`.
   Si aggiungono a `_DEFAULT_EFFECTS` i comandi di Wrangler che pubblicano o cambiano subito ciò che è in linea (Fatti verificati): `("wrangler", "secret", "put")`, `("wrangler", "secret", "delete")`, `("wrangler", "secret", "bulk")`, `("wrangler", "rollback")`, `("wrangler", "delete")`, `("wrangler", "triggers", "deploy")`, `("wrangler", "versions", "deploy")`, `("wrangler", "pages", "deploy")`. Non entrano `versions upload` e `versions secret put` (creano una versione non pubblicata) né i comandi di sola lettura. `bash.is_claude` tiene il suo elenco: riconosce un programma solo, e unirlo cambierebbe un controllo già provato (costo: due elenchi da tenere allineati a mano). Le scritture di `wrangler kv`, `d1`, `r2` con `--remote` restano un rinvio a B5 (codice dei Worker), scritto nel piano principale con il costo: un subagente le può lanciare senza veto. Costo: i comandi di servizio coperti qui, lanciati con un lanciatore, ora chiedono un'approvazione dell'utente come lo stesso comando senza lanciatore; quelli non elencati restano senza veto come oggi.
18. **Le cartelle di GitHub non accendono profili** (mia scelta, che estende il progetto 11: l'utente ha deciso che `.github/workflows/` non accende `infra`; `.github/actions/` e l'esclusione per tutti i profili sono di questo piano, e la revisione 31 lo scrive così). `init.EXCLUDED_PREFIXES` aggiunge `.github/workflows/` e `.github/actions/`: un `Dockerfile` di un'azione container di GitHub non accende `infra`, e niente in quelle cartelle accende un altro profilo. Costo: un'azione di GitHub che ha codice AI non accende `ai` (oggi non succede in nessun test né nei progetti di prova).

## Review Focus

1. **Un nome di file che accende file sbagliati.** Un `Dockerfile` sotto `.github/tollgate/`, `.github/actions/` o nella cartella della proposta, un `vercel.json` in `docs/superpowers/tollgate-init/files/`, un `infra/README.md` da solo, un `src/infra/db.py`, una cartella `docker/Dockerfiles/` con codice dentro: nessuno accende `infra`. Test: Task 2 `test_name_pattern_skips_excluded_prefixes`, `test_doc_files_do_not_light_folders`, `test_root_folder_pattern_only_root`, `test_name_pattern_matches_files_not_folders`.
2. **Il verticale sbagliato vince.** Con `[profiles.web] paths = ["web/**"]` già dichiarato, `web/vercel.json` e `web/Dockerfile` vanno a `infra` (percorsi esatti con due segmenti letterali) e la proposta lo dice. Test: Task 2 `test_concrete_name_path_wins_over_declared_folder`.
3. **`tollgate.toml` dell'utente con `infra` già dichiarato.** Un `vercel.json` nuovo in un'altra cartella dà una riga «aggiungi» con il percorso esatto, una negazione dell'utente resta rispettata, una seconda `--update` non duplica. Test: Task 2 `test_declared_profile_new_name_file_reported`, `test_declared_profile_negation_respected_for_names`; i test di B3 `test_update_twice_no_duplicate` restano verdi.
4. **Regole che nessuno può soddisfare o giudicare.** Ogni `[blocca]` di `rules-infra` si giudica sul diff o sul report; un `major` su una `R-INFRA` non `[blocca]` non ferma; in un lavoro senza passo una `[blocca]` si soddisfa con diff e report; un `.env.example` committato non viola le regole sui segreti. Test: Task 4 `test_blocking_rules_judged_on_diff_or_report`, `test_blocca_lines_have_text`, `test_secret_rules_allow_example_files`; Task 7 `test_infra_profile_non_blocking_rule_approves`, `test_infra_blocking_rule_without_step`.
5. **Un deploy vero, un segreto cambiato o un'evidenza con dati dell'utente.** `npx wrangler deploy`, `npx vercel --prod`, `wrangler secret put` sono effetti da approvare; nella prova il modello non può lanciare `vercel`, `wrangler`, `docker` né `npx`; le evidenze passano da `togli-pagine` e dal controllo dei valori sensibili. Test: Task 3 `test_launcher_wrapped_effects`, `test_launcher_supabase_and_package_names`, `test_wrangler_live_commands_are_effects`; Task 8 `test_flow_disallows_deploy_clis`, `test_flow_case_infra_project_has_no_credentials`; `test_committed_evidence_has_no_long_web_results` (B3-bis) resta verde dopo il Task 9.

## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_core/fragments.py`; `tests/test_fragments.py` | 1 | forme dei pattern, `load_approved`, `rules` che non tace |
| `bin/tollgate_flow/init.py`, `docs/uso/comandi.md` (sezione di `/tollgate:init`); `tests/test_init.py` | 2 | percorsi concreti per le tre forme, documenti e cartelle di GitHub esclusi, test sulla radice vera |
| `bin/tollgate_analysis/bash.py`; `tests/test_bash.py` | 3 | effetti esterni dietro i lanciatori dei pacchetti |
| `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml`, `docs/uso/comandi.md` (`/tollgate:rules-infra`); `tests/test_rules_infra.py`, `tests/test_rules_ai.py` (helper con l'area), `tests/test_fragments.py` | 4, 5, 6 | regole e frammento di `infra` |
| `docs/profili/verifiche/infra-fonti.md`, `docs/profili/infra.md` | 5, 6 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-infra.md`, `agents/reviewer-infra.md`, `hooks/run`, `bin/tollgate_core/config.py`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `docs/uso/comandi.md` (`/tollgate:execute`); `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_profiles.py`, `tests/test_check_task_verdict.py` | 7 | agenti per area; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `spikes/b4/flow/`; `tests/test_b1_scripts.py` | 8 | prova reale: script e progetto |
| `docs/verifiche/2026-11-06-b4-prova-flusso.md`, `docs/verifiche/evidenze/b4/flusso/` | 9 | esecuzione, rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 10 | revisione 31 e stato |

---

### Task 1: Forme dei pattern dei frammenti

**Files:**
- Modify: `bin/tollgate_core/fragments.py`
- Test: `tests/test_fragments.py`

**Interfaces:**
- Consumes: `fragments.load`, `Fragment`, `FragmentError`, `approved`, `rules` (B3); `research.area_rules`.
- Produces:
  - `fragments.Pattern` (dataclass frozen: `kind: str` in `"folder"`, `"root_folder"`, `"name"`; `name: str`);
  - `fragments.parse_pattern(pattern: str) -> Pattern | None` (decisione 2);
  - `Fragment.patterns: tuple[Pattern, ...]`, nello stesso ordine di `profile["paths"]`;
  - `fragments.load_approved(plugin_root) -> list[Fragment]` (i frammenti di `load` la cui skill è approvata, nello stesso ordine);
  - `fragments.rules(fragment) -> tuple[list[str], list[str]]`, che con la skill illeggibile solleva `FragmentError` con il nome del file della skill.

- [ ] **Step 1: I test che falliscono** (radice temporanea):
  - `test_parse_pattern_forms`: `**/ai/**` → `Pattern("folder", "ai")`; `infra/**` → `Pattern("root_folder", "infra")`; `**/vercel.json` → `Pattern("name", "vercel.json")`; `**/Dockerfile*` → `Pattern("name", "Dockerfile*")`; `**/.dockerignore` → `Pattern("name", ".dockerignore")`; `**/ai` → `Pattern("name", "ai")` (un file di nome `ai`, non la cartella).
  - `test_parse_pattern_rejects`: per ognuno `None`: `**/*`, `**/**`, `**`, `**/*.sql`, `**/*.json`, `**/*.Dockerfile`, `**/a*b`, `**/Dockerfile**`, `**/x`, `**/a/b`, `src/x/**`, `/infra/**`, `vercel.json`, `**/.`, `**/..`, `**/./**`, `**/a?b`, `**/a[b]`, `**/a\\b`, `!**/x/**`, `**/*.{tsx,jsx}`, `**/`, `**/ x`, `**/è.json`, `**/a*/**`.
  - `test_load_accepts_three_forms` (un frammento con un pattern per forma si carica e `patterns` ha le tre forme in ordine).
  - **`test_load_rejects_other_pattern_forms` si aggiorna**: dalla tupla di oggi `("**/*.sql", "src/ai/**", "**/ai", "**/a/b/**", "**/**", "!**/ai/**", "**/a*/**", "")` esce `"**/ai"`, che con la decisione 2 è una forma `name` valida; le altre restano errori (il motivo nel report).
  - **`test_rules_from_skill` si aggiorna**: con la skill assente si aspetta `FragmentError` (decisione 10), poi le regole dopo aver scritto la skill (il motivo nel report).
  - `test_load_approved_filters_unapproved` (due frammenti, uno con la skill approvata: torna solo quello); `test_rules_unreadable_skill_raises` (skill assente → `FragmentError` con `rules-<area>/SKILL.md` nel messaggio).
  - L'helper `tomlout_str` del file si toglie e i test che lo usano passano da `tomlout.table`.
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_fragments`: FAIL dei test nuovi.
- [ ] **Step 3: Il codice.** `parse_pattern` per la decisione 2 (una regex per forma, `fullmatch`); `_parse` la usa per ogni voce di `paths` e riempie `patterns`; `load_approved` = `[f for f in load(root) if approved(f)]`; `rules` legge la skill con lo stesso `_skill_text` e, se è `None`, solleva.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_fragments tests.test_init tests.test_rules_ai`: PASS (il frammento di `ai` si carica come prima). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: tre forme di pattern nei frammenti, load_approved, rules che non tace».

---

### Task 2: Percorsi concreti per le tre forme; documenti e cartelle di GitHub esclusi

**Files:**
- Modify: `bin/tollgate_flow/init.py` (`EXCLUDED_PREFIXES`, `_FOLDER_PATTERN`, `_names`, `_folder_prefix`, `_concrete_paths`, `_drift`, `profile_blocks`, `propose`), `docs/uso/comandi.md` (sezione di `/tollgate:init`: le tre forme, i documenti, le cartelle di GitHub)
- Test: `tests/test_init.py`

**Interfaces:**
- Consumes: `fragments.Pattern`, `Fragment.patterns`, `fragments.load_approved` (Task 1); `globs.match`, `globs.match_any`, `globs.escape`; `profiles.vertical_for`.
- Produces:
  - `init.EXCLUDED_PREFIXES` con `.github/workflows/` e `.github/actions/` in più (decisione 18);
  - `init.DOC_EXTENSIONS: tuple[str, ...]` (decisione 4);
  - `init.concrete_for(path: str, patterns: Sequence[fragments.Pattern]) -> str | None` (decisione 3; `None` se nessuna forma accende il file o se è sotto `EXCLUDED_PREFIXES`);
  - `init._concrete_paths(patterns, files) -> list[str]` (ordinati, con le rimozioni della decisione 3);
  - `profile_blocks` e `propose` con la stessa firma di B3, che leggono i frammenti con `fragments.load_approved`.

- [ ] **Step 1: I test che falliscono.** In `ProfileBlocksTest` (il plugin temporaneo di `PluginMixin.plugin(fragment=…)` con il frammento `x`; un helper del test scrive il testo del frammento con i `paths` voluti):
  - `test_name_pattern_exact_paths` (`**/Dockerfile*`; `Dockerfile`, `services/api/Dockerfile`, `services/api/Dockerfile.prod` → `paths = ["/Dockerfile", "services/api/Dockerfile", "services/api/Dockerfile.prod"]`, ognuno corrisponde al suo file con `globs.match`);
  - `test_name_pattern_literal_is_exact_path` (`**/vercel.json`; `vercel.json`, `apps/web/vercel.json` → `["/vercel.json", "apps/web/vercel.json"]`);
  - `test_name_pattern_dir_escaped` (`app/[id]/vercel.json` → `app/\[id\]/vercel.json`, che corrisponde al file);
  - `test_name_pattern_matches_files_not_folders` (`**/Dockerfile*`: `docker/Dockerfiles/base.py` e `docker/Dockerfiles/README.md` non accendono; `Dockerfiles/base/Dockerfile` dà il solo `Dockerfiles/base/Dockerfile`);
  - `test_root_folder_pattern_only_root` (`infra/**`; `infra/deploy.sh` e `src/infra/db.py` → solo `/infra/**`; con il solo `src/infra/db.py` il profilo non è proposto);
  - `test_name_covered_by_folder_not_repeated` (`infra/**` e `**/Dockerfile*`; `infra/Dockerfile` → solo `/infra/**`);
  - `test_leftmost_folder_wins` (`infra/**` e `**/x/**`; `infra/a/x/b.py` → `/infra/**`; `**/x/**` da solo con `src/x/lib/x/a.py` → `src/x/**`, come B3);
  - `test_name_pattern_skips_excluded_prefixes` (`.github/tollgate/Dockerfile`, `.github/actions/build/Dockerfile`, `.github/workflows/vercel.json`, `docs/superpowers/tollgate-init/files/vercel.json`, `.claude/x/vercel.json`: nessuna proposta);
  - `test_doc_files_do_not_light_folders` (`**/x/**`: con `docs/x/guida.md` e `.github/x/a.agent.md` nessuna proposta; con in più `src/x/a.py` solo `src/x/**`; `**/Dockerfile*` non accende `docs/Dockerfile-note.md`; il pattern letterale `**/README.md` accende `README.md`);
  - `test_concrete_name_path_wins_over_declared_folder` (testo con `[profiles.web] paths = ["web/**"]`; `web/vercel.json` e `web/Dockerfile` → le righe di sovrapposizione dicono che vince `x`);
  - `test_declared_profile_new_name_file_reported` (`[profiles.x] paths = ["/vercel.json"]` già nel testo, file nuovo `apps/web/vercel.json` → riga `aggiungi "apps/web/vercel.json" (1 file)`);
  - `test_declared_profile_negation_respected_for_names` (con `"!apps/legacy/vercel.json"` nei `paths` dichiarati, quel file non compare nelle righe).
  - `test_real_trees_light_no_profile` si estende con l'albero «file spinti dalla CLI» della decisione 16 (gli import da `tests.flowkit` e `tests.hookkit`).
  - **`test_install_dir_does_not_light_profile` si aggiorna**: confronta la tupla esatta di `EXCLUDED_PREFIXES`, che ora ha anche `.github/workflows/` e `.github/actions/` (decisione 18; il motivo nel report).
  - `test_doc_extension_case_insensitive` (`docs/x/README.MD` non accende `**/x/**`).
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_init`.
- [ ] **Step 3: Il codice.** `concrete_for` per le decisioni 3, 4 e 18; `profile_blocks` calcola `lighting` come i file con `concrete_for` non `None` e i percorsi con `_concrete_paths`; `_drift` usa le stesse funzioni (i file nuovi fuori dai `paths` dichiarati, con le negazioni come in B3); `propose` e `profile_blocks` leggono i frammenti con `load_approved` (decisione 10). Un frammento che `fragments.rules` rifiuta è un rifiuto di `init` come ogni `FragmentError`. In `docs/uso/comandi.md` tre frasi: le forme dei pattern dei profili, i documenti che non accendono un profilo per cartella, le cartelle di GitHub escluse.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_init tests.test_fragments tests.test_rules_ai tests.test_docs`: PASS; i test di B3 (`ProfileBlocksTest`, `ProfilesProposeTest`, `DetectTest`) restano verdi senza modifiche, salvo `test_install_dir_does_not_light_profile` (Step 1). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: percorsi concreti per cartelle alla radice e nomi di file; documenti e cartelle di GitHub non accendono un profilo».

---

### Task 3: Effetti esterni dietro i lanciatori dei pacchetti

**Files:**
- Modify: `bin/tollgate_analysis/bash.py` (`_DEFAULT_EFFECTS`, `effect_reason`)
- Test: `tests/test_bash.py` (`EffectsTest`)

**Interfaces:**
- Consumes: `bash.parse`, `bash.Cmd`, `bash.EffectsCfg`, `bash.effect_reason` (nucleo, spec 8.5).
- Produces: `bash.unwrap_launcher(argv: list[str]) -> list[str]` (l'`argv` del comando lanciato, o `argv` stesso se non c'è un lanciatore; decisione 17); `effect_reason` che la usa prima del confronto con `_DEFAULT_EFFECTS`, con `[external_effects] commands` e `allow` invariati (confrontati sul testo normalizzato di tutto il comando, come oggi).

- [ ] **Step 1: I test** (testo dato a `bash.parse`, nessun programma lanciato). Falliscono su `main`:
  - `test_launcher_wrapped_effects`: non `None` per `npx wrangler deploy`, `npx --yes wrangler deploy`, `npx -y wrangler@3 deploy`, `npx --package=wrangler wrangler deploy`, `npx -p wrangler wrangler deploy`, `npx --registry https://r.invalid wrangler deploy`, `bunx wrangler deploy`, `pnpx vercel --prod`, `pnpm dlx vercel deploy`, `pnpm exec wrangler deploy`, `pnpm wrangler deploy`, `yarn wrangler deploy`, `npm exec -- wrangler deploy`, `npm x wrangler deploy`, `bun x wrangler deploy`, `yarn dlx vercel`, `yarn exec wrangler publish`, `npx vercel@latest build`, `npx @cloudflare/wrangler@3 deploy`, `npx -c "wrangler deploy"`;
  - `test_launcher_unknown_option_fails_closed`: non `None` per `npx --strano wrangler deploy` e `npx --strano x wrangler deploy`;
  - `test_launcher_supabase_and_package_names`: non `None` per `npx supabase db push` e `npx firebase-tools deploy`, `npx netlify-cli deploy`; `None` per `npx supabase status`;
  - `test_wrangler_live_commands_are_effects`: non `None` per `wrangler secret put KEY`, `wrangler secret delete KEY`, `wrangler secret bulk f.json`, `wrangler rollback`, `wrangler delete`, `wrangler triggers deploy`, `wrangler versions deploy`, `wrangler pages deploy dist`, `npx wrangler secret put KEY`;
  - `test_wrangler_read_and_upload_are_not_effects`: `None` per `wrangler versions upload`, `wrangler versions secret put KEY`, `wrangler versions list`, `wrangler versions view x`, `wrangler secret list`.
  Sono guardie contro le regressioni, già verdi su `main` (lo Step 2 lo dice): `test_launcher_without_effect_passes` (`None` per `npx prettier --write .`, `npx tsc`, `npm exec -- eslint .`, `pnpm dlx create-vite`, `pnpm install`, `yarn add x`; un `npx wrangler deploy --help` resta un effetto, come `wrangler deploy --help` oggi); `test_node_modules_bin_effect` (`./node_modules/.bin/wrangler deploy`); `test_allow_still_wins_with_launcher` (con `EffectsCfg(allow=["npx wrangler deploy --dry-run"])` il comando dà `None`); `test_npm_project_scripts_unchanged` (`npm run deploy` con `project_scripts=["deploy"]` resta «script del progetto»).
- [ ] **Step 2: Verifica.** `python3 -B -m unittest tests.test_bash`: FAIL dei cinque test del primo elenco, PASS delle guardie.
- [ ] **Step 3: Il codice.** `unwrap_launcher` e `PACKAGE_PROGRAMS` per la decisione 17; in `effect_reason` `u = unwrap_launcher(a)` per `_DEFAULT_EFFECTS` e per il ramo `supabase`, il resto sull'`argv` originale; le otto voci nuove in `_DEFAULT_EFFECTS`.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_bash tests.test_effects tests.test_check_effects`: PASS (`bin/tollgate_checks/effects.py` è l'unico chiamante di `effect_reason`). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: i comandi di deploy lanciati con npx e simili sono effetti esterni».

---

### Task 4: Bozza di `rules-infra` e frammento di `infra` con le fonti

**Files:**
- Create: `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml`, `tests/test_rules_infra.py`
- Modify: `tests/test_rules_ai.py` (l'helper `rules` riceve l'area), `docs/uso/comandi.md` (sezione `### \`/tollgate:rules-infra\``, come quella di `rules-ai`)
- Test: `tests/test_rules_infra.py`, `tests/test_rules_ai.py`, `tests/test_fragments.py`, `tests/test_docs.py`

**Interfaces:**
- Consumes: le copie delle fonti in `<workspace>/fonti/infra/` (Step 0); `research.area_rules`, `research.enforced`; `fragments.load`, `parse_pattern` (Task 1).
- Produces:
  - in `tests/test_rules_ai.py` `rules(text: str, area: str = "ai") -> list[tuple[str, bool, str, str, str]]` (`id`, `blocca`, testo, fonte, oggetto), con la regex costruita da `area.upper()`; i test di `ai` la chiamano senza area e non cambiano esito;
  - `skills/rules-infra/SKILL.md` nella forma di B2 (piano principale, sezione 3), senza `approved`; `templates/profiles/infra.toml` (decisioni 1, 5, 7, 8, 13); `tests/test_rules_infra.py` con `RulesInfraTest` e, dal Task 5, `RulesInfraPageTest`.

- [ ] **Step 0 (controller): le fonti.** Copia in `<workspace>/fonti/infra/` le pagine della tabella «Fatti verificati», quelle trovate per i punti (a)-(c) di «Da verificare prima del codice», e il `SKILL.md` della skill `wrangler` dal repository di Cloudflare, con `SHA256SUMS` e `FONTI.md` (URL, data, licenza dichiarata o «non dichiarata»). Solo pagine ufficiali (eccezione 1 delle istruzioni d'esecuzione). Nel brief dell'implementatore va il percorso di `fonti/infra/`.
- [ ] **Step 1: I test che falliscono.** In `tests/test_rules_infra.py`, sul modello di `RulesAiTest`, con `rules(text, "infra")`:
  - `test_frontmatter` (`name: rules-infra`, `description: Regole di tollgate per la configurazione e il deploy (Vercel, Cloudflare, Docker): le caricano in automatico gli agenti dell'area infra, non serve invocarla.`, `version: 1`, nessun `approved`, `research.enforced(text)` falso; il Task 6 lo inverte);
  - `test_has_title` (`# Regole infra (versione 1)`), `test_first_section_is_prima_di_scrivere`, `test_rule_ids_consecutive` (`R-INFRA-01`, …), `test_area_rules_of_research_match_rules`, `test_every_rule_has_a_source`, `test_every_rule_names_what_is_judged`, `test_every_rule_names_a_page_or_the_user_choice`, `test_some_rules_block`, `test_at_most_150_lines`, `test_no_long_quotations`;
  - `test_blocking_rules_judged_on_diff_or_report`; `test_blocca_lines_have_text` (decisione 10);
  - `test_secret_rules_allow_example_files` (la regola sui file dei segreti locali nomina le eccezioni `.example`, `.sample`, `.template`);
  - `test_user_choices_covered` (per id, da una tabella del test: R-INFRA-01 ha `Fonte: progetto di B, sezione 3.4` e `sezione 11`);
  - `test_sources_section` (la sezione `## Fonti` nomina Vercel, Cloudflare, Docker e la skill `wrangler` con la sua licenza, e dice che le regole riportano i fatti con parole nostre);
  - `test_where_to_look_names_skills` (`wrangler` e `cloudflare` in «Dove informarsi»; `workers-best-practices` no, decisione 8);
  - `test_fragment_matches_decisions` (`templates/profiles/infra.toml`: `kind = "vertical"`, `min_level = "L1"`, i tredici pattern della decisione 1 in quell'ordine, `skills = []`, `reviewer_skills = []`, `commands = {}`, `dod = []`, `agent = "tollgate:implementer-infra"`, `reviewer = "tollgate:reviewer-infra"`, nessuna tabella `[detect]`);
  - `test_fragment_leaves_out_ci_and_workers` (nessun pattern contiene `.github`, `workflows` o `workers`);
  - `test_fragment_loads_through_the_loader`; in `tests/test_fragments.py` `test_real_fragments_load` legge `ai` e `infra`.
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Scrivi le regole** dalle fonti, con parole tue: una riga di regola, «Si giudica su» e `Fonte:` ciascuna; sezioni «Prima di scrivere», «Mentre lavori», «Dove informarsi» (gli URL ufficiali per Vercel, Cloudflare e Docker; le skill `wrangler` e `cloudflare`; la versione installata di `wrangler` e `vercel`, dal file delle dipendenze del progetto), «Fonti». Bozza da distillare (l'implementatore può dividere o unire, mai aggiungere obblighi senza fonte):

  | Id | Sezione | `[blocca]` | Cosa dice la regola | Si giudica su | Fonte |
  |---|---|---|---|---|---|
  | R-INFRA-01 | Prima di scrivere | sì | Se il diff tocca la configurazione o i comandi di deploy, il report nomina i file di deploy già presenti nel progetto che ha letto (configurazione di Vercel, di Wrangler, Dockerfile e compose, workflow di deploy in `.github/workflows/`) e dice dove gira oggi il progetto | report | progetto 1 («è su Vercel, leggi le cose prima»), 3.4 riga `infra`, 11 |
  | R-INFRA-02 | Prima di scrivere | sì | Un comando o un'opzione di `vercel`, `wrangler`, `docker` o `docker compose` che il diff scrive (script, `package.json`, documentazione) o che il report dà come fatto ha nel report l'indirizzo della pagina ufficiale del comando | report | progetto 3.4 riga `infra`; skill `wrangler` (Apache-2.0); pagine dei comandi |
  | R-INFRA-03 | Prima di scrivere | sì | Una proprietà di configurazione che il diff scrive in `vercel.*` o `wrangler.*` ha nel report l'indirizzo della pagina ufficiale che la descrive | report | progetto 3.4; pagine della configurazione di Vercel e Wrangler |
  | R-INFRA-04 | Mentre lavori | sì | Un progetto Vercel ha un solo file di configurazione: il diff non aggiunge `vercel.json`, `vercel.toml` o `vercel.ts` in una cartella che nel repo ne ha già uno degli altri due (il revisore guarda la cartella) | diff | pagina della configurazione di Vercel |
  | R-INFRA-05 | Mentre lavori | sì | Nessun segreto nei file versionati: non in `vars` di Wrangler, non nella configurazione di Vercel, non in `ENV` o `ARG` di un Dockerfile né in un file compose; i segreti passano dalle impostazioni dei servizi (variabili `Secret` di Vercel, segreti dei Worker, `--secret` di Docker), che l'utente imposta | diff | pagine dei segreti di Cloudflare, delle variabili di Vercel, dei segreti di build di Docker; buone pratiche dei Dockerfile (sezione `ENV`) |
  | R-INFRA-06 | Mentre lavori | sì | I file dei segreti locali (`.dev.vars*`, `.env`, `.env.*`, salvo quelli che finiscono in `.example`, `.sample` o `.template`) non entrano nel diff; se il diff aggiunge codice, script o documentazione che li usa, `.gitignore` li esclude (nel diff o già nel repo) | diff | pagina dei segreti di Cloudflare; pagina delle variabili di Vercel |
  | R-INFRA-07 | Mentre lavori | no | Una configurazione nuova di Wrangler usa `wrangler.jsonc` e una `compatibility_date` recente; il report dice di aver letto i flag di compatibilità quando il diff cambia la data | diff | pagine della configurazione e delle date di compatibilità di Cloudflare |
  | R-INFRA-08 | Mentre lavori | no | L'immagine di base di un Dockerfile ha una versione fissata (un tag preciso o un digest), non `latest` né il solo nome | diff | buone pratiche dei Dockerfile («Pin base image versions») |
  | R-INFRA-09 | Mentre lavori | no | Un Dockerfile nuovo per un servizio che non ha bisogno di privilegi passa a un utente non root con `USER`, e ha accanto un `.dockerignore` | diff | buone pratiche dei Dockerfile (`USER`, `.dockerignore`) |
  | R-INFRA-10 | Mentre lavori | no | Un Dockerfile che compila separa la build dall'immagine finale con una build a stadi | diff | buone pratiche dei Dockerfile («Use multi-stage builds») |
  | R-INFRA-11 | Mentre lavori | sì | Il task non pubblica e non cambia un servizio. Il report dice quale prova senza pubblicazione ha eseguito (per esempio `npx wrangler deploy --dry-run`, oppure `vercel build` in un progetto collegato), dopo l'approvazione dell'utente che tollgate chiede per quei comandi, oppure perché non l'ha fatta; non riporta comandi che pubblicano o cambiano un servizio (deploy, `--prod`, `secret`, `env add`), lanciati da lui | report | spec del nucleo 8.5 (effetti esterni); pagine di `wrangler deploy` e di `vercel build` |

  Il frammento `templates/profiles/infra.toml` per le decisioni 1, 5, 7, 8 e 13, con un commento per gruppo di pattern che nomina la pagina da cui viene il nome del file.
- [ ] **Step 4: Comando.** In `docs/uso/comandi.md` la sezione di `/tollgate:rules-infra` (`test_every_skill_documented`).
- [ ] **Step 5: Verifica.** `python3 -B -m unittest tests.test_rules_infra tests.test_rules_ai tests.test_fragments tests.test_docs tests.test_init`: PASS (`test_real_trees_light_no_profile` copre ora anche `infra`). `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 6: Commit** «tollgate B4: bozza di rules-infra e frammento del profilo infra con le fonti».

---

### Task 5: Verifica delle fonti e pagina per l'utente

**Files:**
- Create: `docs/profili/verifiche/infra-fonti.md`, `docs/profili/infra.md`
- Modify: `skills/rules-infra/SKILL.md` e `templates/profiles/infra.toml` (solo se una fonte non passa), `tests/test_rules_infra.py`

**Interfaces:**
- Consumes: `tests.test_rules_ai.rules(text, "infra")`; `<workspace>/fonti/infra/`.
- Produces: la pagina che il Task 6 mostra all'utente; il rapporto delle fonti, con due tabelle: «Regole e fonti» (`| Regola | Fonte (pagina, sezione) | Citazione | Esito |`, come `ai-fonti.md`) e «Pattern dei percorsi» (`| Pattern | Fonte (pagina, sezione) | Citazione | Esito |`).

- [ ] **Step 1 (controller): la verifica delle fonti.** Un subagente `Explore` (sonnet, sola lettura) verifica **ogni fonte di ogni regola** e **ogni pattern di `paths`** sulle copie di `fonti/infra/`, sul progetto di B e sulla spec 8.5: il file esiste; la sezione esiste; dice ciò che la regola le attribuisce, o per un pattern che lo strumento legge un file con quel nome (citazione di al più una riga); è una pagina ufficiale (con la licenza di `FONTI.md`), la skill `wrangler` (Apache-2.0), il progetto di B o la spec. Esito `ok` o `no` con il motivo. Il controller salva l'uscita in `<workspace>/task-5-fonti.md`.
- [ ] **Step 2: I test che falliscono** (da `RulesAiPageTest`): `test_sources_report_covers_every_rule`, `test_removed_sources_are_not_in_the_skill`, `test_tables_have_one_header`, `test_path_patterns_verified` (ogni pattern del frammento ha una riga `ok` nella tabella «Pattern dei percorsi»), `test_page_lists_every_rule`, `test_page_number_matches_id`, `test_page_blocca_matches_skill`, `test_page_judged_on_matches_skill`, `test_page_explains_what_changes` (la pagina dice: il profilo si accende solo dove `init` lo propone e l'utente lo copia, da L1; quali nomi di file e quale cartella lo accendono; che i workflow di GitHub e il codice dei Worker non sono `infra`, progetto 11; come aggiungere a mano un comando di prova del deploy in `dod` e approvarlo, decisione 7; che i comandi dei servizi, anche con `npx`, chiedono l'approvazione dell'utente, decisione 17), `test_page_is_a_proposal`, `test_page_brings_the_open_choices_to_the_user`, `test_page_has_removed_section_without_rule_ids`, `test_page_has_no_private_data`.
- [ ] **Step 3: Le correzioni e i due file.** Escono le fonti `no` e le regole o i pattern che restano senza fonte `ok`; le regole rimaste si rinumerano senza buchi. Rapporto e pagina come in B3 (tabella «N.», «In parole semplici», «Blocca?», «Si giudica su», «Da dove viene»; «Regole tolte dalla verifica»; i punti dubbi in «Da decidere tu»; come rispondere), in parole semplici, con le parole tecniche spiegate la prima volta (memoria: spiegazioni semplici).
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_rules_infra`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: fonti di rules-infra verificate e pagina per l'utente».

---

### Task 6: Approvazione dell'utente

**Files:**
- Modify: `skills/rules-infra/SKILL.md`, `docs/profili/infra.md`, `docs/profili/verifiche/infra-fonti.md` (solo con correzioni), `tests/test_rules_infra.py`, `tests/test_fragments.py`

**Interfaces:**
- Consumes: la pagina del Task 5; `fragments.approved`.
- Produces: `approved: <AAAA-MM-GG>` in `skills/rules-infra/SKILL.md`; da qui `init` propone `infra`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Come in B3, Task 7: la pagina nel terminale, in breve; approva, correggi o togli; ogni correzione è un giro di questo task, e una regola nuova o con una fonte nuova ripassa dal verificatore. **Fermata prevista** (decisione 15).
- [ ] **Step 2: I test che falliscono.** `test_frontmatter` si inverte; `test_page_approval_date_matches_skill`; `test_approved_skill_leaves_no_pending_decisions`; in `tests/test_fragments.py` `test_real_infra_fragment_approved`.
- [ ] **Step 3: L'approvazione.** `approved: <data>` dopo `version`; nella pagina «Approvata dall'utente il <data>.». `claude plugin validate --strict .`: uscita 0. `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde.
- [ ] **Step 4: Commit** «tollgate B4: rules-infra approvata dall'utente».

---

### Task 7: Agenti `implementer-infra` e `reviewer-infra`

**Files:**
- Create: `agents/implementer-infra.md`, `agents/reviewer-infra.md`
- Modify: `hooks/run` (`READONLY_TYPES`), `bin/tollgate_core/config.py` (`DEFAULTS["review"]["readonly_agents"]`), `agents/final-reviewer.md` e `agents/finding-verifier.md` (l'esempio «per esempio le `R-AI-…`» nomina anche le `R-INFRA-…`), `docs/uso/comandi.md` (`/tollgate:execute`: l'area `infra`)
- Test: `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_profiles.py`, `tests/test_check_task_verdict.py`

**Interfaces:**
- Consumes: `agents/implementer.md`, `agents/task-reviewer.md`, `agents/*-ai.md` come modello; `skills/rules-infra/SKILL.md` approvata (Task 6); `tests.test_rules_ai.rules(text, area)`.
- Produces: i tipi `tollgate:implementer-infra` e `tollgate:reviewer-infra`; in `tests/test_manifest.py` la tupla `AREAS = ("ai", "infra")`.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_code_agents_preload_rules_base` include i due agenti nuovi, con `skills` uguale a `[rules-base, rules-infra]`; `test_area_agents_derive_from_generic` e `test_area_agents_attribution` girano su `AREAS`; **`test_area_agents_name_rules_ai` diventa `test_area_agents_name_area_rules`**, su `AREAS`, con la regola della decisione 9 (il motivo del cambio nel report); `test_final_reviewers_leave_report_rules_of_areas` nomina anche `R-INFRA-`.
  - `tests/test_taskcmd.py` (un `tollgate.toml` con il blocco `infra` scritto nel test con le regole di una skill finta): `test_infra_task_routed_to_area_agents` (un task che modifica `vercel.json` ha `agent_type` `tollgate:implementer-infra` e `reviewer_type` `tollgate:reviewer-infra`); `test_rules_infra_not_required` (`skills_required` vuoto); `test_infra_and_ai_task_goes_generic` (un task su `vercel.json` e `ai/x.py`: `agent_type` `tollgate:implementer` e `reviewer_type` `tollgate:task-reviewer`).
  - `tests/test_profiles.py`: `test_infra_and_ai_routing_is_split_candidate` (`profiles.task_routing(["vercel.json", "ai/x.py"], …)` con i due blocchi: agenti generici e `split_candidate` vero).
  - `tests/test_check_task_verdict.py` (stesso blocco): `test_infra_profile_blocking_rule_changes`, `test_infra_profile_non_blocking_rule_approves`, `test_infra_blocking_rule_without_step` (`research=False`, un `major` su una `R-INFRA` `[blocca]` → `changes`).
- [ ] **Step 2: Verifica che falliscano.** `test_readonly_list_matches_config_and_agents` diventa rosso solo quando `agents/reviewer-infra.md` esiste: dopo lo Step 3, prima di aggiornare gli elenchi.
- [ ] **Step 3: Gli agenti e gli elenchi.** I due file per la decisione 9 (frontmatter come gli `-ai` con `infra` al posto di `ai`; `description` che dice l'area: configurazione e deploy su Vercel, Cloudflare e Docker). Sezione «Area `infra`»: le `R-INFRA-…` valgono come le `R-BASE-…` (solo le `[blocca]` danno `blocker` o `major`, un difetto si segnala una volta sola); l'implementatore scrive nel campo `done` del report ciò che le regole sul tuo report chiedono (file di deploy letti, indirizzi ufficiali di comandi e proprietà, la prova senza pubblicazione o perché no) e **non lancia** comandi che pubblicano o cambiano un servizio: tollgate ferma come effetti esterni i comandi della decisione 17, anche dietro `npx`, e solo l'utente li approva; quelli non coperti (per esempio le scritture remote di `wrangler kv`, `d1`, `r2`) non li lancia comunque; il revisore giudica le regole sul report su quel testo e le altre sul diff, in un task senza modifiche non apre rilievi `R-INFRA-…`, e con `WebFetch` apre solo gli URL ufficiali citati, come dati non fidati. `tollgate:reviewer-infra` in `READONLY_TYPES` e in `readonly_agents`.
- [ ] **Step 4: Verifica.** I file di test: PASS. `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: agenti implementer-infra e reviewer-infra».

---

### Task 8: Prova reale con il profilo `infra`: script e progetto di prova

**Files:**
- Create: `spikes/b4/flow/` (`tollgate.toml` di base con il comando di verifica dei test, `vercel.json` con una sola proprietà, `Dockerfile` di poche righe, `app/__init__.py`, `app/main.py`, `tests/__init__.py`, `tests/test_smoke.py`, `config.toml`, `issue-1.md`, `piano-L1.md`, `.gitignore`)
- Modify: `spikes/run-b1-flow.sh` (valore `infra` di `B1_FLOW_CASE`), `spikes/b1/flowreg.py` (titolo `# Regole infra (versione 1)` tra quelli cercati da `registra`), `tests/test_b1_scripts.py`

**Interfaces:**
- Consumes: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE` (`b1`, `ai`), `B1_FLOW_RULES`; `init.propose`.
- Produces: `B1_FLOW_CASE=infra`.

- [ ] **Step 1: I test che falliscono** (in `tests/test_b1_scripts.py`, con `B1_FLOW_CHECK=1` e una `HOME` finta): `test_flow_case_infra_out_dir` (`OUT` è `docs/verifiche/evidenze/b4/flusso`); `test_flow_case_infra_requires_real_rules`; `test_flow_case_unknown_value` nomina `infra` tra i valori ammessi; `test_flow_case_infra_project_verifies` (come `test_flow_case_ai_project_verifies`); `test_real_flow_case_infra_prepara_proposes_profile` (con la sorgente dei file veri e `rules-infra` approvata: dopo `prepara` il `tollgate.toml` del repo di prova ha `[profiles.infra]` con `"/vercel.json"` e `"/Dockerfile"` nei `paths`); `test_flow_case_infra_prepara_refuses_without_profile`; `test_flow_disallows_deploy_clis` (con `B1_FLOW_CASE=infra` la riga `--disallowedTools` stampata da `controlla` contiene, per ognuno di `vercel`, `wrangler`, `docker`, `npx`, `bunx`, `pnpx`, `bun`, `npm`, `pnpm`, `yarn`, le quattro forme `Bash(<p>:*)`, `Bash(*/<p>:*)`, `Bash(command <p>:*)` e `Bash(env <p>:*)`, come lo script fa già per `gh`); `test_flow_case_infra_project_has_no_credentials` (nel progetto nessuna cartella `.vercel/`, nessun `.env*`, nessun `.dev.vars*`, nessun file di Wrangler); `test_flow_case_infra_task_forbids_publishing` (`issue-1.md` e `piano-L1.md` dicono che il progetto non è collegato a nessun servizio, che la prova senza pubblicazione non si fa e che il report dice perché); `test_registra_reads_infra_title`; `test_registra_flags_deploy_clis` (uno stream finto con un `Bash` `npx vercel --prod`: `comandi-rischiosi.txt` lo riporta). I test di B1, B2 e B3 restano verdi.
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Lo script e il progetto.** `B1_FLOW_CASE=infra` come `ai`: oggi i rami legati ad `ai` sono `PROJ`, `PROJ_FILES`, `PLAN_SRC`, `OUT`, il caso nel Python di `scrivi_dati_gh` (titolo dell'issue e risposta sulla protezione), `proponi_profilo` (fisso su `profiles.ai` e `services/notify.py`), il controllo di `HOME`, `trascrizioni` e i tipi raccolti da `registra`, i testi di `controlla`: ognuno prende il valore del caso, e `proponi_profilo` riceve area e file da controllare (`infra`, `vercel.json`). Con `infra` `DISALLOWED` ha in più le voci del test e la grep dei comandi rischiosi di `registra` li cerca. Il lavoro L1 del piano: aggiungere in `vercel.json` un'intestazione `X-Content-Type-Options: nosniff` per tutte le risposte, con un test in `tests/` che legge il file e la controlla. Lo script si prova solo con `bash -n`, `controlla` e i test.
- [ ] **Step 4: Verifica.** `bash -n spikes/run-b1-flow.sh`; `python3 -B -m unittest tests.test_b1_scripts`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: prova reale con il profilo infra, script e progetto di prova».

---

### Task 9: Prova reale: esecuzione e rapporto (controller)

**Files:**
- Create: `docs/verifiche/2026-11-06-b4-prova-flusso.md`, `docs/verifiche/evidenze/b4/flusso/`

- [ ] **Step 1 (controller): esecuzione.** `B1_FLOW_CASE=infra B1_FLOW_RULES=vere`: `prepara`, `passo1`, `passo2`, `registra`, solo sotto `/tmp/tollgate-b1/`. Atteso: task 1 `done` con verdetto `approved`; `agent_type` `tollgate:implementer-infra`, `reviewer_type` `tollgate:reviewer-infra`; il titolo di `rules-infra` nelle trascrizioni di entrambi; nota valida prima della prima modifica; il report con l'indirizzo ufficiale della proprietà `headers` di `vercel.json` e la riga sulla prova senza pubblicazione non fatta, con il motivo; `comandi-rischiosi.txt` senza `vercel`, `wrangler`, `docker`, `npx`. Un esito in più tentativi è «composito»; al più 3 tentativi per passo. Un difetto del prodotto scoperto qui è un giro del task che possiede il codice (test che fallisce, correzione, `tests/run`), poi si ripete solo il passo interessato.
- [ ] **Step 2: Evidenze e rapporto.** `flowreg togli-pagine` sulle evidenze; controllo di nome utente, host, `/home/<utente>`, id di sessione e forme di token. Rapporto: passi, tentativi, proposta di `init` (percorsi esatti e file che accendono il profilo), agenti lanciati, precaricamento visto, letture, nota, verdetto e rilievi `R-INFRA-…`, consumo stimato, limiti (R-INFRA-11 vista solo nel ramo «perché no»).
- [ ] **Step 3: Verifica e commit.** `python3 -B -m unittest tests.test_b1_scripts` (compreso `test_committed_evidence_has_no_long_web_results`): PASS. Commit «tollgate B4: prova reale corta con il profilo infra».

---

### Task 10: Prove, revisione 31 della spec, piano principale, catalogo

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 31), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento), `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`

- [ ] **Step 1: Revisione 31 della spec del nucleo.** 6.3 (agenti `-infra`, precaricamento, task misti); 7.1 e 7.3 (`reviewer-infra` di sola lettura con `WebFetch`); 8.5 (lanciatori dei pacchetti, `wrangler secret` e `wrangler versions`; scritture remote di `wrangler kv/d1/r2` rinviate); 11.2 (tre forme, percorsi concreti per forma, documenti e cartelle di GitHub esclusi, `load_approved`; la differenza per `ai` della decisione 4); 11.4 (frammento con le tre forme e quello di `infra`, senza `[detect]`, `dod` vuoto e perché); 16 (i fatti verificati del 6 novembre e l'esito della prova reale); riga 31 della sezione 20.
- [ ] **Step 2: Catalogo.** Sezione 2: riga `infra` con i pattern veri e la frase «fino a B4 un frammento ammette solo…» sostituita dalle tre forme; la nota sulle graffe dice come `infra` le ha sciolte. 2.1: riga `infra` (`rules-infra` precaricata, `wrangler` e `cloudflare` in «Dove informarsi», `workers-best-practices` a `backend`). 2.3: riga `infra` del `dod` (vuoto, decisione 7). 4: le fonti vere di `rules-infra`.
- [ ] **Step 3: Piano principale di B e progetto.** Stato in testa; riga B4 della sezione 2; sezione 3, riga B3→B4-B7 aggiornata con le tre forme e una riga B4→B5-B7 (`parse_pattern`, `concrete_for`, `DOC_EXTENSIONS`, `EXCLUDED_PREFIXES`, `load_approved`, `unwrap_launcher`, `AREAS`, `rules(text, area)`); sezione 9: chiusi i rinvii che B4 chiude (forma dei pattern, documenti nelle cartelle, piccole cose di B3 della decisione 10, test sulla radice vera, id a mano negli agenti), aperti gli altri con il motivo, il rinvio a B5 delle scritture remote di Wrangler (decisione 17), la nota sulla pagina approvata di `ai` (decisione 4), più le righe «minor (deferred)» per B5-B8; una sezione «Prove di B4» con ogni riga della tabella «Copertura» e il test o l'evidenza che la prova. Nel progetto la riga di avanzamento con B4.
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md
git commit -m "tollgate B4: prove, spec rev 31, piano principale di B, catalogo"
```

---

## Copertura: punti del progetto e del piano principale destinati a B4 → task

| Punto | Task |
|---|---|
| Progetto 1: «è su Vercel, leggi le cose prima» | 4 (R-INFRA-01) |
| Progetto 2, obiettivo 3: `infra` nel primo gruppo | 4, 5, 6, 7 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `infra` | 4 (sezione «Dove informarsi»), 5 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 7 |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 5, 6; decisione 15 |
| Progetto 2, anti-obiettivo «fonti inventate» | 5 (verificatore di sola lettura, anche sui pattern); decisione 12 |
| Progetto 3.4, riga `infra`: aprire la configurazione presente, documentazione della versione installata | 4 (R-INFRA-01, 02, 03, «Dove informarsi») |
| Progetto 4, riga `infra`: L1, Vercel | 4 (frammento); decisioni 1, 13 |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 4, 5, 6 |
| Progetto 11: workflow al gate; Worker in `backend`; Docker sì | decisioni 1, 5, 6, 18; 2 (`test_name_pattern_skips_excluded_prefixes`); 4 (`test_fragment_leaves_out_ci_and_workers`); 5 (`test_page_explains_what_changes`) |
| Piano principale, sezione 2, riga B4: `rules-infra` con Vercel, agenti, percorsi (anche `vercel.json`), `dod` | 1, 2, 4, 7; decisione 7 |
| Piano principale, sezione 3, B3→B4-B7: frammenti, `init`, agenti derivati, elenchi di sola lettura | 1, 2, 7 |
| Piano principale, sezione 9, «A B4-B7, da B3»: prefisso `R-INFRA-` | 4 (`test_rule_ids_consecutive`, `test_area_rules_of_research_match_rules`) |
| Sezione 9: forma dei pattern (`_PATTERN`, `_FOLDER_PATTERN`, percorsi concreti) | 1, 2; decisioni 2, 3 |
| Sezione 9: rilevamento per contenuto solo nei sorgenti | decisione 5 |
| Sezione 9: cartelle `agents/` e `prompts/` e file che non sono codice | 2; decisione 4 |
| Sezione 9: agenti nuovi (tupla, `rules-base`, elenchi, id a mano) | 7; decisione 9 |
| Sezione 9: test esistenti sulla radice vera | 2; decisione 16 |
| Sezione 9: test da copiare | 4, 5 |
| Sezione 9: piccole cose rimaste aperte nel codice di B3 | 1; decisione 10 |
| Sezione 9, «A B4-B8, da B3-bis»: cartelle temporanee, test che toccano `start` | Global Constraints |
| Sezione 9, «A B3-B7»: `rules-base` negli agenti nuovi; regole giudicate sul visibile | 7; 4 (`test_blocking_rules_judged_on_diff_or_report`) |
| Spec 8.5: un deploy è un effetto esterno da approvare, anche con `npx` | 3; decisione 17 |
| Brief di scrittura: B4 da sola o unita | decisione 11 |
| Revisione della spec del nucleo | 10 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B (con le sezioni 9-11), il brief di scrittura, il piano principale, la spec rev 30, il catalogo, il codice di `main` e il modello di B3.

| Giro | Rilievi | Esito |
|---|---|---|
| 1 | 1 critical (C-1 nella prova reale niente impediva al modello di usare `vercel` o `wrangler` con le credenziali salvate dell'utente); 7 important (I-1 un pattern di nome accendeva anche le cartelle con quel nome, perché `globs` copre ciò che sta sotto; I-2 i percorsi con `*` non vincevano per specificità; I-3 la forma `name` accettava `**/*.sql` e il test da aggiornare era descritto male; I-4 l'helper `rules` riconosceva solo `R-AI`; I-5 `npx wrangler deploy` e `wrangler secret put` non erano effetti esterni, `vercel build` sì; I-6 R-INFRA-06 bloccava `.env.example` e aveva una parte non giudicabile; I-7 `split_candidate` non esce da `taskcmd`); 14 minor | «Non pronto». Corretti tutti: decisioni 2, 3, 4 riscritte (nome confrontato sul solo nome del file, percorsi esatti, `*` solo finale, ordine delle forme, documenti); decisioni 7, 14, 15, 16 precisate; decisioni 17 (lanciatori dei pacchetti, nuovo Task 3) e 18 (cartelle di GitHub escluse) nuove; R-INFRA-04, 05, 06, 11 riscritte; `rules(text, area)`; test d'area definito; test nuovi o spostati nei Task 1, 2, 4, 5, 7, 8; rami dello script elencati; cautele dichiarate complete |
| 2 | C-1 e I-1…I-7 del giro 1 chiusi (I-2 con il residuo dei segmenti escapati, ora scritto nel costo della decisione 3); 3 important nuovi (I-A due test di B3 rotti dalle decisioni 10 e 18 e non nominati; I-B `wrangler pages deploy`, `rollback`, `delete`, `triggers deploy` senza veto; I-C il lanciatore tolto solo per `_DEFAULT_EFFECTS`: `npx supabase db push` e `npx firebase-tools deploy` senza veto); 11 minor | «Non pronto». Corretti tutti: fatti di Wrangler verificati sulla pagina ufficiale (cosa pubblica subito e cosa crea solo una versione); decisione 17 riscritta (`unwrap_launcher` per `_DEFAULT_EFFECTS` e `supabase`, opzioni con valore, `-c`, opzione sconosciuta fail-closed, scope e versione, `PACKAGE_PROGRAMS`, otto voci di Wrangler, elenco di `is_claude` lasciato a parte con il costo); Task 3 con test nuovi e guardie dichiarate; Task 1 e 2 nominano i test di B3 da aggiornare; decisioni 3, 4, 18, R-INFRA-05, R-INFRA-11, Global Constraints, divieti della prova in quattro forme |
