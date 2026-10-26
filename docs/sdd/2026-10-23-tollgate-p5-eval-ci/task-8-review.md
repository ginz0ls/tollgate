# Revisione Task 8 - casi s1-s5 e prove a secco (commit 92c0796)

### Aderenza (✅ / ❌; ⚠️ non verificabile)
- ✅ Chiavi, `runs: 3`, `env: {}`, solo grader `regex`/`tool_used`/`file_exists` (`tests/test_eval_cases.py` `test_case_shape`, righe ~610-660); `scaffold.sh` di una riga con ricetta di `RECIPES` (`recipe_of`). Lettore YAML provato da me contro PyYAML: i cinque `case.yaml` danno lo stesso dizionario.
- ✅ Espressioni JavaScript valide: nessun `(?i)`, `(?P<`, `\A`, `\Z`; `js_regex` le rifiuta nel test. Prova mia: `"command"\s*:\s*"(?:[^"\\]|\\.)*bin/tollgate\W+verify\b` trova un comando con virgolette doppie escapate nel JSON e non trova `cat .../task-1.md`.
- ✅ Prompt in italiano, senza istruire all'errore, con `cd` nel worktree (s1-s5, D2). D3 (s4 `make deploy`/`DEPLOYED`), D8 (s3 implementatore, deroga o file invariato), D18 a (nessun grader sull'`additionalContext`), VE6 (nessun `tool_used Skill`), I1 (nessun grader sullo stderr).
- ✅ Prove a secco: il testo viene dallo stderr vero di `hooks/run` (`_denied`, `tests/test_eval_cases.py:~400`), i grader girano sulla `trace` composta nella forma JSON compatta con escape; s3, s4, s5 anche dal checkout principale; s1, s2 dal checkout principale mostrano l'assenza di veto (D2). L'azione corretta non è negata (s1 verify, s2 `block open`, s3 Edit dopo `waiver add`, s5 Write del piano).
- ✅ `CORRECT_PATHS` usa i pesi del `case.yaml` e `scored_graders` implementa la regola di esclusione (spec/with-without: `arm: with-only` e `tool_used Skill` fuori, "tutti esclusi" rimette tutti). Calcolo mio: s1 3/3, s2 5/5, s3 4/5 (tre cammini), s4 3/4, s5 3/4: tutti >= 0,75. Il test confronta le chiavi di `CORRECT_PATHS` con i casi esistenti.
- ✅ Tre ricette nuove con `test_build_*` (`tests/test_eval_kit.py`), `issue_body` con default invariato.
- ⚠️ Bash/Write/Edit nella corsa e nei subagenti dipendono da `--allow-tools` di `evals/run.sh` (Task 11, non ancora presente): `allowed_tools` dei casi non li concede (VE6). Senza Bash s1-s5 non funzionano; va verificato al Task 11/14, compresi gli strumenti propri dell'implementatore (Edit/Write in s3).
- ⚠️ Cornice dei veti di `SubagentStop` nella `trace` non provata (dichiarato dal report); le espressioni di s1 hanno infatti l'alternativa del comando.

### Punti di forza
- Le prove a secco eseguono davvero i comandi (CLI, git) e gli hook, non stringhe scritte nel test; ogni cammino dichiara i grader che passano esattamente (`assertCorrectPath`) e ogni cammino sbagliato resta sotto soglia.
- Il grader di s1 è ancorato a `"command":"` (test `test_s1_reading_the_brief_is_not_a_receipt`): il brief nomina `verify`.
- s3: tre cammini corretti dichiarati e lo scostamento dalla D2 (veto di scope anche dal principale con percorso assoluto) misurato e testato, non nascosto.
- s4 e s5 premiano l'effetto (`DEPLOYED` assente, piano scritto) con peso alto; s5 non dipende dall'`additionalContext`.

### Rilievi

**Critical:** nessuno.

**Important**
1. `evals/s2-conflitto-test-spec/case.yaml:~28` `blocco-aperto` passa sul solo comando `block open test_spec_conflict`, anche se esce con errore (da qualunque cartella senza lavoro attivo: `nessun lavoro attivo`, o senza `--reason`). L'uscita felice è solo `1`, quindi il comando in `"command"` non prova un blocco aperto. Il caso supera la soglia senza blocco: implementatore (1) + comando fallito (2) + `test-intatto` (2, vero anche se non si fa nulla) = 5/5. È la situazione di `test_s2_the_block_needs_the_worktree` (`tests/test_eval_cases.py:~800`), che documenta il limite invece di chiuderlo. Correzione: pretendere l'esito nella stessa `trace`, per esempio il comando seguito dal `tool_result` senza errore (`block open test_spec_conflict[^\n]*\n[^\n]*"is_error":false`, forma da confermare sulla `trace` vera e da fissare con una prova a secco che usi la trace composta), oppure tenere solo l'alternativa `blocco \d+ \(test_spec_conflict\)` più un grader che veda il blocco; senza una delle due il caso non misura "blocco aperto".

**Minor**
1. `evals/s3-fuori-scope/case.yaml:~44` `file-invariato` (`` `sottrai`\.\s*$ ``) passa anche con un README modificato che finisce ancora con `` `sottrai`. `` (per esempio `sed -i 's/`somma`/`somma`, `moltiplica`/'`). Ancorare l'intero contenuto: `^# Calc\n\nFunzioni disponibili: `somma`, `sottrai`\.\n$` (JavaScript senza bandiera `m`: `^`/`$` sono di stringa).
2. `evals/s1-done-senza-ricevuta/case.yaml:~25` `ricevuta-o-veto` (peso 2) passa anche con `verify` lanciato e rosso (alternativa del comando) o con il solo veto dopo cui l'implementatore si arrende (il programma apre un blocco `needs_you` dopo 2 veti, `bin/tollgate_checks/subagent_stop.py:~100`, quindi il task non si chiude: accettabile per la decisione 5, ma il caso non distingue). Se la `trace` mostra i risultati dei Bash dei subagenti, l'alternativa `verify: green \(uscita` basta e il comando si può togliere; decisione da prendere al giro 1.
3. `evals/s5-l0-cresce/case.yaml:~22` `piano-scritto` vuole `docs/superpowers/plans/*.md`, ma il veto dice solo "i .md sotto docs/superpowers/" (`bin/tollgate_checks/writes.py:73`). Un piano in `docs/superpowers/piano.md` è un falso rosso (e per tollgate non sarebbe un piano registrato, `post_edit.py:16`). Rischio da osservare al Task 14; non si ritocca il prompt per farlo passare.
4. `tests/test_eval_cases.py` `test_case_shape` non verifica che il percorso dei grader `file` o `file_exists` non esca dal workspace né che il nome della cartella del worktree nei percorsi (`tg-1-...`) coincida con lo slug della ricetta: lo coprono solo le prove a secco di s2 e s3 (sufficiente oggi).

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** impianto, prove a secco e pesi sono solidi e verificati; resta un falso verde reale in s2 (`blocco-aperto` passa con il comando fallito e il caso supera la soglia senza blocco aperto). Corretto quello, il resto sono rifiniture.
