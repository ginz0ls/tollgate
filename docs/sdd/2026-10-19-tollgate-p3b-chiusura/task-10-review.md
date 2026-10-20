# Revisione Task 10 (e96325b..38ff416)

### Aderenza
- ✅ `approve rounds`: un solo tetto per volta, entrambi aperti rifiuta con rinvio a `resolve` (actapply.py:97-103); cicli fatti + n <= 8 con `reviews.count` (actapply.py:67-76, "contando tutti i cicli" di spec 8.4); giri 5 + extra <= 8 in `tasks.add_extra_rounds` (tasks.py:110-124); chiude il blocco. Test: one_more_cycle, over_eight, fix_rounds_cap (sesto e settimo giro, ottavo rifiutato), both_blocks, bad number.
- ✅ `resolve` al tetto dei cicli concede UN ciclo (actapply.py:58); con 8 cicli fatti rifiuta e indica `approve unverified-review` (ruling dubbi 2-3).
- ✅ `approve finding`: gravità `blocker|major|moderate|minor|dismiss`, motivo obbligatorio, solo `confirmed` (via `set_decision`), ricalcolo con `recompute_outcome` senza `close_cycle` (M2, reviews.py:35-59), nessun cambio di fase, `counted` invariato. Il blocco dei cicli si chiude sempre (ruling dubbio 1) quando il rilievo è del ciclo ultimo chiuso: test `..._even_if_still_needs_fix`.
- ✅ `approve unverified-review`: >= 8 cicli, flag, chiude il blocco dei cicli, fase invariata (test asserisce flag, blocco, fase; C7).
- ✅ `approve rebase`: prefisso `SYNC_CONFLICT_REASON`, rebase in corso rifiutato, base = merge-base(HEAD, ref predefinito) con evento `base_realigned`, blocco chiuso, `set_phase(execution)` solo se `pr_open`, un intento `force_push`; `set_phase`/`close_block` fuori da transazione. Test in `pr_open` e in `execution`.
- ✅ L'atto si consuma sempre anche con rifiuto (apply_act consuma prima; asserito in over_eight e unverified_only_after_eight). `GitWriteError` aggiunta alle eccezioni gestite (actapply.py:394).
- ✅ `task start --fix` oltre i 5 giri: tetto `MAX_FIX_ROUNDS + extra_fix_rounds` (taskcmd.py:104); il ramo `renamed`/`launch`/`-r<giro>`/`inherit` è generico da `RENAMED_FROM_ROUND = 4` (taskcmd.py:135-142), quindi il sesto giro si comporta come quarto e quinto.
- ⚠️ Nome `-r6`, `launch` e `model: inherit` al sesto giro non sono asseriti da nessun test (vedi Minor 3); per codice il comportamento è corretto.

### Punti di forza
- `recompute_outcome` è piccola, idempotente (scrive evento solo se cambia), non riapre il tetto.
- Test costruiti con le funzioni vere di `reviews`/`phases` e con `taskcmd.task_start` reale per il tetto dei giri (così la regex del motivo è vincolata al testo vero di taskcmd).
- Test extra utili: doppio tetto, numeri non validi (`²`), downgrade, blocker residuo, rebase senza blocco.
- Correzione del dubbio 1 minima e coerente col ruling, con test dedicato.

### Rilievi
**Critical:** nessuno.

**Important:** nessuno.

**Minor**
1. actapply.py:267-280 e 273: `approve finding` su un rilievo di un ciclo non ultimo (o ultimo non chiuso) ritorna senza chiudere il blocco dei cicli. Il ruling dice «chiude il blocco se aperto, qualunque sia l'esito»: l'asimmetria per i rilievi di cicli vecchi è plausibile ma non decisa né testata. Documentarla (o chiudere comunque) e aggiungere un test.
2. actapply.py:273 + reviews.py:47-48: se l'ultimo ciclo è `superseded` (accade con l'ottavo ciclo: `finalreview.py:100` fa `supersede` prima del controllo `MAX_CYCLES` a riga 106) e ha un rilievo `confirmed`, `recompute_outcome` solleva `ValueError`, non gestito da `apply_act` (cattura solo sqlite3/TransitionError/Git*): traceback dopo che `set_decision` è già scritta. Catturare `ValueError` nell'applicatore (come per `set_decision`) o limitare il ricalcolo agli esiti `ok|needs_fix`.
3. tests: manca un'asserzione sul sesto giro (nome `tg-N-tK-r6`, `pending = launch`, `model: inherit`, brief `task-K-fix-6.md`); `test_approve_rounds_on_fix_rounds_cap` verifica solo `fix_rounds == 6`. Il brief citava anche `tests/test_taskcmd.py`, non toccato.
4. actapply.py:25: `FIX_CAP` duplica il testo del motivo di taskcmd.py:105. Il test end-to-end evita la deriva silenziosa, ma una costante condivisa (per esempio in `tasks`) sarebbe più solida.
5. actapply.py:58-59, 107-111: `_grant_cycles` poi `close_block` non sono atomici (se `close_block` fallisce il ciclo è concesso e il blocco resta). Improbabile, riprovabile solo con un nuovo atto.
6. actapply.py:314-320: `set_base`, `close_block`, `authorize_force` in sequenza; un errore dopo `close_block` lascia base riallineata e blocco chiuso senza intento `force_push` (l'atto è consumato). Ordinare `authorize_force` prima di `close_block` renderebbe il caso ripetibile.
7. Il motivo di `approve finding` vive solo nell'atto e nel messaggio, non nella risoluzione né negli eventi del rilievo (`_log_finding`); la risoluzione del blocco usa `approve finding <id>`. Accettabile (args dell'atto conservati), da tenere presente per `stats`/commento PR (Task successivi).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti di brief, carry, ruling e decisioni 13-14 implementati e coperti da test reali; M2 rispettato, atto sempre consumato, ordine delle chiamate di fase corretto. Restano solo rifiuti minori di robustezza e copertura.
