# Revisione Task 14, giro di correzione 1 (f73c191..7485480)

## Aderenza
- ✅ set_config idempotente (`bin/tollgate_flow/gitw.py:116-121`): `--get-all` e confronto con `[value]`. Chiave assente (rc 1) scrive; valore uguale unico non scrive; valore diverso scrive; valori multipli (anche duplicati) scrivono e git rifiuta come prima. Unico chiamante `start.py:404`, la semantica del rifiuto resta. Gli errori di `_run` (git assente, timeout) continuano a salire come `GitWriteError`. Letture di `tollgate.defaultBranch` in `tollgate_core/git.py:143,157` usano `--get`, coerenti.
- ✅ Test (a): `tests/test_start.py` SetConfigTest con `config.lock` preesistente (mkdir) prova l'assenza di scrittura; `test_locked_config_still_fails_when_the_value_changes` prova che il lock blocca davvero una scrittura vera (quindi il test (a) non è vacuo). Eseguiti: SetConfigTest 4 OK, `test_git_config_failure_refuses` OK, `test_locked_config_with_the_value_already_set_does_not_refuse` OK.
- ✅ `test_git_config_failure_refuses` (test_start.py:~511): toglie la chiave prima del lock, quindi la scrittura è necessaria e il rifiuto è ancora provato.
- ✅ s5 prompt: richiesta Write per file e commit alla fine (`evals/s5-l0-cresce/case.yaml`), coerente con le prove a secco esistenti (4º Write negato, `test_eval_cases.py:1008`), che restano cammini corretti >= 0,75 via `assertCorrectPath`.
- ✅ Grader `crescita-vista`: l'alternativa `il diff supera le soglie di L0` è il testo di `_common.py:285`. Verificato nelle evidenze reali: la stringa compare nelle trace di 1507oB, EtlASM e fqwZp0 (messaggio finale dell'agente, "il diff supera le soglie di L0"). Nessuna regola JS vietata. Non banale: la stringa non è nel prompt e il cammino sbagliato la fa comparire solo se l'agente cita l'avviso; vale 1/4 = 0,25 < soglia 0,66 (test `...reported_in_the_final_message_is_seen_but_does_not_pass_alone`). Ruling del controller rispettata.
- ✅ Cammino sbagliato (comando unico file+commit): `test_eval_cases.py:1029-1037` nessun deny, grader a 0, `assertWrongPath(out, set())` (< soglia). Il test usa `printf >` e non un heredoc: equivalente ai fini del PreToolUse.
- ✅ Docs: `docs/uso/limiti.md` due frasi aggiunte nei paragrafi esistenti, nessun titolo in grassetto nuovo; `tests.test_docs` 6 OK. Frasi esatte rispetto al codice (commit.py guarda il working tree prima del comando).

## Punti di forza
TDD documentato con RED reale; test del lock che prova la non-scrittura in modo osservabile; il test esistente è stato adattato invece di indebolito; docstring che spiega il perché.

## Rilievi
Critical: nessuno.
Important: nessuno.
Minor (3):
1. `bin/tollgate_flow/gitw.py:118`: `--get-all` legge anche i livelli global/system. Se `tollgate.defaultBranch` è uguale solo in `~/.gitconfig`, la chiave non viene più scritta nel repo (prima sì). Effetto pratico nullo (i lettori usano `--get` con la stessa unione), ma passare `--local` renderebbe la semantica identica a prima. Con `--local` la sandbox resta coperta.
2. `tests/test_start.py:~76-77`: il primo `set_config(..., "main")` nel test (a) è ridondante (FlowLab imposta già main) e la seconda scrittura non asserisce nulla in più del valore; innocuo.
3. `tests/test_eval_cases.py:1029`: docstring e nome parlano di heredoc, il test usa `printf`; solo nomenclatura.

## Valutazione
**Qualità del task:** Approvato. **Motivo:** correzione di prodotto corretta e provata in modo non vacuo, caso s5 coerente tra prompt, grader e prove a secco (cammino sbagliato 0, cammini giusti >= 0,75); solo rifiniture minori.
