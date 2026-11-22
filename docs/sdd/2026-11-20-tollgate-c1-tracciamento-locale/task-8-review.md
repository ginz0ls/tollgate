# Revisione Task 8: la fotografia per il gestionale (415ad58..43720fd)

Letto il pacchetto di revisione; eseguiti, su una copia `git archive 43720fd` in una cartella `tollgate-*` con `HOME` e `TOLLGATE_STATE` temporanei (cancellata), `tests.test_turn tests.test_snapshot tests.test_docs` (24 OK) e `snapshot` senza DB (JSON vuoto, nessun file di stato creato).

### Aderenza
- ✅ Chiavi per lavoro: `snapshot.py:_work` produce esattamente le 19 chiavi della decisione 8; `test_snapshot_shape` le confronta con l'insieme esatto (`tests/test_snapshot.py:15-18, 70`). Busta `{"v","at","host","works"}` verificata.
- ✅ `turn`: `turn.py` implementa `decision` se `waiting` non è vuoto, `user` per `pr_open`/`approval`, `agent` altrimenti; `waiting_user = len(waiting) + 1 se user` (`snapshot.py:_work`). `spec_audit` conta `agent` come da decisione 8.
- ✅ `waiting`: blocchi aperti (`closed IS NULL`), effetti `action='effect' AND state='requested'` con id da `data.id` (gli intenti `pr`/`sync` esclusi, testato), domande con la regola esatta della decisione 4: nessuna `stop_answered` con lo stesso `tool_use_id` (su tutto il DB), ultima `stop_asked` della sessione, nessun `act`/`session_start` dello stesso lavoro dopo, `tool_use_id` nullo mai in attesa (`snapshot.py:_questions`). Test per tutti i casi del brief, più `act` di un altro lavoro e id nullo.
- ✅ `cost`: ultimo `cost` per agente (seq più alto), somma e `by_task` per numero; costo senza task conta solo nel totale; chiavi intere in Python, stringhe nel JSON (documentato).
- ✅ D15: il ramo senza DB sta prima di `db.open_db`, accanto a `status` (`cli.py:515-520` nel diff), stampa la forma vuota e non crea niente (verificato anche da processo: `test_snapshot_cli_process`, e da me).
- ✅ Nessun testo libero né dati della macchina: nessuna colonna `worktree`, `reason`, `what`, `question` letta; `branch` è l'unica eccezione ammessa e la pagina la dichiara. `host` è l'unico dato di macchina. Il test controlla sia il valore (`segreto-di-prova`) sia le chiavi.
- ✅ Lavoro pre-C1: `size`/`size_by`/`slices` nulli passano senza errori (`test_snapshot_pre_c1_work`); chiusi esclusi (`test_snapshot_skips_closed`).
- ✅ Test indipendenti dalla macchina: `socket.gethostname` è sostituito con `macchina-prova` (`test_cli_snapshot_without_db`); `HOST` fisso negli altri; il test di processo non asserisce `host`. Nessuna dipendenza silenziosa da variabili d'ambiente (solo `TOLLGATE_STATE` impostato in modo esplicito).
- ✅ Pagina `gestionale.md`: nessun percorso locale (grep di `/home`, `MEGA`: vuoto); D7 (migrazione con copia in `backup/`), D13 e D14 (reopen plan, slices, chiavi stringa, C4/C5, vertical senza `paths`), costo non include la sessione principale, `cost` cumulativo, regola dell'attesa con i suoi limiti, archivio `events_days`. `test_docs_exist` riceve `gestionale`; `comandi.md` ha la voce e il collegamento.
- ✅ Strati: `turn.py` in `tollgate_analysis` non importa niente di tollgate; `snapshot.py` in `tollgate_core` importa solo `tollgate_analysis` e moduli di core; `cli.py` è l'unico che lo usa.
- ⚠️ Misura: i numeri (83 eventi/27787 byte, 335 B/evento; scan 1002/334672) sono coerenti tra loro (27787/83 = 334,8; 334672/1002 = 334) e coincidono con il brief per la scan; che la misura sia stata fatta solo da copie e che la cartella sia stata cancellata si legge solo dal report e dal testo della pagina, non dal diff. Non ho rifatto la misura.

### Punti di forza
- Funzione pura `waiting_on` isolata nello strato di analisi; `snapshot.py` solo SELECT, una responsabilità.
- Test della regola dell'attesa tabellare e completa (le quattro varianti del brief + altro lavoro + id nullo), controllo dei chiavi oltre che dei valori per il testo libero.
- Il report dichiara onestamente gli scostamenti sulla regola (ultima domanda su tutti gli `stop_asked` della sessione, `stop_answered` su tutto il DB): coerenti con la decisione 4 («l'ultima `stop_asked` della sua sessione»).

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `snapshot.py:_questions` rilegge tutte le `stop_answered` del DB a ogni lavoro (`answered` è ricalcolato per lavoro): costo O(lavori x risposte) e una query `later_ask`/`closed` per domanda. Con lavori e archivi piccoli non pesa; se serve, calcolare `answered` una volta in `build` e passarlo.
2. `snapshot.py:_cost`/`_work`: con `[retention] events_days > 0` gli eventi vecchi escono dal DB, quindi `cost.tokens`, `by_task` e `last_event_at` di un lavoro lungo possono scendere o diventare nulli. La pagina dice solo che il gestionale legge più spesso del limite; non avverte che la fotografia dipende dagli eventi ancora presenti. Una riga nei «Limiti noti».
3. `docs/uso/gestionale.md` (sezione «Quanto occupano gli eventi»): la provenienza dice «evidenze degli eval di B8» ma non il percorso relativo (`docs/verifiche/evidenze/eval-b8/`), né quali tre stati né lo schema 6. Aggiungere il percorso relativo (non è un percorso locale) rende la misura ripetibile.
4. `cli.py`: `socket.gethostname()` è chiamato in due rami e il ramo senza DB ricostruisce a mano la busta; piccola duplicazione, accettabile (il brief la prescrive per D15).

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni 3, 4, 7, 8, 9 (D7, D13-D15, D17) rispettati e testati; nessun testo libero né percorso nella fotografia e nella pagina, test indipendenti dalla macchina; restano solo rifiniture minori e la misura da confermare dal controller.
