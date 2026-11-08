# Ri-revisione del giro di correzione finale B4 (`c81fa1e..af0b1bb`)

Sola lettura. Letti: regole, brief, revisione finale, report, diff (parti di codice, test e documenti per intero; stream con controlli mirati). Controlli sulle evidenze fatti con script di lettura (`python3 -B`), nessuna suite rilanciata, nessuna rete.

### Verdetti sui rilievi

**I-1: testo di terzi nelle evidenze (`Grep`/`Read` su `tool-results/`)** — INDIRIZZATO.
- `spikes/b1/flowreg.py`: `SAVED_TOOLS = ("Read","Grep")`, `_saved_copy` (guarda `file_path` o `path`, richiede `tool-results` in una cartella del percorso), `_swap_saved` (sostituisce `content` del blocco e `tool_use_result` come stringa, `content` o `file.content`), ramo "copia salvata" in `_third_party`; qualunque lunghezza, idempotente (`startswith(PAGE_PLACEHOLDER)`). Il segnaposto è lo stesso di prima.
- Test unitario `test_flowreg_togli_pagine_replaces_reads_and_greps_of_saved_copies` (`tests/test_b1_scripts.py`, stream finto con testo `TERZI-*`, nessun testo vero): conta i blocchi (righe 2 e 4), le sostituzioni (2), l'idempotenza (0), il segnaposto in tutti i campi e che un `Read` normale resta intatto. Verifica positiva e negativa.
- `test_committed_evidence_has_no_long_web_results` passa da `third_party_blocks` → `_scan`, che ora include la nuova categoria: con lo scanner allargato sarebbe stato rosso sulle evidenze di prima (le due righe sostituite erano proprio i `Grep`). Copre tutte le evidenze (`rglob` su `evidenze/`, B3 e B3-bis comprese).
- Evidenze: ho letto i `.jsonl` di `b4/flusso`; ogni `tool_use` con `tool-results` nell'input ha ora il risultato sostituito: `passo2` (Grep, 794 caratteri), `passo1` (Grep, 392 caratteri; Read, 2700 caratteri, già a segnaposto). Il diff delle due righe è `2 +-`. Nessun altro `Read`/`Grep`/`Bash`/`Glob` con `tool-results` nell'input. Nessuna `persisted-output` rimasta. JSON valido riga per riga (il test lo percorre).
- Rapporto, riga 146: dice che cosa è stato tolto davvero (WebSearch, Read della pagina, anteprima `persisted-output`, i due `Grep`, e la nuova regola su `Read`/`Grep` sotto `tool-results/`). Corretta e coerente col codice.
- Dubbio dell'implementatore (toglie qualunque risultato sotto `tool-results/`, anche non di terzi): ACCETTABILE per le evidenze. Quelle cartelle contengono solo output che Claude Code ha salvato perché troppo lungo (pagine, risultati di strumenti): per un'evidenza pubblica il sovra-taglio perde al più un output lungo del progetto, e il registro dei comandi/eventi resta altrove (`comandi-modello.txt`, eventi). Il difetto opposto (lasciar passare testo di terzi) è quello che pesa su un repo pubblico. Il limite è dichiarato nel report; consiglio solo di ricordarlo nell'uso di `togli-pagine` (già nel docstring: «qualunque risultato di Read/Grep su copie salvate»).

**M-1: `docker-compose push`** — INDIRIZZATO. `bin/tollgate_analysis/bash.py` (`_DEFAULT_EFFECTS`: `("docker-compose","push")`); `tests/test_bash.py:237` aggiunge `"docker-compose push"` a `check_effects(..., True)` in `test_docker_push_forms`.

**M-2: buco degli script `deploy`/`release` nei monorepo** — INDIRIZZATO. Scritto in spec 8.5 (nucleo) e nel piano principale sezione 9, con le tre forme (`npm -w web run deploy`, `pnpm -F web run deploy`, `yarn workspace web deploy`), la causa (si guarda solo il secondo token, o il terzo dopo `run`), la precisazione che il buco c'era già su `main` e il costo (deploy dal pacchetto di un monorepo senza approvazione, da chiudere in B5-B8).

**M-3: `docs/uso/comandi.md`** — INDIRIZZATO: «Le caricano gli agenti dell'area `infra`…».

**Triage** — INDIRIZZATO. `len([...])` in `tests/test_init.py` (`test_name_pattern_exact_paths`); `spikes/b4/flow/.gitignore` ha `.vercel/`, `.env*`, `.dev.vars*`, `.wrangler/` (senza eccezioni, nessuna preesistente; il report dice che nessun test si rompe e la suite è verde, 3668 OK).

### Danni nuovi nel diff della correzione
Nessuno. Note minori senza azione: (a) il commento del report e il docstring dichiarano il sovra-taglio; (b) `_saved_copy` usa `PurePosixPath` (importato nel modulo, i test passano); (c) la nuova categoria è estesa a `Read`/`Grep` ma non a `Glob`/`Bash` che stampano una copia salvata: nel flusso reale non ne esistono (controllato), caso teorico da tenere presente per B5.

### Controlli aggiuntivi
- Dati dell'utente nei file toccati: grep di nome utente, host, `sk-ant`, `ghp_`, `github_pat_` = 0. Gli unici `/home/` sono `/home/USER` (21), le due righe descrittive del rapporto e il percorso finto preesistente `/home/x/altro/...` (test, non toccato). Nessun id di sessione reale (restano `SESSIONE-N`).
- `skills/rules-*` e `docs/profili/`: nessun file toccato dal diff (`git diff --stat c81fa1e..af0b1bb -- skills docs/profili` vuoto).
- Report: nomina i test e dà gli esiti (289 OK sui 4 moduli con i due interpreti; suite 3668 OK, exit 0). Non rilanciati.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
