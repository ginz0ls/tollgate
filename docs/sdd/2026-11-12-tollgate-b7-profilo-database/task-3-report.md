# Report Task 3 (B7): bozza rules-database, frammento database, tabella delle precedenze

## Sonda dei 47 casi (Q1-Q47, con Q46 in due parti)
Esito: **0 differenze dalla tabella** (nessuna fermata). Output completo in `task-3-sonda.txt`:
differenze: 0
Forma dei paths di D15: Q45 `database: ["**/*.sql", "/drizzle.config.ts", "src/db/schema.ts"]` (runtime .sql, config e schema a database, i due .json a nessuno); Q46a `ai: ["src/ai/**"], database: ["src/ai/db.ts"]`; Q46b `database: ["src/components/db.ts"], frontend: ["src/components/**"]`; Q47 `ai: ["prisma/ai/**", "src/ai/**"], database: ["/prisma/**"]`. Tutti come da brief. P14: proposta con `database: ["/supabase/**"]`, `og/index.tsx` a database.

## TDD
Ordine reale: ho scritto skill e frammento prima dei test; il RED l'ho riprodotto spostando temporaneamente skill e frammento fuori dal repo (poi rimessi). Comando: `python3 -B -m unittest -v tests.test_rules_database tests.test_fragments tests.test_init.FrontendPrecedenceTest tests.test_init.DatabasePrecedenceTest` -> 146 test, failures=48, errors=28 (log: `task-3-red-v.log`). Verde già senza il frammento: solo `test_real_precedence_q13`.
GREEN: `python3 -B -m unittest tests.test_rules_database tests.test_rules_frontend tests.test_rules_backend tests.test_rules_ai tests.test_rules_infra tests.test_fragments tests.test_docs tests.test_init` -> 464 test OK (skipped=10) (`task-3-green.log`). Prima corsa: 2 rossi (R-01 nominava "policy" senza ambito: tolta la parola; docs senza sezione rules-database: aggiunta).

## Regole scritte (16) e fonti
01 [blocca] schema e migrazioni letti (progetto 3.4); 02 [blocca] doc della versione (progetto 3.4, PostgreSQL current, Supabase local dev); 03 [blocca] migrazione nuova (pagina migrazioni Supabase, Prisma migration histories, deprecation-and-migration MIT); 04 [blocca] come si annulla (catalogo 2.1/2.3, deprecation MIT); 05 [blocca] due tempi (deprecation MIT); 06 [blocca] blocchi/riscritture, PostgreSQL (createindex, altertable, deprecation); 07 [blocca] RLS su tabella nuova (pagina RLS, advisor 0013, ddl-rowsecurity); 08 policy per ruolo e operazione (RLS, createpolicy); 09 [blocca] `(select auth.uid())` (RLS, advisor 0003, skill supabase-postgres MIT); 10 [blocca] indici policy e FK (RLS, advisor 0001, skill MIT); 11 [blocca] security definer (pagina funzioni, advisor 0011, createfunction); 12 [blocca] viste security_invoker (RLS, advisor 0010); 13 [blocca] niente segreti (RLS, pagina secrets); 14 [blocca] segreti edge function (progetto 12, pagina secrets); 15 [blocca] verify_jwt=false motivato (function-configuration); 16 [blocca] nessuna scrittura sul progetto collegato (progetto 14, spec nucleo 8.5, CLI, Prisma, Drizzle). Le regole 06-12, 14, 15 dicono "Vale solo per PostgreSQL / Supabase". Skill di 93 righe, senza `approved`.

## File
skills/rules-database/SKILL.md, templates/profiles/database.toml, tests/test_rules_database.py (RulesDatabaseTest), tests/test_init.py (DatabasePrecedenceTest Q1-Q47 con `check = FrontendPrecedenceTest.check`; p14 aggiornato), tests/test_fragments.py, docs/uso/comandi.md (sezione rules-database; frase di init con "frontend e database").

## Scostamenti / note
- Q46 è un solo test con due controlli (a e b). Non ho aggiunto `RulesDatabasePageTest` (Task 4).
- Le pagine di supabase.com: l'istruzione a mandare un rapporto a Supabase era già segnalata in FONTI.md; nelle copie lette non ne ho trovato testo residuo (solo le note "ignorata e tolta"). Non eseguita.
- "major_version" di config.toml è dalla decisione 9, non verificato nelle copie locali.
- Nessun comando di servizio vero, nessuna rete.

## Suite
Vedi `suite-task-3.log`.

## Giro di correzione (contratto delle skill) e suite finale
- RED: `tests.test_skill_contract.SkillContractTest.test_options_exist_in_parser` (skill rules-database) dava `opzione sconosciuta: --remote` due volte: il test cerca ogni `--opzione` nel testo di una skill e la confronta con il parser di tollgate. Fix: in R-DATABASE-16 e nella sua `Fonte:` niente `--remote` letterale ("`supabase db push` verso il progetto remoto", "l'opzione remote"), significato invariato; test e skill approvate non toccati.
- GREEN: `python3 -B -m unittest tests.test_skill_contract` -> 16 OK; file mirati dello Step 4 + test_skill_contract -> 480 test OK (skipped=10).
- `tests.test_eval_kit.BuildTest`: i tre fallimenti del 13/11 erano tempi (138-177 s contro 120) sotto carico 30+. Rilanciata con macchina scarica: 24 test OK su python3.11 e 24 OK su python3 (`task-3-buildtest.log`).
- Suite intera (`suite-task-3.log`, sovrascritto): python3.11 3996 test OK (skipped=13), python3 (3.13.5) 3996 test OK (skipped=11), `exit 0`.
- Commit: vedi git log, oggetto dello Step 5.
