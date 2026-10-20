# Revisione Task 14 — `task start --from-findings` e `--from-gate` (e505bd6..., commit 505bd6d)

### Aderenza
- ✅ `--from-findings`: fase `execution` (fixtask.py:78), ciclo inesistente / non `needs_fix` / senza bloccanti aperti rifiutati (fixtask.py:34-44), `source = cycle:<n>` unico (fixtask.py:85-88), numero `next_number` (max+1), `kind="fix"`, piano e `plan_sha` non toccati (test `…without_touching_plan`).
- ✅ Rilievi dai soli `reviews.blocking_open` del ciclo, in recinto (`brief._block`, più lungo dei backtick, testato con ``` nel testo), nota `DATA_NOTE`; file fuori scope marcato «serve una deroga» (brief.py:53-67); scope invariato (scope del lavoro).
- ✅ Instradamento da `task_routing` sui file dei rilievi (`_fix_files`, taskcmd.py:66-73), sia in `task start` sia in `review-prepare`.
- ✅ `--from-gate`: fase `execution`, PR nota, ultimo commento con `GATE_MARKER` come dato recintato, `source = gate:<sha>`; il testo non va mai in un argomento di `gh` (verificato nel test sugli argv).
- ✅ Riepilogo identico a `task start` (stessa `_task_start`): tipo, `name`, `launch`, revisore; `name` del brief = `tasks.implementer` (stessa `assign`); `tasks.assign` con `pending`.
- ✅ Errori `TaskError`; strati rispettati (fixtask importa solo core/analysis/flow); CLI: combinazioni errate e assenza di argomenti → codice 2.
- ✅ `task_text` persistito; `task start --fix` e `review-prepare` leggono il testo salvato (test `fix_round`, `review_and_done`).
- ✅ Transazione unica: add_task + `_task_start` (db.tx si annida); rollback se brief/assegnazione falliscono. `open_block` non è raggiungibile con `fix=False`, quindi nessuna violazione del vincolo «fuori da transazione».
- ⚠️ Evidenza dei test (1374 OK su 3.11 e 3.13) è solo dichiarata nel report, non rilanciata.

### Punti di forza
- Riuso di `_task_start` invece di duplicare brief/assegnazione; rollback atomico del task.
- Lettura di `gh` fuori dalla transazione; troncamento del commento (20000).
- Test sui casi chiave (doppio avvio, ciclo ok, fase errata, recinto, commenti multipli).

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. fixtask.py:62-64 — `gate:<sha>` usa l'HEAD del worktree, non il commit giudicato dal gate. Se il gate non ha ancora ripostato dopo un commit di correzione, un secondo `--from-gate` rilegge il commento vecchio e crea un duplicato (il controllo `source` non lo ferma). Meglio `headRefOid` della PR o lo sha nel marcatore (da concordare con P4).
2. fixtask.py:55-56 — l'autore del commento non è verificato: chiunque possa commentare la PR può inserire un commento col marcatore. Resta dato recintato (nessuna esecuzione), quindi è solo un rischio di indirizzamento; ⚠️ la spec non chiede il controllo.
3. fixtask.py:74-82 duplica i controlli di `taskcmd._task_start` (lavoro, L0, fase) con messaggi diversi, e chiama la funzione privata `taskcmd._task_start`. Accettabile ma fragile se la firma cambia.
4. taskcmd.py:66-73 — `_fix_files` rilegge `blocking_open` dal vivo: se un rilievo viene poi archiviato (`dismissed`) l'instradamento in `review-prepare` può differire da quello di `task start`. Più stabile salvare i file alla creazione.
5. brief.py:42-44 — `_finding` stampa la gravità originale, non `effective_severity` (rilievo declassato dall'utente).
6. Test: manca un caso di rollback (brief/assegnazione che fallisce lascia 0 task nuovi), L0 e CLI `--from-gate`; l'asserzione sul recinto del gate (`replace("\n\n","\n")`) è lasca. Il file di brief resta in `.tollgate-run` dopo un fallimento (dichiarato dal report, innocuo).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti della decisione 16 e della spec 6.3 rispettati sul diff, testo non fidato sempre recintato e mai in argomenti, task atomico e riuso pulito di `_task_start`; restano solo rifiniture minori (sha del gate, copertura rollback).
