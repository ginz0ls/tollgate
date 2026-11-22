# Revisione Task 3: la presa della taglia (09b4bbb)

Sola lettura sul pacchetto `review-69cf755..09b4bbb.diff`; controlli mirati fuori dal diff: `db.tx` (annidamento), `runner.py:318-322` (errori delle operazioni `record`), `specdoc.slices`, ordine dei passi in `adopt._adopt`.

### Aderenza
- ✅ Funzione pura `worksize` con le firme del brief (`SIZES`, `LABELS`, soglie 4 task / 2 aree, `Signals`, `Proposal`, `Preview`, `propose`, `areas`, `preview`); `tollgate_analysis` importa solo `.profiles` (`worksize.py:11`). `sizes` (core) importa `tollgate_analysis`: ammesso. `tollgate_flow` non importa hooks né checks.
- ✅ Mai giù, grande solo con il sì: `worksize.py:84-87` (`target` = medio se large senza `yes`; `applied = current` se `_rank(current) >= _rank(target)`). `yes` solo con `cause == "approve_spec"` e `confirmed` (`:68-70`). `test_never_goes_down`, `test_large_needs_a_yes`, `test_plan_after_reopen_does_not_shrink`, `test_l1_plan_with_three_slices_stays_medium` lo fissano (Review Focus 3).
- ✅ Taglia dell'utente: resta salvo il sì alle fette, e in quel caso `by` torna `rules` (D12, `sizes.py:34-35`, `:19-22`; `test_yes_on_slices_returns_user_size_to_rules`).
- ✅ `size_decided` a ogni chiamata con i `data` esatti della decisione 2 (`sizes.py:36-41`): `proposed/applied/previous/cause/by/reason/signals/confirmed`, `confirmed` `True`|`None`. `decide` rifiuta `act` e cause ignote (`:27-28`) prima di toccare il DB. `set_by_user` con `cause="act"` e `confirmed` vero.
- ✅ Stessa riga iniettata e registrata: l'hook (`post_edit.py:40-43`) e `decide` chiamano la stessa `preview`; `test_injected_line_equals_decided_line`, `test_decide_line_equals_preview`. La riga dipende da `current` solo tramite `held` e `applied == "large"`: un livello salito nella stessa modifica (taglia già alzata dall'operazione `level`) non la fa divergere.
- ✅ Tre chiamanti di `register_plan` tutti con la taglia: operazione `plan` (`apply.py:48-57`), `approve_plan` (`l2acts.py`, dentro l'`if plan_sha != plan_blob`, prima di `set_phase`: D10, D19), `adopt._register_plan` (D9 con `git.text_at`). `test_size_decided_once_after_an_interrupted_approve_plan` copre D19 (la transazione annidata si unisce, `db.py:217-220`).
- ✅ `start._create`: passo «taglia» in `steps.run` prima di `incomplete = steps.failed`; errore = «registrazione incompleta: taglia» (`test_size_failure_is_incomplete_registration`); riga prima di `prossimo passo:`; la ripresa non decide.
- ✅ `adopt`: passo «taglia» subito dopo `create_work` e prima di cap e piano (`adopt.py:376`), errore = incompleta (test); `spec_own` vero solo con `spec-approval.md` della stessa issue; fetta successiva (`_approved_elsewhere`) → `slices` nullo e nessun `approve_spec`; `slices` e `decide(approve_spec, confirmed=True)` nella stessa transazione. Riga unica `taglia:` prima di `prossimo passo: EnterWorktree`.
- ✅ Operazione `level`: `decide(cause="level")` solo se l'indice del livello sale (`apply.py:36`); il tetto che abbassa passa da `set_level_cap`, non da `_level` (`test_level_cap_lowering_does_not_decide_size`). `apply._OPS` resta a 29 (`"level"` e `"plan"` sostituiti, nessuna chiave nuova). `test_level_failure_does_not_block_plan_registration` non è nel diff: invariato.
- ✅ Lavoro nato prima di C1 (`size` nullo): `_rank(None) = -1`, `previous` nullo, nessun errore (`test_pre_c1_work_gets_a_size_without_error`, `test_reopen_plan_on_pre_c1_work`); nessun ricalcolo silenzioso (decide solo nei punti di chiamata) (Review Focus 4).
- ✅ Niente nome nudo del programma nei messaggi (usa `/tollgate:approve spec`, `/tollgate:start`); `test_lines_never_use_bare_program_name`.
- ✅ Nessun modello di linguaggio: solo regole.
- ⚠️ Non verificato da me (non rilancio la suite): il verde riportato in `suite-task-3.log`; il giro 1 aveva 20 fallimenti per il file non tracciato, spiegati e risolti con `git add`.

### Punti di forza
- `holds_user_size` condiviso fra `preview` e `decide`: la regola vive in un posto solo, `by` non può divergere dalla riga.
- Atomicità giusta dove si può: piano + taglia in un'unica transazione in `approve_plan` e `adopt`; `_decide_size` mette `UPDATE slices` e `decide` insieme.
- Il passo «taglia» di `adopt` è isolato in `step`, quindi un errore non perde il piano.
- Test buoni sui casi limite (L2 con grande non autorizzato, utente `small` con proposta grande, L0, ripetizione dopo interruzione).

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `bin/tollgate_hooks/apply.py:48-57` (`_plan`): due transazioni (`register_plan` con `advance=True`, poi `decide`). Se `decide` solleva `sqlite3.Error`, il piano è già registrato (`plan_sha` impostato, quindi l'hook non lo riprova: `post_edit.py:_plan` esce se `work["plan_sha"]`), manca l'evento `size_decided` con causa `plan`, e `runner.py:318-322` non cattura `sqlite3.Error` nel ciclo dei record: salta il resto dei record e l'iniezione «piano registrato». La taglia non si perde (esiste già dall'avvio), ma il dato per il confronto con un modello resta bucato e non c'è un messaggio all'utente. Correzione possibile: `register_plan(advance=False)` e `decide` in un'unica `db.tx`, poi `set_phase` fuori, oppure catturare `sqlite3.Error` attorno a `decide` e iniettare un avviso di «registrazione incompleta: taglia». Rischio basso e già dichiarato dall'implementatore.
2. `bin/tollgate_flow/adopt.py:376` e `:421-433`: la taglia «start» usa `ev.level` prima del tetto (`_apply_cap`, `:382`). Con un tetto che abbassa (es. L2 → L1) la taglia resta `medium` per «livello L2» e non scende mai (regola corretta, ma il motivo registrato cita un livello poi tolto). Coerente con l'ordine imposto dal brief; basta saperlo.
3. `bin/tollgate_flow/l2acts.py` (fine di `approve_plan`): la riga della taglia viene dopo «poi /tollgate:execute.» nello stesso messaggio, quindi non è «prima del prossimo passo» come negli altri tre punti. Il brief la vincola solo per `start`/`adopt`; è una rifinitura.
4. `tests/test_check_post_edit.py`: nessun test per l'operazione `level` che arriva con livello uguale/più basso (`_level` filtra con `LEVELS.index`, ma il ramo non è provato direttamente; solo il tetto via `set_level_cap`). Copertura, non difetto.
5. Processo: TDD non stretto sui punti di chiamata (dichiarato nel report). I test scritti dopo sono comunque asseriti sul comportamento (eventi, colonne, righe), non tautologici.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** i requisiti del brief e le decisioni D9, D10, D12, D17, D19 sono tutti rispettati sul diff: la taglia non scende da sola, diventa grande solo con il sì, i lavori pre-C1 non danno errori, e gli errori di `decide` in `start` e `adopt` diventano «registrazione incompleta». Restano solo rifiniture, la più utile è rendere atomica o segnalata la doppia transazione dell'operazione `plan`.
