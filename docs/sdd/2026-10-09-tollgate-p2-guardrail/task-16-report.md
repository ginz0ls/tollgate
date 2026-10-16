# Task 16 - Regole su Bash (7.4) ed effetti esterni (8.5)

## Implementato
- `bin/tollgate_checks/bash_rules.py` (pre_bash, ordine 20) ed `effects.py` (pre_bash e pre_mcp, ordine 30).
- Aiuti di `writes.py` spostati in `_common.py` (nessuna duplicazione): `in_main_checkout`, `is_protected_path` (era `_protected`). `writes.py` li importa. `_inside` arriva da `_common` (C13).
- `tollgate_analysis/bash.py` (Task 7), tre aggiunte pubbliche (nessun import nuovo):
  - `git_mutating(cmd)`: parte git di `writes()`, senza i redirect.
  - `git_config_write(cmd)`: `"local"` per `.git/config`, il percorso dato con `--file`, `None` per lettura, `--global` e `--system`.
  - `_read_only_git`: le forme di elenco (`git branch`, `-a`, `--list`, `worktree list`, `stash list`, `tag`, `tag -l`, `remote -v`, `submodule status`) non contano più come scritture. Serve alla decisione 16: su un ramo orfano «quelli di lettura passano», e `git worktree list` dal checkout principale non deve essere negato.

## Decisioni del controller
- C3: redirect, `touch`, `cp`, `tee` e `git config --file` verso `.git/hooks/**` e `.git/config` negati; `git config <chiave> <valore>` (e `--unset`, ecc.) negato come scrittura di `.git/config`; `--get`, `--list`, `-l` e `--global` passano. Test con sessione legata, non legata e senza lavoro (`GitInternalsTest`).
- C7a: `HEAD` in `push` risolto con `git.branch(edir)` prima della regola sul predefinito (anche `HEAD:main`, `git push origin`, `git push`). Test dal checkout principale su `main`, e su un ramo `feat` dove `HEAD` passa.
- C13: `_inside` da `_common`.
- C14: nessuna esenzione per gli script ignorati da git (`test_untracked_ignored_script_is_still_an_effect`).
- Ruling Task 7: pattern di comandi con fnmatch (già in `bash.py`); `mcp_allow` con `fnmatchcase`.

## Coerenza con `writes.py` (Task 15)
Protezione su ogni radice (repo più vicino, worktree del lavoro, repo del contesto); sessione legata che scrive nel worktree di un altro lavoro negata (anche con `cd` e `git commit` lì); `git.worktrees` che fallisce = veto con «non è stato possibile verificare i worktree»; percorsi fuori dai repo attivi passano; i collegamenti simbolici sono risolti.

## Scostamenti dal piano (e perché)
1. Effetti: il piano ritornava al primo effetto della riga. Con `ssh a && ssh b` approvato solo `a`, `b` non veniva valutato (aggira il veto) e l'atto di `a` si consumava anche se la riga non girava. Ora si valutano tutti gli effetti: se uno manca, un solo veto e nessun atto consumato; lo stesso effetto ripetuto nella riga ne consuma uno per volta (quindi serve un atto per esecuzione). Test `test_second_effect_of_the_line_is_not_skipped`, `test_all_effects_of_the_line_approved`, `test_same_effect_twice_in_a_line_needs_two_acts`.
2. Un atto già usato e poi riapprovato lascia passare con un avviso «già eseguito alle…» nell'iniezione.
3. Il piano applicava le regole di repo (push, merge, branch -d, worktree) a qualunque repo; ora solo se il repo del comando è attivo (del contesto, o con `tollgate.toml` sul riferimento predefinito). Le regole globali (claude, `TOLLGATE_`, hook, protetti, `reset --hard`, `--no-verify`, `rm -rf`) restano ovunque. Un `push` in sessione legata resta negato in ogni repo (6.6).
4. Merge: negato per ogni argomento `tg/*` (anche `origin/tg/*`) o ramo di un lavoro attivo, come dice la spec 7.4, non solo per i lavori attivi.
5. `push --all` verso il predefinito negato. `rm -rf` della radice del repo o del worktree stesso negato.
6. `TOLLGATE_X=1; cmd` (assegnazione isolata, che `parse` scarta) intercettata con una regex sul testo grezzo.
7. Ramo orfano: come `writes.py`, i redirect verso `.md` sotto `docs/superpowers/` passano; gli altri bersagli e i comandi git che scrivono sono negati.
8. Regola del coordinatore: esenti anche le cartelle di output (`reports/`, `.tollgate-run/`, C9).
9. Messaggi dei veti con `rule` distinte (`protected`, `other_work`, `main_checkout`, `push`, ecc.) invece di `bash`.

## TDD
- RED: `python3 -B -m unittest tests.test_check_bash tests.test_check_effects` prima dei moduli: 38 test, `FAILED (failures=80, errors=1)` (assertion `0 != 2`: tutto passa con uscita 0; l'errore è `EID.search(...)` su `None`).
- GREEN: `python3 -B -m unittest tests.test_check_bash tests.test_check_effects` -> 38 test OK (25 + 13). `tests.test_bash` 42 OK (2 nuovi).
- Suite: `tests/run` -> Python 3.11.16: 517 test OK; Python 3.13.5: 517 OK. `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` -> 517 OK, output pulito. (477 + 40 nuovi.)

## File
Creati: `bin/tollgate_checks/bash_rules.py`, `bin/tollgate_checks/effects.py`, `tests/test_check_bash.py`, `tests/test_check_effects.py`.
Modificati: `bin/tollgate_checks/_common.py`, `bin/tollgate_checks/writes.py`, `bin/tollgate_analysis/bash.py`, `tests/test_bash.py`.

## Autorevisione e dubbi
- `bash_rules.py` ~230 righe, `effects.py` ~110: dentro le attese.
- Lacune note (best effort, le prende PostToolUse): comandi illeggibili non sono valutati per gli effetti (Task 7 offre il ripiego testuale solo per i pericoli di 7.4: es. `bash <<EOF\nssh host\nEOF` passa per gli effetti); `rm`/`mv` di una cartella antenata di un file protetto (es. `rm -rf .git`) non è riconosciuto come scrittura protetta; un effetto approvato in una riga già negata da `bash_rules` (ordine 20) consuma comunque l'atto, perché i `record` si applicano anche con il veto (motore).
- `git checkout <ramo remoto non locale>` non è riconosciuto come cambio di ramo (solo i rami locali, come nel piano).
- `git config` locale in forma di scrittura è negato anche per chiavi innocue (costo accettato dal ruling C3).

## Fix round 1
Per ogni punto: test scritto prima e visto rosso (`python3 -B -m unittest tests.test_bash`: 8 failures + 29 errors sui nuovi test; `tests.test_check_bash`: 22 failures; `tests.test_check_effects`: 9 failures), poi il codice.

1. `mv`: `write_targets` conta le sorgenti (tutte le posizionali; con `-t dir` sorgenti più `dir`); idem `cp --remove-source*`. Nuovo `bash.removal_targets` (rm, rmdir, sorgenti di mv). Test in `test_bash.py` (`test_mv_source_is_a_target`, `test_removal_targets`) e `test_check_bash.py` (`RemovalTest`).
2. Antenati: in `bash_rules._check`, per i bersagli di rm/rmdir/mv si nega se il percorso è protetto o contiene un percorso protetto. Le sonde sono ricavate da `protected.REPO_PROTECTED` (un percorso concreto per pattern: nessuna lista duplicata), più le radici assolute (`protected_roots`) e la radice del worktree/repo del contesto. Coperti: `rm -rf .tollgate`, `docs/superpowers/reviews`, `.tollgate/waivers`, `.git`, `.`, `..`, `docs`, `rmdir`, `mv` con e senza `-t`, la cartella di stato. Passano: `rm -rf build`, `mv src/a src/b`, `mv src/app.py docs/superpowers/` (destinazione, non sorgente), `cp tollgate.toml /tmp/x`. Una radice di repo annidato non è negata solo perché è un repo (altrimenti `rm -rf` di un clone dentro il repo darebbe falso positivo); lo è se contiene file protetti noti.
3. Consumo in PostToolUse: `effects.py` ha ora gli eventi `pre_bash`, `post_bash`, `pre_mcp` (nessun modulo nuovo, nessuna duplicazione: `_bash_intents` è condivisa). `pre_bash` verifica che ogni effetto della riga abbia un atto valido e registra solo `effect_request`; `post_bash` ricalcola gli effetti della riga con la stessa funzione e registra `effect_execute`. Test: riga negata -> `effect_executed` resta vuoto e l'atto vale ancora; dopo il Post l'atto è consumato e il secondo `ssh a` è negato con «già eseguito alle». Limiti: (a) l'adattatore non ha un `PostToolUse` per gli strumenti MCP, quindi per MCP il consumo resta al Pre; (b) la chiave contiene lo SHA: se la stessa riga cambia HEAD (es. `git commit && ssh a`), il Post ricalcola un'altra chiave e non trova l'atto; l'atto resta non consumato ma vale solo per il vecchio SHA.
4. Comando illeggibile: nuovo `bash.text_effect` (lista predefinita, supabase, gh in scrittura, curl/wget con dati) con confini di parola (`sshd` e `essh` non scattano). Il veto usa l'id calcolato sul testo normalizzato e segue lo stesso ciclo (veto, atto, Post, «già eseguito»). Sostituito `test_unparsable_command_is_not_an_effect`.
5. `core.hooksPath`: `bash.hooks_path_override` (`git -c`, `--config-env`, variabili nell'env del comando, `git config` in scrittura a ogni livello); `--get` passa. Negato in `_forbidden` con messaggio «hooksPath». Test unit, bound e non legato.
6. `git tag -n`, `--contains`, `--merged`, `--points-at`, `--list`, `-l`, `--sort` sono letture; `-a/-d/-f/-s/-u/-m/-F` e i nomi restano scritture. Test unit e sul ramo orfano.
7. `--force-if-includes` da solo non è forzato (lo è con `--force`, `-f`, `--force-with-lease`, `--mirror`). Test unit e in bash_rules.
8. Prefisso doppio tolto: se la ragione inizia con «effetto esterno» non si ripete. Test.

Comandi: `tests/run` -> Python 3.11.16: 535 test OK; Python 3.13.5: 535 OK. `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` -> 535 OK.
Lacune residue: bersagli con glob non espansi (`rm -rf .tollgate/*`) non sono risolti; il ripiego testuale non applica `[external_effects] allow`.

## Fix round 2
Test scritti prima e visti rossi (`tests.test_check_bash`/`test_check_effects`: 16 failures + 1 error; `tests.test_bash`: errori sulle nuove funzioni), poi il codice.

- **Glob e graffe** (`bash_rules._braces`, `_expand`): per ogni bersaglio di scrittura e di rimozione si espandono le graffe (`{a,b}`, anche annidate), poi `glob.iglob(..., recursive=True, include_hidden=True)` (cwd con `glob.escape`, tetto 5000 risultati) e si valuta ogni risultato, oltre al testo stesso. Per le rimozioni ricorsive (`rm -r`, `rmdir`, `find -delete/-exec rm`, `git rm -r`) si valuta anche, sempre, la cartella che precede il primo carattere glob (la radice per `*`). Test per gli otto esempi (`.tollgate/*`, `.toll*`, `.t?llgate`, `.[a-z]*`, `./*`, `*`, `mv .tollgate/* /tmp/zz`, `{.tollgate,x}`) più `**/waivers`, `.tollgate/{waivers,x}`, `waiv[e]rs`, glob senza corrispondenze (antenato); passano `rm -rf build/*`, `rm -f *.pyc`, `rm -rf src/*`, `mv build/* /tmp/zz`, `ls .tollgate/*`.
  - Scostamento dalla richiesta: l'antenato del glob si valuta solo per le rimozioni che possono portare via cartelle (ricorsive). Per `rm -f *.pyc` o `mv *.md docs/` nella radice varrebbe «la radice contiene file protetti» e darebbe un falso positivo costante; lì bastano i risultati dell'espansione (che includono `tollgate.toml` se il glob lo copre).
- **Guardia `effect_request`**: il Pre registra la richiesta solo se la riga non esiste (`i.row is None`), sia nel veto sia nel permesso: un effetto eseguito non torna `requested`. Test sullo stato in `intents`.
- **`-ccore.hooksPath=...`** (forma compatta) riconosciuto da `hooks_path_override`. Test unit e in bash_rules.
- **Altre rimozioni**: `removal_targets` copre `git rm`, `unlink`, `find` con `-delete` o `-exec/-execdir/-ok rm|rmdir|unlink|mv|shred` (bersagli = radici di `find`, `.` se mancano); nuova `removal_recursive`. Verificato: `-exec rm` nel `find` non veniva analizzato (argv di `find`), ora è coperto. `_removes_protected` valuta anche il percorso stesso come file protetto (serve a `unlink .tollgate/waivers/7.toml`, `git rm`). Test per ciascuno, più i casi che passano (`find build -delete`, `find . -name x`, `find build -exec rm {} \;`, `git rm src/app.py`).
- Attrito noto: `find . -name '*.pyc' -delete` è negato (bersaglio = radice di `find`, come da decisione); si passa da una cartella più stretta.

Comandi: `tests/run` -> Python 3.11.16: 546 test OK; Python 3.13.5: 546 OK. `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` -> 546 OK.
