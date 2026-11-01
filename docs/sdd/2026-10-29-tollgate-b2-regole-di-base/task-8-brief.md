### Task 8: Prove, revisione 28 della spec, piano principale, catalogo

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 28), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (riga di avanzamento in testa), `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md` (sezioni 1 e 4)

- [ ] **Step 1: Revisione 28 della spec del nucleo.** 6.3 (le skill comuni comprendono `rules-base`, precaricata con `skills:` dai quattro agenti della decisione 2, fuori dal tetto e fuori da `skills_required`; l'avviso la nomina); 8.1, «Interruttore del blocco» (data dell'approvazione; `no`, `off`, `n`, `false`, anche tra apici; file illeggibile con avviso ed evento, decisione 5, con il motivo per cui è un evento e non una riga di `hooks.log`); 8.6 (task senza modifiche, decisione 6; un difetto della nota si segnala una volta sola, decisione 8); 12.2 (la riga «Lavori in corso all'approvazione di `rules-base`»: l'approvazione è avvenuta, con la data); 16 («ancora da verificare dopo B1»: il rifiuto sulla `rules-base` vera, con l'esito del Task 7; il precaricamento visto o no); 18.4 (evento `research_switch_unreadable`); riga 28 della sezione 20.
- [ ] **Step 2: Catalogo.** Sezione 1, «Skill comuni»: `rules-base` per ogni implementatore e revisore, precaricata. Sezione 4: una riga `rules-base` con le fonti della decisione 1.
- [ ] **Step 3: Piano principale di B e progetto.** Stato in testa (B2 sul ramo, merge in attesa dell'OK dell'utente; numero di test); riga B2 della sezione 2; sezione 3 con i nomi reali di B2 (forma di una regola, approvazione, caricamento); sezione 5 con `PYTHONWARNINGS=error::ResourceWarning` al posto di `-W`; una sezione «Prove di B2» con ogni riga della tabella «Copertura» di questo piano e il test o l'evidenza che la prova; rinvii a B3 e oltre (righe «minor (deferred)» che li riguardano). Nel progetto di B la riga di avanzamento in testa: «B1 e B2 eseguite».
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md
git commit -m "tollgate B2: prove, spec rev 28, piano principale di B, catalogo"
```

---

## Copertura: punti del progetto e del piano principale destinati a B2 → task

| Punto | Task |
|---|---|
| Progetto 2, obiettivo 3: primo gruppo di profili, `base` | 3, 4, 5 |
| Progetto 2, obiettivo 4: «Dove informarsi» per `base` | 3 (sezione «Prima di scrivere») |
| Progetto 2, anti-obiettivo «frase vuota senza lettura registrata» | B1 (controllo 3.3); 3 (R-BASE-01, 03, 06 sulla nota) |
| Progetto 2, anti-obiettivo «regole mai lette da una persona» | 4 (pagina), 5 (approvazione), decisione 13 |
| Progetto 2, anti-obiettivo «fonti inventate» nelle regole | 4 (verificatore di sola lettura, esito per fonte) |
| Progetto 2, anti-obiettivo «passo troppo pesante» | 3 (R-BASE-09); L0 solo avviso, invariato |
| Progetto 3.1: blocco in L1 e L2 | 5 (`test_real_rules_base_blocks_l1`, `…_l2`), 7 |
| Progetto 3.4, riga `base` | 3 (R-BASE-01, 02, 05) |
| Progetto 3.6: nomi dei modelli in `rules-base` | 3 (R-BASE-04, `test_model_name_rule`) |
| Progetto 4, riga `base`: caricata da ogni implementatore e revisore, anche generici | 6 (decisione 2) |
| Progetto 5, punti 1-4: fonte per regola, verifica, pagina, solo regole approvate | 3, 4, 5; decisione 13 |
| Progetto 5, «la prima pagina da rivedere è `base`»; blocco spento fino all'approvazione | 5 |
| Progetto 6: come `rules-base` arriva agli agenti | 6 (decisioni 2 e 3) |
| Progetto 8: lavori iniziati prima di B | invariato (B1, `work_items.research`) |
| Piano principale, sezione 9: lavori in corso all'approvazione | 4 (pagina), 8 (spec 12.2) |
| Piano principale, sezione 9: rinvio 13 | 1 (`test_enforced_refuses_no_off_n`) |
| Piano principale, sezione 9: rinvio 31 | 1 (`test_switch_*`, `test_unreadable_switch_*`) |
| Piano principale, sezione 3, B2→B3-B7: forma di una regola, pagina, rapporto delle fonti | 3, 4; nomi reali nel Task 8 |
| Minori di B1 che il blocco acceso rende reali: task senza modifiche; copia con `git ls-files` | 1; 7 |
| Revisione della spec del nucleo | 8 |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il progetto di B, il piano principale, la spec rev 27, il catalogo, il codice di `main` e il modello di B1.

| Giro | Rilievi | Esito |
|---|---|---|
| 1 | 1 critical (C-1: con l'approvazione rinviata la bozza, già caricata dagli agenti, sarebbe finita su `main`), 6 important (I-1 due test esistenti rotti dalla bozza; I-2 tipo di evento fuori da `EVENT_TYPES`; I-3 test in sottoprocesso e prove a secco degli eval senza strada; I-4 nessuna radice sorgente finta per i test dello script; I-5 regole non verificabili e doppi rilievi sulla nota; I-6 fonti che non dicono ciò che la regola attribuisce), 17 minor | «Non pronto». Corretti: ordine dei task (caricamento dopo l'approvazione), decisioni 2, 4, 5, 7-9, 12, 13 nuova; tabella delle regole; Task 1-8 |
| 2 | Tutti i 24 rilievi del giro 1 chiusi; 2 important nuovi (I-N1 R-BASE-01 impossibile per i file creati dal task; I-N2 R-BASE-06 che prende anche gli URL del codice), 4 minor (M-N1..M-N4) | «Non pronto». Corretti tutti prima del giro 3 |
| 3 | I-N1, I-N2 e M-N1..M-N4 chiusi; nessun rilievo nuovo | **«Pronto». Critical aperti: 0. Important aperti: 0.** |
