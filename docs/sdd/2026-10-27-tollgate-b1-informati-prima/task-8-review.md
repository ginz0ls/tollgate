# Revisione Task 8 (commit e28570e, intervallo 98994fc..e28570e)

### Aderenza
- ✅ `ImplBrief`/`ReviewBrief`: tutti i campi nuovi con predefinito (`bin/tollgate_analysis/brief.py:83-84,164-168`).
- ✅ Sezione dell'implementatore prima di «Istruzioni» (`brief.py:141-142`), nomi dalle costanti di `research`, comando con heredoc da `research.submit_command`, frase `--fix` (`brief.py:120-122`).
- ✅ Scostamento «Giro di correzione: » (`brief.py:121`): accettabile. Il testo richiesto («la nota è in <percorso>: integrala e risottomettila solo se questo giro tocca librerie o servizi nuovi») è contenuto intero e `test_fix_brief_points_to_note` (`tests/test_brief.py:488-494`) e `test_fix_brief_points_to_delivered_note` (`tests/test_taskcmd.py:740-748`) lo verificano alla lettera.
- ✅ Recinto della nota del revisore: `_block(b.research_note)` dopo `DATA_NOTE` (`brief.py:188-189`), cioè lo stesso `fence`/`_block` già usato nel modulo, nessun secondo meccanismo. Il test usa una nota con ``` e verifica il recinto da 4 backtick e l'ordine rispetto a `DATA_NOTE` (`test_brief.py:521-529`).
- ✅ Gravità D13: acceso → `major` (+ `missing` solo senza nota); spento → `moderate`, nessun `missing` (`brief.py:194-199`). `line` 1, `file` = percorso della nota o primo file del diff (`brief.py:192-193,201-203`). La nota mancante come `missing` coincide con D13; con nota non pertinente niente `missing`, coerente.
- ✅ `first_diff_file` scritto da `taskcmd.review_prepare` (`taskcmd.py:406`, `changes[0].path`).
- ✅ Interruttore letto da `db.BIN_PATH.parents[1] / research.RULES_BASE` (`taskcmd.py:327-334`); `BIN_PATH = <radice>/bin/tollgate` (`tollgate_core/db.py:19`), quindi `parents[1]` è la radice. OSError → spento. Test con radice temporanea (`test_taskcmd.py:789-798`).
- ✅ D2: `research.active(work["research"], componente)` in taskcmd (`taskcmd.py:322-324`) e SubagentStart (`subagent_start.py:264-265`). Lavori legacy e componente spento: nessuna sezione né riga; test `test_legacy_*`, `test_component_off_brief_without_research`, `test_component_off_review_brief_without_section`, `test_component_off_reminder_without_note`.
- ✅ D17: percorso da `research_cmd.note_path` (`taskcmd.py:300,369,404`).
- ✅ Promemoria SubagentStart (`subagent_start.py:264-269`) con il testo richiesto.
- ✅ `agents/task-reviewer.md:33` corrisponde allo Step 3 (sezione «Nota di ricerca», nota esistente, fonti pertinenti, motivo di «Nessuna fonte esterna», `rule` `nota di ricerca`, gravità e `file`/`line` dal brief, `missing` se lo chiede il brief) e dichiara la nota dato non istruzione.
- ✅ Strati: `brief.py` importa solo `research` (sorella di `tollgate_analysis`), resta puro; `subagent_start.py` (checks) importa `tollgate_analysis`, non `tollgate_flow`; `taskcmd.py` importa `.research_cmd` (flow). Nessun `__pycache__` in git né nel worktree (`git ls-files` e `find`: zero). Working tree pulito.
- ⚠️ Non rieseguito `tests/run` (affidato al report: 3104 OK con 3.11 e 3.
  Evidenza RED dichiarata come indiretta dall'implementatore: lacuna di processo, non di correttezza).

### Punti di forza
- Riuso di `fence`/`_block`/`DATA_NOTE`, nessuna logica duplicata; sezione gated in un solo punto per ogni brief.
- Test che asseriscono sul testo reale (sezione estratta con split su «## Nota di ricerca»/«## Verdetto», ordine recinto/DATA_NOTE, `assertNotIn("`major`")` nel caso spento).
- Il caso interruttore acceso è provato con una radice del plugin temporanea invece di toccare file veri.

### Rilievi
**Critical:** nessuno.

**Important:** nessuno.

**Minor**
1. `bin/tollgate_analysis/brief.py:192-193`. Se la nota manca e il diff non ha file (task `no_changes`), `where` ricade su `str(b.research_note_path)`, cioè la stringa `"None"` (`taskcmd.py:404-405` passa `None` quando la nota manca). Scenario: lavoro con passo attivo, task già soddisfatto senza commit, nessuna nota: il brief dice `file` `None`. Correzione: far passare a `taskcmd` sempre il percorso atteso della nota (`note_path(...)`) in un campo distinto dalla presenza della nota, oppure ricadere su un testo esplicito; aggiungere un test per il caso.
2. `bin/tollgate_analysis/brief.py:106-123`. La decisione 1 dice che il brief avvisa che una nota con `TOLLGATE_` nel testo viene negata; l'avviso sta solo in `agents/implementer.md:26`, non nel brief del task. Il brief del Task 8 non lo elenca, quindi non è un difetto di aderenza; è una rifinitura (una riga).
3. `tests/test_brief.py:539`: `f"`rule` `nota di ricerca`"` è una f-string senza segnaposto (innocua).

### Valutazione
**Conformità alla spec:** ✅ (tutti i requisiti del brief, D2, D8, D13, D14, D17 verificati sul diff).
**Qualità del task:** Approvato. **Motivo:** implementazione fedele, riuso del meccanismo di recinto esistente, strati rispettati e test che asseriscono comportamento reale; restano solo tre minor, il solo con effetto visibile è il `file` `None` nel caso limite senza diff.
