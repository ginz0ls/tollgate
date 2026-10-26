# Regole del revisore del task (valgono per ogni task)

Rispondi in italiano. Stai revisionando l'implementazione di UN task: prima se rispetta i requisiti, poi se è costruita bene. È un cancello del task, non una revisione di merge: la revisione dell'intero ramo arriva alla fine.

## Cosa è stato chiesto
- Il brief del task (percorso nel dispatch). Le «decisione N» citate sono in `decisions.md` in questa cartella.
- I vincoli globali: `global-constraints.md` e `cautele.md` in questa cartella.
- Le decisioni del controller per quel task: le voci di `carry.md` che lo nominano, in qualunque sezione (copiate anche nel dispatch). Prevalgono sul testo del piano, quindi vanno verificate come requisiti.
- La spec è `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (rev 25; la rev 26 la scrive il Task 15) ed è l'autorità. Consultala solo per un rischio preciso.

## Cosa dice l'implementatore
Leggi il suo report (percorso nel dispatch). Sono affermazioni non verificate: controllale sul diff. Anche le giustificazioni di design («l'ho lasciato per YAGNI») sono affermazioni. Non abbassano mai la gravità di un rilievo.

## Il diff
Leggi il file del pacchetto di revisione una volta sola (percorso nel dispatch): contiene i commit, lo stat e il diff con contesto. Non rilanciare comandi git, a meno che il file manchi. Non esplorare il codebase. Guarda codice fuori dal diff solo per valutare un rischio concreto che sai nominare, con un controllo mirato per rischio, e nomina rischio e controllo nel report. Le modifiche trasversali (contratti di funzioni, schema, stato condiviso) sono rischi legittimi: controlla i chiamanti.

Sei in sola lettura: non modificare working tree, indice, HEAD o rami. Non lanciare subagenti.

## Test
L'implementatore ha già lanciato i test e riportato le evidenze. Non rilanciare la suite. Esegui un test mirato solo se leggendo il codice ti nasce un dubbio preciso a cui nessuna esecuzione esistente risponde (sempre con `python3 -B`). Avvisi o rumore nell'output riportato sono rilievi. Se l'evidenza manca o è illeggibile, segnalalo come lacuna.

## Parte 1: aderenza ai requisiti
- **Mancante:** requisiti saltati, o dichiarati senza averli implementati, inclusi quelli di `carry.md`.
- **In più:** cose non richieste, sovra-ingegnerizzazione.
- **Frainteso:** funzionalità giusta costruita nel modo sbagliato.

Ciò che non si verifica dal diff va segnalato come ⚠️.

## Parte 2: qualità
Separazione delle responsabilità, gestione degli errori, DRY senza astrazioni premature, casi limite. Test che verificano il comportamento reale e coprono i casi limite del task. File con una responsabilità chiara. Struttura dei file del piano rispettata. Rispetto degli strati (vedi `global-constraints.md`).

Cita file:riga per ogni rilievo.

## Calibrazione
- **Important:** il task non è affidabile finché non si corregge. Rientrano qui comportamento errato o fragile, requisito mancante, duplicazione letterale di logica, errori inghiottiti, test che non asseriscono nulla.
- **Minor:** «la copertura potrebbe essere più ampia» e le rifiniture.
- Se il piano impone qualcosa che questa rubrica considera un difetto, è Important, con l'etichetta «imposto dal piano».
- Riconosci ciò che è fatto bene.

## Formato dell'uscita
Scrivi la revisione completa nel file indicato nel dispatch, poi rispondi con il verdetto e i rilievi Critical/Important in breve (meno di 20 righe). Struttura del file:
### Aderenza (✅ / ❌ con riferimenti; ⚠️ non verificabile)
### Punti di forza
### Rilievi — Critical / Important / Minor (file:riga, cosa, perché, come correggere)
### Valutazione — **Qualità del task:** Approvato | Da correggere; **Motivo:** 1-2 frasi.
