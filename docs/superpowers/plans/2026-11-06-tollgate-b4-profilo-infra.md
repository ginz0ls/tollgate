# tollgate B4: profilo `infra`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il secondo profilo verticale, `infra` (configurazione e deploy su Vercel, Cloudflare e Docker), con le regole `rules-infra` scritte dalle pagine ufficiali, verificate e approvate dall'utente, gli agenti `implementer-infra` e `reviewer-infra`, e ciò che manca all'infrastruttura dei profili perché un frammento possa nominare file e cartelle alla radice e non solo cartelle a qualunque profondità.

**Architecture:** Il frammento `templates/profiles/infra.toml` usa tre forme di pattern: `**/<cartella>/**` (già di B3), `<cartella>/**` (una cartella alla radice) e `**/<nome>` (un nome di file, anche con `*`, a qualunque profondità). Le forme si riconoscono in un solo punto, `fragments.parse_pattern`, che `fragments.load` usa per rifiutare le altre e `init` per calcolare i percorsi concreti: per una cartella il prefisso fino alla cartella, per un nome di file la sua cartella seguita dal nome del pattern. I file di documentazione non accendono più un profilo per cartella. `infra` non ha marcatori di contenuto: i suoi file si riconoscono dal nome. A runtime il nucleo non cambia: il profilo vive nel `tollgate.toml` del progetto. Gli agenti per area sono copie dichiarate dei generici, come `-ai`.

**Tech Stack:** Python ≥ 3.11, solo libreria standard; bash; git; Claude Code (`claude plugin validate --strict`; la prova reale con `claude -p --plugin-dir` solo dal controller). Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** il progetto approvato `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (l'autorità: «utente» non si discute, «mia scelta» si corregge solo con un motivo scritto qui), soprattutto le sezioni 1 («è su Vercel, leggi le cose prima»), 2, 3.4 (righe `infra` e `backend`), 4 (riga `infra`: L1, va aggiunto Vercel), 5 e **11 (scelte dell'utente del 6 novembre 2026: workflow al gate, codice dei Worker in `backend`, Docker sì)**; la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 30 (la 31 la scrive il Task 9): 6.3, 7.1, 7.3, 9.2, 11.2, 11.4, 16, 18.4; il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, sezioni 1 (principi 6 e 7), 2 (riga `infra` e nota sulle graffe), 2.1, 2.2, 2.3 e 4. Piano principale di B: `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, riga B4 della sezione 2, righe B1→B3-B7, B2→B3-B7 e B3→B4-B7 della sezione 3, rinvii «A B3-B7» e «A B4-B7, da B3» della sezione 9.

## Fatti verificati (6 novembre 2026, pagine ufficiali aperte con WebFetch)

| Fatto | Pagina | Conseguenza qui |
|---|---|---|
| Wrangler legge `wrangler.toml`, `wrangler.json` e `wrangler.jsonc` (JSON da Wrangler 3.91.0); Cloudflare consiglia `wrangler.jsonc` per i progetti nuovi; la pagina non dice dove deve stare il file, ma i file locali dei segreti stanno «nella stessa cartella» | https://developers.cloudflare.com/workers/wrangler/configuration/ | tre nomi di file nel frammento, a qualunque profondità; una regola non bloccante sul formato dei progetti nuovi |
| Cloudflare consiglia Wrangler installato nel progetto, lanciato con `npx wrangler …` | https://developers.cloudflare.com/workers/wrangler/commands/ | «Dove informarsi»: la versione installata |
| `wrangler deploy --dry-run` compila senza pubblicare (`--outdir` per vedere il risultato); la pagina non dice se servono credenziali; `wrangler types --check` confronta solo i tipi generati con la configurazione | https://developers.cloudflare.com/workers/wrangler/commands/workers/ | `dod` vuoto (decisione 7); il report dice la prova senza pubblicazione |
| I segreti di un Worker non vanno in `vars` della configurazione; si mettono con `wrangler secret put`; in locale stanno in `.dev.vars` o `.env` accanto alla configurazione, file che non si committano | https://developers.cloudflare.com/workers/configuration/secrets/ | regole sui segreti |
| `compatibility_date` non è obbligatoria (le date vecchie restano valide per sempre); si consiglia la data del giorno a inizio progetto e aggiornamenti occasionali dopo aver letto i flag | https://developers.cloudflare.com/workers/configuration/compatibility-dates/ | regola non bloccante |
| Vercel legge `vercel.json`, `vercel.toml` o `vercel.ts`, **uno solo per progetto**; il supporto di `now.json` finisce il 31 marzo 2026 | https://vercel.com/docs/project-configuration | tre nomi di file nel frammento; regola «un solo file» |
| `vercel link` crea `.vercel/` con `project.json` (`orgId`, `projectId`) | https://vercel.com/docs/cli/project-linking | `.vercel/` non è un pattern: di solito non è tracciata |
| `vercel build` costruisce in locale in `.vercel/output`; prima si consiglia `vercel pull` (impostazioni e variabili del progetto collegato) | https://vercel.com/docs/cli/build | `dod` vuoto (decisione 7) |
| Le variabili di Vercel sono `Config` o `Secret` (queste ultime solo in scrittura); in locale stanno in `.env.local` o nel `.env` di `vercel env pull` | https://vercel.com/docs/environment-variables | regole sui segreti |
| Compose legge `compose.yaml` (preferito), `compose.yml`, e per compatibilità `docker-compose.yaml` e `docker-compose.yml` | https://docs.docker.com/compose/intro/compose-application-model/ | quattro nomi di file |
| Buone pratiche dei Dockerfile: build a stadi, `.dockerignore`, versione dell'immagine di base fissata, utente non root quando non servono privilegi; un valore messo con `ENV` resta nello strato anche dopo averlo tolto | https://docs.docker.com/build/building/best-practices/ | regole non bloccanti su Dockerfile; segreti |
| I segreti di una build passano con `docker build --secret` e `RUN --mount=type=secret`, non con argomenti di build né variabili d'ambiente, che restano nell'immagine | https://docs.docker.com/build/building/secrets/ | regola sui segreti |
| Licenze: il repository delle skill di Cloudflare (`cloudflare`, `wrangler`, `workers-best-practices` e altre) è Apache-2.0; il repository della documentazione di Docker è Apache-2.0; le pagine di Vercel e Cloudflare non dichiarano una licenza nella pagina | https://github.com/cloudflare/skills, https://github.com/docker/docs | si prendono i fatti con parole nostre, come per `rules-ai` (catalogo 1.7) |
| Nei progetti dell'utente sul disco (contati per nome di file, senza aprirli né nominarli): `Dockerfile*` in 6 cartelle, `docker-compose.y*ml` in 4, `vercel.json` in 10, `vercel.ts` in 1, file di Wrangler in 3, `*.tf` in 1 | `find` locale del 6 novembre | progetto 11: Docker sì, Terraform no |

**Da verificare prima del codice** (controller, Task 3, Step 0): (a) la pagina di Docker che dà il nome predefinito `Dockerfile` e le forme con suffisso o prefisso (`Dockerfile.<x>`, `<x>.Dockerfile`), per decidere se `**/Dockerfile*` basta o serve anche `**/*.Dockerfile`; (b) la pagina di Docker sul file `.dockerignore` (nome e posizione, anche `<Dockerfile>.dockerignore`); (c) le pagine di `vercel.json` e `vercel.ts` per le proprietà citate dalle regole. Se un fatto della tabella sopra risulta smentito al punto da cambiare una decisione, il controller si ferma e chiede.

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`); verifica finale come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`.
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`.
- **Nessuna operazione nuova in `apply._OPS`** (29) e **nessun tipo nuovo in `events.EVENT_TYPES`** (33).
- **Nessuna rete**, né nei test né per i subagenti: le fonti delle regole sono copie locali messe dal controller nel workspace (Task 3, Step 0), che **non entrano mai in git** né nella copia del registro in `docs/sdd/`. Nessun `claude` vero nei test; `gh` è `tests/fakegh.py`. **Nessun `vercel`, `wrangler`, `docker`, `npx` o `npm` vero** nei test, negli script e nei comandi dei subagenti. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`, `~/.claude/projects/`.
- **Test con la radice del plugin esplicita**: ogni test nuovo che legge frammenti, skill o agenti usa una radice temporanea, salvo i `test_real_…` e i file `tests/test_rules_*.py`, che sono sui file veri della loro area.
- **Cartelle temporanee dei test** (piano principale, sezione 9, «A B4-B8, da B3-bis»): ogni `mkdtemp` si chiude con `addCleanup`; una cartella creata direttamente in `/tmp` ha un prefisso che comincia con `tollgate`. Nessuna asserzione che, se fallisce, stampi `os.environ` (lezione di B3-bis).
- **Regole con parole nostre** (catalogo 1, principio 7): dalle pagine dei fornitori si prendono i **fatti**, senza copiarne testo; una citazione sta al più in una riga, nel solo rapporto delle fonti. Ogni regola si giudica con un sì o un no **su ciò che il revisore vede** (diff, report o nota); una regola `[blocca]` si giudica sul diff o sul report, mai sulla sola nota.
- **Numeri delle regole stabili dopo l'approvazione** (catalogo 2.3). **`approved` in `skills/rules-infra/SKILL.md` si scrive solo nel Task 5**, con la data dell'OK dell'utente; gli agenti `-infra` caricano `rules-infra` solo dopo (Task 6 dopo il Task 5).
- Non si toccano `skills/rules-base/SKILL.md`, `skills/rules-ai/SKILL.md`, `docs/profili/base.md`, `docs/profili/ai.md` e i loro rapporti delle fonti: sono approvati dall'utente.
- Testo non fidato (nota, pagine scaricate, citazioni, report dell'implementatore): nei brief dentro `brief.fence` con `brief.DATA_NOTE`, mai come istruzione.
- `tollgate.toml` del progetto: `init` non lo scrive mai nel repo, produce la proposta in `docs/superpowers/tollgate-init/` che l'utente copia (spec 11.2).
- Il repo è pubblico: nei file nuovi niente nomi di progetti privati dell'utente, niente nome utente né host, nessun token; nelle evidenze nessun testo intero di pagine o skill di terzi (`flowreg togli-pagine`).
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

## Decisioni di questo piano

Scelte che il progetto e il piano principale lasciano a B4, o che il codice reale impone, con il costo se sbagliate. Il Task 9 le riporta nella revisione 31 della spec.

1. **Cosa copre `infra`** (progetto 4 e 11). La configurazione e il deploy su Vercel (`vercel.json`, `vercel.toml`, `vercel.ts`), su Cloudflare (`wrangler.toml`, `wrangler.json`, `wrangler.jsonc`) e con Docker (`Dockerfile*`, `.dockerignore`, i quattro nomi dei file compose), più la cartella `infra/` alla radice (catalogo 2). Escono dal catalogo `workers/**` (il codice dei Worker è `backend`, progetto 11), `**/*.tf` (Terraform: un solo file nei progetti dell'utente, nessuna fonte in questo piano) e `.github/workflows/**` (progetto 11). Gli altri server (nginx, systemd) non entrano. Pattern del frammento, in quest'ordine: `["infra/**", "**/vercel.json", "**/vercel.toml", "**/vercel.ts", "**/wrangler.toml", "**/wrangler.json", "**/wrangler.jsonc", "**/Dockerfile*", "**/.dockerignore", "**/compose.yaml", "**/compose.yml", "**/docker-compose.yaml", "**/docker-compose.yml"]`; il verificatore delle fonti (Task 4) controlla ogni nome su una pagina ufficiale e un pattern senza fonte `ok` esce, come un marcatore di B3. Costo: un cambio a Terraform o alla configurazione di un server proprio va all'agente generico finché un progetto non li chiede.
2. **Tre forme di pattern nei frammenti** (rinvio «Forma dei pattern» di B3). `fragments.parse_pattern(p) -> Pattern | None`, l'unico punto che le riconosce:
   - `**/<cartella>/**` → `Pattern("folder", <cartella>)`, come in B3;
   - `<cartella>/**` → `Pattern("root_folder", <cartella>)`, la sola cartella alla radice (serve anche a `backend` per `api/**` e `server/**`);
   - `**/<nome>` → `Pattern("name", <nome>)`, un nome di file in un solo segmento, a qualunque profondità.
   `<cartella>` è un segmento senza `*`, `?`, `[`, `]`, `!`, `\` e diverso da `.` e `..` (la regex di B3). `<nome>` è un segmento di lettere ASCII, cifre, `.`, `_`, `-` e `*`, con almeno una lettera o cifra, senza `**`, diverso da `.` e `..`. Ogni altra forma è una `FragmentError` (graffe comprese: `globs` non le espande, catalogo 2). `fragments.load` usa `parse_pattern` al posto di `_PATTERN`; `init` lo usa al posto di `_FOLDER_PATTERN` (che sparisce). Costo: nessuno; una forma nuova (per esempio `**/*.sql` di `database`) si aggiunge in quel solo punto.
3. **Percorsi concreti per le forme nuove** (decisione 5 di B3, estesa). Per ogni file tracciato fuori da `init.EXCLUDED_PREFIXES`, il primo pattern del frammento che gli corrisponde dà il suo percorso concreto:
   - `folder`: come in B3, `<percorso fino alla prima cartella con quel nome, compresa>/**` passato da `globs.escape`;
   - `root_folder`: `/<cartella>/**` se il primo segmento del file è la cartella;
   - `name`: `<cartella del file, passata da globs.escape>/<nome>` (il nome del pattern, con il suo `*`, senza escape), oppure `/<nome>` per un file alla radice. Con un nome senza `*` è il percorso esatto del file; con `Dockerfile*` copre anche i Dockerfile nuovi nella stessa cartella.
   Un percorso concreto si toglie se ogni file che accende è già coperto da un altro percorso proposto (un `infra/Dockerfile` con `/infra/**` dà solo `/infra/**`; con `src/x/**`, `src/x/lib/x/**` non serve, come in B3). Così i percorsi concreti hanno segmenti letterali e vincono, per specificità (spec 6.3), su un `web/**` già dichiarato per `web/vercel.json`. Costo: un `vercel.json` in una cartella nuova non è coperto finché l'utente non applica la riga di `init --update` (decisione 7 di B3).
4. **I file di documentazione non accendono un profilo per cartella** (rinvio «Cartelle `agents/` e `prompts/` e file che non sono codice» di B3). Nelle forme `folder` e `root_folder` un file con estensione in `init.DOC_EXTENSIONS = ("md", "mdx", "markdown", "rst", "txt", "adoc")` non accende il profilo e non dà percorsi concreti; vale per tutte le aree (`docs/ai/guida.md` o `.github/agents/x.agent.md` non propongono più `ai`). La forma `name` è esplicita e non ha l'esclusione. Una volta proposto `src/ai/**`, un markdown lì dentro va comunque all'agente dell'area (`vertical_for` guarda i percorsi): l'esclusione decide solo la proposta. Costo: una cartella che contiene solo documenti non riceve più la proposta.
5. **Nessun rilevamento per contenuto per `infra`** (brief, «Da decidere»). I file di `infra` si riconoscono dal nome; i file non sorgente (`.toml`, `.json`, `.yaml`, `Dockerfile`) non hanno righe di import da cercare. Il frammento non ha `[detect]`; `init.SOURCE_EXTENSIONS` resta com'è. Il codice che usa le librerie di runtime (`cloudflare:workers`, `@vercel/functions`) è `backend` (progetto 11) e lo rileverà B5, se serve. Costo: nessuno per `infra`.
6. **CI del progetto** (progetto 11, utente). `.github/workflows/**` non è nei percorsi di `infra`: un workflow del progetto resta del gate (`guard` lo rifiuta se potrebbe pubblicare stati falsi, la deroga `ci` di test-guard per ogni modifica, spec 9.2 e 8.3) e, dopo B, del profilo `ci`. `rules-infra` chiede di leggere i workflow di deploy prima di parlare di deploy (R-INFRA-01). Costo: un task che cambia solo un workflow di deploy va all'agente generico.
7. **`dod` e comandi di `infra` vuoti** (catalogo 2.3: «`wrangler deploy --dry-run` o equivalente», proposta da confermare). Il comando dipende dal progetto: per Vercel la prova in locale vuole un progetto collegato e `vercel pull` (Fatti verificati); per Cloudflare `wrangler deploy --dry-run` compila senza pubblicare, ma vuole Wrangler installato e la pagina non dice se servono credenziali. Un `dod` scritto da `init` fallirebbe in silenzio nei progetti che non lo reggono. Quindi il frammento ha `commands = {}` e `dod = []`; la pagina per l'utente (Task 4) dice come aggiungere a mano un comando del profilo (per esempio `deploy-check = "npx wrangler deploy --dry-run"`) e metterlo in `dod`; R-INFRA-11 chiede al report quale prova senza pubblicazione è stata fatta o perché no. Costo: nessun controllo automatico del deploy finché l'utente non lo aggiunge.
8. **`rules-infra` precaricata, non nel brief** (decisione 9 di B3, modello per B4-B7). `implementer-infra` e `reviewer-infra` hanno `skills: [rules-base, rules-infra]`; il frammento ha `skills = []` e `reviewer_skills = []`. Le skill del catalogo 2.1 restano fuori dal frammento: «Dove informarsi» di `rules-infra` nomina `wrangler` e `cloudflare` (Cloudflare, Apache-2.0); `workers-best-practices` riguarda il codice dei Worker, che è `backend` (progetto 11), e non si nomina qui. Costo: come in B3, circa 2.000-3.000 token in più per lancio; nei task misti le regole dell'area non arrivano all'agente.
9. **Agenti per area derivati dai generici** (decisioni 10 e 11 di B3). `agents/implementer-infra.md` e `agents/reviewer-infra.md`: il testo di `implementer.md` e `task-reviewer.md`, lo stesso frontmatter tranne `name`, `description`, `skills` e, per il revisore, `tools` (`Read, Grep, Glob, Bash, WebFetch`), la riga di attribuzione MIT e una sezione «Area `infra`». `tollgate:reviewer-infra` entra in `READONLY_TYPES` di `hooks/run` e in `config.DEFAULTS["review"]["readonly_agents"]`. Gli id `R-INFRA-…` nominati nella sezione d'area **non** si confrontano più a mano: il test d'area diventa uno per tutte le aree (`AREAS = ("ai", "infra")`), che ricava dalla skill le regole «Si giudica su: report» e quelle sul diff e controlla che la sezione d'area del revisore le nomini tutte e sole (rinvio T8-1 di B3). Costo: due file in più, tenuti allineati dal test di deriva.
10. **Piccole cose rimaste aperte nel codice di B3** (piano principale, sezione 9). Si chiudono: `fragments.load_approved(plugin_root)`, l'unico punto con `load` e il filtro `approved`, usato da `init.propose` e da `init.profile_blocks`; `fragments.rules(fragment)` con la skill che non si legge è una `FragmentError` con il nome del file, non più `([], [])`; ogni `tests/test_rules_<area>.py` nuovo ha `test_blocca_lines_have_text` (una riga `R-<AREA>-NN [blocca]` senza testo dopo sarebbe una regola nota ma non bloccante); `tests/test_fragments.py` usa `tomlout` al posto dell'helper `tomlout_str`. Restano aperte, con il motivo: `tomlout.table` che divide `name` sui punti (i nomi d'area sono `[a-z0-9-]+`) e «profili non valutati» per un repo senza file (messaggio esplicito, ramo testato). Costo: nessuno.
11. **B4 non si unisce a un'altra fetta** (piano principale, sezione 2). Porta le forme nuove dei pattern, che servono a B5-B7, più un profilo con la sua pagina da approvare: non è piccola. Costo: un giro di piano in più per B5.
12. **Fonti di `rules-infra`** (catalogo 4: «skill Cloudflare (Apache-2.0)», più Vercel per il progetto 4). Le pagine ufficiali della tabella «Fatti verificati» più quelle dello Step 0 del Task 3; la skill `wrangler` del repository di Cloudflare (Apache-2.0) per l'idea «documentazione della versione installata»; le scelte dell'utente con `Fonte: progetto di B, sezione 3.4` o `sezione 11`. Le copie locali le fa il controller (Task 3, Step 0) con `SHA256SUMS` e `FONTI.md`. Costo: le pagine cambiano; il rapporto delle fonti ha la data.
13. **Livello e tipo** (progetto 4): `kind = "vertical"`, `min_level = "L1"`, `agent = "tollgate:implementer-infra"`, `reviewer = "tollgate:reviewer-infra"`, nessuno specialista finale.
14. **Prova reale corta** (Task 7 e 8), come in B3: un progetto di prova `spikes/b4/flow/` con `vercel.json`, un `Dockerfile` e un po' di codice, un lavoro L1 che chiede di aggiungere un'intestazione di sicurezza in `vercel.json`. Si prova: `init` propone `infra` con i percorsi concreti di nome, `implementer-infra` e `reviewer-infra` lanciati, `rules-infra` precaricata, nota valida, nessun comando che pubblica. Costo: circa 1-1,5 USD stimati sull'abbonamento (B3: 1,32), nessuna spesa in denaro.
15. **Fermata per l'approvazione e unione anticipata.** La sessione d'esecuzione si ferma per l'utente nel Task 5, dopo la verifica delle fonti e la pagina. Se l'utente rinvia, su `main` si possono unire solo i Task 1 e 2 (forme dei pattern, percorsi concreti, documenti esclusi), che non portano regole né agenti. Costo: B4 resta aperta.
16. **Test di `init` sulla radice vera** (rinvio «Test esistenti che girano sulla radice vera» di B3). `test_real_trees_light_no_profile` si estende all'albero che spingono le classi di `tests/test_init.py` che lanciano la CLI (`DEFAULT_FILES`, `JUNIT_FILES`, `GATE_FILES` con `VERSION`, `package.json`, `.github/workflows/ci.yml`, l'albero installato e la proposta); così il frammento vero di `infra` non cambia in silenzio l'uscita di quei test. Costo: nessuno.

## Review Focus

1. **Un nome di file che accende file sbagliati.** Un `Dockerfile` sotto `.github/tollgate/` o nella cartella della proposta, un `vercel.json` in `docs/superpowers/tollgate-init/files/`, un `infra/README.md` da solo, un `src/infra/db.py`: nessuno accende `infra`. Test: Task 2 `test_name_pattern_skips_excluded_prefixes`, `test_doc_files_do_not_light_folders`, `test_root_folder_pattern_only_root`.
2. **Il verticale sbagliato vince.** Con `[profiles.web] paths = ["web/**"]` già dichiarato, `web/vercel.json` va a `infra` (percorso concreto con due segmenti letterali) e la proposta lo dice. Test: Task 2 `test_concrete_name_path_wins_over_declared_folder`.
3. **`tollgate.toml` dell'utente con `infra` già dichiarato.** Un `vercel.json` nuovo in un'altra cartella dà una riga «aggiungi» con il percorso concreto, una negazione dell'utente resta rispettata, una seconda `--update` non duplica. Test: Task 2 `test_declared_profile_new_name_file_reported`, `test_declared_profile_negation_respected_for_names`; i test di B3 `test_update_twice_no_duplicate` restano verdi.
4. **Regole che nessuno può soddisfare o giudicare.** Ogni `[blocca]` di `rules-infra` si giudica sul diff o sul report; un `major` su una `R-INFRA` non `[blocca]` non ferma; in un lavoro senza passo una `[blocca]` si soddisfa con diff e report. Test: Task 3 `test_blocking_rules_judged_on_diff_or_report`, `test_blocca_lines_have_text`; Task 6 `test_infra_profile_non_blocking_rule_approves`, `test_infra_blocking_rule_without_step`.
5. **Un deploy vero o un segreto in un'evidenza.** Nessun test, script o subagente lancia `vercel`, `wrangler`, `docker` o `npx`; il progetto di prova non è collegato a nessun servizio; le evidenze passano da `togli-pagine` e dal controllo dei valori sensibili. Test: Task 7 `test_flow_case_infra_project_has_no_credentials`, `test_flow_case_infra_task_forbids_publishing`; `test_committed_evidence_has_no_long_web_results` (B3-bis) resta verde dopo il Task 8.

## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_core/fragments.py`; `tests/test_fragments.py` | 1 | forme dei pattern, `load_approved`, `rules` che non tace |
| `bin/tollgate_flow/init.py`, `docs/uso/comandi.md` (sezione di `/tollgate:init`); `tests/test_init.py` | 2 | percorsi concreti per le tre forme, documenti esclusi, test sulla radice vera |
| `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml`, `docs/uso/comandi.md` (`/tollgate:rules-infra`); `tests/test_rules_infra.py`, `tests/test_fragments.py` | 3, 4, 5 | regole e frammento di `infra` |
| `docs/profili/verifiche/infra-fonti.md`, `docs/profili/infra.md` | 4, 5 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-infra.md`, `agents/reviewer-infra.md`, `hooks/run`, `bin/tollgate_core/config.py`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `docs/uso/comandi.md` (`/tollgate:execute`); `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_check_task_verdict.py` | 6 | agenti per area; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `spikes/b4/flow/`; `tests/test_b1_scripts.py` | 7 | prova reale: script e progetto |
| `docs/verifiche/2026-11-06-b4-prova-flusso.md`, `docs/verifiche/evidenze/b4/flusso/` | 8 | esecuzione, rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 9 | revisione 31 e stato |

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
  - `test_parse_pattern_forms`: `**/ai/**` → `Pattern("folder", "ai")`; `infra/**` → `Pattern("root_folder", "infra")`; `**/vercel.json` → `Pattern("name", "vercel.json")`; `**/Dockerfile*` → `Pattern("name", "Dockerfile*")`; `**/.dockerignore` → `Pattern("name", ".dockerignore")`; `**/*.Dockerfile` → `Pattern("name", "*.Dockerfile")`.
  - `test_parse_pattern_rejects`: per ognuno `None`: `**/*`, `**/**`, `**`, `**/a/b`, `src/x/**`, `/infra/**`, `vercel.json`, `**/.`, `**/..`, `**/./**`, `**/a?b`, `**/a[b]`, `**/a\\b`, `!**/x/**`, `**/*.{tsx,jsx}`, `**/a**b`, `**/`, `**/ x`, `**/è.json`.
  - `test_load_accepts_three_forms` (un frammento con un pattern per forma si carica e `patterns` ha le tre forme in ordine).
  - **`test_load_rejects_other_pattern_forms` si aggiorna**: la forma `**/vercel.json` non è più un errore; restano errori `src/x/**`, `**/*.{a,b}`, `**/a/b` e `!**/x/**` (il motivo nel report: la decisione 2 allarga le forme ammesse).
  - `test_load_approved_filters_unapproved` (due frammenti, uno con la skill approvata: torna solo quello); `test_rules_unreadable_skill_raises` (skill assente → `FragmentError` con `rules-<area>/SKILL.md` nel messaggio).
  - L'helper `tomlout_str` del file si toglie e i test che lo usano passano da `tomlout.table`.
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_fragments`: FAIL dei test nuovi.
- [ ] **Step 3: Il codice.** `parse_pattern` per la decisione 2 (una regex per forma, `fullmatch`); `_parse` la usa per ogni voce di `paths` e riempie `patterns`; `load_approved` = `[f for f in load(root) if approved(f)]`; `rules` legge la skill con lo stesso `_skill_text` e, se è `None`, solleva.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_fragments tests.test_init tests.test_rules_ai`: PASS (il frammento di `ai` si carica come prima). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: tre forme di pattern nei frammenti, load_approved, rules che non tace».

---

### Task 2: Percorsi concreti per le tre forme e documenti esclusi

**Files:**
- Modify: `bin/tollgate_flow/init.py` (`_FOLDER_PATTERN`, `_names`, `_folder_prefix`, `_concrete_paths`, `_drift`, `profile_blocks`, `propose`), `docs/uso/comandi.md` (sezione di `/tollgate:init`: le tre forme e i documenti)
- Test: `tests/test_init.py`

**Interfaces:**
- Consumes: `fragments.Pattern`, `Fragment.patterns`, `fragments.load_approved` (Task 1); `globs.match`, `globs.match_any`, `globs.escape`; `profiles.vertical_for`.
- Produces:
  - `init.DOC_EXTENSIONS: tuple[str, ...]` (decisione 4);
  - `init.concrete_for(path: str, patterns: Sequence[fragments.Pattern]) -> str | None` (il percorso concreto che il file accende, dal primo pattern che gli corrisponde, decisione 3; `None` se nessuno, se il file è sotto `EXCLUDED_PREFIXES` o se è un documento per le forme a cartella);
  - `init._concrete_paths(patterns, files) -> list[str]` (ordinati, senza i percorsi i cui file sono tutti coperti da un altro proposto);
  - `profile_blocks` e `propose` con la stessa firma di B3, che leggono i frammenti con `fragments.load_approved`.

- [ ] **Step 1: I test che falliscono.** In `ProfileBlocksTest` (il plugin temporaneo di `PluginMixin.plugin(fragment=…)` con il frammento `x`; un helper del test scrive il testo del frammento con i `paths` voluti):
  - `test_name_pattern_concrete_per_directory` (`**/Dockerfile*`; `Dockerfile`, `services/api/Dockerfile`, `services/api/Dockerfile.prod` → `paths = ["/Dockerfile*", "services/api/Dockerfile*"]`, e ognuno corrisponde ai suoi file con `globs.match`);
  - `test_name_pattern_literal_is_exact_path` (`**/vercel.json`; `vercel.json`, `apps/web/vercel.json` → `["/vercel.json", "apps/web/vercel.json"]`);
  - `test_name_pattern_dir_escaped` (`app/[id]/vercel.json` → `app/\[id\]/vercel.json`, che corrisponde al file);
  - `test_root_folder_pattern_only_root` (`infra/**`; `infra/deploy.sh` e `src/infra/db.py` → solo `/infra/**`; con il solo `src/infra/db.py` il profilo non è proposto);
  - `test_name_covered_by_folder_not_repeated` (`infra/**` e `**/Dockerfile*`; `infra/Dockerfile` → solo `/infra/**`);
  - `test_name_pattern_skips_excluded_prefixes` (`.github/tollgate/Dockerfile`, `docs/superpowers/tollgate-init/files/vercel.json`, `.claude/x/vercel.json`: nessuna proposta);
  - `test_doc_files_do_not_light_folders` (`**/x/**`: con `docs/x/guida.md` e `.github/x/a.agent.md` nessuna proposta; con in più `src/x/a.py` solo `src/x/**`; con `**/README.md` come pattern di nome, `README.md` accende: la forma `name` non ha l'esclusione);
  - `test_concrete_name_path_wins_over_declared_folder` (testo con `[profiles.web] paths = ["web/**"]`; `web/vercel.json` → la riga di sovrapposizione dice che vince `x`);
  - `test_declared_profile_new_name_file_reported` (`[profiles.x] paths = ["/vercel.json"]` già nel testo, file nuovo `apps/web/vercel.json` → riga `aggiungi "apps/web/vercel.json" (1 file)`);
  - `test_declared_profile_negation_respected_for_names` (con `"!apps/legacy/vercel.json"` nei `paths` dichiarati, quel file non compare nelle righe);
  - `test_first_matching_pattern_wins` (`**/x/**` prima di `**/a.py`: `src/x/a.py` dà `src/x/**`).
  - `test_real_trees_light_no_profile` si estende con l'albero «file spinti dalla CLI» della decisione 16.
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_init`.
- [ ] **Step 3: Il codice.** `concrete_for` per le decisioni 3 e 4; `profile_blocks` calcola `lighting` come i file con `concrete_for` non `None` e i percorsi con `_concrete_paths`; `_drift` usa le stesse funzioni (i file nuovi fuori dai `paths` dichiarati, con le negazioni come in B3); `propose` e `profile_blocks` leggono i frammenti con `load_approved` (decisione 10). Un frammento che `fragments.rules` rifiuta è un rifiuto di `init` come ogni `FragmentError`. In `docs/uso/comandi.md` due frasi: le forme dei pattern dei profili e il fatto che i documenti non accendono un profilo per cartella.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_init tests.test_fragments tests.test_rules_ai tests.test_docs`: PASS; i test di B3 (`ProfileBlocksTest`, `ProfilesProposeTest`, `DetectTest`) restano verdi senza modifiche. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: percorsi concreti per cartelle alla radice e nomi di file; i documenti non accendono un profilo».

---

### Task 3: Bozza di `rules-infra` e frammento di `infra` con le fonti

**Files:**
- Create: `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml`, `tests/test_rules_infra.py`
- Modify: `docs/uso/comandi.md` (sezione `### \`/tollgate:rules-infra\``, come quella di `rules-ai`)
- Test: `tests/test_rules_infra.py`, `tests/test_fragments.py`, `tests/test_docs.py`

**Interfaces:**
- Consumes: le copie delle fonti in `<workspace>/fonti/infra/` (Step 0); `research.area_rules`, `research.enforced`; `fragments.load`, `parse_pattern` (Task 1); `tests.test_rules_ai.rules(text)` e `frontmatter(text)`, riusati con il prefisso dell'area (se servono parametri nuovi, l'helper riceve l'area e i due file lo importano dallo stesso punto).
- Produces: `skills/rules-infra/SKILL.md` nella forma di B2 (piano principale, sezione 3), senza `approved`; `templates/profiles/infra.toml` (decisioni 1, 5, 7, 8, 13); `tests/test_rules_infra.py` con `RulesInfraTest` e, dal Task 4, `RulesInfraPageTest`.

- [ ] **Step 0 (controller): le fonti.** Copia in `<workspace>/fonti/infra/` le pagine della tabella «Fatti verificati», quelle trovate per i punti (a)-(c) di «Da verificare prima del codice», le pagine di `vercel.json` e `vercel.ts`, e il `SKILL.md` della skill `wrangler` dal repository di Cloudflare, con `SHA256SUMS` e `FONTI.md` (URL, data, licenza dichiarata o «non dichiarata»). Solo pagine ufficiali (eccezione 1 delle istruzioni d'esecuzione). Nel brief dell'implementatore va il percorso di `fonti/infra/`.
- [ ] **Step 1: I test che falliscono.** In `tests/test_rules_infra.py`, sul modello di `RulesAiTest`:
  - `test_frontmatter` (`name: rules-infra`, `description: Regole di tollgate per la configurazione e il deploy (Vercel, Cloudflare, Docker): le caricano in automatico gli agenti dell'area infra, non serve invocarla.`, `version: 1`, nessun `approved`, `research.enforced(text)` falso; il Task 5 lo inverte);
  - `test_has_title` (`# Regole infra (versione 1)`), `test_first_section_is_prima_di_scrivere`, `test_rule_ids_consecutive` (`R-INFRA-01`, …), `test_area_rules_of_research_match_rules`, `test_every_rule_has_a_source`, `test_every_rule_names_what_is_judged`, `test_some_rules_block`, `test_at_most_150_lines`, `test_no_long_quotations`;
  - `test_blocking_rules_judged_on_diff_or_report`; `test_blocca_lines_have_text` (decisione 10);
  - `test_user_choices_covered` (per id, da una tabella del test: R-INFRA-01 ha `Fonte: progetto di B, sezione 3.4`; la regola sui workflow ha `sezione 11`);
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
  | R-INFRA-04 | Mentre lavori | sì | Un progetto Vercel ha un solo file di configurazione: il diff non ne aggiunge un secondo tra `vercel.json`, `vercel.toml` e `vercel.ts` nella stessa cartella | diff | pagina della configurazione di Vercel |
  | R-INFRA-05 | Mentre lavori | sì | Nessun segreto nei file versionati: non in `vars` di Wrangler, non nella configurazione di Vercel, non in `ENV` o `ARG` di un Dockerfile né in un file compose; i segreti passano dai comandi e dalle impostazioni dei servizi (`wrangler secret put`, variabili `Secret` di Vercel, `--secret` di Docker) | diff | pagine dei segreti di Cloudflare, delle variabili di Vercel, dei segreti di build di Docker; buone pratiche dei Dockerfile (sezione `ENV`) |
  | R-INFRA-06 | Mentre lavori | sì | I file dei segreti locali (`.dev.vars*`, `.env*`) non entrano nel diff, e il diff che li introduce nel progetto li mette in `.gitignore` | diff | pagina dei segreti di Cloudflare; pagina delle variabili di Vercel |
  | R-INFRA-07 | Mentre lavori | no | Una configurazione nuova di Wrangler usa `wrangler.jsonc` e una `compatibility_date` recente; il report dice di aver letto i flag di compatibilità quando il diff cambia la data | diff | pagine della configurazione e delle date di compatibilità di Cloudflare |
  | R-INFRA-08 | Mentre lavori | no | L'immagine di base di un Dockerfile ha una versione fissata (un tag preciso o un digest), non `latest` né il solo nome | diff | buone pratiche dei Dockerfile («Pin base image versions») |
  | R-INFRA-09 | Mentre lavori | no | Un Dockerfile nuovo per un servizio che non ha bisogno di privilegi passa a un utente non root con `USER`, e ha accanto un `.dockerignore` | diff | buone pratiche dei Dockerfile (`USER`, `.dockerignore`) |
  | R-INFRA-10 | Mentre lavori | no | Un Dockerfile che compila separa la build dall'immagine finale con una build a stadi | diff | buone pratiche dei Dockerfile («Use multi-stage builds») |
  | R-INFRA-11 | Mentre lavori | sì | Il task non pubblica: il report dice quale prova senza pubblicazione ha eseguito (per esempio `npx wrangler deploy --dry-run`, oppure `vercel build` in un progetto collegato) o perché non si poteva, e non riporta comandi che pubblicano o cambiano un servizio (deploy, `--prod`, `secret put`) | report | spec del nucleo 8.5 (effetti esterni); pagine di `wrangler deploy` e di `vercel build` |

  Il frammento `templates/profiles/infra.toml` per le decisioni 1, 5, 7, 8 e 13, con un commento per gruppo di pattern che nomina la pagina da cui viene il nome del file.
- [ ] **Step 4: Comando.** In `docs/uso/comandi.md` la sezione di `/tollgate:rules-infra` (`test_every_skill_documented`).
- [ ] **Step 5: Verifica.** `python3 -B -m unittest tests.test_rules_infra tests.test_fragments tests.test_docs tests.test_init`: PASS (`test_real_trees_light_no_profile` copre ora anche `infra`). `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 6: Commit** «tollgate B4: bozza di rules-infra e frammento del profilo infra con le fonti».

---

### Task 4: Verifica delle fonti e pagina per l'utente

**Files:**
- Create: `docs/profili/verifiche/infra-fonti.md`, `docs/profili/infra.md`
- Modify: `skills/rules-infra/SKILL.md` e `templates/profiles/infra.toml` (solo se una fonte non passa), `tests/test_rules_infra.py`

**Interfaces:**
- Consumes: `tests.test_rules_ai.rules(text)`; `<workspace>/fonti/infra/`.
- Produces: la pagina che il Task 5 mostra all'utente; il rapporto delle fonti.

- [ ] **Step 1 (controller): la verifica delle fonti.** Un subagente `Explore` (sonnet, sola lettura) verifica **ogni fonte di ogni regola** e **ogni pattern di `paths`** sulle copie di `fonti/infra/`, sul progetto di B e sulla spec 8.5: il file esiste; la sezione esiste; dice ciò che la regola le attribuisce, o per un pattern che quel nome di file è letto dallo strumento (citazione di al più una riga); è una pagina ufficiale (con la licenza di `FONTI.md`), la skill `wrangler` (Apache-2.0), il progetto di B o la spec. Esito `ok` o `no` con il motivo. Il controller salva l'uscita in `<workspace>/task-4-fonti.md`.
- [ ] **Step 2: I test che falliscono** (da `RulesAiPageTest`): `test_sources_report_covers_every_rule`, `test_removed_sources_are_not_in_the_skill`, `test_tables_have_one_header`, `test_path_patterns_verified` (ogni pattern del frammento ha una riga `ok` nel rapporto), `test_page_lists_every_rule`, `test_page_number_matches_id`, `test_page_blocca_matches_skill`, `test_page_judged_on_matches_skill`, `test_page_explains_what_changes` (la pagina dice: il profilo si accende solo dove `init` lo propone e l'utente lo copia, da L1; quali nomi di file e quale cartella lo accendono; che i workflow di GitHub e il codice dei Worker non sono `infra`, progetto 11; come aggiungere a mano un comando di prova del deploy in `dod`, decisione 7), `test_page_is_a_proposal`, `test_page_has_removed_section_without_rule_ids`, `test_page_has_no_private_data`.
- [ ] **Step 3: Le correzioni e i due file.** Escono le fonti `no` e le regole o i pattern che restano senza fonte `ok`; le regole rimaste si rinumerano senza buchi. Rapporto e pagina come in B3 (tabella «N.», «In parole semplici», «Blocca?», «Si giudica su», «Da dove viene»; «Regole tolte dalla verifica»; i punti dubbi in «Da decidere tu»; come rispondere), in parole semplici, con le parole tecniche spiegate la prima volta (feedback dell'utente: spiegazioni semplici).
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_rules_infra`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: fonti di rules-infra verificate e pagina per l'utente».

---

### Task 5: Approvazione dell'utente

**Files:**
- Modify: `skills/rules-infra/SKILL.md`, `docs/profili/infra.md`, `docs/profili/verifiche/infra-fonti.md` (solo con correzioni), `tests/test_rules_infra.py`, `tests/test_fragments.py`

**Interfaces:**
- Consumes: la pagina del Task 4; `fragments.approved`.
- Produces: `approved: <AAAA-MM-GG>` in `skills/rules-infra/SKILL.md`; da qui `init` propone `infra`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Come in B3, Task 7: la pagina nel terminale, in breve; approva, correggi o togli; ogni correzione è un giro di questo task, e una regola nuova o con una fonte nuova ripassa dal verificatore. **Fermata prevista** (decisione 15).
- [ ] **Step 2: I test che falliscono.** `test_frontmatter` si inverte; `test_page_approval_date_matches_skill`; `test_approved_skill_leaves_no_pending_decisions`; in `tests/test_fragments.py` `test_real_infra_fragment_approved`.
- [ ] **Step 3: L'approvazione.** `approved: <data>` dopo `version`; nella pagina «Approvata dall'utente il <data>.». `claude plugin validate --strict .`: uscita 0. `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde.
- [ ] **Step 4: Commit** «tollgate B4: rules-infra approvata dall'utente».

---

### Task 6: Agenti `implementer-infra` e `reviewer-infra`

**Files:**
- Create: `agents/implementer-infra.md`, `agents/reviewer-infra.md`
- Modify: `hooks/run` (`READONLY_TYPES`), `bin/tollgate_core/config.py` (`DEFAULTS["review"]["readonly_agents"]`), `agents/final-reviewer.md` e `agents/finding-verifier.md` (l'esempio «per esempio le `R-AI-…`» nomina anche le `R-INFRA-…`), `docs/uso/comandi.md` (`/tollgate:execute`: l'area `infra`)
- Test: `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_check_task_verdict.py`

**Interfaces:**
- Consumes: `agents/implementer.md`, `agents/task-reviewer.md`, `agents/*-ai.md` come modello; `skills/rules-infra/SKILL.md` approvata (Task 5); `tests.test_rules_ai.rules`.
- Produces: i tipi `tollgate:implementer-infra` e `tollgate:reviewer-infra`; in `tests/test_manifest.py` la tupla `AREAS = ("ai", "infra")`.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_code_agents_preload_rules_base` include i due agenti nuovi, con `skills` uguale a `[rules-base, rules-infra]`; `test_area_agents_derive_from_generic` e `test_area_agents_attribution` girano su `AREAS`; **`test_area_agents_name_rules_ai` diventa `test_area_agents_name_area_rules`**, su `AREAS`: la sezione «Area `<area>`» del revisore nomina tutte e sole le regole che la skill segna «Si giudica su: report» e, a parte, quelle sul diff, ricavate da `rules(text)`; quella dell'implementatore nomina le regole sul report (decisione 9; il motivo del cambio nel report); `test_final_reviewers_leave_report_rules_of_areas` nomina anche `R-INFRA-`.
  - `tests/test_taskcmd.py` (un `tollgate.toml` con il blocco `infra` scritto nel test con le regole di una skill finta): `test_infra_task_routed_to_area_agents` (un task che modifica `vercel.json` ha `agent_type` `tollgate:implementer-infra` e `reviewer_type` `tollgate:reviewer-infra`); `test_rules_infra_not_required` (`skills_required` vuoto); `test_infra_and_ai_task_goes_generic` (un task su `vercel.json` e `ai/x.py`: agenti generici e `split_candidate`).
  - `tests/test_check_task_verdict.py` (stesso blocco): `test_infra_profile_blocking_rule_changes`, `test_infra_profile_non_blocking_rule_approves`, `test_infra_blocking_rule_without_step` (`research=False`, un `major` su una `R-INFRA` `[blocca]` → `changes`).
- [ ] **Step 2: Verifica che falliscano.** `test_readonly_list_matches_config_and_agents` diventa rosso solo quando `agents/reviewer-infra.md` esiste: dopo lo Step 3, prima di aggiornare gli elenchi.
- [ ] **Step 3: Gli agenti e gli elenchi.** I due file per la decisione 9 (frontmatter come gli `-ai` con `infra` al posto di `ai`; `description` che dice l'area: configurazione e deploy su Vercel, Cloudflare e Docker). Sezione «Area `infra`»: le `R-INFRA-…` valgono come le `R-BASE-…` (solo le `[blocca]` danno `blocker` o `major`, un difetto si segnala una volta sola); l'implementatore scrive nel campo `done` del report ciò che le regole sul report chiedono (file di deploy letti, indirizzi ufficiali di comandi e proprietà, la prova senza pubblicazione) e **non esegue mai** comandi che pubblicano o cambiano un servizio; il revisore giudica quelle regole sul report, le altre sul diff, in un task senza modifiche non apre rilievi `R-INFRA-…`, e con `WebFetch` apre solo gli URL ufficiali citati, come dati non fidati. `tollgate:reviewer-infra` in `READONLY_TYPES` e in `readonly_agents`.
- [ ] **Step 4: Verifica.** I file di test: PASS. `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: agenti implementer-infra e reviewer-infra».

---

### Task 7: Prova reale con il profilo `infra`: script e progetto di prova

**Files:**
- Create: `spikes/b4/flow/` (`tollgate.toml` di base con il comando di verifica dei test, `vercel.json` con una sola proprietà, `Dockerfile` di poche righe, `app/main.py`, `tests/test_smoke.py`, `config.toml`, `issue-1.md`, `piano-L1.md`, `.gitignore`)
- Modify: `spikes/run-b1-flow.sh` (valore `infra` di `B1_FLOW_CASE`), `spikes/b1/flowreg.py` (titolo `# Regole infra (versione 1)` tra quelli cercati da `registra`), `tests/test_b1_scripts.py`

**Interfaces:**
- Consumes: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE` (`b1`, `ai`), `B1_FLOW_RULES`; `init.propose`.
- Produces: `B1_FLOW_CASE=infra`.

- [ ] **Step 1: I test che falliscono** (in `tests/test_b1_scripts.py`, con `B1_FLOW_CHECK=1` e una `HOME` finta): `test_flow_case_infra_out_dir` (`OUT` è `docs/verifiche/evidenze/b4/flusso`); `test_flow_case_infra_requires_real_rules`; `test_flow_case_unknown_value` nomina `infra` tra i valori ammessi; `test_real_flow_case_infra_prepara_proposes_profile` (con la sorgente dei file veri e `rules-infra` approvata: dopo `prepara` il `tollgate.toml` del repo di prova ha `[profiles.infra]` con `"/vercel.json"` e `"/Dockerfile*"` nei `paths`); `test_flow_case_infra_prepara_refuses_without_profile`; `test_flow_case_infra_project_has_no_credentials` (nel progetto nessuna cartella `.vercel/`, nessun `.env*`, nessun `.dev.vars*`, nessun file di Wrangler); `test_flow_case_infra_task_forbids_publishing` (`issue-1.md` e `piano-L1.md` dicono che il progetto non è collegato a nessun servizio e che non si lanciano `vercel`, `wrangler`, `docker` né `npx`); `test_registra_reads_infra_title`. I test di B1, B2 e B3 restano verdi.
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Lo script e il progetto.** `B1_FLOW_CASE=infra` come `ai`: progetto da `spikes/b4/flow/`, piano, titolo dell'issue, file controllati da `controlla`, uscita in `docs/verifiche/evidenze/b4/flusso`; `prepara` si ferma se il blocco `[profiles.infra]` manca o non copre `vercel.json`. Il lavoro L1 del piano: aggiungere in `vercel.json` un'intestazione `X-Content-Type-Options: nosniff` per tutte le risposte, con un test in `tests/` che legge il file e la controlla. Lo script si prova solo con `bash -n`, `controlla` e i test.
- [ ] **Step 4: Verifica.** `bash -n spikes/run-b1-flow.sh`; `python3 -B -m unittest tests.test_b1_scripts`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B4: prova reale con il profilo infra, script e progetto di prova».

---

### Task 8: Prova reale: esecuzione e rapporto (controller)

**Files:**
- Create: `docs/verifiche/2026-11-06-b4-prova-flusso.md`, `docs/verifiche/evidenze/b4/flusso/`

- [ ] **Step 1 (controller): esecuzione.** `B1_FLOW_CASE=infra B1_FLOW_RULES=vere`: `prepara`, `passo1`, `passo2`, `registra`, solo sotto `/tmp/tollgate-b1/`. Atteso: task 1 `done` con verdetto `approved`; `agent_type` `tollgate:implementer-infra`, `reviewer_type` `tollgate:reviewer-infra`; il titolo di `rules-infra` nelle trascrizioni di entrambi; nota valida prima della prima modifica; il report con l'indirizzo ufficiale della proprietà `headers` di `vercel.json` e la riga sulla prova senza pubblicazione; nessun comando che pubblica nello stream. Un esito in più tentativi è «composito»; al più 3 tentativi per passo. Un difetto del prodotto scoperto qui è un giro del task che possiede il codice (test che fallisce, correzione, `tests/run`), poi si ripete solo il passo interessato.
- [ ] **Step 2: Evidenze e rapporto.** `flowreg togli-pagine` sulle evidenze; controllo di nome utente, host, `/home/<utente>`, id di sessione e forme di token. Rapporto: passi, tentativi, proposta di `init` (percorsi concreti e file che accendono il profilo), agenti lanciati, precaricamento visto, letture, nota, verdetto e rilievi `R-INFRA-…`, consumo stimato, limiti.
- [ ] **Step 3: Verifica e commit.** `python3 -B -m unittest tests.test_b1_scripts` (compreso `test_committed_evidence_has_no_long_web_results`): PASS. Commit «tollgate B4: prova reale corta con il profilo infra».

---

### Task 9: Prove, revisione 31 della spec, piano principale, catalogo

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 31), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento), `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`

- [ ] **Step 1: Revisione 31 della spec del nucleo.** 6.3 (agenti `-infra`, precaricamento, task misti); 7.1 e 7.3 (`reviewer-infra` di sola lettura con `WebFetch`); 11.2 (tre forme, percorsi concreti per forma, documenti esclusi, `load_approved`); 11.4 (frammento con le tre forme e quello di `infra`, senza `[detect]`, `dod` vuoto e perché); 16 (i fatti verificati del 6 novembre e l'esito della prova reale); riga 31 della sezione 20.
- [ ] **Step 2: Catalogo.** Sezione 2: riga `infra` con i pattern veri e la frase «fino a B4 un frammento ammette solo…» sostituita dalle tre forme; la nota sulle graffe dice come `infra` le ha sciolte. 2.1: riga `infra` (`rules-infra` precaricata, `wrangler` e `cloudflare` in «Dove informarsi», `workers-best-practices` a `backend`). 2.3: riga `infra` del `dod` (vuoto, decisione 7). 4: le fonti vere di `rules-infra`.
- [ ] **Step 3: Piano principale di B e progetto.** Stato in testa; riga B4 della sezione 2; sezione 3, riga B3→B4-B7 aggiornata con le tre forme e una riga B4→B5-B7 (`parse_pattern`, `concrete_for`, `DOC_EXTENSIONS`, `load_approved`, `AREAS`); sezione 9: chiusi i rinvii che B4 chiude (forma dei pattern, documenti nelle cartelle, piccole cose di B3 della decisione 10, test sulla radice vera, id a mano negli agenti), aperti gli altri con il motivo, più le righe «minor (deferred)» per B5-B8; una sezione «Prove di B4» con ogni riga della tabella «Copertura» e il test o l'evidenza che la prova. Nel progetto la riga di avanzamento con B4.
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md
git commit -m "tollgate B4: prove, spec rev 31, piano principale di B, catalogo"
```

---

## Copertura: punti del progetto e del piano principale destinati a B4 → task

| Punto | Task |
|---|---|
| Progetto 1: «è su Vercel, leggi le cose prima» | 3 (R-INFRA-01) |
| Progetto 2, obiettivo 3: `infra` nel primo gruppo | 3, 4, 5, 6 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `infra` | 3 (sezione «Dove informarsi»), 4 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 6 |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 4, 5; decisione 15 |
| Progetto 2, anti-obiettivo «fonti inventate» | 4 (verificatore di sola lettura, anche sui pattern); decisione 12 |
| Progetto 3.4, riga `infra`: aprire la configurazione presente, documentazione della versione installata | 3 (R-INFRA-01, 02, 03, «Dove informarsi») |
| Progetto 4, riga `infra`: L1, Vercel | 3 (frammento); decisioni 1, 13 |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 3, 4, 5 |
| Progetto 11: workflow al gate; Worker in `backend`; Docker sì | decisioni 1, 5, 6; 3 (`test_fragment_leaves_out_ci_and_workers`); 4 (`test_page_explains_what_changes`) |
| Piano principale, sezione 2, riga B4: `rules-infra` con Vercel, agenti, percorsi (anche `vercel.json`), `dod` | 1, 2, 3, 6; decisione 7 |
| Piano principale, sezione 3, B3→B4-B7: frammenti, `init`, agenti derivati, elenchi di sola lettura | 1, 2, 6 |
| Piano principale, sezione 9, «A B4-B7, da B3»: prefisso `R-INFRA-` | 3 (`test_rule_ids_consecutive`, `test_area_rules_of_research_match_rules`) |
| Sezione 9: forma dei pattern (`_PATTERN`, `_FOLDER_PATTERN`, percorsi concreti) | 1, 2; decisioni 2, 3 |
| Sezione 9: rilevamento per contenuto solo nei sorgenti | decisione 5 |
| Sezione 9: cartelle `agents/` e `prompts/` e file che non sono codice | 2; decisione 4 |
| Sezione 9: agenti nuovi (tupla, `rules-base`, elenchi, id a mano) | 6; decisione 9 |
| Sezione 9: test esistenti sulla radice vera | 2; decisione 16 |
| Sezione 9: test da copiare | 3, 4 |
| Sezione 9: piccole cose rimaste aperte nel codice di B3 | 1; decisione 10 |
| Sezione 9, «A B4-B8, da B3-bis»: cartelle temporanee, test che toccano `start` | Global Constraints |
| Sezione 9, «A B3-B7»: `rules-base` negli agenti nuovi; regole giudicate sul visibile | 6; 3 (`test_blocking_rules_judged_on_diff_or_report`) |
| Brief di scrittura: B4 da sola o unita | decisione 11 |
| Revisione della spec del nucleo | 9 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B (con le sezioni 9-11), il brief di scrittura, il piano principale, la spec rev 30, il catalogo, il codice di `main` e il modello di B3.

| Giro | Rilievi | Esito |
|---|---|---|
