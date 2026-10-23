# Ri-revisione Task 6, giro di correzione 1 (e51939f)

Prove mirate: `tests.test_gate_comment`, `tests.test_prbody` (30 OK), `DiffTest.test_untrusted_ids_stay_in_data_not_text` (OK); script a parte con una voce da 100.000 caratteri di `@`, `<` e backtick in `text`, `data` ed `errors` (resta entro `MAX_BODY`, marcatore in testa) e guardia con 50 problemi da 3.000 `@`.

### Verdetti sui rilievi
- **I-1 testo non fidato in `Item.text`**: INDIRIZZATO. `evaluate.py:433-436` manda la parte dopo «: » del dettaglio (ids di test, soglie) e il path in `data`; `text` resta la frase fissa. I due soli dettagli con «: » (`testguard.py:188` e `:240`) hanno la parte letta dopo il primo «: ». Gli altri `Item(` interpolano solo contatori, nomi di comando e id di deroga (`^w-\d+-\d+$`, `waivers.py:12`). Difesa in profondità `comment._one_line` (`comment.py:36-40`): una riga, `<` come `&lt;`, backtick da 3 in su resi apostrofi, `defuse`, tetto. Test: `test_untrusted_ids_stay_in_data_not_text` e `test_hostile_item_text_is_one_line_and_inert` (recinto, `</details>`, `@`, `-->`, `<!--`, `--!>`).
- **I-2 tetto con voce enorme**: INDIRIZZATO. `_fit` (`comment.py:73-86`) ha `last_resort` e `render` ne fornisce uno minimo con marcatore (`:91-95`); `prbody.render` chiude con un ultimo taglio (nota, blocco JSON intero e ultimo; `prbody.py` ultima riga). `_one_line` applica il tetto. Test: `test_single_huge_entry_stays_under_cap` (sei casi, `len <= MAX_BODY`, marcatore in testa), `test_many_groups_under_cap`, `test_single_huge_entry_stays_under_cap_and_keeps_block` (`prblock.parse` trova il blocco, il corpo termina con `-->`). La lunghezza è misurata sul testo finale, quindi l'espansione di `defuse` non rompe il tetto.
- **I-3 `render_guard` senza tetto**: INDIRIZZATO. `_guard_build` e `render_guard` passano da `_fit` (`comment.py:98-113`), con nota «troncato». Test `test_guard_total_cap` (50 da 2.000, 1.000 da 5.000, una da 100.000).
- **I-4 marcatori senza `sha=`**: INDIRIZZATO. `marker`, `_MARKER` e `_guard_build` scrivono `sha=<40 hex>`; `marker_sha` rifiuta la forma senza `sha=` (test `test_marker_sha_rejects_bad`), `MARKER_PREFIX` resta uguale a `fixtask.GATE_MARKER`.
- **Minori**: `defuse` spegne `--!>` (test); `prbody.cap` e `prbody.CAPS` pubblici, nessun residuo di `_cap` o `_CAPS` nel repo (grep), `comment` importa `prbody.CAPS`; casi limite coperti dai test sopra.

### Danni nuovi nel diff della correzione
Nessuno. Colori e chiavi delle voci di `evaluate.diff` invariati: `_red(ev, v.kind, ...)` non cambia, cambia solo la ripartizione `text`/`data`. Per le violazioni senza «: » `data` resta il solo path come prima.
Annotazioni Minor non bloccanti:
- Gli ultimi tagli (`last_resort` di `comment`/`prbody`, `minimal` della guardia) non sono raggiunti da nessun test: con la scala fino a 30 e `keep=1` il corpo entra sempre. Sono corretti per costruzione.
- `_one_line` non spegne link o immagini Markdown nel `text`: oggi `text` porta solo nomi di comando e id validati, quindi non è sfruttabile.

### Osservazioni fuori ambito
- `waivers._ID` usa `$` con `match`: accetta un `\n` finale nell'id (`w-1-2\n`). Innocuo qui perché `_one_line` riduce a una riga.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
