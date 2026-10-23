# Revisione Task 10 (aad7df7): `gate sentinel`, `tollgate/base` in `detect`, issue di sentinel paginate

### Aderenza
- ✅ `unverified`/`run`/`publish`/CLI `sentinel --event [--publish]` come da brief; i parametri in più (`default_branch`, `attempts`, `wait`, `sleep`) sono opzionali e non rompono la firma (`sentinel.py:117-120`).
- ✅ Decisione 16: solo PR con `merged_at` e `base.ref` = predefinito (`sentinel.py:78-79`); ultimo stato per contesto, dal più recente (`sentinel.py:55-59`; `github.statuses` è paginato e in ordine inverso cronologico, `github.py:141`); `creator.login` controllato (`sentinel.py:68`); elenco vuoto riletto 3 volte con attesa iniettabile (V5); unica issue riusata, la più vecchia se più d'una (`github.py:report_sentinel`); testo non fidato escluso (nel corpo solo SHA, numeri di PR, nomi di contesto e stati) e passato da file; descrizione dello stato troncata a 140 da `set_status` (`github.py:132`).
- ✅ Prima installazione (`sentinel.py:36-47`), `before` tutto zeri, componente spento (`run`: letto da `after`), altro ramo o cancellazione: tutti coperti da test.
- ✅ Strati: `tollgate_flow` può importare `tollgate_gate` (global-constraints); `tollgate_gate.github` non importa strati superiori; `test_layers` non lo vieta. `gh.sentinel_issues` resta la stessa forma (`number`, `title`, `url`) che `start.py` legge, e `test_start.py` è riscritto (D12).
- ✅ `--publish` fuori da Actions rifiutato, abbreviazioni rifiutate.
- ⚠️ Non verificabile qui: che `tollgate-sentinel.yml` faccia checkout con `fetch-depth: 0` (il modello del workflow non esiste ancora; è un Task successivo) e che `tollgate-base` chiami `base-ids --publish` anche quando la cache dell'albero è già presente (in quel caso `compute` non gira e `tollgate/base` non verrebbe scritto sul commit).

### Punti di forza
- Funzioni di lettura iniettate: i test di `unverified` non toccano GitHub né `sleep` vero.
- Test del caso incrociato `gate evaluate` → `gate sentinel` e dello stato scritto da un login diverso dopo `evaluate`: chiudono davvero Review Focus 4.
- `fakegh` allineato al jq reale (scarta le righe `pull_request`), così il test di start e quello di sentinel non passano per caso.
- Report onesto sulle scelte, che hanno tutte un test.

### Rilievi

**Important**

1. `bin/tollgate_gate/sentinel.py:25-34` (`_commits`): il push forzato è fail-open in due modi, e il brief chiede di segnalare anche la sola riscrittura.
   - `before` presente ma non antenato di `after` (storia riscritta) o `after` antenato di `before` (ritorno indietro del ramo): `rev-list before..after` è vuoto o parziale e **non esce alcun segnale**. Un `git push --force origin <vecchio-sha>` da amministratore passa senza stato né issue, mentre la spec (9.1, riga `tollgate-sentinel`) dice che in `protected` il job «intercetta le forzature degli amministratori».
   - `before` assente (caso dichiarato dall'implementatore): si guarda solo `after`; i commit intermedi mai passati da PR restano non controllati. Non è fail-closed. Lo stesso accade se il checkout è superficiale (con `fetch-depth` 1 ogni push normale con più commit ricade qui).
   - Correzione: se `before` non è tutto zeri e `git merge-base --is-ancestor before after` è falso (o `before` non risolvibile), aggiungere un motivo esplicito per `after` («push forzato: intervallo non calcolabile») in aggiunta ai controlli per PR, quindi stato rosso e commento. Per `before` assente, in alternativa, un `git fetch` mirato di `before` (richiede il token nel workflow). Test: ritorno indietro, storia riscritta, `before` ignoto con `after` verde (oggi `test_unknown_before_checks_only_after` asserisce solo il comportamento permissivo).
   - Se il modello del workflow userà `fetch-depth: 0` il caso superficiale sparisce, ma i due casi sopra restano.

2. `bin/tollgate_gate/sentinel.py:68` (`ghcli.BOT_LOGINS`): la costante contiene `github-actions[bot]` **e** `github-actions` (`ghcli.py:22`, pensata per i commenti GraphQL). Per gli stati REST il login legittimo è solo `github-actions[bot]` (V6, decisione 5/16). Il nome senza parentesi è un normale nome utente: chi lo possiede, o un account con quel login in un'organizzazione, scriverebbe stati accettati come verificati. La sentinella è il controllo di fiducia, quindi va stretta. Correzione: costante dedicata `STATUS_BOT = "github-actions[bot]"` e test con `creator.login = "github-actions"` → non fidato (oggi `test_status_from_user_token_not_trusted` usa solo `mario`).

**Minor**

3. `sentinel.py:164-169` e `baseids.py:publish`: l'issue si scrive prima degli stati rossi. Se `report_sentinel` fallisce (GhError → exit 1) nessun commit riceve `tollgate/sentinel` rosso; se uno `set_status` fallisce a metà, il rilancio del job duplica il commento. Meglio scrivere prima gli stati (il segnale che `start` e le regole di ramo leggono) e poi l'issue, oppure assicurare l'idempotenza.
4. `sentinel.py:_commit_problem`: con N commit non verificati il job attende fino a 10 s per ciascuno (due attese da 5 s); un push diretto di molti commit è lento ma non sbagliato. Si potrebbe rileggere solo i commit con elenco vuoto dopo un'unica attesa comune.
5. `tests/test_gh.py` `test_sentinel_issues_paginated`: il `gh` finto non pagina davvero, quindi il test asserisce `--paginate` e l'assenza di `--limit` più che il ritrovamento oltre la pagina; accettabile, ma il nome promette più di quel che prova.
6. `baseids.publish`: in `detect` `tollgate/base` è rosso solo per i comandi `red`. Scelta accettabile (spec: «se la suite fallisce»); i comandi `unverified` non sono visibili neppure nella descrizione dello stato. Se serve, aggiungere il conteggio nella descrizione.
7. `sentinel.run` richiede `GITHUB_REPOSITORY` anche senza `--publish` (dichiarato nel report): coerente, ma va scritto nell'`--help`.

Giudizio sulle scelte dichiarate: `before` assente solo `after`: **non** sufficiente (rilievo 1). Una PR unita e verificata basta: corretto (V5b elenca anche PR impilate, ma qui si filtra per `merged_at` e base). `tollgate/base` rosso solo con `red`: accettabile. `default_branch` in più: ok. Import `tollgate_flow.gh` → `tollgate_gate.github`: ammesso.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** la logica per PR e stati è solida e ben testata, ma il push forzato non produce segnale in due casi (ritorno indietro o riscrittura, `before` assente con intermedi), e la fiducia nel bot accetta anche il login `github-actions` senza `[bot]`. Due correzioni piccole e localizzate.
