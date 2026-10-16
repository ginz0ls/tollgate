# Task 14 — Controlli `SessionStart` e `UserPromptExpansion` (atti)

**Status:** DONE_WITH_CONCERNS
**Commit:** `3c8f44d` tollgate P2: controlli di SessionStart e degli atti dell'utente
**Ramo:** `p2-guardrail` (worktree `.claude/worktrees/p2-guardrail`)

## Implementato

- `bin/tollgate_checks/_common.py`: `repo_key_of`, `orphan_tg`, `governing_work`, `is_docs_md`, `locked_docs`, `waiver_hint`, `explain`, `status_lines`. `_inside` non è stato aggiunto: il Task 14 non la usa (carry, «Task 15»).
- `bin/tollgate_checks/session.py` (`session_start`, ordine 10): scrive `expire_acts`; interrompe i subagenti `running` di sessioni non vive (`subagent_interrupt`); lega la sessione quando il `cwd` è nel worktree di un lavoro attivo e la sessione non è ancora legata (`bind`); inietta stato, blocchi, conteggio task e checkpoint, oppure, per un ramo `tg/N-*` senza lavoro, il suggerimento `/tollgate:adopt #N`.
- `bin/tollgate_checks/acts.py` (`prompt_expansion`, ordine 10): solo `command_name` `tollgate:*` con tipo in `acts.ACT_TYPES`. Oggetto e target secondo la decisione 15 (`command_args` con `shlex`). Oggetti non validi o argomenti mancanti producono un'iniezione «atto non registrato», senza atto. `off`/`on` restano al wrapper.
- `bin/tollgate_hooks/apply.py` non è stato modificato: le operazioni `expire_acts`, `bind`, `subagent_interrupt`, `act` esistevano già.

## Test ed esiti

- RED (prima dei moduli): `python3 -B -m unittest tests.test_check_session tests.test_check_acts` → `Ran 12 tests`, `FAILED (failures=5, errors=4)`.
- GREEN (dopo i moduli): stesso comando → `Ran 12 tests`, `OK`.
- `tests/run`: `python3.11` e `python3` (3.13.5) → `Ran 416 tests`, `OK` in entrambi (404 precedenti + 12 nuovi).
- Registro: `registry.load('tollgate_checks')` carica `acts` e `session`, nessun modulo rotto.

## Scostamenti dal piano

- `session.py`: il piano ricontrollava con `ctx.work_for_path(event.cwd)` che il lavoro fosse quello del percorso. Quel controllo è ridondante: quando la sessione non è legata, `runner.run_hook` imposta già `ctx.work` da `work_for_path(cwd)`. È stato tolto il controllo duplicato, il comportamento è invariato.

## Autorevisione

- Import: tutti usati (verifica a mano, pyflakes non installato).
- Nessun `__pycache__` nel repo (`-B` ovunque).
- Il test di legame verifica anche il segnalino `bound/<sessione>`.
- Le funzioni di `_common.py` non usate da questo task (`governing_work`, `is_docs_md`, `locked_docs`, `waiver_hint`, `explain`) non hanno test qui: le usano i task successivi.

## Dubbi

- Output non pulito: `tests/run` su 3.13 stampa `ResourceWarning: unclosed file` dalla `subprocess.Popen` in `tests/test_wrapper.py` (esistente, non toccata da questo task). Non l'ho corretta per il minimo impatto; va sistemata a parte (chiudendo gli stream del `Popen`).
- `approve spec` richiede il target (numero di fette) per la decisione 15, quindi `/tollgate:approve spec` senza argomento viene rifiutato. È coerente con la spec («`approve spec <fette>`»).

## Fix round 1

Commit `37dad52`. Ogni punto è partito da un test che falliva (RED: `Ran 28 tests`, `FAILED (failures=8)` sui test nuovi e modificati), poi la correzione (GREEN: `Ran 28 tests`, `OK`).

1. **`locked_docs` (`_common.py`).** La spec e il piano sono bloccati solo se la fase è dopo la loro scrittura: `_rank(fase) > _rank("spec_audit")` per la spec, `> _rank("plan")` per il piano (ordine di `phases.SEQUENCES`). Con `blocked` vale `phase_before_block`. Il file di approvazione resta il requisito per la spec. Dopo `reopen spec` o `reopen plan` la fase torna indietro e i file tornano modificabili, anche se l'approvazione resta come storico. Test in `tests/test_check_common.py`: approvata e fase avanzata → bloccata; ritorno alla fase della spec con il file presente → non bloccata; piano in execution → bloccato; dopo `reopen_plan` → non bloccato; blocco con `phase_before_block` = `spec_audit` → non bloccato.
2. **Decisione 15 (`tests/test_check_acts.py`).** Aggiunti i test richiesti: target di `effect`/`finding`/`level`/`rounds`/`spec`; nessun target per `plan`/`rebase`/`unverified-tests`; `reopen spec|plan`; `resolve` anche con `writer`; `abandon #N`; rifiuti (`approve spec`, `approve waiver`, `approve effect` senza argomento, `reopen` senza o con oggetto errato, `resolve` senza argomento, `adopt abc`, `abandon x`); `finish` e `approve pr` da sessione non legata; `args` con virgolette conservate intere; `cleanup` con `work` nullo. Nota: questi test passavano già al RED, perché descrivono il comportamento corretto già presente. Sono test di caratterizzazione.
3. **Messaggio (`acts.py`).** «atto registrato» diventa «atto ricevuto». Test: il testo contiene «atto ricevuto (approve waiver w-7-1)» e non «registrato».
4. **Checkpoint (`session.py`).** Nuova funzione `compose`: tiene le ultime righe del checkpoint entro il budget (≤ 10 righe, ≤ 1.500 caratteri), scartando le prime. Test con 40 righe: l'ultima («Prossimo passo: task 3 ULTIMO») compare nell'iniezione.
5. **`orphan_tg`.** Se `repo_key` è `None`, restituisce `None`. Test: origin rimosso, ramo `tg/7-demo` senza lavoro → nessun orfano.
6. **`expansion_type` (`acts.py`).** Se il campo è presente e diverso da `slash_command`, nessun atto. Test: `other` → nessun atto; campo assente → atto registrato.
7. **ResourceWarning (`tests/test_wrapper.py`).** Il `subprocess.Popen` di `test_watchdog_is_capped_at_85` è dentro `with`, così le pipe si chiudono. Nessun altro `Popen` non chiuso nella suite. Il punto «Dubbi» sopra è quindi risolto.

**Comandi e output:**
- Mirati: `python3 -B -m unittest tests.test_check_common tests.test_check_acts tests.test_check_session` → `Ran 28 tests`, `OK`.
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` → `Ran 432 tests`, `OK`, nessun output.
- `tests/run` → python3.11: `Ran 432 tests`, `OK`; python3.13.5: `Ran 432 tests`, `OK`; nessun output di warning.

**File:** `bin/tollgate_checks/_common.py`, `bin/tollgate_checks/acts.py`, `bin/tollgate_checks/session.py`, `tests/test_check_common.py` (nuovo), `tests/test_check_acts.py`, `tests/test_check_session.py`, `tests/test_wrapper.py`.
