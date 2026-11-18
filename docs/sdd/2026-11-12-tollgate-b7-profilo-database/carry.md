# Decisioni del controller da portare nei task (prevalgono sul testo del piano)

## Task 1
- Fatti dello Step 0 in `task-1-fatti.md` (elenco vincolante: liste di Supabase, Prisma 7 e 8, Drizzle). `snippets list` entra nelle letture; `snippets download` chiede.
- D1: `--help`/`-h`/`--version` fanno passare solo fuori dai valori delle opzioni di `SUPABASE_VALUE_OPTIONS` e prima del primo `--`. Test che chiedono: `supabase --workdir --help db push --db-url postgres://x`, `supabase --profile -h db push --linked`, `supabase db push -- --help`.
- D2: `launcher_candidates` non cambia; un test fissa `npx eslint supabase --fix` tra quelli che chiedono.
- D3: dei test di B5 si scrivono solo i tre mancanti: `[external_effects] allow` e `commands` con una voce nuova di Wrangler (kv/r2/d1), `text_effect` di `kv:namespace`, `text_effect` con `--remote=false`. Gli altri (`pnpm -w release`, `npm run-script deploy`, `-C`/`--dir`/`--prefix`, `yarn workspace … deploy build`) sono già in `tests/test_bash.py:317-356`: il report li elenca come guardie.
- D4: `docs/uso/comandi.md` NON si tocca nel Task 1 (nessuna sezione sugli effetti esterni lì).
- D5: un test fissa `supabase storage ls`, `supabase unlink`, `supabase bootstrap` tra quelli che chiedono (oggi passano).
- D6: `login` e `logout` NON stanno in `SUPABASE_LOCAL`: chiedono (test).
- D7: ripiego testuale di Supabase costruito a parte dalle liste, regex vecchia `supabase\s+(db|functions|…)` tolta; `test_text_effect_supabase_lists` ha anche `echo 'a; supabase db reset --linked` e `echo 'a; supabase gen types --db-url x` (chiedono) e `supabase functions list` (passa).
- D13: chiedono anche `drizzle-kit push:pg`, `push:mysql`, `push:sqlite` (anche dietro `npx`).
- Prisma 8: chiedono anche `prisma db init`, `prisma db update`, `prisma db migrate`, `prisma db sign`.

## Task 2
- D10: la correzione di `_concrete_paths` si fa; nessun caso reale cambia.

## Task 3
- D15: casi in più in `DatabasePrecedenceTest`: Q45 (`drizzle/0000_init.sql`, `drizzle/meta/_journal.json`, `drizzle/meta/0000_snapshot.json`, `drizzle.config.ts` con import da `drizzle-kit`, `src/db/schema.ts` con import da `drizzle-orm/pg-core`: proposta `database: ["**/*.sql", "/drizzle.config.ts", "src/db/schema.ts"]`; runtime `.sql`, config e schema → `database`, i due `.json` → nessuno); Q46 (`src/ai/db.ts` con import da `drizzle-orm/pg-core`, `src/ai/agent.py`: proposta `ai: ["src/ai/**"]`, `database: ["src/ai/db.ts"]`; runtime `db.ts` → `database`, `agent.py` → `ai`; e `src/components/db.ts` (pg-core), `src/components/Table.tsx`: proposta `database: ["src/components/db.ts"]`, `frontend: ["src/components/**"]`; runtime `db.ts` → `database`); Q47 (`prisma/ai/seed.sql`, `prisma/schema.prisma`, `src/ai/agent.py`: proposta `ai: ["prisma/ai/**", "src/ai/**"]`, `database: ["/prisma/**"]`; runtime `seed.sql` → `ai`, schema → `database`). La forma esatta dei `paths` la dà la sonda del Task 3 (il report la incolla); un esito diverso da questo è `Fermata: precedenza diversa dal piano` solo se tocca una scelta dell'utente, altrimenti il report lo dice e il controller decide.
- `test_real_precedence_p14`: proposta con il blocco `database: ["/supabase/**"]` in più; runtime `supabase/functions/og/index.tsx` → `database`.

## Task 4
- D12: la pagina dice che chi ha già dichiarato `[profiles.database]` a mano aggiunge da sé `min_level = "L2"` e `checklist` (`init --update` non li propone a un blocco già dichiarato).
- D14: la pagina dice che il gate della PR ferma un lavoro dichiarato sotto L2 che tocca file del profilo (`level_below_minimum`); `test_page_explains_what_changes` lo controlla.
- D15: Q47 (`prisma/ai/` va ad `ai`) in «Da decidere tu».
- D2, D5, D6, D13: costi dei permessi da dire nella pagina («Cosa cambia»): lint o formattazione della cartella `supabase` dietro `npx` chiede; `storage ls`, `unlink`, `bootstrap`, `login`, `logout` chiedono; un'opzione di `prisma` prima del sottocomando non è guardata.
- Prisma 8 (release candidate): il contratto in `src/prisma/contract.prisma` non è coperto da `prisma/**` (in «Da decidere tu» o in «Cosa cambia»).
- CLI 2 di Supabase: i comandi `with_remote` senza opzioni con la CLI 2 potevano leggere il progetto collegato (`db dump`, `migration list`, `inspect db`): la pagina lo dice.

## Task 7
- D8: `FlowBench.src_repo` di `tests/test_b1_scripts.py` copia anche `skills/rules-database` e ha `database_approved`; un test dice che con `database` approvato la proposta del caso `backend` (progetto di B5) ha anche il blocco `database`; il progetto di B5 non cambia.

## Task 8
- D9: ogni riga di `comandi-rischiosi.txt` si legge a mano; il rapporto elenca i falsi positivi di percorso (`cd …/supabase`, `ls ./supabase`).

## Task 9
- D4: la tabella dei comandi di Supabase va in 8.5.
- D11: in 11.4 il commento di `checklist` diventa «una frase per la lista di controllo del revisore finale».
- D12: rinvio a B8 nel piano principale (`init --update` non propone `min_level` e `checklist` a un blocco già dichiarato).
- D13, Prisma 8, CLI 2: costi nella spec (8.5) e rinvii nel piano principale.

## Task 4 (aggiunte dopo la verifica delle fonti e la revisione del Task 3)
- R-DATABASE-16, `Fonte:`: per `functions deploy` cita https://supabase.com/docs/guides/functions/deploy (porta le funzioni sul progetto remoto collegato) e per `secrets set` https://supabase.com/docs/guides/functions/secrets (i segreti di produzione); per Prisma dice «il database configurato» invece di `DATABASE_URL`.
- R-DATABASE-02, `Fonte:`: per `major_version` cita https://supabase.com/docs/guides/local-development/cli/config (versione principale di PostgreSQL del database locale, uguale a quella remota).
- R-DATABASE-03: «una migrazione che esisteva prima del lavoro (sul ramo di partenza)» invece di «già presente nel repo»; il testo resta giudicabile sul diff (il revisore vede se il diff modifica o cancella un file di migrazione che il lavoro non ha creato).
- R-DATABASE-06: «su una tabella che il diff non crea» invece di «che ha già dati».
- Introduzione della skill: come si riconosce uno schema nel diff (per R-DATABASE-01).
- Le regole e le voci cambiate ripassano dal verificatore: il controller lo rilancia dopo il tuo commit; tu metti nel rapporto delle fonti le righe di queste voci con le citazioni prese dalle copie aggiornate (W/fonti/database/pagine/supabase-edge-functions.md e supabase-local-dev.md, in fondo).

## Task 5
- Nel punto 17 di «Da decidere tu» (e quindi in «Cosa hai deciso») si aggiunge l'introduzione della skill: riconoscere uno schema SQL da `create table` in un file `.sql` è «scelta nostra»; il test `OUR_CHOICES` la richiede. Il controller l'ha detto all'utente nella presentazione.
- (dalla prova reale) correzione del prodotto 2d1441c: in 6.3 della revisione 34, un giro di correzione dei giri 1-3 il cui implementatore apparteneva a una sessione finita si fa con un `Agent` nuovo dello stesso tipo e con lo stesso `name`, ammesso dall'hook solo se l'ultimo subagente del task è di un'altra sessione (o non c'è); nella stessa sessione la ripresa con SendMessage resta obbligatoria; i 4 minor della sua revisione (più task in sospeso dello stesso tipo) vanno nel piano principale per B8.
- (dalla prova reale) i progetti di prova L2 vogliono un `verify` che scriva un rapporto (junit) perché i test dei must-have siano contati: una riga nel piano principale (sezione 16 «Prove di B7»), e la decisione 16 del piano B7 lo segna come correzione.
- (dalla prova reale) la sezione 16 «Prove di B7» del piano principale riporta l'esito «riuscita (composita)», le due esecuzioni, le due scelte dell'utente a metà, i due difetti trovati e corretti, il costo equivalente sulla quota dell'abbonamento (nessun addebito), e il comportamento visto: implementatore che scrive `(select auth.uid())` da sé, revisore del database che blocca per R-DATABASE-10 contro spec e piano, implementatore che nella prima esecuzione si è scostato dal piano (colonna `name`) e revisore del task che l'ha approvato (rinvio a B8: i revisori del task confrontino le colonne con il piano), `final-database` che riporta «ok» e il verificatore che scarta un rilievo fuori dal lavoro.
- (dalla prova reale) il modello della prova ha lanciato un `find /` (libero-2) che ha elencato file fuori dal progetto di prova: rinvio a B8 nel piano principale (limitare le letture fuori dal worktree nelle prove, per esempio con un divieto in `--disallowedTools`).
