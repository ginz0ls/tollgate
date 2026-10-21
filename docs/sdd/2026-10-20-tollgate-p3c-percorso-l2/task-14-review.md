# Revisione Task 14: prova reale del percorso L2 (46c0dd0..4142e88)

Evidenze lette in sola lettura sotto `/tmp/tollgate-p3c/flow` (logs, eventi, `reviews-1/`, repo e worktree) e in `/tmp/tollgate-p3c-keep/tentativo1-logs`.

### Aderenza
- ✅ Giri e esiti: `spec-adversarial` 1 `findings` (0/0/1/2), 2 `empty`; `plan-adversarial` 1 `empty` (solo un minor) e 2 `empty`. Eventi `spec_audit_round` e file `reviews-1/` coincidono col rapporto.
- ✅ `spec_sha` in `plan-approval.md` = `a4816f6b…` = blob della spec a HEAD (`git hash-object`); `plan_sha` `f7340037…` = blob del piano a HEAD = `plan_sha` dell'evento `scope_registered`; `spec-approval.md` ha `sha` `a4816f6b…`.
- ✅ Task 1 `done` (evento `task_change` done/approved, ricevuta verify green, 2 test, `status`: «task: 1 done»); veti 0 nella prova finale (`stats.json`); veto `pre_bash` solo nel tentativo scartato (`tentativo1-logs/events.jsonl`, sessione `fceacf93`), come dichiarato in D1.
- ✅ Token 155743 = 38150+47842+45142+24609; costi per passo sommano a quanto elencato; versione `claude` 2.1.304 e modello `claude-sonnet-5-5` nei log.
- ✅ Sessioni: sei id distinti, cwd dei passi 2-6 = worktree `tg-1-*` sotto `$FLOW` (`sessioni.txt`); gli atti `a-1` e `a-2` portano `source: claude-code` e la sessione del passo.
- ✅ Nessun push (`origin-refs.txt`: solo `main` alla base), `hooks.log` e `*.err` vuoti, `~/.local/state/tollgate` assente, `gh` usato solo dalla CLI via `fakegh` (4 chiamate in `fakegh.log`); nei log dei passi nessun `gh`, `curl`, `git push` digitato dal modello (verificato su tutti i `tool_use` Bash dei sei passi e del tentativo scartato).
- ✅ Ruling del controller dichiarata: D1 spiega la spec scritta dal modello, la spec unica accettata, il ramo `spec-L2.md` non esercitato. Elenco del non esercitato presente (lenti, `reopen`, `--spec`, tetti, interattivo, `finish`, `gh` vero).
- ❌ Vedi Important 1 e 2: due affermazioni del rapporto non reggono alle evidenze.

### Punti di forza
- Evidenze verificabili e coerenti nel resto (numeri, sha, eventi); il rapporto distingue il tentativo scartato e il veto che contiene.
- Script solido sulle cautele: `FLOW` fisso (nessun override da ambiente) con guardia prima del solo `rm -rf "$FLOW"`; `rm -rf "$LOGS/reviews-1"` resta sotto `FLOW` costante; `claude -p` sempre con `--plugin-dir`, `--model sonnet`; passi 2-6 con cwd del worktree verificato (ramo `tg/1-*`, sotto `$FLOW`, `run-p3c-flow.sh:225-228`); `verifica_push` prima di ogni passo (`:222`); `TOLLGATE_STATE` con sentinella (`:62`, `:103`); nessun `pkill`/`kill`; mai `--continue`; nulla scrive sotto `~/.claude` (lo fa solo il processo `claude`, dichiarato).
- Verifica di `check_plan`/`pitch_problems` in `prepara` prima della prova.

### Rilievi

**Important 1: il piano di prova è stato usato, il rapporto dice di no.**
Rapporto, tabella passo 4 («usato … solo come indicazione») e «Ciò che resta non esercitato» («il piano di prova `piano-L2.md` (… non usato)»). Evidenza: `passo4.jsonl` ha `Read /tmp/tollgate-p3c/flow/piano-L2.md` e poi `Write` del piano; `git show 486c3ab:docs/superpowers/plans/2026-10-20-prova.md | diff - piano-L2.md` è vuoto: il primo piano committato è byte per byte `piano-L2.md` (blob `6ad777ba…`); solo la correzione del giro 1 (`4aca8f5`) lo cambia in `f7340037…`. Il piano approvato è quindi il piano di prova più una correzione, non «scritto dal modello». Correggere il rapporto: piano di prova copiato con Write (come da brief), giro 1 con un minor, correzione del modello; togliere `piano-L2.md` dall'elenco del non esercitato.

**Important 2: la versione dello script che ha eseguito il passo 1 non è quella committata, e il rapporto non lo dice.**
`logs/exit-codes.txt` termina il passo 1 con «NOTA: il passo 1 ha lasciato una spec … rifare il passo 1»: è il vecchio `passo1` che si fermava (anche nel tentativo scartato). Il `passo1` committato (`run-p3c-flow.sh:290-301`, nota «ha scritto la spec del modello (N file)» e arresto se N>1) non è mai girato; `tutto` non è mai stato eseguito end to end; il passo 1 è stato accettato dopo aver modificato lo script. La tabella dice «riuscito al secondo tentativo» e D1 descrive il comportamento nuovo come se fosse provato. Dichiarare: passo 1 con lo script in forma precedente (esito per giudizio, 2 esecuzioni entrambe fermate dal controllo), ramo nuovo di `passo1` e `tutto` non esercitati; il solo ramo nuovo girato è quello `spec_nel_ramo` di `passo2` (`:304-310`).

**Important 3: lo script non protegge dal `gh` vero né dalla rete digitati dal modello.**
`claude_step` (`:231`) passa `--allowedTools Bash` senza restrizioni e non mette `fakegh` nel `PATH`: `TOLLGATE_GH` vale solo per la CLI. Con più fette la decisione 22 fa creare le issue al modello con il proprio `gh issue create` (e `finish` userà `gh pr create`): finirebbero sul `gh` vero con il token dell'utente, contro `cautele.md`. In questa esecuzione non è successo (log verificati), ma il rischio è dello script. Correggere: cartella `$FLOW/bin` con un `gh` che esegue `tests/fakegh.py` messa in testa al `PATH` di `claude -p`, oppure `--disallowedTools` su `Bash(gh:*)`, `Bash(curl:*)`, `Bash(wget:*)`.

**Important 4: l'esito di `claude_step` non si propaga.**
`passo3`..`passo6` e `passo2` finiscono con `registra` (`:315-318`), il cui codice di uscita sostituisce quello di `claude_step` (`:231-233` ritorna anche l'`echo`/`tee`, non il `$rc`): un fallimento di `verifica_push`, della verifica del worktree o un `timeout` non fermano `tutto`, che prosegue ed esce 0. Le cautele restano in piedi (`claude` non parte se i controlli falliscono), ma «tutto» può dichiarare successo senza averlo. Correggere: `claude_step ... || return 1; registra`, e fare ritornare `$rc` a `claude_step`.

**Minor**
- `--add-dir "$FLOW"` (`:231`): serve solo a leggere `spec-L2.md` e `piano-L2.md` (usato davvero al passo 4), ma con `acceptEdits` apre in scrittura anche `state/`, `origin.git` e `logs/`. Valutazione: tenerlo è corretto, restringerlo è meglio: spostare i due file in `$FLOW/input` e passare `--add-dir "$FLOW/input"`.
- `worktree_lavoro` (`:211`) legge il percorso con `awk '{p=$2}'`: si rompe con spazi nel percorso (oggi `/tmp` senza spazi, non rilevante qui).
- `verifica_push` controlla l'URL di push solo prima del passo; il modello potrebbe cambiarlo durante il passo (non è successo). Accettabile, ma il rapporto dice «prima di ogni passo» e va letto così.
- Veti: la sezione «Veti, token» dice 0; è la prova finale. Il veto del tentativo scartato è in D1: bene, richiamarlo in una riga anche lì.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** l'esecuzione reale è solida e quasi tutti gli esiti sono sostenuti da evidenze, ma il rapporto afferma il falso sul piano di prova (usato verbatim) e tace che il passo 1 è girato con una versione dello script diversa da quella committata; lo script lascia inoltre il `gh` vero raggiungibile dal modello e non propaga l'esito dei passi. Correzioni al solo rapporto e allo script, nessuna ripetizione della prova necessaria per i primi due punti.
