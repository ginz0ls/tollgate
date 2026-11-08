# Revisione finale del ramo B4 (`b4-profilo-infra`, `0c15d33..c81fa1e`)

Revisore finale a contesto pulito, in sola lettura. Letti: brief, decisioni, review focus, copertura, vincoli, ledger, carry, ruling, minori rinviati, rapporto della prova, i due diff (codice per intero; documenti per le parti di spec, piano principale e rapporto), più controlli mirati sui file del ramo. Sonde con `python3 -B -I` in `/home/USER/.claude/jobs/e28b8553/tmp/final/` (solo `bash.parse`/`effect_reason`, `init.concrete_for`, lettura dei `.jsonl` delle evidenze). Test mirati: `tests.test_bash tests.test_fragments tests.test_rules_infra tests.test_manifest tests.test_profiles tests.test_init.ProfileBlocksTest`: 258 test OK (skipped=2). Nessuna rete, nessun programma di servizio, nessun valore di chiave letto.

## 1. Verdetto

**Non pronto per il merge**: un Important da correggere (testo di terzi rimasto nelle evidenze pubbliche, con il rapporto che dice il contrario). Il codice, le regole, gli agenti e i documenti sono pronti; il giro è piccolo.

Critical 0 · Important 1 · Minor 5

## 2. Rilievi

### I-1 (Important) — Testo di una pagina di Vercel rimasto nelle evidenze; il rapporto dice che è stato tolto

- **Dove**: `docs/verifiche/evidenze/b4/flusso/passo2/tentativo-1/claude.jsonl:128`; in misura minore `docs/verifiche/evidenze/b4/flusso/passo1/tentativo-1/claude.jsonl:153`; il rapporto `docs/verifiche/2026-11-06-b4-prova-flusso.md:146`; la causa in `spikes/b1/flowreg.py:28` e `:315` (`WEB_TOOLS = ("WebFetch", "WebSearch")`) e in `tests/test_b1_scripts.py:1072` (`test_committed_evidence_has_no_long_web_results`).
- **Cosa**: la riga 128 del passo 2 è il risultato di un `Grep` con `-C 1` dell'implementatore sulla copia salvata della pagina `vercel-json` (`~/.claude/projects/…/SESSIONE-2/tool-results/toolu_0166….txt`). Il risultato, circa 800 caratteri, contiene una frase intera della documentazione di Vercel (quella su `cleanUrls` e `vercel dev` che danno 404 in locale) e due esempi JSON della pagina, con i numeri di riga. La riga 153 del passo 1 è un altro `Grep` sulla stessa copia: intestazioni e righe JSON della pagina, più corte e senza prosa. La riga 146 del rapporto dice che «sono stati tolti a mano anche i testi di terzi sotto il tetto di 5.000 caratteri», e nomina il `WebSearch`, il `Read` della pagina salvata e le anteprime `persisted-output`. I due `Grep` non sono stati tolti.
- **Perché è Important**: il repo è pubblico. Il vincolo globale è «nessun testo copiato da pagine di terzi». La ruling del giro 1 del Task 9 dice «nel repo pubblico niente testo di terzi, non solo sopra il tetto» (lezione I-1 di B3, che in B3 era un Important della stessa classe). E il rapporto afferma una pulizia che non è completa. Il buco è strutturale: `togli-pagine` e il test riconoscono solo i risultati di `WebFetch` e `WebSearch`. Un `Read` o un `Grep` sulla pagina che Claude Code salva in `tool-results/` porta lo stesso testo e passa da entrambi. La pulizia a mano ha preso il `Read` (passo 1, riga 161) e ha mancato i `Grep`.
- **Scenario che fallisce**: dopo il merge, `main` pubblica una frase e due esempi della documentazione di Vercel (che non dichiara una licenza), e una prova futura (B5-B7) fa lo stesso senza che nessun controllo se ne accorga, perché il modello legge spesso a pezzi la pagina salvata invece di rifare il `WebFetch`.
- **Come correggere**: (a) mettere il segnaposto di `togli-pagine` (`[pagina di terzi tolta dalle evidenze: vercel.json (pagina di documentazione salvata), N caratteri]`) nel `content` delle due righe, tenendo il JSON valido; (b) in `flowreg._third_party` trattare come testo di terzi anche il risultato di un `Read` o di un `Grep` il cui `file_path`/`path` sta sotto `/tool-results/`, con un test in `tests/test_b1_scripts.py` (rosso sulle evidenze di oggi, verde dopo (a)), così la prova di B5 non dipende da una pulizia a mano; (c) nella riga 146 del rapporto aggiungere i due `Grep`.

### M-1 (Minor) — `docker-compose push` (binario con il trattino) non è un effetto

- **Dove**: `bin/tollgate_analysis/bash.py:984-1000` (`_DEFAULT_EFFECTS`), `tests/test_bash.py` (`test_docker_push_forms`).
- **Cosa**: la ruling D3 ha aggiunto `docker compose push`; `docker-compose push` e `docker-compose -f a.yml push` danno `None` (sonda). La forma non è scritta tra i buchi della spec 8.5 né del piano principale (lì c'è solo `docker compose -f a.yml push`). Il frammento accende `docker-compose.yml` e `docker-compose.yaml` proprio per i progetti che usano ancora quei nomi, cioè quelli in cui il binario v1 è più probabile.
- **Scenario**: un progetto con `docker-compose.yml` e il vecchio `docker-compose`; l'agente lancia `docker-compose push` e le immagini vanno al registro senza approvazione.
- **Come correggere**: `("docker-compose", "push")` in `_DEFAULT_EFFECTS`, con una riga in `test_docker_push_forms` (costo zero, stesso meccanismo di D3), oppure scriverla tra i buchi. Da fare nel giro di I-1.

### M-2 (Minor) — Gli script `deploy`/`release` nelle forme dei monorepo passano senza veto (preesistente, non scritto)

- **Dove**: `bin/tollgate_analysis/bash.py:1167-1170`.
- **Cosa**: `project_scripts` (default `["deploy", "release"]`) guarda solo `a[1]`, o `a[2]` dopo `run`. `npm -w web run deploy`, `pnpm -F web run deploy` e `yarn workspace web deploy` danno `None` (sonda con `project_scripts=["deploy","release"]`). Il buco c'era già su `main`: non è una regressione di B4. Però B4 ha chiuso proprio le forme dei monorepo per i comandi di servizio (`pnpm --filter web exec wrangler deploy`), e la lista dei buchi (piano principale, sezione 9) nomina `npm -w web publish` ma non lo script `deploy` con un'opzione davanti.
- **Come correggere**: almeno una riga tra i buchi del piano principale (sezione 9) e della spec 8.5; meglio, in B5, cercare lo script con la stessa scansione dei lanciatori.

### M-3 (Minor) — `docs/uso/comandi.md:159`: «Le caricheranno» al futuro

- La sezione `/tollgate:rules-infra` dice «Le caricheranno gli agenti dell'area `infra`», ma gli agenti esistono e le precaricano (Task 7, prova del Task 9). La sezione gemella di `rules-ai` dice «Le caricano». Basta cambiare il verbo nel giro.

### M-4 (Minor) — R-INFRA-06, seconda frase, ambigua su «codice che li usa»

- **Dove**: `skills/rules-infra/SKILL.md:35`.
- «Se il diff aggiunge codice, uno script o documentazione che li usa, `.gitignore` li esclude.» Un revisore può leggere «li usa» come «legge variabili d'ambiente» (`process.env.X`, `os.environ`) e aprire un `blocker` su un diff che non tocca nessun `.env`. La regola è approvata e i numeri sono stabili. La frase si chiarisce alla prossima revisione delle regole («che legge uno di quei file», con l'esempio di `wrangler dev` per `.dev.vars`), passando dall'utente. Per ora nessuna azione sul ramo.

### M-5 (Minor) — Test del caso `infra` di `test_b1_scripts.py` che dipendono dai file veri senza il prefisso `test_real_`

- **Dove**: `tests/test_b1_scripts.py` (`test_flow_case_infra_project_verifies`, `test_flow_case_infra_prepara_refuses_without_profile`, `test_registra_flags_deploy_clis`, `test_registra_reads_infra_title`, `test_registra_infra_refuses_an_empty_home`, `test_flow_case_infra_project_has_no_credentials`, `test_flow_case_infra_task_forbids_publishing`).
- Passano da `src_repo(case="infra")`, che copia `bin/`, `templates/`, `agents/` e `skills/rules-infra/` veri, o leggono `spikes/b4/flow/` vero. Se un giorno `rules-infra` perde `approved` o il frammento cambia, falliscono per una ragione che il nome non dice. È lo stesso schema dei test del caso `ai` di B3, già accettato, ed è il minore rinviato del Task 8. Nessuna dipendenza da variabili della macchina o dal nome della cartella (i percorsi vengono da `ROOT`), e nessuna asserzione che possa stampare `os.environ` (controllato su tutto il diff dei test). Rinviabile a B5 con una rinomina in blocco dei test di `ai` e `infra`.

### Controllati e senza rilievi (punti del brief)

- **Pattern di nome dentro le cartelle escluse**: `concrete_for` dà `None` per `Dockerfile` e `vercel.json` sotto `.github/tollgate/`, `.github/workflows/`, `.github/actions/`, `.claude/` e `docs/superpowers/tollgate-init/` (anche `files/`), per `Dockerfile/x.py`, per `docker/Dockerfiles/x.py`, per `infra/README.md`, per `src/infra/db.py`, per `docs/Dockerfile-note.md`. Un nome confina con `.github/` solo fuori dalle due cartelle escluse (`.github/Dockerfile` accende `infra`, come previsto).
- **Specificità**: i percorsi esatti battono `web/**` e `services/api/**`; perdono solo a parità contro un pattern dichiarato con gli stessi segmenti letterali, o con segmenti escapati (`app/\[id\]/vercel.json` vale 2), come scrivono la decisione 3 e la spec 11.2.
- **`tollgate.toml` dell'utente**: `init` non lo scrive (il codice di scrittura non cambia); le righe di deriva per i nomi rispettano le negazioni (`test_declared_profile_negation_respected_for_names`).
- **Regole `[blocca]`**: le sette (`01`, `02`, `03`, `04`, `05`, `06`, `12`) si giudicano sul diff o sul report; nessuna sulla sola nota; ognuna ha un sì o no osservabile.
- **Agenti d'area**: `diff` contro i generici mostra solo frontmatter (`name`, `description`, `skills`, `tools` del revisore) e la sezione «Area `infra`»; la riga di attribuzione è identica.
- **Effetti nuovi non voluti**: i nuovi effetti sono quelli della decisione 17, di D3 e di D13, più i falsi positivi della classe già scritta nel costo (`npx vitest run vercel`, `npx eslint -c x vercel`, `pnpm --filter=vercel build`, `npm --prefix aws exec …`). `npm install`, `npx prettier --write vercel.json`, `npx tsc`, `npx eslint infra/aws`, `npm view wrangler` e `npx jest -t "vercel headers"` restano senza effetto.
- **Deploy comuni**: `npx|bunx|pnpx|pnpm dlx|yarn dlx|bun x|npm exec [--] wrangler deploy`, `vercel --prod`, con `env`, `sudo`, `timeout`, `nice`, `time`, `xargs`, `bash -c`, `$(…)`, `npx -c`/`--call`, `node_modules/.bin/…`, `@cloudflare/wrangler@3`, `netlify-cli`, `firebase-tools`: tutti effetti. Sfuggono solo le forme già scritte (`wrangler --env prod deploy`, `docker build --push`, `docker compose -f … push`, `npm --loglevel info exec …`, `pnpm -c exec '…'`, kv/d1/r2) più M-1 e M-2.
- **Coerenza**: codice, skill approvata, pagina, `comandi.md` (salvo M-3) e spec rev 31 dicono le stesse cose; ogni `test_…` citato nei documenti esiste; R-INFRA-11/12 sono usati bene fuori dal piano di B4; i file approvati di `base` e `ai` non sono toccati; 15 commit, tutti con `Co-Authored-By`; nessun `__pycache__` tracciato.
- **Dati dell'utente nelle evidenze**: nessun nome utente, host, percorso del checkout, `sk-ant`, `ghp_`, `github_pat_`; `/home/USER`, `HOST`, `SESSIONE-1/2` come dice il rapporto. Resta solo I-1.

## 3. Triage di `final-deferred.md`

| Voce | Esito | Motivo |
|---|---|---|
| T1 — `fragments.py:16-17` il segmento ammette il newline (`a\n/**`) | nessuna azione | Come la regex di B3; in TOML serve un `\n` esplicito e nessun percorso tracciato realistico ci corrisponde. |
| T1 — ramo `[None]` contorto in `fragments.py:82-83` | rinviato (B5, se si tocca `_parse`) | Solo leggibilità; il comportamento è giusto e testato (`test_load_rejects_*`). |
| T3 — `docker compose -f a.yml push` → None | nessuna azione | È scritto tra i buchi (spec 8.5, piano principale riga 219). La forma col trattino è M-1. |
| T3 — test su `commands` con lanciatore e `curl`/`gh` sull'argv originale | nessuna azione | Fatto nel giro 1 (`test_commands_config_matches_launcher_text`, `test_curl_and_gh_stay_on_original_argv`). |
| T3 — falsi positivi `npm cache clean vercel`, `npm run docker push`, `npm test -- -c vercel` | nessuna azione | Classe scritta nel costo della decisione 17 e nella spec 8.5 (i primi due nominati). |
| T2 — processo: codice prima dei test | nessuna azione | Il rosso è stato ricostruito; nessun effetto sul prodotto. |
| T2 — `.__len__()` in `test_name_pattern_exact_paths` | da correggere nel giro di I-1 | Una riga, costo nullo. |
| T2 — `init._match` ricalcola `folders` e `roots` per file | nessuna azione | Al più 14 pattern; costo trascurabile anche su repo grandi. |
| T2 — `concrete_for` su un prefisso escluso senza test diretto | nessuna azione | Coperto da `test_name_pattern_skips_excluded_prefixes` (la prima riga di `_match`); confermato con una sonda. |
| T4 — `"@nome"` in `env` di Vercel | nessuna azione | Risolto nel giro del Task 5 (skill, pagina, rapporto, `test_secret_reference_exception_matches_skill`). |
| T4 — R-INFRA-02 senza pagina dei comandi Docker | nessuna azione | Dichiarata scelta nostra, «Dove informarsi» nomina docs.docker.com, approvata dall'utente il 07/11. |
| T4 — R-INFRA-01, Fonte con 3.4 e 11 | nessuna azione | Approvata così; la Fonte è corretta. |
| T4 — R-INFRA-07 «data del giorno» giudicabile solo con la data del commit | nessuna azione | Regola non bloccante; il file del diff porta l'elenco dei commit. |
| T4 — `test_no_long_quotations` guarda solo le «» | rinviato | Le copie delle fonti non sono nel repo; il controllo del testo copiato resta del verificatore (Task 5), come in B3. |
| T5 — `pages project create/delete` senza una riga ok propria | nessuna azione | Le voci sono nel codice e nella Fonte di R-INFRA-12 («i comandi `pages` che creano, cancellano…»); approvate. |
| T5 — numeri «dodici», «N punti», «quattro fonti» senza test | nessuna azione | «Sette punti» è testato; dopo l'approvazione i numeri delle regole non cambiano. |
| T5 — `test_page_has_no_private_data` controlla solo `/home/` | rinviato | Il test non può conoscere nome utente e host senza leggerli dall'ambiente; il controllo vero resta la grep del controller prima del commit. |
| T5 — la pagina nomina solo `env` per `"@nome"`, la skill `env` o `build.env` | rinviato (prossima revisione della pagina, con l'utente) | Il revisore legge la skill, che è la più larga; la pagina è approvata e non si ritocca senza l'utente. |
| T7 — processo: rosso di `test_readonly_list_matches_config_and_agents` non visto | nessuna azione | Il test è verde e confronta tre elenchi; nessun effetto sul prodotto. |
| T7 — nessun test che fissi `wrangler kv`/`d1`/`r2` e le build con push nel testo di `implementer-infra` | rinviato | Testo presente (`agents/implementer-infra.md:53`); la deriva è improbabile finché i buchi non si chiudono, e B5 riscrive quella frase quando copre kv/d1/r2. |
| T7 — `implementer-infra.md:53` «la sua configurazione elenca» approssimativo; non dice che anche la prova di R-INFRA-12 chiede l'approvazione | nessuna azione | R-INFRA-12 (precaricata) dice «dopo l'approvazione dell'utente che tollgate chiede per quei comandi»; l'agente lo ha nel contesto. |
| T8 — la grep di `registra` non segna `(yarn)` nudo né i comandi dopo un backtick | nessuna azione | Scritto nei limiti; il rapporto legge `comandi-modello.txt` a mano, e la difesa vera è l'hook. |
| T8 — `test_registra_flags_deploy_clis` non copre `command`/`env`, `;`, `bash (subagente):` | rinviato | Copertura in più; la regex li tratta e il caso reale era vuoto. |
| T8 — `spikes/b4/flow/.gitignore` non esclude `.vercel/`, `.env*`, `.dev.vars*`, `.wrangler/` | da correggere nel giro di I-1 | Quattro righe, nessun effetto sui test (`test_flow_case_infra_project_has_no_credentials` guarda i nomi dei file, non `.gitignore`); difesa in più per un progetto di prova in un repo pubblico, coerente con R-INFRA-06. |
| T8 — processo: RED non osservato a parte | nessuna azione | Nessun effetto sul prodotto. |
| T8 — due test leggono i file veri di `rules-infra` senza `test_real_` | rinviato | Vedi M-5: stesso schema di `ai`, da rinominare in blocco in B5. |
| T9 — il piano di B4 nomina R-INFRA-11 per «non pubblicare» | nessuna azione | Il piano è storia; spec rev 31, skill, agenti e pagina usano R-INFRA-12 (controllato). |
| T10 — due righe fuori colonna nella sezione 20 della spec (rev 14 e 24) | rinviato | Preesistenti su `main`, fuori dal ramo. |

## 4. Punti di forza

- `fragments.parse_pattern` e `init.concrete_for` sono davvero l'unico punto per le tre forme. Il confronto del nome con `fnmatchcase` sull'ultimo segmento evita alla radice che le cartelle si accendano, e l'esclusione dei prefissi è il primo controllo di `_match`.
- La scansione dei lanciatori è sicura per costruzione: le sonde su una sessantina di forme reali (lanciatori annidati, monorepo, `env`/`sudo`/`xargs`/`bash -c`, `-c`/`--call`, `.bin/`, nomi con scope) danno l'esito atteso, e i falsi positivi restanti sono tutti nella classe dichiarata.
- La scelta di `dod = []`, con l'avviso esplicito che i comandi del `dod` girano senza veto e con le credenziali salvate, è il punto di sicurezza più sottile del profilo, ed è scritto bene nella pagina e nella spec.
- Il test d'area degli agenti, che confronta per frase gli id «sul report» e «sul diff» con la skill, chiude la deriva meglio dei confronti di frasi di B3.
- Il rapporto della prova è onesto sui limiti: il piano scritto dal modello, il report che non prova da solo il precaricamento, R-INFRA-12 vista solo nel ramo «perché no». Fa eccezione la sola riga 146 (I-1).
