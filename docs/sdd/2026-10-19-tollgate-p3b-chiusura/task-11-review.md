# Revisione Task 11 (`sync`), 38ff416..8a3e450

### Aderenza
- ✅ Atto `sync` via `cli_session("sync", argv=…)` e consumo (`sync.py:_sync`, `_consume`); rifiuto senza atto (`test_refused_without_sync_act`).
- ✅ Intento `sync:<lavoro>:<atto>` con from/to/base registrato PRIMA di integrazione e rebase (`sync.py` `intents.request` prima del `try`). ⚠️ nessun test ne fissa l'ordine (vedi Minor 2).
- ✅ `fetch` prima; commit remoti con `merge --ff-only`; divergenza = `needs_you`; push nostro poi riscritto riconosciuto dagli eventi `commit`.
- ✅ Conflitto: `rebase --abort`, nessun rebase in corso, base e fase invariate (la fase passa a `blocked` con `phase_before_block`, come ogni `open_block`), `needs_you` con `SYNC_CONFLICT_REASON` e le due strade; `approve rebase` lo riconosce dal prefisso.
- ✅ Riuscito: `base_realigned`, eventi `commit` dei SHA non noti, `pr_open → execution` (causa `sync`), `authorize_force` solo se il remoto non è antenato di HEAD, poi `finish check`, `review_state` (stesso `patch-id`) e `open_pr(update, via_sync)`. Patch-id diverso: codice 3 «serve una nuova revisione: /tollgate:finish», nessun push (`test_different_patch_id_asks_new_review`).
- ✅ `complete_interrupted`: intento `requested`, nessun rebase in corso, punta di arrivo antenata di HEAD, nessun nuovo rebase; chiamata in `start` dopo il calcolo di `wt` e prima di `_pending_intents` (C20). Con rebase in corso resta la proposta `rebase --abort`.
- ✅ Mai un push forzato senza intento dentro `sync` (il push è di `open_pr`, che richiede l'intento e usa `--force-with-lease=<ref>:<sha>`).
- ✅ Strati rispettati; nessuna rete; `gitw.is_ancestor` riusato (C19). Sezione «Task 11» di carry.md: PR `CLOSED` rifiutata con `CLOSED_HINT` (testato).
- ⚠️ Scostamento del report (fase `review` ammessa solo con PR esistente): giustificato, perché `finish check` dentro `sync` porta la fase a `review` e la ripetizione dopo codice 3 o dopo un `open-pr` fallito deve poter ripartire. Accettato.
- ❌ Review Focus 4, combinazione «Update branch remoto + predefinito avanzato + conflitto»: vedi Important 1.

### Punti di forza
- Passi di `_realign` tutti ripetibili e riusati identici da `sync` e dalla ripresa: nessuna duplicazione, il completamento dell'interrotto è davvero senza rebase.
- Eccezione di `rebase()` ben distinta: falso solo con rebase in corso, altrimenti `GitWriteError` e intento chiuso «non riuscito».
- Test veri su repo git reali (clone con «Update branch», `wraps` su `merge_ff_only`, controllo positivo in `test_post_bash_ignores_rewritten_commits`), TDD e mutazioni dichiarate coerenti con il codice.
- Euristica «push nostro poi riscritto» coperta da un test dedicato (`test_repeat_after_review_needed_is_not_divergent`).

### Rilievi

**Important 1: i commit integrati con `--ff-only` non sono registrati se poi il rebase va in conflitto (o i rami risultano divergenti dopo un'integrazione, o il processo muore tra integrazione e rebase).**
`sync.py:_sync` (blocco `_remote_conflict` → `rebase` → `rebase_abort` → `_block`) lascia HEAD sulla punta remota (es. il merge «Update branch» e i commit del predefinito che porta con sé), con base invariata e senza eventi `commit` per quei SHA. Il primo `PostToolUse Bash` nel worktree (`bin/tollgate_checks/post_bash.py:38-56`) vede `rev_list(base, HEAD)` con SHA ignoti, li registra come nuovi, li passa a `commit_violations` (commit di terzi, fuori scope) e può aprire `needs_you` per «commit con violazioni senza deroga» e invalidare l'atto `finish`. Verificato con una sonda (test temporaneo fuori dal repo): remoto con «Update branch», predefinito avanzato in conflitto su `src/app.py`, `sync` → codice 2, HEAD spostato, 2 commit ignoti in `base..HEAD`. È proprio lo scenario del Review Focus 4 e il test `test_conflict_aborts_and_blocks` non include il merge remoto, quindi non lo vede. Spec 6.5: «`sync` registra i commit riscritti, così PostToolUse Bash non li tratta come nuovi».
Correzione: dopo `merge_ff_only` riuscito registrare subito gli eventi `commit` per `rev_list(base, HEAD)` non noti (stessa logica di `_realign`, da estrarre in una funzione condivisa), oppure farlo anche nel ramo `_block`; aggiungere il test «Update branch + predefinito in conflitto → nessun SHA ignoto in `base..HEAD` e `PostToolUse Bash` non apre blocchi». Stesso discorso per la divergenza dopo l'integrazione e per `complete_interrupted` se l'integrazione è avvenuta ma il rebase no.

**Minor**
1. `sync.py:_remote_conflict`: se un primo `sync` ha integrato il merge «Update branch» M e si è fermato con codice 3, M non è più in HEAD (il rebase lo scarta) né è un evento `commit`; un secondo `sync` vede `origin/<ramo>` = M come divergente e apre `needs_you` a torto. Registrare come noto lo SHA remoto integrato (o confrontare con gli intenti `sync` precedenti).
2. Nessun test fissa l'ordine «intento prima del rebase» (spostare `intents.request` dopo il rebase non romperebbe nulla: `test_interrupted_sync_*` costruiscono l'intento a mano). Un test che, con `gitw.rebase` sostituito, controlla l'intento `requested` con from/to/base al momento della chiamata.
3. `sync.py:_sync`: un'eccezione diversa da `GitWriteError` (per esempio `git.GitError` in `resolve_ref`) tra richiesta e fine lascia l'intento `requested`; alla ripresa chiede conferma anche se non è successo nulla. Chiudere l'intento anche in quel caso.
4. L'autorizzazione al push forzato non porta lo SHA remoto atteso: `open_pr` rilegge `remote_sha` e lo usa come lease, quindi i commit remoti arrivati tra `sync` e `finish` verrebbero sovrascritti. Vale anche per `approve rebase`; è una scelta del Task 9, da ricordare nella revisione del ramo.
5. `complete_interrupted` agisce su DB e fase prima della conferma `--confirm` della sessione viva (ordine imposto da C20): accettabile, da tenere presente.
6. Mancano test per: rifiuto con rebase in corso all'avvio di `sync`, fallimento di `merge_ff_only`, `finish check` rosso dopo il rebase (codice 1).

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** l'impianto (intento prima del rebase, conflitto con abort e `needs_you`, ripresa senza rebase, nessun push forzato senza intento) è corretto e ben testato, ma nel caso del Review Focus 4 con «Update branch» e conflitto l'integrazione `--ff-only` lascia commit non registrati che il hook `PostToolUse Bash` tratta come nuovi, con rischio di blocco spurio; va registrato e coperto da un test.
