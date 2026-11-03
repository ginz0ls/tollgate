# Ri-revisione 1 del giro di correzione finale (b3-profilo-ai, 9b17663..dd0132d)

Letti: regole, cautele, revisione finale, brief, report, diff. Controlli miei, in sola lettura: scansione Python (`-I -B`) di tutti i `.jsonl` di `docs/verifiche/evidenze/` e `grep`; ricontata delle tabelle di `ai-fonti.md`; test mirati `python3.11 -B`: `test_fragments` + `test_manifest` (71 OK), `test_b1_scripts.FlowScriptTest` (40 OK, include `test_committed_evidence_has_no_long_web_results`).

### Verdetti sui rilievi

- **I-1, pagine dei fornitori nelle evidenze:** INDIRIZZATO. Scansione dei `.jsonl`: ogni `tool_result` di WebFetch/WebSearch in b3 è di 124 caratteri (4 segnaposto `[pagina di terzi tolta dalle evidenze: <URL>, <N> caratteri]`); in b1/b2 il massimo è 2.404; nessun `tool_use_result` lungo; ogni riga è JSON valido (0 righe non JSON). `grep` di titoli e testo delle due pagine: nessuna ricorrenza. `registra` lancia `togli-pagine` (`spikes/run-b1-flow.sh`, riga con `fallisce togli-pagine $?`), con test `test_flow_registra_strips_third_party_pages_from_the_streams`, più i due test di `flowreg` e quello sulle evidenze versionate. Rapporto aggiornato (`docs/verifiche/2026-11-01-b3-prova-flusso.md`, anonimizzazione). Il commit `f8f5331` conserva ancora le pagine nella storia: il report lo dice e rinvia la scelta all'utente prima della prima spinta (giusto, vedi Verdetto).
- **M-5, tre frasi e marcatore:** INDIRIZZATO. `templates/profiles/ai.toml:41` ha `"from \"openai\""`; `ai-fonti.md:81` riga con esito «ok per decisione dell'utente del 2026-11-02, non per una citazione», nessuna citazione inventata; `:98` e l'intestazione `:5` aggiornate; `ai.md` punto 4 dice la decisione in parole semplici; «coprono quasi tutti i casi» non c'è più in nessun file (`grep`); «rinumerano» sostituito da «il suo numero non si riusa: le altre tengono il loro»; `--propose` per un progetto nuovo e `--update` per uno che ha già tollgate. `test_detect_markers_verified` e `test_real_markers_not_in_tollgate_bin` verdi (il primo impone la corrispondenza fra marcatori e righe `ok`).
- **M-6:** INDIRIZZATO. `agents/implementer-ai.md:51` «ciò che serve».
- **M-7:** INDIRIZZATO. Riga nel rapporto della prova con il `parent_tool_use_id` del lancio `Revisione task 1`. La riga della prova in spec 16 non è toccata: il brief chiedeva solo il rapporto, accettabile.
- **Conteggi nel piano principale:** INDIRIZZATO. Ricontati: regole 48 righe (45 `ok`, 3 `no`, tutte di R-AI-06); marcatori 20 righe, tutte `ok` (una per decisione dell'utente). Il piano (riga 271) dice proprio questo.
- **Attribuzione `test_page_lists_every_rule`:** INDIRIZZATO. Esiste in `tests/test_rules_ai.py:311`; il piano ora dice `T\`test_rules_ai.py\``.
- **Rinvii M-1 e M-4 in «A B4-B7»:** INDIRIZZATO. Tre bullet nuovi (test sulla radice vera con i nomi delle classi, cartelle `agents/` e `prompts/` con la soluzione proposta, deriva e tipi dei frammenti).
- **M-2:** INDIRIZZATO. `tests/test_manifest.py`: `assertEqual(set(afm), set(gfm))`; test verde; RED mostrato nel report.
- **M-3:** INDIRIZZATO. `fragments.py` fa passare i valori da `config._set_key` e rilancia come `FragmentError` col nome del file; `test_load_rejects_wrong_value_types` copre `paths = "x"`, `min_level = 1`, `skills = [1]`, `min_level = "L9"`, `agent = 3`; verde.
- **Tetto di 5.000 invece di 2.000:** GIUSTO. Le evidenze vecchie di B1 e B2 hanno risultati da 2.404 e 2.202 caratteri (riassunti brevi, già pubblici da giorni); con 2.000 il test costringerebbe a riscriverle senza guadagno. Le pagine vere erano 14.616-22.794, ben sopra 5.000. Resta un rischio piccolo: una pagina breve (sotto 5.000) passa, ma il testo di terzi in quella misura è un riassunto, non una pagina intera. Accettabile.
- **Nessuna regola cambia, `approved` invariato:** CONFERMATO. `git diff 9b17663 dd0132d -- skills` è vuoto; `agents/` ha solo la parola di M-6.

### Danni nuovi nel diff della correzione

Nessuno Critical/Important. Minor:
- **Minor. `spikes/b1/flowreg.py` (`togli_pagine`):** riscrive solo `tool_use_result` quando `result` è una stringa o `tool_use_result` è una stringa; per WebSearch il campo ha un'altra forma (non presente in nessuna evidenza, non verificata), quindi un testo lungo potrebbe restare lì nelle prove future. Anche il test sulle evidenze controlla `tool_use_result` solo se contiene `codeText` (forma di WebFetch). Il test sui `tool_result` resta una rete, ma un `tool_use_result` di WebSearch sfuggirebbe. Da verificare alla prossima prova con WebSearch.
- **Minor. Rimpasto delle righe:** le righe riscritte da `json.dumps` perdono i separatori compatti originali (diff delle sole 4 righe, JSON valido). Nessun effetto.

### Osservazioni fuori ambito

- `docs/verifiche/evidenze/b3/flusso/passo1/tentativo-1/claude.jsonl:96` (109.677 caratteri) e `:139` (28.919) sono l'espansione del testo della skill `claude-api` inclusa nel Claude Code (messaggio utente sintetico, non un risultato di WebFetch): è testo di Anthropic, integrale, nel repo pubblico. Non era nel brief, non è stato toccato dalla correzione, e lo stesso tipo di riga c'è già in b2 (`passo1/tentativo-2`) e nelle evidenze di `gh-p4`/b1, quindi c'è un precedente accettato. Va però detto all'utente insieme alla questione della storia di `f8f5331`, perché è la stessa classe di rischio (testo del fornitore senza licenza aperta). Il test di tetto non lo prende (guarda solo WebFetch/WebSearch).

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.

Prima della prima spinta restano due scelte dell'utente, già note o da segnalare: la storia con `f8f5331` (pagine di WebFetch) e le righe della skill `claude-api` di Claude Code nello stesso stream.
