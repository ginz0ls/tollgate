# Decisioni del controller da portare nei task (prevalgono sul testo del piano)

## Task 1
- Fatti dello Step 0 in `task-1-fatti.md` (elenco vincolante).
- `ENV_LOADERS` = `("dotenv", "dotenvx", "cross-env", "cross-env-shell", "env-cmd", "doppler", "infisical", "op")`.
- `cross-env-shell`, ed `env-cmd` con `--use-shell`: il comando interno è testo di shell, quindi i candidati si costruiscono **anche** con `bash.parse(" ".join(<parole>), cmd.cwd)` (oltre a `shlex.join`). Test: `cross-env-shell "prisma migrate deploy && echo ok"` e `env-cmd -f .env --use-shell -- "npm run build && supabase db push"` chiedono; `cross-env-shell "jest && echo ok"` passa.
- Opzioni «comando da eseguire»: `doppler --command` (anche `--command=…`; `-c` di doppler è `--config` e non conta); `infisical --command` **e `-c`** (anche `--command=…`). Nessuna per gli altri. Test: `infisical run -c 'prisma migrate deploy'` chiede; `doppler run -c prd -- jest` passa.
- Infisical: anche `infisical sm run …` e `infisical secrets-manager run …`; in `true_inner_commands` lo scorrimento del prefisso parte dopo `run` dovunque sia (posizione 1, 2 o 3). Test: `infisical sm run -- prisma migrate deploy` chiede.
- `LOADER_PACKAGES = {"dotenv-cli": "dotenv", "@dotenvx/dotenvx": "dotenvx"}` (niente `@infisical/cli`: nessuna pagina ufficiale). Un test fissa l'esito di oggi di `npx @infisical/cli run -- prisma migrate deploy` (qualunque sia) e il report lo dice.
- `SUPABASE_COMMAND_VALUE_OPTIONS` con l'elenco intero di `task-1-fatti.md` (tutti i sottocomandi di `FLAG_EFFECTS`, anche `with_remote`), mai `--local`, `--remote` né una voce di `REMOTE_FLAGS["supabase"]`. In più dei test del piano: `supabase migration repair -p --local --status applied 1` chiede; `supabase db pull --diff-engine --local` chiede; `supabase db dump -f --linked` passa (il valore è il nome del file).
- D3: `test_git_push_behind_env_loader_unchanged` fissa anche `dotenv -- git push --force origin x` (non è un force push per `parse`) e `dotenv -- rm -rf /tmp/x` (non visto dai controlli su `argv`): limite scritto.
- D8: le due righe di documentazione (involucri dell'ambiente; opzioni con valore dei sottocomandi di Supabase) vanno in `docs/uso/limiti.md`, nel corpo sotto «### Gli effetti esterni» (titolo invariato), non in `docs/uso/comandi.md`. Nessun percorso assoluto né `/home/` nella pagina.
- D13: `Lab` è `tests.hookkit.Lab`.

## Task 2
- D1: in `tests/test_init.py` `DECLARED_X` riceve `min_level = "L1"` (come `FRAGMENT_X`); nessuna asserzione esistente si tocca o si indebolisce. I test nuovi partono da un blocco senza `min_level`.
- D14: test in più in `tests/test_tasks.py`: due task dello stesso tipo prenotati entrambi, vince il più recente (`reserved_at` maggiore).

## Task 3
- D4: `evals/scrub.py` ha anche `strip_web_results(trace: Path) -> int` (numero di risultati sostituiti): sostituisce **ogni** risultato di `WebFetch` e `WebSearch` della trace, nel blocco `tool_result` e in `tool_use_result`, di qualsiasi lunghezza, con un segnaposto che tiene l'indirizzo (o l'interrogazione) e la forma: chiavi, `code`, numeri e booleani restano, ogni stringa di testo diventa il segnaposto. Ordine in `run.sh`: copia, `togli-pagine`, `strip_web_results`, `strip_bash_web`, `anonymize`; se uno fallisce, uscita 5. Test: un `WebFetch` di 1000 caratteri e un `tool_use_result` strutturato di `WebSearch` (`results` con titoli e frammenti) spariscono; una trace di P5 committata resta uguale.
- D5: passano a `--campagna p5` (o `campaign="p5"`) senza cambiare i numeri attesi: `tests/test_eval_run.py` `test_max_cost_is_remaining` (~:217), `test_preamble_prints_paths_and_test_mode` (~:413), `test_dry_run_in_test_mode_touches_nothing` (~:456), `test_dry_run_ignores_held_lock` (~:476), `test_prints_command_and_residual` (~:483), `CostTest.test_remaining` (~:585), `test_remaining_cli_rounds_down_to_cents` (~:600), `test_reserve_then_add_replaces_row_atomically` (~:658).
- D6: in TEST_MODE `run.sh` non chiama `id` né `hostname`: `${TOLLGATE_EVAL_FAKE_USER:-utente-prova}`, `${TOLLGATE_EVAL_FAKE_HOST:-macchina-prova}`. Fuori da TEST_MODE `$(id -un)` e `$(hostname)`, e le due variabili sono rifiutate (con il test delle variabili rifiutate).
- D7: `run.sh` legge cartella e tetto della campagna da `python3 -B evals/cost.py info --campagna <nome>` e i domini da `python3 -B evals/scrub.py domains` (uno per riga). Test: `test_grants_follow_web_domains` e uno gemello sulla cartella della campagna.
- D9: `_do_fetch` della prova a secco fa come `_do_read`: `_use("WebFetch", {"url": …}, agent)`, il `PostToolUse` con `tool_response` `{"code": 200, "result": "…"}`, poi `_result`.
- D12: in `docs/uso/eval-e-ci.md` nessun link al rapporto di B8 (non esiste ancora); aggiorna il conto dei casi e il tetto.
- D16: `research_counts.count` su uno stato senza tabella `lookups` (o `events`) dà zero, non un errore.

## Task 4
- D15: i blocchi `[profiles.ai]` e `[profiles.infra]` delle ricette usano i percorsi che propone `init` (`paths = ["/ai/**"]`, `paths = ["/vercel.json"]`, con la barra); test `test_new_case_profile_blocks_match_init`: `paths`, `agent`, `reviewer`, `rules`, `blocking_rules` del `tollgate.toml` della ricetta uguali a `init.profile_blocks` sul plugin vero.
- D9: il passo `fetch` registra la `tool_use` (vedi Task 3).

## Task 5
- D2: i cinque casi sono s1, s2, s3, s6, s9. Insiemi da aggiornare secondo lo scan (preflight-scan.md, punto 8 della sezione 6).

## Task 6
- D4: punto (b2) della sonda: la forma di un risultato di `WebSearch` (solo chiavi), se il modello l'ha usata.

## Task 8
- D2: correggi PP:288 (s9 cambia) e la sezione 9 del piano principale.
- D3, D10: spec 8.5 con il limite intero degli involucri (controlli su `argv[0]`) e la differenza di `./deploy` non eseguibile.
- D17: cambia **insieme** il titolo in grassetto della spec 1.2 e il `###` di `docs/uso/limiti.md` sugli eval «senza rete» in un titolo vero (rete limitata ai domini concessi da `run.sh`), e i rimandi (cercali con grep); `test_limits_match_spec_1_2` resta verde.
- D12: il link al rapporto di B8 in `docs/uso/eval-e-ci.md`.
- Dopo la sonda e gli eval (ruling nel ledger), da scrivere dove indicato:
  - spec 14 e `docs/uso/eval-e-ci.md`: `WEB_DOMAINS` sono tre (`ai.google.dev`, `aistudio.google.com`, `vercel.com`); i casi `spec` sono dodici (s1-s12), gli `extra` quattro eseguiti (e1, e3, e4, e5) più e2 a secco come in P5 (controlla nel codice); il rapporto di B8 accanto a quello di P5 (link solo ora che esiste: `docs/verifiche/2026-11-18-b8-eval.md`).
  - spec 14 e 16: i fatti della sonda (righe `Sonda:` del ledger, in breve) e il **limite della piattaforma**: in Claude Code 2.1.328 la sandbox degli eval rende di sola lettura `.git/worktrees/`, gli implementatori non possono fare il commit; cinque casi sotto soglia per questo (s1, s3, s6, e3, e4); nessun aggiramento nel kit.
  - spec (dove descrive `lookups.observed`, decisione 7 e 6.x/18.x secondo dove sta oggi): un `WebFetch` con `code` fuori da 200-299 o con un `result` che comincia con l'avviso di redirect non conta come lettura.
  - spec 1.2 (titolo e testo, D17) e `docs/uso/limiti.md`: la shell e `WebFetch` raggiungono solo i tre domini concessi da `run.sh`, `WebSearch` è concessa.
  - piano principale, blocco «Dopo B»: (1) la regola mancante di `rules-base` emersa da s12 («cerca nel progetto prima di aggiungere», che blocchi), scelta dell'utente del 19/11: alla prossima revisione delle skill; (2) il limite della sandbox di Claude Code 2.1.328 sui commit negli eval (rifare s1, s3, s6, e3, e4 quando la piattaforma lo permette, o un aggiramento nel kit da decidere); (3) l'elenco unico delle pagine approvate che invecchiano: quelle della decisione 12 e del Task 8 Step 3 (`backend.md` due frasi, `frontend.md`, `infra.md` due frasi, `ai.md`, `frontend-fonti.md`: trova le frasi esatte nel piano principale, sezione 9, e nel progetto) **più** `skills/rules-ai/SKILL.md` e `docs/profili/ai.md` se citano `https://ai.google.dev/gemini-api/docs/models` (la pagina oggi rimanda con un 301 a `https://aistudio.google.com/docs/models`; verifica con grep, senza toccare quei file); (4) i minori rinviati che la revisione finale dirà (li aggiunge il controller dopo).
  - rapporto e progetto di B: s9 è uno dei cinque casi con la nota (D2).
