### Verdetti sui rilievi
1. **I1: testo su più righe prima del primo campo dava `KeyError('')` (uscita 1) invece di rifiuto con uscita 2.** INDIRIZZATO. `bin/tollgate_flow/ruling_cmd.py:249-255` (nel diff: flag `leading`, `current` resta `None`, un solo avviso). Test a più righe: `tests/test_ruling_cmd.py` (caso `"intro\naltra riga\ncosa: a..."`) e `tests/test_cli.py` `test_cli_ruling_multiline_text_before_the_first_field` (uscita 2, stdout vuoto, niente Traceback, messaggio, nessun evento). Rieseguiti su `git archive d455093` in cartella temporanea (poi cancellata): `test_ruling_cmd`, `test_check_cli_calls`, `test_cli.RulingCliTest` = 47 test OK.
2. **M1 (D11): il controllo negativo deve usare lo stesso corpo con `task start 1`, e verificare `rule == "coordinator_only"`.** INDIRIZZATO. `tests/test_check_cli_calls.py:528-532`: usa `self.command(head=...)` con lo stesso `BODY` (apostrofi, `$`, backtick, `task`, `review`), testa `task start 1 <<'RULING_FINE'`, uscita 2, `[e["rule"] for e in veto] == ["coordinator_only"]`, messaggio «comando del coordinatore».

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minor: `tests/test_ruling_cmd.py` il caso nuovo è inserito in una riga lunga (oltre ~100 colonne), solo stilistico.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
