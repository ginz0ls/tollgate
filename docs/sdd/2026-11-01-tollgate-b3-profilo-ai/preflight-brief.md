# Scan pre-flight del piano B3 (infrastruttura dei profili e profilo `ai`)

Sei un analista in **sola lettura**. Rispondi e scrivi in italiano; identificatori in inglese.

Worktree: `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b3` (ramo `b3-profilo-ai`, HEAD `b35c538`, uguale a `main`). Il percorso contiene spazi: virgolette sempre.
Workspace (W): `.superpowers/sdd/2026-11-01-tollgate-b3-profilo-ai/` nel worktree.

L'unico file che scrivi è `W/preflight-scan.md`. Non modifichi altri file, indice, HEAD o rami. Non lanci subagenti. Non esegui `tests/run` né la suite (gira già una baseline in background: non toccarla). Puoi lanciare `python3 -B` su sonde **fuori dal repo** (nella cartella `/home/USER/.claude/jobs/e28b8553/tmp/preflight/`) e singoli test mirati con `python3 -B -m unittest <modulo.Classe.test>` solo se serve per verificare un'affermazione.

## Da leggere
1. Il piano: `docs/superpowers/plans/2026-11-01-tollgate-b3-profilo-ai.md` (per intero).
2. Le istruzioni d'esecuzione: `docs/superpowers/plans/2026-11-01-tollgate-b3-esecuzione.md` (sezione «Scan pre-flight»).
3. Il progetto di B (l'autorità), con la sezione 9: `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`.
4. La spec del nucleo rev 28, `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`: sezioni 6.3, 7.3, 11.2, 11.4, 18.4.
5. Il codice reale che il piano tocca o consuma («Mappa dei file», «Interfaces» di ogni task) e i test citati.
6. Fatti raccolti per scrivere il piano (da verificare, non autorità): `W/fatti/fatti-profili.md`.
7. Come modello di forma: `docs/sdd/2026-10-29-tollgate-b2-regole-di-base/preflight-scan.md`.

## Cosa scrivere in `W/preflight-scan.md`
1. Metodo e limiti (cosa hai letto, quali sonde hai fatto, cosa non si verifica da qui).
2. **Una tabella per coppie di task** che condividono un file o un'interfaccia: cosa produce uno, cosa consuma l'altro, nomi e firme che devono coincidere, esito.
3. **Una tabella per task** (1-11): test previsti contro codice previsto (i test citati esistono? a che riga? cosa asseriscono?), file toccati da più task, coerenza interna del task.
4. **Conflitti** numerati (D1, D2, …), con gravità (A = blocca o falsa un test/esito; M = difetto reale ma aggirabile; B = precisazione), dove (piano `P:<riga>`, progetto `B:<riga>`, spec `S:<riga>`, codice `file:riga`), cosa, e **una proposta di ruling** con il costo se sbagliata. Conflitti con il progetto di B, con la spec rev 28 e con il codice reale di `main`.

## Punti da guardare apposta (uno per uno, ognuno con una riga di esito)
- le frasi dei rinvii 184-187 (Task 1) contro i test esistenti di `tests/test_manifest.py` che citano frasi alla lettera di `agents/implementer.md`, e contro il test di deriva del Task 8 (`test_area_agents_derive_from_generic`: ogni paragrafo del generico nella copia);
- `area_rules` (Task 2) contro i chiamanti di `base_rules` (`lookups.base_rules`, `task_verdict`, `apply._final_rules`) e contro `tests/test_rules_base.py`;
- `fragments.py` in `tollgate_core` e `tomlout.py` in `tollgate_analysis` contro `tests/test_layers.py` e `tests/test_analysis_isolation.py`; `init.py` (`tollgate_flow`) che li importa;
- `init.propose` e i test esistenti di `tests/test_init.py` (`test_files_tree`, `UpdateTest`, `ModeRewriteTest`) contro i blocchi aggiunti in coda: verifica che nessun test esistente spinga file che i frammenti veri accenderebbero fuori dalle cartelle escluse (decisione 5), compreso l'albero installato in `.github/tollgate/`; è la garanzia di `test_real_trees_light_no_profile` (Task 3);
- `READONLY_TYPES` (`hooks/run`) e `config.DEFAULTS["review"]["readonly_agents"]` contro `test_readonly_list_matches_config_and_agents` e `test_other_agent_types_reach_python` (`tests/test_wrapper.py`), e contro `config.is_readonly`;
- il frontmatter `skills: [rules-base, rules-ai]` contro il parser `frontmatter()` di `tests/test_manifest.py` (non eseguire `claude plugin validate`: guarda solo come `skills: [rules-base]` è letto oggi);
- `B1_FLOW_CASE` (Task 9) contro i test di B1 e B2 in `tests/test_b1_scripts.py` e contro `spikes/run-b1-flow.sh` (modi, variabili, `controlla`), e la chiave della protezione di `tests/fakegh.py:26`;
- in più: `git.ls_files_at`/`_proc`/`_check_ref` in `bin/tollgate_core/git.py` per `tree_sizes_at` e `grep_files_at` (Task 3-4); `globs.escape`, `globs.match`, `globs.match_any`, `globs.literal_segments` e `profiles.vertical_for` per la decisione 5; `init._plain` e `prbody.neutralize` (esistono? firme?); `config.load_config_text` (avvisi su `[profiles.x]`: forma degli avvisi restituiti) per `test_proposal_validates` e `test_fragment_profile_validates`; `tests/test_docs.py` `test_every_skill_documented`; `verdicts.is_blocking` con regole `R-AI-…` quando il profilo `ai` è dichiarato nel `tollgate.toml` del test (Task 8); `lookups.base_rules(root, active)` e se `task_verdict`/`apply._final_rules` usano già le `rules` dei profili attivi.

## Regole di cautela (vincolanti)
## Regole di cautela (obbligatorie, vincolanti per l'utente)

**Stato e configurazione dell'utente**
- Mai toccare `~/.local/state/tollgate`. I test usano solo `tests.helpers.TempState` (`TOLLGATE_STATE` con la sentinella `.tollgate-test`) e una `HOME` temporanea (`tests/flowkit.py`, `tests/gatekit.py`, `evals/_kit/`).
- Mai leggere o scrivere i veri `~/.claude/settings.json`, `~/.claude/plugins/` e `~/.claude/projects/`, né nei test né nel lavoro: le fonti delle regole sono le copie nel workspace (`fonti/ai/`).
- Mai installare, abilitare o disinstallare plugin: niente `claude plugin install` né `claude plugin marketplace add`. `claude plugin validate` (anche `--strict`) è ammesso: non lancia il modello.

**Esperimenti e rete**
- Nessun `claude -p`, nessun `claude plugin eval`, nessun altro `claude` vero (un `claude` finto nel `PATH` dei test è ammesso), nessuna chiamata di rete (niente `curl`, `wget`, `WebFetch`, `WebSearch`), nessun repo su GitHub, nessun push verso la rete. Il solo push ammesso è verso i repo nudi locali dei banchi. `gh` nei test è `tests/fakegh.py`. Mai il `gh` vero (`gh auth`, `gh api`, `gh pr create` o altro).
- `spikes/run-b1-flow.sh`: solo `bash -n`, il modo `controlla` e i test di `tests/test_b1_scripts.py`. Mai un altro modo (`prepara`, `passo1`, `passo2`, `registra` fuori da un test), nemmeno per prova, nemmeno in un giro di correzione: l'esecuzione è del controller.
- `evals/run.sh`: solo `bash -n` e il modo `controlla` (gli eval sono di B8).

**Processi, git e segreti**
- **Mai `pkill`, `killall` o `kill` per nome o pattern**: si fermano solo processi propri, per PID, avviati in questa stessa esecuzione.
- Mai force push, `reset --hard`, `--no-verify`, né amend su commit pubblicati. Mai `npm run dev`.
- Mai `git stash`: lo stack degli stash è condiviso con il checkout principale e con altre sessioni.
- Mai cancellare `.git/index.lock` a mano: la cartella è sincronizzata da MEGA e il lucchetto a volte resta per qualche secondo. Se un commit lo trova, aspetta qualche secondo e ritenta.
- Non leggere né riportare `.env`, `auth.json`, token o segreti. Nessuna chiave API nei test, negli script o nelle evidenze.
- La suite in background solo con lo strumento Bash e `run_in_background`, **mai con `&`, `nohup` o `setsid`** dentro il comando.

**Commit e lingua**
- Un commit dopo ogni task, con la riga `Co-Authored-By` del modello. Prima di ogni commit `tests/run` deve passare con `python3.11` e con `python3`, con `PYTHONWARNINGS=error::ResourceWarning` (come la CI).
- Nessun `__pycache__` nel commit (usa `python3 -B`): controlla `git status` prima di `git add`.
- **Mai scrivere `approved` in `skills/rules-ai/SKILL.md` fuori dal Task 7**: accenderebbe il profilo senza l'utente.
- Il repo `ginz0ls/tollgate` è **pubblico**: nei file nuovi niente nomi di progetti privati dell'utente, niente nome utente né nome dell'host, niente percorsi `/home/<utente>`. Le copie delle fonti (`fonti/ai/` nel workspace) non entrano mai in git: dalle pagine dei fornitori si prendono fatti, con parole nostre, e una citazione sta al più in una riga, solo nel rapporto delle fonti.
- Lavora solo nel worktree `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b3` (ramo `b3-profilo-ai`), mai nel checkout principale né su `main`. Il percorso contiene spazi: virgolette sempre.
- Risposte e messaggi in italiano; identificatori in inglese.

**Tempi della suite**
- Una corsa di `tests/run` (due interpreti, circa 3240 test) dura da 25 a 90 minuti. Lanciala in background con l'uscita su un file e **controlla tu stesso** quel file (notifica, o un ciclo `until` limitato sull'esito): non restare fermo ad aspettare un messaggio. Mentre lavori lancia solo i file di test del task; la suite completa al più una volta per giro, prima del commit.
- `tests.test_cli.CliTest.test_db_restore_interactive_eof_and_ctrl_c` (Ctrl-C su un pty) è instabile sotto carico: se è rosso, ripetilo da solo e riporta entrambi gli esiti.

Rispondi alla fine SOLO con: percorso del file, numero di conflitti per gravità (A/M/B), e una riga per ogni conflitto A.
