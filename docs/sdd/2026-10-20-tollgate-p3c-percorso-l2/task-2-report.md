# Report Task 2 (P3c): analisi pura, forma della spec, intestazioni, recinti

## Implementato
- `bin/tollgate_analysis/specdoc.py` (nuovo): `SLICES_SECTION`, `PITCH_SECTIONS`, `slices`, `slice_titles`, `pitch_problems`. Riusa `plan._Fences` (recinti saltati come nel parser del piano; le intestazioni `##` dentro un recinto non chiudono la sezione).
- `bin/tollgate_analysis/approvals.py`: `REPORT_KINDS`, `SEVERITIES`, `parse_header` (lettore comune, `counts` come dizionario), `parse_approval` (contratto invariato, sopra `parse_header`), `parse_report_header` (`counts` esattamente le quattro gravità, interi >= 0; `number` intero >= 1), `render_approval`, `render_report` (D12: `ValueError` su a capo, `"`, categorie Unicode Cc/Zl/Zp; nomi di campo non identificatori e tipi non ammessi rifiutati), `approval_listing`, `locate_spec_approval` (pura, docstring D3), `check_l2` (messaggi che nominano il file o il report mancante). `_value` toglie il commento anche dopo un valore tra virgolette (triage 30).
- `bin/tollgate_analysis/plan.py`: `_FENCE_OPEN` con al più 3 spazi di rientro (decisione 17).

## Scelte
- `check_l2`: spec non registrata o blob nullo, piano idem, sono problemi. Approvazione propria superata (sha diverso) dà un problema «cambiata dopo l'approvazione». Con approvazione mancante o superata non si cercano i report (evita rumore: il problema è già detto). `plan-approval` con `sha` diverso e `spec_sha` diverso danno due messaggi distinti.
- Un'approvazione propria con `path` uguale ma `sha` vecchio vince su quella di un'altra issue con `sha` giusto (D13: «qualunque sha»); `check_l2` la segnala come superata.
- `approval_listing` mantiene l'ordine dato; `locate_spec_approval` ordina numericamente gli altri candidati.

## TDD
- RED: `python3 -B -m unittest tests.test_specdoc tests.test_approvals tests.test_plan` -> `FAILED (failures=2, errors=22)` (moduli e funzioni assenti, recinto a 4 spazi).
- GREEN: stesso comando -> `Ran 55 tests ... OK`.
- Test: `tests/test_specdoc.py` (nuovo), `tests/test_approvals.py` (HeaderTest, LocateTest, CheckL2Test), `tests/test_plan.py::FenceIndentTest`.

## Suite completa
Vedi il riepilogo in fondo (esito di `tests/run`).

## Scostamenti dal piano
Nessuno. Chiamanti di `parse_approval` (`bin/tollgate_flow/adopt.py:157`) invariati.

## Esito tests/run
python3.11: Ran 1444 tests, OK (692 s). python3 (3.13.5): Ran 1444 tests, OK (506 s). Output pulito.
