### Task 4: Rilevamento del codice AI per contenuto

**Files:**
- Modify: `bin/tollgate_core/git.py`, `bin/tollgate_flow/init.py`
- Test: `tests/test_git.py`, `tests/test_init.py`

**Interfaces:**
- Consumes: `git.tree_sizes_at` e `init.profile_blocks(..., detected=…)` (Task 3); `Fragment.detect` (Task 2).
- Produces:
  - `git.grep_files_at(repo, ref, markers: list[str], pathspecs: list[str]) -> list[str]` (un solo `git grep -z -I -l -F -e <m> … <ref> -- <pathspecs>`, diviso su NUL come `ls_files_at`, percorsi senza il prefisso `<ref>:`; nessun risultato → `[]`; errore di git diverso da «nessun risultato» → `GitError`; tetto di tempo `GIT_TIMEOUT_S` di `_proc`);
  - `init.detect_files(repo, ref, fragments, sizes) -> dict[str, list[str]]` (per area, i file sorgente della decisione 6 che contengono un marcatore, ordinati).

- [ ] **Step 1: I test che falliscono.**
  - `tests/test_git.py`: `test_grep_files_at` (due marcatori, un file che ne ha uno, un binario con il marcatore escluso da `-I`, un pathspec che restringe, un nome accentato che esce non citato).
  - `tests/test_init.py`: `test_detect_adds_exact_paths` (`supabase/functions/notify/index.ts` con una riga `import Anthropic from "npm:@anthropic-ai/sdk"` entra nei percorsi del profilo col suo percorso esatto); `test_detect_skips_manifests_docs_and_tests` (`package.json` con la dipendenza, `README.md` con l'esempio, `tests/test_x.py`, `src/x.test.ts`, `src/x.spec.ts` e `conftest.py` che lo importano: fuori; `src/x.vue` e `src/y.mts` con l'import: dentro); `test_detect_skips_large_and_binary` (un sorgente oltre 256 KiB, e uno con un byte nullo nei primi 8000 byte: fuori); `test_detect_skips_excluded_prefixes` (`.claude/` e `.github/tollgate/`); `test_detect_file_already_covered_not_repeated`; `test_declared_profile_new_detected_file_reported` (profilo dichiarato, file nuovo con il marcatore fuori dai `paths`: una riga «aggiungi a `paths`»); `test_detect_timeout_warns` (`grep_files_at` che solleva `GitError` per il tempo: la proposta c'è, senza file rilevati, con la riga di avviso).
- [ ] **Step 2: Verifica che falliscano.**
- [ ] **Step 3: Il codice.** `grep_files_at` con `_proc` (stessi controlli di `_check_ref`); `detect_files` per la decisione 6: i pathspec sono le estensioni sorgente (forma `:(glob)**/*.py`), le esclusioni si applicano dopo, sui percorsi, insieme al tetto di 256 KiB letto da `sizes`. `propose` passa il risultato a `profile_blocks`.
- [ ] **Step 4: Verifica.** `python3 -B -m unittest tests.test_git tests.test_init`: PASS. `tests/run`: verde.
- [ ] **Step 5: Commit** «tollgate B3: init trova il codice AI fuori dalle cartelle tipiche».

---

