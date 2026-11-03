### Verdetti sui rilievi
1. **Frammento senza `paths` o con `paths = []` deve essere FragmentError col nome del file**: INDIRIZZATO. `bin/tollgate_core/fragments.py:60-62` (`if not paths: raise FragmentError(f"{name}: ...")`), dopo la validazione di forma, quindi nessun percorso porta a `paths` vuoto. Test `test_load_rejects_missing_or_empty_paths` (assente, vuoto, file vuoto) verifica anche il nome del file; `test_load_without_detect_is_empty_tuple` aggiornato con `paths`. `python3 -B -m unittest tests.test_fragments`: 14 OK.
2. **Pattern `**/<cartella>/**` con cartella `.` o `..` deve essere FragmentError**: INDIRIZZATO. `fragments.py:15`, lookahead `(?!\.{1,2}/)` dopo `**/`; `**/./**` e `**/../**` non fanno fullmatch. Nomi come `.github` o `...` restano ammessi (il lookahead richiede il `/` subito dopo i punti). Test `test_load_rejects_dot_folders`.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
