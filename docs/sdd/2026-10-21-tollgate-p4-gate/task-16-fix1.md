# Task 16 — giro di correzione 1

Leggi `task-16-review.md` (stessa cartella) per i dettagli e le righe. Correggi tutto quanto segue. Le cautele del dispatch originale restano valide: solo `bash -n` e `controlla`, mai rete, mai `gh` vero, mai `claude`.

## I-1 (Important) — nel passo con `claude -p` la guardia deve essere un vincolo, non un consiglio
- Il wrapper `gh` messo nel PATH del flusso fissa profilo `flow`, repo `ginz0ls/tollgate-p4-detect` e il percorso del gh vero **dentro il wrapper stesso** (scritti al momento della generazione, non letti da `P4_PROFILE`/`P4_REPO`/`P4_REAL_GH` dell'ambiente). Variabili d'ambiente diverse non devono cambiare niente: test che lo dimostra (ambiente con `P4_PROFILE=script` → la chiamata vietata resta rifiutata).
- `DISALLOWED` di `run-p4-flow.sh` vieta anche: `git push` con `-f`/`--force`/`--force-with-lease`/`+refspec`, `git push` verso `main`, invocazioni di gh per percorso (`*/gh`), `env`, `command gh`, `exec`, impostazione inline di `P4_*`. Se il formato delle regole di Claude Code non permette un divieto pulito, documentalo nel rapporto e affidati all'audit qui sotto.
- `flowcheck.gh_invocations` riconosce gh anche dopo assegnazioni inline, `env`, `command`, percorsi assoluti, dentro `&&`/`;`/`|`.
- Audit a valle obbligatorio: `run-p4-flow.sh registra` confronta `gh-wrap.log` (ogni chiamata passata dal wrapper) con le forme ammesse e con le invocazioni viste nel transcript; qualsiasi chiamata fuori elenco, o un `git push` forzato/verso main nel transcript, rende il caso «non riuscito» con riga esplicita nel rapporto. Test con transcript finti per ciascun aggiramento della revisione.

## I-2 (Important) — `error-sha-superato`
Togli l'attesa `merge_state` da p1; tienila solo su p2. Aggiorna il test che confronta le attese.

## Minori (entrano tutti)
- M-1: tutte le uscite di `run-p4-flow.sh` e `installa-<n>-baseline-file.txt` passano per la rotazione: una seconda `registra` non perde nulla. Test.
- M-2: `repo create --public` ammesso solo per `tollgate-p4-protected`; endpoint `gh api` che contengono `/secrets` rifiutati. Test in `test_p4_ghguard`.
- M-3: `SHAPES` di `flowcheck.py` usa il percorso vero del corpo (`<worktree>/.tollgate-run/<N>/pr-body.md`, come `bin/tollgate_flow/openpr.py`) sotto `$FLOW`.
- M-4: profilo `flow` ammette solo le forme di `SHAPES` (o aggiungi a `FLOW_FORBIDDEN` `issue close`, `issue comment`, `pr comment`, `pr edit --base`). Test.
- M-5: `detect-merge-rosso` resta l'ultimo caso detect; assert nel test sull'ordine e nota nello scheletro del rapporto della prova sul fatto che degrada la base di detect.
- M-6: lo script giudica il criterio 34 (riga «riuscito/non riuscito» se il conteggio delle issue dopo il primo push non è 0; errore di `jq` non mescolato al valore).
- M-7: la conferma sul pubblico non dipende da `P4_CHECK` letto dall'ambiente: il modo `controlla` lo segnala con una variabile interna non esportata o con un argomento.
- M-8: «38 casi» → 37.

Commit nuovo «tollgate P4: correzioni della revisione degli script della prova (Task 16, giro 1)» con «Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>» (scrivi esattamente questa riga). Aggiungi al report una sezione «Giro 1».
