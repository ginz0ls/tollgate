# SDD ledger — plan: docs/superpowers/plans/2026-10-19-tollgate-p3b-chiusura.md

Spec: docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md (rev 22). Worktree: .claude/worktrees/p3b, ramo p3b-chiusura, base cf4fe90. Baseline tests/run: 997 test OK (python3.11 e python3).
Ruling: pre-flight scan delegato a un analista sonnet in sola lettura (preflight-scan.md), giudicato dal controller prima del Task 2; corre in parallelo al Task 1, che non scrive codice di prodotto — come in P2 e P3a — costo se sbagliato: un conflitto sfuggito emerge nelle revisioni dei task.
Task 1: dispatched (sonnet), base cf4fe90
Task 1: implementer DONE_WITH_CONCERNS, commit b5a3630 (G4 nomi dei campi JSON non nell'aiuto di 2.46; G5 formato a riga non provato); review dispatched (sonnet)
Ruling: G1 sì — `gh api` con segnaposto `repos/{owner}/{repo}/…` lanciato con cwd = repo del lavoro, senza `-R`; con `insteadOf` verso un repo locale resta non provato e coperto da `fakegh` — costo se sbagliato: `prs_for_branch_prefix` fallisce col `gh` vero su un origin riscritto, solo nei banchi locali, mai su GitHub.
Ruling: G2 sì — `pr create --head --base --title --body-file`; l'URL non si legge da stdout: dopo la creazione `pr_for_branch` rilegge la PR (decisione 10) — costo se sbagliato: nessuno, una chiamata in più.
Ruling: G3 sì — `pr edit <n> --body-file` — costo se sbagliato: nessuno.
Ruling: G4 in parte — opzioni confermate (`--head`, `--state all`, `--json`, `--limit`); i nomi `headRefOid`, `mergedAt`, `comments` non sono nell'aiuto di 2.46 (manca JSON FIELDS) e si usano dalla conoscenza di `gh` (campi presenti dalla 2.0); `pr_for_branch` passa `--limit 100` esplicito (il default è 30); un'uscita non zero di `gh` è `GhError`, mai «nessuna PR» — costo se sbagliato: col `gh` vero un campo inesistente fa fallire `open-pr`/`prstate` con un errore visibile al primo uso reale (non coperto dal Task 17, che usa `fakegh`): si corregge il nome in un punto.
Ruling: G5 — `--paginate` e `--jq` sì, `--slurp` assente; formato a righe non provato: `run_json_lines` decodifica in sequenza i valori JSON dell'uscita con `JSONDecoder.raw_decode` saltando gli spazi (vale per una riga per oggetto e anche per oggetti su più righe); un testo non JSON è `GhError` — costo se sbagliato: nessuno, la decodifica non dipende dal formato a righe.
Task 1: minor (deferred): spikes/run-p3b-experiments.sh con modo 644 (p3a 755).
Task 1: minor (deferred): lo script non cattura `claude --version` (valore nel rapporto non riproducibile dallo script).
Task 1: minor (deferred): verifiche.md G4 «il limite 30 vale anche con --head» è un'inferenza, non letta nell'aiuto.
Task 1: minor (deferred): nomi dei campi JSON (headRefOid, mergedAt, comments) da controllare col gh vero: tracciato nella Ruling G4 e da riportare nella spec rev 23 (sez. 16).
Task 1: complete (commits cf4fe90..b5a3630, review clean)
Preflight scan: preflight-scan.md (25 conflitti C1-C25: 1 bloccante, 5 da decidere, 19 minori; punti a-g verificati: Task 6 regge senza Task 9, apply.OPS oggi 25, test degli hook verdi se _common conserva i nomi). Ruling per ciascuno:
Ruling: C1 — Task 17: il repo di prova porta uno script stdlib che esegue unittest e scrive il JUnit (`tools/unittest_junit.py`) con `report` configurato come `JUNIT_TOML` del Task 3; M1 resta legato a un test vero — così la prova reale esercita anche il criterio 42 — costo se sbagliato: uno script in più nel banco della prova, nessun effetto sul plugin.
Ruling: C2 — `cli_session` consuma la voce solo con `argv` non nullo; `argv=None` resta lettura senza confronto (test di P3a invariati); tutti i chiamanti reali passano `argv` dopo il Task 2; `test_signal_consumed_once` usa `argv` — costo se sbagliato: nessuno, un chiamante futuro senza `argv` non consumerebbe (va visto in revisione).
Ruling: C3 — `MigrationV3Test` asserisce `str(db.latest_version())` invece di "3"; `tests/test_db.py` già nei Files del Task 3 — costo: nessuno.
Ruling: C4 — le fixture di `test_taskcmd.py` passano a `probe:implementer-web` e `probe:reviewer-web` (forma del criterio 38); `tests/test_taskcmd.py` entra nei Files del Task 5 — costo: nessuno.
Ruling: C5 — `dod._receipt` esclude le righe `command == "related"` come `subagent_stop` (8.1: la DoD guarda il gate completo), con un test in `test_dod.py`, nel Task 3 — costo se sbagliato: una ricevuta related rossa non ferma più la DoD, ma il gate completo deve comunque essere verde.
Ruling: C6 — `open-pr` (esige `HEAD == finish_sha`) prende `guard_scope`, `must_have` e `approvals` da `work_items.finish_report` e ricalcola il resto (`receipt`, `tasks_approved`, `findings`, `skills`, `specialists`, voci dei profili); `finish_report` diventa contratto: `{"items": {chiave: bool|null}, "manual": [...]}` — costo se sbagliato: una voce esterna vecchia, impossibile perché lo SHA è lo stesso.
Ruling: C7 — `approve unverified-review` (solo con almeno 8 cicli): `review_unverified = 1`, chiude il blocco dei cicli se aperto, fase invariata; poi `/tollgate:finish` → `finish check` → `review prepare` «revisione non verificata» → `open-pr` (decisione 10 lo ammette) — spec 8.4 «chiude la revisione come non verificata» — costo: nessuno.
Ruling: C8 — con lo standard acceso, un `approved` dichiarato è non valido se un rilievo scartato per forma «poteva bloccare»: gravità `blocker`/`major` oppure gravità fuori elenco (fail-closed); un `moderate`/`minor` scartato non invalida. `test_finding_with_bad_severity_or_line_dropped` si riscrive (scartato `minor`/`moderate` con riga non intera resta valido; gli altri casi con `outcome="changes"`) e si aggiunge `test_approved_with_dropped_blocker_invalid`; la riga 221 della matrice la aggiorna il Task 18 — costo se sbagliato: un `approved` con un rilievo di gravità illeggibile chiede la riscrittura.
Ruling: C9 — codici di `finish check` come nel piano (0 verde, 1 rosso, 2 rifiuto); la skill `finish` (Task 16): 1 → mostra le voci `[no]`; ogni altro codice diverso da 0 → riporta il messaggio e fermati — costo: nessuno.
Ruling: C10 — `next_step` guarda l'esito attuale dell'ultimo ciclo: `ok` su HEAD in `execution` → `/tollgate:finish` (non `--from-findings`); test in `test_checkpoint` (Task 15) — costo: nessuno.
Ruling: C11 — `orphan_tg` resta com'è; nuova `closed_tg(ctx, repo) -> int | None` in `_common` per il ramo di un lavoro `closed`, e i chiamanti `writes.py`, `bash_rules.py`, `session.py` indicano `/tollgate:cleanup` in quel caso (Task 13, file aggiunti) — costo: tre chiamanti.
Ruling: C12 — `PLAN` e `plan_text` si spostano in `tests/flowkit.py` (che può importare `SECTIONS` da `tests/test_check_post_edit`); `tests/test_taskcmd.py` li reimporta da lì con gli stessi nomi (Task 3) — costo: nessuno.
Ruling: C13 — `finish check` verde con la fase già `review` (altro SHA): solo `set_finish` ed evento, senza `set_phase`; test `test_rerun_in_review_other_sha` (Task 6) — costo: nessuno.
Ruling: C14 — `external` di `compute_dod` è un dizionario `{"guard_scope": bool, "must_have": bool, "approvals": bool}` (Task 6) — costo: nessuno.
Ruling: C15 — `diff_violations(..., components)` legge `components.get(nome, True)` (default acceso come `Ctx.component`); `finish check` passa `cfg.data["components"]` (Task 4) — costo: nessuno.
Ruling: C16 — `open_cycle` scrive `counted = 0`, `close_cycle` lo imposta (decisione 6); un ciclo lasciato aperto su un altro SHA quando `review prepare` apre il successivo si chiude con esito `superseded` (non contato in `counted`, contato in `count`: un ciclo iniziato è un costo, 10 «contando tutti i cicli»); test in `test_reviews` (Task 3, `superseded` usato dal Task 7) — costo se sbagliato: un ciclo interrotto consuma uno degli 8, con `approve unverified-review` come uscita.
Ruling: C17 — `GateRun.sha is None` = gate non eseguito (worktree sporco, config non valida) → `finish check` REFUSED con il messaggio, fase invariata, mai «rosso»; test in `test_finishcheck` (Task 4 e 6) — costo: nessuno.
Ruling: C18 — `reviews.add_report` normalizza i `rejected` prima dell'INSERT (gravità fuori elenco → NULL, `line` non intera → NULL, `file`/`rule`/`text` non stringa → NULL, testo troncato a 2000 caratteri); test con `severity="critical"` (Task 3) — costo: nessuno.
Ruling: C19 — `gitw.is_ancestor(repo, a, b)` nasce nel Task 9 (lo usa `open-pr` per rifiutare prima del push un ramo remoto non antenato di HEAD senza intento `force_push`); il Task 11 lo riusa — costo: nessuno.
Ruling: C20 — nel Task 11 `start` calcola `wt` prima di raccogliere gli intenti da confermare e chiama `sync.complete_interrupted` subito dopo; l'intento completato non entra nella conferma — costo: un riordino in `start.py`.
Ruling: C21 — consumo del segnale senza lucchetto: fail-closed (due Bash paralleli della stessa sessione possono perdere un segnale: si ripete il comando); lo scrive la rev 23 (Task 18) — costo: un comando ripetuto, raro.
Ruling: C22 — la rev 23 (Task 18) riporta anche `abandon` con lavoro nullo (decisione 3), `approve rounds` sui giri di correzione con tetto 8 (13), le ruling di questo ledger che cambiano la spec, e la regola `"v": 1`: gli agenti finali la scrivono nel JSON (regola comune di 18), `parse_final_verdict`/`parse_verifier_results` non la richiedono (campo ignorato come gli altri sconosciuti); 18.5 si allinea con `"v": 1` negli esempi — costo: nessuno.
Ruling: C23 — `test_same_result_as_hook` (Task 4) asserisce le violazioni attese (percorso, tipo, `waiver_type`) su un commit costruito a mano, e in più che `_common.commit_violations` sullo stesso commit dà lo stesso elenco; l'equivalenza col hook resta provata da `test_check_commit`/`test_check_post_bash` invariati — costo: nessuno.
Ruling: C24 — ogni modulo di flusso nuovo converte `GhError`/`GitError`/`GitWriteError` nel proprio esito; in più `cli.main` ha un `except` finale per quelle tre con uscita 1 e messaggio (Task 6, primo sottocomando nuovo) — costo: nessuno.
Ruling: C25 — `adopt`: PR `CLOSED` non unita → ignorata con l'avviso «PR #n chiusa senza merge: ignorata, finish open-pr ne aprirà una nuova» (nessun `pr_number`); tetto dal blocco JSON con `cap_paths` ricalcolati come `actapply._approve_level`; `create_work` con `phase` e `from_approved_spec=True` insieme → `ValueError` (Task 3 e 12) — costo: nessuno.
Ruling: test in più dallo scan §5 (cheap, compatibili): Task 3 test diretti di `set_pr`, `set_finish`, `add_extra_cycles`, `set_review_unverified`, `has_approval`, `intents.complete` e `subTest` in `test_downgrade_and_dismiss`; Task 6 evento `finish_check` {sha, ok} asserito; Task 9 `--update` senza PR aperta rifiutato, `open-pr` con PR `CLOSED` rifiutato con `CLOSED_HINT`, eventi `pr_opened`/`pr_updated`, `test_finish_act_valid_without_session_signal` asserisce anche l'atto `consumed`, `test_block_in_body_parses` confronta `head_sha` con HEAD e `issue`; Task 10 `approve rounds` con entrambi i blocchi aperti rifiutato e `approve rebase` in `execution` resta `execution`; Task 11 `sync` con PR `CLOSED` rifiutato; Task 12 `subTest` nel test dei rifiuti — costo: qualche test in più.
Task 2: dispatched (sonnet), base b5a3630
Task 2: implementer DONE, commit 4ef3f0a (1007 test); review dispatched (sonnet)
Task 2: minor (deferred): nessun test esercita il passaggio reale di argv da cli.main (secondo start/act senza nuovo segnale rifiutato; start 7 --level L1).
Task 2: minor (deferred): docstring di cli_calls.py:3-5 non aggiornato al nuovo elenco dei sottocomandi segnalati, riga oltre 100 colonne.
Task 2: minor (deferred): cli.py:226 continuazione della chiamata a apply_act indentata male.
Task 2: minor (deferred): OSError nella rimozione della voce del segnale lascia il comando ripetibile senza hook, senza test (previsto da C2).
Task 2: minor (deferred): comando non analizzabile di un subagente con «tollgate» e «review» come parole comuni viene negato (accettato dalla decisione 2).
Task 2: complete (commits b5a3630..4ef3f0a, review clean)
Task 3: dispatched (sonnet), base 4ef3f0a
Task 3: implementer DONE, commit 5fd29f7 (1078 test); review dispatched (sonnet)
Task 3: minor (deferred): M1 reviews.py:241 close_cycle non controlla lo stadio né i rilievi con verification nullo (un ciclo non in verify o con un blocker non verificato si chiude ok): contenuto dai chiamanti (Task 7, 8) — portato nel carry.
Task 3: minor (deferred): M2 reviews.py:241 close_cycle ripetuto su un ciclo needs_fix già chiuso rimette la fase a execution e riapre il blocco del tetto: i Task 8 e 10 non lo richiamano dopo approve finding/rounds — portato nel carry.
Task 3: minor (deferred): M3 reviews.py:219 set_decision accetta un «declassamento» verso una gravità più alta.
Task 3: minor (deferred): M4 intents.py:19 request/complete non controllano lavoro, azione e stato di partenza della riga esistente.
Task 3: minor (deferred): M5 tests/test_dod.py:233 assegnazione `kept` inutilizzata.
Task 3: minor (deferred): M6 il test di is_blocking sta in test_reviews.py (come chiede il brief), non in test_verdicts.py.
Task 3: complete (commits 4ef3f0a..5fd29f7, review clean)
Task 4: dispatched (sonnet), base 5fd29f7
Task 4: implementer DONE, commit 0e7558c (1088 test); review dispatched (sonnet)
Task 4: minor (deferred): verify.py, una riga del messaggio «nessun riferimento remoto…» in GateRun oltre 100 caratteri.
Task 4: minor (deferred): tests/test_violations.py importa helper da tests.test_check_writes e usa lab._base (privato).
Task 4: minor (deferred): un dod di profilo senza comando dà ricevuta unverified e run_gate.ok falso — voluto (fail-closed), portato nel carry del Task 6 perché la riga di finish check lo spieghi.
Task 4: minor (deferred): states/junits di GateRun indicizzati per nome: due comandi con lo stesso nome si sovrascriverebbero (teorico, dod_commands esclude i doppioni).
Task 4: complete (commits 5fd29f7..0e7558c, review clean)
Task 5: dispatched (sonnet), base 0e7558c
Task 5: implementer DONE_WITH_CONCERNS, commit 949d1d3 (1111 test; nessun RED separato; rilievo non-dict in rejected → {text}); review dispatched (sonnet)
Task 5: minor (deferred): processo — nessun passo RED separato; il revisore ha ricostruito la prova a posteriori (26 test falliscono sul codice di 0e7558c): test discriminanti.
Task 5: minor (deferred): config.py:342 re.match(…$) accetta un \n finale: meglio re.fullmatch.
Task 5: minor (deferred): task_verdict.py:245-257 _task_files non esercitato (profilo attivato solo da paths, diff illeggibile).
Task 5: minor (deferred): _task_files ripete la base resolve_ref(c0^) or EMPTY_TREE di taskcmd._range e post_bash; import json fuori dal gruppo stdlib.
Task 5: minor (deferred): in test_verdicts.py e test_profiles.py classi nuove dopo unittest.main() (eseguite dalla discovery, non da un lancio diretto).
Task 5: minor (deferred): il problema «ogni risultato ha un id» del verificatore si ripete per ogni elemento difettoso.
Task 5: complete (commits 0e7558c..949d1d3, review clean)
Task 6: dispatched (sonnet), base 949d1d3
Ruling: scope di finish check in L2 (dubbio del Task 6) — `_own_document` non esenta più spec e piano senza condizioni: il piano resta esente solo tramite `is_registered_plan` (stesso blob di `plan_sha`, già in `diff_violations`); la spec è esente solo se il suo blob in HEAD è lo `sha` di `spec-approval.md` in HEAD (altrimenti modificata dopo l'approvazione: fuori scope); i file sotto `docs/superpowers/reviews/<N>/` restano esenti (li scrivono CLI e hook). La regola resta in `finishcheck` (non in `violations`, condiviso con gli hook per commit) — spec 6.2 «blocco dopo l'approvazione» e criterio 36 — costo se sbagliato: in L2 senza `spec-approval.md` (P3c) ogni spec nel diff è fuori scope e `finish check` rosso finché P3c non scrive le approvazioni; P4 deve riprendere la stessa regola nel gate.
Task 6: implementer DONE_WITH_CONCERNS, commit 9b44703 (1146 test); correzione pre-revisione per la Ruling sullo scope L2 inviata all'implementatore
Task 6: correzione pre-revisione commit ec1caa3 (1149 test); residuo: spec senza spec-approval.md esente come .md di docs ma approvals falsa tiene il rosso — nessuna modifica; review dispatched (sonnet)
Task 6: ⚠️ risolto dal controller: in L2 senza spec-approval.md la spec è esente da scope_exempt (Task 4) e non out_of_scope, ma approvals falsa tiene il rosso; la Ruling sullo scope L2 vale con questa precisazione (P3c/P4 lo sanno dalla rev 23).
Task 6: minor (deferred): predicato «task non done/approved» duplicato rispetto a dod._tasks.
Task 6: minor (deferred): json.loads su finish_report non protetto.
Task 6: minor (deferred): git.changes calcolato due volte in finish check.
Task 6: minor (deferred): se set_phase fallisce dopo set_finish manca l'evento finish_check.
Task 6: minor (deferred): approvals._value gestisce male un valore tra virgolette seguito da commento.
Task 6: minor (deferred): mancano i test per kind sbagliato in _approvals e per must_have_tests spento.
Task 6: minor (deferred): docstring di _own_document dice «L2» ma l'esenzione di reviews/<N>/ vale a ogni livello.
Task 6: complete (commits 949d1d3..ec1caa3, review clean)
Task 7: dispatched (sonnet), base ec1caa3
Task 7: implementer DONE_WITH_CONCERNS, commit a9879b7 (1170 test); dubbio issue.md risolto dal controller (lo scrive start.py:77); review dispatched (sonnet)
Ruling: ⚠️ del Task 7 (verificatore che omette degli id, rilanciato senza limite) — il Task 8 conta i riporti del verificatore per ciclo: al secondo riporto valido dello stesso ciclo con rilievi ancora senza esito, apre `needs_you` «verificatore senza esito su: <id>» invece di un terzo lancio; mai `unverified` automatico (non bloccherebbe un major non verificato) — spec 8.6 «open-pr rifiuta se un rilievo registrato non ha esito» — costo se sbagliato: un blocco in più quando il verificatore sbaglia due volte, sciolto con resolve o approve finding.
Task 7: fix round 1 dispatched (resume implementer): Important finalreview.py:198 TaskError inghiottito; più minori a costo nullo (import phases inutilizzato, "v": 1 nei formati JSON dei brief per C22)
Task 7: fix round 1 commit a336123 (1171 test); re-review dispatched (sonnet)
Task 7: fix round 1/5 (3 addressed, 0 open — TaskError del piano inghiottito, import phases, v:1 nei brief; commits a9879b7..a336123)
Task 7: minor (deferred): check_plan ricalcolato per ogni agente del ciclo (la ri-revisione dice: ora letto una volta per ciclo — da confermare nel triage).
Task 7: minor (deferred): dopo un rebase il brief usa lo SHA vecchio del ciclo con head nuovo, senza spiegarlo.
Task 7: minor (deferred): con default_ref None il messaggio d'errore è «riferimento git non valido: None».
Task 7: minor (deferred): issue.md citato nel brief anche se start non l'ha scritto (issue non leggibile alla ripresa).
Task 7: complete (commits ec1caa3..a336123, review clean)
Task 8: dispatched (sonnet), base a336123
Task 8: implementer DONE_WITH_CONCERNS, commit e7aef10 (1192 test; ValueError di add_report ignorato senza evento; VERIFIER/unjudged_ids/verifier_incomplete in reviews); review dispatched (sonnet)
Task 8: minor (deferred): subagent_stop.py:67 salta sempre i revisori finali in attesa, ma final_review ha component final_review: con il componente spento a ciclo aperto il revisore resta running (raro).
Task 8: minor (deferred): apply._final_rules ricalca finalreview._profiles senza il ripiego default_ref per la base (più severo, non meno).
Task 8: minor (deferred): except ValueError: return in apply._review_report perde la traccia del riporto scartato (il runner l'avrebbe già loggato come «registrazione non applicata»).
Task 8: minor (deferred): mancano i test per un revisore interrupted che ha cambiato file e per len(apply.OPS) == 27.
Task 8: minor (deferred): awaiting_final accetta in stadio verify un verificatore di un ciclo precedente (protetto dal code per ciclo).
Task 8: complete (commits a336123..e7aef10, review clean)
Task 9: dispatched (sonnet), base e7aef10
Task 9: implementer DONE_WITH_CONCERNS, commit 7b203d0 (1266 test; firme con parametri in più, review_unverified esclude i rilievi dalla DoD); review dispatched (sonnet)
Ruling: Important 1 del Task 9 (review_unverified) — con `review_unverified` la DoD guarda comunque l'ultimo ciclo chiuso su HEAD (o stesso patch-id): un bloccante confermato senza `approve finding` ferma `open-pr` (spec 8.7; 8.4 dice solo «chiude come non verificata e lo scrive nella PR»); senza cicli chiusi la voce `findings` è vera e `verdict.outcome` null — costo se sbagliato: dopo 8 cicli serve anche `approve finding` sui bloccanti rimasti.
Ruling: `prs_for_branch_prefix` con l'API REST (Task 9) — il jq normalizza `state` nella forma di `gh pr list` usata da P3a: `state: (if .merged_at then "MERGED" else (.state | ascii_upcase) end)`; `fakegh` stampa la forma già normalizzata — costo se sbagliato: col `gh` vero una PR unita vista come chiusa, solo nel messaggio di rifiuto di start/adopt.
Task 9: fix round 1 dispatched (resume implementer): review_unverified nella DoD, take_force prima del push, troncamento per voce in prbody, state normalizzato nel jq di prs_for_branch_prefix
Task 9: fix round 1 commit e96325b (1271 test); re-review dispatched (sonnet)
Task 9: fix round 1/5 (4 addressed, 0 open — review_unverified nella DoD, autorizzazione al push forzato consumata dopo il push, troncamento per voce, state normalizzato nel jq; commits 7b203d0..e96325b)
Task 9: minor (deferred): pr_for_branch non filtra le PR da fork con lo stesso nome ramo.
Task 9: minor (deferred): messaggio d'errore di gh ripetuto tre volte.
Task 9: minor (deferred): json.loads non protetti in open-pr (traceback invece di rifiuto:).
Task 9: minor (deferred): merge_detected non atomico con il cambio di fase.
Task 9: minor (deferred): un atto finish resta vivo se il processo muore tra intents.complete e acts.consume (la ripetizione aggiorna la stessa PR).
Task 9: minor (deferred): corpo della PR senza tetto complessivo (molte voci possono superare il limite di GitHub).
Task 9: minor (deferred): non verificato se GitHub attiva «Closes #N» (è la prima riga, fuori dai recinti).
Task 9: complete (commits e7aef10..e96325b, review clean)
Task 10: dispatched (sonnet), base e96325b
Task 10: implementer DONE_WITH_CONCERNS, commit 2132b7a (1295 test)
Ruling: dubbio 1 del Task 10 — `approve finding` chiude il blocco dei cicli se aperto, qualunque sia l'esito ricalcolato (spec 10 «il blocco si scioglie con approve rounds, approve finding o resolve», decisione 14): il blocco è un punto di decisione dell'utente e l'atto è quella decisione; il tetto non si aggira perché ogni ciclo contato successivo con `needs_fix` lo riapre (decisione 6) e oltre 8 cicli `review prepare` rifiuta — costo se sbagliato: un ciclo in più prima del blocco successivo.
Ruling: dubbi 2 e 3 del Task 10 accettati — `findings_confirmed` ricalcolato senza i `dismissed` con `counted` invariato (il ciclo resta contato: 10 conta i cicli con rilievi confermati, la decisione dell'utente non cancella la storia); `resolve` al tetto con 8 cicli fatti rifiuta e indica `approve unverified-review` (spec 10 «massimo 8 cicli»); `approve rebase` con il rebase ancora in corso rifiuta (6.5: si risolve fuori da Claude prima) — costo: nessuno.
Task 10: correzione pre-revisione per la Ruling sul dubbio 1 inviata all'implementatore
Task 10: correzione pre-revisione commit 38ff416 (1296 test); review dispatched (sonnet)
Task 10: minor (deferred): approve finding su un rilievo di un ciclo non ultimo non chiude il blocco dei cicli (caso non coperto dalla Ruling né da test).
Task 10: minor (deferred): ultimo ciclo superseded con un rilievo confirmed → recompute_outcome solleva ValueError non gestito dopo che la decisione è scritta (traceback).
Task 10: minor (deferred): nessun test asserisce nome -r6, launch e inherit al sesto giro di correzione.
Task 10: minor (deferred): FIX_CAP in actapply.py:25 duplica il testo del motivo di taskcmd (meglio una costante condivisa).
Task 10: minor (deferred): _grant_cycles+close_block e close_block+authorize_force non atomici; per il rebase authorize_force prima di close_block.
Task 10: minor (deferred): il motivo di approve finding sta solo nell'atto, non negli eventi del rilievo.
Task 10: complete (commits e96325b..38ff416, review clean)
Task 11: dispatched (sonnet), base 38ff416
Task 11: implementer DONE, commit 8a3e450 (1314 test; sync ammesso anche in review con PR esistente; push nostro riscritto non conta come divergenza); review dispatched (sonnet)
Ruling: lease del push forzato (minore 4 della revisione del Task 11) — l'autorizzazione `force_push` porta nei suoi dati lo SHA remoto atteso (`sync`: la punta di `origin/<ramo>` dopo l'integrazione; `approve rebase`: la punta remota letta all'applicazione); `open_pr` usa quello come lease quando c'è, altrimenti lo SHA letto prima del push (decisione 10); un remoto avanzato nel frattempo fa fallire il push con lease e l'autorizzazione resta valida — miglioramento compatibile a basso costo — costo se sbagliato: un push rifiutato in più, da ripetere con un nuovo sync.
Task 11: fix round 1 dispatched (resume implementer): commit integrati con --ff-only registrati subito (Important), lease atteso nell'autorizzazione
Task 11: fix round 1 commit 224a508 (1319 test); re-review dispatched (sonnet)
Task 11: fix round 1/5 (2 addressed, 0 open — commit integrati con --ff-only registrati subito, lease atteso nell'autorizzazione; commits 8a3e450..224a508)
Task 11: minor (deferred): nessun test sull'ordine dell'intento sync rispetto al rebase, su rebase già in corso all'avvio, su merge_ff_only che fallisce, su finish check rosso dopo il rebase.
Task 11: minor (deferred): processo morto tra integrazione e registrazione dei commit: la ripetizione li recupera solo se il rebase riesce, non con un conflitto.
Task 11: minor (deferred): _realign non rinnova il lease se esiste già un'autorizzazione force_push non usata.
Task 11: complete (commits 38ff416..224a508, review clean)
Task 12: dispatched (sonnet), base 224a508
Task 12: implementer DONE_WITH_CONCERNS, commit d04bf07 (1343 test; gh.pr_body aggiunto; livello ricalcolato come da spec 12.4); review dispatched (sonnet)
Task 12: fix round 1 dispatched (resume implementer): approvazioni valide solo con sha uguale al blob e path del piano combaciante (Important); righe «PR aperta»/«tetto ripristinato» solo a passo riuscito
Task 12: fix round 1 commit fa6e68d; re-review dispatched (sonnet)
Task 12: fix round 1/5 (2 addressed, 0 open — approvazioni valide solo con sha e path combacianti, righe solo a passo riuscito; commits d04bf07..fa6e68d)
Task 12: minor (deferred): etichette dell'issue illeggibili → solo un avviso e il livello può scendere (coerente con openpr._labels, diverso dalla PR illeggibile che rifiuta).
Task 12: minor (deferred): regola «autore esterno → L2» (6.1) non applicata in adopt (spec 12.4 dice «diff più etichette»).
Task 12: minor (deferred): ramo locale e remoto diversi: si usa la punta locale senza avviso.
Task 12: minor (deferred): adopt.py usa start._write_issue e start.EXCLUDES (accoppiamento tra moduli).
Task 12: minor (deferred): sqlite3.Error in acts.consume dopo create_work dà un rifiuto con il lavoro già creato.
Task 12: complete (commits 224a508..fa6e68d, review clean)
Task 13: dispatched (sonnet), base fa6e68d
Task 13: implementer DONE_WITH_CONCERNS, commit e32ba57 (1363 test); review dispatched (sonnet)
Task 13: minor (deferred): orfani di cleanup solo tg/<N>-* mentre la decisione 19 dice tg/* (coerente con orphan_tg e adopt): da annotare nella rev 23.
Task 13: minor (deferred): dopo worktree_remove nessun `git worktree prune`: resta la voce di un worktree con la cartella sparita.
Task 13: minor (deferred): abandon, processo morto tra set_phase e consume: l'atto resta pending fino alla scadenza.
Task 13: minor (deferred): regex _TG duplicata tra closing.py e _common.py.
Task 13: minor (deferred): mancano test per cwd dentro il worktree, cartella del worktree sparita, --confirm su PR chiusa insieme ad altre conferme.
Task 13: complete (commits fa6e68d..e32ba57, review clean)
Task 14: dispatched (sonnet), base e32ba57
Task 14: implementer DONE, commit 505bd6d (1374 test; source gate:<HEAD>, commento troncato a 20000); review dispatched (sonnet)
Task 14: minor (deferred): fixtask.py:62-64 gate:<sha> usa HEAD del worktree, non il commit giudicato dal gate: un secondo --from-gate prima del nuovo verdetto rilegge il commento vecchio e crea un duplicato — contratto da fissare con P4 (sha nel marcatore o headRefOid), da scrivere nella rev 23.
Task 14: minor (deferred): fixtask.py:55-56 autore del commento col marcatore non verificato (resta dato recintato).
Task 14: minor (deferred): fixtask.py:74-82 ripete i controlli di _task_start e ne chiama la funzione privata.
Task 14: minor (deferred): taskcmd.py:66-73 _fix_files rilegge i rilievi dal vivo (instradamento può cambiare dopo un dismiss).
Task 14: minor (deferred): brief.py:42-44 _finding stampa la gravità originale, non quella effettiva dopo un declassamento.
Task 14: minor (deferred): mancano test per rollback, L0 e --from-gate da CLI; asserzione sul recinto del gate lasca.
Task 14: complete (commits e32ba57..505bd6d, review clean)
Task 15: dispatched (sonnet), base 505bd6d
Task 15: implementer DONE_WITH_CONCERNS, commit 399b2c0 (1383 test; «riga 133» è il rilievo della revisione finale di P3a, non della skill); review dispatched (sonnet)
Task 15: minor (deferred): checkpoint.py:57 _review_brief prende il review-<k>.md con k più alto (contatore globale, non numero del task): euristica fissata dal test.
Task 15: minor (deferred): CAP_PREFIXES in checkpoint.py:21 duplica CAPS e actapply.FIX_CAP.
Task 15: minor (deferred): _cap_step con più blocchi di tetto aperti ne indica solo il primo (approve rounds poi rifiutato).
Task 15: complete (commits 505bd6d..399b2c0, review clean)
Task 16: dispatched (sonnet), base 399b2c0
Task 16: implementer DONE, commit b208c80 (1390 test; claude plugin validate --strict: passed); review dispatched (sonnet)
Task 16: fix round 1 dispatched (resume implementer): atto finish decaduto dal commit del coordinatore, approve rounds al tetto degli 8 cicli, sync codice 2 per rami divergenti; più i minori che sono discordanze testo/codice
Task 16: fix round 1 commit cbda3a7; re-review dispatched (sonnet)
Task 16: fix round 1/5 (9 addressed, 0 open — atto finish decaduto dal commit del coordinatore, approve rounds al tetto degli 8 cicli, sync codice 2 per rami divergenti, minori 4-9; commits b208c80..cbda3a7)
Task 16: minor (deferred): tests/test_manifest.py:475-487 test di sola presenza di sottostringhe («committa», gh pr create).
Task 16: minor (deferred): skills/start/SKILL.md, sotto «1, rifiuto» resta la frase sulla PR chiusa senza merge (ora codice 3): testo morto.
Task 16: minor (deferred): test_skills_use_program_command_form controlla solo le skill, non gli agenti (agents/implementer.md di P3a cita python3 '<percorso>/bin/tollgate' con apici singoli).
Task 16: complete (commits 399b2c0..cbda3a7, review clean)
Task 17: dispatched (sonnet), base cbda3a7
Task 17: implementer DONE_WITH_CONCERNS, commit 313cdac (passo 4a non riuscito: sessione di claude -p con --continue dalla radice non legata al lavoro, limite come D3 di P3a; 4b dal worktree: ciclo 1 ok, PR #1 nel finto gh, fase pr_open, ramo spinto = HEAD; verificatore non esercitato); review dispatched (sonnet)
Task 17: fix round 1 dispatched (resume implementer): rapporto (I1 non esercitato in interattivo, M1 sessioni reali, M2 successo composito, M4 sorgente letto, M5 isolamento) e guida d'uscita per finish in sessione non legata (messaggio di checks/acts.py e skill finish)
Task 17: fix round 1 commit 173949e; re-review dispatched (sonnet)
Task 17: fix round 1/5 (6 addressed, 0 open — via d'uscita nel rifiuto di finish non legato e nella skill, rapporto corretto su sessioni, successo composito, riproducibilità, sorgente letto, rete; commits 313cdac..173949e)
Task 17: minor (deferred): l'elenco d'uso in fondo a spikes/run-p3b-flow.sh non cita passo4-radice (l'intestazione sì).
Task 17: minor (deferred): la ripresa di start non lega la sessione nei ritorni anticipati (PR unita, --confirm mancante, worktree non ripristinato).
Task 17: complete (commits cbda3a7..173949e, review clean)
Task 18: dispatched (sonnet), base 173949e
Task 18: implementer DONE, commit 78705e2 (1396 test, anche -W error::ResourceWarning); review dispatched (sonnet)
Task 18: fix round 1 dispatched (resume implementer): riferimento al registro in docs/sdd/, spec 6.5 sync in review con PR e push riscritto non divergente; minori 11.4 e 12.4
Task 18: fix round 1 commit a29f588; re-review dispatched (sonnet)
Task 18: fix round 1/5 (5 addressed, 0 open — registro in docs/sdd, spec 6.5 sync, 11.4 giri inherit, 12.4 fase plan, Stato; commits 78705e2..a29f588)
Task 18: minor (deferred): test del criterio 26 in test_criteria_p3b asserisce il rifiuto di open-pr solo con returncode != 0; helper prepare_refused_open_pr con nome fuorviante; il «finish successivo» (ciclo 2) provato solo a livello libreria (test_openpr).
Task 18: complete (commits 173949e..a29f588, review clean)
Final review: dispatched (opus), range cf4fe90..a29f588
Final review: final-review.md — non pronto al merge: 0 Critical, 4 Important (I-1 rilievi senza esito di cicli superati o dopo unverified-review bloccano open-pr per sempre; I-2 sync in execution con task non done riscrive i commit del task; I-3 pr_for_branch prende PR da fork; I-4 lease force_push mai rinnovato); triage: 5 righe dei minori da correggere (42=I-3, 57=I-4, 58-59 livello di adopt, 63 testo spec 12.4), 77 rinviabili con destinazione; 6 minori nuovi m1-m6.
Ruling: I-1 — prima strada del revisore: `reviews.supersede` porta a `unverified` (motivo «ciclo superato») i rilievi senza esito del ciclo; `approve unverified-review` fa lo stesso sui rilievi senza esito dell'ultimo ciclo (motivo «revisione non verificata») — il blocco 18.1 non ha mai rilievi con verification nullo e spec 8.6 resta vera («salvo quelli non verificati») — costo se sbagliato: un rilievo mai verificato di un ciclo superato non ferma la PR, ma il ciclo nuovo lo rivede se il difetto c'è ancora.
Ruling: I-2 — `sync` rifiuta in `execution` se un task è `running` o `review`, o non `done` con commit, o se c'è un subagente scrittore `running` sul lavoro («chiudi o riporta in attesa il task k, poi /tollgate:sync»); niente rimappatura per patch-id — costo se sbagliato: un sync rimandato a fine task.
Ruling: I-3 — `pr_for_branch` chiede `isCrossRepository` e scarta le PR da fork; `open-pr` modifica una PR esistente solo se il suo `headRefOid` è lo SHA appena spinto (altrimenti rifiuto); `adopt` ripristina il tetto solo da una PR non da fork — costo se sbagliato: col gh vero un campo in più nel JSON (G4: nome da verificare al primo uso).
Ruling: I-4 — `_realign` aggiorna il `lease` di un'autorizzazione `authorized` alla punta remota appena letta; un push con lease fallito fa dire a `open-pr` «il ramo remoto è avanzato: /tollgate:sync» — costo: nessuno.
Ruling: triage 58-59 — `adopt` con `author_association` fuori da `TRUSTED_AUTHORS` dà almeno L2 (spec 5 e 6.1, come `start`); con l'issue illeggibile `adopt` rifiuta come per la PR illeggibile — costo se sbagliato: un adopt senza rete rifiuta invece di procedere.
Ruling: m1-m5 inclusi nel giro unico (consigliati dal revisore, costo basso, compatibili: preferenza dell'utente). Le correzioni di spec vanno nella rev 23 stessa (non ancora unita su main), non in una rev 24 — costo: nessuno.
Final review: fix wave dispatched (sonnet, implementatore nuovo), base a29f588
Final review: fix wave commits a29f588..6da05bb (1417 test, anche -W error::ResourceWarning); re-review dispatched (sonnet)
Final review: re-review final-rereview.md — 12 punti INDIRIZZATI, nessun danno nuovo Critical/Important; fuori ambito: prs_for_branch_prefix non filtra le PR da fork (minor, P4), nome isCrossRepository da verificare col gh vero (G4).
Final review: minor (deferred): test di I-4 marca R2 come commit noto con un evento invece di riprodurre «Update branch» e integrazione a mano (stesso codice provato).
Final review: closed (commits a29f588..6da05bb), nessun Critical/Important aperto
Suite: 3 corse verdi a 6da05bb — tests/run (python3.11 e python3) e python3 -B -W error::ResourceWarning, 1417 test, nessun «unclosed». Rapporto all'utente consegnato con la richiesta dell'OK per il merge.
Merge: OK dell'utente il 20/10/2026; main unito in fast-forward cf4fe90..6da05bb; registro copiato in docs/sdd/2026-10-19-tollgate-p3b-chiusura/.
