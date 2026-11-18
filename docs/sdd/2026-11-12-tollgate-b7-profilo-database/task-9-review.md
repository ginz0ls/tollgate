# Revisione del Task 9 (30e9f6b..db2af0e)

Solo lettura. Ho letto regole, brief, ledger, report e pacchetto. Non ho rilanciato la suite. Il pacchetto ha righe molto lunghe: ho letto ogni sezione toccata, tagliando le righe a lunghezza fissa solo per le tabelle larghe.

## Aderenza

- ✅ **Quattro file toccati, nessun altro.** `git diff --name-only 30e9f6b..db2af0e` dà solo piano principale, spec del nucleo, catalogo e progetto di B. Nessuna pagina, skill o frammento approvato è toccato (`docs/profili/*.md`, `skills/rules-*`, `templates/profiles/*.toml`, `docs/profili/verifiche/*`).
- ✅ **Sezioni della spec dello Step 1, tutte toccate:** intestazione (rev 34); 4 (riga «Specialista finale»); 6.3 (diagramma, giro di correzione, agenti e specialista, `.sql` sotto un'altra cartella che alza a L2 tramite il profilo attivo, P14, tabella Q1-Q47); 7.1 e 7.3 (di più, ma coerenti: `reviewer-database` e `final-database` nei `READONLY_TYPES`); 8.5 (tabella delle liste di Supabase, `REMOTE_FLAGS`, opzioni globali, ripiego testuale, lanciatori, Prisma e Drizzle, scelta del 12 novembre, costo di `--local` deprecato, CLI 2, limiti); 8.7 (`dod` vuoto con l'esempio `db_reset` e `db_test`, senza opzioni remote); 10 (specialista e «Lista di controllo dell'area» nel brief); 11.2 (rilevamento per contenuto, nessun `exclude`, `final_specialist` solo con l'agente presente, limite D12); 11.4 (`readonly_agents`, commento di `checklist`, frammento di `database`, `exclude`); 16 («Verificato in B7», con date); riga 34 della sezione 20.
- ✅ **Correzione del prodotto in 6.3:** il bullet «Giro di correzione in una sessione nuova» (nucleo, riga 496) dice causa («not reachable», `Agent` negato dalla regola `writer`), fix (`agents.decide`, `_relaunchable`, `_subagent_start`), commit `2d1441c`, costo e test (`RelaunchInNewSessionTest`, sette test). Il diagramma rimanda al bullet.
- ✅ **D11:** nucleo riga 1351, `checklist = "" # una frase per la lista di controllo del revisore finale (10)`. Prima era «percorso di un file con la checklist» (1269 di 30e9f6b). Non resta altra occorrenza del commento vecchio.
- ✅ **D4:** la tabella dei comandi di Supabase è in 8.5, con la nota che `docs/uso/comandi.md` non ha una sezione sugli effetti esterni.
- ✅ **D12:** limite in 11.2, rinvio a B8 nel blocco «A B8, da B7» del piano principale.
- ✅ **D13, Prisma 8, CLI 2:** costi in 8.5 e nel blocco «Prisma, Drizzle e la CLI di Supabase» del piano principale.
- ✅ **Ledger, campione molto oltre dieci voci, tutte trovate sul diff.** Confronto fatto sulla tabella del report contro `grep Ruling:` di `progress.md` (tutte le righe presenti, nessuna mancante). Verificate sul diff:
  - D1 e D2: 8.5, «Opzioni globali» e «Dietro un lanciatore».
  - D5 e D6: 8.5, «Costi del permesso».
  - D7: 8.5, «Il ripiego testuale».
  - D8: piano principale, sezione 3 (riga B7→B8) e test del caso `backend` in sezione 16.
  - D9: spec 16 (riga della prova reale) e sezione 16 del piano.
  - D10: spec 11.2 e rinvio chiuso nel piano, sezione 9.
  - D14: spec 6.3 e 8.7.
  - D15 (Q45-Q47): tabella in 6.3.
  - M1: `--local` solo con un valore vero, in 8.5.
  - Ruling 9-13 (opzioni globali, `inspect report`, `migration up/down/fetch`, CLI 2, gruppi non nominati): tabella e righe di 8.5 e 16.
  - Ruling 14, 15, 17, 18 (Prisma, Drizzle, fatti riconfermati, Prisma 8): 8.5, 11.4, 16 e piano.
  - Righe 81, 82, 87, 93: 16, 11.4 e riga 34 della sezione 20.
  - Righe 129-181 (atti, `libero`, difetto `verify`, correzione del prodotto, copia dei file del plugin, segnaposto di `WebFetch`): 16 e sezione 16 del piano.
  - Le righe di processo (43, 56, 63, 69, 74, 102, 110) e M6 (riga 47) sono dichiarate «nessun contenuto da portare»: giudizio corretto, sono scelte di conduzione e un difetto già corretto dei test.
- ✅ **Minor `(deferred)`:** tutti i 40 circa di `progress.md` hanno una destinazione nel blocco «A B8, da B7» o in una voce chiusa della sezione 9. Ho confrontato Task 1 (M2-M5, M7, M8), 2, 3, 4, 5, 6, 7 e 8 con le righe 48-188: nessuna manca. M8 (tre scorrimenti di `FLAG_EFFECTS`) è rinviato con il motivo.
- ✅ **Sezione 9 del piano:** i rinvii a B7 sono tutti marcati «Chiuso da B7 (task, decisione)» o restano aperti con il motivo («Decisione 6, scritture remote di Wrangler», «Rinvii di B7 rimasti aperti dalla decisione 17»). Il blocco «A B8, da B7» ha i costi Q2, Q4, Q5, Q11, Q15, Q18, Q23, Q31-Q44 (tutti presenti, Q31..Q44 uno per uno) e Q45-Q47; «P1-P38» è scritto come differenza, senza toccare il rapporto delle fonti approvato.
- ✅ **Sezione 16 del piano «Prove di B7»:** la tabella «Copertura» ha 27 righe. Ho confrontato le colonne «Punto» di `coverage.md` e della sezione 16 con `diff` sul testo: identiche. Ogni riga ha test o evidenza, e dove la prova non c'è lo dice («Nessun test nuovo per `database`…», «Le descrizioni sono verificate leggendo il codice del ramo, non da un test»). Segue «Prove oltre la tabella» con la prova reale L2 e l'esito **riuscita, composita**: due esecuzioni, scelta dell'utente a metà, difetto del prodotto corretto, due atti del controller, tre file del plugin copiati a metà. Costi 3,16 + 4,53 = 7,69, nessun addebito: l'aritmetica torna.
- ✅ **P14:** in 6.3 la riga dice «a `frontend` fino alla rev 33, a `database` dalla rev 34 (Q2)… la pagina approvata di `frontend` invecchia». Nel piano è la voce (1) di «Le pagine approvate che invecchiano» (`docs/profili/frontend.md`, punti 10 e 19), con la spiegazione del cambio e senza toccare la pagina. Anche le pagine di `backend` e `infra` sono scritte come invecchiate.
- ✅ **Dati privati:** ho cercato nelle righe aggiunte nome utente, host, `/home/`, `MEGA`, email, forme di token e URL con credenziali. L'unico riscontro è la riga di sezione 16 che descrive l'anonimizzazione («`/home/` solo `/home/USER`», «percorso di un altro progetto dell'utente sostituito con un segnaposto»): non contiene dati. Nessun nome di progetto privato.
- ✅ **Fatti non ricavabili da una pagina scritti come tali:** la CLI 2 compare in 8.5 «Dalla memoria del controller, **non da una pagina**», in 16 («**Non verificato su una pagina**… da ricontrollare»), nel piano («la pagina porta la frase dal controller, non da una pagina») e nel minor del Task 4. Il rinvio dice dove si può verificare (note di rilascio di github.com/supabase/cli).
- ✅ **Catalogo (Step 2):** riga `database` con i 4 pattern veri e senza `**/schema.*` (motivo spiegato), nota sulle graffe chiusa; 2.1 (`database-reviewer` non è fonte, `rules-database` precaricata, `final-database` con `model: inherit` e sola lettura); 2.2 (`WebFetch` per `reviewer-database`, `final-database` no); 2.3 (`dod` vuoto con il motivo e l'avvertenza sulle opzioni remote); 4 (fonti vere, prefisso `R-DATABASE-`); 6 (riga B7); intestazione.
- ✅ **Progetto di B:** una sola riga, l'avanzamento (B6 unita, B7 eseguita), come chiede lo Step 3.
- ✅ **Piano principale, resto dello Step 3:** stato in testa (con base, commit, esito composito, suite 4061), riga B7 della sezione 2, riga B7→B8 della sezione 3 con `FINAL_AREAS`, `DatabasePrecedenceTest`, `REMOTE_FLAGS` e il caso `database` a sei passi di `run-b1-flow.sh`.
- ⚠️ **Step 4, suite:** `suite-task-9.log` ha 4061 test, OK, Python 3.11 (skipped=13) e 3.13 (skipped=11), `exit 0`, nessun «unclosed». Il log non dice con quale `PYTHONWARNINGS` sia girato, quindi non si verifica dal log se la corsa con `error::ResourceWarning` ci sia stata. Non l'ho rilanciata, come da istruzioni. Lo stato in testa dice che l'ha avuta; lo controlla il controller.

## Punti di forza

- Ogni voce del ledger ha un posto scritto, e il report dà una tabella verificabile riga per riga. Le righe di processo sono distinte da quelle di contenuto.
- La spec dichiara onestamente i limiti: CLI 2 dalla memoria, esito composito, nessun rilievo `[blocca]` sul diff visto dal vivo, descrizioni verificate sul codice e non da un test.
- La tabella Q1-Q47 è completa e ogni caso ha il costo nella stessa riga, come in B6. I costi portati nel piano sono raggruppati per tipo (Q5/Q7/Q8/Q26/Q28, Q15/Q37/Q41, Q11/Q23/Q36/Q42/Q43), con il rimedio per quelli che toccano pagine già approvate.
- Cura del metodo: pagine approvate non toccate, differenza «P1-P38» scritta nel piano e non nel rapporto approvato, nota sulle pagine di terzi con istruzioni (da non eseguire mai) riportata in 16.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

1. **Il report afferma più di quel che c'è nella spec.** `task-9-report.md`, sezione «Dubbi»: «la spec 16 e il piano 16 dicono “4061 test”». Nella spec del nucleo la stringa 4061 non compare (grep sul file vivo: nessuna riga); i 4061 test stanno solo nello stato in testa del piano principale (riga 6). La spec dice «4,53 USD…» e altri numeri della prova, ma non il numero dei test. Non è un difetto del documento (la spec per B6 faceva lo stesso), è un'affermazione errata nel report. Correzione: nulla da cambiare nei file, solo non ripetere l'affermazione nella revisione finale.
2. **`PYTHONWARNINGS` non dimostrato nel log di Task 9.** `suite-task-9.log` righe 1-15 non riporta le variabili d'ambiente. La brief chiede le due corse (`tests/run` e `PYTHONWARNINGS=error::ResourceWarning tests/run`). Se il controller non la ha già, aggiungere una riga `PYTHONWARNINGS=` all'intestazione del log. Non blocca, i documenti non cambiano codice.
3. **Rinvii di processo mescolati ai rinvii di prodotto.** Il blocco «A B8, da B7» del piano contiene anche voci puramente dell'esecuzione (lunghezze dei `SessionStart` senza fonte, eventi `spec_audit_round` 5 contro 9). Sono dichiarate come minor del Task 8 con il rapporto di riferimento, quindi vanno bene; la revisione finale farà il triage, come dice la brief.

## Valutazione

**Qualità del task:** Approvato.

**Motivo:** Le otto sezioni della spec, la riga 34, il catalogo, lo stato e la sezione 16 del piano ci sono tutti. Ogni `Ruling:` e ogni minor `(deferred)` del ledger entra nella spec o ha un rinvio con il motivo. Nessun file approvato è toccato, nessun dato privato, e i fatti non verificati su una pagina (CLI 2) sono scritti come tali. Restano tre minor, nessuno sul contenuto dei documenti.
