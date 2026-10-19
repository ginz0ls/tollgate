# Revisione Task 8: act apply (resolve, resolve writer, approve level)

### Aderenza
- ✅ `phases.set_level_cap` (phases.py:166-190): fase di `blocked` letta da `phase_before_block`, rifiuto se la fase non è nella sequenza di `cap`, `level_change` con `cause: "cap"` solo se abbassa, fase intatta (decisione 14).
- ✅ `APPLIERS` con le due chiavi, `ActApplyError`, `apply_act` (actapply.py:77-142). Sessione con `cli_session(..., "act")`, lavoro con `work_for_path`.
- ✅ Un atto di un'altra sessione, scaduto o di un altro lavoro è rifiutato da `acts.consume` (acts.py:86-95) prima di qualunque effetto; senza id la query (actapply.py:92-96) filtra già sessione, lavoro, scadenza e chiave. `consume` aggiorna `state` dentro `db.tx` su `pending`: un secondo `apply` sullo stesso id fallisce («inesistente o non più valido»).
- ✅ `resolve <id>`: blocco aperto del lavoro, nota da `args[1:]`; task `blocked` -> `unblocked` solo se la fase esce da `blocked`.
- ✅ `resolve writer`: interrompe solo i `running` non di sola lettura (`config.is_readonly`), testato con `probe:reviewer-frontend`, `Explore`, `tollgate:implementer`.
- ✅ `approve level`: `cap_paths` da diff dalla base con `old_path`, `output_excludes`, vincolo (5) rispettato (`level_cap_paths` scritto).
- ✅ C9: `Ctx.readonly` e `_common.output_excludes` delegano a `config`; la regex è la stessa di prima (config.py:13), tolta da `context.py`. Comportamento P2 invariato (925 test verdi riportati).
- ✅ Criterio 22: `test_approve_level_cap_holds_until_new_sensitive_path` (test_actapply.py:118). Logica in `lv.next_level` (level.py:54-59): il tetto regge finché `sensitive_now <= cap_paths`.
- ✅ Strati: `actapply` importa solo core e analysis; `cli.py` importa flow in modo pigro (ammesso); `close_block`/`set_phase` fuori da transazione (apply_act non apre transazioni prima: `consume` e `_pick` chiudono le loro).
- ⚠️ Il `Ran 925 tests OK` è dichiarato dal report, non rilanciato (regola del revisore).
- ⚠️ `pkill -f` usato dall'implementatore (dichiarato nel report): viola la cautela, ma non lascia traccia nel diff; segnalato al controller.

### Punti di forza
- Il consumo precede l'applicatore, quindi nessuna doppia applicazione, nemmeno con due `act apply` concorrenti (l'UPDATE è dentro `db.tx` con controllo di `state`).
- Rifiuto netto dei tipi non applicabili (`approve waiver`) senza consumarli (`_pick`, actapply.py:81-84).
- Test numerosi e mirati (rename, output dirs, altro blocco aperto, altra sessione/scadenza, CLI).
- Delega a `config` senza duplicare la regola.

### Rilievi

**Critical**: nessuno.

**Important**
1. actapply.py:56-62 (`_resolve`, ramo blocco): `close_block` e poi i `task_event` `unblocked` sono transazioni separate, e l'atto è già consumato (decisione 13). Se un `task_event` fallisce a metà (`TaskTransitionError`, `sqlite3.Error`), il blocco è chiuso, la fase è già tornata indietro, ma alcuni task restano `blocked`, l'atto non è riapplicabile e `resolve <id>` non ha più un blocco aperto da chiudere: stato incoerente senza via di uscita. Correzione: o fare lo sblocco dei task in un'unica `db.tx` (una funzione `tasks.unblock_all(conn, work, ...)` in core, chiamata subito dopo `close_block`), o rendere ripetibile l'effetto (idempotenza: sblocco dei task `blocked` anche quando non ci sono blocchi aperti, tramite un nuovo `act apply` / `status`). Preferibile la prima; non serve una transazione che includa `close_block` (vincolo fuori-transazione).
2. actapply.py:49-52 (`_resolve`): `act["target"].isdigit()` accetta caratteri come «²», per cui `int()` solleva `ValueError` non gestito (traceback, atto già consumato). L'hook non valida il target (checks/acts.py:64-67). Correzione: `target.isascii() and target.isdigit()` (o `try int()`).

**Minor**
- actapply.py:129-137: l'atto viene consumato anche per errori di sola forma dell'input (livello sconosciuto, motivo mancante: `_approve_level` righe 68-72). È conforme alla lettera della decisione 13, ma costringe l'utente a ridare l'atto per un refuso. Valutare di validare `args` prima di `consume` (nessuna perdita di sicurezza: nessun effetto è prodotto).
- actapply.py:76-77: `cap_paths` è calcolato fuori dalla transazione di `set_level_cap`: un `post_edit` tra i due può aggiungere un percorso sensibile non incluso nel tetto. Effetto prudente (il tetto non regge per quel file); nessuna azione necessaria, ma da annotare.
- Dubbio del report (`cap_paths` senza `min_level` dei profili): con `_common.py:251` il tetto vince anche su un `min_level` di profilo (`min(computed, cap)` dopo il `max` con il profilo), quindi un file nuovo che attiva un profilo L2 non rialza il lavoro finché il tetto regge. Coerente con «tetto = scelta esplicita dell'utente» ma non è scritto in spec 5/12.3 che io sappia: ⚠️ da confermare col controller; non è un difetto del task.
- `output_excludes` è ancora ricostruito a mano in `bin/tollgate_flow/taskcmd.py:206` e `bin/tollgate_core/verify.py:154` (`output_dirs + [".tollgate-run/"]`): ora che esiste `config.output_excludes` sono duplicazioni letterali; fuori dal perimetro del diff, ma conviene chiuderle nello stesso giro o nel Task 14.
- L'id di `resolve` solo intero (dubbio del report): accettabile, coerente con `status`.

### Valutazione
**Qualità del task:** Da correggere (lieve).
**Motivo:** Requisiti, sicurezza dell'applicazione unica e refactoring C9 sono corretti e ben testati. Restano due fragilità in `_resolve`: lo sblocco dei task non atomico dopo un atto già consumato (stato non recuperabile) e il crash su target numerico non ASCII.
