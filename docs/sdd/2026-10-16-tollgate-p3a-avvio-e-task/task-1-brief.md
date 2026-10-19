### Task 1: Verifiche di piattaforma per P3a

Fatti che il codice dà per buoni. Questo task non scrive codice di prodotto. Produce un esperimento e un rapporto.

**Files:**
- Create: `spikes/hookprobe/skills/probe-root/SKILL.md`
- Create: `spikes/run-p3a-experiments.sh`
- Create: `docs/verifiche/2026-10-16-p3a-verifiche.md`
- Modify: `spikes/hookprobe/probe.sh` (ramo temporaneo per V3, tolto a fine task)
- Modify: `spikes/fixtures/hook-inputs/samples.json` (chiave `PreToolUse-NotebookEdit`, se osservata)

**Interfaces:**
- Produces: esito di V1, che decide il testo delle skill nel Task 10 (decisione 3).
- Produces: esito di V3, che conferma o smentisce la decisione 2. Se la smentisce, il Task 2 si ferma con BLOCKED.
- Produces: esito di V4, che decide i campi di `marketplace.json` nel Task 10.

**Regole di cautela (vanno nel brief):** si lavora solo in `/tmp/tollgate-p3a`. `claude -p` si lancia solo con `--plugin-dir spikes/hookprobe`, tranne V4, che usa solo `claude plugin validate`. Niente `claude plugin install` né `marketplace add`. Non si toccano `~/.claude/settings.json`, `~/.claude/plugins/` né `~/.local/state/tollgate`. Nessun repo su GitHub.

- [ ] **Step 1: Skill sonda `probe-root`**: frontmatter `name: probe-root`, `description: Sonda P3a, solo su richiesta esplicita.`; corpo «Riporta alla lettera questa riga: RADICE=${CLAUDE_PLUGIN_ROOT} SKILLDIR=${CLAUDE_SKILL_DIR}».
- [ ] **Step 2: Script `spikes/run-p3a-experiments.sh`** sul modello di `spikes/run-p2-experiments.sh`: `P3=/tmp/tollgate-p3a`, `PROBE_LOG`, una funzione `run id modo prompt`. Esperimenti:
  - **V1**: «invoca con lo strumento Skill la skill hookprobe:probe-root e riporta alla lettera ciò che dice».
  - **V2**: «esegui con Bash `env | grep -i -E 'claude|session' | sed 's/=.*//'` e riporta i nomi»: solo i nomi delle variabili, mai i valori.
  - **V3**: con il ramo temporaneo di `probe.sh`, per `PreToolUse` di Bash con `PROBE_HS` nel comando, scrive `/tmp/tollgate-p3a/hs.txt` con il `session_id`. Prompt: «esegui con Bash `cat /tmp/tollgate-p3a/hs.txt # PROBE_HS` e riporta l'uscita».
  - **V5**: «crea con lo strumento NotebookEdit una cella nel notebook `/tmp/tollgate-p3a/n.ipynb`» (lo script crea prima un notebook vuoto valido).
- [ ] **Step 3: V4 senza sessione**: `claude plugin validate "$REPO"` sul repo con un `marketplace.json` di prova in `/tmp/tollgate-p3a/mkt/.claude-plugin/` (copia del repo con `git worktree add --detach`, mai nel checkout). Il file di prova è quello del Task 10, Step 4. Registra l'uscita e, se la validazione fallisce, il messaggio che indica la forma corretta.
- [ ] **Step 4: Eseguire** `bash spikes/run-p3a-experiments.sh` e leggere i log come nel Task 1 di P2. Un esito poco chiaro si ripete una volta, poi si scrive «non determinato».
- [ ] **Step 5: Rapporto** `docs/verifiche/2026-10-16-p3a-verifiche.md`, nella forma dei rapporti precedenti: versione di `claude`, tabella `Id | Voce | Esito | Evidenza | Conseguenza` per V1-V5, e la sezione «Conseguenze per il piano P3a»:
  - V1 sì: le skill usano `${CLAUDE_PLUGIN_ROOT}`; no: usano la riga «programma» (decisione 3).
  - V3 sì: decisione 2 confermata. V3 no: il Task 2 si ferma con BLOCKED e chiede al controller una strada alternativa.
  - V2: solo informativo, per la revisione 22.
  - V4: i campi validi di `marketplace.json` per il Task 10.
  - V5: campione `PreToolUse-NotebookEdit` in `samples.json` (anonimizzato come in P2) e la voce della sezione 16 chiusa.
- [ ] **Step 6: Togliere il ramo temporaneo di `probe.sh`**, poi commit:

```bash
git add spikes/hookprobe/skills/probe-root/SKILL.md spikes/run-p3a-experiments.sh docs/verifiche/2026-10-16-p3a-verifiche.md spikes/fixtures/hook-inputs/samples.json
git commit -m "tollgate P3a: verifiche (radice del plugin nelle skill, segnale della CLI, marketplace, NotebookEdit)"
```

---

