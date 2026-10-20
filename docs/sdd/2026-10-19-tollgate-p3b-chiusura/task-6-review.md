# Revisione Task 6: `finish check` (949d1d3..ec1caa3)

### Aderenza
- ✅ Interfacce del brief: `MustHaveResult`/`check` (mustcheck.py:12-38), `parse_approval`/`approval_paths` (approvals.py:15-50), `CheckResult`, `OK/RED/REFUSED`, `check(state, cwd, *, now, environ)` (finishcheck.py:20-60).
- ✅ Decisione 4: fase `execution`/`review`, `review` stesso SHA = esito salvato senza gate né eventi (finishcheck.py:80-81, 176-186; criterio 28), fetch con avviso (86-89), rifiuto task non `done`/`approved` con i numeri (91-97; criterio 41), `run_gate(produced_by="finish", extra=dod_commands)`, `diff_violations` da `work_base_sha`, must-have dal JUnit del gate, `approvals` solo in L2.
- ✅ Configurazione dalla base (`config.load_config(state, wt, base)`, 99-101), piano letto a `plan_sha` via `_plan_text`, approvazioni lette da HEAD: mai dal working tree.
- ✅ C13 (review altro SHA: solo `set_finish` + evento, 150-155), C14 (`external` dizionario con le sole chiavi del livello), C17 (`run.sha is None` -> REFUSED, 112-113), C6 (`finish_report = {"items", "manual"}` con tutte le voci, comprese `guard_scope`/`must_have`/`approvals` e voci di profilo), C24 (`except` finale, cli.py), evento `finish_check` {sha, ok} sia verde sia rosso, criterio 31 (rosso: nessun `set_phase`).
- ✅ `dod` di profilo senza comando: ricevuta `unverified`, riga con nome del comando e «[commands]» (131-134), verde con `unverified-tests`.
- ✅ `compute_dod` riceve `required_commands` (gate + dod), `profile_items`, `allow_unverified`, `skip=("findings","specialists")`; il verde esclude le voci saltate.
- ✅ Comandi per il modello via `program_command(db.BIN_PATH)` (riga «prossimo passo», 47-52). Strati rispettati (finishcheck importa solo core/analysis/flow; mustcheck/approvals solo analysis). `set_phase` fuori da transazione.
- ✅ Ruling «scope di finish check in L2»: `_own_document` (194-211) esenta solo `out_of_scope`; reviews/<N>/ sempre; la spec solo se blob in HEAD == `sha` di `spec-approval.md`; il piano non è più esente (resta `is_registered_plan` in `diff_violations`). Coperto da tre test (test_finishcheck.py `test_l2_*`).
- ⚠️ Con L2 e senza `spec-approval.md` la spec non risulta `out_of_scope` (la esenta `scope_exempt` di Task 4), contrariamente al costo descritto nel Ruling; il finish resta comunque rosso per `approvals`. L'implementatore lo dichiara; non è un difetto del task, ma P4/P3c devono saperlo. Non verificato con esecuzione.
- ⚠️ Non verificato: `prstate.detect` (Task 9, previsto).

### Punti di forza
- Percorso idempotente pulito e testato (stesso SHA, altro SHA verde, altro SHA rosso, con asserzioni su ricevute, eventi `phase_change`/`finish_check`).
- `finish_report` e `_saved` ricostruiscono le voci dallo stesso contratto; `set_finish` prima di `set_phase`, quindi un'interruzione tra i due passi si recupera rilanciando.
- Test per i casi limite: worktree sporco, fase sbagliata, nessun lavoro, fetch KO, must-have manuale, L0 senza task, errori esterni con `subTest`, errore sconosciuto che si propaga.
- Fix round mirato, con RED dichiarato prima della correzione.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. finishcheck.py:91-95: il predicato «task non `done`/`approved`» duplica `dod._tasks` (dod.py:66-72). Una sola riga, ma due punti di verità; estrarre un helper pubblico in `dod` (es. `open_task_numbers(conn, work)`) e usarlo in entrambi.
2. finishcheck.py:176-179: `json.loads(work["finish_report"])` non protetto; un report corrotto darebbe un traceback invece di ricalcolare. Rendere `_saved` tollerante (se non decodifica, ricalcola).
3. finishcheck.py:119 e 107-110: `git.changes(wt, base, head=sha)` calcolato due volte; riusare la lista.
4. finishcheck.py:150-155: se `set_phase` solleva `TransitionError` dopo `set_finish`, il `check` esterno risponde REFUSED senza evento `finish_check` e con `finish_sha` già scritto. Improbabile; documentare o registrare l'evento prima.
5. approvals.py:_value: un valore tra virgolette seguito da commento (`"abc" # c`) conserva le virgolette; un `sha` nudo di sole cifre (<=6) diventa `int`. Irrilevante per sha da 40 caratteri, ma fragile. Test mancanti per kind sbagliato in `_approvals` e per `must_have_tests` spento (ramo di `_must_have`, riga ~215).
6. finishcheck.py:194-211: la docstring dice «in un lavoro L2», ma l'esenzione di reviews/<N>/ vale a ogni livello (voluto dal Ruling, serve anche al checkpoint in L1); allineare il testo.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti del brief, carry (C6, C13, C14, C17, C24) e Ruling sullo scope L2 sono implementati e coperti da test sul comportamento reale, strati e vincoli rispettati. Restano solo rifiniture Minor.
