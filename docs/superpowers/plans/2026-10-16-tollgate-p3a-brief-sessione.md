# Brief per la sessione che esegue P3a

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano P3a senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-10-16-tollgate-p3a-avvio-e-task.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** le istruzioni di `docs/superpowers/plans/2026-10-16-tollgate-p3a-esecuzione.md`: ramo, worktree, modelli, regole di cautela, scan pre-flight e chiusura. L'utente ha confermato questo metodo di esecuzione il 16 ottobre 2026.

Il lavoro è finito quando:
- tutti i 14 task sono `complete` nel ledger, ognuno con la revisione pulita;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, anche con `-W error::ResourceWarning`;
- il rapporto all'utente è consegnato, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-10-16-tollgate-p3a-esecuzione.md`: le istruzioni.
2. `docs/superpowers/plans/2026-10-16-tollgate-p3a-avvio-e-task.md`: il piano. Leggi per intero la sezione «Decisioni di questo piano» (22 decisioni) e «Review Focus».
3. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 21): l'autorità. Sezioni 3, 3.1, 5, 6.1, 6.3, 8.4, 8.6, 11.1, 11.3, 12.4, 18.5.
4. `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`, sezione 3: contratti reali di P1 e P2 e vincoli per P3.
5. `docs/sdd/2026-10-09-tollgate-p2-guardrail/`: il registro di P2, modello del metodo. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md` e `preflight-scan.md`.

## Come abbiamo lavorato (non cambiarlo)

- **La spec è l'autorità, il piano è il suo argomento.** I conflitti si decidono con una riga `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger, e si va avanti. Una correzione che cambia la spec va nella revisione 22, scritta dal Task 14.
- **Scan pre-flight prima del Task 2**, come in P2:
  - una tabella per coppie di task (cosa produce uno, cosa consuma l'altro);
  - una tabella per task (test previsti contro codice previsto);
  - per ogni conflitto una ruling, e una voce in `carry.md` per il task che ne dipende.

  In P2 lo scan trovò 16 conflitti, 3 dei quali bloccanti.
- **Gli esiti del Task 1 vanno subito in `carry.md`** per i Task 2 e 10, prima di lanciarli. In P2 non fu fatto, e si è dovuto rimediare in corsa.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, le decisioni da `carry.md` e le regole di cautela. Mai la storia della sessione.
- **Ogni subagente riceve le regole di cautela nel brief al lancio**, non dopo. L'utente lo considera vincolante.
- **I rilievi minori vanno nel ledger** come `Task N: minor (deferred): …`. La revisione finale li sottopone a triage.
- **Revisione finale su opus.** Le si passano il Review Focus, i minori rinviati e il rapporto del Task 13. Seguono giri di correzione, ognuno con una ri-revisione mirata (in P2 furono 4, con una ruling).
- **Commit dopo ogni task**, con la riga `Co-Authored-By` del modello. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Le risposte all'utente sono brevi e in italiano.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i tre casi delle istruzioni: operazioni distruttive, azioni fuori dal worktree, piano rotto.

## Punti delicati del piano

- **Decisione 2, segnale della sessione.** La CLI non conosce il `session_id`. Il modulo `cli_calls` su `pre_bash` scrive `<stato>/cli/<session>.json` e `sessions.cli_session` lo accetta per 120 s, nella stessa cartella e per lo stesso sottocomando. Se il Task 1 (V3) mostra che il file non è visibile al comando, il Task 2 si ferma con BLOCKED e la strada alternativa la decide il controller, con una ruling.
- **Decisione 5, checkpoint fuori dal commit.** `docs/superpowers/reviews/*/checkpoint.md` va in `info/exclude`; altrimenti `verify` troverebbe il worktree sporco.
- **Decisioni 10 e 11, verdetto del revisore del task.** Il modulo `task_verdict` (ordine 15) possiede l'intera chiusura del revisore in attesa. `subagent_stop` deve saltarlo con `_common.awaiting_review`, perché i `record` si applicano anche dopo un `deny`.
- **Decisione 8, contratto verso P4.** Il gate è installato se ci sono `.github/workflows/tollgate-{guard,run,verdict,base,sentinel}.yml` e `.github/tollgate/VERSION`.
- **Origin GitHub nei test.** `FlowLab` imposta `remote.origin.url` su un URL GitHub con `insteadOf` verso il repo nudo locale. `prereq.is_github` legge l'URL grezzo; la chiave del repo resta `repo_key(git.origin_url(repo))` ovunque.
- **Superpowers.** Nella macchina è installata la 7.0.0; l'intervallo accettato è `>= 6.4.1` e `< 8.0.0`. Gli agenti derivano da `~/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/subagent-driven-development/` (`implementer-prompt.md`, `task-reviewer-prompt.md`), con l'attribuzione MIT a Jesse Vincent.
- **Licenza.** MIT, autore «sAInapse» (decisione dell'utente). Marketplace `sainapse`.

## Stato al momento di questo brief

- `main` è a `e454611` (piano P3a scritto e committato). La suite su `main` ha 692 test verdi.
- I worktree e i rami di P0, P1 e P2 sono stati rimossi. `.claude/worktrees/` è in `.gitignore`.
- La memoria del progetto (`~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/memory/`) contiene le decisioni (`plugin-workflow-decisioni.md`, compresa quella su P3), il feedback sulle domande e i rinviati di P1.
