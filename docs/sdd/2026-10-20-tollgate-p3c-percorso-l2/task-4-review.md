# Revisione Task 4 (0ae2d16)

### Aderenza
- ✅ Migrazione 5 (`db.py:157-169`): colonne e CHECK come decisione 1; su DB v4 con riga `spec_audit` esistente i dati restano e la riga diventa `stage='closed'` (`test_db.py` MigrationV5Test, copia `*migrazione-5*`). Rischio 3 chiuso. ADD COLUMN con NOT NULL DEFAULT e CHECK è ammesso da SQLite.
- ✅ `plan_reset` in `events.py:20`; tre cause L2 in `phases.py:23-27`; `set_spec_path` solo se nullo; `create_work` con `from_approved_spec` senza `spec_path` solleva `ValueError` (nessun chiamante di produzione in `bin/`).
- ✅ `audits.py`: D16 (`last_closed(kinds)`, mai `superseded`), D17 (`suspended` con 0 e docstring con `in`), D19 (`cap_reason`/`cap_kind` con test di inversione), `any_rows`, numeri per tipo e per lavoro senza riuso dopo `superseded`.
- ✅ `git.ls_files_at` (D11, `-z`, split su NUL, `[]` se manca il ref) e `git.blob_at` (D15) con test (spazi, accenti, ref assente).
- ✅ D7/decisione 26: `locked_docs` una volta per `diff_violations` (`violations.py:~133`); esenzione di `reviews/<issue>/`. Rischio 1: i chiamanti `writes.py:82` e `_common.py:237-238` non passano `locked` (parametro keyword opzionale, default invariato): corretti. `reviews/8/` resta fuori scope (testato).
- ✅ D10/D18e: `EXPECTED["L2"]`, `CAUSES`, `latest_version()`.
- ✅ Rischio 2 (`reset_plan`, `scope.py:19-37`): `subagents.task` è l'unica colonna con numero di task (nessuna FK; `receipts`, `findings`, `review_cycles` non lo portano). I lettori (`taskcmd._concerns:235`, `subagent_stop:82`, `_common.py:99`, `skills.py:15`) cercano per `(work, task)`: con `task=NULL` un report vecchio non si aggancia ai task rinumerati e un agente ripreso non trova task. Scelta coerente con la decisione 12 («task già soddisfatto»). Il no-op senza `plan_sha` è sensato (i task nascono solo da `register_plan`).
- ⚠️ Non verificabile qui: il chiamante di `reset_plan` (Task su `reopen`) deve rifiutare con task `running`/`review` (la funzione non lo controlla).
- Test mirati rilanciati (`python3 -B`, db/audits/scope/git/violations): 85 OK. Suite non rilanciata, evidenza del report plausibile.

### Punti di forza
Ogni funzione apre la sua transazione; `suspend` annida correttamente; `supersede` non tocca un giro chiuso; numerazione `max+1` che non riusa i report; test che asseriscono comportamento reale (evento `plan_reset`, riga storica del subagente).

### Rilievi
**Critical:** nessuno.

**Important**
1. `bin/tollgate_flow/finishcheck.py:189-190`: il ramo `v.path.startswith(f"{REVIEWS_DIR}/{issue}/")` di `_own_document` duplica la nuova esenzione di `violations.scope_exempt` (`violations.py:~72-75`) ed è ora codice morto (la violazione `out_of_scope` per quei file non nasce più). La decisione 26 dice «ora nel calcolo condiviso»: va tolto il ramo da `_own_document` (aggiornandone il docstring), lasciando solo la spec approvata. In più `violations.py` scrive il letterale `"docs/superpowers/reviews/"` invece di `approvals.REVIEWS_DIR`.

**Minor**
2. `git.py` `blob_at`: su una cartella dà lo SHA dell'albero (verificato: `HEAD:d` rc=0). Usare `f"{ref}:{path}^{{blob}}"` (rc=1 per un albero) per mantenere il contratto «blob o `None`».
3. `audits.py:close_round`: `outcome` e `counts` non sono validati (un `outcome='superseded'` passerebbe da qui e sparirebbe da `rounds`); `supersede` ha `now` inutilizzato.
4. `tests/test_db.py`: `test_latest_version_is_5` sta in `MigrationV4Test` (spostabile in V5).
5. `git.ls_files_at`: `ref` che inizia con `-` non è protetto (stesso stile di `exists_at`, solo se il chiamante passa testo non fidato).

### Valutazione
**Qualità del task:** Da correggere (lievemente).
**Motivo:** requisiti e carry D7/D10/D11/D15/D16/D17/D19 soddisfatti, rischi 1-3 chiusi; resta una duplicazione letterale dell'esenzione in `finishcheck._own_document` (Important, correzione di tre righe) e rifiniture minori.
