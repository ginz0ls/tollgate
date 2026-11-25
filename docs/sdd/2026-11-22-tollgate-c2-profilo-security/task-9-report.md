# Task 9, Step 2-3: report dell'implementatore (opus)

Status: DONE_WITH_CONCERNS (i concern sono le differenze con il ledger, sotto; nessun blocco).
Commit: `d9639cc` «tollgate C2: prova reale L2 con il profilo security e lo specialista finale» (solo `docs/verifiche/2026-11-22-c2-prova-flusso.md` e `docs/verifiche/evidenze/c2/flusso/`, 69 file).

## Cosa ho fatto
- Letto il brief, le regole, le righe «Prova:»/«Ruling:» di `progress.md` dal Task 9 in poi, il rapporto di B7, le decisioni 10, 14, 16, 20, carry (Task 8 D2/D9, Task 10), la sezione «Per il controller» della review del Task 8, i file del registro, `spec-diff.txt`, `piano-diff.txt` e gli stream (solo con script Python in `/tmp/tollgate-t9/`, poi cancellata; mai per intero).
- Scritto il rapporto `docs/verifiche/2026-11-22-c2-prova-flusso.md` sul modello di B7, con `Esito: riuscita` su una riga a sé in testa. Ha in più una sezione «Differenze con il registro del controller».
- Nessuna esecuzione di `claude`, dello script della prova, nessuna rete, nessun subagente; `/tmp/tollgate-b1` non toccato; nessun file di `~/.claude` letto (i nomi di terzi li ho presi dalla riga `init` degli stream stessi).

## Ripulitura (conteggi, mai i valori)
- Id di sessione: 6 id reali → `SESSIONE-1` … `SESSIONE-6` (numerazione di `trascrizioni.txt`), 4.433 occorrenze (stream, `events.jsonl`, `eventi-c1.jsonl`); nessuna cartella aveva un id nel nome.
- Percorso assoluto del checkout (con le cartelle dell'utente) reso relativo: 12 occorrenze (6 in `comandi-modello.txt`, 6 in `togli-pagine.txt`).
- Righe `init` (6, una per stream): tenute ma filtrate. Plugin 18 → 1 (`tollgate`), server MCP 7 → 0, skill 212 → 23, comandi 291 → 23, agenti 43 → 21 (solo `tollgate:`), tolti 8 strumenti `mcp__`. `memory_paths` e `messaging_socket_path` sostituiti con «[tolto dalle evidenze]». Ho scelto di filtrare invece di togliere la riga (B7 la toglieva) perché il brief dice «tieni solo ciò che è di tollgate»; così restano versione, modello e modo dei permessi.
- Righe `hook_started`/`hook_response` dei `SessionStart` non di tollgate: 62 tolte (12 in passo1, 10 negli altri). Resta la coppia di tollgate nei passi 2-6.
- Dopo le modifiche: `flowreg.py togli-pagine` ripassato sui 6 stream (0 sostituiti); ogni riga di ogni stream è JSON valido.
- Restano di proposito (detto nel rapporto): `superpowers:writing-plans` (testo della skill `spec-audit` di tollgate), `context7:` (formato della nota di ricerca), `agent-skills` (fonti di `rules-security` lette da un revisore), `superpowers:test-driven-development` (skill chiamata due volte dagli implementatori, solo nome e «Launching skill»), le uscite `""`/`{}`/`allow` di hook non di tollgate (senza nomi), `prova@example.com` (autore dei commit della prova).

## Controlli (`/usr/bin/grep -ra` e script Python; utente e host da `id -un`/`hostname`, mai stampati)
- nome utente, host: 0 nelle evidenze e nel rapporto;
- `/home/` diverso da `/home/USER`: 0; `MEGA`: 0; `.claude/plugins`, `/run/user`: 0;
- `sk-ant`, `ghp_`, `github_pat_`, `gho_`, `ghs_`, JWT: 0;
- id di sessione reali: 0 (ogni `session_id`/`session` è `SESSIONE-n` o null);
- e-mail: solo `noreply@anthropic.com` e `prova@example.com`;
- nomi delle cartelle della home e di quelle che contengono il repo (ricavati a runtime): nelle evidenze 2 corrispondenze, tutte e due falsi positivi (`README.md` e il nome di un programma vietato); nel rapporto le stesse due;
- stringhe da 60 caratteri in su: solo percorsi della prova, firme dei blocchi di ragionamento, separatori.

## Test
- `python3.11 -B -m unittest tests.test_b1_scripts tests.test_docs`: Ran 168 tests, OK.
- `python3 -B -m unittest tests.test_b1_scripts tests.test_docs` (3.13.5): Ran 168 tests, OK (compreso `test_committed_evidence_has_no_long_web_results`, lanciato anche da solo prima del commit: OK).
- Suite completa non lanciata (nessun codice cambia; eccezione del Task 9).

## Dove evidenze e ledger non corrispondono (il rapporto segue le evidenze)
1. Id dei revisori del task: il ledger dice 01, 03, 04, 05, 08, 10, 12, 15; gli stream hanno anche 07 (revisore task 1, sul diff) e 16, 17 (tutti e due, sul report).
2. Id dello specialista: il ledger dice 03, 04, 05, 06, 07, 08, 10, 12; nel verdetto 06 è tra le «non applicabili» con 09, 11, 13, 14; quelle giudicate rispettate sono 03, 04, 05, 07, 08, 10, 12 (05 anche nel rilievo f-1-3).
3. DoD: il ledger dice «finish check verde … tutte le voci [sì]»; a `finish check` due voci erano `[dopo la revisione]`, diventate `[sì]` a `finish open-pr` (normale, come B7).
4. Costi per modello: i `result` dei passi 1 e 5 hanno anche `claude-haiku-5-5` (0,019 e 0,005 USD), che il ledger non divide; nessun messaggio di agente è su haiku, ed è nei soli passi con WebFetch: con ogni probabilità è il modello interno di Claude Code per WebFetch. Il totale 19,55 lo comprende. Va saputo per la regola «mai sonnet né haiku»: non è un agente di tollgate.
5. Trascrizioni: `registra` non ha trovato quelle dei 9 avversari della spec (sessione 1, «nessuna trascrizione di subagente»); il ledger non lo dice.

## Altri fatti utili per il controller
- Gli avversari della spec hanno letto `tollgate.toml` e citato la `checklist` del profilo nei rilievi del giro 1 («accesso negato provato da un test», «valori predefiniti che rifiutano»): la sicurezza fin dal progetto lavora insieme alla checklist, non solo con la voce della decisione 20. Il rapporto lo dice.
- Modello delle minacce e raggio d'azione: presenti in tutti e due i report degli implementatori (contenuto, non id). `agents/implementer-security.md` nomina solo gli id delle regole sul report; il contenuto viene da `rules-security`. Il limite: gli implementatori hanno letto `tollgate.toml` con la checklist.
- Rilievo `f-1-3` (`can_read("", "")` dà `True`) scartato per regola sbagliata, non per fatto falso: il rapporto lo segnala come limite del verificatore.

## Dubbi
- Ho tenuto le righe `init` filtrate invece di toglierle come B7: se il controller preferisce la forma di B7, basta togliere 6 righe.
- `superpowers:test-driven-development` resta negli stream (comportamento degli implementatori, come B7 teneva i nomi `superpowers:…`); se va tolto anche quello, sono 6 occorrenze in `passo5`.

## Fix round 1

Commit `86b3dff` «tollgate C2: rapporto della prova, correzioni dopo la revisione» (rapporto e 6 stream; HEAD di partenza 3855816, documenti del Task 10 non toccati).

- **I1**: tolta la frase su `implementer-security.md` che «nomina solo gli id». Ora il rapporto dice che modello delle minacce e raggio d'azione li chiede per esteso il testo dell'agente (riga 51), oltre a R-SECURITY-01/16 e alla `checklist`: provano l'instradamento all'agente dell'area, non il precaricamento. La prova resta il titolo con `isMeta: sì` nelle cinque trascrizioni; l'indizio forte sono gli id con il contenuto giusto, perché gli agenti elencano solo i numeri. Corretti i paragrafi «Che cosa vuol dire per la prova», (a) e «Scostamenti»; aggiunto il punto 6 in «Differenze con il registro del controller».
- **m1**: tolto «come dice la skill»; la divisione diff/report è anche nel testo degli agenti; 15 (task 1) e 08 (task 2) dette «non si applica».
- **m2**: la skill di TDD la chiede `implementer-security.md` (riga 57) e riesce perché il plugin è installato; nei Limiti il testo della skill di terzi entrato nel contesto degli implementatori, assente dalle evidenze.
- **m3**: «2 test all'inizio» con la fonte (`spikes/c2/flow/tests/test_tokens.py`, nel repo, non nelle evidenze); tolte le tre lunghezze degli hook (il segnaposto con le lunghezze stava nelle righe tolte).
- **m4**: in «Costi» e «Scostamenti». Fonte: `events.jsonl` dice `outcome: empty` per i giri 4-9 della spec e 4-6 del piano. Rifiuti di `audit prepare` solo dopo i giri 1 (righe 209 di `passo1` e 218 di `passo3`). I giri 5-9 e 5-6 sono nati da correzioni di sole note `minor`: 7 giri, 280.137 token. Nota: il controller scriveva «sei e tre» (il numero dei giri `empty`). Io scrivo entrambi i dati: 6 e 3 giri `empty`, di cui 5 e 2 aperti dopo correzioni di soli `minor`. Il giro 4 di ciascuno seguiva un giro con un `moderate`.
- **m5**: tolte 15 righe `rate_limit_event` e 6 campi `credential_expires_at`; detto in «Anonimizzazione», senza valori.
- **m6**: `f-1-3` descritto come rilievo `minor` tra le note che non chiedono modifiche.
- **m7**: aggiunta la riga sul `finding-verifier` che legge R-SECURITY-05 dal file della skill (riga 262 di `passo6`).
- **m8**: campo `nota` («riga ridotta: tolti plugin, skill, server MCP, agenti e comandi non di tollgate») nelle 6 righe `init`.
- I numeri di riga citati nel rapporto sono stati ricalcolati sugli stream nuovi (63/72, 23/307, 262, 209, 218).

Controlli: ogni riga dei 6 stream è JSON valido. `togli-pagine` ripassato: 0 risultati. `/usr/bin/grep -ra` di nome utente e host: 0 file. `/home/` diverso da USER: 0. Id di sessione reali: 0. `rate_limit_event`/`credential_expires_at`: 0.

Test:
- `python3.11 -B -m unittest tests.test_b1_scripts tests.test_docs` → Ran 168 tests in 179.447s, OK
- `python3 -B -m unittest tests.test_b1_scripts tests.test_docs` → Ran 168 tests in 170.119s, OK
