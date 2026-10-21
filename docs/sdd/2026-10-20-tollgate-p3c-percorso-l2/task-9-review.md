# Revisione Task 9 (58c524d..237ca9d)

### Aderenza
- ✅ `start --spec` (decisione 14, 5, 6.1, criterio 24): percorso convalidato (relativo, normalizzato, sotto `docs/superpowers/specs/`, senza `..` né caratteri di controllo), letto alla punta del predefinito = `base_sha` (`start.py:_slice`, mai il disco: `test_approval_only_on_the_local_disk_is_not_enough`); sha attuale -> L2, `from_approved_spec`, fase `plan`; sha vecchio -> uscita 3 e con `--confirm` `spec_audit`; senza approvazione rifiuto; in ripresa avviso. CLI passa `spec` (`cli.py`, `test_cli_passes_spec`).
- ✅ `finish check`: `_approvals` usa `approvals.check_l2` sui file di HEAD (`finishcheck.py:_approvals`), legge solo approvazioni delle spec, `plan-approval.md` e report delle due cartelle (`l2tree.collect`). `_own_document` esenta la spec con l'approvazione trovata (anche di altra issue), docstring ripulita (D18a). D3 rispettata (HEAD, mai disco).
- ✅ `openpr.facts` (D4, decisione 15): cartelle e `spec_audit` da `locate` a `head`, solo con `spec_path`; `plan_reviews_dir` se esiste `plan-approval.md`. `test_counters_and_reviews_dirs` riscritto con `spec_path`.
- ✅ `adopt` (decisione 16): `_approved_elsewhere`/`_l2_proofs` riusano `_approval`, che verifica che la spec sia ancora con lo sha (quindi «spec ancora con quel blob» è rispettato anche per la fetta successiva); fase `plan` con `plan_adversary` acceso, `approval` spento. Riscritti `test_adopt` (D8/D10) e `l2_lab`/`approve` di `test_finishcheck` con `spec_sha` e report.
- ✅ Review Focus 5: `test_later_slice_end_to_end` attraversa davvero `hooks/run` (`hook()`, `event()`) e `bin/tollgate` (`cli()`, `start`, `audit prepare`, `act apply`, `finish check`, `open-pr`, `adopt`), con Edit sulla spec negato prima e dopo `adopt`, `spec_reviews_dir` dell'issue 3, `adopt` -> `execution`. Il test è scritto dopo il codice, ma la mutazione dichiarata (`_approved_elsewhere` -> None) lo fa fallire; per le altre asserzioni (approvals, dirs, spec_audit) l'oggetto non è vacuo perché verificano valori specifici.
- ⚠️ `adopt 9` dà `execution` solo con la PR CLOSED: coerente con 12.4 (PR aperta -> `pr_open`), non è un difetto. Non rilanciati i test: affido all'evidenza del report (1665 OK su due interpreti).

### Valutazione delle scelte segnalate dall'implementatore
1. `spec_audit` senza `spec_path` = `{"adversarial": None, "lens": None}`: corretto. La spec 18.1 (riga 1501) mostra proprio quel dict con valori `null`; D4 («altrimenti null») va letta sui valori. Accettato, ma il controller dovrebbe chiarire D4 nel carry (Minor).
2. `adopt` con PR CLOSED nel test: accettato (sopra).
3. Duplicazione con `l2tree.py`: confermata, vedi Important.
4. Test end-to-end dopo il codice: accettato per la mutazione e per le asserzioni su valori (Minor: la mutazione copre solo `adopt`; `close_tasks` e `fl.commit` del banco sono scorciatoie dirette, non attraversano la CLI, ma i task non sono l'oggetto del test).

### Punti di forza
- `l2tree` ha una sola responsabilità e una sola lettura dell'albero per commit; niente disco; l'helper puro `approvals.report_listing` è testato.
- Test di `start --spec` ampi: percorso malevolo con a capo, `./`, `..`, assoluto, ramo non creato dopo il rifiuto.
- Riscritture dei test esistenti senza indebolirli (stesse asserzioni su `guard_scope`, più `approvals` falsa).

### Rilievi
**Important**
- `bin/tollgate_flow/audit.py:327-328` e `bin/tollgate_flow/l2acts.py:187-188`: duplicazione letterale di `l2tree.spec_approvals(wt, "HEAD")` (`ls_files_at(..., REVIEWS_DIR + "/")` + `text_at` sui soli `approval_listing`). Il Task 9 introduce il modulo che la centralizza e lascia due copie identiche (il brief chiedeva di usare gli helper esistenti; la giustificazione «minimo impatto» non vale per un modulo nuovo scritto per questo). Rischio concreto: un cambio futuro (per esempio l'elenco dei file) diverge tra i tre punti. Correzione: sostituire le due coppie di righe con `files = l2tree.spec_approvals(wt, "HEAD")` (stesso strato, nessun ciclo: `l2tree` importa solo analysis e core).

**Minor**
- `finishcheck.py:_check` + `_approvals`: l'albero di HEAD è letto due volte (`_approved_spec_blob` -> `l2tree.locate`, poi `l2tree.collect`) e `git.blob_at` della spec due volte. Calcolare una volta con `collect` (che già restituisce `found`) e passarla a `_own_document`; il commento «una sola lettura dell'albero» in `_approved_spec_blob` è inesatto.
- `start.py:4-6`: docstring con riga oltre 100 colonne; `tests/test_adopt.py` ha tre righe vuote prima di `AdoptL2Test`.
- D4 ambigua su `spec_audit` (vedi sopra): annotarla nel carry.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** requisiti e carry D3, D4, D8/D10, D18a/b rispettati e il test end-to-end è reale; resta una duplicazione letterale della lettura dell'albero (audit.py, l2acts.py) che lo stesso task ha il compito di eliminare con `l2tree.py`.
