# Ri-revisione giro 1 del Task 7 (51886dd..649edb3)

### Verdetti sui rilievi

**Workspace con soli segnaposto della sandbox (⚠️ di `_check_places`)** — INDIRIZZATO. `scaffold.py:167-181` (`_only_placeholders`) accetta solo nomi di `PLACEHOLDERS` (`:45-47`, stessi nomi di `EXCLUDES`), file vuoti, cartelle con soli file vuoti, nessun symlink; `:195` lo usa. Test `test_eval_kit.py` `test_workspace_with_only_sandbox_placeholders_is_accepted` (anche `.claude` come cartella e come file, e nulla tracciato) e `test_workspace_with_anything_else_is_refused` (file estraneo, segnaposto pieno, file dentro `.claude`, symlink). `StateTest` rilanciato: 13 OK.

**M4 `_hook` ignora un deny JSON con uscita 0** — INDIRIZZATO. `scaffold.py:112-131`: `_denied` copre `decision` block/deny e `hookSpecificOutput.permissionDecision` deny/block; l'errore riporta i primi 300 caratteri di stdout. Un JSON malformato o non-oggetto non ferma (corretto: `json.loads` sotto `startswith("{")`, e `isinstance(data, dict)` è ridondante ma innocuo). Test `test_hook_denial_stops_the_scaffold`: tre casi di rifiuto (due JSON, uscita 2) e il caso con `additionalContext` che passa.

**M3 HOME vera: `pw_dir` e `installed_plugins.json` esistente** — INDIRIZZATO. `scaffold.py:183-193`: confronto con `pw_dir` risolto, poi `settings.json`, poi registro già presente; tutti prima di scrivere. Test `test_refuses_the_users_real_home_and_an_existing_registry` (mock di `getpwuid`, registro lasciato intatto, nessun `.local`).

**M2/ECC `docs/uso/` nella copia di `target.build`** — INDIRIZZATO. `target.py:20` e ciclo `:57-59`; test `TargetTest` con `docs/uso/limiti.md` copiato e `docs/x.md` ancora escluso. (L'altra parte di M2, cioè le esclusioni restanti, non è cambiata: resta come era, già nota.)

### Danni nuovi nel diff della correzione

Nessuno Critical/Important.

- Minor: `/.claude` in `EXCLUDES` (`scaffold.py:48`). Verificato cosa tollgate legge sotto `.claude/`: `start.py:276` esclude già `.claude/worktrees` dal controllo di pulizia; `gitw.py:196` mette i worktree in `.claude/worktrees/` (working tree separati, non toccati dall'esclusione); `prereq.py:91` guarda `.claude/skills` per percorso nel filesystem, non per git; `protected.py:13` valuta `.claude/settings*.json` per percorso relativo, non per stato git; `cleanup`/`adopt` non toccano `.claude`. Quindi nulla che tollgate controlli viene nascosto. L'unico effetto: un `.claude/settings.json` nuovo creato da un agente nel checkout o in un worktree (l'esclusione è in `info/exclude`, comune) non comparirebbe in `git status` né in `git add -A`, quindi non entrerebbe in una PR senza `-f`. Era già così con `/.claude/*`; `/.claude` copre solo il caso del file. Da ricordare quando si scriverà un caso di eval che tenti di toccare i file protetti di `.claude/`: va scritto con `git add -f` o tracciato nel base, altrimenti il guard non lo vede mai.
- Minor: `_denied` (`:127`) controlla `isinstance(data, dict)` dopo `data.get(...)`: ridondante, perché `startswith("{")` e `json.loads` danno già un dict o un errore. Nessun effetto.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
