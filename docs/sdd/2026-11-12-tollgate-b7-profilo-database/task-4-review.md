# Revisione del Task 4 (commit a906346, pacchetto 4603ade..a906346)

Letti: regole del revisore, brief con carry e cautele, decisioni, vincoli globali, le due verifiche delle fonti (`task-4-fonti.md`, `task-4-fonti-2.md`), il report dell'implementatore, il pacchetto. Controlli mirati fatti: tutte le citazioni «…» del rapporto cercate (normalizzate) nelle copie di `fonti/database/` e nelle spec; il codice di `bin/tollgate_analysis/bash.py` per i permessi che la pagina elenca; `git status` pulito; grep di dati privati; `suite-task-4.log` (4017 test, `OK (skipped=11)`, `exit 0`). Nessun test rilanciato, nessuna rete.

## Aderenza

- ✅ File toccati: solo i quattro del task. Nessun file approvato toccato (`frontend.md`, skill e rapporti degli altri profili intatti). Nessun `approved` in `skills/rules-database/SKILL.md` (95 righe, limite 150).
- ✅ Rapporto delle fonti: una riga per ogni voce di ogni `Fonte:` (tolte le «scelta nostra»), generata dalla skill e controllata da `test_sources_report_covers_every_rule`. Sezioni «Regole e fonti», «Pattern dei percorsi» (4 ok), «Marcatori di contenuto» (4 ok), «Parti dichiarate «scelta nostra»», «Regole tolte dalla verifica». Le due righe `no` di R-DATABASE-16 sono storia vera e il test le controlla davvero.
- ✅ Citazioni: tutte le citazioni «…» sono nelle copie o nelle spec. Le uniche quattro non trovate («una migrazione esistente non si tocca», «da PostgreSQL 15», «sul database configurato», «il database configurato») sono parole del rapporto, non citazioni. Tutte stanno su una riga (test dedicato, massimo 30 parole). Nessuna frase della skill è copiata dalle fonti.
- ✅ Correzioni della skill come dice carry: R-02 con la pagina `cli/config`; R-03 «esisteva prima del lavoro (sul ramo di partenza)», ancora giudicabile sul diff; R-06 «su una tabella che il diff non crea»; R-16 con `functions/deploy` e `functions/secrets` e «il database configurato», senza `DATABASE_URL`. Il test le fissa.
- ❌ Introduzione della skill (`skills/rules-database/SKILL.md:12`, riga «Uno schema si riconosce da …»): il secondo verificatore dà `no` al criterio «`create table` in un file `.sql`» (`task-4-fonti-2.md`, riga «Introduzione»: nessuna copia lo dice). Il commit non cambia né la riga né il rapporto: `database-fonti.md` non ha nessuna riga per l'introduzione e nessuna dichiarazione «scelta nostra». Il report dell'implementatore non lo segnala. Vedi I1.
- ✅ Pagina: tabella a cinque colonne (come B6), 16 righe con id, «Blocca?» e «Si giudica su» uguali alla skill (test). «Sono sedici regole», «Quindici di queste bloccano»: corretti (R-08 è la sola senza `[blocca]`). «Nove regole su sedici (la 6 e dalla 7 alla 12, la 14 e la 15)»: corretto sulla skill, ma non testato (M1). «Su diciassette punti»: uguale ai punti elencati (test).
- ✅ «Cosa cambia»: L2, specialista `final-database`, D14 (`level_below_minimum`, esiste in `bin/tollgate_gate/evaluate.py:543`), D12 (`init --update`, `min_level`, `checklist`), `dod` vuoto con esempio e avviso su `--remote`/`--linked`/`--db-url`, effetti di Supabase con i costi di D2, D5, D6 (`npx eslint supabase --fix`, `storage ls`, `unlink`, `bootstrap`, `login`, `logout`), CLI 2 (`db dump`, `migration list`, `inspect db`), Prisma/Drizzle incluse le forme `push:pg`, Prisma 8 e l'opzione prima del sottocomando, `.tsx` sotto `supabase/` (P14), `.sql` negli altri profili. Le liste dei permessi coincidono con `bash.py:1004-1013` e `SUPABASE_LOCAL`/`SUPABASE_READS` (`bash.py:1057-1064`).
- ✅ «Da decidere tu» copre l'elenco dello Step 3 e le voci di carry: `**/migrations/**` largo, Q15, Q37 (punto 1); Q34 (2); `**/schema.*` (3); Q11, Q23, Q36, Q42, Q43 (4); Q44 (5); Q4, Q31, Q32, Q40 (6); Q47 (7); contratto di Prisma 8 (8); Q12, Q21, Q38 (9); Q33, Q39 (10); Q5 (11); Q35, Q41 (12); permessi di Prisma incluso `migrate dev` (13); `database-reviewer` (14); `dod` (15); Alembic (16); «scelta nostra» (17, sei regole, uguali a quelle della skill). Ogni punto ha «Proposta:».
- ❌ Il costo manca in due punti: il 8 (Prisma 8) e il 16 (Alembic e Rails) non hanno nessuna riga «Costo:». Il brief e la regola dell'utente chiedono per ogni scelta proposta e costo. Vedi I2.
- ✅ Nessun dato privato: grep di nome utente, `/home/`, host, token sui due file della pagina e del rapporto pulito. Nessun testo di terzi copiato; l'istruzione di mandare un rapporto a Supabase è segnalata in una frase del rapporto e non eseguita.
- ✅ Test: classe `RulesDatabasePageTest`, 21 test, decisione 17 rispettata: nessun ciclo vuoto, docstring che dicono solo ciò che il test fa, messaggi fissi, righe entro 100 caratteri (l'unica più lunga, la 324, è del Task 3), `test_page_has_no_private_data` con nome utente e host confrontati senza stamparli, nessun `test_a11y…`, nessun test dell'approvazione. I test `skip_if_approved` fanno saltare le parti che valgono solo prima dell'approvazione.
- ⚠️ Non verificabile dal diff: la frase della pagina «Con la CLI 2 … potevano leggere il progetto collegato» viene dalla memoria del controller (`progress.md:12`: «da verificare, non da una pagina»); è come la vuole carry ma la pagina la dà per fatto. La seconda verifica delle citazioni di R-02, R-03, R-06 e R-16 è stata fatta sul commit; il rapporto dice ancora «un nuovo verificatore le rilegge dopo il commit» (va aggiornato dal controller quando chiude).

## Punti di forza

- Il rapporto è costruito dalla `Fonte:` della skill e un test lo lega alla skill voce per voce: se una `Fonte:` cambia, il rapporto non regge più.
- La storia delle due righe `no` resta nel rapporto, e `test_removed_sources_are_not_in_the_skill` prova che la skill non ne porta le parole.
- La pagina parla con esempi di percorsi e non con i numeri dei casi (Q4, Q31, …), e spiega ogni termine nuovo la prima volta.
- Le proposte della pagina sono scritte per essere accettate o corrette punto per punto, con la conseguenza concreta in parole semplici.
- Le correzioni di R-03 e R-06 sono giudicabili sul diff e sul report, come chiedeva carry.
- Il separatore `;` conta solo fuori dalle parentesi nel test di copertura: evita falsi `ok` su R-07, 11, 12, 13, 15.

## Rilievi

### Critical
Nessuno.

### Important

**I1. L'introduzione della skill ha un criterio senza fonte e senza riga nel rapporto.** `skills/rules-database/SKILL.md:12`: «da un `create table` in un file `.sql`». Il verificatore (`task-4-fonti-2.md`) lo segna `no`, e nel rapporto delle fonti non c'è nessuna riga per l'introduzione (`docs/profili/verifiche/database-fonti.md`, «Regole e fonti»). Il brief chiede che ogni voce passi dal verificatore e che le righe delle voci cambiate siano nel rapporto. Come correggere (a scelta del controller): (a) togliere `create table` dalla frase e tenere solo `schema.prisma` e `drizzle-orm/pg-core`, che hanno citazioni nelle copie (`prisma.md`, `drizzle.md`); oppure (b) dichiararlo «scelta nostra» nell'introduzione e nella sezione «Parti dichiarate «scelta nostra»». In entrambi i casi aggiungere al rapporto una riga per l'introduzione (`schema.prisma` ok, `pg-core` ok), e un test che la riga c'è. Se si sceglie (b), anche il punto 17 di «Da decidere tu» e il test `OUR_CHOICES` vanno estesi, oppure l'introduzione resta fuori dalle sei regole e si dice nel rapporto.

**I2. Due punti di «Da decidere tu» senza costo.** `docs/profili/database.md`, punto 8 (Prisma 8 e il contratto) e punto 16 (Alembic e Rails): non hanno la riga «Costo:». Gli altri quindici sì (controllato sul testo). Il costo da dire: per il punto 8, un cambio a `src/prisma/contract.prisma` non segue le regole del database e non porta il lavoro in L2; per il punto 16, una migrazione di Alembic o di Rails non segue le regole del database e non porta il lavoro in L2. Il test `test_page_choices_count_matches_list` controlla solo «Proposta:»: va esteso a «Costo:» per ogni punto, altrimenti il difetto torna.

### Minor

**M1.** `docs/profili/database.md` («Cosa sono», «Nove regole su sedici (la 6 e dalla 7 alla 12, la 14 e la 15)») e l'introduzione («diciassette punti») sono numeri della pagina non legati alla skill. `test_page_counts_match_skill` controlla solo «Sono N regole» e «N di queste bloccano». Il conteggio è giusto oggi (le regole 6-12, 14, 15 hanno «Vale solo per …»), ma il brief vuole i conteggi della pagina uguali a quelli della skill: aggiungere il conto delle regole con «Vale solo per» e il «diciassette» dell'introduzione.

**M2.** `tests/test_rules_database.py`, `test_page_brings_the_open_choices_to_the_user` cerca ogni parola chiave nell'intera sezione, non nel punto che le spetta: un punto potrebbe perdere il suo contenuto se la parola compare in un altro. Più forte: un dizionario punto → parole. Non blocca.

**M3.** `test_skill_carries_the_corrections_of_the_verification` usa `assertIn`/`assertNotIn` sul testo della skill senza messaggio fisso: se fallisce, stampa la `Fonte:` intera. È la stessa cosa che la decisione 17 toglie dai test della pagina; qui è un test della skill, quindi lieve. Usare `assertTrue(x in y, "messaggio fisso")`.

**M4.** Nel rapporto, le righe R-DATABASE-16 su `functions/secrets`, Prisma e Drizzle e la riga R-DATABASE-04 sul catalogo 2.1 non hanno citazione testuale ma un riassunto della copia (dichiarato dentro la cella). Il secondo verificatore le dà `ok (da rilevare)`. Accettabile, perché la copia non ha una frase da citare; resta il rischio che il riassunto non sia la pagina. Annotarlo nel rapporto finale.

**M5.** La pagina dice «i Task 1 e 2 di questo lavoro» (`database.md`, «Rinvio»): per una persona non tecnica è un'etichetta interna, anche se subito dopo è spiegata tra parentesi. Il test lo richiede (`"i Task 1 e 2"`), come in B6; si può lasciare.

**M6.** Termini non spiegati in pagina: «CLI», «remote» (in `--remote`), «TypeScript», «variabili d'ambiente», «gate» (spiegato), «`security definer`» (spiegato nella riga della regola). Non sono nel brief (il test chiede migrazione, RLS, policy, edge function, specialista finale). Aggiungere «CLI: il programma `supabase` da riga di comando» al glossario.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** La pagina, il rapporto e i test sono in buona forma e aderiscono al brief e a carry, con la suite verde. Restano due correzioni piccole ma richieste: la riga dell'introduzione della skill che il secondo verificatore dà `no` e che non ha riga nel rapporto (I1), e i due punti di «Da decidere tu» senza costo, con il test che non lo controlla (I2).
