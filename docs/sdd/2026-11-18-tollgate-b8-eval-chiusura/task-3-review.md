# Revisione del Task 3 (B8): kit degli eval, campagne, permessi web, pulizia delle trace, conteggi

Pacchetto: `review-6988775..7618110.diff`. Letti: regole del revisore, brief con decisioni del controller (D4, D5, D6, D7, D9, D12, D16) e cautele, decisioni 6, 7, 9, 10, vincoli globali, punti 2, 4, 5 del focus, fatti verificati, report. Una sola verifica eseguita: una sonda in sola lettura su `scrub._fetches_domain` (nessuna rete, nessuna scrittura) per il rilievo I1.

## Aderenza

- ✅ Campagne (decisione 6, D5, D7): `cost.py:30-37` (`Campaign`, `CAMPAIGNS` p5 80 / b8 20), `budget_path(campaign="b8")` senza argomenti, `campaign` in coda a `spent/remaining/reserve/add`, tetto della campagna anche con `path` (`cost.py` `remaining`), `--campagna` per ogni sottocomando via `_take_option` (nome sconosciuto: 64), `info` a due righe. `run.sh` passa sempre `--campagna "$campaign"` a `cost.py` (funzione `cost`, incluse `table` e `plugin-check`), legge cartella e tetto da `cost.py info` e i domini da `scrub.py domains`; `cap="$(cost remaining)"` è il solo valore di `--max-cost-usd`. Nessuna cartella né cifra di campagna in `run.sh` (lo asseriscono `test_campaign_folder_follows_cost_info` e `test_grants_follow_web_domains`). Un eval di B8 non può scrivere nel registro di P5 né calcolare il residuo su 80.
- ✅ Test di P5 spostati su `--campagna p5` / `campaign="p5"` con gli stessi numeri (gli otto di D5: 49,50; 75,00; 60,00; 58,75; 80,0; 79,87; 77,5). `test_p5_registry_untouched_by_b8` verifica il registro e la cartella di P5 byte per byte su tre invocazioni a secco, e che quello di B8 resti la sola intestazione. Nessun numero atteso è stato cambiato.
- ✅ Permessi web (decisione 6): `Bash Write Edit "WebFetch(domain:…)"… WebSearch` per ogni campagna diversa da `p5`, `p5` com'era. `CASE_TOOLS` non toccato.
- ✅ Prova a secco `fetch` (decisione 7, D9): `test_eval_cases.py` `_do_fetch` fa `_use("WebFetch", {"url"})`, `PostToolUse` con `{"code": 200, "result": …}`, `_result`; `FetchStepTest` legge la tabella `lookups` dello stato vero (non un mock) e trova `Lookup("fetch", url normalizzato)`. Il matcher di `hooks/hooks.json` include `WebFetch` e `WebSearch`: la lettura che la prova registra è quella che tollgate registrerebbe.
- ✅ `strip_web_results` (D4): ogni risultato di `WebFetch`/`WebSearch`, di qualsiasi lunghezza, in `tool_result` e in `tool_use_result` (stringhe annidate comprese), chiavi/numeri/booleani/`code` restano, segnaposto con indirizzo o interrogazione, idempotente, subagenti coperti (`parent_tool_use_id`), 8 trace di P5 invariate.
- ✅ Anonimizzazione (decisione 9, D6): `.db` prima (colonne `typeof = 'text'`, `VACUUM`, checkpoint `TRUNCATE`, `integrity_check`), poi i file UTF-8 esclusi `*.db*`; valori troppo corti o riservati: uscita 2 senza toccare niente; i valori non si stampano (test della CLI); in TEST_MODE `run.sh` non chiama `id` né `hostname` e le due variabili finte sono rifiutate fuori da TEST_MODE (test esteso). Anonimizza anche il ramo dell'uscita 3 (con test) e dà 5 se fallisce. I test non dipendono dall'utente o dall'host della macchina (`utente-prova`, `macchina-prova`).
- ✅ `research_counts` (decisione 10, D16): `mode=ro&immutable=1` con URI da `as_uri()` (spazi nel percorso ok), `-wal` rifiutato, nessuna tabella: zero, corse senza stato elencate sotto la tabella. `test_research_counts_leaves_no_files` confronta nomi, dimensioni e `mtime` prima e dopo, anche tramite `main`. Verificati sul codice i nomi: `research_note` con `data.ok` (`research_cmd.py:99`), `research_reminder` e `research_switch_unreadable` (`research_gate.py:150-154`), `veto` con `rule="research_gate"` (`research_gate.py:140`, `runner.py:330`), `lookups.kind` (CHECK di `db.py:189`).
- ✅ Docs (D12): nessun link al rapporto di B8; campagne, tetto, permessi web, uscita 5, pulizia. `.gitignore` e `budget.tsv` con la sola intestazione.
- ⚠️ Non verificabile dal diff: il comportamento di `hostname`/`id -un` fuori da TEST_MODE (corsa vera); l'anonimizzazione su un database con lo schema vero di tollgate (il test usa una tabella `events` sintetica; `research_counts` usa invece lo schema vero). Le `UPDATE` per valore su colonne con `UNIQUE`/`CHECK` (`db.py:107,115`) non hanno rischio concreto qui (stesso valore vecchio, stesso nuovo), e un errore chiuderebbe in 5, quindi fail-closed.
- ⚠️ TDD: il report dichiara codice prima dei test e un RED ricostruito su `git archive` di HEAD. Il RED mostrato (`ImportError` del modulo assente, `_do_fetch` assente) prova solo che i test nuovi non girano senza il codice, non che ciascuna asserzione sia mutante. Giudico sui test (vedi punti di forza e I1): sono per lo più comportamentali, con un buco (I1).

## Punti di forza

- Il confine «un eval di B8 non tocca P5» è chiuso in tre punti indipendenti: `budget_path` per campagna, il tetto da `CAMPAIGNS` anche con `path`, e `run.sh` che non porta più cifre o cartelle. Il test sul registro vero di P5 è byte per byte.
- La pulizia è composta nell'ordine voluto e fallisce chiusa (5), con test sull'uscita 5 per `strip-web` e per l'anonimizzatore, e sul ramo dell'uscita 3.
- `strip_web_results` riusa i punti unici di `flowreg` (`_placeholder`, `_content_text`, `_swap_saved`, `PAGE_PLACEHOLDER`) invece di duplicarli, ed è idempotente.
- `research_counts` non crea file: provato con uno stato vero in WAL e un confronto di `mtime`.
- Il test dell'anonimizzatore copre WAL vivo, `-wal`/`-shm` spariti, BLOB intatto, pagine libere (`VACUUM`), parola intera (`macchina-prova-2`), simlink ignorato, file binario ignorato, rilancio senza cambi.

## Rilievi

### Critical
Nessuno.

### Important

**I1. `strip_bash_web` non copre `python3`/`node` lanciati con uno script su stdin (heredoc o here-string).** `evals/scrub.py` `_fetches_domain` giudica solo `argv[1:]` dopo `bash.parse`, e il corpo di un heredoc non è in `argv`. Sonda eseguita (sola lettura) sui domini concessi:
- `python3 - <<'EOF' … urlopen('https://vercel.com/docs') … EOF` → `None` (non sostituito);
- `python3 <<< "import urllib.request; urlopen('https://vercel.com')"` → `None`;
- `python3 fetch.py` (script scritto con `Write`) → `None`.
Sono il modo normale in cui un modello lancia Python inline, e `WebFetch(domain:…)` apre la rete della shell a quei domini (documentazione, riga 355). Il risultato (testo di terzi) resta nella trace committata, e `togli-pagine` non lo prende se non è lungo o non nomina una copia salvata. Il controllo del controller (`grep -raF` dei due valori e verifica a mano) non cerca testo di pagine. Il test `test_strip_bash_web` copre `python3 -c` ma non lo stdin. Correzione: per i programmi `python3`/`python`/`node` (e anche `bash -s`/`sh -s`, dove si può) guardare, oltre agli `argv`, il testo grezzo del comando quando c'è un heredoc/here-string/`-`, escludendo sempre `research submit`; più i casi nel test (heredoc, here-string, nota con heredoc che nomina il dominio: invariata). La decisione 9 dice «programma … e nomina uno dei domini concessi»: un heredoc lo nomina.

### Minor

**M1. Residui non coperti dalla pulizia, da tenere nel controllo del controller.** (a) `curl -o f URL` in una chiamata e `cat f` in un'altra: la seconda non nomina il dominio e il suo risultato resta. (b) Pagine salvate nel workspace copiato (`runs/*/cwd`, fino a 300k per file, `run.sh` `copy_one_run`): `anonymize` non le tocca per questo e nessun altro passo guarda `cwd`. (c) `xargs curl`, `U=… ; curl $U`, `perl`/`ruby`/`deno` non sono nell'elenco `FETCH_PROGRAMS`. Sono limiti dichiarati dall'elenco di programmi della decisione 9; se si vuole chiuderli in modo robusto, la regola «qualunque `Bash` il cui testo nomina un dominio concesso, tranne `research submit` e `sed` sulla nota» copre (a)-(c) con meno codice. Non blocca il task. Il controller li metta nella verifica a mano del rapporto.

**M2. `_rewrite` rilegge con `errors="replace"`** (`scrub.py` `_rewrite`): se la trace ha byte non UTF-8 in righe non toccate, il file riscritto li cambia in U+FFFD. Innocuo per le evidenze, ma è una modifica silenziosa; `errors="surrogateescape"` in lettura e scrittura la evita.

**M3. `research_counts.table`** propaga `WalError` per una sola corsa e butta via l'intera tabella (`nota.md` resta vuoto, `run.sh` stampa solo un avviso). Con l'ordine di `run.sh` il `-wal` è già tolto dall'anonimizzazione, quindi non succede; ma il messaggio non dice quale corsa. Facoltativo: riportare il nome della corsa nell'errore.

**M4. Test dell'anonimizzatore su schema sintetico** (`tests/test_eval_run.py` `AnonymizeTest.make_db`, `FAKE_STATE_DB`): non passa mai da `db.open_db`. Un caso con lo stato vero (come `ResearchCountsTest.make_state`) darebbe la prova sullo schema reale (⚠️ sopra).

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** campagne, tetti, registro di P5, permessi web, passo `fetch`, `strip_web_results`, anonimizzazione e conteggi sono costruiti bene e coperti da test comportamentali, e le decisioni D4-D16 sono rispettate. Resta un buco concreto nella lente «testo di terzi nelle evidenze»: il risultato di un `python3`/`node` con script su stdin che legge un dominio concesso non viene tolto (I1), e i test non lo coprono.
