# Stato dell'audit: specifica del nucleo di tollgate

Documento auditato: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`.
Metodo: skill `prd-audit` (lenti L1-L10, otto punti di vista, due cicli vuoti per ciascuno, tetto di 30 cicli). In parallelo: revisione avversariale a contesto pulito, senza le motivazioni dell'autore (`2026-10-08-revisione-avversariale-spec-nucleo.md`).
Giudice esterno (`/goal`): **da decidere con l'utente**.
Stato: **in corso**.

## Perimetro

- **Dentro**: la specifica e i documenti con cui deve essere coerente, cioè `docs/COSA-TENERE.md` (decisioni: voci 1-42, H, R1-R16, sezione 9) e `docs/RICERCA-PAPER.md`. Più i fatti esterni: documentazione di Claude Code e Superpowers 6.4.1 installato.
- **Fuori**: report di confronto (`REPORT-CONFRONTO-WORKFLOW.md`), consultato solo se un requisito vi rimanda. Sotto-progetti B, C e D, verificati solo per gli agganci che il nucleo deve lasciare.

## Criterio di gravità tarato su tollgate

| Gravità | Significato in questo progetto |
|---|---|
| **Bloccante** | Un obbligo aggirabile dall'agente senza lasciare traccia. Un effetto esterno (push, PR, deploy, db push) ripetuto o eseguito senza conferma. Stato corrotto. L'utente bloccato senza via d'uscita. Una scelta che impedisce B, C o D |
| **Grave** | Un meccanismo che non può funzionare come scritto su Claude Code o con Superpowers. Una contraddizione che l'implementatore risolverebbe a caso. Un criterio di accettazione che lascia scoperto un obbligo |
| **Rilevante** | Attrito, costo in token, falsi positivi frequenti, ambiguità che produrrà debito |
| **Minore** | Redazionale, numerazione, riferimenti |

Un rilievo rilevante o superiore azzera il contatore.

## Inventario (sezioni × esito)

| Sezione | Lenti applicate | Esito |
|---|---|---|
| 1 Scopo / 1.1 Fuori dal nucleo | — | da fare |
| 2 Decisioni | — | da fare |
| 3 Struttura | — | da fare |
| 4 Ruoli | — | da fare |
| 5 Livelli | — | da fare |
| 6 Ciclo di vita | — | da fare |
| 7 Hook | — | da fare |
| 8 Ricevute, test-guard, deroghe | — | da fare |
| 9 Revisione finale | — | da fare |
| 10 Stato | — | da fare |
| 11 tollgate.toml | — | da fare |
| 12 Errori | — | da fare |
| 13 Test | — | da fare |
| 14 Criteri di accettazione | — | da fare |
| 15 Da verificare | — | da fare |

## Matrice dei punti di vista

| Punto di vista | Cicli | Ultimo esito | Contatore vuoti |
|---|---|---|---|
| Chi esegue | — | mai applicato | 0 |
| Chi usa | — | mai applicato | 0 |
| Chi attacca | — | mai applicato | 0 |
| Chi paga | — | mai applicato | 0 |
| Chi arriva dopo | — | mai applicato | 0 |
| Lo scettico | — | mai applicato | 0 |
| Il caso limite | — | mai applicato | 0 |
| Chi integra | — | mai applicato | 0 |

## Rilievi

(vuoto)

## Fatti verificati

(vuoto)

## Scartati

(vuoto)

## Registro dei cicli

(vuoto)
