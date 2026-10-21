# Revisione Task 11 (0f648ba..170a6d0)

### Aderenza
- ✅ Riga 5: `tests/test_cli.py` ArgvSignalTest, segnale reale via `hooks/run`, due test come da brief.
- ✅ Riga 21: `config.py:194` `re.fullmatch`; test con nome a capo finale.
- ✅ Righe 22-23: `git.range_base` usata da `commit_changes`, `taskcmd._range`, `task_verdict._task_files`, `post_bash`; `import json` riordinato; `TaskFilesTest` copre profilo da soli `paths`, `[blocca]`, nessun file, diff illeggibile (fail-closed `changes`); test di `range_base` in `test_git.py` (D18c).
- ✅ Riga 24: classi sopra `__main__` in verdicts, profiles, checkpoint (carry) e bash; scansione mia di `tests/*.py`: nessun altro file con classi o test dopo il blocco.
- ✅ Riga 25: problema riportato una volta; test con tre forme di risultato senza id.
- ✅ Riga 32 (D18a): frase nella docstring di `violations.scope_exempt` (violations.py:97), non in `finishcheck`.
- ✅ Righe 38-40: `active_profile_names` in `tollgate_core` (strati rispettati), usata da `finalreview` e `apply._final_rules`; `GitError` catturato in apply (fail-closed, test `test_unreadable_diff_blocks_every_r_rule`); fallback `default_ref` testato; `veto` {event, rule, reason} coerente con `audit_round` (apply.py:155); test dell'interrotto manomesso.
- Scostamento `head` opzionale: giustificato (apply deve usare lo SHA del ciclo), nessun cambiamento di comportamento per i chiamanti.

### Punti di forza
Modifiche chirurgiche; TDD con RED documentato; duplicazione di `_profiles` eliminata; test fail-closed espliciti.

### Valutazione del test `test_rejected_report_leaves_trace`
Prova davvero la riga 39 a livello di unità: DB reale, ciclo davvero superato, evento `veto` letto dal DB, nessun rilievo scritto. Un percorso via hook non esiste in pratica: `_common.awaiting_final` filtra prima (stadio, atteso, già riportato), quindi il ramo è raggiungibile solo in una corsa tra eventi. Il ctx minimo è quindi accettabile; non serve un percorso reale.

### Rilievi
Critical: nessuno. Important: nessuno.
Minor:
- violations.py:97 la riga di docstring è lunga 116 caratteri; va a capo.
- violations.py (`active_profile_names`): `head or git.head(wt)`; se `git.head` ritorna None, `changes(head=None)` include il working tree e i non tracciati. Caso limite (worktree senza commit), prima inesistente in `apply`; basta un `if head is None: return []`.
- test_check_final_review.py (`test_rejected_report_leaves_trace`): `cfg=lambda` ricarica la configurazione a ogni chiamata; calcolarla una volta.
- La riga 24 funziona con `PYTHONPATH=bin:.`, non con il solo `python3 -B tests/<f>.py` del brief (già così prima, riportato dall'implementatore).

### Valutazione
**Qualità del task:** Approvato. **Motivo:** tutte le righe e le voci di carry sono implementate con test che asseriscono il comportamento; strati e fail-closed rispettati; restano solo rifiniture.
