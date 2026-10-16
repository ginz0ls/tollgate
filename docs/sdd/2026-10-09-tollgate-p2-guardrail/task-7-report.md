# Task 7 - Analisi: comandi Bash

**Status:** DONE_WITH_CONCERNS
**Commit:** 8ca1a65 tollgate P2: lettura e classificazione dei comandi Bash

## Implementato

- `bin/tollgate_analysis/bash.py`: `BashParseError`, `Cmd`, `parse`, `git_call`, `effective_dir`, classificatori git (push, commit, checkout, branch, worktree, merge, branch -d), `destructive`, `rm_rf_targets`, `write_targets`, `writes`, `is_claude`, `is_tollgate_hook`, `uses_tollgate_bin`, `EffectsCfg`, `effect_reason`, `normalized`, `script_path`, `text_danger`. Solo libreria standard più `from . import globs`. Nessun import di `tollgate_core`, `tollgate_hooks` o `tollgate_checks`.
- `tests/test_bash.py`: i test del brief, più i test delle decisioni di `carry.md` (C7b, C7c, C7d) e il ripiego sul testo.
- I pattern di `effect_reason` usano `globs.match` (non `globs.compile`), come da regola dei task precedenti.

## Decisioni di carry.md (ognuna con il suo test)

- **C7b, `-c` nei flag combinati**: `_shell_command` riconosce `-c` in qualunque gruppo di flag corti (`bash -lc`, `sh -ec`, `bash -ic`) e salta `-o <opt>`. Test: `ParseCarryTest.test_c_flag_in_combined_shell_flags`, `test_shell_without_c_is_not_a_command_string`.
- **C7c, `git commit -n`**: equivale a `--no-verify`, anche nei gruppi corti (`-nm`). `-am` non conta. Test: `ParseCarryTest.test_commit_n_is_no_verify`.
- **C7d, redirezioni numerate**: un token numerico seguito da `<` o `>` viene scartato (`2>&1`, `2>/dev/null`, `1>x`). `cp a b 2>&1` ha bersaglio `b`, `rm -rf build 2>/dev/null` ha argv `["rm","-rf","build"]`. Test: `ParseCarryTest.test_numbered_redirects_leave_no_spurious_argument`.

## Scostamenti dal piano e perché

1. **Heredoc non chiuso**: il piano lo consumava in silenzio fino alla fine del testo. Ora solleva `BashParseError`, così il chiamante ripiega sul testo e non lascia passare il comando in silenzio (Review Focus 1). Test: `test_unparsable_falls_back_to_text`.
2. **Here-string `<<<`**: il regex del heredoc lo scambiava per un heredoc (`cat <<< 'x'` avrebbe cercato il delimitatore `x`). Ora il lookbehind/lookahead esclude `<<<`.
3. **`_matches`**: il piano usava `fnmatch.fnmatchcase`; ora usa `globs.match`, come da regola dei task precedenti. Il confronto esatto e per prefisso di parola (`text == p or text.startswith(p + " ")`) è rimasto.
4. **`git_call`**: `-C` è gestito solo dal ramo dedicato; l'ho tolto da `_GIT_OPT_ARG`. Comportamento invariato.

## Test ed esiti

- Prima di `bash.py` (solo test): `python3 -B -m unittest tests.test_bash` → `FAILED (errors=1)`, errore di import del modulo mancante.
- Mutazione di verifica (copia scratch con le tre correzioni di carry annullate): `python3 -B -m unittest tests.test_bash` → `FAILED (failures=5)`:
  - `test_c_flag_in_combined_shell_flags` (bash -lc, sh -ec, bash -ic: 3 sottotest)
  - `test_commit_n_is_no_verify`
  - `test_numbered_redirects_leave_no_spurious_argument`
  Quindi ogni decisione di carry ha un test che la discrimina.
- GREEN: `python3 -B -m unittest tests.test_bash -v` → `Ran 21 tests` / `OK`.
- `tests/run`, python 3.11.16: `Ran 268 tests in 1.481s` / `OK`.
- `tests/run`, python 3.13.5: `Ran 268 tests in 1.491s` / `OK`.
- 268 = 247 precedenti + 21 nuovi. Nessun `__pycache__` (sempre `-B`); `git status` pulito dopo il commit.

## File cambiati

- `bin/tollgate_analysis/bash.py` (nuovo)
- `tests/test_bash.py` (nuovo)

## Autorevisione

- Completezza rispetto al brief e a carry: tutti i valori e i casi del brief presenti; C7b, C7c, C7d coperti con test.
- Verificata la chiamata nel caso `echo $(echo $(git push --force origin x))`: il comando reale viene trovato dal parse annidato.
- Verificato `echo a \` (backslash finale): `BashParseError`, e `text_danger` restituisce `None` perché non c'è nulla di pericoloso nel testo.

## Dubbi e limiti (da decidere nel controllo)

1. **Artefatti dei `$(...)` annidati**: la lettura esterna lascia nell'argv della shell esterna dei token spuri (`$`, `))`). Il comando annidato viene comunque trovato e il controllo non si rompe, ma un test sull'argv esterno può vedere quei token. Il regex `_SUBST` non gestisce più livelli di parentesi. Non l'ho risolto perché il piano non lo richiede e cambierebbe la tokenizzazione.
2. **Pattern con `/` in `commands` e `allow`**: `globs.match` tratta `*` come non attraversante `/`. Un comando dichiarato come `npm run deploy/*` o con un argomento percorso potrebbe non corrispondere: nel caso di `commands` si perde un effetto, nel caso di `allow` l'eccezione non si applica (fail-safe). Da verificare nel Task 16 con i casi reali.
3. **Ripiego sul testo**: `text_danger` è il ripiego previsto dal piano; la sua chiamata nei controlli dei Task 16 e 17 non è ancora cablata.

## Fix round 1

**Commit:** 237b1de tollgate P2: analisi Bash, heredoc in $(...), punteggiatura, wrapper, gh/curl (fix round 1)

Ogni punto ha prima il suo test (RED, 32 fallimenti e 2 errori su 34 test di `tests/test_bash.py`), poi la correzione (GREEN).

### Important
1. **Heredoc in `$(...)`** (`bash.py`, `_split` e `_balanced`): il vecchio strip esterno consumava la riga `EOF` prima che `$(...)` venisse isolato. Ora il testo viene scandito una volta sola: `$(...)` si estrae con bilanciamento delle parentesi (saltando virgolette e corpi di heredoc) e viene analizzato a parte; il corpo di un heredoc viene tolto solo a livello esterno. `git commit -m "$(cat <<'EOF'...)"` si analizza; con `&& git push --force` il push forzato è un comando di primo livello (`nested=False`). Un heredoc quotato con `$(git push -f)` nel corpo resta dato, non comando. Test: `FixRound1Test.test_commit_with_heredoc_in_substitution_parses`, `test_commit_heredoc_then_forced_push_is_seen`, `test_quoted_heredoc_body_is_data_not_command`.
2. **Pattern di comandi** (`_matches`): ora `fnmatch.fnmatchcase`, quindi `*` attraversa `/`, come da decisione del controller. `globs` non è più importato in `bash.py`. Test: `test_command_patterns_cross_slash_and_allow_applies` (`./scripts/deploy.sh *` corrisponde a `./scripts/deploy.sh a`; `allow` con `/` si applica).
3. **Punteggiatura fusa**: `_ops` spezza i token di sola punteggiatura negli operatori noti (`);`, `)&&`, `&&(`), lasciando intatti i token con redirezioni (`>&`, `&>`). Test: `test_punctuation_tokens_are_split` con i sette casi del controller.
4. **Opzioni dei wrapper**: tabella `_WRAP_ARGS` con le opzioni che prendono un argomento (sudo, env, nice, timeout, xargs, stdbuf, time, exec). Test: `test_wrapper_options_with_argument` (`sudo -u bob`, `env -u X`, `env -C /d`).
5. **Parole chiave**: in testa al comando si scartano `if then else elif do while until { ! time`. Test: `test_leading_keywords_are_dropped`.
6. **`push_is_force`**: `f` riconosciuta nei gruppi corti. Test: `test_short_flag_cluster_contains_f` (`-fu`, `-uf`; `-u` da solo non è forzato).
7. **`gh` e `curl`**: `_gh_args` toglie i flag globali `-R`/`--repo`/`--hostname` (anche `--repo=` e `-Ro/r`) prima di leggere il sottocomando; `gh api -XPOST`/`-XDELETE` e `curl --request=POST` sono riconosciuti. Test: `test_gh_and_curl_flags`.

### Minor
- **Heredoc verso una shell**: se la riga dell'heredoc contiene `bash|sh|zsh|dash|ksh` come parola (`bash <<EOF`, `cat <<EOF | bash`), solleva `BashParseError`. `text_danger` trova `git push`. Test: `test_shell_receiving_heredoc_falls_back`.
- **`text_danger`**: `reset` con opzioni in mezzo (`git reset -q --hard`) e `commit -n`/`-an`. Test: `test_text_danger_options_between`.
- **`write_targets`**: `perl -pi -e 's/a/b/' f` e `sed -i -e ... f` danno `f` (il programma non è un file); `cp -t dir a b` dà `dir`. Test: `test_write_targets_perl_and_cp_target_dir`.
- **`_GIT_MUTATING`**: aggiunti `update-ref`, `remote`, `filter-branch`, `symbolic-ref`, `submodule`, `gc`. `config` è scrittura solo nelle forme di scrittura (`chiave valore`, `--unset`, `--add` ecc.); `--get`, `--list` e simili non lo sono. Test: `test_extra_mutating_git_subcommands`.

### Scostamenti dal piano (aggiuntivi)
- `_strip_heredocs` e `_SUBST` sono sostituiti da `_split`/`_balanced`, perché la sostituzione di `$(...)` doveva conoscere i corpi di heredoc.
- `_OPS_RE` spezza anche token di punteggiatura che contengono virgolette quotate di un solo carattere (`";"` come argomento): limite noto, fail-safe (spezza solo, non nasconde comandi).
- Il file è cresciuto a circa 470 righe contro le circa 380 del piano. È ancora nelle intenzioni del piano (un solo modulo di analisi), ma è da tenere d'occhio. Per questo lo stato è DONE_WITH_CONCERNS.

### Test ed esiti
- RED: `python3 -B -m unittest tests.test_bash` sulla versione di `bash.py` del commit 8ca1a65 con i nuovi test → `FAILED (failures=32, errors=2)` su 34 test (i fallimenti coprono ogni punto del round).
- GREEN: `python3 -B -m unittest tests.test_bash` → `Ran 34 tests` / `OK`.
- `tests/run`, python 3.11.16: `Ran 281 tests in 1.490s` / `OK`.
- `tests/run`, python 3.13.5: `Ran 281 tests in 1.516s` / `OK`.
- 281 = 268 precedenti + 13 nuovi. `git status` pulito dopo il commit.

### File cambiati
- `bin/tollgate_analysis/bash.py`
- `tests/test_bash.py`

### Dubbi aggiornati
- I token spuri dei `$(...)` annidati (`$`, `))`) del report precedente sono risolti dalla nuova scansione.
- Il punto 2 del dubbio precedente (`globs` sui pattern di comandi) è risolto con `fnmatch` per decisione del controller.
- Il ripiego `text_danger` non è ancora cablato nei controlli dei Task 16 e 17.

## Fix round 2

**Commit:** 53c1585 tollgate P2: assegnazioni con sostituzione, redirezioni nei token, heredoc non quotati (fix round 2)

Prima la correzione di ogni punto con il suo test (RED: `python3 -B -m unittest tests.test_bash` → `FAILED (failures=8)` su 40 test, con i fallimenti su assegnazioni, redirezioni, `time` e heredoc non quotati), poi la correzione (GREEN: `Ran 40 tests` / `OK`).

### Important (regressione dell'assegnazione con sostituzione)
- Causa: il placeholder `" SUBST "` aveva spazi intorno, quindi `X=$(cmd) git push -f` diventava `X= SUBST  git push -f` e la parola `SUBST` era presa come comando. Ora il placeholder è `_TG_SUBST_`, senza spazi (`_SUBST_TOKEN`): `X=$(cmd)` resta un'assegnazione e l'argv è `["git","push","-f"]`.
- Test: `FixRound2Test.test_assignment_with_substitution_keeps_command` con `X=$(cmd) git push -f`, `TOKEN=$(cat f) git push -f`, `A=1 B=$(x) git push -f`.

### Minor
1. **`_ops` con `<`/`>`**: la punteggiatura fusa viene spezzata anche nelle redirezioni (`_PUNCT_RE`: `<<<`, `<<`, `<>`, `&>>`, `&>`, `>>`, `>|`, `>&`, `<&`, `[<>]`, poi gli operatori). `true;>f` dà il solo comando `true` e il bersaglio `f`; `(git push -f)>log` dà il bersaglio `log`. Test: `test_redirect_after_semicolon_is_not_a_command`, `test_subshell_then_redirect_targets_log`. Nota: un redirect senza comando produce un `Cmd` con `argv` vuoto e solo `redirects`; i controlli sull'argv gestiscono già il caso.
2. **`time`**: tolto da `_KEYWORDS`, resta nei wrapper con `-f`/`-o` come argomenti; `-p` è un flag. Test: `test_time_is_a_wrapper_with_p_flag`.
3. **Heredoc non quotato**: `_skip_heredoc_bodies` riceve il tipo di delimitatore (quotato o no). Per il corpo non quotato `_collect_subst` estrae `$(...)` e backtick e li analizza come comandi annidati. Quotati (`'EOF'`, `"EOF"`): il corpo resta dato. Test: `test_unquoted_heredoc_body_substitutions_run` (con `$(git push -f)` e con backtick) e `test_quoted_heredoc_body_substitutions_are_data`.
4. **Duplicazione**: `_balanced` e `_split` sono sostituite da una sola funzione, `_scan(text, i, nested)`. Gestisce virgolette, backslash, backtick, `$(...)`, heredoc e a capo in un solo punto. In modalità `nested` si ferma alla `)` che chiude il `$(`. Nessuna funzione duplicata; `_collect_subst` ha solo il compito di estrarre le sostituzioni dal corpo non quotato.

### Correzione al report precedente
- La dimensione indicata nel «Fix round 1» (circa 470 righe) era sbagliata. `bash.py` è di 742 righe dopo questo giro: la maggior parte è il codice di classificazione, che il piano ha in numero di righe simile. Il modulo è ancora unico, come da piano; la scelta di non dividerlo resta al controllo.

### Test ed esiti
- `python3 -B -m unittest tests.test_bash` → `Ran 40 tests` / `OK`.
- `tests/run`, python 3.11.16: `Ran 287 tests in 1.442s` / `OK`.
- `tests/run`, python 3.13.5: `Ran 287 tests in 1.529s` / `OK`.
- 287 = 281 precedenti + 6 nuovi. `git status` pulito dopo il commit.

### File cambiati
- `bin/tollgate_analysis/bash.py`
- `tests/test_bash.py`
