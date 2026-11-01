## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_analysis/research.py` | 1 | `_YAML_EMPTY` con `no`, `off`, `n`; confronto dopo gli apici |
| `bin/tollgate_core/lookups.py` | 1 | `rules_switch`; `rules_enforced` sopra di essa |
| `bin/tollgate_core/events.py` | 1 | tipo `research_switch_unreadable` in `EVENT_TYPES` |
| `bin/tollgate_checks/research_gate.py` | 1, 6 | avviso ed evento con l'interruttore illeggibile; avviso che nomina `rules-base` |
| `bin/tollgate_analysis/brief.py` | 1, 6 | nota del task senza modifiche; standard del revisore con le regole di base |
| `tests/…` che presumono l'interruttore spento, `tests/test_eval_cases.py` | 2 | radice esplicita; nota nei casi a secco |
| `skills/rules-base/SKILL.md` | 3, 4, 5 | le regole |
| `LICENSES/agent-skills-MIT.txt` | 3 | licenza della fonte |
| `docs/uso/comandi.md`, `tests/test_b1_scripts.py` (righe 169 e 555) | 3 | sezione del comando; la `rules-base` del repo non è più assente |
| `docs/profili/verifiche/base-fonti.md`, `docs/profili/base.md` | 4, 5 | verifica delle fonti; pagina per l'utente |
| `agents/implementer.md`, `agents/task-reviewer.md`, `agents/final-reviewer.md`, `agents/finding-verifier.md` | 6 | `skills: [rules-base]`; rimandi alle regole |
| `spikes/run-b1-flow.sh`, `tests/test_b1_scripts.py` | 7 | prova con la `rules-base` vera |
| `docs/verifiche/2026-10-29-b2-prova-flusso.md`, `docs/verifiche/evidenze/b2/flusso/` | 7 | rapporto ed evidenze della prova |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 8 | revisione 28 e stato |

---

