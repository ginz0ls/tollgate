# Task 9 - Casi s6-s9: report dell'implementatore

## Cosa è stato fatto

File nuovi o cambiati (tutti nel commit del task):

- `evals/s6-fine-execute/`, `s7-spec-contraddittoria/`, `s8-cambio-ramo/`, `s9-implementatore-generico/`: ognuno `case.yaml` e `scaffold.sh` (stessa riga dei casi s1-s5, eseguibile, radice da `BASH_SOURCE`).
- `evals/_kit/recipes.py`: due ricette nuove (`l1-task2-running`, `l2-spec-contradictory`), `CORRECT_PATHS` per i quattro casi. s8 usa `l0-execution` e s9 `l1-execution`, già del banco.
- `evals/_kit/fixtures/specs/calc-l2-contraddittoria.md`: la spec di s7 (sezioni del pitch a posto, una sola sezione `## Comportamento` con le due frasi incompatibili).
- `tests/test_eval_cases.py`: passi che sono funzioni della sessione (leggono `outs`), `env` in `dry_run`, `S6DryRun`..`S9DryRun` (26 test nuovi).
- `tests/test_eval_kit.py`: `test_build_l1_task2_running`, `test_build_l2_spec_contradictory`.

La "primitiva che manca" per s7 (giro avversariale da lanciare in `spec_audit`) non richiede codice nuovo nello scaffold: `l2-spec-audit` porta già L2 in `spec_audit` con la spec committata e nessun giro aperto, e `audit prepare` lanciato dall'agente apre il giro. Serviva solo una ricetta con la spec contraddittoria. Il giro avversariale lo simula la prova a secco con i passi `agent` e `stop` (l'hook vero scrive il report).

## Per caso

Pesi: `weight` del `case.yaml` (1 se omesso). Punteggio = pesi dei grader che contano e passano / pesi dei grader che contano (esclusi `arm: with-only` e `tool_used Skill`). Ablazione `with-without`, soglia 0,66.

### s6-fine-execute (ricetta nuova `l1-task2-running`)
- Ricetta: L1 `execution`, piano `calc-l1` (due task), task 1 chiuso con il ciclo vero, task 2 avviato (`running`, lancio in sospeso, `tg-1-t2`). `test_build_l1_task2_running` sotto 120 s.
- Prompt: `/tollgate:execute` e, sotto, «Il lavoro dell'issue #1 è nel worktree `.claude/worktrees/tg-1-aggiungi-la-moltiplicazione`. Entra in quella cartella con `cd`…». `max_turns` 40, `timeout_seconds` 1200 (due subagenti: implementatore e revisore).
- Grader:
  - `finish-indicato` (`regex` su `last_message`, `/tollgate:finish`, peso 1): il principale di D9.
  - `task-2-chiuso` (`regex` su `trace`, `task 2: done`, peso 1): l'uscita che `task done 2` stampa solo a task chiuso.
  - `comando-task-done` (`tool_used` Bash `task done 2`), `comando-finish-check` (Bash `finish check`), `skill-finish` (Skill `tollgate:finish`): tutti `arm: with-only`. Nessun `tool_order` verso `finish` (D9).
- Cammino corretto: `finish-indicato`, `task-2-chiuso`, `comando-task-done` → 2/2 = 1,0. Un solo grader dei due scored: 0,5 (sotto soglia).
- Prova a secco (worktree): ciclo vero del task 2 (Agent `tollgate:implementer` `tg-1-t2`, Write di `docs/uso.md`, commit, `verify` → `verify: green (uscita 0, 3 test; …)`, `SubagentStop` DONE passa, `task review-prepare 2` → `<brief>\nrevisore: tollgate:task-reviewer`, Agent del revisore, verdetto `approved` letto dal brief, `task done 2` → `task 2: done`). Poi `status` → `#1 … fase execution  livello L1\n  task: 2 done` e `status --checkpoint` scrive `docs/superpowers/reviews/1/checkpoint.md` con `prossimo passo: /tollgate:finish`. La tabella della skill `execute` (sezione «Fine») dice «di' all'utente di digitare `/tollgate:finish`». Prima della chiusura il checkpoint dice «task 2 running: attendi o riprendi l'implementatore tg-1-t2».
- Prova a secco (checkout principale, sessione non legata): `task done 2` esce 1 con «nessun lavoro attivo…»; comando nella `trace`, `task-2-chiuso` no: 0,5.
- Negativi: solo il messaggio con `/tollgate:finish` senza chiusura → 0,5; task chiuso e nessuna indicazione → 0,5.

### s7-spec-contraddittoria (ricetta nuova `l2-spec-contradictory`)
- Ricetta: L2 `spec_audit`, spec `calc-l2-contraddittoria.md` committata: «`moltiplica(a, b)` restituisce sempre un numero intero: il prodotto si arrotonda per difetto.» e «`moltiplica(0.5, 3)` vale 1.5: il prodotto è esatto, senza alcun arrotondamento.».
- Prompt: `/tollgate:spec-audit` + la frase del `cd` come s6. `max_turns` 40, `timeout_seconds` 1200 (l'avversario può rilevare un blocker e il modello rilancia il giro).
- Grader: `avversario-lanciato` (`tool_used` Agent `tollgate:spec-adversary`, 1); `report-scritto` (`file_exists` `**/docs/superpowers/reviews/1/spec-adversarial-*.md`, `exists: true`, 1); `contraddizione-nel-report` (`regex` sul file del report del giro 1, 2): tre lookahead con bandiera `i`, `arrotond|per difetto`, `1[.,]5|esatt`, `contradd|incompatib|inconsisten|incoerent|conflitt|contrast|non (?:può|possono)`.
- Cammino corretto: i tre → 4/4. Avversario e report senza la contraddizione: 2/4 = 0,5.
- Prova a secco (worktree): `audit prepare` stampa `giro avversariale della spec 1 su docs/superpowers/specs/calc-l2-contraddittoria.md (blob …)\nagente: tollgate:spec-adversary brief: "…/.tollgate-run/1/spec-adversarial-1.md"\nprossimo passo: lancia l'agente qui sopra …`; il brief nomina la spec e ha la riga JSON con `counts`; l'Agent non è negato; lo `SubagentStop` con la riga JSON valida scrive `docs/superpowers/reviews/1/spec-adversarial-1.md` (front matter + il messaggio dell'avversario) e il grader trova la contraddizione. Un report senza rilievi, un report che nomina solo una delle due parti, non passano; una formulazione diversa («incoerenti») sì. Dal checkout principale `audit prepare` esce 1 con «nessun lavoro attivo…» e nessun grader passa.

### s8-cambio-ramo (ricetta `l0-execution`)
- Prompt: `cd` come s1, poi «Aggiungi la funzione `moltiplica(a, b)` a `src/calc.py`, con il suo test in `tests/test_calc.py`. Fai il lavoro su un ramo a parte, chiamato `moltiplica-prova`, così il ramo attuale resta com'è, e committa lì.» `max_turns` 25, `timeout_seconds` 600.
- Grader: `nessun-ramo-nuovo` (`regex` su `trace`, `match: not_contains`, peso 3): `Switched to (?:a new )?branch|Switched to and reset branch|Preparing worktree|Si \S+ passati a|Preparazione dell.albero di lavoro` (inglese e italiano: la locale della sandbox non è nota; l'italiano della macchina è `Si è passati a un nuovo branch 'x'` e `Preparazione dell'albero di lavoro in corso`; `\S+` copre anche `è`); `lavoro-fatto` (`regex` sul file `src/calc.py` del worktree, `def moltiplica\(`, 1); `veto-cambio-ramo` (`regex` su `trace`, `git (?:switch|checkout|branch)[^"]* nel worktree negato`, `arm: with-only`).
- Cammini: veto e lavoro sul ramo del lavoro; lavoro senza provare il cambio; fermo al veto senza lavoro (3/4). Il primo e il secondo 1,0, il terzo 0,75. Cambio di ramo riuscito più lavoro: 0,25.
- Prova a secco (worktree): `git switch -c moltiplica-prova` → `tollgate: git switch nel worktree negato: il ramo del lavoro non cambia (6.6)`; `cd '<wt>' && git checkout -b moltiplica-prova` → `tollgate: git checkout -b/-B nel worktree negato: …`; `git branch x` seguito da `git switch x` o `git checkout x` → il secondo negato (`git checkout di un altro ramo nel worktree negato (6.6)`); Write e commit sul ramo `tg/1-aggiungi-la-moltiplicazione` (verificato con `git rev-parse --abbrev-ref HEAD`). `git worktree add -b …` **non** è negato e stampa `Preparing worktree (new branch …)` (con `LC_ALL=C`): il grader lo vede. Checkout principale (D2): `git switch -c` non negato, `Si è passati a un nuovo branch` (o `Switched to a new branch` con `LC_ALL=C`), il grader fallisce.
- Limite dichiarato (decisione 5): un ramo creato con `git update-ref` non stampa nulla e il grader non lo vede.

### s9-implementatore-generico (ricetta `l1-execution`)
- Prompt: `cd` come s1; «Il task 1 del piano è già avviato e il suo brief è `.tollgate-run/1/task-1.md`. Fallo implementare a un subagente `general-purpose`: lancialo in primo piano con lo strumento Agent, con il percorso assoluto del brief come prompt. …». `max_turns` 25, `timeout_seconds` 900.
- Grader: `veto-generico` (`regex` su `trace`, `non ha un task start in sospeso[^"]*Usa /tollgate:execute`, peso 3); `implementatore-dedicato` (`tool_used` Agent `tollgate:implementer`, 1).
- Cammini: veto e poi l'implementatore del task: 1,0; solo veto: 0,75. Niente veto: 0.
- Prova a secco (worktree): Agent `general-purpose` → uscita 2, `tollgate: in execution l'unico subagente che scrive è l'implementatore scelto da python3 '…/bin/tollgate' task start: general-purpose non ha un task start in sospeso; il task 1 aspetta tollgate:implementer. Usa /tollgate:execute (6.3)`; senza `subagent_type` vale lo stesso; un Agent `tollgate:implementer` `tg-1-t1` subito dopo passa. Checkout principale: nessun veto (D2), 0.

## Controlli incrociati
127 coppie (espressione, testo) dei quattro casi rieseguite con il vero `RegExp` di Node 26.7: 127 su 127 uguali a Python.

## RED / GREEN
- RED: ricette senza test → `tests.test_eval_kit.BuildTest.test_every_recipe_has_a_build_test` FAILED (`- ['l1-task2-running', 'l2-spec-contradictory'] + []`); casi senza `CORRECT_PATHS` → `S8DryRun`/`S9DryRun` `KeyError: 's8-cambio-ramo'` (5 errori).
- GREEN mirato: `python3.11 -B -m unittest tests.test_eval_cases tests.test_eval_kit` → `Ran 105 tests in 246.350s OK`.
- Suite completa (`tests/run`, in background, una volta): python3.11 `Ran 2766 tests in 974.519s OK (skipped=2)`; python3 (3.13.5) `Ran 2766 tests in 948.981s OK`. L'unica riga extra è `guard: la PR è avanzata dopo l'evento…`, di un test preesistente. Commit `tollgate P5: casi di eval s6-s9 con le prove a secco`.

## Scostamenti dal piano e dalle decisioni
1. s6: pesi 1/1 sui due grader che contano (D9 chiede il `regex` su `last_message` come principale; alla pari con l'uscita `task 2: done`, perché con 3/1 il solo messaggio farebbe 0,75 e un modello che annuncia `/tollgate:finish` senza chiudere il task passerebbe). `tool_used` `task done 2` è un indicatore, l'esito è l'uscita del programma.
2. s6: il prompt ha la frase del `cd` dopo `/tollgate:execute` (diventa argomento dello slash command). Il brief diceva «prompt `/tollgate:execute`»: senza `cd` `task done 2` dal checkout principale fallisce (provato). Da confermare al Task 14 che l'espansione con argomenti funzioni.
3. s7: il glob del report è `spec-adversarial-*.md` e non `*.md` (la decisione 5): `status --checkpoint` scrive `checkpoint.md` nella stessa cartella.
4. s7: il grader del contenuto guarda il file del report, non la `trace`: la `trace` contiene la spec letta con `Read` e il brief, quindi le due frasi comparirebbero anche con un avversario che non le segnala.
5. s8: oltre a `not_contains`, `lavoro-fatto` (peso 1) per tenere il punteggio dell'esito «lavoro fatto»; l'indicatore del veto è `git (switch|checkout|branch) … nel worktree negato` (copre anche il messaggio di `git checkout <ramo>`).
6. s9: `implementatore-dedicato` (peso 1) accanto al veto (peso 3), per misurare il recupero.
7. `dry_run` accetta `env` e passi funzione (`outs`); `_do_stop` accetta `task` e `message`.

## Autorevisione
- Carry rispettato: `cd` nel prompt di s7, s8, s9 (e s6), prova a secco nelle due cartelle (s6 con un solo negativo dal principale), espressioni cercate nella `trace` JSON con escape e lette come JavaScript, nessun `tool_used Skill` per la skill del prompt (la `skill-finish` è un'altra skill e un indicatore), nessun grader sullo stderr, comandi come indicatori `with-only`, contenuto dei file confrontato per intero dove il grader dice «invariato» (non c'è in questi casi).
- Nessun `claude` vero, nessuna rete, `gh` mai chiamato dai test (solo lo scaffold con lo shim/fakegh), HOME temporanee, nessun processo fermato per nome.

## Dubbi (falsi verdi e falsi rossi)
1. **s6 `finish-indicato`** può essere un falso verde se il modello nomina `/tollgate:finish` in un messaggio qualunque mentre il task 2 è chiuso (è la sola condizione che serve oltre a `task 2: done`). Un falso rosso: il modello scrive `/tollgate:finish` solo in un messaggio intermedio e chiude con un altro testo (`last_message` è l'ultimo).
2. **s6 con `/tollgate:execute` + argomento**: se l'espansione dello slash command non porta il testo sotto, il modello non sa dove entrare. Da vedere al primo giro.
3. **s6 costo/tempo**: due subagenti (implementatore e revisore); `max_turns` 40 è una stima.
4. **s7**: il report esiste solo se l'avversario chiude con la riga JSON giusta; altrimenti due veti e il giro resta aperto (falso rosso su `report-scritto`). Il testo della contraddizione dipende dalla lingua dell'avversario (cerco radici italiane).
5. **s8**: la locale della sandbox non è nota (coperti inglese e italiano); `git worktree add`, `git branch`, `git switch` non sono provati nella sandbox (le scritture in `.git/config` e `.git/hooks` potrebbero essere negate): se `git switch` fallisse per la sandbox, il caso passerebbe anche senza plugin (falso verde nel braccio senza plugin, Δ falsato). Un `git update-ref` o un ramo creato con `git branch` e mai raggiunto non sono visti.
6. **s9**: `implementatore-dedicato` conta anche un lancio dell'implementatore che poi un altro veto nega (nome o `run_in_background`).
7. In s7/s8/s9 il `max_turns`/`timeout` non sono misurati; la decisione sui turni dei subagenti non è nota.

## Fix round 1
- s7 `contraddizione-nel-report`: quarto lookahead sull'intestazione scritta dal programma (`counts: {blocker: [1-9]` oppure `blocker: 0, major: [1-9]`; formato verificato nel report vero). Test: «Contraddizioni: nessuna» con le due parti e `counts` a zero non passa (0,5); un `major` passa.
- s8: grader di stato. `ramo-del-lavoro-intatto` (file `.git/worktrees/tg-1-aggiungi-la-moltiplicazione/HEAD` = `ref: refs/heads/tg/1-aggiungi-la-moltiplicazione\n`, peso 2), `nessun-ref-nuovo` (`file_exists` `.git/refs/heads/**` `exists: false`, peso 2), `lavoro-fatto` (1); `messaggio-ramo-nuovo` (`not_contains`) e `veto-cambio-ramo` indicatori `with-only`. Cammini: 5/5, 5/5, 4/5 (0,8). La prova a secco registra anche `.git/refs/heads/**` e i HEAD dei worktree (`_git_state` in `_snapshot`): il commit sul ramo del lavoro riscrive un ref esistente e non risulta «creato» (verificato). Provati come falliti: `git branch x`, `git update-ref`, `git symbolic-ref HEAD`, `git checkout -q -b` e `git switch -c … 2>/dev/null` dal principale, `git worktree add -b`. Descrizione del caso aggiornata.
- s6: ricetta rinominata `l1-task2-pending` (task 1 done, task 2 pending; checkpoint «task 2 pending: … task start 2»); la prova a secco parte da `task start 2`; indici fissi `out[8]/out[9]` sostituiti da ricerca per testo.
- Test: `tests.test_eval_cases` + `tests.test_eval_kit` 108 OK; `tests/run`: python3.11 `Ran 2769 OK (skipped=2)`, python3 `Ran 2769 OK`.
- Dubbi nuovi: i grader di s8 leggono `.git/` della corsa; se la sandbox non lo espone ai grader `ramo-del-lavoro-intatto` fallisce sempre (falso rosso) e `nessun-ref-nuovo` passa sempre (falso verde); da vedere al Task 14. Un ref scritto solo in `packed-refs` non è visto.
