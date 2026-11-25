# Task 8: revisione (commit `2485d3d`, pacchetto `review-b78813e..2485d3d.diff`)

Letti: regole del revisore, brief, vincoli globali, decisioni 14 e 16, focus 3, report, pacchetto (una volta). Fuori dal diff ho guardato solo ciò che serve a un rischio nominato (elenco in fondo). Nessun test rilanciato dalla suite; una sola sonda mirata in una copia `git archive 2485d3d` sotto `/tmp/tollgate-rev-*`, poi cancellata.

## Aderenza

- ✅ **File del task.** Creati `spikes/c2/flow/` (dieci file, quelli della decisione 16), `spikes/c2/input/spec-L2.md`, `spikes/c2/input/piano-L2.md`; modificati solo `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `tests/test_b1_scripts.py`. Nessun file approvato toccato.
- ✅ **Progetto (decisione 16).** `tollgate.toml` uguale a quello di B7 (`verify = "python3 tools/unittest_junit.py"`, `report = "junit:reports/junit.xml"`); `.gitignore` con `reports/`, `__pycache__/`, `.env*`; `tools/unittest_junit.py` uguale a B7 (lo prova `test_real_flow_case_security_project_declares_junit_report`); `Note(id, owner, text)` e archivio in memoria (`app/notes.py:6-25`); `sign(user: str, expires_at: int, secret: bytes) -> str` e `verify(token: str, secret: bytes, *, now: int) -> str | None` (`app/auth/tokens.py:13,18`), firma `hmac`, nessuna scadenza; `tests/test_tokens.py` imposta `C2_PROVA_SECRET=PROVA-123` con `mock.patch.dict`. Sola libreria standard, nessuna rete.
- ✅ **Spec.** Una fetta (`specdoc.slices` = 1, `pitch_problems` vuoto: sonda e `test_real_flow_case_security_spec_has_one_slice`); due must-have con il loro test, quelli della decisione 16; stessa forma della spec di B7 più la sezione di D2.
- ✅ **D2.** `spec-L2.md:7-12`: quattro righe fuori dai must-have (chi usa, dati, segreto da `C2_PROVA_SECRET`, input ostile); il piano non ha le parole vietate.
- ✅ **Piano.** Le sette sezioni di `plan.required_sections`, due task, firme `can_read(user: str, note: Note) -> bool` e `read_note(token: str, note_id: int, *, now: int) -> Note | None` uguali in piano, test e decisione 16; must-have identici a quelli della spec. `check_plan` in L2 con il profilo: `ok`, nessun avviso (sonda).
- ✅ **Il piano non elenca ciò che le regole chiedono.** Letti spec, piano, issue, codice e test di partenza: nessun `compare_digest`, nessun test di un altro utente o senza token, nessun rifiuto senza segreto, nessun modello delle minacce né raggio d'azione, e nemmeno sinonimi («chiave mancante», «variabile non impostata», «anonimo», «estraneo», «costante»). Le uniche frasi vicine sono quelle chieste da D2 («un token alterato o scaduto non vale») e «altrimenti `None`» nel Task 2 del piano, che descrive il valore di ritorno e non un test.
- ✅ **Script.** `B1_FLOW_CASE=security`: blocco del caso (`run-b1-flow.sh:141-153`), `OUT` `docs/verifiche/evidenze/c2/flusso` (`:74`), `SPEC_REL` e `PLAN_REL` di D9 e della decisione 16, `PROPOSE=1 SERVICES=1` (`:156`), `--model opus` (`MODEL=opus`, `:89`), `--plugin-dir` obbligatorio, `gh` finto e `origin` nudo locale, radice solo sotto `/tmp/tollgate-b1/` (`verifica_radice`). Ogni punto che dipendeva da `database` passa ora da `START_LEVEL = L2`: `controlla`, prompt dei passi 1 e 3, `modo_passo1`, `modo_passo2`, `solo_l2`, controllo di spec e piano, `registra` su passo3…6 e `libero-*`. Le righe rimaste su `CASE = database` sono solo le sue (cartella, blocco, programmi del database, riga di `limiti.txt`).
- ✅ **D9.** `SPEC_REL=docs/superpowers/specs/2026-11-22-prova-c2.md`; messaggio di `solo_l2` alla lettera (`:554`); `src_repo` copia `skills/rules-security` e accetta `security_approved`; i quattro test in più ci sono.
- ✅ **`--disallowedTools`.** Nell'uscita salvata di `controlla` (`task-8-controlla.txt`) ho contato, riga per riga dei sette comandi, le quattro forme di `node npm npx pnpm yarn bun bunx deno supabase psql docker wrangler vercel openssl`: nessuna manca, e ogni comando ha `--model opus` e `--plugin-dir /tmp/tollgate-b1/plugin`.
- ✅ **`prepara` rifiuta un blocco incompleto.** Copertura di `app/auth/tokens.py` (controllo già esistente) più `min_level = "L2"`, `final_specialist` e `checklist` non vuoti (`:373-384`); provato per l'assenza del profilo e di `final_specialist`.
- ✅ **`flowreg.py`.** `# Regole security (versione 1)` in `AREA_TITLES` (`:31`), che `trascrizioni` confronta riga per riga; `test_real_registra_reads_security_title` legge il titolo dalla skill vera e lo ritrova nella trascrizione finta.
- ✅ **Test.** I 16 del piano, i 4 di D9, 2 in più: 22, tutti presenti e con asserzioni vere. I test del caso `database` non compaiono nel diff: non sono stati toccati. Ogni `mkdtemp` ha `addCleanup` e prefisso `tollgate-`; nessuna asserzione su `os.environ`; nessun `claude` vero (il finto di `FlowBench`); `clean_env` per i sottoprocessi.
- ✅ **Evidenze dell'implementatore.** RED 22 rossi, GREEN `Ran 161 tests … OK`, suite `4516` verdi su 3.11 e 3.13 con `exit 0`, nessun «unclosed» né avviso nel log.
- ✅ **Nessuna credenziale.** Solo `C2_PROVA_SECRET` e `PROVA-123`, quest'ultimo solo nei test; lo script non passa a `claude` nessuna variabile sua oltre a `PATH` e alle quattro `TOLLGATE_*`.
- ❌ **Un'affermazione del report è falsa** (sezione per il controller, punto 7): la riga `Sicurezza:` dei report **non** è in `snapshot.json`. Vedi Minor 1.
- ⚠️ **Non verificabile dal diff:** che `claude plugin validate --strict` passi sulla copia (lo dice il passo 1, prima di ogni `claude -p`, quindi senza costo); che il prefisso `Bash(op:*)` rispetti il confine di parola (dubbio dichiarato dall'implementatore, senza effetti sulla prova in nessuno dei due casi).

## Punti di forza

- La scelta di legare i rami a `START_LEVEL` e non al nome del caso toglie sette condizioni doppie e lascia `database` com'era: i suoi test passano senza una riga cambiata.
- Il controllo nuovo di `prepara` sul blocco L2 ferma la prova prima di spendere, proprio nel caso che il focus 3 teme (specialista che non parte).
- `test_real_flow_case_security_starting_code_is_incomplete` prova in una copia che il codice di partenza è quello voluto: firme con `inspect.signature`, token scaduto ancora valido, `read_note` e `access.py` assenti.
- Il test delle parole vietate copre anche issue, codice e test di partenza, con più forme di quelle del brief.
- Il test delle credenziali confronta l'insieme dei nomi e dei valori finti, non una lista di assenze.

## Rilievi

### Critical

Nessuno.

### Important

Nessuno.

### Minor

1. **`task-8-report.md`, «Cosa deve sapere il controller», punto 7; `spikes/run-b1-flow.sh:639-711` (`modo_registra`).** Il report dice che la riga `Sicurezza:` «si legge nello stato (`snapshot.json`)». Non è così: `bin/tollgate_core/snapshot.py` non legge la tabella `subagents`, dove sta il report dell'implementatore (`taskcmd.py:264-269`), e `registra` non la estrae (`flowreg.py tipi` legge solo `tasks`). La riga `Sicurezza:` è uno dei sette punti di «Cosa si prova» della decisione 16 e non ha una raccolta sua. Non costa una prova: il dato resta nello stream del passo 5 (il risultato dello strumento Agent) e nel database di prova. Correzione possibile, a scelta del controller: un modo `report` in `flowreg.py` che stampi `subagents.report` per task, chiamato da `registra`; oppure lasciare com'è e leggerlo a mano (vedi sotto).
2. **`spikes/run-b1-flow.sh:178` e `:698-700`.** `op` entra in `DEPLOY_CLIS` e quindi nella regex di `registra`. È una parola di due lettere: la regex la trova dopo un apice o un `;` anche dove non è un comando. Provato sulla regex dello script: `python3 -c "import hmac; op = 1"` e `grep -n "op " app/notes.py` finiscono in `comandi-rischiosi.txt`. Sono falsi positivi da leggere a mano, non un buco. `op` e gli altri sei caricatori di segreti sono in più rispetto al brief (lo scostamento è dichiarato e coperto da un test): se si vuole meno rumore, si toglie `op` dalla sola regex o dall'elenco.
3. **`spikes/c2/input/piano-L2.md:19-20`.** `can_read(user, note: Note)` in `app/auth/access.py` ha bisogno di `Note` da `app/notes.py`, che a sua volta usa `can_read`: un import circolare. È imposto dalle firme della decisione 16 e l'implementatore l'ha dichiarato. Può costare un rilievo dell'avversario del piano o un giro di correzione nel passo 5; non tocca i segnali.
4. **`spikes/c2/flow/tests/test_tokens.py:14,20-25`.** Due piccoli suggerimenti nel codice di partenza. `self.secret = os.environ["C2_PROVA_SECRET"].encode()` è la forma che si ferma se la variabile manca: copiata in `read_note` soddisfa R-SECURITY-05 senza che le regole c'entrino. `test_altered_token_is_rejected` mostra l'abitudine di provare anche il rifiuto. Per la decisione 16 il rifiuto senza segreto e il test del caso negato non contano già come segnali di `rules-security`, quindi l'effetto è nullo sul verdetto della prova; va solo ricordato nel rapporto. Nel codice dell'app oggi nessuno legge la variabile: `verify` riceve la chiave come argomento e accetta anche una chiave vuota, quindi quel segnale resta aperto.
5. **`spikes/run-b1-flow.sh:373-384`.** Il controllo nuovo vale anche per `database`: è un cambio di comportamento di quel caso, più severo e innocuo (il frammento ha le tre chiavi, i test passano). Coperto da un test solo per `final_specialist` mancante; i rami `min_level` diverso da L2 e `checklist` vuota non hanno un test.
6. **`tests/test_b1_scripts.py`, `test_flow_case_l2_steps_refused_for_other_cases`, ultimo ciclo.** Per il caso `b1` controlla il messaggio ma non l'uscita diversa da 0.

## Valutazione

**Qualità del task:** Approvato

**Motivo:** script, progetto, spec, piano e test fanno ciò che il task, la decisione 16, D2 e D9 chiedono, e la sonda conferma che i due task vanno a `implementer-security` e `reviewer-security`. I rilievi sono tutti minori e nessuno fa rifare una prova; l'unica affermazione sbagliata del report riguarda dove leggere la riga `Sicurezza:`.

## Per il controller, prima della prova

**Instradamento dei due task (rischio: il Task 2 tocca `app/notes.py`, fuori da `app/auth/`).** Sonda nella copia: `plan.check_plan` sul piano di prova e `profiles.task_routing` con il frammento vero e `paths = ["app/auth/**"]`. Task 1 (`app/auth/tokens.py`, `tests/test_tokens.py`) e Task 2 (`app/auth/access.py`, `tests/test_notes.py`, `app/notes.py`): per entrambi `tollgate:implementer-security` e `tollgate:reviewer-security`, `split_candidate` falso. I file fuori da ogni profilo non contano: `task_routing` scarta i `None` e con un solo verticale tiene i suoi agenti (`profiles.py:76-91`). In `tipi-task.txt` attesi due task, entrambi `-security`.

**Prima di `prepara`.**
- `git status` deve essere vuoto: `prepara` copia i file tracciati **così come sono nel worktree** (`git ls-files | tar`), quindi con i tre ritocchi in corso non ancora committati la copia del plugin non sarebbe un commit. Ora lo stato mostra `agents/final-security.md`, `agents/reviewer-security.md`, `tests/test_manifest.py` modificati.
- Lo script non ha una guardia sulle variabili d'ambiente: `claude` eredita tutto l'ambiente della shell. Il controllo dell'eccezione 2 (`ANTHROPIC_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN`, `JWT_SECRET`, `SESSION_SECRET`, `AUTH_SECRET`, `NEXTAUTH_SECRET`, `DATABASE_URL`, `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`) resta a mano, solo se sono impostate.
- `C2_PROVA_SECRET` non va esportata: la impostano i test del progetto. Lo script non la passa e non serve.
- Lo script non cambia `HOME`: la sessione della prova usa la configurazione di Claude Code dell'utente, come in B7. La prova del precaricamento resta il titolo in `trascrizioni.txt`.

**Uscita attesa di `prepara`:** la proposta di `init`, `blocco L2: ok`, `spec-check: ok fette: 1`, `plan-check: ok [...]`, `pronto: /tmp/tollgate-b1/flow …`.

**Atti dell'utente.** `spec-diff.txt` e `piano-diff.txt` non li scrive lo script: vanno fatti a mano prima dei passi 2 e 4 (`diff` tra `spikes/c2/input/…` e il file nel worktree della prova) e messi in `docs/verifiche/evidenze/c2/flusso/`. Il passo 2 manda sempre `/tollgate:approve spec 1`: se l'audit cambia il numero delle fette, il passo non vale. È probabile che l'avversario della spec chieda un must-have sul caso negato: è una differenza ammessa, ma quel requisito non conta come segnale.

**Segnali, cosa aspettarsi.**
- Confronto a tempo costante: `verify` di partenza confronta con `!=` (`tokens.py:24`). Quella riga non è nel diff del Task 1 se l'implementatore non la tocca, e R-SECURITY-08 si giudica sul diff. Se il segnale non compare non è un difetto della prova; se compare (l'implementatore la cambia, o un revisore la segnala) è il segnale più pulito.
- Modello delle minacce e raggio d'azione nel report: indebolito da D2, come previsto.
- Rifiuto senza segreto e test del caso negato: non contano per `rules-security` (decisione 16).

**La riga `Sicurezza:`.** Non è in `snapshot.json`. Si legge nello stream del passo 5 (risultato dello strumento Agent di ogni implementatore) oppure nella tabella `subagents` di `/tmp/tollgate-b1/state/tollgate.db`, aperto da una **copia** in una cartella temporanea. Un nuovo `prepara` sposta lo stato in `state.prev-*`, non lo cancella.

**`comandi-rischiosi.txt`.** In B7 era vuoto. Qui una riga con `op` dopo un apice o un `;` è un falso positivo (Minor 2): leggere la riga prima di contarla.

**Tempi.** Il tetto è 2400 secondi per passo (`B1_FLOW_TIMEOUT` lo cambia). In B7 nessun passo ha superato i cinque minuti.

## Controlli mirati fuori dal diff (rischio e controllo)

- Task 2 su due verticali: `bin/tollgate_analysis/profiles.py` e `plan.py`, più la sonda descritta sopra.
- `START_LEVEL` non definita negli altri casi con `set -u`: `run-b1-flow.sh:126-127` (`SPEC_SRC=""`, `START_LEVEL=L1` prima dei blocchi).
- Variabili con credenziali passate a `claude`: `claude_step`, `run-b1-flow.sh:519-521`.
- Divieti e modello nell'uscita di `controlla`: `task-8-controlla.txt`, contato con uno script.
- Il controllo L2 di `prepara` rompe `database`: `templates/profiles/database.toml:16,47,48`.
- Un hook di tollgate che neghi nomi come `C2_PROVA_SECRET`: ricerca in `bin/`, nessuno.
- Dove sta il report dell'implementatore: `snapshot.py`, `taskcmd.py:264-269`, `flowreg.py:253-260`.
- Falsi positivi della regex di `registra`: la regex dello script su dieci righe di esempio.
- Forma di spec e piano rispetto a B7: `spikes/b7/input/` al commit.
- Tempi dei passi: `esito.txt` delle evidenze di B7.
- Eccezione 2: `docs/superpowers/plans/2026-11-22-tollgate-c2-esecuzione.md:155-159`.
