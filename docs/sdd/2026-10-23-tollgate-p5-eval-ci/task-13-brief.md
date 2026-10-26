### Task 13: Prova reale su detect: azioni fissate, rivalutazione, sentinella, cache (controller)

Il controller esegue in prima persona; un implementatore sonnet scrive lo script **senza rete** (modi vietati a ogni giro: tutti tranne `bash -n` e `controlla`).

**Files:**
- Create: `spikes/run-p5-gate.sh`, `tests/test_p5_scripts.py` (parte del Task 13), `docs/verifiche/2026-10-23-p5-prova-gate.md`
- Usa: `spikes/gh-p4/ghguard.py` con il profilo `p5` (Task 1)

- [ ] **Step 1 (implementatore): `spikes/run-p5-gate.sh`** con i modi `controlla`, `aggiorna` (nel clone di detect: `bin/tollgate init --update`, ramo `tollgate-config/0.2.0` con i soli file proposti, PR, attesa di `guard` e `verdict`, merge; procedura 9.4), `pin-on` e `pin-off` (`PUT actions/permissions` con `sha_pinning_required` acceso, poi il valore letto all'inizio), `caso <nome>`, `raccogli`. Casi: `pulita-fissata` (PR pulita con `sha_pinning_required` acceso: `guard`, `verdict`, `attention` `success`; nel log del job `verdict` «Cache mode: read», VG1); `rifiuto-v4` (ramo con un workflow a `@v4` e il fissaggio acceso: run rifiutato); `rivalutazione` (PR verde, PATCH del corpo → `tollgate/verdict` `pending`, poi `success`; registra l'ordine reale, decisione 15); `skip-ci` (dopo un push controllato che lascia il segnale `success`, un push diretto su `main` con `[skip ci]` nel messaggio, poi un push normale: la sentinella segnala il commit saltato, si ferma al segnale e commenta l'unica issue; i vecchi `failure` di P4 su detect non bastano a farlo passare, perché il segnale cercato è il più recente). Test in `tests/test_p5_scripts.py` (`controlla` con `gh` finto: elenco dei casi e dei comandi; ogni comando passa da `ghguard.py check` con il profilo `p5`).
- [ ] **Step 2 (controller):** `aggiorna`, `pin-on`, i quattro casi, `pin-off`, `raccogli`. Ogni tentativo registrato con l'esito; un caso riuscito dopo tentativi falliti è «composito».
- [ ] **Step 3: Rapporto** `2026-10-23-p5-prova-gate.md`: per caso PR, SHA, stati con autore, atteso e ottenuto, minuti; procedura di aggiornamento eseguita; stato finale di detect (`sha_pinning_required` com'era all'inizio, issue di sentinella chiusa dal controller, nessuna PR aperta).
- [ ] **Step 4: Commit** «tollgate P5: prova reale su detect (azioni fissate, rivalutazione, skip ci, cache sul privato)».

---

