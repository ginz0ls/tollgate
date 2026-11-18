# Report del giro di correzione finale di B7

## I1 (e voce 2, M3)
- RED: `tests.test_bash` con il nuovo `test_launcher_double_dash_before_service_args`: 10 fallimenti (le otto forme `npm exec prisma -- ...` ecc. passavano; `npm exec supabase -- start` chiedeva con motivo `supabase start`; `launcher_candidates` restituiva `['prisma', '--', 'migrate']`).
- GREEN: `bin/tollgate_analysis/bash.py` `launcher_candidates` toglie il primo `--` da `argv[i+1:]`. `python3 -B -m unittest tests.test_bash`: 111 OK. Nessun test esistente cambiato; `supabase -- db push` senza lanciatore chiede ancora (asserito nel nuovo test).

## Minori
- 7: docstring di `_concrete_paths` (`bin/tollgate_flow/init.py`) a righe sotto i 100.
- 9: `tests/test_rules_database.py` riga spezzata.
- 10: `test_real_precedence_q46` con due `subTest` (`tests/test_init.py`).
- 21: `spikes/run-b1-flow.sh`, variabile `SLICES=1` nel caso `database`, usata in `approve spec` (prompt, elenco passi, passo2). `bash -n` ok; i test di `tests/test_b1_scripts.py` verdi (già citano `approve spec 1`).
- 23: tolta `STEPS`.
- 25: tolta la riga vuota in più in `tests/test_b1_scripts.py`.
- 34: rapporto prova riga 42: «9 eventi `spec_audit_round`, 5 della spec e 4 del piano».
- Rinvii: nel piano principale, blocco «A B8, da B7», quattro voci nuove (M1, M2, M3, «da verificare» su `db query`/`db advisors`); la voce M3 dei minori del Task 1 aggiornata (ora passa `npm exec supabase -- start`). Spec del nucleo 8.5: `--local` non conta se è il valore «di un'opzione globale».

## Test
Mirati (`test_bash`, `test_init`, `test_rules_database`, `test_b1_scripts`): 528 OK. Suite completa: vedi in fondo.

## Dubbi
Le voci «Dai minori del ledger, Task 2-6/7» del piano citano ancora come aperti `init.py:254`, Q46, `STEPS`, `approve spec $ISSUE`: ora corretti, testo storico non riscritto.

Suite completa: `tests/run` con python3.11 e python3, 4062 test, exit 0 (skipped 13 e 11), nessun «unclosed». Log: suite-final-fix.log.

## Fix round 2 (solo documenti)
- Spec del nucleo 8.5: la frase sul lanciatore dice che `launcher_candidates` toglie il primo `--` dal candidato (I1), così `npm exec prisma -- migrate deploy` chiede e `npm exec supabase -- start` passa; il resto di D2 resta.
- Piano principale: voci «Dai minori del ledger» chiuse con «(chiusa nel giro finale di B7, 5c0138f)»: `init.py:254`, riga di `test_rules_database.py`, Q46, `approve spec $ISSUE`, `STEPS`, riga vuota doppia, «5 giri» del rapporto. Nuova voce in «A B8, da B7» sul doppio `--`.
- Test: `python3 -B -m unittest tests.test_docs` 7 OK; suite completa `exit 0` (4062 test, skipped 13 e 11, nessun «unclosed"), log `suite-final-fix2.log`.
