# Revisione Task 7 (Step 2-4) — 4474f02..75084c1

### Aderenza
- ✅ D3: `spikes/b3bis/progetto/tollgate.toml:1-7` e `test_progetto_toml_is_valid` (tests/test_b3bis_script.py:77) con `config.load_config_text`.
- ✅ D11: `models-prova.sh:111-118` (`git init -q -b main`, identità `prova`, `commit.gpgsign false`, anche nell'origin).
- ✅ D12: `tempfile.mkdtemp(prefix="tollgate-b3bis-test-", dir="/tmp")` + `addCleanup` (test:44-45).
- ✅ Segnaposto di `ai/models.py` non sono ID di fornitori.
- ✅ Chiavi: il valore non è mai stampato; confronto `[[ "$CORSA_OUT" == *"${!n}"* ]]` (sh:136) con comando interno, tra virgolette (letterale), nessun `set -x`, nessun file; variabile vuota saltata (`chiave_impostata`, sh:56); in errore solo il nome (sh:137). Uscita salvata solo dopo il controllo (sh:167-170).
- ✅ `B3BIS_DIR`: `verifica_dir` (sh:41-49) gira prima di ogni modo e di ogni scrittura; rifiuta `..`, `/` finale, `/tmp/tollgate-b3bis-x`, `-test-` senza nome, relativi. Test su tutti e tre i modi.
- ✅ Sotto le cartelle di test senza `B3BIS_TOLLGATE`: errore (sh:52-54, `controlla` rc=1), test con file segnale.
- ✅ `prova`: `cd "$REPO"`, `TOLLGATE_STATE="$STATE"` con sentinella, rifiuta `TOLLGATE_TEST_CONFIG`; due corse, la prima con `--refresh` (verificato dal segnale).
- ✅ Ambiente dei test: `clean_env` toglie `MODEL_KEY_VARS`, `B3BIS_*`, `TOLLGATE_*`, `GIT_*`; `B3BIS_PY=sys.executable` (CI con un solo interprete); nessun socket, nessun `claude`. Eseguiti: 11 test OK, nessuna cartella lasciata in `/tmp`.
- ✅ Nessun `rm -rf` nello script: solo `mv` in `.prev-*` e `rmdir`. Più prudente del richiesto.
- ✅ Scostamenti dichiarati (variabili non impostate elencate; niente `.rc`; rifiuto se `out/` esiste; 4 test in più) accettabili, nessuno peggiora il requisito.

### Punti di forza
Controllo della directory prima di ogni effetto; niente cancellazioni; fallimento sul lato sicuro; test del file segnale che provano che il finto è girato; test del caso «variabile vuota» come in `api_key`.

### Rilievi
**Critical:** nessuno.

**Important**
1. `models-prova.sh:41-49` (e `mkdir -p`, sh:105): nessun controllo sui link simbolici. Se `B3BIS_DIR` (o `/tmp/tollgate-b3bis`, in una `/tmp` condivisa) è un link, o un suo componente sotto `-test-*/a/b` lo è, `mkdir -p`, `rot`, `cp -R` e `: > state/.tollgate-test` scrivono fuori dalle cartelle ammesse. Il brief del controller nomina esplicitamente i link. Correzione: dopo `verifica_dir`, `[ -L "$DIR" ]` => errore, e (se esiste) `[ "$(cd "$DIR" && pwd -P)" = "$DIR" ]`; per `-test-` ammettere solo un livello (`-test-?*` senza `/`). Aggiungere un test con un link in `/tmp/tollgate-b3bis-test-*/` che punta a una cartella del test, verificando che non vi si scriva.

**Minor**
2. `sh:48-49`: `"$DEFAULT_DIR"-test-?*` ammette anche `/tmp/tollgate-b3bis-test-x/a/b/c` (il `*` del `case` attraversa `/`). Basta un controllo `*/*` sul resto.
3. `sh:105,109`: `mkdir` usa la umask dell'utente; `out/` in `/tmp` può essere leggibile da altri. Usare `umask 077` o `chmod 700 "$DIR"`.
4. `sh:131-139`: una chiave corta/comune (1-2 caratteri) rifiuterebbe un'uscita innocua; lato sicuro, già dichiarato. Se `refresh.txt` è salvata e la seconda corsa è sporca, il primo file resta (sh:168, `rmdir` fallisce): innocuo, ma l'`out/` resta parziale e `prova` poi rifiuta; coerente col messaggio.
5. Test: manca la prova che il caso positivo `/tmp/tollgate-b3bis` sia accettato da `controlla` (non scrive, sarebbe testabile) e che la seconda corsa sporca non lasci la chiave in `out/`.
6. `test:151`: `assertIn("chiave", r.stderr)` è debole; meglio asserire anche il nome `ANTHROPIC_API_KEY` in stderr e l'assenza del valore in tutti i file sotto `$work` (non solo `out/`).
7. ⚠️ Non verificabile: che `models check` della seconda corsa non faccia rete (dipende dal prodotto, prova del controller).

### Valutazione
**Qualità del task:** Da correggere (Important minore).
**Motivo:** requisiti e rischi sulle chiavi ben coperti e test verdi; resta il buco dei link simbolici su `B3BIS_DIR`, richiesto esplicitamente dal controller, corregibile in poche righe con un test.
