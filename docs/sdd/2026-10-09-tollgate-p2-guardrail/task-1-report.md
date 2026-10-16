# Task 1: report

Stato: DONE_WITH_CONCERNS.

## Cosa è stato fatto
- Step 1-2: creati `spikes/hookprobe/agents/probe-turns3.md` e `spikes/run-p2-experiments.sh` (eseguibile) come da brief, testo invariato.
- Step 3: `bash spikes/run-p2-experiments.sh` (da `/tmp/tollgate-p2/turns`, `--plugin-dir` assoluto, `--permission-mode manual` accettato). Output atteso `e7/e8/e9 .jsonl/.out, probe.jsonl, turns`.
- E9 con `manual`: le `Write` sono negate dai permessi (`PreToolUse` sì, `PostToolUse` no). Ripetuto una volta con `--permission-mode acceptEdits` dalla stessa cartella (script temporaneo `/tmp/tollgate-p2-e9b.sh`, uscite `e9b.*`): tutti gli eventi presenti. Mai `bypassPermissions`.
- Step 4: campioni presi da `e9b.jsonl` (non `e9.jsonl`), anonimizzati con `/home/USER`: nessuna riga `MANCA`. Chiavi: `PreToolUse-Write`, `PostToolUse-Write`, `PreToolUse-Edit`, `PostToolUse-Edit`, `PostToolUse-Skill`, `PreToolUse-Write-subagent`. Il campo `permission_mode` di questi campioni è `acceptEdits`.
- Step 5: letto `task-1-docs.md`. D2 per `PreToolUse` è risolto dalla documentazione: nessun esperimento `MARCATORE-CTX-77`, `probe.sh` non toccato (diff vuoto). Controllo aggiuntivo in sola lettura: `git ls-remote --tags https://github.com/obra/superpowers` (solo `v6.4.1`, `v6.4.2`).
- Step 6: `docs/verifiche/2026-10-09-p2-verifiche.md`.
- Step 7: spec rev 21 (intestazione, 3.2 eventi e `record`, 16 con nuova tabella e «Ancora da verificare» ridotto, 20 riga 21).
- Test: `tests/run` OK con python3.11 e python3 (124 test).

## Esiti decisivi
- E7: taglio in background applicato, nessun `SubagentStop`; arriva `UserPromptSubmit` con `<task-notification>` e «stopped at its 2-turn limit».
- E8: `maxTurns` riparte da zero alla ripresa (3 letture, poi taglio invece di 5); stesso riconoscimento via `UserPromptSubmit`; nessun secondo `SubagentStop`; `PostToolUse SendMessage` non porta il taglio.
- D1: tag documentati `<plugin>--v<versione>`; Superpowers ha solo `v6.4.1`/`v6.4.2` -> nessun `version` in `dependencies`, ripiego di 11.1.
- D2: `additionalContext` per SessionStart, SubagentStart (al subagente), UserPromptSubmit/Expansion, PreToolUse, PostToolUse, Stop, SubagentStop; uscita 2 come da documentazione.
- D3: `NotebookEdit` con `notebook_path`; `MultiEdit` non documentato.

## Autoverifica
Righe E7, E8, E9, D1, D2, D3 presenti; sezione «Conseguenze» con INJECT_MODE, `version` e riconoscimento del taglio; nessun esito inventato.

## Concerns
- D1 «no» si basa su documentazione e tag elencati, non su un'installazione reale (vietata dalle cautele).
- D2 e D3 sono solo da documentazione; l'input reale di `NotebookEdit` non osservato.
- I campioni hanno `permission_mode: "acceptEdits"`, mentre i precedenti sono `default`.
- Il rapporto propone un evento d'ingresso per `UserPromptSubmit` (`prompt_submit`) o un ramo in `post_agent`: scelta del controller per il Task 18; la spec rev 21 non lo aggiunge all'elenco (il brief non lo chiedeva).
- Il `<summary>` della notifica porta la descrizione del lancio, non il nome: la ricerca del task è per `agent_id`.
- Script esperimenti helper in `/tmp` (`/tmp/tollgate-p2-*.py|sh`), fuori dal repo.

## Fix round 1
Modifiche (solo documentali):
1. Spec 6.3: tolto «Restano da verificare…»; descritto il riconoscimento via `UserPromptSubmit` con `<task-notification>`, evento `prompt_submit` (esce con 0 senza `<task-notification>`, altrimenti `blocked`/`needs_you` e chiusura della riga in `subagents`), `stale_minutes` come rete. `prompt_submit` aggiunto agli eventi d'ingresso di 3.2, all'intestazione rev 21 e alla riga 21 di 20. Il rapporto P2 cita la stessa decisione (supera la nota «concern» sopra sull'evento non aggiunto).
2. Spec 11.1: niente più `>=6.4.1 <7.0.0` né prefisso `v`; Superpowers senza `version`, controllo in `start` (P3), convalida con `claude plugin validate`. Riga tag di 16 corretta (tag `v6.4.1`/`v6.4.2`; documentazione `<plugin>--v<versione>`). Tolta la voce duplicata da «Ancora da verificare».
3. Rapporto D1 e conseguenza riscritti come «probabile, dipende dal tipo di sorgente di Superpowers nel suo marketplace (non verificato)», con la distinzione repository proprio / percorso relativo. Scelta di non mettere `version` mantenuta.

Comando: `tests/run`. Output: python 3.11.16 e 3.13.5, ciascuno `Ran 124 tests ... OK`.
