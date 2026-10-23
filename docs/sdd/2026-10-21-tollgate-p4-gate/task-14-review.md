# Revisione Task 14 (aeb5109)

### Aderenza
- ✅ `open_round(min_number=1)`: `max(DB+1, min_number)` in `bin/tollgate_core/audits.py` (nella transazione); `open_round_row` invariata. Test `test_min_number_raises_the_number` (3, poi 4 con min 2, poi 5): nessun buco né doppione rispetto al DB.
- ✅ m-2: `_next_report_number` (`bin/tollgate_flow/audit.py:489`) legge `reviews/<issue>/` a HEAD con `approvals.report_listing`, il cui regex `_REPORT_NAME` garantisce `\d+`: l'`int()` non può sollevare. `ls_files_at` dà `[]` se HEAD manca. `test_numbering_after_lost_db` (report 1 e 2 committati, DB vuoto → giro 3, brief `plan-adversarial-3.md`) fallirebbe senza la correzione (RED dichiarato verificabile dal diff).
- ✅ Caso (b): `_decide_approval` (`audit.py:~417`) chiama lo stesso `_spec_approval_current` di `approve plan`: stesso rifiuto «spec cambiata dopo approve spec: /tollgate:reopen spec». `peek` passa da `_decide`, quindi dice lo stesso (asserito). Il test ha RED reale (0 != 1).
- ✅ Backtick: `_check_path` copre spec e piano (`audit.py:263,365,376`); `test_backtick_path_refused` ha RED.
- ✅ m-4: `REGISTERED_NOTE` in `audit._committed` solo se il percorso è quello registrato, e in `l2acts._committed` (lì sempre registrato). Test per spec (`prepare`) e piano (`approve plan`) con RED.
- ✅ Riga 19: blob illeggibile → `UNREADABLE_SPEC`, contato major (header `(1, 'findings')`, riga nel report). RED reale.
- ✅ Riga 29: `peek` con `confirm` dà `CONFIRM_STEP` col programma risolto; RED reale.
- ✅ Riga 22 (già corretta, solo test): `test_plan_cap_chain_to_approve_plan` percorre l'intera catena (blocco per tetto con motivo `cap_reason`, `prepare` rifiutato con uscita 1, `resolve` → `plan`, sospeso `{plan-adversarial: 2}`, `prepare` → `approval`, `approve plan` con `adversarial: suspended`, fase `execution`). Asserisce stati scritti da un comando e letti dal successivo: prova il comportamento. Come regressione è valido anche senza RED.
- ✅ Riga 34 (già corretta): il test asserisce rifiuto col messaggio giusto, blocco ancora aperto con il motivo atteso, fase `blocked`, atto `consumed`, secondo `apply` rifiutato senza toccare il blocco. Prova davvero il comportamento. Lo scostamento `open_block(CAP_REASON)` è legittimo: è l'unico modo di avere un blocco dei cicli su un ciclo superato.
- ✅ Review Focus 6: `locate_spec_approval` preferisce l'approvazione corrente alla più bassa; nel test la issue 3 (più bassa) è superata e la 9 corrente, quindi il test discrimina davvero la regola (senza di essa darebbe «reopen»). Percorre `start --spec`, `prepare` del piano, `approve plan`, task, `finish check` con `approvals` «sì». Lo spostamento dei report della spec in `reviews/9/` è coerente con dove `finish check` li cerca.
- ✅ Stratificazione: nessun import nuovo fuori dagli strati; `audits.py` resta senza dipendenze nuove.

### Punti di forza
Modifiche chirurgiche; il caso (b) riusa la funzione esistente invece di duplicare la logica; messaggio e `peek` condividono `_decide`; test di fine catena provenienti dal programma vero; TDD onesto con RED dichiarati per ciò che era davvero rotto.

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. `bin/tollgate_flow/audit.py:489` `_next_report_number` vede solo i report committati a HEAD: un report scritto dall'agente ma non ancora committato al momento della perdita del DB verrebbe sovrascritto. Rientra nel perimetro del caso m-2 (report «già committati»); basta una riga di nota nel docstring.
2. `tests/test_audit_prepare.py` `test_approval_with_plan_adversary_off_and_spec_changed`: l'uguaglianza con `approve plan` è dichiarata nel docstring ma il test non invoca `approve plan`; asserisce la stessa stringa. Sufficiente, ma non prova l'accordo tra i due comandi.
3. `tests/test_check_audit_round.py` (riga di `assertIn("rilievo meccanico: la spec del giro non si legge", ...)`) supera i 100 caratteri, a differenza del resto del file.
4. `test_superseded_refusal_leaves_block_and_act`: il secondo `assertRaises(ActApplyError)` non controlla il messaggio (basterebbe `assertRaisesRegex` su «consumato»/stato), così non distingue il rifiuto per atto consumato da un altro.

⚠️ Non verificato da me: l'esito di `tests/run` (2319 test su 3.11 e 3.13 dal report); non ho rilanciato la suite come da regole.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** ogni caso del brief ha un test che fallirebbe senza la correzione, tranne i tre dichiarati già corretti (righe 22, 34, Review Focus 6), i cui test asseriscono comunque comportamento reale su stati cross-comando; solo rifiniture minori.
