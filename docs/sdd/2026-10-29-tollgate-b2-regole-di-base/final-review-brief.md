# Revisione finale del ramo B2 (regole di base)

Sei il revisore finale dell'intero ramo `b2-regole-base` di tollgate (plugin di Claude Code; CLI Python solo libreria standard). Sei in **sola lettura**. Rispondi in italiano.

Worktree: `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b2` (percorso con spazi: virgolette sempre). Workspace W: `.superpowers/sdd/2026-10-29-tollgate-b2-regole-di-base/` nel worktree. Base del ramo: `fbf7068` (main); testa `c71ab80`.

## Autorità
1. Il progetto di B: `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (le scelte «utente» non si discutono).
2. La spec del nucleo: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (rev 28 scritta da questo ramo).
3. Il piano: `docs/superpowers/plans/2026-10-29-tollgate-b2-regole-di-base.md`.

## Da leggere
- `W/decisions.md` (13 decisioni del piano), `W/review-focus.md` (Review Focus), `W/coverage.md` (tabella «Copertura»), `W/global-constraints.md`, `W/cautele.md`.
- `W/final-rulings.md`: tutte le `Ruling:` prese dal controller durante l'esecuzione, con il costo se sbagliate.
- `W/final-deferred.md`: i minori rinviati da sottoporre a **triage** (per ciascuno: da correggere prima del merge, oppure rinviabile con il motivo, oppure rinvio a B3 e oltre), compreso il rinvio 37 di B1.
- I rapporti dei Task 4 e 7: `W/task-4-report.md`, `W/task-4-fonti.md`, `W/task-5-fonti.md`, `W/task-7-report.md`, e il rapporto pubblico della prova `docs/verifiche/2026-10-29-b2-prova-flusso.md`.
- Il pacchetto del ramo **senza le evidenze**: `W/final-review-package.diff` (commit, stat, diff). Le evidenze della prova sono in `docs/verifiche/evidenze/b2/flusso/`: aprile solo per controlli mirati.
- Il ledger `W/progress.md` per la storia (approvazione dell'utente del 2026-11-01, giri di correzione).

## Cosa cercare in particolare
1. **Guasti che nascono dall'incontro di due stati**: l'interruttore acceso e un lavoro in corso già avvisato; l'interruttore illeggibile e un task senza nota; un task senza modifiche con una nota non valida; le R-BASE `[blocca]` con l'interruttore spento o illeggibile; un difetto della nota con la nota non utilizzabile.
2. Che **nessun test dipenda in silenzio** dallo stato dell'interruttore nel repo (ora acceso: `approved: 2026-11-01`), né nel processo dei test né nei sottoprocessi (`hooks/run`, `bin/tollgate`, prove a secco degli eval).
3. Che **le regole, la pagina e il rapporto delle fonti coincidano** (`skills/rules-base/SKILL.md`, `docs/profili/base.md`, `docs/profili/verifiche/base-fonti.md`): 11 regole, numeri senza buchi, `[blocca]` uguale a «Blocca?», fonti uguali e con esito `ok`.
4. Che **il testo delle fonti non entri mai come istruzione in un brief** (testo non fidato solo dentro `brief.fence` con `brief.DATA_NOTE`), e che `rules-base` non finisca mai in «Skill da usare» né in `skills_required`.
5. Coerenza tra agenti (`agents/*.md`), brief del revisore (`bin/tollgate_analysis/brief.py`) e verdetto (`verdicts.is_blocking` con `lookups.base_rules`): un difetto della nota dà un solo rilievo, con la gravità giusta.
6. Strati, nessuna operazione nuova in `apply._OPS`, `ResourceWarning` (file aperti e non chiusi, anche negli script), anonimizzazione dei file nuovi (il repo è pubblico: niente nome utente, host, id di sessione, progetti privati dell'utente).
7. Che la spec rev 28, il piano principale e il catalogo dicano il vero rispetto al codice.

## Uscita
Scrivi la revisione completa in `W/final-review.md`:
- verdetto: «pronto per il merge» oppure «non pronto»;
- rilievi **Critical / Important / Minor**, ciascuno con file:riga, cosa, perché, come correggere, e un test che fallirebbe;
- **triage** di ogni voce di `W/final-deferred.md`;
- un giudizio sulle `Ruling:` di `W/final-rulings.md` (ce n'è qualcuna sbagliata?).
Poi rispondi in breve (meno di 25 righe) con il verdetto e i Critical/Important.

## Regole di cautela (vincolanti)
- Sola lettura: non modificare file, indice, HEAD o rami. Non lanciare subagenti.
- Nessun `claude` vero (salvo `claude plugin validate`, che non lancia il modello), nessuna rete, nessun `gh` vero. `spikes/run-b1-flow.sh` ed `evals/run.sh` solo con `bash -n` o `controlla`.
- Mai `pkill`, `killall` o `kill` per pattern; mai `git stash`; mai toccare `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`; non leggere `.env`, `auth.json` o segreti.
- Non lanciare `tests/run` (dura un'ora): al più test mirati con `python3 -B -m unittest …`.
