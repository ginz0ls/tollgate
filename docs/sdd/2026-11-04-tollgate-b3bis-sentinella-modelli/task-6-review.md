# Revisione Task 6 (920db67..ae271c8)

### Aderenza
- ✅ `tollgate_skill` (flowreg.py, ~r.262): radici note come letterali, cartelle di `skills/` da `Path(__file__).resolve().parents[2]` (D27), non usa `ROOT.name`. Tutti i casi del brief tornano (verificati leggendo la logica e con i test mirati, verdi).
- ✅ Un solo iteratore `_third_party` + `_scan`; `togli_pagine` e `third_party_blocks` lo usano; il controllo `codeText` è dentro (tipo `tool_use_result`).
- ✅ Hook (D26): type/subtype/hook_event, `json.loads` e `additionalContext` che comincia con `tollgate:`, non JSON → di terzi, segnaposto con `hook_name`, sostituisce `output` e `stdout`; segnaposto già presente e vuoto ignorati. Idempotenza asserita dal test (0 e `[]`).
- ✅ 8 `.jsonl`: ognuno resta JSON valido riga per riga, stesso numero di righe e di `tool_use`; cambiano solo le righe attese (skill `writing-plans` 1 per file; 3 hook di terzi per file in gh-p4). Le uscite di tollgate (463 caratteri) non sono toccate. Nessun testo di terzi nel report né nei file nuovi (solo nomi e lunghezze).
- ✅ Il test esteso scorre `rglob("*.jsonl")` su `evidenze/` (149 `.jsonl` tracciati, nessun altro formato di stream); righe nei tre rapporti presenti.
- ⚠️ Il RED dei tre test unitari non è mai stato visto (dichiarato). Letti: asseriscono davvero (valori esatti dei segnaposto, entrambi i campi, uscita di tollgate invariata, hook non SessionStart, vuoto, idempotenza), quindi discriminano; non sono banali.

### Punti di forza
Logica unica e testabile; sostituzioni con closure applicate dopo la scansione completa; il test esteso copre ora tutte le evidenze; pulizia chirurgica.

### Rilievi
**Important**
- `tests/test_b1_scripts.py` (test_tollgate_skill_by_folder_not_word, ultima riga): `assertNotEqual(ROOT.name, "Plugin IT workflow", ...)`. Il checkout principale si chiama proprio «Plugin IT workflow»: dopo il merge il test fallisce lì (solo nel worktree `b3bis` e in CI passa). Asserzione fragile e inutile: l'indipendenza da `ROOT.name` è già provata dai casi con altre radici. Correzione: toglierla, oppure provare l'indipendenza monkeypatchando/ignorando `ROOT` (i percorsi sono letterali, nessuna dipendenza da verificare).

**Minor**
- `_third_party`: l'ordine (skill, pagine, tool_use_result, hook) fa dipendere `names` dai tool_use della stessa riga; va bene per lo stream reale, nessuna azione.
- `tollgate_skill`: `p.parent.parent.name` vuoto per `/skills/x` è gestito; `REPO_SKILLS.iterdir()` è ricalcolato a ogni chiamata (costo trascurabile, ma si potrebbe calcolare una volta).

### Valutazione
**Qualità del task:** Da correggere (un solo rilievo Important, banale).
**Motivo:** Implementazione, pulizia delle evidenze e test sono corretti e coerenti con D26/D27; resta un'asserzione che rompe la suite nel checkout principale chiamato «Plugin IT workflow».
