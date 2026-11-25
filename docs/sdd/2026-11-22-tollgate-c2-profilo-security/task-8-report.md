# Task 8: report dell'implementatore (opus)

## Cosa ho fatto

- **Script** `spikes/run-b1-flow.sh`: nuovo caso `B1_FLOW_CASE=security` (C2, decisione 16), costruito sul caso `database`.
  - Blocco del caso: `PROJ=spikes/c2/flow`, `SPEC_SRC`/`PLAN_SRC` in `spikes/c2/input/`, `SPEC_REL=docs/superpowers/specs/2026-11-22-prova-c2.md` (D9), `PLAN_REL=docs/superpowers/plans/2026-11-22-prova-c2.md`, `ISSUE_TITLE`, `PROJ_FILES`, `PROFILE_AREA=security`, `PROFILE_FILE=app/auth/tokens.py`, `START_LEVEL=L2`, `SLICES=1`.
  - `OUT` = `docs/verifiche/evidenze/c2/flusso` (anche con `B1_FLOW_EVIDENCE=c2`, che dà la stessa cartella).
  - `PROPOSE=1`, `SERVICES=1`; valori ammessi con `security`; `B1_FLOW_RULES=vere` obbligatorio (la guardia esistente vale per ogni caso diverso da `b1`).
  - Tutto ciò che nel caso `database` era «L2» ora dipende da `START_LEVEL=L2` e non dal nome del caso: `controlla` (sei passi più `libero`), `prompt_l2_passo1`/`prompt_l2_passo3` (rinominati da `prompt_database_*`, testo invariato: usano solo variabili), `modo_passo1`, `modo_passo2`, il controllo dei file di spec e piano in `controlla`, `registra` su tutti i passi e su `libero-*`. Le sole righe ancora legate al nome `database` sono quelle davvero sue (`OUT`, blocco del caso, programmi del database, riga di `limiti.txt`).
  - `solo_database` diventa `solo_l2`, con il messaggio di D9: «il passo $MODE esiste solo con B1_FLOW_CASE=database o B1_FLOW_CASE=security».
  - `proponi_profilo`: nei casi L2 controlla in più che il blocco proposto abbia `min_level = "L2"`, `final_specialist` e `checklist` non vuoti; altrimenti `prepara` si ferma («il blocco [profiles.<area>] proposto non ha min_level = "L2", final_specialist e checklist»). Vale anche per `database` (il suo frammento li ha: i test del caso restano verdi). Senza la skill approvata `prepara` rifiuta come prima («… non ha un blocco [profiles.security] che copra app/auth/tokens.py»).
  - `--disallowedTools` del caso: gli stessi programmi di `backend` (vercel, wrangler, docker, npx, bunx, pnpx, bun, npm, pnpm, yarn, supabase, deno, node) più `psql`, `openssl` (Global Constraints di C2) e i caricatori di segreti delle istruzioni di C2 (`dotenv`, `dotenvx`, `cross-env`, `env-cmd`, `doppler`, `infisical`, `op`), ognuno nelle quattro forme. `registra` li cerca in posizione di comando in `comandi-rischiosi.txt` (stessa regex di prima, alimentata da `DEPLOY_CLIS`).
  - `limiti.txt`: le righe comuni nominano anche `security`; due righe nuove `(security)` (programmi negati in più; progetto con sola libreria standard e segreto finto `PROVA-123` da `C2_PROVA_SECRET`; i test non provano un servizio di login vero; limiti della grep).
  - Commenti d'uso in testa e riga d'uso finale aggiornati.
- **`spikes/b1/flowreg.py`**: `# Regole security (versione 1)` in `AREA_TITLES`.
- **Progetto di prova** `spikes/c2/flow/` (decisione 16, alla lettera): `tollgate.toml` (uguale a quello di B7: `verify = "python3 tools/unittest_junit.py"`, `report = "junit:reports/junit.xml"`), `issue-1.md`, `.gitignore` (`reports/`, `__pycache__/`, `.env*`), `tools/unittest_junit.py` (copia byte per byte di B7, provata da un test), `tests/__init__.py`, `app/__init__.py`, `app/auth/__init__.py`, `app/notes.py` (`Note(id: int, owner: str, text: str)`, dataclass congelata, archivio in memoria con `add_note`, `get_note`, `clear_notes`), `app/auth/tokens.py` (`sign(user: str, expires_at: int, secret: bytes) -> str`, `verify(token: str, secret: bytes, *, now: int) -> str | None`, firma HMAC-SHA256 di `hmac`, token `<utente>.<scadenza>.<firma>`), `tests/test_tokens.py` (`TokensTest`: `test_valid_token_returns_user`, `test_altered_token_is_rejected`; `setUp` imposta `C2_PROVA_SECRET=PROVA-123` con `mock.patch.dict` e ne legge la chiave).
  - Codice di partenza incompleto, non sbagliato: `verify` non controlla la scadenza (`now` non usato, la docstring dice solo che la scadenza non è ancora controllata) e confronta la firma con `!=`. Nessun confronto a tempo costante, nessuna lettura del segreto nel codice dell'app (la lettura da `C2_PROVA_SECRET` arriva con `read_note` nel Task 2 del lavoro di prova: lì scatta R-SECURITY-05), nessun test del caso negato, nessun commento che li suggerisca.
- **Spec di prova** `spikes/c2/input/spec-L2.md`: una fetta; M1 «Un token scaduto non è valido: `verify` restituisce `None`» (`tests.test_tokens.TokensTest::test_expired_token_is_rejected`), M2 «Il proprietario legge la propria nota con un token valido» (`tests.test_notes.NotesTest::test_owner_reads_own_note`); per D2 una sezione «Chi lo usa, quali dati e segreti tocca» fuori dai must-have (utente con un token firmato; note dell'archivio in memoria; un solo segreto da `C2_PROVA_SECRET`, `PROVA-123` nei test; un token alterato o scaduto non vale); tane di coniglio (rinnovo, formato, orologio come argomento `now`, scadenza nell'istante `now` = scaduto); cosa non fare.
- **Piano di prova** `spikes/c2/input/piano-L2.md`: le sezioni di `plan.required_sections` (come B7); Task 1 scadenza in `app/auth/tokens.py` (M1); Task 2 `can_read(user: str, note: Note) -> bool` in `app/auth/access.py` usato da `read_note(token: str, note_id: int, *, now: int) -> Note | None` in `app/notes.py` (M2), con la chiave letta da `C2_PROVA_SECRET`. Nessuna delle parole vietate.
- **Test** in `tests/test_b1_scripts.py`: `FlowBench.src_repo` copia anche `skills/rules-security` e accetta `security_approved` (D9); 22 test nuovi del caso `security` (elenco sotto).

## Test nuovi (22)

I 16 del piano: `test_flow_case_security_out_dir` (anche con `B1_FLOW_EVIDENCE=c2`), `test_flow_case_security_requires_real_rules`, `test_flow_case_unknown_value_names_security`, `test_real_flow_case_security_prepara_proposes_profile` (blocco con `paths = ["app/auth/**"]`, `min_level = "L2"`, `final_specialist = "tollgate:final-security"`, `agent`, `reviewer`, la `checklist` del frammento, regole `R-SECURITY-`; il solo profilo `security`), `test_real_flow_case_security_prepara_refuses_without_profile`, `test_real_flow_case_security_project_verifies`, `test_flow_disallows_tools_security`, `test_real_flow_case_security_project_has_no_credentials` (gli unici nomi `*SECRET|KEY|TOKEN|PASSWORD*` sono `C2_PROVA_SECRET`, gli unici valori `PROVA-…` sono `PROVA-123`, solo nei test; nessun file `.env*`, `.pem`, `.key`…; nessuna stringa che somigli a una credenziale), `test_real_flow_case_security_plan_does_not_list_rule_requirements` (piano, spec, issue e codice di partenza), `test_real_flow_case_security_spec_must_haves`, `test_flow_case_security_has_six_steps` (anche `--model opus` in ogni chiamata), `test_real_flow_case_security_prepara_checks_l2_plan`, `test_flow_case_security_rot_moves_every_step`, `test_flow_case_security_registra_reads_every_step`, `test_real_flow_case_security_spec_has_one_slice`, `test_real_registra_reads_security_title` (il titolo letto dalla skill vera è `# Regole security (versione 1)`).

I 4 di D9: `test_flow_case_l2_steps_refused_for_other_cases` (passi 3-6 e `libero` per `ai`, `infra`, `backend`, `frontend` e `b1`, con il messaggio di D9), `test_real_flow_case_security_project_declares_junit_report`, `test_real_registra_flags_tools_security` (`openssl` compreso, con percorso, dopo `&&`, dopo `env`; i comandi su `app/auth` e `grep -rn openssl app` non contano), `test_real_scrivi_limiti_heading_is_generic_security`.

Due in più, miei: `test_real_flow_case_security_prepara_refuses_a_block_without_specialist` (il controllo nuovo di `prepara` sul blocco L2) e `test_real_flow_case_security_starting_code_is_incomplete` (in una copia temporanea con `python3 -B`: firme di `sign` e `verify` della decisione 16, un token scaduto vale ancora, un token alterato o con un'altra chiave no, `Note` con i tre campi, `read_note` e `access.py` assenti).

I test del caso `database` sono invariati e verdi con `solo_l2` (`test_flow_case_database_steps_only_for_database` trova ancora «B1_FLOW_CASE=database» nel messaggio).

## Evidenza TDD

RED (`.superpowers/sdd/2026-11-22-tollgate-c2-profilo-security/task-8-red.log`), con i soli test di `src_repo` e i 22 nuovi, prima di script e progetto:

```
$ timeout 900 python3 -B -m unittest -k security -k l2_steps tests.test_b1_scripts
Ran 22 tests in 3.968s
FAILED (failures=55, errors=7)
```
Tutti e 22 rossi: `B1_FLOW_CASE=security` rifiutato come valore sconosciuto, progetto e input assenti (`FileNotFoundError`), messaggio di `solo_database`.

GREEN, dopo script e progetto (primo giro: un solo rosso, `test_real_registra_flags_tools_security`, perché il test cercava «non prova un servizio di login vero» e `limiti.txt` dice «non provano»: ho corretto la parola nel test):

```
$ timeout 1800 python3 -B -m unittest tests.test_b1_scripts
Ran 161 tests in 249.863s
OK
```
(`task-8-green.log`). `bash -n spikes/run-b1-flow.sh`: uscita 0.

Suite completa: vedi in fondo.

## `controlla` per il caso `security`

`B1_FLOW_CASE=security B1_FLOW_RULES=vere B1_FLOW_EVIDENCE=c2 bash spikes/run-b1-flow.sh controlla`: uscita 0, `CONTROLLA: ok`, nessuna cartella creata (uscita intera in `task-8-controlla.txt`; il percorso del repo contiene il nome utente, qui ridotto).

```
radice di lavoro: /tmp/tollgate-b1
B1_FLOW_RULES: vere
B1_FLOW_CASE: security
cartella delle uscite: <repo>/docs/verifiche/evidenze/c2/flusso
--- i passi
  prepara   copia del plugin in /tmp/tollgate-b1/plugin (regole vere), progetto di spikes/c2/flow in /tmp/tollgate-b1/flow, poi init --propose sulla copia e commit del blocco [profiles.security]
  passo1    claude plugin validate --strict sulla copia, poi claude -p "/tollgate:start #1 L2" dal checkout, con la spec scritta con Write nel worktree del lavoro
  passo2    dal worktree: /tollgate:approve spec 1
  passo3    dal worktree: Write del piano, commit, poi l'avversario del piano fino a /tollgate:approve plan
  passo4    dal worktree: /tollgate:approve plan
  passo5    dal worktree: /tollgate:execute fino alla chiusura dei due task, senza /tollgate:finish
  passo6    dal worktree: /tollgate:finish fino a finish open-pr (gh finto)
  libero    dal worktree: un prompt dato, ripetibile (cartelle libero-1, libero-2, ...), per un giro di correzione
CONTROLLA: ok
```

Dal comando del passo 1 (uguale per tutti i passi):

```
--model opus
--disallowedTools Bash(*/gh:*),Bash(command gh:*),Bash(gh repo:*),Bash(gh api:*),Bash(gh auth:*),Bash(gh secret:*),Bash(git push https:*),Bash(git push http:*),Bash(git push ssh:*),Bash(git push git@:*),Bash(git push --force:*),Bash(git push -f:*),Bash(git push --mirror:*),Bash(git push --delete:*),Bash(curl:*),Bash(wget:*),Bash(*/curl:*),Bash(*/wget:*),Bash(vercel:*),Bash(*/vercel:*),Bash(command vercel:*),Bash(env vercel:*),Bash(wrangler:*),…,Bash(docker:*),…,Bash(npx:*),…,Bash(bunx:*),…,Bash(pnpx:*),…,Bash(bun:*),…,Bash(npm:*),…,Bash(pnpm:*),…,Bash(yarn:*),…,Bash(supabase:*),…,Bash(deno:*),…,Bash(node:*),…,Bash(psql:*),Bash(*/psql:*),Bash(command psql:*),Bash(env psql:*),Bash(openssl:*),Bash(*/openssl:*),Bash(command openssl:*),Bash(env openssl:*),Bash(dotenv:*),…,Bash(dotenvx:*),…,Bash(cross-env:*),…,Bash(env-cmd:*),…,Bash(doppler:*),…,Bash(infisical:*),…,Bash(op:*),Bash(*/op:*),Bash(command op:*),Bash(env op:*)
```
(«…» = le altre tre forme dello stesso programma; la riga intera è in `task-8-controlla.txt`.)

## I prompt dei sei passi (in breve)

- passo1 (dal checkout `/tmp/tollgate-b1/flow`): `/tollgate:start #1 L2`, poi «non avviare il brainstorming… scrivi con Write nel worktree del lavoro, in `docs/superpowers/specs/2026-11-22-prova-c2.md`, esattamente il testo tra `<<<SPEC` e `SPEC>>>`, committalo, poi segui /tollgate:spec-audit finché audit prepare non chiede /tollgate:approve spec 1», con la spec di `spikes/c2/input/spec-L2.md`.
- passo2 (dal worktree): `/tollgate:approve spec 1` (atto dell'utente).
- passo3: Write del piano in `docs/superpowers/plans/2026-11-22-prova-c2.md` dal testo tra `<<<PIANO` e `PIANO>>>` (`spikes/c2/input/piano-L2.md`), commit, poi l'avversario del piano finché non chiede /tollgate:approve plan.
- passo4: `/tollgate:approve plan` (atto dell'utente).
- passo5: `/tollgate:execute` «Vai avanti fino alla chiusura dei due task del piano. Non lanciare /tollgate:finish.»
- passo6: `/tollgate:finish`.
- libero "<prompt>": un prompt dato, ogni volta in `libero-<n>`.

## Cosa deve sapere il controller per lanciare la prova (Task 9)

Variabili, sempre tutte e tre: `B1_FLOW_CASE=security B1_FLOW_RULES=vere B1_FLOW_EVIDENCE=c2` (senza `B1_FLOW_CHECK`). Dal worktree `c2`, con `bash spikes/run-b1-flow.sh <modo>`:

1. `controlla`: stampa passi e comandi, nessuna scrittura; deve finire con `CONTROLLA: ok`.
2. `prepara`: copia i soli file tracciati del plugin in `/tmp/tollgate-b1/plugin` (si ferma se la `rules-base` non accende l'interruttore), il progetto in `/tmp/tollgate-b1/flow` (senza `issue-1.md`), `origin` nudo locale, stato di prova con la sentinella in `/tmp/tollgate-b1/state`, gh finto in `/tmp/tollgate-b1/ghbin`; lancia `init --propose` sulla copia e stampa la proposta; controlla il blocco `[profiles.security]` (copre `app/auth/tokens.py`; `blocco L2: ok` per `min_level = "L2"`, `final_specialist`, `checklist`), lo copia in `tollgate.toml`, lo committa e lo spinge; poi `spec-check: ok fette: 1` e `plan-check: ok [...]`; chiude con `pronto: /tmp/tollgate-b1/flow …`. Sposta in `<nome>.prev-<tempo>` ciò che c'era (anche `passo1`…`passo6` e `libero-*` delle evidenze), non cancella nulla.
3. `passo1`: prima `claude plugin validate --strict` sulla copia (esito in `validate/validate-N.txt`; se fallisce, nessun `claude -p`), poi `claude -p` dal checkout. Ogni passo stampa `<passo>, tentativo N: claude -p da <cartella>` e `<passo>: tentativo N, uscita R`; al più 3 tentativi per passo in tutta la prova.
4. Prima del passo 2: confrontare la spec scritta dal modello nel worktree (`docs/superpowers/specs/2026-11-22-prova-c2.md`) con `spikes/c2/input/spec-L2.md` (differenze ammesse: quelle di B7, decisione 16 di B7). Se va bene, l'atto dell'utente è il `passo2` (`/tollgate:approve spec 1`, dato dal controller lanciando il passo).
5. `passo3`; poi lo stesso confronto per il piano (`docs/superpowers/plans/2026-11-22-prova-c2.md` contro `spikes/c2/input/piano-L2.md`), e l'atto dell'utente è il `passo4` (`/tollgate:approve plan`).
6. `passo5`, `passo6`; per un giro di correzione `libero "<prompt>"` (per esempio `/tollgate:execute` sul task di correzione, poi `/tollgate:finish`).
7. `registra`: crea `registro-N` con eventi, `status.json`, `snapshot.json`, `eventi-c1.jsonl`, `comandi-modello.txt`, `comandi-rischiosi.txt` (deve restare vuoto), `precarico.txt`, `trascrizioni.txt` (cerca `# Regole security (versione 1)` nelle trascrizioni dei subagenti delle sole cartelle di sessione della prova, sotto la `HOME`), `tipi-task.txt` (atteso `tollgate:implementer-security` e `tollgate:reviewer-security`), `limiti.txt`; toglie le pagine di terzi dagli stream (`togli-pagine.txt`). Stampa `registrato in …`; con una raccolta fallita l'uscita è diversa da 0 e `fallimenti.txt` dice quale.

Evidenze: `docs/verifiche/evidenze/c2/flusso/` (`<passo>/tentativo-N/` con `argv.txt`, `claude.jsonl`, `claude.err`, `uscita.txt`, `esito.txt`; `exit-codes.txt`; `validate/`; `registro-N/`). Il report di ogni implementatore con la riga `Sicurezza:` si legge nello stato (`snapshot.json`) o negli stream del passo 5.

## File cambiati

- `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `tests/test_b1_scripts.py`
- nuovi: `spikes/c2/flow/{tollgate.toml,issue-1.md,.gitignore,tools/unittest_junit.py,tests/__init__.py,tests/test_tokens.py,app/__init__.py,app/notes.py,app/auth/__init__.py,app/auth/tokens.py}`, `spikes/c2/input/{spec-L2.md,piano-L2.md}`

## Scostamenti dal piano e perché

- `prepara` controlla nel blocco proposto anche `min_level`, `final_specialist` e `checklist` (il brief dice «`prepara` controlla che `init` proponga…»): prima lo controllava solo il test. Vale per ogni caso L2, quindi anche per `database`; il suo frammento li ha e i suoi test restano verdi. Un test in più lo prova.
- Le condizioni «caso L2» usano `START_LEVEL=L2` e non `CASE = database || CASE = security`: un punto solo da cambiare per un caso L2 futuro.
- Programmi negati: oltre ai programmi delle Global Constraints (che con `backend` coprono tutto tranne `openssl` e `psql`) anche i caricatori di segreti delle istruzioni di C2 (`dotenv`, `dotenvx`, `cross-env`, `env-cmd`, `doppler`, `infisical`, `op`): leggono segreti veri, e il caso è di sicurezza. Non entrano negli altri casi (un test lo controlla per `backend`, `frontend`, `database`).
- `app/notes.py` ha, oltre a `Note` e all'archivio, `add_note`, `get_note` e `clear_notes` («un archivio in memoria»: servono al test di M2 e a `read_note`); il piano li nomina nei «Fatti verificati».
- Due test in più (sopra). `test_real_flow_case_security_plan_does_not_list_rule_requirements` controlla anche l'issue e il codice di partenza, e con parole più larghe di quelle del brief (`tempo costante`, `timingSafeEqual`, `senza segreto`, `senza token`, `non è il proprietario`, `R-SECURITY`).

## Autorevisione

- Completezza: tutti i 16 test del piano, i 4 di D9, `SPEC_REL`, messaggio di `solo_l2`, `make_src`, D2 nella spec. Firme e file della decisione 16 alla lettera (un test le prova con `inspect.signature`).
- Nessun `claude`, `gh`, rete o programma vietato lanciato: dello script solo `bash -n`, `controlla` e i test. Ogni `mkdtemp` ha `addCleanup` e prefisso `tollgate-`. Nessuna asserzione stampa `os.environ`. Nessun `__pycache__` nei file aggiunti (il progetto si prova solo in copie con `python3 -B`).
- `tests/run` e `bash -n`: vedi «Suite».

## Dubbi

- `Bash(op:*)`: se il prefisso di `--disallowedTools` non tiene conto del confine di parola, nega anche comandi che cominciano con «op» (per esempio `openssl`, già negato). Non ne conosco altri utili alla prova; se il controller preferisce, si toglie `op` senza altri effetti.
- `app/auth/access.py` importerà `Note` da `app/notes.py` e `app/notes.py` userà `can_read`: un import circolare che l'implementatore della prova dovrà risolvere (import dentro la funzione o annotazioni rinviate). Non è un difetto di sicurezza e non l'ho nascosto né suggerito; lo segnalo perché può costare un giro.
- D2: la spec dice già chi usa, i dati, il segreto e l'input ostile; come previsto da D2, il «modello delle minacce» nel report conterà meno come segnale delle regole.

## Suite

`cd <worktree> && { PYTHONWARNINGS=error::ResourceWarning tests/run; echo "exit $?"; } > <W>/suite-task-8.log 2>&1` (in background, con l'attesa `until grep -q "^exit "`):

```
== Python 3.11.16
Ran 4516 tests in 3432.180s
OK (skipped=16)
== Python 3.13.5
Ran 4516 tests in 3416.898s
OK (skipped=14)
exit 0
```
Nessun «unclosed» né `ResourceWarning` nel file. Prima del commit `git status` mostrava solo i 15 file del task, nessun `__pycache__`.

Commit: `2485d3d` «tollgate C2: prova reale L2 con il profilo security, script e progetto di prova».

## Aggiunta: ritocchi del Task 7 e seconda suite

Su richiesta del controller ho fatto i tre ritocchi di `task-7-fix-1.md`; il dettaglio è nel «Fix round 1» di `task-7-report.md`. La prima suite era già finita e il Task 8 già committato (`2485d3d`), quindi non c'era una corsa da fermare: nessun processo e nessuna cartella `/tmp/tollgate-run-*` rimasti. Ho rilanciato la suite una volta, con i ritocchi nel worktree, sullo stesso `suite-task-8.log`: 4516 OK (3.11.16) e 4516 OK (3.13.5), `exit 0`. Il commit dei ritocchi è `348bfec`, dopo `2485d3d`: l'ordine è l'inverso di quello chiesto, perché non riscrivo la storia.
