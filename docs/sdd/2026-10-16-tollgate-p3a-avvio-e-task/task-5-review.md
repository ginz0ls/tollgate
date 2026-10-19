# Revisione Task 5 (fdf5d7b)

### Aderenza
- ✅ `task_text` (`plan.py:281`): si ferma alla `##`/`###` successiva, rispetta i recinti, restituisce None se il task manca.
- ✅ Recinti (`plan.py:218-236`): ``` e ~~~, chiusura solo con lo stesso carattere, lunghezza ≥ e niente altro sulla riga. Provato a mano: `###` dentro ``` e ~~~ non chiude; `~~~~` chiude `~~~`.
- ✅ must-have in grassetto, `M1 duplicato`, `task N duplicato` (`plan.py:323-325`).
- ✅ `task_routing` (`profiles.py:394`) segue la decisione 15: un solo valore dichiarato vince, altrimenti i generici; unione skill; reviewer_skills da verticali e cross elencati; tetto 3; split.
- ✅ `size.task_lines` e `GENERATED`: `subagent_stop._task_lines` calcola la stessa cosa di prima (stessi filtri, stessa somma). `posixpath` e `globs` non servono più in `subagent_stop` (grep: nessun uso residuo); nessun test usa `_GENERATED`.
- ✅ `brief.py`: `fence` = max sequenza + 1 (min 3); tutto il testo esterno è in `_block`; ordine delle sezioni, `name`, `verify_cmd`, `block open test_spec_conflict`, campi di `report.REQUIRED` e campi del verdetto coerenti con 18.5; standard coerente con 8.6; `sha`/`code` alla lettera.
- ✅ Strati: `tollgate_analysis` importa solo se stesso; solo libreria standard.
- ✅ Tipi scelti (`must_haves: list[MustHave]`, `fix_findings: list[dict]`, `concerns: str`): sensati e compatibili con `carry.md`.
- ❌ «le correzioni non cambiano gli esiti dei piani già validi»: vedi Important 1.

### Punti di forza
- `_Fences` è una macchina a stati piccola, usata sia dal parser sia da `task_text`: nessuna duplicazione dei recinti.
- Test sui recinti con tre coppie apertura/chiusura; test del brief verificano ordine, recinto più lungo e rilievi con backtick.
- Refactor di `subagent_stop` minimo.

### Rilievi

**Important 1 — `plan.py:208-215` `_file_values` raccoglie ogni testo tra apici della riga, anche nei commenti.**
Con apici prende tutti i `` `...` `` della riga, quindi un commento come `` - Modify: `a.py` (vedi `docs/x.md`) `` dà `['a.py', 'docs/x.md']` e `` - Create: `b.py` — usa `old()` `` dà `['b.py', 'old()']`. Prima contava solo il primo file. Effetto reale (verificato eseguendo `check_plan` vecchio e nuovo su `docs/superpowers/plans/*.md`):
- il piano P3a stesso passa da 42 a 100 file di scope e **non è più valido** (`pattern o cartella non ammessi nello scope: /tollgate:*`); la riga 436 (`` - Modify: `…/subagent_stop.py` (usa `size.task_lines`; `_GENERATED` si sposta in `size.GENERATED`) ``) mette nello scope `size.task_lines`, `_GENERATED`, `size.GENERATED`;
- il piano P1 passa da 27 a 29 (`git`, `make_repo`), il P2-guardrail da 83 a 118 (`SCHEMA_V1`, `MIGRATIONS`, `"1"`…).
Questi piani sono quelli che `post_edit._plan` (`post_edit.py:26`) registra con `scope=r.scope` e `task_skills(t.files)`: scope gonfiato, falsi problemi, skill sbagliate. È esattamente il rischio «gli esiti dei piani validi non cambiano». `test_existing_cases_unchanged` verifica solo `check(make()).ok` e non lo copre.
Correzione: scartare le parentesi anche nel ramo con apici (`_PAREN.sub("", raw)` prima di `_TICK.findall`) e prendere i token tra apici solo finché la riga è un elenco (apici separati da virgole, spazi, o "e"); fermarsi al primo testo che non è un separatore (`—`, `-`, `:`). Aggiungere test: `` `a.py` (vedi `docs/x.md`) `` → solo `a.py`; `` `b.py` — usa `old()` `` → solo `b.py`; e un test di non regressione che confronta lo scope dei piani reali già validi.

**Minor**
- `profiles.py:394-409` `task_routing` ripete la risoluzione verticale/skill di `task_skills` (`profiles.py:51`) ma con ordine diverso: dichiarazione dei profili (decisione 15) contro ordine dei file. `post_edit.py` salva `skills_required` con `task_skills(...)[:3]` (ordine dei file) e `subagent_stop` verifica quelle: con più di 3 skill o verticali in ordine diverso brief e `skills_required` possono divergere. Il Task 6 deve scegliere una sola fonte (idealmente far usare a `post_edit` e al brief lo stesso risultato) o allineare l'ordine.
- `plan.py:229` apertura con rientro qualsiasi (`^\s*`): CommonMark ammette al massimo 3 spazi (4+ è codice indentato). Innocuo per i piani reali.
- `brief.py:101` `verify_cmd` e `b.name`/`agent_type`/percorsi sono inseriti tra apici semplici non recintati: provengono da config/controller, non dall'issue, quindi ok oggi; un backtick nel percorso del plugin romperebbe il rendering.
- `test_size.py:759` `test_generated_patterns` asserisce solo `len == 4`: poco utile (i pattern sono già coperti dal test precedente).

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** il supporto a più file per riga cambia l'esito di piani già validi (incluso il piano P3a stesso, che diventa invalido) perché raccoglie anche i testi tra apici nei commenti; il resto (recinti, `task_text`, routing, `size`, `brief`) è corretto e ben testato. Test non rilanciati; verifiche fatte con esecuzioni mirate di `check_plan` (vecchio contro nuovo) e `_file_values`, con `python3 -B`.
