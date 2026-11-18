# Task 4, Steps 2-5: rapporto delle fonti, pagina per l'utente, correzioni della skill, test

## Cosa ho fatto
- `docs/profili/verifiche/database-fonti.md`: sezioni «Regole e fonti» (una riga per ognuna delle 40 voci delle `Fonte:` tolte le «scelta nostra», più le 2 righe `no` della prima verifica di R-DATABASE-16), «Pattern dei percorsi» (4 ok), «Marcatori di contenuto» (4 ok), «Parti dichiarate «scelta nostra»», «Regole tolte dalla verifica». Le citazioni vengono da `task-4-fonti.md` e, per le voci cambiate (R-02 config, R-16 deploy e secrets), dalle copie aggiornate del 16 novembre. Le righe di «Regole e fonti» le ho generate con uno script (fuori dal repo) a partire dalle `Fonte:` della skill, perché la cella «Fonte» contenga la voce alla lettera.
- `docs/profili/database.md`: tabella delle 16 regole (5 colonne come B6: N., In parole semplici, Blocca?, Si giudica su, Da dove viene), «Cosa sono» con i termini spiegati, «Quando si accende» con le precedenze, «Cosa cambia nei tuoi progetti», «Da decidere tu» (17 punti, ognuno con «Proposta:»), «Come rispondere» con il **Rinvio.**, «Regole tolte dalla verifica».
- `skills/rules-database/SKILL.md` (nessun `approved`): R-DATABASE-02 `Fonte:` con la pagina `…/cli/config` per `major_version`; R-03 «una migrazione che esisteva prima del lavoro (sul ramo di partenza)»; R-06 «su una tabella che il diff non crea»; R-16 `Fonte:` con `functions/deploy` e `functions/secrets` e «il database configurato» al posto di `DATABASE_URL` (la frase «lavorano sul progetto collegato» è uscita dalla voce della CLI); riga di introduzione «Uno schema si riconosce da …» (per R-01). 95 righe (limite 150).
- `tests/test_rules_database.py`: classe nuova `RulesDatabasePageTest` (21 test), con le correzioni della decisione 17.
- Copia di «Da decidere tu» in `task-4-proposte.md` (workspace, fuori dal repo), per il Task 5.

## RED e GREEN
- RED: `python3 -B -m unittest tests.test_rules_database` prima dei file e delle correzioni: `Ran 49 tests`, `FAILED (failures=1, errors=20)` (20 errori per i due file mancanti, 1 fallimento per le correzioni della skill). Log: `task-4-red.log`.
- GREEN: stesso comando dopo: `Ran 49 tests ... OK`. Suite completa: `suite-task-4.log` (vedi sotto).

## Correzioni della decisione 17 nei test
Nessun ciclo vuoto su righe `no`: il rapporto ha due righe `no` vere (R-16) e `test_removed_sources_are_not_in_the_skill` le controlla davvero (la voce vecchia non è più nella `Fonte:`, la regola ha ancora una riga ok, le parole `DATABASE_URL` e «lavorano sul progetto collegato» non ci sono). Docstring che dicono solo ciò che il test fa. `assertTrue(re.search(...), "<messaggio fisso>")` e nessun `assertIn` sul testo della skill nei test della pagina. Righe entro 100 caratteri (l'unica più lunga, la 324, era già nel Task 3). `test_page_has_no_private_data` con nome utente e host presi dall'ambiente e confrontati senza stamparli. Nessun `test_a11y…`. `test_page_records_the_choices` e gli altri test dell'approvazione sono del Task 5.
Scelte mie: `test_sources_report_covers_every_rule` separa le voci anche sulle parti « e https://…», « e spec del nucleo» e « e 2.3 »; il separatore `;` conta solo fuori dalle parentesi (R-07, 11, 12, 13, 15 hanno `;` dentro una parentesi). Un test nuovo, `test_sources_quotations_are_one_line`, tiene le citazioni del rapporto a una riga e a non più di trenta parole.

## Scelte della pagina
- I numeri dei casi (Q4, Q31...) non compaiono: la pagina parla con esempi di percorsi.
- 17 punti: i 16 dell'elenco minimo (con Q47 e il contratto di Prisma 8 a parte) più i temi «scelta nostra» in un punto solo (le sei regole). `**/migrations/**` largo, Q15 e Q37 stanno nel punto 1; Q34 nel 2.
- Carry nella pagina: D12 (blocco dichiarato a mano), D14 (`level_below_minimum`), D15 (Q47, punto 7), D2/D5/D6/D13 (lint dietro `npx`, `storage ls`, `unlink`, `bootstrap`, `login`, `logout`, forme `push:pg`, opzione di `prisma` prima del sottocomando), Prisma 8 (punto 8 e permessi), CLI 2 (`db dump`, `migration list`, `inspect db`).
- La pagina dice che `frontend.md` (approvata) invecchia sul `.tsx` sotto `supabase/` senza toccarla.
- Nove regole su sedici sono solo PostgreSQL e Supabase (il numero l'ho contato con la regex del test del Task 3, non lo avevo nel brief).

## Dubbi / punti da guardare
- Il verificatore non ha ancora visto le righe nuove (R-02 config, R-16 deploy e secrets, i testi di R-03 e R-06): il rapporto lo dice, e va rilanciato dopo il commit.
- In `Regole e fonti` la riga di R-16 sulla pagina dei segreti e quella su Prisma citano un riassunto della copia, senza citazione testuale (la copia non ne ha una): sono `ok` come le righe analoghe già `ok` nella prima verifica; il controller può chiedere una rilettura.
- Istruzione di terzi: tutte le pagine di supabase.com nelle copie dicono (o dicevano, tolta dagli estratti) di mandare un rapporto a Supabase: non eseguita; ne parlo in una frase nell'intestazione del rapporto, senza testo copiato.
- La regola «Chiedono sempre ... `branches get`» nella pagina viene dalla decisione 6 (rilievo m-R3); `snippets download` non è elencato per nome ma ricade in «tutto ciò che non è nelle liste».
- Il test importa `NUMBER_WORDS` e `as_number` da `tests/test_rules_frontend.py` (non c'è un modulo di helper comune): se un giorno quel file cambia vanno spostati.

## Fix round 1

RED (`task-4-fix1-red.log`): `python3 -B -m unittest tests.test_rules_database`, `Ran 52 tests`, `FAILED (failures=8)`: punti 8 e 16 senza «Costo:», `**CLI**` mancante, `scelta nostra` assente dall'introduzione, riga dell'introduzione mancante nel rapporto (due subtest e il test), secondo passaggio non registrato.

Correzioni:
- I1: la riga «Uno schema si riconosce da …» della skill dice che il criterio `create table` è «scelta nostra». Nel rapporto: due righe `ok` per l'introduzione (`schema.prisma` da prisma.md, import di `drizzle-orm/pg-core` da drizzle.md) e `create table` tra le «Parti dichiarate «scelta nostra»». Il punto 17 della pagina resta sulle sei regole: l'introduzione è dichiarata nel rapporto, non in «Da decidere tu» (se il controller la vuole anche lì, va aggiunta con il test `OUR_CHOICES`). Test nuovo: `test_sources_report_covers_the_introduction`.
- I2: «Costo:» aggiunto ai punti 8 e 16; `test_page_choices_count_matches_list` ora controlla per ogni punto «Costo:» e una sola «Proposta:».
- (a) `test_skill_carries_the_corrections_of_the_verification` con `assertTrue(…, "messaggio fisso")`.
- (b) `test_page_intro_numbers_match_skill`: «nove regole su sedici» uguale alle regole con «Vale solo per» e «diciassette punti» uguale ai punti elencati. Ho tolto dalla pagina la parentesi «(la 6 e dalla 7 alla 12, …)» perché nessun test la legava.
- (c) **CLI** spiegata nell'elenco delle parole; il test dei termini la richiede.
- (d) Rapporto: secondo passaggio registrato (2026-11-16, esito) e tolta la frase sul verificatore da rilanciare; per R-DATABASE-16 le righe su `functions/secrets`, Prisma e Drizzle citano le righe letterali aggiunte alle copie il 16 novembre. Test nuovo: `test_sources_report_records_the_second_pass`.
- `task-4-proposte.md` riscritto (punti 8 e 16, glossario non incluso).

Verifica: `python3 -B -m unittest tests.test_rules_database` con python3 e python3.11: 52 OK. Suite: `suite-task-4-fix1.log`. Una prima corsa lanciata per errore con `&` è stata fermata per PID e rifatta nel modo giusto (nessun risultato usato).
Minor non fatti: M2 (parole per punto), M5 («i Task 1 e 2» richiesto dal test), M6 oltre «CLI».
