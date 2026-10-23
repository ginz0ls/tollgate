# Task 15 — giro di correzione 1

Leggi W/task-15-review.md. Correggi, ogni volta prima il test RED:

- **I-1** Ripristina `test_options_exist_in_parser` in `tests/test_skill_contract.py`. Le opzioni citate nelle skill si verificano contro `tollgate_core.cli.build_parser()` e, per i sottocomandi `gate`, contro `tollgate_gate.cli.build_parser()` (D18a).
- **M-2** Nella skill `finish` le voci «da leggere» e «informative» coincidono con `tollgate_gate.attention.GROUPS`: oggi «PR non `tg/*`» sta nel gruppo sbagliato. Un test confronta la skill con `GROUPS`.
- **M-3** La skill `init` e il README generato da `bin/tollgate_flow/init.py` dicono che i servizi entrano in ogni job che esegue la suite (`install.SERVICES_WORKFLOWS`), non solo in `head`.
- **M-4** Estrai il controllo D18a in una funzione usata sia dal test reale sia da quello sintetico, con un caso valido e uno inventato. Il ramo `gate` deve essere esercitato davvero.

Non toccare `spikes/` né i file del Task 16. Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Se va oltre il timeout, aspetta in primo piano sul file di uscita con un ciclo `until`: non restare fermo in attesa di notifiche. Deve essere verde su python3.11 e python3, poi committa con «(Task 15, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-15-report.md la sezione «Fix round 1».
