# Revisione Task 4 (rilevamento per contenuto), 8e438c0..83ef553

### Aderenza
- ✅ `git.grep_files_at` (git.py:336-355): un solo `git grep -z -I -l -F -e m… <ref> -- <pathspec>`; `_check_ref`; rc 1 senza output = `[]`; altri rc e timeout (`_proc`) = `GitError`; prefisso `<ref>:` tolto; split su NUL. Provato in un repo temporaneo fuori dal progetto: `:(glob)**/*.py` prende anche i file in radice, nomi con spazi, accenti e virgolette escono non citati, un marcatore che comincia con `-` è gestito da `-e`.
- ✅ Decisione 6 alla lettera (init.py:46-52, 227-237): estensioni, `EXCLUDED_PREFIXES`, `tests/ test/ __tests__/`, `*.test.* *.spec.* *_test.* test_*.py conftest.py`, tetto 256 KiB da `sizes` (bordo esatto testato: `edge.py`), `sizes.get` assente = fuori. Binari via `-I` (testato). `package.json` e `README.md` fuori per estensione.
- ✅ D3 (init.py:240-258): un grep per frammento con marcatori, `GitError` per area -> area vuota + avviso, gli altri frammenti proseguono. Test `test_one_grep_per_fragment_with_markers` e `test_detect_timeout_warns`.
- ✅ D17: già in `_drift` (init.py:302-306), `uncovered_detected` richiede `not match_any` e nessun `!p`; test nei due ordini.
- ✅ D16: nel diff di `bin/` nessun `tollgate <sottocomando>` nudo né «protezione».
- ✅ D2 intatta: il `try/except git.GitError` di `propose` copre anche `detect_files`.
- Scostamenti: parametro opzionale `warnings` giudicato accettabile (ritorno invariato, avviso in terminale e nel README, testato). `fragments.load` due volte: accettabile (vedi Minor); l'adattamento del test a un insieme è corretto, non nasconde nulla.
- ⚠️ Suite completa e RED non rilanciati: mi fido dei file `.out` citati nel report.

### Punti di forza
- `_is_detectable` pura e separata dal git; filtri applicati dopo il grep come da piano.
- Gli avvisi passano da `_plain` e `_fenced` (testo di repo ripulito).
- Test sui bordi veri: 256 KiB esatti, byte nullo, `__tests__`, `_test.go`, `.mts`, nome accentato, prefissi esclusi, negazioni in entrambi gli ordini.

### Rilievi
**Critical / Important:** nessuno.

**Minor**
1. init.py:661-663 e `profile_blocks`: `fragments.load` + `approved` fatti due volte (il filtro `approved` è duplicato). Letture di file piccoli, nessun difetto; se in futuro `profile_blocks` accettasse i frammenti già caricati sparirebbe la duplicazione.
2. Nessun test con due frammenti in cui il primo fallisce e il secondo riesce (la promessa di D3 «non ferma gli altri» è nel codice, init.py:246-251, ma non asserita; in B3 c'è un solo frammento).
3. `grep_files_at` con un marcatore stringa vuota matcherebbe ogni file: se la validazione di `Fragment.detect` non lo vieta (non verificato, fuori diff) conviene un test lì (Task 2).
4. I test di `grep_files_at` stanno in `LsFilesAtTest` (nome fuorviante, innocuo).

### Valutazione
**Qualità del task:** Approvato
**Motivo:** requisiti e decisioni D3/D6/D17/D16 rispettati e verificati sul diff e con prove mirate di `git grep`; solo rifiniture Minor.
