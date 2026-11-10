# Revisione Task 8 (commit 09396ba): rapporto della prova reale e evidenze

### Aderenza
- ✅ Il commit contiene solo `docs/verifiche/2026-11-09-b5-prova-flusso.md` e `docs/verifiche/evidenze/b5/flusso/` (42 file, nessun altro percorso, nessun `__pycache__`).
- ✅ In testa al rapporto c'è `Esito: riuscita`; è coerente con le evidenze: un tentativo per passo (`exit-codes.txt`, `esito.txt`), uscita 0, task 1 `done` con `approved` (`events.jsonl`).
- ✅ Numeri verificati sugli stream: passo 1 20 turni, 0,384 USD, 80 s; passo 2 11 turni, 0,541 USD, 126 s; token 53.212 + 36.703 = 89.915 (`stats.json`); tipi `tollgate:implementer-backend` / `tollgate:reviewer-backend` (`tipi-task.txt`, `events.jsonl`); commit `fe49212`, `5ea7b17`, `185409b` (`git-log-worktree.txt`); righe `init` e `SessionStart` tolte; `comandi-rischiosi.txt` vuoto; conteggio strumenti uguale a `comandi-modello.txt`.
- ✅ Precaricamento: `trascrizioni.txt` ha i titoli «Regole di base» e «Regole backend» con `isMeta: sì` per entrambi i subagenti; il rapporto spiega bene perché `precarico.txt` dice solo «indizio».
- ✅ Distinzione dal piano scritto dal modello (decisione 14), verificata sullo stream: nel passo 1 gli id `R-BACKEND-01..12` compaiono solo alla riga 88 (lettura del `tollgate.toml`, solo l'elenco); il piano (Write riga 180) non contiene contratti, indirizzi ufficiali, prova locale né `R-BACKEND`; il testo del task letto dall'implementatore (passo 2, riga 89) non li nomina; il revisore cita `R-BACKEND-01,02,03,04,05,09,10,11,12` (passo 2, righe 247 e 252) e solo lì. Il report dell'implementatore (riga 194) dichiara contratti assenti, indirizzo ufficiale, nessuna prova locale e perché.
- ✅ Nota valida prima della prima modifica (`events.jsonl` seq 9 `ok: true`, poi `verify` e commit); letture (`lookups.txt`) come nel rapporto.
- ✅ Scostamenti dichiarati (piano scritto nel passo 1, revisore `task-reviewer` sbagliato nel piano, M2 nel riepilogo) e limiti presenti e onesti: ramo «niente da dichiarare», nessun rilievo `R-BACKEND` dal vivo, modalità `detect`.
- ✅ Evidenze, controlli miei (senza riportare valori): nessun `/home/` diverso da `/home/USER` (la sola occorrenza è `/home/USER`; le due righe «`/home/`» nel rapporto sono testo descrittivo); nessuna forma di token (`sk-ant`, `ghp_`, `github_pat_`, `vercel_`, `xox`, `AKIA`, JWT); nessun nome utente, nome di macchina, MEGA, progetto privato; nessun `.claude/plugins` o `.claude/projects`; nessun elenco di plugin né `slash_commands`/`mcp_servers`; nessun nome di skill o plugin di terzi tranne `superpowers:writing-plans` (scritto dal modello), `docs/superpowers/...` (cartelle del progetto), `context7:` (testo della skill di tollgate) e `cloudflare:workers` (import del file di prova). Gli id di sessione sono tutti `SESSIONE-1/2`; gli uuid residui sono id di messaggi e hook.
- ✅ Gli output degli hook rimasti (`hook_response`) sono di tollgate (`additionalContext` «tollgate: …»); non ho trovato output di hook di terzi.
- ✅ Tutte le righe JSONL valide: passo 1 212, passo 2 272, `eventi-ricerca.jsonl` 1, `events.jsonl` 17.
- ✅ Nessun risultato di `Read`/`Grep`/`Bash` su `tool-results/` nelle evidenze; nessuna pagina di terzi: nel passo 2 resta il solo `WebFetch` breve dichiarato. `test_committed_evidence_has_no_long_web_results`: OK.
- ⚠️ Non verificabile da me: la lettura delle trascrizioni dei subagenti (`isMeta`) fuori dal worktree, la fa il controller; le evidenze (`trascrizioni.txt`) la riportano e il rapporto lo dice.

### Punti di forza
- Rapporto chiaro, fedele al modello di B4, con la tabella «atteso/esito», la distinzione fra segnale di precaricamento e piano del modello costruita sui fatti e limiti espliciti (ramo non provato, `--disallowedTools` a prefisso).
- Il rapporto attribuisce al controller i controlli fatti da lui e dichiara che «ripulito» vale per quanto grep-ato, con la tabella delle ricerche.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `docs/verifiche/2026-11-09-b5-prova-flusso.md` (sezione «Precaricamento», punto sul brief del revisore): scrive che nel brief del revisore compaiono solo `R-BASE-05, 07, 10, 11`. Nel brief letto dal revisore (`passo2/tentativo-1/claude.jsonl` riga 225) compare solo `R-BASE-05`; 07, 10 e 11 le cita lui nell'uscita. La conclusione (nessuna `R-BACKEND` nel brief) resta vera. Correggere in «solo `R-BASE-05`».
2. Stessa sezione: «riga con il testo della revisione» è impreciso; il prompt dell'`Agent` è solo il percorso di `review-1.md` (riga 208), il testo è la riga 225.
3. `registro-1/limiti.txt:1` dice «Task 9» (intestazione dello script, ereditata da B4): in un'evidenza del Task 8 è fuorviante, ma è output dello script e non va ritoccato; basta una riga nel rapporto o lasciarla.
4. Nota di forma: i `Grep`/`Glob` dei subagenti non entrano in `lookups` (già detto nel rapporto), ok.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** il rapporto è vero rispetto alle evidenze, non dichiara come ripulito ciò che non è stato controllato, le evidenze non contengono dati dell'utente, token né testo di terzi oltre al `WebFetch` breve dichiarato, il JSON è valido e il commit tocca solo i percorsi attesi. Restano solo imprecisioni minori di formulazione.
