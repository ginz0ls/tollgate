# Esecuzione del piano B3: istruzioni per l'agente

Esegui il piano `docs/superpowers/plans/2026-11-01-tollgate-b3-profilo-ai.md` con la skill `superpowers:subagent-driven-development`.

- **Progetto di B** (l'autorità): `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, compresa la sezione 9 (scelte dell'utente del 1° novembre 2026). Le scelte marcate «utente» non si discutono; quelle marcate «mia scelta» si correggono solo con una `Ruling:` che dice il motivo.
- **Spec del nucleo:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, oggi alla revisione 28. La revisione 29 la scrive il Task 11.
- **Piano principale di B:** `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, sezioni 2, 3 e 9.
- **Registro di B2**, modello del metodo: `docs/sdd/2026-10-29-tollgate-b2-regole-di-base/`. Da riusare, adattati: `implementer-rules.md`, `reviewer-rules.md`, `rereview-rules.md`, `cautele.md`, la forma di `progress.md`, `carry.md`, `preflight-scan.md`, `final-review.md`.

## Dove lavorare

- Ramo `b3-profilo-ai`, in un worktree isolato in `.claude/worktrees/b3`, creato con `superpowers:using-git-worktrees` da `main`. Mai su `main`.
- Avvia la sessione dalla **radice del repo**, non dal worktree (memoria `sessioni-nei-worktree`).
- Il workspace SDD sta **nel worktree**: `.claude/worktrees/b3/.superpowers/sdd/<cartella stampata da sdd-workspace>`. I fatti raccolti per scrivere il piano sono in `.superpowers/plan-b3/` della radice (ignorata da git): copiali nel workspace all'inizio, sono un punto di partenza da verificare, non un'autorità.
- Baseline: prima del Task 1 lancia `tests/run` nel worktree e annota nel ledger il numero di test (3238 su `main` dopo B2).
- **Tempi della suite.** Una corsa di `tests/run` dura da 25 a 90 minuti (due interpreti). Lanciala in background e aspetta l'esito sul file d'uscita. Il brief di ogni implementatore lo dice, insieme al divieto di lanciare la suite completa più di una volta per giro quando bastano i file di test del task.
- **Avvisi come errori, come la CI:** `PYTHONWARNINGS=error::ResourceWarning tests/run`.
- **Lucchetto di git.** Il 1° novembre un commit sul checkout principale ha trovato due volte `.git/index.lock` già esistente e poi sparito da solo (la cartella è sincronizzata da MEGA). Se succede: ritenta dopo qualche secondo; **non cancellare mai** `index.lock` a mano.

## Scan pre-flight

Prima del Task 1, un analista sonnet in sola lettura scrive `preflight-scan.md`: tabella per coppie di task (cosa produce uno, cosa consuma l'altro, nomi e firme), tabella per task (test previsti contro codice previsto, file toccati da più task), conflitti con il progetto di B, con la spec rev 28 e con il codice reale di `main`. Lo giudichi tu: una `Ruling:` nel ledger e una voce in `carry.md` per ogni conflitto, **prima** di lanciare i task che ne dipendono. Punti da far guardare apposta:
- le frasi dei rinvii 184-187 (Task 1) contro i test esistenti di `test_manifest.py` che citano frasi alla lettera di `implementer.md`, e contro il test di deriva del Task 8;
- `area_rules` (Task 2) contro i chiamanti di `base_rules` (`lookups.base_rules`, `task_verdict`, `apply._final_rules`) e contro `test_rules_base.py`;
- `fragments.py` in `tollgate_core` e `tomlout.py` in `tollgate_analysis` contro `tests/test_layers.py` e `tests/test_analysis_isolation.py`; `init.py` (`tollgate_flow`) che li importa;
- `init.propose` e i test esistenti di `tests/test_init.py` (`test_files_tree`, `UpdateTest`, `ModeRewriteTest`) contro i blocchi aggiunti in coda: verifica che nessun test esistente spinga file che i frammenti veri accendono fuori dalle cartelle escluse (decisione 5), compreso l'albero installato in `.github/tollgate/`; è la garanzia di `test_real_trees_light_no_profile` (Task 3), non una radice nuova per quei test;
- `READONLY_TYPES` e `readonly_agents` contro `test_readonly_list_matches_config_and_agents` e `test_other_agent_types_reach_python`;
- il frontmatter `skills: [rules-base, rules-ai]` contro il parser di `tests/test_manifest.py` e contro `claude plugin validate --strict`;
- `B1_FLOW_CASE` (Task 9) contro i test di B1 e B2 in `tests/test_b1_scripts.py`.

## Ordine e modelli

1. **Task 1-4:** implementatore sonnet. Il piano dà firme e test, non il codice: niente haiku.
2. **Task 5, Step 0** e **Task 6, Step 1** sono del controller: copia delle fonti; lancio del verificatore delle fonti (`Explore`, sonnet, sola lettura).
3. **Task 5 e 6:** implementatore sonnet, il 6 dopo il verificatore.
4. **Task 7:** il controller con l'utente (Step 1), poi un implementatore sonnet (Step 2-4). È una **fermata pianificata**.
5. **Task 8:** implementatore sonnet, **solo dopo il Task 7**.
6. **Task 9:** script e progetto di prova, scritti da un implementatore sonnet senza rete e senza `claude`, dopo il Task 8. **Task 10:** esecuzione del controller, dopo il Task 9.
7. **Task 11:** implementatore sonnet, dopo il Task 10.
8. **Revisioni:** revisore di ogni task sonnet; ri-revisioni mirate sonnet; **revisione finale dell'intero ramo opus**.
9. Indica sempre il modello a ogni lancio di un subagente.

## Ruling nel ledger e `carry.md`

Il piano dà firme, test e valori; il corpo lo scrive l'implementatore. Se il piano contraddice il progetto o la spec, vince il progetto, poi la spec: decidi tu, scrivi `Ruling: <cosa> — <perché> — <costo se sbagliata>` nel ledger e vai avanti. Una correzione che cambia la spec va nella revisione 29, scritta dal Task 11. I rilievi minori vanno nel ledger come `Task N: minor (deferred): …`: la revisione finale ne fa il triage, e quelli che riguardano B3-bis e B4-B7 finiscono nel piano principale di B. **Le regole di `rules-ai` non si decidono con una `Ruling:`**: le decide l'utente nel Task 7.

## Lezioni dei piani precedenti

- **Le prove reali si dividono**: preparazione con test (Task 9) ed esecuzione del controller (Task 10). Le correzioni del prodotto scoperte in una prova sono giri del Task 9, ognuna con un test, e si ripete **solo** il passo interessato.
- **Gli implementatori non eseguono mai** `spikes/run-b1-flow.sh` fuori da `bash -n`, `controlla` e dai test, né `claude -p`.
- **Un esito ottenuto in più tentativi è «composito»**, e il rapporto lo dice.
- **Evidenze anonimizzate prima del commit**, perché il repo è pubblico: id di sessione, `/home/<utente>`, nome utente e nome dell'host. Prima di ogni commit di evidenze e prima della copia del registro: `grep` del nome utente, dell'host e delle forme di token. Nei file nuovi niente nomi di progetti privati dell'utente.
- **Il brief del revisore contiene il report dell'implementatore** (B2, I-2): le regole sul report si giudicano lì; il revisore finale giudica solo il diff.
- **Gli implementatori a volte restano fermi** dopo aver lanciato la suite in background, aspettando una notifica: il brief dice di controllare da soli il file d'uscita; se un implementatore tace, sollecitalo con `SendMessage`.
- **Workspace e registro.** Il workspace SDD sta nel worktree e si copia in `docs/sdd/` alla chiusura, senza i `.diff`, i log della suite e le copie delle fonti.

## Regole di cautela

Copiale **nel brief di ogni subagente, al lancio** (l'utente lo considera vincolante). Sono quelle di `docs/sdd/2026-10-29-tollgate-b2-regole-di-base/cautele.md`, con i percorsi di B3, e con le **sole** eccezioni elencate dopo, che valgono **solo per il controller** e non vanno mai a un subagente.

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` e una `HOME` temporanea.
- Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/`, né nei test né nel lavoro.
- Mai installare, abilitare o disinstallare plugin. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Esperimenti e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete, nessun repo su GitHub, nessun push verso la rete. `gh` nei test è `tests/fakegh.py`. Mai il `gh` vero.
- `spikes/run-b1-flow.sh`: solo `bash -n`, il modo `controlla` e i test di `tests/test_b1_scripts.py`. `evals/run.sh`: solo `bash -n` e `controlla`.

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID.
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`. Mai `git stash`. Mai cancellare `.git/index.lock` a mano.
- Non leggere né riportare `.env`, `auth.json`, token o segreti. Nessuna chiave API nei test, negli script o nelle evidenze.
- La suite in background solo con lo strumento Bash e `run_in_background`, **mai con `&` o `nohup`** (in B2 un implementatore l'ha fatto).

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`.
- Nessun `__pycache__` nel commit (`python3 -B`): controlla `git status` prima di `git add`.
- **Mai scrivere `approved` in `skills/rules-ai/SKILL.md` fuori dal Task 7.**
- Lavora solo nel worktree `.claude/worktrees/b3` (ramo `b3-profilo-ai`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Eccezioni per il controller, una per una**
1. **Copia delle fonti** (Task 5, Step 0): `curl -sSfL --max-time 60` in sola lettura (GET, senza credenziali) delle pagine ufficiali di Anthropic (`platform.claude.com`, `docs.claude.com`, `docs.anthropic.com`) di Google (`ai.google.dev`, `cloud.google.com`, `github.com/googleapis` per gli SDK), di OpenAI (`platform.openai.com`, `github.com/openai` per gli SDK), di OpenRouter (`openrouter.ai`), di Agno (`docs.agno.com`) e di Supabase (`supabase.com/docs`, per le edge function) elencate nella decisione 13, salvate in `<workspace>/fonti/ai/` con `SHA256SUMS` e `FONTI.md`. Se una pagina ufficiale sta su un altro dominio dello stesso fornitore, ti fermi e chiedi all'utente prima di scaricarla. Nessun'altra rete.
2. **`claude -p` nel Task 10** (prova reale corta): solo da `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=ai B1_FLOW_RULES=vere`, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir /tmp/tollgate-b1/plugin`, `--model sonnet`, `--permission-mode acceptEdits` e l'`--allowedTools` dello script, con il `gh` finto nel `PATH` e lo stato con la sentinella. Al più **3 tentativi per passo**: oltre ti fermi e chiedi.
3. **Rete del modello in quelle esecuzioni:** `WebFetch` e `WebSearch` verso la documentazione pubblica sono ammessi; `curl`, `wget`, `gh` vero e `git push` verso remoti non locali restano vietati al modello con `--disallowedTools`.
4. **Trascrizioni della prova:** `registra` legge in sola lettura le trascrizioni dei subagenti delle sole due cartelle della prova in `~/.claude/projects/` (passo 1 dal checkout, passo 2 dal worktree, ricavate dal `cwd` e dal `session_id`), e salva solo le righe trovate (piano principale, sezione 9, rinvio 181). Nessun'altra lettura di `~/.claude/`.
5. **Push di `main` su `https://github.com/ginz0ls/tollgate.git`**, solo dopo il merge con l'OK dell'utente e solo dopo `spikes/gh-p4/ghguard.py gitcheck -- push https://github.com/ginz0ls/tollgate.git main` con `P4_PROFILE=p5` uscito con 0; mai forzato. Poi `gh run list|view|watch` della CI di `main`, dalla guardia con lo stesso profilo (`run list` senza `--branch`). Nessun altro comando verso GitHub.
6. Le esecuzioni con `claude -p` consumano l'abbonamento dell'utente: nessun denaro in più, ma il consumo va riportato nel rapporto e all'utente.

Vietati anche al controller: ogni operazione sui repo di prova di P4 e su altri repo; segreti; cambi di visibilità; cancellare repo o rami remoti; `claude plugin eval` (gli eval sono di B8).

## Quando fermarsi e chiedere

Solo in questi casi:
- **Task 7, Step 1: l'approvazione della pagina.** È la fermata prevista. Se l'utente rinvia l'approvazione, chiedigli se unire su `main` **solo i Task 1-4** (decisione 17) e lasciare il resto sul ramo.
- più di 3 tentativi di un passo della prova reale;
- un'operazione distruttiva o irreversibile, o un'operazione su GitHub fuori dall'eccezione 5;
- un'azione fuori da questo worktree, come un merge su `main`;
- un piano rotto al punto che ogni strada è un'ipotesi.

Il resto si decide con una `Ruling:`. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.

## Chiusura

1. **Revisione finale** del ramo con **opus**, in sola lettura. Passagli: «Decisioni di questo piano», «Review Focus», la tabella «Copertura», le righe `minor (deferred)` del ledger da sottoporre a triage, i rapporti dei Task 6 e 10, le regole di cautela. Chiedigli in particolare di cercare i guasti che nascono dall'incontro di due stati (un `tollgate.toml` dell'utente con un profilo omonimo; un `--update` ripetuto; un frammento con la skill non approvata; un agente per area che manca; un task che tocca file `ai` e di un altro profilo), di controllare che nessun test dipenda in silenzio dai file veri del plugin, che le regole, la pagina, il rapporto delle fonti e il frammento coincidano, e che le copie degli agenti non divergano dai generici.
2. Correggi i rilievi `critical` e `important`: per ognuno prima un test che fallisce, poi la correzione. Dopo ogni giro una ri-revisione mirata (sonnet), finché non ne restano. Una correzione che cambia una regola approvata torna all'utente (Task 7, Step 1). Se una correzione tocca ciò che la prova reale ha provato, ripeti **solo** il passo interessato, nelle eccezioni 2 e 3.
3. **Suite tre volte**: `PYTHONWARNINGS=error::ResourceWarning tests/run` (python3.11 e python3), tre corse verdi, nessun «unclosed database».
4. **Niente merge su `main` senza l'OK dell'utente.** Riporta all'utente, in italiano, in breve e in parole semplici: commit e numero di test, `Ruling:` prese con il costo, minori rinviati con il triage, regole approvate, esito della prova reale (proposta di `init`, agenti lanciati, precaricamento, nota, verdetto, consumo), e che cosa cambia da ora nei progetti (il profilo arriva solo con `init --update` e la copia del blocco). Poi chiedi l'OK per il merge.
5. Dopo il merge (con l'OK):
   - push di `main` (eccezione 5) e attesa della CI verde su `main`;
   - copia il registro dal worktree in `docs/sdd/2026-11-01-tollgate-b3-profilo-ai/` con un `README.md`, come per B2, dopo il controllo di anonimizzazione, e committalo su `main` (e push);
   - aggiorna la memoria del progetto (`plugin-workflow-decisioni.md`): esito di B3, regole approvate, prossimo passo (scrivere il piano di B3-bis, la sentinella dei modelli);
   - **trascrizioni**: se una sessione del lavoro è partita dalla cartella del worktree, spostane i `.jsonl` (e le cartelle `<id>/`) con `mv -n` nella cartella della radice in `~/.claude/projects/`, mai il file della sessione attiva. Se tutte le sessioni sono partite dalla radice, dillo;
   - chiedi all'utente se rimuovere il worktree e il ramo `b3-profilo-ai` ormai uniti.
