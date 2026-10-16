# Revisione finale del ramo `p2-guardrail` (d87383a..4a91fea)

Revisore: revisione finale, unica passata sull'intero ramo, in sola lettura. Sonde in `/tmp/claude-1000/rv/` (Python con `-B`), nessuna modifica a working tree, indice, HEAD o rami.

Verifiche eseguite:
- `python3.11 -B -W error::ResourceWarning -m unittest discover -s tests -t .` e lo stesso con `python3` (3.13): 642 test, OK su entrambi, nessun `ResourceWarning` in questa esecuzione.
- `test_concurrent_first_open`: riprodotto (1 fallimento su 12 esecuzioni di `tests.test_db`). Causa trovata e riprodotta in modo deterministico, 20 casi su 20 (vedi C1).
- Sonde con `tests.hookkit.Lab` su circa 40 comandi Bash e su scritture verso file protetti raggiunti da un collegamento simbolico (C2, I3).
- Prova con git reale delle opzioni lunghe abbreviate (`--no-verif`, `--har`, `--force-w`): git le accetta tutte.

---

### Punti di forza

- **Architettura a strati pulita e rispettata.** `tollgate_analysis` è puro e un test ne verifica l'isolamento. I controlli non scrivono: `ReadDb` accetta solo `SELECT`, e un `PermissionError` dentro un controllo di tipo `Pre` diventa un veto. Tutte le scritture passano da `apply._OPS`, un elenco chiuso di 22 operazioni che corrisponde alla sezione 3 del piano principale.
- **Fail-closed coerente nel runner** (`bin/tollgate_hooks/runner.py:172-231`): un modulo rotto o in errore, una scadenza, `DbError` o `sqlite3.Error` danno 2 sugli hook di controllo e 0 con avviso su quelli informativi. Il wrapper (`hooks/run:172-184`) converte ogni altra uscita allo stesso modo, e il cane da guardia ha i descrittori chiusi.
- **Logica condivisa davvero una volta sola.** Le ricevute della DoD e di SubagentStop passano entrambe da `dod.receipt_verdict`. Test-guard e scope del commit (pre e post) usano `_common.commit_violations`. I file protetti di `writes.py` e `bash_rules.py` passano da `_common.is_protected_path`, il livello da `_common.level_records`. Non ho trovato logica duplicata tra moduli.
- **Combinazione delle decisioni conforme a 3.2.** Vince il primo `deny`, i `record` si applicano anche dopo un veto, e un `record` non più applicabile diventa un avviso senza annullare gli altri. `prompt_submit` non blocca mai il prompt dell'utente.
- **Parser Bash robusto** sui casi del Review Focus 1: heredoc, `$(...)` annidati, `bash -lc`, `eval`, `git -C`, `cd &&`, `GIT_DIR=`. Quasi tutte le forme di push verso il ramo predefinito che ho provato vengono negate: `HEAD:main`, `@:main`, `refs/heads/x:refs/heads/main`, `-c remote.origin.push=+HEAD:…`, `--mirro`.
- **Sicurezza di git in sola lettura** (`git.py:33-42`): `--no-optional-locks`, `core.fsmonitor=false`, `--no-ext-diff --no-textconv`, timeout.
- **Test che verificano comportamento reale.** Repo, origin e worktree sono veri (con spazi nel percorso), il wrapper bash viene eseguito davvero, i processi sono concorrenti. La matrice criteri→test nel piano principale è precisa.

---

### Rilievi

#### Critical (Must Fix)

**C1. Collisione di nome nelle copie del DB: `disk I/O error` all'apertura concorrente (il test intermittente).**
`bin/tollgate_core/db.py:226-240` (`backup`), chiamato da `_migrate` (`db.py:169-170`).
- **Causa (riprodotta).** Tre processi aprono lo stesso DB nuovo. A crea lo schema 1 e lo committa. B e C leggono `current == 1`, quindi `fresh` è falso, ed entrambi chiamano `backup(..., "migrazione-2")` prima di prendere il lucchetto. Il nome dipende solo dall'ora al microsecondo. Il controllo `dst_path.exists()` è un check-then-act (TOCTOU), e il file temporaneo `.tmp-<nome>` deriva dallo stesso nome. Due processi che svegliano insieme scelgono lo stesso nome, scrivono nello **stesso** `.tmp-…db`, poi il primo lo rinomina. Il secondo fallisce con `SQLITE_IOERR_FSTAT` (codice 1802), che `open_db` trasforma in `DbError`.
- **Prove.**
  - Con una copia strumentata di `db.py`, il processo che fallisce stampa `.tmp-tollgate-20261009T103411018680Z-migrazione-2.db` mentre `backup/` contiene già `tollgate-20261009T103411018680Z-migrazione-2.db`, lo stesso istante.
  - Con l'ora bloccata, due `db.backup` concorrenti falliscono 20 volte su 20 (`/tmp/claude-1000/rv/collide.py`).
  - Con la copia verso `:memory:` i fallimenti spariscono (0 su 1.900 contro 2-3 su 600).
- **Perché conta.** Non riguarda solo il test. Dopo un aggiornamento del plugin, il primo gruppo di hook concorrenti (coordinatore e due subagenti, Review Focus 5) esegue la migrazione 2 su un DB con dati. Uno degli hook esce con `DbError`: su `PreToolUse` è un veto spurio, su `SubagentStop` è un controllo saltato. In più `tmp_path.replace(dst_path)` può sovrascrivere in silenzio la copia di un altro processo. La chiusura del ramo richiede `tests/run` verde, e oggi il risultato è casuale.
- **Correzione.**
  1. Nome temporaneo unico per processo: `tmp_path = state.backup_dir / f".tmp-{os.getpid()}-{secrets.token_hex(4)}-{tag}.db"`.
  2. Pubblicazione che non sovrascrive mai: dopo `conn.backup(dst)`, un ciclo `while True: try: os.link(tmp_path, dst_path); break; except FileExistsError: n += 1; dst_path = …-{n}-{tag}.db`, poi `tmp_path.unlink()`. `os.link` fallisce in modo atomico se la destinazione esiste, a differenza di `replace`.
  3. (Consigliato) In `_migrate`, rileggere la versione sotto `BEGIN IMMEDIATE` prima della copia. Chi arriva dopo la migrazione non copia un DB ormai superato. La copia con il lucchetto preso sulla stessa connessione è ammessa dall'API di backup.
  4. Test di regressione deterministico: due processi con `clock.now` bloccato chiamano `db.backup` insieme, ed entrambi devono riuscire producendo due file distinti. Poi `test_concurrent_first_open` ripetuto, per esempio 200 volte in un ciclo locale, senza fallimenti.

**C2. File protetti raggiunti da un collegamento simbolico: la protezione salta (per esempio `~/.claude/settings.json` gestito con i dotfile).**
`bin/tollgate_checks/_common.py:148-155` (`edit_target` risolve il percorso), `bin/tollgate_checks/bash_rules.py:32-36` (`_abs` risolve), `bin/tollgate_hooks/context.py:111-114` (`protected_roots`: `settings.json` **non** risolto), `bin/tollgate_analysis/protected.py:106-113`.
- **Il difetto.** La protezione si valuta solo sul percorso **risolto**, ma i file protetti sono definiti per **nome** (`.claude/settings.json`, `~/.claude/settings.json`). Se il file è un collegamento verso un'altra posizione, il percorso risolto non corrisponde a nessuna regola.
- **Sonda** (`/tmp/claude-1000/rv/probe_sym.py`, con `HOME` temporanea):
  - `Write ~/.claude/settings.json` (collegamento verso `~/dotfiles/settings.json`) → uscita 0;
  - `echo x > ~/.claude/settings.json` → 0;
  - `Write <repo>/.claude/settings.json` (collegamento verso `config/claude.json`) → 0;
  - `sed -i … .claude/settings.json` → 0;
  - lo stesso file non collegato → 2.
- **Perché conta.** È la protezione del guardrail su se stesso. `settings.json` può spegnere gli hook (`disableAllHooks`), disattivare il plugin o allargare i permessi. Un `~/.claude/settings.json` collegato a un repo di dotfile è una configurazione comune, e l'agente non deve fare nulla di insolito: scrive il percorso normale. Il glossario della spec (file protetti) e 7.4 non prevedono eccezioni.
- **Correzione.** Valutare la protezione sia sul percorso lessicale normalizzato (`os.path.normpath(os.path.join(cwd, expanduser(raw)))`, senza risolvere i collegamenti) sia su quello risolto: è protetto se lo è uno dei due. In `protected_roots`, tenere ogni radice in entrambe le forme (`home/.claude/settings.json` e il suo `resolve()`). Per `writes.py`, `edit_target` deve restituire entrambe le forme oppure `is_protected_path` deve ricevere il percorso grezzo. Test: le quattro sonde sopra, che devono dare 2.

#### Important (Should Fix)

**I1. Il repo attivo si decide solo dal `cwd`: un'azione su un repo attivo lanciata da fuori non riceve nessuna regola.**
`hooks/run:111-131`, `bin/tollgate_hooks/runner.py:122-128` e `:136-152`.
- **Il difetto.** Il wrapper esce con 0 se il `cwd` dell'evento non è in un repo attivo, a meno che la sessione non sia legata. Il runner fa lo stesso (`root is None and not marked`) e legge la configurazione dal repo del `cwd`. Esempi:
  - una sessione non legata avviata in `~/code` (cartella madre, non un repo) o in un repo vicino non attivo scrive `…/repo-attivo/.tollgate/waivers/7.toml`, `…/tollgate.toml` o `.claude/settings.json`;
  - la stessa sessione lancia `git -C ~/code/repo-attivo push origin main`;
  - la stessa sessione scrive nel worktree di un lavoro senza esserne la sessione legata.

  In tutti questi casi nessun controllo gira, e senza messaggio.
- **Perché conta.** La spec 6.6 dice che il ramo si riconosce «per i file, dal loro repository; per Bash, dalla directory effettiva, compresi `cd` e `git -C`», e che i file protetti valgono «rispetto a ogni radice». La riga 6.6 «ogni comando dentro il worktree di un lavoro attivo» non dipende dalla sessione. Una persona ragionevole si aspetta che la protezione segua il bersaglio, non la cartella da cui Claude Code è stato avviato. Avviare Claude in una cartella madre è un errore onesto comune.
- **Correzione.** Python tiene un elenco delle radici attive note: per esempio `<stato>/active/<hash>` con dentro il percorso del checkout e dei worktree, scritto da `start` e dal runner quando vede un repo attivo. Su `PreToolUse`, quando il `cwd` non è attivo, il wrapper cerca con `grep -F` quei prefissi nell'input. Se ne trova uno lancia Python. Il runner, per `pre_edit`, prende la configurazione dal repo del bersaglio quando il `cwd` non è attivo. Test: scrittura protetta e push verso il ramo predefinito con `cwd` fuori da un repo, entrambi devono dare 2.

**I2. `PostToolUseFailure` non è registrato: un effetto approvato che esce con errore non consuma l'atto, e i commit di un comando fallito si vedono solo più tardi.**
`hooks/hooks.json` (nessun `PostToolUseFailure`), `bin/tollgate_checks/effects.py:1-7` e `:142-150` (consumo solo su `post_bash`), ruling del Task 16 (consumo spostato a `PostToolUse`).
- **Il difetto.** La documentazione raccolta nel Task 1 (`task-1-docs.md:107,128`) cita `PostToolUseFailure` come evento distinto. Un Bash con uscita diversa da 0 è, con buona probabilità, uno strumento fallito: niente `PostToolUse`, quindi niente `effect_execute`. Per esempio `gh release create … ; false`, oppure un `curl -X POST` che riceve un 500 dopo aver scritto. L'atto resta `pending` per tutto `ttl_minutes` e lo stesso effetto passa di nuovo con la stessa approvazione, contro 8.5 punto 3, «una volta». Allo stesso modo `git cherry-pick X && false` sfugge a `post_bash` fino al successivo Bash riuscito nel worktree. Viene recuperato da `rev_list`, ma più tardi.
- **Correzione.** Prima una sonda veloce come E9, per confermare che un Bash con uscita 1 produce `PostToolUseFailure` e non `PostToolUse`. Poi aggiungere `PostToolUseFailure` per `Bash`, ed eventualmente `Edit|Write`, in `hooks.json`, e mapparlo in `adapter._POST` sugli stessi eventi d'ingresso (`post_bash`, `post_edit`). Il consumo dell'atto è corretto anche su fallimento, perché il comando è partito. Allineare la spec 8.5 punto 3.

**I3. Falsi negativi economici nelle regole di 7.4: opzioni lunghe abbreviate e alias di git con `-c`.**
`bin/tollgate_analysis/bash.py:449-461` (`push_is_force`), `:521-533` (`destructive`), `:322-335` (`git_call`), `:886-894` (`_TEXT_DANGER`).
- **Prove** (sonde `probe_bash.py` e `abbrev.sh`; git accetta il prefisso univoco di un'opzione lunga):

  | Comando | Uscita | Contesto |
  |---|---|---|
  | `git push --force-w origin x` | 0 | push forzato |
  | `git commit --no-verif -m x` | 0 | anche dall'implementatore nel worktree legato |
  | `git reset --har HEAD~1` | 0 | anche dall'implementatore nel worktree legato |
  | `git -c alias.p=push p origin main` | 0 | push verso il predefinito |
  | `git -c alias.s=switch s main` | 0 | cambio di ramo nel worktree |

  Il ripiego testuale per i comandi illeggibili (heredoc verso una shell) non cerca `rm -rf`, `hooksPath` né i nomi dei file protetti.
- **Perché conta.** Il push forzato e `--no-verify` sono il rischio principale che 7.4 nomina. Dopo un veto, un modello che cerca una strada alternativa prova proprio le varianti. `post_bash` non rileva i push, quindi non c'è un controllo a valle.
- **Correzione.**
  - In `git_call` e nelle regole, normalizzare le opzioni lunghe: se `x` è un prefisso di almeno 3 caratteri di un'opzione pericolosa nota (`--force`, `--force-with-lease`, `--mirror`, `--no-verify`, `--hard`), trattarla come quell'opzione. Un prefisso ambiguo, per git, è un errore, e negarlo non costa nulla.
  - Con `-c alias.<x>=<valore>` nel comando, sostituire il sottocomando `<x>` con il primo token di `<valore>` (gli alias che iniziano con `!` vanno trattati come shell).
  - Aggiungere a `_TEXT_DANGER` `rm\s+-[a-zA-Z]*[rR]`, `hookspath` (senza distinguere maiuscole), `tollgate\.toml`, `\.tollgate/` e `settings(\.local)?\.json`.

#### Minor (Nice to Have)

**M1. `cwd` inesistente: un hook di controllo esce con 0, contro il Review Focus 2 del piano.** `runner.py:122-128`. Il test `tests/test_hook_engine.py:255-257` fissa proprio l'uscita 0 (`/non/esiste` → 0). Il piano diceva «un hook di controllo esce con 2 e un messaggio chiaro», e non trovo una ruling che lo cambi. Effetto pratico basso, perché il wrapper ripiega su `$PWD`. Proposta: su `CONTROL_EVENTS` con `cwd` non valido, usare il repo del bersaglio (vedi I1) oppure negare, e aggiornare il test. Va registrata almeno una ruling.

**M2. Scritture su file protetti tramite git.** `git checkout origin/main -- tollgate.toml` e `git restore .tollgate/waivers/7.toml` passano (sonda). Il danno è limitato, perché ripristinano una versione già committata e la configurazione si legge dalla base. Basta aggiungere a `write_targets` le posizionali dopo `--` di `checkout` e `restore`.

**M3. «Sessione viva» e «subagente fermo» si aggiornano solo con gli strumenti che hanno un matcher.** `hooks.json` non intercetta `Read`, `Grep` e `Glob`, quindi un implementatore che legge per più di `stale_minutes` senza scrivere risulta fermo. Il `PreToolUse Agent` successivo lo segna `interrupted` e ammette un secondo scrittore. È raro con 30 minuti. Da documentare nella spec (0, «sessione viva») o da coprire con un matcher leggero in P3.

**M4. Spec 8.5 punto 3: «Per MCP, che non ha `PostToolUse`».** È impreciso: Claude Code emette `PostToolUse` anche per `mcp__*`, è l'adattatore che non lo mappa. Va riformulato in «l'adattatore di P2 non mappa `PostToolUse` MCP».

**M5. Il piano principale riporta «641 test verdi»** (riga 6), ma la suite ne esegue 642. Va allineato.

**M6. Stesso schema di C1 in `waiver_cli.add_waiver`** (`waiver_cli.py:66-68`): `.tmp` con nome fisso, quindi due `waiver add` concorrenti possono pubblicare un file mescolato o perdere una deroga. È già nei rinviati del Task 11. Conviene correggerlo insieme a C1 (nome unico più lucchetto `fcntl.flock` sul file delle deroghe).

**M7. `rm -rf` fuori dal repo è negato anche per `/tmp/build`** in ogni sessione di un repo attivo (sonda: 2). È conforme alla lettera di 7.4, ma genera attrito. Il messaggio potrebbe suggerire `rm -r` senza `-f` oppure un percorso dentro il worktree.

---

### Triage dei Minor rinviati (`W/deferred.md`)

| Task | Rilievo | Esito | Motivo |
|---|---|---|---|
| 1 | Lo script lancia E9 con `manual`, i campioni vengono da `acceptEdits` | Rinviabile | Solo documentale; il ruling registra già l'origine dei campioni |
| 2 | `tasks.assign` senza `reviewer_type` lo azzera | Rinviabile a P3 | Nessun chiamante in P2 |
| 2 | `is_stale` senza test, `interrupt` solo caso felice | Chiuso | Test aggiunto (`test_subagents.py::…test_is_stale_uses_last_seen_then_started`, criterio 8) |
| 2 | MigrationV2 non provata su DB con dati | **Da correggere con C1** | Il test di regressione di C1 deve migrare un DB v1 con righe, in concorrenza |
| 3 | `register_plan` registrato con fase non avanzata se `set_phase` fallisce | Rinviabile | Imposto dal vincolo 2; il ritorno a `execution` resta possibile da P3 |
| 3 | `offlog`: doppio import se `unlink` fallisce; pid zombie | Rinviabile | Effetto: un evento `off`/`on` doppio nelle statistiche |
| 4 | `plan.py`: più file sulla stessa riga, fence `~~~`, ID duplicati | Rinviabile, **prima dell'uso reale (P3)** | Direzione sicura (veti in più), ma è attrito su piani reali |
| 4 | `globs` `[z-a]`, `compile` → `None` | Rinviabile | Casi patologici |
| 5 | Regex `_DANGER` sui byte del JUnit | Rinviabile | Falso rifiuto raro; da togliere quando P4 legge JUnit reali |
| 6 | Limiti di `testids` e dello scanner JS (`describe` con opzioni, `.each`, JSX) | Rinviabile | La rete grezza fail-closed copre lo sfasamento; li ricalcola il gate |
| 6 | Continuazione con CRLF | Rinviabile | Coperto dalla rete grezza |
| 7 | Punteggiatura quotata spezzata, `env -S` | Rinviabile | Direzione sicura o caso raro; **rivedere insieme a I3** |
| 7 | `write_targets` con segnaposto, dimensione di `bash.py` | Rinviabile | Gestito |
| 8 | `parse_report` annidato, `waivers.parse` senza controllo del numero d'issue, `declared_by`, `size_reason` | Rinviabile | Coerenza verificata dal gate (1.2: deroghe dichiarate dall'agente) |
| 9 | `toplevel` dentro una cartella `.git`, `surrogateescape` | Rinviabile | Casi limite |
| 9 | Indice copiato due volte | Rinviabile | 0,07-0,30 s misurati |
| 10 | Figli in background vivi dopo `verify`; `KeyboardInterrupt`; report validato solo lessicalmente | Rinviabile | Un `killpg` a fine normale costa una riga: consigliato, non bloccante |
| 11 | `waiver add` senza lock, `.tmp` fisso | **Consigliato con C1** (M6) | Stesso difetto di C1, correzione identica |
| 12 | Test OFF senza sentinella, avviso ripetuto, `ReadDb` aggirabile via `_conn`, prompt_submit non documentato | Rinviabile | `_conn` è una protezione contro l'uso accidentale, coerente con 1.1 |
| 13 | `UserPromptExpansion` senza matcher; OFF scaduto con due righe `on`; OFF non atomico | Rinviabile | Costo: qualche avvio della shell in più |
| 13 | `hooks/run:65`: cifre non ASCII con `10#` | **Correggere ora** (una riga, `LC_ALL=C` su quel test) | In bash non interattivo un errore aritmetico può interrompere il ramo off, e l'interruttore d'emergenza deve essere solido |
| 14 | `governing_work` legato; parametro `issue` inutilizzato; `abandon` | Rinviabile a P3 | — |
| 14 | In L1 piano modificabile con `plan_sha` registrato mentre la fase è ancora `plan` | Rinviabile | Finestra quasi nulla: `register_plan` avanza subito a `execution` |
| 16 | Regole distruttive anche in un repo non attivo per le sessioni legate | Rinviabile | Coerente con 6.6 («tutte, in qualunque directory»); serve solo una nota nella spec |
| 16 | `allow` non esenta script non tracciati; heredoc `bash <<EOF` non scansionato | Rinviabile; heredoc **con I3** | — |
| 16 | MCP consuma l'atto al Pre; chiave con SHA; variabili non espanse | Rinviabile; **rivedere con I2** | — |
| 16 | `find -delete` negato; `xargs rm` | Rinviabile | Limite statico dichiarato |
| 17 | Pre-check con indice divergente; due blocchi con fase vecchia; `GitError` inghiottito; test mancanti; rebase e alias | Rinviabile a P3 | Alias **con I3** per la parte `-c alias.` |
| 18 | Due `Agent` nello stesso messaggio | Rinviabile | Servono due lanci con lo stesso `name` e lo stesso task in sospeso; da coprire con una prenotazione del task in `pre_agent` in P3 |
| 18 | `take_pending(resume=True)` fragile; notifica non chiusa | Rinviabile | — |
| 19 | Il motivo di `tampered` non elenca i file; DONE con commit e working tree sporco | Rinviabile | — |
| 19 | `_receipt_ok` senza `work_base_sha`; test sulla ripresa | Rinviabile | — |
| 20 | Criterio 34 passa anche in `protected`; criterio 19 solo sulla lunghezza | Rinviabile | Il criterio 19 è coperto anche da `test_inject_budget_session_start` (righe e caratteri) |

---

### Rifiutati

Comportamenti considerati e lasciati fuori perché esterni al piano o alla spec:
- Scritture su file protetti con un interprete (`python3 -c 'open("tollgate.toml","w")'`, `node -e`, `perl -e`): limite dichiarato in 1.1 («nessuna garanzia contro un agente che lavora apposta») e in 3.1 («un agente può importare il modulo Python»).
- Salto degli hook del progetto con variabili d'ambiente (`HUSKY=0`, `SKIP=…` di pre-commit): 7.4 nomina solo `--no-verify` e `core.hooksPath`; sono hook del progetto, non di tollgate.
- Alias di git scritti con `git config --global alias.x 'push -f'`: `--global` non è un file protetto (spec 0); la parte con `-c` è dentro I3.
- Comandi `!` digitati dall'utente nel prompt: 1.2, fuori dagli hook per verifica di P0.
- Una notifica `<task-notification>` incollata dall'utente: l'utente è fidato e il prompt non lo produce il modello.
- Revisori, avversari e auditor a `SubagentStop`; `open-pr` che rifiuta deroghe in attesa: P3 per decisione 8 e vincoli per P3.
- Esattezza del conteggio dei token dal transcript (`cache_read` escluso): decisione 20, tarabile con D.
- Forma degli identificativi Go: decisione 19, nessun gate Go nel nucleo.
- `marketplace.json` e `version` nelle `dependencies`: decisione 23 e ruling del Task 13, a P3.
- Test spostati fuori da `test_globs` con una rinomina: li ricalcola il gate con gli identificativi della base (P4, 9.2).
- Prestazioni di `level_records` a ogni Bash nel worktree: misurate nei rinviati del Task 9, entro la scadenza.
- Rete negli hook: nessun uso trovato (`socket` serve solo per `gethostname` negli eventi).

---

### Raccomandazioni

1. Correggere C1 e aggiungere il test deterministico con l'ora bloccata. Poi ripetere `test_concurrent_first_open` almeno 200 volte e la suite completa con `-W error::ResourceWarning` su 3.11 e 3.13.
2. Correggere C2 introducendo un solo aiuto in `_common` (percorso lessicale più percorso risolto) usato da `writes.py`, `bash_rules.py` e `_removes_protected`, così la logica resta in un punto.
3. Per I1, decidere con l'utente il meccanismo, perché tocca il wrapper e la spec 7.1 punto 3: elenco delle radici attive nello stato più `grep -F` nell'input dei `PreToolUse`. Scrivere la decisione nella revisione 22 della spec.
4. Sonda di 5 minuti su `PostToolUseFailure` (I2) prima di cambiare `hooks.json`.
5. I3 in un solo commit su `bash.py`, con i casi delle sonde come test.
6. Ruling sulla deviazione M1. Allineare M4 e M5 nella documentazione.
7. Tra i rinviati: la riga `LC_ALL=C` in `hooks/run` e il nome unico del `.tmp` in `waiver_cli` (M6), insieme a C1.

**Ruling del ledger.** Non ne trovo di sbagliate. Due sono incomplete:
- il **Task 16** (consumo dell'atto a `PostToolUse`) è giusto nell'intenzione, ma senza `PostToolUseFailure` apre il buco di I2;
- il **Task 12** (OFF prima del parsing) è corretto, ma la regola «cwd inesistente → 2» del Review Focus 2 è stata abbandonata senza una ruling (M1).

Le altre, in particolare C1 (niente copia su un DB nuovo), C12, C14, il fail-closed di test-guard nel Task 6 e la regola «status sconosciuto = report non valido» del Task 8, sono miglioramenti giustificati e coerenti con la spec.

---

### Valutazione

**Pronto per il merge?** Con correzioni.

**Motivo:** l'architettura, la separazione tra moduli e la condotta fail-closed sono solide, e la suite è ampia e realistica. Restano però un difetto di concorrenza nel DB (C1), che rende `tests/run` casuale e colpisce la migrazione 2 sul campo, e un falso negativo sulla protezione di `settings.json` in una configurazione comune (C2). Vanno chiusi prima del merge. I1-I3 sono fortemente consigliati nello stesso giro, o al più tardi come primo lavoro di P3, con una ruling esplicita.
