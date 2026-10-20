# Revisione Task 3 (4ef3f0a..5fd29f7)

## Aderenza
- ✅ Migrazione 4 (`bin/tollgate_core/db.py`, SCHEMA_V4): tutte le colonne della decisione 1, solo in avanti. Copia `*migrazione-4*` e DB nuovo senza copia testati (`tests/test_db.py::MigrationV4Test`). C3 (`str(db.latest_version())`) fatto.
- ✅ Costanti e firme del brief verificate alla lettera: `SEVERITY_ORDER`, `CAP_COUNTED = 4`, `MAX_CYCLES = 8`, `CAP_REASON`, `SYNC_CONFLICT_REASON`, `open_cycle`, `add_report`, `to_verify`, `apply_verification`, `close_cycle`, `set_decision`, `compute_dod`, `receipt_verdict`, `patch_id`, `off_periods`, intents, `phases.*`, `acts.*`.
- ✅ Decisione 6 (`reviews.py:241-279`): `needs_you` dichiarato -> blocco; confermato bloccante `blocker`/`major` (gravità effettiva) -> `needs_fix` e fase `execution` (causa `needs_fix`); tetto `counted >= 4 + extra_review_cycles` solo con `needs_fix`; `set_phase` e `open_block` chiamati fuori da transazione (`close_cycle` rifiuta se `conn.in_transaction`; le scritture del ciclo stanno in `db.tx` chiusa prima dei passaggi di fase).
- ✅ Decisione 15: `dod._findings` -> `reviews.blocking_open`; `downgraded:blocker|major` blocca, `dismissed` e `downgraded:moderate|minor` passano; `findings_cycle` e `_specialists` come da brief; `skip` -> `None` con «dopo la revisione».
- ✅ Decisioni 1, 5, 8, 13, 25: colonne, `rule`/`blocking` con `is_blocking` pura in `tollgate_analysis` (nessun import di tollgate), `extra_review_cycles`, eventi `finish_check` e `base_realigned`.
- ✅ C5 (ricevute `related` escluse, `dod.py` `_receipt`), C12 (`PLAN`/`plan_text` in `tests/flowkit.py`, `test_taskcmd` li reimporta), C16 (`counted = 0` all'apertura, `supersede`), C18 (normalizzazione dei `rejected`, anche dei `findings`), C25(3) (`phase` + `from_approved_spec` -> `ValueError`), test in più (`set_pr`, `set_finish`, `add_extra_cycles`, `set_review_unverified`, `has_approval`, `complete`, `subTest` in `test_downgrade_and_dismiss`).
- ✅ Strati: `Ctx.approved_waivers` delega a `acts` (hooks importa core, ammesso). Scritture solo via funzioni di core.
- Scostamenti dichiarati: (1) `patch_id` con `--binary --no-ext-diff --no-textconv`: accettabile, coerente con M2 (nessun driver del repo) e il valore resta stabile tra i chiamanti (Task 7, 9, 11 passano tutti da questa funzione). (2) `add_report` che rifiuta fonte non attesa/ripetuta/ciclo non in `review`: coerente, già riportato in carry per il Task 8. (3) `downgraded:<g>` verso l'alto: vedi M3. (4) `set_finish` senza `finish_check`: coerente col brief (il chiamante registra l'evento).
- ⚠️ Non verificabile dal diff: che `tests/run` sia verde su 3.11 e 3.13 (evidenza solo nel report: «1078 test OK»); non rilanciato.

## Punti di forza
- `close_cycle` ripetibile e con transazione separata dai passaggi di fase: un'interruzione tra `UPDATE` e `open_block` si recupera.
- `add_report` normalizza ogni campo prima dell'INSERT: nessun valore fuori vincolo entra nel DB.
- `is_blocking` fail-closed (regola mancante, `R-` ignota); `_off_intervals` condiviso tra `_off_seconds` e `off_periods` (niente duplicazione).
- Test del comportamento reale: ciclo completo con DB vero, tetto con `extra_review_cycles`, `patch_id` dopo un rebase vero, `junit_fake` eseguito davvero.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor
- M1 `bin/tollgate_core/reviews.py:241-279` (`close_cycle`): nessun controllo sullo stadio né sui rilievi senza esito. Un ciclo in stadio `review` (revisori non tutti riportati) o con rilievi `verification IS NULL` si chiude `ok`: un `blocker` mai verificato passa. Fail-open a livello di dati; oggi lo contiene la disciplina dei chiamanti (Task 7, DoD «nessun rilievo senza esito»). Correzione: `ValueError` se `stage != 'verify'` (salvo cicli senza rilievi da verificare) o se restano `NULL`. Da fissare nel Task 7 come precondizione, o qui.
- M2 `bin/tollgate_core/reviews.py:241-279`: la ripetizione di `close_cycle` su un ciclo chiuso `needs_fix` rifà `set_phase -> execution` se la fase è `review` e riapre il blocco del tetto se non c'è uno aperto. I Task 8 e 10 devono chiamarlo solo per riprendere un'interruzione, non dopo `approve finding`/`approve rounds` (che chiudono il blocco e ricalcolano l'esito per conto loro: il blocco ricomparirebbe). `test_close_is_resumable` verifica solo la ripetizione a lavoro finito, non la ripresa a metà che è la ragione d'essere.
- M3 `bin/tollgate_core/reviews.py:219` (`set_decision`): accetta `downgraded:<g>` con gravità superiore all'originale (un `minor` «declassato» a `blocker` diventa bloccante). Lo dichiara il report; per un atto chiamato «downgrade» conviene rifiutare `g` più grave di `severity`. Nessun impatto sulla decisione 15.
- M4 `bin/tollgate_core/intents.py:19-45`: `request` con una chiave esistente non verifica che `work`/`action` coincidano e può riportare a `requested` una riga `authorized`/`used` di `force_push`; `complete` non controlla lo stato di partenza. Rischio solo con chiavi riusate male dai Task 9-11 (le chiavi `force:` nascono solo da `authorize_force`).
- M5 `tests/test_dod.py:233`: assegnazione `kept` inutilizzata in `test_skip_items` (resta solo quella a riga 237).
- M6 Il test di `is_blocking` sta in `tests/test_reviews.py` come da brief, non in `tests/test_verdicts.py` (modulo di `tollgate_analysis`): un test dello strato analysis nel test di core. Imposto dal piano; il Task 5 può aggiungerne uno vicino al modulo.

## Valutazione
**Qualità del task:** Approvato
**Motivo:** contratti, costanti e decisioni 6, 8, 15 e 25 rispettati alla lettera, strati e transazioni corretti, test reali che coprono i casi del brief e i C3/C5/C12/C16/C18/C25. Restano solo minori (M1 e M2 sono precondizioni da ricordare ai Task 7, 8 e 10).
