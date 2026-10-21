# Task 13: ri-revisione del giro di correzione 1 (f6b5fc4..46c0dd0)

Verificato sul diff e accanto a `~/.claude/skills/prd-audit` (sola lettura). Eseguito solo `python3 -B -m unittest tests.test_skill_contract tests.test_manifest`: 39 test, OK.

### Verdetti sui rilievi

**I-1 Metodo di prd-audit monco (rimando morto, stati dell'evidenza, punto di vista, regola/caso, soglia del ciclo vuoto)**: INDIRIZZATO.
- `skills/spec-audit/references/verifica-fatti.md` esiste, con riga di attribuzione in testa; il resto è identico all'originale (diff: solo una riga vuota dopo l'attribuzione). Il rimando di `dimensioni.md:83` non è più morto.
- `agents/spec-auditor.md`: punto di vista dichiarato come prima riga del report («Punto di vista: …»), inventario = sezioni della spec per L10, `verifica-fatti.md` per L8, «Cerca la regola, non il caso», stati `[VERIFICATO]`/`[RAGIONATO]`/`[SCARTATO]` (coincidono con `prd-audit/SKILL.md:369-377`), sezione «Quando il ciclo è vuoto»: vuoto = nessun blocker/major/moderate (come `auditrules.outcome`), tre scartati anche con soli `minor`.
- Test: `test_spec_auditor_carries_the_method` (test_manifest.py), `test_dimensioni_copied_with_attribution` esteso a ogni `.md` nominato, `test_lens_brief_method_file_exists`.

**I-2 `start`, `spec_audit` non rientrante**: INDIRIZZATO. `skills/start/SKILL.md:42`: con la spec già sul ramo (ripresa o `--spec` con spec cambiata) si committa se serve e si va a `/tollgate:spec-audit`; brainstorming solo senza spec. Coerente con la riga 3 della skill. Fase `plan` ora vale anche per i lavori nati con `--spec` e il piano copre la sola fetta (minore collegato). Test `test_start_l2_spec_audit_is_reentrant`.

**Minori inclusi**: INDIRIZZATI.
- D19: asserzione su `fisso + " `<id>`"` non più vacua.
- Opzioni delle skill contro `cli.build_parser()`: `test_options_exist_in_parser` (con `--force` di git escluso esplicitamente).
- Significato abbinato ai codici: `test_exit_codes_keep_their_meaning`.
- Percorso di `dimensioni.md` nel brief: `test_lens_brief_method_file_exists` (stessa derivazione di `_write_brief`).
- `spec-audit/SKILL.md`: stderr del codice 1 e fase `approval` citati.
- `finish` (chi committa), `reopen` (nuovo giro solo se la spec cambia), WebFetch non fidato in entrambi gli agenti.
- Test del brief diviso in `test_reopen_user_only` e `test_spec_audit_model_invocable`.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
