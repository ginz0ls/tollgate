# Ri-revisione 2, Task 1 (guardia gh: ghguard.py)

### Verdetti sui rilievi

**I-1 residuo: `pr|issue|run` a elenco chiuso (opzioni, `--repo`/`-R` unico, posizionali, `-D`, `--body-file`, endpoint)**: INDIRIZZATO.
- Elenco chiuso per coppia: `SPECS` (`ghguard.py`, tabella dopo `REPO_OPTS`) e `_parse`: ogni opzione non in elenco è rifiutata (`--body-file`, `-F`, `-b`, `--web`, `--jq`, `--template`, `--hostname`, `--`).
- Un solo repo: `-R`/`--repo`, separati, con `=` o attaccati, devono essere esattamente uno e valere uno dei due repo. Provati e fermati: `--repo` ripetuto (anche con il secondo repo ammesso), `-R` + `--repo`, `-R ""`, `--repo ""`, `-R` senza valore, `-R=...`.
- Posizionali: URL (anche in maiuscole), `owner/repo#n`, ramo che comincia con `-` (via `--head` o dopo `--`) fermati. `--head other:b` fermato.
- `-D`/`--dir`: fermati `/tmp/o/../etc`, `/tmp/ofoo` (prefisso), `/tmp/o` stessa, `/tmp/o/a/` (non normalizzato), `-D=/etc`, `-D /etc`. `-n ../x` fermato.
- `api`: `-H`, `--hostname`, `-X`, `-f` fermati; `?x=1/../../`, `?x=%2E%2e`, `%2F..%2F`, `/..`, endpoint con `/` iniziale, `graphql`, `user` fermati; secondo endpoint fermato.
- Minori: `ghguard.py comandi <comandi.log>` esiste (`check_comandi`), usato da `controlla` (`run-p4-checks.sh:766-767`): 138 comandi veri, 0 violazioni, 9 «(controller...)» escluse con motivo. Commento sulle scritture della decisione 25 nel docstring del modulo.
- Positivi: forme legittime (`-Rrepo` attaccato, `--repo=`, ramo `feature/x-1`, `run download -D <sotto P4_OUT> -n`, `api ... --jq`, `--paginate`, `repo clone <repo> <sotto P4_WORK> -- -q`) passano.
- `bash spikes/gh-p4/run-p4-checks.sh controlla`: «CONTROLLA: ok», uscite attese presenti, nessun `__pycache__` in `spikes/`.

### Danni nuovi nel diff della correzione
Nessun Critical/Important. Minor, tutti innocui:
- `ghguard.py` `BRANCH_RE`, `NAME_RE`, `FIELDS_RE` e il filtro caratteri dell'endpoint finiscono con `$`, che accetta un `\n` finale (provato: `api repos/<r>/issues\n` ammesso). Con `re.fullmatch` il caso sparisce. Nessun effetto pratico (gh codifica l'URL).
- `int` usa `str.isdigit()`, che accetta cifre Unicode (`²`, `١`): gh le rifiuterebbe, quindi non si apre nulla; `isascii() and isdigit()` sarebbe più stretto.
- `pr view other/x --repo <ok>` è ammesso: gh lo tratta come nome di ramo nel repo di `--repo`, non come altro repo, quindi la regola «niente altri repo» regge.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
