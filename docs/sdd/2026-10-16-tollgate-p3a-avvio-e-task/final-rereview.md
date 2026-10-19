# Ri-revisione dei giri 1 e 2 della revisione finale (71f4230..1636d48)

Sola lettura. Ho letto regole, rilievi, ruling, report e diff una volta. Ho lanciato un solo gruppo di test mirati con `python3 -B`: `tests.test_check_cli_calls`, `tests.test_manifest`, `tests.test_bash`, `tests.test_start.StartNewTest` (124 test, OK). Ho anche provato `cli_calls._program_args` su una quindicina di comandi con uno script in `scratchpad` (fuori dal repo).

### Verdetti sui rilievi

**m1 + righe 65/66: `start` non toglie un ramo in uso o preesistente, e il test passa da `start()`.** INDIRIZZATO.
- `bin/tollgate_flow/gitw.py` (`create_branch`): `update-ref refs/heads/<ramo> <sha> ""` crea il ref solo se non esiste (ruling del giro 2 rispettato alla lettera). Falso se esiste o se git fallisce.
- `bin/tollgate_flow/start.py` (`_create`): se `create_branch` fallisce, `start` rifiuta e non cancella nulla. `delete_branch(main, ramo, base_sha)` si raggiunge solo dopo una `create_branch` riuscita, cioè su un ref creato da questa chiamata, e usa lo SHA atteso (`update-ref -d`). Gli altri percorsi di `_create` non cancellano rami: né il rifiuto per `wt.exists()` né quello per `mkdir`, né la cattura di `create_work`, che lascia ramo e worktree e li nomina.
- Ripresa invariata: `_restore_worktree` (`start.py:97-116`) non è nel diff.
- Test: `tests/test_start.py` (`other_session_takes_the_branch`) simula davvero la corsa. Un hook su `gitw._run` crea il ramo (con o senza worktree) subito prima della prima scrittura di `_create`. I due test verificano rifiuto con codice 1, ramo e worktree dell'altra sessione intatti, nessuna riga del lavoro e il rimando a `/tollgate:adopt`. `test_worktree_add_failure_refuses` copre il caso in cui il ramo creato qui viene tolto. Ho rieseguito `StartNewTest`: verde.
- Limite: la sola finestra residua è un `worktree add` che fallisce dopo una `create_branch` riuscita, e lì il ref è nostro: nessuna corsa.

**m2: connessione sqlite non chiusa in `CtxTest`.** INDIRIZZATO. `tests/test_statusline.py` usa `addCleanup(lab.close)`. Il report dice di aver cercato altre perdite con uno strumento esterno (nessuna) e di aver ottenuto 0 occorrenze in tre corse; la frase del piano (riga 6) è ora vera.

**Riga 150: `sleep(0.3)` fisso.** INDIRIZZATO. `tests/test_verify.py` (`_wait_gone`) fa polling a 50 ms con scadenza di 10 s e conta come morto anche lo zombie (`/proc/<pid>/stat`, stato `Z`). Il test `test_wait_gone_treats_a_zombie_as_dead` copre l'helper.

**m3: `cli_calls` e forme del programma.** INDIRIZZATO.
- `bash.script_index` (`bin/tollgate_analysis/bash.py`) salta le opzioni dell'interprete (`-B`, `-W x`, `-X x`) e dà `None` per `-c`/`-m`. `uses_tollgate_bin` la usa.
- `cli_calls._program_args` restituisce `(argomenti, certo)`. Con script o comando che è un'espansione (`$p`, `$(…)`, backtick, `SUBST_TOKEN`) vale come programma incerto: un subagente è negato sui sottocomandi del coordinatore, il coordinatore non lascia segnale (resta il rifiuto di `start`/`act`).
- Errore di parsing con `agent_id`: negato solo se il testo grezzo contiene `tollgate` e una parola tra `start`, `task`, `act`, `--checkpoint`.
- Falsi positivi: nessuno sui comandi legittimi. `verify` dell'implementatore nella forma `python3 '<bin con spazi>' verify`, anche dopo `cd … &&` e con pipe, dà `(['verify'], True)` e passa. Passano anche `python3 -B "<bin>" verify` e `p="<bin>"; python3 "$p" verify` (test). Comandi normali di un subagente (`pytest`, `python3 -m pytest`, `npm run start`, `make test`, commit con heredoc che contiene «tollgate: task 3 start», `FOO=1 python3 -B x.py task`, `python3 - <<PY`) danno `None`. Il coordinatore non è mai negato: il ramo di diniego richiede `event.agent_id`.
- Test dei tre casi del rilievo e dei casi leciti: `test_interpreter_options_before_the_script`, `test_subagent_cannot_hide_the_program_in_an_expansion`, `test_subagent_unparsable_command_naming_the_program_is_denied`, `ScriptIndexTest`. Rieseguiti: verdi.
- Effetto collaterale corretto: `effects` non nega più `python3 -B "<bin>" start 7` come script non tracciato.

**m4: `agents/implementer.md` con `tollgate` nudo.** INDIRIZZATO. Le righe usano `<programma>`, definito come la forma del brief (`python3 '<percorso>/bin/tollgate'`). `test_agents_and_skills_never_write_a_bare_program_name` copre agenti e skill; RED documentato nel report.

**m5: due frasi della spec rev 22.** INDIRIZZATO. Il diff riscrive la riga 333 (solo i rifiuti dei prerequisiti si raccolgono) e la 459 (revisione preparata, nessun confronto di orari, veto per codice diverso). Le due frasi ora combaciano con `start.py` e con `_common.awaiting_review`.

**m6: firma di `write_checkpoint` nel piano.** INDIRIZZATO. Il piano ora dice `note` obbligatorio per parola chiave, in accordo con `checkpoint.py:90`.

**m7: `start._fence` duplicata.** INDIRIZZATO. Rimossa; `start.py` usa `brief.fence`, e `import re` è stato tolto. `test_hostile_issue_title_and_body` resta verde.

**m8: percorso non quotato nel suggerimento di rebase.** INDIRIZZATO. `shlex.quote(str(wt))` in `start.py:159`. Il test controlla anche che il percorso contenga uno spazio.

**m10: errore di database dopo `worktree_add`.** INDIRIZZATO. `except (phases.WorkExists, sqlite3.Error, db.DbError)` in `_create`, con il messaggio che nomina ramo e worktree. Test: `test_create_work_database_error_names_branch_and_worktree`.

**m9, m11, m12, m13 e gli 8 rinviati (b).** INDIRIZZATI nel piano principale, nella tabella dei contratti: righe «Rinviati dalla revisione finale di P3a, da chiudere in P3b» (m9, m11, m12, m13, righe 55, 56 per le PR, 74, 102, 108, 133), «da chiudere in P3c» (riga 82) e «P4, P5» (riga 56 per `sentinel_issues`, riga 163). Tutti e otto i (b) sono presenti con il piano di destinazione corretto.

**Ruling del giro 2: ramo atomico con `update-ref <ref> <sha> ""`.** RISPETTATO (vedi m1).

**Ruling del giro 2: programma nei messaggi a runtime.** RISPETTATO. `_common.waiver_hint/explain`, `agents.py`, `send_message.py` e `checkpoint.next_step` usano `program_command`. Ho cercato nel repo `tollgate <sottocomando>` nudo: restano solo docstring, le etichette di errore «tollgate verify: …» di `verify.py` e `bash_rules.py:153`, che non sono istruzioni. `bin/tollgate` non ne contiene. `BareProgramInMessagesTest` è utile e non troppo largo: legge i letterali stringa con `ast`, esclude le docstring, il lookbehind lascia fuori `/tollgate:skill`, percorsi e nomi con trattino, e `(?!:)` lascia fuori le etichette «tollgate verify:». Le sue debolezze sono elencate sotto.

### Danni nuovi nel diff della correzione

Nessun Critical né Important. Quattro Minor:

1. **Minor, `tests/test_manifest.py` (fine del file).** `BareProgramInMessagesTest` è definita dopo `if __name__ == "__main__": unittest.main()`. Con `python -m unittest` e con `tests/run` viene trovata, ma con `python tests/test_manifest.py` non gira. Va spostata sopra il blocco `__main__`.
2. **Minor, `tests/test_start.py:29`.** `flow_start_naming()` è un helper nuovo e non è usato da nessuno.
3. **Minor, `BareProgramInMessagesTest.BARE`.** L'elenco dei sottocomandi non ha `stats`, `events`, `db`, `open-pr`, `gate`, `hook`: un messaggio futuro con uno di questi nudi non verrebbe preso. Non c'è oggi nessuna occorrenza. Non vede neanche le composizioni (`"tollgate " + sub`, `f"tollgate {x}"`). Accettabile per un guardrail di scrittura.
4. **Minor, `bin/tollgate_checks/cli_calls.py` (`_undecidable`).** Un subagente che lancia un suo script con una variabile e un sottocomando omonimo (per esempio `python3 "$ROOT/manage.py" start`, o `$HOME/bin/tool task`) viene negato con il messaggio «comando del coordinatore». È fail-closed e raro; il testo del diniego non spiega il motivo. Un cenno nel messaggio («se non è tollgate, scrivi il percorso senza variabili») basterebbe. Stesso discorso per il ramo del parsing fallito, che scatta con `tollgate` più `task`/`start` nel testo.

Nota di forma, non bloccante: `start.py:159` supera i 100 caratteri; la riga 6 del piano dice «un giro di correzione» mentre i giri sono due.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. Quattro Minor, tutti in test o in messaggi: possono essere ripresi con un commit di pulizia oppure rinviati.
