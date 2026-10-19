# Revisione Task 7 (f9107c4..17f77db)

### Aderenza
- ✅ `verdicts.py`: decisione 10 e C14. Ultimo oggetto con `outcome` (`json_candidates`, `bin/tollgate_analysis/verdicts.py:41`), `task` intero (bool escluso), `sha`/`code` uguali, `outcome` in approved|changes. Un verdetto non valido ha sempre `outcome=None`. Rilievi senza rule/file/line intera, o con severity fuori elenco, scartati e contati. Matrice con 12 sottocasi più prosa attorno e "ultimo vince".
- ✅ `awaiting_review` (`_common.py`): richiede `review_code` e `review_sha` non nulli, quindi C10 regge (test dopo `--fix`). Vincolo 6 e decisione 11 rispettati: `subagent_stop` salta i revisori in attesa e `task_verdict` chiude la riga. L'implementatore non può consegnare il verdetto (il tipo non coincide con `reviewer_type`).
- ✅ Tamper: `fingerprint_changed` più `tampered_records`, con `readonly_check`; il verdetto non viene registrato.
- ✅ Veti: 2 veti poi `subagent_finish(done)` più `needs_you`. Il `record` dopo il deny non chiude la riga, perché in veto non c'è `subagent_finish`.
- ✅ Prenotazione (decisione 12, C17): controllo in `decide`, scrittura in `apply`. Lo scostamento 1 è corretto: `take_pending` azzera `reserved_at` nella stessa UPDATE (`tasks.py:122`).
- ✅ Scostamento 2 (spec_compliance assente = non valido): accettabile, fail-closed e coerente con 18.5.
- ✅ Scostamento 3 (fase execution): coerente con `task start`.
- ✅ `_implementer`: il diff mostra solo lo spostamento della firma e la sostituzione di `_fingerprint_changed`. Il corpo di P2 è invariato. L'unica novità è `subagent_report` in testa. È idempotente rispetto a `handback`/`post_agent`, che registrano lo stesso testo.
- ✅ Strati: `verdicts` importa solo `report` (analysis). `task_verdict` non scrive nel DB. `taskcmd` usa core e analysis.
- ⚠️ RED ricostruito a posteriori: non verificabile dal diff. I test nuovi non risultano tautologici.

### Punti di forza
Fail-closed ovunque (outcome None, nessun fallback ad approved). Codice casuale e SHA nel brief. `review_sha` azzerato dal `fix` e `verdict` azzerato da `set_review_prep`, quindi un vecchio approved non sopravvive a una nuova preparazione. Test sul comportamento reale, con il tampering verificato sul filesystem.

### Rilievi

**Important**
1. `bin/tollgate_flow/taskcmd.py:~254` (`task_done`) e `_range` (`review_prepare`): l'ultimo SHA è `tasks.commits[-1]`, non la punta reale del worktree. `task_commit` si registra solo se il commit è fatto da un subagente con task (`post_bash.py:56-58`, `if task is not None`). Percorso che porta a `done` senza approved sul codice finale:
   - il verdetto approved copre `commits[-1]`;
   - il coordinatore (nessun `agent_id`) o un subagente senza task fa un altro commit, oppure sposta HEAD;
   - `task_done` confronta `review_sha` con `commits[-1]`, che è invariato, e chiude `done`.
   - Lo stesso vale per le modifiche non committate. La sola impronta dei file non vede un `git reset --soft`. Il test «commit dopo il verdetto» registra a mano `tasks.add_commit` (test_taskcmd, `commit()`), quindi non copre questo caso.
   - Correzione: in `task_done` richiedi anche `review_sha == git.head(worktree)` (con commit o senza) e un albero pulito, e in `review_prepare` rifiuta o usa `git.head` quando HEAD differisce da `commits[-1]`. Aggiungi un test con un commit fuori da `tasks.commits`.
2. `verdicts.py:67-71` (imposto dalla decisione 10, ma è un rischio di falso approved): con `standard` acceso un verdetto `changes` i cui rilievi bloccanti sono tutti scartati (per esempio un blocker senza `line`) o vuoti diventa `approved`. Il test `test_finding_without_rule_dropped` lo fissa (`outcome "approved"`). `dropped` non viene registrato né mostrato, quindi nessuno sa che un blocker è stato ignorato. Correzione consigliata: se `declared == "changes"` e `dropped > 0` senza alcun rilievo valido, tratta il verdetto come non valido (veto: il revisore riscrive i rilievi con la prova). Altrimenti registra `dropped` nell'evento. Vale la pena segnalarlo al controller come deviazione dalla decisione 10.

**Minor**
3. `_common.py awaiting_review`: senza `row["task"]` sceglie il task in `review` più basso con `reviewer_type` uguale. Con due task in review preparati insieme, un verdetto con `task` giusto ma fascicolo dell'altro risulta non valido (fail-closed), quindi non pericoloso. Il report lo dichiara.
4. `agents.py`: `task_reserve` è un `record` che si applica anche se un altro controllo nega l'`Agent` più tardi. Costo noto (120 s), dichiarato nella decisione 12.
5. `json_candidates` è quadratica in messaggi con molte `{` (una `raw_decode` per parentesi). Il rischio è basso.
6. `task_verdict.py:36`: `last_assistant_message or row["report"]`. In una ripresa dello stesso revisore, un `report` vecchio potrebbe essere letto se manca il messaggio finale. Il codice casuale limita il danno, ma conviene azzerarlo a `review-prepare`.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** il parser del verdetto e la chiusura del revisore sono solidi e fail-closed. `task done` però ancora la copertura a `tasks.commits[-1]`, che non vede commit fuori dai subagenti con task né uno spostamento di HEAD (Important 1). Inoltre un `changes` con blocker scartati diventa approved senza traccia (Important 2).
