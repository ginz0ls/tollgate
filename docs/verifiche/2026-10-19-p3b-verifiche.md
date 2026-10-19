# Esiti delle verifiche P3b

Versioni: gh 2.46.0 (2025-01-13, Debian 2.46.0-3); Claude Code 2.1.304 (`claude --version`, solo annotata). Data: 20 ottobre 2026.

Piano: `docs/superpowers/plans/2026-10-19-tollgate-p3b-chiusura.md` (Task 1). Spec: revisione 22, sezione 16. Uscite grezze in `/tmp/tollgate-p3b/help/` (fuori dal repo). Script: `spikes/run-p3b-experiments.sh`. Nessuna rete: solo `gh --version` e `gh <comando> --help`. Su Claude Code non servono fatti nuovi.

| Id | Voce | Esito | Evidenza | Conseguenza |
|---|---|---|---|---|
| G1 | Segnaposto `{owner}`/`{repo}` di `gh api` presi dal repo della cartella corrente | **sì** (dall'aiuto); non provato con `insteadOf` | `gh api --help`: «placeholder values `{owner}`, `{repo}`, and `{branch}` get populated with values from the repository of the current directory»; esempio `gh api repos/{owner}/{repo}/releases`. Il comportamento con un `origin` riscritto da `insteadOf` verso un repo locale non si può provare senza rete | `gh.py` passa gli endpoint come `repos/{owner}/{repo}/...` dalla cartella del lavoro; la risoluzione su repo locale è coperta solo da `fakegh` |
| G2 | `gh pr create` con `--head`, `--base`, `--title`, `--body-file` | **sì** | `gh pr create --help`: `-H, --head branch`, `-B, --base branch`, `-t, --title string`, `-F, --body-file file` (con `-` per stdin). L'aiuto non dice cosa stampa su stdout né che sia l'URL | `gh.py` usa le quattro opzioni. L'URL non si prende da stdout: il codice rilegge la PR con `pr list --head` (decisione 10). `fakegh` può stampare l'URL ma il codice non deve dipenderne |
| G3 | `gh pr edit <n> --body-file` | **sì** | `gh pr edit --help`: `USAGE gh pr edit [<number> \| <url> \| <branch>] [flags]`; `-F, --body-file file`; anche `-t, --title`, `-B, --base` | `gh.py` aggiorna il corpo con `pr edit <n> --body-file <file>` |
| G4 | `gh pr list --head --state all --json number,state,url,headRefOid,mergedAt`; `gh pr view <n> --json comments` | **in parte**: opzioni sì, nomi dei campi non verificabili dall'aiuto | `gh pr list --help`: `-H, --head string`, `-s, --state string` con `{open\|closed\|merged\|all}` (default `open`), `--json fields`, `-q, --jq`, `-L, --limit int` (default 30), `-S, --search`. `gh pr view --help`: `--json fields`, `-q, --jq`, `-c, --comments`. In 2.46.0 l'aiuto **non ha** la sezione `JSON FIELDS`: `headRefOid` e `mergedAt` non compaiono in nessun testo d'aiuto (grep vuoto), nemmeno `comments` come campo. `--state all` è accettato. Il limite 30 vale anche con `--head` | `gh.py` usa `--state all` e `--limit` esplicito. I nomi dei campi si basano sulla conoscenza di `gh`, non su questa verifica: `fakegh` li riproduce e il primo uso col `gh` vero (revisori finali) è il controllo. Un campo inesistente farebbe fallire `gh` con errore: `gh.py` deve trattare l'uscita non zero come errore del comando, non come «nessuna PR» |
| G5 | `gh api --paginate` con `--jq`: una riga per elemento; `--slurp` | `--paginate` e `--jq` **sì**; formato delle righe **non provato**; `--slurp` **assente** | `gh api --help`: `--paginate` («Make additional HTTP requests to fetch all pages of results»), `-q, --jq string`; il testo spiega solo che le pagine sono richieste in sequenza fino alla fine. Nessuna menzione di `--slurp` (grep vuoto sull'aiuto di `gh api`) | `prs_for_branch_prefix` non usa `--slurp`: con `--paginate --jq '.[] \| ...'` legge l'uscita riga per riga, un oggetto JSON per riga, senza assumere un array unico. `fakegh` stampa una riga JSON per elemento |

Annotazione: `claude --version` → 2.1.304 (Claude Code).

## Conseguenze per il piano P3b

- **G1.** Task 9 (`gh.py`): endpoint con segnaposto, eseguiti dalla cartella del lavoro (cwd = repo). Il `-R` non serve.
- **G2.** L'URL della PR non viene da stdout di `pr create`: dopo la creazione `pr list --head <ramo> --state all --json ...`.
- **G3.** `pr edit <n> --body-file`.
- **G4.** I nomi dei campi JSON sono non verificati su 2.46.0: segnalarlo ai revisori finali. L'uscita non zero è un errore.
- **G5.** Niente `--slurp`: le pagine si leggono come righe JSON separate.

## Come ripetere

`bash spikes/run-p3b-experiments.sh` (nessuna rete). Poi `grep` sui file in `/tmp/tollgate-p3b/help/`.
