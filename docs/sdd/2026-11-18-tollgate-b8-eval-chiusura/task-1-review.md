# Revisione Task 1 (B8), commit f48919b

### Aderenza
- ✅ Decisione 1: `ENV_LOADERS` (con `cross-env-shell`), `LOADER_PACKAGES` (solo dotenv-cli e @dotenvx/dotenvx), `inner_commands` / `true_inner_commands`, profondità 2 (il terzo involucro chiede, `bash.py:_loader_reason`), candidati illeggibili da `text_effect` con ripiego «chiede», `allow`/`commands` sul testo esterno prima degli interni, `--command` di doppler, `--command` e `-c` di infisical, `infisical sm|secrets-manager run`, `cross-env-shell` e `env-cmd --use-shell` con `" ".join`. Filtro dei token con `/` (`_command_path_ok`) come scritto, con `./x` senza punto solo per `_script_reason`.
- ✅ Decisione 2: tabella `SUPABASE_COMMAND_VALUE_OPTIONS` uguale a `task-1-fatti.md` (tutti i sottocomandi di `FLAG_EFFECTS`; un test controlla che ogni prefisso supabase sia in tabella), mai `--local` né `REMOTE_FLAGS`; `_supabase_option_tokens` unica, usata da `_supabase_flag_present`, `_strip_value_options`, `_supabase_asks_help`; `--version` è aiuto solo prima di ogni sottocomando; il ripiego testuale non cambia.
- ✅ Decisione 3: `launcher_candidates` toglie ogni `--` di testa (`while`).
- ✅ D8: due paragrafi in `docs/uso/limiti.md` sotto «### Gli effetti esterni», niente percorsi assoluti. D3 (git push / rm dietro involucro) fissato da `test_git_push_behind_env_loader_unchanged`.
- ✅ Strati: nessun import nuovo in `bash.py` (solo stdlib); `test_layers` verde (rieseguito con test_bash e test_check_effects: 165 test OK in 8 s).
- ✅ Test del brief tutti presenti (elenco Step 1 confrontato voce per voce); `test_check_effects` crea i file con `0o644`/`0o755` e controlla l'esito, quindi asserisce davvero.
- ⚠️ `dotenv -- "supabase db push"` (comando come unica stringa, senza `--use-shell`) passa: `shlex.join` lo quota e `parse` lo legge come un programma dal nome con spazi. Dai fatti ufficiali la forma è un comando eseguito direttamente, quindi non parte; non posso confermarlo senza rete. Se un involucro lo passasse a una shell sarebbe un buco, da verificare dal controller (non è nei fatti).

### Prove mirate (python3 -B su `bin/` del worktree, script `probe_r1.py` in W)
- Chiedono tutte le forme del Review Focus 1 e quelle dietro `env`, `sudo`, `nohup`, `command`, `exec`, `xargs`, `nice`, `time`, `bash -c`, `eval`, `npx`/`pnpm dlx`/`bunx`/`yarn`/`npm exec --`, doppio `--`, con `dotenvx run -f`, `doppler --token x run`, `op run --env-file=…`, `infisical sm run`. Il terzo involucro (anche via `npx`) chiede.
- Passano le forme innocue richieste (`dotenv -- python3 -m unittest`, `npm i -g vercel`, `supabase db push -p x --local`, `cross-env CI=1 python3 tools/build.py`) e quelle comuni (`next dev`, `next build`, `jest --coverage`, `npx prisma generate`, `doppler run -- npm run dev`, `op run -- ./scripts/dev.sh`).
- Costi oltre quelli scritti: nessuno trovato. Chiedono come da decisione 1 `dotenv -e vercel -- echo x` e `doppler run --project supabase …`; stessa famiglia `op item get vercel` (il nome di un servizio come argomento di `op`, `doppler`, `infisical` fuori da `run`): rientra nel costo «valore uguale al nome di un programma», non è scritto per i sottocomandi non `run`.
- Supabase: `-p --local`, `--schema --local`, `--diff-engine --local`, `-p --help`, `--db-url x --local`, `--local=false`, `db -p x push --local` chiedono; `db dump -f --linked`, `db reset --last --linked`, `db lint -s --linked` passano, coerente con pflag (il valore consuma il token) e con la tabella dei fatti.

### Punti di forza
- Base comune `_launcher_hits` per lanciatori e involucri: nessuna logica duplicata.
- `true_inner_commands` separata da `inner_commands`, come da decisione: `_script_reason` non guarda i valori di dati e di test.
- Test per appartenenza (`test_true_inner_commands`) e non per uguaglianza di liste intere dove la scansione è larga; casi di costo e limiti fissati da test.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor:**
- `bin/tollgate_analysis/bash.py:1093` `_SUPABASE_HELP` non è più usata da nessuno (verificato con grep): togliere la costante, il nuovo `_supabase_asks_help` ha le stringhe inline.
- `bash.py:_supabase_asks_help`: `("--help", "-h")` e `"--version"` sono ora scritte a mano; se si toglie `_SUPABASE_HELP`, una costante `_SUPABASE_HELP = ("--help", "-h")` usata qui eviterebbe la duplicazione.
- Il report dichiara due scostamenti dal prototipo (candidato illeggibile che chiede; terzo involucro che chiede invece del quarto): entrambi sono la lettura letterale della decisione 1 e vanno bene. Il testo di `limiti.md` dice «il terzo involucro annidato chiede sempre»: coerente.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti delle decisioni 1-3 e di carry.md implementati e provati con forme nuove senza trovare un comando che scrive passare né un innocuo che chiede oltre ai costi scritti; test asseriscono l'esito voluto e gli strati sono rispettati. Restano due minori di pulizia e un ⚠️ sul comando passato come unica stringa.
