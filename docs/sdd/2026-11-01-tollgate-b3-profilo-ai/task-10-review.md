# Revisione Task 10 (rapporto della prova reale corta, profilo ai)

Diff f8f5331 rispetto a 75ac4a8: rapporto + evidenze `docs/verifiche/evidenze/b3/flusso/`. Controlli fatti con grep mirati e lettura dei file di registro; nessun comando di rete, nessun `claude`.

### Aderenza
- ✅ Passi, tentativi, esito non composito: `exit-codes.txt` (uscita 0 per entrambi, tentativo 1). Durate 124 s / 115 s = `duration_ms` 123917 / 115041; costi 0,7205 + 0,5954 = 1,32 USD (`total_cost_usd` degli eventi `result`).
- ✅ Instradamento: `registro-1/tipi-task.txt` (`implementer-ai` / `reviewer-ai`, stato `done`); token `stats.json` 65.367 + 45.621 = 110.988; veti, giri e blocchi 0.
- ✅ Letture: `lookups.txt` (2 read, 2 fetch dell'implementatore), 3 Grep non registrati (`grep-non-registrati.txt`). Versione 2.1.316 (`versione-claude.txt`).
- ✅ Nota di ricerca: un solo evento `research_note`, nessun veto; `research-1.md` coerente con quanto riportato.
- ✅ Proposta di `init` e commit `31ad748`, `742bf47`, `bc86d6b`: coerenti con `git-log-worktree.txt`. Il piano cita R-AI-01/02, confermato dalla risposta finale del passo 1; RED/GREEN e "non lanciato /tollgate:finish" dalla risposta finale del passo 2.
- ✅ Non esagera: «nessun rilievo R-AI dal vivo» dichiarato in grassetto e rimandato ai tre test; nessun veto `research_gate` visto, rimandato ai test del Task 5; limiti (detect, `--allowedTools`, altri plugin, una sola L1) presenti e coerenti con `limiti.txt`.
- ✅ Anonimizzazione: 0 occorrenze di nome utente e host; `/home/` seguito da altro che `USER`: 0 (restano solo `/home/USER/...`); `session_id` solo `SESSIONE-1/2` (223 e 285 righe, tutte); campo `host` = `HOST` (17); nessun `sk-`, `ghp_`, `github_pat_`, `Bearer <valore>`; restano solo `CHIAVE-ANT` (2) e `Bearer-SEGNAPOSTO` (1), come dichiarato. JSONL ancora valido (parse riga per riga senza errori). Le righe tolte dichiarate tornano: nel passo 1 nessun `SessionStart` residuo, nel passo 2 resta la coppia di tollgate.
- ✅ Forma coerente con B2 (stessa intestazione, tabella dei passi, letture, nota, verdetto, esito rispetto all'atteso, limiti, anonimizzazione).
- ⚠️ Precaricamento: le trascrizioni dei subagenti non sono nelle evidenze, solo `trascrizioni.txt` con i titoli. La spiegazione delle due righe `isMeta: no` come messaggio `api-request-blob` poggia sulla verifica del controller, non riproducibile dal repo. Il rapporto lo attribuisce correttamente al controller e ammette che `precarico.txt` dice «indizio»; accettabile.

### Punti di forza
Onesto sui limiti; tabella «Atteso / Esito» che ricalca il passo 1 del piano; controlli di anonimizzazione senza riportare i valori cercati; modifiche alle evidenze elencate una per una.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. Rapporto, intestazione: il nome del file porta 2026-11-01 (data del piano) ma la prova è del 2 novembre. Una riga lo direbbe (B2 aveva data e nome allineati).
2. Il passo 1 ha segnalato un rischio fuori scope (`ai/summary.py:14` legge `risposta.content[0].text`, pensiero adattivo dei modelli 5.x) e ha chiesto conferma del modello: non è nel rapporto. È un'osservazione utile del profilo `ai`, in «Cosa è stato scritto» o in «Difetti trovati».
3. Le evidenze contengono `/tmp/claude-1000/...` (uid locale) e id di hook; non sono dati identificanti, non serve cambiarli, ma l'elenco delle anonimizzazioni non li menziona.
4. «modello `sonnet`» senza l'ID (`claude-sonnet-5-5`, unico in `modelUsage`): B2 lo riportava.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** il rapporto riflette fedelmente fatti ed evidenze, non gonfia ciò che è provato (nessun R-AI dal vivo) e l'anonimizzazione risulta completa ai controlli; restano solo rifiniture.
