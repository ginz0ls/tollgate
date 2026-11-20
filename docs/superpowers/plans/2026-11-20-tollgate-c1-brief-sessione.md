# Brief per la sessione che esegue C1

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano C1 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-20-tollgate-c1-tracciamento-locale.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-20-tollgate-c1-esecuzione.md`: ramo `c1-tracciamento-locale`, worktree `.claude/worktrees/c1`, sessione avviata dalla radice del repo.

## Il lavoro è finito quando

- tutti i 10 task sono `complete` nel ledger, ognuno con la revisione pulita (il Task 9 per lo script e il rapporto);
- la prova reale del Task 9 ha le sue righe `Prova:` nel ledger e il rapporto `docs/verifiche/2026-11-20-c1-prova-flusso.md` ha la riga `Esito:`; le correzioni nate dalla prova hanno un test;
- le evidenze della prova sono ripulite e verificate a mano, e `test_committed_evidence_has_no_long_web_results` è verde;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente prima del merge è consegnato nella forma del punto 4 di «Chiusura» delle istruzioni;
- **dopo il merge** (solo con l'OK dell'utente) i passi del punto 5 di «Chiusura» sono fatti, e l'utente ha ricevuto il rapporto «Chiusura di C1» e la domanda diretta sul worktree.

**Il merge su `main` non si fa senza l'OK dell'utente.**

**Le condizioni esatte stanno nel brief corto** `docs/superpowers/plans/2026-11-20-tollgate-c1-brief-goal.md`. **A ogni fermata** fai una **domanda diretta** all'utente con `AskUserQuestion`.

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-20-tollgate-c1-esecuzione.md`: le istruzioni.
2. Il piano C1: per intero «Fatti verificati», «Global Constraints», «Decisioni di questo piano» (12 decisioni), «Review Focus», «Mappa dei file» e «Copertura».
3. Il progetto di C, `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`: sezioni 1, 2, 3, 6, 10 e 14.
4. Il piano principale di C, `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`: sezioni 1, 2, 3, 7 e 8.
5. La spec del nucleo rev 35: sezioni 3.1, 3.2, 5 («Spec con più fette»), 6.1, 7.1, 7.2, 8.4, 11.4 (`[retention]`), 12.2, 18.4, 20.
6. Il codice:
   - `bin/tollgate_core/db.py` (migrazioni), `events.py`, `config.py` (`DEFAULTS`, `_set_key`), `scope.py` (`register_plan`), `subagents.py` (`finish`), `reviews.py` (`set_decision`), `acts.py`, `cli.py`;
   - `bin/tollgate_flow/start.py` (`_create`), `housekeeping.py`, `l2acts.py` (`approve_spec`, `approve_plan`), `adopt.py` (`_register_plan`), `actapply.py` (`APPLIERS`), `research_cmd.py` (modello del comando nuovo), `taskcmd.py` (brief);
   - `bin/tollgate_analysis/specdoc.py`, `profiles.py` (`vertical_for`), `report.py` (`transcript_tokens`), `brief.py` (`ImplBrief`);
   - `bin/tollgate_hooks/model.py`, `adapter.py`, `apply.py` (`_OPS`), `runner.py`, `hooks/hooks.json`, `hooks/run`;
   - `bin/tollgate_checks/post_edit.py`, `subagent_stop.py`, `task_verdict.py`, `final_review.py`, `audit_round.py`, `session.py`, `acts.py`, `cli_calls.py`, `_common.py`;
   - `bin/tollgate_core/effects.py` e `intents.py` (gli effetti in attesa in `intents`), `bin/tollgate_flow/adopt.py` (`_approved_elsewhere`);
   - `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `evals/scrub.py` (`anonymize`) e `tests/test_b1_scripts.py`.
7. `docs/sdd/2026-11-18-tollgate-b8-eval-chiusura/`: `README.md`, `progress.md`, `carry.md`, `preflight-brief.md`, `final-review.md` (triage), `cautele.md`.
8. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B8 e di C), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di C è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 1**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.**
  - Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task, le regole di cautela e le tre righe sulla suite. Mai la storia della sessione.
  - Ogni subagente di sola lettura scrive la sua uscita su un file del workspace.
- **Regole di cautela nel brief di ogni subagente, al lancio.** Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Lingua e tono.** Testi in italiano, identificatori in inglese. Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli. Niente gergo nelle domande.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

Dal progetto di C (20 novembre 2026):
- tollgate è il primo modulo di un gestionale agentico futuro: C traccia, non costruisce il gestionale, e il gestionale per ora legge soltanto;
- tre taglie; la presa per un modello di decisione resta vuota, senza CLM in C;
- le sette aggiunte: non bloccare mai, ruling, costi, più computer anche insieme, storia, contratto, avvisi;
- su GitHub solo ciò che si può mostrare (C1 non scrive niente su GitHub);
- profili e regole approvati non si toccano;
- il repo `ginz0ls/tollgate` è pubblico: niente nomi di progetti privati, nome utente, host, token.

Le scelte del piano sono «mia scelta», e la revisione finale le può contestare:
- le soglie delle taglie e il «grande solo con un sì»;
- il costo in token per modello, senza dollari;
- le fermate lette dagli hook di `AskUserQuestion`;
- `events_days = 0` come «mai» e l'archivio;
- la forma della fotografia e di «a chi tocca».

## Punti delicati del piano

- **Un hook sulle domande dirette non deve mai fermarle**: `pre_question` non è un evento di controllo, e il controllo registra o tace (Review Focus 1).
- **La potatura** cancella solo dopo un archivio scritto (Review Focus 2). Il DB è uno per macchina e la configurazione è del repo che parte: con l'archivio niente si perde.
- **La forma di `tool_response` di `AskUserQuestion` non è documentata**: il controllo legge le risposte in due posti e altrimenti le lascia nulle (decisione 4). La prova vera delle fermate è di C6, perché `claude -p` non offre le domande dirette.
- **`register_plan` ha tre chiamanti**: la taglia va calcolata in tutti e tre (decisione 2).
- **La fotografia è senza testo libero** (Review Focus 5).
- **Lo stato vero della macchina non si legge**: la misura degli eventi usa le copie nelle evidenze, copiate prima in una cartella temporanea.
- **`ANTHROPIC_API_KEY` non deve essere impostata** prima della prova reale (si guarda solo se c'è).

## Stato al momento di questo brief

- **`main`** contiene il nucleo e B completi (B chiusa il 20/11/2026, merge di B8 in `3733953`), il progetto di C e i piani di C (piano principale e i quattro file di C1).
- **Suite:** 4180 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- **Sulla macchina.** Claude Code 2.1.328, `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0. Nessun worktree aperto.
- **Il repo locale non ha un remoto configurato**: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.

## Quanto costa

C1 consuma l'abbonamento in due modi, senza nessuna spesa in denaro:
- i subagenti: implementatori, revisori e scan sonnet, revisione finale opus;
- la prova reale del Task 9, l'unico `claude` vero: circa 1-2 USD equivalenti, nessun addebito.
