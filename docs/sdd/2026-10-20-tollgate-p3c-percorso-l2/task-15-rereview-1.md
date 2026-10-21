# Ri-revisione Task 15, giro di correzione 1 (4b4871a..d71f48d)

Diff: 3 file, 43 inserzioni e 35 cancellazioni. Non è una riformattazione: le righe lunghe delle tabelle e dei paragrafi cambiano per poche parole (confronto parola per parola eseguito su tutte le coppie -/+); nessun rilievo sul diff.

### Verdetti sui rilievi

**I-1 (sezione 16: frontmatter dei soli due agenti; incidente `claude -p` e D5 dichiarati)**: INDIRIZZATO. Spec sezione 16: «Frontmatter dei due agenti lanciati (`spec-adversary`, `plan-adversary`) ... (`spec-auditor` non è stato lanciato, quindi il suo frontmatter non è provato)» e inserto su passo 1 con la forma precedente dello script (D5) e `claude -p` partito per errore, fermato per PID, nessuna evidenza usata. Stesso contenuto nello «Stato» del piano (riga 6, diff hunk 1).

**I-2 (decisione 17 in 7.5; decisione 25 e ruling nel corpo; ogni voce della riga 24 ha un punto)**: INDIRIZZATO. 7.5: nuovo paragrafo «Recinti di codice nel piano» (al più 3 spazi, `check_plan` e `task_text`), coerente con `bin/tollgate_analysis/plan.py:16` (`_FENCE_OPEN = ^ {0,3}...`) e `plan.py:105,142` (`check_plan`, `task_text`). 6.3 (spec riga 516): instradamento sulla gravità dichiarata `blocker`/`major` qualunque sia la decisione dell'utente, coerente con `bin/tollgate_flow/taskcmd.py:65-80` (filtro su `findings.severity`, che `approve finding` non modifica: usa `user_decision`, `db.py:82`) e `HEAD` nullo senza profili, coerente con `bin/tollgate_core/violations.py:81-91`. Riga 24 e intestazione ora elencano 6.3 e 7.5. D15 con `git.blob_at` nel passo 4 della 6.2 e nella riga 24.

**I-3 (le tre asserzioni controllano «/tollgate:approve spec»)**: INDIRIZZATO. `tests/test_criteria_p3c.py:371, 407, 471`: `assertIn("/tollgate:approve spec", self.prepare_step())`. `prepare_step` ritorna l'ultima riga di `audit prepare` (:137-142) e il passo `approve_spec` emette «chiedi all'utente /tollgate:approve spec <fette>» (`audit.py:43,485`), quindi l'asserzione distingue davvero dal passo «lancia l'agente». Eseguito `SpecAuditOffTest`: OK.

**Minori**:
- 6.2 passo 4 con `spec_audit` spento: INDIRIZZATO («una fetta sola o con `spec_audit` spento»).
- «D15» chiarito nel piano: INDIRIZZATO («decisione 15 del piano P3c»).
- Riga `reopen` di 8.4 con il task non `done` con commit: INDIRIZZATO.
- Banco unico: INDIRIZZATO. `SpecAuditOffTest` (:460) ha un `setUp` proprio che fa `make_lab(toml=...)` e `start_l2`; `rows` spostato nella base `L2Helpers` (:57); i riferimenti in matrice sono aggiornati a `SpecAuditOffTest`. Nota: la classe `L2FlowTest` non crea più il secondo banco.
- Matrice: `test_check_writes.py::ExecutionL1Test.test_protected_files` aggiunto: INDIRIZZATO (non verificato con AST in questa ri-revisione; il report dichiara 45 riferimenti controllati).
- Colonne «Resta a»: INDIRIZZATO per P3b (righe 249 e 252 annotate «chiuso/chiusa in P3c»). Vedi sotto la riga 225.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important.
- Minor: la frase finale della sezione 4 del piano (riga 269) ora dice «tabelle di P3b ... annotate», ma la tabella P3a (riga 225) ha ancora «spec_adversary, spec_audit, plan_adversary, spec_pitch (P3c)» nella colonna «Resta a», non annotata come chiusa (non era tra i rilievi; residuo della stessa famiglia).
- Minor: la 6.3 cita «riga 71» e «riga 49» dei rinviati di P3b e la riga 24 cita D2-D19: riferimenti che si risolvono solo nel registro `.superpowers/sdd/`, non ancora portato in `docs/sdd/` (già segnalato nel piano).

### Osservazioni fuori ambito
Il report non rilancia la suite con `-W error::ResourceWarning` dopo il fix (lo dichiara; la modifica è solo strutturale sui test, e `SpecAuditOffTest` gira pulito).

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
