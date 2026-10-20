# Revisione Task 5 (949d1d3)

### Aderenza
- ✅ `config.py:312-345`: `rules`/`blocking_rules` in `PROFILE_DEFAULTS`, `blocking_rules` fuori da `rules` -> `ConfigError`, `AGENT_FORMS`, nome fuori forma -> `""` con l'avviso di m9 (forma sostituita nel testo, coerente con il test). Tipo errato (stringa) intercettato da `_set_key`.
- ✅ `profiles.py`: `blocking_rules`, `known_rules`, `final_specialists` (non vuoti, ordine, senza doppioni); `tollgate_analysis` non importa nulla di tollgate (`verdicts` importa solo `.report`).
- ✅ `verdicts.py`: `is_blocking` (Task 3) riusata, non duplicata (`verdicts.py:109-111`). Senza regole dei profili ogni `R-…` blocca (P3a invariato; test `test_no_declared_rules_every_r_rule_blocks`). Standard spento: nessun cambiamento (test).
- ✅ C8: `approved` dichiarato con rilievo scartato che poteva bloccare (`blocker`/`major`/gravità fuori elenco/non dict) -> non valido col messaggio alla lettera (`verdicts.py:115-119`); `moderate`/`minor` scartati non invalidano; test riscritto e nuovo test presenti.
- ✅ C18/C22: `parse_final_verdict` mette in `rejected` anche gravità fuori elenco con il valore com'è; `v` ignorato. Ultimo JSON con `outcome` (`json_candidates` dal fondo, `cands[0]`); `sha`/`code` obbligatori; `outcome` fuori da `ok|needs_fix|needs_you` o non stringa -> non valido.
- ✅ Verificatore: ultimo JSON con `results`, `sha`/`code`, `verification` valida, id sconosciuti ignorati e contati nei problemi solo se nessuno è valido.
- ✅ C4: fixture di `test_taskcmd.py` rinominate (righe 21-22 e asserzioni).
- ✅ `task_verdict` passa `blocking_rules`/`known_rules` dei profili attivi sul diff del task; diff illeggibile o senza commit -> lista vuota -> ogni `R-…` blocca (fail-closed).
- RED separato: assente nel flusso, ma ho ricostruito l'evidenza a posteriori (archivio di 0e7558c + i test di 949d1d3, in scratchpad): 19 errori/fallimenti su test_verdicts, 4 su test_config, 2 su test_profiles, 1 su test_check_task_verdict. I test nuovi sono quindi discriminanti; lo scostamento di processo resta ma non lascia test vacui. Non è un rilievo di qualità del codice.

### Punti di forza
- Fail-closed coerente ovunque (diff illeggibile, gravità illeggibile, regola ignota, non dict).
- Messaggi alla lettera, dataclass chiare, `_sha_code_problems` condiviso tra finale e verificatore.
- Test con casi limite (id sconosciuti soli, `verification` sbagliata, gravità `critical`, ultimo oggetto vince, `findings` non lista).

### Rilievi
**Critical:** nessuno.

**Important:** nessuno.

**Minor**
1. `bin/tollgate_core/config.py:342`: `re.match(r"^…$")` accetta un `\n` finale (`"a:reviewer-web\n"` passa: verificato). Il nome diventa `agent_type`. Usare `re.fullmatch(rf"[^:\s]+:{form}-[a-z0-9-]+", value)`.
2. `bin/tollgate_checks/task_verdict.py:245-257`: il percorso `_task_files` non è esercitato da nessun test: `BlockingRulesTest` (`tests/test_check_task_verdict.py:371-379`) attiva `web` con `profiles.active`, quindi funzionerebbe anche con `_task_files` che restituisce sempre `[]`. Manca un test con profilo attivato solo da `paths` (file nel diff) e uno col diff illeggibile che resta bloccante.
3. `task_verdict.py:245-257` ripete `resolve_ref(f"{c0}^") or EMPTY_TREE` di `taskcmd._range` (`taskcmd.py:198`) e `post_bash.py:59`. Piccola duplicazione (strato `checks` non può importare `flow`); un helper in `tollgate_core.git` per «base del task» eviterebbe la terza copia. Inoltre `import json` è dopo `from pathlib` (`task_verdict.py:229-233`), fuori dal gruppo stdlib.
4. `tests/test_verdicts.py` (blocco `if __name__ == "__main__": unittest.main()` a metà file, righe ~658-660 del diff) e `tests/test_profiles.py`: le classi nuove (`FinalVerdictTest`, `VerifierResultsTest`, `RulesTest`) sono definite DOPO `unittest.main()`, quindi `python3 tests/test_verdicts.py` non le esegue (la discovery di `tests/run` sì). Spostare il blocco in fondo.
5. `verdicts.py:168-185`: `parse_final_verdict` dà `valid` con `ok` e rilievi scartati che potevano bloccare, e `needs_fix` senza rilievi validi. Non richiesto dal brief; il consumatore (Task 7+) deve gestirlo: da annotare lì, non qui.
6. `verdicts.py:202`: un risultato non-dict o senza `id` aggiunge il problema «ogni risultato ha un id» una volta per elemento (rumore ripetuto nel veto). Dedup banale.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e decisioni C4/C8/C18/C22 (8, 9) rispettati e verificati sul diff; test discriminanti (verificato a posteriori su 0e7558c). Solo rifiniture Minor (fullmatch, test del percorso `_task_files`, posizione di `unittest.main()`).
