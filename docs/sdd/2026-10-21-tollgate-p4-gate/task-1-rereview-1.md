### Verdetti sui rilievi

**I-1 — guardia non a lista di ammessi (`guard_args` / `check_gh_log`)**: NON INDIRIZZATO per intero (parte indirizzata).
- Indirizzato: una sola fonte, `spikes/gh-p4/ghguard.py` (`violation`), usata da `guard_args` (`run-p4-checks.sh:28-30`) e `check_gh_log` (`:649-650`). `gh api`: ogni opzione che inizia con `-` fuori da `--include|--paginate|--silent|--jq|-q` è rifiutata (`ghguard.py`, ramo `api`), quindi `--method=POST`, `-XPOST`, `-fk=v`, `--field=`, `--input=`, `--hostname` cadono. Endpoint: nome intero del repo (`.git`, `#` rifiutati), `..`, `//`, `%2e`, `%2f` rifiutati (provato a mano: `repos/<r>/%2E%2e/x` fermato). Elenco chiuso dei sottocomandi di `pr|issue|run` (`run delete|cancel|rerun`, `pr review|ready`, `issue delete|transfer` fermati). `repo create`: solo `--public|--private` (una) e `--add-readme`. Prova negativa a 45 casi in `check_negativi` (`:654-683`).
- Dati veri: ho rieseguito `violation()` sui 146 comandi `gh` di `comandi.log` (parse con shlex, funzione importata, nessuna rete): 144 ammessi; i 2 rifiutati sono le righe con l'annotazione «(controller...)» (già dichiarata dall'implementatore). Quindi la guardia non rifiuta nulla di ciò che lo script usa. Nota: `ghguard.py log` non si può usare su `comandi.log` (formato diverso: data + `gh ...`, non separato da tab), serve solo al registro del gh finto.
- Ancora aperto: per `pr|issue|run` le opzioni e gli argomenti posizionali NON sono un elenco chiuso; si controlla solo il sottocomando e che `--repo`/`-R`/`--repo=` valga uno dei due repo. Provati, tutti AMMESSI da `violation`:
  - `pr view https://github.com/other/x/pull/1 --repo ginz0ls/tollgate-p4-protected` e `pr view other/x#1 --repo ...`: gh risolve il repo dall'URL o da `owner/repo#n` e non da `--repo`, quindi la regola «nessun comando su altri repo» si aggira;
  - `pr list --repo <ok> -Rother/x`: l'opzione attaccata `-Rvalore` non è vista da `_repo_flag` (`ghguard.py:_repo_flag` riconosce solo `-R` separato e `--repo=`), con due `-R` gh usa l'ultimo;
  - `pr comment 1 --repo <ok> --body-file /etc/passwd` e `run download 1 --repo <ok> -D /etc`: opzioni libere (lettura di file locali e scrittura fuori dalla cartella delle uscite);
  - `api repos/<r>/issues?x=1/../../`: il controllo dei segmenti usa solo la parte prima del `?`; inoffensivo per il server (query), ma incoerente con la regola dichiarata.
  È esattamente il difetto indicato nel rilievo («nessun elenco... ammessi per coppia»), solo spostato da `api` a `pr|issue|run`. Per chiuderlo: per ogni coppia un elenco di opzioni ammesse (con e senza valore, come già fatto per `api`), rifiuto di ogni argomento `-X` non in elenco (compreso `-R<valore>` attaccato) e degli argomenti posizionali che non siano un numero o un nome di ramo senza `/` né `:`/`#`/`http`; aggiungere alla prova negativa almeno URL di altro repo, `-Rother/x`, `--body-file`, `-D`.

**I-2 — SHA di pulizia scambiati nel rapporto**: INDIRIZZATO. `docs/verifiche/2026-10-21-p4-verifiche.md:21` ora ha `pulisci-protected.txt` = `a0c1e5f`, `pulisci-detect.txt` = `349020d`, coerente con le evidenze (riletti i due file sopra).

**Verifica del commit `02f9637` (`__pycache__`)**: a HEAD `git ls-tree -r HEAD --name-only | grep pycache` dà 0 risultati; in `spikes/gh-p4/` ci sono solo `ghguard.py`, `run-p4-checks.sh`, `workflows`. Il commit intermedio `48b624b` lo conteneva, rimosso con commit nuovo (nessun amend): corretto.

### Danni nuovi nel diff della correzione
- Minor: `ghguard.py log` e il formato di `comandi.log` non coincidono (vedi sopra); la «sanità sui dati veri» dichiarata nel report è quindi stata fatta con un parsing ad hoc non versionato. Nessun effetto sul funzionamento.
- Minor: la nuova guardia è più restrittiva della decisione 25 per `gh api` (nessun `POST statuses` né `PUT|DELETE branches/main/protection` ammessi, ora né in `guard_args` né nel log). Lo script non li usa (144/146 passano), quindi oggi non danneggia; se il Task 1 o un successivo ne avesse bisogno andrebbero aggiunti come coppie esplicite con endpoint fisso.
- Nessun Critical/Important nuovo.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti: I-1 (parziale). Chiuso `api` e `repo`, ma `pr|issue|run` ammettono ancora opzioni e posizionali liberi: aggirabile con URL/`owner/repo#n` di altro repo e con `-Rvalore` attaccato. I-2 e `__pycache__` risolti.
