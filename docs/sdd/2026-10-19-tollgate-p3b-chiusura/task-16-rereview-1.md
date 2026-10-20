# Ri-revisione giro di correzione 1, Task 16 (b208c80..cbda3a7)

Sola lettura. Controlli mirati su `sync.py`, `start.py`, `openpr.py`, `finishcheck.py`, `actapply.py`, `reviews.py`, `acts.py`, `verify.py`, `finalreview.py`. `python3 -B -m unittest tests.test_manifest`: 24 OK.

### Verdetti sui rilievi

**Important 1, commit dopo l'atto `finish` fa decadere l'atto**: INDIRIZZATO. `skills/finish/SKILL.md` passo 1 ora controlla `git status`: sporco -> committa, chiedi di ridigitare `/tollgate:finish` e **fermati**, prima di `finish check`. Coerente con `acts._FINISH_ALIVE` (acts.py:19, decade a ogni commit successivo) e con `verify.py:200` (il gate rifiuta un albero sporco). Il test (`tests/test_manifest.py`, `test_finish_skill_keeps_worktree_clean`) asserisce la frase e che precede `<programma> finish check`.

**Important 2, tetto degli 8 cicli: `approve rounds` indicato a torto**: INDIRIZZATO. Passo 2.1 ora dice solo `approve unverified-review` al tetto assoluto e che `rounds` rifiuta (`actapply._grant_cycles`: `done + n > MAX_CYCLES`; messaggio di `finalreview.py:106`). Il ramo `needs_you` limita `rounds` al blocco «cicli di revisione esauriti» (4 contati, `reviews.CAP_COUNTED`, totale 8) o ai giri di un task fermo (`FIX_CAP`), e `unverified-review` solo dopo 8 cicli (`_approve_unverified_review`).

**Important 3, `sync` codice 2 con due casi**: INDIRIZZATO. `skills/sync/SKILL.md` distingue «sync: conflitto nel rebase …» (= `intents.SYNC_CONFLICT_REASON`, `sync.py:137`; `approve rebase` lo accetta, `actapply.py:170`) da «sync: il ramo remoto … e HEAD … sono divergenti …» (`sync.py:_remote_conflict`). Per i divergenti: `approve rebase` rifiuta davvero (nessun blocco con quel motivo); `/tollgate:resolve <id>` è accettato (`_resolve` chiude un qualunque blocco aperto del lavoro, motivo diverso da CAP_REASON, nessun vincolo sul testo); `abandon` resta. Il blocco lo apre `_block` con `needs_you` per entrambi i casi.

**Minor 4, `needs_fix` con blocco cicli aperto**: INDIRIZZATO. Il testo dice di non lanciare `task start` se la fase è `blocked` e di andare a `resolve` (concede un ciclo, `_resolve` -> `_grant_cycles(…,1)`) o `approve rounds`. Coerente con `reviews.py:333-335`.

**Minor 5, PR chiusa in `start`**: INDIRIZZATO. `start.py:139-141` mette la riga in `notes.confirms` (codice 3, `conferma:`); la voce 3 ora cita `--confirm` e `/tollgate:abandon #N`. La frase sotto «1, rifiuto» resta (duplicata): innocua, vedi osservazioni.

**Minor 6, «il controllo e la revisione»**: INDIRIZZATO. Ora «Il controllo rifiuta…», vero per `verify.run_gate`.

**Minor 7, `final-reviewer` e cartella temporanea**: INDIRIZZATO. `agents/final-reviewer.md` ora indica `git show <sha>:<percorso>` / `git archive` fuori dal repo e vieta `git checkout` e `git worktree add`.

**Minor 8, `adopt` in `pr_open`**: INDIRIZZATO. `skills/adopt/SKILL.md` aggiunge che `/tollgate:finish` rifiuta in `pr_open` e rimanda a `/tollgate:sync`. `finishcheck.py:80` ammette solo execution/review; `sync` ammette pr_open e lo riporta a execution (`_realign`).

**Minor 9, `--update` e `pr_open`**: INDIRIZZATO. `--update` è detto facoltativo (richiede solo una PR esistente, `openpr.py:208`; in `review` aggiorna comunque), e in `pr_open` il rifiuto (`openpr.py:134`) richiede il ritorno in `execution` via `/tollgate:sync` o `start --reopen-execution` (`start.py:216`) e un nuovo `finish check`. Eccezione di ripresa (`openpr.py:131`) non citata: irrilevante per l'uso normale.

### Danni nuovi nel diff della correzione

Nessuno.

### Osservazioni fuori ambito

- `skills/start/SKILL.md`, voce «1, rifiuto»: la frase sulla PR chiusa senza merge resta, ma `start` non rifiuta più per quel caso (codice 3). Dead text innocuo; si può togliere in un giro futuro.
- Il Minor 10 (test di sola presenza di sottostringhe) è fuori da questo giro come da dispatch; l'asserzione nuova per il rilievo 1 verifica però l'ordine.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
