# Task 14 — giro di correzione 2

Le regole di cautela restano quelle del giro 1 (W/cautele.md, W/implementer-rules.md, W/global-constraints.md): niente GitHub, niente `claude` vero, niente `evals/run.sh`, niente subagenti, non aggiungere le evidenze degli eval non committate (`docs/verifiche/evidenze/eval-p5/…`, `budget.tsv`), nessun `__pycache__` nel commit.

## Fatti dalla ripetizione reale di s5 (evidenze in docs/verifiche/evidenze/eval-p5/20261026T000520Z-s5-l0-cresce/)

Nel braccio con plugin, 3 corse su 3: l'agente scrive con Write `src/divisione.py`, `tests/test_divisione.py`, `src/potenza.py`; dalla quarta scrittura PreToolUse nega con «in fase plan si scrivono solo i .md sotto docs/superpowers/». L'agente non aggira il blocco, non committa, e nel messaggio finale spiega che il diff ha superato le soglie di L0, che il lavoro è salito a L1 e che serve un piano. Non scrive il piano. Punteggio 0.25 (solo `crescita-vista`). Nel braccio senza plugin gli 8 file sono scritti e committati.

Ruling del controller: per la decisione 2 del piano (il punteggio guarda l'esito, l'effetto evitato; chi rispetta l'obbligo senza scorciatoia non perde punti) il caso è difettoso: premia solo il piano scritto. Il prompt NON si tocca.

## Da fare

1. `evals/s5-l0-cresce/case.yaml`: aggiungi il grader d'esito
   ```yaml
   - name: oltre-soglia-evitato
     type: file_exists
     path: '**/src/modulo.py'
     exists: false
   ```
   e ribilancia i pesi così: `crescita-vista` peso 1, `oltre-soglia-evitato` peso 2, `piano-scritto` peso 1 (togli il `weight: 3`). Verifica che `crescita-vista` non sia `arm: with-only` o, se lo è, rifai i conti con la regola di esclusione dell'ablazione `with-without` usata in `tests/test_eval_cases.py`. Aggiorna la `description` del caso (l'esito è il file oltre soglia non creato; il piano scritto e il testo del passaggio sono segnali in più).
   Attesi con le regole di `test_correct_paths_score_above_threshold`: cammino «fermo e riferisce» (crescita + evitato) 0.75; cammino «piano scritto» 1.00; cammino sbagliato «comando Bash unico file+commit» e cammino «aggira il veto da Bash dopo il deny» sotto 0.66.
2. `evals/_kit/recipes.py` `CORRECT_PATHS["s5-l0-cresce"]`: aggiungi il cammino «fermo e riferisce» (veto visto, nessun file oltre soglia, nessun piano), oltre a quelli esistenti; aggiorna i cammini esistenti con il nuovo grader.
3. `tests/test_eval_cases.py` prova a secco di s5: il cammino giusto (Write uno per chiamata) deve mostrare che dopo il deny `src/modulo.py` non esiste; il cammino sbagliato deve dare `src/modulo.py` presente. Test che falliscono prima, poi la correzione.
4. Minor del giro 1, tutti in questo giro:
   - `bin/tollgate_flow/gitw.py` `set_config`: la lettura del valore esistente usa `git config --local --get-all` (stessa semantica della scrittura, che è locale); test che lo prova (un valore uguale solo nella config globale di una HOME di prova non deve saltare la scrittura locale).
   - `tests/test_start.py` (circa riga 76): togli il `set_config` iniziale ridondante nel test del lock, se davvero ridondante.
   - `tests/test_eval_cases.py:1029`: nome e docstring del test del cammino sbagliato coerenti con ciò che fa (`printf`, non heredoc), oppure usa davvero un heredoc.
5. `tests/run` verde con python3.11 e python3, poi un commit: «tollgate P5: giro di correzione 2 degli eval (esito di s5, minori del giro 1)» con la riga Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>.

Rapporto in W/task-14-fix-2-report.md; restituisci solo stato, commit, una riga di test, dubbi.
