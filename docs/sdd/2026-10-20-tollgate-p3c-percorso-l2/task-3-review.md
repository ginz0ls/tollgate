# Revisione Task 3: regole pure dell'audit (9982594)

### Aderenza
- ✅ Interfacce del brief tutte presenti (`auditrules.py`: VIEWPOINTS/LABELS, SEVERITIES, outcome, is_clean, RoundJson, parse_round_json, LensState, lens_state, next_viewpoint, render_lens_status). Ordine e etichette dei punti di vista come decisione 6.
- ✅ Esito (decisione 4, glossario): `outcome` = empty se blocker+major+moderate == 0, quindi `minor` non rompe il ciclo vuoto; `is_clean` = blocker+major == 0 (auditrules.py:32-39).
- ✅ Contatore e chiusura (criterio 24, 6.2): lens_state azzera su ogni esito non `empty` (:96), chiuso se ogni contatore >= 2; 16 vuoti chiude, 15 no (test_auditrules.py, test_closed_needs_two_empty_each). `superseded` e punti di vista ignoti scartati.
- ✅ Decisione 5: `outcome` dichiarato ignorato (counts ricalcolati solo dai quattro interi); problemi = frasi fisse sui nomi dei campi, mai valori (verificato anche con un valore «segreto» nel test). Messaggio per JSON assente identico al brief. `plan_sha` richiesto solo per plan-adversarial; viewpoint atteso solo per spec-lens, null altrimenti. Ultimo JSON vince, anche se non valido (coerente con «l'ultima riga»). bool rifiutati come interi.
- ✅ next_viewpoint: ordine circolare con `last` per ultimo, salta i punti a 2, ad audit chiuso successivo di `last`; senza `last` parte da executor.
- ✅ Strati: importa solo `.report.json_candidates`; nessun DB né file.
- ✅ Prova mirata (python3 -B, non la suite): ultimo JSON non valido dopo uno valido -> non valido; chiavi extra in counts ignorate; `last` ignoto -> executor.
- ⚠️ Non verificato: l'esecuzione di `tests/run` (1456 OK in due interpreti) è solo dichiarata nel report.

### Valutazione delle tre scelte
1. Problemi per nome di campo: corretta, è proprio la decisione 5; i nomi sono costanti, quindi sicuri in un needs_you.
2. `v` non richiesto: accettabile. La decisione 5 elenca i campi vincolanti e `v` non c'è; richiederlo farebbe respingere report utili per un campo cosmetico. Costo: nessun controllo di versione futuro. Minor.
3. `counts` None se non valido: giusta, impedisce a un chiamante di usare conteggi non fidati (e `outcome()` darebbe KeyError). Il chiamante deve controllare `valid`.

### Punti di forza
Modulo piccolo, puro, test su comportamento (non su implementazione), casi limite su counts (stringa, negativo, mancante, bool, float, non dict) e sulla rotazione.

### Rilievi
**Critical / Important:** nessuno.

**Minor**
- auditrules.py:76 (`got != number`): `number` float `1.0` passa (1.0 == 1). Usare `type(got) is not int or got != number`. Impatto trascurabile.
- auditrules.py:80-83: se il chiamante passa `plan_sha=None` per plan-adversarial, un JSON senza `plan_sha` risulta valido (None == None); per `spec-lens` con `viewpoint=None` idem. Sono errori del chiamante, ma un `ValueError`/rifiuto esplicito li renderebbe visibili prima che l'hook (Task 6) li incontri. Il viewpoint atteso non è validato contro VIEWPOINTS.
- auditrules.py:88-103: un esito diverso da `empty`/`superseded` (es. stringa ignota) conta come `findings`. Coerente con la decisione 4, ma silenzioso.
- test_auditrules.py: non c'è un test sul contratto del veto «al più 2 problemi» (spetta al Task 6, non qui).

### Valutazione
**Qualità del task:** Approvato.
**Motivo:** requisiti e decisioni 3-6 rispettati, strati rispettati, scelte dell'implementatore giuste; restano solo rifiniture minori.
