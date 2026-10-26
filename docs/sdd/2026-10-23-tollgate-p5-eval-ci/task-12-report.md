# Task 12: report

Commit 4625ac3. Status DONE_WITH_CONCERNS (vedi dubbi).

## Implementato
- `README.md`, `docs/uso/{installazione,comandi,modalita,limiti,emergenze-e-aggiornamenti,eval-e-ci}.md`, scritti dal codice reale (skill, argument-hint, CLI, run.sh, ci.yml, PINS, case.yaml). Humanizer applicato (niente em dash, grassetti, emoji, elenchi con titolo in grassetto).
- `tests/test_docs.py`: test_docs_exist, test_every_skill_documented, test_limits_match_spec_1_2 (spec letta: 1.2 + le due voci di 17; normalizzazione: senza backtick, spazi compressi, senza . ; : finali, casefold; uguaglianza di insiemi), test_no_local_paths, test_relative_links_exist, test_update_pins_documented.
- `bin/tollgate_core/cli.py`: riga `limiti della garanzia: <radice>/docs/uso/limiti.md` (assoluta, da `Path(__file__)`), stampata anche senza DB e senza lavori, mai in `--json`; frase detect letta da `work_items.gate_mode` solo per la stampa (lavori attivi del repo corrente, o tutti fuori da un repo). `tests/test_cli.py`: test_status_points_to_limits, test_status_without_db_points_to_limits, test_status_detect_sentence.

## TDD
RED: `python3.11 -B -m unittest tests.test_docs tests.test_cli -k status` -> failures=11/errors=2 (docs assenti) e 2 failure in test_cli. GREEN: stessi test, 28 OK dopo i testi.
Suite: `tests/run` 3.11: 2862 test OK (skipped=2); 3.13.5: 2862 OK (rc=0), log nello scratchpad (t12-suite2.log). Un primo giro aveva 1 fallimento (vedi scostamenti).

## Scostamenti dal piano
- `tests/test_eval_cases.py:1098` (Task 8-10): `re.search(r"task: 2 done$", ...)` assumeva che `status` finisse con la riga dei task; con la nuova riga finale falliva. Aggiunto `re.M`. I grader di `evals/*/case.yaml` non dipendono dalla fine dell'uscita di status (verificato con grep).
- `eval-e-ci.md`: i casi extra sono quattro (e1, e3, e4, e5): la directory e2 non esiste, la documentazione non ne parla.
- Il piano parla di «e1-e5»; non ho cambiato nulla nel repo per questo.

## Dubbi per il controller / Task 15
- `limiti.md` segue la rev 25 (24 titoli: 22 voci di 1.2, di cui `Le PR da rami che non sono tg/*`, più 2 di 17). Cinque voci sono chiuse o ridotte da P5 (azioni per SHA, M-1, M-3, M-4, M-5): ho tenuto i titoli della rev 25 e nel corpo scritto lo stato dalla 0.2.0. Il Task 15 che scrive la rev 26 deve aggiornare insieme spec e `limiti.md` (il test li tiene uguali). Il paragrafo finale «Limiti degli eval» è un `##`, fuori dall'insieme.
- Testo non verificato su un marketplace vero: `installazione.md` non dà un comando di `marketplace add` né un indirizzo, perché non so dove verrà pubblicato.
- Nessun risultato né costo degli eval nella documentazione (li aggiunge il Task 14).
