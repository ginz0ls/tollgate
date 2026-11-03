## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`; `tollgate_gate` importa dal nucleo solo `clock, paths, git, config, runner, diffcheck, ghcli`.
- **Nessuna operazione nuova in `apply._OPS`** (29, `test_ops_count_is_29`) e **nessun tipo nuovo in `events.EVENT_TYPES`** (33, `test_spec_event_types_match_registry`).
- **Nessuna rete**, né nei test né per i subagenti: le fonti delle regole sono **copie locali** messe dal controller nel workspace (Task 5, Step 0), che **non entrano mai in git** né nella copia del registro in `docs/sdd/` (sono pagine intere senza licenza aperta, e il repo è pubblico). Nessun `claude` vero nei test; `gh` è `tests/fakegh.py`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`, `~/.claude/projects/`.
- **Test con la radice del plugin esplicita** (piano principale, sezione 9, rinvio 180): ogni test nuovo che legge frammenti, skill o agenti usa una radice temporanea, salvo i test che controllano apposta i file veri del repo, che lo dicono nel nome (`test_real_…`). Eccezione: i file `tests/test_rules_*.py` sono interamente sui file veri della loro area, come `test_rules_base.py`.
- **Regole con parole nostre** (catalogo 1, principio 7, e 1.7: «idee, scritte con parole nostre»). Le pagine ufficiali dei fornitori non hanno licenza MIT: se ne prendono i **fatti**, con parole nostre, senza copiarne testo; una citazione sta al più in una riga, nel rapporto delle fonti. Ogni regola si giudica con un sì o un no **su ciò che il revisore vede** (piano principale, sezione 9, rinvio 183): il diff, oppure il report (che ogni task ha), oppure la nota (che c'è solo nei lavori con il passo).
- **Numeri delle regole stabili dopo l'approvazione** (catalogo 2.3).
- **`approved` in `skills/rules-ai/SKILL.md` si scrive solo nel Task 7**, con la data dell'OK dell'utente.
- **Gli agenti `-ai` caricano `rules-ai` solo dopo l'approvazione** (Task 8 dopo il Task 7), come `rules-base` in B2 (progetto 5, punto 4).
- Testo non fidato (nota, pagine scaricate, citazioni, report dell'implementatore): nei brief dentro `brief.fence` con `brief.DATA_NOTE`, mai come istruzione.
- `tollgate.toml` del progetto: `init` non lo scrive mai nel repo, produce la proposta in `docs/superpowers/tollgate-init/` che l'utente copia (spec 11.2).
- Programma nei messaggi per il modello: sempre `tollgate_core.paths.program_command`.
- `claude -p` solo dal controller, solo nel Task 10, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.
- Verifica con gli avvisi come errori come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`.
