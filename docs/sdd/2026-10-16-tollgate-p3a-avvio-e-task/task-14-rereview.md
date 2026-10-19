# Ri-revisione Task 14, giro di correzione 1 (1d8906f..71f4230)

Letto una volta il diff `review-1d8906f..71f4230.diff` e la sezione «Giro di correzione 1» del report. Suite non rilanciata. Verifiche mirate in sola lettura su `config.py`, `paths.py`, `tests/test_wrapper.py`.

### Verdetti sui rilievi

1. **Important: `test_watchdog_is_capped_at_85` con `sleep(0.5)` fisso e un solo controllo.** INDIRIZZATO. `tests/test_wrapper.py` aggiunge `wait_alive` (polling 50 ms, scadenza 10 s) e il test lo usa al posto di sleep + `proc_alive` (`alive = self.wait_alive("^sleep 87$")`). Il polling non nasconde un fallimento: `alive` resta un booleano e `assertTrue(alive)` è invariato. Senza il tetto a 85 il wrapper avvia `sleep 902`, il pattern `^sleep 87$` non compare mai, `wait_alive` scade dopo 10 s e il test fallisce. Anche `assertFalse(self.proc_alive("^sleep 902$"))` e `p.wait(timeout=30)` sono intatti. Il finto hook `nap` dura 2 s (`tests/test_wrapper.py:20-22`): il watchdog resta vivo per tutta la finestra e il polling a 50 ms lo intercetta.

2. **Minor 1: riga 18 vaga.** INDIRIZZATO. La riga 18 del piano elenca `final_review` e `definition_of_done` (P3b; la seconda anche nel gate, P4), `spec_adversary`, `spec_audit`, `plan_adversary`, `spec_pitch` (P3c), `base_test_ids` e `sentinel` (P4). Tutte le otto chiavi sono in `DEFAULTS["components"]` (`bin/tollgate_core/config.py:87-91`) con la grafia esatta, e l'assegnazione ai piani coincide con quella indicata nel rilievo.

3. **Minor 2: commento «criteri 4 e 38».** INDIRIZZATO. `tests/test_criteria_p3a.py` ora dice «criterio 4 (ramo generico, senza profili verticali)».

4. **Minor 3: `runner.py:50` col percorso nudo.** INDIRIZZATO. `_footer` usa `program_command(db.BIN_PATH)` (`bin/tollgate_hooks/runner.py:50`; import da `tollgate_core.paths`, `paths.py:16`). Test nuovo `test_hook_engine.FooterTest.test_footer_names_the_program_as_the_model_runs_it`; il report dichiara RED prima e GREEN dopo. Resta `db.restore_command` (`db.py:35`) col percorso nudo: è un comando per l'utente da terminale, dichiarato nel report.

5. **Minor 4: `GATE_FILES` a sei voci.** INDIRIZZATO. Piano, sezione 3, riga «Gate installato»: «`prereq.GATE_FILES` (sei voci): i cinque workflow ... più `.github/tollgate/VERSION`». Il conteggio nel «Stato» passa a 985.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- Il test del footer ricalca nell'asserzione la stessa espressione del codice, quindi non prova da solo la forma `python3 '...'`, che è coperta dai test di `program_command`. Accettabile.
- Il report segnala «Exception ignored … unclosed database» a fine suite, preesistente. Non blocca.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
