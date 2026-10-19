# Revisione Task 12 (7240ba8..f3829e0)

### Aderenza
- ✅ `bind_session` / `set_level` su lavoro `closed`: `TransitionError("il lavoro è chiuso")` dentro la transazione (phases.py, bind_session e set_level). Chiamanti verificati: `tollgate_hooks/apply.py:17,75` (runner.py:290 cattura `TransitionError` e avvisa), `tollgate_flow/start.py:182` (`steps.run`; start.py:52 cattura `TransitionError`). I test di start usano lavori aperti.
- ✅ `verify._run_one`: `finally` con `os.killpg` soppresso su `ProcessLookupError`. stdout va su file (nessuna pipe), quindi `communicate` non resta bloccato da figli in background.
- ✅ `waiver_hint(v)` / `explain(violations)` senza `issue`; chiamanti `commit.py:42`, `post_bash.py:62`, `writes.py:84`; il grep in bin/ e tests/ non trova altri usi.
- ✅ Messaggio `rm -rf` (bash_rules.py, `_rm_rf`) con la frase di carry C15; il test asserisce la frase e che non compaia «rm -r senza». Lo scostamento dal piano è corretto (C15 prevale).
- ✅ Tre test nuovi; il report dichiara RED/GREEN su entrambi gli interpreti. ⚠️ Non rilanciati da me.

### Punti di forza
- Modifica minima e chirurgica. Il test del killpg uccide solo il PID che ha avviato; il test su closed verifica anche che sessions e level restino invariati.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `bin/tollgate_core/verify.py` (`finally` dopo `except TimeoutExpired`): nel ramo timeout il gruppo viene ucciso due volte, la seconda dopo `proc.wait()`. Innocuo (ProcessLookupError soppresso), ma resta una finestra teorica di riuso del pgid dopo il reap; `PermissionError` non è soppresso (solo teorico). Si può uccidere solo nel `finally` e fare `proc.wait()` dopo.
2. `tests/test_verify.py` (`test_background_child_killed_after_success`): `time.sleep(0.3)` fisso; se il figlio orfano restasse zombie in attesa di init, `os.kill(pid, 0)` riuscirebbe e il test fallirebbe a torto. Un breve poll con timeout sarebbe più robusto.
3. Scostamenti dal piano (`ClosedWorkTest` inesistente, frase di `rm -rf`): dichiarati e giustificati.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** Requisiti e decisione C15 rispettati, chiamanti dei contratti modificati verificati, test mirati; solo rifiniture minori.
