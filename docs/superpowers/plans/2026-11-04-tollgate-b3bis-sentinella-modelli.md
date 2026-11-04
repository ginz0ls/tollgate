# tollgate B3-bis: sentinella dei modelli

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** All'avvio di un lavoro, sul computer dell'utente, tollgate legge i nomi dei modelli AI dal punto unico che il progetto dichiara, li confronta con gli elenchi ufficiali dei fornitori (Anthropic, Gemini, OpenAI, OpenRouter) usando le chiavi già presenti nell'ambiente e avvisa se esiste un modello stabile più nuovo della stessa famiglia o se uno in uso sta per essere ritirato. In più: i test smettono di lasciare cartelle in `/tmp`, e le evidenze già su `main` perdono il testo di pagine e skill di terzi.

**Architecture:** Il progetto dichiara il punto unico in `tollgate.toml`, sezione nuova `[models] files` (percorsi letterali). I dati dei fornitori (indirizzo dell'elenco, intestazione della chiave, nomi delle variabili d'ambiente, pagina ufficiale da citare) stanno in un file di dati del plugin, `templates/models.toml`, **fuori da `bin/`**: così gli host delle API non finiscono in `.github/tollgate/` dei progetti e `test_real_markers_not_in_tollgate_bin` resta com'è. Il confronto è puro, in `tollgate_analysis/models.py` (nessuna rete, nessuno stato). La rete sta in `tollgate_flow/modelsfetch.py` (`urllib` della libreria standard, solo HTTPS verso l'host del fornitore, niente redirect, tetto di tempo e di dimensione, cache di 24 ore nella cartella di stato). `tollgate_flow/models_check.py` mette insieme le due parti e non solleva mai: lo chiamano `start` (solo per un lavoro nuovo, dopo la creazione) e il sottocomando nuovo `tollgate models check`. Gli hook non cambiano e restano senza rete.

**Tech Stack:** Python ≥ 3.11, solo libreria standard (`tomllib`, `json`, `urllib.request`, `urllib.parse`); bash; git. Test con `unittest` tramite `tests/run` (python3.11 e python3), senza rete: il client si prova con un `opener` finto.

**Spec:** il progetto approvato `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (l'autorità: «utente» non si discute, «mia scelta» si corregge solo con un motivo scritto qui), sezione 9 (punto «Sentinella dei modelli», «Solo modelli stabili», fornitori) e **sezione 10 (scelte dell'utente del 4 novembre 2026)**; la spec del nucleo `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 29 (la 30 la scrive il Task 8): 3.1, 3.2 («Gli hook non usano mai la rete»), 6.1, 11.4, 16, 18.4, 20; il piano principale di B `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, sezione 9, blocco «A B3-bis (sentinella dei modelli), da B3»; `skills/rules-ai/SKILL.md` (R-AI-01, R-AI-03, R-AI-04, R-AI-08: famiglia e stabilità per fornitore).

## Fatti verificati (4 novembre 2026, pagine ufficiali aperte con WebFetch)

| Fornitore | Elenco | Chiave | Campi utili | Cosa non dà |
|---|---|---|---|---|
| Anthropic | `GET https://api.anthropic.com/v1/models`, `limit` 1-1000 (predefinito 20), `after_id`, risposta `data[]`, `has_more`, `last_id`; senza `lifecycle` dà i modelli `active` e `deprecated` (https://platform.claude.com/docs/en/api/models/list) | `Authorization: Bearer $ANTHROPIC_API_KEY` (`x-api-key` è il ripiego legacy) e `anthropic-version` (esempio `2026-10-21`) (https://platform.claude.com/docs/en/api/overview) | `id`, `created_at` (può valere l'epoca se la data è ignota), `line` (può essere `null`: «do not infer a line from the `id`»), `lifecycle`, `deprecated_at`, `retires_at` | un'etichetta «anteprima»; il costo della chiamata |
| Gemini | `GET https://generativelanguage.googleapis.com/v1beta/models`, `pageSize` (predefinito 50, massimo 1000), `pageToken`, `nextPageToken` (assente = ultima pagina) (https://aistudio.google.com/api-reference/models/list-models; `ai.google.dev` vi rimanda con un 301) | intestazione `x-goog-api-key` (https://aistudio.google.com/docs/api-key); variabili `GEMINI_API_KEY` o `GOOGLE_API_KEY`, con precedenza a `GOOGLE_API_KEY` | `name` (`models/<id>`), `baseModelId`, `version`, `displayName` | date di uscita e di ritiro, stato; la stabilità si legge dal nome (https://aistudio.google.com/docs/models, «Model version name patterns»: stable, preview, latest, experimental) |
| OpenAI | `GET https://api.openai.com/v1/models` (https://developers.openai.com/api/reference/resources/models) | `Authorization: Bearer $OPENAI_API_KEY` | `id`, `created`, `owned_by`, `shutdown_date` (`YYYY-MM-DD` o `null`) | famiglia, stabilità |
| OpenRouter | `GET https://openrouter.ai/api/v1/models` (https://openrouter.ai/docs/api-reference/models/get-models) | Bearer secondo il riferimento dell'API (401 se manca); gli esempi della guida sono senza chiave | `id` (`autore/slug`, con varianti come `:free`), `created` (aggiunta a OpenRouter), `expiration_date` (`YYYY-MM-DD` o `null`) | famiglia, stabilità |

Nessuna delle quattro pagine dice che l'elenco sia gratuito; non usa modelli e non produce token. Claude Code usa `ANTHROPIC_API_KEY` al posto dell'abbonamento quando la trova nell'ambiente (in modo interattivo dopo una conferma, con `-p` sempre: https://code.claude.com/docs/en/authentication.md, «Authentication precedence»): per questo esiste una variabile dedicata (decisione 4). **Da verificare nel Task 2, Step 0 (controller):** il nome della variabile d'ambiente che la documentazione di OpenRouter usa negli esempi (`OPENROUTER_API_KEY` non è confermato dalle pagine lette).

## Global Constraints

- Solo libreria standard in `bin/` e nei test. Python ≥ 3.11. Ogni task chiude con `tests/run` verde (`python3.11` e `python3`); verifica finale come la CI: `PYTHONWARNINGS=error::ResourceWarning tests/run`.
- **Strati** (`tests/test_layers.py`, `tests/test_analysis_isolation.py`): `tollgate_analysis/models.py` non importa nulla di tollgate e non fa rete; la rete sta solo in `tollgate_flow/modelsfetch.py`; `tollgate_flow` non importa `tollgate_hooks` né `tollgate_checks`.
- **Hook senza rete** (spec 3.2): nessun file di `hooks/`, `bin/tollgate_hooks/`, `bin/tollgate_checks/` importa `modelsfetch` o `models_check` (`test_hooks_do_not_reach_models_net`, Task 2).
- **Nessuna operazione nuova in `apply._OPS`** (29) e **nessun tipo nuovo in `events.EVENT_TYPES`** (33): la sentinella scrive solo righe d'avviso.
- **Host delle API mai in `bin/`**: stanno in `templates/models.toml`, che `install.files` non copia nei progetti. `test_real_markers_not_in_tollgate_bin` non cambia.
- **La chiave non esce mai**: mai nell'URL, nelle righe, nei messaggi d'errore, nella cache, nei log, nelle evidenze. Nessuna chiave nei test, negli script o nei documenti.
- **Nessuna rete nei test**: il client si prova con un `opener` finto; nessun socket, nemmeno su `127.0.0.1`. Nessun `claude` vero; `gh` è `tests/fakegh.py`. Nessun test tocca `~/.local/state/tollgate`, `~/.claude/`.
- **Test con la radice del plugin esplicita**: i test nuovi che leggono `templates/models.toml` usano una radice temporanea, salvo quelli che controllano il file vero e lo dicono nel nome (`test_real_…`).
- La sentinella **avvisa e basta**: nessun rifiuto, nessun codice d'uscita diverso per colpa sua, nessuna eccezione che esce da `models_check.check`.
- `tollgate.toml` e i file dei modelli si leggono dalla punta del ramo predefinito di `origin` (`ref` di `start`), mai dal working tree (spec 3.2).
- Identificatori in inglese, testi per l'utente e per il modello in italiano. Il codice non usa la parola `sentinel` (già del gate, spec 9.1): componente `models_check`, moduli `models*`. Nessun `__pycache__` nel repo (`-B`). Commit dopo ogni task.

## Decisioni di questo piano

Scelte che il progetto e il piano principale lasciano a B3-bis, o che il codice reale impone, con il costo se sbagliate. Il Task 8 le riporta nella revisione 30 della spec.

1. **Forma del punto unico** (rinvio di B3, decisione 15). Sezione nuova di primo livello in `tollgate.toml`: `[models] files = ["src/ai/models.py"]`, percorsi **letterali** relativi alla radice del repo (niente glob, niente assoluti, niente `..`: una voce così si toglie con un avviso di configurazione). R-AI-01 resta com'è (è approvata): la sezione dice alla sentinella **dove** sta il punto, non come si scrive. `config.DEFAULTS["models"] = {"files": []}` e `[components] models_check = true`. Costo: un progetto che non dichiara `[models]` non riceve avvisi sui modelli (decisione 6 lo segnala quando il profilo `ai` è dichiarato).
2. **Nomi dei modelli dal testo, confronto esatto.** Dai file dichiarati si prendono i letterali tra `"`, `'` o `` ` `` che sembrano un ID (`[A-Za-z0-9][A-Za-z0-9._:/@-]{1,127}`). Un letterale è un modello di un fornitore se coincide con un ID del suo elenco, dopo due normalizzazioni: per Gemini si toglie `models/` dall'elenco; un prefisso `<fornitore>:` della forma di Agno (`anthropic:`, `google:`, `openai:`, `openrouter:`) si toglie dal letterale. Nessuna regola sui nomi per riconoscere un modello: decide l'elenco. Eccezione per i soli prefissi che le pagine fissano: un letterale `claude-<lettere>-<cifra>…` assente dall'elenco di Anthropic, o `gemini-<cifra>…` assente da quello di Gemini, dà «non è nell'elenco: ritirato o scritto male». Costo: un nome di modello costruito a pezzi nel codice non si vede.
3. **Cosa si controlla, per fornitore** (progetto 10: ciò che l'elenco non dà si salta, e si dice).
   - **Anthropic:** famiglia = `line`; stabile = `lifecycle` `active`; più nuovo = un modello stabile della stessa `line` con `created_at` successivo (nessun confronto se `line` è `null` o `created_at` è l'epoca); in ritiro = `lifecycle` `deprecated`, con la data `retires_at` se c'è. Non si chiedono i modelli `retired` (la forma del parametro a più valori non è verificata): un `claude-…` che manca dall'elenco ricade nella decisione 2.
   - **Gemini:** famiglia = la variante del nome `gemini-<versione>-<variante>` (per esempio `flash`, `flash-lite`, `pro`), con la versione confrontata come numeri; stabile = nome senza le parti `preview`, `exp`, `experimental`, `latest`; più nuovo = un nome stabile della stessa variante con versione maggiore; un `*-latest` usato non dà «più nuovo» (si sposta da solo, R-AI-08). Ritiro: **non controllato**, una riga lo dice con la pagina delle deprecazioni.
   - **OpenAI:** in ritiro = `shutdown_date` non `null`; «più nuovo» **non controllato** (una riga).
   - **OpenRouter:** in ritiro = `expiration_date` non `null`; «più nuovo» **non controllato** (una riga, che rimanda alla pagina del fornitore originale come R-AI-03).
   Una riga «non controllato» compare una volta per fornitore, solo se quel fornitore ha almeno un modello in uso. Costo: per tre fornitori su quattro la sentinella copre metà della domanda; l'utente l'ha scelto.
4. **Chiavi dall'ambiente, prima quella dedicata.** Per ogni fornitore si legge la prima variabile non vuota di un elenco fisso in `templates/models.toml`: `TOLLGATE_MODELS_ANTHROPIC_KEY`, poi `ANTHROPIC_API_KEY`; `TOLLGATE_MODELS_GEMINI_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`; `TOLLGATE_MODELS_OPENAI_KEY`, `OPENAI_API_KEY`; `TOLLGATE_MODELS_OPENROUTER_KEY`, poi il nome standard verificato nel Task 2, Step 0. La variabile dedicata serve perché `ANTHROPIC_API_KEY` nell'ambiente fa pagare Claude Code a consumo; in più il guardrail nega `TOLLGATE_` nei comandi Bash (il modello non può stamparla) e `runner.clean_env` la toglie ai comandi del progetto. L'elenco delle variabili **non** si configura in `tollgate.toml`: un repo ostile potrebbe farsi spedire un altro segreto. Un fornitore senza chiave si salta; nessuna chiave per nessun fornitore con modelli in uso dà una riga che nomina le variabili dedicate. Costo: chi vuole un altro nome di variabile non può sceglierlo.
5. **Client HTTP stretto.** `urllib.request` con un `OpenerDirector` costruito da noi: solo `https`, host uguale a quello del fornitore in `templates/models.toml`, nessun redirect seguito (un 3xx è un errore), tetto di 5 s per richiesta e di 8 MiB per risposta (lettura a pezzi, oltre il tetto si ferma), al più 10 pagine per fornitore, JSON obbligatorio. La chiave va solo nell'intestazione (anche per Gemini, con `x-goog-api-key`, mai `?key=`). Gli errori diventano `FetchError` con un testo nostro fisso per tipo (chiave rifiutata per 401 e 403, troppe richieste per 429, nessuna risposta, risposta troppo grande, redirect rifiutato, non JSON, errore HTTP `<n>`): mai il corpo della risposta, mai l'URL completo con i parametri, mai la chiave. Costo: un fornitore che sposta l'API con un redirect smette di funzionare finché non si aggiorna il file di dati, e la riga d'errore lo dice.
6. **Quando gira.** In `start`, solo per un **lavoro nuovo**, in `_create` dopo `housekeeping.run` e prima delle righe finali; non nella ripresa (`_resume`) né senza rete (lì `start` rifiuta già un lavoro nuovo). Non gira con `[components] models_check = false`. Con `[models] files` vuoto non fa rete; se `tollgate.toml` dichiara `[profiles.ai]`, una riga lo ricorda («il profilo ai è dichiarato ma `[models] files` è vuoto: la sentinella non sa dove cercare»). Le righe vanno in `notes.warnings` (prefisso `avviso:` che `start` già mette, «modelli:» dopo), al più 12 più «… e altri N avvisi sui modelli». Costo: un lavoro ripreso non ricontrolla.
7. **Cache di 24 ore.** Un file per fornitore in `<cartella di stato>/models/<fornitore>.json` (`{"fetched_at", "pages"}`), scritto con un temporaneo e `os.replace`; illeggibile o più vecchio di 24 ore → nuova richiesta; una richiesta fallita non cancella la cache e, se la cache c'è, la usa e lo dice. `tollgate models check --refresh` la ignora. La cache contiene solo l'elenco pubblico dei modelli, mai la chiave. Costo: un modello uscito oggi può arrivare con un giorno di ritardo.
8. **Sottocomando `tollgate models check [--refresh]`.** Per la prova e per l'uso a mano: dalla cartella corrente trova il repo, legge `tollgate.toml` e i file dei modelli da `origin/<predefinito>` (senza `git fetch`), stampa le righe di `models_check.check` con il prefisso `avviso: `, oppure `modelli: nessun avviso`. Esce con 0; con 1 solo fuori da un repo, senza `origin` o senza `tollgate.toml` su `origin/<predefinito>`. Non legge la sessione e non è tra i comandi negati ai subagenti. Costo: nessuno.
9. **Dati dei fornitori in un file del plugin.** `templates/models.toml`, una tabella per fornitore (`anthropic`, `gemini`, `openai`, `openrouter`) con `url` (l'elenco, con il parametro della dimensione di pagina), `paging` (`anthropic`, `gemini`, `none`), `auth` (`bearer` o il nome di un'intestazione), `headers` (per Anthropic `anthropic-version = "2026-10-21"`), `env` (decisione 4), `page` (la pagina ufficiale dei modelli o delle deprecazioni da citare nelle righe). `modelsfetch.load_providers(plugin_root)` lo valida: chiavi note, `url` `https`, nessun fornitore in più o in meno. Costo: un file da tenere aggiornato quando un fornitore cambia API o versione.
10. **Temporanei dei test** (progetto 10). `tests/run` crea per ogni corsa `mktemp -d "${TMPDIR:-/tmp}/tollgate-run-XXXXXX"`, lo esporta come `TMPDIR` e lo toglie all'uscita con `trap`: ogni `mkdtemp` dei test ci finisce dentro. Restano sotto `/tmp` (memoria: `TMPDIR` dentro `~/.claude` rompe i test che vogliono il temporaneo fuori da un repo; la guardia di P4 vuole `/tmp` o `$TMPDIR`). In più si chiudono le perdite principali trovate (`tests/test_gh.py:20`, circa 12.300 cartelle, che toglie lo stato ma non `self.tmp`; `tests/test_statusline.py:26`, `tollgate-home-`, circa 2.600; `tests/test_hook_engine.py:196`, `tollgate-finti-`, in `setUpClass`; `tests/test_start.py:87` pulisce già), così un `python3 -m unittest` lanciato a mano non sporca. Le cartelle vecchie le cancella il controller (Task 7, Step 1). Costo: nessuno.
11. **Evidenze già su `main`** (lezione di B3). Si ripuliscono con `spikes/b1/flowreg.py togli-pagine` i file di `docs/verifiche/evidenze/` che contengono testo di skill di terzi (`writing-plans` di Superpowers in B1, B2 e gh-p4) o risultati lunghi di `WebFetch` (B1, passo 2 precedente). Prima si corregge `flowreg.external_skill`, che oggi tratta come esterna ogni skill il cui percorso non contiene «tollgate» (lo è `skills/execute` di questo repo, «Plugin IT workflow»): una skill è di tollgate se il nome della sua cartella è una cartella di `skills/` del repo e il percorso non sta in `/plugins/cache/` (o ci sta sotto una cartella `tollgate/`). Un test sull'intero `docs/verifiche/evidenze/` impedisce che ritorni. **La storia di git non si riscrive** (servirebbe un push forzato; precedente del 01/11/2026 sui nomi): lo si dice all'utente. Costo: le righe restano nei commit vecchi del repo pubblico.
12. **Prova vera, una volta** (progetto 10). Un repo di prova sotto `/tmp/tollgate-b3bis/` con `origin` nudo locale, `tollgate.toml` con `[models] files = ["ai/models.py"]` e un file con un modello vecchio per fornitore (scelti dal controller sulle pagine ufficiali il giorno della prova, Task 7); `tollgate models check --refresh` con l'ambiente dell'utente, poi una seconda volta senza `--refresh` (cache). Al più 3 tentativi. Si salvano solo le righe d'uscita, dopo un controllo che non contengano chiavi. Costo: una chiamata di elenco per fornitore con la chiave, nessun token.

## Review Focus

1. **Chiave che esce.** Un errore di rete o HTTP con la chiave in una variabile: né le righe, né la cache, né il testo di `FetchError`, né `repr` dell'eccezione contengono la chiave; per Gemini l'URL della richiesta non ha `key=`. Test: Task 2 `test_key_never_in_errors_lines_or_cache`, `test_gemini_key_in_header_not_url`.
2. **Rete lenta, assente o strana.** Tempo scaduto, 401, 429, 500, redirect, HTML al posto del JSON, corpo oltre 8 MiB, JSON con la forma sbagliata: ognuno dà una riga e `start` crea il lavoro con codice 0. Test: Task 2 `test_fetch_errors_are_fetch_errors`, `test_redirect_refused`, `test_body_over_cap_stops`; Task 1 `test_parse_wrong_shape_raises`; Task 3 `test_check_never_raises`; Task 4 `test_start_succeeds_when_check_fails`.
3. **Falsi allarmi.** Un letterale che non è un modello (`"claude"`, `"gemini-cli"`, un percorso), un `*-latest`, un'anteprima più nuova di uno stabile, un modello con `created_at` all'epoca, `line` `null`: nessun avviso «più nuovo». Test: Task 1 `test_literals_*`, `test_anthropic_newer_*`, `test_gemini_family_*`, `test_unknown_prefix_only_for_versioned_names`.
4. **Elenchi a più pagine.** Anthropic con `has_more` e `last_id`, Gemini con `nextPageToken`, il tetto di 10 pagine. Test: Task 2 `test_anthropic_pages_followed`, `test_gemini_pages_followed`, `test_page_cap`.
5. **Configurazione e file del progetto.** `[models] files` con un percorso assente su `origin`, uno con `..` o assoluto, la cache illeggibile, due fornitori con uno che fallisce, il componente spento. Test: Task 3 `test_missing_file_line`, `test_bad_paths_dropped_with_warning`, `test_corrupt_cache_refetched`, `test_one_provider_fails_other_reports`, `test_component_off_no_network`.

## Mappa dei file

| File | Task | Responsabilità |
|---|---|---|
| `bin/tollgate_analysis/models.py`; `tests/test_models.py` | 1 | letterali, elenchi, confronto (puro) |
| `templates/models.toml`, `bin/tollgate_flow/modelsfetch.py`; `tests/test_modelsfetch.py` | 2 | dati dei fornitori, client HTTP, cache |
| `bin/tollgate_core/config.py`, `bin/tollgate_flow/models_check.py`; `tests/test_config.py`, `tests/test_models_check.py` | 3 | sezione `[models]`, componente, orchestrazione |
| `bin/tollgate_flow/start.py`, `bin/tollgate_core/cli.py`, `skills/start/SKILL.md`, `docs/uso/comandi.md`, `docs/uso/installazione.md`; `tests/test_start.py`, `tests/test_cli.py` | 4 | `start`, `models check`, documentazione d'uso |
| `tests/run`, `tests/test_gh.py`, `tests/test_statusline.py`, `tests/test_hook_engine.py`; `tests/test_run_script.py` | 5 | temporanei dei test |
| `spikes/b1/flowreg.py`, `docs/verifiche/evidenze/**`, rapporti delle prove di B1, B2, gh-p4; `tests/test_b1_scripts.py` | 6 | evidenze ripulite |
| `spikes/b3bis/models-prova.sh`; `tests/test_b3bis_script.py`; `docs/verifiche/2026-11-04-b3bis-prova-modelli.md`, `docs/verifiche/evidenze/b3bis/` | 7 | pulizia di `/tmp` (controller), prova vera |
| spec del nucleo, progetto di B, piano principale di B | 8 | revisione 30 e stato |

---

### Task 1: Confronto puro dei modelli

**Files:**
- Create: `bin/tollgate_analysis/models.py`, `tests/test_models.py`

**Interfaces:**
- Produces:
  - `models.PROVIDERS = ("anthropic", "gemini", "openai", "openrouter")`;
  - `models.ModelInfo` (dataclass frozen: `provider: str`, `id: str`, `family: str | None`, `stable: bool`, `created: str | None`, `retires: str | None`, `retiring: bool`);
  - `models.ModelsFormatError(ValueError)`;
  - `models.parse_pages(provider: str, pages: list[dict]) -> list[ModelInfo]` (una forma inattesa è `ModelsFormatError`; un elemento senza `id`/`name` stringa si salta);
  - `models.literals(text: str) -> set[str]` (decisione 2);
  - `models.used(literals: set[str], infos: list[ModelInfo]) -> list[ModelInfo]` (con le normalizzazioni della decisione 2);
  - `models.gemini_family(model_id: str) -> tuple[str, tuple[int, ...]] | None`;
  - `models.findings(provider: str, used_infos: list[ModelInfo], infos: list[ModelInfo], literals: set[str], *, where: dict[str, str], page: str) -> list[str]` (`where`: letterale → file dichiarato in cui compare; `page`: la pagina da citare).

- [ ] **Step 1: I test che falliscono** (`tests/test_models.py`, pagine finte costruite nel test, mai testo dei fornitori):
  - `test_literals_quotes_and_charset` (`"claude-x-5"`, `'gemini-3.6-flash'`, `` `gpt-x` `` presi; `"due parole"`, `""` e un letterale di 200 caratteri no); `test_literals_ignore_comments_without_quotes`;
  - `test_parse_anthropic` (`line`, `lifecycle`, `created_at`, `retires_at` → `ModelInfo`; `stable` solo con `active`; `retiring` con `deprecated`); `test_parse_gemini_strips_models_prefix` (`models/gemini-3.6-flash` → `id` `gemini-3.6-flash`, `family` `flash`); `test_parse_openai_shutdown_date`; `test_parse_openrouter_expiration_date`; `test_parse_wrong_shape_raises` (`data` non lista, `models` non lista, pagina non dizionario → `ModelsFormatError`);
  - `test_used_exact_match_and_agno_prefix` (`"anthropic:claude-x-5"` e `"models/gemini-3.6-flash"` riconosciuti; `"claude"` e `"gemini-cli"` no);
  - `test_anthropic_newer_same_line` (in uso `a-old` `sonnet` 2026-01; nell'elenco `a-new` `sonnet` `active` 2026-09 e `b-newer` `opus` 2026-10 → una riga che nomina `a-new`, nessuna su `b-newer`); `test_anthropic_newer_skipped_without_line_or_epoch_date`; `test_anthropic_deprecated_with_date` (riga con `retires_at`); `test_anthropic_deprecated_newer_not_from_deprecated` (un `deprecated` più nuovo non è proposto);
  - `test_gemini_family_parse` (`gemini-3.6-flash` → `("flash", (3, 6))`; `gemini-3.6-flash-lite` → `("flash-lite", (3, 6))`; `gemini-2.5-flash-preview-09-2025` → `("flash", (2, 5))`; `gemini-flash-latest` → `None`); `test_gemini_newer_stable_only` (in uso `gemini-3.5-flash`; nell'elenco `gemini-3.6-flash` e `gemini-3.7-flash-preview-…` → la riga nomina solo `gemini-3.6-flash`); `test_gemini_version_numeric` (`3.10` è più nuovo di `3.9`); `test_gemini_latest_no_newer`; `test_gemini_retirement_not_checked_line` (una sola riga «non controllato», con `page`);
  - `test_openai_shutdown_and_not_checked`, `test_openrouter_expiration_and_not_checked` (riga di ritiro con la data; una riga «più nuovo non controllato» per fornitore);
  - `test_unknown_prefix_only_for_versioned_names` (`"claude-x-5"` assente dall'elenco di Anthropic → riga «non è nell'elenco»; `"claude-code"` e `"gemini-cli"` no);
  - `test_lines_name_file_and_page` (ogni riga ha la forma `modelli: <fornitore>: <id> (<file>): <testo> — <page>`; nessuna riga per un fornitore senza modelli in uso).
- [ ] **Step 2: Verifica che falliscano.** `python3 -B -m unittest tests.test_models`: FAIL (modulo assente).
- [ ] **Step 3: Il codice.** `models.py` per le decisioni 2 e 3. Le date si confrontano come stringhe ISO 8601 (ordinabili); l'epoca è una data che comincia con `1970-01-01`. Il modulo non importa nulla di tollgate.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_models tests.test_analysis_isolation tests.test_layers`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: confronto puro dei modelli con gli elenchi ufficiali».

---

### Task 2: Dati dei fornitori, client HTTP e cache

**Files:**
- Create: `templates/models.toml`, `bin/tollgate_flow/modelsfetch.py`, `tests/test_modelsfetch.py`

**Interfaces:**
- Consumes: `models.PROVIDERS` (Task 1); `paths.State`.
- Produces:
  - `modelsfetch.Provider` (dataclass frozen: `name`, `url`, `host`, `paging`, `auth`, `headers: dict[str, str]`, `env: tuple[str, ...]`, `page`);
  - `modelsfetch.ProvidersError(ValueError)`; `modelsfetch.load_providers(plugin_root: Path) -> dict[str, Provider]` (decisione 9);
  - `modelsfetch.api_key(provider: Provider, environ: Mapping[str, str]) -> str | None` (decisione 4);
  - `modelsfetch.FetchError(Exception)` (solo testi della decisione 5);
  - `modelsfetch.fetch_pages(provider: Provider, key: str, *, opener=None, timeout: float = 5.0, max_bytes: int = 8 * 1024 * 1024, max_pages: int = 10) -> list[dict]`;
  - `modelsfetch.CACHE_HOURS = 24`; `modelsfetch.cached_pages(state: State, provider: Provider, key: str, *, now, refresh: bool = False, fetch=fetch_pages) -> tuple[list[dict], str]` (seconda voce: `"rete"`, `"cache"`, oppure `"cache (rete non riuscita: <testo>)"`; senza cache e con la rete fallita solleva `FetchError`).

- [ ] **Step 0 (controller): la variabile di OpenRouter.** Con `WebFetch` sulle pagine ufficiali di OpenRouter (`openrouter.ai/docs`) cerca il nome della variabile d'ambiente degli esempi. Se c'è, va in `env` dopo `TOLLGATE_MODELS_OPENROUTER_KEY`; se non c'è, resta la sola variabile dedicata. Scrivilo in una `Ruling:` con l'URL.
- [ ] **Step 1: I test che falliscono** (`tests/test_modelsfetch.py`; `opener` finto con `open(request, timeout)` che registra la richiesta e restituisce una risposta finta con `status`, `headers`, `read(n)`, oppure solleva):
  - `test_real_providers_file_loads` (`load_providers(ROOT)` dà i quattro fornitori, `url` `https`, Gemini con `auth = "x-goog-api-key"`, Anthropic con `anthropic-version`); `test_providers_file_rejects_unknown_key_http_and_missing_provider` (radice temporanea);
  - `test_real_providers_not_installed` (nessun file di `install.files(ROOT, …)` è `templates/models.toml`, e nessun file sotto `bin/` contiene un host di `templates/models.toml`);
  - `test_api_key_order` (dedicata prima di quella standard; vuota saltata; nessuna → `None`; Gemini: `GOOGLE_API_KEY` prima di `GEMINI_API_KEY`);
  - `test_bearer_and_version_headers` (Anthropic: `Authorization: Bearer k`, `anthropic-version`); `test_gemini_key_in_header_not_url`;
  - `test_anthropic_pages_followed` (`has_more` vero e `last_id` → seconda richiesta con `after_id`); `test_gemini_pages_followed` (`nextPageToken` → `pageToken`); `test_page_cap` (11 pagine possibili → si ferma a 10 con `FetchError` «troppe pagine»);
  - `test_fetch_errors_are_fetch_errors` (401, 403, 429, 500, `TimeoutError`, `URLError`, HTML, JSON non valido → `FetchError` con il testo fisso della decisione 5); `test_redirect_refused` (l'`opener` vero costruito dal modulo ha il gestore che rifiuta i 3xx: `redirect_request` solleva `FetchError`); `test_body_over_cap_stops` (lettura a pezzi: si ferma oltre `max_bytes`);
  - `test_wrong_host_refused` (un `url` che punta a un altro host o con `http` → `ProvidersError`);
  - `test_key_never_in_errors_lines_or_cache` (chiave `sk-PROVA-123`: dopo ogni errore di `test_fetch_errors_are_fetch_errors` né `str` né `repr` dell'eccezione la contengono; il file di cache scritto dopo un successo non la contiene);
  - `test_cache_fresh_used` (entro 24 ore niente rete); `test_cache_stale_refetched`; `test_corrupt_cache_refetched`; `test_refresh_ignores_cache`; `test_failed_fetch_keeps_and_uses_cache` (seconda voce `cache (rete non riuscita: …)`); `test_cache_written_atomically` (nessun temporaneo resta);
  - `test_hooks_do_not_reach_models_net` (analisi degli import come `tests/test_layers.py`: nessun modulo di `tollgate_hooks`, `tollgate_checks` né `hooks/run` importa `modelsfetch` o `models_check`).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice e i dati.** `templates/models.toml` con i valori della tabella «Fatti verificati» e della decisione 9 (`url` con `limit=1000` per Anthropic e `pageSize=1000` per Gemini; `page`: per Anthropic https://platform.claude.com/docs/en/about-claude/model-deprecations, per Gemini https://ai.google.dev/gemini-api/docs/deprecations, per OpenAI https://developers.openai.com/api/docs/deprecations, per OpenRouter https://openrouter.ai/docs/guides/overview/models.md: gli indirizzi già in «Dove informarsi» di `rules-ai`). `modelsfetch.py` per le decisioni 5, 7 e 9; l'`opener` vero è `urllib.request.build_opener` con un `HTTPRedirectHandler` che solleva e senza gestori di proxy dall'ambiente. Nessun `print`, nessun log.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_modelsfetch tests.test_layers tests.test_rules_ai`: PASS (`test_real_markers_not_in_tollgate_bin` invariato e verde). `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: dati dei fornitori, client HTTP stretto e cache degli elenchi».

---

### Task 3: Sezione `[models]` e controllo completo

**Files:**
- Modify: `bin/tollgate_core/config.py`
- Create: `bin/tollgate_flow/models_check.py`, `tests/test_models_check.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: Task 1 e 2; `git.text_at(repo, ref, path) -> str | None`; `config.Config.get`.
- Produces:
  - `config.DEFAULTS["models"] = {"files": []}`, `config.DEFAULTS["components"]["models_check"] = True`;
  - `models_check.PLUGIN_ROOT` (come `init.PLUGIN_ROOT`); `models_check.MAX_LINES = 12`;
  - `models_check.check(state: State, repo: Path, ref: str, cfg: Config, *, environ: Mapping[str, str], now, plugin_root: Path | None = None, refresh: bool = False, fetch=None) -> list[str]` (righe senza il prefisso `avviso:`; non solleva mai: un'eccezione inattesa dà la sola riga `modelli: controllo non riuscito (<classe>)`).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_config.py`: `test_models_files_default_empty`; `test_models_files_type_checked` (un numero → `ConfigError` come le altre liste); `test_bad_paths_dropped_with_warning` (`"/etc/x"`, `"../x"`, `"src/*.py"` tolti, ognuno con un avviso; `"src/ai/models.py"` resta); `test_models_check_component_default_true`.
  - `tests/test_models_check.py` (repo git temporaneo con `origin` nudo come i lab esistenti, `fetch` finto, radice del plugin temporanea con un `templates/models.toml` che usa host finti `https`): `test_component_off_no_network`; `test_no_files_no_network`; `test_no_files_with_ai_profile_reminds` (con `[profiles.ai]` nel `tollgate.toml`: la riga della decisione 6, nessuna rete); `test_reads_files_from_ref_not_worktree` (il file cambiato solo nel working tree non conta); `test_missing_file_line`; `test_no_key_line_names_dedicated_vars`; `test_provider_without_key_skipped`; `test_one_provider_fails_other_reports`; `test_corrupt_cache_refetched` (attraverso `check`); `test_lines_capped` (20 avvisi → 12 righe più «… e altri 8 avvisi sui modelli»); `test_check_never_raises` (`fetch` che solleva `RuntimeError`, `parse` che solleva, `git.text_at` che solleva → una riga, nessuna eccezione); `test_end_to_end_anthropic_newer_and_deprecated` (un file con due modelli, elenco finto: le due righe attese).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `config`: la sezione e il componente nelle `DEFAULTS`, il filtro dei percorsi della decisione 1 con avvisi in `Config.warnings`. `models_check`: componente → file da `ref` → letterali (con `where`) → per ogni fornitore con chiave `cached_pages`, `parse_pages`, `used`, `findings` → riga d'errore per il fornitore che fallisce → tetto delle righe.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_config tests.test_models_check`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: sezione [models] e controllo dei modelli del progetto».

---

### Task 4: `start`, `models check` e documentazione d'uso

**Files:**
- Modify: `bin/tollgate_flow/start.py` (`_create`), `bin/tollgate_core/cli.py` (sottocomando `models`), `skills/start/SKILL.md` (elenco degli avvisi, righe 28-31), `docs/uso/comandi.md` (sezione di `/tollgate:start` e un paragrafo su `models check`), `docs/uso/installazione.md` (chiavi per la sentinella)
- Test: `tests/test_start.py`, `tests/test_cli.py`, `tests/test_docs.py` (invariato, deve restare verde)

**Interfaces:**
- Consumes: `models_check.check` (Task 3).
- Produces: le righe `avviso: modelli: …` nell'uscita di `start`; `tollgate models check [--refresh]` (decisione 8).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_start.py`: `test_start_appends_model_warnings` (`models_check.check` sostituito con un finto che dà `["modelli: x"]`: l'uscita di un lavoro nuovo ha `avviso: modelli: x` prima della riga `lavoro #… avviato`, codice 0; il finto riceve `ref` `origin/<predefinito>` e `environ` uguale a `os.environ`); `test_start_succeeds_when_check_fails` (il vero `check` con un `fetch` che solleva: codice 0, una riga); `test_resume_does_not_check` (ripresa: il finto non è chiamato); `test_start_without_models_section_unchanged` (i test esistenti di `start` non cambiano esito: nessuna rete con `[models]` assente).
  - `tests/test_cli.py`: `test_models_check_prints_lines` (finto come sopra: righe con `avviso: `, uscita 0); `test_models_check_no_warnings` (`modelli: nessun avviso`); `test_models_check_outside_repo_exits_1`; `test_models_check_refresh_flag_passed`; `test_models_check_allowed_to_subagents` (`cli_calls` non nega `models check` a un input con `agent_id`).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice e i testi.** In `_create`, dopo `housekeeping.run`, `notes.warnings.extend(models_check.check(state, main, ref, cfg, environ=os.environ, now=now))`. In `cli.py` il parser `models` con `check` e `--refresh`, smistato come `status` (sola lettura, nessun segnale di sessione). Nella skill `start` una voce in più nell'elenco degli avvisi: «gli avvisi `modelli:` dicono che c'è un modello stabile più nuovo della stessa famiglia o che uno in uso sta per essere ritirato: riferiscili all'utente, non cambiare modello da solo». In `comandi.md` e `installazione.md`, in parole semplici: la sezione `[models] files`; le variabili dedicate e perché (`ANTHROPIC_API_KEY` nell'ambiente fa usare a Claude Code la chiave al posto dell'abbonamento); che la sentinella non usa modelli; che cosa non controlla per ogni fornitore; la cache di un giorno e `--refresh`.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_start tests.test_cli tests.test_docs`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: avvisi sui modelli all'avvio di un lavoro e comando models check».

---

### Task 5: I test smettono di lasciare cartelle in `/tmp`

**Files:**
- Modify: `tests/run`, `tests/test_gh.py:20`, `tests/test_statusline.py:26`, `tests/test_hook_engine.py:196`
- Create: `tests/test_run_script.py`

**Interfaces:**
- Produces: `tests/run` con `TMPDIR` per corsa (decisione 10).

- [ ] **Step 1: I test che falliscono** (`tests/test_run_script.py`):
  - `test_run_sets_and_removes_tmpdir`: lancia `tests/run -k test_tmpdir_probe` con `PYTHONS` uguale a `sys.executable` e la variabile `RUN_TMP_PROBE` che nomina un file in una cartella del test; la sonda `test_tmpdir_probe` (nello stesso file, saltata senza `RUN_TMP_PROBE`) scrive lì `tempfile.gettempdir()`. Atteso: uscita 0; la cartella scritta comincia con `tollgate-run-`, sta sotto la `TMPDIR` di partenza, e dopo la corsa non esiste più.
  - `test_run_removes_tmpdir_on_failure`: stessa cosa con la sonda che fallisce apposta (`RUN_TMP_PROBE_FAIL=1`): uscita diversa da 0 e cartella tolta.
  - `test_known_leaks_closed`: per `tests.test_gh.FakeGhCase` e le classi di `test_statusline.py:26` e `test_hook_engine.py:196`, dopo `setUp` e i `cleanup` (o `setUpClass`/`tearDownClass`) la cartella creata non esiste più.
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** In `tests/run`, prima del ciclo: `RUN_TMP="$(mktemp -d "${TMPDIR:-/tmp}/tollgate-run-XXXXXX")"`, `trap 'rm -rf "$RUN_TMP"' EXIT`, `export TMPDIR="$RUN_TMP"`. Nelle tre classi, `addCleanup(shutil.rmtree, <cartella>, ignore_errors=True)` (o `tearDownClass`).
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_run_script tests.test_p4_ghguard tests.test_gh`: PASS (la guardia di P4 accetta il `TMPDIR` della corsa). `tests/run`: verde, e dopo la corsa `ls -d /tmp/tollgate*` non ha cartelle nuove create dalla corsa.
- [ ] **Step 5: Commit** «tollgate B3-bis: i test non lasciano più cartelle in /tmp».

---

### Task 6: Evidenze su `main` senza testo di terzi

**Files:**
- Modify: `spikes/b1/flowreg.py` (`external_skill`), i `.jsonl` di `docs/verifiche/evidenze/` che `togli-pagine` cambia, la sezione «Anonimizzazione» (o, se manca, una riga in fondo) dei rapporti `docs/verifiche/2026-10-27-b1-prova-flusso.md`, `docs/verifiche/2026-10-29-b2-prova-flusso.md` e `docs/verifiche/2026-10-21-p4-prova-flusso.md` (evidenze di gh-p4)
- Test: `tests/test_b1_scripts.py`

**Interfaces:**
- Consumes: `flowreg.togli_pagine(paths) -> int`, `flowreg.MAX_WEB_RESULT` (5000), `flowreg.external_skill(text)`.
- Produces: `flowreg.tollgate_skill(path: str) -> bool` (decisione 11).

- [ ] **Step 1: I test che falliscono** (`tests/test_b1_scripts.py`):
  - `test_tollgate_skill_by_folder_not_word` (`…/Plugin IT workflow/skills/execute` → di tollgate; `…/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/writing-plans` → esterna; `…/plugins/cache/x/tollgate/0.2.0/skills/start` → di tollgate; `/tmp/tollgate-b1/plugin/skills/start` → di tollgate);
  - `test_external_skill_keeps_tollgate_execute` (un blocco lungo della skill `execute` di questo repo non si tocca);
  - `test_real_evidence_has_no_third_party_text` (su ogni `.jsonl` tracciato in `docs/verifiche/evidenze/`: nessun blocco che `external_skill` riconosce, nessun risultato di `WebFetch`/`WebSearch` oltre `MAX_WEB_RESULT`; lo stesso controllo di `togli_pagine`, in sola lettura, messo in una funzione `third_party_blocks(path) -> list[str]` usata da entrambi).
- [ ] **Step 2: Verifica che falliscano.** `test_real_evidence_has_no_third_party_text` fallisce sui file di B1, B2 e gh-p4 trovati nella preparazione del piano.
- [ ] **Step 3: Correzione e pulizia.** `external_skill` usa `tollgate_skill`. Poi `python3 -B spikes/b1/flowreg.py togli-pagine` sui file che il test segnala, e controllo a mano del risultato (ogni file resta JSONL valido, i `tool_use` e i prompt restano). Nei tre rapporti una riga: «Il 2026-11-0x il testo di skill e pagine di terzi è stato sostituito da un segnaposto (`flowreg.py togli-pagine`); i commit precedenti lo contengono ancora.» Se un test esistente legge un file ripulito (`grep -rn evidenze tests/`), si controlla che resti verde.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_b1_scripts tests.test_p4_flowstate tests.test_p5_scripts tests.test_eval_run`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3-bis: evidenze delle prove senza testo di skill e pagine di terzi».

---

### Task 7: Pulizia di `/tmp` e prova vera (controller, con lo script dell'implementatore)

**Files:**
- Create: `spikes/b3bis/models-prova.sh`, `spikes/b3bis/progetto/` (`tollgate.toml` con `[models] files = ["ai/models.py"]`, `ai/models.py` con un segnaposto per modello, `README.md`), `tests/test_b3bis_script.py`; poi (controller) `docs/verifiche/2026-11-04-b3bis-prova-modelli.md`, `docs/verifiche/evidenze/b3bis/`

**Interfaces:**
- Consumes: `tollgate models check` (Task 4).
- Produces: lo script con i modi `controlla`, `prepara`, `prova`.

- [ ] **Step 1 (controller): cartelle vecchie in `/tmp`** (progetto 10). `find /tmp -maxdepth 1 -user "$(id -un)" -name 'tollgate*' -mtime +1`, esclusi `/tmp/tollgate-b1`, `/tmp/tollgate-b3bis`, `/tmp/tollgate-eval-target` e le cartelle `tollgate-run-*` di una corsa in corso; mostra all'utente il numero e i primi nomi, poi cancella con `-exec rm -rf {} +`. Riporta il numero nel ledger.
- [ ] **Step 2: I test che falliscono** (`tests/test_b3bis_script.py`, implementatore, senza rete): `test_controlla_mode_no_network` (`controlla` verifica `bash`, `git`, `python3.11`, la presenza del progetto di prova e stampa quali variabili di chiave sono impostate **solo per nome, mai il valore**); `test_prepara_builds_repo_with_origin` (con `B3BIS_DIR` in una cartella temporanea: repo con `origin` nudo, `tollgate.toml` e `ai/models.py` committati e spinti); `test_prova_refuses_outside_tmp_root` (una cartella fuori da `/tmp/tollgate-b3bis/` o dalla cartella del test → errore); `test_prova_output_checked_for_keys` (uscita finta che contiene il valore di una variabile di chiave → lo script rifiuta di salvarla).
- [ ] **Step 3: Lo script** (implementatore). `prepara` copia `spikes/b3bis/progetto/` in `$B3BIS_DIR/repo` (predefinito `/tmp/tollgate-b3bis`), crea `origin` nudo locale, committa e spinge; `prova` lancia due volte `python3.11 -B <plugin>/bin/tollgate models check` (la prima con `--refresh`) con lo stato in `$B3BIS_DIR/state` (con la sentinella `.tollgate-test` di `paths`), salva le uscite in `$B3BIS_DIR/out/` e si ferma se un'uscita contiene il valore di una delle variabili di chiave di `templates/models.toml`. Gli implementatori lanciano solo `bash -n`, `controlla` e i test.
- [ ] **Step 4: Verifica e commit** (implementatore). `bash -n spikes/b3bis/models-prova.sh`; `python3 -B -m unittest tests.test_b3bis_script`: PASS; `tests/run`: verde. Commit «tollgate B3-bis: script e progetto della prova vera».
- [ ] **Step 5 (controller): i modelli della prova.** Apri con `WebFetch` le pagine ufficiali dei modelli e delle deprecazioni dei fornitori di cui l'utente ha la chiave (`controlla` dice quali) e scrivi in `spikes/b3bis/progetto/ai/models.py` un modello stabile ma non il più recente per Anthropic e per Gemini, uno con data di ritiro per OpenAI e OpenRouter se le pagine ne danno uno, ciascuno con l'URL e la data (R-AI-02). Commit «tollgate B3-bis: modelli della prova vera».
- [ ] **Step 6 (controller): la prova.** `prepara`, poi `prova`, con l'ambiente dell'utente. Al più 3 tentativi; oltre ti fermi e chiedi. Atteso: per ogni fornitore con chiave le righe della decisione 3 (più nuovo o in ritiro, «non controllato» dove previsto); la seconda corsa dice di usare la cache e non fa rete. Un difetto del prodotto scoperto qui è un giro del task che possiede il codice (test che fallisce, correzione, `tests/run`), poi si ripete solo `prova`.
- [ ] **Step 7 (controller): rapporto ed evidenze.** `docs/verifiche/2026-11-04-b3bis-prova-modelli.md`: fornitori provati e saltati, righe ottenute contro le attese, tempi, tentativi (un esito in più tentativi è «composito»), limiti (decisione 3). Evidenze: le sole uscite, dopo `grep` dei valori delle chiavi, del nome utente, dell'host e delle forme di token. Commit «tollgate B3-bis: prova vera della sentinella dei modelli».

---

### Task 8: Revisione 30 della spec, progetto, piano principale

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`

- [ ] **Step 1: Revisione 30 della spec del nucleo.** 3 (albero: `templates/models.toml`); 3.1 (riga di `models check`); 3.2 (la rete della sentinella sta nella CLI, mai negli hook); 6.1 (avvisi dei modelli a un lavoro nuovo, decisione 6); 11.4 (`[models] files`, `[components] models_check`, variabili e cache, decisioni 1, 4, 7); 16 (i fatti verificati di questo piano, con gli URL e la data, e l'esito della prova vera); riga 30 della sezione 20; intestazione.
- [ ] **Step 2: Piano principale di B.** Stato in testa (corregge anche la frase di B3 «merge in attesa dell'OK», superata dall'unione del 03/11/2026); una riga B3-bis nella sezione 2; nella sezione 3 una riga B3-bis → B8 (righe `modelli:` dell'uscita di `start` per gli eval; nessun evento); sezione 9: chiusi i due rinvii «A B3-bis» (forma del punto unico: decisione 1; `test_real_markers_not_in_tollgate_bin`: invariato, host in `templates/models.toml`), più i minori rinviati che riguardano B4-B8; una sezione «Prove di B3-bis» con ogni riga della tabella «Copertura» e il test o l'evidenza che la prova.
- [ ] **Step 3: Progetto di B.** Riga di avanzamento: «B1, B2, B3 e B3-bis eseguite».
- [ ] **Step 4: Suite e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi (`tests/test_docs.py` compreso); commit «tollgate B3-bis: spec rev 30, progetto e piano principale di B».

---

## Copertura: punti del progetto e del piano principale destinati a B3-bis → task

| Punto | Task |
|---|---|
| Progetto 9: sentinella sul computer dell'utente, all'avvio di un lavoro, chiave nell'ambiente, niente segreti su GitHub né job programmati, hook senza rete | 2, 3, 4; decisioni 4, 6; Global Constraints |
| Progetto 9: fornitori Anthropic (`GET /v1/models`) e Gemini (`models.list`) | 1, 2; «Fatti verificati» |
| Progetto 9 (scelta del 1° novembre ripresa nel brief): OpenAI e OpenRouter se le loro pagine danno un elenco | 1, 2; «Fatti verificati» (entrambi lo danno) |
| Progetto 9: avviso per un modello stabile più nuovo della stessa famiglia | 1 (decisione 3), 3 |
| Progetto 9: avviso per un modello in uso che sta per essere ritirato | 1 (decisione 3), 3 |
| Progetto 9, «solo modelli stabili» | 1 (`test_gemini_newer_stable_only`, `test_anthropic_deprecated_newer_not_from_deprecated`) |
| Progetto 10: ciò che l'elenco non dà si salta e si dice | 1 (`test_gemini_retirement_not_checked_line`, `test_openai_shutdown_and_not_checked`, `test_openrouter_expiration_and_not_checked`) |
| Progetto 10: una prova vera | 7 |
| Progetto 10: pulizia di `/tmp` | 5; 7, Step 1 |
| Piano principale, sezione 9, «A B3-bis»: forma del punto unico | 3; decisione 1 |
| Piano principale, sezione 9, «A B3-bis»: `test_real_markers_not_in_tollgate_bin` | 2 (`test_real_providers_not_installed`); decisione 9 |
| Memoria, lezione del 03/11/2026: evidenze di B2 e gh-p4 con testo di terzi | 6; decisione 11 |
| Memoria, lezione del 03/11/2026: cartelle `tollgate-test-*` in `/tmp` | 5; decisione 10 |
| Revisione della spec del nucleo | 8 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B (sezioni 9 e 10), il piano principale, la spec rev 29, il codice di `main` e il modello di B3.

| Giro | Rilievi | Esito |
|---|---|---|
