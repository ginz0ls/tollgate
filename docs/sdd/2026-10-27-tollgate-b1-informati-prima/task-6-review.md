# Revisione Task 6: comando `research` (64cbcf9)

### Aderenza
- ✅ Codici OK 0 / INVALID 1 / REFUSED 2 (`research_cmd.py:17`). REFUSED per: nessun lavoro (`:63`), L0 (`:82`), fase diversa da execution (`:85`), `research = 0` con testo «lavoro iniziato prima del passo informati prima» (`:87`), componente spento (`:92`), task inesistente (`:73`), task non `running` (`:101`). Tutti con test.
- ✅ File `.tollgate-run/<N>/research-<k>.md` con nota intera e riga finale `esito: valida|non valida` (`:112`); `note_path` unico punto del percorso (D17); `show` lo usa.
- ✅ Evento `research_note` {task, ok, problems} a ogni consegna (`:115`), test su valida, non valida e riconsegna (2 eventi).
- ✅ Letture di altro `agent_id` dello stesso task contano (`for_task` non filtra), quelle di un altro task no (`test_lookups_of_other_task_do_not_count`).
- ✅ `cli_calls` (D9/D12): nega solo `research submit` alla sessione principale in L1/L2, anche con programma incerto e nel ripiego testuale; `show` e L0 ammessi; l'implementatore non è toccato (il controllo sta dopo il `continue` dei subagenti). B1-V5: nessun `--file`.
- ✅ Heredoc: `test_heredoc_research_passes_bash_rules` usa `hooks/run` vero, nota con backtick, `$(...)` e riga `EOF`, poi esegue il comando con `bash -c` e confronta `research_note` con la nota originale: asserzione reale.
- ✅ Nessun `__pycache__` nel commit né nel worktree; `git status` pulito.
- ⚠️ D2 chiede il rifiuto «attraverso `research.active`»: il modulo non è usato (vedi Minor 1). Comportamento equivalente.
- ⚠️ Non verificabile dal diff: che `.tollgate-run/` sia davvero escluso da git in ogni worktree (il codice si affida alla spec 6.3 e non chiama `add_excludes` come `checkpoint.py:217`).

### Giudizio sui dubbi dell'implementatore
1. `_write_atomic` copiato: il vincolo di strato è vero per `tollgate_hooks` (`tests/test_layers.py:11,81`: `FLOW_FORBIDDEN = hooks, checks`), ma `tollgate_flow` può importare `tollgate_core` (non vietato; `cli.py` e `finalreview.py` lo fanno). Un posto ammesso esiste: una funzione in `tollgate_core` servirebbe `apply.py:125` e `research_cmd.py:36` identiche, e avrebbe assorbito anche il pattern di `checkpoint.py:217-221`. La giustificazione non regge: Important 1.
2. Controllo lavoro/research/worktree non condiviso: accettabile. Gli strati sono davvero diversi (`runner.py` e `lookup_rec` stanno in hooks/checks) e qui i rifiuti hanno messaggi distinti voluti dal brief. Nessun rilievo.
3. RED non osservato per `research_cmd`: dichiarato onestamente; i test finali coprono tutti i casi del brief e fallirebbero senza il modulo (ImportError). Nessun rilievo di sostanza; solo nota di processo.
4. Nota oltre 8.000 caratteri salvata nel DB: coerente con «la nota si salva sempre, anche non valida» e con l'esito INVALID. Non è un difetto; l'unico costo è un testo senza limite in `tasks.research_note` ed evento (Minor 3).
5. Configurazione illeggibile = REFUSED: coerente con la spec 7.1 (errore informativo, nessun silenzio) e con `finalreview.py:88` che propaga l'errore. Il messaggio nomina la causa. Va bene. Manca però un test (Minor 2).

### Punti di forza
Modulo piccolo, `submit` e `show` con lo stesso `_open`/`_task`; ordine dei rifiuti sensato; `finally: conn.close()`; scrittura atomica con pulizia del temporaneo; stdout/stderr separati con codici di uscita propagati; test di `cli_calls` con casi negativi (`echo "unchiuso research submit` → 0) che limitano i falsi positivi del ripiego testuale.

### Rilievi

**Critical**: nessuno.

**Important**
1. `bin/tollgate_flow/research_cmd.py:36-51` duplica letteralmente `bin/tollgate_hooks/apply.py:125-139` (e c'è già un terzo schema tmp+replace in `bin/tollgate_flow/checkpoint.py:217-221`). Lo strato non obbliga alla copia: `tollgate_core` è importabile da flow e da hooks. Scenario: un fix alla scrittura atomica (es. nome del temporaneo, fsync) va fatto in due posti e uno si dimentica. Correzione: una `write_atomic` in `tollgate_core` (modulo piccolo, es. `fsutil`), usata da `apply.py` e `research_cmd.py`; il test di strato resta verde.

**Minor**
1. `research_cmd.py:84-93`: la regola «passo attivo» ricompone a mano `work["research"]` e il componente invece di chiamare `research.active(work["research"], on)` (D2). Si possono tenere i messaggi distinti e usare `active` come predicato unico dopo i due controlli, così la regola non vive in due posti (Task 7 la usa per il gate).
2. Nessun test per `configurazione non leggibile` (`research_cmd.py:95`, ramo REFUSED con `ConfigError`/`GitError`) né per `_write_atomic` che fallisce (`:114`).
3. `research_cmd.py:110-117`: il file viene scritto prima di `set_note`; se il DB fallisce dopo, il file dice «valida» e il DB non ha la nota. Inverti l'ordine (DB poi file) oppure accetta e documenta. Nessun limite di dimensione sul testo letto da stdin (`cli.py` `sys.stdin.read()`).
4. `tests/test_check_cli_calls.py` (circa riga 210+): la classe `ResearchSubcommandTest` è dopo `if __name__ == "__main__": unittest.main()`. Con `python3 tests/test_check_cli_calls.py` i suoi 8 test non girano (con `-m unittest` e `tests/run` sì). Sposta il blocco `__main__` in fondo.
5. `research_cmd.submit` non verifica chi chiama: un subagente (anche di sola lettura) può consegnare la nota di un altro task `running` dello stesso lavoro. Nessuna identità del chiamante arriva alla CLI, quindi è un limite di progetto; vale la pena nominarlo nei rilievi rinviati.
6. `tests/test_research_cmd.py` `test_submit_valid_note`: `assertEqual((r.code, r.lines), (OK, [r.lines[0]]))` verifica solo la lunghezza 1; meglio asserire il testo del messaggio.

### Valutazione
**Conformità alla spec:** Conforme (D2 con scarto formale: `research.active` non usato, Minor 1).
**Qualità del task:** Da correggere. **Motivo:** funzionalità, codici, evento, file e regola di `cli_calls` corretti e ben testati, ma la copia letterale di `_write_atomic` è giustificata con un vincolo di strato che non esiste verso `tollgate_core`; va unificata (Important 1) e si sistemano i minori.
