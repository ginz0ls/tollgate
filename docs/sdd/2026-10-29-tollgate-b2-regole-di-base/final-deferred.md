# Minori rinviati di B2 da sottoporre al triage

Task 1: minor (deferred): test_unreadable_switch_warns_and_logs_once non verifica che `_UNREADABLE` preceda l'avviso normale né che la seconda modifica (già avvisata) non lo inietti di nuovo.
Task 1: minor (deferred): research.py:57 — `"null"`, `"~"`, `"|"` tra apici ora valgono vuoto (coerente con `"false"`), senza test.
Task 1: minor (deferred): lookups.py:183 — la docstring di `rules_enforced` cita `task review`, il chiamante è `taskcmd.py:353`.
Task 2: minor (deferred): tests/test_taskcmd.py:476,491,660, tests/test_fixtask.py:180 e tests/test_criteria_p3a.py:114 usano ancora la radice vera in `review_prepare`; non asseriscono sulla gravità e sono verdi con il file di prova (oggi non dipendono dall'interruttore).
Task 2: minor (deferred): tests/test_eval_cases.py ~957 (`s3_the_veto_does_not_depend_on_the_starting_folder`) senza `*self.PREP`: l'asserzione «file fuori scope» regge perché il veto contiene entrambi i motivi; con PREP il motivo sarebbe isolato.
Task 3: minor (deferred): tests/test_rules_base.py:80-84 `test_model_name_rule` riconosce R-BASE-04 da parole italiane: si rompe se l'utente la riformula.
Task 3: minor (deferred): SKILL.md:7 «un difetto si segnala una volta sola» non è nel brief del Task 3, coerente con la decisione 8 e la Ruling D3.
Task 4: minor (deferred): i test di pagina e «Blocca?» non controllano che «N.» coincida con l'id tra parentesi.
Task 4: minor (deferred): test_page_explains_what_changes confronta frasi quasi alla lettera, fragile alle riformulazioni.
Task 4: minor (deferred): base.md:9 «agente» non spiegato.
Task 5: minor (deferred): nessun test confronta la data della riga «Approvata…» della pagina con `approved` della skill.
Task 5: minor (deferred): docs/profili/base.md:50-54 «Due… sono state tolte» convive in modo contorto con la regola rimessa.
Task 5: minor (deferred): docs/profili/verifiche/base-fonti.md:3 cita ancora il commit b17cbf0 della prima verifica.
Task 6: minor (deferred): gli agenti dicono solo «la gravità del brief»; nel final-reviewer manca una fonte di gravità (frase inerte, come voluto da D6).
Task 6: minor (deferred): nell'implementatore si è persa l'istruzione di leggere anche i file chiamanti (scelta della decisione 11; R-BASE-01 chiede solo i file modificati).
Task 6: minor (deferred): tests/test_check_final_review.py `test_rejected_report_leaves_trace` ora ha `plugin_root=ROOT` (radice vera) perché `_final_rules` la legge; l'esito non dipende dall'interruttore (il riporto è rifiutato prima), ma è un test sulla radice vera da valutare nel triage.
Task 7: minor (deferred): il titolo «# Regole di base (versione 1)» nelle trascrizioni non distingue il precaricamento da una lettura con Read o da un incollato nel prompt: il rapporto lo deve dire.
Task 7: minor (deferred): in `prepara` il controllo dell'interruttore viene dopo `rot` e `mkdir "$OUT"`: un rifiuto sposta da parte le evidenze precedenti (senza perderle).
Task 7: minor (deferred): flowreg precarico cerca agent_transcript_path nello stream-json, dove non c'è con Claude Code 2.1.314: le trascrizioni dei subagenti stanno in ~/.claude/projects/<cartella>/<sessione>/subagents/agent-<agent_id>.jsonl (da B3 in poi, cercarle lì).
Task 7: minor (deferred): registro-1/comandi-modello.txt:1,7 contiene il percorso /home/USER/MEGA/BIZ/VIBE/... (struttura delle cartelle di lavoro, già anonimizzata nell'utente).
Task 8: minor (deferred): piano principale, sezione 10, riga del rinvio 31: «gli ultimi tre» usano una cartella al posto di SKILL.md, ma vale solo per i primi due (test_missing_switch_no_unreadable_event toglie la cartella).
Task 8: minor (deferred): piano principale, sezione 3: «se `rules-<area>` si precarichi», errore di grammatica.
Task 8: minor (deferred): spec rev 28 e piano, sezione 10: «la n. 11 tolta» si confonde con la R-BASE-11 vera; scrivere «la bozza n. 11».

## Rinvio di B1 da rivalutare con il blocco acceso

B1, rinvio 37 (Task 9: minor (deferred)): un `cat` con glob non registra i file toccati dal glob (`bash.read_targets` non espande i glob); il rifiuto della nota lo dice e l'implementatore riapre con Read. Con il blocco acceso costa un giro di rifiuto. (Nella prova reale di B2 l'implementatore ha letto config.toml con `bash_read` e gli altri file con Read: nessun glob.)
