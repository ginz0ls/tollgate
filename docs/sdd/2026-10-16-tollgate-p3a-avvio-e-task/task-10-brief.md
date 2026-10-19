### Task 10: Agenti, skill, manifest e licenze

**Files:**
- Create: `agents/implementer.md`, `agents/task-reviewer.md`
- Create: `skills/start/SKILL.md`, `skills/execute/SKILL.md`, `skills/status/SKILL.md`, `skills/approve/SKILL.md`, `skills/resolve/SKILL.md`, `skills/setup/SKILL.md`
- Create: `.claude-plugin/marketplace.json`, `LICENSE`, `LICENSES/superpowers-MIT.txt`
- Modify: `.claude-plugin/plugin.json`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: gli esiti V1 e V4 del Task 1; i sottocomandi dei Task 3-9.
- Produces: i nomi `tollgate:implementer` e `tollgate:task-reviewer`, che `profiles.DEFAULT_*` già usa.

Contenuti (testo in italiano, identificatori in inglese):

**`agents/implementer.md`**
- Frontmatter: `name: implementer`, `description` (implementatore di un task del piano lanciato da `tollgate:execute`), `tools: Read, Edit, Write, Bash, Grep, Glob, Skill`, `model: inherit`, `maxTurns: 60`.
- Corpo derivato da `implementer-prompt.md` di Superpowers 7.0.0, con in testa la riga di attribuzione «Derivato da superpowers/skills/subagent-driven-development (MIT, © 2025 Jesse Vincent); vedi LICENSES/superpowers-MIT.txt». Le sezioni:
  - leggere prima il brief indicato nel prompt;
  - fare domande prima di cominciare;
  - lavoro in TDD;
  - mai lanciare subagenti;
  - organizzazione del codice e quando fermarsi;
  - autorevisione;
  - le skill del brief da invocare con lo strumento Skill, più `superpowers:test-driven-development` e `superpowers:systematic-debugging` quando servono;
  - prima di DONE: commit e `tollgate verify` green;
  - conflitto tra test e specifica: `tollgate block open test_spec_conflict --reason …` e BLOCKED;
  - messaggio finale con **un solo** blocco JSON di 18.5, con i campi alla lettera, e `size_reason` oltre `task_lines_max`.

**`agents/task-reviewer.md`**
- Frontmatter: `name: task-reviewer`, `tools: Read, Grep, Glob, Bash`, `model: sonnet`.
- Corpo derivato da `task-reviewer-prompt.md`, con la stessa riga di attribuzione:
  - leggere il brief del revisore, il brief del task e il file del diff indicati;
  - sola lettura, mai lanciare subagenti;
  - non fidarsi del report;
  - parte 1, aderenza; parte 2, qualità;
  - standard del revisore (8.6): approvare se il cambiamento migliora la salute del codice; solo `blocker` e `major` chiedono modifiche; ogni rilievo con `file`, `line` e `rule` (`R-…` o il passo del piano), altrimenti non vale; cercare difetti, non confermare;
  - chiusura con **un solo** blocco JSON del revisore del task di 18.5, con `sha` e `code` copiati dal brief.

**`skills/start/SKILL.md`** (anche il modello)
- Frontmatter: `name: start`, `description`, `argument-hint: "#N [L1|L2]"`.
- Corpo:
  - lanciare `<programma> start <N> [--level L]` dal checkout principale;
  - uscita 3: mostrare all'utente gli avvisi e chiedere; solo con il suo sì rilanciare con `--confirm`;
  - uscita 0: `EnterWorktree` con il percorso dell'ultima riga; se non riesce, dire «cd <percorso> && claude» e fermarsi;
  - poi, per livello:
    - L0: implementa la sessione;
    - L1: checkpoint (`status --checkpoint`), `/clear` e writing-plans con le intestazioni di 7.5;
    - L2: brainstorming, fermarsi dopo la spec (P3c);
  - writing-plans chiude con un rimando a subagent-driven-development: si usa invece `/tollgate:execute` (6.3).

**`skills/execute/SKILL.md`** (anche il modello). Il ciclo di 6.3, derivato dal processo di subagent-driven-development con la riga di attribuzione:
- Passo 0: controllo del piano (task che si contraddicono, file condivisi) annotato con `status --checkpoint --note`.
- Per ogni task non `done`, in ordine:
  - `task start k`;
  - `Agent` con `subagent_type` = tipo del riepilogo, `name` = quello del riepilogo, in primo piano, prompt = percorso del brief; `model` solo se il riepilogo lo indica;
  - alla risposta, `task review-prepare k`;
  - `Agent` del revisore con il percorso del brief del revisore;
  - con `approved`: `task done k`;
  - con `changes`: `task start k --fix`. Giri 1-3: `SendMessage` al `name` con il percorso del file dei rilievi. Giri 4-5: un nuovo `Agent` con il nome `-r<giro>` e `model: inherit`.
  - Con NEEDS_CONTEXT si risponde riprendendo lo stesso implementatore.
  - Con BLOCKED, o un veto di budget, ci si ferma, si riferisce all'utente e si indica `/tollgate:resolve`.
- Guardia del contesto: all'avviso di `warn_pct` si scrive il checkpoint; a `stop_pct`, checkpoint, `/clear` e ripresa dal primo task non chiuso.
- Fine dei task: `/tollgate:finish`.
- Mai subagent-driven-development, mai implementatori `general-purpose`.

**Altre skill**
- **`skills/status/SKILL.md`**: `<programma> status` (sola lettura) e `stats --work N` su richiesta.
- **`skills/approve/SKILL.md`** (`disable-model-invocation: true`): l'atto è già registrato dal hook.
  - Per `level`, lanciare `<programma> act apply` e riferire.
  - Per `waiver` ed `effect`, dire che l'approvazione vale già e non lanciare nulla.
  - Per gli altri oggetti: «arriva con /tollgate:finish (P3b) o con il percorso L2 (P3c)».
- **`skills/resolve/SKILL.md`** (`disable-model-invocation: true`): `<programma> act apply` e riferire la fase.
- **`skills/setup/SKILL.md`** (`disable-model-invocation: true`): leggere `~/.claude/settings.json` senza modificarlo e mostrare la modifica di `statusLine.command` (decisione 21). Se c'è già una statusline, proporre `"<radice>/statusline/ctx <comando attuale>"`, altrimenti `"<radice>/statusline/ctx <radice>/statusline/statusline.sh"`. La modifica la fa l'utente: il file è protetto.

Ogni skill indica il programma come `${CLAUDE_PLUGIN_ROOT}/bin/tollgate` oppure con la riga «programma» (esito V1).

**Manifest e licenze**
- `plugin.json`: aggiungere `"author": {"name": "sAInapse"}` e `"license": "MIT"`. `dependencies` resta senza `version`.
- `marketplace.json`: `name: "sainapse"`, `owner: {"name": "sAInapse"}`, `plugins: [{"name": "tollgate", "source": "./", "description": …}]`, `allowCrossMarketplaceDependenciesOn: ["claude-plugins-official"]`, oppure i campi che V4 ha indicato come validi.
- `LICENSE`: MIT, «Copyright (c) 2026 sAInapse».
- `LICENSES/superpowers-MIT.txt`: copia del LICENSE di Superpowers 7.0.0.

- [ ] **Step 1: Test** (`test_manifest.py`, aggiunte):
  - `test_agents_frontmatter`: parser minimo del frontmatter YAML, solo `chiave: valore`. `implementer` ha `maxTurns: 60`, `model: inherit` e i 7 strumenti; `task-reviewer` ha `model: sonnet` e non ha `Edit` né `Write`; entrambi hanno la riga di attribuzione.
  - `test_user_only_skills` (`approve`, `resolve`, `setup`, `off`, `on` → `disable-model-invocation: true`; `start`, `execute`, `status` → no).
  - `test_skills_never_mention_sdd_as_executor` (`execute` contiene `/tollgate:finish` e «mai subagent-driven-development»).
  - `test_plugin_and_marketplace_json` (author, license, nessun `version` nelle dipendenze, `allowCrossMarketplaceDependenciesOn`).
  - `test_license_files`.
  - `test_brief_fields_match_agent_text`: ogni campo `REQUIRED` di `report.py` compare in `implementer.md`; i campi del revisore di 18.5 compaiono in `task-reviewer.md`.
- [ ] **Step 2: Fallimento**, **Step 3: scrivere i file**, **Step 4: verificare** con `tests/run`. Se `claude` è disponibile, `claude plugin validate .` deve dare successo (passo manuale, esito nel report).
- [ ] **Step 5: Commit** «tollgate P3a: agenti implementer e task-reviewer, skill del flusso, marketplace e licenze».

---

