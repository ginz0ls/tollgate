# Minor rinviate dal ledger (da mettere in triage nella revisione finale)

Task 1: minor (deferred): `sotto_tmp` non risolve i symlink (run-b1-checks.sh).
Task 1: minor (deferred): `bash_cat` esclude `eco` con una sottostringa (raccogli.py).
Task 1: minor (deferred): `latenza.py` crea il lavoro con `phases.create_work` e non con `start`.
Task 1: minor (deferred): `latenza.py` non prova che la serie Bash da subagente arrivi davvero in Python (stima indiretta).
Task 1: minor (deferred): `raccogli.py` classifica un Grep senza output_mode su un file non `.py` come `grep_files` (nella sonda il file è sempre src/app.py).
Task 1: minor (deferred): manca il campione `read_missing` (PostToolUseFailure di Read) in samples-b1.json; i test del Task 4 lo costruiscono da sé.
Task 1: minor (deferred): `prompt_id`, `tool_use_id` e `agent_id` veri restano nelle evidenze (identificativi casuali, non segreti).
Task 2: minor (deferred): `test_db_restore_interactive_eof_and_ctrl_c` dipende dalla disposizione di SIGINT ereditata (il figlio sul pty potrebbe rimettere SIG_DFL): fragile in CI o con `nohup`.
Task 2: minor (deferred): nessun test del dedup di `lookups.record` con `task=None` (una regressione da `IS` a `=` passerebbe).
Task 2: minor (deferred): `test_reset_plan_drops_task_lookups` non asserisce che le righe restino con task NULL né che una lettura nuova del nuovo task venga registrata.
Task 2: minor (deferred): `lookups.set_note` su un task inesistente non fa nulla e non segnala (il Task 6 controlla il task prima: `REFUSED`).
Task 3: minor (deferred): i separatori della nota sono la stringa esatta con uno spazio per lato (un tab non separa; il file risulta «non letto», fallisce in modo sicuro).
Task 3: minor (deferred): `approved: no` e `approved: off` contano come approvato (B2 scrive l'approvazione con una data).
Task 3: minor (deferred): `bash.read_targets` non conta `cat < f` (il parser scarta `<`, ruling del Task 3).
Task 4: minor (deferred): M1 la serie post_read_subagent misura il caso ripetuto (riga già in lookups), 250 ms è un limite inferiore.
Task 4: minor (deferred): M2 il controllo lavoro/research/worktree è scritto due volte, in runner.py e in lookup_rec.py.
Task 4: minor (deferred): M3 la via breve usa DEFAULTS per stale_minutes e non la configurazione del repo (pesa solo nel ripiego senza agent_id, spento).
Task 4: minor (deferred): M4 mancano i test della via breve con research_note spento e di lookup_rec con il componente spento.
Task 4: minor (deferred): M5 la via breve non fa sessions.touch né offlog.import_log e trova il lavoro dalla cartella (prescritto dal carry).
Task 4: minor (deferred): M6 due import separati di tollgate_analysis in runner.py; parametro tstate inutilizzato in start_impl nei test.
Task 5: minor (deferred): il modello della nota in agents/implementer.md:29-42 duplica research.submit_command e diverge nel segnaposto dell'ultima riga; il test copre solo titoli e delimitatore.
Task 5: minor (deferred): la regex di test_setup_proposes_web_permissions è larga («da sé» basta).
Task 5: minor (deferred): skills/setup/SKILL.md:20 una riga vuota spezza la lista.
Task 6: minor (deferred): il file della nota si scrive prima di set_note e il testo da stdin non ha limite di dimensione.
Task 6: minor (deferred): submit non sa chi lo chiama, quindi un subagente può consegnare la nota di un altro task running dello stesso lavoro (limite di progetto).
Task 6: minor (deferred): tests/test_research_cmd.py:63 test_submit_valid_note non asserisce il testo del messaggio (aperto dopo il giro 1, va al triage finale).
Task 6: minor (deferred): in apply.py la riga di continuazione della chiamata a write_atomic per spec-lens-stato.md è disallineata dopo il rinomino.
Task 7: minor (deferred): test_reminder_not_consumed_by_other_deny ripete due volte la stessa asserzione.
Task 7: minor (deferred): mancano test per fase diversa da execution (research_gate.py:91 non coperto), L2, PostToolUseFailure di Bash ed esenzioni via Bash.
Task 7: minor (deferred): bash_rules.py:16 importa _braces con noqa solo per test_check_bash.
Task 7: minor (deferred): research_gate.py:62-64 _rules_enforced tratta ogni OSError come interruttore spento (SKILL.md illeggibile → blocco spento senza traccia); distinguere FileNotFoundError. Da guardare al triage finale.
Task 8: minor (deferred): brief.py:192-193 con nota mancante e diff senza file (task no_changes) il brief scrive file None.
Task 8: minor (deferred): l'avviso sul TOLLGATE_ nel testo della nota sta solo in agents/implementer.md:26, non nel brief del task.
Task 8: minor (deferred): tests/test_brief.py:539 f-string senza segnaposto.
Task 9: minor (deferred): la copia del plugin per esclusione includerebbe file ignorati in radice come un futuro .env (oggi nessuno: verificato dal controller con git status --ignored).
Task 9: minor (deferred): fallisce in registra non copre claude --version e grep.
Task 9: minor (deferred): un cat con glob non registra i file toccati dal glob (read_targets non espande i glob); il rifiuto della nota lo dice e l'implementatore riapre con Read.
