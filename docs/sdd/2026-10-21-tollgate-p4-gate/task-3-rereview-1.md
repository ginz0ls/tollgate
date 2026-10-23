# Ri-revisione Task 3, giro di correzione 1 (9e52745)

### Verdetti sui rilievi

**I-1 — un solo calcolo del giudizio sulla spec per `check_l2_detail` e `l2tree.spec_approval`**: INDIRIZZATO.
- `approvals.judge_spec` (`bin/tollgate_analysis/approvals.py`, nuovo, con `SpecJudgement(status, found, approval)` e `CURRENT` aggiunta accanto a `MISSING`/`STALE`) è l'unico calcolo; `check_l2_detail` lo usa (spec solo di un'altra issue e cambiata: `STALE` col percorso di quell'approvazione) e `l2tree.spec_approval` lo usa restituendo `(status, found)`, stessa firma e stessi valori (`l2tree.CURRENT/STALE/MISSING` sono alias di quelli di `approvals`; `bin/tollgate_gate/l2tree.py`).
- Test: `JudgeSpecTest` (3, tra cui l'accordo con `check_l2_detail`) in `tests/test_approvals.py`; `test_agrees_with_check_l2_detail_on_only_another_issue_stale` in `tests/test_l2tree.py`. I test esistenti di l2tree non sono toccati nel diff.
- Isolamento: nessun `import` di `tollgate*` fuori da `tollgate_analysis` nel pacchetto (grep vuoto).

**I-2 — `workflows.problems` fail-closed su escape in stringhe a doppie virgolette (chiave, `on:`) e su chiave complessa**: NON INDIRIZZATO (coperti i casi dei test, restano evasioni equivalenti).
Provate con `python3 -B` su `problems()`; tutte sotto restituiscono `[]` (verde) ma sono YAML validi che GitHub legge come l'evento vietato o lo scope `statuses`:

1. `on: [` / `  push,` / `  "pull_request_\x74arget"` / `]` (elenco di flusso su più righe, con o senza virgola finale): nessuna riga ha `-` o `:`, quindi `_ESCAPED_ITEM`, `_ESCAPED_KEY` non scattano, e `_ESCAPED_ON` guarda solo la riga `on:`. Evasione dell'evento.
2. `on:` + a capo + `  [push, "pull_request_\x74arget"]` (valore di flusso sulla riga successiva): stesso motivo, `[]`.
3. `permissions: {` / `  contents: read,` / `  "\x73tatuses"` / `  : write` / `}` (due punti sulla riga dopo la chiave): `_ESCAPED_KEY` richiede il `:` sulla stessa riga, `[]`.
4. Chiave a doppie virgolette su più righe con continuazione: `"stat\` / `  uses": write`: la prima riga non ha stringa chiusa, `[]`.

Passano, invece, e sono corretti: escape in chiave di blocco, `{"\x73tatuses": write}`, `on: "…\x74arget"`, `on: ["…"]` su una riga, `- "…"` come voce di blocco, chiave di `on` a doppie virgolette, chiave `? statuses` con spazio (anche in flusso, per via di `_SCOPE`). `?statuses` senza spazio è uno scalare semplice, non una chiave complessa: il verde è giusto.

Causa comune: i controlli sono per riga e legati alla forma sintattica; il difetto specifico («un escape in una stringa tra virgolette doppie dove si legge un nome») non è chiuso. Strada più robusta: dentro il blocco `on:` (dalla riga `on:` fino alla prossima chiave di primo livello) e dentro un blocco `permissions` rosso su qualunque `\` in una stringa a doppie virgolette; oppure rosso su ogni stringa a doppie virgolette con `\` fuori da un valore `run:`/`env`/`with`. In alternativa rifiutare le stringhe a più righe con `\` finale e le chiavi con `:` a capo (già non gestite per il resto).

### Danni nuovi nel diff della correzione
Nessuno. Falsi positivi controllati dai test (`run: "echo \"ciao\""`, `A: "x\ny"`, `run: echo ?`); `_COMPLEX_KEY` non scatta su `?` in un valore.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Rilievi ancora aperti: I-2 (evasioni 1-4 sopra, in particolare 1-2 sull'evento `pull_request_target` in elenco di flusso su più righe). I-1 indirizzato.
