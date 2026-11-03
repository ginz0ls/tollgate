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

