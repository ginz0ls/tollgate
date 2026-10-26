# Giro di correzioni finale — report
Commit: vedi git log (tollgate P5: correzioni della revisione finale).
1. F1/T1: test_p5_scripts.py:951 ora con `with open`.
2. F2/F4/T5: piano principale, «Prima di ogni pubblicazione» + nota sul PATH nelle evidenze delle sonde.
3. F3: evals/run.sh esclude `*.lock` dalla copia dello stato; test in test_eval_run.py (RED: migrate.lock copiato; GREEN dopo). Evidenze non toccate.
4. F5: riga in sezione 7 del piano su close_cycle a metà.
5. T2: matrice P5, s5 ed e3 con «sotto soglia al primo giro, difetto del caso/codice, sopra soglia all'ultima». eval.md già spiega (lo modifica il controller).
6. T3: spec 14, e2 con il testo reale di `reopen` («spec riaperto (<motivo>): fase spec_audit», l2acts.py:286-299).
7. T4: voce isolation: worktree in limiti.md e spec 1.2: il subagente parte dal predefinito e le modifiche non entrano nel ramo.
Test: tests/run 3.11 e 3.13 2897 OK; discover con -W error::ResourceWarning 2897 OK; nessun ResourceWarning/unclosed nell'output.
