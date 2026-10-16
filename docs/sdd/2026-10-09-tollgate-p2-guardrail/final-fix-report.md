# Report delle correzioni dopo la revisione finale (p2-guardrail)

Stato: DONE_WITH_CONCERNS (dubbi in fondo). Tutti i comandi con `python3 -B`; nessun `claude`, nessuna rete.
Convenzione: «RED» = test lanciato prima della correzione, «GREEN» = dopo.

## Commit (in ordine)
- 8125473 C1: copie del DB con nome temporaneo unico e `os.link`
- 2757ec0 + commit successivo C2: protezione dietro collegamenti simbolici (il primo commit ha incluso per errore dei `__pycache__` di `bin/tollgate_checks`; il secondo li toglie dall'indice. Niente amend, come da regola: restano nella storia del ramo)
- 984133a I1+M1: la protezione segue il bersaglio
- 80de5e6 I2+M4: `PostToolUseFailure`
- 6b88ac8 I3: opzioni abbreviate, alias, ripiego testuale
- 6de0f20 M2: `git checkout`/`git restore` tra i bersagli di scrittura
- f0aaa1a M6: `waiver add` con nome unico e `flock`
- bbbe07f Triage 13: `LC_ALL=C` sul confronto delle ore
- 6e73c05 M5 + spec (riga 21 della sezione 20, 7.4 collegamenti) + conteggio test del piano

## Evidenza TDD per rilievo

### C1
- Test: `tests/test_db.py::BackupRaceTest` (`test_same_instant_same_name_never_overwrites` con ora bloccata e `Path.exists` forzato a False; `test_concurrent_backups_with_frozen_clock`, 3 processi con ora bloccata e partenza sincronizzata; `test_concurrent_migration_of_v1_db_with_rows`, DB v1 con una riga migrato da 4 processi, righe e copie integre).
- RED: `python3 -B -m unittest tests.test_db.BackupRaceTest` -> 2 FAIL (`AssertionError: PosixPath(...) == PosixPath(...)` sul primo, `sqlite3.OperationalError: disk I/O error` sul secondo, la stessa causa della revisione). Il test di migrazione v1 concorrente passa già prima (la corsa lì è intermittente): resta come regressione.
- GREEN: stesso comando, `OK`. `tests.test_db` completo: 25 OK.
- Stabilità: `tests.test_db.OpenTest.test_concurrent_first_open` lanciato 30 volte di seguito con `python3 -B -m unittest ...`: 30 OK su 30 (due volte, dopo C1 e a fine lavoro).
- Correzione: `db.backup` scrive in `.tmp-<pid>-<token>-<tag>.db` e pubblica con `os.link` (su `FileExistsError` prova `-<n>-`), poi toglie il temporaneo. Non fatto il punto 3 «consigliato» (rilettura della versione sotto `BEGIN IMMEDIATE` prima della copia): non richiesto.

### C2
- Test: `tests/test_symlinks.py` (6 test: symlink `settings.json` verso file esterno nel repo e in HOME, symlink di cartella `.claude` nel repo e in HOME, repo raggiunto da un padre simbolico, casi non protetti che restano 0; sia Write sia Bash `echo >`, `sed -i`).
- RED: `python3 -B -m unittest tests.test_symlinks` -> 4 FAIL (`0 != 2`); il caso del padre simbolico passava già.
- GREEN: stesso comando, 6 OK.
- Funzione condivisa: `_common.path_forms` (forma lessicale, risolta e intermedie) + `_common.is_protected_path` valuta tutte le forme su tutte le radici; `edit_lexical` per Write/Edit; `bash_rules._abs`/`_expand` non risolvono più e `_check` risolve dopo i controlli di protezione; `_removes_protected` usa le stesse forme; `Ctx.protected_roots` aggiunge la forma risolta di HOME.

### I1 + M1
- Test: `tests/test_active_roots.py` (7 test) e 4 test in `tests/test_wrapper.py` (`test_active_root_named_in_input_starts_python`, `..._not_named_never_starts_python`, `..._only_matters_for_pre_tool_use`, `test_empty_registry_line_matches_nothing`).
- RED: `python3 -B -m unittest tests.test_active_roots` -> 7 FAIL/ERROR (scrittura protetta e `git -C <attivo> push origin main` con cwd fuori da qualunque repo e da un repo vicino: `0 != 2`; registro assente). `tests.test_wrapper` con il vecchio `hooks/run`: 1 FAIL (`0 != 2`).
- GREEN: `tests.test_active_roots` 7 OK; `tests.test_wrapper` 27 OK (incluso test triage 13).
- Implementazione: `bin/tollgate_core/active.py` (`register`, `prefixes`; file `<stato>/active/<hash>` con checkout e worktree, una riga ciascuno, più la forma con escape JSON; rinnovo ogni 300 s o se manca la radice); il runner lo scrive quando vede un repo attivo e, per `pre_edit`/`pre_bash` con cwd non attivo o inesistente, prende repo e configurazione dal bersaglio (file, `-C`, `cd`); wrapper: `grep -qFf` del registro sull'input, solo `PreToolUse`, solo se il cwd non è attivo e la sessione non è legata. `tests/test_hook_engine.py` non è cambiato: `/non/esiste` con `ls` resta 0 (nessun bersaglio).
- **Vincolo per P3:** `start` deve scrivere il registro (`active.register(state, repo, extra=[worktree])`) quando crea il worktree del lavoro, prima del primo hook nel nuovo worktree; è annotato anche nella spec 6.6.

### I2
- Campi: `task-1-docs.md` e `docs/verifiche/2026-10-09-p2-verifiche.md` documentano solo che `PostToolUseFailure` accetta `additionalContext` e l'uscita 2 mostra stderr; i campi propri dell'evento non sono documentati lì, quindi nessun campo è usato (nessuno dei controlli legge `tool_response`). Test con la busta di `PostToolUse-Bash` e `hook_event_name="PostToolUseFailure"`.
- Test: `test_manifest.test_hooks_json`, `test_check_effects.test_failed_command_still_consumes_the_act`, `test_check_post_bash.test_commit_of_a_failed_command_is_recorded`, `test_check_post_edit.test_failed_edit_event_recomputes_level`, `test_hook_engine.test_post_tool_use_failure_maps_to_post_kinds`.
- RED: `python3 -B -m unittest tests.test_manifest tests.test_check_effects tests.test_check_post_bash tests.test_check_post_edit` -> 4 FAIL.
- GREEN: stessi + `tests.test_hook_engine`, 70 OK.
- `hooks.json`: `PostToolUseFailure` con matcher `Edit|Write|MultiEdit|NotebookEdit|Bash`; `adapter._kind` mappa Bash -> `post_bash` e modifiche -> `post_edit` (Agent, Skill ecc. -> nessun evento). Spec 7.1 punto 7, 7.2, 8.5 punto 3 (con M4: «l'adattatore di P2 non mappa `PostToolUse` MCP»).

### I3
- Test: `tests/test_bash.py` (`AbbreviationAndAliasTest`, `TextDangerFallbackTest`) e `tests/test_check_bash.py` (`test_abbreviated_options_and_aliases_are_denied`, `test_unparsable_text_covers_more_dangers`), con i casi della tabella.
- RED: `python3 -B -m unittest tests.test_bash` -> 21 FAIL; `tests.test_check_bash` con il vecchio `bash.py` -> 12 FAIL.
- GREEN: `tests.test_bash` 58 OK, `tests.test_check_bash` 43 OK.
- `git_call` completa le opzioni lunghe (prefisso di almeno 3 caratteri di `--force`, `--force-with-lease`, `--mirror`, `--no-verify`, `--hard`; un prefisso ambiguo si nega) e risolve gli alias `-c alias.<x>=` (anche con i token successivi dell'alias, a catena, anche nella forma `-calias.x=`); un alias `!` dà il sottocomando `!` e `parse` analizza il suo testo come comando annidato (`shell_alias_command`). `_TEXT_DANGER` aggiornato con i cinque pattern richiesti.

### M2
- Test: `tests/test_bash.py::GitRestoreTargetsTest`, `tests/test_check_bash.py::test_git_checkout_and_restore_of_protected_files_are_denied`.
- RED: 5 FAIL (`tests.test_bash tests.test_check_bash`). GREEN: 104 OK.
- `write_targets`: posizionali dopo `--` per `checkout` e `restore`; per `restore` anche senza `--` (esempio della revisione), saltando il valore di `-s`/`--source`. Per non cambiare il comportamento esistente (`git checkout -- src/app.py` dal coordinatore resta 0, test già presente) la regola «il coordinatore non scrive codice» ignora `checkout`/`restore`.

### M4, M5
- M4: nella stessa modifica di I2 (spec 8.5 punto 3). M5: piano principale, riga 6: 680 test verdi.

### M6
- Test: `tests/test_waiver_cli.py::test_concurrent_adds_keep_every_waiver` (2 processi x 6 `add_waiver`, partenza sincronizzata: 12 deroghe, id distinti, nessun `.tmp` residuo).
- RED: `FileNotFoundError: ...7.toml.tmp -> ...7.toml`. GREEN: `tests.test_waiver_cli` 8 OK (3 esecuzioni).
- `.tmp` con nome unico e `fcntl.flock` su `7.toml.lock` accanto al file, attorno a lettura, assegnazione e scrittura; il file di lock si toglie a fine lavoro (con riverifica dell'inode per chi aspettava) così non resta nel working tree.

### Triage 13
- Test: `test_wrapper.test_off_hours_with_non_ascii_digits_is_rejected` (cifra `٣` come UTF-8 vero, locale `it_IT.UTF-8` e `C.UTF-8`). RED: `FileNotFoundError` su `OFF` (il ramo off si interrompeva). GREEN: `tests.test_wrapper` 27 OK. Correzione: test in subshell con `LC_ALL=C`.

## Esiti finali
- `tests/run` (python3.11 e python3 = 3.13) due volte: 680 test, OK in tutte e 4 le esecuzioni.
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 680 test, OK.
- `test_concurrent_first_open` x30: 30 OK.
- Un `ResourceWarning` («unclosed database», `events.py:53`) era comparso su 2 delle prime 3 esecuzioni di `tests/run`; era dovuto al mio test `BackupRaceTest` (chiudeva la vecchia connessione invece della nuova): corretto nel commit di I3, poi nessuna comparsa nelle 4 esecuzioni finali.

## Dubbi
1. I `__pycache__` committati per errore nel commit C2 sono stati tolti dall'indice con un secondo commit, ma restano nella storia: se si vuole pulire va fatto con una riscrittura che io non faccio (niente amend).
2. I1: in P3 `start` deve scrivere il registro (vincolo sopra). Fino ad allora il registro nasce al primo hook eseguito in un repo attivo; un worktree creato da `git worktree add` fuori da tollgate entra al rinnovo (300 s) o al primo hook nel repo.
3. I3: le opzioni abbreviate sono riconosciute per `--force*`, `--mirror`, `--no-verify`, `--hard` come da brief (non altre, per esempio `--all`).
4. C2: `path_forms` fa una `resolve()` per ogni componente del percorso (decine di syscall per scrittura): costo trascurabile misurato a occhio, non misurato con strumenti.
5. Non fatto: punto 3 consigliato di C1 (rilettura della versione sotto lucchetto prima della copia) e M3/M7 e rinviati, come richiesto.

## Fix round 2

Commit: 2ea840f (I3, alias), 3f7430d (I1 completo + Minor 3). Nessun `__pycache__` nell'indice (controllato prima di ogni commit).

### I3: alias che coprono un comando integrato
- Test: `tests/test_bash.py::AbbreviationAndAliasTest::test_alias_shadowing_a_builtin_is_ignored`; `tests/test_check_bash.py::test_abbreviated_options_and_aliases_are_denied` (tre casi aggiunti: `alias.push=status`, `alias.commit=status` + `--no-verify`, `alias.reset=status` + `--hard`). Resta un alias non integrato (`alias.p=push`) con veto.
- RED: `python3 -B -m unittest tests.test_bash tests.test_check_bash` -> 3 FAIL (push e reset eseguiti da git ma letti come `status`). GREEN: stesso comando, 105 OK.
- Correzione: `_GIT_BUILTIN` (tutto `_GIT_MUTATING` più `status`, `log`, `diff`, `show`, `config`, `rev-parse`, `ls-files`); `_git_split` scarta gli alias con quel nome (nome in minuscolo, come le chiavi di config), quindi vale per `git_call` e `shell_alias_command`.

### I1 completo
- Test (`tests/test_active_roots.py`, wrapper reale, cwd = cartella madre del repo attivo, HOME = cartella madre, sessione non legata): `test_relative_and_home_forms_from_a_parent_directory` con le sette forme (Write relativo, `echo x > ~/main/tollgate.toml`, `cd main && git push origin main`, `git -C main push origin main`, redirect assoluto, `sed -i` assoluto, `cd main && echo x > tollgate.toml`) più `rm` assoluto: tutte 2. `test_command_touching_no_active_repo_passes_from_outside` (`ls /tmp`, `echo x > note.txt`, `cd vicino && git status` da tre cwd): 0. `test_command_touching_two_active_repos_is_denied_with_a_message`. In `tests/test_wrapper.py`: registro non vuoto avvia Python anche senza radice nominata; registro assente o vuoto no.
- RED: `python3 -B -m unittest tests.test_active_roots tests.test_wrapper` -> 10 FAIL (8 forme, il test dei due repo, il wrapper). GREEN: con `tests.test_hook_engine`, 65 OK.
- Wrapper: su `PreToolUse`, cwd non attivo, sessione non legata: Python parte se `active/` contiene almeno una riga; tolto il `grep -F`. Runner: `_target` restituisce un candidato per repo attivo a partire da directory effettiva, bersagli di scrittura e rimozione (`write_targets`, `removal_targets`: redirect, `sed -i`, `rm`), `~` espanso, percorsi relativi rispetto al `cwd` effettivo (anche dopo `cd`), glob ridotti alla cartella che li precede, Edit/Write relativo risolto sul `cwd`. Con più repo attivi diversi l'azione è negata («l'azione tocca più repo attivi ... dividila»). Se `PreToolUse` non ha né cwd attivo né bersaglio attivo né sessione legata, il runner esce con 0 prima di aprire il DB.
- Spec 6.6, 7.1 punto 3 e riga 21 della sezione 20 aggiornate (costo: finché esiste un repo attivo noto, ogni `PreToolUse` fuori dai repo attivi avvia Python, che esce subito). Piano principale: 685 test.

### Minor 3
- Test: `test_check_bash.py::test_git_checkout_and_restore_of_protected_files_are_denied` esteso (coordinatore: `git checkout origin/main -- f`, `git checkout HEAD~1 -- f`, `git restore --source=... f`, `-s`, `--source ... --` danno 2; `git checkout -- f` e `git restore f` restano 0). RED: 5 FAIL; GREEN: 105 OK.
- Correzione: `bash.restores_from_index`; la regola del coordinatore esenta solo queste due forme.

### Esiti
- `tests/run` x2 (python3.11 e python3.13): 685 test, OK (la prima volta prima del commit, la seconda dopo).
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 685 test, OK.

### Dubbi
- Il costo di I1 sale: con un registro non vuoto Python parte a ogni `PreToolUse` fuori dai repo attivi (decisione del controller). Non l'ho misurato.
- Un redirect su un percorso che contiene `$VAR` non espanso non ricade in nessun repo: limite statico noto.

## Fix round 3

### 1. Più repo attivi: checkout principale e worktree sono lo stesso repo
- Test (`tests/test_active_roots.py`): `test_main_checkout_and_its_worktree_are_one_repo` (quattro comandi: `git -C main status; git -C wt status`, `git -C wt diff && git -C main log`, `echo x > main/a.txt; echo y > wt/b.txt`, `rm main/x wt/y`, da due `cwd` fuori dal repo: uscita 0), `test_worktree_is_preferred_when_main_and_worktree_are_both_named` (scrittura su un file protetto del worktree insieme a una nel main: veto normale, senza «più repo attivi»), e il test dei due repo diversi già presente resta con «più repo attivi».
- RED: `python3 -B -m unittest tests.test_active_roots` -> 7 FAIL sui nuovi casi (uscita 2 con «più repo attivi»). GREEN: stesso comando, OK.
- Correzione (`runner._target`): raggruppa per `git.common_dir`; per lo stesso repo sceglie il worktree collegato se un bersaglio ci cade dentro, altrimenti il primo.

### 2. Bersagli di git con `-C`
- Test: `tests/test_active_roots.py::test_git_c_targets_resolve_against_the_c_directory` (da cwd madre: `git -C main checkout origin/main -- tollgate.toml`, `git -C main restore`, `git -C main rm`, e `-C` assoluto: 2) e `tests/test_check_bash.py::test_git_c_targets_resolve_against_the_c_directory` (cwd `wt/src`, `-C ..` e `-C <abs>`: 2; `git -C .. restore src/app.py` dal subagente: 0).
- RED: 5 + 5 FAIL (`0 != 2`). GREEN: `tests.test_active_roots tests.test_check_bash tests.test_bash` 120 OK.
- Correzione (`bash.py`): `_in_c_dir` risolve rispetto alla directory di `-C` i bersagli di `git checkout/restore` e `git rm`; vale quindi sia per `bash_rules` sia per `runner._target`, senza cambiarli.

### Facoltativo: `restores_from_index`
- Test: `test_restores_from_index_attached_and_abbreviated_source` (`-sHEAD~1`, `--so=HEAD~1`, `--sour HEAD~1` dal coordinatore: 2). RED 3 FAIL, GREEN OK. `_is_source_option` riconosce `-s<albero>` e i prefissi di `--source` da 2 caratteri.

### Esiti
- `tests/run` (3.11 e 3.13): 690 test OK. Spec 6.6 e piano (690 test) aggiornati.

## Fix round 4

- `-C` concatenati: `tests/test_active_roots.py::test_chained_git_c_options_compose` (le cinque forme, più `-C vicino -C <abs>` e `-C . -C main`, cwd madre, uscita 2). RED: 5 FAIL (`0 != 2`; le ultime due passavano già per caso). Correzione: `_git_split` compone i `-C` con `os.path.join` e normpath (un assoluto azzera), quindi `effective_dir`, `_in_c_dir` e `runner._target` usano il percorso composto. GREEN: 15 OK.
- Fail-closed: `test_unverifiable_target_repo_is_denied` (patch di `git.common_dir` con `GitError`). RED: uscita 0. Correzione: `runner._target` solleva `_Unverifiable`, il runner nega con «non è stato possibile verificare il repo del bersaglio» (uscita 2 su evento di controllo). GREEN.
- Esiti: `tests/run` (3.11 e 3.13) 692 test OK; suite con `-W error::ResourceWarning` 692 OK.
