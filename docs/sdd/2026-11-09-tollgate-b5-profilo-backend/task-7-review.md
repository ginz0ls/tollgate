# Revisione Task 7 (commit 161882a, pacchetto 6464a1d..161882a)

### Aderenza

- ✅ `B1_FLOW_CASE=backend`: ogni ramo del caso presente (`PROJ`, `PROJ_FILES`, `PLAN_REL`, `ISSUE_TITLE`, `OUT=b5/flusso`, valori ammessi con messaggio che nomina i quattro, regole vere obbligatorie, `scrivi_dati_gh`, `proponi_profilo backend server/app.py`, `controlla`, `trascrizioni`/`tipi` (`CASE != b1`), `limiti.txt`). `spikes/run-b1-flow.sh` (diff, blocchi `DEPLOY_CLIS` e `registra`).
- ✅ `DISALLOWED` con `backend`: `DEPLOY_CLIS` più `supabase deno node`, quattro forme per ognuno, nello stesso ciclo di `infra`; `infra` resta senza i tre (asserito da `test_flow_disallows_service_clis_backend`). `b1` e `ai` non entrano nel ciclo (condizione `infra || backend`): comportamento invariato.
- ✅ Il grep di `registra` resta condizionato al caso (`infra || backend`); `test_registra_deploy_clis_only_for_infra` (caso `b1`) resta verde.
- ✅ Script senza `--force` (fuori dal divieto `git push --force` già presente), `--no-verify`, `kill ` nel codice nuovo (controllato sulle righe `+` del diff; `bash -n` ok).
- ✅ Progetto di prova: nessuna credenziale né file di Wrangler/Vercel (`ls -a`, `.gitignore` con le sei voci); `.ts` solo testo; nessun `__pycache__`; `server/app.py` in sola libreria standard con funzione pura per rotta.
- ✅ D2: `edge/index.ts` importa da `cloudflare:workers`; `test_real_flow_case_backend_prepara_proposes_profile` controlla prima un marcatore del frammento vero (`templates/profiles/backend.toml`, chiave `detect.content`), poi `/server/**`, `edge/index.ts` e nessun percorso `supabase*`.
- ✅ D10: prefisso solo sui test che leggono i file veri; `test_flow_case_backend_out_dir` e `test_flow_disallows_service_clis_backend` senza (solo `controlla`/`disallowed`); rinominati i sette di M-5 e i quattro gemelli `ai`, solo il nome (diff: `-def test_x` / `+def test_real_x` senza altre righe toccate in quei corpi); `tests/test_rules_*.py` non toccati.
- ✅ Lezione di B4 (decisione 14): `issue-1.md` e `piano-L1.md` chiedono rotta e test, dicono «Non avviare un server su una porta», non nominano contratti, indirizzo, prova locale, pagina ufficiale, «chi li usa» (regex del test e lettura diretta).
- ✅ `togli-pagine` per `Bash`: `SAVED_TOOLS` con `Bash`; `_saved_copy` cerca `tool-results/` nel testo del comando (con lettore); `_swap_saved` sostituisce blocco **e** `tool_use_result.stdout`; il rilevamento guarda anche `stdout` (blocco già segnaposto, stdout col testo: segnalato e riscritto). Verificato eseguendo i due test: passano; JSON valido (round trip nel test); `cat app.py` invariato; idempotente.
- ✅ Titolo `# Regole backend (versione 1)` in `AREA_TITLES`.
- ✅ Il report dichiara onestamente l'assenza di un rosso contro il codice vecchio. Capacità di fallire dei test nuovi, valutata togliendo mentalmente il ramo nuovo: `test_togli_pagine_bash_reading_saved_copy` (senza `Bash` in `SAVED_TOOLS` zero blocchi; senza lo swap di `stdout` il testo TERZI resta), `test_third_party_detects_bash_stdout` (senza il ramo `left` l'atteso `["2: copia salvata (15)"]` diventa `[]`), `test_flow_disallows_service_clis_backend`, `requires_real_rules` e `unknown_value_names_backend` (senza `backend` nel `case` il valore muore con un altro messaggio), `flags_service_clis_backend` (senza la condizione `|| backend` il comando non è riportato), `reads_backend_title` (senza il titolo in `AREA_TITLES` manca la riga). Tutti capaci di fallire.
- ⚠️ Non verificabile senza lanciare lo script/la suite: `test_real_flow_case_backend_prepara_*`, `project_verifies`, `registra_*` (passano per `prepara`/`registra` con HOME finta; ho eseguito solo gli otto test puri: `togli_pagine_bash`, `third_party_bash_stdout`, `disallows_service_clis_backend`, `out_dir`, `requires_real_rules`, `unknown_value`, `task_does_not_list_report_lines`, `no_credentials`: OK). Mi fido dell'evidenza in `task-7-suite.txt` per il resto.

### Punti di forza

- Un solo punto di rilevamento (`_third_party`) e un solo punto di scrittura (`_swap_saved`): il rilevatore e il riscrittore non possono divergere. Il caso «blocco già segnaposto, stdout col testo» è gestito e testato in modo isolato.
- Il bug intermedio (stdout considerato anche senza copia salvata: 271 falsi blocchi nelle evidenze) è stato riconosciuto e risolto vincolando `stdout` a `label`.
- Test del progetto di prova ben mirati (marcatore del frammento prima dei `paths`, nessun percorso `supabase*`).
- `limiti.txt` dichiara i limiti reali del divieto (`env VAR=...`, `sudo`, `xargs`, `bash -c`).

### Rilievi

**Critical:** nessuno.

**Important:** nessuno.

**Minor**

1. `spikes/b1/flowreg.py` (`SAVED_READERS`, riga ~33; `_saved_copy`): la lista dei lettori è una whitelist, quindi il filtro fallisce aperto. Verificato eseguendo `_saved_copy`: `python3 -c "print(open('…/tool-results/x.txt').read())"` e `jq . …/tool-results/x.json` ritornano `None` (stdout di terzi nelle evidenze pubbliche, non redatto né rilevato), mentre `echo more > …/tool-results/y` ritorna `y` (falso positivo innocuo). La lista (`cat, sed, head, tail, grep`) è quella del piano; l'implementatore ha aggiunto `rg awk less more nl`. Correzione: invertire la logica (qualunque `Bash` il cui comando nomina un percorso `tool-results//<file>` riscrive il risultato, salvo `ls`/`find`/`stat`/`wc`), oppure aggiungere almeno `jq`, `python3`, `wc`-no, `xxd`, `strings`, `base64`. Rischio residuo coperto dalla verifica a mano prima del rapporto (Global Constraints), quindi Minor (lettore limitato dal piano).
2. `flowreg.py:_swap_saved`: `tool_use_result.stderr` non viene sostituito (un `grep` con errore potrebbe riportare un pezzo del nome del file, non testo di terzi): nessun effetto reale, solo da sapere.
3. `tests/test_b1_scripts.py` (`test_real_registra_flags_service_clis_backend`): l'assert negativo `"git add supabase"` non può mai fallire (il comando riportato in `risky` sarebbe `git add supabase/functions/hello/index.ts`, che contiene quella stringa solo se erroneamente riportato: va bene, ma `"cat edge/index.ts"` è asserito sul `bash: …` esatto altrove e qui sul sottostringa; coerente con `infra`, nulla da fare). Più utile: nessun test sul caso `registra` di `backend` con `node` dentro un percorso (`cat node_modules/x`), che il regex non riporta perché `node` è in posizione di comando solo dopo `/`: `cat /x/node y` darebbe un falso positivo noto e innocuo.
4. `spikes/b5/flow/server/app.py`: la classe `Handler` (usa `BaseHTTPRequestHandler`) non è esercitata da nessun test; è codice di sola vetrina per il profilo, coerente con «gestore di rotte in sola libreria standard», non serve altro.

### Valutazione

**Qualità del task:** Approvato

**Motivo:** requisiti e decisioni D2/D10/16/14 rispettati e verificati sul diff; i test nuovi sono capaci di fallire. Il solo punto di attenzione è la whitelist dei lettori di `togli-pagine` (Minor, imposta dal piano) che lascia passare `python3`/`jq` sulle copie salvate: va coperta dalla verifica a mano delle evidenze nel Task 8.
