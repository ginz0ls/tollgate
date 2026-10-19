# Task 11 - ri-revisione giro 1 (fc23d3f..7240ba8)

### Verdetti sui rilievi

1. **(Important) session_id con newline poteva spezzare l'output e forgiare la percentuale**: INDIRIZZATO.
   `statusline/ctx` ramo Python: `re.fullmatch(r"[A-Za-z0-9_-]+", sid)` (altrimenti `sys.exit(0)`, nessun output), una sola riga `print(sid, pct)`, poi `[ -n "$parsed" ] || return 0`. Il ramo sed scarta comunque ogni id con caratteri fuori whitelist (`case` finale). Prova mirata (stato e HOME temporanei, sentinella `.tollgate-test`, ramo Python e ramo con PATH ridotto senza python3): `"a\nb"` e `"a\n77\n"` non creano alcun file; il comando avvolto gira. Test: `test_unsafe_session_ignored` esteso con i due casi.
2. **(Minor) percentuale solo 0-100**: INDIRIZZATO.
   Prova mirata, entrambi i rami: `1e+20`, `NaN`, `-1` danno `{"used_pct": null}`; `100` resta 100 (sed: `100.0` resta valido); `0099` nel ramo sed diventa null (non e' JSON valido, accettabile). Test: `test_null_when_out_of_range` (-1, 100.5, 1e20, 1000, 1e+20 testuale, 100) e, per sed, `test_without_python_uses_sed`.
3. **(Minor) test automatico del ramo senza Python**: INDIRIZZATO.
   `tests/test_statusline.py` `test_without_python_uses_sed`: PATH ridotto a symlink di bash/sh/cat/sed/tr/mkdir/mv/rm/printf (nessun python3), verifica valori 33.5, 100, null, 150, -3, `1e+20`, id con newline e l'elenco esatto dei file scritti. Copre davvero il ramo `else`.

### Danni nuovi nel diff della correzione

Nessuno. Note di rango Minor non bloccanti, solo su input non JSON valido nel ramo sed: `5.` viene scritto come `{"used_pct": 5.}` (JSON non valido nel file) e un newline grezzo dentro il `session_id` viene rimosso da `tr -d '\n'`, quindi `a<LF>b` diventerebbe `ab` (id comunque whitelisted, nessuna forgiatura di percentuale). Input reali della statusline sono JSON valido, quindi non raggiungibili in pratica.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
