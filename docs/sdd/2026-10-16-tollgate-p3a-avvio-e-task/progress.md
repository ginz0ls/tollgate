# SDD ledger — plan: docs/superpowers/plans/2026-10-16-tollgate-p3a-avvio-e-task.md

Spec: docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md (rev 21). Worktree: .claude/worktrees/p3a, ramo p3a-avvio-e-task, base 81ce50c. Baseline tests/run: 692 test OK (python3.11 e python3).

Ruling: pre-flight scan delegato a un analista sonnet in sola lettura (preflight-scan.md), giudicato dal controller prima del Task 2; corre in parallelo al Task 1, che non scrive codice di prodotto — come in P2 — costo se sbagliato: un conflitto sfuggito emerge nelle revisioni dei task.
Task 1: dispatched (sonnet), base 81ce50c
Task 1: implementer DONE, commit bc23a85; review dispatched (sonnet)
Ruling: V1 sì — le skill del Task 10 chiamano il programma come "${CLAUDE_PLUGIN_ROOT}/bin/tollgate" tra virgolette; la riga «tollgate: programma …» di UserPromptExpansion (Task 2) resta e le skill la citano come ripiego — esito sperimentale, la decisione 3 prevede entrambe — costo se sbagliato: una skill che non trova il programma, visibile al primo uso.
Ruling: V3 sì — decisione 2 confermata (segnale cli/<session>.json scritto da PreToolUse e visibile al comando Bash che segue); il Task 2 procede senza strada alternativa — costo se sbagliato: start e act apply rifiutano «sessione non riconosciuta», visibile nella prova del Task 13.
Ruling: V4 — marketplace.json del Task 10 nella forma che passa `claude plugin validate --strict`: description di primo livello, author nella voce del plugin, più "author": {"name": "sAInapse"} in plugin.json (già previsto); test_manifest controlla anche description e author — il piano dice «oppure i campi che V4 ha indicato come validi» — costo se sbagliato: nessuno, campi in più accettati.
Ruling: V2 (CLAUDE_CODE_SESSION_ID presente nell'ambiente di Bash; CLAUDE_PLUGIN_ROOT no) solo informativo: la decisione 2 non cambia in P3a (non verificato che coincida con il session_id degli hook); nota nella rev 22 come possibile semplificazione futura — costo se sbagliato: un meccanismo più complesso del necessario, nessun difetto.
Ruling: le due rifiniture minori della revisione del Task 1 (riproducibilità di V3/V4, frase su CLAUDE_PLUGIN_ROOT negli hook) entrano nel giro 1 insieme all'Important — basso costo, rapporto più esatto (feedback dell'utente: miglioramenti utili e a basso costo si fanno) — costo se sbagliato: nessuno.
Task 1: fix round 1/5 (3 addressed, 0 open — V4 su plugin.json verificato, riproducibilità, CLAUDE_PLUGIN_ROOT; commits bc23a85..c301c86)
Task 1: minor (deferred): la controprova di `--strict` sul solo plugin.json è nel rapporto senza un log dedicato.
Task 1: complete (commits 81ce50c..c301c86, review clean)
Ruling: V4 confermato dal giro 1 — `--strict` richiede author sia in plugins[0] sia in .claude-plugin/plugin.json; già in carry.md per il Task 10 — costo se sbagliato: nessuno.
Ruling: V5 — NotebookEdit usa tool_input.notebook_path senza file_path; bin/tollgate_hooks/adapter.py:66 già lo gestisce; voce della sezione 16 chiusa nella rev 22 (Task 14) — costo se sbagliato: nessuno.

## Scan pre-flight (preflight-scan.md: 21 conflitti, C1 e C5 bloccanti) — ruling del controller
Ruling: C1 — tollgate_core/cli.py è la radice di composizione (entrata di bin/tollgate, importa già tollgate_hooks.runner da P2): test_layers esenta solo cli.py; il resto di tollgate_core non importa flow/hooks/checks; vincolo riscritto nella rev 22 (sezione 3) — spostare il dispatch toccherebbe P1/P2 senza beneficio — costo se sbagliato: un import verso l'alto in cli.py, confinato e testato.
Ruling: C5 — verificato dal controller (sola struttura, nessun valore sensibile): ~/.claude/plugins/installed_plugins.json ha version 2 e plugins["superpowers@claude-plugins-official"] = lista di voci con version "7.0.0", installPath, scope; la decisione 7 regge. In più, a basso costo: prereq cerca prima la chiave esatta, poi qualunque chiave che comincia con "superpowers@", e prende la versione più alta; JSON di forma diversa → None (rifiuto con messaggio chiaro). Esito nella rev 22 (11.1) — costo se sbagliato: start rifiuta con un messaggio esplicito, correggibile con una costante.
Ruling: C2 — Task 6 aggiorna tests/test_db.py:140 a str(db.latest_version()) — costo: nessuno.
Ruling: C3 — Task 7 generalizza in report.py una funzione pubblica json_candidates(text, key) (con _candidates che la chiama con "status"); verdicts.py la usa — evita duplicazione e import di un nome privato — costo: nessuno.
Ruling: C4 — ordine di start: toplevel → fetch (esito annotato, non ancora rifiuto) → ramo predefinito → tollgate.toml (rifiuto «non attivo») → cli_session → find_active: se attivo, ripresa (Task 4: rete, gh, stati, sporco = avvisi); altrimenti fetch fallito = rifiuto e poi prerequisiti e controlli — spec 6.1 («in ripresa i passi 0 e 1 cambiano») e 12.4 — costo se sbagliato: un rifiuto/avviso in ordine diverso, visibile nei test.
Ruling: C6 — active.register riceve force: bool = False; start lo usa con extra=[wt]; test in test_active_roots — altrimenti il worktree resta fuori dal registro fino a 300 s — costo: nessuno.
Ruling: C7 — gh.auth_ok(state, repo) -> bool; commit_state usa `gh api repos/{owner}/{repo}/commits/<sha>/status` con cwd nel repo e valuta solo i contesti obbligatori di tollgate (costante, nomi dalla spec 9.1): uno obbligatorio in failure/error/pending → conferma (codice 3); contesti assenti (gate mai girato) → solo avviso; FlowLab.set_gh(**dati) riscrive i dati del finto — spec 6.1 parla di «stati obbligatori» — costo se sbagliato: una conferma in più o in meno.
Ruling: C8 — segnale registrato solo per start e act (gli unici che leggono la sessione); cli/<session>.json è un dizionario per sottocomando ({"start": {...}, "act": {...}}); cli_calls trova l'indice del programma (0, o 1 con python3 <bin>) prima di prendere il sottocomando; note_cli_call cattura OSError e non solleva mai (un pre_bash che fallisce negherebbe ogni Bash). Test per i tre casi — costo: nessuno.
Ruling: C9 — tollgate_core.config espone is_readonly(agent_type) e output_excludes() (con .tollgate-run/); Ctx.readonly e _common.output_excludes delegano lì; act apply resolve writer interrompe solo gli implementatori (non di sola lettura), approve level esclude output_dirs e .tollgate-run/ — spec 8.4 «gli implementatori»; strati rispettati senza duplicare — costo: una piccola modifica a config/context.
Ruling: C10 — set_review_prep azzera verdict e review_findings; l'evento fix azzera review_code e review_sha; task start --fix richiede verdict == changes con review_code non nullo; awaiting_review non riconosce revisori lanciati prima del nuovo review-prepare — altrimenti --fix ammesso senza nuova revisione — costo: nessuno.
Ruling: C11 — task senza commit: review_prepare usa git.head(wt) come SHA, diff vuoto, il brief del revisore dice «nessuna modifica: verifica che il task sia già soddisfatto»; task_done confronta review_sha con lo stesso SHA (tasks.commits vuoto → head del worktree alla preparazione) — spec 8.1 «senza commit e senza modifiche: passa» — costo se sbagliato: un task già soddisfatto approvato da un revisore.
Ruling: C12 — checkpoint: note prima, «prossimo passo» per ultimo (sopravvive al taglio di session.py); next_step copre running (attendere o riprendere), blocked (/tollgate:resolve), review con verdict changes (task start k --fix), review senza verdetto (task review-prepare k), approved (task done k) — costo: nessuno.
Ruling: C13 — Task 10: la frase nella skill e l'assert coincidono («mai subagent-driven-development» in minuscolo in una riga dedicata); il test si chiama test_execute_forbids_sdd_as_executor; il Task 10 legge in sola lettura i tre file di Superpowers 7.0.0 (implementer-prompt.md, task-reviewer-prompt.md in skills/subagent-driven-development/, LICENSE nella radice di /home/crucco/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/); marketplace nella forma V4 — costo: nessuno.
Ruling: C14 — vale la decisione 10 (due veti, poi needs_you) per il revisore del task, come 8.1; la rev 22 armonizza 8.6. Rilievo con severity fuori da blocker|major|moderate|minor o line non intero → scartato (fail-closed). Due sottocasi in più nella matrice: JSON valido tra prosa (valido) e oggetto d'esempio citato prima del vero verdetto (vale l'ultimo). La distinzione delle regole [blocca] dei profili (8.6) si rinvia a P3b (nessuno schema in PROFILE_DEFAULTS) — costo se sbagliato: un rilievo su regola non bloccante che chiede modifiche, fino a P3b.
Ruling: C15 — Task 4 aggiunge bin/tollgate_core/phases.py (set_worktree) e tests/test_phases.py ai Files; Task 12 aggiorna i chiamanti di waiver_hint/explain (post_bash.py, writes.py, commit.py). Il messaggio di rm -rf fuori dal repo dice «usa un percorso dentro il worktree, oppure chiedi all'utente di eseguirlo» invece di suggerire rm -r senza -f — un guardrail non insegna ad aggirarsi (P2 finale M7 chiedeva solo un messaggio più utile) — costo se sbagliato: un messaggio meno pratico.
Ruling: C16 — FlowLab compone hookkit.Lab (stessi ts/tmp/conn, sessione parametrica) invece di duplicarlo, e aggiunge goto(phase) e set_gh(**dati); la riga «programma» va su ogni command_name tollgate:*, anche per un atto rifiutato — costo: nessuno.
Ruling: C17 — la prenotazione del lancio resta controllo in decide + scrittura in apply (non atomica con hook paralleli, stessa lacuna di live_writers); il limite si dichiara nella rev 22 (decisione 12) — il test sequenziale copre il caso osservato in P2 — costo se sbagliato: due implementatori sullo stesso task se Claude Code lancia gli hook in parallelo.
Ruling: C18 — gitw.worktree_add con new_branch usa --no-track; test su branch.<nome>.merge assente — altrimenti il push di P3b fallisce con push.default=simple — costo: nessuno.
Ruling: C19 — Task 2 aggiunge tollgate_flow a FORBIDDEN in tests/test_analysis_isolation.py; il vincolo «checks non scrivono nel DB» è già provato da tests/test_hook_engine.py (ReadDb), test_layers non lo ripete — costo: nessuno.
Ruling: C20 — la riga «programma» resta (ripiego delle skill, già deciso con V1) — costo: una riga di contesto per comando.
Task 2: dispatched (sonnet), base c301c86
Task 2: implementer DONE_WITH_CONCERNS, commit 511a449 (719 test); review dispatched (sonnet)
Ruling: chiave del repo ovunque repo_key(git.origin_url(repo)) come dice il piano (get-url espande insteadOf: nel banco la chiave è il percorso del repo nudo, in produzione senza insteadOf coincide con l'URL); git.origin_url NON cambia; Lab/FlowLab calcolano la chiave con repo_key(git.origin_url(main)) e un test lo fissa (Important 1 della revisione) — cambiare git.origin_url toccherebbe hook e CLI di P1/P2 — costo se sbagliato: con un insteadOf reale dell'utente la chiave è l'URL espanso, coerente tra hook e CLI.
Ruling: Important 2 della revisione del Task 2 (is_github e current_repo_key nel banco) non è un difetto del Task 2: il piano già prescrive is_github su `git config --get remote.origin.url` grezzo e la chiave su git.origin_url; resta in carry per il Task 3 — costo: nessuno.
Task 2: minor (deferred): il merge del segnale cli/<session>.json può andare in race tra hook concorrenti della stessa sessione (trascurabile).
Task 2: minor (deferred): i test di sessions sono stati scritti dopo il codice (nessun RED).
Task 2: minor (deferred): test_layers non vede gli import dinamici (importlib).
Ruling: off e on esclusi dalla riga «programma» — il wrapper li gestisce senza Python e la skill off non esegue comandi; C16 parlava degli atti rifiutati, non di off/on; un test fissa l'esclusione (nel giro 1) — costo se sbagliato: nessuna riga per due comandi che non usano il programma.
Task 2: fix round 1/5 (2 addressed, 0 open — chiave del repo nel banco, test off/on; commits 511a449..75d9f98)
Task 2: minor (deferred): tests/test_flowkit.py import non in ordine e una riga vuota di troppo (estetico).
Task 2: complete (commits c301c86..75d9f98, review clean)
Task 3: dispatched (sonnet), base 75d9f98
Task 3: implementer DONE_WITH_CONCERNS, commit 6d5c654 (762 test); review dispatched (sonnet)
Ruling: scostamenti dichiarati del Task 3 accettati — gh.issue via `gh api repos/{owner}/{repo}/issues/N` (gh issue view non espone authorAssociation), commit_state come dict dei contesti obbligatori (C7), defaultBranch scritto dopo «repo attivo», Lab(worktree=True) per non creare tg/7-demo in FlowLab senza issue, start non stampa il titolo non fidato — tutti coerenti con spec 6.1 e carry — costo se sbagliato: nessuno visibile all'utente.
Ruling: nel giro 1 del Task 3, oltre all'Important (GitWriteError/OSError non gestiti in start), entrano tre minori a basso costo e di robustezza: housekeeping con passi indipendenti (json malformato e errore di prune_events non saltano gli altri), timeout in prereq.is_github, test no_auth con il messaggio completo — feedback dell'utente: miglioramenti utili e a basso costo si fanno — costo: nessuno.
Task 3: minor (deferred): WorkExists dopo worktree_add lascia ramo e worktree orfani (il secondo start propone adopt: Review Focus 3 coperto).
Task 3: minor (deferred): gh pr list --limit 200 e issue list --limit 100 filtrano lato client e possono perdere PR o issue vecchie.
Task 3: minor (deferred): _checks rilegge il ref invece di usare base_sha.
Task 3: ⚠️ i segnaposto {owner}/{repo} di gh api sono provati solo su fakegh: resta non verificato anche nel Task 13 (gh finto); annotato in carry come limite.
Ruling: dopo il riavvio della sessione l'implementatore del Task 3 non è raggiungibile: il giro 1 va a un implementatore nuovo (sonnet, stesso modello) con brief, report e rilievi — la skill lo prevede quando non si può riprendere l'agente — costo: un contesto da ricostruire.
Task 3: fix round 1 dispatched (impl-t3b, sonnet), FIX_BASE 6d5c654
Task 3: fix round 1 implementer DONE, commit 844008b (769 test); re-review dispatched (sonnet)
Task 3: fix round 1/5 (4 addressed, 1 open — danno nuovo: gitw.delete_branch con branch -D incondizionato; commits 6d5c654..844008b)
Task 3: fix round 2 dispatched (impl-t3b)
Task 3: fix round 2/5 (1 addressed, 0 open — delete_branch atomico con update-ref e SHA atteso; commits 844008b..77724f8)
Task 3: minor (deferred): il test del ramo preesistente chiama delete_branch direttamente invece di passare da start().
Task 3: minor (deferred): un ramo preesistente che punta esattamente a base_sha, in caso di corsa, verrebbe tolto (non contiene lavoro).
Task 3: complete (commits 75d9f98..77724f8, review clean)
Task 4: dispatched (sonnet), base 77724f8
Task 4: implementer DONE_WITH_CONCERNS, commit 4dd1782 (786 test); review dispatched (sonnet)
Ruling: in ripresa, se la ricreazione del worktree fallisce, start rifiuta con codice 1 — senza worktree la ripresa non ha senso; spec 12.4 elenca i rifiuti «di ambiente» ammessi, questo è un errore operativo — costo se sbagliato: un rifiuto in più, con il motivo.
Ruling: nel giro 1 del Task 4 entrano anche i due minori a basso costo (avvisi conservati nel rifiuto; issue.md riscritto da gh dopo la ricreazione, o avviso) — feedback dell'utente — costo: nessuno.
Task 4: fix round 1 dispatched (impl-t4), FIX_BASE 4dd1782 — 3 Important: worktree prune globale, housekeeping assente in ripresa, caso di crash non testato
Task 4: fix round 1/5 (5 addressed, 0 open — add --force mirato, housekeeping in ripresa, test con rmtree, avvisi nel rifiuto, issue.md ricreato; commits 4dd1782..65f31ba)
Task 4: minor (deferred): con worktree add --force git non rifiuta un ramo già in uso in un altro worktree (serve percorso registrato-mancante e stesso ramo attivo altrove).
Task 4: minor (deferred): i test di ResumeTest del lancio iniziale scritti dopo il codice (nessun RED); il giro 1 ha RED.
Task 4: complete (commits 77724f8..65f31ba, review clean)
Task 5: dispatched (sonnet), base 65f31ba
Task 5: implementer DONE, commit fdf5d7b (816 test); review dispatched (sonnet)
Task 5: fix round 1 dispatched (impl-t5), FIX_BASE fdf5d7b — Important: _file_values prende i testi tra apici dei commenti (scope gonfiati, piano P3a non più valido)
Ruling: una sola fonte per le skill di un task — task start (Task 6) usa profiles.task_routing sia per il brief sia per tasks.skills_required (set_skills_required), non profiles.task_skills — altrimenti con più di 3 skill brief e veto di SubagentStop divergono — costo se sbagliato: nessuno (la regola di 6.3 è quella di task_routing). In carry del Task 6.
Ruling: lo scope dei piani reali cresce dopo il giro 1 del Task 5 (P2 83→104, P3a 42→83) solo per i file veri delle righe con più file, che il parser vecchio perdeva — è la correzione chiesta dal piano (rinviato P2 T4); il test fissa il nuovo scope e l'assenza di voci spurie, non «uguale a prima» come chiedeva il dispatch — costo se sbagliato: nessuno, gli scope già registrati nel DB non si ricalcolano.
Task 5: minor (deferred): l'apertura di un recinto ammette un rientro qualsiasi.
Task 5: minor (deferred): verify_cmd e i percorsi nel brief stanno tra apici non recintati.
Task 5: fix round 1/5 (2 addressed, 0 open — elenco file di una riga senza testi dei commenti, test dei pattern generati; commits fdf5d7b..54a7894)
Task 5: complete (commits 65f31ba..54a7894, review clean)
Task 6: dispatched (sonnet), base 54a7894
Task 6: implementer DONE_WITH_CONCERNS, commit 15e287e (848 test); review dispatched (sonnet)
Ruling: C10 applicato con una variante — dopo fix il verdetto changes resta (un test di P2 lo richiede) ma review_code e review_sha si azzerano; il secondo --fix si rifiuta finché review-prepare non ha impostato review_sha; i Task 7 (awaiting_review) e 9 (next_step) controllano review_sha/review_code non nulli insieme al verdetto (in carry) — sicuro secondo la revisione — costo se sbagliato: un suggerimento di --fix rifiutato.
Ruling: PlanTask.test_files (solo righe Test:) aggiunto al parser — il brief chiede i test correlati dalle voci Test:, files le fonde con Create/Modify — costo: nessuno.
Task 6: fix round 1 dispatched (impl-t6), FIX_BASE 15e287e — Important: transizioni di task start non atomiche
Task 6: fix round 1/5 (2 addressed, 0 open — task start atomico in db.tx, riga duplicata; commits 15e287e..f9107c4)
Task 6: minor (deferred): task start scrive il brief prima delle transizioni: un fallimento lascia un brief orfano in .tollgate-run/ (ignorato da git).
Task 6: complete (commits 54a7894..f9107c4, review clean)
Task 7: dispatched (sonnet), base f9107c4
Task 7: implementer DONE_WITH_CONCERNS, commit 17f77db (889 test); review dispatched (sonnet)
Ruling: scostamenti dichiarati del Task 7 accettati — clear_reservation ridondante (take_pending azzera reserved_at, test dedicato); spec_compliance assente = verdetto non valido (fail-closed, 18.5 lo prevede sempre); review_prepare e task_done solo in execution come task start — costo se sbagliato: nessuno.
Ruling: Important 2 della revisione (imposto dalla decisione 10) — un verdetto `changes` i cui rilievi blocker/major sono tutti scartati (senza rule, file o line validi) NON si converte in approved: è un verdetto non valido, riceve il veto con «rilievo bloccante senza file, riga o regola: riscrivilo» (dopo 2 veti needs_you, come 8.1). I rilievi scartati continuano a non contare (spec 18.5, criterio 40: un `changes` con soli minor validi resta approved); in più `dropped` va nell'evento task_change — la spec dice che il rilievo non vale, non che il silenzio vale approvazione; un revisore che ha visto un difetto bloccante ma ha sbagliato la forma deve poterlo riscrivere — costo se sbagliato: un giro di revisione in più per revisori sciatti. Va nella rev 22 (8.6).
Ruling: Important 1 della revisione — task done e review-prepare confrontano anche con git.head(wt) e richiedono il worktree pulito (esclusi i file ignorati), non solo tasks.commits[-1]: un commit del coordinatore o modifiche non committate dopo l'approved non chiudono il task — spec 8.6 (verdetto legato allo SHA) — costo: nessuno.
Task 7: fix round 1 dispatched (impl-t7), FIX_BASE 17f77db
Task 7: minor (deferred): awaiting_review senza task sul revisore sceglie il task in review più basso (fail-closed, flusso sequenziale).
Task 7: minor (deferred): task_reserve si applica anche se un altro controllo nega l'Agent dopo (costo noto: 120 s di attesa).
Task 7: minor (deferred): json_candidates è quadratica su messaggi con molte «{».
Task 7: minor (deferred): un report vecchio di un revisore ripreso può essere letto se manca il messaggio finale.
Task 7: fix round 1/5 (2 addressed, 0 open — task done sulla punta con albero pulito, blocker scartati non diventano approved; commits 17f77db..59c925c)
Task 7: minor (deferred): la config viene caricata due volte in _review_prepare; una riga di test lunga.
Ruling: dal Task 7, le skill start (L1) ed execute (Task 10) fanno committare il piano e i file del coordinatore prima del primo task start e tengono il worktree pulito tra i task — review-prepare e task done rifiutano col worktree sporco; la spec dice già che il coordinatore committa spec e piano — costo se sbagliato: un commit del piano in più. In carry del Task 10.
Task 7: complete (commits f9107c4..59c925c, review clean)
Task 7: minor (deferred): un verdetto dichiarato approved con un blocker scartato per forma resta approved (la regola nuova copre solo changes).
Task 8: dispatched (sonnet), base 59c925c
Task 8: implementer DONE, commit 703819d (925 test); review dispatched (sonnet)
Ruling: il tetto di livello vince anche sul min_level dei profili in locale (_common.py:251); il gate lo riporta in attenzione — spec 5 riga 284: «sotto il minimo con un tetto dichiarato → attenzione rosso» — costo se sbagliato: nessuno locale, il gate lo segnala.
Ruling: act apply consuma l'atto anche per errori di forma (livello sconosciuto, motivo mancante) — decisione 13 («l'atto si consuma sempre»), e un atto malformato lasciato pending sarebbe ripreso a ogni act apply senza id — costo: l'utente riscrive il comando.
Task 8: fix round 1 dispatched (impl-t8), FIX_BASE 703819d — Important: sblocco dei task non atomico; resolve con cifre non ASCII solleva ValueError dopo il consumo
Task 8: fix round 1/5 (3 addressed, 0 open — unblock_all atomico, id ASCII, output_excludes unico; commits 703819d..18ea9b7)
Task 8: minor (deferred): cap_paths calcolato fuori dalla transazione di set_level_cap (effetto prudente).
Task 8: complete (commits 59c925c..18ea9b7, review clean)
Task 9: dispatched (sonnet), base 18ea9b7
Task 9: implementer DONE, commit 9764bc8 (937 test); review dispatched (sonnet)
Task 9: review Approvato (nessun Critical/Important); 4 minori.
Ruling: i 4 minori del Task 9 si correggono in un giro breve (status --checkpoint senza DB non crea il DB; dopo --checkpoint niente status completo; test CLI di status --checkpoint e messaggio di --note senza --checkpoint; test che «prossimo passo» sia l'ultima riga iniettata) — basso costo, due sono comportamenti errati — costo: un giro.
Task 9: fix round 1 dispatched (impl-t9b, sonnet; l'implementatore originale non è raggiungibile dopo il riavvio della sessione), FIX_BASE 9764bc8
Task 9: fix round 1/5 (4 addressed, 0 open — checkpoint senza DB, solo percorso, test CLI, ultima riga; commits 9764bc8..0e8b527)
Task 9: complete (commits 18ea9b7..0e8b527, review clean)
Task 10: dispatched (sonnet), base 0e8b527
Task 10: implementer DONE_WITH_CONCERNS, commit 90b2ebe (949 test, validate --strict ok); review dispatched (sonnet)
Ruling: Important 1 del Task 10 — il tipo del revisore è un dato della CLI: il riepilogo di task start e l'uscita di review-prepare stampano «revisore: <tasks.reviewer_type>» e la skill execute lancia quel tipo (mai un tipo fisso); piccola modifica a taskcmd.py nel giro del Task 10 — senza, con un profilo che dichiara reviewer il task si pianta (verdetto mai registrato) — costo: una riga di uscita in più.
Ruling: Important 2 — la skill execute non decide sull'esito dichiarato dal revisore ma su tasks.verdict: dopo il revisore lancia `task done k`; se rifiuta per verdetto changes, `task start k --fix`; i messaggi di rifiuto di task done e task start --fix indicano il comando giusto — il verdetto effettivo (reviewer_standard) può differire da quello dichiarato — costo: nessuno.
Ruling: Important 3 — la ripresa del ciclo (passo 0, dopo /clear) passa da `status --checkpoint` e segue la riga «prossimo passo» (checkpoint.next_step, che copre tutti gli stati); la skill ha la tabella stato → comando — costo: nessuno.
Ruling: Important 4 — checkpoint.next_step copre anche le fasi prima dei task: in `plan` (L1) «prossimo passo: scrivi il piano con superpowers:writing-plans (intestazioni di 7.5), committalo, poi /tollgate:execute»; in spec_audit e approval (L2) «prossimo passo: arriva con P3c»; così SessionStart dopo /clear lo inietta e la skill start L1 è rientrante — piccola modifica a checkpoint.py — costo: nessuno.
Ruling: i minori del Task 10 (giro «sesto --fix», <radice> quotata in setup, esempi JSON validi, test del manifest sui punti 1-3) entrano nello stesso giro — basso costo — costo: nessuno.
Task 10: fix round 1 dispatched, FIX_BASE 90b2ebe
Task 10: fix round 1/5 (5 addressed, 0 open — revisore dal riepilogo, verdetto registrato, ripresa dal checkpoint, start L1 rientrante, minori; commits 90b2ebe..f246234)
Task 10: minor (deferred): il checkpoint non distingue «review preparata senza verdetto» da «non preparata» e indica review-prepare in entrambi i casi; rilanciarlo rigenera il codice e invalida un revisore già lanciato col codice vecchio (dopo 2 veti needs_you).
Task 10: minor (deferred): la riga «revisore:» di review-prepare è testata solo col tipo predefinito, non con un profilo.
Task 10: complete (commits 0e8b527..f246234, review clean)
Task 11: dispatched (sonnet), base f246234
Task 11: implementer DONE, commit fc23d3f (969 test); review dispatched (sonnet)
Ruling: nel giro 1 del Task 11 entrano due minori a basso costo (test del ramo senza Python; percentuale solo 0-100) — costo: nessuno.
Task 11: fix round 1 dispatched (impl-t11), FIX_BASE fc23d3f — Important: session_id con newline non scartato (percentuale forgiabile)
Task 11: minor (deferred): non verificato che housekeeping elimini i .tmp orfani di ctx/.
Task 11: fix round 1/5 (3 addressed, 0 open — session_id validato in Python, percentuale 0-100, test senza Python; commits fc23d3f..7240ba8)
Task 11: minor (deferred): nel ramo sed un input non JSON come «5.» viene scritto così com'è.
Task 11: complete (commits f246234..7240ba8, review clean)
Task 12: dispatched (sonnet), base 7240ba8
Incidente Task 8: l'implementatore ha lanciato `pkill -f "unittest discover"`, che può aver interrotto suite di altre sessioni sulla macchina (dichiarato nel report). Nessun file toccato fuori dal worktree. Da riferire all'utente. Aggiunto a cautele.md il divieto di pkill/killall/kill per pattern; i dispatch successivi lo riportano.
Ruling: codice d'uscita 4 (INCOMPLETE) di start quando il lavoro è creato ma una registrazione fallisce — distinto da 0/1/3 (decisione 6); la skill start (Task 10, in carry) lo tratta come 0 dopo aver mostrato gli avvisi; rev 22 (6.1) — costo se sbagliato: un codice in più da documentare.
Ruling: C21 — statusline/ctx esegue il comando con `sh -c "$*"` (la statusline dell'utente è una stringa di shell con possibili pipe); setup propone ctx seguito dal comando tra apici singoli; test con una pipe — costo: nessuno.
Task 12: implementato (commit f3829e0), in revisione
Task 12: minor (deferred) — verify._run_one: nel ramo timeout killpg doppio (il secondo dopo wait), PermissionError non soppresso
Task 12: minor (deferred) — test_background_child_killed_after_success: sleep(0.3) fisso, uno zombie farebbe fallire os.kill(pid,0); serve un poll con timeout
Task 12: complete (commits 7240ba8..f3829e0, review clean)
Task 13: dispatched (sonnet), base f3829e0
Task 13: implementato (commit cfc07ae correzione D1, f3537ed prova), DONE_WITH_CONCERNS; esito prova riuscito dopo D1
Ruling: D1 (Task 13) — il piano registrato con lo stesso blob di plan_sha si committa senza violazione di scope (_common._is_registered_plan); se cambia dopo la registrazione resta fuori scope — costo: nessuno, la skill start già lo prevedeva.
Ruling: D2 (Task 13) — le skill invocano `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` invece del percorso come nome di comando (Claude Code 2.1.302 nel worktree rifiuta un nome di comando con spazi). Stesso interprete dello shebang (`/usr/bin/env python3`), quindi nessuna regressione; se risponde «richiede Python >= 3.11» la skill riprova con python3.11. cli_calls riconosce già la forma python3 <bin>: test del segnale con percorso con spazi — costo: una parola in più nelle skill.
Ruling: D4 (Task 13) — agents/implementer.md dice che una ricevuta `uncounted` con uscita 0 è normale se il progetto non produce un report e allow_no_tests è acceso — costo: una riga.
Ruling: D6 (Task 13) — due task_change running per un solo task start: da indagare nel giro di correzione; difetto del ramo → correzione con test, altrimenti spiegazione nel report.
Task 13: fix round 1 (commit f7240d1): D2, D4 applicati; D6 non difetto (transizione + assign nella stessa transazione)
Task 13: review — Important: forma D2 non estesa a taskcmd.py:147 (brief verify), subagent_start.py:33,36, subagent_stop.py:126,134,135; minor: test cancellazione/rinomina piano, symlink in _is_registered_plan, «questo percorso», coerenza del rapporto, script sempre col link, push al nudo e trascrizioni sotto ~/.claude non dichiarati
Ruling: Task 13 giro 2 — si correggono l'Important e tutti i minor a basso costo; lo script guadagna l'opzione per usare il percorso reale con spazi e la prova con claude -p si ripete una volta su quel percorso per verificare D2 dal vero (ammesso dal brief: Task 13) — costo: un'esecuzione (~70k token).
Task 13: fix round 2 (commit 8ef5a59): helper paths.program_command; prova reale ripetuta col percorso con spazi: riuscita (done, approved, veti 0, 63762 token)
Task 13: minor (deferred) — runner.py:50: nel ramo _fail con exit 2 il footer su stderr (letto dal modello) nomina il percorso nudo come «Programma», non nella forma program_command
Task 13: minor (deferred) — D6: il task_change di assign non mostra nel payload implementer e pending, quindi sembra un running duplicato
Task 13: complete (commits f3829e0..8ef5a59, review clean)
Task 14: dispatched (sonnet), base 8ef5a59
Task 14: implementato (commit 1d8906f), DONE_WITH_CONCERNS: test_wrapper.WrapperTest.test_watchdog_is_capped_at_85 instabile sotto carico (0,5 s fissi + pgrep)
Ruling: test_watchdog_is_capped_at_85 (codice di P2) si rende robusto con un'attesa a polling nel giro di correzione del Task 14: la condizione «tests/run verde tre volte» non tollera un test instabile — costo: poche righe di test.
Task 14: review — Important: Ruling test_watchdog non applicato; minor: riga 18 vaga, commento del test criteri 4/38, runner.py:50 percorso nudo contro spec 3.1, GATE_FILES sei voci
Ruling: Task 14 giro 1 — si correggono l'Important e i quattro minor; runner.py:50 passa a program_command (chiude anche il minor rinviato del Task 13) invece di dichiarare un'eccezione nella spec — costo: una riga e un test.
Task 14: fix round 1 (commit 71f4230), 985 test; segnalato «Exception ignored … unclosed database» a fine suite (preesistente)
Task 14: complete (commits 8ef5a59..71f4230, review clean)
Revisione finale: dispatched (opus), intervallo 81ce50c..71f4230
Revisione finale: nessun Critical/Important; minori m1-m13; triage dei 30 rinviati 3 a / 8 b / 19 c (final-review.md)
Ruling: revisione finale — si correggono prima del merge tutti i minori marcati «da correggere ora» (m1 con righe 65/66, m2, riga 150, m3, m4, m5, m6, m7, m8, m10); m9, m11, m12, m13 e i rinviati (b) vanno nel piano principale tra i vincoli di P3b/P3c/P5 — costo: un giro di correzione.
Revisione finale: giro 1 dispatched (sonnet, impl-final), base 71f4230
Revisione finale: giro 1 (commit 8ea2edd), 995 test, unclosed database sparito; DONE_WITH_CONCERNS: finestra residua di m1, messaggi a runtime con tollgate nudo
Ruling: m1 residuo — il ramo si crea in modo atomico con `git update-ref refs/heads/<ramo> <base_sha> ""` (vecchio valore vuoto = il ref non deve esistere), poi `worktree add <percorso> <ramo>`; se update-ref fallisce il ramo è di un altro e start non lo tocca mai; si cancella solo il ref creato da noi, con update-ref -d e lo SHA atteso — costo: poche righe, chiude la corsa.
Ruling: i messaggi a runtime destinati al modello (_common.py:194, agents.py:44, send_message.py:41, checkpoint.py:52-62 e ogni altro trovato con grep) usano paths.program_command, come m4 — costo: poche righe e un test.
Revisione finale: giro 2 (commit 1636d48), 996 test; ri-revisione mirata dispatched (sonnet) su 71f4230..1636d48
Revisione finale: ri-revisione giri 1-2 pulita (final-rereview.md); 4 minor in test e messaggi
Ruling: i 4 minor della ri-revisione finale si correggono subito (costo minimo): test prima di unittest.main, helper inutilizzato tolto, elenco dei sottocomandi completo, messaggio di diniego che spiega al subagente come lanciare il proprio script (percorso letterale) — resta fail-closed.
Revisione finale: giro 3 (commit ab64a9a), 997 test; ri-revisione mirata dispatched
Revisione finale: ri-revisione giro 3 pulita (final-rereview-3.md). Revisione finale chiusa senza rilievi critical/important aperti.
Revisione finale: minor (deferred) — cli_calls.py:72: il diniego per parsing fallito ha ancora il messaggio breve (fail-closed corretto) → P3b
Suite finale: 3 corse verdi su ab64a9a (tests/run python3.11 3.11.16 e python3 3.13.5, 997 test; -W error::ResourceWarning 997 OK; 0 occorrenze unclosed/ResourceWarning)
