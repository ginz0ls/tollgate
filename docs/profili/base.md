# Regole di base di tollgate

Questa pagina è per te: dice quali sono le regole e cosa succede ora che le hai approvate.

Approvata dall'utente il 2026-11-01.

## Cosa sono

Sono undici regole semplici, uguali per ogni lavoro e per ogni tipo di progetto. Dicono cosa fare prima di toccare un file: leggere quello che c'è, cercare la documentazione ufficiale, non inventare.

Valgono per chi scrive il codice e per chi lo rivede. Chi scrive può essere un agente a cui è affidato un task, cioè un pezzo del lavoro. Può essere anche Claude Code che lavora direttamente con te.

Prima di scrivere, chi lavora consegna una «nota di ricerca». È un breve elenco di cosa ha letto nel progetto e di quali pagine ufficiali ha consultato. Alla fine l'agente scrive anche un report, cioè il resoconto di quello che ha fatto.

Chi rivede guarda la nota, il «diff» o il report. Il diff è l'elenco delle righe cambiate. Per ogni regola chi rivede risponde sì o no.

Le regole vengono da due metodi di lavoro con licenza libera (agent-skills e superpowers) e dal «progetto di B». Il progetto di B è il documento che hai approvato il 27 ottobre con le tue correzioni.

## Cosa cambia ora che hai approvato

Le regole sono approvate e bloccano. Da ora vale questo.

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
| 10 (R-BASE-10) | Quando si corregge un difetto, si scrive anche un test che lo riproduce. Il report mostra che il test fallisce senza la correzione e passa con la correzione. | sì | Metodo superpowers |
| 11 (R-BASE-11) | Il report dice che una cosa funziona solo se un comando eseguito nel task lo prova, e riporta il comando con il suo esito. | no | Metodo superpowers |

Le fonti sono state controllate una per una. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/base-fonti.md`.

## Regole tolte dalla verifica

Nella bozza erano dodici. Due non hanno passato il controllo delle fonti e sono state tolte, perché una regola senza una fonte che la regga non entra.

- **Bozza n. 10: ogni correzione di un difetto porta un test.** Il 2026-11-01 l'hai rimessa tu in forma corretta ed è la regola 10 di adesso. Ora chiede il test che riproduce il difetto, senza l'eccezione della bozza, e il report deve mostrare che il test fallisce senza la correzione e passa con la correzione. È passata di nuovo dal controllo delle fonti, solo per questa regola.
- **Bozza n. 11: se la documentazione ufficiale non si trova, scriverlo.** Resta tolta. Doveva usare la parola «non verificato» e dire dove si è cercato. La fonte parla di un'etichetta «non verificato», ma non chiede di dire dove si è cercato, e per le fonti in contrasto chiede un'altra cosa (avvisare l'utente). Se la vuoi, si può ridurre a «se la documentazione ufficiale non si trova, dirlo con le parole «non verificato»», con un nuovo controllo delle fonti.

Le altre regole rimaste sono state rinumerate: quella che era la n. 12 ora è la 11.

## Come cambiarle

I numeri delle regole non cambiano più. Se vuoi cambiare, aggiungere o togliere una regola, dillo e la sistemo. Una regola nuova, o con una fonte nuova, passa prima dal controllo delle fonti.
