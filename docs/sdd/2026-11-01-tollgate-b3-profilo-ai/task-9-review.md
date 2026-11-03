# Revisione Task 9 (B3): prova reale con il profilo ai (0ecbfe8..925bc85)

### Aderenza
- ✅ Progetto `spikes/b3/flow/`: tutti i file del brief, più `tests/__init__.py` (D1); `tollgate.toml` identico a quello di b1 (asserito da `tests/test_b1_scripts.py` in `test_flow_case_ai_project_verifies`); nessun nome di modello (il solo `claude-` è il prefisso richiesto dal piano, `piano-L1.md:15,19,39`); `tests/test_smoke.py` non importa `services/`; `services/notify.py` importa l'SDK.
- ✅ `B1_FLOW_CASE` (`b1|ai`), `ai` richiede `vere`, OUT `b3/flusso`, `PLAN_SRC`/`PLAN_REL`/titolo/file di `controlla` dipendenti dal caso (`run-b1-flow.sh:62-70`, `:128-130`, `:173-177`). Casi b1/b2: invariati (stesso `scrivi_dati_gh` senza `api_status`, stesse stringhe; unica differenza visibile la riga `B1_FLOW_CASE: b1`).
- ✅ Ordine di `prepara` come da brief: dati gh finto (`scrivi_dati_gh ""`) -> commit base -> url/insteadOf -> push -> `proponi_profilo` (init sulla copia del plugin, gh finto nel PATH, stato con sentinella creata prima) -> copia del toml -> secondo commit -> push -> cartella della proposta spostata (non cancellata) -> `sha`, stati, `plan-check`. Si ferma se `[profiles.ai]` manca o non copre `services/notify.py` (test `..._refuses_without_profile`). Chiave di protezione = quella di `tests/fakegh.py` (il test passa solo se `init` sceglie davvero `detect`, quindi la chiave è letta).
- ✅ D15: `project_dir_name` = `re.sub(r"[^A-Za-z0-9]", "-", cwd)`; `registra` agisce solo con `ai`, rifiuta HOME vuota prima di creare il registro (`run-b1-flow.sh:401`), usa `glob` solo su `<home>/.claude/projects/<cartella>/<sid>/subagents/agent-*.jsonl`, non elenca altre cartelle, stampa solo i titoli esatti (`strip() in AI_TITLES`) e il nome del file; test con cwd con punto e spazio sotto HOME finta, sessione e cartella estranee ignorate, righe del compito non salvate.
- ✅ D1: `controlla` controlla tutti i file del caso; il verify del progetto copiato gira con esito 0 e senza `__pycache__`.
- ✅ Strumenti: `TOOLS` e `DISALLOWED` invariati; WebFetch/WebSearch ammessi; curl, wget, gh per percorso, `git push` verso http/https/ssh/git@ e forzati vietati. Coerenti con l'eccezione 3.
- ✅ Dubbio su `detect`: la scelta è giusta. `start` in `detect` aggiunge solo avvisi (`bin/tollgate_flow/start.py:334-342`, anche le issue di sentinel illeggibili diventano avviso), `_publish` del gate pubblica stati e non blocca (`bin/tollgate_gate/baseids.py:190`). Il repo di prova è Free/privato (decisione dell'utente: gate con detect su Free). B1 e B2 non lanciavano `init` e non davano `api_status`: lì la protezione risultava «non leggibile: proseguo»; non c'è un precedente da imitare e `protected` con protezione completa nel finto sarebbe una finzione più grande.
- ⚠️ Non verificabile (vietato eseguire): formato reale di `system init` (`cwd`, `session_id`) e posizione `subagents/` nel `claude` vero; se differiscono, `trascrizioni.txt` dirà «nessuna trascrizione» (fallimento visibile, non silenzioso).

### Punti di forza
- `scrivi_dati_gh` unifica la scrittura dei dati del gh finto senza cambiare l'uscita di b1/b2.
- Letture strette: nessun `listdir` della cartella `projects`, nessun contenuto di messaggio salvato (il test asserisce `SEGRETO`, `R-AI-01`, `HOME` assenti).
- Rotazione, mai cancellazione, della cartella della proposta; `die` con messaggio che contiene `profiles.ai` (testato).
- Il test `refuses_without_profile` e il test RED/GREEN documentato nel report.

### Rilievi
**Critical:** nessuno.
**Important:** nessuno.
**Minor**
1. `spikes/b1/flowreg.py` (funzione `trascrizioni`, riga `print(f"# ...: cartella {folder}, sessione {sid}")`): il `session_id` reale finisce in `trascrizioni.txt`, nelle evidenze del repo pubblico; nessun test lo esclude. Il nome della cartella invece è solo `/tmp/...` (nessun `/home`, nessun utente). Correzione: stampare un numero d'ordine al posto dell'id, oppure il Task 10 deve anonimizzare id di sessione nel rapporto. Nota: `passo*/tentativo-*/claude.jsonl` (comportamento già di B1/B2) contiene comunque id di sessione, e il messaggio `system init` del `claude` vero può contenere percorsi `/home/<utente>` (plugin, memoria): il rapporto del Task 10 deve citare solo estratti anonimizzati.
2. `flowreg.py` `trascrizioni`: `sid` viene dal flusso e finisce in un `Path` senza controllo (`/` o `..` uscirebbero dalle due cartelle). Il flusso è prodotto dal `claude` locale, quindi rischio teorico; un `re.fullmatch(r"[A-Za-z0-9_-]+", sid)` chiuderebbe la porta.
3. `tests/test_b1_scripts.py` fine di `test_registra_reads_only_matching_lines`: il commento «senza il caso `ai`…» non c'entra col test e `assertTrue(wt.is_dir())` non asserisce nulla di utile (il worktree lo ha creato il test stesso). Va tolto.
4. Il test non copre un `sid` ripetuto fra passo1 e passo2 (la deduplica `seen`) né la sessione assente (`cwd` mancante): coperture facoltative.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni D1/D15 rispettati, ordine di `prepara` e letture limitate alle due cartelle verificati sul diff; restano solo rifiniture (id di sessione stampato, controllo di `sid`, un'asserzione inutile).
