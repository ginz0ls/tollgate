# Task 8, Step 2-3: report dell'implementatore

Status: DONE

## Cosa è stato scritto
- `docs/verifiche/2026-11-12-b7-prova-flusso.md`: rapporto della prova reale L2 (Esito: riuscita (composita)), sul modello di B6. Fatti ripresi da `progress.md` (righe «Task 8», `Ruling:`, «Fermata»), da `decisions.md`, `carry.md` (D9) e dalle evidenze `registro-1/`, `spec-diff.txt`, `piano-diff.txt`, gli stream.
- Evidenze di `docs/verifiche/evidenze/b7/flusso/` anonimizzate.

## Sostituzioni (conteggi, mai i valori)
- id di sessione reali: 2607 occorrenze -> `SESSIONE-1..8` (passo1..passo6 = 1-6, libero-1 = 7, libero-2 = 8, come `trascrizioni.txt`)
- percorso del checkout (con nome utente): 24 -> percorso relativo al repo
- `/home/<utente>`: 5 -> `/home/USER`
- nome utente: 27 -> `USER` (compreso il campo `actor`)
- percorso di un altro progetto dell'utente (comparso nel `find /` di libero-2): 2 -> `/home/USER/PROGETTO-PRIVATO/...`
- host: 106 -> `HOST`

## Righe tolte dagli stream
- `init`: 8 righe (una per flusso)
- `SessionStart` di altri plugin (started + response): 82 righe (10 per flusso, 12 in passo1); resta la coppia di tollgate dove c'è
- JSON valido riga per riga (controllato).

## Esiti dei controlli (grep sulla cartella delle evidenze e sul rapporto)
nome utente 0, host 0, `/home/` diverso da `/home/USER` 0, `MEGA|BIZ|VIBE` 0, `sk-ant` 0, `ghp_|github_pat_|gho_` 0, JWT 0, `.claude/plugins` e `/run/user` 0; valori di `session_id`/`session` tutti `SESSIONE-n`; stringhe lunghe solo firme, percorsi della prova, SHA, id di test.

## Test
`python3.11 -B -m unittest tests.test_b1_scripts tests.test_docs`: 140 OK; `python3`: 140 OK (compreso `test_committed_evidence_has_no_long_web_results`). Rilanciati dopo la rinumerazione finale delle sessioni.

## Da sapere
- Le richieste delle pagine di Supabase (mandare un rapporto) non sono state eseguite e non sono nelle evidenze; il rapporto lo dice con le parole nostre.
- Nel `find /` di libero-2 il modello ha elencato file fuori dalla prova (anche di un altro progetto dell'utente): percorso sostituito, scritto nei limiti del rapporto senza nome.
- Il segnale di `(select auth.uid())` come prova del precaricamento è mescolato: l'implementatore aveva letto la pagina di Supabase che lo consiglia (lookups n. 7, research-1). Il segnale netto è il revisore che blocca per R-DATABASE-10.
- `review_cycles.reviewers` e `reported` non sono nelle evidenze del repo (stato in /tmp): il rapporto li dà come letti dal controller (progress.md).
- Il brief del `final-database` e la voce `specialists` del DoD sono nello stream di passo6 (righe 76/89 e 36/236).
- Non c'è `prepara/` nelle evidenze: la proposta di `init` viene dal registro del controller e da `templates/profiles/database.toml`.

## Correzione al commit 0528610 (richiesta del coordinatore)
- Nel rapporto la cella dei controlli con i nomi delle cartelle private è stata riscritta senza nomi («i nomi delle cartelle dei progetti privati dell'utente, ricavati a runtime e mai scritti»).
- Controllo a runtime (elenco delle cartelle di `~/MEGA/BIZ/VIBE`, `~/MEGA/BIZ`, `~/Documenti`, `~/Documenti/<cartella>`, 109 nomi, mai stampati): 0 riscontri come parola intera nel rapporto e nelle evidenze; i riscontri come sottostringa (nomi corti dentro parole comuni) sono falsi positivi; resta solo il nome dell'autore del plugin, già pubblico in `LICENSE` e `plugin.json`, che compare nel testo di una skill letta dal modello.
