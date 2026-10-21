# Task 14: report

Esito della prova: **riuscito** (passi 2-6), **composito** per il passo 1 (due tentativi) e con la variante del passo 2 (spec scritta dal modello). Dettaglio in `docs/verifiche/2026-10-20-p3c-prova-flusso.md`.

## Implementato
- `spikes/run-p3c-flow.sh` (`prepara|passo1..passo6|libero|registra|tutto`), sul modello di `run-p3b-flow.sh`: `FLOW` fisso a `/tmp/tollgate-p3c/flow` con guardia prima di `rm -rf`, remoto finto con `insteadOf` e controllo del push prima di ogni passo, `fakegh`, spec e piano di prova verificati da `specdoc`/`plan.check_plan` (L2), dal passo 2 cwd = worktree `tg/1-*` sotto `$FLOW` verificato, mai `--continue`, `--add-dir $FLOW` per leggere i file di prova, `sessioni.txt` con id e cartella di ogni passo, copia dei report `reviews/1`.
- Rapporto `docs/verifiche/2026-10-20-p3c-prova-flusso.md`.

## Esito dei passi
1. `/tollgate:start #1 L2`: il modello fa brainstorming e scrive/committa una spec sua (2 esecuzioni su 2). Il brief fermava lo script ("rifare il passo 1"): ripetere non serve, quindi scostamento dello script (vedi sotto), non difetto di P3c.
2. Spec-audit: giro 1 `findings` (1 moderate, 2 minor), spec corretta, giro 2 `empty`; `audit prepare` chiede `approve spec 1`.
3. `approve spec 1`: `spec-approval.md` con sha della spec, fase `plan`.
4. Piano scritto con Write, giro 1 plan-adversary (1 minor), correzione, giro 2 `empty`, fase `approval`.
5. `approve plan`: `plan-approval.md` (`sha` = `plan_sha` blob del piano, `spec_sha`), fase `execution`.
6. `execute`: task 1 `done` (ricevuta verify green, 2 test, revisore approved).
Veti 0, blocchi 0, token 155743, `hooks.log` e `*.err` vuoti, nessun push (origin.git solo `main`), `~/.local/state/tollgate` assente.

## Scostamenti dal brief
- Passo 1: invece di fermarsi se c'e' una spec, lo script accetta una sola spec scritta dal modello e il passo 2 la usa (altrimenti ricade sulla copia di `spec-L2.md`, ramo non esercitato). Motivo: l'ipotesi del brief e' smentita da due esecuzioni; il primo tentativo e' scartato (log in `/tmp/tollgate-p3c-keep/tentativo1-logs`), quindi passo 1 composito.
- `--add-dir "$FLOW"` aggiunto a `claude -p` per far leggere i file di prova fuori dal worktree.
- Nessun `libero` usato; nessuna correzione al codice di P3c.

## Test
Nessun codice di `bin/` cambiato. `tests/run` lanciato prima del commit (esito in fondo).

tests/run: python3.11 e python3 (3.13.5), 1731 test, OK, output pulito.

## Fix round 1

Cambiato in `spikes/run-p3c-flow.sh` e nel rapporto (nessun codice di `bin/`):
- I-1: rapporto corretto, il piano di prova e' stato copiato dal modello (blob 6ad777ba) e poi corretto (f7340037); tolto dal non esercitato.
- I-2: dichiarato che il passo 1 e' girato con la forma precedente dello script (D5); ramo nuovo di `passo1` e `tutto` non eseguiti nella prova di riferimento.
- I-3: shim `gh` in `$FLOW/shim` (esegue `tests/fakegh.py`), in testa al PATH dei `claude -p`; `verifica_gh` prima di ogni passo.
- I-4: `claude_step` ritorna l'uscita, `passo` registra e propaga; `tutto` si ferma al primo fallimento.
- Minori: `--add-dir "$FLOW/input"`, `worktree_lavoro` robusto agli spazi, `verifica_push` anche dopo il passo.
- Prova di riferimento conservata in `/tmp/tollgate-p3c/prova-1/flow`; il rapporto ha la sezione «Correzioni dopo la prova».
- Verifiche: `bash -n`, `prepara` ok (spec-check, plan-check), `command -v gh` con PATH dello shim = shim, `verifica_gh`/`verifica_push` ok, `passo2` senza worktree esce con errore senza lanciare claude.
- INCIDENTE: nel verificare ho lanciato per errore `tutto`, che ha fatto partire `claude -p` (passi 1-3 e parte del 4, solo in /tmp/tollgate-p3c/flow, con shim, nessun push). Fermato per PID. Dichiarato nel rapporto; log in `/tmp/tollgate-p3c/prova-accidentale/logs`. Non e' evidenza.
- Test: `tests/run` rilanciato prima del commit (esito sotto).
tests/run dopo il fix: python3.11 e python3 (3.13.5), 1731 test, OK.
