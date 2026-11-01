# Report Task 7, Step 1

Implementato in `spikes/run-b1-flow.sh`, `spikes/b1/flowreg.py`, `tests/test_b1_scripts.py`.

- `B1_FLOW_RULES` (`prova` predefinito | `vere`, altro valore = errore, controllato per ogni modo). `vere`: OUT = `docs/verifiche/evidenze/b2/flusso` (dalla radice del repo); `prepara` non scrive la rules-base di prova e fa `python3 -B -` con `bin/` della copia nel `sys.path` che chiama `lookups.rules_enforced` (pathlib), altrimenti die "non accende l'interruttore" prima di creare il progetto.
- `B1_FLOW_SRC`: sorgente della copia (`git ls-files`/`tar`); senza `B1_FLOW_CHECK=1` è un errore (per ogni modo). `fakegh.py` e `OUT` restano dalla radice del repo.
- `controlla` stampa `B1_FLOW_RULES`, radice sorgente, cartella delle uscite.
- `flowreg.py precarico <stream>...`: cerca `# Regole di base (versione 1)` nelle trascrizioni dei subagenti (valori di `agent_transcript_path` nel flusso, ovunque nel JSON), stampa solo il nome del file (niente `/home/...`), `metodo: trascrizioni` oppure `metodo: indizio` con le righe `R-BASE-`. `registra` lo chiama solo con `vere` e scrive `precarico.txt`. `WANTED` invariato.
- D11: lo script non anonimizza nulla (lo fa il controller sulle evidenze); `research_switch_unreadable` non è in `WANTED`, quindi `registra` non lo raccoglie: nessuna modifica. Se il controller lo vuole, va aggiunto a `WANTED` e il percorso anonimizzato.
- D13: `test_flow_copy_fails_on_missing_tracked_file` passa senza modifiche dello script.
- Nuovi test: i sei del brief + `test_flowreg_precarico`. RED: 14 fallimenti e 1 errore prima delle modifiche; GREEN: `tests.test_b1_scripts` 44 test OK.
- `PYTHONWARNINGS=error::ResourceWarning tests/run`: python3.11 e python3, 3218 test, OK, 1447 s.
- Scostamento: il test refuses_unapproved controlla l'assenza di `flow/.git` (la cartella vuota esiste già dopo il `mkdir`).
- Assunzione da verificare dal vivo: che il flusso `--include-hook-events` contenga `agent_transcript_path` (evento SubagentStop); altrimenti `registra` ripiega sull'indizio e lo dichiara.

## Step 3-4

- Rapporto `docs/verifiche/2026-10-29-b2-prova-flusso.md`; evidenze anonimizzate in `docs/verifiche/evidenze/b2/flusso/`: home `/home/USER`, utente `USER`, host `HOST`, 2 id di sessione `SESSION-ID` (testo, su tutti i file); dagli stream tolte 24 righe (2 `init`, 22 eventi `SessionStart` di altri plugin; restano i 2 dell'hook di tollgate nel passo 2).
- grep `USER|HOST|/home/USER` su evidenze e rapporto: vuoto. grep di prefissi di token (`sk-` con 20+ caratteri, `ghp_`, `gho_`, `github_pat_`): vuoto (un primo giro trovava i prefissi nominati nel testo del rapporto: riformulato).
- `python3 -B -m unittest tests.test_b1_scripts tests.test_docs`: 50 test OK. Commit «tollgate B2: prova reale corta con rules-base vera».
- Nota: lo `esito.txt` e `argv.txt` contengono solo percorsi `/tmp/tollgate-b1`.

Giro rapporto: aggiunti i tre punti della revisione (skill writing-plans pubblica nelle evidenze, limite dei plugin attivi, argomento isMeta); test_docs OK, grep di anonimizzazione vuoti; commit nuovo.

Seconda corsa: evidenze nuove anonimizzate (24 righe tolte, home/utente/host/sessioni sostituiti), rapporto con la sezione «Seconda corsa» e percorsi della prima corsa aggiornati; grep USER|HOST|/home/USER e prefissi di token vuoti; test_b1_scripts e test_docs OK.
