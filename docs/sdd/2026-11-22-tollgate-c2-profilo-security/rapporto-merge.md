C2 (profilo `security`) è pronta per il merge. Tutti i 10 task sono fatti e revisionati, le regole le hai approvate tu il 23 novembre, la prova reale è riuscita, la revisione finale (Fable) è chiusa senza rilievi gravi aperti e la suite è verde tre volte.

## Commit e test

Il ramo `c2-profilo-security` ha **18 commit** sopra `main` (`7822aed..1517fd3`). Su `main` entrerebbero come un solo commit.

L'ultima corsa della suite ha **4520 test** verdi su Python 3.11 e su Python 3.13, con gli avvisi trattati come errori (erano 4349 prima di C2). Le tre corse finali sono tutte verdi.

## Regole approvate

Le regole di sicurezza sono **17**, approvate da te il **23 novembre 2026** senza modifiche, con le proposte dei 31 punti della pagina così come erano.

Bloccano un task **13 regole**: la 1 (chi può arrivare al codice), la 3 (test del caso in cui l'accesso va rifiutato), la 4 (controllo sul server), la 5 (senza un segreto il codice si ferma), la 6 (password), la 7 (token), la 8 (confronto dei segreti), la 9 (cookie), la 10 (nessun segreto nel codice o nei log), la 12 (valori che arrivano da fuori), la 13 (reindirizzamenti), la 14 (chiamate da altri siti), la 17 (nessun servizio vero toccato). Non bloccano la 2, la 11, la 15 e la 16.

Si sovrappongono a regole che avevi già approvato la 10 (cinque regole sui segreti di `backend`, `infra` e `database`) e la 12 (due regole di `backend` sui dati in ingresso). Hai deciso di tenerle (punti 21 e 22 della pagina): senza, un file di login che va agli agenti di sicurezza non avrebbe nessuna regola sui segreti caricata.

Il 24 novembre, con il tuo OK, ho precisato una frase del punto 3 della pagina di sicurezza (i file `.tsx` dentro `auth/` vanno agli agenti di sicurezza) e ho corretto una frase sbagliata nella pagina e nell'agente del profilo `database` (i comandi di `dod` girano a fine lavoro, non durante il task).

## Modelli degli agenti

Dopo C2 nessun agente di tollgate usa più sonnet. Vale per tutti i profili, anche quelli già approvati.

| Chi | Modello |
|---|---|
| Chi rivede un task (`task-reviewer` e i revisori di ogni area) | Fable |
| Chi rivede il lavoro intero (`final-reviewer`, `final-database`, `final-security`) | Fable |
| Chi verifica i rilievi e chi controlla spec e piano (`finding-verifier`, `spec-auditor`, `spec-adversary`, `plan-adversary`) | Fable |
| Chi scrive il codice (`implementer` e gli implementatori di ogni area), anche nei giri di correzione | opus |
| Le prove reali e gli eval | opus |

In un progetto puoi cambiarli con `[review] models` nel `tollgate.toml`.

**Sicurezza fin dal progetto.** Vale in ogni lavoro con agenti, anche dove il profilo `security` non è acceso. Chi controlla la spec e il piano cerca ciò che il documento non dice su chi accede, sui dati, sui segreti e sugli input ostili. Ogni implementatore chiude il report con una frase `Sicurezza:` che dice cosa ha considerato. Chi rivede la confronta con il codice.

## Decisioni prese durante il lavoro

Sono le 49 decisioni che ho preso al posto tuo («ruling»), nell'ordine, ognuna con il costo se fosse sbagliata. Quelle che contano di più per te sono la 1, la 27, la 36, la 37 e la 45.

- 1. Due righe di riconoscimento sono uscite dal profilo (`require('bcryptjs')` e `from 'jsonwebtoken'`), perché nessuna pagina ufficiale le mostra. Costo: un file che usa quelle due forme non accende il profilo dal contenuto; era il punto 19 della pagina e hai scelto di lasciarle fuori.
- 2. Nessuna regola cita lo standard OWASP ASVS: le stesse idee vengono dalle guide OWASP, che stanno su un sito che potevo leggere. Costo: nessuno sul contenuto.
- 3. Nessuna scheda dalla guida OWASP sui token (la pagina non c'era): la regola sui token si fonda sulle pagine ufficiali delle due librerie. Costo: nessuno.
- 4. Per aggiungere le regole di sicurezza all'elenco delle aree ho ritoccato la stessa riga anche nell'agente `final-database`, che la ripete uguale. Costo: nessuno; la fetta dopo (C3) dovrà fare lo stesso.
- 5. La spec del lavoro di prova dice in poche righe chi usa il codice, quali dati tocca e cosa succede con un input ostile. Costo: un segnale in meno nella prova, come poi è successo.
- 6. I revisori lanciano i test solo su una copia in una cartella temporanea, mai nella cartella di lavoro. Costo: nessuno.
- 7. La revisione della spec aggiorna anche le sezioni che fissano i modelli degli agenti, che il piano non nominava. Costo: nessuno.
- 8. Ho verificato io che Claude Code accetta i nomi `fable` e `opus` negli agenti. Costo: nessuno.
- 9. Tre controlli dei test sui modelli sono stati resi più severi, perché dopo il cambio non provavano più niente. Costo: nessuno.
- 10. Un test in più per `keep_paths` (vale anche quando il profilo è già acceso) e un controllo più stretto sul tipo del valore. Costo: nessuno.
- 11. Due voci in più nella pagina, per due costi che la tabella dei casi non nominava (le schermate dentro `auth/`; un file e il suo test a due gruppi diversi). Costo: una pagina più lunga.
- 12. Precisazioni allo script della prova (nomi dei file, messaggi, quattro test in più). Costo: nessuno.
- 13. La voce su `import jwt` nella pagina nomina anche la libreria del browser `jwt-decode`. Costo: qualche file dell'interfaccia in L2, che hai accettato al punto 16.
- 14. Gli eval passano a opus ma la campagna predefinita resta quella vecchia: per ora basta una frase nei documenti. Costo: se qualcuno lancia gli eval senza leggere, i costi di due modelli finiscono nello stesso registro.
- 15. Due vincoli dei test sui documenti passati ai task che scrivono i documenti. Costo: nessuno.
- 16. Dove sta, negli agenti, la sezione sulla sicurezza fin dal progetto, e cosa non deve scrivere. Costo: nessuno.
- 17. Tre casi in cui un file di login va agli agenti di sicurezza invece di restare al profilo che lo riconosce li ho lasciati alla tua decisione (punto 5 della pagina, che hai approvato). Costo: nessuno.
- 18. Ho fermato la seconda metà della prima suite di prova (Python 3.13), perché la prima metà era verde e uguale a `main`. Costo: un difetto solo di 3.13 sarebbe comparso al Task 1 (non è successo).
- 19. La revisione del Task 2 è girata insieme al Task 3, su file diversi. Costo: nessuno.
- 20. Sette rilievi minori sul testo della sicurezza fin dal progetto li ho fatti correggere subito, perché quel testo gira in ogni lavoro. Dentro ci sono due scelte mie: se manca solo la frase `Sicurezza:` il rilievo è minore e non ferma il task; all'avversario del piano basta che una cosa la dica la spec approvata. Costo: una corsa della suite in più; le due scelte puoi volerle diverse.
- 21. La revisione del Task 3 è girata insieme alle correzioni del Task 2, su file diversi. Costo: nessuno.
- 22. La seconda revisione del Task 2 è girata insieme alla prima parte del Task 4. Costo: nessuno.
- 23. La tua scelta «le funzioni di Supabase restano al database» è scritta in una frase dell'introduzione delle regole, con un test, non in una regola apposta. Costo: è protetta da una frase e da tre casi provati, non da una regola.
- 24. Un test in più controlla che ogni regola citi una fonte di un tipo ammesso. Costo: nessuno.
- 25. Cinque numeri di regola sono fissati dai test (1, 3, 5, 10, 12). Costo: nessuno.
- 26. La regola 15 (limite ai tentativi di login) non blocca e si giudica sul report. Costo: un login senza limite è segnalato, non fermato; era il punto 29 della pagina.
- 27. Le regole sono 17 e non «tra 12 e 16» come stimava il piano: ho tenuto separati i reindirizzamenti dai valori che arrivano da fuori. Costo: una regola in più, che hai approvato.
- 28. Nel giro di correzione delle regole sono entrati anche tutti i rilievi minori e le correzioni delle fonti. Costo: nessuno.
- 29. I due nomi di funzione dati come esempio nella regola 8 restano senza una pagina copiata. Costo: due nomi sulla mia parola; era il punto 26 della pagina.
- 30. Quattro ritocchi di poche parole alle regole 4, 5, 9 e 10, fatti prima di mostrarti la pagina. Costo: nessuno.
- 31. La forma della pagina (cinque colonne, sezioni fisse, glossario più ampio) è quella delle pagine degli altri profili. Costo: nessuno.
- 32. Nel giro di correzione della pagina sono entrati anche i nove rilievi minori, perché era il testo su cui dovevi decidere. Costo: nessuno.
- 33. La revisione del Task 6 è girata insieme al Task 7, su file diversi. Costo: nessuno.
- 34. La revisione del Task 7 è girata insieme al Task 8, su file diversi. Costo: nessuno.
- 35. Tre ritocchi di una riga agli agenti di sicurezza, fatti prima della prova. Il più importante: una regola che non blocca non può diventare un blocco in revisione finale. Costo: una corsa della suite in più.
- 36. Nella prova reale i controllori della spec hanno fatto aggiungere molti requisiti di sicurezza (da 2 a 13). Li ho accettati e ho dato l'approvazione, perché venivano tutti dai loro rilievi. Costo: la prova mostra meno le regole e più la sicurezza fin dal progetto.
- 37. Ho proseguito la prova anche se il primo passo era costato da solo 7,30 USD equivalenti, più del previsto. Costo: la prova ha consumato 19,55 USD equivalenti di quota invece dei 10-18 stimati, senza nessun addebito.
- 38. Anche le differenze del piano di prova le ho accettate, per lo stesso motivo. Costo: come sopra.
- 39. Nove brevi riassunti di pagine della documentazione di Python, rimasti nelle evidenze della prova, li ho sostituiti con un segnaposto. Costo: le evidenze mostrano gli indirizzi letti, non il contenuto.
- 40. La revisione del rapporto della prova è girata insieme al Task 10, su file diversi. Costo: nessuno.
- 41. Dalle evidenze ho tolto anche alcuni dati tecnici del tuo account (uso della quota, scadenza delle credenziali). Costo: nessuno.
- 42. La revisione del Task 10 è girata insieme alle correzioni del rapporto. Costo: nessuno.
- 43. Nel giro di correzione della spec sono entrati anche gli otto rilievi minori. Costo: nessuno.
- 44. La revisione finale è partita mentre erano in corso le ultime correzioni ai documenti, per non perdere due ore. Costo: quelle poche frasi le ha viste una revisione a parte, non la revisione finale.
- 45. Dopo la revisione finale ho fatto un solo giro di correzione, con dentro anche le due cose che hai deciso tu il 24 novembre e tre rilievi minori. Costo: un giro più largo, senza corse in più.
- 46. Ho fatto partire una corsa finale della suite prima dell'ultima revisione delle correzioni. Costo: l'ho dovuta fermare e rifare.
- 47. Un secondo giro breve di correzione: l'esempio che avevo aggiunto alla pagina del database metteva due comandi nell'ordine sbagliato. Costo: una corsa della suite in più.
- 48. Di nuovo una corsa finale partita insieme all'ultima revisione, che questa volta non ha trovato niente. Costo: nessuno.
- 49. Non ho ripetuto nessun passo della prova reale dopo le ultime correzioni, perché toccano frasi che la prova non usava. Costo: la prova resta fatta con il testo dell'agente di prima dell'ultima correzione.

## Rilievi minori rinviati

Sono i nove rilievi minori che la revisione finale ha rinviato. Vanno nell'elenco dei rinvii del piano principale di C.

- Gli eval su opus scrivono ancora nel registro della campagna vecchia. Motivo: gli eval non girano in C; la campagna nuova va creata prima della prossima corsa.
- Il valore di `[review] models` in un progetto non è controllato. Motivo: tocca la configurazione di tutto tollgate, non è di C2.
- Due test dei profili `database` e `frontend` stampano il nome utente se un giorno lo trovano in una pagina, e sono rossi con un nome utente generico. Motivo: sono test di profili già uniti.
- Nella pagina di sicurezza la frase «i tre agenti arrivano dopo la tua approvazione» ora è superata. Motivo: la pagina è approvata; si ritocca con te alla prossima revisione.
- In un progetto JavaScript l'agente di sicurezza non può lanciare da sé un singolo test, e la pagina non lo dice. Motivo: è un limite da portarti con la prossima revisione della pagina.
- Lo specialista finale deve citare «la regola dell'area del file», che non ha davanti. Motivo: è una frase delle regole approvate; si rivede con C3.
- Se sposti a mano una funzione di login di Supabase sotto `security`, gli agenti leggono una frase che dice che lì valgono le regole del database. Motivo: tocca le regole approvate.
- Lo script delle prove non raccoglie da sé la frase `Sicurezza:` dei report. Motivo: da aggiungere prima della prova di C6.
- Una frase del piano principale sui limiti dei giri di controllo è imprecisa di un giro. Motivo: non cambia il dato; la correggo nel commit di chiusura.

## Prova reale

Esito: riuscita. Una sola esecuzione, un tentativo per passo: non è composita.

- **Consumo:** 19,55 USD equivalenti sulla quota dell'abbonamento, nessun addebito. È sopra la stima di 10-18, perché i controllori della spec e del piano (su Fable) hanno fatto 15 giri.
- **Lo specialista:** `final-security` è partito alla revisione finale insieme al revisore generale e ha riportato «ok». Ha giudicato rispettate le regole 3, 4, 5, 7, 8, 10 e 12 e non applicabili le altre che guarda. Quattro note minori, tutte scartate dal verificatore.
- **Regole viste dal vivo:** i due revisori dei task hanno citato le regole 1, 3, 4, 5, 7, 8, 10, 12, 15, 16 e 17.
- **I tre segnali delle regole:** il confronto dei segreti a tempo costante è comparso, ma è entrato dalla spec per un rilievo dei controllori, quindi non prova le regole. Chi arriva al codice e fin dove arriva il cambio sono nei due report, ma li chiede già il testo dell'agente di sicurezza: provano che il lavoro va all'agente giusto, non le regole. I numeri delle regole citati dai revisori con il contenuto giusto sono un indizio forte.
- **Il titolo delle regole nelle trascrizioni:** sì. «Regole security (versione 1)» è nelle trascrizioni di cinque subagenti: i due implementatori, i due revisori e lo specialista. È la prova che le regole vengono caricate.
- **Sicurezza fin dal progetto:** ha lavorato già sulla spec, che è passata da 2 a 13 requisiti. I due report hanno la frase `Sicurezza:`.

## Cosa cambia nei progetti

- `/tollgate:init --update` propone `security` dove ci sono cartelle `auth/`, `security/`, `rls/`, file `middleware` o `proxy`, o le librerie di password e token. Lo propone anche quando un altro profilo riconosce lo stesso file.
- Un lavoro che tocca quei file sale a L2 e alla fine ha un revisore in più, `final-security`. Sotto `auth/` il lavoro era già L2 anche prima.
- I file sotto `supabase/` alla radice restano a `database`.
- Tutti i revisori di tollgate usano Fable e tutti gli implementatori opus, anche nelle aree già approvate. Costo: più consumo dell'abbonamento a ogni lavoro, nessuna spesa in denaro.
- Ogni piano e ogni implementazione considerano la sicurezza: nei report c'è la frase `Sicurezza:`.
- Se vuoi un controllo automatico dei casi di accesso negato lo aggiungi a mano nel `tollgate.toml`, come dice la pagina: `commands = { denied = "python3 -m unittest discover -s tests -k denied" }` e `dod = ["denied"]`. Gira a fine lavoro. Non deve usare credenziali vere.

Posso unire su `main`?
