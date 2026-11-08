# Revisione Task 8 (73b1ab9..6af06c5)

### Aderenza
- ✅ `DISALLOWED` con `infra`: ciclo sui 10 programmi, quattro forme ciascuno (`spikes/run-b1-flow.sh`, blocco `DEPLOY_CLIS`); `gh` invariato; il test D6 usa `shlex.split` della riga di `controlla` e verifica che `b1` e `ai` non ricevano le voci nuove.
- ✅ Casi `b1` e `ai` invariati: i rami `[ "$CASE" = b1 ] ||` coprono `ai` come prima; messaggio di errore su RULES identico; `PROFILE_AREA/FILE` impostati in entrambi i rami che li usano (nessun problema con `set -u`); `AI_TITLES` rinominato, nessun altro uso nel codice.
- ✅ Progetto di prova `spikes/b4/flow/`: nessun `.vercel`, `.env*`, `.dev.vars*`, file Wrangler, token; `vercel.json` con la sola `cleanUrls`; test `..._has_no_credentials` guarda i file del repo, non la HOME. Nessun nome utente/host nei file nuovi (grep).
- ✅ R-INFRA-12: `issue-1.md` e `piano-L1.md` dicono che il progetto non è collegato, che la prova senza pubblicazione non si fa e che il report dice perché; test dedicato.
- ✅ D5: regex in posizione di comando; provata a mano: `cat vercel.json`, `git add vercel.json`, `python3 npm.py` non segnati; `npx`, `command npx`, `env npm`, `;npm`, percorso, `bash -c '...'`, `&& docker` segnati. `b1`/`ai` invariati (test `only_for_infra`).
- ✅ D8 (`src_repo` con `infra_approved`, niente `rules-base` finta), D9 (riga in `scrivi_limiti` solo per `infra`, con test).
- ✅ HOME: le prove usano la HOME finta del Bench; nessun test legge file veri del plugin fuori da quelli che già usavano i test `ai`. `test_committed_evidence_has_no_long_web_results` non toccato e ancora valido (il titolo nuovo non cambia `third_party_blocks`).
- ✅ `bash -n` ok. Non ho rilanciato la suite (verificata dal controller).

### Punti di forza
Modifica minima e speculare al caso `ai`; costante unica `DEPLOY_CLIS` per ciclo e grep; limiti dichiarati onestamente nel report e in `limiti.txt`.

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. `spikes/run-b1-flow.sh` (regex `risky`): non segna `(yarn)` nudo senza spazio dopo, comandi dopo backtick, `VAR=x npm`, `xargs npm` (gli ultimi due documentati). Falsi positivi: `echo "npm ..."`, `cat dir/npm foo`. È un controllo a posteriori; la difesa vera è `DISALLOWED` + hook + progetto senza credenziali. Aggiungere `` ` `` al set e `)` come terminatore sarebbe a costo zero.
2. `tests/test_b1_scripts.py` (`test_registra_flags_deploy_clis`): non copre `command`/`env` come prefisso, `;`, né la forma `bash (subagente):`, che la regex gestisce.
3. `spikes/b4/flow/.gitignore`: non esclude `.vercel/`, `.env*`, `.dev.vars*`, `.wrangler/`; se il modello (nonostante i divieti) li creasse nel worktree, `git add -A` li committerebbe. Aggiungerli è difensivo e gratuito.
4. Il report ammette di non aver osservato il RED separatamente (TDD non rispettato); l'effetto è coperto dai test finali.
5. `test_flow_case_infra_project_verifies` e `..._prepara_refuses_without_profile` usano i file veri tracciati di `skills/rules-infra` senza il prefisso `test_real_`, come già per `ai` (convenzione esistente, non regressione).

### Valutazione
**Qualità del task:** Approvato. **Motivo:** i quattro rischi richiesti (copertura dei 10 programmi, invarianza di `b1`/`ai`, progetto senza credenziali, R-INFRA-12 in issue e piano) sono soddisfatti e verificati; restano solo rifiniture Minor.
