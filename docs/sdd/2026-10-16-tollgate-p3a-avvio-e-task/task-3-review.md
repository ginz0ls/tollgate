# Revisione Task 3 — `start` su un lavoro nuovo (commit 6d5c654)

Revisore: sola lettura sul pacchetto `review-75d9f98..6d5c654.diff`. Controlli mirati fuori dal diff: `bin/tollgate_core/cli.py` (gestione eccezioni di `main`), `phases.create_work` (WorkExists), `sessions.alive`, `db.backup` (nome dei `.tmp-*`), `tests/test_layers.py` (radice di composizione), spec 6.1. Nessun test rilanciato; l'evidenza del report (762 test verdi su 3.11 e 3.13, RED documentato) è coerente col diff.

### Aderenza

- ✅ `naming.py` puro: `slug` (NFKD, `[a-z0-9-]`, 40 caratteri, taglio senza trattino finale, `issue` se vuoto), `branch_name` con `-2…`, `implementer_name` con `-r<giro>` da 4 (`naming.py:42-60`). Test del brief tutti presenti più due extra.
- ✅ `gitw.py`: `fetch` falso senza rete e mai eccezione (`gitw.py:431`), `worktree_add` con `--no-track` (C18, `gitw.py:444`), `add_excludes` senza duplicati sulla cartella comune, `remote_branches` con `ls-remote`.
- ✅ `gh.py`: nessun testo dell'issue negli argomenti, solo numeri/SHA/prefissi da numeri (`gh.py:349,363,373`); `auth_ok`, `commit_state` sui soli contesti obbligatori (C7), `GhError` per assenza/uscita/JSON.
- ✅ `prereq.py`: C5 (chiave esatta poi `superpowers@*`, versione più alta, forme anomale → `None`), `GATE_FILES` (decisione 8), `is_github` su URL grezzo con test su `github.com.evil.example`, `skill_installed` con nomi validati contro `../` (decisione 16).
- ✅ `start.py`, ordine C4: toplevel/main → origin → fetch annotato → predefinito → `tollgate.toml` su `origin/<def>` → `load_config` → `cli_session` → `find_active` (→ `_resume`) → rifiuto senza rete → prerequisiti raccolti → issue e rami/PR → controlli → rifiuto adopt prima della conferma → creazione. Codici 0/1/3 e ultima riga `prossimo passo: EnterWorktree` come da brief.
- ✅ Livello: massimo tra `--level`, etichette e L2 per autore non fidato (`start.py:837-841`); autore vuoto → L2.
- ✅ `work_base_sha` = SHA già risolto e passato come `start_point` (`start.py:848-852`): stessa lettura per ramo e riga.
- ✅ Registrazioni: `db.backup`, `active.register(extra=[wt], force=True)` (C6), `mark_bound`, `add_excludes` (tre righe, decisione 4), `issue.md`, `housekeeping.run`.
- ✅ `prune_bound` (vincolo 3): tiene sessioni di lavori non chiusi o vive; test su lavoro chiuso.
- ✅ Focus 1 (issue ostile): lo slug è `[a-z0-9-]`; il testo non entra in `gh` né in `git` (il test controlla le chiamate a fakegh; i comandi git ricevono solo ramo e percorso derivati dallo slug); recinto calcolato su titolo+etichette+corpo (`start.py:678-691`) con riga «DATO NON FIDATO» prima; `start` non stampa il titolo (`start.py:862-866`).
- ✅ Focus 3 (avvio interrotto): ramo locale `tg/N-*` senza riga → rifiuto con `/tollgate:adopt #N`, nessun `-2`; il test copre ramo locale, remoto e PR (con falso positivo `tg/70-` escluso dal prefisso con trattino).
- ✅ Focus 5 (spazi): `test_start_creates_work_in_path_with_spaces` asserisce lo spazio nel percorso del worktree e `EnterWorktree <percorso>` esatto.
- ⚠️ Non verificabile dal diff: comportamento reale di `gh api repos/{owner}/{repo}/...` (segnaposto risolti dal vero `gh`); verificato solo contro `fakegh`. Il report dichiara di aver verificato il solo campo `authorAssociation` mancante in `gh issue view`.
- ✅ Scostamenti del report (REST invece di `issue view`, `defaultBranch` dopo il controllo «repo attivo», `FlowLab(worktree=...)`) sono motivati e additivi. Layering: `cli.py` è la radice di composizione dichiarata in `test_layers.py:7`, quindi l'import di `tollgate_flow` lì è lecito.

### Punti di forza

- Rifiuti raccolti in un solo messaggio (`start.py:707-728`, test `test_refusals_are_collected`), invece di un rifiuto alla volta.
- Rifiuto `adopt` prima della richiesta di conferma: niente conferma inutile (`start.py:820-827`, test dedicato).
- `fetch`, `remote_branches`, `auth_ok`, `skill_installed` non sollevano mai su assenza di rete/strumenti.
- Test negativi accurati (autori fidati restano L0, altri contesti in `failure` non bloccano, PR di un altro numero non confonde).

### Rilievi

**Critical:** nessuno.

**Important**

1. `bin/tollgate_flow/start.py:795,848,858` e `bin/tollgate_core/cli.py:~212` — `gitw.GitWriteError` (da `set_config`, `worktree_add`, `add_excludes`) e `OSError` (`mkdir` a `start.py:847`, `_write_issue` a `start.py:859`, `mark_bound`) non sono catturati né in `start` né in `main` (che gestisce solo `DbError`, `UsageError`, `TransitionError`, `sqlite3.Error`). Un `git worktree add` fallito (disco pieno, ramo creato da una corsa, permessi) o un errore di scrittura dopo la riga produce un traceback Python al modello invece di un rifiuto in italiano, e gli errori dopo `create_work` (`start.py:855-860`) lasciano una riga senza `issue.md`, senza registrazioni o senza `exclude`. Correzione: in `_create` avvolgere `worktree_add` in `try/except GitWriteError` → `_refuse(...)`; avvolgere i passi 855-860 in `try/except (GitWriteError, OSError)` che aggiunga un avviso «registrazione incompleta: …» (la riga esiste, la ripresa del Task 4 completa) e prosegua o rifiuti con messaggio; catturare `GitWriteError` per `set_config` a `start.py:795`. Aggiungere un test con `worktree_add` che fallisce (es. destinazione non scrivibile) che asserisce uscita 1 e messaggio, e un test con `issue.md` non scrivibile.

**Minor**

2. `start.py:849-854` — se `create_work` solleva `WorkExists` (corsa tra due `start`) il worktree e il ramo appena creati restano, e il messaggio non lo dice. Raro; basta citare ramo e percorso nel rifiuto, o rimuovere il worktree appena creato.
3. `bin/tollgate_flow/housekeeping.py:522-527` e `sessions.py:241` — `json.loads(row[0])` su `sessions` malformato solleva `ValueError`, non catturato (si prende solo `sqlite3.Error, OSError`) dopo che il lavoro è già stato creato. Inoltre un errore in `prune_events` salta `prune_bound`: separare i due `try`.
4. `bin/tollgate_flow/gh.py:362-368,381-386` — `gh pr list --limit 200` e `issue list --limit 100` filtrano per prefisso lato client: in un repo con più di 200 PR una PR `tg/N-*` vecchia può sfuggire alla guardia «adopt». Il ramo remoto (ls-remote) copre il caso normale; documentarlo o paginare.
5. `start.py:740` — `_checks` rilegge `git.resolve_ref(main, ref)` invece di usare `base_sha` già in mano (e potrebbe passare `None` a `commit_state`). Passare `base_sha`.
6. `start.py:842` — `taken` usa `remote_branches` che in caso di errore ritorna `[]` in silenzio: l'unicità del nome verso `origin` dipende dalla sola ls-remote riuscita poco prima. Accettabile dopo un fetch riuscito; nota.
7. `bin/tollgate_flow/prereq.py:604` — `subprocess.run` senza timeout né gestione di `FileNotFoundError`, a differenza di `gitw._run`. Riusare `git.py` o un helper con timeout.
8. `tests/test_start.py:1349` — il caso `("gh", dict(), no_auth)` asserisce la sottostringa «gh», che trova quasi ogni messaggio; usare «gh auth status» o «autenticato».
9. `tests/test_start.py:1497-1525` — il test ostile asserisce l'assenza di `/tmp/PWNED` e l'assenza del titolo nelle chiamate `gh`, ma non nelle chiamate `git` (la protezione c'è per costruzione, lo slug). Opzionale: asserire che il nome del ramo e del worktree non contengano il titolo grezzo (già implicito dal regex `[a-z0-9-]`: nessuna azione richiesta).

### Valutazione

**Qualità del task: Da correggere.**
**Motivo:** requisiti e decisioni di `carry.md` sono rispettati e i test coprono bene i casi ostili, di spazi e di avvio interrotto; resta da chiudere il rilievo Important 1 (errori di git/filesystem non gestiti in `_create` e `set_config`: traceback e stato parziale invece di un rifiuto leggibile), con due test. Il resto è Minor.
