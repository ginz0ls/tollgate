# Task 17: rapporto dell'implementatore

Stato: DONE_WITH_CONCERNS (dubbi in fondo).

## Step 1: test dal programma vero (`tests/test_criteria_p4.py`)

Base comune `ProgramCase(test_gate_github.VerdictBase)`: ogni caso ha il suo `GateLab` (`fresh`),
la testa spinta in `refs/pull/1/head`, gli artefatti di `tollgate-run` e le risposte del `gh`
finto; poi `bin/tollgate gate evaluate|guard|sentinel … --publish` come processo
(`python3 -B`, `cwd` nel repo, `GITHUB_ACTIONS=true` e `TOLLGATE_GH` dall'ambiente di
`VerdictBase`, `HOME` temporanea). Le asserzioni sono lo stato pubblicato (`tollgate/verdict`,
`tollgate/attention`, `tollgate/guard`, `tollgate/sentinel`) e un testo della voce attesa nel
commento.

- `Criterion10Test.test_criterion_10_matrix`: 25 sottoprove (`case_01`…`case_25`), una per riga
  del criterio 10 non già coperta da `bin/tollgate` (`tollgate.toml` → `guard` rosso lo copre
  già `test_gate_guard.CliTest.test_end_to_end_publish_in_actions`; il token personale in
  `protected` solo GitHub, rapporto del Task 16). Verdi: pulita (anche `guard`),
  `tollgate-config/*` e ramo a mano con `attenzione` rosso. `verdict` rosso: test tolto, skip,
  fuori scope, identificativo della base mancante, `|| true` con un test fallito nel JUnit,
  livello sotto il minimo (etichetta `security`), report L2 mancante. Deroghe: file di
  un'altra issue (rosso) e controprova nel proprio file (verde, `waiver_scope` informativa).
  Sentinel: push diretto e merge di un `verdict` rosso in `detect` (stato `failure` e issue).
  `guard` rosso: `tollgate-verdict.yml` su `tg/*` e i cinque workflow del progetto
  (`statuses: write`, `checks: write`, `pull_request_target`, `workflow_run`, senza
  `permissions`). Verde con `attenzione`: workflow modificato con deroga `ci`. `attenzione`
  rosso: deroga `test`, piano cambiato (con il diff nel commento), tetto, `allow_no_tests` con
  zero test (`empty`). `error`: `../` in `results.json`, XML con entità, SHA superato. Non
  applicabile: nessuno stato e solo il commento `<!-- tollgate-na`.
- `GroupsTest.test_criterion_44_groups_end_to_end`: sola deroga `scope` → `attention`
  `success` con «nessuna voce da leggere» e «Informative (1)»; con la deroga `test` →
  `failure`, la deroga `test` è la prima riga di «Da leggere», prima di `<details>`.
- `ComponentsInGateTest.test_criterion_35_gate`: `spec_audit = false`, tre fette, `lens: off`
  → `verdict` `success`, `attention` `failure` con `audit_off` e `components_off`.
- `ComponentsInGateTest.test_components_in_gate` (criterio 18): `definition_of_done` acceso
  (DoD dichiarata falsa → rosso) e spento (verde con `components_off`); `base_test_ids`
  acceso senza identificativi (`error`) e spento (verde, nessuna cache né artefatto);
  `sentinel` spento (nessuna chiamata a `gh`, nessuna issue).

Nessun criterio è risultato senza codice: tutti i test sono passati al primo giro dopo aver
corretto tre attese sbagliate del test stesso (un `report: null` diventa `uncounted`, non
`empty`; il testo del commento «non applicabile» comincia con la maiuscola; un JUnit senza
`test_zero` faceva mancare un must-have). Non c'è quindi un RED del TDD su codice di
prodotto: sono test di criteri su codice già scritto. Una prova di mutazione non l'ho fatta.
Costo: la sottoprova del push diretto attende 10 s (`sentinel` rilegge `commits/<sha>/pulls`
tre volte a 5 s: dal processo le attese non si iniettano); il modulo dura circa 43 s.

## Docstring di `openpr.py` (carry del controller)

`bin/tollgate_flow/openpr.py:5` e la docstring di `_publish` dicono ora la PATCH REST
(`gh.pr_edit`) al posto di `pr edit`, con la nota su gh 2.46. Nessun cambio di codice.

## Step 3: revisione 25 della spec

Sezioni toccate: intestazione, 1.2 (sette limiti nuovi: identificativi della base da un run
della PR e cache avvelenabile M-9; codice unito in `tollgate-base`, `tollgate/base`
falsificabile e `ACTIONS_RUNTIME_TOKEN`; artefatti con collegamenti seguiti, V8; azioni a
`@v4`; workflow già presenti; approvazioni e `locked_docs` nei guardrail locali; `--publish`
solo in Actions; PR da fork), 3 (`gate/workflows/`, strati di `tollgate_gate`, moduli estratti),
3.1 (sottocomandi `gate` con le opzioni reali, `init --propose|--update` con le opzioni,
`TOLLGATE_GH_RETRY_DELAYS`), 5 (approvazione corrente prima, decisione 22(a)), 6.4 (`finish
check` sul calcolo del gate, decisione 20; PATCH REST al posto di `gh pr edit`), 8.3 (nessuna
deroga senza issue valida; percorso di una violazione `base_ids` con i segmenti maiuscoli
tolti), 8.7 (`check_l2_detail`, mancanti e superati, componenti contro intestazioni, report
legati allo sha approvato, `approvals` locale più severa), 9.1 (tabella riscritta sulla forma
reale dei workflow: tipi con `edited`, job `head`/`base`, `tollgate-base` in due job con
permessi distinti, `verdict` che non salva mai in cache, `guard` rosso = `failure` con il
commento che spiega perché, `tollgate/base` non pubblicato in `protected`; regole comuni,
ritentativi di `gh api`, controlli preliminari, nessuno stato per le PR verso altri rami,
ingressi, identificativi della base per comando, artefatti e formati), 9.2 (righe dei comandi,
dell'issue senza `Closes`, dello scope con `plan_changed`, delle approvazioni, delle voci di
`attenzione`, nuova riga di rilievi e DoD dichiarati; `guard` e `workflows.problems`;
`profile:<p>:<c>`; componenti; gruppi della decisione 7 con i conflitti risolti; `UNSTABLE`;
commento della decisione 14), 9.3 (`sentinel` con `creator.login`, push forzato, riletture,
issue paginate; `protection.read`), 9.4 (`tollgate-config/*` dello stesso repo,
`FINGERPRINT`), 9.5 (una suite della base per merge, minuti misurati), 9.6 (servizi in ogni
job che esegue comandi del progetto, Actions spente), 11.2 (`init`, `classify`, `protect.sh`,
stima, `--update`), 12.4 (m-2 e il limite m-3), 13 (righe nuove), 15 (criterio 10 «non
applicabile» riletto), 16 (tabella P4 con V1-V9 e le due prove, G3 e G4 aggiornati, «ancora
da verificare»), 18.1 (campi `blocking`, `tasks_over`, `skills_absent`; marcatore con lo SHA),
18.2, 18.4 (`size_reason`, evento `skills_absent`), 20 (riga 25). Le righe di tabella
aggiunte hanno tutte il numero di colonne giusto (una barra in `downgraded:blocker\|major`
scappata).

## Step 2 e 4: piano principale

Stato (P4 chiuso sul ramo, merge in attesa dell'OK dell'utente, 2457 test, revisione finale
come passo successivo, repo pubblico da cancellare), sezione 2 (riga P4), sezione 3 (pacchetti
con i moduli reali, regola degli strati, contratto P4 → P3 chiuso, tre righe P4 → P5: moduli e
interfacce, vincoli e rinvii a P5 compresi i rinviati di P3c della decisione 24, minori
rinviati del registro), sezione 4 (tabella «Prove dei criteri di P4» con 74 riferimenti, tutti
verificati con un controllo AST; le note «(P4)» delle tabelle di P2, P3a, P3b e P3c annotate
come chiuse; riga 6.4 e rischio 2). I 334 riferimenti `file::Classe.metodo` del piano
esistono tutti.

## Verifica

- `tests/run`: Python 3.11.16, 2457 test, OK (793 s); Python 3.13.5, 2457 test, OK (729 s).
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: 2457 test, OK
  (867 s); nessun «unclosed database» né `ResourceWarning` nell'uscita.
- Nessun `__pycache__` nel commit; righe entro 100 caratteri nei file toccati (una riga oltre
  in `openpr.py:225` è preesistente).

## Commit

- `17e8cc7` prove dei criteri dal programma vero e docstring di `openpr.py`.
- `463cc84` spec rev 25.
- `f981c97` piano principale.

## Dubbi

1. La sottoprova del push diretto costa 10 s di attesa reale per ciascuna delle due versioni
   di Python: per toglierla servirebbe una variabile di test per le attese di `sentinel` (come
   `TOLLGATE_GH_RETRY_DELAYS`), cioè codice di prodotto in più; non l'ho aggiunta.
2. La riga «Minori rinviati» del piano principale è lunga e raggruppa per tipo i minori del
   ledger: è fedele alle righe «minor (deferred)», ma la revisione finale potrebbe preferirla
   divisa in punti.
3. Il registro dell'esecuzione è in `.superpowers/sdd/…` (ignorato da git): il piano principale
   lo cita lì; se il controller lo sposta in `docs/sdd/` come per P3c, la riga «Stato» va
   aggiornata.
4. Nella rev 25 ho scritto i fatti dal codice reale dove la decisione del piano e il codice
   divergono (per esempio `tollgate-base` in due job, `base-publish`, l'opzione `--service
   NOME=IMMAGINE[,PORTA]`, `verdict` senza scrittura in cache): la spec ora descrive il codice,
   non le decisioni originali.
