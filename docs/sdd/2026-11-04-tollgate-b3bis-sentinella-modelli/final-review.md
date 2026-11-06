# Revisione finale del ramo B3-bis (b3d1549..f202c8c)

Revisore a contesto pulito, sola lettura. Letti: brief, decisioni 1-13, Review Focus, Copertura, Global Constraints, fatti verificati, `final-rulings.md`, `final-deferred.md`, il rapporto della prova vera, i sorgenti nuovi interi (`bin/tollgate_analysis/models.py`, `bin/tollgate_flow/modelsfetch.py`, `bin/tollgate_flow/models_check.py`, `templates/models.toml`, `spikes/b3bis/models-prova.sh`, `tests/run`, `tests/test_run_script.py`), i diff di `cli.py`, `config.py`, `git.py`, `start.py`, `helpers.py`, `flowreg.py`, `skills/start/SKILL.md`, `docs/uso/*.md` e le parti nuove della spec rev 30. Sonde con `python3 -B` in `/home/USER/.claude/jobs/e28b8553/tmp/final/` (nessuna rete, nessuna chiave). Test mirati: `tests.test_models tests.test_models_check tests.test_modelsfetch` con `PYTHONWARNINGS=error::ResourceWarning`, ambiente senza le nove variabili delle chiavi: 117 OK.

## 1. Verdetto

**Non pronto per il merge**: un rilievo Important, piccolo da correggere (una funzione e un test).

Conteggi: **Critical 0 / Important 1 / Minor 7** (più il triage di 24 voci rinviate, sezione 3).

## 2. Rilievi

### 1. Important: un modello Gemini con la modalità dopo `preview` riceve «più nuovo» verso un modello di un'altra modalità

- **Dove:** `bin/tollgate_analysis/models.py:72-75` (`gemini_family`: il ciclo si ferma al primo suffisso e butta ciò che segue); il test lo fissa a `tests/test_models.py:226` (`("gemini-3.7-flash-preview-tts", ("flash", (3, 7)))`).
- **Cosa:** la variante si chiude al primo suffisso (`preview`, `exp`, …), quindi tutto quello che viene dopo si perde, compresa la modalità. I nomi veri di Gemini mettono spesso la modalità *dopo* il suffisso: `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`, `gemini-2.0-flash-preview-image-generation`, `gemini-2.0-flash-exp-image-generation`. Tutti finiscono nella famiglia `flash` o `pro`. La decisione 3 e la spec rev 30 (11.4, «Gemini») dicono il contrario: «le modalità (`flash-tts`, `flash-image`, `flash-live`) sono varianti diverse da `flash`». Il ruling D19 ha guardato solo il lato del candidato (una `preview-tts` non viene mai proposta, perché non è stabile), non quello del modello **in uso**.
- **Scenario che fallisce (sonda):** elenco con `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`, `gemini-3-flash`, `gemini-3-pro`; nel file del progetto `"gemini-2.5-flash-preview-tts"` e `"gemini-2.5-pro-preview-tts"`. Esce
  `modelli: gemini: gemini-2.5-flash-preview-tts (…): esiste gemini-3-flash, più recente della stessa famiglia — …` (e lo stesso per `pro`). È proprio la riga che il brief chiede di cercare: un «più nuovo» sbagliato, che manda chi fa sintesi vocale verso un modello che non la fa. La skill `start` riferisce la riga all'utente come consiglio di cambio.
- **Come correggere:** in `gemini_family` non fermarsi al primo suffisso. Si tolgono i soli pezzi che sono suffissi (`[0-9]{3}`, `preview`, `exp`, `experimental`, `latest`) e i pezzi solo numerici che li seguono (le date `09-2025`, `05-20`, `06-17`), e si tengono le parole che restano: `flash-preview-tts` → `flash-tts`, `flash-preview-09-2025` → `flash`, `flash-lite-preview-06-17` → `flash-lite`, `flash-exp-image-generation` → `flash-image-generation` (una famiglia a sé: nessun confronto, che è l'esito prudente). Poi si aggiorna l'attesa a `tests/test_models.py:226` (`("flash-tts", (3, 7))`) e si aggiunge un test: il modello in uso `gemini-2.5-flash-preview-tts`, con lo stabile `gemini-3-flash` nell'elenco, non dà «più recente»; con lo stabile `gemini-3-flash-tts` sì.

### 2. Minor: a scadenza finita si salta anche un fornitore con la cache fresca

- `bin/tollgate_flow/models_check.py:125`: il controllo `deadline.left() <= 0` viene **prima** di `cached_pages`, che con la cache fresca non userebbe la rete. Scenario: Anthropic non risponde e consuma i 20 s, Gemini ha la cache di un'ora fa e riceve «saltato, tempo del controllo finito» invece dei suoi avvisi (e così ogni fornitore con la cache scaduta perde il ripiego). Come correggere: passare la scadenza a `cached_pages` e controllarla solo prima della `fetch`; se il tempo è finito e c'è una cache, usarla con la riga «rete non riuscita (tempo scaduto), elenco dalla cache del …».

### 3. Minor: una risposta di forma sbagliata non ricade sulla cache valida

- `bin/tollgate_flow/modelsfetch.py:348`: con la rete riuscita ma `validate` che solleva, l'eccezione esce e il fornitore dà «elenco non letto: forma inattesa», anche quando c'è una cache leggibile (fresca con `--refresh`, oppure scaduta). La decisione 7 chiede il ripiego solo per la «richiesta fallita», quindi non è una violazione, ma un fornitore che cambia per un giorno la forma della risposta toglie avvisi che la cache darebbe. Come correggere: trattare `ModelsFormatError` come un fallimento («forma inattesa») e usare la cache se c'è.

### 4. Minor: «modelli: nessun avviso» anche quando nei file non c'è nessun nome riconosciuto

- `bin/tollgate_flow/models_check.py:117` e `bin/tollgate_core/cli.py:322-323`: con almeno una chiave e nessun letterale che corrisponde a un elenco (nomi scritti senza virgolette, costruiti a pezzi, un file sbagliato in `[models] files`, ID OpenAI della serie `o…`), `models check` stampa «modelli: nessun avviso». È una conferma che inganna, lo stesso motivo del ruling D4. Come correggere: con `found` vuoto, o senza nessuna corrispondenza in nessun elenco letto, una riga generale «modelli: nessun nome di modello riconosciuto nei file dichiarati».

### 5. Minor: il tetto di tempo scritto nei documenti è più basso del reale

- `docs/uso/comandi.md` («un tempo massimo di 20 secondi in tutto») e la spec 11.4 («20 s più al più una risoluzione»). Il timeout del socket si fissa all'apertura (`modelsfetch.py:215`): una `read` bloccata dopo la scadenza può durare fino a 5 s in più (voce già rinviata del Task 2). Come correggere: «20 s, più al più una risoluzione DNS e una lettura di 5 s» nei due testi.

### 6. Minor: la pulizia delle evidenze toglierebbe anche un'uscita di tollgate che comincia con «(tollgate:»

- `spikes/b1/flowreg.py:304` (`_hook_text`): un'uscita è di tollgate solo se `additionalContext` comincia con `tollgate:`. Il runner degli hook però mette in testa `(tollgate: controllo «…» in errore: …)` o `(tollgate: registrazione «…» non applicata: …)` quando il primo modulo fallisce (`bin/tollgate_hooks/runner.py:309`, `:323`), e quell'uscita verrebbe sostituita come «di terzi». Il testo si perde dall'evidenza, ma non esce niente di riservato, e nelle evidenze di oggi non succede: i 24 segnaposto sono i tre hook attesi, 10170, 3604 e 1129 caratteri. Come correggere: riconoscere anche il prefisso `(tollgate:`, con un caso nel test.

### 7. Minor: «senza chiave quel fornitore si salta e la riga lo dice» non vale sempre

- `docs/uso/comandi.md` (paragrafo sulle chiavi): la riga «manca la chiave» compare solo se un letterale ha la forma di `hint` (decisione 4). Un modello OpenRouter di un altro autore, o un ID OpenAI non `gpt-`, passa senza nessuna riga. Come correggere: «… e la riga lo dice, se nei file c'è un nome con la forma dei suoi modelli».

### 8. Minor: `line` vuota trattata come una famiglia (conferma del rinvio del Task 1)

- `bin/tollgate_analysis/models.py:100`: sonda con due modelli Anthropic `line: ""` e nomi diversi. Esce `a-1 (…): esiste claude-opus-9, più recente della stessa famiglia`. La documentazione dice `null` e non `""`, quindi oggi non scatta. Ma la prova con le chiavi non è stata fatta, e la correzione costa due caratteri (`_text(item.get("line")) or None`). Va nel triage sotto come «da correggere prima del merge».

## 3. Triage di `final-deferred.md`

| # | Voce | Esito |
|---|---|---|
| 1 | D22: cache con le pagine grezze (fino a 10 × 8 MiB per fornitore), non potata | **Rinviato**: gli elenchi veri pesano poche centinaia di KiB; si rivede dopo la prova con le chiavi (dimensione reale) e con `housekeeping`. |
| 2 | D25: `KeyboardInterrupt` durante il controllo lascia il lavoro senza «prossimo passo» | **Nessuna azione**: la ripresa lo completa; un Ctrl-C è voluto. |
| 3 | `line` stringa vuota dà `family=""` | **Da correggere prima del merge**: due caratteri, toglie un falso «più nuovo» (rilievo 8). |
| 4 | ID e date esterni senza tetto di lunghezza nelle righe | **Rinviato**: c'è già il tetto di `MAX_LINES`; un tetto per ID (per esempio 128, come `_LITERAL`) va con la prova vera. |
| 5 | Il parametro `literals` oscura la funzione omonima | **Nessuna azione**: firma del brief, nessun uso della funzione nel corpo. |
| 6 | `assertRaises(Exception)` troppo largo (`tests/test_models.py:343`) | **Da correggere prima del merge**: una riga (`dataclasses.FrozenInstanceError`). |
| 7 | OpenAI e OpenRouter con `stable=False` per tutti | **Nessuna azione**: `stable` lì non si usa (niente «più nuovo»); lo dicono la decisione 3 e la spec. |
| 8 | `created` confrontato come stringa | **Rinviato**: regge con l'RFC 3339 omogeneo di Anthropic; da verificare con la prova vera (forma reale di `created_at`). |
| 9 | Ogni 3xx, anche 304, diventa «redirect rifiutato» | **Nessuna azione**: il client non manda richieste condizionali, un 304 non può arrivare. |
| 10 | `no_network()` non blocca `socket.getaddrinfo` | **Da correggere prima del merge**: una patch in più in `tests/helpers.py` (e un'asserzione in `test_no_network_helper`). Basso costo, e un test sbagliato non potrà più mandare una query DNS. |
| 11 | La cache non ha un tetto complessivo | **Rinviato**, con la voce 1. |
| 12 | Una lettura bloccata può sforare la scadenza di 5 s | **Rinviato** nel codice; **da correggere prima del merge** il testo di spec e `comandi.md` (rilievo 5). |
| 13 | `_write_cache`: descrittore aperto se `os.fdopen` fallisse | **Nessuna azione**: `fdopen` su un descrittore appena creato non fallisce in pratica. |
| 14 | «… e altri 1 avvisi» | **Nessuna azione**: forma fissa della decisione 13. |
| 15 | Annotazioni `Provider` perse in `_wanted`/`_provider_lines` | **Nessuna azione**: estetica; il modulo si importa in locale apposta. |
| 16 | `assertNotIn("sk-PROVA-123", …)` mostra le righe quando fallisce | **Nessuna azione**: la chiave è finta. |
| 17 | Un SIGKILL di `tests/run` lascia una `tollgate-run-*` | **Nessuna azione**: la toglie la pulizia delle 24 ore. |
| 18 | Con una chiave nell'uscita della seconda corsa, `refresh.txt` (già controllato) resta | **Nessuna azione**: `refresh.txt` ha passato il controllo; lo script esce con 1 e non salva la seconda. |
| 19 | Il caso positivo `/tmp/tollgate-b3bis` non è coperto dai test | **Nessuna azione**: un test toccherebbe la cartella vera della prova. |
| 20 | La ricerca del valore finto esclude `repo/.git` | **Nessuna azione**: oggi non nasconde nessun caso; volendo, una riga per toglierla. |
| 21 | Nessun controllo del proprietario su `/tmp/tollgate-b3bis` | **Rinviato**: c'è un solo utente sulla macchina, e lo script ha già `umask 077`, il rifiuto dei link simbolici e `pwd -P`. Si rivede se la prova passa a un'altra macchina. |
| 22 | `comandi.md`: la copia del gate in `.github/tollgate/` «non contiene» `models check` | **Da correggere prima del merge**: una frase. Il codice c'è (si copia tutto `bin/`), manca `templates/models.toml`, e il comando lanciato da lì dà «controllo non riuscito (ProvidersError)». Va detto così. |
| 23 | Spec 11.4: `--refresh` «ignora la cache» ma con la rete fallita la usa; mancano i `retired` non richiesti e il costo degli alias `~` | **Da correggere prima del merge**: tre frasi della spec, perché la rev 30 sia fedele al codice e ai ruling. |
| 24 | La spec nomina «la pagina dei modelli di OpenRouter» senza l'URL | **Nessuna azione**: l'URL sta in `templates/models.toml`, che la spec indica come unica sede dei dati dei fornitori. |

## 4. Punti di forza

- **La chiave non esce.** `FetchError` si solleva sempre fuori dagli `except`, con testi fissi (`modelsfetch.py:246-282`, `:343-345`), quindi `__context__` e `__cause__` restano vuoti. La chiave va solo nelle intestazioni, anche per Gemini. `check` riduce ogni eccezione al nome della classe (`models_check.py:149-150`). La cache contiene solo le pagine. I test confrontano `environ is os.environ` senza stampare l'ambiente. Lo script della prova confronta i valori dentro bash e non li stampa mai. Non ho trovato altre strade.
- **Il client è stretto davvero**: un `OpenerDirector` minimo, nessun proxy, redirect rifiutati con la risposta chiusa, host fissato su ogni pagina, lettura a pezzi con tetto, scadenza unica.
- **Strati e hook puliti**: `models.py` è puro, `modelsfetch` si importa solo dentro `check`, e due test (statico e a processo) verificano che hook e controlli non lo raggiungano mai.
- **Gli stati incrociati sono pensati**: cache futura, cache illeggibile, rete fallita con la cache (anche scaduta), un fornitore che fallisce e uno che risponde, profilo `ai` senza `[models]`, componente spento, ordine dei controlli che evita righe spurie nelle copie parziali.
- **`tests/run`** ha un temporaneo per corsa con un `trap` robusto, e il codice d'uscita resta quello dei test; le tre perdite in `/tmp` sono chiuse e c'è un test per ognuna.
- **Le evidenze sono ripulite con un solo iteratore** (`_third_party`), in modo idempotente, con radici di tollgate letterali (non dipendono dal nome della cartella). I 24 segnaposto sono i tre hook di terzi attesi, più 7 blocchi di skill di terzi.
- **Il rapporto della prova è onesto**: dice chiaramente che la parte di rete non è provata dal vivo e come ripeterla con le chiavi.
