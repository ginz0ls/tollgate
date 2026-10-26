# Revisione finale del ramo p5-eval-ci (a9b37e3..bf02e5c)

Ho fatto la revisione in sola lettura, in quattro passate sul diff senza le evidenze (171 file, +13.862/-360 righe):
1. prodotto (`bin/`, `gate/workflows/`, `skills/`, `.github/`, `.claude-plugin/`);
2. recinto degli eval (`evals/run.sh`, `evals/cost.py`, `evals/_kit/scaffold.py`, `tests/evalbin/`);
3. test del Review Focus;
4. rapporti, documentazione, evidenze a campione.

Test mirati lanciati, tutti verdi:
- `tests.test_gate_sentinel`, `test_gate_guard`, `test_docs`, `test_ci_workflow`, `test_reviews`, `test_db`, `test_gate_workflows`, `test_init`: 300 test, OK;
- `tests.test_p4_ghguard`, `test_eval_run`: 129 test, OK.

Dopo le corse `git status` è pulito.

## Strengths

- **Sentinella con il segnale scritto dal codice** (`bin/tollgate_gate/sentinel.py:44-76`, `:207-209`). La risalita lungo il primo genitore, fino a uno stato `tollgate/sentinel` di `ghcli.STATUS_BOT`, chiude davvero il buco di `[skip ci]`. I test dicono quello che promettono:
  - `test_skipped_push_checked_next_time` costruisce il segnale con `clean_push`, cioè con il codice e non con un dato;
  - `test_user_written_sentinel_status_ignored` e `test_user_marker_on_after_parent_does_not_skip_commits` escludono gli stati scritti da altri;
  - `test_walk_stops_at_a_failure_marker_too` impedisce la doppia segnalazione.
- **`pending` di guard al posto giusto** (`bin/tollgate_gate/guard.py:108-112`). Arriva dopo il controllo «non applicabile», quindi mai verso un altro ramo, e solo con `publish`. La corsa «verdict prima di guard» è dichiarata in spec 9.1 («Stato in attesa»).
- **`close_cycle` atomico** (`bin/tollgate_core/reviews.py:321-386`). Chiusura, fase e blocchi stanno in una sola transazione, con le copie del DB dopo il commit. `set_phase_in_tx` e `open_block_in_tx` sono estratti senza cambiare il comportamento di `set_phase` e `open_block`. Il rifiuto fuori da `verify` è coerente con i tre chiamanti: `hooks/apply.py:107,120` e `flow/finalreview.py:172` arrivano lì solo da `verify` senza rilievi aperti.
- **Recinto degli eval solido.** `run.sh` blocca per prima cosa le variabili fuori da TEST_MODE e rifiuta ogni opzione che cambi uscita o pubblicazione. Ha in più `flock`, la prenotazione «?» che resta chiusa anche dopo un SIGKILL, `timeout -k`, copie che non seguono i collegamenti simbolici e la scansione delle forme di token su tutto ciò che finisce nelle evidenze. `cost.run_cost` prende il massimo tra il totale e la somma per corsa con i giudici, così il costo non si sottostima.
- **Le azioni fissate hanno una fonte unica** (`gate/workflows/PINS`), condivisa da `ci.yml` e dai workflow del gate e provata su detect (Task 13).
- **Rapporti onesti.** `docs/verifiche/2026-10-23-p5-eval.md` racconta i tre giri di s5 e i due di e3 invece di mostrare solo il numero finale, e dichiara che e3 non è stato riprovato col codice finale, con il motivo.
- **Numeri ricontrollati.** La somma di `budget.tsv` vale 9,0632 USD, con 0,7486 di sonde e 8,3145 di eval; il residuo è 70,94.

## Review Focus, voce per voce

Ogni test esiste e asserisce ciò che la voce dice.

1. **`test_state_seen_without_tollgate_env`** (`tests/test_eval_kit.py`). Controlla che l'ambiente non abbia nessuna `TOLLGATE_*`, poi che `status --json` e il `SessionStart` vero vedano il lavoro. **`test_scaffold_env_never_reaches_agent_env`** controlla che l'ambiente del padre sia identico dopo `main`, che lo stato «altrove» resti con la sola sentinella e che nessun file della corsa nomini `TOLLGATE_`.
2. **`test_<caso>_dry_run`** per s1-s9 ed e1-e5 (`tests/test_eval_cases.py:800-1557`). Asseriscono il testo vero del programma, per esempio `DONE senza ricevuta green su …` e `verify: green (uscita 0`. I cammini passano da `assertCorrectPath` e `assertWrongPath`, con la soglia.
3. **`test_edited_publishes_pending_then_verdict_replaces`** e **`test_no_pending_for_other_base`** (`tests/test_gate_guard.py`). Presenti, verdi.
4. **I tre test della sentinella** (`tests/test_gate_sentinel.py`). Il segnale nasce da `clean_push`; un `success` di «mario» non salta nessun commit.
5. **`test_proposal_workflows_pinned`** (`tests/test_init.py`) e **`test_ci_workflow_pinned`** (`tests/test_ci_workflow.py`). Presenti, verdi.
6. **Recinto degli eval.** `test_shim_without_data_fails_closed` prova anche che la trappola scatterebbe senza lo shim. `test_refuses_without_budget` verifica che non parta nessuna chiamata. `test_always_no_publish` e `test_cost_added_on_nonzero_exit` coprono le uscite 1 e 2 con riga e costo.
7. **`test_every_skill_documented`** e **`test_no_local_paths`** (`tests/test_docs.py`). Presenti, verdi.

## Issues

### Critical

Nessuno.

### Important

Nessuno.

### Minor

1. **`tests/test_p5_scripts.py:951`** — `open(reg).read()` non chiude il file. Già noto al controller, va corretto nel giro finale: `with open(reg) as f:`.
2. **Le evidenze riportano il `PATH` intero della macchina dell'utente**, non solo percorsi assoluti.
   - Dove: `docs/verifiche/evidenze/eval-p5/*-sonda-*/corse/*/settings.json`, `…/sonda-hooks.jsonl` e `…/home/.local/state/sonda/hooks.jsonl`, circa 81 file.
   - Cosa contengono: `~/.opencode/bin`, `~/.kimi-code/bin`, `~/.nvm/versions`, `~/.pyenv` e altri.
   - Perché conta: non sono segreti e il repo è privato. Però la nota «Prima di una pubblicazione» del piano principale (`docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md:482`) parla solo di «percorsi assoluti (radice del plugin, cartelle temporanee delle corse)». Chi ripulirà rischia di non accorgersi che c'è anche l'elenco degli strumenti installati.
   - Come: aggiungere «e il `PATH` dell'utente nelle evidenze delle sonde del Task 1» a quella nota.
3. **84 file `migrate.lock` vuoti nelle evidenze**, per esempio `docs/verifiche/evidenze/eval-p5/20261025T215435Z-s4-deploy/runs/*/home/.local/state/tollgate/migrate.lock`.
   - Perché: sono lucchetti della cartella di stato copiati da `run.sh`; innocui, ma rumore.
   - Come: niente da riscrivere, perché le evidenze non si cancellano (decisione 22). Per le corse future basta escludere `*.lock` nel ciclo `.local/state/tollgate` di `evals/run.sh:239-245`.
4. **`docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md:482`** — «Prima del primo push» è superato: il push c'è già stato, nel run CI 40252693867. È il minore 5 del Task 15, già nel giro finale; lo ripeto solo perché coincide con il punto 2 e conviene correggerli insieme.
5. **`bin/tollgate_core/reviews.py:358-361`** — su un ciclo già chiuso, `close_cycle` non riprende più le conseguenze rimaste a metà.
   - Perché: con la chiusura atomica di P5 è corretto. Un DB scritto da 0.1.0 che avesse avuto un crash tra la chiusura e le conseguenze, cioè con il vecchio codice in due transazioni, non si ripara più da solo.
   - Quanto pesa: è improbabile e senza danno di sicurezza. Al peggio manca il passaggio `review` → `execution` o il blocco di tetto, e `finish check` e `open-pr` ricalcolano comunque.
   - Come: una riga nella sezione 7 «Dopo la v1», oppure niente.

## Minori rinviati

Nessuno dei `minor (deferred)` di `progress.md` diventa important.
- **`gitw.set_config` senza `--local`** (Task 14): è già risolto nel codice. `bin/tollgate_flow/gitw.py:119` usa `config --local --get-all`, quindi la voce si può chiudere.
- **Task 8, s5 `piano-scritto` e s2 `status` dal worktree**: il Task 14 li ha visti succedere. Per s5 sono stati corretti con la ruling dei grader d'esito; s2 è passato 3/3. Restano chiusi nei fatti, non vanno riaperti.

## Declined to judge

- **`spikes/gh-p4/ghguard.py` profilo `p5` e i due script delle prove reali** (`spikes/p5/run-p5-checks.sh`, `spikes/run-p5-gate.sh`, circa 2.700 righe). Li ho letti solo a campione, perché sono strumenti del controller già rivisti in più giri (Task 1: 3 ri-revisioni; Task 13: 2) e i loro 129 test passano. Non li ho eseguiti, come vogliono le cautele.
- **Evidenze grezze** (circa 3.900 file). Ho guardato solo `budget.tsv`, la cartella di s4 e i controlli trasversali: nessun `__pycache__`, nessun gitlink o worktree annidato, nessun `.git/` o `.origin.git` dentro le evidenze, nessuna forma di token con `git grep` su tutto l'albero di bf02e5c.
- **Suite completa.** Non l'ho lanciata, perché la lancia il controller. Il 2897/2897 su 3.11 e 3.13 lo prende dai rapporti.
- **La correttezza delle risposte di GitHub nelle prove su detect** (Task 13). Non ho rete; mi fido del rapporto `docs/verifiche/2026-10-23-p5-prova-gate.md`.
- **Le scelte dei casi e dei pesi dei grader** (s5 ripesato dopo il secondo giro). Sono decisioni del controller con la loro ruling, dichiarate nel rapporto. Il rischio di aver tarato il caso sul risultato è scritto, non nascosto.
- **Il tono e la qualità del testo di `docs/uso/`.** Ho controllato solo la coerenza con il codice nei punti toccati: riga dei limiti e frase di `detect` in `status`, `[skip ci]`, best effort, scrittura da interprete.

## Assessment

**Ready to merge: With fixes.** Le correzioni sono i minori già destinati al giro finale (1 e 4) più la nota del punto 2 sulle evidenze. Nessuno è bloccante, e nessun comportamento del prodotto va cambiato prima del merge.

Conteggi: Critical 0, Important 0, Minor 5.
