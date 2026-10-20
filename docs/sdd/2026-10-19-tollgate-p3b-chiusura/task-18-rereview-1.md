# Task 18 - Ri-revisione del giro di correzione 1 (78705e2..a29f588)

### Verdetti sui rilievi

- **Important 1: registro di P3b nello «Stato» punta a `.superpowers/sdd/...`**: INDIRIZZATO. Piano principale, paragrafo «Stato»: ora «registro dell'esecuzione in `docs/sdd/2026-10-19-tollgate-p3b-chiusura/`», stessa forma di P2/P3a; nessun `superpowers/sdd` residuo nel file.
- **Important 2: spec 6.5 «Dettagli di sync» incompleta (fase `review`; push nostro riscritto)**: INDIRIZZATO. Spec 6.5 ora dice «nelle fasi `execution` e `pr_open`, e in `review` se la PR esiste già» (`bin/tollgate_flow/sync.py:165-166`) e «salvo che il commit remoto sia un nostro push poi riscritto, noto dagli eventi `commit`, o sia già antenato di HEAD» (`sync.py:60-76`: `is_ancestor(remote, head)` e `remote in _known_commits`). Fedele al codice.
- **Minor spec 11.4: giri 4 e 5 `inherit`**: INDIRIZZATO. Ora «dal quarto in poi (fino a 8 con `approve rounds`)».
- **Minor spec 12.4: manca la fase `plan` per L2**: INDIRIZZATO. Ora «L2 senza spec-approval `spec_audit`, con spec approvata e senza piano valido `plan`, con il piano ma senza `plan-approval.md` `approval`, con entrambi `execution`», identico a `bin/tollgate_flow/adopt.py:194-206` (`_phase`).
- **Minor «Stato»: «P3b chiuso» prima della revisione finale**: INDIRIZZATO. Aggiunto «(revisione finale del ramo in corso)».

Il report elenca i controlli (suite 1396 OK su 3.11 e 3.13, `ResourceWarning`); la correzione è solo testo, quindi non servono test mirati.

### Danni nuovi nel diff della correzione
Nessuno. Il diff tocca solo le due righe del piano e tre paragrafi della spec; il resto delle righe non cambia.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
