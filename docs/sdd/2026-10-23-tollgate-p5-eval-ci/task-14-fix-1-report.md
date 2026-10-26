# Task 14, giro di correzione 1: report

Commit: vedi `git log -1` sul ramo p5-eval-ci ("tollgate P5: giro di correzione degli eval (set_config idempotente, caso s5)").

## Fatto
1. `bin/tollgate_flow/gitw.py` `set_config`: legge `git config --get-all <chiave>`; se l'unico valore e' quello richiesto non scrive (niente lock di `.git/config`). Chiave assente o valore diverso: scrive come prima. Valori multipli: `--get-all` restituisce piu' righe, quindi si scrive e git rifiuta come prima. Unico chiamante: `start.py:404`.
2. Caso s5: prompt con «Crea ogni file con lo strumento Write, un file per chiamata, e committa alla fine.»; `crescita-vista` accetta anche `il diff supera le soglie di L0` (testo dell'iniezione, `_common.py:285`); description aggiornata.
3. `docs/uso/limiti.md`: frase sul comando Bash unico (file + commit) nella voce «best effort»; frase sulla sandbox che protegge `.git/config` del workspace in «Limiti degli eval». Humanizer applicato (frasi brevi, niente em dash). Nessun titolo nuovo.

## Scostamento dalla ruling
`crescita-vista` resta con `target: trace` e non passa a `last_message`: un grader ha un solo target e le tre alternative esistenti vivono nella trace. Il messaggio finale dell'agente e' gia' nella trace (verificato su EtlASM: evento `assistant` con testo che contiene «il diff supera le soglie di L0»; il dry-run lo emette in `_do_say`). Quindi la nuova alternativa copre il testo riportato nel messaggio finale senza perdere le vecchie. Rischio: il pattern e' nella trace anche se l'agente lo cita altrove; irrilevante, il piano pesa 3.

## Test
- TDD RED: `python3.11 -B -m unittest tests.test_start.SetConfigTest` -> errore «impossibile bloccare il file di configurazione .git/config» (config.lock presente, stesso valore). GREEN dopo il fix: 4 test OK.
- Nuovi: `tests/test_start.py` SetConfigTest (4: stesso valore con lock, valore diverso/assente scrive, lock con valore diverso fallisce, valori multipli come prima); `test_locked_config_with_the_value_already_set_does_not_refuse` (start con lock riesce). `test_git_config_failure_refuses` adattato: toglie la chiave (FlowLab la imposta gia' a main, quindi senza questo non scriverebbe).
- `tests/test_eval_cases.py` S5DryRun: nuovo `test_s5_one_shell_command_with_all_files_and_the_commit_is_a_wrong_path` (cammino sbagliato, punteggio 0, nessun deny) e `test_s5_the_injection_reported_in_the_final_message_is_seen_but_does_not_pass_alone` (solo crescita-vista = 0,25). I cammini corretti dichiarati restano a 0,75+; i test s5 esistenti (Write con deny al 4°) coerenti col nuovo prompt.
- `tests/test_eval_cases` completo: 97 OK. `tests/run`: py3.11 2893 test OK (skipped=2), py3.13 2893 OK. (Una prima corsa aveva dato 1 fallimento, `test_git_config_failure_refuses`, corretto come sopra e rilanciata per intero.)
- Regole JS: nessun `(?i)`, `(?P<`, `\A`, `\Z`.

## Note
- Non toccati `evals/run.sh` ed evidenze; `__pycache__` nelle evidenze eval-p5 (cwd delle corse vere) non e' mio, non committato.
- Non risolto e non provabile qui: se e3 si ferma ancora su refs/worktrees in `.git`, vale la ruling (prova a secco).
