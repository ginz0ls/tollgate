### Verdetti sui rilievi
- **I1 (criterio `create table` senza fonte): INDIRIZZATO.** `skills/rules-database/SKILL.md:12` ora dice «(questo criterio è una scelta nostra)»; `docs/profili/verifiche/database-fonti.md` ha due righe `ok` per l'introduzione (`schema.prisma` da prisma.md riga 5, import di `drizzle-orm/pg-core` da drizzle.md riga 3, entrambe presenti nelle copie) e `create table` tra le «Parti dichiarate «scelta nostra»». Test `test_sources_report_covers_the_introduction` e `needle "scelta nostra"` nel test dell'introduzione. Il punto 17 di «Da decidere tu» non è esteso: il report lo dichiara, accettabile.
- **I2 (costo ai punti 8 e 16): INDIRIZZATO.** «Costo:» presente nei punti 8 e 16 di `docs/profili/database.md`; `test_page_choices_count_matches_list` controlla per ogni punto «Costo:» e una sola «Proposta:».
- **(a) assertTrue con messaggio fisso: INDIRIZZATO.** `test_skill_carries_the_corrections_of_the_verification` usa `assertTrue(needle in …, msg)`.
- **(b) numeri dell'introduzione legati: INDIRIZZATO.** `test_page_intro_numbers_match_skill` lega «nove su sedici» al conto di «Vale solo per» e «diciassette punti» all'elenco.
- **(c) CLI spiegata: INDIRIZZATO.** Voce `**CLI**` nell'elenco delle parole, richiesta dal test.
- **(d) secondo passaggio e righe letterali: INDIRIZZATO.** Il rapporto registra il secondo passaggio con data (2026-11-16) e toglie la frase «un nuovo verificatore le rilegge». Le citazioni di R-DATABASE-16 (secrets, `migrate deploy`, `db push`, `db execute`, `migrate`, `push`) sono tutte nelle copie (`supabase-edge-functions.md:17`, `prisma.md:9-11`, `drizzle.md:9-10`), controllate con grep letterale. Nota: la citazione di `schema.prisma` nel rapporto omette i backtick presenti nella copia (prisma.md:5), irrilevante.

### Danni nuovi nel diff della correzione
Nessuno. Grep sul diff: niente nome utente, `/home/`, né `approved`. `python3 -B -m unittest tests.test_rules_database`: 52 test OK. La nuova riga `secrets` cita «with the Supabase CLI», mentre l'etichetta dice `secrets set`: sostegno un po' più largo, Minor, già accettato nel secondo passaggio.

### Osservazioni fuori ambito
Restano M2, M5 e il resto di M6, dichiarati non fatti dal report e non bloccanti.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
