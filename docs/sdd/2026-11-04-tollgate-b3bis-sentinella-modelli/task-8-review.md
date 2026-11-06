# Task 8: revisione (34ce2c9..f202c8c)

## Aderenza

- ✅ Intestazione rev 30 e riga 30 della sezione 20 (spec:4, spec:1943): elencano le 13 decisioni, D1, D2, D4, D9, D15, D21, la prova vera con esito «nessuna chiave» e le sezioni toccate.
- ✅ Sezione 3 (albero con `templates/models.toml`, paragrafo sulla rete): verificato con `test_hooks_do_not_reach_models_net` e con grep (nessun import di `tollgate_flow` in `tollgate_hooks` e `tollgate_checks`).
- ✅ 3.1, riga `models check [--refresh]`: coincide con `bin/tollgate_core/cli.py:294-324` (codici 0/1, tre messaggi, `rifiuto: configurazione non valida`, ordine avvisi di configurazione, righe del controllo, messaggio finale; ritorna prima di `db.open_db`).
- ✅ 3.2 (rete solo dalla CLI) e 6.1 (solo lavoro nuovo, dopo `housekeeping.run`, `show_cache=False`): coincidono con `bin/tollgate_flow/start.py:511-513`.
- ✅ 11.4: tabella (`[models] files`, `models_check`), `[models] files` con D2 e D9 (provato eseguendo `config.load_config_text`: `./a`, `a//b`, `a/`, `../x`, `a*` tolte con avviso, `[id]/x` tenuta; `files="x"` e `models_check="yes"` danno `ConfigError`), dati dei fornitori, chiavi e ordine delle variabili, nomi e confronto, client stretto (`OpenerDirector` con `UnknownHandler`, 5 s, 8 MiB, 10 pagine, `DEADLINE_S` 20, FetchError fuori da `except`), cache (futuro, convalida prima di scrivere, riga della cache fresca), forme delle righe, ordine, `MAX_LINES` 12, 256 KiB, 8000 byte: tutto riscontrato in `models_check.py`, `modelsfetch.py`, `templates/models.toml`, `config.py`.
- ✅ Sezione 14: paragrafo su `tests/run` coincide con `tests/run:5-7` (trap con `chmod ... || true; rm -rf ... || true`, `TMPDIR` di corsa). Scostamento dichiarato e motivato (D1 non aveva sede).
- ✅ Sezione 1.2 e `docs/uso/limiti.md:105-109` (D15, stesso commit): limite sulla chiave nell'ambiente presente in entrambi; `python3 -B -m unittest tests.test_docs` OK (7 test, compreso `test_limits_match_spec_1_2`). D2 nella decisione 1 della spec: «tipo sbagliato = errore di configurazione, non avviso».
- ✅ Sezione 16: tabella con URL e data, Step 0 (a) «non confermato», (b) `OPENROUTER_API_KEY`, (c) `gpt-`, ruling D20 (lifecycle scalare). La riga della prova vera non abbellisce: «nessuna chiave», 1 tentativo su 3, 0 richieste, 0,28 s, «non provati dal vivo» elencati; coincide con `docs/verifiche/2026-11-04-b3bis-prova-modelli.md` ed `evidenze/b3bis/*.txt`. I modelli scelti coincidono con `spikes/b3bis/progetto/ai/models.py`. «Ancora da verificare» estesa (rete con chiave, alias, proxy).
- ✅ Progetto di B: riga di avanzamento corretta (`...-b-profili-design.md:4`).
- ✅ Piano principale: stato in testa (frase «merge in attesa» di B3 corretta in «unita su `main` il 03/11/2026»; 3561 test, skipped 5/3, coincide con `task-8-suite.out`), riga B3-bis in sezione 2, riga B3-bis → B8 in sezione 3, i due rinvii «A B3-bis» marcati chiusi (decisione 1; `test_real_markers_not_in_tollgate_bin` invariato, host in `templates/models.toml`), sezione 12 «Prove di B3-bis» con tutte e 13 le righe della tabella «Copertura» più «Prove oltre la tabella». Controllo con script: ogni `test_…` citato esiste nel file indicato (nessun mancante). Il triage dei minori rinviati (`progress.md`, righe `minor (deferred)`) conferma che nessuno riguarda B4-B8.
- ✅ Nessun nome utente, host personale, percorso del workspace o testo copiato nelle righe aggiunte (grep sul diff vuoto). Nessuna chiave. Righe 9 e 10 della sezione 4 del piano e correzione della riga di B2: aggiunte oltre il brief ma corrette e coerenti (B2 aveva lo stesso errore di B3).
- ⚠️ Non verificabile senza rete: gli URL della sezione 16 (provengono da `fatti-verificati.md` e dal ledger, quindi coerenti con ciò che il controller ha letto).

## Punti di forza

- La spec descrive il codice reale fin nei dettagli scomodi (ordine dei controlli in `check`, riga «cache» nascosta solo se fresca, `cat-file` che decide dal codice d'uscita, `UnknownHandler`), e dichiara i costi.
- La riga della prova vera non nasconde che la rete non è stata provata; lo ripete in 16, nel piano (stato e sezione 12) e nel rapporto.
- Sezione 12 del piano: ogni prova ha un nome di test o un'evidenza esistenti, e le parzialità sono scritte (rete, storia di git, cartelle `tmp*`).
- Il dubbio su `docs/uso/comandi.md` è stato visto e la spec dice la forma giusta («ha il codice ma non `templates/models.toml`»).

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor
1. `docs/uso/comandi.md:196` dice che la copia del gate in `.github/tollgate/` «non lo contiene»; la spec 3.1 (riga di `models check`) dice, correttamente per `bin/tollgate_gate/install.py:97-98` (copia tutto `bin/`, non `templates/`), che ha il codice ma non il file dei fornitori. I due testi si contraddicono alla lettera. Correzione: «quella non ha il file dei fornitori e il comando darebbe "controllo non riuscito"». Già in ledger (riga 120); è fuori dai file del task.
2. Spec 11.4 («Cache»): «`models check --refresh` la ignora». Il codice (`modelsfetch.py:cached_pages`) con `--refresh` e rete fallita usa comunque la cache, anche scaduta (ruling del ledger «cache scaduta usata a rete fallita»). Aggiungere «come ripiego a rete fallita» in una riga. Anche la decisione 3 (un `claude-…` che manca dall'elenco ricade nella regola dei nomi non presenti, perché i `retired` non si chiedono) e il costo degli alias `~` di OpenRouter sono omessi dalla spec: rifiniture.
3. Spec sezione 11.4: l'URL di OpenRouter nella riga è la pagina `…/guides/overview/models.md` di `templates/models.toml`; nulla da correggere, ma la spec non la nomina e dice solo «la pagina dei modelli di OpenRouter». Solo promemoria.

## Valutazione

**Qualità del task:** Approvato

**Motivo:** La rev 30 e il piano principale descrivono ciò che il codice del ramo fa (verificato su `models_check.py`, `modelsfetch.py`, `templates/models.toml`, `cli.py`, `config.py`, `start.py`, `tests/run`), riportano le 13 decisioni e i ruling richiesti, includono D15/D2 in spec e `limiti.md`, non abbelliscono la prova vera e collegano ogni riga di copertura a un test esistente. Restano solo rifiniture.
