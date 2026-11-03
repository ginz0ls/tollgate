### Task 11: Prove, revisione 29 della spec, piano principale, catalogo

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 29), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento), `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`

- [ ] **Step 1: Revisione 29 della spec del nucleo.** 6.3 (agenti per area con `skills: [rules-base, rules-<area>]`, fuori dal tetto; task misti, decisione 9); 7.3 (revisori per area negli elenchi di sola lettura, con `WebFetch`); 11.2 (`init` propone i profili: decisioni 4-7 e 12; `propose(..., profiles_root)`); 11.4 (frammento `templates/profiles/<area>.toml`, `[detect] content`, nomi riservati, `rules` calcolate dalla skill); riga 29 della sezione 20.
- [ ] **Step 2: Catalogo.** 1.6 e 2.1, riga `ai`: `rules-ai` precaricata dagli agenti, nessuna skill nel frammento, `claude-api` in «Dove informarsi» (decisione 9); 1.7: le pagine ufficiali come fonte di fatti; sezione 2: i percorsi concreti e il rilevamento per contenuto; sezione 4: le fonti vere di `rules-ai`, con i fornitori del progetto 9; una nota per B4 e B6: `globs` non espande le graffe `{a,b}`, i percorsi del catalogo che le usano vanno scritti in più righe.
- [ ] **Step 3: Piano principale di B e progetto.** Stato in testa; riga B3 della sezione 2; sezione 3, riga B3→B4-B7 con i nomi reali (frammento, `fragments`, `area_rules`, `tomlout`, `init.profile_blocks`, `git.tree_sizes_at`, `git.grep_files_at`, agenti derivati con il test di deriva, elenchi di sola lettura); sezione 9: chiusi i rinvii 175, 178, 180-187 che B3 ha fatto, aperti quelli rimasti, il rinvio a B3-bis sulla forma del punto unico (decisione 15), più le righe «minor (deferred)» che riguardano B3-bis e B4-B7; una sezione «Prove di B3» con ogni riga della tabella «Copertura» e il test o l'evidenza che la prova. Nel progetto la riga di avanzamento: «B1, B2 e B3 eseguite».
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md
git commit -m "tollgate B3: prove, spec rev 29, piano principale di B, catalogo"
```

---

## Copertura: punti del progetto e del piano principale destinati a B3 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: primo gruppo di profili, `ai` | 5, 6, 7, 8 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `ai` | 5 (sezione «Dove informarsi»), 6 |
| Progetto 2, obiettivo 5: implementatore e revisore per area | 8 |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 6, 7; decisione 17 |
| Progetto 2, anti-obiettivo «fonti inventate» | 6 (verificatore di sola lettura), decisione 13 |
| Progetto 3.4, riga `ai` | 5 (R-AI-02, R-AI-05) |
| Progetto 3.6: codice AI fuori da `**/ai/**` | 4 (decisione 6); R-BASE-04 resta |
| Progetto 4, riga `ai`: L1, Gemini e gli altri fornitori dell'utente | 5 (frammento, «Dove informarsi»); decisioni 9, 13; progetto 9 (OpenAI, OpenRouter, Agno) |
| Progetto 5: fonte per regola, verifica, pagina, solo regole approvate | 5, 6, 7; decisioni 4, 17 |
| Progetto 9: regole sui modelli che cambiano, modelli stabili | 5 (`test_user_choices_covered`, R-AI-03) |
| Progetto 9: sentinella dei modelli | **B3-bis** (fuori da questo piano); decisione 15 |
| Piano principale, sezione 2, riga B3: frammenti, `init`, `rules-ai`, agenti, percorsi, `dod` | 2, 3, 4, 5, 8; decisione 14 |
| Piano principale, sezione 3, B1→B3-B7: strumenti, paragrafo sulla nota | 8 (decisione 10, test di deriva) |
| Piano principale, sezione 3, B2→B3-B7: forma della regola, precaricamento o brief | 5; decisione 9 |
| Piano principale, sezione 3, B3→B4-B7: frammenti, `init`, agenti derivati | 2, 3, 4, 8; nomi reali nel Task 11 |
| Piano principale, sezione 9: rinvii 175 (test di deriva), 178 (agenti nuovi con `rules-base`), 180 (radice esplicita), 181 (precaricamento), 182 (test di pagina), 183 (regole sul visibile), 184-187 | 8; 8; Global Constraints; 9-10; 6; 5 e 8; 1 |
| Revisione della spec del nucleo | 11 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B (con la sezione 9), il piano principale, la spec rev 28, il catalogo, il codice di `main` e il modello di B2.

| Giro | Rilievi | Esito |
|---|---|---|
| 3 | N-1, N-2 chiusi; M-1..M-12 chiusi salvo M-2 e M-5 in parte; 7 minor nuovi (R3-1 negazioni e `match_any`; R3-2 chiave della protezione nel gh finto; R3-3 pattern di altra forma; R3-4 tetto di tempo di `git grep`; R3-5 test dei marcatori contro B3-bis; R3-6 righe in forma TOML e `agent = ""`; R3-7 cartella della proposta) | **«Pronto». Critical aperti: 0. Important aperti: 0.** Corretti comunque tutti i minor nuovi e la riga dei rinvii della Copertura |
| 2 | I-1…I-7, I-9, I-10 chiusi, I-8 in parte; 17 minor chiusi, 4 in parte; 2 important nuovi (N-1 un profilo già copiato non riceve mai i percorsi nuovi; N-2 i file di tollgate in `.github/tollgate/` entrano nel rilevamento e il test di protezione non guarda l'albero installato), 12 minor (M-1..M-12) | «Non pronto». Corretti: decisioni 5, 6, 7 (esclusioni con una sola costante, tutti i pattern in percorsi concreti, annidamenti, righe per percorsi e agenti dei profili dichiarati); Task 3, 4, 6, 8, 9 (test nuovi e rinominati, `git grep -z`, ordine di `prepara`); R-AI-01, 02, 03; eccezione per i test `test_rules_*.py` |
| 1 | 0 critical; 10 important (I-1 `ls_files_at` con pathspec vuoto; I-2 nessun modo di dare a `propose` un plugin temporaneo; I-3 `[blocca]` sulla nota insoddisfacibili senza passo; I-4 R-AI-03 non giudicabile; I-5 `**/agents/**` su `.claude/agents/`; I-6 marcatori con falsi positivi e negativi; I-7 regole del progetto ferme dopo un aggiornamento; I-8 `prepara` del Task 8 non fattibile così; I-9 altri fornitori dell'utente; I-10 test esistente rovesciato senza dirlo); 21 minor | «Non pronto». Due scelte portate all'utente (fornitori: OpenAI, OpenRouter, Agno; solo modelli stabili), scritte nel progetto 9. Corretti: decisioni 2, 5-9, 11-13, 15-17 nuove o riscritte; Task 1, 3, 4 (nuovo), 5, 6, 8, 9 (nuovo), 10; Review Focus; mappa dei file |
