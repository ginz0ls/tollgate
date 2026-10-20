Task 1: minor (deferred): spikes/run-p3b-experiments.sh con modo 644 (p3a 755).
Task 1: minor (deferred): lo script non cattura `claude --version` (valore nel rapporto non riproducibile dallo script).
Task 1: minor (deferred): verifiche.md G4 «il limite 30 vale anche con --head» è un'inferenza, non letta nell'aiuto.
Task 1: minor (deferred): nomi dei campi JSON (headRefOid, mergedAt, comments) da controllare col gh vero: tracciato nella Ruling G4 e da riportare nella spec rev 23 (sez. 16).
Task 2: minor (deferred): nessun test esercita il passaggio reale di argv da cli.main (secondo start/act senza nuovo segnale rifiutato; start 7 --level L1).
Task 2: minor (deferred): docstring di cli_calls.py:3-5 non aggiornato al nuovo elenco dei sottocomandi segnalati, riga oltre 100 colonne.
Task 2: minor (deferred): cli.py:226 continuazione della chiamata a apply_act indentata male.
Task 2: minor (deferred): OSError nella rimozione della voce del segnale lascia il comando ripetibile senza hook, senza test (previsto da C2).
Task 2: minor (deferred): comando non analizzabile di un subagente con «tollgate» e «review» come parole comuni viene negato (accettato dalla decisione 2).
Task 3: minor (deferred): M1 reviews.py:241 close_cycle non controlla lo stadio né i rilievi con verification nullo (un ciclo non in verify o con un blocker non verificato si chiude ok): contenuto dai chiamanti (Task 7, 8) — portato nel carry.
Task 3: minor (deferred): M2 reviews.py:241 close_cycle ripetuto su un ciclo needs_fix già chiuso rimette la fase a execution e riapre il blocco del tetto: i Task 8 e 10 non lo richiamano dopo approve finding/rounds — portato nel carry.
Task 3: minor (deferred): M3 reviews.py:219 set_decision accetta un «declassamento» verso una gravità più alta.
Task 3: minor (deferred): M4 intents.py:19 request/complete non controllano lavoro, azione e stato di partenza della riga esistente.
Task 3: minor (deferred): M5 tests/test_dod.py:233 assegnazione `kept` inutilizzata.
Task 3: minor (deferred): M6 il test di is_blocking sta in test_reviews.py (come chiede il brief), non in test_verdicts.py.
Task 4: minor (deferred): verify.py, una riga del messaggio «nessun riferimento remoto…» in GateRun oltre 100 caratteri.
Task 4: minor (deferred): tests/test_violations.py importa helper da tests.test_check_writes e usa lab._base (privato).
Task 4: minor (deferred): un dod di profilo senza comando dà ricevuta unverified e run_gate.ok falso — voluto (fail-closed), portato nel carry del Task 6 perché la riga di finish check lo spieghi.
Task 4: minor (deferred): states/junits di GateRun indicizzati per nome: due comandi con lo stesso nome si sovrascriverebbero (teorico, dod_commands esclude i doppioni).
Task 5: minor (deferred): processo — nessun passo RED separato; il revisore ha ricostruito la prova a posteriori (26 test falliscono sul codice di 0e7558c): test discriminanti.
Task 5: minor (deferred): config.py:342 re.match(…$) accetta un \n finale: meglio re.fullmatch.
Task 5: minor (deferred): task_verdict.py:245-257 _task_files non esercitato (profilo attivato solo da paths, diff illeggibile).
Task 5: minor (deferred): _task_files ripete la base resolve_ref(c0^) or EMPTY_TREE di taskcmd._range e post_bash; import json fuori dal gruppo stdlib.
Task 5: minor (deferred): in test_verdicts.py e test_profiles.py classi nuove dopo unittest.main() (eseguite dalla discovery, non da un lancio diretto).
Task 5: minor (deferred): il problema «ogni risultato ha un id» del verificatore si ripete per ogni elemento difettoso.
Task 6: minor (deferred): predicato «task non done/approved» duplicato rispetto a dod._tasks.
Task 6: minor (deferred): json.loads su finish_report non protetto.
Task 6: minor (deferred): git.changes calcolato due volte in finish check.
Task 6: minor (deferred): se set_phase fallisce dopo set_finish manca l'evento finish_check.
Task 6: minor (deferred): approvals._value gestisce male un valore tra virgolette seguito da commento.
Task 6: minor (deferred): mancano i test per kind sbagliato in _approvals e per must_have_tests spento.
Task 6: minor (deferred): docstring di _own_document dice «L2» ma l'esenzione di reviews/<N>/ vale a ogni livello.
Task 7: minor (deferred): check_plan ricalcolato per ogni agente del ciclo (la ri-revisione dice: ora letto una volta per ciclo — da confermare nel triage).
Task 7: minor (deferred): dopo un rebase il brief usa lo SHA vecchio del ciclo con head nuovo, senza spiegarlo.
Task 7: minor (deferred): con default_ref None il messaggio d'errore è «riferimento git non valido: None».
Task 7: minor (deferred): issue.md citato nel brief anche se start non l'ha scritto (issue non leggibile alla ripresa).
Task 8: minor (deferred): subagent_stop.py:67 salta sempre i revisori finali in attesa, ma final_review ha component final_review: con il componente spento a ciclo aperto il revisore resta running (raro).
Task 8: minor (deferred): apply._final_rules ricalca finalreview._profiles senza il ripiego default_ref per la base (più severo, non meno).
Task 8: minor (deferred): except ValueError: return in apply._review_report perde la traccia del riporto scartato (il runner l'avrebbe già loggato come «registrazione non applicata»).
Task 8: minor (deferred): mancano i test per un revisore interrupted che ha cambiato file e per len(apply.OPS) == 27.
Task 8: minor (deferred): awaiting_final accetta in stadio verify un verificatore di un ciclo precedente (protetto dal code per ciclo).
Task 9: minor (deferred): pr_for_branch non filtra le PR da fork con lo stesso nome ramo.
Task 9: minor (deferred): messaggio d'errore di gh ripetuto tre volte.
Task 9: minor (deferred): json.loads non protetti in open-pr (traceback invece di rifiuto:).
Task 9: minor (deferred): merge_detected non atomico con il cambio di fase.
Task 9: minor (deferred): un atto finish resta vivo se il processo muore tra intents.complete e acts.consume (la ripetizione aggiorna la stessa PR).
Task 9: minor (deferred): corpo della PR senza tetto complessivo (molte voci possono superare il limite di GitHub).
Task 9: minor (deferred): non verificato se GitHub attiva «Closes #N» (è la prima riga, fuori dai recinti).
Task 10: minor (deferred): approve finding su un rilievo di un ciclo non ultimo non chiude il blocco dei cicli (caso non coperto dalla Ruling né da test).
Task 10: minor (deferred): ultimo ciclo superseded con un rilievo confirmed → recompute_outcome solleva ValueError non gestito dopo che la decisione è scritta (traceback).
Task 10: minor (deferred): nessun test asserisce nome -r6, launch e inherit al sesto giro di correzione.
Task 10: minor (deferred): FIX_CAP in actapply.py:25 duplica il testo del motivo di taskcmd (meglio una costante condivisa).
Task 10: minor (deferred): _grant_cycles+close_block e close_block+authorize_force non atomici; per il rebase authorize_force prima di close_block.
Task 10: minor (deferred): il motivo di approve finding sta solo nell'atto, non negli eventi del rilievo.
Task 11: minor (deferred): nessun test sull'ordine dell'intento sync rispetto al rebase, su rebase già in corso all'avvio, su merge_ff_only che fallisce, su finish check rosso dopo il rebase.
Task 11: minor (deferred): processo morto tra integrazione e registrazione dei commit: la ripetizione li recupera solo se il rebase riesce, non con un conflitto.
Task 11: minor (deferred): _realign non rinnova il lease se esiste già un'autorizzazione force_push non usata.
Task 12: minor (deferred): etichette dell'issue illeggibili → solo un avviso e il livello può scendere (coerente con openpr._labels, diverso dalla PR illeggibile che rifiuta).
Task 12: minor (deferred): regola «autore esterno → L2» (6.1) non applicata in adopt (spec 12.4 dice «diff più etichette»).
Task 12: minor (deferred): ramo locale e remoto diversi: si usa la punta locale senza avviso.
Task 12: minor (deferred): adopt.py usa start._write_issue e start.EXCLUDES (accoppiamento tra moduli).
Task 12: minor (deferred): sqlite3.Error in acts.consume dopo create_work dà un rifiuto con il lavoro già creato.
Task 13: minor (deferred): orfani di cleanup solo tg/<N>-* mentre la decisione 19 dice tg/* (coerente con orphan_tg e adopt): da annotare nella rev 23.
Task 13: minor (deferred): dopo worktree_remove nessun `git worktree prune`: resta la voce di un worktree con la cartella sparita.
Task 13: minor (deferred): abandon, processo morto tra set_phase e consume: l'atto resta pending fino alla scadenza.
Task 13: minor (deferred): regex _TG duplicata tra closing.py e _common.py.
Task 13: minor (deferred): mancano test per cwd dentro il worktree, cartella del worktree sparita, --confirm su PR chiusa insieme ad altre conferme.
Task 14: minor (deferred): fixtask.py:62-64 gate:<sha> usa HEAD del worktree, non il commit giudicato dal gate: un secondo --from-gate prima del nuovo verdetto rilegge il commento vecchio e crea un duplicato — contratto da fissare con P4 (sha nel marcatore o headRefOid), da scrivere nella rev 23.
Task 14: minor (deferred): fixtask.py:55-56 autore del commento col marcatore non verificato (resta dato recintato).
Task 14: minor (deferred): fixtask.py:74-82 ripete i controlli di _task_start e ne chiama la funzione privata.
Task 14: minor (deferred): taskcmd.py:66-73 _fix_files rilegge i rilievi dal vivo (instradamento può cambiare dopo un dismiss).
Task 14: minor (deferred): brief.py:42-44 _finding stampa la gravità originale, non quella effettiva dopo un declassamento.
Task 14: minor (deferred): mancano test per rollback, L0 e --from-gate da CLI; asserzione sul recinto del gate lasca.
Task 15: minor (deferred): checkpoint.py:57 _review_brief prende il review-<k>.md con k più alto (contatore globale, non numero del task): euristica fissata dal test.
Task 15: minor (deferred): CAP_PREFIXES in checkpoint.py:21 duplica CAPS e actapply.FIX_CAP.
Task 15: minor (deferred): _cap_step con più blocchi di tetto aperti ne indica solo il primo (approve rounds poi rifiutato).
Task 16: minor (deferred): tests/test_manifest.py:475-487 test di sola presenza di sottostringhe («committa», gh pr create).
Task 16: minor (deferred): skills/start/SKILL.md, sotto «1, rifiuto» resta la frase sulla PR chiusa senza merge (ora codice 3): testo morto.
Task 16: minor (deferred): test_skills_use_program_command_form controlla solo le skill, non gli agenti (agents/implementer.md di P3a cita python3 '<percorso>/bin/tollgate' con apici singoli).
Task 17: minor (deferred): l'elenco d'uso in fondo a spikes/run-p3b-flow.sh non cita passo4-radice (l'intestazione sì).
Task 17: minor (deferred): la ripresa di start non lega la sessione nei ritorni anticipati (PR unita, --confirm mancante, worktree non ripristinato).
Task 18: minor (deferred): test del criterio 26 in test_criteria_p3b asserisce il rifiuto di open-pr solo con returncode != 0; helper prepare_refused_open_pr con nome fuorviante; il «finish successivo» (ciclo 2) provato solo a livello libreria (test_openpr).
