# Rapporto della correzione della revisione finale (p4-gate)

Commit: `5d166cb` (codice e test), `9bb2da1` (spec e piano principale).

## 1. I-1: `base-publish` rosso con la suite della base rossa
- Cosa: `_publish` restituisce un codice d'uscita: 1 se un comando di `result["commands"]` è
  `red`, 0 altrimenti. In `detect` dopo lo stato `failure` e il commento dell'issue (ordine
  invariato), in `protected` senza nessuna chiamata a gh. `publish` e `publish_from` lo
  propagano; `publish_from` senza `--publish` (solo lettura) restituisce lo stesso codice
  (scelta mia, per coerenza: il codice d'uscita riflette la suite anche senza pubblicare).
  Docstring di `publish` e `publish_from` aggiornate.
- File: `bin/tollgate_gate/baseids.py`.
- Test (`tests/test_gate_sentinel.py`): `BaseDetectTest.test_red_suite_exits_1_after_status_and_issue`,
  `test_green_suite_exits_0`; `BaseProtectedTest.test_protected_mode_publishes_nothing` (ora
  asserisce anche il codice 1), `test_protected_green_exits_0_without_writing`;
  `BasePublishProtectedErrorTest.test_protected_red_suite_fails_without_writing` (via
  `publish_from`, rosso 1 e verde 0, nessuna chiamata a gh); in `BasePublishFromTest`
  `test_valid_data_publishes_the_status_even_from_a_cache_hit` ora attende 1 e
  `test_without_publish_nothing_is_written` copre il rosso senza `--publish`.
- RED visto: sì (`python3 -B -m unittest tests.test_gate_sentinel`: 7 failures, `0 != 1` e
  `None != 0`), poi verde (51 test OK).
- Spec 9.1 (riga 853): «In entrambe le modalità il job `tollgate-base` è rosso se la suite della
  base è rossa (`base-publish` esce con 1); in `protected` non c'è uno stato `tollgate/base` e il
  segnale è il job (prova reale di P4, revisione finale).» `protect.sh` non cambia.

## 2. M-2: `base_test_ids = false` non esegue la suite della base
- Cosa: il controllo sta in `baseids.compute`, l'unica funzione chiamata da `cmd_base_ids`, che
  già carica la configurazione della punta (`config_sha=tip`, `cfg_repo=cwd`): con il componente
  spento non esegue né `setup` né comandi e scrive
  `{"v": 1, "tree": <albero>, "sha": <sha>, "ids": {}, "commands": {}}`. `cmd_base_ids` invariato
  (stampa «0 comandi»). Coerenza: `read_result` lo accetta (`{} <= names`), `_publish` lo tratta
  come verde (0); `verdict._base_ids` lo carica come `{}`, e `evaluate.base_ids` con il
  componente spento esce subito (nessun errore, nessuna voce oltre a `components_off`).
- File: `bin/tollgate_gate/baseids.py`.
- Test: `tests/test_gate_run.py::BaseIdsComponentOffTest.test_nothing_runs_and_ids_json_is_valid_and_empty`
  (CLI vera: nessun `ran.txt`, `ids.json` esatto, `load` = `{}`, `publish_from` = 0).
- RED visto: sì (`True is not false`: la suite girava).

## 3. M-6: `unverified` per un comando configurato vale rosso
- Cosa: `_command_state` restituisce `red` se lo stato è `unverified` e `spec.command` non è
  vuoto; la voce è `command_red` («il comando «verify» è rosso»). Vale anche in locale, dove
  `verify.py` scrive `unverified` solo per un comando vuoto come `run.py`.
- File: `bin/tollgate_gate/evaluate.py`.
- Test (`tests/test_gate_evaluate.py`): nuovo `test_unverified_for_a_configured_command_is_red`
  (con e senza `approve unverified-tests`). I tre test esistenti su `unverified`
  (`test_red_empty_uncounted_unverified`, `test_unverified_green_with_declared_act_and_attention`,
  `test_other_act_does_not_approve_unverified`) usavano `verify = "true"` con uno stato
  `unverified`, cioè proprio l'artefatto incoerente: ora usano `UNCONFIGURED_TOML`
  (`verify = ""`), come il CLI vero.
- RED visto: sì (`[] != ['command_red']` e `['command_unverified'] != ['command_red']`).

## 4. M-8: testo delle eccezioni su stderr codificato
- Cosa: `json.dumps(..., ensure_ascii=False)` del motivo in `verdict.main` (anche la riga «stato
  non scritto», stesso difetto due righe sotto) e in `cli.main` (riga 161: il rimando
  `cli.py:570-571` della revisione non corrisponde a questo file di 162 righe, l'unico punto è
  quello).
- File: `bin/tollgate_gate/verdict.py`, `bin/tollgate_gate/cli.py`.
- Test: `tests/test_gate_github.py::BoundaryTest.test_exception_text_cannot_start_a_workflow_command`
  (senza `--publish`, e con `--publish` e stato non scrivibile),
  `tests/test_gate_run.py::MainErrorsTest.test_message_cannot_start_a_workflow_command`.
- RED visto: sì (due subtest e `2 != 1` righe).

## 5. M-7: righe oltre 100 caratteri
- `bin/tollgate_flow/gh.py:9,28,108-110`, `bin/tollgate_flow/init.py:198,419`,
  `bin/tollgate_gate/evaluate.py:446`, `tests/fakegh.py:34`, `tests/test_init.py:244`.
- `init.py:198` è nel testo di `protect.sh`: il percorso va in una variabile locale `runs_path`;
  l'output di `_protect_script("main")` e `("dev-x")` confrontato con `cmp` prima e dopo:
  identico. `gh.py:28` produce lo stesso messaggio (`f"uscita {r.returncode}"`).
- Restano oltre 100 `tests/fakegh.py:46,230,231` (non elencate nel brief, quindi non toccate) e
  molte righe nei test degli script della prova e in `spikes/`.

## 6. Spec 1.2 e piano principale
- Spec 1.2, «Limiti dichiarati in P4»: tre voci nuove (M-1, M-3, M-4), ciascuna rinviata a P5.
- Piano principale: la riga «Minori rinviati dalle revisioni dei task di P4» (riga 98) resta
  nella tabella con il suo titolo e il rimando a un elenco sotto la tabella, «#### Minori rinviati
  di P4»: tre gruppi (Script, Test, Codice) con le stesse voci, una per punto, testo invariato
  (verificato ricomponendo la riga dallo stesso elenco nello script che l'ha divisa). Aggiunto il
  gruppo «Dalla revisione finale del ramo» con M-1, M-3, M-4, M-5, M-9, marcati «(revisione
  finale)» perché l'elenco ha già voci M-4 e M-9 di altre revisioni. Una riga di tabella non può
  contenere un elenco puntato: per questo l'elenco sta sotto.

## Suite (sul commit del codice, i documenti non sono letti dai test)
- `tests/run`: Python 3.11.16, 2465 test OK (2565 s); Python 3.13.5, 2465 test OK (1849 s).
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 2465 test OK.
- Output: una riga «guard: la PR è avanzata dopo l'evento…» su stdout da un test di `guard`
  che non ho toccato (preesistente).

## Dubbi
- M-2: un `ids.json` vuoto finisce in cache `tollgate-ids-<albero>`; se il componente viene
  riacceso, un `merge-base` con quell'albero vecchio usa la cache vuota e non confronta nulla.
  È il caso «cache scritta con una configurazione precedente» di M-1, ora dichiarato in 1.2.
  Con il componente spento, in `detect`, `tollgate/base` è `success` («suite della base verde»)
  anche se nulla è girato: il brief chiede verde e codice 0, ma la descrizione può ingannare.
- I-1 senza `--publish`: ho scelto codice 1 anche in sola lettura.
