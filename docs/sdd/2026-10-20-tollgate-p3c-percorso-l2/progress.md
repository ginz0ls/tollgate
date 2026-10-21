# SDD ledger — plan: docs/superpowers/plans/2026-10-20-tollgate-p3c-percorso-l2.md

Spec: docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md (rev 23). Worktree: .claude/worktrees/p3c, ramo p3c-percorso-l2, base 8ea0f39. Sessione del controller partita dalla radice del repo.
Ruling: pre-flight scan delegato a un analista sonnet in sola lettura (preflight-scan.md), giudicato dal controller prima del Task 2; corre in parallelo al Task 1, che non scrive codice di prodotto — come in P2, P3a e P3b — costo se sbagliato: un conflitto sfuggito emerge nelle revisioni dei task.
Task 1: dispatched (sonnet), base 8ea0f39
Baseline tests/run: 1417 test OK (python3.11 e python3), circa 12 minuti per interprete.
Preflight scan: preflight-scan.md (20 conflitti D1-D20: 1 bloccante, 4 da decidere, 15 minori; punti a-i verificati: con le cause nuove si rompe solo test_table_is_exact; decisione 26 necessaria, riprodotta; apply.OPS oggi 27; load_config_at esiste; orologi: report_round regge). Ruling per ciascuno:
Ruling: D1 — nel Task 5 i giri chiusi si creano dalla libreria con un helper di banco `FlowLab.closed_round(kind, counts, *, viewpoint=None)` (open_round + close_round sul blob attuale, esito da auditrules); `FlowLab.report_round` si sposta nel Task 6, che lo esercita con l'hook vero — il Task 5 non può dipendere da codice del Task 6 — costo se sbagliata: i test del Task 5 non attraversano SubagentStop (lo fanno i Task 6, 7, 8, 15).
Ruling: D2 — variante B, fedele alla spec 6.2 punto 4 («l'ultimo passo è un giro avversariale di conferma sulla versione finale»): durante l'audit a lenti basta che l'avversariale sia «passato» (ultimo giro avversariale chiuso pulito su qualunque SHA, o sospeso); la conferma sul blob attuale (`adversarial_ok`) si chiede solo ad audit a lenti chiuso o sospeso (o con una fetta) e resta la condizione di `approve spec` — costo se sbagliata: i cicli a lenti esaminano versioni non riviste dall'avversario fino alla conferma finale, che resta obbligatoria.
Ruling: D3 — `files` di `locate_spec_approval`: HEAD per `approve plan`, `audit prepare` in `plan`, `finish check`, `open-pr` (HEAD = SHA spinto) e `adopt` (punta del ramo); punta del ramo predefinito per `start --spec`; disco solo per `violations.locked_docs`. `approve plan` e `audit prepare` in `plan` con un `spec-approval.md` su disco ma non in HEAD rifiutano con «committa docs/superpowers/reviews/<N>/spec-approval.md» — costo se sbagliata: un passo in più per il coordinatore, che la skill già prescrive.
Ruling: D4 — `openpr.facts`: `spec_reviews_dir` e `spec_audit` solo con `spec_path` valorizzato (L2 e fette successive), altrimenti null; `test_counters_and_reviews_dirs` si riscrive con un lavoro L2 con `spec_path` — costo se sbagliata: un L1 con approvazione a mano perde i campi nel blocco PR, che in L1 non hanno significato (8.7).
Ruling: D5 — `reopen` rifiuta con la stessa regola di `sync._in_use` (task `running`/`review`, implementatore `running`, task non `done` con commit), estratta in una funzione pubblica condivisa e usata da entrambi; i messaggi di `sync` restano invariati — costo se sbagliata: un `reopen` rifiutato in più, sbloccabile con `resolve writer` o chiudendo il task.
Ruling: D6 — `suspend_on_resolve` decide dal DB, non solo dal testo: tipo da `cap_kind(reason)`; scrive la sospensione solo se la condizione del tetto vale davvero (avversariali: ultimo giro chiuso del tipo non pulito e giri chiusi ≥ tetto, numero = quel giro; lenti: giri chiusi ≥ tetto con audit non chiuso, oppure motivo `DECLINE_REASON` con 0); altrimenti chiude il blocco senza sospendere — costo se sbagliata: un blocco aperto a mano con quel prefisso non sospende (il caso giusto).
Ruling: D7 — decisione 26 confermata (va nella rev 24, 7.4 e 8.3); `locked_docs` si calcola una volta per chiamata di `diff_violations`, non per file — costo: nessuno.
Ruling: D8 — decisione 16 confermata; il Task 9 riscrive `test_adopt.py:146-152` e i tre sottocasi «approval» di `test_l2_superseded_or_mismatched_approvals_go_back` — costo: nessuno oltre i test.
Ruling: D9 — `superseded` come esito e colonne nuove confermati (rev 24: 12.2, 18.3) — costo: nessuno.
Ruling: D10 — i test esistenti rotti e non nominati entrano nei task: Task 4 (`test_db.py:198-199,219`, `test_phases.py` tabella), Task 7 (`test_check_common.py:30`), Task 9 (`test_openpr.py:777`, `test_adopt.py:146-181`, helper `l2_lab` di `test_finishcheck.py`), Task 10 (`test_checkpoint.py:89-100` con un lavoro L2), Task 13 (`test_manifest.py:125`). Riscriverli non vuol dire indebolirli — costo: nessuno.
Ruling: D11 — `git.ls_files_at` usa `ls-tree -r -z --name-only` e divide su `\0` — costo: nessuno.
Ruling: D12 — `render_approval` e `render_report` sollevano `ValueError` per valori stringa con a capo, `"` o caratteri di controllo; `audit prepare` rifiuta una spec o un piano con un percorso così — costo se sbagliata: un nome di file strano rifiutato.
Ruling: D13 — l'operazione `audit_report` cattura `OSError` nella scrittura del report e registra l'evento `veto` come per il giro non più aperto (giro lasciato aperto); `audit_round` emette `subagent_finish` prima di `audit_report` — costo: nessuno.
Ruling: D14 — accettato: un agente tardivo di un giro superato passa dal controllo di manomissione di `subagent_stop` come ogni agente di sola lettura; il test non tocca file tra il suo start e il suo stop e lo dichiara; la skill impone il primo piano — costo se sbagliata: un `needs_you` spurio se il coordinatore lancia in background e corregge nel frattempo.
Ruling: D15 — Task 4 aggiunge `git.blob_at(repo, ref, path) -> str | None` (blob nell'albero di un riferimento, `None` se assente) usato da chi legge «a HEAD»; Task 5 promuove `finalreview._launch_line` a `launch_line` pubblica e `adopt._find_plan` a `find_plan` pubblica (stesso comportamento, chiamanti aggiornati) — costo: nessuno.
Ruling: D16 — `audits.last_closed(conn, work, kinds: tuple[str, ...])` con la tupla dei tipi, mai le righe `superseded`; `approve spec` passa i due tipi della spec; test dedicato — costo: nessuno.
Ruling: D17 — la sospensione con numero 0 si legge con `in`, mai per verità; test `audit decline` → `resolve` → `audit prepare`/`approve spec` nel Task 7 — costo: nessuno.
Ruling: D18 — testo del piano corretto nei brief: (a) il passo 6 del Task 11 mette la frase «l'esenzione di reviews/<N>/ vale a ogni livello» nella docstring di `violations.scope_exempt`; (b) il Task 15 estende `test_criteria_p3c.py` creato dal Task 9; (c) `tests/test_git.py` nei file del Task 11; (e) la tabella di `test_phases.py` si chiama `EXPECTED`/`CAUSES`; (f) il testo di `post_edit` in L2 («plan-adversary, poi /tollgate:approve plan») punta a `/tollgate:spec-audit`, nel Task 10 — costo: nessuno.
Ruling: D19 — un solo costruttore `audits.cap_reason(kind, number) -> str` per i motivi dei tetti (prefisso di `CAP_REASONS` più «(giro <n>)», per le lenti il testo fisso); `_cap_step` sostituisce `<id>` con l'id del blocco; nessun letterale `tollgate audit …` nudo in `bin/` (sempre `program_command`) — costo: nessuno.
Ruling: D20 — `report_round` scrive `self.lab.now` (mai un attributo ombra su FlowLab) e lo dichiara nel docstring; nessun test confronta ore del banco con ore reali; gli atti dei test del Task 7-8 si applicano dalla libreria con `now=fl.now` come in P3b — costo: nessuno.
Ruling: punto c dello scan — `awaiting_audit` ha il ripiego `governing_work` quando `row["work"]` è nullo, come `awaiting_review`/`awaiting_final` — costo: nessuno.
Task 1: implementer DONE_WITH_CONCERNS, commit 835aa1c (colonna «Dove incide» dedotta dai titoli dei task; versioni diverse tra le prove); review dispatched (sonnet)
Task 2: dispatched (sonnet), base 835aa1c
Task 1: review — Da correggere: 3 Important (colonna «Dove incide»: EnterWorktree attribuito a Task 13/14 invece che già usato da start/adopt; UserPromptExpansion/command_args attribuiti a Task 7/8 invece che ad act apply esistente e skill reopen del Task 13; agent_type descritto come riconoscimento degli auditor, mentre il Task 6 usa subagents.type).
Task 1: minor (deferred): la riga SubagentHandback non cita handbackReport di PostToolUse Agent in primo piano (correzione di P0).
Ruling: il giro di correzione 1 del Task 1 parte dopo il commit del Task 2 — due subagenti che committano e lanciano tests/run nello stesso worktree intreccerebbero indice e suite — costo: il Task 1 si chiude più tardi, nessun task dipende da lui.
Task 2: implementer DONE, commit cf5f0e4 (1444 test; scelte di check_l2: approvazione mancante o superata → niente ricerca dei report; approvazione propria con sha vecchio vince su quella di un'altra issue; counts con esattamente quattro gravità); review dispatched (sonnet)
Task 1: fix round 1 dispatched (resume implementer, sonnet), base cf5f0e4
Task 2: minor (deferred): check_l2 continua a cercare i report del piano anche con plan-approval superato (asimmetria con il ramo della spec).
Task 2: minor (deferred): check_l2 non confronta il `path` di plan-approval.md con plan_path.
Task 2: minor (deferred): i report della spec non sono legati allo spec_sha dell'approvazione (conforme a D15): da ricordare nel gate di P4.
Task 2: minor (deferred): `slices` non intero nell'intestazione di spec-approval è ignorato in silenzio (lens non richiesto).
Task 2: minor (deferred): chiavi duplicate in `counts` dell'intestazione: vince l'ultima.
Task 2: minor (deferred): un test di check_l2 asserisce solo che esista un problema, non il messaggio; manca il caso di approvazione propria con `path` diverso.
Task 2: complete (commits 835aa1c..cf5f0e4, review clean)
Task 1: fix round 1 commit 221b47f; re-review dispatched (sonnet)
Task 3: dispatched (sonnet), base 221b47f
Task 1: fix round 1/5 (3 addressed, 0 open — Dove incide: EnterWorktree, UserPromptExpansion/command_args, agent_type; anche il minore su handbackReport; commits cf5f0e4..221b47f)
Task 1: complete (commits 8ea0f39..221b47f, review clean)
Task 3: implementer DONE, commit 9982594 (1456 test; problemi del JSON solo per nome; campo v non richiesto; counts None se non valido); review dispatched (sonnet)
Task 4: dispatched (sonnet), base 9982594
Task 3: minor (deferred): auditrules.py:76 `number` float 1.0 passa il confronto con 1.
Task 3: minor (deferred): auditrules.py:80-83 con plan_sha=None o viewpoint=None passati dal chiamante per un giro che li richiede, un JSON senza quel campo è valido; il viewpoint atteso non è controllato contro VIEWPOINTS (il chiamante del Task 6 passa sempre i valori del giro).
Task 3: minor (deferred): un esito diverso da empty e superseded conta come findings senza segnalarlo.
Task 3: minor (deferred): campo `v` della riga JSON non richiesto (nessun controllo di versione futuro).
Task 3: complete (commits 221b47f..9982594, review clean)
Task 4: implementer DONE, commit 0ae2d16 (1481 test; reset_plan azzera subagents.task e tiene le righe; supersede solo su giro aperto; CHECK su stage; scope_exempt con parametro locked opzionale); review dispatched (sonnet)
Task 4: review — Da correggere: 1 Important (finishcheck._own_document ripete l'esenzione di reviews/<N>/ ora in scope_exempt; letterale invece di approvals.REVIEWS_DIR in violations).
Task 4: minor (deferred): audits.close_round non valida outcome e counts; supersede ha `now` inutilizzato.
Task 4: minor (deferred): test_latest_version_is_5 sta nella classe MigrationV4Test.
Task 4: minor (deferred): git.ls_files_at non protegge un ref che inizia con `-`.
Ruling: il minore di Task 4 su git.blob_at (una cartella restituisce lo SHA dell'albero) entra nel giro di correzione 1 con `^{blob}` — il contratto «blob o None» lo usano i Task 5, 7, 9 per leggere a HEAD; costo basso — costo se sbagliata: nessuno.
Task 4: fix round 1 dispatched (resume implementer), base 0ae2d16
Task 4: fix round 1 commit 3d00185 (blob_at con ls-tree: ^{blob} non funziona su <ref>:<path>); re-review dispatched (sonnet)
Task 4: fix round 1/5 (2 addressed, 0 open — esenzione duplicata in _own_document e letterale REVIEWS_DIR; blob_at solo blob; commits 0ae2d16..3d00185)
Task 4: minor (deferred): test_blob_at_directory_is_none non copre il prefisso comune (d/f con d/f.md presente; comportamento verificato corretto a mano).
Task 4: complete (commits 9982594..3d00185, review clean)
Task 5: dispatched (sonnet), base 3d00185
Task 5: implementer DONE_WITH_CONCERNS, commit a11795c (1546 test; TDD parziale: test di prepare scritti dopo il codice; rifiuti con passo come PrepareResult codice 1, AuditError per errori d'ambiente; peek senza prefisso; plan_adversary spento richiede le precondizioni di approve plan; decline rifiuta anche con lenti già sospese; helper FlowLab.approve_spec_file); review dispatched (sonnet)
Task 5: review — Da correggere: I-1 con plan_adversary spento un giro plan-adversarial aperto non diventa superseded (fase approval con giro aperto: approve plan rifiuta, lavoro fermo); I-2 titolo del task (testo non fidato del piano) nel brief fuori da un recinto.
Ruling: nel giro di correzione 1 del Task 5 entrano anche due minori a basso costo: un rifiuto fix_spec non deve lasciare aperto un giro su un altro SHA (decisione 3: «giro aperto su un altro SHA → superseded e si prosegue», prima di ogni altro ramo); il ValueError di open_round diventa un AuditError/rifiuto, mai un traceback — costo se sbagliata: nessuno.
Task 5: minor (deferred): i backtick nei percorsi non sono neutralizzati nel brief.
Task 5: minor (deferred): ⚠️ dimensioni.md citato nel brief delle lenti arriva col Task 13 (da verificare lì).
Task 5: fix round 1 dispatched (resume implementer), base a11795c
Task 5: fix round 1 commit ff9de1b (1551 test); re-review dispatched (sonnet)
Task 5: fix round 1/5 (4 addressed, 0 open — giro del piano superseded con plan_adversary spento; titoli dei task in recinto; giro su altro SHA superseded anche nei rifiuti; ValueError di open_round come AuditError; commits a11795c..ff9de1b)
Task 5: complete (commits 3d00185..ff9de1b, review clean)
Task 6: dispatched (sonnet), base ff9de1b
Ruling: scenario di test_late_report_of_superseded_round_ignored compatibile con D14 — la spec si corregge e si committa prima dello start dell'agente 1, il giro 2 si apre dopo il suo start: nessun file cambia durante la sua vita e lo started precede l'apertura del giro 2 — costo se sbagliata: nessuno, è una costruzione di test.
Task 6: implementer DONE_WITH_CONCERNS, commits 2fb9bf8 e e095d4a (il secondo toglie il report aggiunto per errore con git add -f; 1585 test; .tollgate-run/ in info/exclude solo nel RoundCase dei test, non in FlowLab; report_round restituisce CompletedProcess; cut = messaggio troncato a metà della riga JSON); review dispatched (sonnet)
Task 6: minor (deferred): _write_atomic cattura solo OSError: con surrogati isolati nel messaggio resta un .tmp vuoto in reviews/<N>/ (il runner cattura il ValueError, nessun crash).
Task 6: minor (deferred): se il blob della spec non si legge, i rilievi meccanici del pitch spariscono in silenzio (audit_round._mechanical).
Task 6: minor (deferred): dopo «report non scritto» l'unico segnale è l'evento veto (D13); audit prepare ristampa il lancio del giro aperto.
Ruling: il minore di Task 6 su `.tollgate-run/` in info/exclude solo nel RoundCase dei test passa al Task 7: FlowLab lo scrive nel banco come fa `start` in produzione, e RoundCase non lo ripete — basso costo, evita impronte cambiate spurie nei test dei Task 7-9 e 15 — costo se sbagliata: nessuno.
Task 6: complete (commits ff9de1b..e095d4a, review clean)
Task 7: dispatched (sonnet), base e095d4a
Task 7: implementer DONE_WITH_CONCERNS, commit 57c79f0 (1624 test; RED non registrato; suspend_on_resolve con cfg opzionale; audit.passed/clean/last_round pubbliche; sospensione delle lenti al tetto con il numero dell'ultimo ciclo; approve spec senza numero scartato dall'hook); review dispatched (sonnet)
Task 7: review — Da correggere: 1 Important (duplicazione letterale: l2acts._on = audit._on, l2acts._committed ripete audit._committed, l2acts._cfg copia actapply._config, check_plan in approve_plan copia audit.py:326-331).
Ruling: nel giro di correzione 1 del Task 7 entrano anche i minori a basso costo: `_spec_approved` di approve plan passa a locate_spec_approval il blob attuale della spec in HEAD (decisione 13: per un'altra issue serve sha == blob); `_resolve` non costruisce la config da un worktree nullo; test_wrong_slice_count_refused asserisce il messaggio intero; test di approve plan e approve spec in `blocked` (decisione 27) e di approve spec con spec non committata — costo se sbagliata: nessuno.
Task 7: minor (deferred): resolve e approve nei test del Review Focus applicati dalla libreria (D20), il main() di act apply non esercitato lì.
Task 7: minor (deferred): non coperta la catena reale di un tetto del piano fino a approve plan.
Task 7: fix round 1 dispatched (resume implementer), base 57c79f0
Task 7: fix round 1 commit dfe3938 (1629 test; actapply._config con base o worktree assenti dà «configurazione non valida»); re-review dispatched (sonnet)
Task 7: fix round 1/5 (5 addressed, 0 open — helper condivisi in audit e config unica; approvazione della spec col blob attuale; resolve senza worktree; test più stretti e in blocked; commits 57c79f0..dfe3938)
Task 7: minor (deferred): con TOLLGATE_TEST_CONFIG impostato audit.work_config rifiuta comunque se manca la base (solo ambiente di test).
Task 7: minor (deferred): finalreview, openpr, taskcmd, finishcheck e sync ripetono ancora «base o ramo predefinito + load_config» (fuori ambito, preesistente).
Task 7: complete (commits e095d4a..dfe3938, review clean)
Task 8: dispatched (sonnet), base dfe3938
Task 8: implementer DONE, commit 543d29a (1638 test; subagents.in_use condivisa con sync; reset_plan prima di set_phase); review dispatched (sonnet)
Task 8: review — Da correggere: 1 Important (reopen plan in L1 indica audit prepare, che in L1 rifiuta; la frase su L1 compare anche in L2).
Ruling: nel giro di correzione 1 del Task 8 entrano due minori a basso costo: test che reopen lascia intatte le sospensioni (decisione 7); la config si carica solo quando serve, così una config non valida non blocca reopen senza subagenti in corso — costo se sbagliata: nessuno.
Task 8: minor (deferred): testi di rifiuto per task e implementatore duplicati tra sync.py e l2acts.py, a parte il suffisso.
Task 8: minor (deferred): nessun test dell'interruzione fra reset_plan e set_phase (il codice regge: reset_plan ritorna [] con plan_sha già nullo).
Task 8: fix round 1 dispatched (resume implementer), base 543d29a
Task 8: fix round 1 commit 58c524d (1640 test); re-review dispatched (sonnet)
Task 8: fix round 1/5 (3 addressed, 0 open — messaggio di reopen per livello; sospensioni intatte; config solo se serve; commits 543d29a..58c524d)
Task 8: complete (commits dfe3938..58c524d, review clean)
Task 9: dispatched (sonnet), base 58c524d
Task 9: implementer DONE_WITH_CONCERNS, commit 237ca9d (1665 test; test end-to-end scritto a codice fatto, provato con una mutazione; spec_audit senza spec_path = {adversarial: None, lens: None}; modulo nuovo l2tree.py per leggere l'albero di un commit, letture duplicate in audit.py e l2acts.py non toccate); review dispatched (sonnet)
Task 9: review — Da correggere: 1 Important (audit.py:327-328 e l2acts.py:187-188 ripetono alla lettera l2tree.spec_approvals(wt, "HEAD")).
Ruling: D4 precisata — senza spec_path `spec_reviews_dir` è null e `spec_audit` ha la forma di 18.1 con i due valori null ({"adversarial": null, "lens": null}, spec riga 1501), non null intero — fedele alla forma del blocco PR — costo se sbagliata: nessuno, il gate legge la stessa forma in L1 e L2.
Ruling: nel giro di correzione 1 del Task 9 entrano i minori a basso costo: finishcheck legge l'albero di HEAD una volta sola (o il commento si corregge), riga troppo lunga nella docstring di start.py, righe vuote in test_adopt.py — costo: nessuno.
Task 9: minor (deferred): nel test end-to-end close_tasks e fl.commit del banco sono scorciatoie dirette sul DB; la mutazione provata copre solo adopt.
Task 9: fix round 1 dispatched (resume implementer), base 237ca9d
Task 9: fix round 1 commit 461c4f3 (1665 test; doppia lettura in finishcheck tenuta, commento corretto); re-review dispatched (sonnet)
Task 9: fix round 1/5 (2 addressed, 0 open — letture dell'albero via l2tree; commento e formattazione; commits 237ca9d..461c4f3)
Task 9: minor (deferred): righe oltre 100 colonne (finishcheck.py:187 nuova; start.py:199,347,462 e audit.py:485 preesistenti).
Task 9: complete (commits 58c524d..461c4f3, review clean)
Task 10: dispatched (sonnet), base 461c4f3
Task 10: implementer DONE, commit 0f648ba (1670 test; in plan L2 senza spec registrata peek dà «/tollgate:reopen spec», il rifiuto di prepare); review dispatched (sonnet)
Task 10: minor (deferred): con NEEDS_CONFIRM peek dà il generico «lancia audit prepare» senza dire che serve la conferma.
Ruling: due minori di Task 10 passano ai task dei rinviati, dove stanno lavori della stessa forma: CheckpointL2Case dopo il blocco `if __name__ == "__main__"` in tests/test_checkpoint.py va nel Task 11 (riga 24, stessa correzione per test_verdicts e test_profiles); `audit.peek` che non cattura `UnicodeDecodeError` di git.text_at va nel Task 12 (flusso) con un test — costo: nessuno.
Task 10: complete (commits 461c4f3..0f648ba, review clean)
Task 11: dispatched (sonnet), base 0f648ba
Task 11: implementer DONE, commit 170a6d0 (1684 test; active_profile_names con head opzionale; classi spostate anche in test_bash.py; test di _review_report con ctx minimo); review dispatched (sonnet)
Task 11: minor (deferred): violations.py:97 riga di docstring da 116 caratteri.
Task 11: minor (deferred): nel test di _review_report `cfg=lambda` ricarica la configurazione a ogni chiamata.
Task 11: minor (deferred): il lancio diretto dei file di test (riga 24) richiede PYTHONPATH=bin:. (preesistente).
Ruling: il minore di Task 11 su `active_profile_names` con `git.head(wt)` nullo (changes(head=None) include worktree e non tracciati) passa al Task 12 con un `return []` e un test — basso costo, evita profili attivati da file non committati — costo se sbagliata: nessuno.
Task 11: complete (commits 0f648ba..170a6d0, review clean)
Task 12: dispatched (sonnet), base 170a6d0
Task 12: implementer DONE_WITH_CONCERNS, commit 6cc4f31 (1715 test; riga 71 instrada su tutti i rilievi confermati e bloccanti del ciclo, il DB non registra quali servirono; riga 72 formato «[major (originale blocker)]»; riga 55 ff-only fallito è un rifiuto con intento chiuso, non un blocco); review dispatched (sonnet)
Task 12: review — Da correggere: I-1 taskcmd._fix_files filtra confirmed AND blocking=1 senza gravità: entrano moderate/minor con regola di piano, non nel task (regressione d'instradamento); I-2 test_ff_only_failure_blocks asserisce un rifiuto, nome e docstring dicono blocco.
Ruling: I-1 si corregge con la gravità **dichiarata** blocker o major (riga 71: instradamento stabile, «senza filtrare per decisione dell'utente», quindi non la gravità effettiva dopo un declassamento) — costo se sbagliata: un rilievo declassato dall'utente continua a instradare, come vuole la riga 71.
Ruling: nel giro di correzione 1 del Task 12 entra il minore sui test NonUtf8Test che accettano qualunque esito: asseriscono l'esito preciso (con il ripiego Latin-1 di text_at, il valore che ne risulta) — costo: nessuno.
Task 12: minor (deferred): un rilievo archiviato prima della creazione del task entra comunque nell'instradamento, senza test (conforme alla riga 71).
Task 12: minor (deferred): dopo il rifiuto del caso superseded (riga 50) blocco e atto restano aperti, senza test.
Task 12: fix round 1 dispatched (resume implementer), base 6cc4f31
Task 12: fix round 1 commit a9306a2 (1716 test); re-review dispatched (sonnet)
Task 12: fix round 1/5 (3 addressed, 0 open — instradamento sui soli blocker/major dichiarati; test ff-only come rifiuto; esiti precisi non UTF-8; commits 6cc4f31..a9306a2)
Task 12: complete (commits 170a6d0..a9306a2, review clean)
Task 13: dispatched (sonnet), base a9306a2
Task 13: implementer DONE, commit f6b5fc4 (1725 test; plugin validate --strict OK; skill spec-audit scritta dal brief e dalle decisioni, senza leggere prd-audit/SKILL.md; test di sottostringa su finish/start restano dove non sono codici d'uscita); review dispatched (sonnet)
Task 13: review — Da correggere: I-1 metodo di prd-audit monco (L8 rimanda a verifica-fatti.md assente; L10 usa stati dell'evidenza definiti solo in prd-audit/SKILL.md; spec-auditor senza punto di vista in cima, regola «cerca la regola, non il caso», soglia del ciclo vuoto con minor); I-2 start/SKILL.md:42 in spec_audit manda sempre al brainstorming (non rientrante; contraddice --spec con spec cambiata).
Ruling: I-1 si corregge copiando anche `references/verifica-fatti.md` di prd-audit con la riga di attribuzione (spec 3: «versione di prd-audit incorporata, con l'accordo dell'autore») e portando in `spec-auditor.md` le definizioni che le lenti usano — costo se sbagliata: un file di riferimento in più nella skill.
Ruling: nel giro di correzione 1 del Task 13 entrano tutti i minori della revisione a basso costo (test D19 che verifica davvero `<id>` nel passo resolve; opzioni citate dalle skill controllate contro il parser; test che il percorso di dimensioni.md nel brief esiste; spec-audit con i messaggi su stderr del codice 1 e la fase approval; imprecisioni di start, reopen, finish; test del brief) — costo: nessuno.
Task 13: fix round 1 dispatched (resume implementer), base f6b5fc4
Task 13: fix round 1 commit 46c0dd0 (1731 test, plugin validate --strict OK); re-review dispatched (sonnet)
Task 13: fix round 1/5 (2 Important + minori addressed, 0 open — verifica-fatti.md copiato e spec-auditor completo; start rientrante in spec_audit; contratto più stretto; commits f6b5fc4..46c0dd0)
Task 13: minor (deferred): il test delle opzioni delle skill esclude `--force` (cleanup lo cita come comando git da non usare).
Task 13: minor (deferred): nessun test copre il testo della fase plan di start (fetta successiva e piano della sola fetta).
Task 13: complete (commits a9306a2..46c0dd0, review clean)
Task 14: dispatched (sonnet), base 46c0dd0
Task 14: implementer DONE_WITH_CONCERNS, commit 4142e88 (prova riuscita fino al task 1 done, passo 1 composito in due tentativi; 2 giri spec-adversarial (findings poi empty), approve spec 1, 2 giri plan-adversarial (minor poi empty), approve plan con plan_sha = blob approvato, verify green, revisore approved; 0 veti, 0 blocchi, 155743 token; nessun push; nessun difetto di P3c; 1731 test); review dispatched (sonnet)
Ruling: Task 14 passo 1 — in due esecuzioni su due il modello, seguendo la skill start (brainstorming → spec), ha scritto e committato una spec sua; lo script accetta una sola spec nuova e il passo 2 usa quella invece di fermarsi con «rifare il passo 1» — il controllo del piano voleva evitare che il «primo file nuovo» fosse una spec diversa da quella di prova, e con una sola spec il primo file nuovo è comunque univoco; è anche il comportamento atteso della skill — costo se sbagliata: il ramo che copia spec-L2.md resta non esercitato, e la spec esaminata è quella del modello (dichiarato nel rapporto).
Task 14: minor (deferred): i log del primo tentativo sono stati spostati in /tmp/tollgate-p3c-keep, fuori dalla cartella della prova prescritta (/tmp/tollgate-p3c).
Task 14: review — Da correggere: I-1 il rapporto dice «piano di prova non usato», mentre il modello l'ha copiato byte per byte (486c3ab) e poi corretto un minor; I-2 il passo 1 è girato con una versione precedente dello script (controllo «rifare il passo 1»), non dichiarato; I-3 il gh vero resta raggiungibile dal modello (Bash senza restrizioni, fakegh non nel PATH); I-4 l'esito dei passi non si propaga (tutto non si ferma).
Ruling: il giro di correzione del Task 14 non rifà la prova reale — I-1 e I-2 sono correzioni del rapporto, I-3 e I-4 irrobustiscono lo script (shim `gh` nel PATH che esegue fakegh, esito propagato) e si dichiarano nel rapporto come non esercitati da un `claude -p`; si verificano con `bash -n`, `prepara` e un controllo che `command -v gh` nel PATH del passo sia lo shim — un'altra prova reale costerebbe circa 160k token per un rischio che in questa esecuzione non si è presentato (tool_use verificati dal revisore) — costo se sbagliata: lo script corretto non è provato con il modello fino alla prossima prova reale (P4).
Ruling: nel giro entrano i minori a basso costo: `--add-dir` ristretto a una cartella `input/` con i soli file di prova; `worktree_lavoro` robusto agli spazi; `verifica_push` anche dopo ogni passo — costo: nessuno.
Task 14: fix round 1 dispatched (resume implementer), base 4142e88
Task 14: fix round 1 commit 214913e (1731 test; shim gh, esito propagato, input ristretto, rapporto corretto; prova di riferimento conservata in /tmp/tollgate-p3c/prova-1/flow).
Task 14: incidente — nel giro di correzione l'implementatore ha lanciato per errore `tutto` invece del solo controllo: un claude -p è partito (passi 1-3 e parte del 4) contro l'indicazione del controller ma dentro le cautele del Task 14 (solo /tmp/tollgate-p3c/flow, shim gh, --plugin-dir, --model sonnet, nessun push: origin.git ha solo main; processi fermati per PID, nessun processo residuo verificato dal controller). Dichiarato nel rapporto, log in /tmp/tollgate-p3c/prova-accidentale, non usati come evidenza. Da riferire all'utente.
Task 14: re-review dispatched (sonnet)
Task 14: fix round 1/5 (4 Important + 3 minori addressed, 0 open — rapporto corretto su piano copiato e passo 1; shim gh; esito propagato; input ristretto, spazi, push dopo il passo; commits 4142e88..214913e)
Task 14: minor (deferred): rapporto della prova: backtick rotti alla riga 5; righe 11, 14, 21 citano /tmp/tollgate-p3c/flow come se fosse la prova (ora è prova-1/flow); doppia parentesi nel non esercitato.
Task 14: minor (deferred): verifica_gh controlla il PATH dello script, non quello della shell del tool Bash di claude: da verificare alla prossima prova reale.
Task 14: complete (commits 46c0dd0..214913e, review clean)
Task 15: dispatched (sonnet), base 214913e
Task 15: implementer DONE, commit 4b4871a (1736 test su due interpreti, -W error::ResourceWarning verde; 5 test dei criteri dal programma vero, passati subito; atti dalla CLI con l'ora reale; spec rev 24 con decisioni 1-27 e ruling D2-D19, 6.2 riscritta; matrice con 44 riferimenti verificati); review dispatched (sonnet)
Task 15: review — Da correggere: I-1 sezione 16 della spec inesatta (frontmatter dei tre agenti letto, ma spec-auditor non esercitato; mancano l'esecuzione accidentale e il passo 1 girato con lo script precedente); I-2 decisioni 17 e 25 (e il ruling sull'instradamento del task di correzione) dichiarate nella riga 24 di sez. 20 ma assenti dal corpo (7.5, 6.3); I-3 tre asserzioni `startswith("prossimo passo: ")` in test_criteria_p3c.py che non controllano «approve spec».
Ruling: nel giro di correzione 1 del Task 15 entrano i minori a basso costo della revisione (6.2 passo 4 con spec_audit spento; riferimento «D15» ambiguo nel piano; colonne «Resta a» vecchie di P2 e P3b se toccate da P3c; banco creato due volte) — costo: nessuno.
Task 15: fix round 1 dispatched (resume implementer), base 4b4871a
Task 15: fix round 1 commit d71f48d (1736 test); re-review dispatched (sonnet)
Task 15: fix round 1/5 (3 Important + minori addressed, 0 open — sezione 16 e Stato; decisioni 17 e 25 nel corpo; asserzioni dei passi; banco unico; commits 4b4871a..d71f48d)
Task 15: minor (deferred): tabella P3a del piano principale (riga ~225) ha ancora «(P3c)» in «Resta a».
Task 15: minor (deferred): riferimenti «riga 49/71» e D2-D19 nella spec si risolvono solo nel registro (da portare in docs/sdd/ dopo il merge).
Task 15: complete (commits 214913e..d71f48d, review clean)
Final review: dispatched (opus), range 8ea0f39..d71f48d
Final review: 0 Critical, 1 Important (I-1 audit prepare in plan cerca l'approvazione della spec con spec_blob=None: con due approvazioni della stessa spec vince la più vecchia, superata, e rifiuta a torto «spec cambiata»; approve plan invece accetta), 6 Minor; triage dei 41 minori: 3 da correggere prima del merge (18 .tmp in reviews/<N>/ non rimovibile, 38 rapporto della prova, 40 «(P3c)» nel piano principale), 22 rinviabili, 16 chiusi; nessuna ruling sbagliata; verdetto: sì con correzioni.
Ruling: un solo giro di correzione finale con I-1, le righe 18, 38, 40 del triage e i Minor a basso costo m-1 (rimandi incrociati in approval senza /tollgate:reopen plan), m-5 (messaggi senza program_command: vincolo globale), m-6 (testo del passo resolve); m-2 (report sovrascritti dopo un DB perso), m-3 (adopt dopo reopen con documento identico) e m-4 (spec_path e plan_path registrati una volta) vanno a P4 con il resto dei rinviabili — costo se sbagliata: tre casi di ripresa dopo DB perso o rinomina restano da gestire in P4.
Final fix: dispatched (sonnet), base d71f48d
Final fix: commit 3aa47c2 (1753 test su due interpreti, ResourceWarning verde); re-review dispatched (sonnet)
Final fix: re-review — tutti i rilievi indirizzati (I-1, righe 18, 38, 40, m-1, m-5, m-6), nessun danno nuovo Critical/Important; 175 test mirati OK.
Final review: parked — con la propria approvazione della spec superata e quella di un'altra issue corrente, l2tree.spec_approval risponde «superata» (la propria ha la precedenza) e audit prepare/approve plan indicano /tollgate:reopen spec — Ruling: il codice resta, è coerente tra i comandi e con la decisione 13 (la propria vince, qualunque sha), e ha un'uscita reale (reopen spec); il caso va deciso in P4 — costo se sbagliata: una fetta che ha cambiato la propria spec dopo un'approvazione altrui deve rifare approve spec.
Final review: parked — in `approval` con plan_adversary spento, audit prepare dice di chiedere approve plan anche con la spec cambiata, mentre approve plan rifiuta indicando /tollgate:reopen spec — Ruling: preesistente e non toccato dal giro; l'utente ha comunque l'uscita dal rifiuto di approve plan; a P4 insieme a m-1 per il caso componente spento — costo se sbagliata: un passo in più (prepare → approve plan → reopen spec).
Final review: closed (0 Critical, 0 Important aperti; minori m-2, m-3, m-4 e 22 righe del triage rinviati a P4/P5 come da final-review.md)
Suite finale: tre corse in corso su 3aa47c2 (tests/run + -W error::ResourceWarning)
Suite finale: tre corse verdi su 3aa47c2 — tests/run 1753 test con python3.11 e python3, e python3 -B -W error::ResourceWarning 1753 test OK, ogni volta; nessun «unclosed database». In attesa dell'OK dell'utente per il merge.
