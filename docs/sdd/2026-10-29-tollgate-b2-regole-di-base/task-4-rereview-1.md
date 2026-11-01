# Ri-revisione Task 4, giro di correzione 1 (8c8e6fd..1a0b6d9)

### Verdetti sui rilievi
1. **IMPORTANT, gergo non spiegato e frasi lunghe in `docs/profili/base.md`**: INDIRIZZATO. «task» spiegato alla prima comparsa (:9, «un pezzo del lavoro»), «report» (:11, «il resoconto»), «diff» (:13), «main» («ramo principale (main)», :26), «plugin» (:26, «tollgate installato in Claude Code»), «build» (:41, «la preparazione del programma»), «progetto di B» (:15, «il documento che hai approvato il 27 ottobre con le tue correzioni», data verificata in `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md:3`). La frase di decisione 10 copiata è sostituita da «la nuova versione, una volta unita al ramo principale, viene installata sul tuo computer». Le righe ora sono quasi tutte sotto ~140 caratteri (restano 2 paragrafi di ~200-240 caratteri, di 2 frasi corte l'uno); colonna «Da dove viene» accorciata.
2. **L0: l'avviso lo riceve la sessione principale**: INDIRIZZATO. `base.md:24` «Lo riceve la sessione principale di Claude Code, cioè chi lavora con te direttamente».
3. **`base-fonti.md` riga 3, licenze**: INDIRIZZATO. Ora dice che il verificatore non ha letto `LICENSES/` e che il confronto con `cmp` è dell'implementatore (le due coppie di file; `ls LICENSES` mostra entrambi i file). Resta la frase generica «la licenza è MIT o Apache-2.0» tra i criteri del verificatore, ma subito dopo il limite è dichiarato: non fuorviante.

Controlli aggiuntivi:
- `test_page_explains_what_changes`: non indebolito. Tre needle invariate; la quarta cambia in una frase più lunga e altrettanto specifica («nei lavori veri vale da quando la nuova versione, una volta unita al ramo principale (main), viene installata sul tuo computer»), che corrisponde al testo della pagina (`base.md:26`).
- Decisione 10 (`decisions.md:20`): la pagina dice ancora L1/L2 rifiuto alla prima modifica senza nota valida (:23), L0 solo avviso (:24), anche nei lavori in corso e nei task già avvisati (:25), lavori veri dalla versione unita e installata (:26). Corretto. Report: 19 test OK nominati con comando.

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minor: `base.md:9` «agente» non è spiegato (si dice solo «un agente a cui è affidato un task»); `base.md:21` «lavori medi e grandi» resta parafrasi non verificata sulla spec (già nota dalla revisione precedente, invariata).

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
