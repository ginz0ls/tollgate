# Revisione Task 8 (c71ab80): documenti

Base 56215cf, pacchetto `review-56215cf..c71ab80.diff`. Solo documenti (4 file, +69/-15). Fatti confrontati con ledger, report della prova reale e codice del ramo con controlli mirati.

### Aderenza

- ✅ Spec rev 28, 6.3: `rules-base` skill comune, precaricata con `skills: [rules-base]` dai quattro agenti (verificato: `agents/{implementer,task-reviewer,final-reviewer,finding-verifier}.md:5`), fuori dal tetto, dal brief e da `skills_required`; avviso in L0 che nomina `tollgate:rules-base`; agenti per area dei rinvii (D15).
- ✅ 8.1: data 2026-11-01 (skill:5); `no`, `off`, `n`, `false` anche tra apici, `0` e `none` accendono (`research.py:37,56-60`, apici tolti prima del confronto); file assente spento in silenzio, altro `OSError` spento con traccia (`lookups.py:170-180`); `rules_enforced` = `rules_switch(root)[0]` (`lookups.py:195-197`); evento una volta «per piano» (`research_gate.py:148`, `work_events` dopo l'ultimo `plan_reset`, D11); `_UNREADABLE` anteposto solo a `pre_*` quando c'è l'avviso normale (`research_gate.py:141-145`); motivazione «registro degli eventi (`tollgate events`)», non `stats` (D10; comando `events` esiste in `bin/tollgate_core/cli.py:84`).
- ✅ 8.6: difetto della nota segnalato una volta sola (D3: caso nota non utilizzabile e caso difetto di contenuto); task senza modifiche con nota mancante o non valida (decisione 6); distinzione `[blocca]` meccanica anche per le R-BASE (`lookups.base_rules`, usata da `task_verdict.py:54` e `apply.py:84`; spenta nessuna blocca; skill illeggibile: fail-closed, `lookups.py:183-192`).
- ✅ 12.2: approvazione avvenuta il 01/11/2026. 16: riga della prova reale (5 `read`, 1 `bash_read`, 1 `fetch`, prima nota non valida poi valida, nessun veto, 0,92 USD, token 49.015/30.531) coerente con ledger e rapporto; rifiuto dal vivo non visto, prova deterministica (`test_real_rules_base_blocks_l1/l2`); precaricamento visto nelle trascrizioni (`isMeta` iniziale), non nello stream-json. «Nessun `research_reminder`» e «`R-BASE-06` come conferma» sono nel rapporto (righe 39, 43). 18.4: `research_switch_unreadable` {`error`} con il percorso assoluto. Riga 28 della sezione 20: decisioni 1-13 e ruling D3, D5, D6, D10, D11 e giro 1 del Task 6.
- ✅ Catalogo: sezione 1 (skill comune, precaricata) e riga della sezione 4. Le fonti elencate sono quelle vere della skill finale (`context-engineering`, `source-driven-development`, `verification-before-completion`, correzioni dell'utente); `systematic-debugging` non c'è più perché la fonte della R-BASE-10 è cambiata dopo la verifica: la riga è corretta, la decisione 1 dice «quattro» ma il fatto vince.
- ✅ Piano principale: stato (3218, ramo, merge in attesa dell'OK), riga B2, sezione 3 coi nomi reali (verificati: `research.base_rules`, `lookups.base_rules`, `rules_switch`, titolo, sezioni, `test_manifest`, `test_taskcmd`), sezione 5 con `PYTHONWARNINGS=error::ResourceWarning`, sezione 9 con i rinvii (D15, D16, minori di B2), sezione 10 con tutte le 20 righe di Copertura più le prove oltre la tabella. Ho controllato con grep che ognuno dei ~40 nomi di test citati esista: tutti presenti. Valori delle regole: `[blocca]` su 01-06, 09, 10 (R-BASE-01, 03, 06, 09 citati correttamente).
- ✅ Progetto di B: «B1 e B2 eseguite».
- ✅ Riservatezza: nessun percorso `/home/...`, nome utente, nome dell'host o progetto privato nel diff.
- ⚠️ Non verificate dal codice: i numeri dei token e dei costi della prova reale (affidati al rapporto), il testo delle trascrizioni (evidenze fuori diff).

### Punti di forza

Le sezioni dicono onestamente cosa non è provato (rifiuto dal vivo, giudizio del revisore sul diff, due test fragili, `_UNREADABLE` senza test di ordine). La sezione 10 è una tabella 1:1 con la Copertura, con i limiti dichiarati per riga. I rinvii a B3 sono operativi (copiare l'agente non basta, test di pagina, dove cercare le trascrizioni).

### Rilievi

**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md` sezione 10, riga rinvio 31: «Gli ultimi tre usano una radice con una cartella al posto di `SKILL.md`». Non è vero per `test_missing_switch_no_unreadable_event`, che toglie la cartella (`tests/test_check_research_gate.py:324-329`) per provare il file assente. Correggere in «i primi due».
2. Piano principale, sezione 3 riga B2→B3-B7: «se `rules-<area>` si precarichi nello stesso modo o resti nel brief» è grammaticalmente rotto («se si precarichi»): scrivere «se `rules-<area>` si precarica...».
3. Spec rev 28 riga 28 e sezione 10 («la n. 11 tolta»): la skill finale ha una R-BASE-11; la «n. 11» è della bozza (tolta dalla verifica delle fonti), un lettore la scambia con la regola vera. Scrivere «la bozza n. 11 tolta».
4. Sezione 9 non porta alcuni minori deferred del ledger: `s3_the_veto_does_not_depend_on_the_starting_folder` senza `PREP` (Task 2), `"null"`, `"~"`, `"|"` tra apici senza test (Task 1), in `prepara` il controllo dell'interruttore dopo `rot`/`mkdir "$OUT"` (Task 7). Non riguardano B3 e oltre in modo stretto e restano nel ledger per il triage finale: segnalati per completezza.

### Valutazione

**Qualità del task:** Approvato.
**Motivo:** i documenti corrispondono a ledger, rapporto della prova reale e codice del ramo su tutti i punti richiesti, con i limiti dichiarati e la copertura completa; restano tre ritocchi di testo, nessuno sostanziale.
