# Revisione Task 3 (B7): bozza rules-database, frammento database, tabella delle precedenze

Pacchetto letto: `review-88ee27c..4603ade.diff` (commit 4603ade), più i file veri nel worktree per i controlli mirati. Nessun test rilanciato, nessuna rete.

## Aderenza

- ✅ **File toccati**: solo i sei dichiarati (`docs/uso/comandi.md`, `skills/rules-database/SKILL.md`, `templates/profiles/database.toml`, `tests/test_fragments.py`, `tests/test_init.py`, `tests/test_rules_database.py`). Nessun file approvato toccato (rules-frontend/backend/ai/infra/base, i loro frammenti e pagine). Nessun `approved` nella skill (`SKILL.md:1-5`).
- ✅ **Forma della skill** (decisioni 9, 12): titolo, paragrafo iniziale, sezioni «Prima di scrivere», «Mentre lavori», «Dove informarsi», «Fonti»; 93 righe (limite 150); 16 regole consecutive, ognuna con «Si giudica su» e `Fonte:`.
- ✅ **Ogni `[blocca]` si giudica sul diff o sul report**: 01, 02, 04, 06, 15, 16 sul report; 03, 05, 07, 09-14 sul diff. Nessuna sulla sola nota. Il test `test_blocking_rules_judged_on_diff_or_report` lo asserisce davvero (itera sulle regole con `blocca`, e `test_some_rules_block` esclude il ciclo vuoto).
- ✅ **Riconoscimento di una migrazione nel diff**: `SKILL.md:10` dà file nuovo o cambiato sotto `supabase/migrations/` o altra `migrations/`, `.sql` con `create/alter/drop`, la policy e la edge function; `test_migration_rules_say_how_to_recognize_a_migration` controlla ogni elemento sulla riga unica.
- ✅ **Ambito PostgreSQL/Supabase** (decisione 9): `SKILL.md:12` dice che le regole su RLS, policy, `security definer`, `concurrently` e edge function valgono solo per PostgreSQL e Supabase e che per SQLite/MySQL/Django si risponde «non si applica». Le regole 06-12, 14, 15 portano «Vale solo per…»; 01, 03, 04, 05 no (test `test_general_rules_do_not_claim_a_scope`). `test_postgres_rules_say_their_scope` non ha `if` tautologico: conta `checked >= 8` (le regole che nominano le parole sono più di otto).
- ✅ **Fonti dei tipi ammessi**: ogni `Fonte:` ha un indirizzo ufficiale, o «progetto di B, sezione», o catalogo/spec del nucleo, o una skill MIT con nome e licenza nella stessa riga. `database-reviewer` e `everything-claude-code` non compaiono (test + grep). Gli indirizzi sono tutti di supabase.com, postgresql.org, prisma.io, orm.drizzle.team (`test_urls_are_official_pages`, `seen > 10`). Le sezioni citate esistono: progetto di B 3.4 (riga `database`, riga 88-), 12 e 14; spec del nucleo 8.5; catalogo 2.1 («migrazioni reversibili, RLS, indici, dati esistenti») e 2.3 (dod up/down). Ho controllato sulle copie locali che reggano: advisor 0001/0003/0010/0011/0013, `security_invoker` da PostgreSQL 15, una policy per operazione e `to anon` solo per dati pubblici, `bypassrls` di `service_role`, `verify_jwt = false`, `Deno.env.get` e `functions/.env`, «non modificare migrazioni applicate» di Prisma, i default locali della CLI 3.
- ✅ **Frammento = decisioni** (`database.toml:13-61`): `kind = vertical`, `min_level = "L2"`, i quattro pattern nell'ordine di decisione 2, nessun `[detect] exclude`, `skills = []`, `reviewer_skills = []`, `commands = {}`, `dod = []`, i tre agenti, `final_specialist`, `checklist` non vuota (con «reversibili», «dati esistenti», «RLS», «indici»), quattro marcatori Drizzle nelle due forme di virgolette, nessun client (`supabase-js`, `pg`, `@prisma/client`). Un commento con la fonte per ogni pattern e per ogni gruppo di marcatori. `test_fragment_matches_decisions` asserisce tutto e `test_fragment_loads_through_the_loader` controlla i `Pattern` tipizzati (`root_folder`, `folder`, `root_folder`, `ext`) e `exclude == ()`.
- ✅ **Tabella delle precedenze**: ho confrontato a mano i 44 test con la tabella della decisione 5. Proposta e runtime coincidono per ogni caso, compresi i `detected` (Q4, Q9, Q11, Q19, Q22, Q40, Q44), il caso senza blocco `database` (Q13, `{}`) e le parti con `None` (Q9, Q12, Q20, Q23, Q29, Q36). `check` è quello di `FrontendPrecedenceTest` e confronta la proposta come uguaglianza dell'insieme dei profili e dei `paths` ordinati, il runtime come uguaglianza esatta sui file elencati: nessuna asserzione debole.
- ✅ **D15 (Q45-Q47)**: i tre casi sono scritti con le proposte e i runtime di `carry.md`, compresi i due `.json` di `drizzle/meta` a `None` (Q45), le due parti di Q46 (`src/ai/` e `src/components/`) e Q47 (`ai: ["prisma/ai/**", "src/ai/**"]`, `database: ["/prisma/**"]`). La sonda (`task-3-sonda.txt`) riporta «differenze: 0» e le stesse forme.
- ✅ **P14**: `test_real_precedence_p14` ha `{"database": ["/supabase/**"], "frontend": ["**/*.tsx"]}` e `og/index.tsx -> database`, `main.tsx -> frontend`; `FrontendPrecedenceTest` non cambia altro (il diff tocca solo p14 in quella classe).
- ✅ **Decisione 17 sulle copie dei test**: nessun test `test_a11y…`; nessun ciclo vuoto; `assertTrue(re.search(…), "<messaggio fisso>")` in `test_intro_names_the_other_databases` e `test_sources_section` (niente `assertIn` sul testo della skill nel messaggio); `USER_CHOICES` copre le quattro scelte e `test_user_choices_covered` verifica anche che ogni regola che cita «progetto di B» sia nella tabella (insiemi uguali); nessun `test_rules_database_not_required`; `test_draft_is_not_approved_before_task_5` fa `skipTest` solo se la skill è approvata (previsto per il Task 5). Righe entro 100 caratteri, tranne una (vedi Minor 1).
- ✅ **TDD**: l'ordine reale è stato skill e frammento prima dei test, dichiarato nel report; il rosso è stato riprodotto togliendo temporaneamente skill e frammento (`task-3-red-v.log`: 146 test, failures=48, errors=28; `q13` verde come previsto, p14 e `test_real_fragments_load` rossi). Evidenza leggibile e coerente. Il verde (`task-3-green.log`, 464 test OK) e la suite intera (`suite-task-3.log`: 3996 test OK su due interpreti, `exit 0`) ci sono.
- ✅ **Testo di terzi e dati privati**: nessun nome utente, host o percorso nei tre file nuovi (grep); le regole sono parole nostre e le citazioni di terzi nei file del repo sono assenti; `test_no_long_quotations` limita le «…» a 12 parole. Il giro sul contratto delle skill (`--remote` letterale tolto da R-16) è corretto senza toccare i test approvati. L'istruzione delle pagine di Supabase (mandare un rapporto) non è stata eseguita: il report lo dice.
- ✅ **docs**: sezione `/tollgate:rules-database` dopo quella di `rules-frontend`, che dice «bozza, in attesa dell'approvazione» e che `init` non propone il profilo finché manca; la frase di `/tollgate:init` nomina `frontend` e `database` per i pattern per estensione. `test_docs` verde.
- ⚠️ **Non verificabile dal diff**: i fatti di alcune `Fonte:` non stanno nelle copie locali (vedi Minor 2): ne risponde il verificatore del Task 4, ma li segnalo.

## Punti di forza

- La tabella Q1-Q47 è tradotta in test uno a uno con `detected` esplicito e la sonda dei 47 casi incollata nel report: la pista di ogni precedenza è ricostruibile.
- Il frammento ha le fonti accanto a ogni pattern e a ogni marcatore e dichiara in testa cosa resta fuori e perché (nessun `exclude`, `.sql` che perde contro le altre cartelle).
- La skill separa bene le regole generali da quelle PostgreSQL/Supabase, con una frase di ambito dentro la regola (non solo in testa), così il revisore può rispondere «non si applica» su una `migrations/` di Laravel o di D1.
- Le `Fonte:` distinguono i fatti delle pagine ufficiali dalle «scelte nostre» (R-01, 02, 04, 05, 06, 15) e un test lo impone.
- `test_user_choices_covered` chiude la voce «cosa si è perso nell'implementatore» (schema e migrazioni letti prima) come chiedeva la decisione 17.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

1. `tests/test_rules_database.py:317`: una riga di 101 caratteri (la tupla di `Pattern` in `test_fragment_loads_through_the_loader`); la decisione 17 vuole righe entro 100. Andare a capo prima di `fragments.Pattern("folder", ...)`.
2. `SKILL.md:20` (R-DATABASE-02) e `SKILL.md:78` (R-DATABASE-16): due fatti che le copie locali delle fonti non coprono. `major_version` di `supabase/config.toml` non compare in nessuna pagina copiata (la pagina `local-dev` dice solo che `init` crea `config.toml`); il report lo ammette. «`functions deploy` e `secrets set` lavorano sul progetto collegato» è attribuito a `https://supabase.com/docs/reference/cli`, ma la copia di quella pagina non ha né `deploy` né `secrets set`. Il Task 4 deve chiuderli: o la fonte li regge, o la `Fonte:` li dà come scelta nostra / li toglie, senza cambiare i numeri delle regole.
3. `SKILL.md:26` (R-DATABASE-03): la regola dice «già presente nel repo», le fonti dicono «già applicata». Su una catena di task non uniti, un task che corregge una migrazione creata dal task precedente (mai applicata) riceverebbe un blocco. Scelta prudente, ma da dichiarare «scelta nostra» nella `Fonte:` o da riformulare.
4. `SKILL.md:38` (R-DATABASE-06): «su una tabella che ha già dati» non si vede né nel diff né nel report; R-05 ha la forma giudicabile («può avere dati», eccezione per la tabella creata nello stesso diff). Allineare R-06 a R-05 renderebbe la regola decidibile da chi rivede. Il Task 4 e l'utente decidono (il testo è bozza).
5. `SKILL.md:10` + R-01 (riga 16): R-01 parla di «schema» ma l'introduzione definisce solo come si riconosce una migrazione; uno schema (`schema.prisma`, `schema.ts` di Drizzle) non è riconosciuto nel diff. Una mezza riga nell'introduzione basterebbe.
6. `tests/test_init.py` `test_real_precedence_q46`: le due parti (a e b) sono due `check` consecutivi senza `subTest`: se la prima fallisce, la seconda non gira. Il brief ammette un solo test per Q46; un `with self.subTest(...)` sarebbe più chiaro.
7. `tests/test_rules_database.py:77` (`test_draft_is_not_approved_before_task_5`): dopo il Task 5 resterà un test sempre saltato. Il Task 5 deve toglierlo o riscriverlo (non asserisce il vero per costruzione, ma il suo nome e il suo scopo scadono).

## Valutazione

**Qualità del task:** Approvato

**Motivo:** requisiti e voci di `carry.md` rispettati: skill con `[blocca]` giudicabili, riconoscimento della migrazione e ambito PostgreSQL/Supabase dichiarati, frammento uguale alle decisioni, 47 casi di precedenza asseriti come la tabella (proposta e runtime), nessun file approvato toccato. Restano solo rifiniture e due fatti di fonte da chiudere nel Task 4.
