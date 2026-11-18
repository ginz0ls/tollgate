# Report Task 6 (B7)

## RED
`python3 -B -m unittest tests.test_manifest tests.test_finalreview tests.test_init.DatabaseAgentsProposeTest tests.test_taskcmd tests.test_check_task_verdict`:
217 test, 2 fallimenti e 16 errori attesi (agenti `*-database` assenti; `r-database-` assente da
`final-reviewer` e `finding-verifier`).

## GREEN
Stessi file piu' `tests.test_wrapper` e `tests.test_config`: 295 test OK dopo la scrittura degli
agenti e degli elenchi. `claude plugin validate --strict .`: Validation passed. Suite completa `PYTHONWARNINGS=error::ResourceWarning tests/run`: exit 0, 4034 test su python3.11 (skipped=13) e su python3 (3.13, skipped=11). Commit 356ad9d.

## Agenti
- `agents/implementer-database.md` (da `implementer-frontend`, `skills: [rules-base, rules-database]`).
  Sezione d'area sul report: R-DATABASE-01, 02, 04, 06, 15, 16. Divieto: supabase, psql, docker, prisma,
  drizzle-kit, npx/npm/pnpm/yarn/bunx/bun; le prove passano da `<programma> verify` e dal `dod`.
- `agents/reviewer-database.md` (da `reviewer-frontend`, + WebFetch). Report: 01, 02, 04, 06, 15, 16;
  diff: 03, 05, 07, 08, 09, 10, 11, 12, 13, 14.
- `agents/final-database.md` (da `final-reviewer`, stessi tools, `model: inherit`, stessa attribuzione).
  Nomina solo le regole sul diff: 03, 05, 07-14; le regole sul report restano al revisore del task, senza id.
- Elenchi: `hooks/run` (`READONLY_TYPES`) e `config.py` (`readonly_agents`) con `reviewer-database` e
  `final-database`; virgola e `R-DATABASE-` in `final-reviewer.md` e `finding-verifier.md`;
  `docs/uso/comandi.md` (`execute`, `finish`).

## Scostamenti
- `tests/test_wrapper.py` non modificato: `test_readonly_list_matches_config_and_agents` copre gia' i due agenti.
- `tests/test_finalreview.py`: `FinalCase.lab` ha un parametro `extra` per committare una migrazione nel lavoro.
- Il test d'area (`test_area_agents_name_area_rules`) per `final-database` e' un ramo aggiuntivo (una sola frase
  «si giudicano sul diff», nessuna «sul report»).

## Dubbi
Nessuno.
