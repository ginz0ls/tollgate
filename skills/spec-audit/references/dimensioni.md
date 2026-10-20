Derivato da prd-audit (sAInapse), con l'accordo dell'autore: le dieci lenti dell'audit della spec e del piano.

# Le dieci lenti dell'audit

Le domande da porre per ciascuna. Non andare a memoria: le domande che sembrano ovvie sono quelle
che si saltano.

**Una lente per passata, applicata all'intero documento.** Non mescolarle: applicate insieme, se ne
applica bene una sola.

---

## L1. Coerenza verticale — rispetto al livello superiore

- Ogni requisito discende da qualcosa scritto nel documento superiore, o ne è stato inventato?
- Il documento **reinterpreta in silenzio** una decisione del livello sopra? La reinterpretazione
  silenziosa è più pericolosa della contraddizione aperta, perché nessuno se ne accorge.
- Il documento superiore è cambiato dopo che questo è stato scritto? Confronta le date e i numeri
  di revisione.
- Ci sono decisioni prese qui che **spettavano al livello sopra**? Una milestone che decide
  l'architettura è una milestone che sta sconfinando.

## L2. Coerenza orizzontale — rispetto ai documenti pari grado

- Le dipendenze dichiarate sono vere? Un documento che dice «dipende da M2» ma usa qualcosa
  costruito in M3 ha una dipendenza nascosta.
- **Le dipendenze dichiarate sono minime?** È l'errore opposto e costa di più: una dipendenza
  scritta per abitudine ritarda una milestone di mesi senza motivo tecnico. Per ognuna chiedi:
  *cosa esattamente va a prendere lì dentro?* Se non sai rispondere, la dipendenza non esiste.
- Esiste un requisito assegnato a **due** milestone diverse? Una delle due lo costruirà per niente.
- Esiste un requisito assegnato a **nessuna**? Cerca nella specifica le funzionalità promesse e
  verifica che ognuna abbia una casa.
- Un documento successivo assume qualcosa che questo non consegna?

## L3. Coerenza interna

- Due sezioni si escludono a vicenda? Accosta deliberatamente le sezioni distanti: architettura
  contro modello dati, requisiti contro criteri di accettazione, scope contro task.
- Un termine è usato con due significati diversi in due punti?
- Un numero compare due volte con valori diversi?
- Lo scope escluso contiene qualcosa che i requisiti includono?

## L4. Requisiti verificabili

- Ogni requisito si può dichiarare soddisfatto o non soddisfatto **senza discutere**?
- Cerca gli aggettivi vaghi: «adeguato», «robusto», «performante», «intuitivo», «appropriato».
  Ognuno nasconde una decisione non presa.
- Cerca i verbi deboli: «gestire», «supportare», «considerare», «tenere conto di». Gestire come?
- Un requisito che descrive una soluzione invece di un bisogno impedisce soluzioni migliori.
- I requisiti dicono **cosa**, non **come**? Il come sta nel piano, non nel PRD.

## L5. Criteri di accettazione osservabili

- I criteri descrivono ciò che si osserva da fuori, o ciò che fa il codice?
  «Il motore calcola la CA» è un criterio inutile; «la CA mostrata coincide con quella del manuale
  in questi cinque casi» è verificabile.
- Ogni criterio dice **come si verifica**? Se non lo dice, verrà verificato guardando lo schermo e
  annuendo.
- I criteri coprono i casi di fallimento, o solo il percorso felice?
- Esiste un criterio che nessuno saprebbe come verificare? Va riscritto o tolto.

## L6. Copertura in entrambe le direzioni

- Ogni requisito ha almeno un task che lo realizza? Costruisci la tabella e guarda le righe vuote.
- Ogni task serve almeno un requisito? Un task senza requisito è lavoro che nessuno ha chiesto.
- I criteri di accettazione hanno un task che li verifica, o si presume che «passeranno»?
- Le domande aperte hanno un momento in cui verranno risolte, o restano lì?

## L7. Proiezione sulle milestone future

Per ogni scelta strutturale, chiedi cosa le succede a N+1, N+2, N+3.

- Questa struttura dati regge quando arriveranno **più** entità dello stesso tipo?
- Questo permesso regge quando ci sarà **più di un utente**?
- Questo campo regge quando **due dispositivi** lo modificheranno insieme?
- Questa operazione regge quando dovrà essere **annullata**?
- Questa scelta è **fondativa** (modello dati, permessi, identità: va decisa ora) o **additiva**
  (vive sopra: va rimandata)? Sbagliare la classificazione costa in entrambe le direzioni.
- Cosa in questa milestone impedirebbe una milestone futura già dichiarata?

## L8. Fatti

Vedi `verifica-fatti.md`. In sintesi: nessuna affermazione fattuale passa senza verifica.

## L9. Le dodici lacune ricorrenti

Sono le omissioni che si ripetono in quasi ogni documento. Controllale una per una: la maggior parte
degli audit produttivi nasce da qui.

| # | Lacuna | La domanda |
|---|---|---|
| 1 | **Annullamento** | Ogni azione dell'utente si può disfare? Anche quelle che aggiungono o rimuovono righe, non solo quelle che cambiano un valore? |
| 2 | **Errori** | Cosa succede quando l'operazione fallisce? Chi lo scopre, come, e cosa può fare? |
| 3 | **Concorrenza** | Cosa succede se due utenti, o due dispositivi, fanno la stessa cosa insieme? |
| 4 | **Offline e rete lenta** | Il documento presuppone che la rete ci sia sempre? |
| 5 | **Ordine e ripetizione** | Le operazioni accodate vanno applicate in ordine? Una ripetuta ha effetto una o due volte? |
| 6 | **Sicurezza: dove avviene il filtro** | I dati riservati sono filtrati dal server o dal client? Un filtro nel client non è un filtro. |
| 7 | **Prestazioni sotto vincolo** | Le regole di sicurezza vengono valutate riga per riga? Le colonne interrogate sono indicizzate? |
| 8 | **Volume** | Quanti dati saranno davvero? Misura, non stimare: la differenza fra 300 KB e 300 MB cambia l'architettura. |
| 9 | **Cancellazione e integrità** | Cosa succede alle righe collegate? La cancellazione è reversibile? |
| 10 | **Crescita senza limite** | Quali tabelle crescono a ogni uso e non vengono mai potate? |
| 11 | **Evoluzione dello schema** | Come si migrano i dati esistenti quando la forma cambia? |
| 12 | **Accessibilità e lingua** | Contrasto, aree toccabili, ordine di tabulazione, etichette. E: chi traduce i contenuti, e quando? |

Aggiungine altre quando le trovi: una lacuna che hai incontrato due volte in progetti diversi merita
di entrare in questa tabella.


---

## L10. Completezza dell'audit

**Questa lente non guarda il documento, guarda il lavoro fatto finora.** È quella che impedisce al
ciclo di chiudersi per stanchezza invece che per esaurimento.

- Quale sezione dell'inventario è ancora senza esito?
- Quale lente non ho applicato a quale sezione? Costruisci la griglia sezioni × lenti e cerca le
  caselle vuote: sono lì che si nasconde ciò che non hai guardato.
- Quale affermazione ho dato per verificata senza verificarla davvero?
- Quale rilievo è marcato `[RAGIONATO]` quando potevo promuoverlo a `[VERIFICATO]` eseguendo
  qualcosa? Ogni `[RAGIONATO]` evitabile è un debito.
- **Quale correzione ho applicato e non ho ancora riauditato?** Il testo scritto durante l'audit è
  il meno controllato del documento.
- Ho trovato un difetto e l'ho corretto in un punto solo? Dove altro vale lo stesso ragionamento?
- Sto per fermarmi: è perché ho esaurito, o perché sono stanco? Se non sai distinguere, non hai
  esaurito.

**Quello che trova L10 diventa il lavoro della passata successiva.** Se L10 non trova niente due
cicli di fila, e l'inventario è coperto, l'audit è finito.
