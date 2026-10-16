# Decisioni del controller da portare nei task (dallo scan pre-flight e dal Task 1)

Fonte: preflight-scan.md (conflitti numerati C1..C16) e docs/verifiche/2026-10-09-p2-verifiche.md. La spec rev 21 è l'autorità.

## Task 2
- C1: la migrazione 2 non deve creare backup su un DB appena creato. In `bin/tollgate_core/db.py::_migrate` leggere `fresh = current == 0` prima del ciclo e fare `backup(...)` solo se `not fresh`. Aggiornare `tests/test_db.py::test_migration_makes_backup_first` (righe ~71-85): migrazione finta con numero `db.latest_version() + 1` e ricerca di `*migrazione-3*.db`. Devono restare verdi `test_fresh_db_makes_no_backup_and_reopen_is_idempotent` e `tests/test_phases.py::test_set_phase_records_and_backs_up`.
- C16: `subagents.is_stale` è un Produces del Task 2 (il Task 18 la usa).

## Task 4
- C4: nel test di config usare `load_config_text(...)` (il file importa solo quel nome), non `config.load_config_text`.

## Task 6
- C11: `test_binary_and_latin1_do_not_crash` deve usare davvero byte non UTF-8 (es. `b"caff\xe8"`) in un file Latin-1.

## Task 7
- C7b: riconoscere `-c` anche nei flag combinati della shell (`bash -lc`, `sh -ec`, `-ic`), con test su `git push` annidato.
- C7c: `git commit -n` equivale a `--no-verify`, con test.
- C7d: le redirezioni numerate (`2>&1`, `2>/dev/null`, `1>x`) non lasciano un argomento spurio "2": il bersaglio di scrittura di `cp a b 2>&1` è `b`, e `rm -rf build 2>/dev/null` non aggiunge un bersaglio `2`. Con test.

## Task 9
- C3 (parte git): `git.toplevel(p)` per un percorso dentro una cartella `.git` (o dentro `.git/` di un repo, esistente o no) restituisce la radice del repo che possiede quella `.git` (ripiego: risalire alla componente `.git` e prenderne il genitore, oppure `rev-parse --git-common-dir`). Test: `test_toplevel_inside_git_dir`.
- C11: un test di `git._text` (o della funzione di decodifica) con byte `\xe8` non UTF-8.

## Task 10
- C13: `verify.run_verify` con un lavoro senza `work_base_sha` usa il `ref` di base invece di `None` (niente `TypeError` in `git.changes`). Test.

## Task 11
- C13: `waiver_cli.add_waiver` normalizza `file` in percorso relativo alla radice del worktree e rifiuta `type=test` senza `--test` (messaggio in italiano). Test.

## Task 12
- Ruling Task 1 / C2: nuovo evento d'ingresso `prompt_submit` (`UserPromptSubmit`), informativo (mai `deny`, mai uscita 2: bloccherebbe il prompt dell'utente). In `INPUT_EVENTS`, `_PLAIN["UserPromptSubmit"] = "prompt_submit"`.
- INJECT_MODE (esito Task 1 / D2): `additionalContext` per SessionStart, UserPromptExpansion, UserPromptSubmit, PreToolUse, PostToolUse, SubagentStart. Per `SubagentStop` e `SubagentHandback` (C6) nessuna iniezione: un `inject` su quegli eventi va scritto nel log degli hook (non su stderr con uscita 0, che Claude Code non mostra). Il veto di SubagentStop resta uscita 2 + stderr.
- C10: in `run_hook`, se `session_id` è vuoto il segnalino `bound/<session>` si ignora (non usare la cartella `bound` stessa).
- C11: `test_malformed_input_missing_fields` asserisce `2` esatto, non `(0, 2)`. Aggiungere un test del ramo `sqlite3.DatabaseError` del runner (modulo di prova che alza `sqlite3.DatabaseError` durante le operazioni → messaggio con suggerimento di `db restore`, uscita 2 per un hook di controllo, 0 per uno informativo).
- C3 (parte contesto): `Ctx.protected_roots(repo)` riceve il repo del contesto (toplevel del `cwd` dell'evento o worktree del lavoro), così `.git/hooks/**` e `.git/config` sono sempre tra le radici protette.

## Task 13
- Ruling Task 1 / C2: voce `UserPromptSubmit` in `hooks.json` (senza matcher) e in `test_manifest`. Il wrapper `hooks/run`, per `UserPromptSubmit`, esce subito con 0 se l'input non contiene `<task-notification>` (Python non parte a ogni prompt).
- C5: `plugin.json` dichiara la dipendenza da superpowers **senza** `version` (esito D1); `test_plugin_json` aggiunge `assertNotIn("version", dep)`. Niente campi `license` né `author` (nel repo non c'è LICENSE; scelta che resta all'utente in P3 con il marketplace).
- C10: `json_str` del wrapper prende la **prima** occorrenza della chiave (i campi di primo livello come `cwd`, `session_id`, `hook_event_name` precedono `tool_input`); `off <ore>` valida `command_args` con `^[0-9]+$` e usa `10#$HOURS` (altrimenti nessuna scadenza e un avviso); test con `08` e `0.5`.

## Task 15
- C3: Write/Edit su `<repo>/.git/hooks/x`, `<repo>/.git/config` negati come file protetti (sessione legata e non legata). Test.
- C9: escludere `[review] output_dirs` e `.tollgate-run/` da `level_records` (e dal calcolo della dimensione del diff) e dalla verifica di scope. Test con `reports/junit.xml` non ignorato.
- C13: `_inside` va in `_common.py` una volta sola e i moduli la importano (niente copie in `writes.py`, `bash_rules.py`, `commit.py`).

## Task 16
- C3: redirect, `touch`, `cp`, `tee` verso `.git/hooks/**` o `.git/config` negati; `git config <chiave> <valore>` (forme di scrittura, non `--get`/`--list`/`-l`) negato come scrittura di `.git/config` (file protetto). Test legati e non legati.
- C7a: `git push origin HEAD` e `git push -u origin HEAD` risolvono `HEAD` nel ramo corrente (`git.branch`) prima di applicare la regola sul ramo predefinito. Test dal checkout principale su `main`.
- C13: usare `_inside` da `_common.py`.
- C14: lo script non tracciato resta «effetto esterno» anche se ignorato da git (lettera di 8.5) — nessuna esenzione in P2.

## Task 17
- C8: `post_bash` registra `invalidate_finish(work, HEAD)` ogni volta che HEAD è diverso dallo SHA di un `finish` in attesa, anche senza commit nuovi (vincolo 3 del piano principale). Test: finish su A, reset --soft HEAD~1 → atto non più usabile.
- C9: escludere `output_dirs` e `.tollgate-run/` da `commit_violations`.
- C13: usare `_inside` da `_common.py`.

## Task 18
- Ruling Task 1 / C2 / C15: modulo nuovo `bin/tollgate_checks/prompt_submit.py` (ordine 20, evento `prompt_submit`): esce senza decisioni se il prompt non contiene `<task-notification>`; altrimenti, se contiene `stopped at its N-turn limit`, legge `<task-id>` come `agent_id` e registra la chiusura del subagente come tagliato, il task in budget superato e il blocco `needs_you` (componente `task_budget`), come il taglio in primo piano. Test con il campione `UserPromptSubmit-none` (o la busta di base) e `prompt` col testo di E7/E8 del rapporto.
- C12: i controlli da implementatore si applicano a ogni subagente non in sola lettura (glossario della spec, riga 22): resta come nel piano.

## Task 20
- Spec rev 21: citare 6.3 (taglio in background/ripresa, prompt_submit) tra le sezioni toccate; allineare i tre elenchi di decisioni per la rev 21 (titolo Files, Step 3, intestazione «Decisioni»). `Ctx.approved_waivers` resta come API per P3 (documentarla).

## Task 18 (aggiunta dopo la revisione del Task 2)
- Coprire con test `subagents.is_stale` e i rami no-op di `subagents.interrupt` (subagente non running; task non running) dove il Task 18 li usa.

## Task 13 (aggiunta dopo la revisione del Task 3)
- Il wrapper scrive `off.log` con un `>>` per evento (una scrittura breve per riga, mai un descrittore tenuto aperto), perché `offlog.import_log` reclama il file con un rename.

## Task 15 (aggiunta dopo la revisione del Task 4)
- I percorsi dello scope registrato (dal piano) sono nomi letterali (possono contenere [ ], es. app/[id]/page.tsx): quando il controllo di scope li confronta con globs, passarli per `globs.escape(path)`; i pattern di `[scope] always` restano pattern.

## Task 15 (aggiunta dopo la revisione del Task 5)
- `level_records` passa a `level.diff_level` un `changes` che include i file nuovi non tracciati (non ignorati) e `diff_bytes` = lunghezza del diff unificato dalla base + dimensione dei file non tracciati (decisione 18). Test.

## Task 20 (aggiunta dopo il Task 7)
- Spec 3.2, «I pattern usano ovunque il dialetto di .gitignore»: precisare «I pattern di percorsi»; i pattern di comandi (`[external_effects] allow`, comandi configurati) seguono fnmatch (`*` attraversa `/`).

## Task 19 (aggiunta dopo il Task 18)
- Un subagente tagliato da maxTurns ha gia la riga chiusa come `cut` (da post_agent o prompt_submit, helper `_common.budget_cut_records`). SubagentStop non deve chiuderla come `done` ne sovrascriverne lo stato: chiudi solo righe ancora `running`.

## Task 20 (ruling della sessione che la spec rev 21 deve riportare, oltre allo Step 3)
- 3.2: prompt_submit gia nell elenco (Task 1); aggiungere che i pattern di percorsi seguono .gitignore e quelli di comandi fnmatch (vedi sopra).
- 6.3: taglio in background/ripresa riconosciuto da un prompt che INIZIA con <task-notification>, blocco per blocco, frase in <summary>; la riga si chiude cut sempre, budget_exceeded e needs_you solo con task_budget acceso.
- 7.1/11.x: i messaggi di /tollgate:off e /tollgate:on escono su stdout come systemMessage + additionalContext (stderr con uscita 0 non arriva al modello); ore valide 1-9999; un modulo rotto su un evento informativo da un avviso con uscita 0; OFF si controlla prima di leggere l input.
- 6.2: la spec e il piano sono bloccati solo nelle fasi successive alla loro approvazione (dopo reopen tornano modificabili).
- 6.6: una sessione legata che scrive nel worktree di un altro lavoro attivo e negata; i file protetti valgono rispetto a ogni radice (repo piu vicino, worktree, checkout principale).
- 7.4: rm/rmdir/mv/git rm/unlink/find -delete su cartelle che contengono file protetti (anche via glob) negati; core.hooksPath negato a ogni livello.
- 8.5: l atto di un effetto si consuma a PostToolUse Bash (comando partito), non a PreToolUse; MCP resta al Pre (nessun PostToolUse MCP).
- 8.1: SubagentStop richiede tutti i comandi del gate green sull ultimo commit con la stessa regola della DoD (dod.receipt_verdict), oppure una related green; alla ripresa veti azzerati e, per la sola lettura, impronta ripresa (7.3).
- 18.5: uno status del report fuori dai 4 valori rende il report non valido (fail-closed).
- 18.2: waiver add --file e relativo alla radice del worktree; per type=test serve --test; una deroga copre una violazione con id solo se tutti gli id sono elencati.
- 8.2: test-guard conta salti e asserzioni anche sul testo grezzo (fail-closed); soglia rimossa o commentata = abbassata; file di copertura noti controllati ovunque nel repo.
- 11.1: (gia nel Task 1) dependencies senza version.
