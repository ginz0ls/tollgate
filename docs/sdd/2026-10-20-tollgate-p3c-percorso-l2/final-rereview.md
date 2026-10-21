# Ri-revisione del giro di correzione d71f48d..3aa47c2

Metodo: diff letto per intero, report letto, verifica sul codice a 3aa47c2. Unico comando lanciato: `python3 -B -m unittest tests.test_audit_prepare tests.test_l2acts tests.test_check_audit_round tests.test_skill_contract` (175 test, OK).

### Verdetti sui rilievi

1. **I-1: un solo helper cerca l'approvazione della spec (prima con il blob, poi con `None`)**: INDIRIZZATO. `bin/tollgate_flow/l2tree.py:31-52` (`spec_approval`), usato da `audit._spec_approval_current` (`audit.py:327`, quindi `prepare` in `plan`, `peek` e `status` via `_decide`) e da `l2acts._spec_approved` (`l2acts.py:185`). La ricerca con `None` serve solo a distinguere STALE da MISSING. Test: `tests/test_audit_prepare.py::SpecApprovalOfLaterSliceTest` (helper nelle combinazioni, `prepare` apre il giro plan-adversarial, `peek` senza «reopen», caso con sole approvazioni superate) e `test_l2acts.py::ApprovePlanTest.test_later_slice_prepare_and_approve_plan_agree`. Il caso riprodotto dalla revisione (reviews/3 superata, reviews/9 corrente, issue 12 senza file proprio) ora passa.
2. **Riga 18: nessun `.tmp` in nessun ramo d'errore, veto invece di traceback**: INDIRIZZATO. `bin/tollgate_hooks/apply.py:125-137` pulisce il temporaneo su `(OSError, ValueError)`; i due chiamanti (`apply.py:205`, `apply.py:220`) catturano `(OSError, ValueError)` e danno veto. Sono gli unici due usi di `_write_atomic`. Test in `test_check_audit_round.py::WriteFailureTest`.
3. **Riga 38: rapporto di prova**: INDIRIZZATO. Backtick della riga 5 bilanciati, percorsi della prova di riferimento in `/tmp/tollgate-p3c/prova-1/flow` (righe 11, 13, 14, 21), doppia parentesi del «non esercitato» sistemata. Restano `/tmp/tollgate-p3c/flow` solo dove si parla della cartella rigenerata e della prova accidentale (righe 5, 71, 77), come dichiarato.
4. **Riga 40: «(P3c)» nella tabella P3a**: INDIRIZZATO. Piano principale riga 225 ora «chiuse in P3c (tabella «Prove dei criteri di P3c»)»; `grep "(P3c)"` non trova altro nelle colonne «Resta a».
5. **m-1: `reopen plan` in `approval`**: INDIRIZZATO. `audit._decide_approval` (`audit.py:395-407`) confronta blob di piano e spec in HEAD con `last["sha"]`/`last["spec_sha"]` (solo con `plan_adversary` acceso), come `l2acts._plan_adversarial` (`l2acts.py:~205`), che usa lo stesso testo `audit.PLAN_CHANGED`. `peek` passa da `_decide` anche in `approval` (con ripiego `approve_plan` se la lettura fallisce). Test: `ApprovalPhaseTest` e `test_plan_changed_after_last_round_points_to_reopen_plan`.
6. **m-5: nessun «audit prepare» nudo**: INDIRIZZATO. `STEPS["resolve"]`, i rifiuti di `l2acts.py`, i due rifiuti di fase (`prepare`, `decline`) usano `<programma>`/`_prog()`/`_program()`; grep su `bin/` non trova altri letterali nei messaggi (restano solo docstring). Skill `spec-audit` allineata (`<programma> audit prepare`), `test_skill_contract` verde.
7. **m-6: frase sulla sospensione**: INDIRIZZATO. `skills/spec-audit/SKILL.md` («I tetti»): «In entrambi i casi il `resolve` sospende; per l'audit a lenti la sospensione è definitiva.» Test `test_caps_section_says_resolve_always_suspends`.

Spec rev 24: 6.2 (paragrafo «Dove sta l'approvazione», punti 7 e 8) e riga 24 della sezione 20 descrivono il codice nuovo (helper `l2tree.spec_approval`, controllo in `approval`, uscita `reopen plan`). Nessuna revisione nuova, coerente col ledger.

### Danni nuovi nel diff della correzione

Nessuno. Controllato in particolare la divergenza fra comandi sullo stesso stato: `prepare`, `peek` (e quindi `status`/checkpoint) e `approve plan` usano la stessa funzione per l'approvazione della spec e la stessa condizione (blob piano e spec contro l'ultimo giro) per `PLAN_CHANGED`. Il confronto in `approval` usa `work["plan_path"]`/`work["spec_path"]` e `last_round` come `approve plan`.

### Osservazioni fuori ambito

- Con la propria approvazione (`reviews/<issue>/`) superata e un'altra corrente, `locate_spec_approval` dà la precedenza alla propria, quindi l'helper risponde STALE (codificato nel test `test_helper_own_stale_approval`). Coerente fra tutti i comandi e con la spec 6.2; il secondo scenario della revisione finale (fetta in `execution` la cui approvazione propria è vecchia dopo una correzione di altra fetta) resta quindi rifiutato con `reopen spec`. Da decidere in P4 se la regola «propria prima» sia voluta.
- In `approval` con `plan_adversary` spento `prepare` dice ancora «chiedi all'utente approve plan» anche se la spec è cambiata, mentre `approve plan` rifiuta con «spec cambiata»: preesistente e non toccato dal diff.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
