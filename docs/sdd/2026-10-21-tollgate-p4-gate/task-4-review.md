# Revisione Task 4 (commit cc49a86)

## Aderenza

- ✅ `model.py`: dataclass e firme come da brief; `verdict_state` e `attention_state` corretti (`model.py:88-103`).
- ✅ `attention.py`: `GROUPS` coincide con la decisione 7, più `task_over_max` come `info` (D13). `group` dà `KeyError` per chiavi ignote.
- ✅ D3: `prblock.FIELDS` con `tasks_over` e `skills_absent`, `DEFAULTS` con liste vuote (copiate per chiamata), test di ordine aggiornato. `blocking` passa invariato: `build` non tocca i rilievi.
- ✅ D6: `path` derivato dal `classname`, violazioni raggruppate per `path`, copertura con `waivers.unresolved`/`covers` (tutti gli identificativi: `test_test_waiver_covers_only_with_all_ids`).
- ✅ D13: `test_plan_sha_absent_is_red` e `test_l0_without_plan_over_thresholds_is_red` presenti e con chiavi precise.
- ✅ D17e: `git.object_in_history` con `--find-object` e `_check_ref` su `obj` e `ref`; aggiunto alla tabella di rifiuto di `test_git.py`.
- ✅ D5: `setup` e `*:setup` rossi trattati come comando rosso (ma vedi I-2).
- ✅ Decisione 12 / N-2: `base_ids` confronta solo `ctx.required` (profili attivi dal diff). `test_inactive_profile_ids_not_compared` asserisce entrambi i casi.
- ✅ Strati: `evaluate.py` importa `tollgate_analysis`, `tollgate_core.{git, runner, diffcheck, config}` e `l2tree` (modulo del gate). Niente `db` né `sqlite3`. ⚠️ `l2tree` non è nel diff: ho assunto che sia un modulo già presente di `tollgate_gate` senza import vietati.
- ✅ Testo non fidato: ID dei must-have (`M\d+`) e delle deroghe (`_ID`) sono validati dai parser, quindi sicuri in `text`; percorsi, ID di test, diff e motivi delle deroghe stanno solo in `data`. Eccezione: I-2.
- ✅ Test di tutti i passi 1-4 del brief con chiavi e famiglie precise (`keys(ev.red, "commands") == ["command_red"]`, `[(i.key, i.data)] == [("out_of_scope", "src/extra.py")]`), non solo «c'è una voce rossa».
- ⚠️ `test_testguard_on_every_pr` e `test_out_of_scope_tg_only` verificano le due metà del criterio 10, ma nessun test pone `where="local"` sulla famiglia `diff` (vedi I-1).
- ⚠️ Blocco assente su ramo `tg/*`: `_scope` restituisce `None` senza voce rossa (`evaluate.py:_scope`). Il brief lo assegna al Task 5 (`issue`/`declared`): da non dimenticare lì.

### Controlli mirati sui rischi indicati dal controller

1. **Stato «peggiore tra dichiarato e ricalcolato»** (`evaluate.py:_command_state`). Controllo: `runner.receipt_state` (`runner.py:73-83`). Coerente: la funzione è quella usata in locale, `empty` e `uncounted` hanno rango intermedio, `unverified` esce prima. Due note. Un `CommandResult` dichiarato `green` con `exit=None` diventa `red` (`-1`): corretto per `results.json` (D13 porta sempre `exit`), ma il docstring del modello dice che `exit=None` vale «comando non girato», quindi una ricevuta locale senza uscita sarebbe rossa. Minor M-1.
2. **`commands`/`base_ids` a `None`.** Su GitHub `errors` (due messaggi quando mancano entrambi: accettabile), in locale famiglia saltata; `test_no_results_on_github_is_error_but_not_local` e `test_missing_base_ids_on_github_is_error` li fissano. `base_ids` spento da componente non produce errore con `base_ids=None` (asserito).
3. **Euristica `base_path`** (`evaluate.py:227-236`). Falsi positivi: un modulo il cui ultimo segmento ha l'iniziale maiuscola e non è una classe (`pkg.Models` senza classe, `tests.TestFoo` come file `TestFoo.py`) perde il segmento e diventa `pkg.py`. Effetto: solo il raggruppamento e la copertura da deroga per file (mai verde/rosso); la deroga per pattern resta possibile. Minor M-2.
4. **Famiglia `diff` uguale in locale e su GitHub salvo `plan_change_is_attention`.** Non è così: il valore è fisso `True` (I-1).
5. **Allentamento di `test_facts_keys_match_block_fields`** (`test_openpr.py:751`). `set(data) | set(DEFAULTS) == set(FIELDS)` richiede ancora che ogni altro campo sia prodotto e che non ce ne siano di estranei; ammette però anche `data` che contiene i due campi nuovi, quindi non obbliga il Task 13 a riempirli. È un compromesso accettabile e annotato nel carry (Task 13): Minor M-3.
6. **Asserzioni dei test.** Vedi sopra: chiavi e famiglie precise. Unica eccezione debole: `test_findings_carry_blocking_field` (M-4).

## Punti di forza

- Struttura a `Context` con proprietà `cached_property` e famiglie `(ctx, ev)`: il Task 5 aggiunge funzioni all'elenco senza toccare le esistenti.
- Banco `GateLab` pulito: repo vero con `origin` nudo, nessuna rete né `gh`; i test lavorano su git reale.
- Deroghe: validità legata all'issue (decisione 8) e al ramo della PR, con sei casi in `test_waivers_do_not_apply_without_a_valid_issue`.
- Test del diff del piano con tetto di 200 righe, blob fuori storia (`test_blob_outside_history...`), errore di git → `error` senza traceback.
- TDD dichiarato onestamente (RED verificato con stub dopo).

## Rilievi

### Critical
Nessuno.

### Important

**I-1. `plan_change_is_attention=True` fisso anche in locale.** `evaluate.py:384` (chiamata a `diffcheck.diff_check`) e `evaluate.py:388` (`_plan_changed`). La decisione 9 dice che solo il gate passa `True`; `finish check` (che dalla decisione 20 usa questa stessa famiglia `diff` con `where="local"`) deve passare `False` e restare più severo, perché in locale il piano registrato è bloccato (6.2). Con il codice attuale, un piano modificato dopo la registrazione in `finish check` non è una violazione ma solo `plan_changed` di `attenzione`. È proprio la «unica differenza voluta» tra le due famiglie (review-focus 1), e nessun test la asserisce, nemmeno `where="local"` sulla famiglia `diff`. Correzione: `plan_change_is_attention=ctx.is_github`, chiamare `_plan_changed` solo se `ctx.is_github`, e aggiungere un test locale (piano cambiato: voce rossa `out_of_scope`/violazione sul piano, nessuna `plan_changed`) accanto a `test_plan_changed_after_registration`.

**I-2. Nome di comando non fidato in `Item.text`.** `evaluate.py:185` (`commands`, ramo `setup`): il filtro `name == "setup" or name.endswith(":setup")` accetta qualunque nome presente in `results.json`, che viene dall'artefatto del run della PR (D13: `artifacts.validate` controlla i percorsi, non i nomi), e il nome finisce in `text` (`f"il comando «{name}» è rosso"`), che per il modello (`model.py:76-79`) è testo scritto da tollgate e non va nel recinto. Vincolo globale: testo non fidato solo in `Item.data`. Il test `test_setup_red_is_a_red_command` anzi usa `profile:web:setup` in una configurazione senza il profilo `web`. Correzione: accettare solo `setup` e `profile:<p>:setup` con `<p>` in `ctx.cfg.profiles`, ignorare il resto (o metterlo in `data`) e aggiornare il test usando `PROFILE_TOML`.

### Minor

- **M-1.** `model.py:23-25` e `_command_state`: documentare (o gestire) `exit=None` con `state` diverso da `unverified`; oggi vale rosso silenzioso.
- **M-2.** `evaluate.py:227-236`: `base_path` per euristica sul maiuscolo; preferibile derivare il percorso verificando in git che il file esista (`git.exists_at(head/base)`) o limitarsi a documentare il caso. Il carry per il Task 17 lo annota già.
- **M-3.** `tests/test_openpr.py:751`: l'allentamento è corretto ma non forza il Task 13; meglio asserire `set(data) - set(prblock.DEFAULTS) == set(prblock.FIELDS) - set(prblock.DEFAULTS)` o lasciare una nota nel test.
- **M-4.** `tests/test_prblock.py` `test_findings_carry_blocking_field` passa anche senza alcuna modifica al codice (`build` non guarda i rilievi): testa un contratto che non esiste ancora; va bene come fissaggio, ma non copre D3.
- **M-5.** `evaluate()` cattura solo `git.GitError` (`evaluate.py:430`): un errore diverso (es. `OSError`) nelle famiglie dà un traceback invece di `error`. Da valutare quando i Task 5-9 aggiungono letture.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** i requisiti del brief e del controller sono quasi tutti soddisfatti con test precisi, ma la famiglia `diff` non distingue gate e `finish check` sul piano cambiato (decisione 9, review-focus 1) e un nome di comando preso da `results.json` finisce in `text` contro il vincolo sul testo non fidato; entrambi sono correzioni piccole.
