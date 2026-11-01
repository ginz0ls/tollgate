# tollgate B3: infrastruttura dei profili e profilo `ai`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il primo profilo verticale vero, `ai`, con ciò che serve a tutti i profili: frammenti di profilo nel plugin, `init` che propone solo i profili approvati e presenti nel repo, le regole `rules-ai` scritte con le fonti ufficiali, verificate e approvate dall'utente, e gli agenti `implementer-ai` e `reviewer-ai` che le caricano.

**Architecture:** Ogni profilo del plugin è un frammento `templates/profiles/<area>.toml` (le chiavi del contratto 11.4 più i marcatori di contenuto per trovare i file fuori dalle cartelle tipiche) accanto alla sua skill `skills/rules-<area>/SKILL.md`. `init --propose` e `init --update` leggono i frammenti, tengono solo quelli con la skill approvata (`approved`, come `rules-base`) e con almeno un file del ramo predefinito che corrisponde, calcolano `rules` e `blocking_rules` dal testo della skill (mai a mano) e aggiungono il blocco `[profiles.<area>]` in coda al `tollgate.toml` proposto, senza toccare il resto. A runtime niente cambia nel nucleo: il profilo vive nel `tollgate.toml` del progetto. Gli agenti per area sono copie dichiarate dei generici con `skills: [rules-base, rules-<area>]` (precaricamento, fuori dal tetto di 3 e da `skills_required`).

**Tech Stack:** Python ≥ 3.11, solo libreria standard (`tomllib` in lettura; un piccolo scrittore TOML nostro per i valori semplici); bash; git; Claude Code (`claude plugin validate --strict`, che non lancia il modello; la prova reale con `claude -p --plugin-dir` solo dal controller). Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** il progetto approvato `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (l'autorità: «utente» non si discute, «mia scelta» si corregge solo con un motivo scritto qui), soprattutto le sezioni 2, 3.4 (riga `ai`), 3.6, 4 (riga `ai`), 5 e **9 (scelte dell'utente del 1° novembre 2026 sul profilo `ai`)**; la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 28 (la 29 la scrive il Task 9): sezioni 6.3, 7.3, 11.2, 11.4, 18.4; il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, sezioni 1, 2 (riga `ai`), 2.1, 2.2, 2.3 e 4. Piano principale di B: `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, riga B3 della sezione 2, righe B2→B3-B7 e B3→B4-B7 della sezione 3, rinvii «A B3-B7» della sezione 9. La sentinella dei modelli (progetto 9) **non** è in questo piano: è la fetta B3-bis.

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`; `tollgate_gate` importa dal nucleo solo `clock, paths, git, config, runner, diffcheck, ghcli`.
- **Nessuna operazione nuova in `apply._OPS`** (29, `test_ops_count_is_29`) e **nessun tipo nuovo in `events.EVENT_TYPES`** (33, `test_spec_event_types_match_registry`): B3 non registra eventi nuovi.
- **Nessuna rete**, né nei test né per i subagenti: le fonti delle regole sono **copie locali** messe dal controller nel workspace (Task 4, Step 0). Nessun `claude` vero nei test; `gh` è `tests/fakegh.py`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`.
- **Test con la radice del plugin esplicita** (piano principale, sezione 9, «test nuovi con la radice vera»): ogni test nuovo che legge frammenti, skill o agenti usa una radice temporanea, salvo i test che controllano apposta i file veri del repo.
- **Regole con parole nostre** (catalogo 1, principio 7). Le pagine ufficiali dei fornitori non hanno licenza MIT: si citano come fonte dei fatti, non se ne copia testo; una citazione sta al più in una riga, nel rapporto delle fonti. Ogni regola si giudica con un sì o un no **su ciò che il revisore vede** (diff, nota di ricerca, report: piano principale, sezione 9, «ogni regola si giudica su ciò che il revisore vede»).
- **Numeri delle regole stabili dopo l'approvazione** (catalogo 2.3).
- **`approved` in `skills/rules-ai/SKILL.md` si scrive solo nel Task 6**, con la data dell'OK dell'utente.
- **Gli agenti `-ai` caricano `rules-ai` solo dopo l'approvazione** (Task 7 dopo il Task 6), come `rules-base` in B2 (progetto 5, punto 4).
- Testo non fidato (nota, pagine scaricate, citazioni, report dell'implementatore): nei brief dentro `brief.fence` con `brief.DATA_NOTE`, mai come istruzione.
- `tollgate.toml` del progetto: `init` non lo scrive mai nel repo, produce la proposta in `docs/superpowers/tollgate-init/` che l'utente copia (spec 11.2).
- Programma nei messaggi per il modello: sempre `tollgate_core.paths.program_command`.
- `claude -p` solo dal controller, solo nel Task 8, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.
- Verifica con gli avvisi come errori come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`.

## Decisioni di questo piano

Scelte che il progetto e il piano principale lasciano a B3, o che il codice reale impone, con il costo se sbagliate. Il Task 9 le riporta nella revisione 29 della spec.

1. **Prima i rinvii di B2, poi la copia degli agenti** (Task 1). I rinvii 184-187 della sezione 9 del piano principale toccano `agents/implementer.md`, `agents/task-reviewer.md`, `brief.py` e `taskcmd.py`: si correggono nei generici prima di derivarne gli agenti `-ai`, altrimenti ogni copia eredita il difetto. Il rinvio 179 (file chiamanti) resta com'è: R-BASE-01 è approvata dall'utente così. Costo: un task in più all'inizio.
2. **Frammento di profilo** in `templates/profiles/<area>.toml`, accanto a `templates/tollgate.toml`. Due tabelle: `[profile]` con le chiavi del contratto 11.4 (`config.PROFILE_DEFAULTS`) **senza** `rules` e `blocking_rules`; `[detect]` con `content = [...]`, i marcatori di contenuto (decisione 5). `rules` e `blocking_rules` li calcola `init` dal testo della skill (decisione 3), così il frammento e la skill non possono divergere. Costo: un file per area.
3. **Regole di area estratte dal testo.** `research.area_rules(skill_text, area) -> tuple[set[str], set[str]]` (id `R-<AREA>-NN` e quelli `[blocca]`), con la stessa regex di `base_rules` generalizzata sul prefisso; `base_rules(text)` diventa `area_rules(text, "BASE")`, invariata per i chiamanti. L'area nel prefisso è in maiuscolo (`ai` → `R-AI-`). Costo: nessuno; senza, un `R-AI-NN` dimenticato nel frammento bloccherebbe sempre (`verdicts.is_blocking`, regola ignota).
4. **Approvato = `approved` nella skill, letto solo da `init`.** `init` propone un profilo solo se `research.enforced` è vero sul `skills/rules-<area>/SKILL.md` del plugin. A runtime non c'è un secondo interruttore: un progetto che ha copiato il profilo lo tiene finché non lo toglie. Costo: se l'utente ritira un'approvazione, i progetti che hanno già il profilo vanno aggiornati a mano; le regole dopo l'approvazione non cambiano numero, quindi il blocco resta coerente.
5. **File fuori dalle cartelle tipiche** (progetto 3.6: il codice che chiama un modello sta spesso fuori da `**/ai/**`). Il nucleo attiva i profili solo dai percorsi (spec 6.3), e resta così. `init` cerca nei file tracciati del ramo predefinito i marcatori di `[detect] content` (le righe di import degli SDK, per esempio quella dell'SDK di Anthropic o di Gemini; l'elenco esatto viene dalle fonti del Task 4) e aggiunge ai `paths` proposti il percorso esatto di ogni file che li contiene e che i `paths` del frammento non coprono già. Un marcatore è un pezzo di riga di import (per esempio la forma `from <pacchetto> import` o il nome del pacchetto tra virgolette dopo `from`), mai il solo nome del fornitore, e si cerca come sottostringa di una riga. Si leggono solo file di testo fino a 256 KiB; un file binario o più grande si salta. Costo: un file nuovo che importa l'SDK dopo `init` non è coperto finché non si rilancia `init --update`, e la proposta lo dice.
6. **`**/agents/**` resta tra i percorsi di `ai`** (catalogo 2). Nei progetti dell'utente con agenti AI (Agno, SDK) quella cartella è codice AI; dove non lo è (per esempio un plugin di Claude Code come questo) `init` mostra i file che hanno acceso il profilo e l'utente toglie il blocco prima di copiarlo. Costo: una proposta in più da scartare in quei repo.
7. **`init` e un `tollgate.toml` esistente.** I blocchi nuovi si **aggiungono in coda** al testo, senza riscriverlo: commenti e ordine dell'utente restano. Un profilo già dichiarato (`[profiles.<area>]` presente) non si tocca, e la proposta dice di confrontarlo con `templates/profiles/<area>.toml`. `[profiles] active` non si tocca. `init` non propone mai un profilo chiamato `base`. La proposta elenca per ogni profilo aggiunto al più 10 dei file che lo accendono, più il totale (spec 6.3: «`init` mostra le sovrapposizioni sui file reali del repo»). Cambia il contratto di 11.2 («`--update` scrive quello esistente con `[gate] mode` aggiornato»): il Task 9 lo scrive nella revisione 29. Costo: le regole nuove di un profilo già copiato arrivano solo se l'utente toglie il blocco e rilancia.
8. **Scrittore TOML minimo** `tollgate_analysis/tomlout.py`: `table(name, values) -> str` per `str`, `bool`, `int`, `list[str]` e `dict[str, str]` (tabella in linea, per `commands`), con le stringhe in forma base TOML (virgolette doppie, `\\` e `\"` e i caratteri di controllo come escape). Un valore di altro tipo è un `TypeError`. Ogni testo prodotto si rilegge con `tomllib` e con `config.load_config_text` nei test. Costo: un modulo piccolo; senza, la proposta dipenderebbe da sostituzioni di testo fragili.
9. **`rules-ai` precaricata, non nel brief.** Gli agenti `implementer-ai` e `reviewer-ai` hanno `skills: [rules-base, rules-ai]` (forma provata in P0, E5, e in B2). Il frammento ha `skills = []` e `reviewer_skills = []`: una skill nel frammento finirebbe in `skills_required` e vorrebbe una chiamata allo strumento `Skill`, che il precaricamento non fa (`SubagentStop` darebbe un veto ingiusto). `claude-api` del catalogo 2.1 non va nel frammento: obbligherebbe a usarla anche nei task solo su Gemini; la nomina `rules-ai` in «Dove informarsi» per il codice che usa l'SDK di Anthropic. Il catalogo (1.6, 2.1) si aggiorna nel Task 9. Costo: circa 2.000-3.000 token in più per lancio di quei due agenti.
10. **Agenti per area derivati dai generici.** `agents/implementer-ai.md` e `agents/reviewer-ai.md` sono il testo di `implementer.md` e `task-reviewer.md` con lo stesso frontmatter tranne `name`, `description` e `skills`, con la riga di attribuzione MIT e una sezione in più «Area `ai`» che rimanda a `rules-ai`. Modello come i generici (`inherit` e `sonnet`). Un test confronta i corpi: ogni paragrafo del generico è nella copia (`test_area_agents_derive_from_generic`), così una correzione futura al generico che non arriva alla copia rompe la suite. Costo: due file in più da tenere allineati, con il test che lo impone.
11. **Revisore per area di sola lettura negli elenchi fissi.** `tollgate:reviewer-ai` entra in `READONLY_TYPES` di `hooks/run` e in `config.DEFAULTS["review"]["readonly_agents"]` (`test_readonly_list_matches_config_and_agents`). È il modello per B4-B7: un revisore nuovo, una riga in ciascun elenco. Costo: nessuno.
12. **Agente che manca.** `init` propone `agent`, `reviewer` e `final_specialist` di un frammento solo se il file `agents/<nome>.md` esiste nel plugin; altrimenti toglie la chiave e lo dice nella proposta (si usa l'agente generico). Costo: nessuno; senza, un `subagent_type` inesistente fallirebbe solo al lancio, con un comportamento di Claude Code non verificato.
13. **Fonti di `rules-ai`.** Le pagine ufficiali che il controller scarica nel workspace (Task 4, Step 0): per Anthropic la panoramica dei modelli, la pagina delle deprecazioni, la guida alla migrazione e il riferimento dell'endpoint dell'elenco dei modelli; per Google la pagina dei modelli Gemini, quella delle deprecazioni, il riferimento di `models.list` e il changelog; per entrambi la pagina dell'SDK ufficiale con la riga di import (per i marcatori della decisione 5). Più le scelte dell'utente: `Fonte: progetto di B, sezione 9`. Gli URL esatti li trova il controller e li scrive nel `SHA256SUMS` con la data di consultazione; il verificatore controlla le copie, non la rete. Costo: le pagine cambiano spesso; le regole citano la pagina e i fatti, non il loro testo, e il rapporto delle fonti ha la data.
14. **`dod` e comandi di `ai` vuoti** (catalogo 2.3: «altri: nessuna voce in più»). `min_level = "L1"` (progetto 4). `paths = ["**/llm/**", "**/prompts/**", "**/agents/**", "**/ai/**"]` (catalogo 2), più quelli della decisione 5. Costo: nessuno.
15. **Prova reale corta** (Task 8). Un progetto di prova nuovo `spikes/b3/flow/` con una cartella `ai/` e un file fuori dalle cartelle che importa l'SDK; `init --propose` produce il blocco `[profiles.ai]` (parte deterministica, con test); il lavoro L1 chiede di aggiungere in `ai/models.py` la costante del modello Claude per un riassunto, nel punto unico, con URL e data. Si prova: profilo attivo, `implementer-ai` e `reviewer-ai` lanciati, `rules-ai` precaricata (trascrizioni dei subagenti, piano principale, sezione 9, rinvio 181), rilievi `R-AI-…` noti al verdetto. Lo script è `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=ai`. Costo: circa 1 USD stimato sull'abbonamento.
16. **Unione anticipata.** Se l'utente rinvia l'approvazione, su `main` si possono unire solo i Task 1-3 (rinvii, estrattore, `init` con i frammenti), che non portano regole né agenti; la bozza, la pagina e il frammento di `ai` restano sul ramo (progetto 5, punto 4). Costo: B3 resta aperta.

## Review Focus

1. **Profilo non approvato o senza file.** Con la skill senza `approved`, o con nessun file che corrisponde, `init` non propone il profilo, anche con `--update`, e lo dice. Test: Task 3 `test_unapproved_profile_not_proposed`, `test_profile_without_files_not_proposed`.
2. **`tollgate.toml` dell'utente rovinato.** Con un file esistente con commenti, un profilo `ai` già dichiarato e `--update` lanciato due volte: il testo dell'utente resta identico byte per byte salvo la riga `mode` e i blocchi aggiunti in coda, e nessun blocco è duplicato. Test: Task 3 `test_update_appends_and_keeps_user_text`, `test_update_twice_no_duplicate`, `test_declared_profile_left_alone`.
3. **Regola ignota che blocca sempre.** Ogni `R-AI-NN` della skill è in `rules` del blocco proposto e ogni `[blocca]` in `blocking_rules`; un rilievo `major` su una regola `R-AI` non `[blocca]` non ferma il task. Test: Task 2 `test_area_rules_*`; Task 3 `test_proposed_rules_match_skill`; Task 7 `test_ai_profile_non_blocking_rule_approves`.
4. **Codice AI fuori dalle cartelle.** Un file `supabase/functions/x/index.ts` che importa l'SDK entra nei `paths` proposti; un file che lo nomina solo in un commento senza la riga di import no; un binario o un file oltre 256 KiB si salta. Test: Task 3 `test_detect_adds_exact_paths`, `test_detect_skips_large_and_binary`.
5. **Agenti per area che divergono o che non sono di sola lettura.** `reviewer-ai` è negli elenchi di sola lettura; le copie contengono ogni paragrafo dei generici; `rules-ai` non finisce in `skills_required`. Test: Task 7 `test_area_agents_derive_from_generic`, `test_readonly_list_matches_config_and_agents`, `test_rules_ai_not_required`.

## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `agents/implementer.md`, `agents/task-reviewer.md`, `bin/tollgate_analysis/brief.py`, `bin/tollgate_flow/taskcmd.py` | 1 | rinvii 184-187 di B2 |
| `bin/tollgate_analysis/research.py`, `bin/tollgate_core/lookups.py` | 2 | `area_rules`; `base_rules` sopra di essa |
| `bin/tollgate_analysis/tomlout.py` | 2 | scrittore TOML minimo |
| `bin/tollgate_core/fragments.py` | 2 | lettura dei frammenti, approvazione, regole |
| `bin/tollgate_flow/init.py`, `skills/init/SKILL.md`, `docs/uso/comandi.md` | 3 | proposta dei profili |
| `skills/rules-ai/SKILL.md`, `templates/profiles/ai.toml`, `tests/test_rules_ai.py` | 4, 5, 6 | regole e frammento di `ai` |
| `docs/profili/verifiche/ai-fonti.md`, `docs/profili/ai.md` | 5, 6 | verifica delle fonti; pagina per l'utente |
| `agents/implementer-ai.md`, `agents/reviewer-ai.md`, `hooks/run`, `bin/tollgate_core/config.py` | 7 | agenti per area; elenchi di sola lettura |
| `spikes/run-b1-flow.sh`, `spikes/b3/flow/`, `tests/test_b1_scripts.py` | 8 | prova reale con il profilo `ai` |
| `docs/verifiche/2026-11-01-b3-prova-flusso.md`, `docs/verifiche/evidenze/b3/flusso/` | 8 | rapporto ed evidenze |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 9 | revisione 29 e stato |

---

### Task 1: Rinvii di B2 negli agenti generici e nel brief

**Files:**
- Modify: `agents/implementer.md`, `agents/task-reviewer.md` (riga ~53), `bin/tollgate_analysis/brief.py` (sezione del report in `review_brief`), `bin/tollgate_flow/taskcmd.py:278-281`
- Test: `tests/test_manifest.py`, `tests/test_brief.py`, `tests/test_taskcmd.py`

**Interfaces:**
- Consumes: `brief.ReviewBrief` (campo `research`), `taskcmd` resa del report (B2).
- Produces: i testi dei generici che il Task 7 copia.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_implementer_reads_listed_files` (la sezione «Informati prima di scrivere» contiene «i file che elenchi nella nota aprili con `Read`»; rinvio 184); `test_implementer_fix_round_repeats_red_green` (il paragrafo del report dice che il report di un giro di correzione ripete il riscontro RED/GREEN del difetto corretto; rinvio 186).
  - `tests/test_brief.py`: `test_review_brief_no_research_says_base_rules_do_not_block` (`research=False`: la sezione del report contiene «in questo lavoro le regole `R-BASE-…` non bloccano»; con `research=True` la frase non c'è; rinvio 185).
  - `tests/test_taskcmd.py` (`ReviewDoneTest`, radice temporanea esplicita): `test_report_concerns_shown_with_done` (stato `DONE` con `concerns` non vuoto: il testo di `concerns` compare nella sezione del report), `test_report_null_not_python_none` (un campo `null` del report non compare come `None`; rinvio 187).
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_manifest tests.test_brief tests.test_taskcmd`: FAIL dei test nuovi.
- [ ] **Step 3: Il codice e i testi.** In `implementer.md` la riga del rinvio 184 e quella del 186 (nel paragrafo del report). In `brief.py`, con `research` falso, la frase del rinvio 185 nella sezione del report; in `task-reviewer.md` accanto alla riga 53 la stessa indicazione per il revisore. In `taskcmd.py` `concerns` si esclude dalla resa del report solo quando la sezione dei dubbi c'è (`DONE_WITH_CONCERNS`), e un valore `None` si rende `null`.
- [ ] **Step 4: Verifica.** Gli stessi file di test: PASS (anche `test_implementer_tools`, `test_implementer_mentions_*`, `test_code_agents_preload_rules_base`). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: rinvii di B2 negli agenti generici e nel brief».

---

### Task 2: Regole di area, scrittore TOML e frammenti

**Files:**
- Modify: `bin/tollgate_analysis/research.py`, `bin/tollgate_core/lookups.py` (solo se serve per `base_rules`)
- Create: `bin/tollgate_analysis/tomlout.py`, `bin/tollgate_core/fragments.py`, `tests/test_tomlout.py`, `tests/test_fragments.py`
- Test: `tests/test_research.py`, `tests/test_lookups.py`

**Interfaces:**
- Consumes: `research.enforced(text)`, `research.base_rules(text)`, `config.PROFILE_DEFAULTS`, `config.load_config_text(text)`.
- Produces:
  - `research.area_rules(skill_text: str, area: str) -> tuple[set[str], set[str]]`;
  - `tomlout.table(name: str, values: dict) -> str` (decisione 8);
  - `fragments.Fragment` (dataclass frozen: `area: str`, `profile: dict`, `detect: tuple[str, ...]`, `skill_path: Path`);
  - `fragments.load(plugin_root) -> list[Fragment]` (ordinati per `area`; un frammento illeggibile o con chiavi fuori da `PROFILE_DEFAULTS`, o con `rules`/`blocking_rules`, è un `ValueError` con il nome del file);
  - `fragments.approved(fragment) -> bool` (`research.enforced` sul testo della skill; skill assente → `False`);
  - `fragments.rules(fragment) -> tuple[list[str], list[str]]` (ordinati, da `area_rules`).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_research.py`: `test_area_rules_extracts_prefix` (un testo con `R-AI-01 [blocca] …`, `R-AI-02 …` e una riga `R-BASE-01 …` → `({"R-AI-01","R-AI-02"}, {"R-AI-01"})` per `area="ai"`); `test_area_rules_ignores_inline_mentions` (un id citato a metà riga non conta); `test_base_rules_unchanged` (`base_rules(t) == area_rules(t, "BASE")` sul testo vero di `skills/rules-base/SKILL.md`).
  - `tests/test_tomlout.py`: `test_round_trip` (un dizionario con stringhe con `"`, `\`, a capo, accenti, un `bool`, un `int`, una lista di stringhe vuota e piena, un `dict` di stringhe → `tomllib.loads(table("profiles.ai", d))["profiles"]["ai"] == d`); `test_rejects_other_types` (float, `None`, lista di numeri → `TypeError`).
  - `tests/test_fragments.py` (radice temporanea): `test_load_reads_profile_and_detect`; `test_load_rejects_unknown_key`; `test_load_rejects_rules_in_fragment`; `test_approved_needs_approved_skill` (skill assente, senza `approved`, con `approved: 2026-11-01`); `test_rules_from_skill`; `test_fragment_profile_validates` (il `[profile]` del frammento con le `rules` calcolate, messo in `[profiles.x]` con `tomlout.table`, passa `config.load_config_text` senza avvisi).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `area_rules` con la regex di `base_rules` generalizzata (`^(R-<AREA>-\d{2})( \[blocca\])? \S`, `<AREA>` = `re.escape(area.upper())`); `base_rules` la chiama. `tomlout` per la decisione 8. `fragments` in `tollgate_core` (legge file del plugin; importa `tollgate_analysis.research` e `config`), con `skill_path = plugin_root / "skills" / f"rules-{area}" / "SKILL.md"` e l'area presa dal nome del file del frammento (`[a-z0-9-]+`, altrimenti `ValueError`).
- [ ] **Step 4: Verifica.** I file di test: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: regole di area dal testo, scrittore TOML e frammenti di profilo».

---

### Task 3: `init` propone i profili approvati e presenti

**Files:**
- Modify: `bin/tollgate_flow/init.py` (`propose`, dopo `with_mode` e prima di `config.load_config_text`), `skills/init/SKILL.md`, `docs/uso/comandi.md` (sezione di `/tollgate:init`)
- Test: `tests/test_init.py`

**Interfaces:**
- Consumes: `fragments.load/approved/rules` e `tomlout.table` (Task 2); `git.ls_files_at(repo, ref, prefix)`, `git.text_at(repo, ref, path)`; `globs.match_any`; `init.PLUGIN_ROOT`.
- Produces: `init.profile_blocks(repo, ref, current_text, plugin_root) -> tuple[str, list[str]]` (il testo da aggiungere in coda e le righe da mostrare all'utente); il blocco `[profiles.<area>]` nella proposta.

- [ ] **Step 1: I test che falliscono** (in `tests/test_init.py`, con un plugin temporaneo che ha un frammento `x` e la sua skill, e un repo di prova):
  - `test_approved_profile_with_files_proposed` (il `tollgate.toml` proposto ha `[profiles.x]` con `rules` e `blocking_rules` uguali a quelli della skill, e le righe mostrate nominano i file che lo accendono, al più 10, e il totale);
  - `test_unapproved_profile_not_proposed`, `test_profile_without_files_not_proposed` (e la proposta lo dice);
  - `test_detect_adds_exact_paths` (un file fuori dai `paths` con un marcatore di `[detect] content` entra nei `paths` proposti col suo percorso esatto; un file che nomina il fornitore senza la riga di import, per esempio in un commento, resta fuori, perché un marcatore è un pezzo di riga di import, non il nome del fornitore; un file già coperto dai `paths` non si ripete);
  - `test_detect_skips_large_and_binary` (un file oltre 256 KiB e uno con un byte nullo nei primi 8 KiB non si leggono);
  - `test_update_appends_and_keeps_user_text` (un `tollgate.toml` esistente con commenti: il testo proposto è uguale all'originale salvo la riga `mode`, più i blocchi in coda);
  - `test_update_twice_no_duplicate` (applicata la prima proposta, una seconda `--update` non aggiunge blocchi e dice «nulla da aggiornare» se nient'altro cambia);
  - `test_declared_profile_left_alone` (con `[profiles.x]` già nel file: niente blocco, una riga che rimanda a `templates/profiles/x.toml`);
  - `test_base_never_proposed` (un frammento `base.toml` è ignorato);
  - `test_missing_agent_dropped` (un frammento con `agent = "tollgate:implementer-x"` senza `agents/implementer-x.md`: la chiave non c'è e la proposta lo dice);
  - `test_proposed_rules_match_skill`;
  - `test_proposal_validates` (il `tollgate.toml` proposto passa `config.load_config_text` senza avvisi).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `profile_blocks` per le decisioni 4, 5, 7 e 12: frammenti caricati da `PLUGIN_ROOT`, saltati `base`, i non approvati e quelli già dichiarati in `current_text` (cercati con `tomllib`, non col testo); per gli altri, i file del ramo predefinito (`ls_files_at(repo, ref, "")`) che corrispondono ai `paths` e quelli trovati dai marcatori; un profilo senza file non entra. Il testo del blocco è `tomlout.table(f"profiles.{area}", …)` preceduto da una riga di commento `# profilo <area> da templates/profiles/<area>.toml (tollgate <VERSION>)`. In `propose` il testo si aggiunge dopo `with_mode`; le righe vanno in `InitResult.lines`. La skill `init` e `docs/uso/comandi.md` dicono che la proposta può contenere profili e come leggerli.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_init`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: init propone i profili approvati e presenti nel repo».

---

### Task 4: Bozza di `rules-ai` e frammento di `ai` con le fonti

**Files:**
- Create: `skills/rules-ai/SKILL.md`, `templates/profiles/ai.toml`, `tests/test_rules_ai.py`
- Modify: `docs/uso/comandi.md`
- Test: `tests/test_rules_ai.py`, `tests/test_docs.py`, `tests/test_fragments.py`

**Interfaces:**
- Consumes: le copie delle fonti in `<workspace>/fonti/` (Step 0); `research.area_rules`, `research.enforced`; `fragments.load` (Task 2); `tests/test_rules_base.rules(text)` come modello.
- Produces: `skills/rules-ai/SKILL.md` nella forma di B2 (piano principale, sezione 3, riga B2→B3-B7), senza `approved`; `templates/profiles/ai.toml` (decisioni 2, 5, 9, 14); in `tests/test_rules_ai.py` la funzione `rules(text)` per i Task 5 e 6.

- [ ] **Step 0 (controller): le fonti.** Copia in `<workspace>/fonti/ai/` le pagine della decisione 13 (una per file, `.md` o `.html` come le serve il sito), con un `SHA256SUMS` e un `FONTI.md` con URL e data di consultazione per ogni file. Solo pagine ufficiali di Anthropic e Google. Nel brief dell'implementatore va il percorso di `fonti/ai/`.
- [ ] **Step 1: I test che falliscono.** In `tests/test_rules_ai.py`, sul modello di `RulesBaseTest`:
  - `test_frontmatter` (`name: rules-ai`, `description: Regole di tollgate per il codice che usa modelli AI: le caricano in automatico gli agenti dell'area ai, non serve invocarla.`, `version: 1`, **nessun `approved`**, `research.enforced(text)` falso; il Task 6 lo inverte);
  - `test_has_title` (`# Regole ai (versione 1)` subito dopo il frontmatter); `test_first_section_is_prima_di_scrivere`; `test_rule_ids_consecutive` (`R-AI-01`, …); `test_every_rule_has_a_source`; `test_some_rules_block`; `test_at_most_150_lines`;
  - `test_user_choices_covered` (per ogni scelta del progetto 9 c'è almeno una regola con `Fonte: progetto di B, sezione 9`: modello più recente della famiglia; nome in un punto solo con URL e data; note di migrazione prima di cambiare; errore chiaro per un modello ritirato; alias che cambia da solo dichiarato nel report). Il test cerca gli id elencati in una tabella del test, non le parole delle regole (piano principale, sezione 9, rinvio 182);
  - `test_fragment_matches_catalogue` (`templates/profiles/ai.toml`: `kind = "vertical"`, `min_level = "L1"`, i quattro `paths` della decisione 14, `skills = []`, `reviewer_skills = []`, `agent = "tollgate:implementer-ai"`, `reviewer = "tollgate:reviewer-ai"`, `dod = []`, `[detect] content` non vuoto);
  - in `tests/test_fragments.py`: `test_real_fragments_load` (`fragments.load(ROOT)` legge `ai` senza errori).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Scrivi le regole** dalle fonti, con parole tue, una riga di regola e una riga `Fonte:` ciascuna, sezioni «Prima di scrivere», «Mentre lavori», «Dove informarsi» (gli URL ufficiali, compresa la skill `claude-api` per il codice che usa l'SDK di Anthropic), «Fonti». Bozza da distillare (l'implementatore può dividere o unire, mai aggiungere obblighi senza fonte):

  | Id | Sezione | `[blocca]` | Cosa dice la regola | Fonte |
  |---|---|---|---|---|
  | R-AI-01 | Prima di scrivere | sì | Il nome di un modello sta in un solo punto del codice (costante o configurazione); il diff non lo ripete altrove | progetto 9 |
  | R-AI-02 | Prima di scrivere | sì | Accanto al nome del modello il diff scrive l'URL della pagina ufficiale dei modelli e la data della verifica | progetto 9; pagina dei modelli del fornitore |
  | R-AI-03 | Prima di scrivere | sì | Un modello scelto o toccato dal diff è il più recente della sua famiglia sulla pagina ufficiale letta nel task; se no, il report dice perché | progetto 9; pagina dei modelli |
  | R-AI-04 | Prima di scrivere | sì | Se il diff cambia modello, «Documentazione» della nota ha la guida alla migrazione o le note di versione ufficiali del modello nuovo, e il report dice cosa ha cambiato per seguirle | progetto 9; guida alla migrazione |
  | R-AI-05 | Prima di scrivere | sì | Parametri, limiti (token, contesto) e prezzi scritti nel diff o nel report vengono da una pagina ufficiale in «Documentazione» | progetto 3.4, riga `ai` |
  | R-AI-06 | Mentre lavori | no | Il codice che chiama il modello gestisce l'errore di un modello non disponibile o ritirato con un messaggio che nomina il modello e il punto della configurazione | progetto 9; pagina delle deprecazioni |
  | R-AI-07 | Mentre lavori | no | Un alias che cambia da solo (per esempio `*-latest`) si usa solo se il report lo dichiara, con il motivo | progetto 9; pagina dei modelli Gemini |
  | R-AI-08 | Mentre lavori | no | Il testo prodotto da un modello si tratta come dato non fidato: non diventa codice eseguito, comando o HTML senza controllo | fonte da trovare nel Task 4, Step 0 (pagina ufficiale sulla sicurezza dei fornitori), altrimenti esce dalla bozza |

  Il frammento `templates/profiles/ai.toml` per le decisioni 2, 5, 9 e 14, con i marcatori di `[detect] content` presi dalle pagine degli SDK ufficiali (le righe di import, una per linguaggio documentato).
- [ ] **Step 4: Comando.** In `docs/uso/comandi.md` la sezione `### \`/tollgate:rules-ai\`` come quella di `rules-base` (`test_every_skill_documented`).
- [ ] **Step 5: Verifica.** `python3 -B -m unittest tests.test_rules_ai tests.test_fragments tests.test_docs`: PASS. `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 6: Commit** «tollgate B3: bozza di rules-ai e frammento del profilo ai con le fonti».

---

### Task 5: Verifica delle fonti e pagina per l'utente

**Files:**
- Create: `docs/profili/verifiche/ai-fonti.md`, `docs/profili/ai.md`
- Modify: `skills/rules-ai/SKILL.md` e `templates/profiles/ai.toml` (solo se una fonte non passa), `tests/test_rules_ai.py`

**Interfaces:**
- Consumes: `tests/test_rules_ai.rules(text)` (Task 4); `<workspace>/fonti/ai/`.
- Produces: la pagina che il Task 6 mostra all'utente; il rapporto delle fonti.

- [ ] **Step 1 (controller): la verifica delle fonti.** Come in B2 (Task 4, Step 1): un subagente `Explore` (sonnet, sola lettura) verifica **ogni fonte di ogni regola** e **ogni marcatore di `[detect] content`** sulle copie di `fonti/ai/` e sul progetto di B: il file esiste, la sezione esiste, dice ciò che la regola o il marcatore le attribuisce (citazione di al più una riga). Esito `ok` o `no` con il motivo. Il controller salva l'uscita in `<workspace>/task-5-fonti.md`.
- [ ] **Step 2: I test che falliscono** (copiati da `RulesBasePageTest`, con i correttivi del rinvio 182): `test_sources_report_covers_every_rule`, `test_page_lists_every_rule` (anche «N.» uguale all'id tra parentesi), `test_page_blocca_matches_skill`, `test_page_explains_what_changes` (la pagina dice che il profilo si accende solo nei progetti dove `init` lo propone e l'utente lo copia, a partire da L1, e quali cartelle e file lo accendono), `test_detect_markers_verified` (ogni marcatore del frammento ha una riga `ok` nel rapporto).
- [ ] **Step 3: Le correzioni e i due file.** Escono le fonti `no` e le regole o i marcatori che restano senza fonte `ok`; le regole rimaste si rinumerano senza buchi. Rapporto e pagina come in B2 (tabella «N.», «In parole semplici», «Blocca?», «Da dove viene»; sezione «Regole tolte dalla verifica»; come rispondere), in parole semplici.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_rules_ai`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: fonti di rules-ai verificate e pagina per l'utente».

---

### Task 6: Approvazione dell'utente

**Files:**
- Modify: `skills/rules-ai/SKILL.md`, `docs/profili/ai.md`, `docs/profili/verifiche/ai-fonti.md` (solo con correzioni), `tests/test_rules_ai.py`

**Interfaces:**
- Consumes: la pagina del Task 5; `fragments.approved` (Task 2).
- Produces: `approved: <AAAA-MM-GG>` in `skills/rules-ai/SKILL.md`; da qui `init` propone il profilo `ai`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Come in B2, Task 5, Step 1: la pagina nel terminale, approva, correggi o togli; ogni correzione è un giro di questo task, una regola nuova o con una fonte nuova ripassa dal verificatore. Fermata prevista.
- [ ] **Step 2: I test che falliscono.** `test_frontmatter` si inverte; `test_page_approval_date_matches_skill`; in `tests/test_fragments.py` `test_real_ai_fragment_approved` (`fragments.approved` vero sul frammento vero).
- [ ] **Step 3: L'approvazione.** `approved: <data>` dopo `version`; nella pagina «Approvata dall'utente il <data>.». `claude plugin validate --strict .`: uscita 0. `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde.
- [ ] **Step 4: Commit** «tollgate B3: rules-ai approvata dall'utente».

---

### Task 7: Agenti `implementer-ai` e `reviewer-ai`

**Files:**
- Create: `agents/implementer-ai.md`, `agents/reviewer-ai.md`
- Modify: `hooks/run` (`READONLY_TYPES`), `bin/tollgate_core/config.py` (`DEFAULTS["review"]["readonly_agents"]`)
- Test: `tests/test_manifest.py`, `tests/test_wrapper.py`, `tests/test_taskcmd.py`, `tests/test_check_task_verdict.py`

**Interfaces:**
- Consumes: `agents/implementer.md`, `agents/task-reviewer.md` dopo il Task 1; `skills/rules-ai/SKILL.md` approvata (Task 6); `templates/profiles/ai.toml`.
- Produces: i tipi `tollgate:implementer-ai` e `tollgate:reviewer-ai`.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_code_agents_preload_rules_base` include i due agenti nuovi (con `skills` uguale a `[rules-base, rules-ai]` per loro); `test_area_agents_derive_from_generic` (ogni paragrafo del corpo del generico, dopo la riga di attribuzione, è nella copia; il frontmatter della copia ha gli stessi `tools` e `model`); `test_area_agents_attribution` (la riga `ATTRIBUTION` in entrambe); `test_area_agents_name_rules_ai` (la sezione «Area `ai`» nomina `rules-ai` e `R-AI-`).
  - `tests/test_wrapper.py`: `test_readonly_list_matches_config_and_agents` resta com'è e fallisce finché gli elenchi non hanno `tollgate:reviewer-ai`.
  - `tests/test_taskcmd.py` (radice temporanea con il frammento `ai` approvato e un `tollgate.toml` col blocco proposto da `init`): `test_ai_task_routed_to_area_agents` (un task che tocca `ai/x.py` ha `agent_type` `tollgate:implementer-ai` e `reviewer_type` `tollgate:reviewer-ai`); `test_rules_ai_not_required` (`skills_required` vuoto, «Skill da usare» senza `rules-ai`).
  - `tests/test_check_task_verdict.py`: `test_ai_profile_blocking_rule_changes` (un `major` su una `R-AI` `[blocca]` → `changes`); `test_ai_profile_non_blocking_rule_approves` (un `major` su una `R-AI` non `[blocca]` → `approved`).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Gli agenti e gli elenchi.** I due file per la decisione 10 (frontmatter: `name: implementer-ai` / `reviewer-ai`, `description` che dice l'area, gli stessi `tools` e `model` dei generici, `skills: [rules-base, rules-ai]`); la sezione «Area `ai`»: le regole `R-AI-…` di `rules-ai` valgono come le `R-BASE-…` (solo le `[blocca]` danno `blocker` o `major`; un difetto si segnala una volta sola, con la regola che viola). `tollgate:reviewer-ai` in `READONLY_TYPES` e in `readonly_agents` (decisione 11).
- [ ] **Step 4: Verifica.** I file di test: PASS. `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: agenti implementer-ai e reviewer-ai».

---

### Task 8: Prova reale corta con il profilo `ai` (preparazione con test, esecuzione del controller)

**Files:**
- Create: `spikes/b3/flow/` (progetto di prova: `ai/__init__.py`, `ai/summary.py` senza nome di modello, `services/notify.py` che importa l'SDK con la riga di un marcatore, `config.toml`, `issue-1.md`, `piano-L1.md`, `tests/test_smoke.py`, `.gitignore`), `docs/verifiche/2026-11-01-b3-prova-flusso.md`, `docs/verifiche/evidenze/b3/flusso/`
- Modify: `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py` (se serve per cercare le trascrizioni dei subagenti), `tests/test_b1_scripts.py`

**Interfaces:**
- Consumes: `spikes/run-b1-flow.sh` (modi e variabili di B1 e B2, `B1_FLOW_RULES`, `B1_FLOW_SRC`); `init.propose` (Task 3).
- Produces: la variabile `B1_FLOW_CASE` (`b1`, il predefinito, oppure `ai`).

- [ ] **Step 1 (implementatore, senza rete e senza `claude`): lo script.** Con `B1_FLOW_CASE=ai`: progetto da `spikes/b3/flow/`, `OUT` `docs/verifiche/evidenze/b3/flusso`, `B1_FLOW_RULES` deve essere `vere` (altrimenti errore); `prepara` genera il `tollgate.toml` del progetto con `init --propose` sulla copia del plugin e lo committa nel repo di prova, e si ferma se il blocco `[profiles.ai]` manca o se `services/notify.py` non è nei suoi `paths`; l'issue chiede di aggiungere in `ai/models.py` la costante del modello Claude da usare in `ai/summary.py`, nel punto unico, con URL e data; `registra` cerca `# Regole ai (versione 1)` e `# Regole di base (versione 1)` nelle trascrizioni dei subagenti in `~/.claude/projects/<cartella della prova>/<sessione>/subagents/` (rinvio 181; solo lettura, solo la cartella della prova) e raccoglie `agent_type` e `reviewer_type` del task. Ogni altro valore di `B1_FLOW_CASE` è un errore. Test in `tests/test_b1_scripts.py`: `test_flow_case_ai_out_dir`, `test_flow_case_ai_requires_real_rules`, `test_flow_case_ai_prepara_proposes_profile` (con `B1_FLOW_SRC` su un repo temporaneo con la skill approvata), `test_flow_case_unknown_value`; i test di B1 e B2 restano verdi.
- [ ] **Step 2 (controller): esecuzione.** `B1_FLOW_CASE=ai B1_FLOW_RULES=vere`: `prepara`, `passo1`, `passo2`, `registra`. Atteso: task 1 `done` con verdetto `approved`; `agent_type` `tollgate:implementer-ai`, `reviewer_type` `tollgate:reviewer-ai`; il titolo di `rules-ai` nelle trascrizioni di entrambi; nota valida prima della prima modifica; il diff con il nome del modello in un punto, URL e data. Un esito in più tentativi è «composito». Un difetto del prodotto scoperto qui è un giro di questo task (test che fallisce, correzione, `tests/run`), poi si ripete solo il passo interessato.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-11-01-b3-prova-flusso.md`: passi, tentativi, proposta di `init` (file che hanno acceso il profilo), agenti lanciati, precaricamento visto, letture, nota, verdetto e rilievi `R-AI-…`, token e consumo stimato, limiti. Evidenze anonimizzate come in B2 (id di sessione, `/home/<utente>`, nome utente e host).
- [ ] **Step 4: Commit** «tollgate B3: prova reale corta con il profilo ai».

---

### Task 9: Prove, revisione 29 della spec, piano principale, catalogo

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 29), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento), `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`

- [ ] **Step 1: Revisione 29 della spec del nucleo.** 6.3 (agenti per area con `skills: [rules-base, rules-<area>]`, fuori dal tetto; frammenti); 7.3 (revisori per area negli elenchi di sola lettura); 11.2 (`init` propone i profili: decisioni 4, 5, 7, 12); 11.4 (frammento `templates/profiles/<area>.toml`, `[detect] content`, `rules` calcolate dalla skill); riga 29 della sezione 20.
- [ ] **Step 2: Catalogo.** Sezione 1.6 e 2.1, riga `ai`: `rules-ai` precaricata dagli agenti, nessuna skill nel frammento, `claude-api` in «Dove informarsi» (decisione 9); sezione 2: i percorsi più il rilevamento per contenuto; sezione 4: le fonti vere di `rules-ai`; una nota per B4 e B6: `globs` non espande le graffe `{a,b}`, i percorsi del catalogo che le usano vanno scritti in più righe.
- [ ] **Step 3: Piano principale di B e progetto.** Stato in testa; riga B3 della sezione 2; sezione 3, riga B3→B4-B7 con i nomi reali (frammento, `fragments`, `area_rules`, `init.profile_blocks`, agenti derivati con il test di deriva, elenchi di sola lettura); sezione 9: chiusi i rinvii 178, 180-187 che B3 ha fatto, aperti quelli rimasti, più le righe «minor (deferred)» che riguardano B3-bis e B4-B7; una sezione «Prove di B3» con ogni riga della tabella «Copertura» e il test o l'evidenza che la prova. Nel progetto la riga di avanzamento: «B1, B2 e B3 eseguite».
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md
git commit -m "tollgate B3: prove, spec rev 29, piano principale di B, catalogo"
```

---

## Copertura: punti del progetto e del piano principale destinati a B3 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: primo gruppo di profili, `ai` | 4, 5, 6, 7 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `ai` (pagine ufficiali di Gemini e Claude) | 4 (sezione «Dove informarsi»), 5 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 7 |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 5, 6; decisione 16 |
| Progetto 2, anti-obiettivo «fonti inventate» | 5 (verificatore di sola lettura), decisione 13 |
| Progetto 3.4, riga `ai` | 4 (R-AI-02, R-AI-05) |
| Progetto 3.6: codice AI fuori da `**/ai/**` | 3 (decisione 5, `test_detect_adds_exact_paths`); R-BASE-04 resta |
| Progetto 4, riga `ai`: L1, Gemini oltre `claude-api` | 4 (frammento, «Dove informarsi»); decisione 9 |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 4, 5, 6; decisioni 4, 16 |
| Progetto 9: scelte dell'utente sui modelli che cambiano (regole) | 4 (`test_user_choices_covered`) |
| Progetto 9: sentinella dei modelli | **B3-bis** (fuori da questo piano) |
| Piano principale, sezione 2, riga B3: frammenti, `init`, `rules-ai`, agenti, percorsi, `dod` | 2, 3, 4, 7; decisione 14 |
| Piano principale, sezione 3, B2→B3-B7: forma della regola, precaricamento o brief | 4; decisione 9 |
| Piano principale, sezione 3, B3→B4-B7: frammenti, `init`, agenti derivati | 2, 3, 7; nomi reali nel Task 9 |
| Piano principale, sezione 9: rinvii 178 (agenti nuovi con `rules-base`), 180 (radice esplicita), 181 (precaricamento nelle trascrizioni), 182 (test di pagina), 184-187 | 7; Global Constraints; 8; 5; 1 |
| Revisione della spec del nucleo | 9 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B (con la sezione 9), il piano principale, la spec rev 28, il catalogo, il codice di `main` e il modello di B2.

| Giro | Rilievi | Esito |
|---|---|---|
| — | — | da fare |
