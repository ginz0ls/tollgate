# Giro di correzione 1 della revisione finale (commit 8ea2edd)

Base 71f4230, un solo commit, suite verde: 995 test (erano 985), `bash tests/run` su python3.11 e python3, più `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` (exit 0). Nessun «Exception ignored … unclosed database» né «ResourceWarning» in nessuna delle tre esecuzioni (grep sull'output: 0 occorrenze).

## Esito per rilievo

| Rilievo | Esito |
|---|---|
| m1 + righe 65/66 | fatto, in TDD |
| m2 | fatto; messaggio sparito |
| riga 150 | fatto (polling) |
| m3 | fatto, in TDD |
| m4 | fatto, in TDD |
| m5, m6 | fatto |
| m7, m8, m10 | fatto, in TDD (m7 è un refactor coperto dai test esistenti) |
| piano principale | m9, m11, m12, m13 e gli 8 rinviati (b) aggiunti, con piano di destinazione |

## m1 (`bin/tollgate_flow/start.py`, `_create`)

Scelta: segui la correzione di final-review.md, senza scelte di design nuove. Prima di `worktree_add` si rilegge `git.local_branches(main)`. Se `worktree_add` fallisce, il ramo si toglie solo se NON era già in quella lettura e NON compare in `git.worktrees(main)`. Altrimenti il messaggio dice «il ramo X esiste già o è in uso da un altro worktree: non è stato toccato». Resta `delete_branch` (atomico sullo SHA) per il caso in cui il ramo è davvero nostro.

Limite residuo (non risolvibile senza cambiare il modo di creare il ramo): la finestra di pochi millisecondi in cui l'altra sessione ha creato il ref ma non ancora registrato il worktree, e il nostro `add` fallisce proprio lì. La revisione non proponeva altro; una creazione atomica del ref con `update-ref` a valore vecchio vuoto sarebbe la via, ma è una scelta di design (non applicata).

Test (passano da `start()`, chiudono anche la riga 65):
- `test_failed_add_keeps_branch_used_by_another_worktree`: l'altra sessione crea ramo e worktree, il nostro add fallisce.
- `test_failed_add_keeps_branch_that_existed_before_the_add`: ramo preesistente alla base, `branch_name` e `_existing_branches` simulati stantii.

RED (comando: `python3 -B -m unittest tests.test_start.StartNewTest.test_failed_add_keeps_branch_used_by_another_worktree tests.test_start.StartNewTest.test_failed_add_keeps_branch_that_existed_before_the_add`):
```
ERROR: ...test_failed_add_keeps_branch_used_by_another_worktree
subprocess.CalledProcessError: ... 'rev-parse', 'tg/7-aggiungi-export-csv' ... returned non-zero exit status 128.   (ramo cancellato)
ERROR: ...test_failed_add_keeps_branch_that_existed_before_the_add
subprocess.CalledProcessError: ... 'rev-parse', 'tg/7-aggiungi-export-csv' ... returned non-zero exit status 128.
Ran 2 tests ... FAILED (errors=2)
```
GREEN: `python3 -B -m unittest tests.test_start` -> `Ran 59 tests ... OK`.

## m2

L'unica Lab/FlowLab non chiusa era `CtxTest.test_context_guard_reads_it`: ora `addCleanup(lab.close)`. Ho cercato le altre con uno strumento fuori dal repo (scratchpad `findleaks.py`: avvolge `Lab.__init__`/`close` e controlla a fine di ogni test, dopo i cleanup). Prima: `LEAKS 1 tests.test_statusline.CtxTest.test_context_guard_reads_it`. Nessun altro. Dopo la correzione: output completo di `tests/run` (3.11 e 3.13) e della corsa con `-W error::ResourceWarning`: 0 occorrenze di «Exception ignored», «unclosed» o «ResourceWarning».

## Riga 150 (`tests/test_verify.py`)

`test_background_child_killed_after_success` usa `_wait_gone(pid, seconds=10)`: polling a 50 ms con scadenza, considera morto un `ProcessLookupError` oppure uno zombie (stato `Z` in `/proc/<pid>/stat`). Nuovo test `test_wait_gone_treats_a_zombie_as_dead` (vivo = non gone; ucciso e non raccolto = gone). Nessun RED significativo: è un irrobustimento del test, non un cambio di comportamento; il vecchio `sleep(0.3)` non era riproducibile a comando. Tre esecuzioni consecutive del test: OK.

## m3

- `bash.script_index(argv)` (nuova, `bin/tollgate_analysis/bash.py`): posizione dello script saltando le opzioni dell'interprete (`-B`, `-W x`, `-X x`); None per `-c`/`-m`. `uses_tollgate_bin` la usa, il che ripara anche `effects` (prima `python3 -B "<bin>" start 7` veniva negato come «script non tracciato» dal controllo degli effetti: lo ha mostrato il RED).
- `cli_calls._program_args` restituisce `(argomenti, certo)`. Se lo script (o il comando) è un'espansione (`$p`, `$(…)`, backtick, `SUBST_TOKEN`) è «incerto»: per un subagente vale come programma (fail-closed), per il coordinatore non scrive il segnale (resta il rifiuto di `start`/`act`).
- Errore di parsing con `agent_id`: negato se il testo grezzo contiene `tollgate` e una parola tra `start`, `task`, `act`, `--checkpoint`.
- `_SUBST_TOKEN` rinominata `SUBST_TOKEN` (ora pubblica, tre occorrenze).
- Test: `test_interpreter_options_before_the_script`, `test_subagent_cannot_hide_the_program_in_an_expansion`, `test_subagent_unparsable_command_naming_the_program_is_denied`, `ScriptIndexTest` (2 test). Casi leciti verificati: `verify` con variabile, `python3 -c`, `python3 "$x" tasks`, `echo "$HOME" start`, parse error senza tollgate.

RED (`python3 -B -m unittest tests.test_check_cli_calls`): `Ran 11 tests ... FAILED (failures=11, errors=2)`, per esempio `AssertionError: 0 != 2` su `p="<bin>"; python3 "$p" task done 1`, su `python3 -W error '<bin>' act apply` e su `python3 -B -X dev '<bin>' status --checkpoint`. GREEN: `python3 -B -m unittest tests.test_bash tests.test_check_cli_calls tests.test_check_bash tests.test_check_effects` -> OK.

## m4

`agents/implementer.md` (descrizione, righe 50, 65, 69, 82) usa `<programma>`, definito come la forma esatta del brief e del messaggio di avvio (`python3 '<percorso>/bin/tollgate'`), con l'avvertenza che `tollgate` nudo non è nel PATH. Nuovo test `test_agents_and_skills_never_write_a_bare_program_name` in `tests/test_manifest.py` (agenti e skill). RED: `FAIL ... (path='implementer.md') Lists differ: ['tollgate verify', 'tollgate block', ...] != []`. Le skill erano già pulite.

Osservazione, fuori dal perimetro chiesto (non toccata): alcuni messaggi a runtime scrivono ancora `tollgate ...` nudo come istruzione al modello: `bin/tollgate_checks/_common.py:194` (suggerimento `waiver add`), `agents.py:44` (`status --checkpoint`), `send_message.py:41`, `bin/tollgate_flow/checkpoint.py:52-62` (`next_step`). Vanno valutati con P3b (vincolo 2 del piano principale: mai il percorso nudo).

## m5, m6

- Spec rev 22, riga 459: «esiste una revisione preparata per il codice corrente» (e il codice non confronta gli orari). Riga 333: si raccolgono insieme solo i rifiuti dei prerequisiti, gli altri escono uno alla volta.
- Piano principale: firma di `write_checkpoint(state, cwd, *, note, now=None)` con `note` obbligatorio per parola chiave. Riga 6 (Stato): la frase su `ResourceWarning` ora è vera (verificato) e precisa «nemmeno con `-W error::ResourceWarning` e nessun “unclosed database” a fine suite»; numero dei test 985 -> 995.

## m7, m8, m10

- m7: `start._fence` tolta, si usa `brief.fence` (coperto dal test `test_hostile_issue_title_and_body`, verde). `import re` non più usato, rimosso.
- m8: `shlex.quote(str(wt))` nel suggerimento di `rebase --abort`. RED: `AssertionError: "git -C '/tmp/tollgate lab …/wt 7' rebase --abort" not found in '…git -C /tmp/tollgate lab …/wt 7 rebase --abort…'`. Il test ora controlla anche che il percorso contenga uno spazio.
- m10: `except (phases.WorkExists, sqlite3.Error, db.DbError)` dopo `create_work`, con messaggio «(creati il ramo … e il worktree …: rimuovili a mano)». Test `test_create_work_database_error_names_branch_and_worktree`. RED: `sqlite3.OperationalError: locked` non gestita (ERROR). Il vecchio testo «creati nel frattempo» non era usato da nessun test.

## Piano principale: vincoli aggiunti (tabella «Contratti»)

Tre righe nuove prima di «P3 | P4»: P3b (m9, m11, m12, m13, righe 55, 56 per le PR, 74, 102, 108, 133), P3c (riga 82), P4/P5 (riga 56 per `sentinel_issues`, riga 163). Gli 8 rinviati (b) sono: 55, 56, 74, 82, 102, 108, 133, 163.

## Scostamenti e dubbi

- Nessuno scostamento dalla revisione, salvo il limite residuo di m1 descritto sopra.
- Cautele rispettate: nessun accesso a `~/.local/state/tollgate`, `~/.claude`, plugin, rete o `claude -p`; nessun processo terminato per nome (solo un mio job in background fermato per ID).
- Restano nel `/tmp` alcune cartelle `tollgate lab *` lasciate dalle corse precedenti al fix di m2 (non toccate, non sono nel repo).

# Giro 2 (commit 1636d48, «fix round 2 della revisione finale»)

Suite: 996 test verdi con `bash tests/run` (python3.11 e python3) e con `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`; grep di «Exception ignored», «unclosed», «ResourceWarning» sugli output: 0.

## m1 atomico
- `gitw.create_branch(repo, branch, sha)`: `git update-ref refs/heads/<ramo> <sha> ""`; falso se il ref esiste o git fallisce. `start._create` crea il ramo con questa funzione. Se fallisce e il ramo esiste, rifiuta (codice 1) con «ramo locale X per #N, creato nel frattempo da un'altra sessione: adottalo con /tollgate:adopt #N» e non lo tocca; se non esiste, «creazione del ramo X non riuscita». Poi `worktree_add(new_branch=False)` sul ramo nostro; se fallisce, `delete_branch(main, ramo, base_sha)` toglie solo il ref creato qui. Tolta la logica del giro 1 (rilettura dei rami e controllo dei worktree: la proprietà ora è atomica). La ripresa (`_restore_worktree`) non cambia.
- Test, con corsa simulata da un hook su `gitw._run` che crea il ramo dell'altra sessione prima della prima scrittura di `_create`: `test_branch_taken_by_another_session_without_worktree_is_never_deleted` e `..._with_its_worktree_...`. RED sul codice del giro 1: ERROR su rev-parse del ramo (ramo cancellato) nel caso senza worktree; il caso con worktree falliva sul messaggio (`'ramo locale' not found`). GREEN dopo: `tests.test_start` 59 OK. `test_worktree_add_failure_refuses` verifica che il ramo creato qui venga tolto.
- `tollgate_flow` scrive su git solo via `gitw` (grep: `start.py` non usa subprocess; l'unica lettura fuori è `prereq.py` con `git config --get`, preesistente).

## Programma nei messaggi
Corretti con `program_command`: `_common.waiver_hint/explain` (ora prendono `ctx`; aggiornati `commit`, `writes`, `post_bash`), `agents.py` (contesto e «task start»), `send_message.py`, `checkpoint.next_step` (con `db.BIN_PATH`). Lasciati: le etichette di errore «tollgate verify: …» in `verify.py`, `db.restore_command` (terminale), `bash_rules.py` («tollgate hook»: non è un'istruzione).
Test: `BareProgramInMessagesTest` in `tests/test_manifest.py` scandisce con `ast` i letterali di tutto `bin/` (docstring escluse) e vieta `tollgate <sottocomando>` nudo. RED con 8 occorrenze (`_common.py:194`, `agents.py:43` e `67`, `send_message.py:41`, `checkpoint.py:52/59/61/62`), GREEN dopo. Aggiornati `test_check_writes.test_scope` e `test_checkpoint.test_next_step_sequence` alla forma `python3 '<bin>' …`.

# Giro 3 (commit ab64a9a, «fix round 3 della revisione finale»)

997 test verdi: `bash tests/run` (python3.11 e python3) e `-W error::ResourceWarning`; 0 occorrenze di «Exception ignored», «unclosed», «ResourceWarning».
1. `BareProgramInMessagesTest` spostata prima di `unittest.main()`.
2. `flow_start_naming` tolto da `tests/test_start.py` (grep: nessun altro uso).
3. I sottocomandi del test vengono da `cli.build_parser()` (scelte di `cmd`, meno `hook`, eccezione mirata) più i futuri (`open-pr`, `gate`, `finish`, `init`, `setup`, `sync`, `adopt`, `cleanup`, `abandon`, `resolve`, `approve`). Nessuna nuova occorrenza nei letterali di `bin/`.
4. `cli_calls._deny_subagent(sub, certain)`: per un programma incerto il messaggio aggiunge di scrivere il percorso dello script in modo letterale, senza variabile né `$(…)`; resta fail-closed. Test `test_uncertain_program_denial_says_what_to_do` (RED: messaggio senza l'indicazione; GREEN dopo; il caso certo non ha l'aggiunta).
