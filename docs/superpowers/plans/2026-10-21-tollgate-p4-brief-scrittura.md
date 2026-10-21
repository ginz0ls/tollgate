# Brief per la sessione che scrive il piano P4

Questa sessione parte con il contesto pulito. Scrive il piano P4 di tollgate (il gate su GitHub) e **non lo esegue**. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Da leggere, in quest'ordine

1. La memoria del progetto: `plugin-workflow-decisioni.md` (soprattutto le voci «Controllo autorevole», «Garanzia del gate v1», «Repo privati su GitHub Free», P0, P3b e P3c), `feedback-domande.md` e `sessioni-nei-worktree.md`.
2. `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`, per intero. Contano soprattutto:
   - la riga P4 nella tabella dei piani (criterio 10 sui due repo di prova `protected` e `detect`, criteri della colonna P4);
   - la sezione 3: il pacchetto `tollgate_gate`, la regola degli strati, e ogni riga con destinazione P4: «Gate installato» (P3a: `prereq.GATE_FILES`, i cinque workflow e `.github/tollgate/VERSION`, `gh.REQUIRED_CONTEXTS`), i rinviati di P3a (riga 56, `sentinel_issues` con `--limit 100`), il blocco JSON 18.1 e il marcatore `<!-- tollgate-verdict` (P3b), «`finishcheck.check` è l'interfaccia che P4 sostituisce», «Vincoli per P4» di P3b (sei punti), «Contratti verso il gate» di P3c (sei punti) e «Vincoli per P4 emersi in P3c» (sei punti), «P4 → P3: `gate run` locale usato da `finish check`»;
   - la matrice dei criteri, con le colonne «Resta a» che puntano a P4 (criteri 10, 11, 18, 21, 22, 27, 29, 30, 32, 33, 34, 35, 36, 41, 42, 44 e le note «(P4)» nelle tabelle delle prove di P2, P3a, P3b e P3c);
   - la sezione 5, rischio 2 (`finish check` minimo in P3, sostituito in P4).
3. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, alla revisione 24. È l'autorità. Per P4 contano:
   - la sezione 9 per intero (workflow, cosa controllano, protezione del ramo e modalità `protected`/`detect`, aggiornamenti ed emergenze, costo, servizi);
   - 11.2 `/tollgate:init` e 11.4 `tollgate.toml`;
   - 8.2 test-guard, 8.7 Definition of Done (voci ricalcolate nel gate), 18.1 blocco JSON, 18.3 intestazioni dei report, 18.5 verdetti;
   - la sezione 13 (le righe sul gate), la sezione 15 (criteri), la sezione 16 e le revisioni 20-24.
4. `docs/verifiche/2026-10-08-p0-esiti.md` (voci G1-G5) e `docs/verifiche/evidenze/gh/gh-evidenze.md`: i fatti già provati su GitHub Free (403 su protezione e rulesets dei privati, `workflow_sha`, stato di `github-actions[bot]`, permessi). Anche `spikes/gh/run-gh-experiments.sh`, come modello e come lezione (l'incidente delle uscite perse).
5. `docs/superpowers/plans/2026-10-20-tollgate-p3c-percorso-l2.md`, come modello di forma, con i suoi due compagni `2026-10-20-tollgate-p3c-esecuzione.md` e `2026-10-20-tollgate-p3c-brief-sessione.md`.
6. `docs/sdd/2026-10-20-tollgate-p3c-percorso-l2/` e `docs/sdd/2026-10-19-tollgate-p3b-chiusura/`: `README.md`, `progress.md` (le `Ruling:`), `final-review.md` (il triage: le righe rinviate a P4 vanno coperte dal piano) e `cautele.md`. Le ultime righe del ledger di P3c contengono i due casi «parked» decisi per P4.
7. Il codice reale di `main`: `bin/tollgate_flow/finishcheck.py`, `bin/tollgate_core/{prereq,gh,verify,dod,violations}.py`, `bin/tollgate_analysis/{approvals,prblock,testguard,junit,plan}.py`. Il gate li riusa: non li riscrive.

## Cosa deve fare il piano

- **Metodo.** Si scrive con `superpowers:writing-plans`.
- **Forma.** Firme e test, non codice completo. Gli implementatori sono sonnet.
- **Ambito.** Il pacchetto `tollgate_gate` (`gate run`, `gate evaluate`, `gate guard`, `gate base-ids`, sentinel), i cinque workflow con esattamente i nomi di `prereq.GATE_FILES`, `.github/tollgate/VERSION`, `init` (e `init --update`) con la misura della modalità, e `finish check` che passa al `gate run` locale conservando firma, codici d'uscita e il contratto di `work_items.finish_report`.
- **Task 1.** Verifiche reali su GitHub solo per i fatti non ancora provati e necessari al disegno, per esempio i nomi dei campi JSON di `gh` 2.46 (`headRefOid`, `mergedAt`, `comments`, `isCrossRepository`), il comportamento dei workflow `pull_request_target`/`workflow_run` usati, gli stati scritti da `github-actions[bot]`. Se un fatto è già negli esiti di P0, non si riprova.
- **Penultimo task.** Il criterio 10 sui due repo di prova (`protected` e `detect`), e una prova reale con `claude -p` del flusso fino alla PR e al verdetto del gate. Lo script corretto della prova di P3c (`spikes/run-p3c-flow.sh`, shim `gh`) non è mai stato eseguito da un `claude -p`: la prova di P4 lo esercita o lo sostituisce, e controlla il `PATH` della shell del tool Bash di `claude` (vincolo 4 di P3c).
- **Ultimo task.** Le prove dei criteri, la revisione 25 della spec e l'aggiornamento del piano principale.
- **Criteri.** Chiude quelli assegnati a P4 nella matrice, compresi i pezzi «(P4)» lasciati dai piani precedenti (per esempio: livello dichiarato sotto il minimo → `verdict` rosso; `skipped` nel JUnit della testa; `attenzione` a due gruppi; componenti spenti riportati in `attenzione`, criterio 35 nel gate; piano registrato nel gate, criterio 36).
- **Contratti da rispettare.** Il gate ricalcola le approvazioni L2 con `approvals.check_l2` e `locate_spec_approval` (non le riscrive); esenta dallo scope i file sotto `docs/superpowers/reviews/<N>/`, il piano registrato (blob di `plan_sha`) e la spec il cui blob è lo `sha` di `spec-approval.md`; mette nel marcatore del commento lo SHA giudicato; legge l'**ultimo** blocco JSON della PR con `prblock.parse`; tratta `spec_audit` `suspended` e `off` come voci di `attenzione`.
- **Casi da decidere nel piano** (lasciati da P3c, ledger righe «parked» e «Ruling» finali): (a) approvazione propria superata contro approvazione corrente di un'altra issue: oggi vince la propria e si chiede `reopen spec`; (b) fase `approval` con `plan_adversary` spento e spec cambiata: `audit prepare` suggerisce `approve plan`, che rifiuta; (c) m-2, m-3, m-4 (report sovrascritti dopo un DB perso, `adopt` dopo `reopen` con documento identico, `spec_path`/`plan_path` registrati una volta); (d) report della spec non legati allo `spec_sha` (decisione 15 di P3c): il gate deve volere di più?
- **Rinviati.** Tutte le righe con destinazione P4 dei triage di P3b e P3c (`final-review.md`) e dei «Vincoli per P4» del piano principale. Quelle che il piano decide di non fare vanno nella tabella Copertura con il motivo e la nuova destinazione (P5 o dopo la v1).
- **Regole del codice.** Rispetta gli strati (`tests/test_layers.py`): `tollgate_gate` gira su GitHub senza DB locale, quindi importa `tollgate_analysis` e le parti di `tollgate_core` che non richiedono stato; il piano fissa la regola e la aggiunge a `test_layers.py`. Ogni comando destinato al modello passa da `paths.program_command`. Testo non fidato (corpo della PR, issue, commenti, rilievi) mai in un argomento di git o `gh` né interpolato in una riga `run:` dei workflow: su file o in variabili d'ambiente, in un recinto, marcato come dato.

## Domanda da fare all'utente prima di scrivere i task

Il criterio 10 e il Task 1 richiedono **GitHub vero**: repo di prova sull'account dell'utente, Actions che consumano minuti, `gh` autenticato (in P3 era vietato). In P0 l'utente ha dato il consenso per `tollgate-probe` (privato) e `tollgate-probe-public` (pubblico). È un compromesso vero, quindi si chiede, con una raccomandazione:
- quali repo usare (riusare i due di P0 o crearne di nuovi; `protected` richiede un repo pubblico su GitHub Free);
- quali operazioni sono ammesse alla sessione che esegue (creare repo, push sui repo di prova, aprire e chiudere PR, cambiare la protezione del ramo) e chi cancella i repo alla fine;
- se il Task 1 e il penultimo task li esegue il controller in prima persona o un subagente.

La risposta finisce nelle decisioni del piano e nelle cautele di esecuzione. Fuori dai repo di prova autorizzati restano vietati push in rete, `gh auth`, `gh api` e `gh pr create`.

## Lezioni di P3b e P3c da portare nel piano

- **Interazioni tra task.** Le revisioni finali di P3b (4 Important) e di P3c (I-1: `audit prepare` in fase plan con `spec_blob=None`) hanno trovato difetti nati dall'incontro di task diversi o da due funzioni che ricalcolavano lo stesso fatto in modo diverso. Nel piano: un solo punto di calcolo per ogni fatto condiviso tra `finish check` e gate (sul modello di `l2tree.spec_approval` e `violations.diff_violations`), un Review Focus per ogni stato toccato da due comandi, test che attraversano i comandi.
- **Skill contro codice.** `tests/test_skill_contract.py` controlla codici d'uscita e righe che le skill citano: la skill `init` e i testi nuovi delle skill si aggiungono lì.
- **Prova reale.** In P3c un implementatore, durante un giro di correzione, ha lanciato un `claude -p` contro le istruzioni. Il brief di ogni giro di correzione del penultimo task dice in chiaro quali passi dello script sono vietati.
- **Carry per task.** Le decisioni del controller per un task stanno in `carry.md` e nei `task-N-carry.md`: le istruzioni di esecuzione dicono di leggerle tutte.
- **Workspace.** Il workspace SDD sta nel worktree (`.claude/worktrees/p4/.superpowers/sdd/...`), non nella radice: le istruzioni di chiusura lo dicono.

## File da scrivere (sul modello di P3c)

- `docs/superpowers/plans/2026-10-21-tollgate-p4-gate.md`: il piano, con la tabella Copertura che porta ogni criterio, vincolo e rinviato al suo task.
- `docs/superpowers/plans/2026-10-21-tollgate-p4-esecuzione.md`: come eseguirlo con `superpowers:subagent-driven-development`.
  - **Dove:** ramo `p4-gate`, in un worktree sotto `.claude/worktrees/p4`.
  - **Come:** i modelli, lo scan pre-flight, le Ruling nel ledger, la revisione finale su opus, la suite tre volte (anche con `-W error::ResourceWarning`).
  - **Regole di cautela nel brief di ogni subagente, al lancio.** Le stesse di `docs/sdd/2026-10-20-tollgate-p3c-percorso-l2/cautele.md` (compresi i divieti di `pkill`, `killall` e `kill` per nome o pattern e di `git stash`), con le sole eccezioni per GitHub autorizzate dall'utente, scritte una per una.
  - **Chiusura:** niente merge senza l'OK dell'utente. Registro copiato in `docs/sdd/` con un `README.md`, memoria aggiornata, trascrizioni della cartella del worktree in `~/.claude/projects` spostate nella cartella della radice (solo se la sessione è partita dal worktree), repo di prova lasciati come l'utente ha deciso.
- `docs/superpowers/plans/2026-10-21-tollgate-p4-brief-sessione.md`: il brief per la sessione che esegue il piano.

## Come lavorare

- Prima di consegnare, il piano passa a un revisore opus a contesto pulito, che lo confronta con la spec rev 24, con il piano principale e con il codice reale di `main`. I rilievi vanno corretti, e dopo le correzioni una ri-revisione mirata.
- All'utente si chiedono solo le scelte che sono compromessi veri (la domanda su GitHub qui sopra è una di queste). Il resto si decide e si registra nel piano, tra le decisioni. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.
- I tre file si committano su `main`, con la riga `Co-Authored-By` del modello.
- Testi in italiano, identificatori in inglese. Risposte all'utente brevi.

## Stato al momento di questo brief

- `main` contiene P3c (fino a `3aa47c2`) e il suo registro (`7e20855`). La suite su `main` ha 1753 test verdi.
- Sulla macchina: Claude Code 2.1.305, `gh` 2.46.0 (senza `--slurp`), Superpowers 7.0.0.

## Hai finito quando

- i tre file sono committati su `main`;
- il piano copre ogni criterio, vincolo e rinviato destinato a P4, o ne motiva il rinvio;
- la revisione del piano non ha rilievi critical o important aperti;
- hai consegnato all'utente, in italiano, un riepilogo breve (numero di task, decisioni prese, domande aperte) e il prompt `/goal` per la sessione che eseguirà il piano.
