# Pre-flight scan del piano B3 (infrastruttura dei profili e profilo `ai`)

Piano: `docs/superpowers/plans/2026-11-01-tollgate-b3-profilo-ai.md` (350 righe, 11 task, 17 decisioni; sotto `P:<riga>`). Autorità: progetto di B `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (`B:<riga>`, sezione 9 compresa), poi la spec del nucleo rev 28 `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (`S:<riga>`), poi il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md` (`C:<riga>`). Modello di forma: `docs/sdd/2026-10-29-tollgate-b2-regole-di-base/preflight-scan.md`. Il codice è quello di `main` (HEAD `b35c538`, worktree `b3`).

**Esito in una riga: 0 conflitti A, 3 M, 17 B.** Il piano regge: nessun test esistente si rompe per come il piano è scritto, e nessuna firma di un task contraddice ciò che un altro task consuma. I tre M sono difetti reali ma aggirabili (D1, D2, D3).

## 1. Metodo e limiti

- Letti per intero: il piano; le istruzioni d'esecuzione (sezione «Scan pre-flight»); il progetto di B (186 righe); `fatti/fatti-profili.md` (da verificare, non autorità). Della spec rev 28: 6.3 (S:432-520, soprattutto S:473-479 e S:509), 7.1 (S:603), 7.3 (S:632-634), 11.2 (S:1046-1059), 11.4 (S:1069-1217, profili e `readonly_agents` S:1143), 18.4 (S:1796-1803). Del catalogo: sezione 1 (principi e «Skill comuni»), 2 (riga `ai`), 2.1, 2.2, 2.3. Del piano principale di B: sezioni 3 e 9 (le righe «A B3-B7»).
- Letto il codice che il piano tocca o consuma: `bin/tollgate_analysis/{research,brief,globs,profiles,verdicts,prbody}.py`; `bin/tollgate_core/{config,git,lookups,cli,paths}.py`; `bin/tollgate_flow/{init,taskcmd}.py`; `bin/tollgate_gate/install.py`; `bin/tollgate_checks/{task_verdict,_common,subagent_start}.py` (e il grep di `agent_type` negli altri); `bin/tollgate_hooks/apply.py`; `hooks/run`; `agents/{implementer,task-reviewer,final-reviewer,finding-verifier}.md`; `skills/{rules-base,init}/SKILL.md`; `templates/tollgate.toml`; `spikes/run-b1-flow.sh` (tutto) e `spikes/b1/flowreg.py`; `spikes/b1/flow/`.
- Test letti: `tests/test_manifest.py` (tutto), `test_wrapper.py` (righe 220-290), `test_layers.py`, `test_analysis_isolation.py`, `test_init.py` (1-240, 379-560), `test_brief.py` (120-260), `test_taskcmd.py` (596-670), `test_check_task_verdict.py` (1-60, 168-290), `test_rules_base.py` (1-90), `test_docs.py` (1-100), `test_skill_contract.py` (1-30, 85-235), `test_b1_scripts.py` (1-115, 450-700, 835-875), `flowkit.py` (1-175), `hookkit.py` (`DEFAULT_FILES`), `test_protection.py:1-25`, `fakegh.py:1-60`.
- **Sonde (tutte fuori dal repo, in `/home/USER/.claude/jobs/e28b8553/tmp/preflight/`, `python3 -B`, nessun file nel repo toccato):**
  1. repo git di prova con file `.ts`, `.py`, un binario con NUL, un nome con accento, `app/[id]/x/p.ts`: verificato l'output di `git ls-tree -r -l -z` (dimensione allineata a destra con spazi, tabulazione, percorso non citato) e di `git grep -z -I -l -F -e … <ref> -- ':(glob)**/*.py'` (percorsi `<ref>:<percorso>` separati da NUL, `-I` esclude il binario, nessun risultato = uscita 1, il pathspec `**/*.py` prende anche i file alla radice).
  2. `globs.escape`/`match`/`match_any`/`literal_segments`/`profiles.vertical_for` su `ai`, `src/ai`, `app/[id]/x`, `!weird/ai` e sui quattro pattern del frammento (vedi D4 e il punto 9 del §4).
  3. Tutti i 147 percorsi di `install.files(ROOT)` (compreso `.github/tollgate/bin/**`), di `DEFAULT_FILES`, `GATE_FILES`, `JUNIT_FILES` del banco e i file spinti da `test_init.py` (`package.json`, `ci.yml`) contro `["**/llm/**","**/prompts/**","**/agents/**","**/ai/**"]`: **zero corrispondenze**, anche senza le cartelle escluse. Nel repo del plugin stesso corrispondono solo `agents/*.md`, `spikes/**/agents/*.md` (atteso: vedi punto 4).
  4. `unittest discover -s tests -t .` su un progetto con `tests/test_smoke.py` senza `tests/__init__.py`, con `python3.11` e con `python3` (3.13): `ImportError: Start directory is not importable` in entrambi (D1).
  5. `tests.test_manifest.frontmatter` su un agente con `skills: [rules-base, rules-ai]`: restituisce la stringa `[rules-base, rules-ai]`.
- **Non verificabile da qui:** `claude plugin validate --strict` con la lista di due skill (decisione 9; non lanciato, come da brief) e il precaricamento reale di due skill; la struttura reale delle cartelle delle trascrizioni in `~/.claude/projects/` (la regola del nome si ricava dalla memoria `sessioni-nei-worktree`: ogni carattere non alfanumerico del percorso diventa `-`, quindi `/.claude/` dà `--claude-`); il comportamento di Claude Code con `subagent_type` sconosciuto; i contenuti delle pagine dei fornitori (Task 5 Step 0 non è ancora eseguito: `fonti/ai/` non esiste). Non ho eseguito `tests/run`, `spikes/run-b1-flow.sh`, `evals/run.sh`, `claude`, `gh`, né nulla in rete.

## 2. Tabella per coppie di task

| A | B | Cosa produce A / cosa consuma B; nomi e firme che devono coincidere | Esito |
|---|---|---|---|
| T1 | T8 | T1 corregge `implementer.md`, `task-reviewer.md`, `brief.py`, `taskcmd.py`; T8 copia i due agenti con `test_area_agents_derive_from_generic` (ogni paragrafo del generico nella copia) | Coerente: l'ordine T1 < T8 è lineare e T8 copia il testo già corretto. Il test di deriva non vincola le frasi nuove di T1 (le copia). Vedi punto 1 del §4 |
| T1 | T9 | T1 cambia la resa del report nel brief (`taskcmd._implementer_report`); T9 raccoglie `agent_type`/`reviewer_type` | Indipendenti |
| T2 | T3 | `fragments.load/approved/rules`, `tomlout.table`, `research.area_rules`; T3 le chiama in `profile_blocks` | Coerente. `fragments` in `tollgate_core` importa `tollgate_analysis.research` e `config`: ammesso da `test_layers` (il nucleo non importa gli strati sopra; l'analisi è importabile da tutti). `init` (flow) importa `fragments` e `tomlout`: ammesso |
| T2 | T5 | `fragments.load(ROOT)` sul frammento vero (`test_real_fragments_load`); `research.area_rules` per `test_rules_ai` | Coerente. Il frammento vero ha `agent = "tollgate:implementer-ai"` quando l'agente non c'è ancora (T8): `fragments.load` non valida la forma del nome (la valida `config`, che avvisa); lo copre `test_fragment_profile_validates` solo se il test aggiunge `schema_version` e `[gate] mode` (D14) |
| T3 | T4 | T3: `git.tree_sizes_at`, `init.EXCLUDED_PREFIXES`, `profile_blocks(..., detected=)`; T4: `git.grep_files_at`, `init.detect_files(repo, ref, fragments, sizes)` | Coerente per un solo frammento. **D3**: «un solo `git grep`» e «risultato per area» non stanno insieme con 2 o più frammenti (B4-B7) |
| T3 | T9 | `init.propose` col gh finto e `tollgate.toml` esistente; T9 lo lancia dalla copia del plugin in `prepara` | Coerente: `PLUGIN_ROOT` è calcolato dalla posizione del file (`init.py:27`), quindi la copia legge i frammenti e le skill della copia; `install.files` ha bisogno di `gate/workflows/`, che la copia tracciata contiene. **D1** per il progetto di prova |
| T3 | T5/T7 | `test_real_trees_light_no_profile` (T3) deve restare vero dopo che T5 aggiunge il frammento vero e T7 lo approva | Coerente: misurato (§1, sonda 3) che né il banco `FlowLab` né l'albero installato né i file spinti da `test_init.py` accendono nessun pattern, anche senza esclusioni |
| T4 | T6 | marcatori di `[detect] content` (T5) verificati in T6; `test_real_markers_not_in_tollgate_bin` | Coerente. Precondizione: `bin/tollgate_analysis/bash.py:911` contiene `@anthropic-ai/claude-code` (D11); nessun altro marcatore plausibile è in `bin/` o `hooks/` |
| T5 | T6 | `tests/test_rules_ai.rules(text) -> list[tuple[id, blocca, testo, fonte, oggetto]]` | Coerente: la tupla ha 5 campi (quella di B2 ne ha 4), la regex `RULE` di B2 si riusa invariata |
| T6 | T7 | pagina e rapporto → `approved` + «Approvata dall'utente il …» | Coerente (stesso schema di B2) |
| T7 | T8 | `approved` in `rules-ai` prima che gli agenti la precarichino | Coerente per ordine; T8 non legge `approved` |
| T7 | T9 | `prepara` con `B1_FLOW_RULES=vere` esige `rules-ai` approvata nella sorgente | Coerente: `test_flow_case_ai_prepara_refuses_without_profile` copre il caso contrario; i test usano una sorgente finta (`src_repo(case="ai")`), non il file vero |
| T8 | T9 | `agents/implementer-ai.md`/`reviewer-ai.md` tracciati nella sorgente, nomi uguali a `agent`/`reviewer` del frammento | Coerente: `git ls-files` della copia li prende; `init` toglie `agent`/`reviewer` se il file manca (decisione 12), quindi T9 non può partire con agenti assenti senza accorgersene |
| T9 | T10 | variabile `B1_FLOW_CASE`, uscite in `docs/verifiche/evidenze/b3/flusso`, `registra` che legge le trascrizioni | Coerente per nomi. Regola del nome delle cartelle di `~/.claude/projects` e `tests/__init__.py`: D1, D15 |
| T2/T3/T4/T5/T6/T7 | `tests/test_fragments.py` | T2 crea; T5 aggiunge `test_real_fragments_load`; T7 aggiunge `test_real_ai_fragment_approved` | Nessuna sovrapposizione di righe; ordine lineare |
| T3/T5/T8 | `docs/uso/comandi.md` | T3: sezione `/tollgate:init`; T5: `### /tollgate:rules-ai`; T8: `/tollgate:execute` | Sezioni diverse; `test_every_skill_documented` vuole `rules-ai` senza «solo l'utente» nel corpo (la skill non è `disable-model-invocation`) |
| T3/T4 | `init.py`, `git.py`, `test_init.py`, `test_git.py` | T3 `tree_sizes_at`/`profile_blocks`/`propose`; T4 `grep_files_at`/`detect_files`/chiamata in `propose` | Lineare: T4 parte dall'esito di T3 |
| T8 | `agents/final-reviewer.md`, `agents/finding-verifier.md` | modificati da T8 (una frase) ma assenti dalla «Mappa dei file» (P:71) | **D9** (B) |
| T11 | spec, piano principale, progetto, catalogo | T11 scrive la rev 29 | Mancano due luoghi della spec che elencano gli agenti di sola lettura (D5) |

## 3. Tabella per task

| Task | Test previsti contro codice previsto | File toccati da più task / coerenza interna |
|---|---|---|
| 1 | `test_manifest.py`: `test_implementer_tools` (104), `test_implementer_mentions_untrusted_pages` (148), `…_research_submit` (154), `test_implementer_note_model_matches_submit_command` (175), `…_phrase_has_an_antecedent` (180) citano frasi di `implementer.md` alla lettera: nessuna delle tre righe nuove ci cade (la riga dei file letti va in «Informati prima di scrivere», dove `test_implementer_points_to_rules_base` (123) vieta solo «file delle dipendenze»). `test_taskcmd.py:653` esiste ed è l'unico test che il rinvio 187 rovescia; `test_concerns_reach_review_brief` (618, `DONE_WITH_CONCERNS`) e `test_report_reaches_review_brief_even_when_done` (628, `concerns: ""`) restano veri se `concerns` si esclude solo con `DONE_WITH_CONCERNS` e i valori vuoti non producono righe (D12). `test_brief.py`: `ReviewReportTest.test_implementer_report_fenced_after_data_note` (151) asserisce `DATA_NOTE` < recinto: la frase nuova va dopo `DATA_NOTE` o prima, non nel recinto | `agents/implementer.md` (T1, poi copiato da T8), `agents/task-reviewer.md:53` (T1, copiato da T8), `brief.py`, `taskcmd.py:278-281` (verificato: il `concerns` escluso è alla 279). Coerente. La frase del rinvio 185 è legata a `research=False`, la spec dice anche «interruttore spento» (D13) |
| 2 | `test_research.py` esiste; `base_rules` è usata solo da `lookups.base_rules` (`lookups.py:192`) e da `tests/test_rules_base.py:59`: restano valide con `base_rules = area_rules(…, "BASE")`. `test_layers`/`test_analysis_isolation` ammettono i due moduli (§2). `config.load_config_text` restituisce `Config.warnings: list[str]` (forme: «chiave sconosciuta: profiles.x.k», «profilo x: agent «…» non ha la forma …», «profilo attivo non dichiarato: x»); richiede `schema_version` e `[gate] mode` | `research.py` (solo T2). Coerente. D10: il prefisso `R-<AREA>-` da `area.upper()` non vale per il catalogo (`R-FE-`, `R-DB-`) |
| 3 | `test_git.py` ha `LsFilesAtTest` (311): `test_tree_sizes_at` si aggiunge accanto. `test_init.py`: `test_files_tree` (183), `UpdateTest` (469), `ModeRewriteTest` (535) restano veri (misura §1, sonda 3). `init._plain` esiste (`init.py:62`); `prbody.neutralize(text, max_len)` esiste (`prbody.py:30`) ma **recinta** il testo e non toglie i caratteri di controllo (D8). `globs.escape` (`globs.py:173`): vedi D4. Tre vincoli di testo dei test esistenti: `test_init.py:512` (`assertNotIn("protezione", r.stdout)` sull'uscita di `--update`), `test_skill_contract.py` `CONTRACTS["init"]` (la sezione «## Codici d'uscita» di `skills/init/SKILL.md` deve restare `{0,1}`), `test_manifest.py:514` (nessun `tollgate init|task|…` nudo nelle stringhe di `bin/`) (D16) | `init.py`/`git.py`/`test_init.py`/`test_git.py` con T4; `skills/init/SKILL.md` e `docs/uso/comandi.md` solo qui. Coerente. **D2** (timeout di `tree_sizes_at`) |
| 4 | `git.grep_files_at`: sonda 1 conferma `-z -I -l -F`, uscita 1 senza risultati, prefisso `<ref>:`. `_proc` ha timeout 10 s (`GIT_TIMEOUT_S`), `GitError` per timeout e per `git` assente. `test_git.py` e `test_init.py` come T3 | `init.py`, `git.py` con T3. **D3** (un solo grep contro il risultato per area) |
| 5 | `test_rules_ai.py` nuovo, modello `test_rules_base.py` (id 2 cifre, `RULE` alla riga 12). `tests/test_docs.py:79 test_every_skill_documented` richiede `### `/tollgate:rules-ai``. `test_manifest.py:268 test_agents_and_skills_never_write_a_bare_program_name` e `test_skill_contract.py:184 test_no_skill_mentions_plan_numbers` (`\bP[0-9][a-z]?\b`) si applicano al testo della nuova skill (D16). Il frammento: `fragments.load` rifiuta `rules`/`blocking_rules`, chiavi fuori da `PROFILE_DEFAULTS`, forme di pattern diverse da `**/<cartella>/**` | `docs/uso/comandi.md` (T3, T5, T8); `tests/test_fragments.py` (T2, T5, T7). Coerente; le fonti (`fonti/ai/`) non esistono ancora: Step 0 del controller |
| 6 | Modello `RulesBasePageTest` (`test_rules_base.py:122`), con `test_page_approval_date_matches_skill` (142). `test_real_markers_not_in_tollgate_bin` cerca i marcatori in `bin/`: oggi l'unico candidato che cade è `@anthropic-ai/claude-code` (`bash.py:911`) | `skills/rules-ai/SKILL.md` e `templates/profiles/ai.toml` (T5, T6, T7). Coerente |
| 7 | `test_frontmatter` si inverte; `fragments.approved` legge `research.enforced` (accetta qualunque valore non vuoto e non in `_YAML_EMPTY`) | Solo T7 scrive `approved` (vincolo del brief) |
| 8 | `test_wrapper.py:253 test_readonly_list_matches_config_and_agents` legge `agents/*.md` per l'assenza di Edit/Write/NotebookEdit: `reviewer-ai` (Read, Grep, Glob, Bash, WebFetch) entra, `implementer-ai` no; `test_other_agent_types_reach_python` (244) usa `tollgate:reviewer-web`, mai in elenco: resta vero. `test_manifest.py:112 test_code_agents_preload_rules_base`; `frontmatter()` legge `skills: [rules-base, rules-ai]` come stringa (sonda 5). `config.is_readonly` (`config.py:281-287`) tratta già `^[^:]+:(reviewer|final)-` come sola lettura, quindi l'aggiunta a `readonly_agents` serve solo al test e alla lista del wrapper. `verdicts.is_blocking` (`verdicts.py:91`) e `task_verdict.py:54-60` usano già `prof.blocking_rules/known_rules` dei profili attivi: i tre test `test_ai_*` sono coperti da un meccanismo che c'è (`test_check_task_verdict.py:168-290` ha casi `R-WEB-…` identici) | `agents/final-reviewer.md` e `finding-verifier.md` (D9); `hooks/run` riga 56 e `config.py` riga 73-75 (due elenchi che un test confronta). Coerente |
| 9 | `test_b1_scripts.py`: `test_flow_syntax_and_static_rules` (529) vieta `git stash`, `--amend`, `kill`, `claude plugin install…`, e vuole **esattamente** un `=(claude -p` e un `&& claude plugin validate --strict`; `test_flow_controlla_lists_steps` (545) e `test_flow_rules_vere_out_dir` (630) devono restare veri per il caso predefinito `b1`; `FlowScriptTest` ha una guardia che le evidenze del repo non cambiano (`FLOW_EVIDENCE` = `b1/flusso`). `fakegh.py:26` e `test_protection.py:7`: chiave `repos/{owner}/{repo}/branches/main/protection`, letterale | `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `tests/test_b1_scripts.py`. **D1**, **D15** |
| 10 | Esecuzione del controller | — |
| 11 | Nessun test legge la spec salvo `test_docs.py` (limiti di 1.2 e tipi di evento di 18.4) | D5 |

## 4. Punti da guardare apposta (una riga di esito ciascuno)

1. **Rinvii 184-187 contro `test_manifest.py` e il test di deriva.** Nessuna frase nuova cade in una frase che un test cita alla lettera; il test di deriva (T8) copia i paragrafi già corretti. **Esito: nessun conflitto.** Il rinvio 186 («~97») sta oggi tra le righe 99-109 di `implementer.md`; il rinvio 185 vale solo per `research=False` (D13); la resa del report con `null` e con `concerns` vuoto: D12.
2. **`area_rules` contro i chiamanti di `base_rules`.** `lookups.base_rules` (`lookups.py:183-193`, usata da `task_verdict.py:54` e `apply.py:84`) e `test_rules_base.py:57-59` chiamano `research.base_rules(text)`: con `base_rules` come involucro di `area_rules(text, "BASE")` non cambia nulla. La regola `[blocca]` dei profili passa da `prof.blocking_rules`, non da qui. **Esito: nessun conflitto**; D10 per B4-B7.
3. **Strati.** `tollgate_core/fragments.py` → `tollgate_analysis.research` + `config`: ammesso; `tollgate_analysis/tomlout.py`: nessun import di tollgate; il test di isolamento vieta anche le **stringhe** uguali a un nome vietato (`tollgate_core…`): `tomlout` non ne ha bisogno. `init.py` importa `fragments` e `tomlout`: ammesso (il flusso può importare nucleo e analisi). **Esito: nessun conflitto.**
4. **`init.propose` e i test esistenti.** Misurato (sonda 3): 0 corrispondenze sui 147 percorsi di `install.files`, sul banco e sui file spinti, anche senza esclusioni; il solo albero che accende `ai` è il repo del plugin stesso (`agents/`), che nessun test usa come progetto di `init`. Vincoli di testo (D16): `test_init.py:512`, `CONTRACTS["init"]`, `test_manifest.py:514`. **Esito: nessun conflitto**, `test_real_trees_light_no_profile` è una garanzia vera.
5. **`READONLY_TYPES`/`readonly_agents`.** `test_wrapper.py:253-270` si rompe solo quando esiste `agents/reviewer-ai.md` e si ripara con le due aggiunte; `test_other_agent_types_reach_python` non è toccato; `is_readonly` copre già `reviewer-ai` per regex. **Esito: nessun conflitto**; la spec elenca i tipi in S:603 e S:1143 (D5).
6. **Frontmatter `skills: [rules-base, rules-ai]`.** Il parser di `test_manifest.py:16-26` dà la stringa `[rules-base, rules-ai]`; i test del piano la confrontano come stringa. **Esito: nessun conflitto nel parser**; la validità per Claude Code è «non verificabile da qui» (decisione 9 lo dice).
7. **`B1_FLOW_CASE` contro B1/B2.** Compatibile se il caso predefinito resta identico: `controlla` (stampa e controlla `b1/flow`), `OUT` per `vere` = `b2/flusso`, `registra` senza lettura delle trascrizioni per `b1`. Mancano `tests/__init__.py` (D1) e la regola del nome delle cartelle delle trascrizioni (D15). **Esito: D1 (M), D15 (B).**
8. **`git.ls_files_at`/`_proc`/`_check_ref`.** `_check_ref` rifiuta un riferimento che comincia per `-`; `_proc` dà `GitError` per timeout. `ls_files_at` con prefisso vuoto non serve a T3/T4 (usano `ls-tree -r -l -z <ref>` senza pathspec). **Esito: D2** (timeout di `tree_sizes_at` non gestito dal piano).
9. **`globs.escape/match/match_any/literal_segments`, `profiles.vertical_for`.** `escape("app/[id]/x") + "/**"` = `app/\[id\]/x/**` e corrisponde a `app/[id]/x/p.ts` (sonda 2); `literal_segments` conta 2 (non 3), come dice il piano; `vertical_for` ignora le negazioni, `match_any` le applica (decisione 5 è giusta). **`escape("ai")` dà `/ai/**`, non `ai/**`: D4.** La regola «una negazione esclude» della decisione 7 ignora l'ordine, che in `match_any` conta (D17).
10. **`init._plain` e `prbody.neutralize`.** Esistono: `_plain(text)` (`init.py:62`) sostituisce i caratteri non stampabili con `?` (copre anche i surrogati di `surrogateescape`); `neutralize(text, max_len=2000)` (`prbody.py:30`) tronca a 2000 caratteri e **recinta** il testo, non toglie i caratteri di controllo. Per il README vale come dice il piano (è un recinto), purché il test non si aspetti un testo ripulito. **Esito: nessun conflitto**; D8.
11. **`config.load_config_text`.** Avvisi in `Config.warnings` (liste di stringhe); manca `gate.mode` → `ConfigError`. `test_fragment_profile_validates`, `test_proposal_validates` e `test_active_lists_new_area_warned` devono avere `schema_version = 1` e `[gate] mode` nel testo (D14). **Esito: precisazione.**
12. **`test_docs.py test_every_skill_documented`.** Vuole l'intestazione `### `/tollgate:rules-ai`` e, poiché la skill non è `disable-model-invocation`, **nessun** «solo l'utente» (casefold) nel corpo. **Esito: nessun conflitto**, vincolo di testo per T5.
13. **`verdicts.is_blocking` con `R-AI-…`.** Blocca se la regola è in `blocking_rules` del profilo attivo o se nessun profilo attivo la dichiara; con `[profiles.ai] rules/blocking_rules` calcolati dalla skill (T3) e `ai` attivo dai file del diff (`task_verdict._task_files`), una `R-AI` `[blocca]` dà `changes`, una non `[blocca]` `approved`. Un task senza commit ha `_task_files() == []`: nessun profilo attivo, ogni `R-AI` `major` è «ignota» e blocca (stesso comportamento fail-closed di oggi; vedi D18). **Esito: nessun conflitto con T8.**
14. **`lookups.base_rules(root, active)`.** Chiamata in `task_verdict.py:54` e `apply._final_rules` (`apply.py:84`): già usa `research.active`; le `rules` dei profili attivi entrano separatamente (`prof.blocking_rules(active, profs) | base_blocking`). **Esito: nessun conflitto.**

## 5. Conflitti

Gravità: A = blocca o falsa un test/un esito, M = difetto reale ma aggirabile, B = precisazione o costo basso.

### 5.1 Gravità A

Nessuno. Ho cercato in particolare: test esistenti che il piano rompe senza dirlo (nessuno: i tre rovesciati sono dichiarati), firme che due task usano in modo diverso (nessuna), file che i frammenti veri accendono nei banchi dei test (nessuno), strati violati (nessuno).

### 5.2 Gravità M

**D1 (M). Il progetto di prova `spikes/b3/flow/` non ha `tests/__init__.py`, e il comando di verifica di B1 non gira senza.**
- Dove: P:277 (elenco dei file da creare), P:286; `spikes/b1/flow/tollgate.toml` (`verify = "python3 -m unittest discover -s tests -t ."`); `spikes/b1/flow/tests/__init__.py` esiste; `spikes/run-b1-flow.sh` righe `modo_controlla` (elenco dei file controllati).
- Cosa: l'elenco di P:277 ha `ai/__init__.py` ma non `tests/__init__.py` (e il «`tollgate.toml` di base con il comando di verifica» non dice quale). Misurato (sonda 4): con `-s tests -t .` e senza `tests/__init__.py`, sia `python3.11` sia `python3` falliscono con `ImportError: Start directory is not importable`. `prepara` non lancia la verifica, quindi l'errore emerge solo nel Task 10: `verify` rosso, il task non si chiude, un tentativo su 3 di `passo2` perso e consumo dell'abbonamento.
- Ruling proposta: nell'elenco di P:277 aggiungere `tests/__init__.py`, e fissare nel Task 9 che `spikes/b3/flow/tollgate.toml` ha lo stesso `verify` di B1; far verificare a `controlla` (caso `ai`) tutti i file del progetto del caso, compreso `tests/__init__.py`; un test (`test_flow_case_ai_project_verifies`) lancia il comando di verifica sul progetto copiato da `prepara` con `python3 -B` e si aspetta uscita 0.
- Costo se sbagliata: un tentativo reale di `passo2` (su 3) e il tempo del controller, più un giro del Task 9.

**D2 (M). Un timeout (o un errore) di `git ls-tree -r -l -z` fa fallire tutto `init`, mentre `git grep` degrada.**
- Dove: P:137 (`tree_sizes_at`: «riferimento assente → `{}`», nient'altro), P:40 (solo il timeout di `git grep` è gestito), `git.py:42-51` (`_proc` solleva `GitError` per timeout), `cli.py:495-505` (un `GitError` esce con «tollgate: …», codice 1).
- Cosa: oggi `init` non fa alcuna scansione dell'albero, quindi funziona su qualunque repo. Con T3 `propose` chiama `tree_sizes_at` (10 s di tetto, `-l` legge la dimensione di ogni blob): su un repo molto grande, o su un disco lento, `init` smette di funzionare del tutto, anche per chi non ha nessun profilo da proporre. È una regressione di una funzione che c'era.
- Ruling proposta: in `propose` tutto il calcolo dei profili (`tree_sizes_at`, `detect_files`, `profile_blocks`) sta in un `try … except git.GitError`; in caso di errore il resto della proposta si scrive e si aggiunge una riga «profili non valutati: <motivo>» (nelle righe e nel README). Un test: `tree_sizes_at` che solleva `GitError` → `code == 0`, proposta scritta, riga di avviso; vale anche per `--update`. `FragmentError` resta un rifiuto (è un guasto del plugin, non del repo).
- Costo se sbagliata: `init` rifiuta su repo grandi; si scopre dall'utente, non dai test.

**D3 (M). «Un solo `git grep`» (decisione 6, Task 4) non dà «i file per area» (`detect_files -> dict[area, list]`) con più di un frammento.**
- Dove: P:40, P:165, P:164 (`grep_files_at(...) -> list[str]` senza dire quale marcatore ha colpito), P:46 («è il modello per B4-B7» per gli agenti, e il Task 11 riporta i nomi reali a B4-B7).
- Cosa: con un solo frammento (`ai`) l'attribuzione è banale. Con due (B4 aggiunge `frontend`, ecc.) l'unione dei marcatori in una sola chiamata non dice a quale area appartiene ogni file. L'interfaccia che B3 fissa e che il Task 11 consegna a B4-B7 non regge senza cambiarla.
- Ruling proposta: `detect_files` fa **una chiamata per frammento che ha marcatori** (stessi pathspec, stesso tetto), e il Task 4 lo scrive; la decisione 6 dice «un `git grep` per frammento». Resta un solo grep in B3 (c'è un solo frammento), quindi nessun costo oggi. In alternativa, tenere la firma e dire in Task 11 che B4 la cambia: peggio, perché la cambierebbe con i frammenti già in produzione.
- Costo se sbagliata: B4 rifà `grep_files_at`/`detect_files` e i loro test.

### 5.3 Gravità B

**D4 (B). `escape("ai")` dà `/ai/**`, non `ai/**`.**
- Dove: P:39 («per esempio `src/ai/**`, `ai/**`» e «ogni percorso passa da `globs.escape`»), `globs.py:173-184` (un percorso senza `/` viene ancorato con `/` iniziale; sonda 2: `'ai' -> '/ai/**'`, e per `src/ai` `src/ai/**`).
- Cosa: se l'implementatore costruisce il pattern come `escape(prefisso) + "/**"`, per una cartella alla radice esce `/ai/**` (equivalente, `globs.match("/ai/**", "ai/x.py")` è vero e `literal_segments` vale 1 come per `ai/**`). Il piano scrive `ai/**`; un test che confronta la stringa `"ai/**"` fallirebbe. I test elencati confrontano `src/x/**` e `app/\[id\]/x/**` (che escono giusti).
- Ruling proposta: nessun cambiamento del codice di `globs`; nei test si confronta con `globs.match` e con la stringa solo dove ha uno slash; l'esempio di P:39 diventa `/ai/**` (o `ai/**` se si preferisce togliere la barra iniziale quando la cartella è alla radice, ma allora il percorso `ai` con `[` va ancora passato da `escape`). La pagina (T6) e il README mostrano il pattern com'è.
- Costo se sbagliata: un test rosso da correggere in un minuto.

**D5 (B). La rev 29 deve toccare anche S:603 e S:1143, che oggi elencano i tipi di sola lettura.**
- Dove: P:308 (Step 1 nomina 6.3, 7.3, 11.2, 11.4), S:603 (7.1: «`READONLY_TYPES`: `tollgate:task-reviewer`, …, `tollgate:spec-auditor`»), S:1143 (11.4: `readonly_agents = [...]`), `hooks/run:56`, `config.py:73-75`.
- Cosa: dopo T8 le due liste del codice hanno `tollgate:reviewer-ai` e la spec no; nessun test confronta la spec con le liste, quindi la deriva non si vede.
- Ruling proposta: Task 11 Step 1 aggiunge «7.1 (S:603) e il blocco `readonly_agents` di 11.4 (S:1143)». Costo se sbagliata: spec e codice divergono in silenzio.

**D6 (B). Il catalogo dice altro su tetto di 3 e strumenti dei revisori; il piano lo sa e lo corregge in T11.**
- Dove: C:19 e C:52 (`rules-<area>` nel tetto di 3, «prima delle tre»), C:61 (`ai`: `rules-ai`, `claude-api` per implementatore e revisore), C:2.2 («i revisori hanno solo `Read, Grep, Glob, Bash` e `disallowedTools: Edit, Write`»); P:43-44 (decisioni 9 e 11), P:309.
- Cosa: tre scarti dichiarati (precaricamento fuori dal tetto, `claude-api` fuori dal frammento, `WebFetch` al revisore) contro il catalogo. La spec (S:477) già porta `rules-base` fuori dal tetto per il precaricamento, quindi il primo non è contro il nucleo. Il progetto di B (B:129) lascia a chi costruisce «come la si carica».
- Ruling proposta: confermare le decisioni 9 e 11 com'è scritto; T11 Step 2 aggiorna 1.6, 2.1 e 2.2 (aggiungere anche la riga 2.2 sugli strumenti dei revisori, oggi non nominata in P:309). Costo se sbagliata: il catalogo resta in contrasto con il codice.

**D7 (B). La frase dei rinvii non ha i numeri che il piano usa.**
- Dove: P:35, P:310 («chiusi i rinvii 175, 178, 180-187»), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md` sezione 9 (elenco puntato senza numeri; i numeri 173-188 sono un conteggio del controller, in `fatti/fatti-profili.md`).
- Cosa: l'implementatore del Task 11 non può risalire a quali punti siano «175», «178», «180-187».
- Ruling proposta: nel Task 11 citare ogni rinvio per le sue parole di apertura («L'avviso sul `TOLLGATE_`», «ogni agente nuovo che scrive o rivede codice», «test nuovi con la radice vera», «come si prova il precaricamento», «test di pagina», «ogni regola si giudica su ciò che il revisore vede», «letture con glob», «lavoro senza passo», «report dei giri di correzione», «resa del report nel brief»), oppure numerare gli elementi nella sezione 9 prima di cominciare. Costo se sbagliata: rinvii chiusi o lasciati aperti per sbaglio.

**D8 (B). `prbody.neutralize` recinta e tronca a 2000 caratteri; non è una «pulizia».**
- Dove: P:145 (`test_paths_shown_neutralized`), `prbody.py:30-34`.
- Cosa: con molti percorsi il README di una proposta si tronca a 2000 caratteri con «… (troncato)». Il piano mostra «al più 10 dei file» per profilo, quindi di norma sta nel tetto, ma `Profili proposti` con più profili o percorsi lunghi potrebbe superarlo.
- Ruling proposta: chiamare `neutralize` per sezione di profilo, con `max_len` generoso (per esempio 4000), e il test controlla anche che un nome con carattere di controllo non esca nel recinto come tale (`init._plain` prima di `neutralize`). Costo se sbagliata: elenco troncato nel README.

**D9 (B). La «Mappa dei file» non nomina `agents/final-reviewer.md` e `agents/finding-verifier.md`.**
- Dove: P:71 (riga del Task 8) contro P:256 (Files del Task 8).
- Ruling proposta: aggiungere i due file alla riga di P:71. Costo se sbagliata: nessuno oltre alla coerenza del documento (l'elenco dei file toccati serve alla revisione di T8).

**D10 (B). `area_rules(text, area)` costruisce `R-<AREA>-` dal nome dell'area, il catalogo usa sigle.**
- Dove: P:37 e P:122; C:5 (`R-FE-07`, `R-DB-03`), piano principale sezione 3 riga B2→B3-B7 («`R-<AREA>-NN`»).
- Cosa: per `ai` coincidono (`R-AI-`). Per `frontend` il nome dell'area darebbe `R-FRONTEND-`, il catalogo `R-FE-`. B3 non è toccato.
- Ruling proposta: nessuna ora; il Task 11 lo scrive tra i rinvii a B4-B7 («il prefisso è il nome dell'area, maiuscolo: dichiaralo nella skill o cambia `area_rules`»). Costo se sbagliata: B4 scopre che `init` calcola `rules` vuote per `frontend` e il profilo, senza regole note, farebbe bloccare ogni `R-FE-…` come ignota.

**D11 (B). Precondizione sui marcatori: `bin/tollgate_analysis/bash.py:911` contiene `@anthropic-ai/claude-code`.**
- Dove: P:229 (`test_real_markers_not_in_tollgate_bin`), P:211 (marcatori dal Task 5), `bin/tollgate_analysis/bash.py:911`.
- Cosa: un marcatore che è un prefisso (`@anthropic-ai/`, `anthropic-ai`) cadrebbe in quel file e rompe il test; l'unica forma sicura per Anthropic in JS/TS è `@anthropic-ai/sdk`. Nessun altro candidato plausibile (`from anthropic`, `import anthropic`, `from openai`, `google.generativeai`, `@google/genai`, `from agno`, `openrouter.ai/api`, `api.openai.com`) è in `bin/` o `hooks/` (grep, §1).
- Ruling proposta: dirlo nel brief del Task 5/6 come vincolo ai marcatori; il test c'è già. Costo se sbagliata: un giro del Task 6.

**D12 (B). Resa del report nel brief (Task 1): valori vuoti e `null`.**
- Dove: P:91, P:93; `taskcmd.py:268-281`; `tests/test_taskcmd.py:628` (`"concerns": ""` con `DONE`).
- Cosa: oggi `left: ""` esce come riga vuota `left: `; con `concerns` incluso per `DONE` un `concerns: ""` aggiungerebbe una riga vuota in più, e `"size_reason": null` esce come `None`. Il piano chiede «`null` o saltare il campo».
- Ruling proposta: per i campi del report rendere `null` come `null` e **saltare** i campi stringa vuoti **solo per `concerns`** (gli altri restano come oggi, per non cambiare i test esistenti); `concerns` non vuoto con `DONE` compare nella sezione del report. Costo se sbagliata: rumore nel brief, nessun test rosso.

**D13 (B). La frase del rinvio 185 è legata a `research=False`, la spec dice anche «interruttore spento».**
- Dove: P:90, P:93; `brief.py:253-258` (la sezione del report c'è solo se `implementer_report`); S:478-479 e il testo di 8.6 rev 28 («con l'interruttore spento o in un lavoro senza passo le `R-BASE-…` sono note e nessuna blocca»); `taskcmd.py:~385` (`research_enforced=research_on and lookups.rules_enforced(...)`).
- Cosa: con `research=True` e `research_enforced=False` nessuna `R-BASE-…` blocca, ma la frase non compare. Con il plugin vero (rules-base approvata) il caso non si presenta.
- Ruling proposta: condizione `not (b.research and b.research_enforced)`; test con le tre combinazioni (`research` falso; vero con interruttore spento; vero con interruttore acceso, senza frase). Costo se sbagliata: nessuno oggi.

**D14 (B). I test di `config.load_config_text` del piano hanno bisogno di un `tollgate.toml` completo.**
- Dove: P:120 (`test_fragment_profile_validates`), P:145 (`test_proposal_validates`, `test_active_lists_new_area_warned`); `config.py:206-243`.
- Cosa: il testo deve avere `schema_version = 1` e `[gate] mode = "protected"` o `load_config_text` solleva `ConfigError`; per «senza avvisi» il frammento di prova non deve avere un `agent` fuori dalla forma `<plugin>:implementer-<area>` (avviso e chiave svuotata).
- Ruling proposta: nei brief dei Task 2 e 3. Costo se sbagliata: test rossi per un motivo estraneo.

**D15 (B). `registra` (Task 9): regola del nome delle cartelle di trascrizioni e confini della lettura.**
- Dove: P:286; `spikes/b1/flowreg.py` (`precarico` cerca solo il titolo di `rules-base`, `test_flowreg_precarico` in `test_b1_scripts.py:666`); `esecuzione.md` eccezione 4.
- Cosa: la cartella di una sessione in `~/.claude/projects/` si chiama come il `cwd` con ogni carattere non alfanumerico sostituito da `-` (`/tmp/tollgate-b1/flow/.claude/worktrees/tg-1-x` → `-tmp-tollgate-b1-flow--claude-worktrees-tg-1-x`; prova indiretta: la memoria `sessioni-nei-worktree`). Se l'implementatore indovina la regola male, `registra` non trova nulla e lo scopre il Task 10. Inoltre la ricerca va fatta **solo** con `B1_FLOW_CASE=ai`, con `HOME` non vuota (come `raccogli.py` rifiuta una `HOME` vuota) e senza mai elencare altre cartelle; l'output stampa solo le righe col titolo (niente percorsi, come `precarico`).
- Ruling proposta: scrivere la regola nel brief del Task 9; test con `cwd` che contengono punto e spazio; titolo da cercare `# Regole ai (versione 1)` e `# Regole di base (versione 1)`; i test esistenti di `registra`/`flowreg precarico` per `b1` e `b2` restano identici. Costo se sbagliata: un giro del Task 9 dopo il Task 10 (nessun consumo di tentativi `claude -p` se si corregge e si rilancia solo `registra`).

**D16 (B). Vincoli di testo dei test esistenti sul testo che i task aggiungono.**
- Dove: `tests/test_init.py:512` (`assertNotIn("protezione", r.stdout)` dopo `--update` con protezione presente: le righe dei profili non devono contenere la parola); `tests/test_skill_contract.py` `CONTRACTS["init"]` e `CODE_LINE` (la sezione «## Codici d'uscita» di `skills/init/SKILL.md` dichiara solo 0 e 1; il testo nuovo sui profili va fuori da quella sezione e senza righe che comincino per `- **<n>`), e `test_init_skill_never_copies_or_protects`; `tests/test_manifest.py:268` e `:514` (nessun `tollgate init|task|status|…` nudo nei testi di agenti, skill e nelle stringhe di `bin/`: usare `program_command` o `/tollgate:init`); `test_skill_contract.py:184` (`\bP[0-9][a-z]?\b` vietato nelle skill); `test_docs.py` (`solo l'utente` vietato nel corpo di `rules-ai`); `test_manifest.py:455` (`bin/tollgate` nei nuovi agenti solo come `python3 "…/bin/tollgate"`).
- Cosa: non sono conflitti del piano, ma ognuno è un rosso che un implementatore troverebbe da sé alla prima corsa.
- Ruling proposta: elencarli nei brief dei Task 3, 5 e 8. Costo se sbagliata: un giro di correzione per task.

**D17 (B). La regola «una negazione dell'utente esclude» (decisione 7) non dice che l'ordine conta.**
- Dove: P:41 («segnalando un file solo se nessun pattern positivo dei `paths` lo copre **e** nessun pattern `!p` lo esclude»), `globs.match_any` (`globs.py:161-170`: decide l'ultimo pattern che corrisponde).
- Cosa: letta alla lettera la regola ignora l'ordine. Con `["!lib/x/gen/**", "lib/x/**"]` il file `lib/x/gen/a.py` è coperto (il positivo viene dopo la negazione) e non va segnalato; con `["lib/x/**", "!lib/x/gen/**"]` è escluso e non va segnalato; solo se nessun pattern lo copre e nessuna negazione lo riguarda va segnalato. La formulazione che regge è: segnalare solo se `match_any(paths, f)` è falso **e** nessun `!p` dei `paths` corrisponde a `f`.
- Ruling proposta: scriverla così nel Task 3 e testare i due ordini. Costo se sbagliata: un file escluso dall'utente segnalato a ogni `--update`.

**D18 (B). Task senza commit: ogni `R-AI` `major` è «ignota» e blocca.**
- Dove: `task_verdict.py:29-41` (`_task_files` → `[]` se non ci sono commit), `verdicts.py:99-101`.
- Cosa: un revisore `reviewer-ai` che chiude un task senza modifiche con un `major` su una `R-AI-…` non `[blocca]` ottiene `changes`, mentre su un task con modifiche otterrebbe `approved`. Identico a oggi per qualunque profilo; per `R-BASE-…` non succede perché le note di base si leggono dalla skill. Il brief del revisore ha già «Nessuna modifica: verifica che il task sia già soddisfatto».
- Ruling proposta: nessun cambiamento di codice in B3; la sezione «Area `ai`» di `reviewer-ai` dice: «in un task senza modifiche non apri rilievi `R-AI-…`». Costo se sbagliata: un giro `--fix` inutile sul caso raro.

**D19 (B). Test nuovi di T1 nella classe che usa la radice vera.**
- Dove: P:91 (`ReviewDoneTest`, `tests/test_taskcmd.py:365`), Global Constraints P:19 (radice esplicita), piano principale sezione 9 («test nuovi con la radice vera»).
- Cosa: `ReviewDoneTest.prepare()` chiama `review_prepare`, che legge `lookups.rules_enforced(db.BIN_PATH.parents[1])`, cioè la `rules-base` vera: i due test nuovi di T1 dipendono dall'interruttore come gli altri della classe, ma asseriscono solo sulla sezione del report, che non cambia con l'interruttore.
- Ruling proposta: accettare (stessa dipendenza degli altri test della classe, già nota come «da valutare»); nel nome non serve `test_real_…`. Costo se sbagliata: nessuno.

**D20 (B). `profile_blocks` è detta «pura sui dati», ma legge frammenti, skill e agenti dal `plugin_root`.**
- Dove: P:140. Ruling proposta: dire «senza rete né git: legge solo `plugin_root`», nei test si passa sempre un plugin temporaneo (già previsto). Costo: nessuno.

## 6. Voci per `carry.md` (una per conflitto, da aprire prima dei task che ne dipendono)

| Conflitto | Task che ne dipende | Quando decidere |
|---|---|---|
| D1 | 9 (e 10) | prima del Task 9 |
| D2 | 3 | prima del Task 3 |
| D3 | 4 (e 11) | prima del Task 4 |
| D4, D8, D14, D16, D17, D20 | 3 | prima del Task 3 |
| D5, D6, D7, D10 | 11 | prima del Task 11 (D10 e D3 anche nel piano principale come rinvii a B4-B7) |
| D9 | 8 | nel brief del Task 8 |
| D11 | 5, 6 | nel brief dei Task 5 e 6 |
| D12, D13, D19 | 1 | prima del Task 1 |
| D15 | 9, 10 | prima del Task 9 |
| D18 | 8 | nel brief del Task 8 |
