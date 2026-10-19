# Report Task 1 (P3a): verifiche di piattaforma

Status: DONE. Il rapporto completo (comando, evidenza, esito per V1-V5) è `docs/verifiche/2026-10-16-p3a-verifiche.md`; qui il riepilogo.

| Id | Esito | Evidenza in breve |
|---|---|---|
| V1 | sì | `claude -p --plugin-dir spikes/hookprobe ... "invoca con lo strumento Skill la skill hookprobe:probe-root ..."`: la risposta riporta `RADICE=<worktree>/spikes/hookprobe SKILLDIR=.../skills/probe-root`, variabili già espanse (percorsi con spazi) |
| V2 | sì, informativo | Solo nomi. Presente `CLAUDE_CODE_SESSION_ID`; assente `CLAUDE_PLUGIN_ROOT` nell'ambiente di Bash |
| V3 | sì | `hs.txt` scritto dal `PreToolUse` (ramo temporaneo di probe.sh) è letto dal `cat` successivo; `stdout` = `session_id` della sessione. Decisione 2 confermata |
| V4 | sì | `claude plugin validate` su copia in `/tmp`: passa con 2 avvisi (description marketplace, author); `--strict` fallisce; con description + author passa `--strict` |
| V5 | sì | `PreToolUse NotebookEdit`: `notebook_path`, `new_source`, `cell_type`, `edit_mode`; campione aggiunto a `samples.json` |

Scostamenti dal piano: nessuno di sostanza. Il ramo temporaneo di `probe.sh` è stato tolto con `git checkout` (diff contro main vuoto); la copia `/tmp/tollgate-p3a/mkt` è stata rimossa con `git worktree remove --force`.
Nessun esito ripetuto: tutti chiari al primo giro.
Cautele rispettate: nessun plugin installato, nessun accesso a `~/.claude/settings.json`, `~/.claude/plugins/`, `~/.local/state/tollgate`; V2 senza valori.

## Fix round 1

- V4 rilanciato su directory (copia --detach in /tmp, poi rimossa) con `claude plugin validate --strict /tmp/tollgate-p3a/mkt`:
  - (b) author solo in plugins[0], plugin.json com e oggi: avvisi su marketplace e plugin.json, Validation failed, uscita 1 (/tmp/tollgate-p3a/v4-fix-b.out).
  - (a) author in plugins[0] e in plugin.json: Validation passed, uscita 0 (v4-fix-a.out). Il blocco "Validating plugin" compare solo con avvisi; controprova --strict sul solo plugin.json: passa.
  - Esito aggiornato: aggiungere author a plugin.json ora e dimostrato; author solo in plugins[0] non basta per --strict.
- Rapporto: sezione "Come ripetere gli esperimenti" (snippet del ramo temporaneo di probe.sh e comandi di V4); corretta la frase su CLAUDE_PLUGIN_ROOT (provata solo per le skill); annotato il limite su SKILLDIR.
- Test: tests/run, python3.11 e python3.
