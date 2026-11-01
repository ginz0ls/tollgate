# tollgate B3: infrastruttura dei profili e profilo `ai`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il primo profilo verticale vero, `ai`, con ciò che serve a tutti i profili: frammenti di profilo nel plugin, `init` che propone solo i profili approvati e presenti nel repo, le regole `rules-ai` scritte con le fonti ufficiali, verificate e approvate dall'utente, e gli agenti `implementer-ai` e `reviewer-ai` che le caricano.

**Architecture:** Ogni profilo del plugin è un frammento `templates/profiles/<area>.toml` (le chiavi del contratto 11.4 più i marcatori di contenuto per trovare il codice fuori dalle cartelle tipiche) accanto alla sua skill `skills/rules-<area>/SKILL.md`. `init --propose` e `init --update` leggono i frammenti, tengono solo quelli con la skill approvata (`approved`, come `rules-base`) e con file veri sul ramo predefinito, trasformano i pattern del frammento in percorsi concreti del repo, calcolano `rules` e `blocking_rules` dal testo della skill (mai a mano) e aggiungono il blocco `[profiles.<area>]` in coda al `tollgate.toml` proposto, senza toccare il resto. A runtime il nucleo non cambia: il profilo vive nel `tollgate.toml` del progetto. Gli agenti per area sono copie dichiarate dei generici con `skills: [rules-base, rules-<area>]` (precaricamento, fuori dal tetto di 3 e da `skills_required`).

**Tech Stack:** Python ≥ 3.11, solo libreria standard (`tomllib` in lettura; un piccolo scrittore TOML nostro per i valori semplici); bash; git; Claude Code (`claude plugin validate --strict`, che non lancia il modello; la prova reale con `claude -p --plugin-dir` solo dal controller). Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** il progetto approvato `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (l'autorità: «utente» non si discute, «mia scelta» si corregge solo con un motivo scritto qui), soprattutto le sezioni 2, 3.4 (riga `ai`), 3.6, 4 (riga `ai`), 5 e **9 (scelte dell'utente del 1° novembre 2026: regole sui modelli che cambiano, fornitori e framework, solo modelli stabili, sentinella in B3-bis)**; la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 28 (la 29 la scrive il Task 11): sezioni 6.3, 7.3, 11.2, 11.4, 18.4; il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, sezioni 1 (principio 7 e 1.7), 2 (riga `ai`), 2.1, 2.2, 2.3 e 4. Piano principale di B: `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, riga B3 della sezione 2, righe B1→B3-B7, B2→B3-B7 e B3→B4-B7 della sezione 3, rinvii «A B3-B7» della sezione 9. La sentinella dei modelli (progetto 9) **non** è in questo piano: è la fetta B3-bis.

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`; `tollgate_gate` importa dal nucleo solo `clock, paths, git, config, runner, diffcheck, ghcli`.
- **Nessuna operazione nuova in `apply._OPS`** (29, `test_ops_count_is_29`) e **nessun tipo nuovo in `events.EVENT_TYPES`** (33, `test_spec_event_types_match_registry`).
- **Nessuna rete**, né nei test né per i subagenti: le fonti delle regole sono **copie locali** messe dal controller nel workspace (Task 5, Step 0), che **non entrano mai in git** né nella copia del registro in `docs/sdd/` (sono pagine intere senza licenza aperta, e il repo è pubblico). Nessun `claude` vero nei test; `gh` è `tests/fakegh.py`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`, `~/.claude/projects/`.
- **Test con la radice del plugin esplicita** (piano principale, sezione 9, rinvio 180): ogni test nuovo che legge frammenti, skill o agenti usa una radice temporanea, salvo i test che controllano apposta i file veri del repo, che lo dicono nel nome (`test_real_…`). Eccezione: i file `tests/test_rules_*.py` sono interamente sui file veri della loro area, come `test_rules_base.py`.
- **Regole con parole nostre** (catalogo 1, principio 7, e 1.7: «idee, scritte con parole nostre»). Le pagine ufficiali dei fornitori non hanno licenza MIT: se ne prendono i **fatti**, con parole nostre, senza copiarne testo; una citazione sta al più in una riga, nel rapporto delle fonti. Ogni regola si giudica con un sì o un no **su ciò che il revisore vede** (piano principale, sezione 9, rinvio 183): il diff, oppure il report (che ogni task ha), oppure la nota (che c'è solo nei lavori con il passo).
- **Numeri delle regole stabili dopo l'approvazione** (catalogo 2.3).
- **`approved` in `skills/rules-ai/SKILL.md` si scrive solo nel Task 7**, con la data dell'OK dell'utente.
- **Gli agenti `-ai` caricano `rules-ai` solo dopo l'approvazione** (Task 8 dopo il Task 7), come `rules-base` in B2 (progetto 5, punto 4).
- Testo non fidato (nota, pagine scaricate, citazioni, report dell'implementatore): nei brief dentro `brief.fence` con `brief.DATA_NOTE`, mai come istruzione.
- `tollgate.toml` del progetto: `init` non lo scrive mai nel repo, produce la proposta in `docs/superpowers/tollgate-init/` che l'utente copia (spec 11.2).
- Programma nei messaggi per il modello: sempre `tollgate_core.paths.program_command`.
- `claude -p` solo dal controller, solo nel Task 10, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.
- Verifica con gli avvisi come errori come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`.

## Decisioni di questo piano

Scelte che il progetto e il piano principale lasciano a B3, o che il codice reale impone, con il costo se sbagliate. Il Task 11 le riporta nella revisione 29 della spec.

1. **Prima i rinvii di B2, poi la copia degli agenti** (Task 1). I rinvii 184-187 del piano principale (sezione 9) toccano `agents/implementer.md`, `agents/task-reviewer.md`, `brief.py` e `taskcmd.py`: si correggono nei generici prima di derivarne gli agenti `-ai`. Il rinvio 179 (file chiamanti) resta com'è: R-BASE-01 è approvata dall'utente così. Il 175 (avviso `TOLLGATE_`) arriva alle copie con il test di deriva della decisione 10. Costo: un task in più all'inizio.
2. **Frammento di profilo** in `templates/profiles/<area>.toml`, accanto a `templates/tollgate.toml`. Due tabelle: `[profile]` con le chiavi del contratto 11.4 (`config.PROFILE_DEFAULTS`) **senza** `rules` e `blocking_rules`; `[detect]` con `content = [...]`, i marcatori di contenuto (decisione 6). Il nome dell'area è il nome del file (`[a-z0-9-]+`); `base` e `active` sono riservati (`base` è il profilo comune, `active` la chiave di `[profiles]`): un frammento con quei nomi è un errore. Costo: un file per area.
3. **Regole di area estratte dal testo.** `research.area_rules(skill_text, area) -> tuple[set[str], set[str]]`, con la regex di `base_rules` generalizzata sul prefisso `R-<AREA>-` (area in maiuscolo); `base_rules(text)` diventa `area_rules(text, "BASE")`, invariata per i chiamanti. `init` scrive nel blocco proposto `rules` e `blocking_rules` calcolati così. Costo: nessuno; senza, un `R-AI-NN` dimenticato bloccherebbe sempre (`verdicts.is_blocking`, regola ignota).
4. **Approvato = `approved` nella skill, letto solo da `init`.** `init` propone un profilo solo se `research.enforced` è vero sul `skills/rules-<area>/SKILL.md` del plugin. A runtime non c'è un secondo interruttore: un progetto che ha copiato il profilo lo tiene finché non lo toglie. Costo: se l'utente ritira un'approvazione, i progetti che hanno già il profilo vanno aggiornati a mano.
5. **Percorsi concreti, non i pattern del frammento.** Il nucleo attiva i profili dai percorsi (spec 6.3), e `vertical_for` ignora le negazioni (`globs.match`, mentre `active_profiles` le applica): un `!.claude/**` aggiunto dall'utente farebbe andare instradamento e attivazione in direzioni opposte. Quindi `init` non propone i pattern del frammento così come sono. Si guardano solo i file tracciati **fuori dalle cartelle escluse** `init.EXCLUDED_PREFIXES = (".claude/", install.INSTALL_DIR + "/", "docs/superpowers/tollgate-init/")`, cioè gli agenti e le skill di progetto, la copia di tollgate che ogni progetto ha in `.github/tollgate/` e la cartella della proposta di `init`, che ne contiene un'altra copia. Per un pattern della forma `**/<cartella>/**` si propone, per ogni file che gli corrisponde, il pattern `<percorso fino alla prima cartella che corrisponde, compresa>/**` (per esempio `src/ai/**`, `ai/**`); un pattern già coperto da un altro proposto si toglie (con `src/ai/**`, `src/ai/agents/**` non serve). Fino a B4 un frammento accetta **solo** pattern della forma `**/<cartella>/**` (l'unica che serve ad `ai`): un'altra forma è una `FragmentError`, e la forma giusta per le altre (per esempio `**/*.sql`) la decide il piano della fetta che ne ha bisogno. Ogni percorso passa da `globs.escape` (un `app/[id]/` di Next.js resta letterale). Così gli agenti di progetto in `.claude/agents/` e i file di tollgate non accendono `ai`. Limite noto: `globs.literal_segments` conta come non letterale un segmento con `[` anche escapato, quindi un percorso così pesa un segmento in meno nella scelta del verticale (`vertical_for`); la proposta mostra comunque chi vince (decisione 7). Costo: una cartella nuova che nasce dopo la prima proposta non è coperta finché l'utente non applica la riga che `init --update` gli scrive (decisione 7).
6. **Codice AI fuori dalle cartelle tipiche** (progetto 3.6). `init` cerca i marcatori di `[detect] content` con **un solo** `git grep -I -l -F` sul ramo predefinito, **solo nei file sorgente** (estensioni `.py .ts .tsx .mts .cts .js .jsx .mjs .cjs .vue .svelte .go .rb .java .kt .rs .php .cs .swift`), esclusi `init.EXCLUDED_PREFIXES` (decisione 5), le cartelle `tests/`, `test/`, `__tests__/`, i file `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`, `conftest.py`, e i file oltre 256 KiB (le dimensioni da un solo `git ls-tree -r -l -z`); `-I` salta i binari. Manifesti (`package.json`), lockfile e documenti non sono file sorgente, quindi non entrano. Ogni file trovato e non coperto dai percorsi della decisione 5 entra con il suo percorso esatto (con `globs.escape`). Un marcatore è un pezzo di riga di import o di chiamata (il nome del pacchetto dell'SDK o del framework come compare nell'import, comprese le forme `npm:` ed `esm.sh` delle edge function di Supabase, oppure l'host dell'API per chi la chiama con `fetch`), mai il solo nome del fornitore. Se `git grep` supera il tetto di tempo, `init` prosegue senza rilevamento e lo dice in una riga, invece di fallire. Costo: un file nuovo che importa l'SDK dopo la prima proposta non è coperto finché l'utente non applica la riga di `init --update` (decisione 7); un marcatore troppo generico accenderebbe file sbagliati, per questo ogni marcatore passa dal verificatore delle fonti (Task 6).
7. **`init` e un `tollgate.toml` esistente.** I blocchi nuovi si **aggiungono in coda** al testo, senza riscriverlo: commenti e ordine dell'utente restano (le fini riga si normalizzano come già fa `with_mode`). Un profilo già dichiarato non si tocca; se esiste il suo frammento, `init` lo confronta con ciò che proporrebbe e scrive le righe esatte da cambiare, senza modificare il file: `rules` e `blocking_rules` contro quelli calcolati dalla skill (per esempio «`[profiles.ai] rules`: aggiungi `R-AI-09`»); i percorsi concreti e i file rilevati (decisioni 5 e 6) che nessun pattern dei `paths` dichiarati copre, segnalando un file solo se nessun pattern positivo dei `paths` lo copre **e** nessun pattern `!p` lo esclude (`globs.match_any` da solo non distingue i due casi), così una negazione dell'utente resta rispettata; la riga mostra il pattern nella forma TOML da copiare, scritta con `tomlout` (per esempio «`[profiles.ai] paths`: aggiungi `"packages/x/ai/**"` (3 file)»); `agent`, `reviewer` e `final_specialist` che mancano nel file e il cui agente ora esiste nel plugin (una chiave scritta vuota dall'utente, `agent = ""`, è una scelta e non dà righe). `[profiles] active` non si tocca; se contiene un'area che `init` sta per aggiungere, la proposta lo segnala (accenderebbe il profilo su ogni task). Per ogni profilo aggiunto la proposta mostra i percorsi proposti, al più 10 dei file che lo accendono con il totale, e i file che corrispondono anche a un verticale già dichiarato con chi vince (spec 6.3: «`init` mostra le sovrapposizioni sui file reali del repo»); le stesse cose vanno in una sezione «Profili proposti» del `README.md` della proposta, con come togliere un blocco prima di copiarlo. Queste righe compaiono anche quando il resto della proposta dice «nulla da aggiornare». Cambia il contratto di 11.2: il Task 11 lo scrive nella revisione 29. Costo: le regole nuove di un profilo già copiato arrivano solo se l'utente applica le righe.
8. **Scrittore TOML minimo** `tollgate_analysis/tomlout.py`: `table(name, values) -> str` per `str`, `bool`, `list[str]` e `dict[str, str]` (tabella in linea, per `commands`), con le stringhe in forma base TOML (virgolette doppie; escape di `\\`, `\"`, dei caratteri di controllo e di DEL) e le chiavi tra virgolette quando non sono chiavi semplici (`[A-Za-z0-9_-]+`). Un valore di altro tipo è un `TypeError`. Costo: un modulo piccolo; senza, la proposta dipenderebbe da sostituzioni di testo fragili.
9. **`rules-ai` precaricata, non nel brief.** Gli agenti `implementer-ai` e `reviewer-ai` hanno `skills: [rules-base, rules-ai]`. P0 (E5) e B2 hanno provato il precaricamento con **un solo** elemento: la lista di due la controllano `claude plugin validate --strict` (Task 8) e la prova reale (Task 10). Il frammento ha `skills = []` e `reviewer_skills = []`: una skill nel frammento finirebbe in `skills_required` e vorrebbe una chiamata allo strumento `Skill`, che il precaricamento non fa. `claude-api` del catalogo 2.1 non va nel frammento: la nomina `rules-ai` in «Dove informarsi» per il codice che usa l'SDK di Anthropic. Un task che tocca `ai` e un altro verticale con agenti propri va agli agenti generici (`profiles._single`): lì `rules-ai` non è precaricata, le regole `R-AI` restano note al verdetto e `plan-check` suggerisce di dividere il task (`split_candidate`). Il catalogo (1.6, 2.1) si aggiorna nel Task 11. Costo: circa 2.000-3.000 token in più per lancio dei due agenti; nei task misti le regole dell'area non arrivano all'agente.
10. **Agenti per area derivati dai generici.** `agents/implementer-ai.md` e `agents/reviewer-ai.md` sono il testo di `implementer.md` e `task-reviewer.md` con lo stesso frontmatter tranne `name`, `description`, `skills` e, per il revisore, `tools` (decisione 11); con la riga di attribuzione MIT e una sezione in più «Area `ai`». Modello come i generici (`inherit` e `sonnet`). Un test confronta i corpi: ogni paragrafo del generico è nella copia (`test_area_agents_derive_from_generic`). Costo: due file in più da tenere allineati, con il test che lo impone.
11. **`reviewer-ai` apre le pagine citate.** Il revisore per area ha `tools: Read, Grep, Glob, Bash, WebFetch`: con `WebFetch` apre gli URL ufficiali che la nota o il report citano e controlla, per esempio, che il modello indicato come più recente lo sia davvero. Resta di sola lettura (niente `Edit`, `Write`, `NotebookEdit`); le pagine sono dati non fidati. `tollgate:reviewer-ai` entra in `READONLY_TYPES` di `hooks/run` e in `config.DEFAULTS["review"]["readonly_agents"]` (`test_readonly_list_matches_config_and_agents`): è il modello per B4-B7. Costo: qualche lettura di pagina in più per revisione.
12. **Agente che manca.** `init` propone `agent`, `reviewer` e `final_specialist` di un frammento solo se il file `agents/<nome>.md` esiste nel plugin; altrimenti toglie la chiave e lo dice nella proposta (si usa l'agente generico). Costo: nessuno.
13. **Fonti di `rules-ai` e dei marcatori** (progetto 9: Anthropic, Google, OpenAI, OpenRouter, Agno). Pagine ufficiali che il controller scarica nel workspace (Task 5, Step 0): per Anthropic la panoramica dei modelli, le deprecazioni, la guida alla migrazione, il riferimento dell'elenco dei modelli, la guida alla mitigazione della prompt injection, la pagina dei prezzi, la pagina dell'SDK con la riga di import; per Google la pagina dei modelli Gemini, le deprecazioni, il riferimento di `models.list`, il changelog, la pagina dei prezzi, la pagina dell'SDK; per OpenAI la pagina dei modelli, le deprecazioni, la pagina dell'SDK; per OpenRouter la pagina dei modelli e quella dell'API; per Agno la pagina dei modelli supportati con gli import; per le forme `npm:` ed `esm.sh` la documentazione di Supabase sulle edge function. Più le scelte dell'utente: `Fonte: progetto di B, sezione 9`. Gli URL esatti li trova il controller e li scrive in `FONTI.md` con la data di consultazione e la licenza della pagina, se la pagina la dichiara. Costo: le pagine cambiano spesso; le regole citano la pagina e i fatti, e il rapporto delle fonti ha la data.
14. **`dod` e comandi di `ai` vuoti** (catalogo 2.3: «altri: nessuna voce in più»). `min_level = "L1"` (progetto 4). Pattern del frammento: `["**/llm/**", "**/prompts/**", "**/agents/**", "**/ai/**"]` (catalogo 2), trasformati come nella decisione 5. Costo: nessuno.
15. **Regole sul punto unico per B3-bis.** R-AI-01 chiede che il nome del modello stia in un solo punto, ma non ne fissa la forma: la sentinella di B3-bis dovrà sapere dove cercare, e quella forma la decide B3-bis (per esempio una chiave in `tollgate.toml` che nomina il file). Il Task 11 lo scrive tra i rinvii a B3-bis, insieme a `test_real_markers_not_in_tollgate_bin` (Task 6), che B3-bis dovrà adattare quando scriverà in `bin/` gli host delle API. Costo: nessuno qui.
16. **Prova reale corta** (Task 9 e 10). Un progetto di prova nuovo `spikes/b3/flow/` con `ai/`, un file `services/notify.py` fuori dalle cartelle che importa l'SDK di Anthropic (il progetto non lo installa: nessun test lo importa) e un `tollgate.toml` di base con il comando di verifica; `prepara` lancia `init --propose` sulla copia del plugin e committa il blocco proposto. Il lavoro L1 chiede di aggiungere in `ai/models.py` la costante del modello Claude per il riassunto di `ai/summary.py`. Si prova: profilo attivo, `implementer-ai` e `reviewer-ai` lanciati, `rules-ai` precaricata (trascrizioni dei subagenti, rinvio 181), rilievi `R-AI-…` noti al verdetto. Costo: circa 1 USD stimato sull'abbonamento.
17. **Unione anticipata.** Se l'utente rinvia l'approvazione, su `main` si possono unire solo i Task 1-4 (rinvii, estrattore, `init` con i frammenti e il rilevamento), che non portano regole né agenti; la bozza, la pagina e il frammento di `ai` restano sul ramo (progetto 5, punto 4). Costo: B3 resta aperta.

## Review Focus

1. **Profilo non approvato o senza file.** Con la skill senza `approved`, o con nessun file che corrisponde fuori da `.claude/` e da `.github/tollgate/`, `init` non propone il profilo, anche con `--update`, e lo dice; un profilo già copiato riceve le righe per i percorsi nuovi. Test: Task 3 `test_unapproved_profile_not_proposed`, `test_profile_without_files_not_proposed`, `test_claude_agents_do_not_light_ai`, `test_install_dir_does_not_light_profile`, `test_declared_profile_new_paths_reported`; Task 6 `test_real_markers_not_in_tollgate_bin`.
2. **`tollgate.toml` dell'utente rovinato.** Un file esistente con commenti, un profilo `ai` già dichiarato con regole vecchie, `--update` lanciato due volte: il testo dell'utente resta uguale salvo la riga `mode` e le fini riga, i blocchi nuovi sono in coda una volta sola, le righe sulla differenza delle regole compaiono anche quando il resto è «nulla da aggiornare». Test: Task 3 `test_update_appends_and_keeps_user_text`, `test_update_twice_no_duplicate`, `test_declared_profile_rules_drift_reported`.
3. **Regola ignota che blocca sempre, o regola che nessuno può soddisfare.** Ogni `R-AI-NN` della skill è in `rules` del blocco proposto e ogni `[blocca]` in `blocking_rules`; un `major` su una `R-AI` non `[blocca]` non ferma il task; in un lavoro senza passo (nessuna nota) ogni `R-AI` `[blocca]` si soddisfa con il diff o il report. Test: Task 2 `test_area_rules_*`; Task 3 `test_proposed_rules_match_skill`; Task 5 `test_blocking_rules_judged_on_diff_or_report`; Task 8 `test_ai_profile_non_blocking_rule_approves`, `test_ai_blocking_rule_without_step`.
4. **Codice AI fuori dalle cartelle, e falsi positivi.** Un `supabase/functions/x/index.ts` con `npm:@anthropic-ai/sdk` entra nei percorsi proposti; `package.json` con la dipendenza, un `README.md` con l'esempio di import, un test che finge l'SDK, un binario e un file oltre 256 KiB no. Test: Task 4 `test_detect_*`.
5. **Agenti per area che divergono o che non sono di sola lettura.** `reviewer-ai` è negli elenchi di sola lettura; le copie contengono ogni paragrafo dei generici; `rules-ai` non finisce in `skills_required`. Test: Task 8 `test_area_agents_derive_from_generic`, `test_readonly_list_matches_config_and_agents`, `test_rules_ai_not_required`.

## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `agents/implementer.md`, `agents/task-reviewer.md`, `bin/tollgate_analysis/brief.py`, `bin/tollgate_flow/taskcmd.py`; `tests/test_manifest.py`, `tests/test_brief.py`, `tests/test_taskcmd.py` | 1 | rinvii 184-187 di B2 |
| `bin/tollgate_analysis/research.py`, `bin/tollgate_analysis/tomlout.py`, `bin/tollgate_core/fragments.py`; `tests/test_research.py`, `tests/test_tomlout.py`, `tests/test_fragments.py` | 2 | regole di area, scrittore TOML, frammenti |
| `bin/tollgate_core/git.py`, `bin/tollgate_flow/init.py`, `skills/init/SKILL.md`, `docs/uso/comandi.md`; `tests/test_git.py`, `tests/test_init.py` | 3 | proposta dei profili dai percorsi |
| `bin/tollgate_flow/init.py`, `bin/tollgate_core/git.py`; `tests/test_init.py`, `tests/test_git.py` | 4 | rilevamento per contenuto |
| `skills/rules-ai/SKILL.md`, `templates/profiles/ai.toml`, `docs/uso/comandi.md`; `tests/test_rules_ai.py`, `tests/test_fragments.py` | 5, 6, 7 | regole e frammento di `ai` |
| `docs/profili/verifiche/ai-fonti.md`, `docs/profili/ai.md` | 6, 7 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-ai.md`, `agents/reviewer-ai.md`, `hooks/run`, `bin/tollgate_core/config.py`, `docs/uso/comandi.md` (`/tollgate:execute`); `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_check_task_verdict.py` | 8 | agenti per area; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `spikes/b3/flow/`; `tests/test_b1_scripts.py` | 9 | prova reale con il profilo `ai`: script e progetto |
| `docs/verifiche/2026-11-01-b3-prova-flusso.md`, `docs/verifiche/evidenze/b3/flusso/` | 10 | esecuzione, rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 11 | revisione 29 e stato |

---

### Task 1: Rinvii di B2 negli agenti generici e nel brief

**Files:**
- Modify: `agents/implementer.md`, `agents/task-reviewer.md` (riga ~53), `bin/tollgate_analysis/brief.py` (sezione del report in `review_brief`), `bin/tollgate_flow/taskcmd.py:278-281`
- Test: `tests/test_manifest.py`, `tests/test_brief.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Consumes: `brief.ReviewBrief` (campo `research`), la resa del report in `taskcmd` (B2).
- Produces: i testi dei generici che il Task 8 copia.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_implementer_reads_listed_files` (la sezione «Informati prima di scrivere» contiene «i file che elenchi nella nota aprili con `Read`»; rinvio 184); `test_implementer_fix_round_repeats_red_green` (il paragrafo del report dice che il report di un giro di correzione ripete il riscontro RED/GREEN del difetto corretto; rinvio 186).
  - `tests/test_brief.py`: `test_review_brief_no_research_says_base_rules_do_not_block` (`research=False`: la sezione del report contiene «in questo lavoro le regole `R-BASE-…` non bloccano»; con `research=True` la frase non c'è; rinvio 185).
  - `tests/test_taskcmd.py` (`ReviewDoneTest`, come gli altri test della classe): **`test_done_report_without_concerns_adds_none` (riga 653) si sostituisce** con `test_report_concerns_shown_with_done` (stato `DONE` con `concerns` non vuoto: il testo di `concerns` compare nella sezione del report), perché il rinvio 187 chiede il contrario di quel test; più `test_report_null_not_python_none` (un campo `null` del report non compare come `None`). Il test vecchio va tolto con questo motivo scritto nel report.
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_manifest tests.test_brief tests.test_taskcmd`: FAIL dei test nuovi.
- [ ] **Step 3: Il codice e i testi.** In `implementer.md` la riga del rinvio 184 e quella del 186 (nel paragrafo del report). In `brief.py`, con `research` falso, la frase del rinvio 185 nella sezione del report; in `task-reviewer.md`, accanto alla riga 53, la stessa indicazione per il revisore. In `taskcmd.py` `concerns` si esclude dalla resa del report solo quando la sezione dei dubbi c'è (`DONE_WITH_CONCERNS`), e un valore `None` si rende `null`.
- [ ] **Step 4: Verifica.** Gli stessi file di test: PASS (anche `test_implementer_tools`, `test_implementer_mentions_*`, `test_code_agents_preload_rules_base`). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: rinvii di B2 negli agenti generici e nel brief».

---

### Task 2: Regole di area, scrittore TOML e frammenti

**Files:**
- Modify: `bin/tollgate_analysis/research.py`
- Create: `bin/tollgate_analysis/tomlout.py`, `bin/tollgate_core/fragments.py`, `tests/test_tomlout.py`, `tests/test_fragments.py`
- Test: `tests/test_research.py`

**Interfaces:**
- Consumes: `research.enforced(text)`, `research.base_rules(text)`, `config.PROFILE_DEFAULTS`, `config.load_config_text(text)`.
- Produces:
  - `research.area_rules(skill_text: str, area: str) -> tuple[set[str], set[str]]`;
  - `tomlout.table(name: str, values: dict) -> str` (decisione 8);
  - `fragments.Fragment` (dataclass frozen: `area: str`, `profile: dict`, `detect: tuple[str, ...]`, `skill_path: Path`, `source: Path`);
  - `fragments.FragmentError(ValueError)` con il nome del file nel messaggio;
  - `fragments.load(plugin_root) -> list[Fragment]` (ordinati per `area`; cartella assente → `[]`; un frammento illeggibile, con un nome riservato o non valido, con chiavi fuori da `PROFILE_DEFAULTS`, o con `rules`/`blocking_rules` è una `FragmentError`);
  - `fragments.approved(fragment) -> bool` (`research.enforced` sul testo della skill; skill assente o illeggibile → `False`);
  - `fragments.rules(fragment) -> tuple[list[str], list[str]]` (ordinati, da `area_rules`).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_research.py`: `test_area_rules_extracts_prefix` (un testo con `R-AI-01 [blocca] …`, `R-AI-02 …` e una riga `R-BASE-01 …` → `({"R-AI-01","R-AI-02"}, {"R-AI-01"})` per `area="ai"`); `test_area_rules_ignores_inline_mentions` (un id citato a metà riga non conta); `test_real_base_rules_unchanged` (`base_rules(t) == area_rules(t, "BASE")` sul testo vero di `skills/rules-base/SKILL.md`).
  - `tests/test_tomlout.py`: `test_round_trip` (un dizionario con stringhe con `"`, `\`, a capo, tabulazione, DEL e accenti, un `bool`, una lista di stringhe vuota e piena, un `dict` di stringhe con una chiave `lint:fix` → `tomllib.loads(table("profiles.ai", d))["profiles"]["ai"] == d`); `test_rejects_other_types` (`int`, `float`, `None`, lista di numeri → `TypeError`).
  - `tests/test_fragments.py` (radice temporanea): `test_load_reads_profile_and_detect`; `test_load_missing_dir_is_empty`; `test_load_rejects_unknown_key`; `test_load_rejects_rules_in_fragment`; `test_load_rejects_reserved_names` (`base.toml`, `active.toml`); `test_load_rejects_other_pattern_forms` (un pattern che non è `**/<cartella>/**` → `FragmentError`, decisione 5); `test_load_rejects_unreadable` (TOML non valido → `FragmentError` col nome del file); `test_approved_needs_approved_skill` (skill assente, senza `approved`, con `approved: 2026-11-01`); `test_rules_from_skill`; `test_fragment_profile_validates` (il `[profile]` con le `rules` calcolate, scritto con `tomlout.table` in `[profiles.x]`, passa `config.load_config_text` senza avvisi).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `area_rules` con la regex `^(R-<AREA>-\d{2})( \[blocca\])? \S` (`<AREA>` = `re.escape(area.upper())`); `base_rules` la chiama. `tomlout` per la decisione 8. `fragments` in `tollgate_core` (legge file del plugin; importa `tollgate_analysis.research` e `config`), con `skill_path = plugin_root / "skills" / f"rules-{area}" / "SKILL.md"`.
- [ ] **Step 4: Verifica.** I file di test: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: regole di area dal testo, scrittore TOML e frammenti di profilo».

---

### Task 3: `init` propone i profili approvati e presenti (percorsi)

**Files:**
- Modify: `bin/tollgate_core/git.py`, `bin/tollgate_flow/init.py` (`propose` e la scrittura del `README.md`), `skills/init/SKILL.md` (passo 4: riferire la sezione «Profili proposti»), `docs/uso/comandi.md` (sezione di `/tollgate:init`)
- Test: `tests/test_git.py`, `tests/test_init.py`

**Interfaces:**
- Consumes: `fragments.load/approved/rules` e `tomlout.table` (Task 2); `globs.match`, `globs.match_any`, `globs.escape`; `profiles.vertical_for`; `init.PLUGIN_ROOT`, `init.with_mode`.
- Produces:
  - `git.tree_sizes_at(repo, ref) -> dict[str, int]` (`git ls-tree -r -l -z <ref>`: percorso → dimensione in byte; i sottomoduli si saltano; riferimento assente → `{}`);
  - `init.EXCLUDED_PREFIXES: tuple[str, ...]` (decisione 5; una sola costante, usata anche dal Task 4);
  - `init.ProfileProposal` (dataclass frozen: `text: str` da aggiungere in coda, `lines: list[str]` per il terminale, `readme: str` per la sezione «Profili proposti»);
  - `init.profile_blocks(files: dict[str, int], current_text: str, plugin_root: Path, *, detected: dict[str, list[str]] | None = None) -> ProfileProposal` (pura sui dati: `files` da `tree_sizes_at`, `detected` per area dal Task 4);
  - `init.propose(..., profiles_root: Path | None = None)` (predefinito `PLUGIN_ROOT`; solo i frammenti e le skill vengono da lì, `install.files` resta su `PLUGIN_ROOT`).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_git.py`: `test_tree_sizes_at` (dimensioni vere di due file, uno in una sottocartella; riferimento assente → `{}`).
  - `tests/test_init.py`, diretti su `profile_blocks` con un plugin temporaneo che ha un frammento `x` (pattern `**/x/**`) e la sua skill: `test_approved_profile_with_files_proposed` (il testo ha `[profiles.x]` con `paths = ["src/x/**"]` per un file `src/x/a.py`, `rules` e `blocking_rules` uguali a quelli della skill; le righe nominano il file e il totale); `test_unapproved_profile_not_proposed`, `test_profile_without_files_not_proposed` (e le righe lo dicono); `test_claude_agents_do_not_light_ai` (con il solo `.claude/x/a.md` il profilo non entra); `test_install_dir_does_not_light_profile` (con il solo `.github/tollgate/bin/x/a.py` il profilo non entra); `test_concrete_paths_escaped` (`app/[id]/x/p.ts` → `app/\[id\]/x/**`, e quel pattern corrisponde al file con `globs.match`); `test_nested_dirs_first_match` (`src/x/lib/x/a.py` e `src/x/b.py` danno il solo `src/x/**`); `test_declared_profile_rules_drift_reported` (con `[profiles.x]` già nel testo e una regola in meno: nessun blocco, una riga «aggiungi R-X-02»); `test_declared_profile_new_paths_reported` (con `[profiles.x] paths = ["src/x/**"]` e un file nuovo `lib/x/a.py`: una riga «aggiungi a `paths`» con il pattern e il numero di file; un file escluso dall'utente con una negazione nei `paths` non compare); `test_declared_profile_agent_now_available` (blocco senza `agent`, agente ora presente nel plugin: una riga che lo propone); `test_declared_profile_same_rules_silent_ok`; `test_paths_shown_neutralized` (un nome di file con un carattere di controllo esce nelle righe passato da `init._plain` e nel README da `prbody.neutralize`); `test_active_lists_new_area_warned`; `test_overlap_with_declared_vertical_shown`; `test_missing_agent_dropped` (`agent = "tollgate:implementer-x"` senza `agents/implementer-x.md` nel plugin temporaneo: la chiave non c'è e le righe lo dicono); `test_proposed_rules_match_skill`; `test_proposal_validates` (`current_text + text` passa `config.load_config_text` senza avvisi).
  - `tests/test_init.py`, su `init.propose` nello stesso processo (lo stato e il gh finto come `InitCase`; `profiles_root` sul plugin temporaneo): `test_update_appends_and_keeps_user_text` (un `tollgate.toml` esistente con commenti: il testo proposto è l'originale, salvo la riga `mode`, più i blocchi in coda); `test_update_twice_no_duplicate` (applicata la prima proposta, una seconda `--update` non aggiunge blocchi); `test_drift_lines_survive_nothing_to_update` (con il resto invariato, l'uscita «nulla da aggiornare» contiene le righe sulla differenza delle regole e dei percorsi); `test_readme_lists_proposed_profiles`; `test_bad_fragment_refuses_init` (un frammento con TOML non valido: `code` diverso da 0 e il nome del file nelle righe).
  - I test esistenti di `tests/test_init.py` passano dalla CLI con la radice vera: né l'albero di `FlowLab` né l'albero installato che gli `UpdateTest` spingono (`install.files(ROOT, …)`, con `bin/` copiato in `.github/tollgate/`) hanno file che i frammenti veri accendono fuori dalle cartelle escluse. `test_real_trees_light_no_profile` (nuovo) lo controlla su entrambi, così l'esito non cambia dopo il Task 7.
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `tree_sizes_at` come sopra. `profile_blocks` per le decisioni 4, 5, 7 e 12: saltati i non approvati; i profili già dichiarati (cercati con `tomllib` su `current_text`) danno solo le righe della differenza (regole, percorsi, agenti: decisione 7); per gli altri i percorsi concreti della decisione 5, più `detected[area]`; un profilo senza percorsi non entra. Il testo di ogni blocco è una riga `# profilo <area> da templates/profiles/<area>.toml` seguita da `tomlout.table(f"profiles.{area}", …)`. In `propose` il testo si aggiunge dopo `with_mode`, le righe vanno in `InitResult.lines` anche nel ramo «nulla da aggiornare», la sezione nel `README.md`. Un `FragmentError` fa rifiutare `init` (`code` diverso da 0) con il nome del file.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_git tests.test_init`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: init propone i profili approvati e presenti nel repo».

---

### Task 4: Rilevamento del codice AI per contenuto

**Files:**
- Modify: `bin/tollgate_core/git.py`, `bin/tollgate_flow/init.py`
- Test: `tests/test_git.py`, `tests/test_init.py`

**Interfaces:**
- Consumes: `git.tree_sizes_at` e `init.profile_blocks(..., detected=…)` (Task 3); `Fragment.detect` (Task 2).
- Produces:
  - `git.grep_files_at(repo, ref, markers: list[str], pathspecs: list[str]) -> list[str]` (un solo `git grep -z -I -l -F -e <m> … <ref> -- <pathspecs>`, diviso su NUL come `ls_files_at`, percorsi senza il prefisso `<ref>:`; nessun risultato → `[]`; errore di git diverso da «nessun risultato» → `GitError`; tetto di tempo `GIT_TIMEOUT_S` di `_proc`);
  - `init.detect_files(repo, ref, fragments, sizes) -> dict[str, list[str]]` (per area, i file sorgente della decisione 6 che contengono un marcatore, ordinati).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_git.py`: `test_grep_files_at` (due marcatori, un file che ne ha uno, un binario con il marcatore escluso da `-I`, un pathspec che restringe, un nome accentato che esce non citato).
  - `tests/test_init.py`: `test_detect_adds_exact_paths` (`supabase/functions/notify/index.ts` con una riga `import Anthropic from "npm:@anthropic-ai/sdk"` entra nei percorsi del profilo col suo percorso esatto); `test_detect_skips_manifests_docs_and_tests` (`package.json` con la dipendenza, `README.md` con l'esempio, `tests/test_x.py`, `src/x.test.ts`, `src/x.spec.ts` e `conftest.py` che lo importano: fuori; `src/x.vue` e `src/y.mts` con l'import: dentro); `test_detect_skips_large_and_binary` (un sorgente oltre 256 KiB, e uno con un byte nullo nei primi 8000 byte: fuori); `test_detect_skips_excluded_prefixes` (`.claude/` e `.github/tollgate/`); `test_detect_file_already_covered_not_repeated`; `test_declared_profile_new_detected_file_reported` (profilo dichiarato, file nuovo con il marcatore fuori dai `paths`: una riga «aggiungi a `paths`»); `test_detect_timeout_warns` (`grep_files_at` che solleva `GitError` per il tempo: la proposta c'è, senza file rilevati, con la riga di avviso).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `grep_files_at` con `_proc` (stessi controlli di `_check_ref`); `detect_files` per la decisione 6: i pathspec sono le estensioni sorgente (forma `:(glob)**/*.py`), le esclusioni si applicano dopo, sui percorsi, insieme al tetto di 256 KiB letto da `sizes`. `propose` passa il risultato a `profile_blocks`.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_git tests.test_init`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: init trova il codice AI fuori dalle cartelle tipiche».

---

### Task 5: Bozza di `rules-ai` e frammento di `ai` con le fonti

**Files:**
- Create: `skills/rules-ai/SKILL.md`, `templates/profiles/ai.toml`, `tests/test_rules_ai.py`
- Modify: `docs/uso/comandi.md`
- Test: `tests/test_rules_ai.py`, `tests/test_docs.py`, `tests/test_fragments.py`

**Interfaces:**
- Consumes: le copie delle fonti in `<workspace>/fonti/ai/` (Step 0); `research.area_rules`, `research.enforced`; `fragments.load` (Task 2); `tests/test_rules_base.rules(text)` come modello.
- Produces: `skills/rules-ai/SKILL.md` nella forma di B2 (piano principale, sezione 3, riga B2→B3-B7), senza `approved`; `templates/profiles/ai.toml` (decisioni 2, 6, 9, 14); in `tests/test_rules_ai.py` la funzione `rules(text) -> list[tuple[str, bool, str, str, str]]` (`id`, `blocca`, testo, fonte, oggetto: `diff`, `report` o `nota`) per i Task 6 e 7.

- [ ] **Step 0 (controller): le fonti.** Copia in `<workspace>/fonti/ai/` le pagine della decisione 13 (una per file, nel formato che serve il sito), con `SHA256SUMS` e `FONTI.md` (per ogni file: URL, data di consultazione, licenza dichiarata dalla pagina o «non dichiarata»). Solo pagine ufficiali dei fornitori e dei framework. Nel brief dell'implementatore va il percorso di `fonti/ai/`.
- [ ] **Step 1: I test che falliscono.** In `tests/test_rules_ai.py`, sul modello di `RulesBaseTest`:
  - `test_frontmatter` (`name: rules-ai`, `description: Regole di tollgate per il codice che usa modelli AI: le caricano in automatico gli agenti dell'area ai, non serve invocarla.`, `version: 1`, **nessun `approved`**, `research.enforced(text)` falso; il Task 7 lo inverte);
  - `test_has_title` (`# Regole ai (versione 1)` subito dopo il frontmatter); `test_first_section_is_prima_di_scrivere`; `test_rule_ids_consecutive` (`R-AI-01`, …); `test_every_rule_has_a_source`; `test_every_rule_names_what_is_judged` (ogni regola dice se si giudica sul diff, sul report o sulla nota); `test_some_rules_block`; `test_at_most_150_lines`;
  - `test_blocking_rules_judged_on_diff_or_report` (nessuna regola `[blocca]` si giudica solo sulla nota: Review Focus 3, perché nei lavori senza passo la nota non c'è);
  - `test_user_choices_covered` (per ogni scelta del progetto 9 una regola con `Fonte: progetto di B, sezione 9`, cercata per id in una tabella del test, non per parole: rinvio 182);
  - `test_sources_section` (la sezione `## Fonti` nomina le pagine ufficiali di ogni fornitore della decisione 13 e dice che le regole ne riportano i fatti con parole nostre, senza testo copiato);
  - `test_fragment_matches_decisions` (`templates/profiles/ai.toml`: `kind = "vertical"`, `min_level = "L1"`, i quattro pattern della decisione 14, `skills = []`, `reviewer_skills = []`, `agent = "tollgate:implementer-ai"`, `reviewer = "tollgate:reviewer-ai"`, `dod = []`, `[detect] content` non vuoto e senza il solo nome di un fornitore);
  - in `tests/test_fragments.py`: `test_real_fragments_load` (`fragments.load(ROOT)` legge `ai` senza errori).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Scrivi le regole** dalle fonti, con parole tue: una riga di regola e una riga `Fonte:` ciascuna; sezioni «Prima di scrivere», «Mentre lavori», «Dove informarsi» (gli URL ufficiali per fornitore, e la skill `claude-api` per il codice che usa l'SDK di Anthropic), «Fonti». «Famiglia» si definisce per fornitore, con la fonte (per Anthropic la linea del modello dell'elenco ufficiale, per Gemini la variante, per OpenAI e OpenRouter quanto dicono le loro pagine dei modelli). Bozza da distillare (l'implementatore può dividere o unire, mai aggiungere obblighi senza fonte):

  | Id | Sezione | `[blocca]` | Cosa dice la regola | Si giudica su | Fonte |
  |---|---|---|---|---|---|
  | R-AI-01 | Prima di scrivere | sì | Il nome di un modello sta in un solo punto del codice (costante o configurazione); il resto del codice, test compresi, usa quel punto e non ripete il nome | diff | progetto 9 |
  | R-AI-02 | Prima di scrivere | sì | Accanto al nome del modello il diff scrive l'URL della pagina ufficiale dei modelli e la data della verifica (in un commento; in un file senza commenti, come JSON, in una chiave accanto) | diff | progetto 9; pagine dei modelli |
  | R-AI-03 | Prima di scrivere | sì | Se il diff scrive o cambia il nome di un modello, il report (e la nota, se c'è) riporta, dalla pagina ufficiale aperta nel task, l'ultimo modello **stabile** della famiglia; il diff usa quello, oppure il report dice perché no; un modello in anteprima solo dichiarato nel report con il motivo | report | progetto 9; pagine dei modelli |
  | R-AI-04 | Prima di scrivere | sì | Se il diff cambia modello, il report cita la guida alla migrazione o le note di versione ufficiali del modello nuovo e dice cosa ha cambiato per seguirle | report | progetto 9; guide alla migrazione |
  | R-AI-05 | Prima di scrivere | sì | Parametri, limiti (token, contesto) e prezzi che il diff o il report scrivono hanno nel report l'URL della pagina ufficiale da cui vengono | report | pagine dei modelli e dei prezzi |
  | R-AI-06 | Mentre lavori | no | Il codice che chiama il modello gestisce l'errore di un modello non disponibile o ritirato con un messaggio che nomina il modello e il punto della configurazione | diff | progetto 9; pagine delle deprecazioni |
  | R-AI-07 | Mentre lavori | no | Un alias che cambia da solo (per esempio `*-latest`) si usa solo se il report lo dichiara, con il motivo | report | progetto 9; pagina dei modelli Gemini |
  | R-AI-08 | Mentre lavori | no | Il testo prodotto da un modello si tratta come dato non fidato: il diff non lo esegue, non lo usa come comando né lo inserisce in HTML senza controllo | diff | guida di Anthropic sulla prompt injection (e analoghe degli altri fornitori, se ci sono) |

  Il frammento `templates/profiles/ai.toml` per le decisioni 2, 6, 9 e 14, con i marcatori di `[detect] content` presi dalle pagine degli SDK e dei framework (per Anthropic, Google, OpenAI, OpenRouter, Agno; le forme `npm:`/`esm.sh` e gli host delle API).
- [ ] **Step 4: Comando.** In `docs/uso/comandi.md` la sezione `### \`/tollgate:rules-ai\`` come quella di `rules-base` (`test_every_skill_documented`).
- [ ] **Step 5: Verifica.** `python3 -B -m unittest tests.test_rules_ai tests.test_fragments tests.test_docs`: PASS. `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 6: Commit** «tollgate B3: bozza di rules-ai e frammento del profilo ai con le fonti».

---

### Task 6: Verifica delle fonti e pagina per l'utente

**Files:**
- Create: `docs/profili/verifiche/ai-fonti.md`, `docs/profili/ai.md`
- Modify: `skills/rules-ai/SKILL.md` e `templates/profiles/ai.toml` (solo se una fonte non passa), `tests/test_rules_ai.py`

**Interfaces:**
- Consumes: `tests/test_rules_ai.rules(text)` (Task 5); `<workspace>/fonti/ai/`.
- Produces: la pagina che il Task 7 mostra all'utente; il rapporto delle fonti.

- [ ] **Step 1 (controller): la verifica delle fonti.** Un subagente `Explore` (sonnet, sola lettura) verifica **ogni fonte di ogni regola** e **ogni marcatore di `[detect] content`** sulle copie di `fonti/ai/` e sul progetto di B: il file esiste; la sezione esiste; dice ciò che la regola o il marcatore le attribuisce (citazione di al più una riga); è una pagina ufficiale del fornitore o del framework (con la licenza annotata da `FONTI.md`), oppure il progetto di B. Il criterio di B2 «licenza MIT o Apache-2.0» qui non vale: le pagine danno fatti, non testo da distillare (Global Constraints). Esito `ok` o `no` con il motivo. Il controller salva l'uscita in `<workspace>/task-6-fonti.md`.
- [ ] **Step 2: I test che falliscono** (da `RulesBasePageTest`, con i correttivi del rinvio 182): `test_sources_report_covers_every_rule`, `test_page_lists_every_rule` (anche «N.» uguale all'id tra parentesi), `test_page_blocca_matches_skill`, `test_page_explains_what_changes` (la pagina dice che il profilo si accende solo nei progetti dove `init` lo propone e l'utente lo copia, a partire da L1; quali cartelle e quali import lo accendono; che R-AI-01 guarda il solo diff; che «più recente» vuol dire ultimo modello stabile), `test_detect_markers_verified` (ogni marcatore del frammento ha una riga `ok` nel rapporto); `test_real_markers_not_in_tollgate_bin` (nessun marcatore del frammento vero compare nei file di `bin/`, che ogni progetto riceve in `.github/tollgate/`: difesa in più oltre all'esclusione della decisione 5).
- [ ] **Step 3: Le correzioni e i due file.** Escono le fonti `no` e le regole o i marcatori che restano senza fonte `ok`; le regole rimaste si rinumerano senza buchi. Rapporto e pagina come in B2 (tabella «N.», «In parole semplici», «Blocca?», «Da dove viene»; sezione «Regole tolte dalla verifica»; come rispondere), in parole semplici.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_rules_ai`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: fonti di rules-ai verificate e pagina per l'utente».

---

### Task 7: Approvazione dell'utente

**Files:**
- Modify: `skills/rules-ai/SKILL.md`, `docs/profili/ai.md`, `docs/profili/verifiche/ai-fonti.md` (solo con correzioni), `tests/test_rules_ai.py`, `tests/test_fragments.py`

**Interfaces:**
- Consumes: la pagina del Task 6; `fragments.approved` (Task 2).
- Produces: `approved: <AAAA-MM-GG>` in `skills/rules-ai/SKILL.md`; da qui `init` propone il profilo `ai`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Come in B2, Task 5, Step 1: la pagina nel terminale; approva, correggi o togli; ogni correzione è un giro di questo task, una regola nuova o con una fonte nuova ripassa dal verificatore. Fermata prevista.
- [ ] **Step 2: I test che falliscono.** `test_frontmatter` si inverte; `test_page_approval_date_matches_skill`; in `tests/test_fragments.py` `test_real_ai_fragment_approved`.
- [ ] **Step 3: L'approvazione.** `approved: <data>` dopo `version`; nella pagina «Approvata dall'utente il <data>.». `claude plugin validate --strict .`: uscita 0. `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde (`test_real_trees_light_no_profile` garantisce che i test di `init` dalla CLI non cambino esito).
- [ ] **Step 4: Commit** «tollgate B3: rules-ai approvata dall'utente».

---

### Task 8: Agenti `implementer-ai` e `reviewer-ai`

**Files:**
- Create: `agents/implementer-ai.md`, `agents/reviewer-ai.md`
- Modify: `hooks/run` (`READONLY_TYPES`), `bin/tollgate_core/config.py` (`DEFAULTS["review"]["readonly_agents"]`), `agents/final-reviewer.md` e `agents/finding-verifier.md` (una frase: le regole di un'area che si giudicano sul report sono del revisore del task, come per le `R-BASE`, rinvio 183), `docs/uso/comandi.md` (`/tollgate:execute`: gli agenti per area)
- Test: `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_check_task_verdict.py`

**Interfaces:**
- Consumes: `agents/implementer.md`, `agents/task-reviewer.md` dopo il Task 1; `skills/rules-ai/SKILL.md` approvata (Task 7); `init.profile_blocks` (Task 3) per il blocco di prova.
- Produces: i tipi `tollgate:implementer-ai` e `tollgate:reviewer-ai`.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_code_agents_preload_rules_base` include i due agenti nuovi, per loro con `skills` uguale a `[rules-base, rules-ai]`; `test_area_agents_derive_from_generic` (ogni paragrafo del corpo del generico, dopo la riga di attribuzione, è nella copia; `model` uguale; `tools` dell'implementatore uguale, del revisore uguale più `WebFetch`); `test_area_agents_attribution`; `test_area_agents_name_rules_ai` (la sezione «Area `ai`» nomina `rules-ai`, `R-AI-`, e quali regole si giudicano sul report); `test_final_reviewers_leave_report_rules_of_areas` (`final-reviewer.md` e `finding-verifier.md` dicono che le regole di area sul report sono del revisore del task).
  - `tests/test_taskcmd.py` (un `tollgate.toml` con il blocco `ai` scritto nel test con le regole di una skill finta, non i file veri): `test_ai_task_routed_to_area_agents` (un task che tocca `ai/x.py` ha `agent_type` `tollgate:implementer-ai` e `reviewer_type` `tollgate:reviewer-ai`); `test_rules_ai_not_required` (`skills_required` vuoto, «Skill da usare» senza `rules-ai`).
  - `tests/test_check_task_verdict.py` (stesso blocco): `test_ai_profile_blocking_rule_changes` (un `major` su una `R-AI` `[blocca]` → `changes`); `test_ai_profile_non_blocking_rule_approves` (un `major` su una `R-AI` non `[blocca]` → `approved`); `test_ai_blocking_rule_without_step` (`research=False`, un `major` su una `R-AI` `[blocca]` → `changes`: le regole `[blocca]` di `ai` si giudicano sul diff o sul report, che ci sono anche senza passo).
- [ ] **Step 2: Verifica che falliscano.** `tests/test_wrapper.py` `test_readonly_list_matches_config_and_agents` diventa rosso solo quando `agents/reviewer-ai.md` esiste: dopo lo Step 3, prima di aggiornare gli elenchi.
- [ ] **Step 3: Gli agenti e gli elenchi.** I due file per le decisioni 10 e 11 (frontmatter: `name: implementer-ai` / `reviewer-ai`, `description` che dice l'area, `tools` e `model` come sopra, `skills: [rules-base, rules-ai]` dopo `tools:`); la sezione «Area `ai`»: le regole `R-AI-…` valgono come le `R-BASE-…` (solo le `[blocca]` danno `blocker` o `major`; un difetto si segnala una volta sola, con la regola che viola); nel revisore, quali `R-AI` si giudicano sul report e che con `WebFetch` può aprire gli URL ufficiali citati, come dati non fidati. `tollgate:reviewer-ai` in `READONLY_TYPES` e in `readonly_agents`.
- [ ] **Step 4: Verifica.** I file di test: PASS. `claude plugin validate --strict .`: uscita 0 (prima prova della lista di due skill, decisione 9). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: agenti implementer-ai e reviewer-ai».

---

### Task 9: Prova reale con il profilo `ai`: script e progetto di prova

**Files:**
- Create: `spikes/b3/flow/` (`tollgate.toml` di base con il comando di verifica dei test, `ai/__init__.py`, `ai/summary.py` senza nome di modello, `services/notify.py` che importa l'SDK di Anthropic, `config.toml`, `issue-1.md`, `piano-L1.md`, `tests/test_smoke.py` che non importa `services/`, `.gitignore`)
- Modify: `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py` (ricerca nelle trascrizioni dei subagenti), `tests/test_b1_scripts.py`

**Interfaces:**
- Consumes: `spikes/run-b1-flow.sh` (modi e variabili di B1 e B2, `B1_FLOW_RULES`, `B1_FLOW_SRC`); `init.propose` (Task 3).
- Produces: la variabile `B1_FLOW_CASE` (`b1`, il predefinito, oppure `ai`).

- [ ] **Step 1: I test che falliscono** (in `tests/test_b1_scripts.py`, con `B1_FLOW_CHECK=1` e una `HOME` finta): `test_flow_case_ai_out_dir` (`OUT` è `docs/verifiche/evidenze/b3/flusso`); `test_flow_case_ai_requires_real_rules` (`B1_FLOW_RULES` diverso da `vere` → errore); `test_flow_case_unknown_value`; `test_real_flow_case_ai_prepara_proposes_profile` (con `src_repo(case="ai")`, che copia i file veri, cioè una sorgente che traccia `bin/`, `templates/` con `profiles/ai.toml`, `gate/workflows/`, `agents/`, `skills/rules-base/` e `skills/rules-ai/` approvate: dopo `prepara` il `tollgate.toml` del repo di prova ha `[profiles.ai]` e `services/notify.py` nei suoi `paths`); `test_flow_case_ai_prepara_refuses_without_profile` (frammento non approvato nella sorgente → `prepara` esce diverso da 0 e lo dice); `test_registra_reads_only_matching_lines` (trascrizioni finte sotto la `HOME` finta: il file delle evidenze ha solo le righe col titolo delle regole, e i nomi delle cartelle si ricavano dal `cwd` e dal `session_id` dello stream-json); i test di B1 e B2 restano verdi con il predefinito `b1`.
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Lo script.** Con `B1_FLOW_CASE=ai`: progetto da `spikes/b3/flow/`; `PLAN_SRC`, `PLAN_REL`, il titolo dell'issue nei dati del gh finto e i file controllati da `controlla` dipendono dal caso; nei dati del gh finto la risposta sulla protezione con la chiave che `tests/fakegh.py` usa alla lettera (`tests/fakegh.py:26`, come `tests/test_protection.py:7`), perché `init` determini la modalità. Ordine in `prepara`: i dati del gh finto con la risposta sulla protezione (lo `sha` per gli stati si aggiunge dopo, come oggi) → commit del progetto con il `tollgate.toml` di base → `git config remote.origin.url` e `insteadOf` come oggi (la protezione si legge da `{owner}/{repo}` dell'URL di `origin`) → push → `init --propose` sulla copia del plugin, con il gh finto nel `PATH` (o `TOLLGATE_GH`) e lo stato con la sentinella → copia di `docs/superpowers/tollgate-init/files/tollgate.toml` nel repo → secondo commit → push → rimozione della cartella della proposta (`start` avvisa se resta) → poi `sha`, stati e `plan-check` come oggi. `prepara` si ferma se il blocco `[profiles.ai]` manca o non copre `services/notify.py`. `registra` cerca `# Regole ai (versione 1)` e `# Regole di base (versione 1)` nelle trascrizioni dei subagenti delle sole due cartelle della prova (passo 1 dal checkout, passo 2 dal worktree), ricavate dal `cwd` e dal `session_id`, e salva solo le righe trovate (rinvio 181); raccoglie `agent_type` e `reviewer_type` del task. Lo script si prova solo con `bash -n`, `controlla` e i test.
- [ ] **Step 4: Verifica.** `bash -n spikes/run-b1-flow.sh`; `python3 -B -m unittest tests.test_b1_scripts`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: prova reale con il profilo ai, script e progetto di prova».

---

### Task 10: Prova reale: esecuzione e rapporto (controller)

**Files:**
- Create: `docs/verifiche/2026-11-01-b3-prova-flusso.md`, `docs/verifiche/evidenze/b3/flusso/`

- [ ] **Step 1 (controller): esecuzione.** `B1_FLOW_CASE=ai B1_FLOW_RULES=vere`: `prepara`, `passo1`, `passo2`, `registra`. Atteso: task 1 `done` con verdetto `approved`; `agent_type` `tollgate:implementer-ai`, `reviewer_type` `tollgate:reviewer-ai`; il titolo di `rules-ai` nelle trascrizioni di entrambi (prova della lista di due skill); nota valida prima della prima modifica; il diff con il nome del modello in un punto, URL e data; il report con l'ultimo modello stabile della famiglia. Un esito in più tentativi è «composito». Un difetto del prodotto scoperto qui è un giro del Task 9 (test che fallisce, correzione, `tests/run`), poi si ripete solo il passo interessato.
- [ ] **Step 2: Rapporto** `docs/verifiche/2026-11-01-b3-prova-flusso.md`: passi, tentativi, proposta di `init` (percorsi e file che hanno acceso il profilo), agenti lanciati, precaricamento visto, letture, nota, verdetto e rilievi `R-AI-…`, token e consumo stimato, limiti. Evidenze anonimizzate come in B2 (id di sessione, `/home/<utente>`, nome utente e host).
- [ ] **Step 3: Commit** «tollgate B3: prova reale corta con il profilo ai».

---

### Task 11: Prove, revisione 29 della spec, piano principale, catalogo

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 29), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento), `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`

- [ ] **Step 1: Revisione 29 della spec del nucleo.** 6.3 (agenti per area con `skills: [rules-base, rules-<area>]`, fuori dal tetto; task misti, decisione 9); 7.3 (revisori per area negli elenchi di sola lettura, con `WebFetch`); 11.2 (`init` propone i profili: decisioni 4-7 e 12; `propose(..., profiles_root)`); 11.4 (frammento `templates/profiles/<area>.toml`, `[detect] content`, nomi riservati, `rules` calcolate dalla skill); riga 29 della sezione 20.
- [ ] **Step 2: Catalogo.** 1.6 e 2.1, riga `ai`: `rules-ai` precaricata dagli agenti, nessuna skill nel frammento, `claude-api` in «Dove informarsi» (decisione 9); 1.7: le pagine ufficiali come fonte di fatti; sezione 2: i percorsi concreti e il rilevamento per contenuto; sezione 4: le fonti vere di `rules-ai`, con i fornitori del progetto 9; una nota per B4 e B6: `globs` non espande le graffe `{a,b}`, i percorsi del catalogo che le usano vanno scritti in più righe.
- [ ] **Step 3: Piano principale di B e progetto.** Stato in testa; riga B3 della sezione 2; sezione 3, riga B3→B4-B7 con i nomi reali (frammento, `fragments`, `area_rules`, `tomlout`, `init.profile_blocks`, `git.tree_sizes_at`, `git.grep_files_at`, agenti derivati con il test di deriva, elenchi di sola lettura); sezione 9: chiusi i rinvii 175, 178, 180-187 che B3 ha fatto, aperti quelli rimasti, il rinvio a B3-bis sulla forma del punto unico (decisione 15), più le righe «minor (deferred)» che riguardano B3-bis e B4-B7; una sezione «Prove di B3» con ogni riga della tabella «Copertura» e il test o l'evidenza che la prova. Nel progetto la riga di avanzamento: «B1, B2 e B3 eseguite».
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md
git commit -m "tollgate B3: prove, spec rev 29, piano principale di B, catalogo"
```

---

## Copertura: punti del progetto e del piano principale destinati a B3 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: primo gruppo di profili, `ai` | 5, 6, 7, 8 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `ai` | 5 (sezione «Dove informarsi»), 6 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 8 |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 6, 7; decisione 17 |
| Progetto 2, anti-obiettivo «fonti inventate» | 6 (verificatore di sola lettura), decisione 13 |
| Progetto 3.4, riga `ai` | 5 (R-AI-02, R-AI-05) |
| Progetto 3.6: codice AI fuori da `**/ai/**` | 4 (decisione 6); R-BASE-04 resta |
| Progetto 4, riga `ai`: L1, Gemini e gli altri fornitori dell'utente | 5 (frammento, «Dove informarsi»); decisioni 9, 13; progetto 9 (OpenAI, OpenRouter, Agno) |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 5, 6, 7; decisioni 4, 17 |
| Progetto 9: regole sui modelli che cambiano, modelli stabili | 5 (`test_user_choices_covered`, R-AI-03) |
| Progetto 9: sentinella dei modelli | **B3-bis** (fuori da questo piano); decisione 15 |
| Piano principale, sezione 2, riga B3: frammenti, `init`, `rules-ai`, agenti, percorsi, `dod` | 2, 3, 4, 5, 8; decisione 14 |
| Piano principale, sezione 3, B1→B3-B7: strumenti, paragrafo sulla nota | 8 (decisione 10, test di deriva) |
| Piano principale, sezione 3, B2→B3-B7: forma della regola, precaricamento o brief | 5; decisione 9 |
| Piano principale, sezione 3, B3→B4-B7: frammenti, `init`, agenti derivati | 2, 3, 4, 8; nomi reali nel Task 11 |
| Piano principale, sezione 9: rinvii 175 (test di deriva), 178 (agenti nuovi con `rules-base`), 180 (radice esplicita), 181 (precaricamento), 182 (test di pagina), 183 (regole sul visibile), 184-187 | 8; 8; Global Constraints; 9-10; 6; 5 e 8; 1 |
| Revisione della spec del nucleo | 11 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B (con la sezione 9), il piano principale, la spec rev 28, il catalogo, il codice di `main` e il modello di B2.

| Giro | Rilievi | Esito |
|---|---|---|
| 3 | N-1, N-2 chiusi; M-1..M-12 chiusi salvo M-2 e M-5 in parte; 7 minor nuovi (R3-1 negazioni e `match_any`; R3-2 chiave della protezione nel gh finto; R3-3 pattern di altra forma; R3-4 tetto di tempo di `git grep`; R3-5 test dei marcatori contro B3-bis; R3-6 righe in forma TOML e `agent = ""`; R3-7 cartella della proposta) | **«Pronto». Critical aperti: 0. Important aperti: 0.** Corretti comunque tutti i minor nuovi e la riga dei rinvii della Copertura |
| 2 | I-1…I-7, I-9, I-10 chiusi, I-8 in parte; 17 minor chiusi, 4 in parte; 2 important nuovi (N-1 un profilo già copiato non riceve mai i percorsi nuovi; N-2 i file di tollgate in `.github/tollgate/` entrano nel rilevamento e il test di protezione non guarda l'albero installato), 12 minor (M-1..M-12) | «Non pronto». Corretti: decisioni 5, 6, 7 (esclusioni con una sola costante, tutti i pattern in percorsi concreti, annidamenti, righe per percorsi e agenti dei profili dichiarati); Task 3, 4, 6, 8, 9 (test nuovi e rinominati, `git grep -z`, ordine di `prepara`); R-AI-01, 02, 03; eccezione per i test `test_rules_*.py` |
| 1 | 0 critical; 10 important (I-1 `ls_files_at` con pathspec vuoto; I-2 nessun modo di dare a `propose` un plugin temporaneo; I-3 `[blocca]` sulla nota insoddisfacibili senza passo; I-4 R-AI-03 non giudicabile; I-5 `**/agents/**` su `.claude/agents/`; I-6 marcatori con falsi positivi e negativi; I-7 regole del progetto ferme dopo un aggiornamento; I-8 `prepara` del Task 8 non fattibile così; I-9 altri fornitori dell'utente; I-10 test esistente rovesciato senza dirlo); 21 minor | «Non pronto». Due scelte portate all'utente (fornitori: OpenAI, OpenRouter, Agno; solo modelli stabili), scritte nel progetto 9. Corretti: decisioni 2, 5-9, 11-13, 15-17 nuove o riscritte; Task 1, 3, 4 (nuovo), 5, 6, 8, 9 (nuovo), 10; Review Focus; mappa dei file |
