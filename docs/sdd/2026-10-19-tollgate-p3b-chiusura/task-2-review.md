# Revisione Task 2 (b5a3630..4ef3f0a)

### Aderenza
- ✅ `sessions.cli_session(..., argv=None)` (`bin/tollgate_core/sessions.py:126-154`): con `argv` la voce vale solo se `entry["argv"] == argv` e si toglie con `_consume_signal` (tmp + `os.replace`, `OSError` ignorato, tocca la sola voce del sottocomando); senza `argv` resta lettura che non consuma (C2). Un argv diverso non consuma (`:143`, test `test_argv_mismatch_refused`).
- ✅ `start.start` / `actapply.apply_act` ricevono `argv` per parola chiave e lo passano (`start.py:315`, `actapply.py:118`); `cli.main` passa `argv[argv.index(cmd):]` (`cli.py:161-164`, `:198`, `:226`). Coincide con ciò che registra l'hook (`cli_calls.py:~88`, `args[args.index(sub):]`): il solo parser globale è `--version`, quindi il sottocomando è sempre il primo token non-opzione da entrambe le parti.
- ✅ `_SIGNALLED` e `_COORDINATOR_ONLY` identici al piano (`cli_calls.py:15-17`). `review` negato ai subagenti ma non segnalato (solo il coordinatore lo lancia, nessuna lettura di sessione). `task` resta non segnalato.
- ✅ Testo di diniego al parsing fallito alla lettera della decisione 2 (`cli_calls.py:75-79`), senza nome di sottocomando. `cli_calls` non solleva: `note_cli_call` resta immutato (try/except OSError).
- ✅ `abandon` con `work_id = None` (`acts.py:75`), come `adopt` e `cleanup`.
- ✅ `report.MAX_SCAN_CHARS = 65536`, `MAX_DECODES = 500`; `rfind("{", lo)` con `lo = max(0, len-MAX)` e condizione `pos >= lo` corretta anche quando `rfind` restituisce -1 (`report.py:28-47`). Ho verificato che il test temporizzato discrimina il tetto di decodifiche: con `MAX_DECODES` disattivato lo stesso input impiega 2,9 s (soglia 1 s). Un JSON seguito da 600 `{` non viene trovato (fail-closed, come da decisione 23).
- ✅ `git.CACHE_DIRS` e salto per qualunque segmento del percorso (`git.py:~320`); stessa funzione usata da `subagent_start`/`_common.fingerprint_changed`, nessuna copia della logica.
- ✅ Strati rispettati: `report.py` senza import di tollgate; `cli_calls`/`acts` solo `record`/`inject`.
- ✅ `tests/flowkit.py` non toccato: `FlowLab.cli` scrive il segnale con lo stesso argv passato alla CLI, quindi resta compatibile (verificato a `flowkit.py:69-74`). Scostamento giustificato.
- ⚠️ Non verificato da me: `tests/run` (1007 test su 3.11 e 3.13) è affermazione del report; non l'ho rilanciato per regola.

### Punti di forza
- Modifica chirurgica e nei file previsti; il confronto di `argv` è fail-closed (un `$VAR` negli argomenti non coincide e rifiuta).
- Test aggiuntivi oltre al brief (`not_consumed`, `keeps_other_subcommands`) che coprono la semantica di C2; test del diniego esteso a `cleanup`, `abandon`, `adopt`.
- `_consume_signal` non fa fallire la chiamata né cancella le voci degli altri sottocomandi.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `tests/` non esercita il passaggio reale di `argv` da `cli.main` (`_hook_argv`): `FlowLab.cli` riscrive il segnale a ogni chiamata, quindi nessun test dimostra che un secondo `start`/`act` lanciato senza hook venga rifiutato dalla CLI né che `argv` con opzioni (`start 7 --level L1`) coincida. Aggiungere un test in `test_flowkit`/`test_cli_start` che chiami `subprocess` due volte con un solo `note_cli_call`.
2. `bin/tollgate_checks/cli_calls.py:3-5`: il docstring ora è incoerente («`start` e `act`, i soli sottocomandi… (e quelli di chiusura…)») e la riga supera le 100 colonne. Riscrivere: «per i sottocomandi in `_SIGNALLED`».
3. `bin/tollgate_core/cli.py:226-227`: continuazione di `apply_act(...)` indentata male (allineata a 46 colonne invece che alla parentesi).
4. `sessions.py:111-121`: se la rimozione fallisce (`OSError`) la voce resta e il comando è ripetibile senza hook. È previsto da C2, ma il caso non ha test. Inoltre lettura-modifica-scrittura non atomica tra due hook concorrenti (già presente in `note_cli_call`).
5. `cli_calls.py:73-79`: con `review` e `sync` tra le parole del coordinatore, un comando non analizzabile di un subagente che contenga «tollgate» e «review» come parole comuni viene negato; il nuovo testo spiega l'uscita. Accettato dalla decisione 2.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** tutti i requisiti del brief e di C2/decisioni 2, 3, 22, 23 sono implementati con le firme richieste e coperti da test che discriminano; restano solo rifiniture minori (test del passaggio CLI di `argv`, docstring, indentazione).
