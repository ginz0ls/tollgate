# Ri-revisione 1 del giro di correzione della revisione finale B5 (80e9f47..8cae7d2)

Letti: regole, final-review.md, ruling, report, diff (commit 8cae7d2) e `init.py:360-385`. Eseguiti solo test mirati: `tests.test_init.ProfileBlocksTest`, `tests.test_bash`, `tests.test_rules_backend`, `tests.test_manifest` (248 test, OK, 3 saltati).

### Verdetti sui rilievi

**I-1: un percorso di `backend` annidato in una cartella di `ai` vince su `ai` anche per file riconosciuti per contenuto.** INDIRIZZATO. `bin/tollgate_flow/init.py:370-377`: in `lighting` entra un file solo se è in `detected[area]` o non è in `detected` di nessun altro frammento. Verificato sul codice e sui test (`tests/test_init.py`, ProfileBlocksTest):
- file rilevato da `y` non accende `x` (per `lighting`, `paths` e righe di avviso), anche nella deriva (`test_path_only_light_skipped_in_drift_too`);
- trovato da tutti e due: resta in tutti e due (`test_file_found_by_content_in_both_profiles_stays_in_both`, e il codice lo dà per costruzione: `f in mine`);
- senza marcatore: proposta invariata (`test_path_only_light_kept_without_the_marker`);
- frammenti veri: `src/ai/routes/chat.ts` resta ad `ai`, `backend` non proposto; senza `detected` `backend` ha ancora `src/ai/routes/**` (`test_real_content_match_of_ai_keeps_nested_routes_out_of_backend`).
Controlli richiesti: nessun test di B3, B4, B5 su `profile_blocks` o sulle sovrapposizioni è stato toccato (il diff di `tests/test_init.py` è solo di aggiunte); con `detected` vuoto o `None` `taken` è vuoto e la condizione è sempre vera, quindi la proposta del progetto di prova (nessun file assegnato ad altri profili, come dice il ruling) e quelle di B1-B4 non cambiano; nessun marcatore aggiunto in `bin/` (il diff di `bin/` ha solo `init.py` e `bash.py`, senza stringhe di marcatori). Il limite (file senza marcatore; `infra/handlers/`) è scritto in spec 11.2, 11.4, riga 32 della sezione 20 e piano principale, sezione 9.

**M-1: `_flag_present` legge anche i token dopo `--`.** INDIRIZZATO. `bin/tollgate_analysis/bash.py:1166-1168` ferma la scansione al primo `--`; test: `wrangler kv key put K -- --local` fermato, `wrangler d1 execute DB --remote -- --local` fermato, `wrangler kv key put K V --local -- x` libero (`tests/test_bash.py`). Spec 8.5 allineata. Il ripiego `text_effect` è sul lato sicuro e non cambia.

**M-2: `implementer-backend.md` non nomina `d1 time-travel restore`.** INDIRIZZATO. `agents/implementer-backend.md:53` lo nomina; `tests.test_manifest` verde.

### Triage «da correggere»
- **7** (test mancanti per `pnpm -w release`, `npm run-script deploy`, `-C`/`--dir`/`--prefix`, `yarn workspace deploy build`): INDIRIZZATO, aggiunti a `test_script_name` e `test_monorepo_deploy_scripts` (`tests/test_bash.py:323-328, 344-354`), sia casi fermati sia liberi.
- **13** (`USER_CHOICES` solo R-BACKEND-01): INDIRIZZATO, aggiunti R-BACKEND-02 e R-BACKEND-12 (`tests/test_rules_backend.py:33-39`); il test `test_user_choices_covered` passa.
- **14** (`if any` tautologico): INDIRIZZATO, righe tolte.
- **16** (`sources_main` inutilizzato): INDIRIZZATO, metodo tolto.
- **22** (`psql` tra i non coperti): INDIRIZZATO, ora `mysql`/`mongosh` con «che Tollgate non conosce».
- **23** (`kv namespace`/`r2 bucket` sempre fermati): INDIRIZZATO, «salvo le letture `list`, `get` e `info`».
- **28** e **29** (riga 58 del rapporto): INDIRIZZATO, la frase ora dice che il prompt dell'Agent (riga 208) è il percorso di `review-1.md`, il testo sta nel `Read` (riga 225) e vi compare solo `R-BASE-05`.
- **33** (due parentesi in 8.5): INDIRIZZATO, unite in una (il punto e virgola tiene insieme la frase).

### Danni nuovi nel diff della correzione
Nessuno Critical o Important. Minor:
- **Minor, spec 11.2/11.4 e piano principale sez. 9 (limite di I-1):** il limite è scritto come «file senza righe da AI». Resta scoperto anche il caso misto: `src/ai/routes/chat.ts` (con marcatore) accanto a `src/ai/routes/plain.ts` (senza). `plain.ts` accende `src/ai/routes/**` per `backend`, che per specificità vince anche su `chat.ts`, che va a `backend` nonostante il marcatore. Il costo è dello stesso tipo di quello già scritto, ma la formulazione lo lascia fuori. Suggerimento: una mezza frase («anche un file con righe da AI, se accanto ce n'è uno senza»), non blocca.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important (un Minor sulla formulazione del limite di I-1).
