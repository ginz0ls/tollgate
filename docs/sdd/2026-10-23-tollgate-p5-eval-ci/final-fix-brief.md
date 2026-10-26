# Giro di correzioni finale del ramo P5 (unico)

Fonti: W/final-review.md (minori F1-F5) e W/task-15-review.md (minori T1-T5). Regole: W/implementer-rules.md, W/cautele.md, W/global-constraints.md, come nel Task 15. Niente GitHub, niente `claude`, niente `evals/run.sh` vero.

Correzioni (tutte, nessuna esclusa):
1. **F1 = T1** `tests/test_p5_scripts.py:951`: `open(reg).read()` → `with open(reg) as f:` (o `Path(reg).read_text()`, come nel resto del file).
2. **F2 + F4 = T5** piano principale `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md:~482`: «Prima del primo push» → «Prima di ogni pubblicazione»; alla nota aggiungi che le evidenze delle sonde del Task 1 (`docs/verifiche/evidenze/eval-p5/*-sonda-*/`) contengono anche il `PATH` dell'utente (l'elenco degli strumenti installati), oltre ai percorsi assoluti.
3. **F3** `evals/run.sh:~239-245`: nel ciclo che copia `.local/state/tollgate` nelle evidenze escludi i `*.lock` (oggi copia `migrate.lock` vuoti). Le evidenze già committate NON si toccano (decisione 22). Test TDD in `tests/` dove sono i test di run.sh (rosso prima, verde dopo).
4. **F5** sezione 7 «Dopo la v1» del piano principale: una riga — un DB di 0.1.0 con un `close_cycle` rimasto a metà (vecchio codice in due transazioni) non si ripara più da solo (`bin/tollgate_core/reviews.py:358-361`); `finish check` e `open-pr` ricalcolano.
5. **T2** matrice «Prove dei criteri di P5» del piano principale (e, se serve, `docs/verifiche/2026-10-23-p5-eval.md`): dove compaiono s5/e3 spiega in poche parole «sotto soglia al primo giro, corretto (difetto del caso/codice), sopra soglia all'ultima invocazione», così la matrice non sembra contraddire «tutti sopra soglia».
6. **T3** spec rev 26, sezione 14 (dove si parla di `e2`): una riga col testo reale di `reopen` («spec riaperto (…): fase spec_audit», `bin/tollgate_flow/l2acts.py:286`) che la prova a secco di e2 verifica. Verifica il testo esatto nel codice prima di citarlo.
7. **T4** `docs/uso/limiti.md:~107` e spec 1.2 (voce «I subagenti con `isolation: worktree` non vengono bloccati»): sostituisci «Gli hook non li bloccano» con il fatto utile (spec ~577): il subagente parte dal predefinito e le sue modifiche non entrano nel ramo. Mantieni identico l'insieme dei titoli (test_limits_match_spec_1_2).

Poi: `bash tests/run` (python3.11 e python3) e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` — verdi, e nell'output nessun `ResourceWarning` né «unclosed». Niente `__pycache__` nel commit. Un commit: «tollgate P5: correzioni della revisione finale». Rapporto in W/final-fix-report.md; restituisci stato, commit, una riga di test, dubbi.
