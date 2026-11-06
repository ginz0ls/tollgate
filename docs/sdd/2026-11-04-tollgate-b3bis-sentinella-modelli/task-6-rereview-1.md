### Verdetti sui rilievi
1. **Asserzione su `ROOT.name` nel test da togliere (verde anche nel checkout «Plugin IT workflow»)**: INDIRIZZATO. Rimossa la riga in `tests/test_b1_scripts.py` (~1017, diff -1); i percorsi letterali con altre radici e i casi negativi restano (righe 1014-1025 del diff) e provano l'indipendenza; `flowreg` non usa `ROOT`. `ROOT` è ancora usato altrove nel file (21 occorrenze), nessun import orfano.
2. **Elenco cartelle di `skills/` calcolato una volta**: INDIRIZZATO. `spikes/b1/flowreg.py:259-261` `_repo_skill_names()` con `@functools.cache`, usata a `:267`; parte ancora da `Path(__file__).resolve().parents[2] / "skills"` (`:256`); `import functools` aggiunto.

### Danni nuovi nel diff della correzione
Nessuno. (Il report mostra `tests.test_b1_scripts` verde: Ran 64, OK, su python3 e python3.11; non rilanciato.)

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
