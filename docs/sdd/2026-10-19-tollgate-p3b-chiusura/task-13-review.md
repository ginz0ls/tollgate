# Revisione Task 13 (e32ba57): abandon, cleanup, merge e chiusura in ripresa

### Aderenza
- ✅ `gitw.worktree_remove` senza `--force` (`gitw.py:55-58`); worktree sporco rifiutato da git e, prima, saltato da `_wt_state` (`closing.py:405`, `_remove` 477). `info/exclude` copre `.tollgate-run/` e checkpoint (`start.py:23`), quindi non blocca la rimozione di un worktree pulito.
- ✅ `abandon` (dec. 3 e 20): atto con `work=None` e `target=N` (`closing.py:380`), lavoro attivo trovato per (repo, N), `set_phase(closed, abandoned)`, ramo/worktree/PR intatti, atto consumato dopo la chiusura. Test su fase, causa evento, ramo e worktree presenti, atto non coincidente.
- ✅ `cleanup` (dec. 19): senza `--confirm` elenca, codice 3, atto non consumato (`closing.py:519-523`); con `--confirm` consuma e poi toglie. Ramo con `gitw.delete_branch` sullo SHA letto in `collect` (`update-ref -d <sha>`, atomico; lo SHA è nel messaggio per il recupero). Salta ramo del checkout principale, rami di lavori attivi, worktree in cui si trova `cwd`.
- ✅ Orfani: solo con `--orphans`; senza, indicati con «adottalo con /tollgate:adopt #N, se non c'è già un lavoro attivo». Caso riga 55 (ramo `tg/7-*` non in `known`, riga attiva per lo stesso N su altro ramo) coperto da `test_cleanup_orphans_only_with_flag`.
- ✅ Ripresa (`start.py:131-150, 162-166`): `merged` -> «lavoro #N chiuso: la PR è stata unita», codice 0, nessun `EnterWorktree`; `closed` -> conferma (3) con `closed_line`/`CLOSED_HINT`, con `--confirm` `set_pr(None, None)` dopo il ripristino del worktree; errore di `gh`/senza rete -> avviso (`prstate.detect` lo restituisce in `error`) e ripresa. `complete_interrupted` resta dopo il rilevamento e usa `row` rinfrescato: non rotto.
- ✅ C11: `closed_tg` nuova, `orphan_tg` invariata (i suoi test non cambiano), tre chiamanti passano da `orphan_next`; `tollgate_checks` non scrive nel DB (solo SELECT). Test su edit, Bash e SessionStart, più il caso di controllo che resta `adopt`.
- ✅ Strati: `closing` importa solo core/flow; la CLI lo importa in `cli.py` (ammesso). `cli_session` usata per entrambi i sottocomandi. Comando da ripetere con `program_command`.
- Dubbi del report: (1) `cleanup --confirm` con avvisi esce 0: corretto (nessun errore, solo voci saltate). (2) `pr_open` con PR scollegata resta tale: già assegnato al Task 15 (carry). (3) `program_command(db.BIN_PATH)`: in linea con i vincoli.
- ⚠️ Non verificato: nessuna esecuzione propria; mi fido di `tests/run` verde (1363 test, due interpreti) riportato.

### Punti di forza
Ordine sicuro in `_remove` (se il worktree resta, resta il ramo); doppia difesa sul worktree sporco; `delete_branch` condizionata allo SHA; test che verificano effetti reali su git e DB (atto `pending`/`consumed`, secondo giro rifiutato, repo diverso, ramo del checkout principale); `collect` separa chiaramente elenco e rimozione.

### Rilievi
Critical: nessuno. Important: nessuno.

Minor
1. `closing.py:333` e `_common.py` (`_TG`): gli orfani sono solo `tg/<N>-*`, mentre la decisione 19 dice «rami `tg/*`». Coerente con `orphan_tg` e con `adopt` (serve N) e dichiarato nel report; un `tg/foo` non è né adottabile né ripulibile. Valutare di annotarlo nella rev 23.
2. `closing.py:440-441`: registrazione di worktree senza cartella ignorata, ma non si fa `git worktree prune`: dopo `cleanup` resta la voce stantia (il ramo viene tolto comunque, `update-ref -d` non guarda i worktree). Innocuo; un `prune` dopo la rimozione sarebbe più pulito.
3. `closing.py:387-391` (`abandon`): se il processo muore tra `set_phase` e `consume`, l'atto resta `pending` e la ripetizione rifiuta («nessun lavoro attivo»); si risolve alla scadenza. Accettabile, ma l'ordine opposto a `open-pr` (atto per ultimo) merita una riga di commento.
4. Regex `_TG` duplicata fra `closing.py` e `_common.py` (strati diversi: `tollgate_checks` non può essere importato dal flow). Se esiste un parser del nome ramo in `tollgate_analysis.naming`, usarlo in entrambi.
5. Test mancanti, non bloccanti: worktree con `cwd` dentro (avviso), cartella del worktree sparita, `start --confirm` su PR chiusa insieme ad altre conferme.

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti, decisioni 3/12/19/20 e C11 rispettati, sicurezza delle cancellazioni solida e test aderenti al comportamento; restano solo rifiniture minori.
