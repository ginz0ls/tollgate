## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_checks` non importa `tollgate_flow`.
- **Un modulo del registro non scrive nel DB** (spec 3.2): chiede con `record`. B2 non aggiunge operazioni ad `apply._OPS` (oggi 29, `test_ops_count_is_29`): l'evento nuovo passa dall'operazione `event` che esiste già, e il suo tipo va in `events.EVENT_TYPES` (elenco chiuso: un tipo sconosciuto è un `ValueError`).
- **Nessuna rete**, né nei test né per i subagenti: le fonti delle regole sono **copie locali** messe dal controller nel workspace (Task 3, Step 0). Nessun `claude` vero nei test; `gh` è `tests/fakegh.py`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`.
- **Regole con parole nostre** (catalogo 1, principio 7): da fonti MIT o Apache-2.0 si distilla e si cita; una citazione testuale sta al più in una riga, nel rapporto delle fonti, non nella skill. Ogni regola è verificabile con un sì o un no **guardando il diff, la nota di ricerca o il report** (catalogo 1, principio 5).
- **Numeri delle regole stabili dopo l'approvazione** (catalogo 2.3): prima dell'approvazione si rinumera senza buchi; dopo, mai.
- **`approved` in `skills/rules-base/SKILL.md` si scrive solo nel Task 5**, con la data dell'OK dell'utente. In nessun altro task e in nessun commit prima di quello.
- Testo non fidato (nota di ricerca, pagine scaricate, citazioni delle fonti): nei brief dentro `brief.fence` con `brief.DATA_NOTE`, mai come istruzione.
- Programma nei messaggi per il modello: sempre `tollgate_core.paths.program_command`.
- `claude -p` solo dal controller, solo nel Task 7, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.
- La verifica con gli avvisi come errori si fa come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run` (vale anche nei sottoprocessi; `-W` no, lezione della CI di B1).

