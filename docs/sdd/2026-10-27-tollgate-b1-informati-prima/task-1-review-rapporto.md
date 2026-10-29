# Revisione del rapporto delle verifiche, Task 1 (sola lettura)

## Aderenza

- Valori numerici verificati sulle evidenze e corretti: 30 eventi (`riepilogo.txt`), Claude Code 2.1.312 (`versione.txt`), costo 0,362 (0,348 + 0,014), 401.579 / 75.893 / 3.949 token, 62 s API (`claude.json`), 153 byte (`eco-esito.txt`), latenze 547,6 / 695,7 / 415,2 e 483,0 / 850,6 (`latenza.json`, ricalcolate), uscita 2 a secco (`b1v3-prova.json`), `agent_id`/`agent_type` su tutti gli strumenti del subagente e assenti solo su Skill e Agent (`hooks.jsonl`).
- Forma del rapporto: colonne `Id | Fatto | Esito | Evidenza | Conseguenza per il piano` presenti, versione di `claude` presente (riga 5), B1-V2/V3 "non determinato" con causa. Campioni: tutte le chiavi dello Step 3 (tranne `mcp_docs`, ammesso) più `grep_content_dir`, `grep_default`; ognuna con `pre` e `post`.
- Anonimizzazione: nessun `/home/<utente>`, nessuna variabile d'ambiente, nessun token. `session_id` = `SESSION-ID`, percorsi = `/home/USER/...`. Restano veri `prompt_id`, `tool_use_id`, `agent_id` (e `agent_transcript_path` anonimo): non segreti, ma sono identificativi veri (Minor 6).

## Rilievi

### Critical
Nessuno.

### Important

1. **Incoerenza tra V1 e V6 sul `Grep`.** La conseguenza di B1-V1 dice «`Grep` conta solo in modo `content` esplicito con `path` su un file» (`docs/verifiche/2026-10-27-b1-verifiche.md:14`), la ruling D15 di `progress.md` (riga 47) lo ribadisce; ma la conseguenza di B1-V6 (`verifiche.md:19`) e la ruling V6 (`progress.md` riga 52) tolgono `Grep` dal matcher di `PostToolUse`. Senza `PostToolUse` di `Grep` nessun `Grep` si registra mai: la regola di V1 e il campione `grep_content` diventano codice dormiente. Il rapporto non lo dice e non indica quanto perde la regola 3.3 (le letture con `Grep` non contano più; l'implementatore deve usare `Read`/`cat`). Va scritto in chiaro (e la decisione 4 del piano resta con una forma di lettura che nel Task 4 non esiste).
2. **V6: la soglia di 300 ms non è raggiungibile con la via breve, e il rapporto non lo conclude.** `verifiche.md:19` afferma che «la via breve risparmia la sola configurazione e il registro», cioè circa 65 ms (547,6 contro 483,0), quindi resta sopra 300 ms. La ruling lo ammette ("fa risparmiare poco", `progress.md` riga 52), ma la decisione 15 lega la soglia a Grep fuori dal matcher + via breve come se bastassero. Manca una conseguenza esplicita: o si accetta ~480 ms per ogni lettura del subagente (WebFetch/WebSearch/Read), o serve un'altra via (filtro nel wrapper `hooks/run` prima di Python, per `agent_id` assente, oppure matcher più stretto). La frase «il grosso del costo è l'avvio di Python» è una deduzione dalla serie Read, non misurata separatamente (nessuna serie "solo shell").
3. **Misura V6 rumorosa, usata come se fosse stabile.** Nella serie `post_read_no_agent` la mediana della prima metà è 522,8 ms e della seconda 403,8 ms, con minimo 309,4 e massimo 952,5 (`latenza.json`): la serie è dominata dal carico della macchina (dichiarato 3,8/8, ma non misurato durante le serie). La ruling "483 ms anche per un Read che esce prima del DB" tratta il valore come pavimento; il minimo 309 ms suggerisce che a macchina scarica il pavimento è ~310-400. Conviene dirlo e ripetere la misura a carico noto, o riportare almeno la mediana per metà.
4. **V4: il reindirizzamento non è provato dalle evidenze.** Il rapporto scrive «301 verso `.../3/library/json.html`» (`verifiche.md:8`), ma `redirect-url.txt` contiene solo l'URL e non c'è l'esito della richiesta `HEAD`. Nel `tool_response` `url` è uguale all'URL chiesto e `code` è 200: da qui non si distingue "WebFetch ha seguito un 301 e non espone l'URL finale" da "nessun reindirizzamento è avvenuto". L'esito «URL finale assente» è plausibile ma poggia su un'evidenza (la HEAD) non archiviata. Salvare l'intestazione `Location` in `evidenze/b1/`.
5. **V2: «negativo» poggia solo sul testo del subagente.** Il rapporto cita «risposta del passo 10» (`verifiche.md:15`): nel `claude.json` la risposta di context7 è il **passo 12**, non il 10 (errore di riferimento). Inoltre non c'è traccia in `hooks.jsonl` di alcun evento MCP (né `PreToolUse` né negazioni), quindi "chiede l'autenticazione" è la frase del modello («Il server richiede l'autenticazione»), non un fatto osservato dagli hook; resta aperta l'ipotesi che gli strumenti MCP fossero differiti/non esposti al subagente per altra ragione. L'affermazione "plugin dell'utente (abilitato)" viene dal contesto della sessione, non da una evidenza. Va scritto «dichiarato dal subagente» e la causa limitata a quanto visto. Anche «le voci non impediscono il lancio» è dedotta dal solo `SubagentStart` avvenuto con l'agente `lettore.md` che le contiene: corretto, ma va citato `SubagentStart` come evidenza.

### Minor

1. `verifiche.md:14`: «`PostToolUseFailure` con `tool_response` nullo»: nel JSON (`hooks.jsonl` riga 9) la chiave `tool_response` è **assente**; ci sono `error` e `is_interrupt`. Il parser del Task 4 deve usare `.get`, non aspettarsi `null`. Stessa formulazione in `progress.md` riga 38.
2. `verifiche.md:17`: «`tool_response.results[].content[]`»: gli elementi di `results` sono misti, il primo è un oggetto con `content[]` (title/url), i successivi sono stringhe di testo (`hooks.jsonl` riga 27, `samples-b1.json` `websearch`). Un parser che assume oggetti fallisce. Il campo `searchCount` esiste ed è ignorato.
3. Il rapporto non segnala che nel `tool_response` di `Grep` `files_with_matches` i percorsi sono **relativi alla cwd** (`src/app.py`) mentre `tool_input.path` è assoluto: rilevante per `research.normalize_path` (decisione 4). Aggiungere una riga.
4. V7 (`verifiche.md:20`): `README_MISSING` è marcato dal validatore come «✘ problem the plugin directory refuses», non come avviso (solo `ICON_MISSING` è `⚠`); il rapporto li chiama entrambi «avvisi». Con `--profile directory` l'esito sarebbe fallito. Irrilevante per l'esito, ma la formulazione è imprecisa. L'output non nomina mai la skill, quindi non prova che `approved` sia stato letto; la prova è solo lo heredoc dello script (`run-b1-checks.sh` ~riga 193-194). Un controllo negativo (campo in `plugin.json` o chiave assurda) renderebbe la prova più forte.
5. Etichette delle ruling in `progress.md` (righe 45-52): «D1», «D5», «D6», «D15», «D16» non coincidono con i numeri delle decisioni di `decisions.md` (il `Grep` content riguarda la decisione 4, non la 15; l'uscita anticipata la 15; il registro degli URL la 4). Allineare i riferimenti.
6. Nei campioni restano `prompt_id`, `tool_use_id`, `agent_id` veri (`samples-b1.json:19` ecc.) e in `hooks.jsonl` anche; non sono segreti, ma l'incarico chiedeva niente identificativi veri: sostituirli con segnaposto, se i test non li confrontano.
7. Il campione `Read` fallito (`PostToolUseFailure`) non è in `samples-b1.json`, mentre la decisione 4 («né `PostToolUseFailure` di `Read`») dipende dalla sua forma. Aggiungere `read_missing` con `error`.
8. La ruling V1 estende l'uscita anticipata a `mcp__*` senza `agent_id` e scrive «agent_id c'è sempre» (`progress.md` righe 45-46), mentre per MCP l'`agent_id` è «non determinato» (V3). Innocuo (nessun MCP agli implementatori) ma l'affermazione supera l'evidenza.
9. Brief Step 4: V4 non obbliga una ruling, ma V6 sì ed esiste; manca invece una ruling esplicita per «B1-V1 positivo → uscita anticipata» come dal brief (c'è, riga 46, ok). Manca il nome della costante `research.ATTRIBUTE_UNNAMED = True` del brief: la ruling usa `ATTRIBUTE_UNNAMED_TOOLS` (frozenset vuoto), scelta ragionevole ma divergente dal testo del brief; segnalare la deviazione.

## Coerenza con Step 4 e decisioni 4-8, 15

- V1 positivo → nessun ripiego di attribuzione, uscita anticipata (decisione 15, B1-V1): coerente. Decisione 4: `Grep` default = `files_with_matches` non conta, `content` su cartella non conta (`filenames` vuoto): coerente con l'evidenza.
- V2 negativo → nessuna voce MCP in `implementer.md`, `DOC_MCP_TOOLS` resta (decisioni 6-7, Step 4): coerente con il brief; scelta giusta anche se l'evidenza è debole (rilievo 5).
- V4: si registra solo l'URL chiesto (decisione 4): coerente. Rischio dichiarato nel costo della ruling.
- V5 positivo: nessun `--file` (decisione 1): coerente e ben provato.
- V6 > 300 ms → Grep fuori dal matcher + via breve (decisione 15): applicato alla lettera, ma contraddice la ruling `Grep` di V1 (rilievo 1) e non raggiunge la soglia (rilievo 2).
- V7 positivo → `approved` nel frontmatter (decisione 8): coerente.
- "Un esito ottenuto con lo strumento negato è non determinato": rispettato (`permission_denials: []`).

## Valutazione

Rapporto accurato nei numeri e fedele alle evidenze; forma e campioni conformi, anonimizzazione buona. Da correggere prima del Task 2: l'incoerenza V1/V6 sul `Grep` (1), la conclusione mancante sulla soglia di 300 ms (2), la prova della redirect (4) e il riferimento errato «passo 10» con la formulazione di V2 (5). I Minor sono correzioni di testo o di campione. Nessun blocco.
