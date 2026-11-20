## Decisioni di questo piano

Scelte che il progetto e il piano principale lasciano a B8, o che il codice reale impone, con il costo se sbagliate. Il Task 8 le riporta nella revisione 35 della spec.

1. **Dietro un involucro dell'ambiente si controlla il comando interno per intero** (utente: chiudere il buco; mia scelta: come; giro 1, I1, M13).
   - `bash.ENV_LOADERS = ("dotenv", "dotenvx", "cross-env", "env-cmd", "doppler", "infisical", "op")`, riconfermato nello Step 0 del Task 1.
   - Funzione nuova `bash.inner_commands(cmd: Cmd) -> list[Cmd | str]` (i candidati illeggibili come testo, sotto): per un `Cmd` il cui `basename(argv[0])` è in `ENV_LOADERS`, restituisce i comandi interni candidati. **Ogni candidato si costruisce con `bash.parse(shlex.join(<parole>), cmd.cwd)`**, così il comando interno passa dagli stessi passi di un comando diretto: `_unwrap` toglie `env`, `sudo`, `timeout`, `time` e le assegnazioni `NOME=valore`, e `bash -c`, `sh -c` ed `eval` si aprono (giro 2, N1).
     - Con un `--`, le parole dopo il primo `--`.
     - **Sempre**, anche quando c'è un `--` (giro 3, N8: con `cross-env NODE_ENV=production npm run deploy -- --prod` il `--` è del comando interno), le parole **fino in fondo** da ogni posizione `i ≥ 1` prima del primo `--`, se il token in `i` non comincia con `-` e non è un'assegnazione `NOME=valore`. È una scansione, non una grammatica (lezione di B4).
     - Un token con `/` si scandisce solo se è un **comando per percorso** (giro 4, N11, m1; giro 5, N13, N15, m1, m2):
       - un percorso assoluto, o un percorso dentro una cartella `bin/` o `.bin/` (`/usr/local/bin/vercel`, `/usr/bin/curl`, `./node_modules/.bin/prisma`);
       - un percorso che finisce in `.sh` o `.bash`;
       - un percorso `./…` o `../…` il cui `basename` non ha un punto (`./deploy`, `../scripts/release`). Questo caso va **solo** a `_script_reason` (file eseguibile), mai a `effect_reason` per `basename`: `jest ./src/aws` e `pytest ./tests/vercel` passano (giro 6, m1).

       Gli altri token con `/` si saltano, per evitare i falsi permessi (giro 2, m2). Sono i dati e i file di test: `tests/vercel`, `src/aws`, `./test/.env`, `test/**/*.spec.js`, `src/new.test.ts`. Uno script di un interprete (`node scripts/migrate.js`) si vede dal candidato che comincia con l'interprete.
     - Così chiedono come la forma diretta `cross-env A=1 /usr/local/bin/vercel --prod`, `env-cmd -f .env /usr/local/bin/vercel --prod`, `cross-env A=1 /usr/bin/curl -X POST https://x`, `cross-env A=1 /usr/bin/make deploy`, `cross-env A=1 ./deploy.sh`, `cross-env A=1 ./deploy` e `dotenv -e .env ./scripts/deploy.sh`. Passano `env-cmd -f ./test/.env mocha -R spec`, `dotenv -e ./.env.test -- jest`, `cross-env NODE_ENV=test jest src/aws` e `cross-env NODE_ENV=test mocha 'test/**/*.spec.js'`.
     - Per `doppler`, `infisical` e `op`, il valore delle opzioni che lo Step 0 conferma come «comando da eseguire» (attese `--command` e `--cmd`, anche nella forma `--command=…`; per `doppler` `-c` è `--config` e non conta: giro 3, m5), **prima** del primo `--`, aperto con `bash.parse`.
     - Un candidato che `parse` non sa leggere (`BashParseError`) passa da `text_effect` sul suo testo; se `text_effect` non dà un motivo, il comando chiede il permesso (giro 3, m2).
     - `[external_effects] allow` e `commands` si confrontano prima sul testo esterno intero, come oggi; i comandi interni si guardano solo se il testo esterno non è già ammesso (giro 3, m11).
   - **Un involucro dietro un lanciatore** (giro 2, N2; giro 3, N9, m4): in `effect_reason`, per un comando con `basename(argv[0])` in `LAUNCHERS`, ogni posizione `i ≥ 1` il cui token normalizzato è in `ENV_LOADERS` produce anche `effect_reason(Cmd([norm] + argv[i+1:]))`, con la stessa profondità.
     - Il token si normalizza con `_launcher_token` (toglie la versione, `dotenv@16`) e poi con la tabella nuova `bash.LOADER_PACKAGES: dict[str, str]` (nome del pacchetto npm → programma), attesa `{"dotenv-cli": "dotenv", "@dotenvx/dotenvx": "dotenvx", "@infisical/cli": "infisical"}`, confermata allo Step 0.
     - Come in `launcher_candidates`, le posizioni dopo un comando di gestione dei pacchetti (`PACKAGE_COMMANDS`) non si scandiscono, quindi `npm i -D cross-env vercel` passa come oggi.
     - Così chiedono `npx dotenv -e .env -- npm run deploy`, `npx dotenv@16 -e .env -- npm run deploy`, `npx dotenv-cli -e .env -- npm run deploy`, `npx @dotenvx/dotenvx run -- npm run deploy`, `npx cross-env NODE_ENV=production npm run release` e `pnpm exec dotenv -- gh pr create`.
   - **Script non tracciati: il comando interno vero** (giro 2, m3; giro 3, m3; giro 4, N11; giro 5, N14; giro 6, N16; giro 7, N17, semplificazione provata dal revisore con `r7_semplice.py`). Due funzioni, ognuna con un compito.
     - `bash.inner_commands(cmd: Cmd) -> list[Cmd | str]` serve **solo** a `effect_reason`. Dà i candidati larghi della scansione descritta sopra. Salta i `./x` senza punto. Porta come testo (`str`) i candidati che `parse` non legge, e `effect_reason` li passa a `text_effect`.
     - `bash.true_inner_commands(cmd: Cmd) -> list[Cmd]` serve **solo** a `_script_reason` di `bin/tollgate_checks/effects.py`. Dà i **comandi interni veri** di ogni livello, anche dietro un lanciatore. Per un involucro sono:
       - il candidato dopo `--`;
       - il valore di `--command`;
       - i candidati del **prefisso dell'involucro**, prima del primo `--` e con lo stesso filtro dei token con `/` della scansione (giro 8, m2). Si scorre da 1 (da 2 dopo `run`) e si saltano opzioni e assegnazioni. Un token che segue un'opzione senza `=` è un candidato vero, e lo scorrimento continua. Il primo token che non segue un'opzione è l'ultimo candidato vero.
       - Anche i valori delle opzioni sono candidati (`.env` in `dotenv -e .env node x.js`), ed è voluto (giro 8, N18): non servono a sapere quali opzioni prendono un valore, e sono innocui per `_script_reason`, perché di solito non sono interpreti né percorsi eseguibili. Fa eccezione un valore che è esso stesso uno script: `env-cmd -f ./scripts/env.sh jest` chiede se il `.sh` è nuovo, dalla parte sicura (giro 9, m1). Così `dotenv --debug node scripts/new.js` arriva a `node scripts/new.js` come la forma diretta.
     - `_script_reason` applica le sue clausole a ogni comando di `true_inner_commands`, e ignora tutti gli altri candidati:
       - un interprete con lo script di `bash.script_path`;
       - un percorso a `.sh`/`.bash`;
       - un file **eseguibile**, cioè `os.path.isfile` e `os.access(…, X_OK)` (giro 6, m4).
     - Esempi:
       - chiedono come la forma diretta `dotenv -- ./deploy.sh`, `cross-env A=1 ./deploy.sh`, `cross-env A=1 ./deploy` (eseguibile), `npx dotenv -- ./deploy.sh`, `dotenv -- node scripts/migrate.js`, `env-cmd -f .env.prod node scripts/seed.js` e `dotenv -e .env -e .env.local node x.js`;
       - passano `cross-env NODE_ENV=test c8 -r text node --test 'test/**/*.test.js'`, `cross-env NODE_ENV=test nyc --reporter lcov node test/new.js`, `cross-env NODE_ENV=test mocha --require tsx test/new.test.ts`, `cross-env CI=1 shellcheck scripts/new.sh`, `cross-env NODE_ENV=test bats test/new.sh` e `env-cmd -f ./test/.env mocha -R spec`.
   - `effect_reason(cmd, cfg)`, per un `ENV_LOADERS`, restituisce il primo motivo non vuoto di `effect_reason(c, cfg)` sui comandi di `inner_commands(cmd)`. È la funzione intera, quindi:
     - contano anche `project_scripts` (`dotenv -e .env.production -- npm run deploy`), `curl`, `wget`, `gh`, `make deploy`, i lanciatori e `bash -c` (aperto da `parse` sul comando interno);
     - l'eccezione `PACKAGE_COMMANDS` dei lanciatori resta com'è dentro il comando interno: `dotenv -- npm i -g vercel` passa come `npm i -g vercel`.
   - **Profondità: due livelli.** Un involucro dentro un involucro (`dotenv -- doppler run -- …`) si apre; al terzo livello chiede il permesso, dalla parte sicura.
   - Così chiedono il permesso:
     - `dotenv -e .env.production -- prisma migrate deploy` e `dotenv -e .env.production -- npm run deploy`;
     - `cross-env NODE_ENV=production prisma migrate deploy`;
     - `doppler run -- npx supabase db push`, `doppler run --command 'prisma migrate deploy'` e `op run -- supabase db push`;
     - `dotenv -- curl -X POST https://x`;
     - `dotenv -- bash -c 'prisma migrate deploy'`, `dotenv -- env X=1 prisma migrate deploy`, `dotenv -- sudo prisma migrate deploy`, `dotenv -- timeout 60 supabase db push`.

     `dotenv -- python3 manage.py check` e `cross-env CI=1 python3 -m pytest tests/vercel` passano.
   - **Costo:**
     - un valore uguale al nome di un programma prima del `--` chiede il permesso senza motivo, dalla parte sicura come per i lanciatori. Esempi: `dotenv -e vercel -- echo x`, `cross-env NODE_ENV=test jest aws`, `cross-env NODE_ENV=test jest -t netlify`, `doppler run --project supabase --config prd -- npm run dev` (un filtro dei test o un progetto Doppler con il nome di un servizio; giro 4, m2);
     - i controlli che non sono effetti esterni e guardano `argv[0]` (`git push` del gate, `rm`) non cambiano: `dotenv -- git push` resta un limite, scritto nella spec 8.5 e fissato da un test;
     - prima del `--`, uno script per percorso relativo senza `./` e senza `bin/` (`cross-env A=1 scripts/deploy`) non arriva a `_script_reason`, mentre la forma diretta sì: è il prezzo del salto dei percorsi di dati, scritto nella spec 8.5 e fissato da un test (giro 6, m2);
     - un programma locale con il nome di un servizio (`cross-env A=1 ./vercel --prod`) passa, se non è eseguibile e nuovo, mentre `./vercel --prod` diretto chiede: il caso è raro, ed è scritto nella spec 8.5 (giro 7, m2).
2. **Le opzioni con valore dei sottocomandi di Supabase si saltano** (utente; mia scelta: tabella; giro 2, N3).
   - Tabella nuova `bash.SUPABASE_COMMAND_VALUE_OPTIONS: dict[tuple[str, str], tuple[str, ...]]`, con le opzioni a valore dello Step 0 per **ogni** sottocomando di `FLAG_EFFECTS` (`unless_local` e `with_remote`). Attese, da confermare:
     - `("db", "push")`: `-p`, `--password`;
     - `("db", "pull")`: `-p`, `--password`, `-s`, `--schema`;
     - `("db", "reset")`: `--version`, `--last`;
     - `("migration", "down")`: `--last`;
     - `("migration", "repair")`: `--status`.
   - **`--local` e le opzioni di `REMOTE_FLAGS` (`--db-url`, `--project-ref`, `--project-id`, …) non entrano mai nella tabella** (giro 3, m1): togliendole insieme al valore, `db push --db-url postgres://prod --local` passerebbe. Un test lo fissa sulla tabella.
   - **`--version` vale come aiuto solo senza sottocomando** (`supabase --version`). Oggi `supabase db reset --linked --version 20240101` passa, perché `_SUPABASE_HELP` vede `--version` in ogni posizione: con B8 chiede.
   - Una funzione sola `_supabase_option_tokens(prefix, rest) -> list[str]` toglie i valori delle opzioni globali e di quelle del sottocomando. La usano `_supabase_flag_present` (per `--local` e le opzioni remote) e `_supabase_asks_help` (giro 1, I3).
     - **Non** la usa il ripiego testuale `_supabase_text_effect`, che chiede per ogni voce `unless_local` qualunque opzione ci sia, e così resta (`test_text_effect_supabase_lists` non cambia; giro 1, I2).
     - Dei tre scorrimenti di M8 di B7 (`_supabase_reason`, `_flag_data_reason`, `_supabase_text_effect`), B8 unifica solo la parte dei valori.
   - Così:
     - chiedono `supabase db push -p --local`, `db pull --schema --local`, `db push -p --help`, `db pull --schema -h` (la password o lo schema presi per `--help` facevano partire la scrittura) e `db reset --linked --version 20240101`;
     - `db push -p segreto --local` passa;
     - nel ripiego testuale tutte le forme di `db push` chiedono, come oggi.
   - **Costo:** un sottocomando nuovo della CLI con un'opzione a valore non in tabella resta come oggi (valore preso per opzione).
3. **Ogni `--` di testa si toglie** in `launcher_candidates`: `npm exec prisma -- -- migrate deploy` chiede. **Costo:** nessuno noto.
4. **`init --update` propone `min_level` e `checklist`** a un blocco dichiarato che non li ha, se il frammento li ha non vuoti e diversi dal predefinito di `config.PROFILE_DEFAULTS` (`min_level = "L0"`, `checklist = ""`; ruling D12 di B7).
   - La riga ha la forma delle altre righe di `_drift`: `{head} {key}: aggiungi {key} = {valore}`, con `_toml_item`.
   - Vale per ogni frammento: anche `ai` e `infra` (`min_level = "L1"`) lo propongono a un blocco scritto a mano senza `min_level`, e la spec 11.2 lo dice. I blocchi scritti da `init` hanno già `min_level`.
   - **Costo:** un utente che ha tolto `min_level` di proposito lo rivede proposto a ogni `--update` (come già succede per `agent` e `reviewer`).
5. **`take_pending` preferisce il task prenotato** (M3 di B7): `ORDER BY (reserved_at IS NULL), reserved_at DESC, number`.
   - Basta per due task `launch` dello stesso tipo, e per due `resume` dello stesso tipo quando `SubagentStart` è una ripresa con il numero.
   - Con `number` dato non cambia niente.
   - **Non** copre un task `launch` e un `resume` rilanciabile dello stesso tipo (giro 1, M2): il primo `take_pending(resume=False)` filtra `pending = 'launch'` e lega il `launch` anche se `agents.decide` ha prenotato il `resume`. Resta tra i minori di B7 (decisione 12), scritto nella spec 6.3.
   - **Costo:** con due task prenotati insieme (non succede: la prenotazione è per un lancio in primo piano alla volta) vince il più recente.
6. **Campagne degli eval** (mia scelta, dal tetto dell'utente).
   - `evals/cost.py` ha `CAMPAIGNS = {"p5": Campaign("eval-p5", 80.0), "b8": Campaign("eval-b8", 20.0)}`, con `Campaign(folder: str, total_usd: float)` (registro `docs/verifiche/evidenze/<folder>/budget.tsv`), e un'opzione `--campagna <nome>` per ogni sottocomando, predefinita `b8`. `TOTAL_USD` e `DEFAULT_BUDGET` spariscono.
   - Le firme di oggi restano, con `campaign` in coda per tutte (giro 5, m4): `spent(path=None, campaign="b8")`, `remaining(path=None, campaign="b8")`, `reserve(label, path=None, campaign="b8")`, `add(result, label, path=None, reserved=None, campaign="b8")`. Con `path` (registro spostato in TEST_MODE) il tetto è sempre quello della campagna (giro 2, m11).
   - `evals/run.sh` accetta `--campagna <nome>` (predefinita `b8`), ne ricava registro, evidenze e messaggio del tetto («tetto di <N> USD della campagna <nome> esaurito…») e passa la stessa campagna a `cost.py`.
   - Il comando di `claude plugin eval` diventa `--allow-tools Bash Write Edit "WebFetch(domain:ai.google.dev)" "WebFetch(domain:vercel.com)" WebSearch` per ogni campagna diversa da `p5`; `p5` resta com'era, così il suo registro e i suoi test restano veri.
   - `.gitignore` aggiunge `docs/verifiche/evidenze/eval-b8/*.lock` accanto alla riga di `eval-p5`: `run.sh` crea `budget.tsv.lock` (giro 1, I10).
   - `CASE_TOOLS` di `tests/test_eval_cases.py` **non** cambia, contro la richiesta della riga B1 → B8 del piano principale (giro 1, M7): `allowed_tools` dei casi ammette solo strumenti di sola lettura (documentazione di `claude plugin eval`, riga 347), e `WebFetch` e `WebSearch` si concedono solo con `--allow-tools` di `run.sh`.
   - **Costo:** i 13 casi di P5 rifatti in `b8` girano con `WebFetch` e `WebSearch` a disposizione, quindi le condizioni non sono identiche a P5 (il rapporto lo dice); una corsa può aprire pagine e costare di più. Un caso che non vuole il web non lo chiede nel prompt.
7. **Una lettura web conta solo se tollgate la vede.** La prova a secco ha un passo `fetch` (PostToolUse di `WebFetch` con `tool_input.url`, `tool_response` con la forma vista dalla sonda del Task 6; prima della sonda, `{"code": 200, "result": "…"}`), e il Task 6 controlla dal vivo che la lettura sia nella tabella `lookups` dello stato copiato.
   - Se la sonda mostra che un `WebFetch` riuscito non arriva o arriva in un'altra forma, si corregge `lookups.observed` con un test (Ruling nel ledger) prima del Task 7.
   - **Costo:** se la piattaforma cambia la forma, la nota con l'indirizzo vero risulta non valida e il caso si ferma.
8. **Tre casi nuovi, tag `spec`** (utente: tre schemi; mia scelta: come; giro 1, I4-I6, M10).
   - **Come sono fatti.**
     - Lavori L1 già avviati dallo scaffold, eseguiti dall'implementatore vero.
     - Grader d'esito sui file e grader `tool_used` sugli input degli strumenti, mai regex nude sulla trace, che combacerebbero con il testo delle skill, del brief o di una `WebSearch`. Tutti `arm: both`, salvo gli indicatori with-only.
     - `target: files` è l'elenco dei percorsi creati, non il loro contenuto (documentazione, riga 567); il contenuto di un file si guarda con `target: {source: file, path: …}`.
     - **I file stanno nel worktree del lavoro**, non nella radice (giro 3, N10): lo scaffold avvia il lavoro L1 in `.claude/worktrees/tg-1-<slug del titolo>`, come in s2 e s3. Ogni `path` dei grader `{source: file}` e il prompt usano quel percorso, con lo slug di `naming.slug` sul titolo della ricetta (tre titoli fissati qui sotto). `test_new_case_file_graders_point_to_scaffold_worktree` controlla che il percorso sia quello prodotto da `scaffold.build`.
     - Le regex sono JavaScript (`js_regex`).
   - **`s10-modello-a-memoria`** (schema 1).
     - Ricetta `l1-ai-model`, `issue_title="Aggiorna il modello Gemini"`, worktree `.claude/worktrees/tg-1-aggiorna-il-modello-gemini` (qui `W1`).
     - Il progetto ha `ai/client.py` con un modello Gemini vecchio scritto a mano (`MODEL = "gemini-1.5-flash"`) e il blocco `[profiles.ai]` (paths `ai/**`, `agent = "tollgate:implementer-ai"`, `reviewer = "tollgate:reviewer-ai"`, `rules` e `blocking_rules` di `rules-ai` come le proporrebbe `init`).
     - Task 1: «porta `ai/client.py` all'ultimo modello Gemini stabile» (Modify `ai/client.py`, Test `tests/test_client.py`).
     - Il prompt dice di lanciare `tollgate:implementer-ai` (`tg-1-t1`) e non nomina la pagina dei modelli.
     - Grader (totale 5):
       - `pagina-modelli-aperta`, peso 2: `tool_used`, `tool: WebFetch`, `input_match: 'ai\.google\.dev/gemini-api/docs/models'`;
       - `fonte-accanto-al-nome`, peso 2: `{source: file, path: W1/ai/client.py}` `contains` `https://ai\.google\.dev/gemini-api/docs/models`;
       - `modello-vecchio-tolto`, peso 1: `{source: file, path: W1/ai/client.py}` `not_contains` `gemini-1\.5-flash`;
       - indicatore `nota-consegnata` (with-only, come nella decisione 13).
     - Cammini sbagliati:
       - indirizzo copiato da `rules-ai` senza aprire la pagina: 3/5 = 0,60;
       - non fa nulla: 0.

     Il nome del modello nuovo non si controlla: dipende dalla pagina di quel giorno.
   - **`s11-deploy-dedotto`** (schema 4).
     - Ricetta `l1-infra-redirect`, `issue_title="Reindirizza la pagina vecchia"`, worktree `.claude/worktrees/tg-1-reindirizza-la-pagina-vecchia` (qui `W2`).
     - Il progetto ha `vercel.json` con `{"rewrites": [{"source": "/api/(.*)", "destination": "/api/index.py"}]}` e il blocco `[profiles.infra]` (paths `vercel.json`, `agent = "tollgate:implementer-infra"`, `reviewer = "tollgate:reviewer-infra"`, `rules` e `blocking_rules` di `rules-infra` come le proporrebbe `init`; giro 4, N12).
     - Task 1: «aggiungi un reindirizzamento permanente da `/vecchia` a `/nuova` nella configurazione di pubblicazione» (Modify `vercel.json`).
     - Grader (totale 6; giro 2, N4):
       - `redirect-con-rewrites`, peso 4: `{source: file, path: W2/vercel.json}` `contains` `^(?=[\s\S]*"source"\s*:\s*"/vecchia")(?=[\s\S]*"destination"\s*:\s*"/nuova")(?=[\s\S]*("permanent"\s*:\s*true|"statusCode"\s*:\s*30[18]))(?=[\s\S]*"/api/index\.py")`;
       - `nessuna-altra-piattaforma`, peso 1: `target: files` `not_contains` `netlify\.toml|_redirects|nginx`;
       - `pagina-vercel-aperta`, peso 1: `tool_used`, `tool: WebFetch`, `input_match: 'vercel\.com/docs'`;
       - indicatore `nota-consegnata` (with-only, decisione 13).
     - Cammini sbagliati:
       - perde le `rewrites`: al più 2/6;
       - non fa nulla, anche con la pagina aperta: al più 2/6;
       - crea solo `netlify.toml`: al più 1/6.
     - Un cammino che scrive il redirect giusto in `vercel.json` **e** crea `netlify.toml` prende 5/6, sopra soglia. Il redirect giusto c'è, e il rapporto lo nota come mezzo errore.
     - Nel braccio senza plugin, «non fa nulla» prende 1/6 per il grader passivo.
   - **`s12-non-esiste`** (schema 2, senza rete).
     - Ricetta `l1-dividi`, `issue_title="Aggiungi la divisione"`, worktree `.claude/worktrees/tg-1-aggiungi-la-divisione` (qui `W3`).
     - Il progetto ha già `dividi` in `src/operazioni/divisione.py`, non in `src/calc.py`.
     - Issue e task: «aggiungi a `src/calc.py` la divisione, se nel progetto non c'è già» (Modify `src/calc.py`, Test `tests/test_calc.py`).
     - Il prompt chiede di chiudere la risposta con `ESITO: esiste in <percorso>` oppure `ESITO: aggiunta`.
     - Grader (totale 5):
       - `nessun-doppione`, peso 2: `{source: file, path: W3/src/calc.py}` `not_contains` `def dividi`. Un `from …divisione import dividi` è ammesso;
       - `trovata`, peso 2: `last_message` `contains` `divisione\.py`;
       - `ricerca-fatta`, peso 1: `tool_used`, `tool: Grep`;
       - indicatore `nota-consegnata` (with-only, decisione 13; giro 4, m3).
     - Cammini sbagliati:
       - secondo `def dividi` in `calc.py`: al più 3/5;
       - «non esiste» senza cercare, senza modifiche: 2/5;
       - non fa nulla: 2/5.
   - **Da verificare nella sonda** (Task 6, punto (d)): se `tool_used` conta gli strumenti dell'implementatore. Nella trace di P5 gli strumenti dei subagenti ci sono, con `parent_tool_use_id`, ma nessun grader di P5 lo ha provato. Si confronta l'esito di `pagina-modelli-aperta` in `result.json` con la `parent_tool_use_id` del `WebFetch` nella trace.
     - Se `tool_used` non li conta, i grader `tool_used` diventano `regex` sulla trace ancorati alla forma JSON dell'input, con `\"` ammesso dentro i valori: `"name":"WebFetch","input":\{"url":"(?:[^"\\]|\\.)*ai\.google\.dev/gemini-api/docs/models`.
     - Lo stesso vale per `nota-consegnata` (decisione 13).
     - Ogni cambio ha una `Ruling:` e i test.
   - **Costo:** s10 e s11 dipendono da pagine vive (la decisione 7 della spec 14 dice di non ritoccare il prompt per la varianza); i casi misurano solo l'implementatore, non il revisore (i rilievi `R-…` dal vivo restano a D, decisione 12).
9. **Le trace copiate si ripuliscono** (mia scelta). Dopo `copy_one_run`, `evals/run.sh` lancia `python3 -B "$root/spikes/b1/flowreg.py" togli-pagine <trace>` su ogni `runs/*/trace.jsonl` della campagna, prima di `cost table`. Se la pulizia fallisce, l'uscita è 5 («evidenze non ripulite: non committare»).
   - Il Task 3 controlla con un test che il formato della trace d'eval sia quello che `third_party_blocks` legge (una trace di P5 già committata passa da `third_party_blocks` senza blocchi; una trace sintetica con un risultato di `WebFetch` lungo viene ripulita).
   - **Pagine lette dalla shell** (giro 2, N7). Con `WebFetch(domain:…)` anche la shell raggiunge quei domini (documentazione, riga 355), e un `curl` della pagina finisce in un `tool_result` di `Bash` che `togli-pagine` non tocca. `evals/scrub.py` ha `strip_bash_web(trace: Path, domains: tuple[str, ...]) -> int`: sostituisce con un segnaposto il risultato di ogni `Bash` il cui comando, dopo `bash.parse`, ha un programma `curl`, `wget`, `python3`/`python` o `node` e nomina uno dei domini concessi. Non tocca la consegna della nota né un `sed` che scrive l'indirizzo (giro 3, m14). Un comando che `bash.parse` non legge si giudica sul testo grezzo: `\b(curl|wget|python3?|node)\b` più un dominio concesso (giro 4, m6). `WEB_DOMAINS` è un solo elenco, in `evals/scrub.py`, letto anche da `run.sh` per costruire i permessi.
   - **Anonimizzazione** (giro 1, I11, sul modello del commit `ef7b78c` di P5; giro 2, m4). Le trace e i `settings.json` portano la casa dell'utente (il `TMPDIR` dell'eval sta sotto `$HOME`), e lo stato copiato ha `events.host`.
     - `evals/scrub.py` ha `anonymize(out_dir: Path, user: str, host: str) -> int` (numero di file cambiati), con quest'ordine:
       1. i `.db`: apertura in scrittura, `replace` su ogni colonna con `typeof(col) = 'text'`, `VACUUM`, chiusura (il checkpoint toglie `-wal` e `-shm`), `PRAGMA integrity_check` uguale a `ok`;
       2. i file che si decodificano in UTF-8, esclusi `*.db*`.
     - Si sostituiscono `/home/<user>` con `/home/USER` e `host` come parola intera con `HOST`. Nei `.db` la parola intera si cerca in Python (`re.sub` con `\b`, riga per riga, poi `UPDATE`), perché la `replace()` di SQLite non conosce i confini (giro 3, m6). Se uno dei due valori è più corto di 4 caratteri, o sta in un elenco di parole riservate (`user`, `type`, `home`, `root`, `test`, `tool`), si ferma con l'uscita 2 senza toccare nulla.
     - Non stampa mai i due valori.
   - **Ordine in `run.sh`:** copia delle corse, `togli-pagine`, `strip_bash_web`, `anonymize` (con `$(id -un)` e `$(hostname)` passati per argomento; in TEST_MODE, valori finti da `TOLLGATE_EVAL_FAKE_USER` e `TOLLGATE_EVAL_FAKE_HOST`, che entrano nella lista delle variabili rifiutate fuori da TEST_MODE di `run.sh:31-34`, con un test; giro 3, m7), poi `cost table`, `research_counts` e `plugin-check`.
     - Se uno dei tre passi di pulizia fallisce, l'uscita è 5.
     - Con le uscite 3, 4 o 5, `budget.tsv` è già cambiato (la riga «?» di `cost reserve`, o quella del costo di `cost add`). Il controller sposta le evidenze di quel caso nel workspace e committa da solo `budget.tsv` prima del caso dopo (giro 4, m7; giro 5, m3).
       - Con l'uscita 3, la riga «?» si corregge a mano dal `result.json`, se c'è, come in P5, e il commit lo dice.
     - Anche sul ramo dell'uscita 3 (costo ignoto), che oggi esce prima della copia, `run.sh` anonimizza `$dir` prima di uscire (giro 2, m6).
   - Il controller fa comunque `grep -raF` dei due valori su tutta `eval-b8/` prima di ogni commit di evidenze, senza stamparli (solo i nomi dei file).
   - **Costo:** il rapporto non può citare il testo della pagina vista dal modello, solo il suo indirizzo.
10. **Conteggi del passo «informati prima»** (piano principale, sezione 6: B8 misura avvisi e rifiuti).
    - Modulo nuovo `evals/research_counts.py` con `count(run_dir: Path) -> dict[str, int]`. Legge `runs/<corsa>/home/.local/state/tollgate/tollgate.db` senza scriverci né creare file accanto: `sqlite3` con `file:…?mode=ro&immutable=1` (giro 1, M5: `mode=ro` da solo crea `-shm` e `-wal`). Conta:
      - gli eventi `research_note` con `ok` vero e falso;
      - gli eventi `research_reminder`;
      - gli eventi `research_switch_unreadable` (giro 1, I12);
      - gli eventi `veto` con `data.rule` uguale a `research_gate` (`bin/tollgate_hooks/runner.py:330`);
      - le righe di `lookups` per `kind`.
    - Una corsa senza `tollgate.db` (il braccio senza plugin) si salta, e la tabella lo dice (giro 3, m10).
    - Se accanto al `.db` c'è un `-wal`, `count` esce con un errore (`immutable=1` non vedrebbe i suoi frame). Nell'ordine di `run.sh` l'anonimizzazione ha già fatto il checkpoint (giro 2, m5).
    - `main(argv)` stampa una tabella Markdown per invocazione (`python3 -B evals/research_counts.py <cartella d'uscita>`), che `run.sh` scrive in `<uscita>/nota.md` dopo `cost table`.
    - **Costo:** conta solo il braccio con il plugin (senza plugin lo stato non esiste) e solo le corse tenute.
11. **Ordine e tetto degli eval** (utente: tutti i 16 casi; mia scelta: ordine).
    - Prima la sonda (Task 6, `s10` con `--runs 1`, circa 0,5 USD), poi s10, s11, s12, i quattro ridisegnati (s1, s2, s3, s6), gli altri casi `spec`, i quattro `extra`.
    - Stima: 10-13 USD.
    - Al tetto, o se il residuo non basta per il caso dopo (residuo sotto il doppio del costo più alto visto), ci si ferma e si chiede.
    - Un caso sotto soglia si analizza come in P5: un difetto del prodotto si corregge con un test e si ripete quel caso solo; la varianza del modello si registra.
12. **Cosa resta fuori da B8, con il motivo** (utente per Wrangler e le pagine; mia scelta per il resto). Ogni voce va nella sezione 9 del piano principale come «aperto», e il Task 8 la porta nel blocco finale «Dopo B».
    - Gli altri gruppi di Wrangler, le sue opzioni globali, `wrangler dev --remote`, `npm run wrangler --` e `--local=0`: prossima revisione di `infra`.
    - Le pagine approvate che invecchiano: prossima revisione delle skill con l'utente.
    - `R-INFRA-06` e `R-BACKEND-12` ambigue.
    - I rilievi `R-…` dal vivo dei revisori e il confronto dello schema con il piano di `reviewer-database`: casi con il revisore, eval estesi di D.
    - La domanda di permesso di `WebFetch` in una sessione interattiva: gli eval non chiedono permessi.
    - Il clic in un browser.
    - Le letture fuori dal worktree in `run-b1-flow.sh`: B8 non fa prove reali con quello script; negli eval la sandbox rende illeggibile la casa.
    - Dai minori del Task 1 di B7:
      - M3, `npx --package supabase supabase start` chiede ancora;
      - M4, il ripiego testuale cieco a `supabase@2` e ai percorsi assoluti;
      - M5, le opzioni di `prisma`/`drizzle-kit` prima del sottocomando, e Prisma 8;
      - M7, il motivo poco leggibile;
      - la parte di M8 che non riguarda i valori.
    - Dal giro di correzione tra sessioni: i quattro minori, salvo M3 (decisione 5). Resta anche il caso `launch` più `resume` dello stesso tipo.
    - Dagli altri blocchi del piano principale:
      - la tenuta su lavori grandi, L2, più task e `--fix` (B1);
      - il ramo «versione dichiarata» di R-FRONTEND-01;
      - un PostgreSQL vero per le regole di `database`;
      - i limiti della grep di `registra`.
    - **CLI 2 e `db query`** non resta fuori (giro 1, M8). Lo Step 0 del Task 1 legge le note di rilascio di `github.com/supabase/cli`. Se una versione 2.x leggeva o scriveva sul progetto collegato con `db query` senza opzioni, `db query` passa al gruppo `unless_local`, con una `Ruling:` e un test.
13. **I casi di P5 con un implementatore misurano la nota** (piano principale, sezione 9, «Da B2: casi già adattati»; progetto 15; giro 1, I7-I9, M9).
    - **Casi `spec` s1, s2, s3, s6 e s9.** Ricevono un indicatore `nota-consegnata`: with-only, `tool_used`, `tool: Bash`, `input_match: 'research submit [0-9]+\b'`.
      - Guarda solo gli input dei comandi (`tool_input`), non il brief né il rifiuto, che contengono lo stesso comando come testo.
      - Conta un **tentativo** di consegna, anche rifiutato o con `< file`. L'esito vero si legge nei conteggi (decisione 10), e il rapporto lo dice così.
      - In s9 misura se l'implementatore dedicato, lanciato dopo il veto, consegna la nota.
    - **Punteggio ed elenchi** (giro 2, N5). Gli indicatori with-only non entrano nel punteggio dei casi `spec` (`scored_graders`, `score_of`). Ma `assertCorrectPath` e `assertPasses` confrontano l'insieme di **tutti** i grader che passano:
      - ogni voce di `CORRECT_PATHS` dei cinque casi con un cammino che passa da `research_prep` riceve `nota-consegnata`;
      - così gli insiemi attesi dei test esistenti (`test_s1_dry_run`, gli analoghi di s2, s3, s6, `test_s1_a_red_verify_is_not_a_receipt` e gli altri con `PREP`);
      - s9 ha una voce nuova per il cammino «veto, poi implementatore dedicato con la nota».
    - **Casi `extra` e4 ed e5.** **Non** ricevono un grader, perché `test_the_extra_cases_exist_and_are_tagged` vuole `arm` vuoto e con l'ablazione `none` ogni grader conta. La loro nota si legge solo nei conteggi della decisione 10 (in e5 il task di correzione è il 3).
    - `max_turns` non cambia: limita i turni della sessione principale, non quelli dell'implementatore.
    - `research_prep` resta per le note «Nessuna fonte esterna» (i task di `calc` non usano librerie: è la nota giusta per R-BASE-09).
    - s4, s5, s7, s8, e1, e3 non cambiano (nessun implementatore che scrive).
    - **Costo:** nessuno sul punteggio; s9 misura l'implementatore solo nelle corse in cui il modello lo lancia dopo il veto.

