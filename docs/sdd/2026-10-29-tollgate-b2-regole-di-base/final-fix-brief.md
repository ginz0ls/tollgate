# Giro di correzione della revisione finale di B2

Sei l'implementatore del giro di correzione della revisione finale del ramo `b2-regole-base` di tollgate. Rispondi in italiano; identificatori in inglese.

Worktree (lavora SOLO qui): `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b2` (percorso con spazi: virgolette sempre). Workspace W: `.superpowers/sdd/2026-10-29-tollgate-b2-regole-di-base/` nel worktree.

## Da leggere prima
- `W/final-review.md`: la revisione finale (opus), con i rilievi completi: file:riga, cosa, perché, come correggere, test che fallirebbe. È la fonte dei requisiti di questo giro.
- Le righe del ledger `W/progress.md` dopo «Revisione finale (opus…)»: le decisioni del controller su questo giro (le `Ruling:`).
- `W/implementer-rules.md` (TDD, report, commit, suite in background), `W/global-constraints.md`, `W/decisions.md`, `W/cautele.md`.

## Cosa correggere (ogni correzione: prima un test che fallisce, poi il codice; per i documenti basta la correzione)

### Important
1. **I-1.** In `bin/tollgate_checks/task_verdict.py` e in `bin/tollgate_hooks/apply.py` (`_final_rules`) le `R-BASE-…` restano sempre regole note, ma quelle `[blocca]` diventano bloccanti solo se l'interruttore è acceso **e** il lavoro ha il passo attivo: `research.active(work["research"], ctx.component("research_note"))`. Una funzione sola per la condizione (per esempio un parametro `active` in `lookups.base_rules`), niente condizione duplicata. Test: in `tests/test_check_task_verdict.py` la classe gemella con `research=False` (un `major` su `R-BASE-01` → `approved`) accanto a quella con `research=True` (→ `changes`; `BaseRulesTest` passa a `research=True`), un caso con `[components] research_note = false`, e lo stesso per il verdetto finale in `tests/test_check_final_review.py`. Allinea spec 8.6 rev 28 e piano principale sezione 3 («solo nei lavori con il passo»).
2. **I-2** (strada (a), decisa dal controller: non si toccano le regole approvate dall'utente).
   - Il brief del revisore del task (`bin/tollgate_analysis/brief.py`, `ReviewBrief` e `review_brief`; dati da `bin/tollgate_flow/taskcmd.py`, dove oggi `_concerns` legge `subagents.report`) contiene il **report dell'ultimo implementatore** del task: testo non fidato, sempre in un recinto con `brief.fence`/`_block` preceduto da `brief.DATA_NOTE`, mai come istruzione. Non solo con `DONE_WITH_CONCERNS`: sempre, quando c'è un report. Guarda la forma reale di `subagents.report` (campi del report, 18.5) e riporta ciò che serve a giudicare le regole sul report (per esempio i campi del report in forma leggibile o il testo intero, al più con un tetto di lunghezza se il codice ne ha già uno simile).
   - `agents/task-reviewer.md`: dice che il report dell'implementatore è nel brief, in un recinto, ed è il dato su cui si giudicano le regole sul report (R-BASE-05, 07, 10, 11 e le parti sul report delle altre).
   - `agents/final-reviewer.md` e `agents/finding-verifier.md`: le `R-BASE-…` si giudicano solo su ciò che il revisore vede (il diff); le regole sulla nota di ricerca e sul report sono del revisore del task, e il revisore finale non apre rilievi su di esse. Mantieni la frase condizionata di D6.
   - Test: in `tests/test_brief.py` `review_brief` con un report che contiene tre backtick lo recinta dopo `DATA_NOTE`; in `tests/test_taskcmd.py` (`ReviewDoneTest`, radice temporanea esplicita come gli altri test della classe) con un report registrato, `review_prepare` produce un brief che contiene il report nel recinto, anche con stato `DONE`; in `tests/test_manifest.py` le frasi nuove degli agenti. I test esistenti restano verdi.

### Minori da correggere prima del merge (dal triage e dai Minor della revisione finale)
3. `tests/test_check_research_gate.py`, `test_unreadable_switch_warns_and_logs_once`: l'avviso «non si legge» precede l'avviso normale, e la seconda modifica non lo ripete.
4. `tests/test_rules_base.py`: la data della riga «Approvata dall'utente il …» di `docs/profili/base.md` è uguale ad `approved` della skill; e `research.base_rules(testo della skill vera)` coincide con gli id e i `[blocca]` di `rules(...)` (Minor 6).
5. `docs/profili/verifiche/base-fonti.md`: riga 3 cita anche il commit della seconda verifica (la R-BASE-10 attuale è stata verificata dopo b17cbf0, il 2026-11-01); la riga `no` di `systematic-debugging` per R-BASE-10 esce dalla tabella principale e va sotto, come fonte scartata (Minor 7), così ogni riga della tabella è una fonte citata dalla skill con esito `ok`. Se il test `test_sources_report_covers_every_rule` va adattato, non indebolirlo.
6. Spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`: Minor 1 (6.3: il paragrafo su `rules-base` dopo la frase su `SubagentStop` e «Una skill non installata…»), Minor 2 (16: `research_switch_unreadable` nell'elenco «Tipi:»; aggiungi in `tests/test_docs.py` un test che confronti `events.EVENT_TYPES` con l'elenco «Tipi:» della spec, se l'elenco ha una forma che si legge in modo affidabile), Minor 3 (`rules_enforced` non è più il gate unico: il gate usa `rules_switch`, `taskcmd.review_prepare` usa `rules_enforced`; anche la docstring in `bin/tollgate_core/lookups.py` e il piano principale sezione 3), e le frasi su I-1 e I-2.
7. Piano principale `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: Minor 4 (sezione 3: «`no`, `off` e `n`, e il confronto dopo gli apici (anche per `false`)»); sezione 10, rinvio 31: «i primi due» al posto di «gli ultimi tre»; sezione 3: la grammatica di «se `rules-<area>` si precarichi»; «la bozza n. 11» al posto di «la n. 11» (anche nella spec rev 28); nei rinvii a B3: il rinvio 37 di B1 (una riga in `implementer.md` o nel brief: «i file che elenchi nella nota aprili con Read») e i minori marcati «rinviabile a B3» nel triage di `W/final-review.md` che non ci sono già.
8. `bin/tollgate_checks/research_gate.py`: la docstring del modulo nomina l'interruttore illeggibile e l'evento `research_switch_unreadable` (Minor 8).
9. `agents/implementer.md`, punto 1: aggiungi che, se le regole di base non sono nel contesto, si leggono comunque i file che si modificano prima di scriverli (Minor 9). Verifica che `test_implementer_*` restino verdi.

Non toccare `approved`, il testo delle regole di `skills/rules-base/SKILL.md` né la pagina `docs/profili/base.md` (salvo nulla: la pagina è approvata dall'utente così). Se una correzione ti sembra richiedere di cambiare una regola approvata, fermati: BLOCKED con il motivo.

## Verifica e consegna
- Test mirati dei file toccati, poi `PYTHONWARNINGS=error::ResourceWarning tests/run` in background una volta (python3.11 e python3), verde e senza «unclosed database». Quando finisce, leggi l'esito e chiudi senza aspettare messaggi; se la notifica non arriva, controlla tu il file d'uscita.
- `claude plugin validate --strict .` uscita 0.
- Uno o più commit (mai amend, mai `--no-verify`) con la riga `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; nessun `__pycache__`, nessun file del workspace.
- Report completo in `W/final-fix-report.md`: per ogni rilievo cosa hai cambiato, RED (comando e fallimento atteso) e GREEN, file, scostamenti, dubbi. Poi rispondi SOLO con: Status, commit, una riga di test, dubbi, percorso del report.

## Regole di cautela (vincolanti, dall'utente)
- Mai toccare `~/.local/state/tollgate`; i test usano solo `tests.helpers.TempState` e una `HOME` temporanea. Mai leggere o scrivere i veri `~/.claude/settings.json` e `~/.claude/plugins/`. Mai installare, abilitare o disinstallare plugin (`claude plugin validate` è ammesso).
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero oltre a `validate`, nessuna chiamata di rete, nessun repo su GitHub, nessun push. Mai il `gh` vero. `spikes/run-b1-flow.sh` ed `evals/run.sh`: solo `bash -n` e il modo `controlla` (e i test).
- Mai `pkill`, `killall` o `kill` per nome o pattern: solo processi propri, per PID. Mai force push, `reset --hard`, `--no-verify`, né amend. Mai `npm run dev`. Mai `git stash`. Non leggere né riportare `.env`, `auth.json`, token o segreti.
- Lavora solo nel worktree, mai nel checkout principale né su `main`. Non lanci subagenti.
- Una corsa di `tests/run` dura da 25 a 90 minuti: in background (strumento Bash con run_in_background, mai `&`/`nohup`), al più una volta prima del commit finale; mentre lavori lancia solo i file di test toccati.
