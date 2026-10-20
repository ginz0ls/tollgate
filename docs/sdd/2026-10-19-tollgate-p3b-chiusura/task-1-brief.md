### Task 1: Verifiche dell'interfaccia di `gh`

Il codice di P3b chiama `gh` in forme non ancora provate (spec 16: «`gh` vero» non esercitato). La verifica è sul testo d'aiuto della versione installata, **senza rete**. Su Claude Code non servono fatti nuovi: i revisori finali usano gli stessi eventi provati in P0-P3a.

**Files:**
- Create: `spikes/run-p3b-experiments.sh`, `docs/verifiche/2026-10-19-p3b-verifiche.md`

**Interfaces:**
- Produces: esiti G1-G5, che decidono le forme di `gh.py` (Task 9) e di `fakegh.py`.

**Regole di cautela (vanno nel brief):** niente rete: solo `gh --version` e `gh <comando> --help`. Mai `gh auth`, `gh api` verso GitHub, `gh pr create`. Nessun repo su GitHub.

- [ ] **Step 1: Script** `spikes/run-p3b-experiments.sh`: scrive in `/tmp/tollgate-p3b/help/` l'uscita di `gh --version`, `gh api --help`, `gh pr create --help`, `gh pr edit --help`, `gh pr list --help`, `gh pr view --help`.
- [ ] **Step 2: Rapporto** `docs/verifiche/2026-10-19-p3b-verifiche.md`, tabella `Id | Voce | Esito | Evidenza | Conseguenza`:
  - G1 segnaposto `{owner}`/`{repo}` di `gh api` presi dal repo della cartella corrente (atteso sì; resta non provato con `insteadOf` verso un repo locale, coperto da `fakegh`);
  - G2 `gh pr create` con `--head`, `--base`, `--title`, `--body-file` (atteso sì); l'URL stampato su stdout non è nell'aiuto: il codice rilegge la PR con `pr list --head` (decisione 10);
  - G3 `gh pr edit <n> --body-file`; G4 `gh pr list --head --state all --json number,state,url,headRefOid,mergedAt`; `gh pr view <n> --json comments`;
  - G5 `--paginate` con `--jq` (atteso: una riga JSON per elemento, pagina dopo pagina); `--slurp` assente in 2.46 (decisione per `prs_for_branch_prefix`).
  
  Più la versione di `claude` (`claude --version`), solo annotata.
- [ ] **Step 3: Commit** «tollgate P3b: verifiche dell'interfaccia di gh».

---

