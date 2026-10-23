# Brief per la sessione che esegue P5

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano P5 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-10-23-tollgate-p5-eval-ci.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-10-23-tollgate-p5-esecuzione.md`: ramo `p5-eval-ci`, worktree `.claude/worktrees/p5`, workspace SDD nel worktree, modelli, scan pre-flight dopo il Task 1, regole di cautela con le eccezioni del controller, chiusura.

Il lavoro è finito quando:
- tutti i 15 task sono `complete` nel ledger, ognuno con la revisione pulita;
- gli eval sono girati con 3 corse per caso nel tetto di 80 USD, con il costo misurato e riportato, e la CI del ramo è verde su `ginz0ls/tollgate`;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, anche con `-W error::ResourceWarning`;
- il rapporto all'utente è consegnato, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-10-23-tollgate-p5-esecuzione.md`: le istruzioni.
2. Il piano: per intero «Decisioni di questo piano» (24 decisioni), «Review Focus» e «Copertura».
3. La spec rev 25, sezioni 1.2, 1.3, 3, 3.1, 9.1-9.5, 11, 14, 15, 17, 20.
4. Il piano principale, sezione 3: «Vincoli e rinvii per P5» e «Minori rinviati di P4»; sezione 4: le tabelle delle prove (per la forma della tabella di P5).
5. La documentazione di `claude plugin eval` (`https://code.claude.com/docs/en/plugin-evals`) e `claude plugin eval --help`.
6. `docs/verifiche/2026-10-21-p4-verifiche.md`, `2026-10-21-p4-prova-gate.md`, `2026-10-21-p4-prova-flusso.md`: i fatti già provati, da **non** riprovare, e la forma dei rapporti.
7. `docs/sdd/2026-10-21-tollgate-p4-gate/`: `README.md`, `progress.md` (forma delle `Ruling:`), `final-review.md` (triage), `cautele.md`, le regole per implementatori e revisori.
8. La memoria del progetto: `plugin-workflow-decisioni.md`, `feedback-domande.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **La spec è l'autorità, il piano è il suo argomento.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight dopo il Task 1**, con le ruling, `carry.md` e i `task-N-carry-extract.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` e dei `task-N-carry-extract.md` che nominano il task (anche fuori dalla sua sezione) e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio**, compreso il divieto di `pkill`, `killall` e `kill` per pattern e di `git stash`. Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente (23/10/2026), da non riaprire

- **Repo del plugin:** privato `ginz0ls/tollgate`, creato dal controller nel Task 1 dopo la ricerca di token. Push di `main` (non forzato), di `p5-eval-ci` e dei `p5-probe-*`; letture e run. Niente segreti, visibilità, cancellazioni.
- **Eval:** tetto complessivo **80 USD**, modello `claude-sonnet-5-5`, solo in locale dal controller; in CI solo la suite, nessuna chiave API come segreto.
- **Repo di prova di P4:** si riusa **solo** `ginz0ls/tollgate-p4-detect` (fissaggio per SHA, cache sul privato, M-3, M-4); `ginz0ls/tollgate-p4-protected` lo cancella l'utente e P5 non lo tocca.

## Punti delicati del piano

- **La sandbox di `claude plugin eval`** (decisione 3): casa temporanea per corsa, rete chiusa, Superpowers assente, all'agente solo variabili `EVAL_*`, hook del plugin attivi fuori dalla sandbox, `scaffold_script` solo con `--scaffold`, grader senza codice. Lo stato di tollgate lo costruisce lo scaffold con il programma vero; il `gh` è uno shim nel `PATH` di chi lancia l'eval. Il Task 1 (VE1-VE9) prova ciò che la documentazione non dice; la decisione 9 fissa il ripiego (copia senza `dependencies`, esecutore locale `local.py`).
- **`--no-publish` sempre**: senza, `claude plugin eval` pubblica il rapporto su claude.ai.
- **`socat` manca sulla macchina** (verificato il 23/10/2026): `claude plugin eval` su Linux richiede `bubblewrap` (c'è) e `socat`. Lo Step 0 del Task 1 si ferma e chiede all'utente di installarlo.
- **Punteggio sull'esito** (decisione 2): un modello che rispetta l'obbligo senza tentare la scorciatoia non perde punti; il testo del veto è un indicatore, tranne nei casi che chiedono l'azione vietata in modo esplicito.
- **Un solo calcolo del gate**: le voci nuove (M-1) vanno in `evaluate` con il loro gruppo.
- **`pending` di `guard`** (decisione 15): solo su `edited`/`reopened` e solo verso il predefinito; mai stati sulle PR verso altri rami.
- **Versione 0.2.0** (decisione 13): cambia `.github/tollgate/VERSION` atteso dai banchi e l'avviso di `start` sulle installazioni vecchie; detect si aggiorna con la procedura di 9.4 nel Task 13.

## Stato al momento di questo brief

- `main` contiene P4 (fino a `6c59a24`), il suo registro, il brief di scrittura di P5 (`68ca3be`) e i tre file di questo piano. La suite su `main` ha 2465 test verdi su Python 3.11 e 3.13.
- Sulla macchina: Claude Code 2.1.309, `gh` 2.46.0, Superpowers 7.0.0, `bwrap` presente, `socat` assente, `jq` presente. Il token di `gh` ha gli scope `gist`, `read:org`, `repo`, `workflow`; nessun `delete_repo`.
- Il worktree `.claude/worktrees/p4` e il ramo `p4-gate` esistono ancora: non toccarli.
- Le trascrizioni delle sessioni nei worktree vanno spostate a fine lavoro nella cartella della radice, solo se la sessione è partita dal worktree (`sessioni-nei-worktree.md`).
