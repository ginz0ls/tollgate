# Revisione Task 7, Step 3-4 (rapporto della prova reale con la rules-base vera)

Sola lettura. Verifiche fatte su rapporto, evidenze (`docs/verifiche/evidenze/b2/flusso/`), pacchetto `review-7e46b47..0c534a3.diff` (l'unico file fuori da `evidenze/b2/flusso/` è il rapporto), modello B1. Per il punto sul precaricamento ho letto anche (solo lettura) le due trascrizioni dei subagenti in `~/.claude/projects/-tmp-tollgate-b1-flow--claude-worktrees-tg-1-.../fb1ad8ee-.../subagents/`.

### Aderenza (✅ / ❌; ⚠️ non verificabile)

- ✅ Passi e tentativi: `exit-codes.txt` e `esito.txt` dicono tentativo 1, uscita 0, per `passo1` e `passo2`; `validate-1.txt` termina con «Validation passed» e uscita 0 (ICON_MISSING e consiglio README come scritto). Esito non composito dichiarato in chiaro (rapporto, sezione «Passi e tentativi»).
- ✅ Durate e consumo: evento `result` di `claude.jsonl`: passo1 `duration_ms` 84987 (85 s), 0,4019 USD; passo2 71562 (72 s), 0,5242 USD; totale 0,92. `modelUsage` ha `claude-sonnet-5-5` e `claude-haiku-5-5`. `stats.json`: 49.015 + 30.531 = 79.546, uguale al rapporto. `esito.txt` dà 87 e 73 s di orologio: la differenza è coerente.
- ✅ `lookups.txt`: 1 `bash_read` (config.toml), 1 `fetch` (tomllib), 5 `read` (task-1.md, `src/__init__.py`, `tests/test_smoke.py`, `tests/__init__.py`, `config.toml`), tutte con `ae75e2b139ac5a408`. Il rapporto le riporta uguali. `grep-non-registrati.txt` dice 0.
- ✅ Nota: `research-1.md` ha i quattro file, una fonte, «Cosa ho trovato», riga `esito: valida`. `eventi-ricerca.jsonl`: seq 11 `ok:false` (tre file non letti, 04:41:14), seq 12 `ok:true` (04:41:22, otto secondi dopo). Nel flusso di passo2 l'ordine è: `research submit` (riga 112), tre `Read` (124-139), `Read config.toml` (151), seconda `research submit` (159), primi `Write` (172, 197). Quindi nessuna modifica prima della nota valida: vero. Il «solo con i glob di cat e ls» è vero (riga di Bash del subagente `ls src tests && cat tests/*.py | head -30`). Nessun `research_reminder` in `events.jsonl` (20 eventi).
- ✅ Veti: `coordinator` (redirect Bash del piano, poi `Write`) e `plan_check` (nessun task, poi corretto con `Edit`); nessun `research_gate`. Coincide con `stats.json` (`vetoes` 2) e con il flusso di passo1 (righe 125, 137, 149).
- ✅ Verdetto: `task_change` seq 20 `done`, `approved`. Il revisore cita `R-BASE-06` e l'`os.chdir` ridondante (flusso passo2, riga 281/286): il rapporto lo riporta con le stesse parole.
- ✅ Il rifiuto dal vivo non si è visto e perché: detto due volte (sezioni «Nota, avvisi e rifiuti», tabella «Esito», «Limiti»). Prova deterministica nominata: `test_real_rules_base_blocks_l1`/`_l2` del Task 5.
- ✅ Precaricamento: il rapporto distingue bene l'«indizio» di `precarico.txt` (metodo: indizio, 3 righe `R-BASE-`, nessun `agent_transcript_path` nello stream: confermato, il flusso non lo contiene) dalla prova di `precarico-trascrizioni.txt`. Ho controllato le trascrizioni: revisore, riga 2 = messaggio `user` `isMeta` con `<command-name>rules-base</command-name>`, prima di qualsiasi turno dell'assistente; implementatore, riga 4, idem; nessun `tool_use` (né `Read` né `Skill`) in testa. Il rapporto dice onestamente che la prova è un file scritto a mano e che il titolo da solo non basta.
- ✅ Versione `2.1.314` in `registro-1/versione-claude.txt`; `approved: 2026-11-01` in `skills/rules-base/SKILL.md`.
- ✅ Anonimizzazione: `grep -rIl -e USER -e HOST` su rapporto ed evidenze: vuoto. `"session_id"` è sempre `SESSION-ID` (970 occorrenze, nessun altro valore), `"session"` `SESSION-ID` o null. Negli stream-json nessun messaggio `init` e nessun evento `SessionStart` se non i due di tollgate (passo2, `additionalContext` di tollgate). Nessuna forma di token (grep di `sk-`, `ghp_`, `gho_`, `ghs_`, `github_pat_`, `xox`, `AKIA`, `eyJ`, `Bearer`: solo la parola «tokens» di `stats.json` e `thinking_tokens`). `claude.err` vuoti. Gli UUID rimasti sono `hook_id`/`uuid` dei messaggi.
- ✅ Lingua: italiano chiaro. Limiti presenti: `WebFetch` con `--allowedTools`, un solo lavoro, divieti a prefisso, prova di precaricamento a mano, uscita di `prepara` non salvata.
- ⚠️ Non ho rilanciato nulla (né `claude` né `tests/run`); `bash -n spikes/run-b1-flow.sh` ok.

### Punti di forza

Rapporto fedele alle evidenze fino al dettaglio dei secondi e dei numeri di riga; distingue prova e indizio; non spaccia per prova il blocco dal vivo mai visto; la prima consegna rifiutata della nota (seq 11) è riportata, e mostra comunque il controllo delle letture in azione.

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor**
1. `passo1/tentativo-1/claude.jsonl:68`: il messaggio `user` contiene per intero il testo della skill `superpowers:writing-plans` di un altro plugin, con la base directory `/home/USER/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/writing-plans`. Non è un `init` né un hook di `SessionStart`, ma rivela un plugin installato (con versione) e pubblica testo di terzi (licenza MIT). Coerenza con la scelta fatta per gli `init`: togliere la riga o sostituirla con un segnaposto, oppure dire nel rapporto che resta. Il rapporto, nella sezione di anonimizzazione, dice solo di `init` e `SessionStart`.
2. Limite non dichiarato: la prova gira con i plugin dell'utente attivi (il modello ha invocato `superpowers:writing-plans` in passo1, `claude.jsonl:60`). Non cambia l'esito (il precaricamento è provato dalle trascrizioni), ma va tra i limiti, come differenza dalla prova in un ambiente pulito.
3. `registro-1/comandi-modello.txt:1,7`: righe di intestazione con `/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/b2/...` (home sostituita, ma resta la struttura delle cartelle di lavoro). Innocuo, solo coerenza con «nessuna cartella home reale»; si può ridurre al percorso relativo.
4. Il rapporto usa come argomento forte «titolo + nessuna lettura di `rules-base/SKILL.md`». Ne ha uno più forte, verificato sopra: il messaggio `isMeta` è prima di ogni turno dell'assistente, quindi non può essere una chiamata `Skill` dell'agente. Aggiungerlo a «Cosa dice la prova» (una frase).
5. Fuori ambito ma notato: `docs/verifiche/evidenze/gh-p4/` contiene `/home/USER/...` (`caso-verde-pulita-...-case.json:18`, `comandi.log:260`). Non è di questo task; segnalo per la revisione finale, dato che il repo è pubblico.

### Valutazione

**Qualità del task:** Approvato.
**Motivo:** il rapporto dice il vero rispetto alle evidenze su passi, durate, consumo, letture, nota, eventi, verdetto e token; è chiaro su esito non composito, rifiuto dal vivo non visto e prova deterministica; il precaricamento è provato (e confermato da me sulle trascrizioni) e distinto dall'indizio. Restano solo rifiniture sull'anonimizzazione e sui limiti.
