# Revisione Task 5: `audit prepare` e `audit decline` (a11795c)

### Aderenza
- ✅ D2: i sei rami di `_decide_spec` (audit.py `_decide_spec`) sono nell'ordine della ruling: 1 giro aperto (stesso SHA ristampa, altro SHA superseded), 2 avversariale non passato (passato = pulito a qualunque SHA o sospeso), 3 lenti con conferma (`any_rows`, quindi un primo ciclo superseded non richiede conferma), 4 `adversarial_ok` falso, 5 lenti di conferma solo con avversariale spento, 6 `approve_spec`. Verificato ramo per ramo; i due test di D2 ci sono e asseriscono davvero.
- ✅ Rischio 2: documento letto a HEAD (`_committed`: `blob_at` + `blob_sha` del worktree); worktree diverso o file non committato dà «committa <percorso> prima del giro»; testo e blob vengono da HEAD. D3 ok (`_spec_approval_current` da `ls_files_at`/`text_at` HEAD, messaggio testuale richiesto). D12 ok.
- ✅ Rischio 3: `launch_line` pubblica con la stessa forma `agente: <tipo> brief: "<path>"[ model: m]`, `Launch` di `finalreview`; chiamanti aggiornati, `adopt.find_plan` pubblica. D19 ok (`program_command`).
- ✅ CLI, `_COORDINATOR_ONLY`, `STEPS` (parte fissa senza segnaposto), brief con codice/SHA e riga JSON via `json.dumps`, fette/tane/«cosa non fare», tabella task.
- ✅ Rischio 4: `set_phase` e `open_block` sono chiamati con la connessione in autocommit dopo le `db.tx` chiuse, mai dentro una transazione. Ordine in `advance`: registra piano, poi set_phase; una ripetizione dopo interruzione è idempotente.
- ❌ Rischio 5: vedi I-1.
- Sei scelte dell'implementatore: tutte accettabili (rifiuti come `PrepareResult` e `AuditError` solo per ambiente; `CONFIRM_STEP` fuori da `STEPS`; punto di vista seguente dopo un ciclo con rilievi, coerente con la decisione 6; `peek` col ripiego della decisione 20; `decline` con la condizione in più «lenti non già sospese», sensata).
- TDD parziale: i test di `prepare` scritti dopo il codice sono comunque buoni: asseriscono righe di lancio, righe del DB, fase, evento `phase_change`, contenuto del brief. Il buco non è nella forma ma in un caso non coperto (I-1).
- ⚠️ `skills/spec-audit/references/dimensioni.md` (metodo delle lenti nel brief) non esiste ancora: arriva col Task 13, il test controlla solo il nome.

### Punti di forza
Decisione pura (`_decide_*`) separata dall'esecuzione, riusata da `peek` e `decline`; nessuna scrittura in `peek`; rientranza dopo `/clear` (reprint con lo stesso codice, brief riscritto se manca); percorsi con `"`/a capo rifiutati prima di scrivere; ottima copertura dei rami di D2.

### Rilievi
**Important**
- I-1 `audit.py:_decide_plan` (`if not _on(cfg, PLAN_KIND): return _Act("advance", ...)`): con `plan_adversary` spento un giro `plan-adversarial` ancora aperto non viene chiuso `superseded` (l'`_Act` non porta `supersede`). Verificato con una prova a parte: fase `approval` con il giro `open`; poi `approve plan` rifiuta per «giro aperto» e `audit prepare` in `approval` stampa solo `approve_plan`: vicolo cieco. È il rischio 5 per il piano (in spec il codice lo gestisce, con test `test_open_round_of_disabled_component_is_superseded`). Correzione: `_Act("advance", supersede=row, ...)` anche nel ramo spento, e test (giro del piano aperto, componente spento, fase plan -> approval e nessuna riga `open`).
- I-2 `brief.py:_task_line`: il titolo del task (testo del piano, non fidato) è in prosa e in backtick, fuori da un recinto; la regola globale vuole il testo non fidato in un recinto marcato come dato. Correzione: mettere la tabella dei task in un `_block`/recinto con `fence`, o ridurre a numero+file+agente. Test con titolo contenente backtick.

**Minor**
- M-1 `audit.py:_adv_or_fix` e il ramo lenti con `fix_spec`: il rifiuto avviene prima di `_execute`, quindi un giro aperto su un altro SHA resta `open` fino al prossimo `prepare` riuscito (verificato: giro lenti aperto + rifiuto, resta `open`). Innocuo (`approve spec` lo rifiuta comunque, il successivo `prepare` lo chiude) ma incoerente con il ramo 1 di D2 («prosegue» dopo la superseded). Valutare di superare `stale` anche prima di un rifiuto.
- M-2 `brief.py:audit_brief`: percorsi con backtick nel documento in `` `…` `` non sono neutralizzati (D12 non li copre); una riga, impatto basso.
- M-3 `_execute`: `ValueError` di `audits.open_round` non è in `ERRORS` (solo corsa tra due `prepare`): traceback invece di rifiuto.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** l'ordine di D2, la lettura a HEAD e la forma delle righe sono corretti e ben provati, ma con `plan_adversary` spento un giro del piano aperto resta tale e blocca `approve plan` (I-1), e i titoli dei task finiscono nel brief fuori dal recinto dati (I-2).
