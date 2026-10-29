# Ri-revisione Task 3, giro di correzione 1 (c4fb8dd..b8c28de)

### Verdetti sui rilievi

1. **(Important) `parse_note` quadratica / nessun cortocircuito oltre il tetto**: INDIRIZZATO. research.py (`parse_note`) ritorna subito con il solo problema di lunghezza oltre `MAX_NOTE_CHARS`. Separatore e intestazione senza regex (`str.find`, `startswith`); `_BULLET` resta una regex ma ancorata e lineare su riga già `strip()`. Test: `test_parse_note_too_long_not_analyzed` (100.000 spazi, < 0,5 s), `test_parse_note_long_line_under_cap_is_fast` (7.900 spazi, ` -` ripetuto, ` — ` ripetuto, in entrambe le sezioni e nell'intestazione). Provato: riga con 7.900 spazi in 0,0 s; `tests.test_research` 34 OK.
2. **(Minor) `--color`/`--colour` come opzioni con argomento**: INDIRIZZATO. bash.py `_READ_OPT_ARG["grep"]` senza le due voci; test aggiunti in `ReadTargetsTest` (`grep --color foo f` → `["f"]`, `--colour=auto`).
3. **(Minor) `approved: null/~/|/""`**: INDIRIZZATO. research.py `_YAML_EMPTY` + `enforced`; `test_enforced_not_a_real_value` (null, ~, |, >, |-, "", '', false, commento). `false` non esclude le date: provato `approved: 2026-11-02 # ok` → vero; test con data tra apici → vero.
4. **(Minor) `docs/A - B.md` troncato**: INDIRIZZATO. `_item(line, (_SEP_LONG,))` per i file, `_SEP_ANY` per le fonti; `test_parse_note_file_with_dash_in_name` (`docs/A - B.md` intero, `c.py — descrizione - con trattino` → `c.py`). Le fonti con ` - ` e ` — ` provate a mano: entrambe riconosciute.

Casi `test_parse_note_*` (too_long, never_raises, valid, ecc.) ancora verdi.

### Danni nuovi nel diff della correzione
- **Minor** research.py (`_SEP_LONG`/`_SEP_ANY`, `_split_description`): i separatori sono ora la stringa esatta con un solo spazio per lato; il vecchio `[ \t]+` accettava anche tab e spazi multipli. Spazi multipli: ok (il riferimento viene `strip()`ato). Tab: `- a\t—\tb` ora dà il file `a\t—\tb` (provato). Raro, fallisce in modo sicuro (file «non letto»).

### Osservazioni fuori ambito
- `approved: no` / `off` contano come approvato (non richiesto dai rilievi).

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
