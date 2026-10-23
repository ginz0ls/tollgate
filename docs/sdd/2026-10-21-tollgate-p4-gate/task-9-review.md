# Revisione Task 9: `gate evaluate` su GitHub (3df4592..6afc140)

Letti: cautele, regole del revisore, brief, carry-extract (V4, D7, D16, rev-t7, rerev-t8), review-focus, decisioni 4, 5, 12, 13, 14, 16, ultimo ruling di progress.md, report, diff. Controlli mirati sul codice fuori dal diff: `evaluate.py` (usi di `is_tg_branch`/`issue_from_branch`), `comment.py` (render di `errors`), `baseids.load`, `git.fetch_ref/resolve_ref`, `github.py` (upsert, `shared_sha_prs`). Nessun test rilanciato: l'evidenza riportata (2124 verdi su 3.11 e 3.13) è coerente con il diff.

## Aderenza

- ✅ `evaluate.py` resta puro; l'I/O sta in `verdict.py` (`verdict.py:452-638`). La modifica a `evaluate.py` (`is_work`, `issue_no`, `waiver_issue`, `_issue_state`) è minima e coerente con il ruling su fork `tg/*`. Gli altri usi di `issue_from_branch` (`evaluate.py:653`) stanno già dopo `if not ctx.is_work`, quindi nessun altro punto da allineare.
- ✅ V4: nessun `--head-ids-out`, nessuna scrittura in cache. `test_verdict_never_writes_cache` fa lo snapshot dei file nei tre esiti; `test_no_head_ids_option` verifica che l'opzione non esista.
- ✅ Decisione 5: PR verso un altro ramo senza stati `tollgate/*`, solo commento `<!-- tollgate-na` (`verdict.py:546-548,607-609`, `test_not_applicable_writes_no_status`, `test_other_base_next_to_default_base_pr`). SHA condiviso, SHA superato, nessuna PR → `error` sullo SHA, senza commento. Artefatto mancante/non valido, `sha` o `config_sha` diversi, `applicable` falso → `error` con commento.
- ✅ rev-t7: `read_results(meta=...)` riempie `sha` e `config_sha` dalla stessa lettura; confronto con la testa risolta e con `origin/<default>` (`verdict.py:501-513`), con test per entrambi.
- ✅ Decisione 14: ricontrollo via `GET pulls/<n>` subito prima di commento e stati (`verdict.py:586-589`, `test_head_rechecked_just_before_writing`); commento uno per SHA, solo del bot (`BOT_LOGINS`), paginato (`github.py` `upsert_comment`; test su autore diverso e su più di 100 commenti).
- ✅ D7: `shared_sha_prs` riusata; `SharedShaPrsTest` la copre direttamente (stessa testa, impilata, chiusa, altra base, numero ripetuto).
- ✅ D16: `github.issue` restituisce `is_pr`; `_issue_state` dà rosso «#M è una PR, non un'issue»; `waiver_issue` non vale per una PR (`test_closes_a_pr_number_is_red`).
- ✅ Review Focus 7: ordine cache → artefatto → errore, `tree` diverso e collegamento simbolico ignorati, per comando (`test_base_ids_source_order`, `test_artifact_ids_of_another_tree_or_symlink_are_ignored`, `test_ids_are_per_command`).
- ✅ Testo non fidato: corpo PR solo in `PrFacts.body` → `Item.data`; commenti scritti da file (`test_text_goes_through_files_not_arguments`); `ev.errors` passa da `neutralize` in `comment.py`; la descrizione degli stati è generica per gli artefatti (nomi non fidati). Percorsi: gli artefatti li legge `read_results`/`validate` (Task 7), qui nessun percorso seguito fuori dalla cartella.
- ✅ Ruling di progress.md: `tg/*` da fork = PR manuale, prefisso `<!-- tollgate-na`; `fixtask.GATE_MARKER` non lo vede.
- ⚠️ Non verificabile qui: i campi reali di `GET pulls/<n>` per un fork cancellato (`head.repo` nullo) e di `workflow_run.pull_requests` per i fork; il report lo dichiara tra i dubbi.

## Punti di forza

- Il flusso è lineare e leggibile: `prechecks` puro, `inputs_from_github` che trasforma ogni problema di raccolta in motivi (mai eccezioni per git/config/artefatti), `finish` unico per scrivere o stampare.
- Descrizioni di stato scritte da tollgate, con motivo utile per `config_sha` e configurazione non valida.
- Test di buona qualità: banco `GateLab` vero con `gh` finto, casi ostili (entità XML, `../`, percorso assoluto, symlink), due PR sulla stessa testa, avanzamento della testa durante il run.

## Rilievi

### Important

**I-1. Con `--publish` alcuni rami d'errore escono con 1 senza nessuno stato** (`verdict.py:564-621`; il comportamento è fissato da `test_gh_failure_is_a_clean_refusal`, `tests/test_gate_github.py` classe `CliTest`).
Decisione 5 e il brief: ogni ramo d'errore pubblica uno stato esplicito, con `--publish` per ogni esito. Qui un `GhError` da `github.shared_sha_prs` / `github.pull` / `prs_for_commit` (limite di rate, 5xx, una PR sparita), un `ValueError` da `github.pr_from_rest` (`verdict.py:484`, fuori dal `try`, per esempio `head.ref` assente) o un `ValueError`/`OSError` da `evaluate.evaluate` (cattura solo `GitError`, `evaluate.py:876`), come anche il `GhError` del ricontrollo in `finish` (`verdict.py:586`), risalgono a `cli.main` che stampa su stderr e ritorna 1. Non c'è traceback, ma `tollgate/verdict` e `tollgate/attention` restano senza stato. Il merge resta comunque fermo (stato obbligatorio mancante), quindi è fail-closed, ma l'utente vede un job rosso senza motivo sulla PR e il gate non è «esplicito per ogni esito» come la decisione 5 chiede.
Correzione: dopo aver letto `sha` (`verdict.py:578`), avvolgere il corpo di `main` in un `try/except (GhError, GitError, ConfigError, OSError, ValueError)` che, con `publish`, prova a scrivere `error` su `sha` con una descrizione di tollgate (`DESC_ERROR` esiste già e non è usata) e, in ogni caso, stampa il motivo. Il test `test_gh_failure_is_a_clean_refusal` va aggiornato: con `gh` rotto lo stato non si può scrivere, quindi il caso utile da asserire è un errore di lettura (es. `pulls/<n>` assente) con `POST statuses` funzionante, che deve dare `error`.

**I-2. Duplicazione della regola «issue della PR»** (`verdict.py:469-473` ripete `evaluate.py:65-66`).
`_issue_number` riscrive `None if cross_repo else issue_from_branch(...)` `or closes_issue(...)` per scegliere quale file di deroghe leggere. Questo task ha dovuto correggere proprio quella regola in `evaluate.py` per il fork: la prossima modifica la sposterà in un posto solo e `verdict` leggerà le deroghe di un'issue diversa da quella che `evaluate` giudica (con `waiver_issue`, la deroga verrebbe scartata in silenzio). Estrarre una funzione sola (in `evaluate.py` o in `prref`, per esempio `pr_issue_number(pr: PrFacts)`) usata da `Context.issue_no` e da `verdict`.

### Minor

- `verdict.py:607-609`: il commento «non applicabile» si scrive senza il ricontrollo della testa (decisione 14) e anche per una PR che ha già un'altra testa, quindi può riscrivere sul commento un SHA più vecchio. Solo estetico (il testo non cambia), ma coerente sarebbe saltare le PR la cui `head.sha` non è `sha`.
- `verdict.py:600-605,613`: i numeri di `workflow_run.pull_requests` non sono filtrati per `state == "open"`; `next((p ... == sha), here[0])` potrebbe scegliere una PR chiusa con la stessa testa. In pratica GitHub elenca le sole aperte; basta filtrare `pulls` per `state == "open"` per non dipenderne.
- `verdict.py:586`: `github.pull(...)["head"]["sha"]` solleva `KeyError` se la risposta è malformata (vedi I-1); meglio `(... .get("head") or {}).get("sha")`.
- `verdict.py:452-466`: `_base_ids` calcola albero e legge cache/artefatto anche con `base_test_ids = false`; inoffensivo (la famiglia è saltata), ma `path.stat()` (`:463`) può sollevare `OSError` fuori dal `try`.
- `tests/fakegh.py:26`: riga di 141 caratteri nella docstring (il task ha riscritto quel paragrafo senza riandare a capo), contro il limite di 100 del progetto.
- Test mancante: un `tg/*` da fork con corpo senza blocco e `Closes #N` verso un'issue chiusa non è coperto; `test_fork_pr_treated_as_manual` copre solo il caso pulito.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** Il task è completo rispetto a brief, carry e ruling, con test solidi e `evaluate.py` ancora puro. Va corretto I-1, perché con `--publish` gli errori di lettura da GitHub o di forma della PR non producono lo stato esplicito che la decisione 5 richiede, e I-2, perché la regola «issue della PR» ora vive in due posti.
