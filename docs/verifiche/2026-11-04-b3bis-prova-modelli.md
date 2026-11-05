# B3-bis: prova vera del controllo dei modelli

Data: 5 novembre 2026 (piano del 4 novembre). Piano: B3-bis (sentinella dei modelli), Task 7, Step 6 e 7. La prova lancia `tollgate models check` su un repo di prova, con l'ambiente dell'utente così com'è, due volte: la prima con `--refresh`, la seconda senza (cache).

- Versioni: Claude Code `2.1.318` (solo come ambiente: la prova non lancia `claude`), Python `3.11.16`, git della macchina.
- Script: `spikes/b3bis/models-prova.sh` (modi `controlla`, `prepara`, `prova`), con le predefinite: `B3BIS_DIR=/tmp/tollgate-b3bis`, `B3BIS_PY=python3.11`, `B3BIS_TOLLGATE=<plugin>/bin/tollgate`.
- Progetto di prova: `spikes/b3bis/progetto/` (`tollgate.toml` con `[models] files = ["ai/models.py"]`; in `ai/models.py` un modello non aggiornato per Anthropic, Gemini e OpenAI, ciascuno con la pagina ufficiale e la data). `origin` nudo locale, stato di prova con la sentinella in `/tmp/tollgate-b3bis/state`.
- Evidenze: `docs/verifiche/evidenze/b3bis/refresh.txt` (prima corsa) e `cache.txt` (seconda corsa).
- Chi ha fatto cosa: script e test dell'implementatore; scelta dei modelli, esecuzione e rapporto del controller.

## Esito

**Nessun fornitore provato in rete: nell'ambiente della sessione non c'era nessuna chiave.** `controlla` ha dato «non impostata» per tutte e nove le variabili di `templates/models.toml` (le quattro dedicate `TOLLGATE_MODELS_*_KEY` e `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`). Lo script guarda solo **se** una variabile è impostata, mai il valore.

| Corsa | Uscita | Righe | Rete |
|---|---|---|---|
| `models check --refresh` | 0 | una: «nessuna chiave nell'ambiente: imposta» le quattro variabili dedicate | nessuna richiesta |
| `models check` | 0 | la stessa riga | nessuna richiesta |

Le righe sono quelle attese dalla decisione 4 del piano per il caso «`[models] files` non vuoto e nessuna chiave»: una sola riga che nomina le quattro variabili dedicate, nessuna rete. Dopo le due corse la cartella di stato contiene solo la sentinella `.tollgate-test`: niente cache (giusto, senza elenchi letti) e niente database (`models check` non apre il DB, decisione 8).

- Tentativi: 2, ciascuno completo da solo. Il primo il 5 novembre alle 3.58; il secondo alle 6.09, dopo le correzioni della revisione finale che toccano `models_check` (stesso ambiente, nessuna chiave), con uscite identiche alla prima. L'esito **non è composito**.
- Tempi: le due corse insieme 0,28 s.
- Richieste di rete verso i fornitori: 0. Nessun modello usato, nessun token.

## Cosa la prova dimostra e cosa no

Dimostra, sul repo vero e con il comando vero: la lettura di `tollgate.toml` e di `ai/models.py` da `origin/main`, il percorso «nessuna chiave», l'uscita 0, nessun file scritto oltre la sentinella, l'assenza delle chiavi nelle uscite (controllo dello script).

**Non dimostra** la parte di rete: la forma vera delle risposte dei quattro elenchi, la paginazione vera, le intestazioni (`Authorization`, `x-goog-api-key`, `anthropic-version`), gli avvisi «più recente della stessa famiglia» e «ritiro», la cache del secondo giro. Queste parti sono provate solo dai test con un `opener` finto (`tests/test_modelsfetch.py`, `tests/test_models_check.py`, `tests/test_models.py`), con pagine costruite nei test sulla forma documentata.

Righe attese se la prova si ripete con le chiavi (dai modelli di `ai/models.py`):

- Anthropic: `claude-sonnet-5` → «esiste claude-sonnet-5-5, più recente della stessa famiglia»; `claude-sonnet-4-5-20250929` → «deprecato, ritiro previsto il 2026-11-30».
- Gemini: `gemini-3.1-flash-lite` → «esiste gemini-3.5-flash-lite, …», più una riga «ritiro non controllato».
- OpenAI: `gpt-4.1-2025-04-14` → «ritiro il 2027-01-14», più una riga «più nuovo non controllato».
- OpenRouter: nessun modello nel file (senza chiave non si è potuto verificare un ID con data di ritiro).
- Seconda corsa: «elenco dalla cache del <data>» per ogni fornitore con chiave, nessuna rete.

## Come ripeterla con le chiavi

Basta mettere nell'ambiente, prima di avviare la sessione, le variabili dedicate dei fornitori di cui si ha una chiave (per Anthropic `TOLLGATE_MODELS_ANTHROPIC_KEY`, non `ANTHROPIC_API_KEY`, che farebbe usare a Claude Code la chiave al posto dell'abbonamento), poi:

```
bash spikes/b3bis/models-prova.sh controlla
bash spikes/b3bis/models-prova.sh prepara
bash spikes/b3bis/models-prova.sh prova
```

Costo: una richiesta di elenco per fornitore e per pagina, nessun token. Le pagine dei fornitori non dicono che la richiesta sia gratuita.

## Limiti (decisione 3)

- Gemini: l'elenco non ha date di ritiro: il ritiro non si controlla.
- OpenAI e OpenRouter: l'elenco non dice la famiglia: «più nuovo» non si controlla.
- Un nome di modello costruito a pezzi nel codice, o scritto senza virgolette (`.env`, YAML), non si vede.

## Evidenze

Le due uscite sono state salvate dallo script solo dopo il suo controllo che non contenessero il valore di una variabile di chiave (nessuna era impostata). Prima del commit: `grep` del nome utente, dell'host e delle forme di token (`sk-…`, `ghp_…`, `github_pat_…`, `AIza…`) sulle evidenze e su questo rapporto, senza risultati.
