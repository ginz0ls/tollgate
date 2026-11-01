# Revisione Task 6 (3c4697a..81ad7fd)

### Aderenza
- ✅ `skills: [rules-base]` dopo `tools:` nei quattro agenti (implementer.md:5, task-reviewer.md:5, final-reviewer.md:5, finding-verifier.md:5); spec-auditor, spec-adversary, plan-adversary invariati (nessun `skills`), provato da `test_other_agents_do_not_preload`.
- ✅ `rules-base` mai in «Skill da usare» né in `skills_required`: nessun file di produzione di quella parte toccato; guardia `tests/test_taskcmd.py` `test_rules_base_not_required` con radice temporanea esplicita e asserzione sull'intero testo del brief.
- ✅ Decisione 11: punti 1 e 2 fusi in un rimando (implementer.md:100-101), restano documentazione/pagine non fidate e consegna nota, rinumerati 1-3. Frase sul file delle dipendenze tolta (la copre R-BASE-02).
- ✅ D3 / decisione 8, coerenza agente-brief:
  - nota non utilizzabile: un solo rilievo `nota di ricerca`, gravità e `missing` del brief, «nessun rilievo R-BASE in più» (brief.py:220-224; task-reviewer.md riga «Se la nota manca o non è valida»);
  - nota utilizzabile con difetto: `R-BASE-…` se esiste (`blocker`/`major` solo se `[blocca]` e interruttore acceso, altrimenti `moderate`), altrimenti `nota di ricerca` con la gravità del brief; mai due rilievi (brief.py:225-229; task-reviewer.md; standard task-reviewer.md:51 con la clausola dell'interruttore spento).
  - Inciso «non una regola R-…» tolto. I due testi non si smentiscono.
- ✅ D6: final-reviewer condizionato («Se il brief ti mostra la nota di ricerca…»); `FINAL_STANDARD` non toccato.
- ✅ `brief.STANDARD` «regole dei profili e di base»; `_warning` finisce con «Le regole di base sono nella skill `tollgate:rules-base`.»; WARNING dei test è un prefisso, nessun altro posto duplica il testo (grep).
- ✅ Isolamento dall'interruttore: `test_warning_names_rules_base` usa `make_root(False)` + `plugin_root` esplicita (L0 e L1); i test di brief e manifest non leggono l'interruttore. `skills/rules-base/SKILL.md`, `approved` e regole non toccati (diff: solo agenti, brief.py, research_gate.py, test).
- ✅ I tre test dell'implementatore invariati; da me rilanciati `tests.test_manifest`, `tests.test_brief`, il test di guardia: 85 OK.
- ✅ `claude plugin validate --strict` e suite completa: dichiarati nel report (3197 OK su 3.11 e 3.13); non rilanciati, nessun segnale contrario.

### Punti di forza
- Il ramo «nota non utilizzabile» esce subito (`return`) invece di concatenare condizioni: il doppio rilievo è escluso dalla struttura, non solo dal testo.
- Il test sulla sezione del brief gira su tre varianti (mancante/acceso, spento, nota valida).
- Nessun test dipende in silenzio dallo stato del repo.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `tests/test_brief.py` `test_review_note_section_names_base_rules_and_single_report`: le tre varianti passano con `R-BASE-` e «una volta sola» anche nel ramo «non utilizzabile», dove `R-BASE-` compare solo nel «nessun rilievo R-BASE in più». Non distingue i due rami né copre la nota consegnata ma non valida. Aggiungere: ramo non utilizzabile `assertNotIn("che viola", section)`; ramo utilizzabile `assertIn("[blocca]", section)`; una variante con nota e `research_valid=False`.
2. `agents/task-reviewer.md` (riga «Se la nota è utilizzabile…») e `agents/final-reviewer.md:37`: dicono solo «la gravità del brief» / niente gravità; in final-reviewer non c'è sorgente di gravità (il brief finale non ha la sezione, quindi la frase è inerte, come voluto da D6). Nessun danno oggi.
3. `agents/implementer.md:100`: il vecchio punto 1 chiedeva anche di leggere «quelli che li chiamano»; R-BASE-01 copre solo i file modificati. Perdita voluta dalla decisione 11, segnalata solo per memoria.
4. ⚠️ Fuori dal diff: `verdicts.is_blocking` (verdicts.py:91-101) considera bloccante ogni `R-…` non dichiarata da un profilo attivo (fail-closed), e `R-BASE-…` non è in `known_rules`. Quindi un `major` su una `R-BASE` non `[blocca]` (07, 08, 11) bloccherebbe comunque se il revisore sbaglia gravità; la distinzione `[blocca]` regge solo sull'istruzione al revisore. Non è un difetto del Task 6 (il piano non lo chiede), ma è da portare a un task finale o alla revisione di merge.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** agenti, brief e avviso sono coerenti con D3/D6 e decisioni 2, 8, 11; nessun passaggio di `rules-base` in `skills_required`, test con radice esplicita e verdi. Restano solo rifiniture ai test e una nota di rischio fuori ambito.
