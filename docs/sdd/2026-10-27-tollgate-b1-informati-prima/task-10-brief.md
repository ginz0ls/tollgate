### Task 10: Prove, revisione 27 della spec, piano principale di B

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 27), `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md` (solo una riga di stato in testa: «B1 eseguita, vedi piano principale di B»)

- [ ] **Step 1: Prove.** Nel piano principale di B una tabella «Prove di B1»: ogni riga della tabella «Copertura» qui sotto con il test o l'evidenza che la prova; un punto senza prova si scrive così, con il motivo.
- [ ] **Step 2: Revisione 27 della spec del nucleo** (decisione 17): 3.2 (evento `post_lookup`); 7.1 (uscita anticipata di `hooks/run`); 7.2 (righe `PostToolUse` delle letture e `PreToolUse` della nota); 8.1 (la nota come ricevuta delle letture: «non si crede a quello che l'agente dice»); 8.5 (strumenti MCP di documentazione); 8.6 (pertinenza della nota dal revisore del task); 11.4 (`[components] research_note`); 12.2 (migrazione 6); 16 (esiti del Task 1 e della prova del Task 9); 18.4 (eventi `research_note` e `research_reminder`); riga 27 della sezione 20.
- [ ] **Step 3: Piano principale di B:** stato in testa (B1 chiusa sul ramo, merge in attesa dell'OK dell'utente, numero di test), riga B1 della sezione 2, sezione 3 con i nomi reali di B1, rinvii a B2 e oltre (righe «minor (deferred)» che riguardano le fette successive).
- [ ] **Step 4: Suite completa e commit.** `tests/run` e `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .` verdi, nessun «unclosed database».

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md
git commit -m "tollgate B1: prove, spec rev 27, piano principale di B"
```

---

## Copertura: punti del progetto destinati a B1 → task

| Punto del progetto | Task |
|---|---|
| 1, causa tecnica: implementatore senza `WebFetch`, `WebSearch`, context7 | 5 |
| 2, obiettivo 1: passo comune prima di modificare file | 4, 6, 7, 8 |
| 2, obiettivo 2: controllo delle fonti sulle letture registrate | 2, 3, 4, 6 |
| 2, anti-obiettivo «frase vuota senza lettura registrata» | 3 (`check_note`), 6, 7 |
| 2, obiettivi 3 e 5 (primo gruppo di profili, agenti per area) | **B2-B7** (piano principale di B, sezione 4) |
| 2, anti-obiettivo «passo troppo pesante»: L0 solo avviso, una volta per lavoro; permessi di `WebFetch` | 7 (`test_l0_warns_once`); 5 (decisione 18) |
| 2, anti-obiettivo «regole mai lette da una persona» | **B2-B7** (pagine approvate) |
| 2, anti-obiettivo «fonti inventate» nella nota | 3 (`test_check_note_source_not_read`), 6 |
| 3.1 L0 avvisa, L1 e L2 bloccano; L0 che cresce | 7; interruttore: decisione 8 (accensione in B2) |
| 3.2 contenuto della nota, «nessuna fonte esterna» con motivo | 3, 6, 8 (revisore) |
| 3.3 punti 1-4 | 3 (`check_note`), 4 (letture), 6 |
| 3.3 pertinenza dal revisore del task | 8 |
| 3.4 «Dove informarsi» | **B2-B7**: sono le regole dei profili; B1 consegna il formato delle fonti (decisione 2) |
| 3.5 strumenti, pagine come dati non fidati | 5 |
| 3.5 le tre verifiche e i ripieghi | 1 (Step 2 e 4); conseguenze nei Task 3-7 |
| 3.5 context7 assente → solo `WebFetch` | 1 (Step 4), 5 |
| 3.6 giri di correzione, nota del task; `reopen plan` | 2 (`for_task`, `reset_plan`), 6, 7, 8 |
| 3.6 L0 senza task: un avviso per lavoro | 7 |
| 3.6 nomi dei modelli in `rules-base` | **B2** (è una regola) |
| 4 i profili; `base` caricata da ogni agente | **B2-B7** |
| 5 regole approvate; il blocco acceso dopo `rules-base` | interruttore nel Task 3 e 7 (decisione 8); approvazione in **B2** |
| 6 dove sta la nota e in che formato | decisioni 1, 2; Task 3, 6 |
| 6 come gli hook registrano le letture | decisioni 4, 5, 15; Task 2, 4 |
| 6 normalizzazione degli URL, libreria e context7 | decisione 4; Task 3 |
| 6 come `rules-base` arriva agli agenti | **B2** |
| 6 testo dell'avviso e del rifiuto | Task 7 |
| 6 ordine e dimensione delle fette | piano principale di B |
| 6 revisione della spec del nucleo | 10 |
| 7 test della suite (quattro casi) | 7 (`test_l1_without_note_denied_when_enforced`, `test_l0_warns_once`, `test_invalid_note_denied_with_problems`, `test_valid_note_passes`) e 3 |
| 7 prova reale L1 | 9 |
| 7 eval minimi | **B8** |
| 8 vincoli del nucleo | Global Constraints |
| 8 lavori iniziati prima di B; deroga per `adopt` | 2, 6, 7 (decisione 10) |

## Revisione del piano

Revisore: opus, a contesto pulito, in sola lettura, contro il brief di scrittura, il progetto di B, la spec rev 26, il codice di `main` e il modello di P5.

| Giro | Rilievi | Esito |
|---|---|---|
| 1 | 1 critical (C-1: in `claude -p` `WebFetch`, `WebSearch` e MCP non concessi falserebbero sonda e prova reale), 7 important (I-1 revisore che blocca con l'interruttore spento; I-2 letture del vecchio task dopo `reopen plan`; I-3 latenza misurata su un percorso che oggi non esiste e senza soglia; I-4 piano della prova non registrato; I-5 atteso della prova che dipende da una scelta del modello; I-6 campo `approved` non provato contro `validate --strict`; I-7 permessi di `WebFetch` nelle sessioni vere), 17 minor | «Non pronto». Corretti: decisioni 1, 4, 8, 10-16, 18 nuova; Task 1-9 |
| 2 | Tutti i 25 rilievi del giro 1 chiusi; 4 minor nuovi (M-n1 `file` del rilievo con la nota mancante; M-n2 seconda misura senza conseguenza; M-n3 B1-V7 nello scan pre-flight; M-n4 test del modo `valida`) | **«Pronto». Critical aperti: 0. Important aperti: 0.** M-n1..M-n4 corretti prima del commit |
| 3 | M-n1..M-n4 chiusi; 1 minor nuovo (M-n5: manca nel brief del revisore il campo con il primo file del diff) | **«Pronto». Critical aperti: 0. Important aperti: 0.** M-n5 corretto (`ReviewBrief.first_diff_file`) |
