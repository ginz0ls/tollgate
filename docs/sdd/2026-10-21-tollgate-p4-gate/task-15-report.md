# Report Task 15

## Implementato
- skills/init/SKILL.md (nuova, invocabile dal modello): domande prima del lancio (servizi, merge al mese), `init --propose`/`--update`, codici 0 e 1 (init.OK, init.REFUSED), modalità misurata, «non determinata» con rilancio `! ...`, passi dell'utente dal README, token separato. Mai copiare, mai protect.sh.
- finish: tre tipi di riga (DoD [sì]/[no], `rosso:`, attenzione `da leggere:`/`informative:`) e esito salvato (D21b).
- start: avvisi Actions, protezione (protected), modalità detect e issue di sentinel.
- status: non legge GitHub; l'issue di sentinel la mostra start (scostamento dal brief, che la voleva in status: il codice di status non la legge).
- execute: `task start --from-gate` legge lo SHA dal marcatore del commento del bot.
- tests/test_skill_contract.py: riga init in CONTRACTS/MEANING; sottocomandi `gate` contro tollgate_gate.cli.build_parser() (D18a), opzioni anche del parser gate; nessun «P<n>» nelle skill; test D21b; test init mai copia/protegge.
- tests/test_manifest.py: test_init_model_invocable.

## RED
```
ERROR: test_exit_codes_keep_their_meaning (tests.test_skill_contract.SkillContractTest.test_exit_codes_keep_their_meaning)
ERROR: test_exit_codes_match_constants (tests.test_skill_contract.SkillContractTest.test_exit_codes_match_constants) (skill='init')
ERROR: test_init_skill_never_copies_or_protects (tests.test_skill_contract.SkillContractTest.test_init_skill_never_copies_or_protects)
ERROR: test_init_model_invocable (tests.test_manifest.ManifestTest.test_init_model_invocable)
FAIL: test_finish_separates_attention_lines_from_dod_lines (tests.test_skill_contract.SkillContractTest.test_finish_separates_attention_lines_from_dod_lines)
Ran 43 tests in 0.348s
FAILED (failures=1, errors=4)
```
## GREEN
Mirati: Ran 43 tests, OK. `tests/run`: python3.11 Ran 2322 OK; python3 (3.13.5) Ran 2322 OK.
`claude plugin validate --strict .`: Validation passed (solo avviso ICON_MISSING, non bloccante).

## Dubbi
Nessuno bloccante. Lo scostamento su status è sopra.

## Giro 1 (fix round 1)
- I-1: `test_options_exist_in_parser` ripristinato (l'avevo cancellato per errore sostituendo il blocco dei sottocomandi). Ora usa `call_problems`, che verifica le opzioni contro il parser del nucleo, o contro quello del gate per le righe con `<programma> gate`.
- M-2: la skill `finish` elenca le chiavi di `attention.GROUPS` per gruppo (`not_tg_branch` ora in «da leggere»); `test_finish_attention_groups_match_the_code` le confronta con GROUPS.
- M-3: skill `init` e README di `init.py`: servizi in `head` e `base` di `tollgate-run` e `ids` di `tollgate-base`; `test_init_services_in_every_job_that_runs_the_suite` (legato a `install.SERVICES_WORKFLOWS`).
- M-4: funzione condivisa `call_problems`; `test_call_check_handles_gate_and_core_calls` esercita il ramo gate con casi validi e inventati.
- RED (con skill e init.py riportati al commit precedente): 1 ERROR (gruppi finish) e 4 FAIL (servizi, skill e init.py) su 13 test di test_skill_contract. GREEN: stesso modulo OK.
- `tests/run`: python3.11 Ran 2372 OK; python3 3.13.5 Ran 2372 OK.
