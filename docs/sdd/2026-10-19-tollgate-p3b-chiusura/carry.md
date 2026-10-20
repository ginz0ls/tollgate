# Decisioni del controller da portare nei task (dallo scan pre-flight e dal Task 1)

Fonte: preflight-scan.md e docs/verifiche/2026-10-19-p3b-verifiche.md. La spec rev 22 è l'autorità. Ogni voce prevale sul testo del brief del task.

## Task 1
- Modello per script e rapporto: `spikes/run-p3a-experiments.sh` e `docs/verifiche/2026-10-16-p3a-verifiche.md`.
- Annota anche se `gh pr list` accetta `--state all` e i campi `headRefOid`/`mergedAt` in `--json` (l'elenco dei campi è nell'aiuto di `gh pr list --help`/`gh pr view --help`, sezione JSON FIELDS), e se `gh api` ha `--paginate`, `--jq`, `--slurp`.

## Task 9 (esiti del Task 1: docs/verifiche/2026-10-19-p3b-verifiche.md)
- G1: `gh api` con `repos/{owner}/{repo}/…`, cwd = repo del lavoro, nessun `-R`.
- G2: `pr create --head <ramo> --base <predefinito> --title <titolo> --body-file <file>`; l'URL NON si legge da stdout: dopo la creazione si rilegge con `pr_for_branch`. `fakegh` può stampare l'URL, il codice non ne dipende.
- G3: `pr edit <n> --body-file <file>`.
- G4: `pr_for_branch` = `pr list --head <ramo> --state all --limit 100 --json number,state,url,headRefOid,mergedAt`; `pr_view` = `pr view <n> --json number,state,url,mergedAt`; `pr_comments` = `pr view <n> --json comments`. Uscita non zero → `GhError`, mai «nessuna PR». `fakegh` deve rifiutare (uscita 1) un campo `--json` che non conosce, così un nome sbagliato nel codice fa fallire i test.
- G5: niente `--slurp`. `gh.run_json_lines` decodifica in sequenza i valori JSON dell'uscita con `json.JSONDecoder().raw_decode`, saltando gli spazi tra un valore e l'altro (vale per una riga per oggetto e per oggetti su più righe); un testo non JSON → `GhError`. `fakegh` per `api --paginate …/pulls` stampa una riga JSON compatta per PR.

---
Voci dallo scan pre-flight (numeri C in preflight-scan.md; le Ruling complete sono in progress.md).

## Task 2
- C2: `cli_session(..., argv=None)` è lettura senza confronto e NON consuma (i test di P3a con `argv` assente restano invariati: `test_sessions.py` righe 68-74 e 97-103, `test_criteria_p3a.py:41`, `test_flowkit.py:57`). Con `argv` non nullo: la voce vale solo se `entry["argv"] == argv` e si toglie dal file (lettura, rimozione della sola voce del sottocomando, tmp + `os.replace`, come `note_cli_call`; un `OSError` nella rimozione non fa fallire la chiamata). `test_signal_consumed_once` usa `argv`.
- Il confronto: l'hook salva `argv = args[args.index(sub):]` (dal sottocomando in poi); `cli.main` passa gli argomenti dal sottocomando in poi (`sys.argv[1:]`). `start` e `act` in `cli.main` passano `argv`.

## Task 3
- C3: `tests/test_db.py` `MigrationV3Test` asserisce `str(db.latest_version())` invece di `"3"`.
- C5: `dod._receipt` esclude le ricevute con `command == "related"` (come `subagent_stop.py:51`); test in `test_dod.py` (`test_related_receipt_ignored`: ricevuta `related` `empty` sullo SHA più gate verde → voce `receipt` vera).
- C12: `PLAN` e `plan_text` si spostano da `tests/test_taskcmd.py` a `tests/flowkit.py` (che importa `SECTIONS` da `tests.test_check_post_edit`); `tests/test_taskcmd.py` li reimporta da `tests.flowkit` con gli stessi nomi. `FlowLab.register_plan` usa `plan_text`.
- C16: `open_cycle` scrive `counted = 0`; `close_cycle` imposta `counted` (1 se ci sono rilievi confermati). Funzione `reviews.supersede(conn, work, cycle, *, now)`: chiude un ciclo aperto con `outcome = 'superseded'`, `stage = 'closed'`, `counted = 0` (la usa il Task 7). `count()` conta tutte le righe; `counted()` somma `counted`. Test `test_superseded_not_counted`.
- C18: `add_report` normalizza i `rejected` prima dell'INSERT: `severity` fuori da `SEVERITY_ORDER` → NULL, `line` non intera → NULL, `file`/`rule`/`text` non stringa → NULL, `text` troncato a 2000 caratteri. Test con `severity="critical"` e `line="2"`.
- C25 (3): `create_work(..., phase=…, from_approved_spec=True)` → `ValueError` (esclusivi).
- Test in più: test diretti di `set_pr`, `set_finish`, `add_extra_cycles`, `set_review_unverified`, `acts.has_approval`, `intents.complete`; `test_downgrade_and_dismiss` con `subTest` per i tre casi.

## Task 4
- C15: `diff_violations(..., components)` legge `components.get(nome, True)` (default acceso, come `Ctx.component`).
- C17: `GateRun.sha is None` significa gate non eseguito (worktree sporco, config non valida, nessun comando): `lines` porta il motivo.
- C23: `test_same_result_as_hook` asserisce le violazioni attese (percorso, tipo, `waiver_type`) su un commit costruito a mano e, in più, che `_common.commit_violations` sullo stesso commit dà lo stesso elenco.
- I nomi `commit_violations`, `scope_exempt`, `locked_docs`, `is_docs_md`, `orphan_tg`, `level_records` restano in `_common` con la stessa firma a base di `ctx` (deleghe): nessun test degli hook si modifica.

## Task 5
- C4: in `tests/test_taskcmd.py` le fixture `probe:web-dev` → `probe:implementer-web` e `probe:web-reviewer` → `probe:reviewer-web` (righe 21-22 e asserzioni 138-140). `tests/test_taskcmd.py` entra nei file del task.
- C8: con lo standard acceso un `approved` dichiarato è non valido se un rilievo scartato per forma «poteva bloccare»: gravità `blocker`/`major` oppure gravità fuori elenco (fail-closed). Un `moderate`/`minor` scartato non invalida. Riscrivi `tests/test_verdicts.py::test_finding_with_bad_severity_or_line_dropped`: i casi che restano `approved` validi con `dropped` usano un `minor`/`moderate` con `line` non intera o `file` vuoto; il caso `severity="critical"` va con `outcome="changes"` (o diventa un caso del nuovo test di invalidità). Aggiungi `test_approved_with_dropped_blocker_invalid`.
- C22: `parse_final_verdict` e `parse_verifier_results` non richiedono `"v"` (campo ignorato).
- C18: `parse_final_verdict` mette in `rejected` anche i rilievi con `severity` fuori elenco, con il valore com'è (la normalizzazione la fa `reviews.add_report`).

## Task 6
- C13: verde con la fase già `review` (altro SHA): solo `set_finish` ed evento, niente `set_phase`. Test `test_rerun_in_review_other_sha`.
- C14: `external={"guard_scope": bool, "must_have": bool, "approvals": bool}` (dizionario).
- C17: `GateRun.sha is None` → `REFUSED` (codice 2) con il motivo, fase invariata. Test: worktree sporco → rifiuto, fase invariata.
- C6: `finish_report` = `{"items": {chiave: bool | null}, "manual": [...]}` con TUTTE le voci calcolate (comprese `guard_scope`, `must_have`, `approvals`): è il contratto che `open-pr` (Task 9) legge.
- C24: `cli.main` riceve un `except` finale per `gh.GhError`, `git.GitError` e `gitw.GitWriteError` → messaggio e uscita 1 (verifica i nomi reali delle eccezioni nel codice).
- Il test verde asserisce anche l'evento `finish_check` {sha, ok: true}; il rosso `ok: false`.
- (a) `prstate.detect` non esiste ancora: si aggancia nel Task 9.

## Task 7
- C16: se l'ultimo ciclo è aperto su uno SHA diverso da HEAD (e il `patch-id` non coincide), `prepare` lo chiude con `reviews.supersede` prima di aprire il successivo.
- C7: con `review_unverified` nessun lancio, riga «revisione non verificata» e `prossimo passo: finish open-pr`.

## Task 9 (dallo scan)
- C6: `open-pr` prende `guard_scope`, `must_have`, `approvals` da `work_items.finish_report["items"]` (si esige `HEAD == finish_sha`) e li passa come `external` a `compute_dod`; ricalcola il resto (con `findings_cycle`, `specialists`, `required_commands`, `profile_items`, `allow_unverified`).
- C19: `gitw.is_ancestor(repo, a, b) -> bool` nasce qui (`git merge-base --is-ancestor`); `open-pr` legge `remote_sha` prima del push: se c'è ed è diverso da HEAD e non antenato di HEAD, senza intento `force_push` rifiuta senza push. Il Task 11 lo riusa.
- C24: `GhError`/`GitWriteError` diventano righe `rifiuto:` con codice 1, mai traceback.
- Test in più: `--update` senza PR aperta → rifiuto; PR `CLOSED` non unita → rifiuto con `CLOSED_HINT`; eventi `pr_opened` (prima volta) e `pr_updated` asseriti; `test_finish_act_valid_without_session_signal` asserisce anche l'atto `finish` `consumed`; `test_block_in_body_parses` confronta `head_sha` con HEAD e `issue` con il numero del lavoro.
- `prstate.detect` si aggancia a `finish check` qui.

## Task 10
- C7: `approve unverified-review` (solo con almeno 8 cicli, `reviews.count`): `review_unverified = 1`, chiude il blocco dei cicli se aperto, fase invariata. Il test asserisce flag, blocco chiuso e fase.
- Test in più: `approve rounds` con entrambi i blocchi aperti → rifiuto che chiede `resolve`; `approve rebase` con la fase tornata `execution` resta `execution` (nessun `set_phase`), base riallineata e intento `force_push` comunque.

## Task 11
- C20: in `start` (ripresa) `wt` si calcola prima di raccogliere gli intenti da confermare; `sync.complete_interrupted` si chiama subito dopo; l'intento completato non entra nella conferma.
- C19: `gitw.is_ancestor` esiste dal Task 9: riusalo.
- Test in più: `sync` con PR `CLOSED` non unita → rifiuto con `CLOSED_HINT`.

## Task 12
- C25: PR `CLOSED` non unita → ignorata con l'avviso «PR #n chiusa senza merge: ignorata, finish open-pr ne aprirà una nuova» (nessun `pr_number`); tetto dal blocco JSON: `cap_paths` ricalcolati come `actapply._approve_level` (righe 72-75); `create_work` riceve `phase` senza `from_approved_spec`.
- `test_refused_with_active_work_or_merged_pr_or_two_branches` con `subTest` per i tre casi.

## Task 13
- C11: `orphan_tg` resta com'è; nuova `closed_tg(ctx, repo) -> int | None` in `_common` (ramo `tg/<N>-*` che è il `branch` di un lavoro `closed` del repo e di nessun lavoro attivo). I chiamanti `bin/tollgate_checks/writes.py`, `bash_rules.py`, `session.py` (file aggiunti al task) indicano `/tollgate:cleanup` in quel caso; i test esistenti su `orphan_tg` restano invariati.

## Task 15
- C10: `next_step` guarda l'esito attuale dell'ultimo ciclo: `needs_fix` → `task start --from-findings <ciclo>`; `ok` su HEAD (per esempio dopo `approve finding … dismiss`) in `execution` → `/tollgate:finish`. Test `test_ok_cycle_after_dismiss_points_to_finish`.

## Task 16
- C9: skill `finish`: `finish check` uscita 1 → mostra le voci `[no]` e fermati; ogni altro codice diverso da 0 → riporta il messaggio così com'è e fermati.
- C22: negli agenti `final-reviewer` e `finding-verifier` il JSON finale porta `"v": 1` (regola comune di 18).

## Task 17
- C1: il repo di prova porta `tools/unittest_junit.py` (stdlib: esegue `unittest` e scrive il JUnit in `reports/junit.xml` con gli id nella forma che `junit.parse_junit` riconosce per unittest) e il `report` configurato nella stessa forma di `JUNIT_TOML` di `tests/flowkit.py`; il must-have M1 resta legato a un test vero del repo di prova.

## Task 18
- C22: la rev 23 riporta anche: `abandon` con lavoro nullo (decisione 3), `approve rounds` sui giri di correzione con tetto 8 (13), la regola `"v": 1` (18.5 si allinea), il consumo del segnale fail-closed senza lucchetto (C21), e le `Ruling:` di progress.md che cambiano la spec (G4, C5, C6, C7, C8, C16, C25).
- C8: la riga del criterio 40 nella matrice del piano principale (oggi `test_finding_with_bad_severity_or_line_dropped`) si aggiorna con i test riscritti del Task 5.

## Task 8 (dal Task 3)
- `reviews.add_report` solleva `ValueError` per una fonte non attesa, già riportata o un ciclo non in stadio `review`; `close_cycle` si può ripetere su un ciclo chiuso. L'operazione `review_report` di `apply.py` deve gestire il `ValueError` senza far fallire l'hook (riporto ignorato con un evento o un avviso, mai un'eccezione al runner).
- Al tetto dei cicli `close_cycle` porta prima la fase a `execution`, poi apre `needs_you` con `CAP_REASON`.
- (dalla revisione del Task 3, M1) `close_cycle` non controlla stadio né rilievi senza esito: chiamalo solo con lo stadio `verify` e zero rilievi con `verification` nullo (dopo `to_verify`/`apply_verification`), oppure dopo un riporto che porta a `verify` senza rilievi da verificare.

## Task 7 (dalla revisione del Task 3)
- M1: `prepare` chiama `close_cycle` solo con lo stadio `verify` e nessun rilievo con `verification` nullo.

## Task 10 (dalla revisione del Task 3)
- M2: dopo `approve finding` NON richiamare `close_cycle` su un ciclo già chiuso (rimetterebbe la fase a `execution` e riaprirebbe il tetto). Il ricalcolo dell'esito è una funzione nuova di `reviews` (per esempio `reviews.recompute_outcome(conn, work, cycle, *, now) -> str`) che aggiorna `outcome` e `findings_confirmed` del ciclo chiuso senza cambiare fase né blocchi; la chiusura del blocco dei cicli la fa `actapply` con `close_block`.

## Task 6 (dalla revisione del Task 4)
- Un `dod` di profilo che nomina un comando senza voce in `[commands]` dà una ricevuta `unverified` e `run_gate.ok` falso: è voluto (fail-closed); la riga di `finish check` per quella voce dice il nome del comando e che manca in `[commands]`.

## Task 8 (dalla revisione del Task 5)
- L'esito del ciclo NON viene dall'`outcome` dichiarato dal revisore finale, salvo `needs_you` (decisione 6): un `ok` dichiarato con rilievi scartati per forma resta un riporto valido (gli scartati vanno `rejected`, criterio 40), un `needs_fix` dichiarato senza rilievi validi chiude il ciclo `ok` se nulla viene confermato.

## Task 8 (dalla revisione del Task 7)
- Riporti del verificatore: al secondo riporto valido del verificatore nello stesso ciclo con rilievi ancora senza esito, `finding_verify` apre `needs_you` «verificatore senza esito su: <id, …>» (mai `unverified` automatico). Il conteggio dei riporti del verificatore per ciclo sta in `review_cycles.reported` (per esempio la chiave `tollgate:finding-verifier` con un contatore). Test `test_verifier_omits_ids_twice_needs_you`.

## Task 15 (dal Task 13)
- Dopo `start --confirm` su una PR chiusa senza merge, un lavoro in `pr_open` resta in `pr_open` con `pr_number` nullo: `next_step` in `pr_open` senza PR dice «PR chiusa senza merge: /tollgate:start #N --reopen-execution, poi /tollgate:finish per aprirne una nuova (oppure /tollgate:abandon #N)». Test `test_pr_open_without_pr_step`.

## Task 18 (dall'esecuzione)
- Le `Ruling:` di `progress.md` (in questa cartella) sono decisioni prese durante l'esecuzione: quelle che cambiano o precisano la spec vanno nella rev 23 accanto alle decisioni 1-26. Almeno: G1-G5 (sezione 16, con i nomi dei campi JSON di `gh` non verificati sull'aiuto 2.46), C5 (`related` fuori dalla DoD), C6 (`finish_report` come contratto per `open-pr`), C7 (`unverified-review` chiude il blocco), C8 (`approved` con rilievo scartato che poteva bloccare), C16 (`superseded`, `counted`), C21 (segnale consumato senza lucchetto), C22 (`"v": 1`), C25 (adopt), scope di `finish check` in L2, verificatore che omette id due volte → `needs_you`, Important 1 del Task 9 (`review_unverified` e DoD), stato normalizzato di `prs_for_branch_prefix`, lease atteso nell'autorizzazione `force_push`, dubbio 1 del Task 10 (`approve finding` chiude il blocco), dubbi 2-3 del Task 10, rifiuto di `finish` in sessione non legata con la via d'uscita.
- Per P4 (sezione 3 del piano principale e 18.1): `GATE_MARKER = "<!-- tollgate-verdict"` e il minore del Task 14 (`gate:<sha>` va legato allo SHA giudicato dal gate: P4 mette lo SHA nel marcatore); `finishcheck.check` è l'interfaccia che P4 sostituisce; la regola di scope L2 di `finish check` va ripresa nel gate.
- Esiti della prova reale: `docs/verifiche/2026-10-19-p3b-prova-flusso.md` (sezione 16 della spec).
- Il piano principale riceve anche i rinviati: le righe `minor (deferred)` di `progress.md` le tria la revisione finale dopo questo task; nel piano principale scrivi solo i vincoli per P3c e P4 emersi qui.
