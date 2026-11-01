# Scan pre-flight del piano B2 (regole di base)

Sei un analista in **sola lettura**. Rispondi e scrivi in italiano; identificatori in inglese.

Worktree: `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b2` (ramo `b2-regole-base`, HEAD `fbf7068`, uguale a `main`). Il percorso contiene spazi: virgolette sempre.
Workspace (W): `.superpowers/sdd/2026-10-29-tollgate-b2-regole-di-base/` nel worktree.

L'unico file che scrivi è `W/preflight-scan.md`. Non modifichi altri file, indice, HEAD o rami. Non lanci subagenti. Non esegui `tests/run` né la suite (gira già una baseline in background: non toccarla). Puoi lanciare `python3 -B` su sonde **fuori dal repo** (nello scratchpad `/tmp/claude-1000/scratch_b2/`) e singoli test mirati con `python3 -B -m unittest <modulo.Classe.test>` solo se serve per verificare un'affermazione.

## Da leggere
1. Il piano: `docs/superpowers/plans/2026-10-29-tollgate-b2-regole-di-base.md` (per intero).
2. Le istruzioni d'esecuzione: `docs/superpowers/plans/2026-10-29-tollgate-b2-esecuzione.md` (sezione «Scan pre-flight»).
3. Il progetto di B (l'autorità): `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`.
4. La spec del nucleo rev 27, `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`: sezioni 6.3, 8.1 («Interruttore del blocco»), 8.6, 12.2, 16, 18.4.
5. Il codice reale che il piano tocca o consuma (vedi «Mappa dei file» e le «Interfaces» di ogni task), e i test citati.
6. Come modello di forma: `docs/sdd/2026-10-27-tollgate-b1-informati-prima/preflight-scan.md`.

## Cosa scrivere in `W/preflight-scan.md`
1. Metodo e limiti (cosa hai letto, quali sonde hai fatto, cosa non si verifica da qui).
2. **Una tabella per coppie di task** che condividono un file o un'interfaccia: cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere, esito.
3. **Una tabella per task**: test previsti contro codice previsto (i test citati esistono? a che riga? cosa asseriscono?), file toccati da più task, coerenza interna del task.
4. **Conflitti** numerati (D1, D2, …), con gravità (A = blocca o falsa un test/esito; M = difetto reale ma aggirabile; B = precisazione), dove (piano `P:<riga>`, progetto `B:<riga>`, spec `S:<riga>`, codice `file:riga`), cosa, e **una proposta di ruling** con il costo se sbagliata. Conflitti con il progetto di B, con la spec rev 27 e con il codice reale di `main`.

## Punti da guardare apposta (uno per uno, ognuno con una riga di esito)
- `rules_switch` (Task 1) contro i due chiamanti di `rules_enforced` (`research_gate`, `taskcmd`) e contro `test_unreadable_is_off_for_now`, che il Task 1 sostituisce;
- il tipo nuovo `research_switch_unreadable` contro `events.EVENT_TYPES` (elenco chiuso) e contro la spec 18.4;
- l'ordine dei moduli in `pre_edit` (`writes` 20, `research_gate` 25): il primo `deny` vince, gli `inject` si sommano; e se c'è un caso `pre_bash` / `post_bash` rilevante per l'evento della decisione 5;
- i test che oggi usano la radice vera, nel processo dei test (`tests/hookkit.py` `ROOT`, `taskcmd.db.BIN_PATH`) e in sottoprocesso (`hooks/run` e `bin/tollgate` lanciati da `tests/flowkit.py` e dalle prove a secco di `tests/test_eval_cases.py`), contro l'accensione del Task 5 (decisione 7). Elenca i file di test candidati e, per le prove a secco degli eval, quali casi (s1, s2, s3, s9 o altri) hanno un implementatore L1/L2 che modifica file; verifica che il banco non abbia oggi un'azione `read`;
- i test che oggi vogliono `skills/rules-base/` assente o ogni skill documentata (`tests/test_b1_scripts.py` righe 169 e 555, `tests/test_docs.py` `test_every_skill_documented`) contro il file di prova del Task 2 e la bozza del Task 3;
- il formato del frontmatter `skills: [rules-base]` contro il parser di `tests/test_manifest.py` e contro `claude plugin validate --strict` (non eseguirlo: guarda solo `spikes/hookprobe/agents/probe-agent.md` e gli esiti di P0 E5 nel repo);
- `test_implementer_tools`, `test_implementer_mentions_untrusted_pages`, `test_implementer_mentions_research_submit` contro le modifiche di `implementer.md` del Task 6;
- `B1_FLOW_RULES` e `B1_FLOW_SRC` (Task 7) contro i test di `tests/test_b1_scripts.py` che oggi controllano la `rules-base` di prova;
- in più: se qualche altro punto del codice legge `skills/` o elenca le skill (manifest, `docs`, `setup`, statistiche, brief «Skill da usare», `skills_required`) e potrebbe cambiare comportamento quando `skills/rules-base/` comparirà.

## Regole di cautela (vincolanti)
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
- Lavora solo nel worktree `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b2` (ramo `b2-regole-base`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Tempi della suite**
- Con circa 3200 test una corsa di `tests/run` dura da 25 a 55 minuti quando la macchina è carica. Lanciala in background e aspetta l'esito sul file d'uscita, senza restare fermo. Mentre lavori lancia solo i file di test del task; la suite completa al più una volta per giro, prima del commit.

Rispondi alla fine SOLO con: percorso del file, numero di conflitti per gravità (A/M/B), e una riga per ogni conflitto A.
