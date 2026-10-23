# Revisione Task 16: script della prova reale (84c8dc3)

Revisore in sola lettura. Eseguito solo: `bash -n` sui sei script, `python3 -B -m unittest tests.test_p4_ghguard` (23 test, ok) e una batteria di ~70 chiamate offline a `ghguard.py check` per cercare aggiramenti. Nessun `gh`, nessuna rete, nessun `claude`, nessuno script lanciato.

## Aderenza (✅ / ❌; ⚠️ non verificabile dal diff)

- ✅ Step 1, modi `elenco`, `installa`, `protezione`, `caso`, `raccogli`, `controlla` (`run-p4-gate.sh:517-525`). `installa` su protected richiede `P4_CONFERMA_PUBBLICO=1` (`run-p4-gate.sh:84`) e lo chiede prima di qualunque clone o push.
- ✅ Step 3, copertura dei casi: tutte le righe del brief hanno un caso (37 casi: 32 protected, 5 detect). Verificato riga per riga contro `make_case.py`.
- ✅ Step 4, i cinque casi detect (`detect-pulita`, `detect-closes`, `detect-merge-rosso`, `detect-push-diretto`, `attenzione-zero-test`) più `installa detect` per il criterio 34.
- ✅ Step 5, i nove modi del flusso più `issue`; `claude -p` solo in `claude_step` (`run-p4-flow.sh:94`), da `$FLOW`, sempre con `--plugin-dir` e controllo sull'array; in modo `controlla` non parte mai (`run-p4-flow.sh:99`).
- ✅ Carry: aggancio del run per numero di PR senza ripiego (`common.sh:196-225`); merge non ripetuto (`run-p4-gate.sh:240-247`); lista unica degli ammessi condivisa tra script e `controlla` (`ghguard.py`, `common.sh:12-15`); `GET pulls/<n>` registrato (`run-p4-gate.sh:331`); `verde-edit` per il PATCH del commento; `tollgate/base` su miss e hit registrato in `installa_attese`.
- ✅ Scostamento 1 (`|| true` nel comando del profilo `web`) non è davvero uno scostamento: il brief stesso dice «qui `unittest … || true`».
- ✅ Estrazione in `run-p4-checks.sh`: confrontate le funzioni spostate con quelle di `common.sh`, i corpi sono identici, cambia solo `$here/ghguard.py` in `$GH4_DIR/ghguard.py` (stessa cartella). Comportamento del Task 1 invariato.
- ✅ `init` riscrive il `mode` del `tollgate.toml` dal tipo di repo (`bin/tollgate_flow/init.py:67-86,375-387`), quindi il `mode` messo nella base non falsa il criterio 11.
- ⚠️ Step 2 (criterio 11, parte `start` e protezione con `strict` tolto a mano): non c'è un modo dello script, è lasciato al controller. Il PUT manuale con `strict` tolto non passa dalla guardia (le righe «(controller...)» sono escluse dal controllo di `comandi.log`).
- ⚠️ Tutte le attese dei casi con `oracle=False` (error-*, non-applicabile, token-personale, detect-*, verde-edit) restano ipotesi non provate dall'oracolo locale; il report lo dice.

## Punti di forza

- La guardia regge agli aggiramenti tentati: `--method=PUT`, `-XPUT`, `-x`, `-F/--field/--raw-field`, `-H X-HTTP-Method-Override`, `--input` in lettura, endpoint con `..` / `%2e` / `graphql` / `user`, altro owner, `-R` vs `--repo=` (accettati solo i due repo), `--repo` ripetuto o assente, `pr merge --admin/--delete-branch`, `repo delete/edit`, `auth` diverso da `status`, `alias`, `extension`, `secret`, `issue transfer`, `run download -D` fuori da `P4_OUT`, `--input /etc/passwd`, `--input /tmp/../etc/...`. Tutte rifiutate con motivo chiaro. PUT/DELETE di protezione solo su protected; POST solo `statuses/<sha>` con i tre campi fissi.
- `rot` al posto della cancellazione, controllo del remoto prima di ogni git di rete, nessun push forzato negli script (il test lo asserisce), `claude -p` e `rm -r` vincolati da test.
- `OracleTest`: le attese di 27 casi sono confrontate con `gate run` + `guard` + `evaluate` veri, quindi gli scostamenti 2-6 del report sono motivati dall'esecuzione e non da una lettura della spec.
- `controlla` esercita tutti i modi su repo nudi locali e ripassa ogni `gh` dal registro del finto e da `comandi.log` attraverso `ghguard`.

## Rilievi

### Critical

Nessuno.

### Important

**I-1. La guardia del flusso è aggirabile dal modello e il controllo a posteriori è parziale** (`ghwrap.py:490`, `ghwrap.py:451-452`, `run-p4-flow.sh:48-49,102-104`, `flowcheck.py:95-108`).
Scenario: `claude -p` ha `Bash` consentito per intero (`TOOLS`, riga 48) e il profilo, il repo, il gh vero e il registro sono letti dall'ambiente ereditato (`P4_PROFILE`, `P4_REPO`, `P4_REAL_GH`, `P4_LOG`). Un comando come `P4_PROFILE=script gh pr merge 5 --squash`, oppure `/usr/bin/gh pr merge 5` o `command gh ...`, o `git push --force origin main`, non è fermato da nulla: `--disallowedTools` copre solo cinque pattern `gh`. `gh_invocations` riconosce solo un `gh` come prima parola (dopo assegnazioni): `/usr/bin/gh`, `command gh`, `env gh`, `bash -c`, `$(...)` non si vedono, quindi il «STOP» di `post_passo` non scatta. In più `gh-wrap.log` (la traccia vera dei gh del modello) non viene mai passato da `ghguard comandi`. La cautela «nessun push forzato su main» non è garantita per il passo con `claude -p`.
Correzione: (a) per il flusso usare un wrapper dedicato che imposta `P4_PROFILE=flow` e `P4_REPO` senza ereditarli (per esempio `GHBIN/gh` come piccolo script che li esporta incondizionatamente) e non legge `P4_REAL_GH` dall'ambiente del modello; (b) aggiungere a `DISALLOWED` `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git push:* main*)`, `Bash(*/gh *)`, `Bash(command gh:*)`, `Bash(env:*)`; (c) estendere `gh_invocations` a basename `gh` e ai prefissi `command|env|exec|xargs`, e segnalare qualunque comando Bash che nomina `P4_` o un `gh` con percorso; (d) in `post_passo` passare `gh-wrap.log` da `ghguard.py comandi` con profilo `flow`.

**I-2. `error-sha-superato`: l'attesa `merge_state=BLOCKED` su `p1` giudica la PR sbagliata e dà un esito casuale** (`make_case.py:709-712`, `run-p4-gate.sh:334-342,393-395`).
Quando `p1` viene giudicato, la testa della PR è già `p2`: `pr view --json mergeStateStatus` descrive `p2`, non `p1`. Se i run di `p2` non hanno ancora finito, esce `BLOCKED` (per caso giusto); se hanno finito prima dell'attesa di `p1`, esce `CLEAN` e il caso risulta «non riuscito» senza difetto del gate. Il tentativo ripetuto poi dovrebbe essere dichiarato composito per una causa dello script.
Correzione: togliere `merge_state` dall'attesa di `p1` (resta `ERROR`/`ANY` sugli stati) e tenerlo solo su `p2`.

### Minor

- **M-1. Uscite sovrascritte, contro «mai cancellate»** (E): `run-p4-flow.sh:256-262` ricrea con `>` `events.jsonl`, `events.err`, `stats.err`, `hooks.log`, `skipped.log` (non sono nel `rot` di riga 254) e `ricapitolo.txt` via `save_text` ok; `run-p4-gate.sh:95` scrive `installa-<n>-baseline-file.txt` senza `rot`. Una seconda `registra` perde le uscite della prima. Aggiungerli a `rot`.
- **M-2. Guardia più larga della decisione 25** (`ghguard.py:29,291-295`, `:187-199`): `repo create` accetta `--public` anche per `tollgate-p4-detect` (deve essere privato; oggi innocuo perché il repo esiste già); la lettura `api` ammette `repos/<repo>/actions/secrets` (solo nomi, ma la decisione vieta i segreti). Restringere: `--public` solo con PROT, endpoint che contengono `/secrets` rifiutati.
- **M-3. `SHAPES` non è il vero gh del flusso** (`flowcheck.py:37-38`): il file del corpo è `/tmp/tollgate-body/body.md`, ma `bin/tollgate_flow/openpr.py:226` lo scrive in `<worktree>/.tollgate-run/<N>/pr-body.md`. Passa solo perché il worktree sta sotto `/tmp` (`ghguard._temp_roots`). Usare un percorso uguale al vero sotto `$FLOW`, così il test dice la verità.
- **M-4. Profilo `flow` troppo largo** (`ghguard.py:38`): restano ammessi `issue close`, `issue comment`, `pr comment`, `pr edit --base`, che il flusso di tollgate non fa mai (le 12 forme di `SHAPES`). Aggiungerli a `FLOW_FORBIDDEN` (o ammettere solo le forme di `SHAPES`).
- **M-5. Deriva della base detect** (`make_case.py:780-783`): `detect-merge-rosso` unisce in `main` di detect un cambio con un test tolto; i casi detect rilanciati dopo partono da una base degradata (gli identificativi della base non hanno `test_sottrai`). Va fatto girare per ultimo (ora lo è nell'elenco) e scritto nel rapporto; un ripristino richiederebbe un commit nuovo, non un reset.
- **M-6. Criterio 34 non giudicato dallo script** (`run-p4-gate.sh:164-167`): il conteggio delle issue dopo il primo push è solo registrato in un file, e `jq ... 2>&1` mette un eventuale errore nel campo. Il passo `hit` poi chiude l'issue (registrandola prima, quindi nulla viene nascosto). Aggiungere una riga «riuscito/non riuscito» se il conteggio non è `0`.
- **M-7. `P4_CHECK=1` letto dall'ambiente salta la conferma sul pubblico** (`run-p4-gate.sh:84`): bypass innocuo (poi `check_remote` richiede `P4_GIT_BASE`), ma una guardia di sicurezza non dovrebbe dipendere da una variabile che il modo `controlla` esporta.
- **M-8. Commento e test** (`tests/test_p4_scripts.py:13`): «38 casi», sono 37.

## Risposta ai focus

- **A (sicurezza degli script).** Gli script del gate passano ogni `gh` dalla guardia (`gh_call`/`gh_q` → `guard_args` prima dell'esecuzione) e `git_call` controlla il remoto: nessuna scappatoia trovata nella guardia stessa (vedi batteria sopra). Nessuna cancellazione di repo, cambio di visibilità, segreto, `gh api user`, `gh auth` diverso da `status`, push forzato negli script. `claude -p` solo da `/tmp/tollgate-p4/flow` con `--plugin-dir`. L'unico buco reale è il passo con `claude -p` (I-1): lì la guardia è un consiglio, non un vincolo.
- **B (scostamenti).** Giustificati dall'oracolo: (1) `|| true` nel profilo `web` è previsto dal brief; (2)-(3) i casi `error` passano per la copia di `gate run` in `.github/tollgate/bin`, coerenti con la decisione 13/V8 del carry (guard rosso atteso perché cambia un file di tollgate; `verdict` ed `attention` in `error` con difesa in profondità di `artifacts.validate`); (4) i due `tollgate.toml` che differiscono solo per `allow_no_tests` (e `mode`, riscritto da `init`): giustificato, e il rapporto deve dirlo accanto alla riga `attenzione-zero-test` che gira su detect; (5) verde con `attenzione` = verdict verde e attention rosso, coerente con le altre righe «attenzione rosso». ⚠️ le attese `error` non sono provate dall'oracolo (nessun run reale di `tollgate-run` con la copia modificata).
- **C (issue di sentinel).** `close_sentinel_issues` chiude solo issue con il titolo esatto di sentinel (`ghcli.py:19`) nei due repo di prova, le registra (`view` con commenti) prima di chiuderle, e nei casi detect lo fa dopo `collect_judged`: non nasconde il rosso misurato dal caso. Un'issue rimasta aperta farebbe comparire `sentinel_open` in `attenzione` o contare 2 issue, quindi un errore visibile e non silenzioso (M-6 per il conteggio del criterio 34). Nessuna issue altrui viene chiusa.
- **D (estensioni).** `common.sh`, `fakegh.sh` e `ghwrap.py` sono necessari (libreria condivisa richiesta dal carry; `init` e `protect.sh` chiamano `gh` da soli e devono passare dalla guardia). `flowcheck.py` serve alla decisione 27 ma ha il limite di I-1. `verde-edit` copre la verifica del PATCH chiesta dal carry. Nessuna sovra-ingegneria evidente; `make_case.py` (939 righe) è grande ma ha una sola responsabilità.
- **E (uscite).** Tutte le uscite vanno in `docs/verifiche/evidenze/gh-p4/` e `rot` rinomina; nessuna cancellazione. Eccezioni in M-1.

## Valutazione

**Qualità del task:** Da correggere.
**Motivo:** nessun difetto Critical e la guardia di `ghguard.py` regge, ma il passo `claude -p` non ha un vincolo vero su profilo, `gh` con percorso e `git push` (I-1), e un caso (`error-sha-superato`) ha un'attesa che dà un esito casuale (I-2). Entrambi si correggono con modifiche piccole e senza eseguire nulla.
