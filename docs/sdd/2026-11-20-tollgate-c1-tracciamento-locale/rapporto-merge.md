C1 (tracciamento locale) è pronta per il merge. Tutti i 10 task sono fatti e revisionati, la prova reale è riuscita, la revisione finale (opus) è chiusa senza rilievi gravi aperti e la suite è verde tre volte.

## Commit e test

- Il ramo `c1-tracciamento-locale` ha **16 commit** sopra `main` (`055dc80..4cf5824`).
- L'ultima corsa della suite ha **4349 test** verdi su Python 3.11 e su Python 3.13, con gli avvisi trattati come errori (erano 4180 prima di C1). Le tre corse finali sono tutte verdi.

## Decisioni prese durante il lavoro

Sono le 44 decisioni che ho preso al posto tuo («ruling»), nell'ordine, ognuna con il costo se fosse sbagliata.

1. D1: un secondo test sulla pulizia di `start`, che il piano non nominava, si adatta come il primo (limite di 180 giorni nel progetto di prova, evento nell'archivio). Costo: nessuno sul prodotto.
2. D2: un test della migrazione 6 che fissava il numero «6» ora usa l'ultima versione. Costo: nessuno.
3. D3: un subagente senza righe di consumo nella trascrizione non ha l'evento `cost`. Costo: quel subagente resta senza costo, come uno con la trascrizione illeggibile.
4. D4: un subagente non può registrare una ruling come «scelta dell'utente» (`--by user`); lo può fare solo la sessione principale. Costo: un subagente che riporta una tua frase deve registrarla come sua.
5. D5: i giorni di `[retention]` sono rifiutati sopra 36500 (cento anni). Costo: chi vuole tenere tutto per sempre usa `0`.
6. D6: la cartella delle evidenze della prova si sceglie con una variabile controllata, senza poter uscire da `docs/verifiche/evidenze/`. Costo: nessuno.
7. D7: la fotografia è «di sola lettura dei dati»; il primo avvio dopo un aggiornamento può aggiornare lo schema, con una copia in `backup/`. Costo: il gestionale può trovare una copia in più.
8. D8: la cartella `archive/` nasce con i permessi riservati della cartella di stato. Costo: nessuno.
9. D9: in `adopt` il numero di fette di un piano L1 si legge dal testo del piano nel commit. Costo: in un caso raro le fette risulterebbero 1, e la taglia resterebbe comunque media.
10. D10: con `approve spec` e `approve plan` la taglia si scrive prima del cambio di fase. Costo: nessuno.
11. D11: il test «un subagente può registrare una ruling» ha anche la prova contraria (lo stesso testo con un comando vietato è negato). Costo: nessuno.
12. D12: la taglia si riscrive anche quando cambia solo chi l'ha decisa (le regole o tu). Costo: nessuno.
13. D13: la pagina per il gestionale dice che `reopen plan` rinumera i task, quindi il costo per task può unire piano vecchio e nuovo. Costo: un conto per task impreciso nei lavori riaperti.
14. D14: la pagina per il gestionale dice quando le fette sono vuote, che le chiavi dei task sono testo, e che avanzamento, dipendenze e coda arrivano con C4 e C5. Costo: nessuno.
15. D15: senza database la fotografia non crea niente. Costo: nessuno.
16. D16: le domande dirette si leggono dall'input grezzo dell'hook, che regge ogni forma. Costo se la forma vera è un'altra: le risposte restano vuote, la domanda resta registrata.
17. D17: nessun messaggio nuovo scrive il nome nudo del programma. Costo: nessuno.
18. D18: le revisioni in parallelo leggono solo i commit, mai il worktree vivo. Costo: nessuno.
19. D19: una ripetizione di `approve plan` dopo un'interruzione non registra due volte la taglia. Costo: nessuno.
20. D20: le etichette di una ruling (`cosa:`, `perché:`, `costo:`) valgono anche in maiuscolo. Costo: nessuno.
21. D21: il costo legge la trascrizione una volta sola, e la vecchia funzione che cancellava eventi senza archiviarli è tolta. Costo: nessuno.
22. Le correzioni dei numeri di riga trovate dallo scan vanno nei brief dei task. Costo: nessuno.
23. La seconda metà della prima suite di prova (Python 3.13) l'ho fermata perché la macchina era lenta e `main` era già verde. Costo: un difetto solo di 3.13 sarebbe comparso al Task 1 (non è successo).
24. La revisione del Task 4 è girata insieme al Task 5, su file diversi. Costo: nessuno.
25. La revisione del Task 5 è girata insieme al Task 6, su file diversi. Costo: nessuno.
26. Un rilievo «minore» del Task 5 era in realtà un requisito (la prova contraria con lo stesso testo), quindi è entrato nella correzione. Costo: nessuno.
27. La revisione del Task 6 è girata insieme alla correzione del Task 5. Costo: nessuno.
28. La forma vera della risposta di una domanda diretta non si può vedere ora: resta alla prova vera di C6. Costo: risposte vuote negli eventi fino ad allora.
29. La seconda revisione del Task 5 è girata insieme al Task 7. Costo: nessuno.
30. La revisione del Task 7 è girata insieme al Task 8. Costo: nessuno.
31. Il test di `approve finding` sta nel file dei test degli atti, dove vive il comando, e non in quello dei rilievi. Costo: nessuno.
32. Ho controllato io che la misura dello spazio sia stata fatta solo su copie (nessun file accanto alle copie nel repo). Costo: nessuno.
33. La revisione del Task 8 è girata insieme alla correzione del Task 7. Costo: nessuno.
34. La seconda revisione del Task 7 è girata insieme allo script della prova. Costo: nessuno.
35. Le evidenze della prova sono in un commit a parte, fatto da me dopo la pulizia; il rapporto in un commit a parte, dopo la suite. Costo: un commit in più.
36. I minori rinviati entrano nella sezione 8 del piano principale solo dopo la revisione finale. Costo: nessuno.
37. La revisione del rapporto della prova è girata insieme al Task 10. Costo: nessuno.
38. F1: il costo del revisore di un task ora conta in quel task (prima restava solo nel totale). Costo: per i revisori, il task dell'evento `cost` è diverso da quello dell'evento di chiusura (scritto nella pagina).
39. F2: una ruling con `perchè:` (accento sbagliato) è accettata. Costo: nessuno.
40. F3: quando il livello sale, il messaggio dice anche la taglia nuova. Costo: una riga in più in quel messaggio.
41. F4, F5, F6: frasi della spec e della pagina corrette o aggiunte (lo zero di `[retention]`, «taglia nulla», l'indirizzo locale del repo). Costo: nessuno.
42. La prova dal vivo di una domanda diretta (punto V1) non è una scelta tua da fermare: te la propongo qui sotto, con la domanda del merge. Costo: nessuno.
43. Nella sezione 8 del piano principale sono entrati i due minori rinviati e una nota per C4. Costo: nessuno.
44. Due minori nuovi dell'ultima revisione restano così: due righe di codice lunghe, e uno «zero» al posto di «non so» nei token di due casi rari. Costo: solo forma e precisione in casi rari.

## Rilievi minori rinviati

Sono le voci della tabella di triage della revisione finale con l'esito «rinviato». Stanno nella sezione 8 del piano principale di C.

1. Riga 6: se il database dà un errore proprio tra la registrazione del piano e la taglia, la taglia e il messaggio «piano registrato» si perdono. Motivo: serve un errore raro in quel punto, e il rimedio tocca l'ordine delle fasi, quindi conviene farlo con il lavoro sul piano di C5.
2. Riga 18: la regola che riconosce le domande dirette dipende dall'ordine dei campi nell'input degli hook. Motivo: l'ordine vero si vede solo dal vivo (C6), e il caso guasto richiede più cose insieme.

In più, fuori dalla tabella, due piccoli minori dell'ultima revisione (decisione 44 qui sopra).

## Prova reale

- **Esito: riuscita.** Tutti i passi al primo tentativo, nessun difetto trovato.
- **Taglia:** all'avvio «piccolo», motivo «ancora nessun piano»; dopo il piano «piccolo», motivo «piano con 1 task».
- **Costi registrati:** due subagenti, l'implementatore con 49 528 token e il revisore con 32 293, entrambi sul modello `claude-sonnet-5-5`; nella fotografia il lavoro ha 81 821 token in tutto.
- **Costo equivalente della prova:** 0,93 USD sulla quota dell'abbonamento, **nessun addebito**.
- **Cosa non si è potuto provare:** le domande dirette (con `claude -p` non esistono: la prova vera è di C6) e la crescita del costo di un subagente ripreso (nella prova nessuno è stato ripreso).

## Cosa cambia nei progetti

- Ogni lavoro ha una taglia (piccolo, medio, grande) con il motivo, e tu la puoi fissare con `/tollgate:approve size`.
- Gli eventi non si cancellano più da soli; con `events_days` vanno prima in un archivio.
- Le domande dirette, le ruling e i costi in token restano nello stato locale.
- `tollgate snapshot` e `docs/uso/gestionale.md` sono il contratto per il gestionale.

**Un punto da sapere prima del merge (V1).** Dopo il merge l'hook nuovo sulle domande dirette gira subito nelle tue sessioni normali. Il codice non può bloccare una domanda, ma nessuna prova ha ancora mostrato una domanda vera con l'hook acceso. Per controllarlo bastano pochi minuti in una sessione normale su un repo di prova: il modello fa una domanda, tu rispondi e guardi che la risposta gli arrivi. Non costa niente oltre la sessione. Se qualcosa non va, `/tollgate:off` spegne tutto subito. Il mio consiglio: unire ora e fare il controllo alla prima occasione.

Posso unire su `main`?
