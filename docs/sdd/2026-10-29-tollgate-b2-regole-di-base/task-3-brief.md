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

