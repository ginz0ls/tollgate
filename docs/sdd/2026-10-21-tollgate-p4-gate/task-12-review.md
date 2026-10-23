# Revisione Task 12 (commit 5475e54, base 89acde5)

Controlli fatti oltre alla lettura del diff: il filtro jq di `protect.sh` provato con il `jq` locale su un JSON di prova (nome e slug esatti, scarta l'altra app: stampa `completed<TAB>success<TAB>15368`); `install.files` provato con un nome di servizio con a capo finale. Nessun test della suite rilanciato, nessuna rete.

### Aderenza

- ✅ `classify`: 200 protected, 403 «Upgrade…» detect, 404 «Branch not protected» protected_unset, il resto (403 amministrazione, `None`) undetermined (`protection.py:763-772`). Criterio 34 rispettato: `propose` rifiuta con `undetermined` e non scrive nulla (`init.py:486-493`).
- ✅ `missing` (`protection.py:794-818`): PR, i due controlli con `app_id` intero positivo (`-1`, `None`, bool scartati), `strict`, `enforce_admins`, push forzato, cancellazione. `protection_body` rifiuta `-1`, 0, non interi.
- ✅ `protect.sh` (`init.py:289-344`): valori quotati (`_quote`), ramo già validato da `protection.read` con `_BRANCH` prima di arrivare al generatore, SHA validato con `^[0-9a-f]{40}$`, check-run per nome esatto e `app.slug`, solo `completed`, un solo `app.id`, `^[1-9][0-9]*$` prima del `sed`, mai `-1`. Il filtro jq è sintatticamente corretto sul jq vero.
- ✅ `init` non scrive su GitHub (solo GET; test `test_no_write_call_to_github`); scrive solo in `docs/superpowers/tollgate-init/`.
- ✅ `--update` propone solo i file diversi dalla punta del predefinito e il ramo `tollgate-config/<versione>` (`init.py:510-518`, `541`).
- ✅ `start`: `_check_gate_runs` (`start.py:604-627`) solo avvisi; in `detect` non legge la protezione; Actions `False` avvisa, `None` nota; presente in avvio e in ripresa.
- ✅ `fakegh.py`: le aggiunte sono rami nuovi (`PUT` protezione, `check-runs`); `api_status` resta prioritario e `POST/PATCH` invariati.
- ✅ Ruling accettati: `NOME=IMMAGINE,PORTA` con `ports: ["P:P"]`; `BASE_JOB = "tollgate-base"`; stima dichiarata nel README.
- ❌ Nomi di servizio: vedi I-1 (la regola `^[a-z0-9-]+$` non è chiusa).
- ❌ Stima dei minuti: vedi I-2 (le ricevute non sono filtrate per repo).

### Punti di forza

- `protect.sh` è costruito con cura: ogni dato letto dall'API passa da un controllo di forma prima di entrare nel corpo, e i test lo provano con un `gh` finto nel `PATH` coprendo app.id duplicati, `-1`, `0` e `"1; rm -rf /"`.
- `read` non lancia mai eccezioni e non deduce `protected` per esclusione.
- `with_mode` cambia una sola riga e il risultato viene rivalidato con `config.load_config_text`.
- La suite ha test per ogni caso del brief, più il rifiuto con e senza rete e la forma di `fakegh` fedele a V2.

### Rilievi

**Important**

- **I-1 `bin/tollgate_flow/init.py:150,207` — `SERVICE_NAME.match` con `$` accetta un a capo finale.** `init._services({"db\n": "x"})` torna `None` (accettato). Poi `install.files` (stessa debolezza: `install.py:19-20,46-48`, che usa `.match` con `$`) produce nel YAML `      db\n:\n        image: postgres:16\n\n        ports:`, cioè un file di workflow rotto con un nome non ammesso. Lo stesso vale per un'immagine con `\n` finale. Il brief chiede esplicitamente «niente iniezione YAML né shell»; i test (`tests/test_init.py:239-241,249`) provano solo a capo in mezzo (`x\ny`), mai in fondo. Correzione: `fullmatch` in `init.py` (e sulla stessa regola in `install.py`, che il giro di correzione del Task 11 già tocca con M-1: coordinare per non avere due regole divergenti, meglio che `init` riusi la funzione di `install` invece di duplicare la regex). Aggiungere ai due test `"db\n=x"` e `{"db\n": "x"}`, `{"db": "x\n"}`.
- **I-2 `bin/tollgate_flow/init.py:224-251` — `_gate_seconds` legge le ricevute di tutti i repo.** La query non filtra per `work_items.repo_key` (`receipts.work` è la FK, `db.py:59`; il DB di stato è unico per l'utente, non per repo). Con più progetti e un comando chiamato `verify` (il nome del modello `templates/tollgate.toml`), la stima dei minuti usa la durata di un altro repo e la presenta come «misurata». Il test (`tests/test_init.py:264-268`) inserisce le ricevute con `work=None`, quindi non vede il problema. Correzione: `JOIN work_items w ON w.id = receipts.work WHERE w.repo_key = ?` con `repo_key` dell'origin; test con una ricevuta di un altro repo che non conta. Le ricevute con `work` nullo (se esistono davvero) non contano, e va detto nel README oppure nel docstring.

**Minor**

- `init.py:516-518` — `--update` con file tutti uguali risponde «nulla da aggiornare» e non dice nulla sulla protezione mancante o incompleta (`read.kind == protected_unset` o `read.missing`), che nel flusso `--propose` produce `protect.sh`. Basta una riga in uscita che rimandi a `--propose` per `protect.sh`.
- `init.py:153-200` — `with_mode` non gestisce `mode = 'detect'` con apici singoli (aggiunge una seconda chiave, il TOML diventa non valido e si rifiuta: fail-closed, ma il messaggio non spiega) né una riga `["x"]` dentro un array su più righe (letta come sezione). Casi rari, già coperti dalla rivalidazione.
- `init.py:412-417` — nomi di file e testo dei problemi dei workflow esistenti entrano nel `README.md` e nell'uscita senza recinto né neutralizzazione (regola del testo non fidato, `global-constraints.md`). Il rischio è basso (file già sul predefinito), ma il percorso con backtick o a capo può rompere il markdown del README che l'utente segue. Si può usare `prbody.neutralize` o scartare i percorsi con caratteri di controllo.
- `templates/tollgate.toml:7-8` + `init.py:361-436` — il modello nasce con `setup` e `verify` vuoti e il README non dice di compilarli (solo i commenti nel file). Aggiungere un passo «compila `[commands]` in `tollgate.toml`» quando il file viene dal modello.
- `init.py:235-239` — la stima conta anche ricevute rosse (`state` non filtrato): un `finish` fallito a metà ha una durata troncata. Filtrare per `state = 'green'` oppure dichiararlo.
- `tests/fakegh.py:935` — riga di 154 caratteri nel docstring (la regola di lunghezza del repo è 100/141, vedi il minore del Task 9).

### Valutazione

**Qualità del task:** Da correggere

**Motivo:** La parte di protezione, `protect.sh` e `start` è solida e verificata (anche con il jq vero). Restano due Important: la regola dei nomi di servizio lascia passare un a capo finale fino al workflow generato (I-1), e la stima dei minuti pesca ricevute di altri repo (I-2).
