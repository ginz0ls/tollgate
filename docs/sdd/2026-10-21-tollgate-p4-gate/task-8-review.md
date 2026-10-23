# Revisione Task 8: `gate guard` (4250bcf..60a4cf6)

### Aderenza

- ✅ `guard.check` (`bin/tollgate_gate/guard.py:35-58`): file di tollgate confrontati con la punta del predefinito (`evaluate.tollgate_files_in_work` su `git.changes(base_tip, head=...)`, che include `old_path`, quindi cancellazioni e spostamenti); eccezione `tollgate-config/*` solo con `not cross_repo`, con file di tollgate più `.tollgate/waivers/**`; workflow del progetto non cancellati e non di tollgate passati a `workflows.problems`, file illeggibile = rosso (fail-closed).
- ✅ Sicurezza `pull_request_target`: il codice della PR non viene mai eseguito. La testa si scarica con `git.fetch_ref(repo, "refs/pull/<n>/head", token=GH_TOKEN)` (`guard.py:101`), il token passa solo in `GIT_CONFIG_*` (`bin/tollgate_core/git.py:441-445`) e `test_token_reaches_fetch_only_as_token` lo asserisce. I contenuti si leggono con `git diff --no-ext-diff --no-textconv` e `git show`. `number` è un intero validato (`_number`), lo SHA è `[0-9a-f]{40}`, lo slug è validato: negli argomenti di `gh` entrano solo questi. Corpo, titolo e nome del ramo non arrivano mai a `gh` né a `git` (il nome del ramo è confrontato solo in Python). Commenti con `-F body=@file`, stati con `--input`.
- ✅ Dry-run: i problemi si stampano con `json.dumps` (nessun `::` interpretabile dal runner); nel commento passano da `render_guard` (`_lines` → `prbody.neutralize`, già coperto da `test_gate_comment`).
- ✅ N-3: PR non verso il predefinito → nessuno stato, solo il commento «non applicabile» (`guard.py:86-92`); `test_not_default_base_writes_no_status` e `test_other_base_on_shared_sha_does_not_overwrite_guard`. `len(shared) > 1` → `error` (`guard.py:105-110`).
- ✅ Decisione 14 (parte di `upsert_comment`): prefisso più autore in `BOT_LOGINS`, `--paginate`, corpo da file; `test_upsert_ignores_user_comment_with_same_prefix`.
- ✅ `cli.py`: `allow_abbrev=False`, `_require_actions` condiviso con `base-ids` (comportamento invariato), D21c ereditata da `main`; testati `--pub/--publ/--ev` (exit 2), rifiuto senza `GITHUB_ACTIONS=true`, evento malformato senza traceback.
- ✅ `ghcli.api(file_fields=...)`: aggiunto in coda ai fields, nessun uso esistente cambia (`test_ghcli` aggiornato). Modifiche a `fakegh.py` compatibili (`_ISSUE_REST.match(argv[-1])` è equivalente per le chiamate precedenti; `_ok` stampa lo stesso JSON).
- ✅ Scelte dichiarate: uscita 0 con `--publish` e guard rosso (il segnale è lo stato; un'eccezione dà 1 e nessuno stato, quindi la protezione blocca per stato assente) e `repo` facoltativo (comodo, innocuo; `cli.cmd_guard` non lo usa).
- ✅ Carry rev-t7 (`setup` `uncounted`): test aggiunto in `test_gate_evaluate.py`, passa senza toccare `evaluate`.
- ❌ Ruling D7 (`carry.md:59`, V5b): `github.shared_sha_prs` non filtra `head.sha == sha` (vedi I-1).
- ⚠️ Non verificabili dal diff: il formato reale di `gh api --paginate --jq` con i jq di `statuses`/`pr_comments`/`prs_for_commit` (il fake non valuta il jq); il comportamento reale di `-F body=@file` con `PATCH issues/comments/<id>` (coperto in V1/V3 per il resto, non per questa chiamata).

### Punti di forza

- Strato pulito: `github.py` parla solo attraverso `ghcli`, validazione di slug, SHA e numeri prima di entrare in un percorso; descrizione dello stato ridotta a una riga di al più 140 caratteri.
- Test d'integrazione veri: il `git fetch` gira contro un remoto nudo locale (`push_pr_head`), non un mock, e `test_publish_uses_files_not_args` guarda gli argv reali registrati dal `gh` finto. Test del processo vero (`CliTest`) per `--publish`, abbreviazioni e dry-run.
- `fakegh` estende lo stato in modo coerente con V1 (REST `github-actions[bot]`, GraphQL `github-actions`).
- Ordine «commento poi stato» ragionato e dichiarato.

### Rilievi

**Important**

- **I-1** `bin/tollgate_gate/github.py:166-176` (`shared_sha_prs`), usata da `guard.py:104`. Filtra solo `state == "open"` e `base.ref`, non `head.sha == sha`. La V5b (verificata nel Task 1, `docs/verifiche/2026-10-21-p4-verifiche.md:39`) dice che `commits/<testa di A>/pulls` elenca anche la PR B impilata su A, con `head.sha` diverso. Con due PR impilate verso il predefinito (caso normale con tollgate: slice che partono dal ramo della slice precedente) la PR A riceve `error` «SHA condiviso da più PR» pur avendo una testa propria, e non si sblocca finché B esiste. La docstring stessa dice «che hanno `sha` come testa». Il carry assegna D7 al Task 9, ma la funzione nasce qui e `guard` la usa già: oggi è sbagliata. Correzione: aggiungere `(pr.get("head") or {}).get("sha") == sha` al filtro (`prs_for_commit` già restituisce `head.sha`), e un test `test_stacked_pr_does_not_make_sha_shared` con due PR aperte verso `main`, una con `head.sha` diverso, che dà `success`; il Task 9 la riusa.
- **I-2** `bin/tollgate_gate/comment.py:127` (`_guard_build`, P3) usato da `guard.py:123`. Il commento rosso si intitola «tollgate: **in attesa** sullo SHA» (e la spec 9.2 dice «lo stato in attesa»), ma `guard` pubblica `failure`. L'utente legge «in attesa» su un controllo fallito. O si pubblica `pending` (come dice la spec), oppure si aggiorna il titolo e la docstring di `render_guard` («quando lo stato resta in attesa») e la riga 833 della spec nella rev 25. Va deciso dal controller; il test `test_red_publishes_failure_and_comment` fissa oggi `failure` e il titolo non è asserito. (Se la decisione è `failure`, il titolo è un difetto del Task 8 di coerenza fra comando e testo.)

**Minor**

- **M-1** `guard.py:96-130`: nessun ricontrollo che la testa sia ancora quella dell'evento prima di scrivere il commento (la decisione 14 lo chiede per il commento di `verdict`; `upsert_comment` non riceve lo SHA e non può farlo). Se la PR avanza in fast-forward fra evento e fetch, `resolve_ref(pr.head_sha)` riesce comunque (lo SHA vecchio è antenato), e un guard in ritardo può sovrascrivere il commento di quello nuovo con la versione dello SHA vecchio. Lo stato resta corretto (è per SHA); il rischio è il solo commento e dipende dal gruppo `concurrency` del workflow (Task 11). Da coprire nel workflow o confrontando `FETCH_HEAD` con `pr.head_sha`.
- **M-2** `guard.py:117-120`: un guard verde non aggiorna un commento rosso precedente: dopo la correzione resta «in attesa sullo SHA <vecchio>» accanto a uno stato verde. Il marcatore porta lo SHA, quindi non è ingannevole, ma una riga «ora in regola» con `upsert_comment` solo se il commento esiste sarebbe più chiara. Decisione 14 dice «solo se rosso», quindi è una scelta del controller.
- **M-3** `guard.py:17`: `WAIVERS = [".tollgate/waivers/**"]` duplica il letterale di `protected.REPO_PROTECTED` (`bin/tollgate_analysis/protected.py:11`) e di `waivers.path_for`. Meglio una costante in `protected.py` (per esempio `WAIVER_FILES`) usata da entrambi.
- **M-4** `guard.py:105-110`: con SHA condiviso si scrive `error` ma non si tocca un eventuale commento rosso precedente; innocuo, solo da sapere.
- **M-5** `github.py:131-137` (`create_issue`): il titolo è un argomento `-f title=...`; va bene con `SENTINEL_TITLE`, ma la firma accetta qualunque testo. Basta una frase nella docstring (c'è: «il titolo lo scrive tollgate») o togliere il parametro e usare la costante.
- **M-6** Lacune nei test: nessun test di un file di tollgate **spostato** (il nome `test_tollgate_file_deleted_or_moved_is_red` copre solo la cancellazione, `guard.py` gestisce `old_path` grazie a `evaluate`); nessun test di un nome di file ostile (backtick, `::`) nell'uscita dry-run e nel commento di `guard`; nessun test di un `edited` che cambia la base da `main` a `other` dopo un guard verde.
- **M-7** `bin/tollgate_core/ghcli.py:121-123`: la docstring ora ha una riga oltre i 100 caratteri («testo non fidato non entra mai negli argomenti. `paginate` vuole `jq` (G5…»); da riandare a capo come il resto del file.

### Valutazione

**Qualità del task:** Da correggere

**Motivo:** La struttura, la sicurezza di `pull_request_target` (nessun testo della PR negli argomenti, token solo in `GIT_CONFIG_*`, nessuna esecuzione del codice della PR) e la copertura dei test sono solide; ma `shared_sha_prs` ignora il ruling D7 e fa dare `error` alle PR impilate (I-1), e il titolo del commento rosso («in attesa») contraddice lo stato `failure` pubblicato (I-2).
