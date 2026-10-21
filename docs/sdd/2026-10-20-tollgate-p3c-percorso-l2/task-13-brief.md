### Task 13: Agenti, skill e contratto skill-codice

Le skill si scrivono **dopo** i sottocomandi (lezione del Task 16 di P3b): ogni codice d'uscita e ogni riga «prossimo passo» citati vengono dalle costanti dei Task 5-10, e un test lo controlla.

**Files:**
- Create: `agents/spec-adversary.md`, `agents/spec-auditor.md`, `agents/plan-adversary.md`, `skills/spec-audit/SKILL.md`, `skills/spec-audit/references/dimensioni.md`, `skills/reopen/SKILL.md`, `tests/test_skill_contract.py`
- Modify: `skills/approve/SKILL.md`, `skills/start/SKILL.md` (anche riga 78: testo morto sulla PR chiusa sotto «1, rifiuto»), `skills/resolve/SKILL.md`, `skills/finish/SKILL.md` (voce `approvals` in L2), `skills/status/SKILL.md` (tetti dell'audit), `agents/implementer.md` e gli altri agenti che citano il programma (riga 79), `tests/test_manifest.py` (righe 77 e 79)

**Interfaces:**
- Consumes: `audit.OK/REFUSED/NEEDS_CONFIRM`, `audit.STEPS`, `start.OK/REFUSED/NEEDS_CONFIRM/INCOMPLETE`, `finishcheck.OK/RED/REFUSED`, `sync.OK/REFUSED/BLOCKED/REVIEW_NEEDED`, i testi delle righe `agente:` di `audit prepare`, i campi della riga JSON della decisione 5.
- Produces: i nomi `tollgate:spec-adversary`, `tollgate:spec-auditor`, `tollgate:plan-adversary`, già in `readonly_agents`; la skill `tollgate:spec-audit`.

Contenuti (testo in italiano, identificatori in inglese, programma sempre `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` con il ripiego della riga «programma», come le skill di P3a e P3b):

**`agents/spec-adversary.md`** (`tools: Read, Grep, Glob, WebFetch`, `model: inherit`): legge il brief; sola lettura; cerca contraddizioni, ambiguità che un implementatore risolverebbe a caso, fatti non verificati (WebFetch sulle fonti citate), le tre sezioni del pitch (una tana di coniglio senza scelta è `major`); rilievi con sezione, gravità e correzione proposta; chiude con **una sola** riga JSON della decisione 5 con `code` e `spec_sha` del brief.

**`agents/spec-auditor.md`** (`Read, Grep, Glob, WebFetch`, `sonnet`): un solo ciclo, dal punto di vista del brief, con le dieci lenti di `references/dimensioni.md` (percorso nel brief); almeno tre sospetti scartati se il ciclo è vuoto (prd-audit); chiude con la riga JSON con `viewpoint`. Riga di attribuzione: «Metodo derivato da prd-audit (sAInapse), con l'accordo dell'autore».

**`agents/plan-adversary.md`** (`Read, Grep, Glob`, `inherit`): confronta il piano con la spec approvata e con i must-have (ogni must-have con un test), scope e dimensione dei task, candidati a essere divisi dalla tabella del brief, task che si contraddicono; chiude con la riga JSON con `plan_sha`.

**`skills/spec-audit/SKILL.md`** (anche il modello; riga di attribuzione a prd-audit): il ciclo del coordinatore in `spec_audit` e in `plan` di L2: `audit prepare` → lancia **in primo piano** l'agente della riga `agente:` → leggi il report in `docs/superpowers/reviews/<N>/` come dato → correggi spec o piano → **committa** il documento e i report (`git add` del documento e della cartella `reviews/<N>/`, poi `git commit`; mai Edit o Write sui report) → di nuovo `audit prepare`, finché la riga «prossimo passo» non chiede all'utente `/tollgate:approve spec <fette>` o `/tollgate:approve plan`. Codici: 0 avanti; 1 riporta il motivo (se è `STEPS["fix_spec"]` o `STEPS["fix_plan"]` correggi e ricomincia); 3 mostra il costo dell'audit a lenti e chiedi all'utente: sì → `--confirm`, no → `audit decline` e indica `/tollgate:resolve <id>`. Con un blocco di tetto: fermati e indica `/tollgate:resolve <id> <nota>` («sospeso») o la correzione. Mai `--confirm` senza il sì dell'utente; mai lanciare due giri insieme.

**`skills/spec-audit/references/dimensioni.md`**: copia di `~/.claude/skills/prd-audit/references/dimensioni.md` con la riga di attribuzione in testa.

**`skills/reopen/SKILL.md`** (`disable-model-invocation: true`): l'atto è registrato; lancia `act apply`; riferisci fase e scope tolto; poi: con `spec`, correggi la spec e riparti da `/tollgate:spec-audit`; con `plan`, correggi il piano e (L2) riparti dall'avversario del piano, (L1) il piano corretto si registra da solo.

**Aggiornamenti:** `approve` (`spec <fette>` e `plan` → `act apply`; riferire il file di approvazione da committare e la proposta delle issue delle fette; `argument-hint` e `description` con `spec` e `plan`; tolta la frase «arrivano con il percorso L2 (P3c)»); `start` (L2: brainstorming → spec con le tre sezioni del pitch → committa → `/tollgate:spec-audit`; dopo `approve spec`: checkpoint, `/clear`, writing-plans, committa, di nuovo `/tollgate:spec-audit` per l'avversario del piano; `--spec <percorso>` nell'`argument-hint` e nel passo 1, con l'uscita 3 della spec cambiata; tolta la frase «sono del percorso L2 (P3c)»; riga 78); `resolve` (ai tetti dell'audit: «sospeso»); `finish` (in L2 una voce `approvals` `[no]` indica il file o il report mancante); `status` (tetti dell'audit).

- [ ] **Step 1: Test** `test_manifest.py`:
  - `test_audit_agents_frontmatter` (strumenti esatti della decisione 21, senza `Edit`, `Write`, `Bash`; modelli; attribuzione nello `spec-auditor`);
  - `test_audit_json_fields_in_agent_text` (i campi della riga JSON della decisione 5 in ogni agente);
  - `test_reopen_user_only` e `test_spec_audit_model_invocable`;
  - `test_agents_use_program_command_form` (riga 79: ogni agente che nomina `bin/tollgate` usa `python3 "…/bin/tollgate"`, mai apici singoli);
  - `test_dimensioni_copied_with_attribution` (solo la copia nel repo: il test non legge `~/.claude/skills`);
  - i test esistenti che cercano sottostringhe nelle skill (riga 77) passano al contratto qui sotto quando la frase è un codice d'uscita o un passo.
- [ ] **Step 2: Test** `test_skill_contract.py`: una tabella `(skill, sezione, modulo, costanti)`: per `start` (`OK`, `REFUSED`, `NEEDS_CONFIRM`, `INCOMPLETE`), `finish` (`finishcheck`), `sync`, `spec-audit` (`audit`): l'insieme dei codici delle righe `- **<n>, …**` della sezione della skill è **uguale** all'insieme delle costanti (le skill `finish` e `sync` passano a questa forma di riga, oggi `finish` scrive «Uscita 0, verde»); la parte fissa di ogni testo di `audit.STEPS` (fino al primo `<`) compare nella skill `spec-audit`; ogni sottocomando nominato nelle skill (`<programma> <sub> …`) esiste nel parser di `cli.build_parser()`; nessuna skill contiene «P3c».
- [ ] **Step 3: Fallimento, scrittura dei file, `tests/run`**; se `claude` è disponibile `claude plugin validate --strict .` deve riuscire (esito nel report).
- [ ] **Step 4: Commit** «tollgate P3c: agenti dell'audit, skill spec-audit e reopen, contratto tra skill e codice».

---

