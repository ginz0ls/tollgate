# Revisione Task 10 (461c4f3..0f648ba)

### Aderenza
- ✅ `next_step` in L2 per `spec_audit`/`plan`/`approval` usa `audit.peek` senza duplicarne la logica (`checkpoint.py` riga ~123); il testo «arriva con P3c» è tolto; L1 in `plan` invariato.
- ✅ `CAPS` con i tre prefissi di `audits.CAP_REASONS` e `DECLINE_REASON`, non in `CAP_PREFIXES` (D20).
- ✅ D19: `_cap_step` usa `audits.cap_kind` e stampa `audit.STEPS["resolve"]` con `<id>` sostituito; controllato in `audits.cap_kind` che il rifiuto del costo valga `spec-lens`.
- ✅ D18f: `post_edit.py` punta a `/tollgate:spec-audit`; test con `assertIn`/`assertNotIn` in `tests/test_check_post_edit.py`.
- ✅ D10: il vecchio controllo «P3c» su lavoro L1 è tolto e sostituito da `CheckpointL2Case` su `FlowLab(level="L2")` (committa `tollgate.toml` nella base). Non è una riscrittura in loco delle righe 89-100, ma la copertura equivale.
- ✅ Programma: `peek` usa `_prog()`; il test `test_steps_use_program_command` verifica il comando nudo escluso.
- ✅ `python3 -B -m unittest tests.test_checkpoint`: 23 OK (rilanciato).
- ⚠️ `tests/run` su 3.11 e 3.13 (1670 OK) non verificato da me, come da regole.

### Valutazione del caso segnalato (plan L2 senza spec registrata)
Sensato. `_decide_plan` (`audit.py:354-355`) rifiuta con «/tollgate:reopen spec» e `peek` passa per `_Refuse.hint()` (`audit.py:94-95`), che restituisce il messaggio quando non c'è `step`. È lo stesso rifiuto di `prepare` (decisione 3, ramo `plan`) e l'unico rimedio reale: una spec non registrata in fase `plan` è uno stato anomalo (adopt o riapertura), e `reopen spec` riporta a `spec_audit` dove la spec si adotta. `status` e `prepare` danno così lo stesso passo. Resta una frase senza prefisso «lancia», ma è un comando per l'utente, coerente con gli altri `STEPS`.

### Punti di forza
- Nessuna logica duplicata; `peek` non solleva eccezioni dei suoi `ERRORS` e ha il fallback «lancia <programma> audit prepare».
- Test sulle ragioni reali (`audits.cap_reason`) e non su stringhe copiate; il test D19 cicla tre blocchi e li chiude uno a uno.
- Ordine in `_cap_step`: il blocco audit viene riconosciuto prima di `CAP_PREFIXES`, senza regressioni sui tetti vecchi.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `tests/test_checkpoint.py` (dopo `if __name__ == "__main__": unittest.main()`, in coda): `CheckpointL2Case` è definita dopo il blocco di avvio, quindi `python3 tests/test_checkpoint.py` non la esegue (discover e `-m unittest` sì). Spostare il blocco `__main__` in fondo.
2. `peek` in `plan` con `act.kind` diverso da approve (reprint/open/confirm) restituisce il generico «lancia audit prepare»: corretto, ma con `NEEDS_CONFIRM` non dice che serve la conferma; accettabile perché `prepare` lo spiega.
3. `peek` cattura solo `ERRORS`: un `UnicodeDecodeError` da `git.text_at` su piano non UTF-8 non è coperto (verificare se `text_at` decodifica con `errors="replace"`); rischio basso, il «mai un'eccezione» della D20 vale per `ConfigError`, `GitError` e worktree assente, tutti coperti.
4. Due voci `CAPS` danno lo stesso nome «audit a lenti»: voluto, ma `test_audit_caps_in_stopped_by` lo asserisce solo per l'ordine di inserimento.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** i requisiti di D10, D18f, D19, D20 sono soddisfatti senza duplicazioni e con test sul comportamento reale; restano solo rifiniture minori (blocco `__main__` a metà file).
