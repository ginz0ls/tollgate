# Revisione Task 5: comando `ruling add` (7d121f5..53b309c)

### Aderenza
- ✅ Tre campi `cosa:`/`perché:`/`perche:`/`costo:` (senza maiuscole, D20), obbligatori, non vuoti, max 1000 con rifiuto (non taglio): `ruling_cmd.py:225-263,290-293`. Campo ripetuto o mancante: rifiuto.
- ✅ stdin letto a `4*3*RULING_TEXT_MAX+1` (`cli.py` nuovo blocco `ruling`); righe su stdout con 0, su stderr con 2; `--by` con `choices`.
- ✅ Lavoro trovato dalla cartella; senza lavoro o task inesistente codice 2; DB chiuso nel `finally`; evento `ruling` con `data == {what, why, cost, by, task}` e `work` (`ruling_cmd.py:308`); riga `ruling registrata (evento <seq>)`.
- ✅ D4: `_ruling_by_user` (`cli_calls.py:88-98`) nega `--by user`, `--by=user`, `--b user` solo nel ramo subagente, dopo `_coordinator_only`; `--by agent`/senza `--by` passano; il ramo della sessione principale non cambia. Nessun comando del coordinatore diventa permesso: il `continue` finale è invariato e il nuovo `if` può solo aggiungere un diniego.
- ✅ Il subagente può registrare una ruling (test `test_subagent_may_add_ruling`, `test_subagent_may_register_its_own_ruling`); il heredoc quotato non tocca `bash.parse`.
- ✅ D17 (messaggi senza programma nudo), D20 (avviso `TOLLGATE_…=` in brief e skill), brief con `ruling add`, `--task`, `RULING_FINE`; `taskcmd` riempie il campo come `verify_cmd`; skill `execute` e `docs/uso/comandi.md` aggiornati. Strati rispettati (`brief.py` non importa il nucleo; `ruling_cmd` importa solo core; import di `cli.py` lazy).
- ⚠️ Non ho rilanciato la suite (4266 test dichiarati verdi su 3.11 e 3.13). `TOLLGATE_…=` dentro un heredoc negato da `bash_rules`: non verificato.
- ⚠️ Nessun RED registrato (dichiarato): vedi M2.

### Punti di forza
- Copre le abbreviazioni argparse di `--by` (`--b`), cosa che il piano non chiedeva e che sarebbe stata un bypass di D4.
- Il corpo di prova di D11 ha apostrofi, `$`, backtick, `task`, `review`, `start` ed è eseguito davvero dall'hook (`Lab.bash`).
- Test di `parse_text`, limiti (1000 accettato, 1001 rifiutato), nessun evento dopo i rifiuti, task inesistente, `cwd` fuori dai lavori.

### Rilievi

**Important**
- I1. `bin/tollgate_flow/ruling_cmd.py:249-255`: dopo un testo prima del primo campo si imposta `current = ""`; se quel testo ha una seconda riga non vuota prima di `cosa:`, la riga entra nel ramo `elif current is not None` e fa `parts[""].append(...)` con la chiave assente: `KeyError('')` (riprodotto su copia esportata di 53b309c con `"intro\naltra riga\ncosa: a\nperché: p\ncosto: c"`). Via CLI è un traceback con uscita 1 invece di un rifiuto con uscita 2 e il messaggio; il requisito «testo prima del primo campo = rifiuto» è violato per un testo di più righe. Il test (`test_missing_repeated_or_leading_text_are_problems`) prova una sola riga iniziale (`chi: x`), quindi non lo vede. Correzione: usare un flag `preamble_seen` e lasciare `current = None` (ignorando le righe successive), oppure `if current:` come condizione di accumulo; aggiungere il caso a più righe nel test.

**Minor**
- M1. `tests/test_check_cli_calls.py:528-532`: il controllo negativo di D11 è più debole del richiesto: la docstring dice «lo stesso corpo», ma il comando è solo `task start 1` senza il heredoc con il corpo, e controlla il testo di stderr ma non `rule == coordinator_only`. Un `task start 1 <<'RULING_FINE'` + corpo sarebbe la prova che il heredoc non maschera un comando vero.
- M2. Nessun RED: i test sono stati scritti dopo. Per il resto affermano comportamento reale (valori esatti dell'evento, codici, stderr), ma il caso I1 mostra che il codice-prima ha lasciato un buco nei casi limite.
- M3. `cli_calls.py:95`: `name != "-"` è ridondante con `len(name) >= 3`.
- M4. Etichette con «é» in forma NFD (e + accento combinante) non sono riconosciute: rifiuto con «manca il campo», non una perdita di dati.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** requisiti, D4/D11/D17/D20 e strati rispettati, nessun comando del coordinatore diventa permesso e nessuna ruling viene tagliata; ma `parse_text` va in `KeyError` su un testo iniziale di più righe (I1), un caso limite esplicito del brief che produce un traceback invece di un rifiuto. Correzione di due righe più un test.
