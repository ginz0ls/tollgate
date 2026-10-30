# Esecuzione del piano B2: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-10-29-tollgate-b2-regole-di-base.md` con la skill `superpowers:subagent-driven-development`.

- **Progetto di B** (l'autorità): `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`. Le scelte marcate «utente» non si discutono; quelle marcate «mia scelta» si correggono solo con una `Ruling:` che dice il motivo.
- **Spec del nucleo:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 27. La revisione 28 la scrive il Task 8.
- **Piano principale di B:** `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, sezioni 3 e 9.
- **Registro di B1**, modello del metodo: `docs/sdd/2026-10-27-tollgate-b1-informati-prima/`. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md` e di `preflight-scan.md`.

## Dove lavorare

- Ramo `b2-regole-base`, in un worktree isolato in `.claude/worktrees/b2`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`.
- Avvia la sessione dalla **radice del repo**, non dal worktree: così la trascrizione resta visibile in `/resume` dalla radice (memoria `sessioni-nei-worktree`).
- Il workspace SDD (ledger, brief, report, copie delle fonti) sta **nel worktree**: `.claude/worktrees/b2/.superpowers/sdd/<cartella stampata da sdd-workspace>`.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (3166 su `main` dopo B1).
- **Tempi della suite.** Con circa 3200 test una corsa di `tests/run` dura da 25 a 55 minuti quando la macchina è carica (due interpreti). Lanciala in background e aspetta l'esito sul file d'uscita, senza restare fermo. Il brief di ogni implementatore lo dice, insieme al divieto di lanciare la suite completa più di una volta per giro quando basta il file di test del task (il Task 2 è l'eccezione: la sua misura è la suite completa).
- **Avvisi come errori, come la CI:** `PYTHONWARNINGS=error::ResourceWarning tests/run`. `python -W …` non arriva ai sottoprocessi e in B1 ha nascosto due file non chiusi, visti solo dalla CI.

## Scan pre-flight

Prima del Task 1, un analista sonnet in sola lettura scrive `preflight-scan.md`:
- una tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere);
- una tabella per task (test previsti contro codice previsto, file toccati da più task);
- i conflitti con il progetto di B, con la spec rev 27 e con il codice reale di `main`.

Lo giudichi tu: per ogni conflitto una riga `Ruling:` nel ledger e una voce in `carry.md` per i task che ne dipendono, **prima** di lanciarli. Punti da far guardare apposta:
- `rules_switch` (Task 1) contro i due chiamanti di `rules_enforced` (`research_gate`, `taskcmd`) e contro `test_unreadable_is_off_for_now`, che il Task 1 sostituisce;
- il tipo nuovo `research_switch_unreadable` contro `events.EVENT_TYPES` (elenco chiuso) e contro la spec 18.4;
- l'ordine dei moduli in `pre_edit` (`writes` 20, `research_gate` 25): il primo `deny` vince, gli `inject` si sommano;
- i test che oggi usano la radice vera, nel processo dei test (`tests/hookkit.py` `ROOT`, `taskcmd.db.BIN_PATH`) e in sottoprocesso (`hooks/run` e `bin/tollgate` lanciati da `tests/flowkit.py` e dalle prove a secco di `tests/test_eval_cases.py`), contro l'accensione del Task 5 (decisione 7);
- i test che oggi vogliono `skills/rules-base/` assente o ogni skill documentata (`tests/test_b1_scripts.py` righe 169 e 555, `tests/test_docs.py` `test_every_skill_documented`) contro il file di prova del Task 2 e la bozza del Task 3;
- il formato del frontmatter `skills: [rules-base]` contro il parser di `tests/test_manifest.py` e contro `claude plugin validate --strict`;
- `test_implementer_tools`, `test_implementer_mentions_untrusted_pages`, `test_implementer_mentions_research_submit` contro le modifiche di `implementer.md` del Task 6;
- `B1_FLOW_RULES` e `B1_FLOW_SRC` (Task 7) contro i test di `tests/test_b1_scripts.py` che oggi controllano la `rules-base` di prova.

## Ordine e modelli

1. **Task 1-3:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku.
2. **Task 3, Step 0** e **Task 4, Step 1** sono del controller: copia delle fonti; lancio del verificatore delle fonti (`Explore`, sonnet, sola lettura).
3. **Task 4:** implementatore sonnet, dopo il verificatore.
4. **Task 5:** il controller con l'utente (Step 1), poi un implementatore sonnet (Step 2-4). È una **fermata pianificata**: la regola «non fermarti tra i task» non vale qui.
5. **Task 6:** implementatore sonnet, **solo dopo il Task 5** (decisione 2: gli agenti caricano solo regole approvate).
6. **Task 7:** script scritto da un implementatore sonnet senza rete e senza `claude`; esecuzione del controller, dopo il Task 6.
7. **Task 8:** implementatore sonnet, dopo il Task 7.
8. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
9. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger e `carry.md`

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice il progetto o la spec, vince il progetto, poi la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. Una correzione che cambia la spec va nella revisione 28, scritta dal Task 8. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage, e quelli che riguardano B3 e oltre finiscono nel piano principale di B. **Le regole di `rules-base` non si decidono con una `Ruling:`**: le decide l'utente nel Task 5.

## Lezioni dei piani precedenti

- **Le prove reali si dividono**: preparazione con test (Task 7, Step 1) ed esecuzione del controller (Task 7, Step 2). Le correzioni del prodotto scoperte in una prova sono giri del task della prova, ognuna con un test, e si ripete **solo** il passo interessato.
- **Gli implementatori non eseguono mai** `spikes/run-b1-flow.sh` fuori da `bash -n`, `controlla` e dai test, né `claude -p`: il brief di ogni lancio e di ogni giro di correzione lo dice.
- **Un esito ottenuto in più tentativi è «composito»**, e il rapporto lo dice.
- **Evidenze anonimizzate prima del commit**, perché il repo è pubblico: id di sessione, `/home/<utente>`, nome utente e **nome dell'host** (in B1 era rimasto in una revisione copiata in `docs/sdd/`). Prima di ogni commit di evidenze e prima della copia del registro: `grep` del nome utente, dell'host e delle forme di token.
- **Workspace e registro.** Il workspace SDD sta nel worktree e si copia in `docs/sdd/` alla chiusura, senza i `.diff`. La riga «Stato» del piano principale non cita `.superpowers/` (è ignorato da git).

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante). Sono quelle di `docs/sdd/2026-10-27-tollgate-b1-informati-prima/cautele.md`, con i percorsi di B2, e con le **sole** eccezioni elencate dopo, che valgono **solo per il controller** e non vanno mai a un subagente.

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`) e una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`, `evals/_kit/`).
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/`, né nei test né nel lavoro: le fonti delle regole sono le copie nel workspace.
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Esperimenti e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete, nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py`. Mai `gh auth`, `gh api`, `gh pr create` né alcun altro comando col `gh` vero.
- `spikes/run-b1-flow.sh`: solo `bash -n`, il modo `controlla` e i test di `tests/test_b1_scripts.py`. Mai un altro modo, nemmeno per prova, nemmeno in un giro di correzione: l'esecuzione è del controller.
- `evals/run.sh`: solo `bash -n` e il modo `controlla` (gli eval sono di B8).

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push verso remoti veri, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Non leggere né riportare `.env`, `auth.json`, token o segreti.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit: controlla `git status` prima di `git add`. Il file di prova del Task 2 (`skills/rules-base/SKILL.md` con `approved: 2026-01-01`) **non si committa mai**.
- **Mai scrivere `approved` in `skills/rules-base/SKILL.md` fuori dal Task 5**: accenderebbe il blocco senza l'utente.
- Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b2` (ramo `b2-regole-base`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Tempi della suite**
- Con circa 3200 test una corsa di `tests/run` dura da 25 a 55 minuti quando la macchina è carica. Lanciala in background e aspetta l'esito sul file d'uscita, senza restare fermo. Mentre lavori lancia solo i file di test del task; la suite completa al più una volta per giro, prima del commit.

**Eccezioni per il controller, una per una**
1. **Copia delle fonti** (Task 3, Step 0): lettura in sola lettura dei file di `~/.claude/plugins/cache/` elencati nel Task 3, copiati nel workspace con `SHA256SUMS`. Nessun'altra lettura di `~/.claude/plugins/`.
2. **`claude -p` nel Task 7** (prova reale corta): solo da `spikes/run-b1-flow.sh` con `B1_FLOW_RULES=vere`, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir /tmp/tollgate-b1/plugin` (la copia con la `rules-base` vera), `--model sonnet`, `--permission-mode acceptEdits` e l'`--allowedTools` dello script, con il `gh` finto nel `PATH` e lo stato con la sentinella. Al più **3 tentativi per passo**: oltre ti fermi e chiedi. Motivo: progetto 5 e piano principale, riga B2.
3. **Rete del modello in quelle esecuzioni:** `WebFetch` e `WebSearch` verso la documentazione pubblica sono ammessi; `curl`, `wget`, `gh` vero e `git push` verso remoti non locali restano vietati al modello con `--disallowedTools`.
4. **Push di `main` su `https://github.com/ginz0ls/tollgate.git`**, solo dopo il merge con l'OK dell'utente e solo dopo `spikes/gh-p4/ghguard.py gitcheck -- push https://github.com/ginz0ls/tollgate.git main` con `P4_PROFILE=p5` uscito con 0; mai forzato. Poi `gh run list|view|watch` della CI di `main`, dalla guardia con lo stesso profilo (`run list` senza `--branch`, che la guardia non ammette). Nessun altro comando verso GitHub.
5. Le esecuzioni con `claude -p` consumano l'abbonamento dell'utente: nessun denaro in più, ma il consumo va riportato (token da `tollgate stats` e dalle trascrizioni) nel rapporto e all'utente.

Vietati anche al controller: ogni operazione sui repo di prova di P4 (`ginz0ls/tollgate-p4-protected`, `ginz0ls/tollgate-p4-detect`) e su altri repo; segreti; cambi di visibilità; cancellare repo o rami remoti; `claude plugin eval` (gli eval sono di B8).

## Quando fermarsi e chiedere

Solo in questi casi:
- **Task 5, Step 1: l'approvazione della pagina.** È la fermata prevista: mostri la pagina e aspetti la risposta. Se l'utente rinvia l'approvazione, chiedigli se unire su `main` **solo i Task 1 e 2** (interruttore e test indipendenti, che non portano regole: decisione 13 e progetto 5, punto 4) e lasciare il resto sul ramo per una sessione successiva; B2 non è finita finché la pagina non è approvata.
- più di 3 tentativi di un passo della prova reale;
- un'operazione distruttiva o irreversibile, o un'operazione su GitHub fuori dall'eccezione 4;
- un'azione fuori da questo worktree, come un merge su `main`;
- un piano rotto al punto che ogni strada è un'ipotesi.

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: «Decisioni di questo piano», «Review Focus», la tabella «Copertura», le righe `minor (deferred)` del ledger da sottoporre a triage (con il rinvio 37 di B1, `cat` con glob che non registra i file, che con il blocco acceso costa un giro di rifiuto), i rapporti dei Task 4 e 7, le regole di cautela. Chiedigli in particolare di cercare i guasti che nascono dall'incontro di due stati (l'interruttore acceso e un lavoro in corso già avvisato; l'interruttore illeggibile e un task senza nota; un task senza modifiche con una nota non valida), di controllare che nessun test dipenda in silenzio dallo stato dell'interruttore nel repo, che le regole, la pagina e il rapporto delle fonti coincidano, e che il testo delle fonti non entri mai come istruzione in un brief.
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano. Una correzione che cambia una regola approvata torna all'utente (Task 5, Step 1). Se una correzione tocca ciò che la prova reale ha provato, ripeti **solo** il passo interessato, nelle eccezioni 2 e 3.
3. **Suite tre volte**: `tests/run` (python3.11 e python3) e `PYTHONWARNINGS=error::ResourceWarning tests/run`, tre corse verdi, nessun «unclosed database» a fine suite.
4. **Niente merge su `main` senza l'OK dell'utente.** Riporta all'utente, in italiano, in breve e in parole semplici: commit e numero di test, `Ruling:` prese, minori rinviati con il triage, regole approvate, esito della prova reale (letture, nota, avvisi e rifiuti, consumo), e che cosa cambia da ora nei lavori L1 e L2 (compresi quelli già in corso). Poi chiedi l'OK per il merge.
5. Dopo il merge (con l'OK):
   - push di `main` (eccezione 4) e attesa della CI verde su `main`;
   - copia il registro dal worktree in `docs/sdd/2026-10-29-tollgate-b2-regole-di-base/` con un `README.md`, come per B1, dopo il controllo di anonimizzazione, e committalo su `main` (e push);
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`): esito di B2, regole approvate, blocco acceso, prossimo passo (scrivere il piano di B3);
   - **trascrizioni**: se una sessione del lavoro è partita dalla cartella del worktree, spostane i `.jsonl` (e le cartelle `<id>/`) con `mv -n` da `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow--claude-worktrees-b2/` a `~/.claude/projects/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/`, mai il file della sessione attiva mentre è in uso. Se tutte le sessioni sono partite dalla radice, non c'è nulla da spostare: dillo;
   - chiedi all'utente se rimuovere il worktree e il ramo `b2-regole-base` ormai uniti.
