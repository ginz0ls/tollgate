# Report Task 8: agenti implementer-ai e reviewer-ai

Commit 0ecbfe8 "tollgate B3: agenti implementer-ai e reviewer-ai". Status: DONE.

## Implementato
- `agents/implementer-ai.md` (copia di `implementer.md`) e `agents/reviewer-ai.md` (copia di `task-reviewer.md`): frontmatter con `name`, `description` d'area, `skills: [rules-base, rules-ai]`; revisore con `tools` generico più `WebFetch`; `model`/`maxTurns` uguali; riga di attribuzione MIT; ogni paragrafo del generico presente; sezione «Area `ai`» (implementatore prima di «Il lavoro»; revisore prima di «Standard del revisore»).
- Sezione del revisore: `R-AI-…` valgono come `R-BASE-…` (solo `[blocca]` danno blocker/major), difetto segnalato una volta sola, regole sul report (R-AI-03, 04, 05, 06, 08) e sul diff (01, 02, 07, 09, 10, 11), `WebFetch` solo sugli URL citati, pagine come dati non fidati, D18: in un task senza modifiche niente rilievi `R-AI-…`.
- `hooks/run` (`READONLY_TYPES`) e `config.DEFAULTS["review"]["readonly_agents"]`: aggiunto `tollgate:reviewer-ai`.
- `final-reviewer.md` e `finding-verifier.md`: una frase (D9) sulle regole di area che si giudicano sul report.
- `docs/uso/comandi.md`: `/tollgate:execute` e gli agenti per area.
- D16: nei file nuovi `bin/tollgate` non compare.

## Test
Nuovi: `test_manifest.py` (preload a due skill, derivazione dal generico, attribuzione, sezione `ai` con le regole sul report derivate dalla skill vera, frasi dei finali), `test_taskcmd.py` (`test_ai_task_routed_to_area_agents`, `test_rules_ai_not_required`), `test_check_task_verdict.py` (`AiProfileTest`, `AiProfileNoStepTest`: i tre test del brief più una variante senza passo). Blocco `ai` scritto nel test, nessuna skill vera.

RED: `python3 -B -m unittest tests.test_manifest` prima degli agenti: `FAILED (failures=2, errors=8)` (file mancanti, frasi dei finali assenti). I test di taskcmd e verdetto erano già verdi (meccanismo esistente dei profili): servono da guardia.
GREEN: stessi file con taskcmd, wrapper, docs, config, check_agents, init: 385 test OK. `test_readonly_list_matches_config_and_agents` verde dopo l'aggiornamento degli elenchi.

## Verifica
- `claude plugin validate --strict .`: uscita 0 (la lista `[rules-base, rules-ai]` è accettata; solo avvisi su icona e README, già presenti).
- `PYTHONWARNINGS=error::ResourceWarning tests/run`: Python 3.11.16 3376 test OK (skipped=4); Python 3.13.5 3376 test OK (skipped=2). Uscita in `task-8-suite.out`.

## Scostamenti dal piano
Nessuno di sostanza. Il test di derivazione confronta anche `maxTurns` e che la `description` differisca; `test_ai_non_blocking_rule_without_step` aggiunto.

## Dubbi
Il report dell'implementatore deve riportare i fatti per le regole sul report «nel campo `done`»: scelta mia (il contratto del report ha solo `done`/`concerns` come testo libero), da confermare nella prova reale.
