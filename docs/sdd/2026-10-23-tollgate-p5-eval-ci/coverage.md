## Copertura: criteri, vincoli e rinviati → task

| Voce | Task |
|---|---|
| Casi di eval 1-9 della spec 14, 3 corse per caso (matrice: «Casi di eval (spec 14, 1-9): P5») | 7, 8, 9, 11, 14, 15 |
| CI del repo di tollgate (spec 14, riga «CI»; riga P5 della sezione 2: «CI verde») | 1 (VC1), 2, 3, 14 |
| Documentazione d'uso; spec 1 nella matrice («i limiti di 1.2 diventano testo di `status` e della documentazione»); spec 17 | 12 |
| Rischio «Costo degli eval in P5» | decisione 8; 1, 11, 14 |
| Vincolo P4 (1): azioni a `@v4`, fissaggio per SHA | 1 (VC2, VG2), 3, 13 |
| Vincolo P4 (2): eval su ciò che le prove reali non hanno esercitato | 10 (e1 audit a lenti, e2 `reopen`, e3 `start --spec`, e4 più task, `/tollgate:finish` e PR in L2, e5 rientro con `--from-gate`); tetti, più fette oltre la seconda, unione della PR e gate: **ai test dal programma vero**, motivo nella decisione 6 |
| Vincolo P4 (3): limiti di 1.2 della rev 25 come documentazione d'uso | 12 |
| Vincolo P4 (4): rinviati di P3c con motivo (righe 11, 12, 20, 13, 15, 24-28, 36, «base o predefinito più `load_config`») | riga 12 → Task 6 (decisione 18: `close_round` valida `outcome` e `counts`); 11, 20, 13, 15, 24-28, 36 e la duplicazione: **dopo la v1** (11: serve solo con una versione 2 della riga; 20: il giro resta aperto e `audit prepare` lo ristampa; gli altri: posizione dei test, refactoring, stile e testo senza guasti) |
| Vincolo P4 (5): CI con spazi nel percorso | 2 (decisioni 10, 11) |
| Vincolo P4 (6): cache in sola lettura dei job `workflow_run` sul privato | 1 (VG1), 13 |
| P4 M-1, M-5 | 4 |
| P4 M-3, M-4 | 5, 13 |
| P4 M-9 (test di accordo dagli ingressi veri) | 4 |
| Residui della ri-revisione di P4: testo di `tollgate/base` con `base_test_ids` spento; righe lunghe di `fakegh.py` | 5 |
| Minori di P4, gruppo «Codice»: `{statuses:write}` e valori spazzatura; `closes_issue` con citazioni e commenti HTML; `_one_line` e Markdown; `waivers._ID` con `\n`; `exit=None`; `evaluate()` e `runner.py` che catturano poco; `with_mode` con apici singoli; `base_path` con segmento maiuscolo | 4 |
| Minori di P4, gruppo «Codice»: `api(paginate=True)` con valori non oggetto; `TOLLGATE_GH_RETRY_DELAYS` malformato; guard verde che non aggiorna il commento rosso; PR verso un altro ramo con `GhError`; `publish_from` con `ConfigError`/`GitError` | 5 |
| Minori di P4, gruppo «Codice», **dopo la v1**: `_run_checked` duplica `ghcli._failed`; doppio calcolo del blob; diff del piano superato ricalcolato a mano; voci `notes` non in locale; tagli di emergenza del commento senza test; `read_results` senza `sha`/`config_sha`; motivo di un'eccezione nella descrizione (una riga, troncato); attese di `sentinel`; descrizione troncata di `tollgate/base`; M-4 `extraheader` in shell (nessun testo non fidato: `gate cache-key` non serve finché resta così); M-9 cache del job `base` avvelenabile (limite di 1.2, modalità rinforzata con GitHub App dopo la v1); `environ` inutilizzato, `warnings` come secondo canale, dettaglio `approvals` con righe di diff, una chiamata `gh` a ogni `finish check`; `_next_report_number` vede solo i committati | motivo: duplicazione, prestazioni o testo senza un verdetto sbagliato |
| Minori di P4, gruppo «Test»: tre test con spazi nel percorso; `BackupRaceTest` instabile; `test_findings_carry_blocking_field`; il `gh` finto che non pagina; `edited` che cambia la base | 2, 4, 5 |
| Minori di P4, gruppo «Test», **dopo la v1**: `test_same_result_as_diff_violations` (sostituito nei fatti da M-9, Task 4); `CoverageTest` rilanciato; `test_gate_evaluate.py` oltre le 1000 righe; nome di `test_deleted_and_moved_tollgate_files_count`; test di M-3 che scrive i nomi dei job; sottostringhe nei test delle skill; RED ricostruito a posteriori; rientro di `test_token_only_in_env`; caso (b) del Task 14 di P4, riga lunga e `assertRaises` senza messaggio | motivo: qualità dei test senza un guasto coperto male |
| Minori di P4, gruppo «Script della prova»: `ghguard.py` (regex con `$`, `isdigit` Unicode, PATCH valida per qualsiasi PR); `TOLLGATE_GH_RETRY_DELAYS` malformato (M4-3); V4 da rileggere sul privato; la guardia del Task 1 di P4 solo in lettura | 1 (`ghguard.py`, profilo `p5`), 5 (M4-3), 1 e 13 (V4 sul privato: VG1) |
| Minori di P4, gruppo «Script della prova»: `wait_run` con ripiego, `merge_pr` ripetuto, percorsi assoluti in `v8-find.txt`, PR del commit originale del rebase in V5, `ghguard.py log` che non legge `comandi.log`, `__pycache__` nella storia del ramo di P4 | **nessuna azione**: script e storia della prova di P4, superati; le lezioni (ritentativi, merge non ripetuto, evidenze senza percorsi assoluti) entrano nella decisione 22 |
| P1: traceback senza `git`; `input()` senza EOF/Ctrl-C; test CLI del ramo interattivo di `db restore` | 6 |
| P1: `mkdtemp` non ripuliti nei test | **dopo la v1**: 44 punti, nessun guasto (cartelle temporanee sui runner usa e getta) |
| P3a riga 163: `task_change` di `assign` senza `implementer` e `pending` | 6 |
| P3b righe 10, 11, 13, 27, 44, 54, 74, 76 | 6 |
| P3b righe 15, 17, 20, 26, 52, 56, 61, 70, 75 | **dopo la v1**: posizione dei test e processo (15, 17, 20), duplicazioni senza guasto (26, 52, 61, 70, 75), finestra stretta con un blocco in più come esito (56) |
| P3b righe 28, 66 | chiuse: in `finishcheck.py` `git.changes` si calcola una volta sola e la regex `_TG` duplicata non esiste più (verifica del Task 6, nel report) |
| Esiti nuovi del Task 1 (VE1-VE11, VC1-VC2, VG1-VG2) | 1; conseguenze con `Ruling:` prima del Task 7 (decisione 9) |
| Revisione 26 della spec; piano principale; chiusura del nucleo e «Dopo la v1» | 15 |
| Revisione del piano (C1, C2, I1-I10, minori) | decisioni 2, 3, 9, 10, 14, 15, 16, 17, 19, 20, 22, 23; Task 1, 3, 4, 5, 6, 7, 11, 12, 13, 15 |
| Review Focus 1-7 | 7, 8-10, 5, 5, 3, 7 e 11, 12 |
