# Report Task 2 (rinvii piccoli di B6)

## Implementato
- `spikes/b1/flowreg.py:32`: il lookahead di `SAVED_PATH` ammette anche `, } ] : \` dopo `tool-results` (oltre a spazi, apici, `|;&<>()` e fine stringa).
- `bin/tollgate_flow/init.py` `_concrete_paths`: un percorso esatto (`name`) non si tiene se un `**/*.<ext>` proposto dello stesso frammento lo copre (D10: la correzione c'e', nessun caso reale cambia).
- `bin/tollgate_core/fragments.py` `_parse`: f-string spezzata in una stringa unica senza placeholder inutili; messaggio identico.
- Test: `test_togli_pagine_bash_folder_followed_by_punctuation`, `..._lookahead_negatives`, `..._stdout_and_stderr`, `test_togli_pagine_bash_any_reader` esteso (cat, awk, cp si aggiungono a `<`, python3 -c, jq gia' presenti), `test_name_path_dropped_when_ext_covers`, `test_parse_error_message`.

## RED
Comando: flowreg.py ripristinato alla BASE, poi `python3 -B -m unittest tests.test_b1_scripts tests.test_init tests.test_fragments`.
```
FAIL: test_togli_pagine_bash_folder_followed_by_punctuation ... [ls {/x/tool-results,/y}]
FAIL: ... [echo ${D:-/x/tool-results}]
FAIL: ... [ls [/x/tool-results]]
FAIL: ... [ls /x/tool-results:/y]
FAIL: ... [ls /x/tool-results\]
FAIL: test_name_path_dropped_when_ext_covers (tests.test_init.ProfileBlocksTest)
Ran 326 tests in 473.159s
FAILED (failures=6)
```
Gli altri nuovi test (negativi, stdout+stderr, any_reader esteso, parse_error_message) passano gia' prima: documentano comportamento che deve restare.

## GREEN
- `python3 -B -m unittest -k togli_pagine -k third_party tests.test_b1_scripts`: Ran 15, OK.
- `python3 -B -m unittest tests.test_fragments tests.test_init`: Ran 213 tests, OK.
- `bash -n spikes/run-b1-flow.sh`: ok.
- Suite completa: vedi `suite-task-2.log`.

## Scostamenti
Nessuno. Il test del piano `test_name_path_dropped_when_ext_covers` usa `paths_of` con frammento scritto nel test.

## Autorevisione
Completo rispetto a brief e D10; nessun file fuori elenco; nessun `__pycache__`; nessuna rete ne' programmi di servizio.

## Dubbi
Nessuno.

## Suite
`PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 Ran 3918 OK (skipped=13); python3.13 Ran 3918 OK (skipped=11); `exit 0`. Commit fatto dopo.
