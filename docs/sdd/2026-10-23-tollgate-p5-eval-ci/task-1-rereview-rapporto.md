# Ri-revisione della correzione del rapporto del Task 1 (2ec895b)

### Verdetti sui rilievi

- **I1 (file fantasma e rumore `.bashrc` della sandbox non registrati):** INDIRIZZATO. Nuova sezione «File fantasma della sandbox e limiti delle prove» in `docs/verifiche/2026-10-23-p5-verifiche.md` (diff +`## File fantasma…`): elenca i nomi, la fonte (trace `…201258Z-sonda-ws-worktree`), il rumore su stderr e la conseguenza per i Task 7-10 (`.git/info/exclude`, `git add` espliciti, nessun grader su stderr).
- **M1 (minuti «da sottrarre» non provato):** INDIRIZZATO. La frase ora dice che la API non misura i minuti e che i 43 minuti sono una stima dalle durate dei job; la sottrazione ai 2000 minuti non è più asserita.
- **M2 (VE6: `allowed_tools` e flag `--allow-tools`):** INDIRIZZATO. La riga VE6 dice che `Agent`, `Skill`, `EnterWorktree` sono accettati senza errore e che `Bash`/`Write`/`Edit` servono solo con `--allow-tools`. Resta implicito (non nella colonna «Conseguenza») che `evals/run.sh` deve passare il flag: lacuna lieve.
- **M3 (D18 (a): assenza nella trace diversa da non ricevuto):** INDIRIZZATO. «Non determinato se il modello riceve il contesto; la trace non lo mostra».
- **M5 (git worktree add/branch/config non provati):** INDIRIZZATO. Voce «Non provati nella sandbox» con il rischio sulla `denyWrite` di `.git/config` e `.git/hooks`.
- **M6 (VC1: suite 2465 vs 2559; motore di `setup-python@v5`):** PARZIALMENTE INDIRIZZATO. La riga VC1 ora precisa «sulla suite di 2465 test del codice di `main` a9b37e3», ma il limite del timeout resta «sopra i 12 minuti misurati» senza il +4% di test (2559 appare solo nei controlli finali, righe 63-64), «già corretta in dcd0485/9d5c802» resta non qualificato e il motore di `setup-python@v5` non è aggiunto (grep: nessuna occorrenza). Minor, non cambia la decisione 13.

(M4 restava minore, non richiesto.)

### Danni nuovi nel diff della correzione
Nessuno. Solo documentazione toccata; l'ultima riga dei controlli (rilancio di `tests/run`, 2559 test OK) è coerente con la precedente.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi Important indirizzati, nessun danno nuovo Critical/Important. Resta aperto solo il residuo minor di M6 (+4% di test accanto al timeout, motore di `setup-python@v5`), non bloccante.
