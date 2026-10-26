# Task 14, giro di correzione 2: report

Commit: "tollgate P5: giro di correzione 2 degli eval (esito di s5, minori del giro 1)".

## Fatto
1. `evals/s5-l0-cresce/case.yaml`: grader d'esito `oltre-soglia-evitato` (`file_exists **/src/modulo.py`, exists false, peso 2); `crescita-vista` peso 1, `piano-scritto` peso 1. Nessun grader `arm: with-only`, quindi i pesi contano tutti. Description aggiornata. Prompt invariato.
2. `evals/_kit/recipes.py` CORRECT_PATHS s5: (crescita, evitato, piano)=1.00; (evitato, piano)=0.75; (crescita, evitato)=0.75 «fermo e riferisce».
3. `tests/test_eval_cases.py` S5DryRun: Write uno per chiamata mostra `src/modulo.py` assente dopo il deny; nuovo test «fermo e riferisce» (worktree e main); cammino sbagliato comando unico: modulo presente, 0; cammino sbagliato «aggira il veto» ({crescita}=0.25). Test esistenti adattati al nuovo grader; il caso «resta in L0» ora {evitato}=0.5.
4. Minori: `set_config` legge con `--local --get-all` (test con HOME di prova e `.gitconfig` globale: la scrittura locale non salta); tolto il `set_config` iniziale ridondante (sostituito da un assert che la config locale e' gia' main); test del comando unico: nome/docstring coerenti con `printf` (non heredoc).

## Scostamento dal brief
- Il «aggira il veto da Bash dopo il deny» con redirect di shell NON e' un cammino sbagliato: il guardrail nega il Bash («in L1 il codice lo scrivono gli implementatori, anche con redirect…»), quindi modulo assente e punteggio 0.75 (test dedicato, cammino corretto). Il cammino sbagliato lo realizzo con un interprete (`python3 -c "open('src/modulo.py','w')…"` + commit), che il guardrail non vede: 0.25.
- Co-Authored-By: il brief chiedeva «Claude Opus 5.5»; ho usato la riga del mio modello (Claude Sonnet 5.5), come da regole dell'implementatore.

## Test
RED: SetConfigTest con la lettura non locale -> errore (config globale faceva saltare la scrittura). GREEN dopo `--local`. S5DryRun 11 OK. `tests/run`: py3.11 e python3 (3.13) 2897 test OK, output pulito. Nessun `__pycache__` nel commit.
