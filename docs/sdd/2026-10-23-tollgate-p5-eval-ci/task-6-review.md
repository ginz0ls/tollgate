# Revisione Task 6 (e1a9e97, rinviati del nucleo e del flusso)

### Aderenza
- ✅ P1 git assente: `cli.py:19-22` (`FileNotFoundError` -> `UsageError`, uscita 1 via `cli.py:449`); test con `PATH` senza git su 3 comandi (`test_cli.py` nuovo).
- ✅ P1 EOF/Ctrl-C: `cli.py:_restore` (`interrupted`, «annullato» su stderr, uscita 1, «n» resta uscita 0); test pty per EOF e SIGINT, DB e `broken/` invariati. Il test di conferma da CLI è caratterizzazione (già verde), dichiarato.
- ✅ P3a 163, P3b 13, 54, 76, P3c 12: codice e test presenti e coerenti col brief.
- ✅ P3b 10 (`reviews.py:335-340`), con in più il rifiuto dei rilievi senza esito (dichiarato, la riga 10 li nomina; i chiamanti `apply.py:107,120` e `finalreview.py:172` lo garantivano già).
- ✅ P3b 44: tutti i `json.loads` di `openpr.py` passano da `db.load_json`; `finishcheck.check` cattura `DbError` (`finishcheck.py:64`).
- ✅ Step 5: i grep nel report sono coerenti con il codice (`git.changes` una volta in `finishcheck.py`).
- ⚠️ P3b 11 (scostamento 4): vedi Important 1.
- ✅ P3b 27 (scostamento 2): vedi sotto, regge.
- ✅ P3b 74 (scostamento 1): regge, vedi sotto.

Esame degli scostamenti richiesti
1. Riga 11. La transazione di `close_cycle` (`reviews.py:326-355`) copre solo la riga del ciclo (`stage='closed'`, esito, `counted`) e l'evento `review_cycle`. `set_phase`, `open_block` (`reviews.py:357-367`) stanno DOPO la transazione, come ogni docstring del modulo dice (`close_cycle` «va chiamato fuori da una transazione»). Quindi un processo morto tra la chiusura e `set_phase`/`open_block` lascia ciclo chiuso `needs_fix`, fase ancora `review`, nessun blocco del tetto: prima la seconda chiamata completava, ora ritorna l'esito e basta (`reviews.py:333-336`). La modifica toglie quel recupero. Nessun chiamante di oggi lo esercita (hook e `finalreview` chiamano solo da stadio `verify`, e `_prepare` su un ciclo chiuso needs_fix sullo stesso SHA ne apre uno nuovo, `finalreview.py:102-112`), ma il recupero era la «ragione d'essere» dichiarata in `task-3-review.md` (M2) e `task-3-report.md:14`. Vedi Important 1.
2. Riga 27. Coerente con spec 6.4 («mai un traceback») e col ruling C6: il report è una cache (`finishcheck.py:93-101`), l'avviso `esito salvato illeggibile, si ricalcola` compare nell'output (`lines` resta in `CheckResult`), il gate si riesegue e riscrive il report solo se verde. Un report corrotto non può far aprire una PR senza un `finish check` valido: `openpr._compute_dod` (`openpr.py:319-323`) legge con `load_json` + `report_items` e rifiuta con `rifiuto:` che nomina `work_items.finish_report` (test `OpenCorruptTest`, 3 casi, nessuna PR/push, fase invariata). Se il ricalcolo è rosso, il report resta guasto e `open-pr` rifiuta. Il rifiuto per sempre sarebbe stato peggiore (lavoro bloccato in `review`).
3. Riga 74. Il `k` di `review-<k>.md` è `len(glob("review-*.diff"))+1` (`taskcmd.py:322-325`), contatore del lavoro: l'euristica «k più alto» sbagliava task. Il `code` è scritto nel brief (`ReviewBrief(code=...)`, `taskcmd.py:328`), quindi `_review_brief` (`checkpoint.py:65-80`) è la soluzione corretta e il brief del task è davvero quello con il suo codice. Il test esistente `test_prepared_review_not_reprepared` è stato adeguato legittimamente (prima poneva contenuti `b` che fissavano l'euristica sbagliata). Rischio residuo minimo: corrispondenza per sottostringa di 8 hex (Minor 2).
4. `events._as_dict` (`events.py:58`): necessario, non è scope creep. `stats.off_periods` (`stats.py:39`) esporta tutti gli eventi, quindi un `events.data` guasto rompeva `facts` prima di qualunque altro punto. Il chiamante CLI (`cli.py:441`) è dentro il `except DbError` di `cli.py:449`; l'altro (`stats.py:39,65`) è raggiunto da CLI e da `openpr`, che ora catturano `DbError`. Nessun hook lo chiama.
5. Test pty (`test_cli.py` nuovi): lo slave è chiuso nel padre subito dopo il `Popen` (e nel `finally` se il `Popen` fallisce), il master nel `finally`, `Popen` in `with` (attende il figlio); `select` con timeout 30 s e `proc.kill()` su silenzio: non resta appeso. Ctrl-D è scritto sul master (EOF in modo canonico su riga vuota), SIGINT al solo PID del figlio (processo proprio, nessun pattern). Nessun descrittore aperto in coda: coerente con `-W error::ResourceWarning`.
6. RED vero: verificato per lettura sul vecchio codice del diff. `test_close_cycle_requires_verify_stage` (vecchio codice chiudeva da `review`), `twice_is_idempotent` (vecchio rifaceva `set_phase`, fase `review`->`execution`), `review_brief_by_task_number` (avrebbe scelto `review-10.md`), `all_cap_blocks_listed` (un solo passo), `request_existing_key...` (sovrascriveva), `close_round...` (nessun controllo), `assign_event...` (KeyError), `finish_report` e `openpr` (JSONDecodeError/TypeError), `reason_in_event`. Eccezione: vedi Minor 1.

### Punti di forza
- `db.load_json(raw, what, kind)` è un punto unico, con il nome `tabella.campo` nel messaggio: DRY e messaggi utili; `report_items` evita la validazione duplicata tra `finishcheck` e `openpr`.
- Il report spiega in chiaro i tre scostamenti e i due dubbi; le scelte 1 e 2 sono corrette.
- `close_round` valida prima della transazione ed esclude i bool; il test copre 7 forme e verifica che il giro resti aperto e senza evento.
- `_cap_step` mantiene il testo di prima con un solo blocco.

### Rilievi

**Critical**: nessuno.

**Important**
1. `bin/tollgate_core/reviews.py:333-336` (e docstring `:324-328`), scostamento 4, «imposto dal piano»: la transazione di chiusura non include fase e blocchi (`:357-367`, fuori da `db.tx`), quindi un crash dopo la chiusura lascia ciclo `needs_fix`/`needs_you` chiuso con fase `review` e senza blocco del tetto/del revisore, e `close_cycle` non lo ripara più. Prima la riesecuzione completava i passi. Oggi nessun chiamante la rilancia, ma la garanzia di recupero è sparita senza sostituto, e `test_close_is_resumable` (`test_reviews.py:212-221`) ne ha mantenuto solo il nome. Correzione: o rendere atomica la conseguenza (fase e blocco nella stessa transazione della chiusura, con una variante che non apre transazioni annidate), o tenere un recupero esplicito e distinguibile da `approve finding`/`approve rounds` (per esempio completare i passi solo se `ciclo.outcome == needs_fix` e `ultimo ciclo` e il tetto è raggiunto e non c'è alcun `block_closed` successivo alla chiusura), oppure, se il controller accetta il rischio, registrarlo come rinviato con il motivo («nessun chiamante ripete la chiusura») in `Dopo la v1` e correggere docstring/nome del test che ancora parla di «resumable».

**Minor**
1. `bin/tollgate_flow/openpr.py:494,530`: i `load_json` di `_size_reasons` e `_skills_absent` non hanno un RED proprio: `facts` valuta `off_periods` (`:482`) prima, e lì `_as_dict` fa già fallire il test con lo stesso messaggio, quindi le casistiche `subagent_stop` e `skills_absent` di `OpenCorruptTest` passerebbero anche senza quelle due modifiche. Inoltre dopo `load_json` restano `data["task"]`/`data["skills"]` non protetti (`:531`). Basta un `kind=dict` in meno al rischio; non serve altro per v1.
2. `bin/tollgate_core/events.py:45`: `known_commits` ha ancora un `json.loads` nudo su `events.data` (hook e sync), stesso tipo di traceback; fuori dal brief, da annotare.
3. `bin/tollgate_flow/checkpoint.py:76`: `code in testo` è una sottostringa di 8 caratteri esadecimali in un brief che contiene diff path, SHA e testo: collisione teorica con un altro task. Un match sul blocco JSON/riga `code` del brief sarebbe più stretto.
4. `bin/tollgate_core/db.py:43`: per `kind=None` un valore falso (`''`/`NULL`) diventa `[]` e una forma non-oggetto passa: in `events._as_dict` `data` può essere una lista. Passare `dict` anche lì.
5. `bin/tollgate_flow/finishcheck.py:282-287`: `_saved` ignora in silenzio `manual`/`gate.attention` di forma sbagliata (ok per una cache), ma non lo segnala come avviso.

### Valutazione
**Qualità del task:** Da correggere
**Motivo:** Tutto il resto è affidabile e testato con RED vero, ma lo scostamento sulla riga 11 toglie senza sostituto il recupero dopo un crash tra chiusura del ciclo e cambio di fase/blocco (la transazione non li copre); va corretto, accettato per iscritto o reso atomico. Il resto sono minori.
