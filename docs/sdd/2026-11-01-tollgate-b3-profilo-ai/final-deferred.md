Task 1: minor (deferred): brief.py — inciso aggiunto alla frase del rinvio 185 non richiesto dal brief (innocuo).
Task 1: minor (deferred): taskcmd.py — un `concerns` non stringa è reso con str() (nessun difetto reale).
Task 2: minor (deferred): fragments.rules() con skill assente dà ([], []) senza segnale: il Task 3 la chiama solo dopo approved().
Task 2: minor (deferred): research.area_rules — una riga `R-AI-NN [blocca]` senza testo dopo non è bloccante (come base_rules): ogni regola del Task 5 ha testo dopo [blocca].
Task 2: minor (deferred): tests/test_fragments.py:129 l'helper tomlout_str duplica l'escape.
Task 2: minor (deferred): tomlout.table divide `name` sui punti (una parte con un punto non si esprime; oggi non serve).
Task 3: minor (deferred): un repo senza file è ora «profili non valutati» (messaggio esplicito).
Task 4: minor (deferred): fragments.load e il filtro approved duplicati tra propose (init.py:661-663) e profile_blocks.
Task 4: minor (deferred): tests/test_init.py — il test del grep fallito di un frammento è di guardia (verde subito).
Task 5: minor (deferred): R-AI-11 (Agno, id esplicito) è un obbligo derivato da fatti, non detto da una pagina: lo giudica il verificatore e lo conferma l'utente.
Task 5: minor (deferred): «stabile» per OpenAI e OpenRouter è un'inferenza del redattore: al verificatore.
Task 6: minor (deferred): test_page_explains_what_changes — la regex su R-AI-01 «solo diff» è soddisfatta dal capoverso di «Cosa sono», non dalla riga della tabella.
Task 6: minor (deferred): docs/profili/ai.md «Quando si accende» — frase su --update un po' ridondante.
Task 7: minor (deferred): «Come rispondere» rinominata «Se vuoi cambiare qualcosa» (non richiesto, innocuo).
Task 8: minor (deferred): gli id R-AI-03…08 sono scritti a mano nei testi degli agenti (il test li confronta con la skill); due assertIn fissano frasi esatte.
Task 9: minor (deferred): il test di registra non copre la deduplica dello stesso sid né la sessione senza cwd.
Task 9: minor (deferred): test_flowreg_trascrizioni_skips_an_unsafe_session_id mette la cartella estranea in tmp/estranea invece di tmp/.claude/estranea: l'assertNotIn passerebbe anche senza il controllo (il test regge per la riga «session_id non valido»).
Task 9: minor (deferred): il controllo del cwd con startswith("/tmp/tollgate-b1/") accetta /tmp/tollgate-b1/../x (nessun impatto reale).
Task 10: minor (deferred): il nome del rapporto porta la data del piano (2026-11-01), la prova è del 2 novembre (detto nel rapporto).
Task 11: minor (deferred): piano principale, sezione 11, riga «2, obiettivo 3»: test_page_lists_every_rule attribuito a test_fragments.py, sta in tests/test_rules_ai.py.
Task 11: minor (deferred): piano principale — conteggi delle fonti (46/45/1, 20/19/1) diversi dalle tabelle di docs/profili/verifiche/ai-fonti.md (48 righe di regole: 45 ok, 3 no; 19 marcatori ok; `from "openai"` solo tra le voci tolte).
Task 11: minor (deferred): DetectTest esiste anche in tests/test_prstate.py (omonimia; attribuzione corretta).
Task 11: minor (deferred): il rinvio sulla radice vera del plugin nei test esistenti non è ripetuto nel blocco B4-B7.
