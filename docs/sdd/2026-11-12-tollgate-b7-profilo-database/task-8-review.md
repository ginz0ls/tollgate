# Revisione Task 8 (rapporto della prova reale L2 e evidenze), commit 0528610 + 30e9f6b

Sola lettura. Nome utente e host ricavati a runtime, mai stampati. Eseguito `python3 -B -m unittest tests.test_b1_scripts`: 133 test OK (compreso `test_committed_evidence_has_no_long_web_results`).

### Aderenza
- ✅ Esito `riuscita (composita)` (rapporto:3) con i cinque motivi (:7-13), uguali al ledger.
- ✅ Passi, tentativi, atti `approve spec 1` e `approve plan` dati dal controller con confronto con l'input (:43, :44, :51), scelte dell'utente e arrivo al modello con `libero` (:45-46), i due difetti (:105-109), la prima esecuzione (:111-120): coincidono con le righe «Task 8», `Ruling:`, «Fermata» di progress.md.
- ✅ Costi: ricalcolati dai messaggi `result` degli stream, uguali alla tabella (0,94/0,18/0,77/0,17/0,66/0,28/0,91/0,62 = 4,53; prima 3,16; totale 7,69); turni e durate coincidono; la spiegazione «nessun addebito, quota dell'abbonamento» c'è (:124). Token per agente = `stats.json` (620.986).
- ✅ Specialista: eventi `review_cycle` (number 1, ok, 1 confermato), rilievi f-1-1/f-1-2 con confidenza e verifica, riporto da stato letto dal controller (dichiarato non nelle evidenze), voce `specialists` `[dopo la revisione]` → `[sì]` (righe 36/236 dello stream di passo6 verificate), brief con la lista di controllo (righe 76/89 verificate).
- ✅ Precaricamento: dice cosa mostra (righe `isMeta: sì` in trascrizioni.txt, uguali al file) e cosa no (`isMeta: no` non provato, `precarico.txt` solo indizio, segnale `(select auth.uid())` mescolato con la pagina letta, lookups n. 7). Distingue ciò che è entrato dalla spec per un rilievo.
- ✅ 18 `subagent_start` e 18 `subagent_stop` negli eventi; tipi-task, ricevute `tests_run` 2,2,3,3, tre commit di codice, atti a-1/a-2/a-3: tutto uguale.
- ✅ Evidenze: 0 occorrenze di nome utente e host (anche nel rapporto); `/home/` solo `/home/USER`; 0 `sk-ant`, `ghp_`, `github_pat_`, `gho_`, JWT, `MEGA/BIZ/VIBE`, `.claude/plugins`, `/run/user`, percorso del checkout. Solo email: `noreply@anthropic.com` (attribuzione dei commit, innocua).
- ✅ 2618 righe JSONL, 0 non valide; nessuna riga `init`; i soli `SessionStart` rimasti (14) sono di tollgate («tollgate: lavoro #1 (L2), fase …»); `session_id`/`session` solo `SESSIONE-1..8`; i UUID rimasti sono id dei messaggi.
- ✅ Nessun risultato WebFetch con testo di terzi: i 3 sono segnaposto («pagina di terzi tolta dalle evidenze: <url>, <n> caratteri»; 1723, 2879, 656 come nel rapporto e nel ledger). Nessuna richiesta di Supabase eseguita: nessun `curl`/`wget`/`gh`/`git push`/programma vietato in `comandi-modello.txt`; `comandi-rischiosi.txt` vuoto; il testo della richiesta non è nelle evidenze. Le 14 righe con «supabase» sono percorsi o testo (D9).
- ✅ Percorso dell'altro progetto privato dal `find /` sostituito con `PROGETTO-PRIVATO` (1 file, `libero-2`); il rapporto non nomina cartelle private (30e9f6b).
- ⚠️ Non verificabile dalle evidenze rimaste: che il riassunto della pagina di Supabase dica di averla ignorata (:150): il risultato è stato sostituito; il fatto sta solo nel ledger (dichiarato come tale nel rapporto, ok). Il riporto `reported = {final-reviewer: ok, final-database: ok}` e `review_cycles.reviewers` idem (dichiarato, :81).

### Punti di forza
- Rapporto onesto sui limiti del segnale di precaricamento e sul conflitto spec-regola, con l'esito composito spiegato.
- Tabella di controllo dell'anonimizzazione senza i valori cercati; conteggi nel report dell'implementatore coerenti con le evidenze.
- Costo equivalente separato dall'addebito, come chiesto dall'utente.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.

**Minor**
1. `docs/verifiche/2026-11-12-b7-prova-flusso.md:151`: «3 uscite di hook di terzi dei `SessionStart` (1.129, 3.604 e 10.170 caratteri), 24 in tutto». Le lunghezze non compaiono né in `registro-1/togli-pagine.txt` (dice solo «3 risultati sostituiti» per flusso), né nel ledger, né in B6, né negli stream (le righe sono state tolte): non sono verificabili e potrebbero provenire da un altro run. Correggere togliendo i numeri o citando la fonte.
2. `:42`: «eventi `spec_audit_round` in `events.jsonl`» per i 5 giri della spec: nel file gli eventi sono 9 (5 spec + 4 piano); dirlo o specificare.
3. `:59`/`:17`: la proposta di `init` e `prepara` non sono nelle evidenze (dichiarato). Nessun rimedio richiesto.
4. `:15`: due versioni di Claude Code (2.1.325 nel ledger, 2.1.326 nel file): annotato nel rapporto, ok.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** il rapporto coincide con il ledger e con gli stream, i costi sono ricalcolati e giusti, le evidenze sono pulite (utente, host, token, sessioni, righe di terzi, WebFetch, progetto privato) e i test mirati passano. Restano solo minori (numeri di caratteri non tracciabili a :151, precisione sugli eventi a :42).
