# Revisione Task 11 — i cinque workflow e l'installazione (32264ae..89acde5)

Revisore: opus. Letti: cautele, regole del revisore, brief, carry del Task 11, review focus 6-7, vincoli globali, decisioni 5/12/16/17, spec 9.1-9.6, ruling finale di `progress.md`, report, diff. Controlli mirati fuori dal diff (ognuno legato a un rischio):
- `bin/tollgate_gate/cli.py:30-56`. Rischio: flag dei `run:` inesistenti. Esito: `--event`, `--out`, `--sha`, `--root`, `--artifacts`, `--base-ids-cache`, `--base-ids-artifact` e `--publish` esistono tutti.
- `bin/tollgate_core/runner.py:86-110`, `bin/tollgate_core/config.py:31` e `bin/tollgate_gate/baseids.py:20-37`. Rischio: codice del progetto eseguito con il token di scrittura. Esito: vedi C-1.
- Prova locale: un figlio lanciato da Python con `env` ripulito legge `GH_TOKEN` del padre da `/proc/$PPID/environ` (stesso uid). Comando: `SECRET_X=visibile python3 -B -c '… subprocess.run(["/bin/sh","-c","tr … < /proc/$PPID/environ | grep SECRET_X"], env={"PATH": …})'`, che stampa `SECRET_X=visibile`.
- `install.files` con valori al limite (`python3 -B`, sola lettura). Nota: il working tree ha `install.py` modificato e non committato da un altro task (porte dei servizi). Le regex che ho provato sono identiche a quelle di 89acde5.

### Aderenza

- ✅ Nomi dei file uguali a `prereq.GATE_FILES` e `name:` uguale al nome del file (D18b). `workflow_run.workflows: [tollgate-run]` (`tollgate-verdict.yml:302-304`).
- ✅ Permessi di ogni workflow esattamente quelli di 9.1 (`tollgate-guard.yml:164-167`, `tollgate-run.yml:195-196`, `tollgate-verdict.yml:307-312`, `tollgate-base.yml:113-116`, `tollgate-sentinel.yml:276-280`).
- ✅ Eventi e tipi come da brief. `tollgate-run` senza `paths` né `branches`, `concurrency` per numero di PR con `cancel-in-progress` (`tollgate-run.yml:197-199`).
- ✅ Nessuna `${{ }}` in una riga `run:`. I valori del payload passano da `env:` (`HEAD_SHA`, `MERGE_BASE`, `DEFAULT_BRANCH`) e sono sempre quotati in shell (`tollgate-run.yml:239-242,259`, `tollgate-verdict.yml:345-351`).
- ✅ Guard, verdict e sentinel fanno un solo checkout, del predefinito, con `persist-credentials: false` e `fetch-depth: 0` (D2, rev-t10 per sentinel). Nessuno contiene `github.event.pull_request`, e la CLI eseguita è sempre quella del predefinito.
- ✅ `tollgate-verdict` non ha `if:` sulla conclusione, né sul job né sui passi principali. I download hanno `continue-on-error: true`, `run-id`, `github-token` e un `path:` sotto `runner.temp`.
- ✅ V4: `tollgate-verdict` non salva mai in cache e non usa `--head-ids-out`. V4b: `tollgate-base` salva solo su miss (`tollgate-base.yml:145-149`). rev-t10: `base-ids --publish` gira anche sul cache hit.
- ✅ D8: il job `base` di `tollgate-run` usa il checkout `trusted` (CLI), la sottocartella `base` (`merge-base`) e `--root "$GITHUB_WORKSPACE/base"`, con `working-directory: trusted`.
- ✅ D2/V3b: il token sta in `GH_TOKEN` o nel `GIT_CONFIG_*` esportato dentro la shell del passo, mai negli argomenti (`tollgate-verdict.yml:345-349`).
- ✅ Cache poisoning da `pull_request` verso un job privilegiato: non possibile. Le cache scritte da un job `pull_request` hanno lo scope `refs/pull/N/merge`. `tollgate-verdict` (`workflow_run`, contesto del predefinito) e `tollgate-base` (push sul predefinito) ripristinano solo dallo scope del predefinito, che scrive solo `tollgate-base`. Artefatti e cache vanno sotto `runner.temp`, mai sul workspace né su `.github/tollgate/bin`.
- ✅ `install.files`: niente `__pycache__` né `.pyc`, `FINGERPRINT` stabile e calcolato sugli stessi file copiati (`install.py:45-59,99-100`), `VERSION` uguale a `tollgate_core.VERSION`, servizi solo nel job `head`.
- ❌ «Nessun workflow con un permesso `write` esegue codice del progetto»: `tollgate-base` lo fa (C-1).
- ⚠️ Servizi: la spec (9.6) e il brief li mettono solo nel job `head`, ma la suite della base gira anche nel job `base` di `tollgate-run` e in `tollgate-base`, che restano senza (I-1). Il report lo segnala solo in parte (dubbio 3, porte).
- ⚠️ Dubbio 4 del report («il fetch per SHA fallisce per le teste da fork»): non si verifica senza GitHub. Con ogni probabilità il fetch riesce, perché GitHub serve gli oggetti raggiungibili da `refs/pull/N/head`. In entrambi i casi il comportamento è sicuro (vedi sotto).

**Dubbio 4 (passo `key` di verdict con `git fetch` autenticato): sicuro e necessario.**
- Necessario: il checkout fidato non ha gli oggetti della testa, e la chiave della cache (albero di `merge-base`) va calcolata prima di `evaluate` e in un job fidato (decisione 12). Il payload non contiene `merge-base`.
- Sicuro: il fetch scrive solo oggetti nel database del checkout del predefinito e non tocca il working tree da cui gira la CLI. Hook e configurazione restano quelli del checkout fidato. Il token va solo a `https://github.com/` in un header, non negli argomenti. `HEAD_SHA` viene da GitHub ed è quotato. Un fallimento lascia `tree` vuoto e salta il ripristino (fail-safe), e `baseids.load` scarta comunque un `ids.json` di un altro albero.
- Unico difetto: duplica in shell la costruzione dell'header di `git.fetch_ref` (M-4).

**Dubbio 3 (terzo checkout `head` nel job `base`): solo dati, accettabile.** Sul checkout `head` girano solo `git merge-base` e `git rev-parse`. Un working tree estratto non può portare configurazione, hook o filtri git attivi. Anche nel caso peggiore il job ha `contents: read`, nessun segreto e niente `GH_TOKEN`. `merge-base` è per costruzione un commit del predefinito, quindi la PR non sceglie un albero arbitrario. Costa un secondo clone completo: accettabile.

### Punti di forza
- La superficie è progettata bene. La CLI viene sempre dal predefinito, i dati della PR sono solo letti, e i valori del payload passano sempre da `env:` e sono quotati.
- I nomi dei job sono pensati per V6 (`tollgate-base` come nome esatto del check-run).
- `test_pr_code_only_in_run_workflow` è un buon test negativo: vieta `github.event.pull_request` nei workflow privilegiati. `test_downloads_under_runner_temp` conta i passi (`seen == 5`), quindi non passa a vuoto.
- `install.files` valida ramo e servizi prima di scriverli nello YAML e rifiuta un `tollgate-run.yml` senza segnaposto. `fingerprint` codifica lunghezza e percorso, quindi la concatenazione è senza ambiguità.
- Il ruling sui tre problemi attesi di `workflows.problems` è applicato con precisione: si scarta solo quella regex, e `tollgate-run` deve dare `[]` anche con i servizi.

### Rilievi

#### Critical

**C-1 — `tollgate-base` esegue la suite del progetto in un job con `statuses: write` e `issues: write`** (`gate/workflows/tollgate-base.yml:113-116,135-144`; imposto in parte dalla spec 9.1, che dà i permessi per workflow).

Cosa succede: il passo `gate base-ids … --publish` esegue `setup` e comandi `gate` sul checkout di `$GITHUB_SHA` (`baseids.compute` → `run_commands`). Lo fa nello stesso job e nello stesso processo che ha `GH_TOKEN` in `env:`. `runner.clean_env` toglie `GH_TOKEN` dall'ambiente del figlio, ma non basta:
1. Il figlio ha lo stesso uid del padre e legge `GH_TOKEN` da `/proc/$PPID/environ`: l'ho provato, vedi sopra.
2. Sui runner ospitati il codice del job ha `sudo` e può leggere la memoria di `Runner.Worker`, che tiene il `GITHUB_TOKEN` del job. È la tecnica dell'attacco a tj-actions/changed-files: togliere `GH_TOKEN` dall'ambiente non chiude questa strada.

Il token scrive stati come `github-actions[bot]` con l'`app_id` di Actions su qualunque SHA del repo, e scrive, modifica e chiude issue. Scenari concreti:
- **`detect` (e push forzati in `protected`)**: un merge non verificato è proprio il caso che `tollgate-sentinel` deve segnalare. Il codice di quel merge gira in `tollgate-base` in parallelo alla sentinella. Può aspettare che la sentinella finisca e poi: riscrivere `tollgate/sentinel` `success` sul proprio commit (gli stati sono per contesto e vince l'ultimo); chiudere o modificare l'issue «tollgate: merge non verificato», o cancellarne il commento. La garanzia di rilevazione salta.
- **Ogni modalità**: una PR verificata (il gate controlla test e scope, non le intenzioni) può contenere un aiuto di test che, sul predefinito, scrive `tollgate/guard` e `tollgate/verdict` `success` come `github-actions[bot]` sulla testa di un'altra PR dell'agente. Quella PR soddisfa la protezione, e anche `sentinel`, che si fida di `creator.login == github-actions[bot]`, senza essere mai valutata.

È esattamente ciò che 9.2 vieta ai workflow del progetto («nessuno dichiara `statuses: write` … così un workflow aggiunto in una PR non può pubblicare stati falsi»). `tollgate-base` lo reintroduce con un workflow di tollgate. Nessun test lo vede: `test_privileged_checkout_is_default_branch` (`tests/test_gate_workflows.py:533-537`) codifica come accettabile il secondo checkout `${{ github.sha }}` nel workflow con permessi di scrittura.

Correzione (serve un ruling del controller, perché tocca la CLI del Task 10):
- `tollgate-base` diventa due job. (1) Job `ids` con `permissions: {contents: read}` e senza `GH_TOKEN`: ripristina la cache, lancia `gate base-ids` senza `--publish`, salva la cache su miss e carica `ids.json` come artefatto. (2) Job `publish` con `needs: ids`, `permissions: {contents: read, statuses: write, issues: write}`, checkout del solo predefinito: scarica l'artefatto sotto `runner.temp` e pubblica da quel file, senza eseguire codice del progetto.
- Serve un modo di pubblicare da un `ids.json` già calcolato (per esempio `gate base-ids --publish --from <ids.json>`, oppure un sottocomando). È la stessa opzione che chiude il minor rinviato «`tollgate-base` ricalcola la suite anche sul cache hit»: con il cache hit il job `publish` pubblica dalla cache.
- La spec 9.1 resta vera se si legge «permessi» come il massimo del workflow. La rev 25 (Task 17) dovrebbe dire che il job che esegue la suite ha sola lettura.
- Il test deve pretendere che nessun job con un permesso `write` contenga un passo `gate base-ids` o `gate run`, né un checkout diverso dal predefinito.

#### Important

**I-1 — I servizi mancano dove gira la suite della base, e senza `ports:` non sono raggiungibili** (`bin/tollgate_gate/install.py:62-81`, `gate/workflows/tollgate-run.yml:217-264`, `gate/workflows/tollgate-base.yml`; imposto dal piano: brief «servizi inseriti nel job `head`», spec 9.6).
- `runner.ids_commands` esegue gli stessi comandi `gate` nel job `base` di `tollgate-run` e in `tollgate-base`, ma il blocco `services:` entra solo nel job `head`.
- In un progetto che ha bisogno di un database la suite della base fallisce sempre. I comandi sono `red` e senza identificativi, quindi la famiglia `base_ids` non protegge nulla. In `detect`, `tollgate/base` è rosso a ogni push e l'issue di sentinella riceve un commento a ogni merge.
- In più, un job che gira sull'host raggiunge un container di servizio solo con `ports:` mappate (dubbio 3 del report). Vedo nel working tree che il Task 12 sta aggiungendo le porte, ma solo al job `head`.
- Correzione: lo stesso blocco `services:` in tutti i job che eseguono la suite (job `base` di `tollgate-run` e, dopo C-1, il job `ids` di `tollgate-base`), con un segnaposto per job. Un test pretende blocchi identici. La rev 25 corregge 9.6.

#### Minor

- **M-1** `install.py:40-42,65-67,89`: `re.match` con `$` accetta un `\n` finale. `default_branch="main\n"` e `image="postgres:16\n"` passano e lasciano una riga vuota nello YAML: innocuo, ma la validazione non è quella dichiarata. Correzione: `fullmatch` o `\Z`, e un caso `"main\n"` in `test_default_branch_placeholder_replaced`.
- **M-2** `install.py:40-42,69,74`: i valori finiscono nello YAML senza virgolette, e la regex accetta nomi che YAML non legge come stringhe. Ramo `true`, `null`, `on`, `123`: in `branches:` diventano booleano, nullo o numero. Immagine `postgres:` (due punti finali): YAML non valido. Provati, tutti accettati. Non c'è iniezione di chiavi, perché spazi, `#`, `{`, `$` e `'` sono esclusi, ma il file può risultare rotto o scorretto. Correzione: scrivere i valori tra virgolette singole (la regex esclude già `'`) e vietare `:` finale nell'immagine.
- **M-3** `tests/test_gate_workflows.py:516-521`: il brief chiede anche «espressioni ammesse solo in `with:`, `if:`, `concurrency:` ed `env:`», ma il test controlla solo i `run:`. Oggi i workflow rispettano la lista, ma il test non la difende. Correzione: ogni riga con `${{` deve stare dentro uno di quei blocchi o essere una chiave `if:`.
- **M-4** `gate/workflows/tollgate-verdict.yml:343-351`: la costruzione dell'header `extraheader` duplica in shell `git.fetch_ref`. In più `evaluate` rifà lo stesso fetch subito dopo. Accettabile, perché la chiave serve prima di `evaluate`, ma due implementazioni dello stesso protocollo divergono facilmente. Correzione possibile: un sottocomando di sola lettura (`gate cache-key --event …`) che riusa `git.fetch_ref` e scrive `tree=` in `$GITHUB_OUTPUT`.
- **M-5** Nessun test dice che `tollgate-verdict` non ha `if:` (requisito esplicito del brief). Una regressione lascerebbe le PR senza stato dopo un run cancellato o fallito. Correzione: nessuna riga `if:` contenente `conclusion` e nessun `if:` a livello di job in `tollgate-verdict`.
- **M-6** Nessun test confronta i flag delle righe `run:` con il parser di `tollgate_gate.cli`. Oggi i flag esistono tutti (verificato), ma un cambio di nome nella CLI romperebbe i workflow solo su GitHub. Correzione: estrarre gli argomenti dai `run:` (sostituendo le variabili con valori fittizi) e passarli a `parse_args`.
- **M-7** `tests/test_gate_workflows.py:609-614`: `test_token_only_in_env` non vede `secrets.GITHUB_TOKEN`. Basta estendere la ricerca.
- **M-8** `gate/workflows/tollgate-base.yml:121-129`: `trusted` è la punta del predefinito al momento del run, non `$GITHUB_SHA`. Dopo un push forzato che toglie `$GITHUB_SHA` dal ramo, `rev-parse "$GITHUB_SHA^{tree}"` fallisce: il job fallisce senza stato `tollgate/base`. La sentinella copre il caso, quindi è solo da documentare.
- **M-9** (nota, nessuna azione) La cache del job `base` di `tollgate-run` ha lo scope della PR, che il codice del job `head` può avvelenare leggendo `ACTIONS_RUNTIME_TOKEN` con `sudo`. L'effetto peggiore è un job `base` che salta il calcolo. Non va oltre il limite dichiarato nella decisione 12 (gli identificativi calcolati da un run della PR vengono da codice della PR).

### Valutazione

**Qualità del task:** Da correggere.

**Motivo:** guard, verdict, sentinel e `tollgate-run` sono costruiti bene e rispettano ogni regola di superficie: checkout del predefinito, niente espressioni nei `run:`, cache e artefatti sotto `runner.temp`, nessun cache poisoning verso i job privilegiati. Ma `tollgate-base` esegue il codice del progetto con un token che scrive stati come `github-actions[bot]` e modifica issue. Così si possono annullare le segnalazioni della sentinella e falsificare `tollgate/verdict` su altre PR (C-1). In più i servizi non arrivano dove gira la suite della base (I-1). Entrambi richiedono un ruling, perché toccano la CLI (Task 10) e la spec (9.1, 9.6).
