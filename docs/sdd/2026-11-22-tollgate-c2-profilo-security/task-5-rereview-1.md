# Task 5: ri-revisione del giro di correzione 1 (commit `3610a18`, pacchetto `review-12c0b2d..3610a18.diff`)

Ri-revisore Fable, 23/11/2026, sola lettura. Nessun subagente, nessuna rete, nessun `claude`. Suite non rilanciata (`suite-task-5-fix-1.log`: 4474 test `OK` sui due interpreti, come da report). Il diff tocca solo `docs/profili/security.md`, `docs/profili/verifiche/security-fonti.md` e `tests/test_rules_security.py`: skill, frammento, agenti e file approvati non sono cambiati.

Controlli mirati fatti sul codice al commit `3610a18` (con `git show`), uno per ogni frase nuova della pagina:

- `bin/tollgate_core/config.py:40`: `levels.sensitive_paths = ["**/migrations/**", "**/auth/**"]`. `bin/tollgate_analysis/level.py:41-43`: un percorso sensibile dà sempre L2. `bin/tollgate_checks/_common.py:322-328`: il ricalcolo prende il massimo fra il livello del diff e il `min_level` dei profili attivi; lo stesso minimo lo calcolano il gate (`bin/tollgate_gate/evaluate.py:148-158`) e `open-pr` (`bin/tollgate_flow/openpr.py:412-422`), quindi sotto `auth/` il minimo è L2 con o senza il profilo.
- Prova con `globs.match_any` (copia del solo `globs.py` nello scratchpad) sui percorsi che la pagina nomina. Sensibili già oggi: `src/components/auth/…`, `tests/auth/…`, `packages/auth/…`, `db/migrations/auth/…`, `vendor/lib/auth/…`, `public/auth/…`, `prisma/auth/…`, `app/api/auth/…`. Non sensibili: `infra/security/…`, `src/ai/middleware.ts`, `.github/security/…`, `db/rls/policies.sql` (questo è L2 solo se nel progetto è acceso `database`, per `**/*.sql` con `min_level = "L2"` in `templates/profiles/database.toml`).
- `bin/tollgate_analysis/profiles.py:40-43` (`active_profiles`: basta un file che corrisponde ai `paths`), `:28-37` (`vertical_for`), `:76-91` (`task_routing`: un implementatore e un revisore per task; con due agenti diversi i generici e `split`).
- `agents/reviewer-backend.md:5`, `agents/implementer-backend.md:5` (`skills: [rules-base, rules-backend]`), `agents/reviewer-database.md:5`, `agents/implementer.md:5` e `agents/task-reviewer.md:5` (`skills: [rules-base]`); `templates/profiles/security.toml` ha `skills = []` e `reviewer_skills = []`, e `bin/tollgate_analysis/brief.py` non mette nel brief le regole dei profili attivi: a livello di task nessuno riceve le regole di un'area che non è la sua.
- `bin/tollgate_checks/task_verdict.py:54-62`: le regole dei profili attivi sui file del task entrano solo in `known_rules` e `blocking_rules` del controllo del verdetto.
- `bin/tollgate_flow/finalreview.py:114-117`: in L2 la revisione finale aggiunge `final_specialists` dei profili attivi sul diff del lavoro. `final_specialist` c'è solo in `database.toml` e `security.toml`.
- `agents/final-database.md:38`: lo specialista giudica le regole sul diff e lascia al revisore del task quelle sul report. Per `final-security` (che arriva con il Task 7) la decisione 10 fissa la stessa forma.
- `docs/uso/comandi.md:124-127` (`--propose`, `--update`); `bin/tollgate_flow/init.py:45-46` (`TEST_DIRS`, `TEST_NAMES`); skill `rules-security` righe 36, 40, 48-50, 56-58 per m-1.
- Test mirato su una copia `git archive 3610a18` in `/tmp/tollgate-rev-…` (repo privato, cancellata alla fine; base 37 test `OK`): esito in m-9.

### Verdetti sui rilievi

**I-1 — la pagina presentava L2 sotto `auth/` come costo del profilo, e il rimedio dei punti 1 e 10 prometteva di toglierlo.** INDIRIZZATO.
`docs/profili/security.md:84` dice che sotto `auth/` il lavoro è L2 già oggi (con `migrations/`, e «salvo che tu abbia cambiato quell'impostazione»), che lì il profilo cambia chi scrive, chi rivede e aggiunge lo specialista, e per cosa L2 è nuovo. Vero contro `config.py:40` e `level.py:41-43`. I punti dicono il costo vero: 1 (`:130-131`, rimedio: «il lavoro resta L2 perché sta sotto `auth/`»), 2 (`:133`), 10 (`:157-158`, rimedio distinto fra `auth/` e `middleware.yaml`/`security/`), 13 (`:166`), 14 (`:169`: nuovo solo per `infra/security/` e il middleware; migrazione e pacchetto `auth` già L2, confermato dalla prova sui percorsi), 15 (`:172`). Dubbio 3 della mano Fable (punto 12, `:163`): la condizione «se nel progetto non è già acceso il profilo `database` (che porta in L2 ogni file `.sql`)» è vera e si legge.

**I-2 — «note a chi rivede» diceva più del vero.** INDIRIZZATO.
La formula non c'è più (nessuna riga con «note a chi rivede» o «restano note»). Il paragrafo nuovo `security.md:98` dice, e il codice conferma frase per frase: un solo agente che scrive e uno che rivede, quelli dell'area che vince, ognuno con le sole regole della sua area (`profiles.py:76-91`, frontmatter degli agenti); chi rivede può citare una regola di sicurezza e tollgate la accetta (`task_verdict.py:54-62`); lo specialista finale guarda a fine lavoro le regole sul diff (`finalreview.py:114-117`, `final-database.md:38`, decisione 10); le cinque sul report (1, 2, 15, 16, 17: corrispondono alla tabella) per quel task non le ha davanti nessuno; al contrario, per `database` c'è `final-database` sul diff e le altre quattro aree non hanno uno specialista (frammenti). Il costo è scritto nei punti 3 (`:136`, con «la 1 e la 17 bloccano»: vero), 1 (`:130`), 2 (`:133`), 4 (`:139`: generici con le sole regole di base, quelle di `backend` nessuno), 6 e 7 (rimando al punto 3), 12 (`:163`), 13 (`:166`), 14 (`:169`); la riga `:96` rimanda al paragrafo; la voce **Attivo** (`:31`) dice cosa vuol dire e cosa no; `:112` dice «chi scrive e chi rivede il task».

**m-1 — righe 4, 5, 9 della tabella e punto 31.** INDIRIZZATO. `security.md:63` (callback di un login, spiegata), `:64` (interruttore che spegne un controllo; valore finto nei test), `:68` (le due eccezioni, fedeli alla riga 56 della skill), `:220` (R-SECURITY-07: il divieto di spegnere il controllo della firma; R-SECURITY-09: `Secure` legato all'ambiente e `SameSite=None` con il motivo), fedeli alle `Fonte:` della skill (righe 50 e 58).

**m-2 — `crypto`, `hashlib`, `hmac` non sono marcatori.** INDIRIZZATO. `security.md:160` (punto 11).

**m-3 — termini non spiegati.** INDIRIZZATO. `security.md:32-35`: Frammento, Monorepo, Server Function, Policy.

**m-4 — come arriva la proposta.** INDIRIZZATO. `security.md:41`, uguale a `docs/uso/comandi.md:127` e alla pagina di `database` (`:41`).

**m-5 — il costo del rinvio.** INDIRIZZATO. `security.md:231`, coerente con la decisione 19 (C3 è il profilo `ci`, decisione 10).

**m-6 — una riga in testa a «Da decidere tu».** INDIRIZZATO. `security.md:128`: sette punti (5, 19, 25, 30, 28, 21, 22), tutti scelte vere; il conteggio «sette» corrisponde. Vedi la nota Minor 3 sotto.

**m-7 — rapporto, i file di test.** INDIRIZZATO. `security-fonti.md:136`, fedele a `init.py:45-46`.

**m-8 — rapporto, i ritocchi riletti.** INDIRIZZATO. `security-fonti.md:11`, coerente con la revisione del Task 5.

**m-9 — i test non provavano i punti che nominano una regola.** INDIRIZZATO. `tests/test_rules_security.py:386` (`CHOICE_POINTS`: parole nel titolo in grassetto e nel testo dello stesso punto), `:459` (`choice_points`), `:711` (gli id «scelta nostra» cercati solo nel punto con quel titolo, che deve essere uno), `:652` (`test_page_explains_what_changes` cerca nelle due sezioni giuste). Sulla mia copia, con il conteggio aggiornato: tolto il punto 25, rosso («R-SECURITY-08 blocca o no»); tolti 21, 22, 25, 27, 28, 29, sei rossi, uno per punto; tolto il 6, il 2, il 4 o il 31, rosso ciascuno. Approvazione simulata (`approved` nella skill, «Da decidere tu» e «Rinvio» tolti): 3 test saltati, rosso solo `RulesSecurityTest.test_frontmatter` (del Task 4, il Task 6 lo cambia per forza). Nessun test fissa testo che il Task 6 deve cambiare senza `skip_if_approved`. Il report nomina i test e ne mostra l'uscita; le sue affermazioni reggono sul diff.

### Danni nuovi nel diff della correzione

Nessuno Critical o Important. Tre Minor, nessuno cambia una decisione dell'utente:

1. **Minor — `docs/profili/security.md:131` e `:158` (dubbio 4 della mano Fable, non risolto nel testo).** «senza lo specialista» e «toglie … lo specialista» valgono per un lavoro che tocca solo quel file. Se lo stesso lavoro tocca un altro file del profilo, `final-security` parte lo stesso e guarda tutto il diff, quel file compreso (`finalreview.py:114-117`). L'errore va dal lato prudente: l'utente riceve più controllo di quello scritto. Basterebbe «(se il lavoro non tocca altri file del profilo)».
2. **Minor — `security.md:31` (voce «Attivo»).** «Vuol dire tre cose» ne salta una: con il profilo attivo tollgate lancia anche i suoi comandi di gate e di `dod` (`bin/tollgate_core/runner.py:47-66`). Per `security` oggi sono vuoti e la pagina lo dice più sotto («`dod` e comandi restano vuoti»), quindi nessun effetto finché l'utente non ne aggiunge.
3. **Minor — `security.md:128` (m-6).** Fra «gli altri sono costi da conoscere» restano due punti con una scelta vera accanto: il 18 (`iron-session`, al confine con la scelta dell'utente «niente session») e il 6 (`keep_paths` esteso a middleware e proxy, «scelta nostra»). La riga comincia con «Se hai poco tempo» e ogni punto ha la sua proposta, quindi non inganna; nominarli la renderebbe completa.

Nota sul punto 12 (`:163`), non un rilievo: la frase sul livello vale per i file `.sql` di `rls/`; un file non `.sql` in `rls/` sale a L2 con questo profilo anche se `database` è acceso. La parentesi lo lascia capire.

### Osservazioni fuori ambito

- `W/task-5-proposte.md` è la copia della sezione «Da decidere tu» al commit `3610a18` (`diff`: solo la riga vuota in coda, come nella revisione). 31 punti nell'elenco, «trentuno» nell'introduzione (`:3`) e in testa alla sezione (`:128`).
- Nessun nome utente, host o `/home/` nei due documenti (conteggio 0, senza stampare). Nessuna citazione nuova nella pagina; nel rapporto le due righe nuove non citano terzi.
- La pagina descrive `final-security` prima che esista (dubbio 1 della mano Fable): se il Task 7 scrive l'agente in modo diverso dalla decisione 10, il paragrafo `:98` e il punto 3 vanno riletti.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.

Le frasi nuove su L2 e su chi ha caricate quali regole sono vere contro il codice. I tre Minor si possono correggere con poche parole prima di mandare la pagina all'utente, oppure lasciare: nessuno porta l'utente a una scelta sbagliata.
