# Report Task 4 (implementatore)

Commit: 980432e «tollgate B6: fonti di rules-frontend verificate e pagina per l'utente».

## Cosa ho fatto
- `docs/profili/verifiche/frontend-fonti.md`: rapporto con le quattro tabelle («Regole e fonti», 29 righe `ok`, una per voce della `Fonte:`; «Pattern dei percorsi» 9; «Marcatori di contenuto» 4, ognuna vale per le due virgolette; «Esclusione» 6), «Parti dichiarate «scelta nostra»» e «Regole tolte dalla verifica». Generato da uno script fuori dal repo a partire dalle `Fonte:` della skill, così le celle coincidono con le voci.
- `docs/profili/frontend.md`: pagina in parole semplici (cosa sono, quando si accende con le precedenze, tabella delle 12 regole, comandi/`dod`, «Da decidere tu» con 22 voci e una proposta ciascuna, regole tolte, come rispondere, rinvio). Niente `approved`, niente «Approvata dall'utente».
- `skills/rules-frontend/SKILL.md` (decisione del controller, senza fonti nuove): R-FRONTEND-04 perde «e caratteri» (e «gerarchia dei caratteri» dalla `Fonte:`); R-FRONTEND-12 perde «carattere di sistema scelto per default» (restano viola o indaco ovunque, gradienti in eccesso, schede tutte uguali). Nessuna regola esce, numeri invariati. `templates/profiles/frontend.toml` non toccato.
- `tests/test_rules_frontend.py`: classe `RulesFrontendPageTest` (21 test) con le correzioni della decisione 16: voci per `Fonte:` (non per regola), `test_page_counts_match_skill`, `test_page_has_no_private_data` (nome utente, host, forme di token; messaggi fissi), dizionario dei numeri fino a «trenta» con errore esplicito, `test_our_choices_are_named_in_the_open_choices` (R-01, R-02, R-11), `test_page_rinvio_...` con le stringhe di B6.

## TDD
RED: `python3 -B -m unittest tests.test_rules_frontend` con rapporto presente e pagina assente -> `Ran 48 tests`, `FAILED (errors=15)` (tutti i test della pagina, FileNotFoundError). I test sul rapporto erano già verdi perché il rapporto è stato scritto prima; i controlli sulle correzioni di R-04 e R-12 (`test_removed_sources_are_not_in_the_skill`) falliscono sulla skill di c4fff87 («carattere di sistema», «gerarchia dei caratteri» presenti).
GREEN: `python3 -B -m unittest tests.test_rules_frontend` -> `Ran 48 tests ... OK`; con `test_docs`, `test_manifest`, `test_fragments` -> 139 OK.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> Python 3.11.16: 3867 test, OK (skipped=10); Python 3.13.5: 3867 test, OK (skipped=8); `exit 0` (log in `W/suite-task-4.log`).

## Scostamenti e note
1. Il brief dice 9 regole che bloccano nel report del Task 3; in realtà sono 10 (01-09 e 11). La pagina e `test_page_counts_match_skill` usano il conteggio vero (10).
2. `test_extensions_of_the_sources_are_declared_as_our_choice` esiste già in `RulesFrontendTest` (Task 3); la parte «nominato in Da decidere tu» è nel nuovo `test_our_choices_are_named_in_the_open_choices`.
3. R-FRONTEND-07: il rapporto e la pagina dicono che «Screen Readers» ammette `aria-label` e «Forms» chiede l'etichetta visibile (voci verificate nella copia della lista di controllo; la `Fonte:` della regola cita solo «Form Labels»).
4. Nel rapporto la riga di ogni regola con più parti `ok` è unica per voce; le note delle verifiche stanno nella colonna «Citazione» (l'esito è sempre solo `ok`, come richiede il test).
5. «Lo accendono N file» conta anche i file delle cartelle escluse: scritto come da carry, non riverificato nel codice di `init` (`bin/tollgate_flow/init.py:417`, `lit` da `candidates`).
6. Fatti della pagina presi dalla tabella P1-P38 senza ricontrollarli uno a uno sui test di `FrontendPrecedenceTest` (già verdi al Task 3).

## Dubbi
Nessuno bloccante. La pagina è lunga (22 punti): il controller può mostrarla per gruppi.

## Fix round 1
- Test: `assertNotIn("/home/", text)` e `assertNotIn("Approvata dall'utente", ...)` diventano `assertFalse(... in ..., "<messaggio fisso>")`; tutti gli `assertIn(x, text|section|rinvio)` della classe della pagina diventano `assertTrue(x in ..., "manca un testo atteso")`, così nessun fallimento stampa la pagina.
- `test_page_explains_the_terms`: aggiunti `**Percorso esatto**`, `**Profilo**`, `**Loader**`, `**CDN**`, `**Client delle API**`. `test_page_brings_the_open_choices_to_the_user`: aghi per P14 («finché non arriva il profilo del database»), P35 (`web/api/`), P32/P33 (`index.module.css`, «foglio di stile»).
- Pagina: glossario esteso; B7 detto nella riga delle esclusioni e al punto 10; punto 12 riscritto (costo, «parte sicura»).
- `python3 -B -m unittest tests.test_rules_frontend`: 48 OK. Suite: 3.11 e 3.13, 3867 test OK, `exit 0` (`suite-task-4-fix1.log`).

## Fix round 2
- `tests/test_rules_frontend.py`: 12 `assertRegex(testo, ...)` su testi lunghi diventano `assertTrue(re.search(...), "manca un passo atteso nel testo")`; gli `assertIn`/`assertNotIn` sulle celle del rapporto (R-04, R-12, R-01) diventano `assertTrue`/`assertFalse` con messaggi fissi. Restano solo `assertRegex`/`assertNotRegex` su una riga di tabella. Nessun cambio di comportamento.
- `python3 -B -m unittest tests.test_rules_frontend`: 48 OK. Suite: 3.11 e 3.13, 3867 test OK, `exit 0` (`suite-task-4-fix2.log`).
