# Revisione dei rapporti del Task 14 (eval reali e CI)

Verdetto: CONFORME CON RISERVE. Tutti i numeri di costo, punteggio e Δ coincidono con le evidenze. Restano due fatti del rapporto CI privi di prova su file (important) e un'etichetta di esito ambigua.

## Verificato e corretto
- `2026-10-23-p5-eval.md:23-35`: tutte le 13 righe coincidono con l'ultima `tabella.md` di ciascun caso (s5 e e3 dalle ripetizioni 26/10 01:02 e 00:07). Punteggi, Δ, corse, costo, durata, token.
- Costi (`:46-50`) ricalcolati da `budget.tsv`: sonde (10 righe, fino al 23/10) 0.7486; eval 25/10 (13 righe) 6.9257; ripetizioni 26/10 (3 righe) 1.3889; totale 9.0632; residuo 70.94. Tutto giusto.
- Δ medio dei casi spec (`:40`): (0.67+0.40+0.40+1+0.75+1+1+0.60+0.75)/9 = 0.73. Giusto.
- s5 (`:62-68`): 1° giro 0.00 (result.json 25/10 22:05, tutte le corse Bash), 2° giro 0.25 con 8 Write per corsa e nessun commit, 3° giro 0.75 vs 0.00. Nelle 3 corse con plugin `src/modulo.py` manca e non c'è alcun `git commit` nella trace. Nelle 3 senza plugin ci sono 8 Write e `git commit`. Nessun `piano-scritto`. Pesi 1/2/1 coerenti con 747bf13.
- e3 (`:56-60`): `start.py:404` chiama `gitw.set_config`. `gitw.py:116-122` è l'idempotenza con `--local --get-all`. Le trace del 1° giro mostrano `config.lock` come `/dev/null`. Commit 7485480 (gitw.py, test_start.py) e 747bf13 (`--local`) corrispondono a `git show --stat`.
- Passaggio dalla decisione 7: i 13 casi hanno punteggio con plugin >= 0,66 nell'ultima invocazione.
- Nessun token o segreto nei due rapporti.
- CI: SHA 87cc62f è la testa al momento del push (a9e2099 aggiunge solo rapporti e 8 righe di `comandi.log`). Le 8 righe nuove di `comandi.log` coincidono con la sequenza descritta (push 01:07:56, watch 01:08:38, view finali fino a 01:31:47, timing). Aritmetica coerente: 21:12 e 23:29, 1411 s, circa 45 minuti. Campi dello Step 4 presenti (run, SHA, job, durata, minuti, esito).

## Rilievi

### Important
1. `2026-10-23-p5-ci.md:5-11`: nessun file del repo contiene l'output di `gh run view` / `actions/runs/40252693867/timing` (`grep -rl 40252693867` trova solo il rapporto e `comandi.log`). Orari di inizio/fine dei job, durate, `billable.UBUNTU.total_ms = 0` e l'esito success non sono sostenuti da alcuna evidenza salvata, a differenza dei run delle sonde (`evidenze/p5/raccogli-timing-*.out`). Prova: `ls docs/verifiche/evidenze/p5` non ha file per questo run. Rimedio: salvare gli output (`gh run view --json`, `timing`) in `evidenze/p5/` e citarli.
2. `2026-10-23-p5-ci.md:12`: «la scansione dei token su tutta la storia ... non ha trovato nulla». L'unico file è `evidenze/p5/token-scan.txt` (23/10 21:06, righe `AMMESSO (P5_TOKEN_ALLOW_PATHS)`), precedente al push del 26/10, e mostra occorrenze ammesse, non «nulla». Nel `comandi.log` non c'è il `git grep` pre-push, e nemmeno la riga `ghguard.py gitcheck` citata (c'è solo `git-net dir=. push`). Affermazione non sostenuta da un file.

### Minor
3. `2026-10-23-p5-eval.md:27,33`: la colonna «Esito» dice «sotto soglia: difetto corretto» per s5 (0.75) ed e3 (1.00), cioè l'esito del primo giro, mentre la tabella è «ultima invocazione» con punteggio sopra 0,66 (e `:40` dichiara tutti sopra soglia). Secondo la decisione 7 l'esito della riga finale sarebbe «sopra soglia». Va esplicitato nella testata («esito: storia del caso») o con «sopra soglia dopo correzione».
4. `:60`: «Alla ripetizione il caso dà 1.00» — la ripetizione di e3 (26/10 00:07Z) è precedente al commit 747bf13 (`--local`, 00:58Z), quindi il codice finale non è stato riprovato su e3. Dichiararlo (s5, 01:02Z, è invece sul codice finale).
5. `:70`: «Limite da dichiarare» sull'interprete (`python3 -c`) — `docs/uso/limiti.md` non lo cita (grep «interprete» vuoto); la prova a secco 0,25 è in `tests/test_eval_cases.py:1037`. Il rapporto segnala il debito ma non dice dove si dichiara.
6. `:41` e passRate: `result.json` riporta `passRate` 0 per s3, s5, s8, s9 (score 0.75-0.80 >= soglia). Il rapporto usa lo score, giusto per la decisione 7, ma non lo dice; una riga di nota eviterebbe equivoci.
7. `:7`, «Esecutore ... per tutti i casi»: e2 non è eseguito (nota `:38`), quindi i casi sono 13 su 14; la nota c'è, ma la riga d'apertura va letta con essa.

Non sono emersi problemi critical.
