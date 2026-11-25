# Task 10: revisione 37 della spec, catalogo, progetto di C, piano principale

Implementatore: opus. Worktree `.claude/worktrees/c2`, ramo `c2-profilo-security`, partenza da `d9639cc`.

## Cosa ho fatto, documento per documento

### Spec del nucleo (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`), revisione 37

- **Intestazione**: «Revisione: **37**: …» in testa, con la prova (19,55 USD equivalenti contro 10-18, nessun addebito), l'approvazione del 23/11 (17 regole, 13 `[blocca]`, 31 punti), i fatti del 22/11, le decisioni 1-20 e l'elenco delle sezioni; la 36 diventa «Revisione 36: …».
- **1.2**: solo il testo della voce «Gli eval misurano un modello, in tre corse per caso.» (titolo in grassetto invariato): `claude-opus-5-5` dalla rev 37, punteggi di `p5` e `b8` su sonnet, non confrontabili.
- **3**: tabella «Modello degli agenti» riscritta per ruolo (opus implementatori, fable tutti gli altri), con il motivo (scelta dell'utente del 22/11/2026), la tabella vecchia detta come storia, gli alias, i tre test (`test_agent_models_by_role`, `test_no_agent_on_sonnet`, `test_no_sonnet_in_skills_and_scripts`), il comportamento di Claude Code senza il modello e con `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`, prove su `opus` ed eval su `claude-opus-5-5`, gli script storici rimasti su sonnet.
- **4**: riga «Specialista finale»: due specialisti dalla rev 37, `ci` con C3.
- **6.3**:
  - diagramma dei giri 4-5 e voce «Giri di correzione»: `MODEL_HINT = "opus"` o `[review] models`, con il perché (il parametro di `Agent` non accetta `inherit`) e i tre test;
  - voce «Derivazione degli agenti»: «rev 37: anche `security`, con `final-security`»; voce di `database`: `final-database` ora `fable`;
  - tre voci nuove: **«Gli agenti di `security` e lo specialista finale»** (skill, sezioni «Area», regole su report e su diff dalla skill, `final-security` per rischio e raggio d'azione poi regole sul diff e checklist, la frase sul rischio che nessuna regola copre, L2 e `sensitive_paths`, `AREAS`/`FINAL_AREAS`, D1, divieto di `node` e simili con `verify`, instradamento e i due test); **«`security` attivo con un file che va agli agenti di un'altra area»** (regole accettate dal verdetto ma non precaricate, lo specialista guarda solo quelle sul diff, sovrapposizioni della decisione 15); **«Sicurezza fin dal progetto in ogni lavoro»** (decisione 20, senza sezione obbligatoria nuova, tre test, effetto nella prova);
  - **tabella S1-S71** dopo la Q, nella forma delle tabelle P e Q (cinque colonne, «Proposta di `init`» e «A runtime»), generata dalla tabella della decisione 5 (che ho confrontato con i 71 test di `SecurityPrecedenceTest`: coincide), in ordine numerico (S67 tra S66 e S68), con un paragrafo d'apertura (forma, test, regole che decidono) e una riga sui costi N4 e N9.
- **7.1**: `READONLY_TYPES` con `reviewer-security` e `final-security`; la frase «ogni revisore per area nuovo» con i due nomi.
- **7.3**: frase «Rev 37» su `reviewer-security` (`WebFetch` solo sugli URL citati) e `final-security` (senza `WebFetch`, nei due elenchi).
- **8.7**: paragrafo «Rev 37: lo stesso per `security`»: `dod` e `commands` vuoti, proposta del catalogo diventata R-SECURITY-03, esempio `denied`, comandi senza veto che non devono usare credenziali vere né servizi, canale di `verify`.
- **10**: «oggi solo `final-database`» diventa i due specialisti; paragrafo nuovo su `final-security` (checklist, `test_real_security_and_database_specialists_together`, cosa guarda, il rischio non coperto, il limite della regola dell'area del file, numeri della prova, test); frase «Per C3» sulla `checklist` e su `rules-ci`.
- **11.2**: in coda alla voce I-1 la **deroga `keep_paths`** (condizione di `lighting`, solo `security`, cartelle scelta dell'utente e nomi scelta del piano, effetti S49-S65, S53/S54/S61, solo proposta, deriva, quattro test più i due di non regressione); voce nuova **«Rilevamento per contenuto di `security`»** (21 marcatori, i quattro tolti, i non marcatori, testo fisso e `import jwt`, `session` fuori, `exclude` sul contenuto); «Agente che manca»: `security` è il secondo con `final_specialist`.
- **11.4**: `readonly_agents` con i due nomi nuovi; esempio di `models` con `"tollgate:implementer" = "fable"` (un alias che non è sonnet) e «solo alias»; elenco dei frammenti con `security.toml`; `[detect]` con `keep_paths` (booleano, `isinstance`, test); paragrafo nuovo **«Il frammento di `security`»** (6 pattern in ordine, cosa esce ed entra, cosa non copre, larghezza delle forme e rimedio, chiavi, 17 regole e non 12-16, 13 `[blocca]` con gli id, report e diff, R-15, R-09 a due forme, R-03, introduzione della skill, fonti vere senza ASVS, esempi di R-08 nostri, rapporto delle fonti, costo di L2); `[detect] exclude` anche per `security`, che senza forme `ext` lo ha di fatto anche a runtime, S67; frase «Nomi degli agenti»: i giri dal quarto non sono più `inherit`, il valore va dato come alias e non è validato.
- **14**: esecutore degli eval `claude-opus-5-5`, scelta dell'utente, punteggi di `p5` e `b8` su sonnet, campagna nuova con `--campagna` perché la predefinita è `b8`.
- **16**: blocco nuovo «Verificato in C2, il 22-23/11/2026» con sette righe (Next.js 16 Proxy; pagina dei subagenti con la data; `validate --strict`; librerie e marcatori; licenze e ASVS; conteggi sui progetti dell'utente, solo numeri; la prova reale con esito, costi, segnali e limiti). Le righe storiche delle prove passate non sono toccate. «Ancora da verificare dopo … B8 e C2»: aggiunti `reviewer-security` e due voci di `security`.
- **20**: riga 37 (23/11/2026) con le decisioni 1-20, le ruling D1, D2, D4, D5, D6, D7, D8, D11, D12, D13, D14 e quelle sui marcatori, ASVS, R-15, R-09, R-08, la frase del progetto di B, i ritocchi, le differenze della prova; sezioni toccate.

### Catalogo (`docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`)

- Stato e riga dei riferimenti: C2 ha costruito `security` (approvato il 23/11/2026, sul ramo); «aggiornamenti di C2 alla revisione 37».
- **2**: paragrafo dei marcatori con `security` (21 righe, `exclude`, `keep_paths`); riga `security` con i pattern veri (`**/*session*` fuori, `**/proxy.ts` e `**/proxy.js` dentro), cosa resta fuori, larghezza, «sì, `final-security`».
- **2.1**: riga `security` riscritta (skill precaricata, consigliate in «Dove informarsi», modelli, divieto, `final-security` con cosa guarda e la checklist); `final-database` ora `fable`.
- **2.2**: la riga del modello (che diceva `inherit` per `security` e `database`, `sonnet` per `copy` e `docs`) ora dice i modelli per ruolo; `reviewer-security` con `WebFetch`, `final-security` senza; conto degli agenti 21.
- **2.3**: `dod` di `security` vuoto, con la regola R-SECURITY-03 e l'esempio.
- **4**: riga `rules-security` con le fonti vere (nessuna ASVS, marcatori tolti, rapporto delle fonti); nota del prefisso con `R-SECURITY-`.
- **6**: paragrafo «C2 (revisione 37)».

### Progetto di C (`docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`)

- Avanzamento: C1 unita su `main` (fatto: `e0929a8`); **C2 costruita sul ramo `c2-profilo-security`, in attesa del merge**, con approvazione, prova e rev 37.
- Sezione 11: dopo «Gli implementatori meccanici possono restare sonnet» una frase datata 23/11 che dice che non vale più, per la scelta dell'utente del 22/11 (la frase originale resta, perché era «mia scelta» del progettista e la correzione si scrive con data e motivo).
- Sezione 14: chiarito che `fable`/`opus` nella riga `model:` sono il modello dei subagenti, non un modello nel codice di C.

### Piano principale (`docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`)

- Testa: revisione «37 dopo C2»; stato del 23/11 con **C2 costruita sul ramo, in attesa del merge** (nessun «unita su» per C2).
- Sezione 2, riga C2: «**Stato:** costruita sul ramo `c2-profilo-security`, in attesa del merge» con ciò che è consegnato davvero (il controllo `"unita" in riga` dà 0).
- Sezione 3, riga «C2 → C3»: `final-security` con i suoi dati, `final_specialist` di `ci`, la scelta su `rules-ci` lasciata a C3, `AREAS` e `FINAL_AREAS`, **D1** (C3 riscrive l'elenco delle aree anche in `final-database.md` e `final-security.md`), modelli e sezione della sicurezza fin dal progetto per gli agenti di `ci`.
- Sezione 6, rischio del costo: superato dalla scelta del 22/11 e il dato della prova (19,55 contro 10-18; 15 giri avversari su Fable 9,53).
- Sezione 7, decisione 4: superata il 22/11, con i ruoli e i modelli.
- Sezione 8: voce 6 di «Dopo C» (security sul ramo di C2); voce 8 nuova (campagna nuova degli eval prima della prossima corsa, D11) e voce 9 nuova (costo degli avversari su Fable); in «Rinvii dalle fette chiuse» le voci «Da C2»: decisione 17 (cosa resta aperto), forme fuori della decisione 1, marcatori tolti, esempi di R-08 senza pagina, S67 contro la frase della skill, `final-security` e la regola dell'area del file, `[review] models` non validato, `Sicurezza:` senza raccolta in `registra`, i test di `rules-database`/`rules-frontend` che stamperebbero nome utente o host, il limite di `implementer-security` senza `node`; e una voce pronta per i minori della revisione finale.

## Fatti al posto delle stime del piano

- 17 regole (il piano: «tra 12 e 16»), 13 `[blocca]` con gli id, sul report 01, 02, 15, 16, 17.
- Marcatori 21: tolti `require('bcryptjs')`, `require("bcryptjs")`, `from 'jsonwebtoken'`, `from "jsonwebtoken"`.
- Nessuna fonte OWASP ASVS (la decisione 8 e la 9 dicevano «idee di ASVS»): idee dall'OWASP Cheat Sheet Series e da Trail of Bits.
- Prova a 19,55 USD equivalenti (stima 10-18), 15 giri degli avversari, spec da 2 a 13 must-have, specialista più caro del revisore generale (in B7 il contrario).
- `can_read(user, owner)` invece di `can_read(user, note)`: non l'ho scritto nella spec del nucleo (è un dettaglio del progetto di prova, già nel rapporto).

## Test

- Mirati, dopo le modifiche: `python3 -B -m unittest tests.test_docs tests.test_manifest tests.test_rules_security` → `Ran 116 tests … OK (skipped=3)`.
- `tests/test_docs.py` non fissa numeri di revisione né conteggi che la rev 37 cambia: nessun test toccato.
- Suite completa: vedi «Esito della suite» in fondo.

## File cambiati

- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`
- `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`
- `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`
- `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`

`docs/uso/limiti.md` non cambia: la rev 37 non aggiunge voci in grassetto a 1.2 (D12) e il testo della voce sugli eval in `limiti.md` («Un solo modello…») resta vero. La riga `**Tipi:**` non è toccata.

## Scostamenti dal piano

- Nella sezione 3 della spec ho lasciato la tabella vecchia come frase storica sopra la nuova, perché la scelta dell'utente sostituisce una decisione scritta di P0/P1 e il perché del cambio serve a chi legge.
- Nel progetto di C la frase «Gli implementatori meccanici possono restare sonnet» resta, seguita dalla correzione datata (regola 3 del piano principale: le correzioni del progetto si scrivono con data e motivo).
- Nel piano principale ho aggiunto due voci a «Dopo C» (8 e 9) invece di metterle nella voce 7, perché sono di D o delle prove successive, non «da C stessa».
- Ho aggiunto alla 16 la riga su `claude plugin validate --strict` (D5) e una sui conteggi nei progetti dell'utente: sono fatti verificati di C2 che reggono la decisione 1 e la 14.

## Autorevisione: le decisioni 1-20 nella revisione 37

| Decisione | Dove sta |
|---|---|
| 1 Cosa copre | 11.4 «Il frammento di `security`» (copre / non copre / larghezza / rimedio); 16 (conteggi) |
| 2 Pattern | 11.4 (6 pattern in ordine, `session` fuori, `proxy`); tabella S (S7, S9, S46, S47, S57, S59, S66, S68-S71) |
| 3 `exclude` | 11.4 (frammento e `[detect] exclude`), 11.2 (contenuto, S43), tabella S (S11, S12, S56) |
| 4 Contenuto e `keep_paths` | 11.2 (deroga e rilevamento), 11.4 (`[detect]`), 6.3 (attivo con un'altra area), tabella S |
| 5 Tabella delle precedenze | 6.3 «Precedenze del profilo `security`», S1-S71, test |
| 6 Proposta e runtime | 11.4 (`exclude` di fatto a runtime, S67), 11.2 («cambia solo la proposta») |
| 7 Nessuna skill nel brief | 6.3 (agenti di `security`), 11.4 (`skills = []`) |
| 8 Fonti | 11.4 (Fonti), 16 (licenze e idee), catalogo 4 |
| 9 Temi, 17 regole | 11.4 (17 regole, 13 `[blocca]`, R-15, R-09, R-03), 20 |
| 10 `final-security` | 4, 6.3, 10, 11.2 (agente che manca), 11.4; piano principale sezione 3 |
| 11 Agenti per area | 6.3 (derivazione, `AREAS`, test), 7.1, 7.3 |
| 12 `dod` vuoto | 8.7, 11.4; catalogo 2.3 |
| 13 Livello L2 | 6.3 (L2 e `sensitive_paths`), 11.4 (costo di L2) |
| 14 Modelli | 1.2, 3, 6.3 (giro 4), 11.4 (`models`, nomi degli agenti), 14, 16 (pagina dei subagenti); catalogo 2.2; piano principale 6, 7; progetto di C 11 e 14 |
| 15 Sovrapposizioni | 6.3 («`security` attivo con un file che va agli agenti di un'altra area»), 11.4 |
| 16 Prova reale | 16 (riga della prova), 10 (numeri dello specialista), 6.3 (effetto sulla spec) |
| 17 Rinvii | piano principale sezione 8 |
| 18 Test sulla radice vera | 20 (riportata); nessun albero dei test accende `security` (scan), niente da cambiare nel testo della spec |
| 19 Una fetta sola | 20 (unione parziale non scattata) |
| 20 Sicurezza fin dal progetto | 6.3 (voce nuova), 16, 20; catalogo 6 |

## Dubbi

1. Nel progetto di C la riga «Avanzamento» diceva per C1 «in attesa del merge»: l'ho corretta in «unita su `main` il 22/11/2026 (`e0929a8`)», che è un fatto (il piano principale lo diceva già). Per C2 ho scritto solo «costruita … in attesa del merge».
2. Il minore rinviato del Task 6 (`tests/test_rules_security.py:822`, elenco chiuso delle frasi «da decidere») non è nella lista delle decisioni del controller per la sezione 8: non l'ho scritto; il controller lo può aggiungere con i minori della revisione finale.
3. Nella riga «C2 → C3» ho scritto indicazioni per C3 (`AREAS`, modelli di `reviewer-ci` e `implementer-ci`): sono conseguenze dei test esistenti, ma la sezione 3 dice che i nomi li fissa la fetta che li produce.

## Esito della suite

Comando (strumento Bash in background, uscita su file): `cd "<worktree>" && { PYTHONWARNINGS=error::ResourceWarning tests/run; echo "exit $?"; } > "<W>/suite-task-10.log" 2>&1`, poi il ciclo `until` in primo piano.

- Python 3.11.16: `Ran 4516 tests in 3593.402s`, `OK (skipped=16)`.
- Python 3.13.5: `Ran 4516 tests in 3732.842s`, `OK (skipped=14)`.
- `exit 0`; nessun «unclosed» nel file (`grep -c unclosed` = 0).

Commit: `3855816` «tollgate C2: spec rev 37, catalogo, progetto e piano principale».

## Fix round 1

Rilievi da `task-10-review.md`, decisioni da `task-10-fix-1.md`. Rapporto della prova riletto a `86b3dff` («Segnali delle regole e precaricamento», «Costi»).

- **I1** (spec 16, riga della prova): il modello delle minacce e il raggio d'azione «li chiede per esteso il testo di `agents/implementer-security.md` (…): provano che il task è andato all'agente dell'area e che l'agente fa ciò che il suo testo chiede, non il precaricamento»; gli id citati con il contenuto giusto (07, 08, 10, 12) sono un «indizio forte», perché gli agenti hanno solo i numeri e l'abbinamento viene dalla skill; «la prova del precaricamento resta il titolo `isMeta` nelle cinque trascrizioni». Aggiunto il dato dei giri: 4-9 della spec e 4-6 del piano senza rilievi sopra `minor` (`outcome: empty`), i giri 5-9 e 5-6 aperti per le correzioni delle note `minor`, sette giri, 280.137 token. Ora coincide con la 6.3.
- **I2** (catalogo, riga `security` di 2): «sotto `auth/` il lavoro è L2 già senza il profilo (`levels.sensitive_paths`, spec 11.4): il livello è nuovo per `security/`, `rls/`, `middleware.*`, `proxy.ts`, `proxy.js` e i file trovati per contenuto».
- **m1** (spec 6.3): «accettate dal verdetto (`rules` dei profili attivi, `profiles.known_rules`; `blocking_rules` decide solo se un rilievo può bloccare, `verdicts.is_blocking`)». Sul codice: `bin/tollgate_analysis/profiles.py:99-101` (`known_rules` dalle `rules`), `bin/tollgate_analysis/verdicts.py:91-101` (blocca un passo del piano, una `[blocca]` o una `R-…` non dichiarata da nessun profilo attivo).
- **m2** (spec 3 e 16): «con un avviso nelle sessioni interattive», senza «solo»; in 3 «Se `availableModels` esclude il modello chiesto … (dove il fornitore lo consente)». `docs/uso/comandi.md` non toccato.
- **m3** (piano principale, voce 9 di «Dopo C»): tolto «oggi nessun tetto sotto quello dell'audit»; ora dice che i tetti aprono un blocco solo per un giro sporco oltre il tetto, che i giri puliti non hanno tetto e che ogni correzione del documento chiede un giro nuovo, con il dato dei giri 4-9 e 4-6 e dei sette giri da 280.137 token. Vedi sotto ciò che ho visto nel codice.
- **m4** (spec 6.3, voce di `database`): `AREAS` «era, fino alla rev 36, (…) (dalla rev 37 anche `security`, voce sotto)»; `FINAL_AREAS` «che era `("database",)` fino alla rev 36».
- **m5** (catalogo, riga `security` di 2): «La riga dell'8/10/2026, citata come «riga 40 del catalogo» dal rapporto approvato delle fonti, era: `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**`, L2, specialista sì».
- **m6** (piano principale, sezione 8): «I minori che la revisione finale di C2 lascerà rinviati e i minori differiti dei task che il triage tiene si aggiungono qui…».
- **m7** (piano principale, riga «C2 → C3»): «C3 decide anche le skill del revisore di `ci`: il catalogo (riga `ci` di 2.1) mette `rules-security` tra le sue `reviewer_skills`, ma da B3 le regole le precaricano gli agenti (`skills:` del frontmatter), non il brief».
- **m8** (spec 16): «quasi tutti sessioni di chat in due copie di terzi, 100 documenti, 449 test».

### m3: ciò che ho visto nel codice

- `bin/tollgate_core/config.py:72`: `spec_rounds = 4`, `plan_rounds = 2`.
- `bin/tollgate_hooks/apply.py:178-192` (`_cap_block`, alla chiusura di un giro): `done = len(audits.rounds(...))` conta i giri chiusi non superati del tipo; il blocco `needs_you` si apre solo se `done >= spec_rounds` (o `plan_rounds`) **e** il giro appena chiuso non è pulito (`auditrules.is_clean`: `blocker + major == 0`, `bin/tollgate_analysis/auditrules.py:33-35`).
- `bin/tollgate_flow/audit.py` (`adversarial_ok`, `passed`, `last_round`): `approve spec` (e i rami di `prepare`) vogliono che l'ultimo giro chiuso stia sul blob attuale del documento e sia pulito o sospeso; quindi ogni modifica del documento dopo un giro chiede un giro nuovo.
- `bin/tollgate_flow/l2acts.py:347-350` (`approve rounds`/sospensione): sospende solo se `len(rows) >= cap` e l'ultimo giro non è pulito.
- Con i dati della prova: spec, giro 1 e 2 con `major`, dal 3 puliti; piano, giro 1 con `major`, dal 2 puliti. Quando il conteggio ha raggiunto il tetto (giro 4 della spec, giro 2 del piano) il giro era pulito, quindi nessun blocco si è aperto e nessun `approve rounds` era chiamato in causa dal codice. Non c'è nel codice un tetto sui giri puliti: il numero dei giri dipende da quante volte la sessione corregge il documento. Non traggo conclusioni sul fatto che sia o no un difetto del prodotto.

Test mirati: `python3 -B -m unittest tests.test_docs tests.test_manifest tests.test_rules_security` → OK (skipped=3). Suite completa: vedi sotto.

Suite del giro 1 (`suite-task-10-fix-1.log`): Python 3.11.16 `Ran 4516 tests` OK (skipped=16); Python 3.13.5 `Ran 4516 tests` OK (skipped=14); `exit 0`; nessun «unclosed». File cambiati: spec del nucleo, catalogo, piano principale (il progetto di C no). Commit «tollgate C2: spec rev 37, correzioni dopo la revisione».
