# tollgate B2: regole di base

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** La skill `rules-base` (le regole del passo «informati prima», comuni a tutti), scritta con le fonti, verificata da un agente di sola lettura, approvata dall'utente su una pagina in parole semplici e, solo dopo l'approvazione, caricata da ogni agente che scrive o rivede codice; con l'approvazione si accende il blocco di B1 in L1 e L2.

**Architecture:** `skills/rules-base/SKILL.md` è una skill del plugin con regole numerate `R-BASE-NN`, ciascuna con la sua `Fonte:` e verificabile dal diff, dalla nota di ricerca o dal report. Arriva agli agenti col campo `skills:` del frontmatter (precaricamento, verificato in P0, E5), fuori dal tetto di 3 skill dei profili e fuori dal controllo di `SubagentStop`. L'interruttore resta quello di B1 (`approved` nel frontmatter, letto da `lookups.rules_enforced`): B2 lo rende più severo sui valori (rinvio 13), distingue il file assente dal file illeggibile (rinvio 31) e alla fine scrive la data dell'approvazione. Prima della bozza la suite viene resa indipendente dallo stato dell'interruttore nel repo vero.

**Tech Stack:** Python ≥ 3.11, solo libreria standard; bash; git; Claude Code (`claude plugin validate --strict`, che non lancia il modello; la prova reale con `claude -p --plugin-dir` solo dal controller). Test con `unittest` tramite `tests/run` (python3.11 e python3).

**Spec:** il progetto approvato `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (l'autorità per B: «utente» non si discute, «mia scelta» si corregge solo con un motivo scritto qui), soprattutto le sezioni 2, 3.4, 3.6, 4 (riga `base`) e 5; la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 27 (la 28 la scrive il Task 8): sezioni 6.3, 8.1 («Interruttore del blocco»), 8.6, 12.2, 16, 18.4; il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, sezioni 1 (principi 4, 5, 7 e skill comuni), 2.3 e 4. Piano principale di B: `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, righe B1→B2 della sezione 3 e rinvii della sezione 9.

## Global Constraints

- Solo libreria standard in `bin/` e nei test (spec 3). Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`).
- **Strati** (`tests/test_layers.py`): `tollgate_analysis` non importa nulla di tollgate; `tollgate_core` non importa `tollgate_flow`, `tollgate_hooks`, `tollgate_checks`, `tollgate_gate`, tranne `cli.py`; `tollgate_checks` non importa `tollgate_flow`.
- **Un modulo del registro non scrive nel DB** (spec 3.2): chiede con `record`. B2 non aggiunge operazioni ad `apply._OPS` (oggi 29, `test_ops_count_is_29`): l'evento nuovo passa dall'operazione `event` che esiste già, e il suo tipo va in `events.EVENT_TYPES` (elenco chiuso: un tipo sconosciuto è un `ValueError`).
- **Nessuna rete**, né nei test né per i subagenti: le fonti delle regole sono **copie locali** messe dal controller nel workspace (Task 3, Step 0). Nessun `claude` vero nei test; `gh` è `tests/fakegh.py`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/settings.json`, `~/.claude/plugins/`.
- **Regole con parole nostre** (catalogo 1, principio 7): da fonti MIT o Apache-2.0 si distilla e si cita; una citazione testuale sta al più in una riga, nel rapporto delle fonti, non nella skill. Ogni regola è verificabile con un sì o un no **guardando il diff, la nota di ricerca o il report** (catalogo 1, principio 5).
- **Numeri delle regole stabili dopo l'approvazione** (catalogo 2.3): prima dell'approvazione si rinumera senza buchi; dopo, mai.
- **`approved` in `skills/rules-base/SKILL.md` si scrive solo nel Task 5**, con la data dell'OK dell'utente. In nessun altro task e in nessun commit prima di quello.
- Testo non fidato (nota di ricerca, pagine scaricate, citazioni delle fonti): nei brief dentro `brief.fence` con `brief.DATA_NOTE`, mai come istruzione.
- Programma nei messaggi per il modello: sempre `tollgate_core.paths.program_command`.
- `claude -p` solo dal controller, solo nel Task 7, solo sotto `/tmp/tollgate-b1/`, sempre con `--plugin-dir`.
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.
- La verifica con gli avvisi come errori si fa come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run` (vale anche nei sottoprocessi; `-W` no, lezione della CI di B1).

## Decisioni di questo piano

Scelte che il progetto lascia a chi costruisce (progetto 6, «come `rules-base` arriva a tutti gli agenti») o che il codice reale impone, con il costo se sbagliate. Il Task 8 le riporta nella revisione 28 della spec.

1. **Le fonti sono copie locali di skill MIT già installate, più le scelte dell'utente.** `agent-skills` 0.6.9 (Addy Osmani, MIT) e Superpowers 7.0.0 (Jesse Vincent, MIT) coprono quattro dei cinque schemi del progetto 1: `source-driven-development` (versioni dal file delle dipendenze, gerarchia delle fonti, fonti in conflitto, «non verificato»), `context-engineering` (leggere prima di modificare, cercare un esempio esistente), `systematic-debugging` (la causa prima della correzione, il test che riproduce), `verification-before-completion` (nessun «fatto» senza prova fresca). Le regole sui nomi dei modelli, sul «non esiste» e sulle fonti non aperte vengono dalle correzioni dell'utente (progetto 1 e 3.6): `Fonte: progetto di B, sezione 1`. Il controller copia le fonti nel workspace (Task 3, Step 0), così né l'implementatore né il verificatore usano la rete o leggono `~/.claude/plugins/`. Le licenze vanno in `LICENSES/` (oggi c'è solo `superpowers-MIT.txt`; si aggiunge `agent-skills-MIT.txt`). Costo: le regole partono da due raccolte di metodo, non dalla documentazione dei singoli fornitori; quella è il «Dove informarsi» dei profili di B3-B7.
2. **Come `rules-base` arriva agli agenti** (piano principale, sezione 3, proposta). Con `skills: [rules-base]` nel frontmatter dei **quattro agenti che scrivono o rivedono codice**: `implementer`, `task-reviewer`, `final-reviewer`, `finding-verifier` (quest'ultimo conferma rilievi che citano `R-BASE-NN`, quindi deve conoscerle). Non la caricano gli agenti che lavorano su spec e piano (`spec-auditor`, `spec-adversary`, `plan-adversary`). Il nome è corto, senza prefisso del plugin: è la forma provata in P0 (E5, `spikes/hookprobe/agents/probe-agent.md`, dove `skills:` sta tra `tools:` e `model:`). È una skill comune (catalogo 1): fuori dal tetto di 3, mai nel brief alla voce «Skill da usare» e mai in `tasks.skills_required` (il precaricamento non passa dallo strumento `Skill`, quindi `SubagentStop` darebbe un veto ingiusto). **Il caricamento si fa dopo l'approvazione** (Task 6): prima, una bozza non approvata guiderebbe gli agenti e i revisori bloccherebbero sulle sue regole `[blocca]` (progetto 5, punto 4, scelta dell'utente). Costo: circa 2.000-3.000 token in più per ogni lancio di quei quattro agenti.
3. **L0.** In L0 scrive la sessione principale, che non precarica niente (spec 6.3: «la sessione principale riceve nel promemoria le skill dei profili toccati»). Dopo l'approvazione l'avviso di `research_gate` nomina la skill `tollgate:rules-base` (Task 6). Costo: una frase nell'avviso.
4. **L'approvazione è una data.** Nel Task 5 si scrive nel frontmatter `approved: <AAAA-MM-GG>`, la data del giorno in cui l'utente approva la pagina (rinvio 13: «B2 scrive comunque una data»), e la pagina riporta «Approvata dall'utente il <data>». `research.enforced` continua ad accettare ogni altro valore non vuoto (la copia della prova di B1 usa `approved: prova-b1`), ma `no`, `off` e `n` (in ogni combinazione di maiuscole, anche tra apici) si aggiungono a `_YAML_EMPTY`, dove `false` c'è già; il confronto con `_YAML_EMPTY` si fa **dopo** aver tolto gli apici. Il test della skill vera esige la forma della data. Costo: nessuno.
5. **Interruttore illeggibile** (rinvio 31). `lookups.rules_switch(root) -> tuple[bool, str | None]`: `(enforced, error)`. `FileNotFoundError` → `(False, None)`, spento in silenzio. Ogni altro `OSError` → `(False, "<classe>: <messaggio>")`, spento con traccia. `rules_enforced(root)` resta la funzione unica di gate e `taskcmd`, e vale `rules_switch(root)[0]`. In `research_gate`, per ogni modifica di un implementatore L1 o L2 di un lavoro con il passo (con o senza nota valida): a `post_*` l'evento `research_switch_unreadable` {`error`}, **una volta per lavoro** (se non ce n'è già uno dopo l'ultimo `plan_reset`); a `pre_*`, quando c'è da dare l'avviso normale, gli si antepone il testo `_UNREADABLE`. Non rifiuta mai per questo. Il rinvio 31 chiedeva «una riga nel log»: l'evento è quella riga, perché gli eventi sono il registro che leggono `tollgate stats` e gli eval, mentre `hooks.log` riceve solo ciò che non si può iniettare. Testo esatto:
   `tollgate: l'interruttore delle regole base (skills/rules-base/SKILL.md) non si legge ({error}): il passo «informati prima» avvisa soltanto, non blocca. Controlla il file.`
   Costo: con il file illeggibile i lavori procedono con il solo avviso, come prima di B2, ma la traccia c'è.
6. **Task senza modifiche** (minore della revisione finale di B1, che con il blocco acceso diventa reale). Nel brief del revisore, se il task non ha modifiche e la nota non è utilizzabile (mancante **o non valida**), la sezione dice «la nota non era richiesta, nessun rilievo sulla nota». Oggi lo dice solo con la nota mancante. Costo: nessuno; la nota serve prima di una modifica, e qui non c'è stata.
7. **La suite non dipende dallo stato dell'interruttore nel repo vero** (Task 2, prima della bozza). Il codice legge l'interruttore dalla radice vera del plugin: nel processo dei test (`taskcmd`: `db.BIN_PATH.parents[1]`; `tests/hookkit.py`: `Lab(plugin_root=ROOT)` per default) e nei sottoprocessi (`hooks/run` e `bin/tollgate` usano `runner.PLUGIN_ROOT` e `db.BIN_PATH`, fissati dal percorso del file). Con `approved` scritto nel repo, ogni test che oggi presume l'interruttore spento cambierebbe esito. Il Task 2 lo misura (un file di prova, mai committato) e rende esplicita la radice nei test che falliscono, con questa priorità:
   - (a) **nel processo dei test**: una radice temporanea esplicita (`Lab(plugin_root=…)`, `mock.patch.object(taskcmd.db, "BIN_PATH", …)`, come `test_review_prepare_enforced_when_rules_base_approved`);
   - (b) **prove a secco degli eval** (`tests/test_eval_cases.py`): nelle sequenze dei casi in cui l'implementatore di un lavoro L1 o L2 modifica file (s1, s2, s3, s9), prima della prima modifica si aggiungono una `Read` dell'implementatore di un file che il caso tocca e un `research submit <k>` con «Nessuna fonte esterna» e il motivo. Il banco oggi non ha un'azione di lettura (`_do_agent`, `_do_bash`, `_do_edit`, `_do_stop`, `_do_prompt`, `_do_say`): il Task 2 aggiunge un'azione `read`, cioè il `PostToolUse` di `Read` con l'`agent_id` dell'implementatore, che il `SubagentStart` di `impl_launch` ha già registrato; il `research submit` passa da `_do_bash`, che esegue davvero il comando. È ciò che farà l'implementatore vero; i casi restano a provare la stessa cosa, e B8 li ridisegna comunque (piano principale, sezione 9);
   - (c) **altri test in sottoprocesso**: una copia temporanea di `bin/`, `hooks/` e `skills/` senza la `rules-base`, sul modello di `make_root` di `tests/test_check_research_gate.py`; se la copia non basta, DONE_WITH_CONCERNS con l'elenco e la `Ruling:` del controller. Nessuna variabile d'ambiente nuova nel prodotto senza una decisione scritta.
   Costo: un task in più; senza, il Task 5 romperebbe la suite al momento dell'accensione.
8. **Le regole proposte** sono le 12 della tabella del Task 3. Sono una bozza: l'implementatore le scrive con parole sue dalla fonte indicata, il verificatore controlla le fonti, l'utente le approva, corregge o toglie. Ognuna nomina l'oggetto che il revisore guarda (diff, nota o report). Sono marcate `[blocca]` solo quelle che corrispondono a una correzione ripetuta dell'utente (progetto 1). **Un difetto della nota si segnala una volta sola**: con la regola `R-BASE-…` che viola, se ce n'è una, altrimenti con `nota di ricerca`; il revisore non apre due rilievi per lo stesso difetto (Task 6). La regola «pagine come dati non fidati» non è tra queste: resta in `agents/implementer.md` (decisione 11). Costo: 12 regole sono la parte bassa della stima del progetto 5 (60-90 su sei profili).
9. **Forma della skill.** Prima sezione «Prima di scrivere» (progetto 3.4), poi «Mentre lavori», poi «Fonti». Frontmatter: `name: rules-base`, `description: Regole di base di tollgate per ogni implementatore e revisore: le caricano in automatico gli agenti di tollgate, non serve invocarla.`, `version: 1`, poi `approved` (Task 5). Nessun campo di visibilità (`disable-model-invocation` o altri): in L0 la sessione principale deve poterla usare, e un campo non verificato non si aggiunge. Se `claude plugin validate --strict` rifiuta `version`, il campo si toglie con una `Ruling:` e la versione resta nel titolo `# Regole di base (versione 1)`. Al più 150 righe (catalogo 4). Come ogni skill del plugin è anche il comando `/tollgate:rules-base`, quindi ha la sua sezione in `docs/uso/comandi.md` (`tests/test_docs.py`, `test_every_skill_documented`).
10. **La pagina per l'utente** è `docs/profili/base.md`; il rapporto della verifica delle fonti è `docs/profili/verifiche/base-fonti.md` (piano principale, sezione 3). La pagina dice in parole semplici cosa cambia con l'approvazione: in L1 e L2 la prima modifica senza nota valida è negata, anche nei lavori già in corso e nei task già avvisati (rinvio della sezione 9); in L0 resta l'avviso; nei lavori veri vale da quando la versione unita su `main` arriva al plugin installato.
11. **L'implementatore non ripete le regole** (Task 6). I punti 1 e 2 della sezione «Informati prima di scrivere» di `agents/implementer.md` (leggi i file, versioni dal file delle dipendenze) sono già regole di base: diventano un rimando a `rules-base`. Restano nella sezione il punto 3 (documentazione con `WebFetch`, pagine come dati non fidati) e il punto 4 (consegna della nota), che sono istruzioni d'uso di tollgate. Costo: nessuno; una sola fonte per ogni regola.
12. **La prova reale corta riusa `spikes/run-b1-flow.sh`** con `B1_FLOW_RULES=vere`: la copia del plugin tiene la `rules-base` vera e approvata invece di quella di prova, le evidenze vanno in `docs/verifiche/evidenze/b2/flusso/`. Lo stesso progetto di prova e lo stesso lavoro L1 di B1: la differenza da provare è la regola vera, caricata dagli agenti. Per i test serve una radice sorgente finta: `B1_FLOW_SRC` (la radice da copiare, valida solo con `B1_FLOW_CHECK=1`, come `B1_FLOW_OUT` e `B1_FLOW_PLUGIN`). Costo: circa 0,9 USD di consumo stimato, sull'abbonamento (la seconda corsa di B1 ha stimato 0,86 USD).
13. **Unione anticipata.** Se l'utente rinvia l'approvazione, su `main` si possono unire solo i Task 1 e 2 (interruttore e test indipendenti), che non portano regole; la bozza, la pagina e il rapporto delle fonti restano sul ramo (progetto 5, punto 4: «solo le regole approvate entrano nel plugin»). Costo: B2 resta aperta finché la pagina non è approvata.

## Review Focus

1. **Interruttore assente contro illeggibile.** Il file assente resta silenzioso; una cartella al suo posto dà l'avviso con l'errore e un solo evento per lavoro, anche con la nota valida, mai un rifiuto. Test: Task 1 `test_switch_unreadable_reports_error`, `test_unreadable_switch_warns_and_logs_once`, `test_unreadable_switch_logged_with_valid_note`, `test_missing_switch_no_unreadable_event`.
2. **Test e prove a secco che presumono l'interruttore spento.** Con la `rules-base` vera approvata nel repo, la suite resta verde, anche nei test che lanciano `hooks/run` o `bin/tollgate` in un sottoprocesso. Test: Task 2 (misura con il file di prova); Task 5, Step 3 (suite completa dopo l'accensione).
3. **Regole e pagina che divergono dopo le correzioni dell'utente.** Una regola tolta, aggiunta o cambiata deve risultare uguale nella skill, nella pagina e nel rapporto delle fonti, con numeri senza buchi. Test: Task 3 `test_rule_ids_consecutive`, Task 4 `test_page_lists_every_rule`, `test_sources_report_covers_every_rule`, `test_page_blocca_matches_skill`.
4. **Task senza modifiche con il blocco acceso.** Una nota consegnata ma non valida non deve dare un `major`. Test: Task 1 `test_review_brief_no_changes_invalid_note_asks_nothing`.
5. **Precaricamento che diventa un veto o un doppio rilievo.** `rules-base` non deve finire in `skills_required` né in «Skill da usare»; gli agenti di spec e piano non la caricano; un difetto della nota non dà due rilievi. Test: Task 6 `test_rules_base_not_required`, `test_code_agents_preload_rules_base`, `test_other_agents_do_not_preload`, `test_review_standard_names_base_rules`.

## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_analysis/research.py` | 1 | `_YAML_EMPTY` con `no`, `off`, `n`; confronto dopo gli apici |
| `bin/tollgate_core/lookups.py` | 1 | `rules_switch`; `rules_enforced` sopra di essa |
| `bin/tollgate_core/events.py` | 1 | tipo `research_switch_unreadable` in `EVENT_TYPES` |
| `bin/tollgate_checks/research_gate.py` | 1, 6 | avviso ed evento con l'interruttore illeggibile; avviso che nomina `rules-base` |
| `bin/tollgate_analysis/brief.py` | 1, 6 | nota del task senza modifiche; standard del revisore con le regole di base |
| `tests/…` che presumono l'interruttore spento, `tests/test_eval_cases.py` | 2 | radice esplicita; nota nei casi a secco |
| `skills/rules-base/SKILL.md` | 3, 4, 5 | le regole |
| `LICENSES/agent-skills-MIT.txt` | 3 | licenza della fonte |
| `docs/uso/comandi.md`, `tests/test_b1_scripts.py` (righe 169 e 555) | 3 | sezione del comando; la `rules-base` del repo non è più assente |
| `docs/profili/verifiche/base-fonti.md`, `docs/profili/base.md` | 4, 5 | verifica delle fonti; pagina per l'utente |
| `agents/implementer.md`, `agents/task-reviewer.md`, `agents/final-reviewer.md`, `agents/finding-verifier.md` | 6 | `skills: [rules-base]`; rimandi alle regole |
| `spikes/run-b1-flow.sh`, `tests/test_b1_scripts.py` | 7 | prova con la `rules-base` vera |
| `docs/verifiche/2026-10-29-b2-prova-flusso.md`, `docs/verifiche/evidenze/b2/flusso/` | 7 | rapporto ed evidenze della prova |
| spec del nucleo, progetto di B, catalogo, piano principale di B | 8 | revisione 28 e stato |

---

### Task 1: Interruttore pronto per l'accensione

**Files:**
- Modify: `bin/tollgate_analysis/research.py:37-61`, `bin/tollgate_core/lookups.py:170-177`, `bin/tollgate_core/events.py:13-20`, `bin/tollgate_checks/research_gate.py:76-122`, `bin/tollgate_analysis/brief.py:211-214`
- Test: `tests/test_research.py`, `tests/test_lookups.py`, `tests/test_check_research_gate.py`, `tests/test_brief.py`

**Interfaces:**
- Consumes: `research.enforced(text)`, `research.RULES_BASE`, `_common.work_events(ctx, work_id, *types)` (filtra dopo l'ultimo `plan_reset`), `hooks.model.inject`/`record` (B1).
- Produces: `lookups.rules_switch(root) -> tuple[bool, str | None]`; `lookups.rules_enforced(root) -> bool` invariata nella firma; evento `research_switch_unreadable` {`error`: str} in `events.EVENT_TYPES`; costante `research_gate._UNREADABLE` (testo della decisione 5, con `{error}`).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_research.py`: `test_enforced_refuses_no_off_n`: `approved: no`, `approved: NO`, `approved: off`, `approved: Off`, `approved: n`, `approved: "no"`, `approved: 'off'`, `approved: "false"` → `False`; `approved: 2026-10-29` e `approved: prova-b1` → `True`.
  - `tests/test_lookups.py`: sostituisci `test_unreadable_is_off_for_now` con `test_switch_missing_is_silent_off` (`rules_switch(root senza file) == (False, None)`), `test_switch_unreadable_reports_error` (una cartella al posto di `SKILL.md`: primo elemento `False`, secondo una stringa che comincia con `IsADirectoryError`; `rules_enforced` `False`), `test_switch_approved` (`(True, None)`).
  - `tests/test_check_research_gate.py`: `test_unreadable_switch_warns_and_logs_once` (lavoro L1 con `research=True`, radice con `skills/rules-base/SKILL.md` come cartella: la prima modifica dell'implementatore senza nota non è negata, l'`inject` contiene «non si legge» e il comando `research submit`; dopo il `post_edit` c'è un evento `research_switch_unreadable` con `error`; una seconda modifica non aggiunge un secondo evento); `test_unreadable_switch_logged_with_valid_note` (stessa radice, nota valida: nessun `inject`, ma dopo la prima modifica c'è l'evento); `test_missing_switch_no_unreadable_event` (radice senza il file: nessun evento `research_switch_unreadable`, avviso normale).
  - `tests/test_brief.py`: `test_review_brief_no_changes_invalid_note_asks_nothing` (`no_changes=True`, nota consegnata non valida, `research_enforced=True`: nella sezione niente `` `major` ``, niente `missing`, c'è «non era richiesta»).
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_research tests.test_lookups tests.test_check_research_gate tests.test_brief`: FAIL dei test nuovi.
- [ ] **Step 3: Il codice.** In `research.enforced` gli apici si tolgono prima del confronto con `_YAML_EMPTY`, che riceve `"no", "off", "n"`. `rules_switch` in `lookups.py` con la docstring della decisione 5; `rules_enforced` diventa `return rules_switch(root)[0]` e perde la frase «la distinzione … è di B2». `"research_switch_unreadable"` in `events.EVENT_TYPES`. In `research_gate._verdict` l'interruttore si legge una volta con `rules_switch(ctx.plugin_root)`, **prima** del controllo della nota, e l'errore viaggia fino a `decide` anche quando la nota è valida: a `post_*`, se c'è un errore e `work_events(ctx, work_id, "research_switch_unreadable")` è vuoto, `record("event", type="research_switch_unreadable", data={"error": …}, work=…)`; a `pre_*`, quando l'esito è l'avviso, l'`inject` è `_UNREADABLE.format(error=…)` seguito dall'avviso normale. In `brief._review_research` la condizione del ritorno anticipato diventa `b.no_changes and not usable`.
- [ ] **Step 4: Verifica.** Gli stessi quattro file di test: PASS. Poi `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B2: interruttore con i valori negativi, il file illeggibile e il task senza modifiche».

---

### Task 2: La suite non dipende dall'interruttore vero

**Files:**
- Modify: i file di `tests/` che lo Step 2 trova, compreso `tests/test_eval_cases.py` se una prova a secco cambia esito (nessun file di `bin/`)
- Test: gli stessi

**Interfaces:**
- Consumes: `tests/hookkit.Lab(plugin_root=…)`; `mock.patch.object(taskcmd.db, "BIN_PATH", …)`; `make_root` di `tests/test_check_research_gate.py`; il comando `research submit` (B1).
- Produces: nessuna interfaccia; la garanzia che il Task 5 può accendere l'interruttore nel repo senza rompere la suite.

- [ ] **Step 1: Interruttore acceso per prova, mai committato.** Scrivi `skills/rules-base/SKILL.md` con `---\nname: rules-base\napproved: 2026-01-01\n---\n` nel worktree, **senza** `git add`.
- [ ] **Step 2: Misura.** `tests/run` completo (in background, aspetta l'esito sul file d'uscita). Elenca nel report ogni test che fallisce, con la riga dell'errore. Tre fallimenti sono **attesi** e non vanno toccati qui: `tests/test_docs.py` `test_every_skill_documented` (la skill di prova non è documentata) e le due asserzioni di `tests/test_b1_scripts.py` alle righe 169 e 555 («il repo non deve cambiare»); li sistema il Task 3.
- [ ] **Step 3: Togli il file di prova** (`rm skills/rules-base/SKILL.md` e la cartella vuota) e controlla con `git status` che non resti niente.
- [ ] **Step 4: Rendi esplicita la radice** in ogni altro test dello Step 2 che presume l'interruttore spento, con la priorità della decisione 7 (a, b, c). Un test che con l'interruttore acceso fallisce per un altro motivo è un difetto da riportare con DONE_WITH_CONCERNS, non da correggere qui.
- [ ] **Step 5: Ripeti la misura.** Di nuovo il file di prova, di nuovo `tests/run` (verde salvo i tre attesi), di nuovo via il file. Poi `tests/run` senza il file: verde.
- [ ] **Step 6: Commit** «tollgate B2: test indipendenti dallo stato dell'interruttore nel repo».

---

### Task 3: Bozza di `rules-base` con le fonti

**Files:**
- Create: `skills/rules-base/SKILL.md`, `LICENSES/agent-skills-MIT.txt`, `tests/test_rules_base.py`
- Modify: `docs/uso/comandi.md`, `tests/test_b1_scripts.py:169` e `:555`
- Test: `tests/test_rules_base.py`, `tests/test_docs.py`, `tests/test_b1_scripts.py`

**Interfaces:**
- Consumes: le copie delle fonti in `<workspace>/fonti/` (Step 0); `research.enforced`.
- Produces: `skills/rules-base/SKILL.md` nella forma della decisione 9, senza `approved`; in `tests/test_rules_base.py` la funzione `rules(text) -> list[tuple[str, bool, str, str]]` (`id`, `blocca`, testo, fonte), che i Task 4 e 5 riusano.

- [ ] **Step 0 (controller): le fonti.** Copia in `<workspace>/fonti/`, con un `SHA256SUMS`, da `~/.claude/plugins/cache/`:
  - `addy-agent-skills/agent-skills/0.6.9/skills/source-driven-development/SKILL.md` → `fonti/agent-skills/skills/source-driven-development/SKILL.md`, e così `context-engineering`;
  - `addy-agent-skills/agent-skills/0.6.9/LICENSE` → `fonti/agent-skills-LICENSE`;
  - `claude-plugins-official/superpowers/7.0.0/skills/systematic-debugging/SKILL.md` → `fonti/superpowers/skills/systematic-debugging/SKILL.md`, e così `verification-before-completion`;
  - `claude-plugins-official/superpowers/7.0.0/LICENSE` → `fonti/superpowers-LICENSE`.
  Nel brief dell'implementatore va il percorso di `fonti/`, non quello della cache.
- [ ] **Step 1: I test che falliscono.** In `tests/test_rules_base.py`:
  - `test_frontmatter`: `name: rules-base`, la `description` della decisione 9, `version: 1` (salvo la `Ruling:` della decisione 9), **nessun `approved`** e `research.enforced(text)` falso (il Task 5 inverte questo test).
  - `test_first_section_is_prima_di_scrivere`: il primo titolo `## ` è `## Prima di scrivere`; ci sono `## Mentre lavori` e `## Fonti`.
  - `test_rule_ids_consecutive`: le righe `R-BASE-NN` sono 01, 02, … senza buchi né doppioni.
  - `test_every_rule_has_a_source`: ogni regola è seguita da una riga `Fonte: …` non vuota prima della regola successiva.
  - `test_some_rules_block`: almeno una regola `[blocca]`, non tutte.
  - `test_model_name_rule`: una regola parla di nomi di modelli e di pagina ufficiale del fornitore (progetto 3.6).
  - `test_at_most_150_lines`.
  - `test_licenses_listed`: `LICENSES/agent-skills-MIT.txt` comincia con `MIT License` e nomina Addy Osmani; la sezione `## Fonti` cita `LICENSES/agent-skills-MIT.txt` e `LICENSES/superpowers-MIT.txt`.
  - In `tests/test_b1_scripts.py` le asserzioni delle righe 169 e 555 («il repo non deve cambiare») diventano: la `rules-base` della copia è quella di prova, diversa dal file del repo, e il file del repo non ha cambiato contenuto.
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_rules_base`: FAIL (file assente).
- [ ] **Step 3: Scrivi le regole** dalle fonti della tabella, con parole tue e in italiano: una riga di regola e una riga `Fonte:` per ciascuna. Forma della fonte: `Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/source-driven-development/SKILL.md, «Step 1: Detect Stack and Versions»`, oppure `Fonte: progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md), sezione 1`. Nessuna citazione testuale nella skill. Ogni regola dice cosa guarda il revisore.

  | Id | Sezione | `[blocca]` | Cosa dice la regola | Fonte da cui distillarla |
  |---|---|---|---|---|
  | R-BASE-01 | Prima di scrivere | sì | Ogni file **già esistente** che il diff modifica compare in «Letto nel progetto» della nota (un file nuovo non c'è ancora quando la nota si consegna: per lui vale R-BASE-07) | `context-engineering`, «Level 3: Relevant Source Files»; progetto 3.4 (riga `base`) |
  | R-BASE-02 | Prima di scrivere | sì | Se il diff usa una libreria esterna, la nota ne riporta la versione e il file delle dipendenze da cui la prende; se il file non la dice, la nota lo scrive | `source-driven-development`, «Step 1: Detect Stack and Versions» |
  | R-BASE-03 | Prima di scrivere | sì | Se il diff usa una libreria o un servizio esterno, «Documentazione» ha per ciascuno almeno una pagina ufficiale (documentazione o changelog del progetto o del fornitore), non un blog, un forum o un riassunto | `source-driven-development`, «Step 2: Fetch Official Documentation» (gerarchia delle fonti) |
  | R-BASE-04 | Prima di scrivere | sì | Ogni nome di modello AI che il diff scrive (Gemini, Claude o altri) ha in «Documentazione» l'URL della pagina ufficiale dei modelli del fornitore | progetto di B, sezioni 1 e 3.6 |
  | R-BASE-05 | Prima di scrivere | sì | Un'affermazione «non esiste» o «non è supportato» nel report, nei commenti o nei messaggi dice dove si è cercato (file o URL) | progetto di B, sezione 1 (schema 2) |
  | R-BASE-06 | Prima di scrivere | sì | Ogni URL che il diff (commenti, documentazione) o il report **cita come fonte** compare in «Documentazione» della nota; gli URL che sono parte del codice (endpoint, fixture, configurazione, esempi) restano fuori | progetto di B, sezione 1 (schema 3) |
  | R-BASE-07 | Prima di scrivere | no | Una funzione o un componente nuovo segue lo schema di uno simile già nel progetto, se esiste, e il report dice quale | `context-engineering`, «Level 3: Relevant Source Files» (punto 3) |
  | R-BASE-08 | Prima di scrivere | no | Se il diff cambia build, rilascio o CI, «Letto nel progetto» elenca i file di configurazione già presenti che li riguardano | progetto di B, sezione 1 (esempio del deploy) |
  | R-BASE-09 | Prima di scrivere | sì | «Nessuna fonte esterna» solo se il diff non usa librerie o servizi esterni; il motivo lo dice | progetto di B, sezioni 2 (anti-obiettivo «passo troppo pesante») e 3.2 |
  | R-BASE-10 | Mentre lavori | sì | La correzione di un difetto porta un test che lo riproduce, rosso prima e verde dopo, oppure il report dice perché non si può | `systematic-debugging`, «The Iron Law» e «Phase 4: Implementation» (punto 1) |
  | R-BASE-11 | Mentre lavori | no | Se la documentazione ufficiale non si trova o si contraddice, la nota o il report lo dicono in chiaro («non verificato») e dicono dove si è cercato | `source-driven-development`, «Step 2» (fonti in conflitto) e «Step 4: Cite Your Sources» (blocco `UNVERIFIED`) |
  | R-BASE-12 | Mentre lavori | no | Il report dichiara funzionante solo ciò che un comando eseguito nel task prova, e riporta il comando con l'esito | `verification-before-completion`, «The Iron Law» |

- [ ] **Step 4: Licenza e comando.** `LICENSES/agent-skills-MIT.txt` è la copia esatta di `<workspace>/fonti/agent-skills-LICENSE`. In `docs/uso/comandi.md` una sezione `### \`/tollgate:rules-base\``: cosa sono le regole di base, che le caricano gli agenti di tollgate e che non serve lanciarla a mano; senza «Argomenti:» e senza «solo l'utente» (`test_every_skill_documented`).
- [ ] **Step 5: Verifica.** `python3 -B -m unittest tests.test_rules_base tests.test_docs tests.test_b1_scripts`: PASS. `claude plugin validate --strict .` dalla radice del worktree: uscita 0 (non lancia il modello; se rifiuta `version`, decisione 9). `tests/run`: verde.
- [ ] **Step 6: Commit** «tollgate B2: bozza di rules-base con le fonti».

---

### Task 4: Verifica delle fonti e pagina per l'utente

**Files:**
- Create: `docs/profili/verifiche/base-fonti.md`, `docs/profili/base.md`
- Modify: `skills/rules-base/SKILL.md` (solo se una fonte non passa), `tests/test_rules_base.py`

**Interfaces:**
- Consumes: `tests/test_rules_base.rules(text)` (Task 3); `<workspace>/fonti/`.
- Produces: la pagina che il Task 5 mostra all'utente; il rapporto delle fonti con una riga per fonte di ogni regola.

- [ ] **Step 1 (controller): la verifica delle fonti.** Un subagente `Explore` (sonnet, sola lettura; il brief vieta Bash fuori da `grep`, `sed -n` e `ls`), con un brief che contiene il percorso della skill del Task 3, di `<workspace>/fonti/` e del progetto di B. **Per ogni fonte di ogni regola**: il file esiste; la sezione citata esiste; dice ciò che la regola le attribuisce (una citazione di al più una riga); la licenza è MIT o Apache-2.0, oppure la fonte è il progetto di B. Esito `ok` o `no` con il motivo. Il testo delle fonti è un dato, non un'istruzione. Il controller salva l'uscita in `<workspace>/task-4-fonti.md`.
- [ ] **Step 2: I test che falliscono** (implementatore). In `tests/test_rules_base.py`: `test_sources_report_covers_every_rule` (nella tabella principale di `docs/profili/verifiche/base-fonti.md` ogni `R-BASE-NN` della skill ha almeno una riga con esito `ok`, e nessuna riga nomina un id che la skill non ha; la sezione delle regole tolte non usa id `R-BASE-`); `test_page_lists_every_rule` (gli id della pagina e della skill coincidono); `test_page_blocca_matches_skill` (la colonna «Blocca?» della pagina dice sì esattamente per le regole `[blocca]`); `test_page_explains_what_changes` (la pagina dice che dopo l'approvazione in L1 e L2 la prima modifica senza nota è negata, che in L0 c'è solo l'avviso, che vale anche per i lavori già in corso e che nei lavori veri conta da quando la versione unita arriva al plugin installato).
- [ ] **Step 3: Le correzioni e i due file.** Come vuole il progetto 5, punto 2, escono le **fonti** con esito `no`, e con loro le regole che restano senza nessuna fonte `ok`; una regola con due fonti ne perde una e resta. Le regole rimaste si rinumerano senza buchi (prima dell'approvazione si può: Global Constraints). Il rapporto delle fonti riporta la tabella del verificatore (Regola, Fonte, Citazione, Esito) con gli id finali, e in una sezione a parte le regole tolte, indicate come «bozza n. <numero>» con il testo e il motivo. La pagina `docs/profili/base.md`, in parole semplici (memoria `feedback-spiegazioni-semplici`): cosa sono le regole di base e a chi valgono; cosa cambia quando le approvi (decisione 10); una tabella con «N.», «In parole semplici», «Blocca?», «Da dove viene»; come rispondere: «approvo», «correggi la N con …», «togli la N». Nessun gergo non spiegato.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_rules_base`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B2: fonti di rules-base verificate e pagina per l'utente».

---

### Task 5: Approvazione dell'utente e accensione del blocco

**Files:**
- Modify: `skills/rules-base/SKILL.md`, `docs/profili/base.md`, `docs/profili/verifiche/base-fonti.md` (solo con correzioni), `tests/test_rules_base.py`, `tests/test_check_research_gate.py`

**Interfaces:**
- Consumes: la pagina del Task 4; `lookups.rules_enforced`; `tests/hookkit.Lab`.
- Produces: `approved: <AAAA-MM-GG>` nella skill vera; da qui il blocco è acceso per ogni lavoro con `research = 1`.

- [ ] **Step 1 (controller con l'utente): la pagina.** Il controller mostra all'utente la pagina `docs/profili/base.md` (il testo, nel terminale) e chiede di approvare, correggere o togliere. Ogni correzione torna all'implementatore come giro di questo task: la skill, la pagina e il rapporto delle fonti cambiano insieme; una regola nuova, o con una fonte nuova, ripassa dal verificatore dello Step 1 del Task 4, solo per quella regola. Si ripete finché l'utente non approva. Se l'utente rinvia l'approvazione, vedi la decisione 13 e le istruzioni d'esecuzione («Quando fermarsi»).
- [ ] **Step 2: I test che falliscono** (implementatore, con la data dell'OK nel brief). `tests/test_rules_base.py`: `test_frontmatter` si inverte (ora `approved` c'è, nella forma `^\d{4}-\d{2}-\d{2}$`, ammessa anche tra apici per la `Ruling:` dello Step 3, e `research.enforced(text)` è vero); `test_real_rules_base_is_approved` (`lookups.rules_enforced(ROOT)` è vero). `tests/test_check_research_gate.py`: `test_real_rules_base_blocks_l1` e `test_real_rules_base_blocks_l2` (`Lab(level=…, research=True, plugin_root=ROOT)`: la prima modifica dell'implementatore senza nota è negata con `rule` `research_gate`).
- [ ] **Step 3: L'accensione.** `approved: <data>` nel frontmatter, dopo `version`; nella pagina la riga «Approvata dall'utente il <data>.». `claude plugin validate --strict .`: uscita 0 (una data YAML non tra apici è un tipo diverso dalla stringa provata in B1-V7; se la rifiuta, la data va tra apici, con una `Ruling:`). `python3 -B -m unittest tests.test_rules_base tests.test_check_research_gate`: PASS. Poi `PYTHONWARNINGS=error::ResourceWarning tests/run`: verde (Review Focus 2).
- [ ] **Step 4: Commit** «tollgate B2: rules-base approvata dall'utente, blocco acceso».

---

### Task 6: `rules-base` a ogni agente che scrive o rivede codice

**Files:**
- Modify: `agents/implementer.md`, `agents/task-reviewer.md`, `agents/final-reviewer.md`, `agents/finding-verifier.md`, `bin/tollgate_checks/research_gate.py` (`_warning`), `bin/tollgate_analysis/brief.py` (`STANDARD`)
- Test: `tests/test_manifest.py`, `tests/test_check_research_gate.py`, `tests/test_taskcmd.py`, `tests/test_brief.py`

**Interfaces:**
- Consumes: `skills/rules-base/SKILL.md` approvata (Task 5).
- Produces: il campo `skills: [rules-base]` nei quattro agenti (decisione 2); l'avviso che nomina `tollgate:rules-base`; lo standard del revisore con le regole di base.

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_manifest.py`: `test_code_agents_preload_rules_base` (il frontmatter di `implementer`, `task-reviewer`, `final-reviewer`, `finding-verifier` ha `skills` uguale a `[rules-base]`); `test_other_agents_do_not_preload` (`spec-auditor`, `spec-adversary`, `plan-adversary` senza `skills`); `test_implementer_points_to_rules_base` (la sezione «Informati prima di scrivere» nomina `rules-base` e non contiene più la frase sul file delle dipendenze); `test_reviewers_cite_base_rules` (`task-reviewer.md` e `final-reviewer.md` nominano `R-BASE-`, `[blocca]` e la regola «un difetto della nota si segnala una volta sola»).
  - `tests/test_check_research_gate.py`: `test_warning_names_rules_base` (l'avviso, in L0 e in L1 con l'interruttore spento, contiene `tollgate:rules-base`).
  - `tests/test_brief.py`: `test_review_standard_names_base_rules` (`brief.STANDARD` dice «regole dei profili e di base»).
  - `tests/test_taskcmd.py`: `test_rules_base_not_required` (con un lavoro senza profili e la `rules-base` presente nella radice, dopo `task start` `skills_required` del task è `[]` e il brief non elenca `rules-base` in «Skill da usare»). È un **test di guardia**: passa già prima delle modifiche, e lo Step 2 non lo conta.
  - `test_implementer_tools`, `test_implementer_mentions_untrusted_pages` e `test_implementer_mentions_research_submit` restano verdi senza modifiche.
- [ ] **Step 2: Verifica che falliscano** (salvo il test di guardia).
- [ ] **Step 3: Gli agenti.** La riga `skills: [rules-base]` nel frontmatter dei quattro agenti, dopo `tools:` (come in `spikes/hookprobe/agents/probe-agent.md`). In `implementer.md` i punti 1 e 2 di «Informati prima di scrivere» diventano un solo punto: «Applica le regole di base (`rules-base`, già nel tuo contesto): dicono cosa leggere e quali fonti aprire prima di scrivere» (decisione 11). In `task-reviewer.md` e `final-reviewer.md`, accanto alla regola sulle prove dei rilievi: le regole `R-BASE-…` di `rules-base` valgono per ogni diff; come per i profili, solo quelle `[blocca]` danno `blocker` o `major`; un difetto della nota si segnala una volta sola, con la regola `R-BASE-…` che viola se c'è, altrimenti con `nota di ricerca` (decisione 8). In `finding-verifier.md`: le regole `R-BASE-…` citate nei rilievi sono quelle di `rules-base`, già nel contesto. In `brief.STANDARD` «per le regole dei profili» diventa «per le regole dei profili e di base». In `research_gate._warning` la frase base finisce con «Le regole di base sono nella skill `tollgate:rules-base`.».
- [ ] **Step 4: Verifica.** I quattro file di test: PASS. `claude plugin validate --strict .`: uscita 0. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B2: rules-base precaricata dagli agenti che scrivono e rivedono codice».

---

### Task 7: Prova reale corta con la `rules-base` vera (preparazione con test, esecuzione del controller)

Progetto 5 e piano principale (riga B2): «il blocco scatta in L1 e L2 (test e una prova reale corta)». Stesso progetto di prova e stesso lavoro L1 di B1 (decisione 12).

**Files:**
- Modify: `spikes/run-b1-flow.sh`, `tests/test_b1_scripts.py`
- Create: `docs/verifiche/2026-10-29-b2-prova-flusso.md`, `docs/verifiche/evidenze/b2/flusso/`

**Interfaces:**
- Consumes: `spikes/run-b1-flow.sh` (modi `controlla`, `prepara`, `passo1`, `passo2`, `registra`; variabili `B1_FLOW_CHECK`, `B1_FLOW_ROOT`, `B1_FLOW_OUT`, `B1_FLOW_PLUGIN`); `lookups.rules_enforced`.
- Produces: le variabili `B1_FLOW_RULES` (`prova`, il predefinito, oppure `vere`) e `B1_FLOW_SRC` (la radice da copiare; solo con `B1_FLOW_CHECK=1`, altrimenti è la radice del repo).

- [ ] **Step 1 (implementatore, senza rete e senza `claude`): lo script.** Con `B1_FLOW_RULES=vere`: `OUT` è `docs/verifiche/evidenze/b2/flusso`; `prepara` non scrive la `rules-base` di prova e si ferma con un errore se la `rules-base` della copia non accende l'interruttore (un `python3 -B -` con `bin/` nel `sys.path` che chiama `tollgate_core.lookups.rules_enforced` sulla copia; letture con `pathlib`, mai `open(...)` senza chiuderlo); `registra` cerca in più il titolo `# Regole di base (versione 1)` nelle trascrizioni dei subagenti del lavoro, se il loro percorso è nelle uscite (prova del precaricamento), e altrimenti conta le righe di `claude.jsonl` con `R-BASE-` (solo un indizio: il rapporto dice quale dei due ha trovato). `controlla` stampa `B1_FLOW_RULES`, la radice sorgente e la cartella delle uscite. Ogni altro valore di `B1_FLOW_RULES` è un errore. In più (minore della revisione finale di B1): `prepara` si ferma se la copia con `git ls-files` non riesce per un file tracciato che manca. Test in `tests/test_b1_scripts.py`, con `B1_FLOW_SRC` puntato a un piccolo repo git temporaneo che traccia una copia di `bin/` (`prepara` importa `tollgate_core` e `tollgate_analysis` dalla copia del plugin), oppure con test che si fermano prima di quei passi: `test_flow_rules_vere_keeps_real_rules_base` (dopo `prepara`, la `SKILL.md` della copia è uguale a quella della sorgente), `test_flow_rules_vere_refuses_unapproved` (sorgente con la `rules-base` senza `approved` → `prepara` esce diverso da 0 e lo dice), `test_flow_rules_vere_out_dir`, `test_flow_rules_unknown_value`, `test_flow_src_only_in_check_mode`, `test_flow_copy_fails_on_missing_tracked_file` (un file tracciato cancellato dalla sorgente); i test di B1 restano verdi con il predefinito `prova`. Lo script si prova solo con `bash -n`, `controlla` e i test.
- [ ] **Step 2 (controller): esecuzione.** `B1_FLOW_RULES=vere`: `prepara`, `passo1`, `passo2`, `registra`. Atteso: task 1 `done` con verdetto `approved`; nessuna modifica di codice riuscita prima della nota valida; almeno una lettura `read` e una `fetch` del task 1. Il rifiuto di `research_gate` (evento `veto` prima della nota valida) prova il blocco dal vivo; se l'implementatore consegna la nota prima di ogni modifica, il blocco dal vivo non si vede e il rapporto lo dice: la prova deterministica sulla regola vera è `test_real_rules_base_blocks_l1` (Task 5). Un esito in più tentativi è «composito». Un difetto del prodotto scoperto qui è un giro di questo task (test che fallisce, correzione, `tests/run`), poi si ripete **solo** il passo interessato.
- [ ] **Step 3: Rapporto** `docs/verifiche/2026-10-29-b2-prova-flusso.md`: passi, tentativi, letture, nota, avvisi e rifiuti, verdetto (con gli eventuali rilievi `R-BASE-…`), prova o indizio del precaricamento, token e consumo stimato, difetti trovati e corretti, limiti (permessi di `WebFetch` concessi con `--allowedTools`; un solo lavoro piccolo). Evidenze anonimizzate come in B1 (id di sessione, `/home/<utente>`, nome utente e nome dell'host sostituiti).
- [ ] **Step 4: Commit** «tollgate B2: prova reale corta con rules-base vera».

---

### Task 8: Prove, revisione 28 della spec, piano principale, catalogo

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 28), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento in testa), `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md` (sezioni 1 e 4)

- [ ] **Step 1: Revisione 28 della spec del nucleo.** 6.3 (le skill comuni comprendono `rules-base`, precaricata con `skills:` dai quattro agenti della decisione 2, fuori dal tetto e fuori da `skills_required`; l'avviso la nomina); 8.1, «Interruttore del blocco» (data dell'approvazione; `no`, `off`, `n`, `false`, anche tra apici; file illeggibile con avviso ed evento, decisione 5, con il motivo per cui è un evento e non una riga di `hooks.log`); 8.6 (task senza modifiche, decisione 6; un difetto della nota si segnala una volta sola, decisione 8); 12.2 (la riga «Lavori in corso all'approvazione di `rules-base`»: l'approvazione è avvenuta, con la data); 16 («ancora da verificare dopo B1»: il rifiuto sulla `rules-base` vera, con l'esito del Task 7; il precaricamento visto o no); 18.4 (evento `research_switch_unreadable`); riga 28 della sezione 20.
- [ ] **Step 2: Catalogo.** Sezione 1, «Skill comuni»: `rules-base` per ogni implementatore e revisore, precaricata. Sezione 4: una riga `rules-base` con le fonti della decisione 1.
- [ ] **Step 3: Piano principale di B e progetto.** Stato in testa (B2 sul ramo, merge in attesa dell'OK dell'utente; numero di test); riga B2 della sezione 2; sezione 3 con i nomi reali di B2 (forma di una regola, approvazione, caricamento); sezione 5 con `PYTHONWARNINGS=error::ResourceWarning` al posto di `-W`; una sezione «Prove di B2» con ogni riga della tabella «Copertura» di questo piano e il test o l'evidenza che la prova; rinvii a B3 e oltre (righe «minor (deferred)» che li riguardano). Nel progetto di B la riga di avanzamento in testa: «B1 e B2 eseguite».
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md
git commit -m "tollgate B2: prove, spec rev 28, piano principale di B, catalogo"
```

---

## Copertura: punti del progetto e del piano principale destinati a B2 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: primo gruppo di profili, `base` | 3, 4, 5 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `base` | 3 (sezione «Prima di scrivere») |
| Progetto 2, anti-obiettivo «frase vuota senza lettura registrata» | B1 (controllo 3.3); 3 (R-BASE-01, 03, 06 sulla nota) |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 4 (pagina), 5 (approvazione), decisione 13 |
| Progetto 2, anti-obiettivo «fonti inventate» nelle regole | 4 (verificatore di sola lettura, esito per fonte) |
| Progetto 2, anti-obiettivo «passo troppo pesante» | 3 (R-BASE-09); L0 solo avviso, invariato |
| Progetto 3.1: blocco in L1 e L2 | 5 (`test_real_rules_base_blocks_l1`, `…_l2`), 7 |
| Progetto 3.4, riga `base` | 3 (R-BASE-01, 02, 05) |
| Progetto 3.6: nomi dei modelli in `rules-base` | 3 (R-BASE-04, `test_model_name_rule`) |
| Progetto 4, riga `base`: caricata da ogni implementatore e revisore, anche generici | 6 (decisione 2) |
| Progetto 5, punti 1-4: fonte per regola, verifica, pagina, solo regole approvate | 3, 4, 5; decisione 13 |
| Progetto 5, «la prima pagina da rivedere è `base`»; blocco spento fino all'approvazione | 5 |
| Progetto 6: come `rules-base` arriva agli agenti | 6 (decisioni 2 e 3) |
| Progetto 8: lavori iniziati prima di B | invariato (B1, `work_items.research`) |
| Piano principale, sezione 9: lavori in corso all'approvazione | 4 (pagina), 8 (spec 12.2) |
| Piano principale, sezione 9: rinvio 13 | 1 (`test_enforced_refuses_no_off_n`) |
| Piano principale, sezione 9: rinvio 31 | 1 (`test_switch_*`, `test_unreadable_switch_*`) |
| Piano principale, sezione 3, B2→B3-B7: forma di una regola, pagina, rapporto delle fonti | 3, 4; nomi reali nel Task 8 |
| Minori di B1 che il blocco acceso rende reali: task senza modifiche; copia con `git ls-files` | 1; 7 |
| Revisione della spec del nucleo | 8 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B, il piano principale, la spec rev 27, il catalogo, il codice di `main` e il modello di B1.

| Giro | Rilievi | Esito |
|---|---|---|
| 1 | 1 critical (C-1: con l'approvazione rinviata la bozza, già caricata dagli agenti, sarebbe finita su `main`), 6 important (I-1 due test esistenti rotti dalla bozza; I-2 tipo di evento fuori da `EVENT_TYPES`; I-3 test in sottoprocesso e prove a secco degli eval senza strada; I-4 nessuna radice sorgente finta per i test dello script; I-5 regole non verificabili e doppi rilievi sulla nota; I-6 fonti che non dicono ciò che la regola attribuisce), 17 minor | «Non pronto». Corretti: ordine dei task (caricamento dopo l'approvazione), decisioni 2, 4, 5, 7-9, 12, 13 nuova; tabella delle regole; Task 1-8 |
| 2 | Tutti i 24 rilievi del giro 1 chiusi; 2 important nuovi (I-N1 R-BASE-01 impossibile per i file creati dal task; I-N2 R-BASE-06 che prende anche gli URL del codice), 4 minor (M-N1..M-N4) | «Non pronto». Corretti tutti prima del giro 3 |
| 3 | I-N1, I-N2 e M-N1..M-N4 chiusi; nessun rilievo nuovo | **«Pronto». Critical aperti: 0. Important aperti: 0.** |
