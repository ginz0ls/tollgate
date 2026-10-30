# Brief per la sessione che esegue B2

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B2 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-10-29-tollgate-b2-regole-di-base.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-10-29-tollgate-b2-esecuzione.md`: ramo `b2-regole-base`, worktree `.claude/worktrees/b2`, sessione avviata dalla radice del repo, workspace SDD nel worktree, modelli, scan pre-flight prima del Task 1, regole di cautela con le eccezioni del controller, fermata per l'approvazione nel Task 5, chiusura.

Il lavoro è finito quando:
- tutti gli 8 task sono `complete` nel ledger, ognuno con la revisione pulita;
- la pagina `docs/profili/base.md` è approvata dall'utente e `skills/rules-base/SKILL.md` ha `approved` con la data;
- la prova reale del Task 7 è riuscita, oppure il rapporto dice con chiarezza perché no;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, anche con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente è consegnato, in parole semplici, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-10-29-tollgate-b2-esecuzione.md`: le istruzioni.
2. Il piano B2: per intero «Decisioni di questo piano» (13 decisioni), «Review Focus», la tabella delle regole del Task 3 e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, per intero: è l'autorità.
4. Il piano principale di B, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3 e 9.
5. La spec del nucleo rev 27, sezioni 6.3, 8.1 («Interruttore del blocco»), 8.6, 12.2, 16, 18.4.
6. Il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, sezioni 1, 2.3 e 4.
7. `docs/sdd/2026-10-27-tollgate-b1-informati-prima/`: `README.md`, `progress.md` (forma delle `Ruling:`, la sezione «Merge e CI»), `final-review.md` (triage), `cautele.md`, le regole per implementatori e revisori.
8. La memoria del progetto: `plugin-workflow-decisioni.md` (voci «B, progetto approvato» e «B1 eseguito»), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di B è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti. Le regole di `rules-base` no: le decide l'utente.
- **Scan pre-flight prima del Task 1**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio**, compreso il divieto di `pkill`, `killall` e `kill` per pattern e di `git stash`. Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- **Le regole le scrive Claude con la fonte, un agente verifica le fonti, l'utente approva una pagina per profilo in parole semplici.** Un profilo senza approvazione non si attiva; il blocco si accende solo con `rules-base` approvata.
- **L0 avvisa e basta; L1 e L2 bloccano** la prima modifica di un task senza una nota valida.
- **Solo sviluppo software**: niente profili per testi legali, preventivi o mail.
- **Il repo `ginz0ls/tollgate` è pubblico**, e l'utente ha scelto di lasciarci i percorsi locali già presenti. Nei file nuovi niente nomi di progetti privati dell'utente né citazioni dalle sue altre sessioni; le evidenze si anonimizzano, nome dell'host compreso.

## Punti delicati del piano

- **L'approvazione accende il blocco per davvero.** Sul ramo vale da quel commit; nei lavori veri dell'utente da quando la versione unita su `main` arriva al plugin installato (merge, push, aggiornamento). Da lì ogni lavoro L1 o L2 con il passo, anche già in corso, riceve il rifiuto alla prima modifica senza nota valida. La pagina e il rapporto finale lo dicono all'utente.
- **La suite legge l'interruttore dal repo vero** (`taskcmd` usa `db.BIN_PATH.parents[1]`; `Lab` di `tests/hookkit.py` ha `plugin_root=ROOT` per default; nei sottoprocessi `hooks/run` e `bin/tollgate` usano la radice del loro percorso). Per questo il Task 2 misura la suite con un `approved` temporaneo, **mai committato**, prima della bozza; le prove a secco degli eval ricevono una `Read` e una nota «Nessuna fonte esterna» (decisione 7).
- **Gli agenti caricano `rules-base` solo dopo l'approvazione** (Task 6 dopo il Task 5): una bozza non approvata non deve guidare gli agenti né far bloccare i revisori (progetto 5, punto 4). Se l'utente rinvia l'approvazione, su `main` vanno al più i Task 1 e 2.
- **Le regole sono scritte su ciò che il revisore vede** (diff, nota, report), e un difetto della nota si segnala una volta sola (decisione 8).
- **Le fonti sono locali** (decisione 1): il controller le copia nel workspace nel Task 3, Step 0, e i subagenti non usano la rete né leggono `~/.claude/plugins/`. Le fonti scelte: `agent-skills` 0.6.9 (MIT) e Superpowers 7.0.0 (MIT), più le correzioni dell'utente scritte nel progetto di B.
- **Precaricamento con `skills:`** (decisione 2): provato in P0 (E5) con il nome corto in un agente di plugin. Una skill precaricata non passa dallo strumento `Skill`: `rules-base` non va mai in `skills_required`, altrimenti `SubagentStop` darebbe un veto.
- **`claude plugin validate --strict`** va eseguito dopo i Task 3, 5 e 6 (non lancia il modello). B1-V7 ha provato il campo `approved`; il campo `version` no: se lo rifiuta, si toglie (decisione 9).
- **Avvisi come errori**: `PYTHONWARNINGS=error::ResourceWarning`, come la CI. In B1 il solo `-W` ha nascosto due `open(...)` non chiusi in un `python3 -c` degli script di prova.
- **La prova del Task 7** riusa `spikes/run-b1-flow.sh` con `B1_FLOW_RULES=vere`. L'implementatore può consegnare la nota prima di ogni modifica: in quel caso il rifiuto dal vivo non si vede, e la prova deterministica sulla regola vera è `test_real_rules_base_blocks_l1` (Task 5).

## Stato al momento di questo brief

- `main` contiene il nucleo completo, B1 (unita il 29/10/2026 fino a `6b4fd3d`, registro in `f6f9f61` e `f556f04`) e i tre file di questo piano. La suite su `main` ha 3166 test verdi su Python 3.11 e 3.13, anche con `PYTHONWARNINGS=error::ResourceWarning`; la CI di `main` è verde.
- `skills/rules-base/SKILL.md` non esiste: su `main` il passo avvisa e basta, a ogni livello.
- Sulla macchina: Claude Code 2.1.312, `gh` 2.46.0, Superpowers 7.0.0, agent-skills 0.6.9. Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- I worktree e i rami locali di P4, P5 e B1 sono stati rimossi; i rami remoti `p4-gate` e `p5-eval-ci` esistono ancora su GitHub: non toccarli.
- Le trascrizioni delle sessioni nei worktree vanno spostate a fine lavoro nella cartella della radice, solo se la sessione è partita dal worktree (`sessioni-nei-worktree.md`).
