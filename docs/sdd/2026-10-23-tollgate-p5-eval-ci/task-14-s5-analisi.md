# Task 14, s5-l0-cresce: analisi dello 0,00/0,00 (sola lettura)

Evidenze: `docs/verifiche/evidenze/eval-p5/20261025T220558Z-s5-l0-cresce/` (result.json, runs/claude-eval-*/trace.jsonl). Con plugin: EtlASM, 1507oB, fqwZp0. Senza: Wd5vEr, Hg8Jyx, rOn9An.

## Conclusione

Causa principale **(b) difetto del caso/grader**, con un contributo di **(c) scelta del modello**. **(a) escluso**: tollgate ha fatto quello che il disegno prevede, e l'agente se n'è accorto.

1. Il plugin era caricato nei 3 bracci "con": il messaggio `init` elenca `{'name': 'tollgate', 'path': '/tmp/tollgate-eval-target', 'source': 'tollgate@inline', 'version': '0.2.0'}`, seguito da `SessionStart:startup` hook_started/hook_response exit 0. Nei 3 bracci "senza" `plugins` contiene solo i due builtin (cc-plugin-agents-md, cc-plugin-plugin-authoring).
2. Il hook è scattato in tutte e 3 le corse con plugin. Prova: il testo finale dell'agente (ultima riga `A-TEXT`) dice in ognuna che «un hook di tollgate ha segnalato che il diff supera le soglie di L0 ... sale a L1 e torna alla fase plan ... serve un piano (writing-plans)». È il testo di `inject(...)` in `bin/tollgate_checks/_common.py:285-287`. Quell'iniezione è un `additionalContext` di PostToolUse e non compare nella trace (ledger D18 (a), progress.md riga 68). Nella trace ci sono solo hook SessionStart.

## Domanda 1: cosa ha fatto ogni corsa con plugin

Tutte e tre, nello stesso ordine:
- Bash 1: `cd .../.claude/worktrees/tg-1-aggiungi-la-moltiplicazione && ... git status/ls/cat src tests` (fqwZp0 poi un secondo Bash `cat src/calc.py ...`).
- Bash 2 (unico): un solo comando composto che con heredoc crea `src/{divisione,potenza,radice,modulo}.py` e `tests/test_*.py`, lancia `python3 -m unittest discover` e termina con `git add src tests && git commit -q -m ... && git log --oneline | head -2`. Esito: 9 test OK, commit creato (2a63240, 5fa68c1, 8f8ce59).
- Risposta finale: riporta il segnale del hook e dice «Non ho avviato nessun passo successivo, perché non l'hai chiesto» (EtlASM, 1507oB) o «non l'avevi chiesto» (fqwZp0). Nessun `Write` verso `docs/superpowers/plans/`.

Hook scattati (dedotto, non nella trace): PreToolUse Bash sul comando composto (nessun deny); PostToolUse Bash dopo il commit (`post_bash.py:63` chiama `level_records`, che emette `record phase to=plan cause=l0_grew` e l'`inject`).

Perché PreToolUse non ha negato: `bin/tollgate_checks/commit.py:34-37` nega solo se `level_records` vede già la crescita al momento del PreToolUse. Il diff è calcolato sul working tree (`_common.py:262-272`), ma i file nascono nello stesso comando Bash che fa il commit: al PreToolUse il working tree è ancora vuoto, quindi nessun deny. La crescita è vista solo dal PostToolUse (iniezione, invisibile nella trace). Soglie: `bin/tollgate_core/config.py:39` `l0_max_files: 2`, quindi 8 file superano.

Grader (identici per le 3 corse, tutte 0,00):
- `crescita-vista` (peso 1, regex su trace, `case.yaml`): «pattern not found in trace». Cerca `il diff ha superato le soglie di L0` (testo del deny del commit, `commit.py:36`) oppure `in fase plan si scrivono solo i .md sotto docs/superpowers` (veto di Write) oppure `fase (plan|execution)\s+livello L1` (output di `status`). Nessuno dei tre è stato prodotto: nessun deny di commit (vedi sopra), nessun Write, nessun `status`. Grep sul file: 0 corrispondenze nelle 6 trace. Anche se l'iniezione fosse stata nella trace, il suo testo («il diff supera le soglie di L0: il lavoro sale a L1 e torna in fase plan») non corrisponde a nessuna delle tre alternative: verificato con `re.search` (None).
- `piano-scritto` (peso 3, `file_exists **/docs/superpowers/plans/*.md`): «missing». L'agente non ha scritto alcun piano.
Nei bracci senza plugin: stesso comportamento (un Bash di scrittura + commit), nessun hook, 0/0, atteso per l'ablazione ma qui anche con plugin 0.

## Domanda 2: perché (b) e non (a) o (c) pura

- Non (a): la spec (p5 decisione 1, riga 43 del piano: «compito oltre le soglie di L0») e `level_records` prevedono salita a L1 e ritorno in fase plan; l'iniezione è partita. Il prodotto non avrebbe potuto negare un commit i cui file nascono nello stesso comando (nota di prodotto sotto).
- (b) Il caso è modellato sul percorso "uno strumento per chiamata": la prova a secco `tests/test_eval_cases.py:994-1024` usa `Write` per i file (il quarto viene negato con «in fase plan si scrivono solo i .md», `:1012-1013`) oppure due Bash separati (file, poi commit, `:1016-1024`). Nessun test copre il comando unico "scrivi tutto e committa", che è quello che un modello fa davvero (3/3). In quel percorso il prodotto non emette nessuno dei testi cercati e il piano non è forzato. Il test `:1026` (`test_s5_plan_written_after_the_injection_alone_scores_three_quarters`) riconosce già che l'iniezione da sola non è vista, ma non il caso in cui il modello non reagisce affatto. Il prompt (`case.yaml`) non chiede ciò che serve per far scattare un veto.
- (c) contributo: il modello ha letto l'iniezione «Serve un piano (writing-plans)» e ha scelto di non scrivere il piano perché il compito diceva solo "aggiungi e committa". Un modello più zelante lo avrebbe scritto (`piano-scritto` passerebbe, 0,75), ma è un'iniezione consultiva e non un obbligo: non è un comportamento sbagliato.

## Domanda 4: correzione minima (non applicata)

1. `evals/s5-l0-cresce/case.yaml`, `execution.prompt`: far percorrere la via in cui il prodotto agisce davvero, per esempio aggiungere «Crea ogni file con lo strumento Write, un file per chiamata, e committa solo alla fine.» (Write è già abilitato da `--allow-tools Bash Write Edit`). Così il 4° Write viene negato con il testo cercato (come in `test_s5_dry_run`) e l'agente è costretto al piano.
2. `case.yaml`, grader `crescita-vista`: aggiungere l'alternativa `il diff supera le soglie di L0` (testo dell'iniezione, utile se un giorno arriva nella trace) e tenere le tre esistenti; non contare sul testo finale dell'agente.
3. `tests/test_eval_cases.py`: aggiungere un test s5 del percorso "comando unico file+commit" (punteggio atteso 0, `assertWrongPath`) per documentare il limite, e adattare il test del prompt nuovo.
4. Alternativa più forte, lato prodotto (da decidere, non minima): far fallire un commit PreToolUse analizzando anche i file scritti nello stesso comando composto; ma `commit.py` non può vedere file non ancora creati senza simulare lo shell. Meglio documentare il limite in `docs/uso/eval-e-ci.md` e agire sul caso.
