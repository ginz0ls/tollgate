# Revisione Task 15 - `checkpoint.next_step` per le fasi di chiusura (505bd6d..399b2c0)

### Aderenza
- ✅ Tetti (m12, decisione 13): `checkpoint.py:_cap_step` (r.44-50) prende i blocchi aperti con prefisso "giri di correzione esauriti sul task" o `reviews.CAP_REASON` e propone `approve rounds <n>`, `resolve <id>`, `abandon #N`. Coerente con `actapply._approve_rounds` (gestisce entrambi i tipi di tetto). Precede ogni altro passo.
- ✅ Revisione preparata: con `review_sha`, `review_code` e verdetto assente indica il revisore (`reviewer_type` o `DEFAULT_REVIEWER`) e il brief; `task review-prepare k` solo se non preparata o brief assente (r.131-140). Nessun tipo/costante inventata: `prof.DEFAULT_REVIEWER` esiste (`profiles.py:10`).
- ✅ `pr_open` con PR, testo identico al vincolo; `pr_open` senza PR come da carry C13 (r.67-69).
- ✅ Fase `review` per stadio dell'ultimo ciclo (nessun ciclo/superseded, review, verify, ok, needs_you); L0: `finish open-pr`. I comandi del programma passano da `program_command` (`prog`), niente percorso nudo; slash command letterali.
- ✅ `needs_fix` -> `task start --from-findings <n>` solo se mancano task `cycle:<n>` e ci sono rilievi bloccanti aperti (C10); `ok` in execution -> `/tollgate:finish`.
- ✅ Scostamento «ciclo `needs_fix` con task `cycle:<n>` già presente -> finish»: valido. Un task di correzione non ancora `done` è indicato prima, perché `next_step` sceglie il primo task `state <> 'done'` (r.108-110) e `_closing_step` si raggiunge solo con tutti i task `done`; quindi nessun loop e nessun salto. Corretto.
- ✅ Scostamento «riga 133»: accettabile, la tabella della skill execute è il riferimento giusto per l'allineamento; il comportamento corrisponde.
- ✅ Strati: `checkpoint.py` importa `tollgate_analysis.profiles` (ammesso a `tollgate_flow`), nessun import vietato. Test esistenti di `next_step` invariati nel comportamento (ramo task invariato, solo aggiunta prima del fallback).
- ⚠️ Non rilanciati i test: affidamento al report (18 OK in test_checkpoint, 1383 OK in `tests/run` su 3.11 e 3.13).

### Punti di forza
- Cambiamento chirurgico: la funzione conserva la struttura, con `_closing_step` isolato e testabile.
- Test con RED/GREEN dichiarati, uno per ogni stadio e tetto, più verifica trasversale della forma di `program_command`.
- Il tetto è controllato per primo, quindi nessun passo fuorviante mentre il lavoro è bloccato.

### Rilievi
**Critical:** nessuno. **Important:** nessuno.

**Minor**
1. `checkpoint.py:57-64` (`_review_brief`): sceglie il `review-<k>.md` con k massimo nella cartella, ma k è un contatore globale dei file `review-*.diff` (`taskcmd.py:311`), non il numero del task. Funziona perché i task si rivedono in sequenza e l'ultimo preparato è quello corrente; resta un'euristica (se rimane un brief più recente di un altro task, indicherebbe quello). Il test `test_prepared_review_not_reprepared` usa review-1/review-2 per il task 1 e fissa questo comportamento. Rimedio: persistere il percorso del brief nella riga del task, o documentare l'ipotesi nel docstring.
2. `checkpoint.py:21` `CAP_PREFIXES` duplica la conoscenza dei motivi già in `CAPS` (r.19) e in `actapply.FIX_CAP`. Se un motivo cambia vanno aggiornati tre punti. Rimedio: derivare `CAP_PREFIXES` da `CAPS` escludendo "budget superato".
3. `_cap_step` restituisce solo il primo blocco quando ce ne sono più di uno; `approve rounds` in quel caso rifiuta ("più tetti insieme") e rinvia a `resolve <id>`. Il testo proposto («approve rounds <n>») in quel caso porterebbe a un rifiuto. Caso raro; basta nominare il blocco id come già fatto.
4. `next_step` ora dà `TypeError` se il lavoro non esiste (`item` None); prima falliva comunque solo nel ramo senza task. I chiamanti passano un lavoro esistente (`checkpoint.py:180`): nessun impatto pratico.
5. Il budget ("budget superato") non ha un passo dedicato: preesistente, fuori ambito.

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni del controller (C10, pr_open senza PR, decisione 13) rispettati; gli scostamenti dichiarati sono corretti, il task di correzione non `done` precede il rinvio a `/tollgate:finish`. Restano solo rifiniture minori.
