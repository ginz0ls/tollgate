# Report Task 2
Implementato: SAVED_READERS tolto; SAVED_PATH accetta prefissi `< > , { [ @` e la sola cartella `tool-results[/]` (con controllo di fine percorso); `_swap_saved` e `_third_party` trattano anche `stderr`; riga 2 e intestazione di `scrivi_limiti` generiche in run-b1-flow.sh.
Test nuovi (RED poi GREEN, 10 fallimenti iniziali): bash_any_reader (inclusi `cat<` e `jq . <`), bash_on_the_folder_alone, bash_stderr, third_party_detects_bash_stderr, leaves_plain_bash, scrivi_limiti_heading_is_generic (b1) e _backend.
Verifica: `bash -n` ok; `python3 -B -m unittest tests.test_b1_scripts` 98 OK (evidenze committate verdi); `tests/run` exit 0 (suite-task-2.log).
Scostamenti: test dell'intestazione diviso in due metodi (b1, backend) perché ognuno usa il proprio banco.
