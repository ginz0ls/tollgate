# Report Task 7

Status: DONE_WITH_CONCERNS

Fatto:
- `spikes/run-b1-flow.sh`: caso `database` (OUT b7/flusso, progetto spikes/b7/flow, spec e piano in spikes/b7/input, piano controllato con level L2 e spec con una fetta), passo1..passo6 e `libero` (cartelle libero-N), `rot` e `registra` su tutti i passi, DISALLOWED con psql, postgres, pg_ctl, pg_dump, prisma, drizzle-kit, limiti, `controlla`. Variabili PROPOSE e SERVICES al posto delle catene di `||`.
- `spikes/b1/flowreg.py`: titolo `# Regole database (versione 1)`.
- `tests/test_b1_scripts.py`: i test del brief, la Ruling sul caso backend (blocco `database`), `database_approved` in `src_repo`, tolto il confronto con `spikes/b1/flow` dal test del frontend.
- Suite: exit 0, 4053 test su python3.11 e python3 (log suite-task-7.log).

Dubbi:
- Ho scritto il codice prima dei test (niente RED separato); il test del piano L2 non valido prova comunque il rifiuto.
- `--allowedTools` è rimasto uguale ai casi esistenti: non ho trovato nulla da aggiungere per gli atti.
- passo1 mette l'istruzione di Write dopo `/tollgate:start #1 L2` nello stesso prompt (decisione 16): da verificare dal vivo che start non confonda il testo con gli argomenti.
- passo5 usa `/tollgate:execute` seguito da una riga di istruzioni.

## Fix round 1

Causa: in L2 `verify` senza rapporto e` `uncounted`, i test dei must-have non si contano.
- `spikes/b7/flow/tools/unittest_junit.py` (copia dello script di P3c), `tollgate.toml` con `verify = "python3 tools/unittest_junit.py"` e `report = "junit:reports/junit.xml"`; `.gitignore` aveva gia` `reports/`.
- `PROJ_FILES` del caso `database` include il file; la spec vieta di modificarlo.
- Test: `test_real_flow_case_database_project_verifies` (copia temporanea, controlla `reports/junit.xml` con `classname::name`), nuovo `test_real_flow_case_database_project_declares_junit_report`. RED visto prima del codice.
- Mirati `tests.test_b1_scripts`: 133 test, python3 e python3.11, verdi tranne `test_committed_evidence_has_no_long_web_results`.
- Suite (suite-task-7-fix1.log), rilanciata dopo che il controller ha spostato fuori dal repo le evidenze grezze: exit 0, 4054 test su python3.11 e python3. Il rosso precedente (`test_committed_evidence_has_no_long_web_results`) veniva da quelle evidenze, non dal codice.
- Commit: 048173e (nessuna modifica nuova da committare dopo la suite verde).
