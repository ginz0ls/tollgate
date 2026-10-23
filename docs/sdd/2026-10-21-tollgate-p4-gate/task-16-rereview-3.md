# Ri-revisione Task 16, giro 3 (a768319..f301c6e): D-1 e D-2

Sola lettura. Eseguito: `python3 -B -m unittest tests.test_p4_ghguard tests.test_gh tests.test_p4_make_case tests.test_p4_scripts.PullBodyTest` (82 test, ok). Nessun gh vero, rete, claude, token.

## Verdetti

**D-1 (attesa UNSTABLE con attention rossa).** INDIRIZZATO.
- `make_case.py` `merge_for`: guard o verdict non `success` -> `BLOCKED`; verdi con attention `failure`/`error` -> `UNSTABLE`; altrimenti `CLEAN`. `case()` risolve `DERIVE` alla registrazione (`dataclasses.replace`), quindi `case.json` e il giudizio vedono sempre una stringa.
- (c) Controllato caso per caso contro le attese reali: verdi puliti (`verde-pulita`, `verde-edit`, `error-sha-superato` p2) -> CLEAN; i sei casi con attention rossa (verde-config, verde-ramo-libero, verde-workflow-ci, attenzione-deroga-test, attenzione-piano-testo, attenzione-tetto-livello) -> UNSTABLE; tutti i `rosso-*` (verdict failure, anche `rosso-piano-file-nuovo` con attention failure) -> BLOCKED; `guard-*` e `error-dotdot`/`error-entita` (guard failure) -> BLOCKED; `error-due-pr` (error su tutto) -> BLOCKED. `error-sha-superato` p1 non ha attesa sul merge (giro 1) e resta senza. `non-applicabile` non ha `merge_state` (nessuna regola di protezione sulla base `other`): corretto lasciarlo fuori. `token-personale` ha `BLOCKED` scritto, negazione voluta della regola (stati tutti `success` ma lo stato del verdict non è del bot), e il test lo tratta a parte. I casi `detect` non hanno `merge_state` (repo senza protezione): non toccati.
- Test: `test_merge_state_follows_the_rule_for_every_protected_case` (≥25 controlli, ricalcola la regola in modo indipendente dal codice) e `test_the_six_attention_cases_expect_unstable`: passano.

**D-2 (`gh pr edit` rotto con gh 2.46).** INDIRIZZATO.
- (a) `bin/tollgate_flow/gh.py:pr_edit` ora lancia `gh api --method PATCH repos/{owner}/{repo}/pulls/<int(n)> -F body=@<file>`. Il numero passa da `int()` (un valore non intero dà `ValueError`, test `test_edit_number_must_be_an_integer`); un'uscita non zero di gh è un `GhError` tramite `_run_checked` (test `test_edit_failure_is_a_gh_error_and_leaves_the_body`); `{owner}/{repo}` lo risolve gh dalla cartella di lavoro, come in `sentinel_issues` (`gh.py:141-143`). Aggiorna solo il corpo: un solo campo, nessun altro parametro.
  - Conversione di tipo di `-F`: non c'è rischio per un corpo che inizia con un numero o con `true`/`false`/`null`. Nel codice di `gh api` la conversione «magica» (interi, booleani, `null`, segnaposto) vale per il valore letterale; un valore che comincia con `@` viene letto dal file e restituito come stringa, senza alcuna conversione. Questo non si può provare offline senza il gh vero (la regola del dispatch lo vieta); lo stesso modo `-F body=@file` è già usato dal prodotto per i commenti del verdetto (`bin/tollgate_gate/github.py:2`) e dal caso `verde-edit` con la PATCH del commento. Il corpo reale della PR inizia comunque con `Closes #N` (`prbody.render`), quindi non è nemmeno un caso possibile. Se si vuole la prova, basta che la prima esecuzione reale di `passo4b` (`pr_edit` su PR aperta) mostri il corpo aggiornato.
  - Chiamanti: `openpr.py` `_publish` (`gh.pr_edit(..., body_file=body_file)`) e `sync` (via `openpr`) non cambiano. I test sono coerenti: `test_gh` verifica gli argomenti esatti, che `pr edit` non venga più chiamato e che un guasto lasci il corpo; `test_openpr` e `test_sync` contano le PATCH al posto di `pr edit`; `tests/fakegh.py` emula la PATCH (404 per PR assente, guasto simulato con `fail=["pr edit"]`, che resta il nome nei test).
  - Guardrail del modello (`bin/tollgate_analysis/bash.py:901`): `gh api` con `-X` non GET, `-F`, `--input` era già una scrittura in repo attivo (spec riga 604), quindi il modello non guadagna una via nuova; la CLI non passa dagli hook. Nessuna modifica necessaria.
- (b) Guardia (`ghguard.py` `_check_api_write`, ramo `PATCH`): ammessa solo con repo == protected, endpoint `repos/<o>/<r>/pulls/<intero>$`, nessun `-f`, nessun `--input`, esattamente il campo `-F body`, valore che comincia con `@` e file ammesso da `_infile` (profilo script: cartelle dell'ambiente e temporanee; profilo flow: solo sotto `P4_TMP`). Provato dai test (82 ok) e letto il codice: rifiutati detect, altro owner, `pulls/3/merge`, `issues/3`, `number=x`, `-f title=`, secondo `-F`, `--input`, `-f body=`, `-F body=testo` senza `@`, `-F state=@...`, `/etc/passwd`, percorso relativo, `/tmp` nel profilo flow, `DELETE`. `--method=PATCH` (con `=`) è rifiutato perché ogni opzione non elencata lo è. Fuori dal ramo PATCH nel profilo flow ogni altra scrittura `api` resta rifiutata (`flow` → errore), e `FLOW_FORBIDDEN` ha ora anche `pr edit`. `comandi.log` legge la forma (test), `flowcheck.SHAPES` e `FORBIDDEN_SHAPES` aggiornate e provate.
- `run-p4-gate.sh` op `edit`: stessa forma, con il file nelle cartelle ammesse del profilo script.

## Danni nuovi nel diff

Nessuno Critical o Important. Minori:

**M3-1. Documentazione di prodotto non aggiornata.** `bin/tollgate_flow/openpr.py:5` e `:259` (docstring: «`pr edit` : `pr create`», «poi `pr edit` o `pr create`»), e la specifica `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` riga 514 («`gh pr edit --body-file`»), riga 1501 (G3, «`gh pr edit <n> --body-file`: Sì») e riga 1331: dicono ancora `pr edit`. Per la regola della documentazione vivente vanno allineati («corpo aggiornato con `gh api --method PATCH ... -F body=@file`, perché `gh pr edit` esce con 1 su gh 2.46»), con una riga nel registro delle decisioni/rev della specifica.

**M3-2. Il profilo flow ammette la PATCH del corpo di una qualunque PR di protected da un file qualunque sotto `$FLOW`** (`ghguard.py`, ramo PATCH). Non è nuovo (prima `pr edit --body-file` era ammesso allo stesso modo) ma ora l'endpoint nomina un numero qualsiasi e `flowstate` non vede i corpi delle PR (dichiarato). Accettabile nel modello cooperativo; da sapere perché il corpo della PR contiene il blocco che il gate legge.

**M3-3. Nota di prova.** `tests/test_p4_ghguard.py` ha una riga lunga `for args in ((["pr","edit",...],["issue","close"...` senza spazio dopo la virgola (`test_flow_profile_has_only_the_flow_forms`): solo formattazione.

## Osservazioni fuori ambito

Nessuna.

## Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. Minori non bloccanti: M3-1 (docstring di `openpr.py` e specifica ancora su `pr edit`), M3-2, M3-3.
