# Revisione Task 8 (rapporto della prova reale ed evidenze), sola lettura

Controllato: rapporto `docs/verifiche/2026-11-10-b6-prova-flusso.md`, `docs/verifiche/evidenze/b6/flusso/` (tutti i file, `claude.jsonl` dei due passi riga per riga con Python), brief, report. Nessuna suite, nessuna rete, nessun `claude`.

### Aderenza
- ✅ `Esito: riuscita` giusto: `exit-codes.txt` e `esito.txt` dicono un solo tentativo per passo, uscita 0; non composito.
- ✅ Passi, turni, costi, durate: 23 turni / 0,5119 USD / 109 s (passo 1); 16 turni / 0,9405 USD / 176 s (passo 2) dagli eventi `result` e da `esito.txt`. Token per agente e totale (179.600) tornano con `stats.json` e `events.jsonl`.
- ✅ Tipi di agente (`tipi-task.txt`), 4 agenti, titoli `isMeta: sì` nei quattro subagenti (`trascrizioni.txt`), `precarico.txt` «solo indizio», `comandi-rischiosi.txt` vuoto, note di ricerca valide e consegnate prima della prima modifica (task 1: riga 164 prima della Write a 186; task 2: nota a 404/415, poi modifica a 418), conteggi di `lookups.txt` e degli strumenti, commit `8ad7a20`/`4b991ab`/`d360da3`/`e5c5df6` (`git-log-worktree.txt`).
- ✅ Origine delle regole nel passo 1: il rapporto lo dice bene. Il modello legge `tollgate.toml` (solo gli id, `claude.jsonl` passo 1 righe 128/135), poi carica da sé `tollgate:rules-frontend` con lo strumento `Skill` (tool_use riga 156, risultato con il testo 163-164) e solo dopo scrive il piano (Write riga 182), che cita 01, 02, 04, 06, 09, 11 e «04/08/12». Controllato: nessun altro canale porta il testo delle regole (l'hook `UserPromptExpansion` è di 306 caratteri e non le contiene).
- ✅ Il revisore cita da sé regole che il task non nomina: elenchi del rapporto esatti (task 1: 04, 05, 06, 08, 09, 12 in più; task 2: 03, 04, 05, 06, 08, 09, 11, 12 in più, dove la 12 è solo nel rilievo). `task-1.md` e `task-2.md` non contengono nessuna `R-…`.
- ✅ Ramo di R-FRONTEND-01 (versione non dichiarata, react.dev), R-FRONTEND-02 (`StatusBadge.tsx` non riusabile), pulsante con `aria-label="Salva"` e `span aria-hidden`, `p#salvato role="status"` vuoto, in pagina e nel componente: tutto nel diff dello stream (`review-2.diff` riga 487, Bash del task 1/2).
- ✅ Ripulitura: JSON valido su ogni riga di `claude.jsonl` (passo 1 e 2), `events.jsonl`, `eventi-ricerca.jsonl`. Nessuna occorrenza di nome utente, host (6 caratteri, cercato per valore), `ginz0ls`, `sainapse`; `/home/` solo come testo nel rapporto (nessun percorso `/home/<altro>` nelle evidenze); nessuna forma di token (`sk-ant`, `ghp_`, `github_pat_`, `vercel_`, AKIA, JWT); `session_id` tutti `SESSIONE-1/2`; stringhe da 40 caratteri solo percorsi, SHA, firme. Nessun elenco plugin né `SessionStart` di terzi: resta solo l'hook di tollgate. Testo di skill di terzi: `writing-plans` sostituita da segnaposto; `test-driven-development` appare solo come «Launching skill», senza corpo; `execute` e `rules-frontend` sono di tollgate.
- ✅ Il risultato breve di `WebFetch` (1238 caratteri, react.dev) è dichiarato nel rapporto («Limiti»), con la descrizione giusta (riassunto in italiano, esempio JSX, due frasi tra virgolette).
- ⚠️ Non verificabile dalle evidenze: la proposta di `init` («4 file», `backend`/`ai`/`infra` non proposti, P9 dal vivo) e «`plan-check` ok» nel passo di `prepara`. In `evidenze/b6/flusso/` non c'è nessun file con l'uscita di `init --propose` né di `plan-check`: restano solo il `tollgate.toml` letto dal modello (`paths`) e il commit `e5c5df6`. Vengono dal controller (`progress.md`).
- ⚠️ «Compare anche una riga `isMeta: no` per ciascun titolo: è la richiesta all'API già composta»: interpretazione non provata dalle evidenze (`trascrizioni.txt` dà solo i titoli).

### Punti di forza
- Il rapporto non nasconde che il piano del passo 1 è scritto con le regole già lette, corregge il brief e sposta la prova sul task 2 e sui titoli `isMeta`: onesto e corretto.
- Evidenze pulite e coerenti; conteggi esatti; limiti ben esposti (pagina statica, nessun browser, `verify` «uncounted»).

### Rilievi

**Important**
1. `docs/verifiche/2026-11-10-b6-prova-flusso.md`, sezione «Precaricamento» (ultimo punto) e «Limiti» (voce «Le letture del revisore non sono registrate… lo stream non le mostra»): **falso**. Lo stream mostra le letture dei revisori (righe SUB: task 1 `Read` di `review-1.md` 288, `task-1.md` 297, `review-1.diff` 300; task 2 `Read` 463, 472, 475; `tool_uses: 3` in entrambi i resoconti, righe 321 e 496). Nessuna è il piano. Quindi l'incertezza residua («non si può escludere che abbia letto anche il piano per 04, 06, 08, 09, 11, 12») cade: tutte le regole citate dal revisore e assenti da `review-N.md`/`task-N.md` possono venire solo dalla skill precaricata. Correggere le due frasi e rafforzare la conclusione (e togliere la voce dai limiti).
2. Stesso file, «Proposta di `init`» e riga della tabella «`init --propose` … `plan-check` ok»: affermazioni che non stanno nelle evidenze (⚠️ sopra). Dire che vengono dall'osservazione del controller e non sono salvate, oppure far salvare l'uscita di `init --propose` e `plan-check` tra le evidenze (ripulita).
3. Stesso file, «Comandi del modello» e «Scostamenti»: il modello ha lanciato `tollgate plan-check` nel passo 1 (`claude.jsonl` passo 1 riga 193, esito 204) e **ha fallito**: «invalid choice: 'plan-check'», `exit=2`. Il rapporto lo elenca tra i comandi `tollgate` senza dire che non esiste, e non lo mette tra gli scostamenti. Va segnalato (è un comando inventato dal modello, probabilmente dalla skill o dal piano; il piano fu registrato lo stesso dall'hook alla Write, riga 190).

**Minor**
4. Riferimenti di riga dello stream incoerenti di uno: «riga 134» (tollgate.toml) è 128 (uso) / 135 (risultato); «riga 181» (piano) è 182 (la 181 è il testo che lo annuncia); «riga 350» (`task-2.md`) è 351; «riga 293» è 294; «riga 468» è 469. Solo «righe 155-163» è esatto.
5. «Rilievo `R-FRONTEND-12`, `src/components/SaveButton.tsx:22`»: il file ha 11 righe; la riga 22 è quella del diff (`review-2.diff`). Scrivere «riga 22 del diff».
6. Il rapporto non dice che l'implementatore del task 1 ha letto il piano (`lookups.txt` n. 5, stream riga 147), quindi per il task 1 il report con 01/02/11 non è un testimone pulito: il rapporto lo usa già bene per il task 2, ma una frase lo renderebbe esplicito.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** Evidenze e ripulitura sono a posto e l'esito è giusto, ma il rapporto contiene un'affermazione contraddetta dallo stream (letture del revisore), tre punti non fondati o taciuti (init/plan-check non nelle evidenze, `plan-check` fallito non riportato). Sono correzioni di testo, nessun cambio alle evidenze se si accetta il punto 2 come dichiarazione.
