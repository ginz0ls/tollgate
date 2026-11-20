# Revisione Task 2 (f48919b..53dcef1)

### Aderenza
- ✅ Decisione 4: `bin/tollgate_flow/init.py:361-364` propone `min_level` e `checklist` solo se il frammento li ha non vuoti, diversi da `config.PROFILE_DEFAULTS` (L0 / "") e la chiave manca nel blocco dichiarato (`key not in decl`). Il blocco dell'utente non viene mai riscritto: `_drift` produce righe di proposta (`lines`/readme), come per `agent`. Un `min_level` dichiarato anche diverso dal frammento (es. L0 contro L2) non viene toccato.
- ✅ Decisione 5: `bin/tollgate_core/tasks.py:158` `ORDER BY (reserved_at IS NULL), reserved_at DESC, number`; firma invariata. `reserved_at` è scritto da `clock.fmt` (formato a larghezza fissa), quindi il confronto testuale è corretto. Il filtro `pending`/`agent_type`/`number` resta nel WHERE, quindi il ramo `resume` con `number=task` (apply.py:40) non cambia; il ripiego `resume=True` senza numero (apply.py:44) ora preferisce un task prenotato (vedi Minor 1).
- ✅ D1: `DECLARED_X` riceve `min_level = "L1"` (test_init.py:677); nessuna asserzione esistente toccata o indebolita (il diff di test_init.py ha solo la fixture e i due test nuovi).
- ✅ D14: `test_take_pending_most_recent_reservation_wins` (test_tasks.py): prenota 1 a T0+10 s e 2 a T0, vince 1 e il 2 resta `launch`.
- ✅ Test richiesti presenti: i due di `test_init`, i due di `take_pending` (launch/resume), `test_second_task_of_same_type_bound_by_name`.
- ⚠️ RED/GREEN e suite (4094 test, due interpreti) non rilanciati: affermazioni dell'implementatore, coerenti con il codice (nel test di `check_agents` senza l'ORDER BY nuovo il task 1 vincerebbe per numero).

### Punti di forza
- Modifica chirurgica (4 righe in `init.py`, 1 clausola SQL), nessuna nuova astrazione, pattern identico al ciclo di `agent`.
- `test_update_does_not_repeat_declared_min_level` usa `min_level = "L0"` e `checklist = ""` (diversi dal frammento): prova la regola «chiave presente = non si propone», non una coincidenza di valori.
- Il test del task prenotato asserisce davvero: stato di entrambi i task dopo la presa, poi la seconda presa che restituisce 1; il test in `check_agents` verifica anche `subagents.task == 2`.
- Test di controllo senza prenotazione (numero più basso) che protegge il comportamento precedente.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `bin/tollgate_core/tasks.py:158`: una prenotazione scaduta (> 120 s, mai azzerata: `clear_reservation` non ha chiamanti in `bin/`) conta come preferenza. Un lancio prenota sempre il proprio task (`agents.py:102`), quindi il caso normale è corretto; lo scenario residuo è un `SubagentStart` senza `PreToolUse` mentre un altro task ha una prenotazione vecchia (prima si legava al numero più basso, ora al prenotato vecchio: sbagliato in entrambi i casi, non peggiore). Possibile rafforzamento: ignorare nell'ordinamento le prenotazioni oltre `RESERVATION_S`. Non richiesto dalla decisione 5.
2. `tests/test_tasks.py`: nessun test per `take_pending(..., number=N)` insieme a una prenotazione su un altro task (il WHERE su `number` prevale: oggi corretto ma non protetto).
3. `tests/test_init.py`: nessun caso esplicito «valore del frammento uguale al predefinito, nessuna riga» a livello di test nuovo (coperto indirettamente da `test_real_precedence_p39`, backend L0).
4. `tests/test_init.py:677-678`: la riga di `DECLARED_X` supera la lunghezza usata nel file (cosmetico).

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni del controller (4, 5, D1, D14) implementati alla lettera, nessuna riga proposta o riscritta a torto nel `tollgate.toml` dell'utente e `take_pending` lega il task giusto per i chiamanti di `apply._subagent_start`; i test asseriscono comportamento reale e nessuna asserzione esistente è indebolita.
