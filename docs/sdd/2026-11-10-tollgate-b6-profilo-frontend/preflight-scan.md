# Scan pre-flight del piano B6 (profilo `frontend`)

Analista: sonnet, sola lettura. Worktree `b6`, ramo `b6-profilo-frontend`, HEAD `f3ca4a2` (uguale a `main`). Sigle: `P:<riga>` piano (`docs/superpowers/plans/2026-11-10-tollgate-b6-profilo-frontend.md`), `B:<riga>` progetto di B, `S:<riga>` spec del nucleo rev 32, altrimenti `file:riga` del codice di `main`.

**Esito in una riga:** 0 conflitti A, 2 M, 8 B. Le 36 righe della tabella delle precedenze (P1-P36) escono **come scritte**, sia nella proposta sia a runtime, sui frammenti veri di `ai`, `infra`, `backend` e su un `frontend` scritto come le decisioni 3, 5 e 7. Nessun caso diverso tocca una scelta dell'utente (progetto 12 o 13). Nel cercare un caso che la tabella non ha ne sono usciti quattro (D3, D4, D5, tutti B).

## 1. Metodo e limiti

**Letto per intero:** il piano (395 righe), la sezione «Scan pre-flight» e le regole di cautela del brief, il progetto di B (3.4, 4, 11, 12, 13), il modello `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/preflight-scan.md`. Dalla spec del nucleo: 6.3 (S:483-491), 7.1 (S:615), 11.2 (S:1093-1099), 11.4 (S:1286-1288). Dal codice: `bin/tollgate_core/fragments.py` (tutto), `bin/tollgate_flow/init.py` (28-50, 203-430), `bin/tollgate_analysis/profiles.py`, `globs.py`, `bin/tollgate_core/config.py` (72-82, 308-318), `hooks/run` (51-66), `spikes/b1/flowreg.py` (24-40, 290-420), `spikes/run-b1-flow.sh` (1-125, 206-262, 400-495), `templates/profiles/ai.toml`, `infra.toml`, `backend.toml`. Test letti o cercati: `test_fragments.py` (85-110, 170-262), `test_init.py` (666-720, 925-1000, 1050-1200, 1300-1340), `test_manifest.py` (1-15, 100-235), `test_wrapper.py` (245-270), `test_b1_scripts.py` (495-580, 1113-1121, 1650-1710), `test_rules_ai.py` (`rules`, riga 62), `test_rules_backend.py` (125, 247-259, 420-490), `test_docs.py`, `test_taskcmd.py`, `test_profiles.py`, `test_check_task_verdict.py` (nomi).

**Sonde** (tutte fuori dal repo, in `/home/USER/.claude/jobs/e28b8553/tmp/preflight/`, `python3 -B`, nessuna rete, nessun programma di servizio, nessun `node`):
- `lib.py`: importa `tollgate_core`/`tollgate_flow` dal worktree e **simula la forma `ext`** come la descrive la decisione 2, con tre sostituzioni nel solo processo della sonda: `fragments.parse_pattern` (regex `\*\*/\*\.([A-Za-z0-9]+)` provata per ultima), `init._match` (se nessuna forma ha acceso il file, il file non è un documento e il nome finisce con `.<estensione>`, maiuscole rispettate; resta il controllo di `EXCLUDED_PREFIXES` e `exclude`), `init.concrete_for` e `init._concrete_paths` (il valore `ext` va nei `paths` così com'è, uno per estensione). `profile_blocks`, `_drift`, `vertical_for`, `config.load_config_text` sono quelli veri di `main`.
- `frontend.toml`: il frammento scritto come le decisioni 3 (nove pattern, in ordine), 5 (otto marcatori, due forme di virgolette), 7 (`exclude` di sei prefissi), 8 (`commands = {}`, `dod = []`), 13 (`min_level = "L0"`), con `agent`/`reviewer` `-frontend`. Una radice temporanea con i frammenti veri `ai`, `infra`, `backend` e quello di prova, ognuno con una skill finta approvata (`R-<AREA>-01 [blocca] x`), come fa `test_real_trees_light_no_profile`.
- `cases.py`: P1-P36 più P22b. `detected` è calcolato come `detect_files` (file sorgente rilevabili che contengono un marcatore, con `exclude` del frammento) salvo dove la riga dice altro (P22 forzato). Il confronto è sull'insieme dei `paths` proposti per ogni profilo e su `vertical_for` di ogni file, con i blocchi nell'ordine in cui `profile_blocks` li scrive (`ai`, `backend`, `frontend`, `infra`: ordine alfabetico del nome del file).
- `extra.py`: i casi che la tabella non ha (sezione 4.2), P2/P21/P22 senza `exclude`, e una corsa di `_drift`.
- Alberi: i quattro di `test_real_trees_light_no_profile` (push 5 file, CLI 14, installato 139, installato + proposta 278) con il frammento di prova; l'intero `git ls-files` del worktree (10670 file) con `detected` calcolato sul contenuto vero; il progetto di prova previsto per `spikes/b6/flow/`.
- Evidenze: `flowreg.third_party_blocks`/`_scan` con `_saved_copy` sostituita dalla versione senza `SAVED_READERS` (come la descrive il Task 2) su tutti i `.jsonl` di `docs/verifiche/evidenze/` (sola lettura); 424 `Bash`.
- `git grep -F` dei marcatori su `bin spikes evals hooks gate templates agents skills statusline tests docs`.

**Non verificabile da qui:** il contenuto delle pagine ufficiali (P:17-35: nessuna rete; compresa la questione se i moduli di React Router 7 importino da `react-router`, P19/P23); i conteggi sul disco dell'utente (P:32); la suite intera e `claude plugin validate` (baseline in corso); il comportamento reale di `init` dalla CLI su un repo git (la sonda chiama `profile_blocks` e non `git grep`); WCAG 2.2 e «Using ARIA» (P:28-29); il testo di `frontend-ui-engineering` e `frontend-design`.

## 2. Tabella per coppie di task

| Coppia | File o interfaccia condivisi | Cosa produce / consuma | Nomi e firme che devono coincidere | Esito |
|---|---|---|---|---|
| T1 - T3 | `fragments.Pattern`, `parse_pattern` | T1: `Pattern("ext", "<estensione>")`; T3: `frontend.toml` con sei pattern `**/*.<ext>` | `kind == "ext"`, `name` = estensione senza punto, maiuscole conservate | Coincidono. Nessun chiamante fuori da `init._match` legge `.kind` (`grep` su `bin`); `fragments.py:33` ha il commento `# "folder" \| "root_folder" \| "name"` da aggiornare (D6) |
| T1 - T3 | `init._match`, `concrete_for`, `_concrete_paths`, `profile_blocks` | T1 le estende; T3 le usa dal vivo con 36 casi | `concrete_for` → `**/*.<ext>` senza `globs.escape`; `_concrete_paths` un valore per estensione | Coincidono (sonda: P1-P36 come scritti). Il piano non nomina la firma di `_match` per la nuova forma (`("ext", "**/*.<ext>")`): lo dice solo la decisione 2, P:60 |
| T1 - T3 | `tests/test_fragments.py` | T1 aggiorna `test_parse_pattern_rejects` e `test_load_rejects_other_pattern_forms`; T3 `test_real_fragments_load` | stessa classe `RealFragmentsTest` (riga 222) per T3 e T5 (`test_real_frontend_fragment_approved`) | Righe diverse, nessun conflitto di merge. Il piano dice che **tutti e due** i test rifiutano oggi `.sql`, `.json`, `.Dockerfile` (P:163): vero solo per `test_parse_pattern_rejects` (`test_fragments.py:183-185`); `test_load_rejects_other_pattern_forms` ha solo `**/*.sql` (`:94`). D6 |
| T1 - T3 | `tests/test_init.py` | T1: sei test in `ProfileBlocksTest` (riga 699); T3: `FrontendPrecedenceTest` e la funzione d'aiuto `_real_fragments_root` estratta da `test_real_trees_light_no_profile` (riga 1143) | `_real_fragments_root(test, areas)`; stessi nomi di `PluginMixin`, `BASE_TOML`, `ROOT` | Coincidono. `test_real_trees_light_no_profile` resta verde con il frammento vero (sonda: nessuno dei quattro alberi accende `frontend`) |
| T1 - T3 | `docs/uso/comandi.md`, sezione `/tollgate:init` (riga 117) | T1 scrive la frase sui pattern per estensione senza nominare `frontend`; T3 la completa e aggiunge `### /tollgate:rules-frontend` | frase unica | Sezioni distinte, nessun conflitto di cherry-pick per il rinvio (decisione 14). Oggi la sezione non parla di pattern: la frase si aggiunge, non si sostituisce |
| T1 - T6 | `tests/test_profiles.py` | T1: quattro guardie (`test_ext_pattern_*`, `test_nested_components_beats_root_folder`, `test_exact_infra_file_beats_web_folder`); T6: `test_frontend_and_backend_routing_is_split_candidate` | classi/dati `PROFILES` in testa (riga ~103) | Guardie T1 verificate: già verdi su `main` (sonda con `profiles.vertical_for`: `backend`/`backend`, `frontend`, `infra`, `frontend`). Nessun conflitto con T6 |
| T2 - T7 | `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py` | T2: riga 2, intestazione di `scrivi_limiti` (riga 408), `SAVED_READERS` tolto; T7: il caso `frontend` in 12 punti dello script, `AREA_TITLES` (flowreg.py:27) | `scrivi_limiti` prima riga uguale per tutti i casi | Zone diverse dello script; T7 viene dopo T2. L'elenco dei 12 punti dello script è in D8 |
| T2 - T8 | `flowreg togli-pagine` e `test_committed_evidence_has_no_long_web_results` (test_b1_scripts.py:1113) | T2 allarga il rilevatore; T8 pulisce le evidenze nuove | rilevatore uguale prima e dopo | Sulle evidenze già committate il rilevatore più largo trova **0** segnalazioni (424 `Bash`, 0 che nominano `tool-results/`, 0 `tool_use_result.stderr` non vuoti): resta verde. Il 424 del giro 4 del piano torna. Lacune del rilevatore: D1 |
| T3 - T4 | `skills/rules-frontend/SKILL.md`, `frontend.toml`, `tests/test_rules_frontend.py` | T3 scrive bozza e frammento; T4 il rapporto e la pagina, e corregge la skill/frammento se una fonte esce | pattern, marcatori, prefissi di `exclude` = righe `ok` del rapporto | Coincidono nel disegno. `test_real_exclude_matches_root_folders_of_other_fragments` verificato: i root_folder dei frammenti veri sono `api server backend functions` (backend) e `infra`: uguali a `exclude` meno `supabase/` |
| T3 - T5 | `test_frontmatter` (si inverte), `test_page_choices_count_matches_list`, `test_extensions_...` | T5 sposta le asserzioni da «Da decidere tu» a «Cosa hai deciso» | stessi nomi | Coincidono. Il dizionario delle parole di B5 arriva a 11 (`test_rules_backend.py:469-474`): T4 lo estende a «trenta» (P:253) |
| T3 - T6 | `AREAS` di `tests/test_manifest.py:9`; skill `rules-frontend` approvata prima degli agenti | T3/T5 producono la skill con «Si giudica su: report» solo su R-FRONTEND-01 e 02; T6 la legge | `^Si giudica su: report$` (test_manifest.py:166), almeno una regola sul report e una sul diff | Coincidono con la bozza di P:222-233. Finestra tra T5 e T6: `frontend` approvato ma agenti assenti, `init` dice «agent non proposto: manca agents/implementer-frontend.md» (sonda, riga di `profile_blocks`). Solo tra due commit, innocuo |
| T5 - T6 | `skills/rules-frontend` approvata → `skills: [rules-base, rules-frontend]` | T6 carica la skill solo dopo T5 | `f"[rules-base, rules-{area}]"` (test_manifest.py:118-122) | Coincide |
| T6 - T7 | `reviewer-frontend` in `READONLY_TYPES`/`readonly_agents`; `proponi_profilo` cerca gli agenti | T7 prova gli agenti | `hooks/run:56`, `config.py:76-80` | Coincide: dopo T6 `init --propose` sul progetto di prova propone anche `agent`/`reviewer` (prima no) |
| T7 - T8 | `spikes/b6/flow/`, `OUT=docs/verifiche/evidenze/b6/flusso` | T8 esegue | percorsi | Coincide. Sonda sul progetto di prova previsto (D8): proposta `["**/*.tsx", "/web/**", "src/components/**"]` e nessun `backend`: P9 dal vivo |
| T1/T2 - T9 | rev 33 della spec, S:1093-1099 | T9 la scrive | 11.2: «`init` non propone i pattern del frammento così come sono» (S:1093) | Va riscritta: D10 |
| T1 - B7 | forma `ext` per `**/*.sql` | T9 scrive che B7 può usarla | `Pattern("ext", "sql")` | Verificato: `**/*.sql` ora è accettato (D6) |

## 3. Tabella per task

### Task 1 (forma `ext`)

| Test previsto | Esistenza / stato oggi | Contro il codice | Esito |
|---|---|---|---|
| `test_parse_pattern_rejects` (P:163) | esiste, `test_fragments.py:182-188`; rifiuta `**/*.sql`, `**/*.json`, `**/*.Dockerfile` | con `ext` i tre sono accettati (sonda); gli altri 23 restano rifiutati (`**/*`, `**/**`, `**/a*b`, `**/*.{tsx,jsx}`, `**/è.json`, `**/a*/**`, …) | Va aggiornato come dice il piano: i tre valori passano a `test_ext_pattern_parsed` |
| `test_load_rejects_other_pattern_forms` | esiste, `:93-99`; elenco `**/*.sql`, `src/ai/**`, `**/a/b/**`, `**/**`, `!**/ai/**`, `**/a*/**`, `""` | solo `**/*.sql` diventa accettato | Va aggiornato; il piano gli attribuisce anche `.json` e `.Dockerfile` (D6) |
| `test_ext_pattern_parsed`, `test_ext_rejects_bad_forms` | nuovi | `**/*.CSS` → `Pattern("ext","CSS")`. Delle 9 forme da rifiutare (P:160), tutte rifiutate dalla regex; in più `**/*.1` e `**/*.Dockerfile` sono accettati (corretto: sono sole lettere/cifre) | Coerente. Il messaggio di `_parse` (`fragments.py:88-90`) oggi non nomina `**/*.<estensione>`: il test lo chiede, il Task lo cambia |
| `test_concrete_for_ext` | nuovo | `src/main.tsx` → `**/*.tsx`; `src/components/a.tsx` → `src/components/**`; `src/Foo.TSX` → `None`; `.github/tollgate/x.tsx` → `None` (`EXCLUDED_PREFIXES`); con `["**/*.md"]` `docs/a.md` → `None`; con `exclude=("supabase/",)` `supabase/x.tsx` → `None` | Tutti confermati dalla sonda |
| `test_ext_proposed_once`, `test_ext_not_proposed_when_folder_covers_all` | nuovi | tre `.tsx` in cartelle diverse → un solo `**/*.tsx`; tutti sotto `src/components/` → solo `src/components/**` | Confermati |
| `test_ext_in_drift` | nuovo | `_drift` con `[profiles.x] paths=["src/components/**"]` e `src/main.css` → `profilo x: [profiles.x] paths: aggiungi "**/*.css" (1 file)` | Confermato (la sonda dà la riga per `**/*.css` e `**/*.tsx`) |
| `test_content_found_file_covered_by_ext` | nuovo | `.tsx` trovato per contenuto: nessun percorso esatto (P9); `.ts`: percorso esatto (XE, P23) | Confermato |
| `test_exclude_multi_segment_prefix` | nuovo | `_EXCLUDE` (`fragments.py:25`) accetta già più cartelle; `startswith` regge `apps/api/` | Confermato dal codice |
| quattro guardie di `test_profiles.py` | nuove, «già verdi su `main`» | `vertical_for` con profili scritti: `server/app.tsx` → `backend` in tutti e due gli ordini; `server/components/m.tsx` → `frontend`; `web/vercel.json` → `infra`; `src/main.tsx` → `frontend` | Davvero verdi su `main` |
| `test_existing_forms_unchanged` | nuovo, «già verde» | `test_name_pattern_exact_paths` (`test_init.py:931`) e `test_concrete_for_exclude_default_is_b4` (`:939`) esistono | Coerente |

File toccati anche da altri task: `docs/uso/comandi.md` (T3, T6), `tests/test_fragments.py` (T3, T5), `tests/test_init.py` (T3), `tests/test_profiles.py` (T6). Coerenza interna: la decisione 2 dice che `_concrete_paths` non toglie `ext` per copertura (P:60), e il codice di `_concrete_paths` oggi toglie i soli percorsi esatti coperti da cartelle (`init.py:245-254`): compatibile.

### Task 2 (`togli-pagine`)

| Test | Stato | Esito |
|---|---|---|
| `test_togli_pagine_bash_reading_saved_copy`, `test_third_party_detects_bash_stdout` | esistono (`test_b1_scripts.py:1671`, `:1691`), «già verdi» | Restano verdi anche con `_saved_copy` senza lettori (i loro comandi hanno `cat`, `sed`, `grep`, `stderr: ""`; con `stderr` vuoto `_swap_saved` non lo tocca) |
| `test_togli_pagine_bash_any_reader` | nuovo | `python3 -c "…open('/x/tool-results/toolu_a.txt')…"` (percorso dopo `'`) e `jq . /x/tool-results/toolu_b.json` (dopo spazio): trovati dalla regex di `SAVED_PATH` (`flowreg.py:32`) |
| `test_togli_pagine_bash_stderr`, `test_third_party_detects_bash_stderr` | nuovi | `cat /x/tool-results/toolu_c.txt 1>&2`: trovato. Il rilevatore deve tenere conto di `stderr` in `left` (`flowreg.py:381`) |
| `test_scrivi_limiti_heading_is_generic` | nuovo | «Task 9» compare nello script solo alle righe 2 e 408: il test «lo script non contiene più Task 9» è soddisfabile. Resta «Task 9» nel docstring di `flowreg.py:2` e in docstring di test (non toccati dal piano) |
| `test_togli_pagine_leaves_plain_bash` | nuovo, verde dall'inizio | `cat app.py` non ha `tool-results/`: non cambia |
| `test_committed_evidence_has_no_long_web_results` | `:1113` | verde con il rilevatore più largo (0 segnalazioni su 424 `Bash`) |

Lacune del rilevatore descritto dal Task: **D1**.

### Task 3 (bozza, frammento, tabella)

| Test | Stato | Esito |
|---|---|---|
| `test_real_trees_light_no_profile` | esiste (`test_init.py:1143`), il piano indica righe 1151-1161 per la parte da estrarre: corrispondono al ciclo di copia dei frammenti | Con `frontend.toml` nessuno dei quattro alberi accende `frontend` (sonda) |
| `test_real_fragments_load` | esiste (`test_fragments.py:225`) | Si aggiunge `frontend`; `found["frontend"].exclude` = i sei prefissi |
| `test_real_precedence_p1..p36` | nuovi | Tutti i valori attesi della sonda coincidono con P:66-101 (sezione 4). Le righe «già verdi senza `frontend`» (P2, P5, P7, P16-P18, P21, P22: P:217) sono esattamente quelle senza `frontend` nella colonna «Proposta»; P22 con `server/entry.ts` anche nel `detected` di `frontend` dà lo stesso esito di P22b senza |
| `test_real_frontend_exclude_several_prefixes` | nuovo | per costruzione di `exclude` + `_match`; non lanciato come test, vedi P2/P21 senza `exclude` sotto |
| `test_real_exclude_matches_root_folders_of_other_fragments` | nuovo | verificato a mano (sezione 2, T3-T4) |
| `test_fragment_matches_decisions`, `test_fragment_leaves_out_tool_configs`, `test_markers_are_router_imports` | nuovi | `frontend.toml` della sonda si carica con `fragments.load`; nessun pattern contiene `services`, `hooks`, `vite`, `tsconfig`, `eslint`, `html`, `app/**`, `page` |
| `test_real_markers_not_in_tollgate_bin` | nuovo | `git grep -F` dei tre moduli: 0 occorrenze fuori da `docs/superpowers/plans/…b6-profilo-frontend.md`. `bin/` pulito |
| `test_area_agents_*`, `test_manifest` | non toccati da T3 | — |
| test della skill (`test_at_most_150_lines`, `test_no_long_quotations`, …) | modello `test_rules_backend.py:138`, `:247` | Le skill esistenti stanno a 76-84 righe: 12 regole nel tetto di 150 sono plausibili |
| `test_every_skill_documented` | `test_docs.py:79` | richiede `### /tollgate:rules-frontend` (Step 4) |
| `claude plugin validate --strict` | non lanciato | — |

Coerenza interna: R-FRONTEND-01 e 02 sono le sole «report» (P:222-223), così il test di `test_manifest.py:166-176` (`on_report` non vuoto, `ids - on_report` non vuoto) è soddisfatto. Fonte di R-FRONTEND-10: D9.

### Task 4 (fonti e pagina)

| Test | Stato | Esito |
|---|---|---|
| copia da `RulesBackendPageTest` (`test_rules_backend.py:264`) | esiste; i nomi `test_sources_report_covers_every_rule`, `test_removed_sources_are_not_in_the_skill`, `test_tables_have_one_header`, `test_path_patterns_verified`, `test_detect_markers_verified`, `test_exclude_verified`, `test_page_choices_count_matches_list`, `test_page_has_no_private_data`, `test_page_rinvio…`, `test_extensions_of_the_sources…` esistono (grep) | Coerente. `test_sources_report_covers_every_rule` esiste già in `test_rules_base.py:128` e `test_rules_ai.py:243`: le versioni da copiare con le correzioni (decisione 16) sono quelle di `backend` |
| `test_page_choices_count_matches_list` | dizionario di B5 fino a 11 | T4 lo porta a 30 con errore esplicito: serve, la lista di P:253 ha almeno 18 voci |
| `test_page_explains_what_changes` | nuovo | Elenca P2, P3, P4, P13, P32-P34: tutti verificati. Mancano nella pagina i casi nuovi D3-D5 |

### Task 5 (approvazione)

Nessun conflitto. `test_real_frontend_fragment_approved` segue lo schema di `test_fragments.py:236-250`. Prima dell'approvazione `fragments.load_approved` non carica `frontend` e nessun test della CLI cambia; dopo, il frammento entra negli alberi dei test della CLI (`ModeTest`, `FilesTest`, `ServicesTest`, `HintsTest`, `UpdateTest`, `ProtectScriptTest`): sonda sull'albero di ciascuno, vedi sezione 5.

### Task 6 (agenti)

| Test | Stato | Esito |
|---|---|---|
| `test_area_agents_derive_from_generic`, `_attribution`, `_name_area_rules`, `test_code_agents_preload_rules_base`, `test_final_reviewers_leave_report_rules_of_areas` | esistono (`test_manifest.py:124`, `:149`, `:154`, `:113`, `:214`) e iterano su `AREAS` (`:9`) | Rossi con `frontend` finché non esistono i due agenti e le frasi di `final-reviewer.md`/`finding-verifier.md` (oggi nominano solo `R-AI-`, `R-INFRA-`, `R-BACKEND-`: `agents/final-reviewer.md:37`, `finding-verifier.md:13`). **`:135` richiede che la `description` contenga la parola intera `frontend`** (D7) |
| `test_readonly_list_matches_config_and_agents` | `test_wrapper.py:253` | rosso quando esiste `reviewer-frontend.md` (ha `WebFetch`, nessun `Edit`/`Write`); da aggiornare `hooks/run:56` e `config.py:76-80`. `config.is_readonly` (`:312-318`) riconosce già `reviewer-*` per prefisso |
| guardie di `test_taskcmd.py`, `test_check_task_verdict.py`, `test_profiles.py` | esistono quelle di `backend` come modello | già verdi: lo smistamento legge solo le stringhe `agent`/`reviewer` |

### Task 7 (prova: script e progetto)

| Punto | Stato | Esito |
|---|---|---|
| `src_repo` (`test_b1_scripts.py:504`) | l'indice `{"ai":…,"infra":…,"backend":…}[case]` (`:519`) e la tupla `parts` (`:512-513`) non conoscono `frontend` | Il piano dà la firma `src_repo(case="frontend", frontend_approved=True)`; con la sola opzione senza voce nel dizionario sarebbe un `KeyError` (D8) |
| `proponi_profilo` «approva anche `rules-backend`» (P:312) | la funzione (`run-b1-flow.sh:232-260`) non approva niente: `init --propose` legge la copia del plugin, dove `rules-backend` è approvata perché tracciata così su `main` | Imprecisione del piano (D8). La sonda sul progetto di prova previsto, con `backend` approvato: nessun `[profiles.backend]` |
| `test_real_flow_case_frontend_prepara_proposes_profile` | nuovo | La sonda dà `paths = ["**/*.tsx", "/web/**", "src/components/**"]`, `src/routes/home.tsx` trovato da `frontend` (marcatore TanStack), `backend` e `ai` «nessun file… non proposto». Con `SaveButton.tsx` e `web/app.js` aggiunti dal lavoro: stesso risultato |
| `DISALLOWED` e `risky` | `run-b1-flow.sh:100-112`, `:483-486` | non coprono `python3 -m http.server` (D2) |
| titolo `# Regole frontend (versione 1)` | `AREA_TITLES` (`flowreg.py:27`) esiste e contiene ai/infra/backend/base | si aggiunge |

### Task 8 e 9

Task 8 non ha test propri oltre a `test_committed_evidence_has_no_long_web_results` (verde sulle evidenze attuali). Task 9: S:1093 e S:1095 vanno riscritte (D10); l'elenco dei punti della rev 33 (P:334) copre 6.3, 7.1, 7.3, 8.7, 11.2, 11.4, 16 e la riga 33 della sezione 20; la sezione 6.3 oggi dice «a parità, il primo dichiarato» (S:483): con D3 è l'ordine alfabetico del nome del file a decidere, e va scritto.

## 4. La sonda della tabella delle precedenze (decisione 4)

### 4.1 P1-P36

Notazione: `/dir/**` è come `init` scrive una cartella alla radice (la sonda mostra `/server/**`, `/web/**`, `/prompts/**`, `/infra/**`, `/api/**`, `/functions/**`); le altre cartelle e i percorsi esatti non hanno la barra iniziale. «Proposta» = `paths` di ogni profilo da `init.profile_blocks` (un profilo assente non ha blocco); «Runtime» = `profiles.vertical_for` di ogni file, con i blocchi proposti messi in un `tollgate.toml` nell'ordine `ai`, `backend`, `frontend`, `infra`. Esito «come scritto» = identico alle colonne di P:66-101.

| Caso | Proposta (sonda) | Runtime (sonda) | Esito |
|---|---|---|---|
| P1 | `frontend`: `src/components/**` | `Button.tsx` → `frontend` | come scritto |
| P2 | `backend`: `/server/**`; `frontend` non proposto | tutti e due → `backend` | come scritto |
| P3 | `backend`: `/server/**`; `frontend`: `**/*.tsx` | `server/app.tsx` → `backend`; `src/main.tsx` → `frontend` | come scritto |
| P4 | `ai`: `src/ai/**`; `frontend`: `src/ai/components/**` | `Chat.tsx` → `frontend` | come scritto |
| P5 | `ai`: `src/ai/**`; `frontend` non proposto | `Chat.tsx` → `ai` | come scritto |
| P6 | `ai`: `src/ai/**`; `frontend`: `src/ai/components/**` | `Chat.tsx` e `Button.tsx` → `frontend` | come scritto |
| P7 | `backend`: `/api/**`; `frontend` non proposto | `og.tsx` → `backend` | come scritto |
| P8 | `backend`: `src/app/api/og/route.tsx`; `frontend`: `**/*.tsx` | `route.tsx` → `backend`; `page.tsx` → `frontend`. Senza il marcatore (`export const GET = …`) `route.tsx` → `frontend` (provato); un `route.ts` senza marcatore → generico | come scritto |
| P9 | `frontend`: `**/*.tsx`; `backend` non proposto | tutti e due → `frontend` | come scritto |
| P10 | `backend`: `src/routes/**`; `frontend`: `**/*.tsx` | tutti e tre → `backend` | come scritto |
| P11 | `frontend`: `**/*.tsx` | `api.ts` → nessuno; `Widget.tsx` → `frontend` | come scritto |
| P12 | `infra`: `web/vercel.json`; `frontend`: `/web/**` | `vercel.json` → `infra`; `index.css` → `frontend` | come scritto |
| P13 | `ai`: `/prompts/**`; `frontend`: `**/*.tsx` | `Card.tsx` → `ai` | come scritto |
| P14 | `frontend`: `**/*.tsx` (da `src/main.tsx`) | `index.tsx` sotto `supabase/` → `frontend` | come scritto |
| P15 | `backend`: `src/routes/**`; `frontend`: `**/*.svelte` | tutti e due → `backend` | come scritto |
| P16 | nessuna proposta | nessuno | come scritto |
| P17 | nessuna | nessuno | come scritto |
| P18 | nessuna | `Foo.TSX` → nessuno (`globs.match` rispetta le maiuscole, provato) | come scritto |
| P19 | `frontend`: `**/*.tsx` | `home.tsx` → `frontend`; `app/routes.ts` → nessuno | come scritto (il fatto sui moduli di React Router 7 non si verifica da qui) |
| P20 | `ai`: `src/ai/**`; `frontend`: `src/ai/components/**` | `retriever.py` → `frontend` | come scritto |
| P21 | `infra`: `/infra/**`; `frontend` non proposto | tutti e due → `infra`. **Senza `exclude`** (provato): `frontend` propone `infra/components/**` e `vpc.ts` → `frontend` | come scritto |
| P22 | `backend`: `/server/**`; `frontend` non proposto (anche con `server/entry.ts` forzato nel `detected` di `frontend`: P22b) | tutti e due → `backend`. **Senza `exclude`** (provato): `frontend` propone `server/entry.ts` e `entry.ts` → `frontend` | come scritto |
| P23 | `frontend`: `**/*.tsx`, `app/routes/api.users.ts` | tutti e due → `frontend` | come scritto |
| P24 | `frontend`: `**/*.tsx` | `hello.tsx` → `frontend` | come scritto |
| P25 | `ai`: `src/ai/**`; `frontend`: `**/*.tsx`; `backend` non proposto | `chat.tsx` → `ai` | come scritto |
| P26 | `ai`: `src/ai/**`; `frontend`: `src/ai/routes/chat.ts` | `chat.ts` → `frontend` | come scritto |
| P27 | `ai`: `src/ai/**`; `backend`: `src/ai/routes/**`; `frontend`: `**/*.tsx` | `chat.tsx` → `backend` | come scritto |
| P28 | `ai`: `src/components/ai/**`; `frontend`: `src/components/**` | `ChatBubble.tsx` → `ai`; `Button.tsx` → `frontend` | come scritto |
| P29 | `backend`: `src/components/routes/**`; `frontend`: `src/components/**` | `Nav.tsx` → `backend` | come scritto |
| P30 | `ai`: `src/components/Chat.tsx`; `frontend`: `src/components/**` | `Chat.tsx` → `ai`; `Button.tsx` → `frontend` | come scritto |
| P31 | `ai`: `src/app/agents/**`; `frontend`: `**/*.tsx` | `agents/page.tsx` → `ai`; `page.tsx` → `frontend` | come scritto |
| P32 | `backend`: `src/routes/**`; `frontend`: `**/*.tsx` | tutti e due → `backend` | come scritto |
| P33 | `backend`: `src/routes/**`; `frontend`: `**/*.css`, `**/*.tsx` | tutti e due → `backend` | come scritto |
| P34 | `backend`: `src/routes/**`; `frontend`: `**/*.tsx`, `src/routes/api.ts` | `api.ts` → `frontend`; `index.tsx` → `backend` | come scritto |
| P35 | `frontend`: `/web/**` | `index.html` e `api.ts` → `frontend` | come scritto |
| P36 | `frontend`: `**/*.css`, `**/*.tsx` | tutti e sei → `frontend` | come scritto |

**Nessun caso con esito diverso: 36 su 36 come scritti.** Nessun caso diverso tocca una scelta dell'utente (progetto 12 o 13). Il rimedio per `routes/` (progetto 13) regge nei tre punti che lo provano: P9 (nessun `backend`), P10 (resta `backend` con un solo file senza import), P34 (il file con tutti e due i marcatori).

### 4.2 Casi che la tabella non ha (lezione di I-1 di B5)

| Caso | File | Proposta (sonda) | Runtime (sonda) | Giudizio |
|---|---|---|---|---|
| **XA** | `src/lib/server.ts` con `from "react-router"` **e** `from 'express'` (fuori da ogni cartella) | `backend`: `src/lib/server.ts`; `frontend`: `src/lib/server.ts` (lo stesso percorso esatto in due profili) | → `backend` | **D3 (B)**: a parità (3 segmenti letterali contro 3) vince il primo dichiarato, che con l'ordine di `profile_blocks` è l'ordine alfabetico del nome del file: `backend` prima di `frontend`. In P34 lo stesso file in una cartella `routes/` va a `frontend`; fuori da una cartella va a `backend`. Con `frontend` dichiarato prima nel `tollgate.toml` dell'utente, l'esito si inverte. Con in più `src/main.tsx`: `frontend`: `**/*.tsx` e `src/lib/server.ts`, stesso runtime |
| **XC** | `src/components/Form/Form.tsx`, `src/components/Form/handlers/onSubmit.ts` | `backend`: `src/components/Form/handlers/**`; `frontend`: `src/components/**` | `onSubmit.ts` → `backend` | **D4 (B)**: stesso meccanismo di P29 con `handlers/`, molto più comune in codice d'interfaccia di `routes/`. P:103 nomina `handlers/` ma senza caso né voce nella pagina (P:253). Anche `src/handlers/onClick.ts` (XC2) → `backend`, `src/App.tsx` → `frontend` |
| **XB** | `web/routes/home.tsx` (import), `web/routes/loader.ts` (nessun marcatore) | `backend`: `web/routes/**`; `frontend`: `/web/**` | tutti e due → `backend` | Come P10, sotto `web/`; con tutti i moduli che importano (XB2) solo `frontend` `/web/**`. Nessun difetto, ma una variante in più da citare |
| **XD** | `docs/assets/site.css` (un sito di documentazione), `.github/pages/x.css` | `frontend`: `**/*.css` | → `frontend` | **D5 (B)**: `.html` è tenuto fuori perché accenderebbe troppo (P:61), ma `**/*.css` e `**/*.scss` accendono per un `.css` generato (Sphinx `_static`, MkDocs, rapporti di copertura committati) un repo che non ha interfaccia: la proposta compare in progetti di sola API o di documentazione. È solo una proposta; il profilo conta nei lavori L1 e L2 |
| XE | `src/hooks/useNav.ts` con `from 'react-router-dom'`, `src/main.tsx` | `frontend`: `**/*.tsx`, `src/hooks/useNav.ts` | → `frontend` | È il costo già scritto (P:104, decisione 5): confermato |
| XF | `web/Dockerfile`, `web/index.html` | `infra`: `web/Dockerfile`; `frontend`: `/web/**` | `Dockerfile` → `infra` | Come P12 |
| XG | `functions/Hero.tsx`, `src/main.tsx` | `backend`: `/functions/**`; `frontend`: `**/*.tsx` | `Hero.tsx` → `backend` | Come P3 |
| XI | `prompts/a.txt`, `prompts/style.css` | `ai`: `/prompts/**`; `frontend`: `**/*.css` | tutti e due → `ai` | Come P13 |
| XJ | `server/app.py`, `server/views/A.vue` | `backend`: `/server/**` | tutti e due → `backend` | Come P2 |
| XK | `src/pages/api/x.ts` (`export async function GET(`), `src/pages/index.astro` | `backend`: `src/pages/api/x.ts`; `frontend`: `**/*.astro` | `x.ts` → `backend`; `index.astro` → `frontend` | Come P8 |
| XM | `src/llm/Panel.tsx`, `src/llm/chat.py` | `ai`: `src/llm/**`; `frontend`: `**/*.tsx` | → `ai` | Come P13 |

Altre sonde: lo stato dichiarato (`_drift`): con `[profiles.frontend] paths = ["src/components/**"]` e i nuovi `src/main.css` e `src/x.tsx` dà `paths: aggiungi "**/*.css" (1 file)` e `paths: aggiungi "**/*.tsx" (1 file)`, più le righe `rules` e `blocking_rules` mancanti. L'intero `git ls-files` del worktree (10670 file, con `detected` calcolato sul contenuto vero): `frontend` «nessun file del repo corrisponde ai suoi percorsi: non proposto»; `ai`, `backend`, `infra` propongono le stesse cose di B5 (solo cartelle `spikes/`).

## 5. I punti da guardare apposta, uno per uno

1. **Forma `ext` contro i chiamanti.** `fragments.parse_pattern` ha un solo chiamante (`fragments.py:86`); `Pattern.kind` è letto solo da `init._match` (`init.py:223-232`). `concrete_for` (`:236`) e `_concrete_paths` (`:245`) sono chiamati da `profile_blocks` (`:376`, `:386`) e da `_drift` (`:340`); `detect_files` (`:270`) non guarda i pattern, usa `exclude` con `_is_detectable`; `_drift` e `exclude` trattano la forma come le altre (sonda: `_drift` con `**/*.css`). Test che oggi si aspettano un rifiuto: `test_fragments.py:93-99` (`test_load_rejects_other_pattern_forms`, solo `**/*.sql`), `:182-188` (`test_parse_pattern_rejects`, `**/*.sql`, `**/*.json`, `**/*.Dockerfile`; tutti gli altri rifiuti restano). In `test_init.py` non c'è nessun test che si aspetti un rifiuto di un pattern con `*` iniziale (`grep` di `FragmentError`, `parse_pattern`, `**/*`: nessun risultato). Altrove `**/*.<ext>` compare solo in `test_b1_scripts.py:249`, `test_size.py:22`, `test_testguard.py:6`, `test_init.py:1428`, che non riguardano i frammenti. **Esito:** coerente, salvo D6 (la formula del piano e il commento di `fragments.py:33`).
2. **Tabella delle precedenze.** 36 su 36 come scritta (sezione 4.1). Nessun caso su una scelta dell'utente con esito diverso.
3. **Nove pattern e marcatori contro gli alberi.** I quattro alberi di `test_real_trees_light_no_profile` (5, 14, 139, 278 file; estensioni solo `py`, `yml`, `md`, `json`, `toml`) non accendono `frontend` (`text == ""`, nessuna riga «proposto con»). `ModeTest`, `FilesTest`, `ServicesTest`, `HintsTest`, `UpdateTest`, `ProtectScriptTest` spingono solo file di `DEFAULT_FILES`/`GATE_FILES`/`package.json`/`.github/workflows/ci.yml`/`tollgate.toml`/`tools/junit_fake.py` e alberi di installazione: nessun `.tsx`, `.jsx`, `.vue`, `.svelte`, `.astro`, `.css`, `.scss`, nessuna cartella `components/` o `web/` (`grep` di `test_init.py`, `flowkit.py`, `hookkit.py`). I test di `test_init.py` che usano `web/**` (riga 1105), `apps/web/vercel.json` (1053, 1133) e `src/x.vue` (1335) lavorano con frammenti finti (`FRAGMENT_X`) e non leggono `templates/profiles/`: non cambiano. `install.files(ROOT)` copia 139 file `.py`/`.yml`: nessuno acceso. **Esito:** nessun albero da cambiare (decisione 17 confermata).
4. **Marcatori contro `bin/` e `spikes/b1`-`b5/flow/`.** `git grep -F` di `@tanstack/react-router`, `react-router`, `@remix-run/react` su `bin spikes evals hooks gate templates agents skills statusline tests`: 0 occorrenze (solo il piano le nomina). `test_real_markers_not_in_tollgate_bin` regge; nessun file di `spikes/b1`-`b5/flow` o di `evals/` è acceso da pattern o marcatori (sonda sull'intero albero tracciato). Nessun file tracciato ha estensione `tsx jsx vue svelte astro css scss` (solo `.html` di `docs/verifiche/evidenze/eval-p5/`, fuori dai pattern).
5. **`flowreg` senza `SAVED_READERS`.** Sulle evidenze committate di B1-B5, P5, `gh`, `hook`: 424 `Bash`, 0 nominano `tool-results/`, 0 `tool_use_result.stderr` non vuoti, 0 nuove segnalazioni. `test_committed_evidence_has_no_long_web_results` resta verde. Lacune della regex: D1.
6. **`test_area_agents_name_area_rules` e frasi esatte contro `AREAS` con `frontend`.** Il test (`test_manifest.py:154`) pretende nel file skill righe `^Si giudica su: report$` (almeno una) e almeno una regola sul diff; per il revisore, esattamente una frase con «si giudicano sul report» e una con «si giudicano sul diff», «WebFetch», «dati non fidati», «senza modifiche», «si segnala una volta sola» nella sezione «Area `frontend`»; per l'implementatore esattamente una frase con «sul tuo report» che nomina le sole regole sul report (la frase sui programmi vietati non deve contenere «sul tuo report»). Le frasi esatte di `final-reviewer.md`/`finding-verifier.md` (`test_final_reviewers_leave_report_rules_of_areas`) vogliono `r-frontend-` nel testo minuscolo, oggi assente. **Esito:** coerente col piano; D7 per la `description`.
7. **`READONLY_TYPES` contro `readonly_agents`.** `hooks/run:56` e `config.py:76-80` hanno l'elenco con `reviewer-backend` e senza `reviewer-frontend`; il test (`test_wrapper.py:253`) confronta con `agents/` quelli senza `Edit`/`Write`/`NotebookEdit` e diventa rosso quando esiste `reviewer-frontend.md`. Il piano lo prevede (P:293). **Esito:** coerente.
8. **`run-b1-flow.sh` con `B1_FLOW_CASE=frontend`.** Contro i test esistenti (casi `b1`, `ai`, `infra`, `backend`: `test_b1_scripts.py:1167`, `:1509-1650`) il messaggio di `die` a riga 118 ("i valori ammessi sono b1, ai, infra e backend") cambia con `frontend`: i test `…_unknown_value_names_*` lo leggono. «`proponi_profilo` approva anche `rules-backend`» è impreciso. D8, D2.
9. **I nomi che il piano dichiara esistenti.** Esistono tutti: `test_parse_pattern_rejects` (`test_fragments.py:182`), `test_load_rejects_other_pattern_forms` (`:93`), `test_name_pattern_exact_paths` (`test_init.py:931`), `test_concrete_for_exclude_default_is_b4` (`:939`), `test_real_fragments_load` (`test_fragments.py:225`), `test_real_trees_light_no_profile` (`test_init.py:1143`), `ProfileBlocksTest` (`:699`), `RulesBackendTest` (`test_rules_backend.py:73`), `RulesBackendPageTest` (`:264`), `test_area_agents_derive_from_generic` (`test_manifest.py:124`), `test_area_agents_attribution` (`:149`), `test_area_agents_name_area_rules` (`:154`), `test_code_agents_preload_rules_base` (`:113`), `test_final_reviewers_leave_report_rules_of_areas` (`:214`), `test_readonly_list_matches_config_and_agents` (`test_wrapper.py:253`), `test_committed_evidence_has_no_long_web_results` (`test_b1_scripts.py:1113`), `test_togli_pagine_bash_reading_saved_copy` (`:1671`), `test_third_party_detects_bash_stdout` (`:1691`), `test_every_skill_documented` (`test_docs.py:79`), `src_repo` (`:504`), `_third_party` (`flowreg.py:340`), `_saved_copy` (`:297`), `_swap_saved` (`:309`), `SAVED_TOOLS` (`:30`), `SAVED_READERS` (`:33`), `SAVED_PATH` (`:32`), `PAGE_PLACEHOLDER` (`:34`). `fragments._SEGMENT` (`fragments.py:19`), `parse_pattern` (`:37`), `_parse` (`:55`); `init.EXCLUDED_PREFIXES` (`:37`), `SOURCE_EXTENSIONS` (`:43`), `DOC_EXTENSIONS` (`:40`), `TEST_NAMES` (`:46`), `TEST_DIRS` (`:45`), `_match` (`:213`), `concrete_for` (`:236`), `_concrete_paths` (`:245`), `detect_files` (`:270`), `profile_blocks` (`:352`), `_drift` (`:319`); `profiles.vertical_for` (`profiles.py:23`), `task_routing`; `globs.literal_segments` (`globs.py:34`), `match_any` (`:161`); `research.area_rules` (`research.py:64`), `enforced` (`:46`); `tests.test_rules_ai.rules` (`:62`, `rules(text, area="ai")`). **Non ancora esistenti, come previsto:** `test_existing_forms_unchanged`, `test_real_frontend_fragment_approved`, `test_real_exclude_matches_root_folders_of_other_fragments` e tutti i test nuovi.

## 6. Conflitti

### Gravità M

**D1 (M) — Task 2, il rilevatore «ogni `Bash` che nomina `tool-results/`» ha buchi e la frase «dalla parte sicura» non è vera.**
Dove: P:116 (decisione 16), P:183 (Step 3), `flowreg.py:32`, `:297-306`.
Cosa: `SAVED_PATH` vuole un carattere di `[\s'"=:(]` davanti al percorso e almeno un carattere dopo `tool-results/`. Provato (`_saved_copy` senza lettori, come il Task 2): `cat</x/tool-results/a.txt`, `jq .[0] </x/tool-results/a.json`, `cat 2>&1 </x/tool-results/a`, `echo x>/x/tool-results/a` → **nessuna copia salvata**, quindi il testo di terzi resterebbe nelle evidenze; `cat {/x/tool-results/a,b}` dà il nome `a,b}`; `curl -d @/x/tool-results/a` dà il nome giusto (perché `@` è di sola lettura qui, funziona per caso: dopo uno spazio). Inoltre `ls /x/tool-results/` e `ls /x/tool-results` non diventano un segnaposto, contro la frase di P:116 («un `ls …/tool-results/` diventa un segnaposto»): la regex vuole un nome dopo la barra.
Ruling proposto: nel Task 2 allargare i caratteri ammessi prima del percorso (aggiungere `<`, `>`, `,`, `{`, `[`, `@` a `[\s'"=:(]`) e togliere dalla decisione 16 la frase sull'`ls` (un elenco di directory non porta testo di terzi), con un test per `cat</x/tool-results/a.txt` e per `jq . < /x/tool-results/b.json`.
Costo se sbagliata: una `Bash` di quel tipo lascia nelle evidenze pubbliche il testo di una pagina di terzi; lo ferma solo la verifica a mano del Task 8, Step 2 (`grep` dei risultati che nominano `tool-results/`), che però cerca proprio il nome `tool-results/` e lo trova, quindi aggirabile, ma il punto del Task 2 è non contare su quella.

**D2 (M) — Task 7, la prova del profilo `frontend` non vieta né rileva `python3 -m http.server`.**
Dove: P:312, P:114 (decisione 15: «`DISALLOWED` vieta gli stessi programmi del caso `backend` più `vite`, `next`, `tsc`, `eslint`, `vitest`, `playwright`, `chromium`, `chromium-browser`, `google-chrome`, `firefox`»), `run-b1-flow.sh:100-112` e `:483-486`; regola del brief: «nessun server avviato su una porta (nemmeno `python3 -m http.server`)».
Cosa: la lista di divieti è per programma (`Bash(<p>:*)`, `Bash(*/<p>:*)`, `Bash(command <p>:*)`, `Bash(env <p>:*)`), e la regex di `registra` cerca gli stessi programmi in posizione di comando. Il lavoro è una pagina HTML: il modo naturale di «guardarla» è `python3 -m http.server`, che non è un programma della lista. L'agente `implementer-frontend` lo vieta solo nel testo (P:294); `comandi-rischiosi.txt` non lo segnalerebbe.
Ruling proposto: aggiungere a `DISALLOWED` per il caso `frontend` `Bash(python3 -m http.server:*)`, `Bash(python -m http.server:*)`, `Bash(*/python3 -m http.server:*)`, `Bash(command python3 -m http.server:*)`, e alla regex di `registra` il motivo `http\.server`; nel test `test_flow_disallows_ui_tools_frontend` e `test_real_registra_flags_ui_tools_frontend` un caso per `python3 -m http.server 8000`.
Costo se sbagliata: la prova reale può avviare un server su una porta locale (violazione di una cautela vincolante, rilevata solo a posteriori nello stream); nessun danno ai dati.

### Gravità B

**D3 (B) — un file con i marcatori di `backend` e di `frontend` fuori da una cartella `routes/` va a `backend` per ordine alfabetico (caso XA).** Dove: P:99 (P34), P:104 (decisione 5), S:483, `profiles.py:23-37`, `init.py:389-428`. Cosa: la sonda dà lo stesso percorso esatto in due profili e `vertical_for` sceglie il primo dichiarato, che per `init` è l'ordine alfabetico del nome del frammento (`backend` < `frontend`). P34 dice «il percorso esatto di `frontend` vince sul file di server» solo perché lì la cartella ha meno segmenti. Ruling: aggiungere XA come P37 (stesso test dei P1-P36), scrivere nella pagina «Da decidere tu» e nella rev 33 (6.3) che a parità vince l'ordine dei blocchi nel `tollgate.toml`, e che `init` li scrive in ordine alfabetico. Costo se sbagliata: la pagina promette `frontend` per quel file e `backend` lo prende; caso raro (un file con un import di server e uno di router).

**D4 (B) — `handlers/` d'interfaccia non ha un caso né una voce nella pagina (XC).** Dove: P:94 (P29), P:103, P:253. Cosa: `src/components/Form/handlers/onSubmit.ts` e `src/handlers/onClick.ts` vanno a `backend` (tre/due segmenti contro due/zero), stesso meccanismo di P29 per `routes/`, ma più frequente nel codice d'interfaccia. Ruling: aggiungere P38 (e la variante `web/routes/` come XB nella nota di P10) con test, e nominare `handlers/` accanto a `components/routes/` nella voce di «Da decidere tu» e in `test_page_brings_the_open_choices_to_the_user`. Costo se sbagliata: l'utente non sa che i gestori di eventi della sua interfaccia passano all'agente `backend`.

**D5 (B) — `**/*.css` e `**/*.scss` propongono `frontend` per un `.css` che non è un'interfaccia (XD).** Dove: P:61 (decisione 3: `.html` escluso perché accenderebbe troppo). Cosa: un repo di sola API con `docs/_static/custom.css` o un `.css` di copertura committato riceve la proposta `frontend` con `**/*.css`. Nessun danno (è una proposta che l'utente può rifiutare), ma l'argomento usato per `.html` vale in piccolo anche per i fogli di stile. Ruling: lasciare i pattern, aggiungere la voce a «Da decidere tu» («un `.css` in un sito di documentazione fa proporre `frontend`; togli `**/*.css` dal blocco se non ti serve»). Costo se sbagliata: proposta rumorosa nei repo senza interfaccia.

**D6 (B) — Task 1: formula dei test da aggiornare e commento del codice.** Dove: P:163, `test_fragments.py:94`, `:183-185`, `fragments.py:33`, `:88-90`. Cosa: `test_load_rejects_other_pattern_forms` rifiuta solo `**/*.sql`, non anche `.json` e `.Dockerfile`; il commento `# "folder" | "root_folder" | "name"` di `Pattern.kind` e il messaggio di `_parse` vanno aggiornati con la quarta forma (il test `test_ext_rejects_bad_forms` pretende il messaggio). Ruling: correggere la frase del piano; nel report del Task 1 elencare i due test con le righe e i valori che escono. Costo se sbagliata: un implementatore cerca valori che non ci sono e si ferma, o lascia il commento vecchio.

**D7 (B) — Task 6: la `description` dei due agenti deve contenere la parola intera `frontend`.** Dove: P:294 («`description` che dice l'area: componenti, pagine, stili, accessibilità»), `test_manifest.py:135` (`assertRegex(afm["description"], r"\b%s\b" % name.split("-")[1])`). Cosa: il piano non dice che la parola `frontend` deve comparire. Ruling: scriverlo nel Task 6, Step 3. Costo se sbagliata: un giro di correzione.

**D8 (B) — Task 7: punti dello script e dei test non elencati.** Dove: P:312, `run-b1-flow.sh:10-17, 48, 52-54, 73-93, 108-111, 118-119, 180-184, 213-223, 421-431, 472-483`, `test_b1_scripts.py:504-520, 1509-1650`. Cosa: il caso `frontend` tocca 12 punti dello script: il commento di riga 10-17, il valore predefinito e `OUT` (48-54), il blocco `PROJ`/`PROJ_FILES`/`PROFILE_AREA`/`PROFILE_FILE` (87-93), `DEPLOY_CLIS` (110) e il `for` dei divieti (111), il `case` dei valori ammessi (118) e il suo messaggio, il testo di `controlla` (180-184), `data["api_status"]` in `scrivi_dati_gh` (223: `case in ("ai","infra","backend")`; senza, `init` non riesce a determinare la modalità), i testi di `scrivi_limiti` (421-431) e la regex `risky` (483). `src_repo` (`:519`) ha un dizionario `{"ai":…,"infra":…,"backend":…}[case]` che dà `KeyError` per `frontend` e la tupla `parts` (`:512-513`) senza `skills/rules-frontend`. L'espressione «`proponi_profilo` approva anche `rules-backend`» (P:312) è imprecisa: la funzione non approva nulla; `rules-backend` risulta approvata perché è così su `main`. Ruling: elencare questi punti nel brief dell'implementatore del Task 7 e correggere la frase. Costo se sbagliata: un caso `frontend` incompleto, scoperto dai test o dalla prova reale.

**D9 (B) — R-FRONTEND-10: la fonte citata non dice «Esc».** Dove: P:231. Cosa: i criteri 2.4.3 (Focus Order) e 2.1.2 (No Keyboard Trap) non prescrivono la chiusura con Esc (viene dai modelli di dialogo di WAI-ARIA); il verificatore del Task 4 lo troverà `no`. Il piano ha già «da verificare nello Step 0, punto (c)». Ruling: nessuna ora; se esce, la regola perde la parte su Esc o cita la fonte giusta. Costo: una regola in meno o riscritta.

**D10 (B) — Task 9, rev 33: due frasi della spec 11.2 diventano false.** Dove: S:1093 («`init` non propone i pattern del frammento così come sono»), S:1095 (la forma `name` «dopo e solo se nessuna forma a cartella ha acceso il file»), S:483 (a parità il primo dichiarato). Cosa: con `ext` la proposta contiene il pattern così com'è, e la nuova forma viene per ultima. Ruling: nominarle esplicitamente nel Step 1 del Task 9 (P:334). Costo se sbagliata: la spec dice una cosa e il codice un'altra.

Nessun conflitto con il progetto di B (sezioni 3.4, 4, 12, 13): la riga `frontend` di 3.4 è seguita da R-FRONTEND-01/02 (la via d'uscita per i progetti senza `package.json` è già dichiarata «scelta nostra»); L0 (B:134-136) è nel piano; `services/` al generico (B:207) è nella decisione 6; accessibilità dentro `rules-frontend` e rimedio per `routes/` (B:215-217) sono nelle decisioni 9 e 5, e la prova P9, P10, P34 li conferma.

## 7. Cosa porta al controller

- Prima di lanciare il Task 1: nessuna `Ruling:` obbligatoria. Conviene fissare D6 (una riga di correzione nel brief) e il piano di test come scritto.
- Prima del Task 2: D1 (la regex, con due test in più). Ruling consigliata: allargare i caratteri e togliere la frase sull'`ls`.
- Prima del Task 3: D3, D4, D5 come casi P37, P38 e voci in «Da decidere tu» (il Task 3 ha già la forma per i casi: costo di due test, `test_real_precedence_p37`, `…p38`). Non cambiano pattern, marcatori né `exclude`; non servono nuove sonde.
- Prima del Task 6: D7. Prima del Task 7: D2 e D8.
- Nessun conflitto A: nessun task è bloccato o ha un test rosso senza una ragione già scritta nel piano.
