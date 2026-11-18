# B7: prova reale L2 con il profilo database

Esito: riuscita (composita)

Data: 17 novembre 2026. Piano: B7 (profilo `database`), Task 8. Stesso schema delle prove di B1-B6, ma con un lavoro di livello L2 portato fino alla revisione finale e alla PR (finta), eseguito con `claude -p` vero. Il profilo `database` è acceso da `init`, con le sue regole vere caricate dagli agenti e lo specialista finale `final-database`. Il lavoro è piccolo: una tabella `tags` collegata a `notes`, con la sua policy di lettura, e la lettura dei tag nella edge function `notes` di un progetto Supabase di prova. Due task, nessuna credenziale, nessun servizio collegato, nessun database: i file `.sql` e `.ts` sono solo testo e i test li leggono come testo.

L'esito è **composito**, per cinque motivi:

- la prova è stata eseguita due volte: la prima si è fermata prima della revisione finale e l'utente ha scelto di rifare da capo;
- a metà del passo 5 della seconda esecuzione l'utente ha dovuto scegliere (R-DATABASE-10 contro la spec) e la scelta è arrivata al modello con il modo `libero`;
- la prova ha trovato un difetto del progetto di prova (prima esecuzione, corretto nel Task 7) e un difetto del prodotto (seconda esecuzione, corretto con il commit `2d1441c`);
- due atti dell'utente (`approve spec 1`, `approve plan`) li ha dati il controller dopo il confronto con l'input (decisione 16);
- la copia del plugin usata dalla prova è stata aggiornata a metà con tre file.

- Versioni: Claude Code `2.1.326` (`registro-1/versione-claude.txt`; nei controlli preliminari il controller aveva annotato `2.1.325`), modello `sonnet` (`claude-sonnet-5-5`).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_CASE=database` e `B1_FLOW_RULES=vere` (modi `controlla`, `prepara`, `passo1` ... `passo6`, `libero` due volte, `registra`). Nessun GitHub vero: `gh` finto (`tests/fakegh.py`), `origin` nudo locale, stato di prova in `/tmp/tollgate-b1/state`. Comandi esatti in `argv.txt` di ogni tentativo.
- Evidenze: `docs/verifiche/evidenze/b7/flusso/` (`validate/`, `passo1` ... `passo6/tentativo-1/`, `libero-1/tentativo-1/`, `libero-2/tentativo-1/`, `registro-1/`, `spec-diff.txt`, `piano-diff.txt`, `exit-codes.txt`). Sono le evidenze della **seconda** esecuzione; quelle della prima sono state tenute fuori dal repo (vedi «La prima esecuzione»). `prepara` non ha una cartella: il suo esito sta nel registro del controller.
- Chi ha fatto cosa: la prova l'ha eseguita il controller (eccezione 2 delle istruzioni); questo rapporto la racconta partendo dalle evidenze e dal registro del controller.
- Prima di partire, nell'ambiente erano assenti `ANTHROPIC_API_KEY`, `SUPABASE_ACCESS_TOKEN`, `SUPABASE_DB_PASSWORD`, `DATABASE_URL`, `DIRECT_URL`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN` e `NPM_TOKEN` (controllata solo la presenza, mai il valore). Il modo `controlla` ha dato ok: `--disallowedTools` nega `supabase`, `psql`, `postgres`, `pg_ctl`, `pg_dump`, `prisma`, `drizzle-kit`, `docker`, `vercel`, `wrangler`, `deno`, `node`, `npm`, `npx` e gli altri lanciatori, nelle quattro forme (da soli, con un percorso, dopo `command`, dopo `env`); `gh`, `curl` e `wget` sono negati come su `main`. Nessun controllo di tollgate è spento nel `tollgate.toml` del progetto di prova.
- `claude plugin validate --strict` sulla copia del plugin: «Validation passed», uscita 0 (`validate/validate-1.txt`); un solo consiglio sul README, che non cambia l'esito.

## Passi, tentativi ed esecuzioni (seconda esecuzione)

Tutti i passi sono riusciti al tentativo 1 (`exit-codes.txt`: uscita 0 per tutti e otto). Gli orari di `esito.txt` sono locali, quelli degli eventi sono UTC.

| Passo | Tentativi | Esito | Durata | Turni | Costo equivalente |
|---|---|---|---|---|---|
| `controlla` e `prepara` | 1 | interruttore acceso, progetto e stato pronti; `init` propone `database`; `spec-check` e `plan-check` ok | n/d | n/d | nessuno |
| `passo1`: `/tollgate:start #1 L2` | 1 | lavoro #1 in L2 sul ramo `tg/1-aggiungi-i-tag-alle-note`; spec scritta con `Write` e committata (`de29f85`), 5 giri avversariali | 241 s | 20 | 0,94 USD |
| `passo2`: `/tollgate:approve spec 1` | 1 | spec approvata, fase `plan`, `spec-approval.md` committato | 20 s | 3 | 0,18 USD |
| `passo3`: piano | 1 | piano scritto e committato (`c88bf8e`), 4 giri dell'avversario del piano | 180 s | 19 | 0,77 USD |
| `passo4`: `/tollgate:approve plan` | 1 | piano approvato, 2 task, fase `execution` | 10 s | 2 | 0,17 USD |
| `passo5`: `/tollgate:execute` | 1 | task 1 fatto e revisionato, **la sessione si ferma** per un conflitto tra R-DATABASE-10 e la spec | 125 s | 10 | 0,66 USD |
| `libero-1` | 1 | scelta dell'utente portata al modello; `task start 1 --fix` riuscito, ma l'implementatore non si raggiunge: nuova fermata | 41 s | 11 | 0,28 USD |
| `libero-2` | 1 | con la correzione del prodotto: task 1 corretto e chiuso, task 2 fatto e chiuso | 207 s | 17 | 0,91 USD |
| `passo6`: `/tollgate:finish` | 1 | `finish check` verde, revisione finale ciclo 1 (`ok`), PR finta #1 | 75 s | 10 | 0,62 USD |

Nessun passo ha avuto un secondo tentativo.

Cosa è successo, in ordine:

1. **`passo1`.** Il modello ha scritto la spec con `Write` nel worktree del lavoro e l'ha fatta passare per cinque giri dell'avversario della spec (`tollgate:spec-adversary`, un agente per giro): giro 1 con un rilievo major, due moderate e due minor; giro 2 con un moderate e tre minor; giro 3 con due minor; giro 4 con tre minor; giro 5 senza rilievi (9 eventi `spec_audit_round` in `registro-1/events.jsonl`, 5 della spec e 4 del piano). I rilievi toccano la policy di lettura, la forma della risposta, il criterio del test di M2, il nome del file della migrazione e la scrittura dei tag (fuori dal lavoro).
2. **`approve spec 1` dato dal controller.** Prima di darlo il controller ha confrontato la spec committata con l'input (`spikes/b7/input/spec-L2.md`): `spec-diff.txt` è il confronto. Ogni differenza viene da un rilievo dei giri avversariali. Una differenza pesa sulla prova: al giro 3 l'avversario ha proposto due correzioni per l'indice su `tags.note_id` (creare l'indice, oppure dire «nessun indice, fuori scopo») e la sessione ha scelto la seconda. La spec approvata dice quindi «nessun indice su `note_id`», **in contrasto con R-DATABASE-10**, che blocca. Il controller non l'ha cambiata (non è un suo atto): la prova ha misurato come la trattano implementatore, revisore e specialista.
3. **`passo3` e `passo4`.** Il piano è stato scritto e committato in `passo3`, corretto in quattro giri dell'avversario del piano (giro 1 con un major e due moderate, giro 2 con due minor, giro 3 con un moderate, giro 4 senza rilievi). `approve plan` dato dal controller dopo il confronto con l'input (`piano-diff.txt`): le differenze vengono dai rilievi e riprendono la spec approvata. Il piano non nomina `(select auth.uid())` né come si annulla la migrazione; ripete «nessun indice su `note_id`».
4. **`passo5`.** L'implementatore del task 1 (`tollgate:implementer-database`) ha chiuso con `DONE_WITH_CONCERNS`; il revisore (`tollgate:reviewer-database`) ha dato `changes` con un rilievo `major` su R-DATABASE-10 (manca l'indice su `tags.note_id`). La sessione principale non ha lanciato `task done 1` e ha chiesto all'utente: aggiungere l'indice con `--fix` scostandosi dal piano e dalla spec, oppure tenere la decisione con `/tollgate:resolve`.
5. **La scelta dell'utente.** L'utente ha scelto «Aggiungi l'indice»: vale R-DATABASE-10. La scelta è arrivata al modello con il modo `libero` (`libero-1`), con un prompt che la riporta alla lettera e chiede di proseguire con `/tollgate:execute` fino alla chiusura dei due task, senza `/tollgate:finish` (`passo5` ha un prompt fisso che avrebbe rifatto la stessa domanda).
6. **`libero-1`: il difetto del prodotto.** `task start 1 --fix` è riuscito (giro di correzione 1, task `running`, in attesa di «resume» dell'implementatore). Ma la sessione `claude -p` di `passo5` era finita, e `SendMessage` all'implementatore ha risposto «not reachable». Un implementatore nuovo con lo stesso nome è stato **negato dall'hook** (evento `veto`, regola `writer`: «non ha un task start in sospeso»). Il modello non ha aggirato l'hook e si è fermato. Vedi «Difetti trovati».
7. **La correzione del prodotto** (`2d1441c`, con revisione) e la ripresa con **`libero-2`**: un implementatore nuovo (`tg-1-t1`) è stato lanciato in una sessione nuova con il brief di correzione `task-1-fix-1.md`, ha aggiunto `create index on public.tags (note_id);` e ha esteso il test; `reviewer-database` ha approvato e `task done 1` è passato. Poi il task 2 (`tg-1-t2`): test rosso, poi verde, `select("id, title, body, tags(id, text)")`; approvato, `task done 2`.
8. **`passo6`.** `finish check` verde (ricevuta `verify` green sullo SHA finale, 3 test; l'unica riga di attenzione è informativa: `allow_no_tests` è acceso), revisione finale al ciclo 1, PR finta #1 aperta con il `gh` finto (`registro-1/fakegh.log`). Nessuna voce `[no]` nella Definition of Done. L'atto `finish` è `a-3` in `events.jsonl`.

Gli atti di approvazione, `approve spec 1` e `approve plan`, sono registrati in `events.jsonl` come atti dell'utente (`a-1`, `a-2`, fonte `claude-code`); la spec e il piano non li ha scritti il controller: li ha scritti il modello, e il controller ha solo dato l'atto dopo il confronto con l'input.

## Proposta di `init`

Il progetto di prova è una migrazione (`supabase/migrations/20261112000000_notes.sql`, tabella `notes` con RLS e una policy di lettura), una edge function (`supabase/functions/notes/index.ts`), `supabase/config.toml` con PostgreSQL 15, due file di test Python che leggono i testi (`tests/test_migrations.py` e, dopo il lavoro, `tests/test_function.py`), un `verify` con `tools/unittest_junit.py` e `report = "junit:reports/junit.xml"`, e i workflow di tollgate. Nessun file `.tsx`.

- `init` propone `database` con `paths` che comprendono `supabase/**` (qui con la forma `/supabase/**` dei percorsi alla radice nel `tollgate.toml` proposto), `min_level = "L2"`, `final_specialist = "tollgate:final-database"` e la `checklist` («migrazioni reversibili e dati esistenti; con PostgreSQL anche RLS sulle tabelle nuove e indici delle policy e delle chiavi esterne»). Il frammento del profilo è `templates/profiles/database.toml`; la proposta è stata copiata nel `tollgate.toml` del progetto e committata (`e57de4a`, «profilo database proposto da init»).
- Gli altri profili non sono proposti: nessun file corrisponde ai loro percorsi.
- Non c'è una cartella `prepara/` nelle evidenze: l'esito di `prepara` (profilo proposto, `spec-check` ok con una fetta, `plan-check` ok) lo ha annotato il controller nel registro. Questo punto non si riverifica dalle evidenze.

## Il lavoro in L2 e gli agenti lanciati

Diciotto subagenti in tutto nella seconda esecuzione (`registro-1/events.jsonl`, eventi `subagent_start`):

| Passo | Agenti |
|---|---|
| `passo1` | 5 `tollgate:spec-adversary` (uno per giro) |
| `passo3` | 4 `tollgate:plan-adversary` (uno per giro) |
| `passo5` | task 1: `tollgate:implementer-database` e `tollgate:reviewer-database` |
| `libero-2` | task 1 (correzione): implementatore nuovo e `reviewer-database`; task 2: `implementer-database` e `reviewer-database` |
| `passo6` | `tollgate:final-reviewer`, `tollgate:final-database`, `tollgate:finding-verifier` |

`registro-1/tipi-task.txt`: entrambi i task con `agent_type=tollgate:implementer-database` e `reviewer_type=tollgate:reviewer-database`. `libero-1` non ha lanciato nessun subagente (l'unico tentativo è il veto). Il lavoro in L2 è quello descritto sopra: spec con giri avversariali, piano con giri avversariali, due atti dell'utente, esecuzione con revisore per task, revisione finale con specialista e verificatore dei rilievi.

Per i task: nota di ricerca prima di ogni modifica (`registro-1/research-1.md` e `research-2.md`). La nota del task 1 è stata rifiutata una volta («il file della spec è nella nota ma non l'hai letto in questo task»: eventi `research_note`, `ok: false`) e accettata al secondo invio; la nota del task 2 è stata valida al primo. Nessun veto di `research_gate`: le note sono arrivate prima delle modifiche.

Il giro di correzione del task 1 (`fix_rounds` 1 in `stats.json`) ha cambiato la migrazione e il test: `afdd9db` («indice su tags.note_id e verifica di (select auth.uid()) nel test»). Il lavoro finale ha tre commit di codice dopo l'approvazione del piano (`3ce626f`, `afdd9db`, `18896e6`; `registro-1/git-log-worktree.txt`).

## Lo specialista finale

- `passo6` lancia tre agenti: `tollgate:final-reviewer` (generale), `tollgate:final-database` (lo specialista) e, per i rilievi, `tollgate:finding-verifier`. Il controller ha letto dallo stato (non è nelle evidenze del repo, perché lo stato sta sotto `/tmp/tollgate-b1/state`) che `review_cycles.reviewers` è `["tollgate:final-reviewer", "tollgate:final-database"]` e che i due riporti sono `ok` (`reported = {final-reviewer: ok, final-database: ok}`, esito del ciclo `ok`). Nelle evidenze il ciclo si vede in `registro-1/events.jsonl` (evento `review_cycle`: `number` 1, `outcome` `ok`, `findings_confirmed` 1).
- **Il brief.** Il file di brief della revisione finale, letto dai due revisori finali nello stream di `passo6` (righe 76 e 89 di `passo6/tentativo-1/claude.jsonl`), ha la sezione «Lista di controllo dell'area» con la `checklist` del profilo: «migrazioni reversibili e dati esistenti; con PostgreSQL anche RLS sulle tabelle nuove e indici delle policy e delle chiavi esterne». Il brief porta anche i must-have M1 e M2, lo scope, le gravità e il blocco JSON del verdetto con `sha` e `code`.
- **Voce `specialists` del DoD.** Nell'uscita di `finish check` la voce «Specialisti finali passati» è `[dopo la revisione]` (riga 36 dello stream) e dopo il ciclo diventa `[sì]` (riga 236); nessuna voce `[no]`.
- **Rilievi.** Due rilievi: `f-1-1` (moderate, confidenza 0,8): piano e spec dicono «nessun indice su `note_id`» e usano `auth.uid()`, mentre la migrazione ha l'indice e `(select auth.uid())`, come chiede la lista di controllo dell'area: il codice è giusto, sono i documenti a essere indietro; il verificatore l'ha **confermato**. `f-1-2` (minor, confidenza 0,4): manca un indice su `notes.user_id`; il verificatore l'ha **scartato** (riguarda la migrazione di `notes`, che il lavoro non tocca). Nessun rilievo `blocker` o `major`.
- Token (`registro-1/stats.json`): `final-reviewer` 54.762, `final-database` 38.646, `finding-verifier` 23.792.

## Precaricamento delle skill

Le regole arrivano agli agenti con il campo `skills: [rules-base, rules-database]`. `registro-1/trascrizioni.txt` elenca i titoli trovati nelle trascrizioni dei subagenti (lette dal controller, solo nelle cartelle della prova). I numeri di sessione sono quelli di quel file: 1-5 sono `passo1` ... `passo5`, 6 è `passo6`, 7 è `libero-1`, 8 è `libero-2`.

- Sessione 5 (`passo5`): implementatore e revisore del task 1, entrambi con `# Regole di base (versione 1)` e `# Regole database (versione 1)` come messaggi `isMeta: sì`.
- Sessione 6 (`passo6`): `final-database` con i due titoli `isMeta: sì`; `final-reviewer` e `finding-verifier` solo con `# Regole di base (versione 1)`.
- Sessione 8 (`libero-2`): i quattro agenti (due implementatori, due revisori) con i due titoli `isMeta: sì`.
- Sessione 3 (`passo3`): i quattro avversari del piano, «nessun titolo» di regole nelle trascrizioni.
- Per ogni titolo compare anche una riga `isMeta: no`. `trascrizioni.txt` dà solo i titoli: la lettura che sia la richiesta già composta è un'ipotesi non provata da queste evidenze; la prova è quella delle righe `isMeta: sì`.
- `registro-1/precarico.txt` dice «indizio» e non «prova» (15 righe con `R-BASE-` nelle uscite): le trascrizioni dei subagenti non stanno nello stream, e vale quanto sopra.

**Le regole viste dal vivo.**

- **`(select auth.uid())` messo dall'implementatore (R-DATABASE-09).** La spec e il piano non lo chiedevano, e la migrazione d'esempio (`notes`) usa `auth.uid()`. Nella migrazione di `tags` la policy ha `(select auth.uid())`. Un limite al segnale: l'implementatore ha anche letto la pagina di Supabase sulla sicurezza per riga (`registro-1/lookups.txt`, n. 7) e la sua nota di ricerca (`research-1.md`) cita la forma con `select` come «chiede la documentazione». Quindi la regola precaricata e la pagina letta convergono, e non si può dire quale delle due abbia deciso.
- **`reviewer-database` che blocca per R-DATABASE-10 contro spec e piano.** L'implementatore ha seguito la spec («nessun indice»); il revisore, con le regole precaricate, ha dato `changes` con un rilievo `major` su R-DATABASE-10 (manca l'indice sulla chiave esterna `note_id`), che dice il contrario di spec e piano. È il segno più netto del profilo: il revisore applica la regola, e non il piano. Il risultato è stato lo scontro che ha portato alla scelta dell'utente.
- **Ciò che è entrato dalla spec per un rilievo non conta come segnale.** Il divieto di modificare la migrazione esistente (R-DATABASE-03), la policy di lettura su `tags` (R-DATABASE-07) e la forma della lettura sono entrati nella spec perché un avversario li ha chiesti: non provano il precaricamento.
- **Lo specialista in revisione finale** ha riconosciuto che il codice (indice, `(select auth.uid())`) segue la lista di controllo dell'area, e che è la spec a dover essere allineata.

## Difetti trovati

1. **`verify` non contato nel progetto di prova (prima esecuzione).** In `passo6` della prima esecuzione, `finish check` era rosso: il `verify` del progetto di prova usciva 0 senza rapporto (`uncounted`) e in L2 i test dei must-have non risultavano contati. Il progetto di prova aveva copiato il `verify` di B6 (L1); le prove L2 di P3c e P3b avevano `tools/unittest_junit.py` e `report = "junit:reports/junit.xml"`. È un difetto del piano di prova e del Task 7, non del prodotto. Corretto nel Task 7 (giro 1: `tools/unittest_junit.py`, `report` in `tollgate.toml`, file del progetto di prova, spec di prova, test). Nella seconda esecuzione le ricevute sono `green` con il numero dei test (`registro-1/events.jsonl`: `tests_run` 2, 2, 3, 3).
2. **Giro di correzione tra due sessioni (seconda esecuzione, `libero-1`).** Quando un task tocca un giro di correzione dopo che la sessione che ha lanciato l'implementatore è finita, il prodotto lo chiedeva «da riprendere» (`resume`) con `SendMessage`, che non lo raggiunge, e negava un implementatore nuovo (hook `writer`). Corretto nel prodotto con `2d1441c` («giro di correzione in una sessione nuova (implementatore non raggiungibile)»): nell'hook `tollgate_checks/agents.py` un `Agent` del tipo del task e con il nome dell'implementatore è ammesso anche quando il task aspetta «resume», se l'ultimo subagente è stato lanciato da un'altra sessione (o non c'è); il lancio nuovo prende il posto della ripresa; nella stessa sessione la ripresa resta obbligatoria. Nessuna operazione nuova né tipo di evento nuovo. Suite verde: 4061 test su `python3.11` e `python3.13`, 5 test nuovi rossi prima del codice; revisione: approvato, nessun critical o important, 4 minor rinviati. L'utente ha scelto «Correggi ora in B7». **`libero-2` mostra la correzione funzionante dal vivo.**
3. **Tre file copiati a metà prova.** La copia del plugin della prova (`/tmp/tollgate-b1/plugin`) non è stata ricreata con `prepara`: il controller ha copiato i tre file cambiati da `2d1441c` (`bin/tollgate_checks/agents.py`, `bin/tollgate_hooks/apply.py` e `skills/execute/SKILL.md`) e ha controllato con `cmp` che fossero uguali al commit. Gli sha256 (ridotti ai primi 16 caratteri): `2b9fb1dafe99b889`, `7e1e60b4165b6602`, `0d542c84cdb18b62`. Dopo la copia la prova è ripresa con `libero-2` dal task 1 fermo.

## La prima esecuzione

La prima esecuzione non è nelle evidenze del repo (le copie grezze stanno fuori dal repo; non avevano passato `test_committed_evidence_has_no_long_web_results` durante il giro del Task 7). Cosa si sa dal registro del controller:

- passi 1-5 riusciti;
- al passo 5 il task 1 era stato fatto e approvato, ma la migrazione si scostava dal piano (colonna `name` al posto di `text`, `user_id` e `created_at` in più, policy su `user_id` invece che sulla nota collegata); il revisore aveva approvato con `findings: []` senza confrontare le colonne con il piano. La sessione principale se n'è accorta e ha chiesto all'utente, che ha scelto «chiudi e vai avanti»: il task 1 si chiude così com'è e la revisione finale con lo specialista deve trovare lo scostamento;
- al passo 6 `finish check` era rosso per il `verify` non contato (difetto 1);
- l'utente ha chiesto se pagava qualcosa (nessun addebito: i dollari sono equivalenti API e usano la quota dell'abbonamento) e poi ha scelto «Rifai da capo»: la prova è ripartita da `prepara` con il progetto corretto.

Costo equivalente della prima esecuzione: 0,86 + 0,17 + 0,52 + 0,17 + 0,60 + 0,65 (`libero-1`) + 0,19 (`passo6`), circa 3,16 USD.

## Costi

I costi vengono dai messaggi `result` degli stream (`total_cost_usd`): sono **equivalenti API**, non addebiti. Non c'era nessuna `ANTHROPIC_API_KEY`: la prova usa la quota dell'abbonamento e non si è speso denaro.

| Esecuzione | Costo equivalente |
|---|---|
| prima (fuori dalle evidenze) | circa 3,16 USD |
| seconda (nelle evidenze) | 4,53 USD (0,94 + 0,18 + 0,77 + 0,17 + 0,66 + 0,28 + 0,91 + 0,62) |
| totale | circa 7,69 USD |

Token dei subagenti nella seconda esecuzione (`registro-1/stats.json`, totale 620.986): `spec-adversary` 125.329, `plan-adversary` 100.767, `implementer-database` 167.540, `reviewer-database` 110.150, `final-reviewer` 54.762, `final-database` 38.646, `finding-verifier` 23.792. Giri di correzione: 1. Veti: 1 (regola `writer`, in `libero-1`). Blocchi: 0. Deroghe: 0. Ore di fase: 5,24 h in `execution` (ci sono le soste tra una fermata e l'altra), 0,07 h in `spec_audit`, 0,05 h in `plan`.

## Comandi del modello

`registro-1/comandi-modello.txt` elenca i comandi del modello (sessione principale e subagenti) e il totale degli strumenti. Letti a mano: comandi `tollgate` (`start`, `audit prepare`, `act apply`, `status`, `status --checkpoint`, `research submit`, `task start`, `task start --fix`, `task review-prepare`, `task done`, `finish check`, `review prepare`, `finish open-pr`), `git` (elenco dei file, log, stato, `add`, `commit`, `diff`), `cat`, `ls`, `grep` e uno script `python3` di modifica della spec, e `python3 -m unittest discover` per i test. Nessun `supabase`, `psql`, `postgres`, `pg_ctl`, `pg_dump`, `prisma`, `drizzle-kit`, `docker`, `node`, `npm`, `npx`, `deno`, `wrangler`, `vercel`, `gh`, `curl`, `wget` o `git push`.

- `registro-1/comandi-rischiosi.txt` è **vuoto**.
- **Falsi positivi di percorso (D9).** La parola «supabase» compare in 14 righe di `comandi-modello.txt`, tutte come parte di un percorso di file del progetto di prova (`supabase/migrations/…`, `supabase/functions/notes/index.ts`, `supabase/config.toml`) in `ls`, `cat`, `git add`, `git diff … -- supabase tests` e in un `grep` di un subagente; e come testo dentro le note di ricerca e nella modifica della spec. Nessuna è il programma `supabase`.
- In `libero-2` il modello ha lanciato, per ritrovare il file del brief, un `find` su tutto il filesystem (`find / -newer … -type f`), che non è un programma vietato ma ha elencato anche file fuori dalla prova (tra cui un percorso di un altro progetto dell'utente: nelle evidenze quel percorso è stato sostituito, vedi «Anonimizzazione»). È un limite dell'ambiente di prova, non del prodotto.

Strumenti del modello (totale, di cui da subagenti): `Agent` 19 (0), `Bash` 58 (13), `Edit` 7 (4), `EnterWorktree` 1 (0), `Glob` 21 (21), `Grep` 4 (4), `ListAgents` 1 (0), `Read` 88 (87), `SendMessage` 1 (0), `Skill` 4 (0), `ToolSearch` 2 (0), `WebFetch` 3 (3), `Write` 5 (2).

Letture registrate (`registro-1/lookups.txt`): 15 `read` e 3 `fetch` degli implementatori; i `Grep` degli implementatori non sono registrati (B1-V6; `grep-non-registrati.txt`).

## Risultati di WebFetch e pagine di terzi

- I tre `WebFetch` della seconda esecuzione sono stati fatti dagli implementatori: la pagina di Supabase sulla sicurezza per riga e la pagina di PostgreSQL su `CREATE POLICY` (`passo5`, 1.723 e 2.879 caratteri), e la pagina di riferimento di Supabase sulla `select` (`libero-2`, 656 caratteri).
- Tutti e tre sono **sotto i 5000 caratteri**: `flowreg.py togli-pagine` toglie solo quelli lunghi, quindi li ha letti il controller uno per uno (la descrizione è nel registro del controller). Poi, perché due contengono codice o sintassi copiati da pagine di terzi e il repo è pubblico, il controller li ha sostituiti con il segnaposto di `togli-pagine` («pagina di terzi tolta dalle evidenze», con indirizzo e lunghezza). **Nelle evidenze non resta nessun risultato di `WebFetch`**, e `test_committed_evidence_has_no_long_web_results` è verde.
- **Le richieste delle pagine di Supabase.** Una delle pagine conteneva una richiesta agli agenti di mandare un rapporto a Supabase. È un testo di terzi: non si esegue mai. Il modello di `passo5`, nel riassunto che dà della pagina, dice di averla ignorata; il controller ha controllato a mano che nessuna richiesta fosse seguita (nessun rapporto mandato, nessuna pagina di feedback aperta). Il testo della pagina non è nelle evidenze.
- Per ogni flusso `togli-pagine` ha anche sostituito 3 uscite di hook di terzi dei `SessionStart` (1.129, 3.604 e 10.170 caratteri), 24 in tutto; poi le righe stesse sono state tolte (vedi «Anonimizzazione»).

## Scostamenti dall'atteso

- **La fermata di `passo5`.** `passo5` doveva portare il task 1 alla fine; si è fermato per la regola contro la spec (voluto dalla prova: un conflitto vero) e ha chiesto all'utente. Questo ha richiesto il modo `libero`, previsto per il giro di correzione dopo la revisione finale ma usato qui per portare una scelta dell'utente a metà del passo.
- **Il difetto del prodotto** (sopra) ha interrotto `libero-1` e aggiunto la correzione `2d1441c` fuori dai task di B7, come lavoro del Task 8.
- **La spec approvata dice «nessun indice»**, contro R-DATABASE-10 [blocca]. Non era in programma: è la sessione che ha scelto la seconda correzione proposta dall'avversario. La prova ha misurato un conflitto spec-regola invece del caso pulito; per questo l'esito è raccontato come composito.
- **Il revisore del task 1 della prima esecuzione ha approvato** uno scostamento di schema dal piano senza confrontare le colonne. Nella seconda esecuzione lo scostamento non si è ripetuto (migrazione come il piano); la prova non dice perché.

## Limiti

- **Un lavoro piccolo (L2).** Due task, una sola fetta. La prova mostra il percorso completo (spec, piano, esecuzione, revisione finale, PR) con il profilo; non è un lavoro grande.
- **Il test di testo non esegue SQL.** I test leggono le migrazioni e la edge function come testo con la libreria standard. Un test di testo su una migrazione non prova che la migrazione giri su PostgreSQL, né che il `select` annidato di Supabase restituisca i tag. Nessun database, nessuna CLI di Supabase, nessun `.sql` o `.ts` eseguito; il modulo `sqlite3` non sostituisce PostgreSQL.
- **Le difese che `--disallowedTools` non chiude** (`registro-1/limiti.txt`): i divieti sono a prefisso e non chiudono `env VAR=… <programma>`, `sudo`, `xargs`, `bash -c '…'`; per `git`/`gh` restano aperti `git -C x push …`, `git push --force-with-lease`, `git remote set-url` seguito da un push, `env gh`. `Write` ed `Edit` nudi valgono per qualsiasi percorso. La difesa vera è l'hook `effects` di tollgate più un progetto di prova senza credenziali.
- **I limiti della grep di `registra`:** un `(yarn)` nudo, un comando dopo un backtick e i falsi positivi su `echo` non sono coperti; per i percorsi con `supabase` vale D9 (vedi sopra).
- **`--allowedTools`** concede gli strumenti senza domande: in una sessione interattiva `WebFetch` chiede un permesso per dominio, che qui non è rappresentato.
- **Altri plugin attivi.** La prova gira con gli altri plugin dell'utente attivi nella sessione.
- **La copia del plugin aggiornata a metà con tre file** (difetto 3): il comportamento di `libero-2` è quello del commit `2d1441c`, e quello di `passo1`-`passo5` e `libero-1` è quello precedente; nessun altro file è stato toccato.
- **Le scelte dell'utente a metà** (una nella prima esecuzione, una nella seconda, più la scelta di rifare e quella di correggere il prodotto) cambiano il flusso rispetto a una prova di corsa: il tempo `execution` di 5,24 ore include le fermate.
- **Il precaricamento ha un segnale mescolato** (`(select auth.uid())` e la pagina letta) e un segnale netto (il revisore che blocca per R-DATABASE-10); la prova del precaricamento viene da trascrizioni lette a mano dal controller, non dallo script.
- Gli orari degli eventi sono UTC; quelli di `esito.txt` sono locali.

## Anonimizzazione delle evidenze

Prima del commit, su tutti i file di `evidenze/b7/flusso/`:

- **Sessioni.** Gli otto id di sessione sono diventati `SESSIONE-1` ... `SESSIONE-8`, uno per flusso, con la stessa numerazione di `registro-1/trascrizioni.txt` (`passo1` ... `passo6` = 1-6, `libero-1` = 7, `libero-2` = 8): 2.607 occorrenze, anche in `events.jsonl`, in `eventi-ricerca.jsonl` e nei percorsi delle cartelle di lavoro dei subagenti. Gli `agent_id` restano: non sono segreti.
- **Utente e percorsi.** Il percorso del checkout del repo (con il nome utente) è diventato relativo al repo (24 occorrenze, in `comandi-modello.txt`, `togli-pagine.txt` e in un risultato di `find`); il percorso della cartella dell'utente è diventato `/home/USER` (5 occorrenze); il nome utente è diventato `USER` (27 occorrenze, compreso il campo `actor` degli atti); il percorso di un altro progetto dell'utente, comparso nel risultato del `find` di `libero-2`, è diventato `/home/USER/PROGETTO-PRIVATO/…` (2 occorrenze).
- **Host.** Il nome della macchina è diventato `HOST` (106 occorrenze, nel campo `host` degli eventi e in `eventi-ricerca.jsonl`).
- **Righe tolte dagli stream-json.** Il messaggio `init` (elenco dei plugin, dei server MCP, delle skill e degli agenti della macchina, percorsi di memoria e del socket): 1 riga per flusso, 8 in tutto. Le righe `hook_started` e `hook_response` dei `SessionStart` degli altri plugin: 82 righe in tutto (10 in ciascun flusso, 12 in `passo1`, dove tollgate non aveva ancora un lavoro attivo e quindi non resta nessuna riga `SessionStart`). Resta in ogni altro flusso la coppia dell'hook di tollgate («lavoro #1 (L2), fase …»). Il JSON resta valido riga per riga.
- Restano, perché non identificano l'utente: gli id degli hook, dei messaggi e dei blocchi, gli id degli agenti, i nomi `superpowers:…` usati dal modello, le firme dei blocchi di ragionamento, gli SHA dei commit della prova, il numero di utente di sistema nel percorso `/tmp/claude-1000/…`, e le righe vuote o `{}` degli hook `PreToolUse` e `PostToolUse`.

Controllo (comandi con `grep -rIE` sulla cartella `evidenze/b7/flusso/` e su questo rapporto, valori cercati non riportati; esito zero in tutti i casi tranne l'ultima riga):

| Cercato | Dove | Occorrenze |
|---|---|---|
| nome utente (ricavato a runtime) | `docs/verifiche/evidenze/b7/` e questo rapporto | 0 |
| nome dell'host (ricavato a runtime) | `docs/verifiche/evidenze/b7/` e questo rapporto | 0 |
| `/home/` seguito da qualcosa di diverso da `USER` | `docs/verifiche/evidenze/b7/` | 0 |
| i nomi delle cartelle dei progetti privati dell'utente, ricavati a runtime e mai scritti | `docs/verifiche/evidenze/b7/` e questo rapporto | 0 |
| i prefissi di token di API e di GitHub (`sk-ant`, `ghp_`, `github_pat_`, `gho_`) e le forme di JWT | `docs/verifiche/evidenze/b7/` e questo rapporto | 0 |
| cartelle dei plugin dell'utente (`.claude/plugins`) e percorso del socket (`/run/user`) | `docs/verifiche/evidenze/b7/` | 0 |
| gli id di sessione reali (ogni valore di `session_id` degli stream e di `session` degli eventi è `SESSIONE-n` o assente) | `docs/verifiche/evidenze/b7/` e questo rapporto | 0 |
| stringhe lunghe da 60 caratteri in su | `docs/verifiche/evidenze/b7/` | solo firme dei blocchi di ragionamento, percorsi di cartelle di lavoro e della prova, SHA di commit, id di test e righe di separazione |
