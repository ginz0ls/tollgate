# Task 11 — giro di correzione 1

Leggi W/task-11-review.md e il ruling «Task 11 giro 1» in W/progress.md. Correggi, ogni volta prima il test RED.

## C-1 (Critical): nessun job che esegue codice del progetto ha un token che scrive
- Dividi `gate/workflows/tollgate-base.yml` in due job.
  - **`ids`**: `permissions: {contents: read}` a livello di job, nessun `GH_TOKEN` nell'ambiente. Fa il checkout del predefinito su `$GITHUB_SHA` con `persist-credentials: false`, poi `actions/cache/restore`. Solo sul miss lancia `gate base-ids` senza `--publish` e salva la cache. Carica sempre come artefatto (`upload-artifact`) `ids.json` e ciò che serve a pubblicare, cioè l'esito dei comandi.
  - **`publish`**: `needs: ids`, `if: always()`, `permissions: {contents: read, statuses: write, issues: write}`. Fa solo il checkout del predefinito con `persist-credentials: false` e `download-artifact` sotto `${{ runner.temp }}` con `continue-on-error: true`. Poi lancia `gate base-publish --ids <dir> --event "$GITHUB_EVENT_PATH" --publish` con `env: GH_TOKEN`. Non esegue `setup`, comandi del progetto né script del repo che non siano la CLI fidata `.github/tollgate/bin`.
- Nuovo sottocomando `tollgate gate base-publish --ids <dir> --event <file> [--publish]` in `bin/tollgate_gate/cli.py` e `baseids.py`.
  - Pubblica `tollgate/base`, e in `detect` il commento sull'issue, dai dati dell'artefatto, con lo stesso codice di pubblicazione di oggi.
  - Il contenuto dell'artefatto è non fidato: lettura fail-closed, come `baseids.load`, con controllo che `sha` coincida con `$GITHUB_SHA` dell'evento. Artefatto mancante o non valido → stato `error` con motivo.
  - Eredita `allow_abbrev=False`, il rifiuto di `--publish` senza `GITHUB_ACTIONS=true` e D21c.
  - Togli `--publish` da `base-ids`, oppure lascialo senza usi nei workflow; preferisci toglierlo, e aggiorna i test del Task 10 che lo usavano. Il guardrail di `cli_calls` su `--publish` deve continuare a valere anche per `base-publish`.
- Test:
  - in `tollgate-base` il job che esegue `base-ids` non ha permessi di scrittura né `GH_TOKEN`;
  - nessun job, in nessun workflow, esegue comandi del progetto (`gate run`, `gate base-ids`) avendo un permesso `write` o `GH_TOKEN`;
  - `base-publish`: dati validi → stato; artefatto mancante, SHA diverso o JSON ostile → `error`; cache hit → pubblicato lo stesso.

## I-1 (Important): servizi dove gira la suite
- `install.files` inserisce i servizi in ogni job che esegue comandi del progetto: `head` e `base` di `tollgate-run`, `ids` di `tollgate-base`. Usa la forma con le porte del Task 12: leggi cosa ha fatto in `install.py` e `init.py` e generalizzala, senza duplicare il codice. Test.

## Minori
- **M-1** `fullmatch` nelle regex di `install.py`. Test con `"main\n"`.
- **M-2** Valori nello YAML tra virgolette singole; l'immagine non può finire con `:`. Test con ramo `true`, `123` e immagine `postgres:`: rifiutati o scritti come stringhe.
- **M-3** Test: ogni riga con `${{` sta in un blocco `with:`, `env:` o `concurrency:`, oppure è una chiave `if:`.
- **M-5** Test: `tollgate-verdict` non ha `if:` sulla conclusione, né `if:` a livello di job.
- **M-6** Test: gli argomenti delle righe `run:` che lanciano `tollgate gate …`, con le variabili sostituite da valori fittizi, passano dal parser di `tollgate_gate.cli`.
- **M-7** `test_token_only_in_env` vede anche `secrets.GITHUB_TOKEN`.
- **M-8** Un commento in `tollgate-base.yml`: dopo un push forzato che toglie `$GITHUB_SHA` dal ramo il job può fallire senza stato, e la sentinella copre il caso.

Ogni workflow deve continuare a passare da `workflows.problems` con i soli problemi attesi. Il workspace W è ignorato di proposito: niente `git add -f`, niente commit dei report. Lancia `tests/run` in primo piano con timeout lungo e aspetta che finisca. Se va oltre il timeout, aspetta in primo piano sul file di uscita con un ciclo `until`: non restare fermo in attesa di notifiche. Deve essere verde su python3.11 e python3, poi committa con «(Task 11, fix round 1)» e Co-Authored-By. Aggiungi in fondo a W/task-11-report.md la sezione «Fix round 1».

## Vincolo dal Task 12 (aggiunto dal controller)
`bin/tollgate_gate/protection.py` ha `BASE_JOB = "tollgate-base"`: `protect.sh` legge `app.id` dal check-run con quel nome esatto, e il nome del check-run è il nome del job (V6). Dopo la divisione, il job **`publish`** deve avere come nome esatto `tollgate-base`, con la chiave del job `tollgate-base` oppure `name: tollgate-base`. Il job `ids` deve avere un nome diverso. Un test lega `protection.BASE_JOB` al nome del job di pubblicazione in `tollgate-base.yml`. Il Task 12 ha anche aggiunto a `install.files` il parametro `ports`, con la forma `--service NOME=IMMAGINE,PORTA`: generalizza quello per I-1.
