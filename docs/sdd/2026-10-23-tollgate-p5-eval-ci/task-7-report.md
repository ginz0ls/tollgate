# Task 7 - Banco degli eval: report dell'implementatore

## Cosa è stato fatto

File nuovi (tutti sotto `evals/_kit/`, `tests/evalbin/`, `tests/test_eval_kit.py`):

- `evals/_kit/__init__.py`, `recipes.py` (`Recipe`, `RECIPES`, `CORRECT_PATHS` vuoto: lo riempiono i Task 8-10 coi `case.yaml`),
  `scaffold.py` (`build`, `main`, `Built`, `ScaffoldError`), `target.py` (`build(plugin_root, out)`).
- `evals/_kit/fixtures/`: `project/` (progetto Python con `unittest`, `tools/unittest_junit.py` copiato da `spikes/p4/make_case.py`,
  `tollgate.toml` con `verify`/`gate`/`report junit`), `plans/calc-l1.md` e `calc-l2.md`, `specs/calc-l2.md`,
  `changes/` (i file che implementatore e sessione principale committano: `calc-l1/1`, `calc-l1/2`, `calc-l0`).
- `tests/evalbin/gh` (shim: esegue `tests/fakegh.py` sui dati di `$HOME/.tollgate-eval/`, senza dati esce 1 con
  «gh finto dell'eval: dati assenti», mai un altro `gh`), `tests/evalbin/python3` (da `spikes/p5/probe-bin/python3`).
- `tests/test_eval_kit.py` (34 test).

Come funziona `scaffold.build(recipe, workspace, home, state)`: nessun import di `tollgate_*` né di `sqlite3` (test AST). Tutto passa da
processi: `bin/tollgate` (`start`, `task start|review-prepare|done`, `verify`, `audit prepare`, `act apply`, `finish check|open-pr`,
`status --json`, `--version`), `hooks/run` (PreToolUse/PostToolUse Bash, PostToolUse Write, PreToolUse Agent, SubagentStart/Stop,
UserPromptExpansion) e `tests/fakegh.py` via `TOLLGATE_GH`. L'ambiente dei sottoprocessi toglie ogni `TOLLGATE_*`, `GIT_*`, `CLAUDE*`
ereditati e mette `HOME`, `TOLLGATE_STATE` (la cartella predefinita della HOME con la sentinella, o `state` se dato), `TOLLGATE_GH`,
`TOLLGATE_FAKEGH_DATA/LOG`, `TOLLGATE_GH_RETRY_DELAYS=0,0`, `PYTHONDONTWRITEBYTECODE=1`; il processo padre non cambia mai
(`os.environ` identico prima/dopo, test) e nessun file della corsa nomina `TOLLGATE_*` o un `TOLLGATE_STATE` altrove.
Il segnale della sessione `scaffold` lo scrive `hooks/run` dal PreToolUse di Bash, solo per `start`, `act apply`, `finish ...` (D15);
`task start` gira con la cwd nel worktree. I `commit` li registra `hooks/run` dal PostToolUse di Bash.
`scaffold.py` è uno script (`sys.dont_write_bytecode = True`, import assoluto `evals._kit.recipes` con la radice in `sys.path`, nessun
import relativo), eseguibile; `target.py` anche.

### Primitive (ricette) e loro sequenza

| Ricetta | Sequenza (tutta dal programma vero) | Fase finale | `build` |
|---|---|---|---|
| `l0-execution` | `PreToolUse` Bash → `start 1` | execution | 1,1 s |
| `l0-review` | + commit di `calc-l0` (PostToolUse Bash) → `finish check` (con `verify` dentro il comando) | review | 2,1 s |
| `l0-pr-open` | + `UserPromptExpansion` `tollgate:finish` → `finish open-pr` (push sul nudo locale, `pr create` del gh finto) | pr_open | 3,1 s |
| `l0-level-cap` | `UserPromptExpansion` `tollgate:approve level L0 …` (sessione `scaffold`) → `PreToolUse` → `act apply` | execution, `level_cap` L0 | 1,9 s |
| `l1-plan` | `start 1 --level L1` | plan | 1,1 s |
| `l1-plan-registered` | + PostToolUse `Write` del piano → commit | execution | 1,8 s |
| `l1-execution` | + `task start 1` (task 1 running, pending launch) | execution | 2,0 s |
| `l1-task-done` | `task start 1`, PreToolUse `Agent`, SubagentStart implementatore, commit con agent_id, `verify`, SubagentStop con report 18.5, `task review-prepare 1`, SubagentStart/Stop revisore con verdetto (sha e code letti dal brief), `task done 1` | execution | 4,3 s |
| `l1-review` | task 1 e 2 fatti + `finish check` | review | 7,7 s |
| `l2-spec-audit` | `start --level L2` + spec committata | spec_audit | 1,6 s |
| `l2-spec-audited` | + `audit prepare` → SubagentStart/Stop dell'agente del giro con la riga JSON del brief (conteggi a zero) → commit del report | spec_audit (prossimo passo: approve spec) | 2,8 s |
| `l2-spec-approved` | + `UserPromptExpansion` `tollgate:approve spec 1` → `act apply` → commit di `spec-approval.md` | plan | 3,9 s |

Tutti sotto i 120 s (il più lungo 7,7 s a macchina scarica; `test_build_under_120_seconds` costruisce `l1-review`).
Ogni `build` termina con un controllo: la fase di `status --json` deve essere `recipe.phase`.

## Scostamenti dal piano e perché

1. `Recipe` ha campi in più (ordine D6/D7, «può ricevere i campi che servono»): `change` (L0: cartella di `fixtures/changes/` committata dalla
   sessione principale), `audit_rounds`, `acts` (atti con sessione `scaffold`), `finish` (`check|open-pr`). Servono a descrivere la sequenza
   senza codice per ricetta. `extra_files` sono file del progetto di base (commit `base` su main), non del worktree. Il costruttore rifiuta
   combinazioni incoerenti (piano in L0, spec fuori da L2, `open-pr` fuori da L0).
2. `finish open-pr` solo in L0: in L1 e L2 `open-pr` esige un ciclo di revisione finale `ok` (`openpr.review_state`), cioè agenti
   `final-reviewer` e `review prepare`; non è tra le primitive del ruling e non l'ho costruito. `finish check` è provato anche in L1 (`l1-review`).
3. L2 è costruito fino a `approve spec` (fase plan). Piano L2, giri sul piano e `approve plan` non ci sono: se un caso li vuole, il Task
   8-10 li compone con `audit_round`, `register_plan` e `user_act` (già generici); servirà un campo d'ordine oltre a `audit_rounds` e `acts`.
4. Dopo ogni atto e ogni giro lo scaffold committa i file nuovi di `reviews/<N>/` (report e approvazioni): i non committati non contano per `audit prepare`.
5. `.git/info/exclude` (I1): `/.origin.git/` e i segnaposto della sandbox, con `/.claude/*` e non `/.claude/`: i worktree stanno in
   `.claude/worktrees/` (già escluso da `start`) e il progetto di prova non versiona nulla sotto `.claude/`, quindi escludere il contenuto non nasconde
   niente. File aggiunti sempre espliciti (`git add -- <percorsi>`, mai `-A` dopo il commit base).
6. Nome e posta di git in `.git/config` del checkout (`user.name=eval`, `user.email=eval@example.invalid`, `commit.gpgsign=false`): la HOME della corsa
   non ha `.gitconfig`, senza questo l'agente non potrebbe committare (test `test_agent_can_commit_with_the_run_home`).
7. `target.build` copia con una lista di esclusione (`.git`, `.github`, `.claude`, `.superpowers`, `docs`, `spikes`, `tests` tranne `evalbin` e
   `fakegh.py`, `__pycache__`) invece di una lista di inclusione: una cartella nuova del plugin entra da sola. Toglie solo `dependencies`.
   Riscrive solo una cartella di uscita che ha creato (marcatore `.tollgate-eval-target`) o vuota; rifiuta un'uscita dentro o sopra la radice.
8. Guardie dello scaffold: rifiuta una HOME con `.claude/settings.json`, una cartella di stato non vuota, un workspace non vuoto.

## Esito di VE12 / D1 (workspace che coincide col worktree del lavoro)

**Funziona, solo con il programma**, ma la strada è `adopt`, non `start`. Prova (script nella scratchpad, riprodotta con il banco):
1. checkout principale in `$HOME/proj` costruito come `_make_checkout` (origin nudo, gate, `tollgate.toml`);
2. il workspace è un worktree di quel checkout, creato con `git worktree add <workspace> -b tg/1-aggiungi-la-moltiplicazione`;
3. `UserPromptExpansion` `tollgate:adopt #1` (sessione `scaffold`, cwd `$HOME/proj`), poi `PreToolUse` e `tollgate adopt 1` dal checkout principale.
Esito: `lavoro #1 adottato: livello L0, fase execution … worktree esistente riusato: <workspace>`; `status --json` lo vede; un `SessionStart` con
`session_id` nuovo e `cwd` = workspace risponde `tollgate: lavoro #1 (L0), fase execution` e **lega la sessione** (`state/bound/run-1`).
Limiti: `start` non può farlo (crea il worktree sempre sotto `<checkout principale>/.claude/worktrees/` e riprende quello registrato, non c'è
un comando che sposta il percorso); `adopt` ricostruisce lo stato dalle prove nel ramo e nella PR, quindi livello e fase vengono dal ramo e i task
risultano `pending` (nessun task running o done, nessun ricevuta). Va quindi bene per stati L0 o L1 con piano committato, non per «task in
corso». Non l'ho messo come opzione di `Recipe` (richiederebbe lo slug del ramo, che lo calcola il programma e non va replicato): se il controller
sceglie questa forma per e2/e4 è un campo `workspace_is_worktree` con `git worktree add` + `adopt`, da provare con un test come gli altri.
Nella sandbox VE12 aveva già mostrato che `git status/log/commit` funzionano con il gitdir sotto la HOME.

## Dubbi

- `start` (anche in ripresa) fa sempre `git config tollgate.defaultBranch main` (`bin/tollgate_flow/start.py`, `gitw.set_config`), anche se il valore
  è uguale: se la sandbox nega davvero `.git/config` (il rapporto dice «da trattare come negato finché non provato») un `start` lanciato dall'agente
  fallirebbe con «scrittura della configurazione git non riuscita». Lo scaffold lo imposta già, ma i casi non devono far rilanciare `start`
  all'agente finché non si prova. Non l'ho toccato (fuori dal task).
- `repo_key` è l'URL espanso da `insteadOf` e in minuscolo (`/…/ws.xxxx/.origin`), come nei test di P3a: coerente tra hook e CLI, ma non è un URL github.
- `CORRECT_PATHS` è vuoto: dipende dai `case.yaml` (Task 8-10).

## TDD, test e commit

- RED: con `evals/_kit` e `tests/evalbin` spostati altrove, `python3 -B -m unittest tests.test_eval_kit` →
  `ModuleNotFoundError: No module named 'evals._kit'`, `Ran 1 test … FAILED (errors=1)`.
- GREEN mirato: `python3 -B -W error::ResourceWarning -m unittest tests.test_eval_kit` → `Ran 34 tests in 54.084s OK`;
  `python3.11 -B -m unittest tests.test_eval_kit` → `Ran 34 tests in 53.073s OK`. Un solo errore al primo giro (un test che scriveva un
  file dove c'era la cartella `.origin.git`): corretto nel test.
- `tests/run` (python3.11 poi python3): `Ran 2695 tests in 794.465s OK (skipped=2)` e `Ran 2695 tests in 776.540s OK`, output pulito.
- Commit: vedi `git log -1` («tollgate P5: banco degli eval (scaffold dal programma vero, gh finto, ricette)»).

## Fix round 1
1. `_check_places`: il workspace può contenere solo i segnaposto noti (file vuoti, cartelle di soli file vuoti, nessun symlink); altro, o un segnaposto non vuoto, è rifiutato. `/.claude` aggiunto a `EXCLUDES` (copre `.claude` come file).
2. `_hook`: ferma lo scaffold se stdout ha `permissionDecision` deny/block o `decision` block/deny anche con uscita 0 (l'uscita 2 già falliva).
3. HOME: rifiuta se uguale a `pwd.getpwuid(os.getuid()).pw_dir` risolto, o se `installed_plugins.json` esiste già.
4. `target.py` tiene `docs/uso/` se esiste.
Test nuovi: workspace con segnaposto accettato / altro rifiutato, HOME vera e registro esistente, deny degli hook, `docs/uso` nella copia. `test_eval_kit` 38 OK (con `-W error::ResourceWarning`); `tests/run`: python3.11 `Ran 2699 OK (skipped=2)`, python3 `Ran 2699 OK`.
