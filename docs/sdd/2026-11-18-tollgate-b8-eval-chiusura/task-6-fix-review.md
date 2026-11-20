# Revisione delle correzioni dopo la sonda (Task 6, Step 3), commit 2bb649c

### Aderenza
- ✅ 1. `bin/tollgate_core/lookups.py:63-71`: `code` intero non booleano fuori da 200-299 e `result` stringa che inizia (dopo spazi) con `REDIRECT DETECTED` non registrano; senza `code`, con `tool_response` None o non dict, con `code` booleano contano come prima. Unico punto di regola: `observed` serve sia `runner.py:192` sia `lookup_rec.py:31` (controllati i chiamanti; nessun'altra copia della regola in `bin/`). Test in `tests/test_lookups.py` (301, 302, 307, 404, 500, 199, 200 con avviso, 200 normale, senza code, None, bool) e passo `fetch` a secco con `response` facoltativo (`tests/test_eval_cases.py`, predefinito invariato).
- ✅ 2. I punti che leggono `message` come oggetto sono tutti protetti: `flowreg.py:46` e `:254` corretti qui; `:177`, `:348` e `evals/scrub.py:62` già lo erano. `anonymize` lavora su byte: giusto non toccarlo. Test: `flowreg` (web_results, tool_uses, third_party_blocks, togli_pagine), `scrub` strip-web/strip-bash con uscita 0 e riga intatta, `run.sh` in TEST_MODE con `FAKE_DENIED_ROW` (uscita 0).
- ✅ 3. `WEB_DOMAINS` con `aistudio.google.com`; i permessi di `run.sh` lo seguono; `case.yaml` con le due alternative nei due grader, pesi e prompt invariati; `docs/uso/eval-e-ci.md` aggiornato; `skills/rules-ai/SKILL.md` non toccato. Test del cammino giusto con l'indirizzo nuovo e del redirect rifiutato.
- ✅ Scostamento dichiarato: `test_p5_registry_untouched_by_b8` ora confronta i byte prima/dopo invece di pretendere la sola intestazione. Corretto: il vecchio test dipendeva dallo stato del registro vero. `test_dry_run_reads_real_registry` gestisce già sia il tetto esaurito sia quello con residuo, quindi non dipende dal contenuto.
- ⚠️ Non verificabile dal diff: la forma reale di `tool_response` di `WebFetch` per un redirect (la sonda non la vede nella trace). La regola copre sia il codice sia il testo; la sonda ripetuta lo confermerà (già nel ruling).

### Punti di forza
- Una sola regola, fallimento sicuro (forme non riconosciute seguono la regola di prima).
- Il test rosso/verde è documentato nel report (12 failure + 1 error prima, suite verde su due interpreti dopo).
- Il test «solo all'inizio del risultato» evita falsi positivi su pagine che citano l'avviso.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
- `tests/test_lookups.py` (fine file): `ObservedWebFetchTest` sta dopo il blocco `if __name__ == "__main__": unittest.main()`. Con `python -m unittest` e `tests/run` gira, ma lanciando il file direttamente la classe non viene raccolta. Spostarla sopra il blocco.
- `evals/s10-modello-a-memoria/case.yaml`: il pattern `aistudio\.google\.com/docs/models` accetta anche prefissi (`.../docs/models-altro`); innocuo (l'`input_match` non ha ancorature e anche quello vecchio era così).
- ⚠️ Nel worktree c'è `docs/verifiche/evidenze/eval-b8/20261119T024436Z-s10-modello-a-memoria/` non tracciata: `test_committed_evidence_has_no_long_web_results` fa `rglob` anche su file non tracciati, quindi la suite verde dipende dal fatto che quella cartella sia già pulita. Il brief dice che non c'è nulla da ripulire; va ricontrollato prima di committarla.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** le tre correzioni seguono il brief, la regola di `observed` è unica e coperta nei casi limite (301/302/200 con avviso/senza code), nessun punto di `flowreg` o `scrub` legge ancora `message` come oggetto senza controllo, e i grader di s10 accettano i due indirizzi senza allargare i cammini sbagliati.
