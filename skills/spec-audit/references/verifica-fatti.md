Derivato da prd-audit (sAInapse), con l'accordo dell'autore: la procedura di verifica dei fatti della lente L8.

# Verifica dei fatti

**La regola:** nessuna affermazione fattuale in un documento di progetto passa senza verifica, anche
quando sembra ovvia, e **soprattutto quando l'hai scritta tu**. Un fatto assunto è il modo più
veloce di produrre un audit sbagliato con l'aria di essere rigoroso.

## Cosa va sempre verificato

| Categoria | Esempi | Come |
|---|---|---|
| **Versioni e disponibilità** | «La libreria X supporta Y dalla versione 3» | Documentazione ufficiale, note di rilascio |
| **Capacità di API e servizi** | «L'API espone il campo immagine» | **Chiamala** e guarda la risposta |
| **Dimensioni e volumi** | «Le immagini sono leggere» | **Scaricane alcune** e misura |
| **Prezzi e licenze** | «È gratuito», «è open source» | Pagina ufficiale dei prezzi, file di licenza nel repository |
| **Date di uscita** | «Esce a settembre», «è già uscito» | Fonte ufficiale, con la data odierna sotto gli occhi |
| **Contenuto di uno standard** | «Fa parte dello standard» | L'indice dello standard, non un articolo che ne parla |
| **Prestazioni comparative** | «X è più veloce di Y» | Confronto pubblicato con numeri, non un'opinione in un forum |
| **Comportamento di una piattaforma** | «Funziona su mobile» | Documentazione ufficiale sui limiti, non l'assenza di smentite |

## Come verificare bene

**Misura invece di ragionare.** Un `curl` che restituisce l'intestazione con la dimensione del file
chiude una discussione che dieci argomentazioni lasciano aperta. Preferisci sempre la verifica
eseguibile a quella letta.

**Vai alla fonte primaria.** La documentazione ufficiale batte l'articolo che la riassume, che batte
il messaggio nel forum. Un articolo può essere vecchio di due anni senza dichiararlo.

**Controlla la data di tutto.** Un fatto vero nel 2024 può essere falso oggi. Quando una fonte non
ha data, trattala come inaffidabile.

**Distingui «non l'ho trovato» da «non esiste».** Sono cose diverse e vanno scritte in modo diverso
nell'audit. La seconda richiede una fonte che lo affermi.

**Verifica anche i fatti che ti fanno comodo.** La tentazione è controllare solo ciò che sembra
sbagliato: così passano tutti gli errori che confermano quello che pensavi già.

## Come scrivere un fatto verificato nel documento

Un fatto verificato porta con sé **fonte e data**, così fra sei mesi si sa cosa riverificare:

```markdown
- L'API espone le immagini solo per le creature (verificato l'11/08/2026: 334 voci,
  es. /api/images/monsters/aboleth.png, HTTP 200, 739 KB)
- Le immagini pesano da 712 KB a 2,0 MB: circa 300 MB per l'intera raccolta, misurati
```

Un fatto **non** verificato va marcato come tale, non lasciato indistinguibile dagli altri:

```markdown
- La libreria dovrebbe supportare il tracciato variabile (non verificato, da controllare
  prima di sceglierla)
```

## Rilievi tipici prodotti da questa verifica

- Un'affermazione vera al momento della scrittura e falsa adesso
- Una capacità data per scontata che il servizio non ha
- Un volume di dati sottostimato di due ordini di grandezza
- Una licenza incompatibile con l'uso previsto
- Una data di uscita passata, o spostata
- Una libreria abbandonata da anni presentata come scelta corrente
