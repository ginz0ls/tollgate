# Revisione Task 4 (7d121f5): taglia grande con `approve spec` e atto `approve size`

### Aderenza
- ✅ `approve_spec` (`bin/tollgate_flow/l2acts.py:174-182`): `UPDATE slices` e `sizes.decide` in un solo `db.tx`, prima di `phases.set_phase` (D10); `cause="approve_spec"`, `confirmed=slices > 1`; segnali `Signals(level, n_task, 0, slices)`.
- ✅ Riga della taglia in uscita prima di «Committa» (`l2acts.py:187`) e dopo il recinto dei titoli (non dentro); l'uscita resta fase `plan` + proposta issue (test `test_approve_spec_records_slices_and_large`).
- ✅ `approve spec 1`: `slices = 1`, resta `medium`, `confirmed` nullo (`tests/test_l2acts.py` single_slice).
- ✅ Lavoro pre-C1 (`size` nullo): nessun errore, una chiamata di `decide` con `previous` None (test dedicato).
- ✅ `approve size`: `_approve_size` (`actapply.py:241-250`) con `LABELS` invertito, valore sconosciuto rifiutato con i tre ammessi, motivo obbligatorio, `set_by_user` (`size_by='user'`, anche verso il basso: `test_approve_size_can_lower`); l'atto si consuma sempre (asserito nei test di rifiuto e di successo). Nessun errore inghiottito: `ValueError` di `set_by_user` non raggiungibile grazie al controllo sul dizionario.
- ✅ `"size"` in `APPROVE_OBJECTS` (`core/acts.py:13`) e `_TARGET_ARG` (`checks/acts.py:12`); `APPLIERS` e messaggio di `_pick` aggiornati. Controllati gli altri punti che enumerano gli oggetti (`git grep`): non ce ne sono altri.
- ✅ `approve size grande` non autorizza le fette: `set_by_user` non tocca `slices` né produce proposta di issue; skill e pagina lo dicono («Non autorizza le fette»). ⚠️ Nessun test lo asserisce (vedi Minor).
- ✅ D17: skill `approve` (solo `description`, `argument-hint`, elenco e riga di `size`; un esempio) e `docs/uso/comandi.md` cambiano insieme, `argument-hint` identico alla riga «Argomenti». Nessun nome nudo del programma aggiunto (si usa `<programma>` e `/tollgate:...`). Profili e regole approvati intatti (stat: nessun file di `skills/rules-*`, `docs/profili`, `templates/profiles`).
- ✅ Due test esistenti di `approve plan`: il primo filtra per causa `plan` e asserisce ancora esattamente un evento di quella causa (stessi controlli su `applied`, `signals.level`, `size`, riga). Il secondo prima asseriva `len == 1` e poi `["plan"]`; ora asserisce la lista completa `["approve_spec", "plan"]` prima e dopo il retry: uguale o più forte (prova ancora che il retry non duplica la decisione del piano). Nessun indebolimento.
- ⚠️ Suite (4245 test su due interpreti, `suite-task-4.log`): affermazione del report, non rilanciata.

### Punti di forza
- Applicazione di D10 corretta e motivata (backup dopo il commit); modello `_approve_level` seguito; nessuna duplicazione (la riga viene da `sizes.decide`/`preview`).
- Test sul comportamento reale: ordine della riga rispetto a «Committa», evento con `cause`/`confirmed`/`previous`, stato dell'atto.
- Modifica chirurgica, 9 file, niente file nuovi.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `l2acts.py:174-182`: se `set_phase` fallisce dopo il `db.tx` (interruzione), il ritentativo di `approve spec` registra un secondo `size_decided` (`approve_spec`, confirmed). `approve_plan` ha invece la guardia «decisa una volta» e il test relativo. Effetto: un evento duplicato (dato per il confronto regole/modello), nessuna taglia errata. Se si vuole la stessa garanzia: saltare `decide` quando `work["slices"] == slices` e l'ultimo evento di taglia ha già causa `approve_spec`, oppure accettarlo e dirlo. Non bloccante.
2. `tests/test_check_acts.py` (riga della lista di `test_refused_forms_are_not_recorded`): supera i 100 caratteri (`("tollgate:approve", "spec"), ("tollgate:approve", "size"), ("tollgate:approve", "waiver"),` su una riga); andare a capo come le altre.
3. Manca un test che `approve size grande` su un lavoro senza fette lasci `slices` invariato e non emetta proposta di issue (vincolo del progetto, oggi coperto solo dal codice).
4. `approve spec N` con taglia già `user` piccola: il sì porta a `large` ma `size_by` resta `rules` (decisione del Task 3, `sizes.decide`); non è del Task 4, segnalato solo perché il test lo fissa (`("large", "rules")`). Da confrontare con la spec in revisione finale.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** tutti i requisiti del brief, D10 e D17 sono rispettati e verificati sul diff; i test esistenti adattati non perdono forza. Restano solo rifiniture Minor (evento duplicato al ritentativo, riga lunga, un test mancante).
