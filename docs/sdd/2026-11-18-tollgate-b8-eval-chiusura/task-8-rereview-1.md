# Task 8, ri-revisione del giro di correzione 1

### Verdetti sui rilievi
**I1. La spec 14 diceva «I nove casi sono `evals/s1-…`» sotto un elenco di dodici**: INDIRIZZATO.
- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:1654` ora dice «I casi `spec` sono dodici: i nove di P5, `s1`-`s9`, e i tre di B8, `s10`-`s12` (descritti in «Casi di B8», sotto). I nove di P5 sono …». La lista dei nove resta, correttamente attribuita a P5; il resto del paragrafo è invariato (diff di una sola riga).
- Grep di «nove casi», «9 casi», «nove eval/scenari» nella spec: nessun'altra occorrenza sullo stato di oggi (le altre corrispondenze di «nove» sono «novembre»; riga 4 inclusa). In `docs/uso/`: nessuna occorrenza di «nove» né «9 casi». Nei due documenti di catalogo/profili (`2026-10-27-tollgate-b-profili-design.md`, `2026-10-08-tollgate-profili-verticali.md`): nessuna occorrenza. Restano «9 casi»/«i nove casi» solo in piani e `docs/sdd/` di P5 (frasi storiche, fuori ambito per definizione) e in `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md:33,395` («I 9 casi … di P5», «Δ medio dei nove casi della spec»), che parlano di P5 e sono storici.
- Il report (Fix round 1) nomina `tests.test_docs` e la suite `exit 0` su 3.11 e 3.13; coerente con un diff di sola documentazione.

### Danni nuovi nel diff della correzione
Nessuno. Il diff è una riga; la frase «tre di B8, `s10`-`s12`» coincide con l'elenco 10-12 sopra e con «Casi di B8».

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
