# Task 9: report

## Cosa ho fatto (solo documenti, nessun codice)

- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 33: intestazione; 6.3 (parità: primo blocco dichiarato e `init` in ordine alfabetico, P37; pattern per estensione a zero segmenti; task misti `frontend`+`backend`; profilo attivo anche quando il file va a un altro verticale; bullet «Gli agenti di `frontend`» con il costo del divieto di `node`/`npm`; tabella P1-P38 in breve con i costi); 7.1 (`READONLY_TYPES`); 7.3 (`reviewer-frontend` con `WebFetch`); 8.7 (`dod` di `frontend`); 11.2 (frase «non propone i pattern così come sono» riscritta, forma `name` seguita da `ext`, bullet della forma `ext`, bullet dei marcatori e del rimedio per `routes/` con i costi e la pagina di `backend` che invecchia, P36 nel bullet di `exclude`); 11.4 (quattro forme, `**/*.sql` ora accettato, frammento di `frontend`, `readonly_agents`); 16 («Verificato in B6» con la prova reale, «Ancora da verificare» aggiornato); riga 33 della sezione 20.
- Catalogo (`2026-10-08-tollgate-profili-verticali.md`): intestazione, sezione 2 (quattro forme, riga `frontend`, nota sulle graffe), 2.1, 2.2, 2.3, 3, 4, 6.
- Piano principale: stato in testa (B5 portata a «unita» perché `525d8d8` è su `main`), righe B5 e B6 della sezione 2, riga B6→B7 della sezione 3, sezione 9 (voci chiuse da B6, nuovo blocco «A B7-B8, da B6»), nuova sezione 15 «Prove di B6».
- Progetto di B: riga di avanzamento.

## Scelte e scostamenti

- B5 nel piano principale e nel progetto era ancora «unione in attesa»: l'ho scritta «unita su `main`, `525d8d8`» (verificato con `git log`), perché la riga di B6 non poteva stare accanto a un B5 sbagliato.
- Riga «Un profilo resta attivo…» della sezione 15: nessun test nuovo la prova (è `active_profiles` già esistente); l'ho scritto, senza attribuire test.
- Il blocco «A B7-B8, da B6» riassume i `minor (deferred)` dei Task 1-7 che toccano B7-B8 (non il ledger intero) e le `Ruling:` D1 (limiti), D5, node/npm, pagine che invecchiano.
- Il Task 8 era ancora in revisione: se cambia l'esito, la sezione 16 della spec e la sezione 15 del piano vanno ritoccate.

## Test

- `tests.test_docs`: 7 test OK prima della suite.
- Suite completa: `suite-task-9.log`, python3.11 e python3.13 3894 test OK (skipped=13 e 11), `exit 0`.
