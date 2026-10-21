# Revisione Task 7 (57c79f0): approve spec, approve plan, sospensioni da resolve

Controlli fatti: lettura del diff, del report, di `scope.register_plan`, `audits.*`, `approvals.locate_spec_approval`, `specdoc`; eseguiti solo `python3 -B -m unittest tests.test_l2acts tests.test_check_common` (46 test OK, output pulito). Sola lettura.

### Aderenza
- ✅ `approve spec` (decisione 9, D2, D16): fase, spec in HEAD uguale al disco, numero di fette (rifiuto col numero atteso), giro aperto, `audit.adversarial_ok` riespresso in `_adversarial_check` (l2acts.py `_adversarial_check`), lenti chiuse/sospese/off/None, ultimo giro chiuso con `audits.last_closed(SPEC_KINDS)` sul blob attuale anche con avversario spento, file con `render_approval`, poi `set_phase` fuori transazione (causa `approve_spec`). Proposta delle issue in un solo recinto con `brief.fence` + `DATA_NOTE`, nessuna chiamata a `gh`.
- ✅ `approve plan` (decisione 10, D3): fase `approval`, giro aperto, plan-check, approvazione della spec cercata nei file in HEAD (rifiuto «committa ... prima di approve plan» se solo su disco), `spec_sha` coerente, giro del piano su `sha` e `spec_sha`. Ordine register_plan, file, fase; `register_plan` saltato se `plan_sha` è già il blob. Verificato: `audit prepare` registra solo `plan_path` (`scope.set_plan_path`), quindi `plan_sha` valorizzato significa davvero scope registrato; la ripetizione dopo interruzione è sicura in ogni punto (dopo register, dopo file, dopo file e prima della fase).
- ✅ `suspend_on_resolve` (decisione 7, D6): tipo da `cap_kind`, condizione dal DB (adversariali: ultimo giro chiuso non pulito e `len >= tetto`; lenti: `len >= spec_audit_cycles` e non chiuso; `DECLINE_REASON` con 0), altrimenti `None`. In `_resolve` gira prima di `close_block`, in transazione propria (`audits.suspend`), idempotente. Decisione 27: fase ripristinata da `close_block` e sospensione nella stessa chiamata, asserito da `test_cap_resolve_suspended_then_approve`.
- ✅ `APPLIERS`, `_pick`, conversione `Refused` -> `ActApplyError`, `l2acts` non importa `actapply` (importa `audit`, stesso strato).
- ✅ `locked_docs` (decisione 19, D7): `locate_spec_approval(..., spec_blob=None)` sui `spec-approval.md` del disco, anche di altre issue; letto una volta per `diff_violations` (`violations.py:151`).
- ✅ D10 (fixture con `render_approval`), D17, D3 e D2 coperti da test; `FlowLab` con `.tollgate-run/` in `info/exclude`, `RoundCase.lab` rimosso.
- ✅ Review Focus 3, 4, 6: i test attraversano hook (`UserPromptExpansion`, `SubagentStop`, `PreToolUse Bash`/`Edit`), CLI (`audit prepare`, `audit decline`) e `apply_act`. `resolve` e `approve` sono applicati dalla libreria `apply_act` con `now=fl.now` (D20), non dal sottocomando `act apply`: accettabile per D20, ma il passaggio da `main()` non è esercitato qui.
- ⚠️ RED non registrato (dichiarato): non verificabile. Dai test letti, quelli che contano falliscono se si toglie la condizione corrispondente (ultimo giro sul blob, sospensione con numero, blocco in `blocked`, HEAD della approvazione, un solo `scope_registered`), quindi il rischio sul valore dei test è basso.

### Punti di forza
- Rifiuti con messaggi che dicono cosa fare; ordine delle scritture scelto in modo che ogni interruzione sia ripetibile; test dell'interruzione con `scope_registered` e task contati.
- Test di sospensione ben delimitati: blocco aperto a mano senza giri, sotto il tetto, ultimo giro pulito, idempotenza, soglia da config.
- `test_untrusted_slice_titles_stay_in_a_longer_fence` e `gh_calls() == []` provano il vincolo sul testo non fidato.
- La pubblicazione di `passed`, `clean`, `last_round` evita di duplicare la regola dei giri (scelta giusta, vedi però l'Important sotto).

### Rilievi
**Critical:** nessuno.

**Important**
1. Duplicazione letterale di logica già in `audit.py`, mentre le tre funzioni vicine sono state rese pubbliche proprio per non duplicare: `l2acts._on` (identica a `audit._on`/`_comp`), `l2acts._committed` (stessa sequenza `blob_at` / esiste / `blob_sha` di `audit._committed`, audit.py:179-192, con messaggio diverso), `l2acts._cfg` (copia di `actapply._config`, actapply.py:32-39), e la chiamata a `check_plan` di `approve_plan` (copia di audit.py:326-331, parametri compresi: se cambia una soglia va cambiata in due posti e `approve plan` può accettare un piano che `audit prepare` rifiuta, o viceversa). Correzione: rendere pubbliche (`audit.on`, una funzione `audit.committed_blob(wt, path, what)` con il messaggio dato dal chiamante, una `audit.plan_check(cfg, text)`), e per la config una funzione unica (per esempio in `tollgate_flow`) usata da `actapply` e `l2acts`.

**Minor**
- l2acts.py `_spec_approved`: `locate_spec_approval(..., spec_blob=None)` con più candidati di altre issue sceglie la più bassa anche se è stantia, mentre la decisione 13 per `approve plan` prevede `spec_blob=<blob attuale>` (trova quella con lo sha giusto). Caso raro (fette successive con approvazione della prima fetta riscritta), ma passando `spec_blob` e poi `is_current` sul risultato si evita. Va aggiunto un test con due approvazioni di issue diverse.
- tests/test_l2acts.py `test_wrong_slice_count_refused`: `assertIn("3", ...)` è debole (il messaggio contiene altri numeri); meglio asserire «prevede 3 fette».
- Non coperti: `approve plan` in `blocked` (rifiuto verso `/tollgate:resolve`), `approve spec` con spec non committata («committa ... prima di approvare»), catena reale di un tetto del piano (`plan_rounds` → blocco → `resolve` → `approve plan`; c'è solo `suspend_on_resolve` per libreria).
- `test_plan_approval_committable_in_execution`: la prima `fl.bash("git add ...")` serve solo all'hook, il vero `git add` lo fa `fl.git`; ok ma il commento nel test non lo dice.
- actapply.py `_resolve`: `_config(state, work)` con `work["worktree"]` nullo darebbe `TypeError` (`Path(None)`); un lavoro con blocco del tetto ha sempre un worktree, ma il resolve non dovrebbe dipendere da esso.
- `cfg` opzionale di `suspend_on_resolve`: scostamento dal brief, motivato (tetti da config) e provato da un test; accettato.
- RED non registrato (processo): da annotare, nessuna azione sul codice.

### Valutazione
**Qualità del task:** Da correggere (solo per l'Important 1, correzione meccanica).
**Motivo:** Comportamento, ordine delle scritture, sospensioni e blocco della spec sono corretti e ben provati sui comandi veri; resta la duplicazione letterale con `audit.py` e `actapply.py` (incluso `check_plan`) che rischia divergenze future fra `audit prepare` e `approve plan`.
