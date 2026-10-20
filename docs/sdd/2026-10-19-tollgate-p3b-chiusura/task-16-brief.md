### Task 16: Agenti e skill della chiusura

**Files:**
- Create: `agents/final-reviewer.md`, `agents/finding-verifier.md`
- Create: `skills/finish/SKILL.md`, `skills/sync/SKILL.md`, `skills/adopt/SKILL.md`, `skills/abandon/SKILL.md`, `skills/cleanup/SKILL.md`
- Modify: `skills/approve/SKILL.md`, `skills/execute/SKILL.md`, `skills/start/SKILL.md`, `skills/resolve/SKILL.md`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: le uscite dei Task 6-15 (righe `agente: … brief: …`, `prossimo passo: …`, codici d'uscita).
- Produces: i nomi `tollgate:final-reviewer` e `tollgate:finding-verifier`, già in `readonly_agents`.

Contenuti (testo in italiano, identificatori in inglese, programma sempre `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` con il ripiego della riga «programma», come le skill di P3a):

**`agents/final-reviewer.md`**: frontmatter `name: final-reviewer`, `tools: Read, Grep, Glob, Bash`, `model: inherit`. Corpo derivato da `superpowers/skills/requesting-code-review/code-reviewer.md` di Superpowers 7.0.0, con la riga di attribuzione MIT come gli agenti di P3a: leggere il brief; sola lettura, mai subagenti, nessun test che scrive file (m13); cercare difetti, non confermare (8.6); confronto con piano, must-have e scope; asserzioni indebolite e casi speciali (R3); ogni rilievo con `file`, `line`, `rule`; chiusura con **un solo** JSON di 18.5 del revisore finale con `sha` e `code` del brief.

**`agents/finding-verifier.md`**: `name: finding-verifier`, `tools: Read, Grep, Glob, Bash`, `model: sonnet`. Testo proprio: per ogni rilievo del brief controlla la prova su file e riga, conferma o scarta, senza discutere con il revisore; un rilievo senza prova si scarta; chiusura con un solo JSON di 18.5 del verificatore.

**`skills/finish/SKILL.md`** (anche il modello): l'atto `finish` lo registra l'hook solo quando l'utente digita `/tollgate:finish`; poi, dal worktree pulito (committa prima i file del coordinatore, vincolo (3)):
1. `finish check`: uscita 1 → mostra le voci `[no]` e fermati; uscita 0 → avanti;
2. L1 e L2: `review prepare`, lancia **in primo piano** ogni riga `agente:` (le righe dello stesso stadio insieme, nello stesso messaggio), poi di nuovo `review prepare` finché la riga «prossimo passo» non è `finish open-pr`; con un ciclo `needs_fix` la fase torna `execution`: `task start --from-findings <ciclo>`, poi il ciclo di `/tollgate:execute`, poi chiedi all'utente di digitare di nuovo `/tollgate:finish`; con un blocco: fermati e indica `/tollgate:resolve`, `/tollgate:approve finding` o `/tollgate:approve rounds`;
3. `finish open-pr`: mostra l'URL; i rifiuti si riportano così come sono. Mai `git push` né `gh pr create` da Bash.

**`skills/sync/SKILL.md`**, **`adopt`**, **`abandon`**, **`cleanup`** (`disable-model-invocation: true`): l'atto è già registrato; lanciano il sottocomando e riferiscono. `adopt`: dal checkout principale, poi `EnterWorktree` come `start`. `cleanup`: prima senza `--confirm`, mostra l'elenco, chiede all'utente; solo con il suo sì rilancia con `--confirm` entro i 10 minuti dell'atto. `sync`: con codice 2 (conflitto) mostra le due strade; con 3 indica `/tollgate:finish`.

**Aggiornamenti:** `approve` (oggetti `finding`, `rounds`, `unverified-review`, `rebase` → `act apply`; `unverified-tests`, `waiver`, `effect` valgono dal DB; `pr` lo usa `finish open-pr`; `spec` e `plan` restano a P3c); `execute` (fine dei task: «di' all'utente di digitare `/tollgate:finish`»; task `fix` come gli altri); `start` (`/tollgate:adopt #N` esiste; PR chiusa senza merge: le due strade); `resolve` (al tetto dei cicli concede un ciclo).

- [ ] **Step 1: Test** `test_manifest.py`:
  - `test_final_agents_frontmatter` (strumenti senza `Edit`/`Write`; `final-reviewer` `inherit` con la riga di attribuzione; `finding-verifier` `sonnet`);
  - `test_closing_skills_user_only` (`sync`, `adopt`, `abandon`, `cleanup` con `disable-model-invocation: true`; `finish` senza);
  - `test_skills_use_program_command_form` (ogni skill che nomina `bin/tollgate` lo fa nella forma `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`; vincolo (2));
  - `test_finish_skill_never_pushes` (contiene «mai `git push`»);
  - `test_finish_skill_keeps_worktree_clean` (`finish` chiede di committare i file del coordinatore prima di `finish check`; vincolo (3));
  - `test_final_verdict_fields_in_agent_text` (i campi di 18.5 del revisore finale e del verificatore compaiono negli agenti).
- [ ] **Step 2: Fallimento, scrittura dei file, `tests/run`**; se `claude` è disponibile `claude plugin validate --strict .` deve riuscire (esito nel report).
- [ ] **Step 3: Commit** «tollgate P3b: agenti final-reviewer e finding-verifier, skill della chiusura».

---

