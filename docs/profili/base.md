# Regole di base di tollgate

Questa pagina è per te: devi dire se le regole vanno bene.

## Cosa sono

Sono dieci regole semplici, uguali per ogni lavoro e per ogni tipo di progetto. Dicono cosa fare prima di toccare un file: leggere quello che c'è, cercare la documentazione ufficiale, non inventare.

Valgono per chi scrive il codice e per chi lo rivede. Chi scrive può essere un agente a cui è affidato un task, cioè un pezzo del lavoro. Può essere anche Claude Code che lavora direttamente con te.

Prima di scrivere, chi lavora consegna una «nota di ricerca». È un breve elenco di cosa ha letto nel progetto e di quali pagine ufficiali ha consultato. Alla fine l'agente scrive anche un report, cioè il resoconto di quello che ha fatto.

Chi rivede guarda la nota, il «diff» o il report. Il diff è l'elenco delle righe cambiate. Per ogni regola chi rivede risponde sì o no.

Le regole vengono da due metodi di lavoro con licenza libera (agent-skills e superpowers) e dal «progetto di B». Il progetto di B è il documento che hai approvato il 27 ottobre con le tue correzioni.

## Cosa cambia se approvi

Oggi le regole sono una bozza e non bloccano niente. Dopo la tua approvazione cambia questo.

I lavori hanno tre livelli. L0 sono i lavori piccoli. L1 e L2 sono i lavori medi e grandi.

- In L1 e L2 la prima modifica senza una nota valida viene rifiutata.
- In L0 resta il solo avviso. Lo riceve la sessione principale di Claude Code, cioè chi lavora con te direttamente, e può andare avanti.
- Il rifiuto vale anche nei lavori già in corso e nei task già avvisati. Non c'è un periodo di tolleranza.
- Nei lavori veri vale da quando la nuova versione, una volta unita al ramo principale (main), viene installata sul tuo computer. Il plugin è tollgate installato in Claude Code.

La colonna «Blocca?» dice quali regole sono le più serie. Se una di queste non è rispettata, chi rivede ferma il task. Le altre sono segnalate ma non lo fermano. Un difetto viene segnalato una sola volta, con la regola che viola.

## Le regole

| N. | In parole semplici | Blocca? | Da dove viene |
|---|---|---|---|
| 1 (R-BASE-01) | Ogni file che esisteva già e che il lavoro modifica è elencato nella nota, sotto «Letto nel progetto». | sì | Metodo agent-skills e progetto di B |
| 2 (R-BASE-02) | Se il lavoro usa una libreria esterna, la nota scrive la sua versione e da quale file l'ha presa. Se il file non la dice, la nota lo scrive: non si indovina. | sì | Metodo agent-skills |
| 3 (R-BASE-03) | Per ogni libreria o servizio esterno c'è almeno una pagina ufficiale (documentazione o novità di versione). Un blog o un forum non bastano. | sì | Metodo agent-skills |
| 4 (R-BASE-04) | Ogni nome di modello di intelligenza artificiale scritto nel codice ha l'indirizzo della pagina ufficiale dei modelli del fornitore. | sì | Le tue correzioni raccolte nel progetto di B |
| 5 (R-BASE-05) | Se si scrive «non esiste» o «non è supportato», si dice dove si è cercato: un file o un indirizzo. | sì | Le tue correzioni raccolte nel progetto di B |
| 6 (R-BASE-06) | Ogni indirizzo citato come fonte nel codice o nel report compare anche nella nota. Gli indirizzi che servono al programma (per esempio un indirizzo da chiamare) restano fuori. | sì | Le tue correzioni raccolte nel progetto di B |
| 7 (R-BASE-07) | Una funzione o un componente nuovo segue lo schema di uno simile già nel progetto, se c'è, e il report dice quale. | no | Metodo agent-skills |
| 8 (R-BASE-08) | Se il lavoro cambia la build (la preparazione del programma), il rilascio o la CI (i controlli automatici), la nota elenca i file di configurazione già presenti che li riguardano. | no | Le tue correzioni raccolte nel progetto di B |
| 9 (R-BASE-09) | Scrivere «nessuna fonte esterna» è ammesso solo se il lavoro non usa librerie o servizi esterni, e la nota ne dice il motivo. | sì | Il progetto di B |
| 10 (R-BASE-10) | Il report dice che una cosa funziona solo se un comando eseguito nel task lo prova, e riporta il comando con il suo esito. | no | Metodo superpowers |

Le fonti sono state controllate una per una. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/base-fonti.md`.

## Regole tolte dalla verifica

Nella bozza erano dodici. Due non hanno passato il controllo delle fonti e sono state tolte, perché una regola senza una fonte che la regga non entra.

- **Bozza n. 10: ogni correzione di un difetto porta un test.** Il test doveva essere rosso (cioè fallire) prima della correzione e verde (cioè passare) dopo. La fonte dice una cosa vicina, ma non quella: parla di capire la causa del difetto, e non ammette l'eccezione «se non si può, il report dice perché», aggiunta nella bozza. Correzione possibile: tenere solo il test prima della correzione, senza eccezione, e appoggiarla a un'altra riga dello stesso metodo che parla del ciclo rosso-verde.
- **Bozza n. 11: se la documentazione ufficiale non si trova, scriverlo.** Doveva usare la parola «non verificato» e dire dove si è cercato. La fonte parla di un'etichetta «non verificato», ma non chiede di dire dove si è cercato, e per le fonti in contrasto chiede un'altra cosa (avvisare l'utente). Correzione possibile: ridurla a «se la documentazione ufficiale non si trova, dirlo con le parole «non verificato»».

Se vuoi una delle due, scrivi per esempio «rimetti la bozza n. 10 corretta». In quel caso passa di nuovo dal controllo delle fonti prima di entrare. Le regole rimaste sono state rinumerate: quella che era la n. 12 ora è la 10.

## Come rispondere

- «approvo»: le dieci regole entrano come sono e il blocco si accende come descritto sopra.
- «correggi la N con …»: cambio il testo della regola N come dici tu. Se cambia ciò che dice la fonte, la ricontrollo.
- «togli la N»: la regola esce e le altre si rinumerano. Dopo l'approvazione i numeri non cambiano più.
