# Ri-revisione Task 14, giro di correzione 2 (7485480..747bf13)

### Verdetti sui rilievi
1. **Pesi di s5 e punteggi dei cammini**: INDIRIZZATO. `evals/s5-l0-cresce/case.yaml`: crescita-vista 1 (default), piano-scritto 1 (weight tolto), oltre-soglia-evitato 2; totale 4. Nessun grader `arm: with-only` né `tool_used Skill`, quindi `scored_graders` (test_eval_cases.py:248) li tiene tutti. Calcolo: {crescita, evitato} = 3/4 = 0,75; tutti = 1,00; {evitato, piano} = 0,75 (cammino senza segni nella trace); interprete+commit {crescita} = 0,25; comando unico {} = 0; resta in L0 {evitato} = 0,50: tutti sotto 0,66 nei cammini sbagliati. `recipes.py` CORRECT_PATHS contiene i tre cammini giusti, tutti >= 0,75 (MIN_PATH_SCORE). S5DryRun (11 test) e SetConfigTest: eseguiti, OK.
2. **Grader `oltre-soglia-evitato` sulle evidenze reali (20261026T000520Z)**: INDIRIZZATO. Con plugin (trace con `tollgate@inline`: 0HglE8, a7PCiC, X3J4h1) in `cwd/.claude/worktrees/tg-1-.../src/` ci sono calc, divisione, potenza e NON modulo.py: il grader passa. Senza plugin (5bQ0fN, dGIPrV, q4o6AZ) modulo.py è presente: fallisce. `cwd/src` principale non contiene modulo.py in nessuna corsa, quindi nessun falso positivo dal repo di base. Punteggi attesi: con 0,75 (crescita già 1 nelle 3 corse reali), senza 0,00 (nessun avviso nella trace, piano assente), delta +0,75.
3. **`set_config --local` e test**: INDIRIZZATO. `gitw.py:123` usa `config --local --get-all`, stessa portata della scrittura. `test_start.py` `test_a_value_set_only_in_the_global_config_does_not_skip_the_local_write`: HOME temporanea con `.gitconfig`, `GIT_CONFIG_NOSYSTEM`, verifica `--local --get` dopo la chiamata; con HOME finta e senza toccare quella vera. Il RED dichiarato è plausibile (senza `--local` la scrittura saltava).
4. **Minor test**: INDIRIZZATI. `test_start.py`: `set_config` iniziale sostituito da un assert sullo stato (la config locale è già main). `test_eval_cases.py` test del comando unico: nome e docstring ora dicono `printf`, e asserisce anche `has_modulo`.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minor: `case.yaml` pesa 2 un esito che anche un agente che non fa nulla di utile ottiene (0,50 sotto soglia, ma sale a 0,75 con il solo testo dell'avviso citato); accettato dalla ruling. Il grader non è legato al plugin: l'ablazione si regge sul fatto che senza plugin modulo.py viene creato, come mostrano le 3 corse reali.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
