## Mappa dei file

| File | Responsabilità |
|---|---|
| `docs/verifiche/2026-10-21-p4-verifiche.md`, `docs/verifiche/evidenze/gh-p4/`, `spikes/gh-p4/` | Task 1: fatti nuovi di GitHub e `gh` 2.46 |
| `bin/tollgate_core/{runner,ghcli,diffcheck}.py` (nuovi) | Moduli senza stato (decisione 2) |
| `bin/tollgate_core/{verify,violations,git,audits}.py`, `bin/tollgate_flow/gh.py` | Importano dai moduli nuovi; `ls_files_at` e `text_at` protetti; `open_round(min_number=)` |
| `bin/tollgate_analysis/{workflows,prref}.py` (nuovi) | Regole dei workflow del progetto; issue dal ramo e dal corpo |
| `bin/tollgate_analysis/{approvals,prblock,prbody}.py` | `check_l2_detail`, caso (a) e (d); campi nuovi; tetto del corpo |
| `bin/tollgate_gate/__init__.py` | Pacchetto |
| `bin/tollgate_gate/{model,attention,evaluate}.py` | Ingressi, gruppi, calcolo puro |
| `bin/tollgate_gate/{comment,artifacts,run,baseids,guard,github,verdict,sentinel,protection,install,l2tree,cli}.py`, `bin/tollgate` | Commento, artefatti, sottocomandi, I/O verso GitHub, misura della protezione, impronta del CLI |
| `bin/tollgate_core/cli.py` | Sottocomando `init` (il `gate` lo smista `bin/tollgate`) |
| `bin/tollgate_flow/{finishcheck,openpr,fixtask,taskcmd,start,audit,init}.py`, `bin/tollgate_flow/l2tree.py` | `finish check` sul gate, campi del blocco, marcatore, evento, protezione in `start`, casi P3c, `init` |
| `bin/tollgate_checks/audit_round.py` | Riga 19 di P3c |
| `gate/workflows/tollgate-*.yml`, `templates/tollgate.toml` | Modelli proposti da `init` |
| `skills/init/SKILL.md`; `skills/{finish,start,status,execute}/SKILL.md` | Skill nuova e aggiornate |
| `tests/test_*.py`, `tests/gatekit.py` (nuovo), `tests/fakegh.py` | Un file per modulo; banco del gate; `gh` finto con statuses, commenti, protezione |
| `spikes/run-p4-gate.sh`, `spikes/run-p4-flow.sh`, `spikes/p4/` | Task 16 |
| `docs/verifiche/2026-10-21-p4-prova-gate.md`, `docs/verifiche/2026-10-21-p4-prova-flusso.md` | Rapporti del Task 16 |
