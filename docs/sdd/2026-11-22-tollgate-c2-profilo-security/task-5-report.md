# Task 5: report

## Mano 1 (Step 2)

**Status:** DONE. Mano opus, solo test. Nessun commit, nessuna suite completa, nessun documento scritto; `git add tests/test_rules_security.py` fatto (file in stato `M ` nell'indice). Nessun subagente, nessuna rete, nessun `claude`.

### I test scritti

In `tests/test_rules_security.py` una classe nuova `RulesSecurityPageTest` (16 test), dopo `RulesSecurityTest`, sul modello di `RulesDatabasePageTest` nella forma **prima** dell'approvazione (commit di B7 `eec75d2`, recuperato dal ramo `349bb5b..33968ca`: la storia di `main` è schiacciata in `02f900c`). Il file legge i file veri (nessun prefisso `test_real_`). Costanti nuove: `PAGE`, `SOURCES`, `ID`, `REPORT_SECTIONS`, `OURS`, `REMOVED_SOURCE`, `APPROVED_ID`, `TERMS`, `CHOICE_CASES`, `S53_PHRASE`, `CHOICE_NEEDLES`, `RINVIO_NEEDLES`, `NUMBERS`; funzioni `normal`, `as_number` (fino a quaranta), `voci`, `cases_named`. Importa solo funzioni e costanti da altri moduli di test (`table_rows`, `NUMBER_WORDS`), nessuna classe, quindi nessun test duplicato. Righe entro 100 caratteri; ogni ciclo controlla prima che l'elenco non sia vuoto; messaggi fissi sulle asserzioni del testo lungo; conteggi ed elenchi (regole, `[blocca]`, «Si giudica su», sovrapposizioni, regole «scelta nostra», pattern, marcatori) calcolati dalla skill e dal frammento.

1. `test_sources_report_covers_every_rule`: le cinque sezioni del rapporto; ogni voce di ogni `Fonte:` ha una riga `ok` della sua regola; ogni regola con «scelta nostra» nella `Fonte:` è nominata nella sezione «Parti dichiarate «scelta nostra»».
2. `test_removed_sources_are_not_in_the_skill`: l'unica riga `no` è di R-SECURITY-10 ed è la voce uscita; la skill non la porta più; R-SECURITY-10 ha ancora una riga `ok`.
3. `test_path_patterns_verified`: i pattern `ok` sono esattamente quelli del frammento.
4. `test_detect_markers_verified`: i marcatori `ok` (a meno delle virgolette) sono esattamente quelli del frammento; una riga `no` non è di un marcatore del frammento.
5. `test_no_long_quotations`: la skill (citazioni in «» al più 12 parole); rapporto e pagina (ogni «» su una riga, al più 30 parole, almeno una); la pagina non riporta una citazione di terzi del rapporto di più di 10 parole (confronto senza maiuscole).
6. `test_page_lists_every_rule`: righe della tabella di «Le regole» = id della skill, nell'ordine, cella «N.» nella forma `<n> (R-SECURITY-<nn>)`.
7. `test_page_blocca_matches_skill`.
8. `test_page_judged_on_matches_skill`.
9. `test_page_explains_what_changes`: come si accende, L2, lo specialista, `dod` vuoto con l'esempio, i modelli degli agenti, la sicurezza fin dal progetto, `supabase/` escluso alla radice, `keep_paths`.
10. `test_page_lists_overlaps`: una riga per coppia (regola di `security`, id approvato) delle righe «Si sovrappone a:» della skill, niente di più.
11. `test_page_brings_the_open_choices_to_the_user` (salta se la skill ha `approved`).
12. `test_page_choices_count_matches_list` (salta se approvata).
13. `test_page_counts_match_skill` (la parte su «Da decidere tu» solo prima dell'approvazione).
14. `test_page_explains_the_terms`.
15. `test_page_has_no_private_data` (pagina e rapporto).
16. `test_page_rinvio_says_what_stays_on_the_branch` (salta se approvata).

### Evidenza RED

Comando: `python3 -B -m unittest tests.test_rules_security` (uguale con `python3.11`).

```
ERROR: test_detect_markers_verified (RulesSecurityPageTest.test_detect_markers_verified)
ERROR: test_no_long_quotations (RulesSecurityPageTest.test_no_long_quotations)
ERROR: test_page_blocca_matches_skill (RulesSecurityPageTest.test_page_blocca_matches_skill)
ERROR: test_page_brings_the_open_choices_to_the_user (...)
ERROR: test_page_choices_count_matches_list (...)
ERROR: test_page_counts_match_skill (...)
ERROR: test_page_explains_the_terms (...)
ERROR: test_page_explains_what_changes (...)
ERROR: test_page_has_no_private_data (...)
ERROR: test_page_judged_on_matches_skill (...)
ERROR: test_page_lists_every_rule (...)
ERROR: test_page_lists_overlaps (...)
ERROR: test_page_rinvio_says_what_stays_on_the_branch (...)
ERROR: test_path_patterns_verified (...)
ERROR: test_removed_sources_are_not_in_the_skill (...)
ERROR: test_sources_report_covers_every_rule (...)
Ran 37 tests in 0.092s
FAILED (errors=16)
```

Tutti per `FileNotFoundError` su `docs/profili/verifiche/security-fonti.md` o `docs/profili/security.md`. `python3 -B -m unittest tests.test_rules_security.RulesSecurityTest`: `Ran 21 tests … OK` con i due interpreti.

**Con i file presenti ma senza il contenuto giusto** (prove su file temporanei `mkdtemp(prefix="tollgate-t5-")`, cancellati a fine corsa, con `SOURCES` e `PAGE` del modulo sostituiti in memoria; gli script stanno nello scratchpad della sessione, fuori dal repo):

- **Rapporto costruito da `task-5-fonti.md`** (esiti ripuliti alla sola parola `ok`/`no`, più la riga `ok` della seconda passata per la voce nuova di R-SECURITY-10, più le due sezioni mancanti): i quattro test del rapporto **passano**. Quindi la divisione delle voci regge sulla tabella vera (anche le due voci di R-SECURITY-07 unite da « e »). Mutazioni, ognuna fa scattare una sola asserzione:
  - commento nella cella Esito (`ok (nota)`): `test_sources_report_covers_every_rule`, «'ok (nota)' not found in ('ok', 'no') : l'esito è `ok` o `no`, senza altro testo»;
  - tolta la riga `ok` della voce nuova di R-SECURITY-10: `test_sources_report_covers_every_rule (rule='R-SECURITY-10', …)`, «nessuna riga `ok` del rapporto per questa voce»;
  - un pattern rinominato (`**/rlsx/**`): `test_path_patterns_verified`, `'**/rls/**'` mancante;
  - un marcatore tolto (`from 'jsonwebtoken'`) messo come `ok`: `test_detect_markers_verified`, «il rapporto verifica un marcatore che non c'è più».
- **Pagina di prova** con le tabelle di «Le regole» e «Regole che si sovrappongono» generate dalla skill e le altre sezioni quasi vuote: `test_page_lists_every_rule`, `test_page_blocca_matches_skill`, `test_page_judged_on_matches_skill`, `test_page_lists_overlaps` **passano**; scattano gli altri, per esempio `test_page_brings_the_open_choices_to_the_user` («mancano dei casi della tabella in «Da decidere tu»», con l'elenco dei casi; l'intervallo `S61-S64` è riconosciuto), `test_page_choices_count_matches_list` («2 not greater than or equal to 20»), `test_page_counts_match_skill` («manca «N regole, di cui M bloccano» in «Da decidere tu»»), `test_page_explains_the_terms` (un `subTest` per termine), `test_page_explains_what_changes` (un `subTest` per testo), `test_page_rinvio_says_what_stays_on_the_branch` (`c2-parziale`, `modelli`, …). Mutazioni: un `sì` diventato `no` nella riga 8 → `test_page_blocca_matches_skill`; una sovrapposizione tolta → `test_page_lists_overlaps` (`('R-SECURITY-12', 'R-BACKEND-06')`).
- **Citazioni e dati privati**: pagina con una frase di `security-and-hardening` copiata (con l'iniziale minuscola) → `test_no_long_quotations`, «la pagina riporta una citazione di una fonte di terzi»; una citazione di 31 parole → «31 not less than or equal to 30»; un JWT d'esempio → `test_page_has_no_private_data`, «False is not true : una forma di token o di chiave compare nel testo» (il valore non si stampa).

Due difetti trovati con queste prove e corretti prima del report: il confronto delle citazioni copiate distingueva le maiuscole (ora no); `assertFalse(re.search(…))`, preso da B7, stampava l'oggetto `Match`, cioè il token o il nome utente o l'host trovato; ora le asserzioni sono `assertTrue(… is None, "…")`. Il difetto c'è ancora in `tests/test_rules_database.py` e `tests/test_rules_frontend.py` (verificato con `grep`), che non tocco: lo segnalo.

### Per la seconda mano: i vincoli di forma, uno per uno

**Generali (tutti e due i file)**
- Ogni citazione tra «» sta su una sola riga e ha al più **30 parole** (contate con `split()`); ogni file ha almeno una citazione tra «».
- Nessuna stringa `/home/`; nessun nome utente né host (come parola intera, senza maiuscole); nessuna forma di token o chiave: `sk-ant`, `ghp_`, `github_pat_`, `eyJ` seguito da 10 o più caratteri `[A-Za-z0-9_-]`, `-----BEGIN`. Niente JWT d'esempio, nemmeno finti.

**Rapporto `docs/profili/verifiche/security-fonti.md`**
- Titoli esatti, ognuno su una riga sua: `## Regole e fonti`, `## Pattern dei percorsi`, `## Marcatori di contenuto`, `## Parti dichiarate «scelta nostra»`, `## Regole tolte dalla verifica`. Altre sezioni (per esempio `## Sovrapposizioni`, `## Riepilogo`) sono ammesse.
- In ognuna delle tre tabelle **l'ultima colonna è l'esito ed è esattamente `ok` o `no`**, senza grassetto e senza altro testo. Le osservazioni che `task-5-fonti.md` mette nella cella Esito («ok (pagina ufficiale: fatti)», «ok, al confine», «no: la sezione 11 …») vanno spostate nella cella della citazione o in una riga di testo sotto la tabella.
- `## Regole e fonti`: intestazione `| Regola | Fonte (pagina, sezione) | Citazione | Esito |`. Cella 1 = l'id (`R-SECURITY-NN`, solo id della skill); cella 2 = la voce della `Fonte:`, che deve **contenere alla lettera** (spazi normalizzati) la voce com'è scritta nella skill dopo i ritocchi. Una riga `ok` per ogni voce. Le voci si contano così: si divide la `Fonte:` sui `;` fuori dalle parentesi; si saltano le parti con «scelta nostra» o «esempi nostri»; dentro una parte si divide su `, e ` o ` e ` seguiti da `https://`, `spec del nucleo`, una cifra-punto-cifra o `` `security- ``. Quindi R-SECURITY-07 dà due righe per le pagine (jsonwebtoken; PyJWT) e due per agent-skills: la riga di `security-and-hardening` contiene «`security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Security Review Checklist»», quella di `security-auditor` contiene «`security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» (i token di reset scadono)». Se un ritocco della skill cambia il testo di una `Fonte:`, la cella del rapporto cambia con lui.
- Le righe `no` di quella tabella: **una sola**, di `R-SECURITY-10`, con nella cella 2 la voce vecchia (deve contenere «nessun segreto nel codice né nei log», per esempio «progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: nessun segreto nel codice né nei log)»). Serve anche la riga `ok` della voce nuova («progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: i segreti si considerano in ogni lavoro)», seconda passata in `task-4-rereview-1.md`).
- `## Pattern dei percorsi`: cella 1 = il pattern tra backtick e nient'altro (`` `**/auth/**` ``); una riga `ok` per ognuno dei sei pattern del frammento, nessuna riga `ok` di un pattern che il frammento non ha.
- `## Marcatori di contenuto`: cella 1 = il marcatore tra backtick e nient'altro; una riga `ok` per ogni marcatore del frammento (basta una delle due virgolette, ma le 21 righe di `task-5-fonti.md` vanno bene); nessuna riga `ok` di un marcatore che non c'è. I quattro marcatori tolti, se si vogliono in tabella, solo come `no`.
- `## Parti dichiarate «scelta nostra»`: nomina per id ogni regola che ha «scelta nostra» nella `Fonte:` (oggi tutte e 17, da R-SECURITY-01 a R-SECURITY-17).
- Nelle tre tabelle, le righe la cui cella 2 non comincia con `progetto di`, `catalogo` o `spec del nucleo` sono «di terzi»: deve esserci almeno una loro citazione di più di 10 parole (c'è già), e nessuna di queste può comparire nella pagina.
- La barra verticale dentro una cella resta scritta `\|` (come nella citazione del catalogo): il test divide le celle sulla barra, e regge solo se le barre in più stanno nella colonna della citazione.

**Pagina `docs/profili/security.md`**
- Sezioni con questi titoli esatti: `## Cosa sono`, `## Le regole`, `## Cosa cambia nei tuoi progetti`, `## Regole che si sovrappongono`, `## Da decidere tu`, `## Come rispondere`. Prima di `## Cosa sono` l'introduzione contiene «su quali <N> punti» con N il numero dei punti di «Da decidere tu» (in lettere o in cifre).
- `## Cosa sono` contiene «Sono <N> regole in più» (N = 17) e «<M> di queste bloccano» (M = 13; anche «Tredici di queste bloccano»).
- Termini in grassetto, alla lettera, in qualunque punto della pagina: `**Autenticazione**`, `**Autorizzazione**`, `**Token**`, `**Sessione**`, `**Middleware**`, `**Specialista finale**`, `**Proxy**`, `**Hash**`, `**Profilo**`, `**Livello L2**`, `**Marcatore**`, `**Percorso esatto**`, `` **`dod`** ``.
- `## Le regole`: intestazione `| N. | In parole semplici | Blocca? | Si giudica su | Da dove viene |` (cinque colonne, come ai, infra, backend, frontend, database). Una riga per regola, nell'ordine; cella 1 = `<n> (R-SECURITY-<nn>)` (per esempio `1 (R-SECURITY-01)`); cella 3 = `sì` o `no` secondo `[blocca]`; cella 4 = `il diff` o `il report` secondo «Si giudica su». In questa sezione nessun'altra tabella con un id `R-SECURITY-` nella prima cella.
- `## Cosa cambia nei tuoi progetti` deve esistere; i testi sotto si cercano in **tutta** la pagina (spazi normalizzati):
  - regex `` `/tollgate:init`[^.]*propone[^.]*\btu copi\b `` (una frase senza punti, per esempio «… il comando `/tollgate:init` lo propone e tu copi il blocco …»);
  - regex `lavoro[^.]*\bL2\b[^.]*spec[^.]*piano`; regex `specialista finale[^.]*\bL2\b`; regex `attivo[^.]*\bL2\b`;
  - la parola `opus` (minuscola, parola intera) e la parola `Fable` (qualunque maiuscola); regex senza maiuscole `sicurezza fin dal progetto`;
  - regex `` `supabase/`[^.]*alla radice `` oppure `` alla radice[^.]*`supabase/` ``;
  - alla lettera: `` `min_level = "L2"` ``, `` `level_below_minimum` ``, `` `final-security` ``, `` `/tollgate:finish` ``, `` `implementer-security` ``, `` `reviewer-security` ``, `` `Sicurezza:` ``, `` `keep_paths` ``, `` `dod` ``, `denied = "python3 -m unittest discover -s tests -k denied"` (la riga d'esempio della decisione 12), `credenziali vere`, `senza chiedere`.
  - Attenzione ai `[^.]`: un nome di file con il punto (`proxy.ts`) dentro la frase la spezza.
- `## Regole che si sovrappongono`: una tabella a **tre colonne**, intestazione `| Regola di security | Regola approvata | Cosa cambia |` (i nomi delle colonne non si controllano, il numero sì). **Una riga per coppia**: cella 1 con un solo id `R-SECURITY-NN`, cella 2 con un solo id approvato, cella 3 non vuota. Le righe sono esattamente sette: R-SECURITY-10 con R-BACKEND-07, R-BACKEND-08, R-INFRA-05, R-INFRA-06, R-DATABASE-13; R-SECURITY-12 con R-BACKEND-03, R-BACKEND-06. Nessuna riga per R-SECURITY-17 (R-INFRA-12, R-DATABASE-16, R-BACKEND-12, segnalate dal verificatore): se si vuole dirlo, in una frase sotto la tabella.
- `## Da decidere tu`:
  - una frase «Su <N in lettere> punti» (N = numero dei punti; «uno» non vale); almeno **20** punti; il dizionario arriva a quaranta;
  - ogni punto comincia a inizio riga con `<n>. **` (numero, punto, spazio, grassetto), ha `Costo: ` nel testo e **una sola** riga che comincia con spazi e poi `Proposta: ` (rientrata, come in B7);
  - la frase «<N> regole, di cui <M> bloccano» (17 e 13, in lettere o in cifre), nella forma esatta con la virgola;
  - tutti questi casi, scritti come `S<n>` (un intervallo `S61-S64` o `S68–S71` vale per i casi che contiene; attenzione: `S4` deve comparire da solo, `S49` non lo conta): S4, S39, S54, S49, S50, S61, S62, S63, S64, S53, S51, S52, S16, S9, S46, S57, S59, S13, S34, S19, S40, S44, S68, S69, S70, S71, S11, S56, S67;
  - la frase del piano per S53, alla lettera (senza maiuscole): «un file di login dentro una cartella del server va agli agenti di sicurezza; fuori da una cartella del server resta a quelli del server»;
  - questi testi alla lettera, uno per punto: `` `vendor/ `` (codice di terzi), `` `public/auth/` ``, `` `i18n/auth/` ``, `` `middleware.yaml` ``, `` `**/proxy.ts` `` (aggiunti al catalogo), `` `middleware/` ``, `` `Auth/` ``, `` `proxy.page.ts` ``, `` `_middleware.ts` ``, `` `import jwt` ``, `jwt-decode`, `jose`, `iron-session`, `require('bcryptjs')` e `from 'jsonwebtoken'` (i marcatori tolti, con le virgolette semplici), `` `supabase/` ``, `annidat` (la `supabase/` annidata), `` `supabase/functions/auth/**` `` (rimedio a mano di S67), `` `keep_paths` ``, `` `dod` ``, `scelta nostra`, `R-SECURITY-10`, `R-SECURITY-12`, `R-SECURITY-08` (blocca o no), `R-SECURITY-01` e `R-SECURITY-16` (vicine), `R-SECURITY-09` (le due forme e il loro costo), `R-SECURITY-15` (non blocca, sul report), `` `hmac.compare_digest` `` e `` `crypto.timingSafeEqual` `` (esempi nostri), `` `.tsx` `` con i backtick attorno a `.tsx` soli (N4: un `.tsx` dentro `auth/` fuori da `components/` va a `security`), `agenti generici` (N9);
  - ogni regola con «scelta nostra» nella `Fonte:` nominata per id (oggi tutte e 17): un punto «I temi «scelta nostra»» con l'elenco degli id, come il punto 17 di B7.
- `## Come rispondere`: **un solo** paragrafo che comincia a inizio riga con `**Rinvio.**`, tutto su una riga, che contiene alla lettera: `` `main` ``, `` `c2-profilo-security` ``, `` `c2-parziale` ``, `i Task 1, 2 e 3`, `modelli`, `sicurezza fin dal progetto` (minuscolo), `` `keep_paths` ``, `` non vanno su `main` `` (la bozza, la pagina e il frammento restano sul ramo e non vanno su `main`).
- Nessuna citazione di terzi del rapporto (più di 10 parole) nella pagina, nemmeno tradotta alla lettera o con l'iniziale cambiata; vale anche per le frasi delle schede del controller (`idea letta dal controller …`) e per i «fatto del controller». Le frasi del progetto di C, del catalogo e della spec si possono riprendere.
- Prima dell'approvazione la pagina non dice «Approvata dall'utente» (lo cambia il Task 6).

### Scostamenti dal piano e perché

- **Colonna «Si giudica su».** Lo Step 3 del piano dà la tabella «N. · In parole semplici · Blocca? · Da dove viene», ma lo Step 2 chiede `test_page_judged_on_matches_skill`, che la vuole, e tutte le pagine da B3 in poi hanno cinque colonne. Il test fissa cinque colonne.
- **Due sezioni in più fissate:** `## Le regole` (per separare la tabella delle regole da quella delle sovrapposizioni, che ha anch'essa id `R-SECURITY-` nella prima cella) e `## Cosa sono` con l'introduzione «su quali N punti» (forma di B7).
- **`test_no_long_quotations`** copre tre documenti invece della sola skill: la skill (12 parole, come B7), rapporto e pagina (una riga, 30 parole, come `test_sources_quotations_are_one_line` di B7) e la pagina contro le citazioni di terzi del rapporto (la regola «più di una decina di parole» dello Step 1).
- **Termini:** oltre ai sei del piano, `Proxy`, `Hash`, `Profilo`, `Livello L2`, `Marcatore`, `Percorso esatto`, `` `dod` ``, dalle pagine di B7: la pagina li usa e la preferenza dell'utente è di parole semplici. Costa sette voci di glossario; si tolgono dalla costante `TERMS` se il controller non le vuole.
- **`voci()` propria** e non quella di B7: salta anche «esempi nostri» (R-SECURITY-08) e divide le voci di agent-skills unite da «, e» (R-SECURITY-07), come fa la tabella del verificatore.
- **`as_number` fino a quaranta** (quella di `test_rules_frontend` arriva a trenta): i punti di «Da decidere tu» sono quasi trenta.
- **`skip_if_approved`** anche su `test_page_choices_count_matches_list` e sulla parte di `test_page_counts_match_skill` che legge «Da decidere tu» (in B7 il conteggio non saltava): dopo l'approvazione quella sezione non c'è più, e il Task 6 scrive i suoi test.
- **Asserzioni sui dati privati con `is None`** invece di `assertFalse(re.search(…))` di B7, perché quella forma stampa il valore trovato.

### Dubbi

1. N4 e N9 hanno parole chiave deboli (`` `.tsx` ``, `agenti generici`): non trovo una parola che li distingua meglio senza imporre una frase. Se il controller ne vuole una precisa, basta cambiare le due voci di `CHOICE_NEEDLES`.
2. Il confronto «nessuna citazione di terzi nella pagina» conta come terzi anche le schede del controller (idee CC BY-SA): la seconda mano deve parafrasarle, non riusarle. Mi sembra la parte sicura; se il controller considera le schede parole nostre, la condizione della riga «di terzi» va ristretta.
3. Il rinvio chiede `i Task 1, 2 e 3` alla lettera: è la forma della decisione 19 («I Task 1, 2 e 3 sono indipendenti …»).
4. La riga di R-SECURITY-17 senza «Si sovrappone a:» (osservazione del verificatore) resta fuori dalla tabella delle sovrapposizioni, come chiede il dispatch; se l'utente o il controller la vogliono dentro, cambiano insieme la skill (riga «Si sovrappone a:») e la costante `OVERLAPS`, e il test segue da solo.
5. `tests/test_rules_database.py` e `tests/test_rules_frontend.py` stampano il nome utente o l'host se un giorno li trova: fuori dal mio compito, da segnalare per C3 o per un rinvio.

## Mano 2 (Step 3)

Fable, 23/11/2026, sopra il commit `1749ee8`. Tre cose: i ritocchi alla skill, il rapporto delle fonti, la pagina per l'utente; più la copia di «Da decidere tu» in `task-5-proposte.md` (nel workspace). Nessun commit, nessuna suite completa, nessun subagente, nessuna rete. `git add` dei due file nuovi (`docs/profili/security.md`, `docs/profili/verifiche/security-fonti.md`); `skills/rules-security/SKILL.md` è modificato e **non** in indice. Nessun test toccato.

### 1. Ritocchi alla skill (6 righe cambiate, 107 righe in tutto)

Frontmatter, titolo, introduzione, numero, ordine e stato `[blocca]` delle regole invariati; `Si sovrappone a:` solo in 10 e 12 con gli stessi id. Nessuna voce di fonte cambia: cambia solo la frase «scelta nostra» di R-SECURITY-05.

**N2 (R-SECURITY-04): «dati pubblici» definiti, frase spezzata**

> R-SECURITY-04 [blocca] Se il diff aggiunge o cambia una funzione del server che legge o cambia dati legati a un utente (un endpoint, un gestore di rotta, una Server Function), il controllo di chi chiama gira sul server per quella funzione, mai solo nel codice del browser: dentro di essa o in una guardia applicata alla sua rotta (per una Server Function di Next.js solo dentro di essa: `proxy.ts` o `middleware.ts` da soli non bastano). Dove il dato ha un proprietario, il codice lo confronta con il chiamante. Non si applica a una funzione che è essa stessa il login, la registrazione, la richiesta di reset o la callback di un login. Non si applica nemmeno a una funzione che legge solo dati pubblici (dati che chiunque può già leggere senza login), se il diff lo dichiara dove registra la rotta o in un commento accanto.

**Valori finti nei test (R-SECURITY-05)**

> R-SECURITY-05 [blocca] Se il diff aggiunge o cambia codice che legge un segreto (anche una chiave di firma) o un'impostazione di sicurezza, quando il valore manca il codice si ferma o nega l'accesso. Per un segreto nessun valore di ripiego scritto nel codice (come `process.env.X || "…"` o `os.environ.get("X", "…")`). Per un'impostazione di sicurezza l'unico ripiego ammesso è il valore che nega (un elenco vuoto, il controllo acceso). Sono impostazioni di sicurezza solo queste: l'elenco delle origini ammesse, l'elenco dei ruoli ammessi, un interruttore che spegne un controllo. Un controllo d'accesso che non riconosce il caso (un ruolo sconosciuto, il ramo `default`) nega. Nei file di test un valore finto evidente (come `PROVA-123`) è ammesso.
> Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: valori predefiniti chiusi); idea di Trail of Bits `insecure-defaults` (senza un segreto o una configurazione il programma rifiuta, non ripiega su un valore permissivo); idea di OWASP Cheat Sheet «Authorization» (si nega quando nessuna regola concede); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Sensitive Data Exposure» (l'esempio si ferma se la chiave non è configurata); gli esempi di ripiego, l'elenco chiuso delle impostazioni e i valori finti ammessi nei test sono una scelta nostra

**N3 a, b (R-SECURITY-09): «dichiara accesi», il motivo di `SameSite=None`**

> R-SECURITY-09 [blocca] Se il diff costruisce da sé un cookie di sessione (l'intestazione `Set-Cookie`, una chiamata come `res.cookie` o `cookies().set` con opzioni proprie), il codice dichiara accesi `HttpOnly` e `Secure` e dichiara `SameSite`; un `Secure` legato all'ambiente (vero in produzione) vale come dichiarato. Se il cookie lo scrive una libreria di sessioni o di login, il diff non ne indebolisce le opzioni (`httpOnly: false`, `secure: false`). In tutti e due i casi `SameSite=None` è ammesso solo insieme a `Secure` e con il motivo scritto accanto, che dice quale altro sito deve mandare il cookie. Il codice del diff non salva un token di sessione o d'accesso dove il JavaScript della pagina può leggerlo (come `localStorage`).

**N1 (R-SECURITY-10): la password nelle risposte, il token di reset mai**

> R-SECURITY-10 [blocca] Nessun segreto scritto nel codice, in un file versionato o in un test: nei test solo valori finti evidenti (come `PROVA-123`). Nessun segreto, token, password o hash di password in una riga di log o in un messaggio d'errore. Nel corpo di una risposta nessuna password, nessun hash di password e nessun segreto del server, e mai un token di reset, nemmeno a chi lo chiede; il token consegnato al chiamante a cui appartiene (la risposta di un login, una chiave d'API mostrata al suo titolare quando la crea) non è questo caso.
> Si sovrappone a: R-BACKEND-07, R-BACKEND-08, R-INFRA-05, R-INFRA-06, R-DATABASE-13. Qui vale per ogni file dell'area, anche fuori da un server o da una configurazione, e comprende i test e, nelle risposte, le password, gli hash delle password e i token di reset.

In R-SECURITY-09 ho scritto «dichiara accesi `HttpOnly` e `Secure` e dichiara `SameSite`»: `SameSite` non è un interruttore acceso o spento, ha un valore; il caso `None` lo regola la frase dopo.

### 2. Rapporto delle fonti

`docs/profili/verifiche/security-fonti.md` (176 righe), generato dalle tabelle di `task-5-fonti.md` con uno script (nello scratchpad della sessione, fuori dal repo), poi letto. Le cinque sezioni fissate più «Sovrapposizioni». «Regole e fonti»: 43 righe, 42 `ok` e la riga `no` di R-SECURITY-10 (voce uscita), seguita dalla riga `ok` della voce nuova (seconda passata). Le note che il verificatore metteva nella cella dell'esito sono in coda alla cella della citazione («Nota del verificatore: …»): l'ultima colonna è solo `ok` o `no`. Le dieci voci CC BY-SA portano «idea letta dal controller sulla pagina». L'intestazione dice chi ha verificato (Explore su Fable, sola lettura, 23/11/2026, commit `abccbe0`), la seconda passata (`1749ee8`) e che i quattro ritocchi di oggi **non sono ripassati dal verificatore**. Marcatori tolti dal controller e assenza di ASVS e di `security-review` sono detti nel testo. Nessun percorso della home, nessun nome utente o host; delle copie restano solo i nomi `pagine/marcatori.md` e `pagine/nextjs-proxy.md`.

### 3. Pagina per l'utente

`docs/profili/security.md` (226 righe). Sezioni: «Cosa sono» (con 21 termini spiegati), «Quando si accende», «Le regole», «Cosa cambia nei tuoi progetti», «Regole che si sovrappongono» (7 righe), «Da decidere tu» (31 punti), «Regole tolte dalla verifica», «Come rispondere» con il paragrafo **Rinvio.** Nessun conteggio dei file dell'utente, nessun nome di progetto o di cartella suoi: gli esempi di percorso sono quelli della tabella della decisione 5.

Punti di «Da decidere tu», con la proposta:

1. I moduli di login dell'interfaccia vanno agli agenti di sicurezza. → lasciare così, perché un modulo di login tratta password; chi non lo vuole toglie quel percorso dal blocco prima di copiarlo.
2. Ogni schermata dentro una cartella `auth/`. → lasciare così.
3. Le rotte di login che `backend` riconosce restano a `backend`. → lasciare così.
4. Un file e il suo test possono finire a due gruppi diversi. → lasciare così; se capita spesso in un progetto, togli dal blocco uno dei due percorsi.
5. Un file di login dentro una cartella del server. → lasciare così: un file di login lo scrive chi ha caricate le regole di sicurezza.
6. Middleware e proxy riconosciuti anche da un altro profilo. → tenere l'estensione; senza, in questi casi `security` non si accenderebbe affatto.
7. Cartelle di altri profili dentro `auth/`. → lasciare così.
8. Middleware e proxy che non c'entrano con la sicurezza. → lasciare così, perché nella maggior parte dei progetti quel nome è davvero il controllo del login; chi ha un caso toglie il percorso dal blocco.
9. `**/proxy.ts` e `**/proxy.js` aggiunti all'elenco. → tenerli.
10. File che non sono codice di login dentro `auth/` o `security/`. → lasciare così. Il rimedio è gratuito: togli quel percorso dal blocco proposto prima di copiarlo nel `tollgate.toml`.
11. Forme che restano fuori. → lasciarle fuori per ora; chi ne ha le aggiunge a mano al blocco, e si riprendono alla prossima revisione delle regole.
12. Regole di accesso e schemi del database dentro `rls/` o `auth/`. → lasciare così; chi tiene le policy in una cartella `rls/` può togliere quel percorso dal blocco.
13. Configurazione, istruzioni per i modelli e automazioni dentro `auth/` o `security/`. → lasciare così, sono comunque file che parlano di accessi.
14. `auth/` e `security/` dentro le cartelle degli altri profili. → lasciare così; per la migrazione le regole di `database` restano note a chi rivede.
15. Test e documenti. → lasciare così.
16. Il marcatore `import jwt`. → tenerlo; un file che legge un token merita comunque queste regole.
17. Il marcatore `jose`. → tenerlo.
18. `iron-session`. → tenerla; se in un progetto pesa, togli quei percorsi dal blocco.
19. Due marcatori tolti. → lasciarli fuori. Se li vuoi, dimmelo: si rimettono, dichiarati come scelta tua.
20. La cartella `supabase/`. → lasciare così, è la tua scelta del progetto di B.
21. R-SECURITY-10 ripete cinque regole approvate. → tenerla; senza, un file di login che va a `security` non avrebbe nessuna regola sui segreti caricata.
22. R-SECURITY-12 ripete due regole approvate. → tenerla, per lo stesso motivo.
23. La regola 17 somiglia a tre regole approvate. → lasciarla così. Se la vuoi tra le sovrapposizioni, è un cambio di una riga.
24. `dod` vuoto. → lasciarlo vuoto, come negli altri profili.
25. R-SECURITY-08 blocca oppure no. → farla bloccare, perché correggerlo costa una riga.
26. Gli esempi di R-SECURITY-08 sono nostri. → tenerli, perché dicono a chi scrive cosa usare. In alternativa si tolgono senza toccare la regola.
27. R-SECURITY-01 e R-SECURITY-16 sono vicine. → tenerle separate: sono due domande diverse e la prima blocca, la seconda no. Se le trovi doppie, si uniscono nella prima.
28. Le due forme di R-SECURITY-09. → tenere la forma scritta, per non fermare codice corretto.
29. R-SECURITY-15 non blocca e si giudica sul report. → lasciarla così.
30. Quante bloccano. → tenere questa divisione; puoi spostare ogni regola dicendomi il numero.
31. I temi «scelta nostra». → tenerle tutte.

Rispetto all'elenco del brief ho aggiunto tre punti: 15 (test e documenti, S22-S24), 23 (R-SECURITY-17 fuori dalla tabella delle sovrapposizioni, osservazione del verificatore) e 30 nella forma «quante bloccano» con il motivo delle quattro che non bloccano (la 2 per l'appoggio debole). N4 è il punto 2, N9 il punto 4, D10 il punto 16, i marcatori tolti il punto 19, D14 il punto 5 (con la frase del piano alla lettera e la frase dell'utente citata).

### Esito dei test

`python3 -B -m unittest tests.test_rules_security tests.test_docs tests.test_manifest`:

```
----------------------------------------------------------------------
Ran 108 tests in 0.569s

OK
```

Un solo rosso durante il lavoro, corretto nel testo: il punto 25 aveva «Costo se blocca:» invece di «Costo: ».

### `docs/uso/comandi.md`

Va riallineato in un punto solo (mano opus): nel riassunto di R-SECURITY-10 «nelle risposte nessun hash di password, token di reset o segreto del server» manca la **password** (ritocco N1). Facoltativi, se il riassunto scende a quel dettaglio: per R-SECURITY-05 i valori finti ammessi nei test; per R-SECURITY-09 che il motivo di `SameSite=None` dice quale altro sito manda il cookie. Il riassunto di 04 («dati pubblici … lo dichiarano nel diff») resta giusto.

### Dubbi

1. **I ritocchi non sono ripassati dal verificatore.** Il brief dello Step 3 dice che una correzione ripassa; qui sono ruling del controller su testo di regola, e l'unica `Fonte:` toccata cambia solo nella frase «scelta nostra». Il rapporto lo dice apertamente. Se il controller vuole una terza passata, riguarda quattro righe.
2. **«I file che `init` riconosce come test sono saltati»** (rapporto, sotto i marcatori): l'ho scritto da `test_real_security_markers_skip_tests`. `task-5-fonti.md` diceva invece che un marcatore accende anche «un file di test»: ho seguito il test. Da confermare con chi conosce `init.detect_files`.
3. **Punto 5 (D14):** la proposta è lasciare S53, S54 e S61 a `security`. Se l'utente sceglie l'altra strada serve un giro del Task 3 prima dell'approvazione: la pagina lo dice come costo.
4. **Punto 19:** dico che i due marcatori «si rimettono, dichiarati come scelta tua»; rimetterli vuol dire toccare frammento, test (`MARKERS`, `REMOVED_MARKERS`) e rapporto.
5. **Punto 28 (R-SECURITY-09):** non nomino nessuna libreria con protezioni deboli per difetto, perché nelle copie non c'è una pagina che lo dica (il ri-revisore lo lasciava «da verificare»).
6. **Termini in più** rispetto ai tredici dei test: Controllo d'accesso, Password, Cookie di sessione, Segreto, CORS, Agente, `tollgate.toml`, Attivo. Li usa la pagina.
7. **«Regole tolte dalla verifica» anche nella pagina** (come in quella di `database`): i test non la chiedono lì; si toglie senza effetti se è di troppo.
8. Il difetto di `tests/test_rules_database.py` e `tests/test_rules_frontend.py` segnalato dalla prima mano (stampano il valore trovato) resta fuori dal mio compito.

## Mano 3 (Step 4, 5)

**Status:** DONE. Mano opus. Commit `12c0b2d` «tollgate C2: fonti di rules-security verificate e pagina per l'utente» (nuovo, nessun amend), con le due righe `Co-Authored-By` (Opus 5.5, Fable 5.2) e nel corpo chi ha fatto cosa. Non ho toccato il testo della skill, della pagina né del rapporto.

### Cosa ho cambiato

Solo `docs/uso/comandi.md`, nella sezione `/tollgate:rules-security` (un paragrafo, una riga del diff), tre ritocchi del riassunto:
- R-SECURITY-10: «nelle risposte nessuna password, nessun hash di password e nessun segreto del server, e mai un token di reset» (prima: «nessun hash di password, token di reset o segreto del server»);
- R-SECURITY-05: «per un'impostazione solo il valore che nega, e nei test un valore finto evidente ammesso»;
- R-SECURITY-09: «`SameSite=None` solo con `Secure` e un motivo scritto che dice quale altro sito manda il cookie» (il riassunto scendeva già a quel dettaglio).
Il riassunto di 04 resta com'era (giusto, come dice la mano 2).

### Il dubbio 2 della mano Fable

La frase del rapporto (`docs/profili/verifiche/security-fonti.md:136`, «I file che `init` riconosce come test sono saltati») è **vera ma incompleta**. Il codice:
- `bin/tollgate_flow/init.py:297-298`: `detect_files` tiene solo i file trovati da `git grep` per cui `_is_detectable` è vero;
- `bin/tollgate_flow/init.py:275-276`: `_is_detectable` scarta un file se una cartella del suo percorso si chiama `tests`, `test` o `__tests__`, o se il nome corrisponde a `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`, `conftest.py` (`TEST_DIRS` e `TEST_NAMES`, `:45-46`);
- `:268-274`: scarta anche i file oltre 256 KiB (`MAX_DETECT_BYTES`, `:47`), quelli sotto `EXCLUDED_PREFIXES` (`:37`) o sotto l'`exclude` del frammento (`supabase/`), e quelli senza un'estensione di codice (`SOURCE_EXTENSIONS`, `:43-44`; quindi niente documenti).

Frase giusta proposta: «Il rilevamento per contenuto salta i file di test: quelli dentro una cartella `tests/`, `test/` o `__tests__/` e quelli con un nome `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py` o `conftest.py`. Un file di test dentro una cartella del profilo (per esempio `tests/auth/`, caso S22) si accende lo stesso per il percorso.» Un mock o una fixture fuori da quelle cartelle e senza quei nomi resta rilevato: per quel caso `task-5-fonti.md` («un file di test o un mock») aveva ragione a metà. Non l'ho corretta: decide il controller.

### Comandi e output

- `python3.11 -B -m unittest tests.test_rules_security tests.test_rules_database tests.test_fragments tests.test_docs tests.test_init tests.test_manifest`: `Ran 506 tests in 23.207s` `OK`; con `python3`: `Ran 506 tests in 24.369s` `OK`.
- `claude plugin validate --strict .`: `✔ Validation passed`, uscita 0.
- `git status --short` prima della suite: solo `A docs/profili/security.md`, `A docs/profili/verifiche/security-fonti.md`, `M docs/uso/comandi.md`, `M skills/rules-security/SKILL.md`, `M tests/test_rules_security.py`, tutti in indice.
- `/usr/bin/grep -rai -c -w` del nome utente e dell'host e `/usr/bin/grep -ra -c "/home/"` sui due documenti nuovi: 0, 0, 0 per ciascuno (valori non stampati).
- Suite (`PYTHONWARNINGS=error::ResourceWarning tests/run`, in background, uscita in `suite-task-5.log`): Python 3.11.16 `Ran 4474 tests in 1884.507s` `OK (skipped=13)`; Python 3.13.5 `Ran 4474 tests in 1861.436s` `OK (skipped=11)`; `exit 0`; nessun «unclosed».

### Errori trovati

Nessuno nei file del task oltre alla frase del dubbio 2. Resta il difetto già segnalato dalla mano 1: `tests/test_rules_database.py` e `tests/test_rules_frontend.py` usano `assertFalse(re.search(…))`, che in caso di errore stampa il nome utente o l'host trovato.

## Fix round 1, mano Fable

Fable, 23/11/2026, sopra il commit `12c0b2d`. Toccati solo `docs/profili/security.md` (232 righe), `docs/profili/verifiche/security-fonti.md` e la copia `task-5-proposte.md`; la skill e i test no. Nessun commit, nessun `git add`, nessuna suite completa, nessun subagente, nessuna rete. I punti di «Da decidere tu» restano 31 (introduzione, «Su trentuno punti», elenco); la copia è rigenerata dalla sezione.

### Cosa ho verificato sul codice

**I-1 (percorsi sensibili).**
- `bin/tollgate_core/config.py:40`: il predefinito è `"sensitive_paths": ["**/migrations/**", "**/auth/**"]` (un progetto può cambiarlo nel suo `tollgate.toml`: la pagina dice «salvo che tu abbia cambiato quell'impostazione»).
- `bin/tollgate_analysis/level.py:41-43`: un percorso sensibile dà sempre L2.
- `bin/tollgate_checks/_common.py:322-327`: al ricalcolo il livello è il massimo fra quello del diff (con i percorsi sensibili) e il `min_level` dei profili attivi.
- Quindi sotto `auth/` e `migrations/` il lavoro è L2 senza il profilo; `security/`, `rls/`, `middleware.*`, `proxy.ts`/`.js` e i file trovati per contenuto fuori da `auth/` diventano L2 solo con il profilo. Caso per caso: S19, S40, S22, S70 (sotto `auth/`) e S68 (sotto `migrations/`) erano già L2; S44, S69, S71, S24, `middleware.yaml` sono nuovi. Per `db/rls/policies.sql` (S13) il livello è nuovo solo se `database` non è acceso (`templates/profiles/database.toml` ha `min_level = "L2"` e `**/*.sql`).

**I-2 (cosa vuol dire «attivo»).**
- `bin/tollgate_analysis/profiles.py:40-43` (`active_profiles`): attivo = il lavoro tocca un file dei `paths` del profilo.
- `bin/tollgate_analysis/profiles.py:76-91` (`task_routing`): un solo implementatore e un solo revisore per task, quelli del verticale che vince; con due agenti diversi i generici e `split`.
- `agents/reviewer-backend.md:5` (`skills: [rules-base, rules-backend]`), `agents/task-reviewer.md:5` e `agents/implementer.md:5` (`skills: [rules-base]`): ogni agente ha caricate solo le regole della sua area; i generici solo quelle di base.
- `bin/tollgate_checks/task_verdict.py:54-62`: le regole dei profili attivi entrano in `known_rules` e `blocking_rules` del controllo del verdetto, cioè il verdetto accetta quegli id. Nient'altro arriva al revisore del task.
- `bin/tollgate_flow/finalreview.py:114-117`: in L2 la revisione finale aggiunge gli specialisti dei profili attivi nel lavoro. `templates/profiles/*.toml`: hanno `final_specialist` solo `database` e `security`.
- `agents/final-database.md:38`: lo specialista giudica solo le regole sul diff e lascia quelle sul report al revisore del task. `agents/final-security.md` non esiste ancora (Task 7): per lui la pagina dice ciò che fissa la decisione 10, con la stessa forma.

### Testo nuovo, rilievo per rilievo

**I-1.** «Il lavoro sale a L2», frasi nuove:
> Attenzione a cosa è nuovo. Sotto una cartella `auth/` il lavoro è L2 già oggi, anche senza questo profilo: `auth/` è, insieme a `migrations/`, tra i percorsi che tollgate tratta come delicati fin dall'inizio (salvo che tu abbia cambiato quell'impostazione in un progetto). Lì il profilo non cambia il livello: cambia chi scrive e chi rivede, e aggiunge lo specialista finale. Il livello L2 è nuovo per le cartelle `security/` e `rls/`, per i file `middleware` e `proxy` e per i file riconosciuti dal contenuto, quando non stanno sotto `auth/`: per questi anche un cambio piccolo porta tutto il lavoro in L2, ed è il costo.

Punti: 1 («Il livello non cambia: sotto `auth/` il lavoro è L2 già oggi» e, nella proposta, «il file torna agli agenti di `frontend`, senza queste regole e senza lo specialista, ma il lavoro resta L2 perché sta sotto `auth/`»); 2 («il livello era già L2»); 10 (costo: «sotto `auth/` il livello non cambia (era già L2), ma quei file vanno agli agenti di sicurezza e fanno partire lo specialista. Per un file come `middleware.yaml`, e per una cartella `security/`, è nuovo anche il livello L2»; rimedio: «Sotto `auth/` toglie gli agenti di sicurezza e lo specialista, non il livello L2; per `middleware.yaml` e per `security/` toglie anche quello»); 13 («Sotto `auth/` il livello era già L2; sotto `security/` è nuovo»); 14 («Il livello L2 è nuovo solo per `infra/security/` e per il middleware: la migrazione e il pacchetto `auth` erano già L2»); 15 («lo era già, perché sta sotto `auth/`»; «sotto `security/` un lavoro piccolo su test o documenti sale a L2»).

**I-2.** La formula «note a chi rivede» non c'è più in nessun punto (`grep`: nessuna riga). Paragrafo nuovo in «Cosa cambia nei tuoi progetti»:
> **Quando un file va agli agenti di un'altra area.** Ogni task ha un solo agente che scrive e uno solo che rivede, quelli dell'area che vince, e ognuno ha caricate solo le regole della sua area. Se un file di login resta agli agenti di `backend` con `security` attivo, succede questo: il lavoro è L2; chi rivede il task può citare una regola di sicurezza (tollgate la accetta), ma non le ha davanti, e nemmeno chi scrive; a fine lavoro lo specialista `final-security` controlla le regole di sicurezza che si giudicano sul diff. Le regole che si giudicano sul report (1, 2, 15, 16 e 17) per quel task non le ha davanti nessuno. Vale anche al contrario: se un file di un'altra area va agli agenti di sicurezza, le regole di quell'area non le ha caricate né chi scrive né chi rivede il task. Per `database` le guarda a fine lavoro il suo specialista, `final-database`, e solo quelle sul diff; `frontend`, `backend`, `infra` e `ai` non hanno uno specialista finale.

La riga «Un file riconosciuto anche da un altro profilo» ora chiude con «in quel caso `security` è attivo, con gli effetti e i limiti scritti qui sotto». La voce **Attivo** del glossario dice le tre cose che vuol dire e quella che non vuol dire. Punti: 3 (costo: «né chi scrive né chi rivede quella rotta ha caricate queste regole; chi rivede può citarle, ma non le ha davanti. Le controlla solo lo specialista finale, a fine lavoro, e solo quelle che si giudicano sul diff: le cinque sul report (1, 2, 15, 16 e 17; la 1 e la 17 bloccano) per quel task non le guarda nessuno»); 1 («le regole di `frontend` per quel task non le ha caricate nessuno (`frontend` non ha uno specialista finale)»); 2; 4 («Le regole di sicurezza sul diff le guarda lo specialista a fine lavoro; quelle di `backend` nessuno»); 6 e 7 («con i limiti del punto 3»); 12 («le guarda a fine lavoro lo specialista `final-database`, e solo quelle sul diff»); 13; 14 («per `infra` e `ai` nessuno»). L'introduzione di «Regole che si sovrappongono» dice «chi scrive e chi rivede il task hanno caricate solo queste regole».

**m-1.** Riga 9 della tabella: «Due eccezioni: `Secure` può dipendere dall'ambiente (acceso in produzione), e il valore più aperto di `SameSite`, `None`, è ammesso solo con `Secure` e con il motivo scritto accanto». Riga 4: «… la richiesta di reset e la callback di un login (la pagina a cui un servizio di login esterno rimanda l'utente)». Riga 5: «… o per un interruttore che spegne un controllo, …» e «Nei test è ammesso un valore finto evidente». Punto 31: per R-SECURITY-07 anche «il divieto di spegnere il controllo della firma»; per R-SECURITY-09 anche «`Secure` legato all'ambiente; `SameSite=None` con il motivo scritto».

**m-2.** Punto 11: «le librerie standard `crypto`, `hashlib` e `hmac`, per cui un file che firma token solo con quelle non è riconosciuto dal contenuto».

**m-3.** Quattro voci di glossario nuove: **Frammento**, **Monorepo**, **Server Function**, **Policy**.

**m-4.** «Quando si accende»: «Un progetto nuovo riceve la proposta con `/tollgate:init --propose`; uno che ha già tollgate con `/tollgate:init --update`» (opzioni controllate su `docs/uso/comandi.md:124-127`).

**m-5.** Rinvio, in coda allo stesso paragrafo: «Costo del rinvio: questa fetta di lavoro resta aperta e quella dopo, il profilo `ci` per le automazioni, aspetta.»

**m-6.** In testa a «Da decidere tu»: «Se hai poco tempo, guarda questi sette, dove la tua scelta cambia davvero qualcosa: il 5 e il 19 (quali file prende il profilo), il 25 e il 30 (quali regole fermano un task), il 28 (quanto è severa la regola sui cookie), il 21 e il 22 (le regole ripetute). Gli altri sono costi da conoscere, e la proposta è lasciare com'è.»

**m-7.** Rapporto, sotto i marcatori: «Il rilevamento per contenuto salta i file di test: le cartelle `tests/`, `test/`, `__tests__/` e i nomi `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`, `conftest.py`. Un test dentro una cartella del profilo si accende lo stesso, per il percorso (caso S22 della tabella delle precedenze). Un mock fuori da quelle cartelle e senza quei nomi resta rilevato.» (da `bin/tollgate_flow/init.py:45-46`).

**m-8.** Rapporto, intestazione: «Li ha riletti il revisore del Task 5 (Fable, sola lettura, 23/11/2026, commit `12c0b2d`): le righe toccate di 04, 05, 09 e 10 sono tutte `ok`.»

### Esito dei test

`python3 -B -m unittest tests.test_rules_security tests.test_docs`:

```
----------------------------------------------------------------------
Ran 44 tests in 0.111s

OK
```

### Test da adeguare (mano opus)

Nessun test fissa una frase che ho dovuto cambiare: i due file restano verdi senza toccarli. Resta solo m-9. Per chi lo scrive: i titoli in grassetto dei punti non sono cambiati; il punto 31 nomina ancora tutti e 17 gli id; il paragrafo nuovo «Quando un file va agli agenti di un'altra area» sta in «Cosa cambia nei tuoi progetti».

### Dubbi

1. **`final-security` non esiste ancora** (Task 7): la pagina dice che controlla le regole sul diff, come fissa la decisione 10 e come fa `final-database`. Se il Task 7 scrive altro, la pagina va riletta.
2. **m-6:** ho indicato sette punti, non quattro: ai 5, 19, 25, 28 della revisione ho aggiunto il 30 (quali regole bloccano) e il 21 e il 22 (tenere o togliere le regole ripetute), che sono scelte vere dell'utente.
3. **Punto 12 (S13):** il livello L2 per `db/rls/policies.sql` è nuovo solo se `database` non è acceso nel progetto; l'ho scritto così, è una frase un po' lunga.
4. **Punto 1, rimedio:** «senza lo specialista» vale se nel lavoro non c'è un altro file del profilo.

## Fix round 1, mano opus

**Status:** DONE. Commit `3610a18` «tollgate C2: pagina di security, correzioni dopo la revisione» (nuovo, sopra `12c0b2d`, nessun amend, le due righe `Co-Authored-By` Opus 5.5 e Fable 5.2). Della pagina e del rapporto ho fatto solo `git add`, senza cambiarli.

### m-9: cosa ho cambiato in `tests/test_rules_security.py`

- `CHOICE_NEEDLES` (una parola chiave cercata in tutta la sezione) diventa `CHOICE_POINTS`: per ogni voce, le parole che devono stare nel **titolo in grassetto** di un punto e quelle che devono stare nel **testo dello stesso punto**. Gli id di regola stanno nel titolo, insieme alla seconda parola: `R-SECURITY-10` + «ripete», `-12` + «ripete», `-08` + «blocca», `-08` + «esempi» (e nel punto `hmac.compare_digest`, `crypto.timingSafeEqual`), `-01` + `-16` + «vicine», `-09` + «forme», `-15` + «report». Si cercano nel titolo anche `**/proxy.ts`, «restano fuori», `import jwt`, `jose`, `iron-session`, «marcatori tolti», `supabase/` e `dod`. Le voci senza un titolo proprio cercano tutte le loro parole nello **stesso** punto: terzi, immagini, testi tradotti, `middleware.yaml`; `keep_paths` + «scelta nostra»; N4 (`` `.tsx` `` + `` `components/` ``); N9 («agenti generici» + «test»).
- Gli id «scelta nostra» calcolati dalla skill si cercano solo nel punto il cui titolo contiene «scelta nostra», che deve essere uno solo.
- Funzione nuova `choice_points(section)`: restituisce (titolo, testo) per ogni punto. Il grassetto si chiude solo su `**` seguito da uno spazio o dalla fine, perché il titolo del punto 9 contiene `` `**/proxy.ts` `` (alla prima corsa questo dava un falso rosso; corretto).
- `test_page_explains_what_changes`: «init propone, tu copi» si cerca in `## Quando si accende` (titolo ora fissato), tutto il resto in `## Cosa cambia nei tuoi progetti` e non più in tutta la pagina. Ho controllato prima che ogni testo stia davvero in quella sezione.
- Nessun altro test cambiato; la mano Fable non ne segnalava altri.

Su ogni voce di `CHOICE_POINTS` la pagina di oggi ha **un solo** punto che la soddisfa, ed è quello giusto (10, 9, 11, 16, 17, 18, 19, 20, 6, 24, 21, 22, 25, 26, 27, 28, 29, 2, 4).

### Prova: togliere un punto ora dà rosso

Su una copia temporanea (`mkdtemp(prefix="tollgate-t5-")`, cancellata alla fine; `PAGE` del modulo sostituita in memoria; la pagina vera resta com'è, `git status` lo conferma) tolgo il punto e aggiorno «su quali N punti» e «Su N punti» a «trenta». Poi lancio `RulesSecurityPageTest`:

```
tolti - (punti 31): 16 test, 0 failures 0 errors
tolti 25 (punti 30): 16 test, 1 failures 0 errors
  --- test_page_brings_the_open_choices_to_the_user (point='R-SECURITY-08 blocca o no') | … manca il punto «R-SECURITY-08 blocca o no»
tolti 21 (punti 30): … manca il punto «sovrapposizione di R-SECURITY-10»
tolti 22 (punti 30): … manca il punto «sovrapposizione di R-SECURITY-12»
tolti 27 (punti 30): … manca il punto «R-SECURITY-01 e R-SECURITY-16 vicine»
tolti 28 (punti 30): … manca il punto «le due forme di R-SECURITY-09»
tolti 29 (punti 30): … manca il punto «R-SECURITY-15 non blocca e si giudica sul report»
tolti 26 (punti 30): … manca il punto «esempi nostri di R-SECURITY-08»
tolti 24 (punti 30): … manca il punto «dod vuoto»
```

Prima di m-9 la revisione aveva visto verdi le versioni senza i punti 21, 22, 25, 27, 28 e 29. Ho anche spostato la riga `denied = "python3 -m unittest discover -s tests -k denied"` fuori da «Cosa cambia», in fondo alla pagina: `test_page_explains_what_changes (needle='denied = …')` dà rosso, «manca un testo atteso in «Cosa cambia»».

### Verifica

- `python3 -B -m unittest tests.test_rules_security tests.test_docs tests.test_manifest`: `Ran 108 tests` `OK`, con `python3.11` e con `python3`.
- `claude plugin validate --strict .`: `✔ Validation passed`, uscita 0.
- `/usr/bin/grep -rai -c -w` del nome utente e dell'host e `/usr/bin/grep -ra -c "/home/"` su `docs/profili/security.md` e `docs/profili/verifiche/security-fonti.md`: 0, 0, 0 per ciascuno (nessun valore stampato).
- `git status --short` prima della suite: `M docs/profili/security.md`, `M docs/profili/verifiche/security-fonti.md`, `M tests/test_rules_security.py`, tutti in indice.
- Suite (`suite-task-5-fix-1.log`): Python 3.11.16 `Ran 4474 tests in 1871.175s` `OK (skipped=13)`; Python 3.13.5 `Ran 4474 tests in 1882.840s` `OK (skipped=11)`; `exit 0`; nessun «unclosed».

### Dubbi

1. I testi di «Cosa cambia» sono legati alla sezione: se il Task 6 sposta un paragrafo in un'altra sezione, il test lo segnala. È lo scopo di m-9.
2. Per N9 la seconda parola è «test»: è debole (molti punti la contengono), ma insieme ad «agenti generici» oggi trova un solo punto, il 4.
