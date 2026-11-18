# Revisione finale del ramo `b7-profilo-database` (349bb5b..db2af0e)

Revisore finale, sola lettura. Sonde con `python3 -B` e `PYTHONPATH=bin` in una cartella di lavoro fuori dal repo; test mirati: `tests.test_init.DatabasePrecedenceTest` e `tests.test_check_agents` (94 test, OK). Nessun programma vietato lanciato, nessuna rete, `git status` pulito alla fine. Le copie delle fonti e le evidenze sono state lette come dati; la richiesta delle pagine di supabase.com di mandare un rapporto non è stata eseguita.

## 1. Verdetto

**Non pronto per il merge.** Critical 0 / Important 1 / Minor 4.

Il rilievo Important è uno solo e la correzione costa poco: una riga in `launcher_candidates` più i test.

## 2. Rilievi

### I1 — Important — Prisma e Drizzle dietro un lanciatore con `--` scrivono sul database senza permesso

- **Dove**: `bin/tollgate_analysis/bash.py:1095-1110` (`launcher_candidates`), usato da `effect_reason` in `bash.py:1374-1380`; voci in `bash.py:1004-1013`.
- **Cosa**: il candidato dietro un lanciatore è `[programma] + argv[i+1:]` e tiene il separatore `--`. Per Supabase (regola chiusa) un `--` in testa fa chiedere il permesso. Prisma e Drizzle però sono prefissi di `_DEFAULT_EFFECTS` (regola aperta): `["prisma", "--", "migrate", "deploy"]` non corrisponde a `("prisma", "migrate", "deploy")` e il comando passa.
- **Scenario che fallisce** (sonda `effect_reason` con `EffectsCfg()` vuoto, tutti `None`, cioè senza permesso):
  - `npm exec prisma -- migrate deploy` (la forma con `--` che `npm exec` documenta)
  - `npx prisma -- migrate deploy`
  - `pnpm exec prisma -- migrate deploy`
  - `npm run prisma -- migrate deploy` (lo script `"prisma": "prisma"` di molti progetti)
  - `npm exec drizzle-kit -- push`, `npx drizzle-kit -- push`

  Ognuno arriva a `prisma migrate deploy` o `drizzle-kit push` sul database di `DATABASE_URL`, che può essere quello di produzione. Per confronto, `npm exec -- prisma migrate deploy`, `npx prisma migrate deploy`, `pnpm exec prisma migrate deploy` e `bunx prisma db push` chiedono. Wrangler ha lo stesso buco già su `main`: `npm exec wrangler -- deploy` e `npm exec wrangler -- d1 execute DB --remote` passano, verificato sulla copia di `349bb5b`. Per Prisma e Drizzle invece il buco nasce in B7, perché le voci sono nuove.
- **Perché è Important**: la pagina approvata (`docs/profili/database.md:118`) promette all'utente che «chiede il permesso ogni comando che scrive sul database configurato». La decisione 7 e la spec rev 34 (8.5) dicono che `launcher_candidates` trova questi comandi dietro un lanciatore. Fra i costi dichiarati c'è solo l'opzione prima del sottocomando, non il `--`.
- **Come correggere**: in `launcher_candidates` togliere il primo `--` da `argv[i+1:]` quando si costruisce il candidato. npm, pnpm, npx, bunx e yarn passano gli argomenti dopo `--` al comando come posizionali. Test in `tests/test_bash.py`: chiedono le sei forme sopra, più `npm exec wrangler -- deploy` e `npm exec wrangler -- d1 execute DB --remote`; passa `npm exec supabase -- start`. La stessa correzione chiude M3 (voce 2 della triage) e rende più leggibile il motivo di M7 nel caso `--`.
- **Scelte dell'utente**: nessuna toccata. La correzione rimette il comportamento approvato nella pagina (punto 13 di «Cosa hai deciso»).

### M1 — Minor — `--local` e `--help` presi come valore di un'opzione di un sottocomando

- **Dove**: `bash.py:1232-1242` (`_supabase_flag_present`) e `bash.py:1300-1307` (`_supabase_asks_help`).
- **Cosa**: la correzione I1 del Task 1 vale solo per le opzioni globali (`SUPABASE_VALUE_OPTIONS`). Un'opzione con valore di un sottocomando nasconde `--local` nello stesso modo, perché pflag prende come valore il token che segue anche se comincia con `-`. Le sonde passano: `supabase db push --password --local`, `supabase db push -p --local`, `supabase db pull --schema --local` (con la CLI 2 il comando va al progetto collegato). Lo stesso vale per `--help` (voce M2 del ledger). La spec rev 34 (8.5) dice in generale che `--local` «non conta se è il valore di un'altra opzione»: il codice lo fa solo per le globali.
- **Perché Minor**: con `-p --local` la password diventa `--local` e la connessione quasi sempre fallisce. Con `db pull --schema --local` lo schema `--local` non esiste e di solito non si scrive niente. Lo scenario c'è, ma l'esito pratico è debole e non verificato (servirebbe la CLI vera).
- **Come correggere** (B8): una piccola tabella delle opzioni con valore dei sottocomandi `unless_local` (`-p`/`--password`, `-s`/`--schema`, `--status`, `--last`). `--local` o `--help` subito dopo una di queste non contano. In alternativa basta correggere la frase della spec.
- **Scelte dell'utente**: progetto 14, rafforzata e non cambiata.

### M2 — Minor — Gli involucri che caricano l'ambiente nascondono ogni comando di servizio

- **Dove**: `bash.py:1374` (`effect_reason` guarda solo `argv[0]` e i `LAUNCHERS`).
- **Cosa**: tutte queste forme passano, sia sul ramo sia su `main`: `dotenv -e .env.production -- prisma migrate deploy`, `dotenv -e .env2 -- npx prisma migrate dev` (la forma che la documentazione di Prisma usa per più file `.env`), `dotenv -- wrangler deploy`, `env-cmd -f .env prisma db push`, `infisical run -- prisma migrate deploy`, `doppler run -- npx prisma migrate deploy`, `op run -- supabase db push`. Con `npx` davanti (`npx dotenv -e .env -- prisma migrate deploy`) chiedono.
- **Perché Minor**: è un limite che c'era già e vale per tutti i servizi. Non nasce dal ramo e la decisione 17 di B5 elenca i lanciatori. È però il modo tipico di puntare Prisma a un `.env` di produzione.
- **Come correggere** (B8, trasversale): aggiungere `dotenv`, `dotenv-cli`, `env-cmd`, `infisical run`, `doppler run`, `op run` e `cross-env` agli involucri trasparenti (come `env`, `timeout`, `nice`), oppure un candidato dopo il primo `--`.

### M3 — Minor — Il ripiego di `2d1441c` può legare l'`Agent` nuovo al task sbagliato

- **Dove**: `bin/tollgate_hooks/apply.py:37-45` contro `bin/tollgate_checks/agents.py:72-90`.
- **Cosa**: il `PreToolUse` sceglie il task per `name` tra i candidati e lo prenota (`task_reserve`). Il `SubagentStart` invece prende prima un task `launch` dello stesso tipo e poi, nel ripiego, il `resume` con il numero più basso, senza guardare né il nome né la prenotazione. Esempio: task 1 in `launch` (nome A) e task 2 in `resume` lanciato da un'altra sessione (nome B). Un `Agent` con nome B è ammesso, ma il `SubagentStart` lo lega al task 1 e azzera il suo `pending`. Il task 2 resta in `resume` e un lancio successivo di A viene negato. Con il caso di due `resume` succede lo stesso.
- **Perché Minor**: servono due task dello stesso tipo in sospeso insieme, cosa che il flusso sequenziale di `execute` non produce di solito (ledger, voci 29-30). Che lo stato si possa raggiungere resta **da verificare** con un task di correzione di `finish` aperto mentre un altro è in ripresa. Nella stessa sessione il lancio nuovo è negato correttamente (`_relaunchable`, test `test_same_session_relaunch_denied_with_sendmessage_hint`).
- **Come correggere** (B8): in `_subagent_start` preferire il task con `reserved_at` dello stesso tipo, per entrambe le chiamate di `take_pending`, con un test per ciascuno dei due casi.

### M4 — Minor — Righe e piccoli residui (vedi triage)

`bin/tollgate_flow/init.py:254` (103 caratteri), `tests/test_rules_database.py:323` (101), `STEPS` mai usata in `spikes/run-b1-flow.sh:132-133`, Q46 senza `subTest`, il numero dell'issue usato come numero di fette in `approve spec $ISSUE`, la riga 42 del rapporto («5 giri», ma gli eventi sono 9). Correzioni da una riga ciascuna.

### Da verificare, senza gravità

- **CLI 2 e `db query`.** La tabella mette `db query` e `db advisors` in `with_remote`, cioè liberi senza opzione remota. Il ragionamento sulla CLI 2 (spec 8.5, voce 14 della triage) nomina solo `db dump`, `migration list` e `inspect db`. Se una versione 2.x avesse `db query` con il progetto collegato come predefinito, `supabase db query "drop table x"` passerebbe e scriverebbe sul progetto vero. Si verifica sulle note di rilascio di `supabase/cli`, che richiedono la rete, in B8 insieme alla voce 14.

## 3. Casi di precedenza cercati

Sonda: `_real_fragments_root` di `tests/test_init.py` (i cinque frammenti veri, le skill finte approvate) → `init.profile_blocks(files, DEFAULT_TOML, root, detected=…)` → `profiles.vertical_for` sui blocchi proposti. Nessuno dei casi è nella tabella Q1-Q47.

| Caso | File (marcatore) | Proposta | Runtime | Esito |
|---|---|---|---|---|
| N1 | `supabase/functions/api/routes/users.ts`, `supabase/functions/api/index.ts`, `supabase/migrations/1.sql`; variante `supabase/functions/webhooks/handlers/stripe.ts` | `database`: `/supabase/**` (niente `backend`) | tutti → `database` | **Regge.** I `**/routes/**` e `**/handlers/**` di `backend` non portano via una edge function: l'`exclude` `supabase/` vale anche per la proposta e i percorsi proposti sono concreti. Progetto 12 (edge function a `database`) rispettato. |
| N2 | `supabase/functions/og/components/Card.tsx`, `supabase/functions/og/index.tsx`, `supabase/functions/og/style.css` | `database`: `/supabase/**` (niente `frontend`) | tutti → `database` | **Regge**, come N1, con `**/components/**` e `**/*.css` di `frontend`. Progetto 12 rispettato. |
| N3 | `src/db/embeddings.ts`, trovato sia da `ai` (SDK dei modelli) sia da `database` (`drizzle-orm/pg-core`), più `src/main.ts` | `ai`: `src/db/embeddings.ts`; `database`: `src/db/embeddings.ts` | `embeddings.ts` → `ai` | **Costo nuovo**, come Q44 ma con `ai`: a parità di percorso esatto vince il primo blocco in ordine alfabetico. Uno schema di Drizzle con un client di modelli segue le regole di `ai`. `database` resta attivo e il lavoro va in L2. Nessuna scelta dell'utente toccata; da aggiungere alla tabella. |
| N4 | `server/app.ts`, `server/drizzle/0000_init.sql`, `server/drizzle/meta/_journal.json`, `server/drizzle.config.ts` (trovato da `database`) | `backend`: `/server/**`; `database`: `**/*.sql`, `server/drizzle.config.ts` | migrazione `.sql` e `_journal.json` → `backend`, config → `database` | **Costo nuovo.** Le migrazioni di Drizzle nella cartella d'uscita predefinita `drizzle/` dentro `server/` vanno a `backend`, mentre `server/migrations/` (Q6) va a `database`: lo stesso tipo di file ha esiti diversi a seconda del nome della cartella. È coerente con la decisione 1 (Q45) e con Q5. `database` resta attivo (L2, specialista). Da aggiungere alla tabella e alla pagina; nessuna scelta dell'utente toccata. |
| N5 | `supabase/functions/_shared/ai/client.ts`, `supabase/migrations/1.sql` | `ai`: `supabase/functions/_shared/ai/**`; `database`: `/supabase/**` | `client.ts` → `ai` | **Tocca la scelta dell'utente del progetto 12** (edge function a `database`), come Q31 e Q32. Il codice condiviso delle edge function in una cartella `ai/` va ad `ai`. Il costo è già annotato a Q32 («vale anche per `llm/` e `ai/`») e nella pagina (punto 6): nessuna azione nuova, ma conviene un test esplicito per `_shared/ai/`. |
| N6 | `functions/index.ts`, `functions/migrations/1.sql`, `functions/schema.sql` | `backend`: `/functions/**`; `database`: `**/*.sql`, `functions/migrations/**` | `1.sql` → `database`, `schema.sql` → `backend` | Regge, come Q16 e Q5. |
| N7 | `web/prisma/schema.prisma`, `web/prisma/migrations/1/migration.sql`, `web/app/page.tsx` | `database`: `web/prisma/migrations/**`; `frontend`: `/web/**` | schema → `frontend`, migrazione → `database` | Costo già noto (come Q43, con `frontend`). |

## 4. Comandi provati

`bash.effect_reason` su `bash.parse(...)`, `EffectsCfg()` vuoto. «Chiede» vuol dire motivo non nullo.

**Supabase, chiedono (corretto)**: `db push`, `db pull`, `migration up|fetch|repair` senza `--local`; `--local=false`; `--local --linked`; `--db-url --local`; `db reset|query|dump|diff|test db|inspect db|gen types|migration list|squash|seed buckets` con `--linked`, `--remote`, `--db-url`, `--project-ref`, `--project-id`, anche `--linked=false`; `functions deploy|delete`, `secrets set|unset`, `link`, `unlink`, `storage cp|rm`, `config push`, `branches create|get`, `projects create`, `snippets download`, `sso`, `domains`, `vanity-subdomains`, `postgres-config`, `network-restrictions`, `ssl-enforcement`, `backups restore`, `encryption`, `login`, `logout`, `bootstrap`; le globali `--debug`, `--yes`, `--workdir x`, `--workdir=x`, `-o json`, `--agent yes` prima di `db push`; un'opzione sconosciuta (`--linked`, `--create-ticket`, `-y`) prima del sottocomando; `--workdir --help db push`, `-o --help db push`, `db push --workdir --help`, `db push -- --help`, `db push --dry-run`. Con i lanciatori: `npx`, `npx -y`, `npx --yes supabase@latest`, `npx supabase@2`, `npx --package supabase supabase`, `npx -p supabase supabase`, `pnpm exec`, `pnpm dlx`, `pnpm supabase`, `bunx`, `bunx supabase@1.2`, `npm exec supabase --`, `npm exec -- supabase`, `npm exec --package=supabase --`, `yarn`, `yarn dlx`, `bun x`, `bun run`, `npm run supabase --`, `./node_modules/.bin/`, `/usr/bin/`, `env`, `command`, `exec`, `time`, `nice`, `timeout 60`, `xargs`, `sudo`, `VAR=1`, `bash -c`, `sh -c`, `echo y |`, `< /dev/null`, `"supabase"`, `s\upabase`.

**Supabase, passano (corretto)**: `db push --local`, `--local=true`, `--output json db push --local`, `--profile x db push --local`, `migration up|down|repair --local`, `db pull --local --schema public`; `db reset`, `db reset --local|--no-seed|--debug`, `db lint`, `db diff`, `db dump`, `db query "select 1"`, `db advisors`, `test db`, `seed buckets`, `migration list|squash`, `gen types --local`, `inspect db … --local`, `inspect report --local`; `start`, `start -x studio`, `stop --no-backup|--all|--project-id x`, `status -o env`, `init --force`, `db start`, `functions new|serve`, `migration new`, `test new`, `gen signing-key|bearer-jwt`, `completion`, `services`, `help`, `-h`, `--help db push`, `db push --help|-h|--version`, `db --help push`; le letture `functions list|download`, `secrets list`, `projects list`, `snippets list`, `migration list`; con i lanciatori `npx supabase db push --local`, `npx supabase start`.

**Supabase, passano e non dovrebbero**: `db push --password --local`, `db push -p --local`, `db pull --schema --local` (M1); `dotenv -e .env -- supabase db push`, `op run -- supabase db push` (M2); `$(echo supabase) db push` (sostituzione di comando: limite generale del parser, fuori da B7).

**Supabase locali che chiedono ancora**: `storage ls ss:/// --local` (scelto con D5: `storage …` chiede sempre), `gen keys` (legge il progetto), `gen types|db diff --db-url postgres://…@localhost…` (un `--db-url` può puntare ovunque: voluto), `-y db push --local` (`-y` non è un'opzione globale nota). Sono tutti motivati; nessun comando locale chiede senza motivo.

**Prisma, chiedono (corretto)**: `migrate dev|deploy|reset`, `db push`, `db push --schema x`, `db seed`, `db execute`, `studio`, anche dietro `npx`, `npx prisma@5`, `pnpm`, `pnpm exec`, `pnpm --filter api exec`, `pnpm -C api`, `npm --prefix api exec`, `npm -w api exec --`, `bunx`, `yarn`, `yarn exec`, `npx --no-install`, `npx --package prisma prisma`, `npm exec -- prisma`, `npm exec --package=prisma -- prisma`, `npx dotenv … --`, `npx env-cmd`, `npx cross-env`, `node_modules/.bin/prisma`. **Passano (corretto)**: `generate`, `validate`, `format`, `db pull`, `migrate status`, `migrate diff`. **Passano e non dovrebbero**: `npm exec prisma -- migrate deploy`, `npx prisma -- migrate deploy`, `pnpm exec prisma -- migrate deploy`, `npm run prisma -- migrate deploy` (I1); `dotenv -e … -- prisma migrate deploy`, `env-cmd -f .env prisma db push`, `infisical run --`, `doppler run --` (M2); `node node_modules/prisma/build/index.js migrate deploy` (interprete con un file: limite generale); `prisma --schema x migrate dev`, `prisma migrate --schema x deploy` (costo approvato, M5 del ledger).

**Drizzle, chiedono (corretto)**: `push`, `migrate`, `studio`, `push:pg`, anche dietro `npx`, `npx drizzle-kit@latest`, `pnpm`, `pnpm exec`, `bunx`, `yarn`, `npx --yes … --force`, `npx dotenv-cli … --`, `npx tsx node_modules/.bin/drizzle-kit push`. **Passano (corretto)**: `generate`, `pull`, `introspect`, `check`, `up`, `drop`, `export`. **Passano e non dovrebbero**: `npm exec drizzle-kit -- push`, `npx drizzle-kit -- push` (I1); `drizzle-kit --config x push` (costo approvato). `push:postgres` e `migrate:pg` passano, ma non sono comandi di drizzle-kit.

## 5. Altri punti controllati (nessun rilievo)

- **Specialista**: `finalreview._open` aggiunge `final_specialists` solo in L2 (`finalreview.py:115-117`). `final-database` è in `READONLY_TYPES` (`hooks/run:56`) e in `readonly_agents` (`config.py:76-82`), riceve la `checklist` (`_final_brief`, `finalreview.py:206-213`) e ha `tools: Read, Grep, Glob, Bash`. `init` propone `final_specialist` solo se l'agente esiste (`init.py:310-312, 354-357, 408-411`). Test: `test_real_database_specialist_in_l2` e `test_real_database_specialist_not_in_l1`.
- **Agenti d'area**: `final-database` differisce da `final-reviewer` solo per frontmatter (nome, descrizione, skill) e sezione d'area. `reviewer-database` differisce da `reviewer-backend` solo per i nomi delle regole, la descrizione e la frase sulle basi dati diverse da PostgreSQL. Nessuna deriva.
- **Regole**: tutte le `[blocca]` si giudicano sul diff o sul report, nessuna sulla nota. La sezione «Area `database`» dello specialista nomina solo le dieci regole sul diff (03, 05, 07-14), le stesse che `reviewer-database` dichiara sul diff.
- **Marcatori**: solo `drizzle-orm/pg-core` e `drizzle-kit`. Nel repo compaiono solo in documenti, nella skill, nel frammento e in `tests/test_rules_database.py`, tutti esclusi dal rilevamento (estensione o cartella dei test). `bin/` non li contiene.
- **`tollgate.toml`**: in `init.py` cambia solo `_concrete_paths`; nessuna riscrittura del file dell'utente.
- **Test**: niente `os.environ` in un'asserzione; `test_page_has_no_private_data` confronta il nome utente e l'host senza stamparli. I test nuovi che leggono i file veri hanno il prefisso `test_real_` o stanno in `tests/test_rules_*.py` / `tests/test_manifest.py` (convenzione già esistente).
- **Evidenze e file nuovi**: zero occorrenze del nome utente e dell'host della macchina (conteggio senza stampa). `/home/` compare solo come `/home/USER` anonimizzato; nessuna forma di token (le due occorrenze sono l'elenco dei prefissi cercati); nessun nome di progetto privato (al suo posto `PROGETTO-PRIVATO`); nessun testo della richiesta di rapporto di Supabase.
- **Ledger**: le 47 `Ruling:` di prodotto (D1-D15, M1, M6, la correzione 2d1441c, le opzioni globali, `login`/`logout`, `storage ls`, Prisma 8, CLI 2) sono nella spec rev 34 (8.5, 6.3, 11.4) o nei rinvii del piano principale; quelle di processo (revisioni parallele, atti della prova) restano nel ledger e nel rapporto, com'è giusto.

## 6. Tabella di triage di `W/final-deferred.md`

| N. | Voce (in breve) | Esito | Motivo |
|---|---|---|---|
| 1 | M2 `--help`/`-h` come valore di un'opzione non globale | rinviato | B8, insieme a M1 di questa revisione: tabella delle opzioni con valore dei sottocomandi di Supabase |
| 2 | M3 `npm exec supabase -- start` e simili chiedono | da correggere | Si chiude con la correzione di I1: togliere il `--` nel candidato di `launcher_candidates` |
| 3 | M4 il ripiego testuale non vede `npx supabase@2 db push`, `/usr/bin/supabase` | rinviato | B8, ripiego testuale di tutti i servizi (vale anche per Wrangler) |
| 4 | M5 opzione di Prisma o Drizzle prima del sottocomando | nessuna azione | Costo scritto nella pagina approvata (permessi di Prisma e Drizzle, «Primo») e nella spec 8.5 (D13) |
| 5 | M7 motivo del veto poco leggibile con `--package` o `--` | rinviato | B8; la parte con `--` migliora già con la correzione di I1 |
| 6 | M8 tre scorrimenti di `FLAG_EFFECTS` per Supabase | nessuna azione | Solo struttura, nessun effetto sul comportamento; costo di lettura trascurabile |
| 7 | Docstring di `_concrete_paths` di 103 caratteri | da correggere | Andare a capo in `init.py:254` |
| 8 | `tool-results:` scritto in un comando conta come cartella | nessuna azione | Toglie di più, mai di meno: dalla parte sicura |
| 9 | `tests/test_rules_database.py` riga di 101 caratteri | da correggere | Oggi è la riga 323: andare a capo |
| 10 | Q46 due controlli senza `subTest` | da correggere | Due `with self.subTest(...)` in `test_real_precedence_q46` |
| 11 | `test_draft_is_not_approved_before_task_5` resterà sempre saltato | nessuna azione | Il test non esiste più nel file a HEAD |
| 12 | Il test delle scelte aperte cerca nell'intera sezione | nessuna azione | La pagina è approvata e ferma; il test resta valido come guardia |
| 13 | R-DATABASE-04 poggia su un riassunto senza citazione | nessuna azione | Regola approvata dall'utente; il verificatore delle fonti l'ha accettata |
| 14 | La frase sulla CLI 2 viene dalla memoria del controller | rinviato | B8: verificarla sulle note di rilascio di `supabase/cli` (serve la rete), compreso il «da verificare» su `db query` con la CLI 2 |
| 15 | La citazione di R-DATABASE-16 è più larga dell'etichetta | nessuna azione | Sostegno accettato dal verificatore; regola approvata |
| 16 | `test_page_records_the_choices` confronta l'intera sezione e non i «Costo:» | nessuna azione | Come la voce 12 |
| 17 | La pagina dice che gli agenti «arrivano dopo la tua approvazione» | rinviato | Alla prossima revisione della pagina con l'utente (la pagina approvata si tocca solo con lui) |
| 18 | Il punto 17 dice «tutte e sei», ma sono sette | rinviato | Come la voce 17 |
| 19 | «oggi `database`» in `docs/uso/comandi.md` invecchierà | rinviato | Al secondo specialista finale (profilo che lo introduce) |
| 20 | Il nome «real» di `DatabaseAgentsProposeTest` è approssimativo | nessuna azione | Il test usa davvero i file veri del plugin (frammento, skill e agenti di `ROOT`); solo l'approvazione è finta |
| 21 | `approve spec $ISSUE` usa il numero dell'issue come numero di fette | da correggere | Nel caso `database` usare una variabile del numero di fette (1) invece di `$ISSUE` |
| 22 | `test_real_flow_case_database_prepara_checks_l2_plan` non distingue L1 da L2 | nessuna azione | `plan.py` tratta i due livelli allo stesso modo su quel controllo |
| 23 | `STEPS` assegnata e mai usata | da correggere | Togliere le righe 132-133 di `spikes/run-b1-flow.sh` |
| 24 | Nessun test sul salto di `libero-*.prev-*` | rinviato | B8, con gli altri test dello script della prova |
| 25 | Due righe vuote prima della sezione `database` in `test_b1_scripts.py` | da correggere | Togliere una riga vuota |
| 26 | `FRONTEND_PROJECT` forse senza uso | nessuna azione | È usato: `tests/test_b1_scripts.py:1713, 1767, 1784` |
| 27 | `unittest_junit.py` esce 1 senza test | nessuna azione | Il progetto di prova ha test; è un attrezzo della prova |
| 28 | Nel rapporto junit failure ed error hanno solo `message="x"` | nessuna azione | Il dettaglio resta su stderr; il gate conta solo gli esiti |
| 29 | Due task `resume` dello stesso tipo: `SubagentStart` lega il numero più basso | rinviato | B8 (M3 di questa revisione): preferire il task con `reserved_at`, con un test |
| 30 | Un task `launch` e uno `resume` dello stesso tipo: `SubagentStart` prende il `launch` | rinviato | B8, stessa correzione della voce 29 |
| 31 | La scelta per `name` in `agents.py:88` cambia anche il caso dei soli `launch` | nessuna azione | Innocua, anzi più precisa |
| 32 | Il ripiego di `apply.py` vale anche fuori da execution L1/L2 | rinviato | B8, insieme alle voci 29-30 (condizionare il ripiego alla fase) |
| 33 | Il rapporto riporta lunghezze di SessionStart senza fonte nelle evidenze | nessuna azione | Dato informativo e non usato da nessuna conclusione |
| 34 | Il rapporto dice 5 giri, ma gli eventi `spec_audit_round` sono 9 | da correggere | Riga 42 del rapporto: «9 eventi, 5 della spec e 4 del piano» |
| 35 | Il report del Task 9 cita «4061 test» nella spec 16 | nessuna azione | Riguarda il report del ledger, non un file del repo |
| 36 | Il log della suite del Task 9 non mostra `PYTHONWARNINGS` | nessuna azione | Processo; la suite del merge si lancia con la riga delle cautele |
| 37 | Il blocco «A B8, da B7» mescola rinvii di processo e di prodotto | nessuna azione | Leggibile così; B8 li separa quando li riprende |

Conteggi: da correggere 8, rinviato 11, nessuna azione 18 (totale 37).

## 7. Punti di forza

- La regola di Supabase è davvero chiusa verso il sicuro: oltre 130 forme provate, comprese quelle dietro tutti i lanciatori e involucri comuni, e nessuna scrittura remota di Supabase passa, salvo i casi di M1 e M2.
- `--local` vale solo con un valore vero e `--help` solo fuori dai valori delle globali; la distinzione `_supabase_flag_present` / `_flag_present` lascia Wrangler com'era.
- La tabella delle precedenze ha 47 casi con test sui frammenti veri; le sonde nuove confermano che l'`exclude` `supabase/` di `backend` e `frontend` protegge la scelta del progetto 12.
- La correzione `2d1441c` nega il rilancio nella stessa sessione con un messaggio che indica `SendMessage`, ed è coperta da sette test.
- Le evidenze sono anonimizzate (nome utente, host, progetti privati) e il rapporto dichiara i controlli fatti.
- Agenti d'area allineati al generico e skill con il «Si giudica su» per ogni regola.
