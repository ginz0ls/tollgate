# Report Task 2 (B5): scritture di Wrangler su KV, D1, R2 e script dei monorepo

## Implementato (`bin/tollgate_analysis/bash.py`)
- `_DEFAULT_EFFECTS`: aggiunte `wrangler d1 create`, `d1 delete`, `d1 time-travel restore`.
- `ACCOUNT_GROUPS`, `FLAG_EFFECTS` (modi `unless_local` e `with_remote`), `_flag_present(rest, name)`, `_account_group_read`, `_wrangler_data_reason`, richiamata nel ciclo di `effect_reason` su argv e candidati dei lanciatori.
- `SCRIPT_VALUE_OPTIONS` e `script_name(argv)` al posto di `a[1]`/`a[2]`; eccezione di `-w` con `pnpm`; `workspace` solo per `yarn`.
- `_TEXT_EFFECTS`: regex per i prefissi di `ACCOUNT_GROUPS` e `FLAG_EFFECTS` (`with_remote`: prefisso + `--remote|--preview` nello stesso comando). Tabelle definite prima di `_TEXT_EFFECTS`.
- Nessun marcatore della decisione 3 in `bin/`; nessun messaggio con «tollgate init/approve».

## Test (`tests/test_bash.py`, `EffectsTest`)
Aggiunti i 8 test del brief (writes, local writes, reads, launcher, reason, text_effect, script_name, monorepo).
RED: `python3 -B -m unittest tests.test_bash.EffectsTest` -> 52 failure + 10 errori sui test nuovi; le guardie (local writes, reads) già verdi.
GREEN: `python3 -B -m unittest tests.test_bash tests.test_effects tests.test_check_effects` -> 113 test OK.
Sonda extra (`npm run`, `yarn workspace`, `pnpm -w`, `yarn run docs`, `echo wrangler kv key put`) senza effetti spuri.

## Scostamenti dal piano
Nessuno.

## Suite completa
`PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 3685 test OK (7 skipped), python3 (3.13.5) 3685 test OK (5 skipped), exit 0.
