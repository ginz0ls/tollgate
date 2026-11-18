# Brief per la sessione che esegue B8

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B8 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-18-tollgate-b8-eval-chiusura.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-18-tollgate-b8-esecuzione.md`: ramo `b8-eval-chiusura`, worktree `.claude/worktrees/b8`, sessione avviata dalla radice del repo.

## Il lavoro è finito quando

- tutti gli 8 task sono `complete` nel ledger, i Task 1-5 e 8 ognuno con la revisione pulita;
- la sonda del Task 6 ha le sue righe `Sonda:` nel ledger, e le correzioni che ne sono nate hanno un test;
- gli eval del Task 7 sono girati nel tetto di 20 USD, e il rapporto `docs/verifiche/2026-11-18-b8-eval.md` ha la riga `Esito:`. Fa eccezione una fermata per il tetto, per la sonda o per un caso: in quel caso vale ciò che ha scelto l'utente;
- le evidenze degli eval sono ripulite, verificate a mano prima del rapporto (anche i risultati di `WebFetch` sotto i 5000 caratteri, letti uno per uno), e `test_committed_evidence_has_no_long_web_results` è verde;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente prima del merge è consegnato nella forma del punto 4 di «Chiusura» delle istruzioni;
- **dopo il merge** (solo con l'OK dell'utente) i passi del punto 5 di «Chiusura» sono fatti, e l'utente ha ricevuto il rapporto «Chiusura di B8» e la domanda diretta sul worktree.

**Il merge su `main` non si fa senza l'OK dell'utente.**

**Le condizioni esatte stanno nel brief corto** `docs/superpowers/plans/2026-11-18-tollgate-b8-brief-goal.md`. **A ogni fermata** fai una **domanda diretta** all'utente con `AskUserQuestion`.

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-18-tollgate-b8-esecuzione.md`: le istruzioni.
2. Il piano B8: per intero «Fatti verificati», «Global Constraints», «Decisioni di questo piano» (13 decisioni), «Review Focus» e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`: sezioni 1, 2, 7 e **15** (le scelte dell'utente del 18 novembre).
4. Il piano principale di B: sezioni 2, 3, 5, 6, 9 (ogni blocco con «B8») e 16.
5. La spec del nucleo rev 34: sezioni 1.2, 6.3, 8.5, 11.2, 14, 16, 18.4, 20.
6. Il rapporto degli eval di P5, `docs/verifiche/2026-10-23-p5-eval.md`, e la documentazione di `claude plugin eval` copiata in `docs/sdd/2026-10-23-tollgate-p5-eval-ci/plugin-evals-doc.md`.
7. Il codice:
   - `evals/run.sh`, `evals/cost.py`, `evals/_kit/` (scaffold, ricette, bersaglio);
   - `tests/test_eval_cases.py` (prova a secco, `research_prep`, `ScoreTest`) e `tests/test_eval_run.py`;
   - `bin/tollgate_analysis/bash.py` (da `_WRAPPERS` a `_unwrap`, da `_DEFAULT_EFFECTS` a `text_effect`);
   - `bin/tollgate_flow/init.py` (`_drift`), `bin/tollgate_core/tasks.py` (`take_pending`);
   - `bin/tollgate_core/lookups.py` (`observed`), `bin/tollgate_checks/research_gate.py`;
   - `spikes/b1/flowreg.py` (`togli-pagine`, `third_party_blocks`).
8. `docs/sdd/2026-11-12-tollgate-b7-profilo-database/`: `README.md`, `progress.md`, `carry.md`, `preflight-scan.md`, `final-review.md` (triage), `final-rulings.md`, `cautele.md`.
9. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B7 e del piano di B8), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di B è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
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

- **Eval minimi con e senza plugin, tetto di 20 USD di costo stimato** (progetto 7). I dollari sono equivalenti: con l'abbonamento non c'è addebito.
- **B8 chiude i buchi dei comandi rimasti da B7** (progetto 15): involucri dell'ambiente, opzioni con valore di Supabase, doppio `--`, `init --update`, `SubagentStart` con due task dello stesso tipo. Restano fuori Wrangler e le pagine approvate che invecchiano.
- **Tre casi nuovi e tutti i 13 casi di P5** (progetto 15), circa 10-12 USD stimati.
- **Profili e regole approvati non si toccano**: `base`, `ai`, `infra`, `backend`, `frontend`, `database`. Le pagine che invecchiano vanno nel rapporto finale e nel piano principale.
- **Il profilo `security`, gli altri profili, gli eval estesi e il kanban sono fuori da B** (progetto 2).
- **Il repo `ginz0ls/tollgate` è pubblico:** niente nomi di progetti privati, nome utente, host, token; niente testo di pagine di terzi nelle evidenze.

Le altre scelte del piano sono «mia scelta», e la revisione finale le può contestare:
- le campagne;
- `WebFetch` per dominio;
- i tre casi e i loro grader;
- la pulizia delle trace;
- i conteggi;
- l'ordine degli eval.

## Punti delicati del piano

- **La sonda del Task 6 viene prima di tutti gli eval.** I grader di s10 e s11 e il passo `fetch` della prova a secco poggiano su fatti che solo una corsa vera mostra: `WebFetch` tra gli strumenti, la forma del risultato, la lettura registrata, gli strumenti dell'implementatore nella trace. Un fatto diverso si corregge con un test prima del Task 7.
- **Le pagine vive.** s10 e s11 aprono `ai.google.dev` e `vercel.com` dal vivo: il nome del modello non si controlla, la varianza non si corregge ritoccando il prompt.
- **Il registro di P5 non cambia mai**: la campagna predefinita è `b8`, e `p5` resta solo per leggere la storia.
- **Le trace degli eval contengono testo di pagine**: `run.sh` le ripulisce subito; il controller rilegge a mano ciò che resta sotto i 5000 caratteri.
- **Gli eval girano con il worktree pulito**, uno per invocazione e senza implementatori al lavoro: `run.sh` copia il plugin dal worktree.
- **`ANTHROPIC_API_KEY` non deve essere impostata** prima di un eval (si guarda solo se c'è).
- **Il rapporto prima del merge** ha l'elenco unico delle pagine approvate che invecchiano: è l'ultima occasione di B per dirlo all'utente.

## Stato al momento di questo brief

- **`main`** contiene:
  - il nucleo completo e B1-B7 (B7 unita il 18/11/2026 in `02f900c`, registro in `docs/sdd/2026-11-12-tollgate-b7-profilo-database/`, `7cf4b28`);
  - la sezione 15 del progetto di B (`e42f1a9`);
  - i quattro file di questo piano.

  La suite su `main` ha 4062 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- **Profili.** Le sei skill `rules-*` sono approvate, e i profili `ai`, `infra`, `backend`, `frontend`, `database` si propongono con `init`.
- **Eval.** Il registro degli eval di P5 ha 70,93 USD di residuo sul suo tetto di 80; il registro di B8 non esiste ancora (lo crea il Task 3).
- **Sulla macchina.**
  - Claude Code 2.1.327, con `claude plugin eval` e le opzioni `--allow-tools`, `--disallow-tools`, `--concurrency`.
  - `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0.
  - Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- **Push in sospeso.** I commit del piano di B8 su `main` non sono ancora stati inviati a GitHub: vanno con il primo push dopo il merge.

## Quanto costa

B8 consuma l'abbonamento in due modi, senza nessuna spesa in denaro:
- i subagenti: implementatori, revisori e scan sonnet, revisione finale opus;
- gli eval dei Task 6 e 7, l'unico `claude` vero: circa 10-13 USD stimati, con un tetto di 20.

Le pagine ufficiali dello Step 0 si leggono con `WebFetch`, senza costo.
