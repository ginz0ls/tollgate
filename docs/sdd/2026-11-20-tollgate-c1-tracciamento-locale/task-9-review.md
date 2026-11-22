# Revisione Task 9, Step 1-2 (b0dbdef)

### Aderenza
- ✅ `flowreg.py eventi-c1` (`spikes/b1/flowreg.py:104-117`, `main` :471): stampa solo `size_decided` (data intero), `cost` (solo `tokens` e chiavi ordinate di `by_model`), `ruling` (data intero). Righe non JSON ignorate. `WANTED` ed `eventi` invariati; il test esistente non è toccato; `togli-pagine` resta l'unico comando che scrive.
- ✅ `registra` (`run-b1-flow.sh:615-616`): `eventi-c1.jsonl` dopo `eventi`; `snapshot.json` scritto dopo `export TOLLGATE_STATE="$STATE"` (:606), nel repo di prova, con lo stesso schema di `status --json` (`( cd "$REPO" && "${TG[@]}" snapshot ...)`). Nessun ramo in cui `snapshot` parta senza la variabile: l'export precede tutti i comandi di raccolta. Senza DB, `cli.py:512` stampa una fotografia vuota senza creare nulla (sola lettura).
- ✅ `B1_FLOW_EVIDENCE` (`run-b1-flow.sh:67-70`): validata con `*[!a-z0-9-]*`, errore col nome della variabile, applicata dopo le righe `OUT=` e prima della riga del banco di prova (:72), quindi vince su RULES/CASE e `B1_FLOW_OUT` dei test vince ancora. Verificato: `bash -n` ok.
- ✅ Test: `test_flow_evidence_out_dir` (c1, e c1 con RULES=vere/CASE=ai), `test_flow_evidence_rejects_bad_values` (`../x`, `A`, `a/b`, `x y`), `test_flow_evidence_test_out_still_wins`, `test_registra_lists_c1_events`, `test_flow_registra_writes_c1_files` (fallimenti.txt vuoto, snapshot.json dict). Rilanciati i 5: OK, working tree pulito.
- ✅ Caso predefinito invariato (L1, rules-base vera con `B1_FLOW_RULES=vere`, nessun default cambiato).
- ⚠️ Non verificabile senza prova reale: la forma vera degli eventi `cost`/`size_decided` nelle evidenze (il test usa righe finte coerenti con la decisione 3).

### Punti di forza
Diff minimo e chirurgico, nessun file nuovo, errori di raccolta riportati in `fallimenti.txt` come gli altri comandi, test del rifiuto con più forme di valore errato.

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. `run-b1-flow.sh:11-40` (intestazione) e `modo_controlla` (:247-): non citano `B1_FLOW_EVIDENCE` come variabile né i nuovi file di `registra` (`eventi-c1.jsonl`, `snapshot.json`); `controlla` non stampa `B1_FLOW_EVIDENCE:` accanto a RULES/CASE. Solo documentazione/leggibilità, già segnalato dall'implementatore.
2. `eventi_c1`: un `cost` con `data` non dict produce `tokens: null, by_model: []` senza segnalarlo. Accettabile per un raccoglitore; in Step 4 il controller verifichi a occhio che `by_model` non sia vuoto.

### Sicurezza del lancio
Sicuro da lanciare: nessun uso di chiavi, rete o stato vero. `snapshot`/`events`/`stats` leggono solo lo stato di prova (`/tmp/tollgate-b1/state`, o `B1_FLOW_ROOT`); le uscite vanno in `docs/verifiche/evidenze/c1/flusso` nel worktree, mai cancellate. Con `B1_FLOW_EVIDENCE=c1` usare `B1_FLOW_RULES=vere` (CASE predefinito b1). Ricordare `git status` sulle evidenze prima del commit e `togli-pagine`/anonimizzazione come da Step 4.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** requisiti degli Step 1-2 e D6 rispettati, `snapshot` sempre con `TOLLGATE_STATE` di prova, test mirati verdi; restano solo ritocchi di documentazione.
