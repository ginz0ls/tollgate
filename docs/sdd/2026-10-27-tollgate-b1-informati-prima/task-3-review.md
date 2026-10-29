# Revisione Task 3 (c4fb8dd): research.py, read_targets

### Aderenza
- ✅ D1: `ATTRIBUTE_UNNAMED_TOOLS = frozenset()` (research.py:162), test :677. ✅ D2: `active` (:175), `test_active`.
- ✅ B1-V2: `doc_library` legge `libraryId` poi `context7CompatibleLibraryID` (:170,:200), test sintetico; `resolve-library-id` (solo `libraryName`) non conta come docs. `DOC_MCP_TOOLS` coincide con la decisione 6. ✅ B1-V7: nessun `APPROVAL_FILE`.
- ✅ D13: tabelle per comando (bash.py:33-62), `-` escluso, asserzioni `head -n 5 f`, `grep -A 3 foo f`, `cat a | head -n 5` presenti. `Cmd.redirects` non porta `<`: rispetta il ruling (nessun conteggio).
- ✅ Ruling: `grep -l/-L/-c/-q`, `rg --files` danno `[]` (verificato).
- ✅ Review Focus 2: `normalize_path` con `..`, assoluto nel checkout principale, `~`, `/wx` vs `/w`, vuoto, radice: tutti `None`; `check_note` normalizza con `cwd=worktree`. Verificato con prove.
- ✅ Review Focus 3: schema/host minuscoli, porta predefinita, frammento, barra finale, credenziali tolte, query mantenuta, schemi non http e URL senza host o con porta non valida `None`.
- ✅ Anti-obiettivi: `search`/`glob`/`fetch` non soddisfano un file; `search` non soddisfa una fonte; il modello di `submit_command` non compilato produce problemi (test). `submit_command` ha il delimitatore tra apici e niente `TOLLGATE_`.
- ✅ Strati: research.py importa solo stdlib. `enforced` legge `approved` solo nel frontmatter (corpo e dopo la chiusura: falso).
- ⚠️ Non verificato: la suite completa (report: 2967 OK su 3.11 e 3.13); non rilanciata per regola.

### Punti di forza
Modulo puro, piccolo, costanti di sezione esportate; test ricchi (30 + subTest) con casi negativi veri; `check_note` raccoglie tutti i problemi; parser delle opzioni di `read_targets` scritto bene (opzione corta in coda al gruppo che consuma l'argomento, `--x=v`, `--`).

### Rilievi

**Important**
- research.py:285-290 + :258, :256. `parse_note` segnala il superamento di 8000 caratteri ma poi analizza comunque tutto il testo, e `_SEPARATOR.split` (e `_HEADING`) sono quadratiche su lunghe sequenze di spazi. Misurato: una riga `- a` + 8.000 spazi + `b` richiede 0,34 s, con 100.000 spazi 53 s. La nota è testo non fidato dentro un hook/CLI con timeout, e il contratto è «mai un'eccezione» (qui un blocco). Correzione: se `len(text) > MAX_NOTE_CHARS` restituire subito la `Note` con il solo problema di lunghezza, senza analizzare (più un test con 100.000 spazi che finisce in tempi brevi).

**Minor**
- bash.py:45 (`--color`, `--colour` in `_READ_OPT_ARG["grep"]`): l'argomento di `--color` è solo opzionale (`--color=WHEN`); `grep --color foo f` consuma `foo` e restituisce `[]` (verificato) invece di `["f"]`. Falso negativo che fallisce in modo sicuro; togliere le due voci.
- research.py:192: `approved: null` / `~` / `|` contano come approvato (valore non vuoto). Improbabile; accettabile, ma se si vuole stretto escludere `null`, `~`.
- research.py:258: un percorso con « - » dentro (es. `docs/A - B.md`) viene troncato dal separatore e risulta «non letto». Raro; documentarlo o accettare solo ` — ` per i file.
- `less`, `sed` con opzioni lunghe abbreviate (`--line 5`) non gestite; `cat -` ecc. ok. Best effort dichiarato.
- Una cartella (`grep -r foo src/`) è restituita da `read_targets`: filtro al Task 4, come da ruling.

### Valutazione
**Qualità del task:** Da correggere (un solo Important).
**Motivo:** requisiti, decisioni del controller e Review Focus 2/3 rispettati e ben testati; resta da chiudere il costo quadratico di `parse_note` su testo non fidato, correzione di due righe.
