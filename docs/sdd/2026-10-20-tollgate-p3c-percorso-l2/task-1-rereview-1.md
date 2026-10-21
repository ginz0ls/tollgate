# Ri-revisione giro 1, Task 1 (cf5f0e4..221b47f)

### Verdetti sui rilievi
1. **EnterWorktree attribuito a Task 13/14**: INDIRIZZATO. `docs/verifiche/2026-10-20-p3c-verifiche.md` (riga EnterWorktree) ora dice «nessuna nuova dipendenza», cita `skills/start/SKILL.md:30`, `skills/adopt/SKILL.md:22`, `bin/tollgate_flow/adopt.py:360` (verificati con grep) e dice che il Task 14 usa `cd` (piano riga 514: ogni `claude -p` parte dalla cartella del worktree).
2. **UserPromptExpansion/command_args attribuiti a Task 7/8 come lettura diretta**: INDIRIZZATO. La cella dice «nessun uso nuovo nel codice di P3c», meccanismo di P3b, Task 7 e 8 via `act apply` (piano righe 317-326, 360: `APPLIERS`), skill `reopen` con `disable-model-invocation: true` (piano riga 485, Task 13).
3. **agent_type: il Task 6 usa `subagents.type`**: INDIRIZZATO. La cella cita `awaiting_audit` e `row["type"] == audits.AGENTS[giro.kind]` (piano riga 288), esclude il payload di `SubagentStop`, dice che i tipi vuoti restano senza riga. I nomi dei tre agenti coincidono con `audits.AGENTS` (piano riga 35).

Minor della revisione: `handbackReport` aggiunto nella riga SubagentHandback, con riferimento a K3 e alla tabella dei rilievi di P0 (riga 108: la correzione di K3 esiste lì). Chiuso.

### Danni nuovi nel diff della correzione
Nessuno. Solo 4 righe di tabella cambiate in un documento.

### Osservazioni fuori ambito
Nessuna. Nota: il report cita «1444 test» contro i 1417 del primo report; non è contraddittorio (suite cresciuta), ma non è verificabile dal diff, che tocca solo un .md.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
