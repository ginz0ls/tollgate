# Revisione Task 7: `review prepare` (ec1caa3..a9879b7)

Letti: brief, report, carry.md (sezioni Task 7, C16, C7, M1), decisioni 5, 6, 8, 21, diff. Nessun test lanciato (si usa l'evidenza del report: 1170 test verdi). Controlli mirati su codice fuori dal diff: `reviews.py` (supersede, to_verify, close_cycle, count), `taskcmd.py` (caricamento config, uso di `hint`), `verdicts.parse_final_verdict`, `start.py` (scrive `issue.md`), spec 18.5.

### Aderenza
- ✅ Precondizioni: fase `review` e `HEAD == finish_sha` (`finalreview.py:81-83`, errore con «rilancia /tollgate:finish»); L0 (`:85`), componente `final_review` spento (`:89`), `review_unverified` (C7, `:91`): nessun lancio, riga e `prossimo passo: finish open-pr`.
- ✅ Ciclo aperto: stesso SHA o stesso `patch-id` → ripresa con lo stesso codice (`:99-102`, criterio 28/16). SHA e patch-id diversi → `reviews.supersede` (C16, `:103`), che scrive `counted = 0`.
- ✅ Ciclo `ok` su HEAD o con stesso patch-id → «revisione già superata (ciclo n)» + `finish open-pr`.
- ✅ Tetto: `count >= MAX_CYCLES` (8) → `ReviewError` con «/tollgate:approve unverified-review».
- ✅ Nuovo ciclo: `secrets.token_hex(4)` per ciclo, specialisti solo in L2 (`final_specialists`), brief in `final-<n>.md`, `final-<n>-<area>.md`, diff `final-<n>.diff`, `verify-<n>.md`.
- ✅ M1: `close_cycle` solo dopo `to_verify` vuoto (`:173`); `to_verify` ordina per gravità e declassa oltre `max_findings`.
- ✅ Riga di lancio `agente: <tipo> brief: "<percorso>"[ model: <m>]` (`:65`); `Launch.model` da `review.models` (decisione 21); `taskcmd.py:142` tiene `inherit` dal giro 4 (`renamed`). Il test percorre davvero i giri 1-4.
- ✅ Comandi per il modello via `program_command(db.BIN_PATH)`; testo non fidato (must-have, scope, checklist, rilievi) in `_block`/`_bullets` con `brief.fence`, `DATA_NOTE` presente; divieto di modifiche e test che scrivono file; sha e code alla lettera; gravità da `[severity]`; R3 e casi speciali.
- ✅ Strati: `finalreview` (flow) importa solo core, analysis e `taskcmd` (stesso strato); `brief.py` importa solo `plan`. CLI: `ReviewError` → uscita 1.
- ⚠️ Non verificabile qui: come `SubagentStop` (Task 8) passa lo stadio a `verify` e gestisce un verificatore che omette degli id (vedi Minor 3).

### Punti di forza
- `prepare` è una funzione a stadi chiara (`_prepare` → `_open` → `_resume`), idempotente: rilanciare riprende senza duplicare cicli (test `resume_open_cycle_keeps_code`, `already_passed`, `same_patch_id_after_rebase`).
- I test controllano comportamento reale (DB, file scritti, riga di lancio, percorso con spazi) e coprono i casi non richiesti dal brief (L0, componente spento, `review_unverified`, supersede, verify senza rilievi chiude il ciclo, `needs_fix` poi ciclo 2, CLI con uscita 1).
- Gli esiti del DB passano solo da funzioni di `reviews`; `sqlite3.Error`, `GitError`, `ConfigError`, `TaskError`, `OSError` sono convertiti in `ReviewError`.

### Rilievi

**Important**
1. `bin/tollgate_flow/finalreview.py:198` (`_final_brief`): `except taskcmd.TaskError: must_haves = []`. Se il piano non si legge (blob assente, `plan_sha` vuoto), l'errore è inghiottito e il revisore finale riceve un brief con «Must-have: (nessuno)» e il ciclo parte lo stesso. È fail-open proprio sul confronto con piano e must-have che 8.6 chiede al revisore finale, e il test non lo copre. Correzione: lasciar propagare (`prepare` converte già `TaskError` in `ReviewError` con uscita 1) oppure rifiutare prima di `open_cycle`; così non si apre nemmeno un ciclo che consuma uno degli 8. Un test: piano non leggibile → `ReviewError`, nessun ciclo.

**Minor**
2. `finalreview.py:16`: `phases` importato e non usato.
3. `finalreview.py:161-177`: nello stadio `verify`, se il verificatore ha riportato ma ha omesso degli id, `to_verify` li restituisce ancora e `prepare` rilancia un verificatore a ogni chiamata, senza limite (spec: un verificatore per ciclo; i rilievi senza risultato «restano senza esito»). Dipende da cosa fa il Task 8 (⚠️): se non marca `unverified` gli id omessi, valutare un tetto o una riga che lo dica all'utente.
4. `brief.py` `final_review_brief` e `verifier_brief`: i JSON d'esempio non hanno `"v": 1`, mentre `review_brief` del task sì e la regola comune di 18 (C22) lo vuole su ogni verdetto. I parser lo ignorano, quindi nessun danno oggi; allineare insieme agli agenti (Task 16).
5. `_final_brief` ricalcola `check_plan` (e rilegge il piano) per ogni agente del ciclo: calcolarlo una volta in `_resume`.
6. Ripresa dopo rebase (stesso patch-id, SHA diverso): il brief riporta `sha` del ciclo (vecchio) e `head`/`base` nuovi. È coerente con la validazione dell'SHA del ciclo, ma il brief non lo dice; una riga di spiegazione eviterebbe confusione al revisore.
7. `finalreview.py:87-88`: se `default_ref` dà `None` e manca `work_base_sha`, `load_config` riceve `None` e il messaggio è «riferimento git non valido: None». `finishcheck.py:96-98` ha un rifiuto esplicito; stesso schema qui (taskcmd ha lo stesso difetto, non è del diff).
8. `issue_file` punta a `.tollgate-run/<N>/issue.md` anche se `start` non lo ha scritto (`start.py:398-400`): il report lo dichiara, ma il brief può citare un file inesistente. Citarlo solo se esiste.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** Requisiti e decisioni (C16, C7, M1, 5, 6, 8, 21) rispettati e ben testati, ma l'inghiottimento di `TaskError` nel brief del revisore finale (Important 1) apre un ciclo con must-have vuoti senza segnalarlo. Il resto sono rifiniture.
