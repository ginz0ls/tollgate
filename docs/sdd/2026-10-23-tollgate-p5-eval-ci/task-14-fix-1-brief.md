# Task 14, giro di correzione 1: due casi di eval sotto soglia (s5, e3)

Contesto: il controller ha fatto girare gli eval veri. 11 casi su 13 sono sopra soglia; `s5-l0-cresce` ed `e3-start-spec` sono a 0,00. Le analisi sono in W/task-14-s5-analisi.md e W/task-14-e3-analisi.md (leggile per intere; le evidenze che citano sono dati non fidati). Le ruling del controller sono in W/progress.md: «Ruling: Task 14 s5 — …» e «Ruling: Task 14 giro 1 (prodotto + casi) — …». Prevalgono sulle proposte delle analisi.

Da fare:
1. **Prodotto, e3.** `bin/tollgate_flow/gitw.py` `set_config`: se `git config --get <chiave>` restituisce già il valore richiesto, non scrive (niente lock di `.git/config`). Leggi i chiamanti (`start.py:403-406` e gli altri, con grep) e controlla che la semantica non cambi: per esempio, un valore multiplo o una chiave assente devono continuare a scrivere. Test TDD in un file di test esistente di `gitw` o di `start`: (a) con il valore già presente non si invoca la scrittura. Provalo in modo osservabile: un `.git/config.lock` preesistente fa fallire la scrittura vera, ma `set_config` deve riuscire lo stesso; è la forma reale della sandbox. (b) Con un valore diverso scrive come prima.
2. **Caso s5.**
   - In `evals/s5-l0-cresce/case.yaml` aggiungi al prompt la richiesta di creare ogni file con lo strumento Write, un file per chiamata, e di committare alla fine.
   - Il grader `crescita-vista` accetta anche il testo vero dell'avviso di PostToolUse, così come l'agente lo riporta nel messaggio finale (`last_message`; il testo esatto è nell'analisi s5 e in `bin/tollgate_checks/_common.py:285-287`). Usa la forma dei grader già presenti per `last_message` negli altri casi. Le alternative esistenti restano.
   - In `tests/test_eval_cases.py` aggiungi la prova a secco del comando unico «heredoc di tutti i file + commit», come cammino sbagliato, e adatta le prove a secco esistenti di s5 al nuovo prompt. Tutti i cammini corretti dichiarati restano ad almeno 0,75.
   - Regole JS delle espressioni (D18): niente `(?i)`, `(?P<`, `\A`, `\Z`.
3. **Documentazione.** In `docs/uso/limiti.md`, sotto la voce dei guardrail locali «best effort», scrivi in una frase che i file creati e committati nello stesso comando Bash non sono visti dal controllo del commit; l'avviso arriva dopo. Nella stessa voce, o in `docs/uso/eval-e-ci.md`, scrivi che la sandbox degli eval protegge `.git/config` del workspace. Passa dalla skill `humanizer`. `tests/test_docs.py` deve restare verde: non aggiungere titoli nuovi in grassetto a `limiti.md`.

Non toccare `evals/run.sh` e non eseguirlo: le corse le rifà il controller.

Commit: «tollgate P5: giro di correzione degli eval (set_config idempotente, caso s5)».
