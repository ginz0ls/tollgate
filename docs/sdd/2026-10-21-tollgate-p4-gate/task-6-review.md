# Revisione Task 6: commento del gate e tetto del corpo della PR (6279719)

Prove mirate (`python3 -B`, script nello scratchpad, nessuna modifica al repo): una voce rossa con `text` di 100.000 caratteri, `render_guard` con 60 problemi da 5.000, 4.000 voci per gruppo con `data` da 5.000 più `watch` ed `errors`, e un `Item.text` ostile.

### Aderenza
- ✅ D17c: `comment.MAX_BODY` è lo stesso oggetto di `prbody.MAX_BODY` (`comment.py:11`, test `assertIs`, `test_gate_comment.py:47`).
- ✅ D19: `render(sha, ev)` senza `plan_diff` e `approval_diff` (`comment.py:90`).
- ✅ `prbody.render` con tetto totale: il blocco resta intero e ultimo; `prblock.parse` lo trova (`rfind` dell'ultima apertura; le sezioni passano da `defuse`, quindi non contengono `<!-- tollgate `). Casi verificati dai due test di `test_prbody.py`.
- ✅ Deviazione 1 (tetto 60 invece di 30 nel taglio): corretta. La nota «… (troncato: altre N voci omesse)» è lunga ~40 caratteri e con 30 verrebbe troncata a «… (troncato)». Il comportamento resta monotono: le voci tolte sono dichiarate.
- ✅ Deviazione 2 (`defuse` estratta): comportamento di `neutralize` invariato (stesso ordine: taglio, defuse, recinto). Il refactoring è giusto; è l'uso di `defuse` da solo per `Item.text` a non bastare (rilievo I-1).
- ✅ Deviazione 3 (marcatore letterale): corretta, `tollgate_gate` non può importare `fixtask` (strati); l'uguaglianza è fissata da `test_marker_matches_fixtask`.
- ❌ Decisione 14: il marcatore deve essere `<!-- tollgate-verdict sha=<40 esadecimali> -->` e quello della guardia `<!-- tollgate-guard sha=<sha> -->`; il codice scrive `<!-- tollgate-verdict <sha> -->` (senza `sha=`). Vedi I-4.
- ✅ Il ValueError su SHA non valido, i tre gruppi nell'ordine voluto, `<details>` solo con voci informative.

### Punti di forza
- Tetto a due fasi (accorcia, poi toglie dalla coda) con nota esplicita; test dei casi «voci omesse» in entrambi i moduli.
- `test_neutralized` verifica davvero i recinti (apertura/chiusura, lunghezza maggiore di ogni sequenza interna), `-->` unico, `<!--` unico e assenza di menzioni.
- `marker_sha` richiede 40 esadecimali minuscoli ed è ancorato a inizio commento.
- Caso «molti gruppi» verificato: 4 gruppi × 4.000 voci da 5.000 caratteri danno 50.412 caratteri, entro il tetto.

### Rilievi

**Important**

- **I-1. `Item.text` non è neutralizzato e contiene testo non fidato** (`comment.py:36`, produttore `evaluate.py:433` e `testguard.py:188`). Il commento passa `Item.text` solo da `defuse` (menzioni e commenti HTML), senza recinto. Ma `evaluate.py:433` scrive `f"{v.detail} ({v.waiver_type})"` e per `test_id_missing` `v.detail` è `"test della base assenti o saltati: " + ", ".join(missing)`: gli identificativi sono titoli di test letti dal codice della PR (in JS, `testids.py:51-56`, stringhe arbitrarie). Provato: un `text` con `a\n```\n</details>\n@x --> <!--` arriva al commento con il recinto aperto e `</details>` attivo (solo `@`, `-->` e `<!--` sono spenti). Un titolo di test può rompere la struttura del commento (chiudere `<details>`, aprire un recinto che inghiotte il resto, titoli e link). Contraddice il vincolo globale «testo non fidato nei commenti in un recinto» e D19 («il testo non fidato sta solo in `Item.data`»). Correzione: in `evaluate.py:433` il testo diventa solo la parte scritta da tollgate («test della base assenti o saltati») e gli identificativi vanno in `data` (come già a `evaluate.py:318-320`); aggiungere in `test_gate_comment.py` un test con `Item.text` ostile non necessario se `text` resta solo dei nostri, ma un test su `evaluate` che nessun `v.detail` porti ids. In alternativa difensiva, in `_item` rendere `text` su una sola riga (`" ".join(text.split())`) e togliere i backtick e i `<`. La correzione di `evaluate.py` è del Task 5: va nel giro di correzione di quel task o in questo con il controller.
- **I-2. `Item.text` senza tetto: `render` può superare `MAX_BODY`** (`comment.py:36`, `:96-101`). `_item` non applica `cap` al `text`. Provato: una voce rossa con `text` di 100.000 caratteri dà un commento di 100.166 (> 60.000 e > 65.536 di GitHub: la scrittura fallirebbe). Dato che `text` può portare gli id di I-1, il caso è raggiungibile. In più la fase finale (`while keep > 1`, `:97-100`) si ferma a `keep = 1` e restituisce comunque `body` troppo lungo senza dirlo. Correzione: applicare `_cap(text, cap)` in `_item`; a fine `render` se `len(body) > MAX_BODY` cadere su un testo minimo valido (marcatore, titolo, «commento troncato: N voci») invece di restituire il corpo troppo lungo; stessa garanzia in `prbody.render` (`prbody.py:84`, torna `body` oltre il tetto se il blocco o le voci a `keep = 1` non entrano).
- **I-3. `render_guard` senza tetto totale** (`comment.py:111-118`). Tiene 50 problemi da 2.000 caratteri: 100.842 caratteri provati con 60 problemi da 5.000. Supera 65.536, quindi il commento della guardia non si scrive proprio quando lo stato è rosso. Il brief chiede il tetto del commento del gate; la guardia ha la stessa esposizione (i problemi sono testo non fidato: percorsi dei workflow). Correzione: riusare la stessa scala di tagli di `render` (o un tetto per voce di 500 per 50 voci = 25.000) e verificare `len <= MAX_BODY`; test con 1.000 problemi da 5.000.
- **I-4. Marcatore senza `sha=`, contro la decisione 14** (`comment.py:17-18,30,50,114`). La decisione 14 scrive `<!-- tollgate-verdict sha=<40 esadecimali> -->` e `<!-- tollgate-guard sha=<sha> -->`. Il formato è internamente coerente, ma Task 7, 9 e 13 e il controller leggono la decisione: un commento prodotto da altro codice o dai test dei task successivi nella forma `sha=` non verrebbe riconosciuto da `marker_sha`. Correzione: scrivere `sha=` nei due marcatori e in `_MARKER`, aggiornare i test; oppure far correggere la decisione 14 dal controller. Va chiuso ora, prima del Task 13.

**Minor**

- **M-1.** `comment.py:20` duplica la scala `_CAPS` di `prbody.py:15` (`(MAX_TEXT, 1000, ... 30)`): una sola definizione (`prbody.CAPS`) e il comment la importa. Stessa duplicazione della logica «accorcia, poi togli dalla coda» in due moduli: accettabile per ora, ma un helper in `prbody` la eviterebbe.
- **M-2.** `comment.py:44` e `:70` usano `prbody._cap`, un nome privato di un altro modulo. Meglio renderlo pubblico o passare da una funzione pubblica.
- **M-3.** `test_gate_comment.py` non copre i casi limite di I-1, I-2 e I-3 (voce sola enorme, guardia con molti problemi, testo ostile in `text`). `test_neutralized` non mette nulla di ostile in `Item.text`, per questo non vede I-1.
- **M-4.** `defuse` spegne `-->` e `<!--` ma non `--!>` (anch'esso chiude un commento HTML nel parser HTML5). Oggi non importa perché nessun testo finisce dentro un commento; da ricordare se un campo entrerà in un marcatore.

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** la struttura, il tetto sul corpo della PR e le tre deviazioni dichiarate sono corretti, ma `Item.text` arriva al commento senza recinto con titoli di test non fidati (I-1), il tetto non regge con una voce enorme né con la guardia (I-2, I-3) e il marcatore diverge dalla decisione 14 (I-4).
