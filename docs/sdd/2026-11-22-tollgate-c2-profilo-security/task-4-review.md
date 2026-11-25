# Task 4: revisione (commit `abccbe0`, pacchetto `review-c0a60df..abccbe0.diff`)

Revisore Fable, 23/11/2026, sola lettura. Nessun test rilanciato: nessun dubbio che le esecuzioni riportate non coprissero. Nessun subagente, nessuna rete.

Controlli mirati fuori dal diff (rischio → controllo):
- *Un test della tabella che asserisce meno della riga* → letto `FrontendPrecedenceTest.check` (`tests/test_init.py:1342-1350`): la «Proposta» si confronta per uguaglianza su **tutti** i profili proposti, il «Runtime» sui file dati.
- *S43 verde per il motivo sbagliato* → letto `init.profile_blocks` (`bin/tollgate_flow/init.py:382-394`): `found` scarta i file sotto `fragment.exclude`, quindi il caso prova davvero l'esclusione sul contenuto.
- *Il frammento che accende se stesso o i test* → `SOURCE_EXTENSIONS`, `TEST_DIRS`, `TEST_NAMES` (`init.py:43-46`): un `.toml` e un `.md` non sono sorgenti, i test sono saltati.
- *Regola che contraddice una regola approvata* → lette R-BACKEND-03/06/07/08, R-INFRA-05/06/12, R-DATABASE-13/16, R-FRONTEND-01.
- *Indirizzo inventato* → ogni `https://` di skill, frammento e `comandi.md` cercato in `FONTI.md` e `pagine/`: tutti presenti (25 su 25; `https://github.com/trailofbits/skills` è la radice dei due indirizzi delle schede I-8 e I-9).
- *Testo copiato* → confronto di R-01, 03, 04, 05, 06, 07, 09, 10, 12, 13, 14, 15 con le sezioni citate delle copie MIT, con `pagine/` e con le schede.
- *Nome utente o host nei file* → `/usr/bin/grep -ciF` sui sei file del commit: 0.

### Aderenza

- ✅ File del task: solo i sei previsti; nessun file approvato né `agents/*.md` toccato; `approved` assente (`test_frontmatter` lo fissa).
- ✅ Frammento (decisioni 2, 3, 4, 10, 12, 13): sei pattern in ordine, `exclude = ["supabase/"]`, `keep_paths = true`, `min_level = "L2"`, tre agenti, `checklist` alla lettera, `skills`/`reviewer_skills`/`commands`/`dod` vuoti, 21 marcatori confermati e i quattro tolti assenti; `test_fragment_matches_decisions` confronta tutto per uguaglianza.
- ✅ Tabella della decisione 5: confrontati **tutti** i 71 casi con le righe (file, `detected`, «Proposta», «Runtime»): nessuna differenza. Dove la riga scrive «attivo» c'è `check_active` (S4, S13, S16, S49, S50, S62, S63, S64, S68) e S67 controlla `vertical_for` e `active_profiles` sui due blocchi a mano. Punti delicati S11, S12, S43, S49, S50, S53, S54, S61-S64, S16, S29, S55, S56, S67: dati e attese uguali alla riga.
- ✅ `FrontendPrecedenceTest` e `DatabasePrecedenceTest` non toccati dal diff (ora girano con `security` fra i frammenti veri e restano verdi: 89).
- ✅ Decisioni del controller: nessuna fonte «ASVS» né `security-review` in una `Fonte:` (test); D9 titolo; D12 niente «Argomenti:» né «solo l'utente»; D13 frase su `keep_paths` in `/tollgate:init`, vera rispetto a `init.py:385-392` e a `test_real_fragments_load` (gli altri cinque frammenti `keep_paths` falso).
- ✅ Ruling del ledger: frase sul «progetto di B, sezione 12» nell'introduzione con il suo test (scritto come test a parte, `test_supabase_edge_functions_stay_with_database`, invece che dentro `test_user_choices_covered`: equivalente, con prova del rosso nel report); `test_every_rule_names_a_source_of_the_allowed_kinds` resta; id 01, 03, 05, 10, 12 fissati; 17 regole; R-SECURITY-15 non blocca e si giudica sul report.
- ✅ Vincoli dei test: prefisso `test_real_` o file `test_rules_*`; `TemporaryDirectory(prefix="tollgate-")` con `addCleanup`; nessun `os.environ`.
- ✅ `comandi.md`: 17 temi nell'ordine delle regole; la frase su `exclude` di `security` e quella su `keep_paths` sono vere.
- ✅ Idee CC BY-SA: ogni `OWASP` e `Trail of Bits` di una `Fonte:` è «idea di …» (test con lookbehind, più la lettura).
- ✅ Evidenze: RED e GREEN riportati, suite 4458 verdi sui due interpreti, sonda 70 su 70 sul commit. L'unica riga di rumore («guard: la PR è avanzata…») e l'avviso `ICON_MISSING` c'erano già.
- ⚠️ Non verificabile da qui: i fatti sulle librerie che non stanno nelle copie (vedi I3 su Supabase) e la verifica voce per voce delle fonti, che è del Task 5.

### Punti di forza

- La tabella è coperta riga per riga con i frammenti veri e confronto esatto della proposta; S43 dà apposta a `detected` un file sotto `supabase/`, così prova l'esclusione in `profile_blocks` e non solo in `detect_files`.
- `test_real_security_markers_skip_tests` ha i controlli positivi (`src/lib/hash.ts`, `app/login.py`) accanto a sette forme di file di test, a un documento e alla edge function: prova quello che dice. `test_real_markers_not_in_tollgate_bin` è la stessa forma del test approvato di `database`.
- `test_overlaps_name_approved_rules` controlla anche che gli id esistano nelle skill approvate; `test_user_choices_covered` confronta gli insiemi esatti.
- Regole scritte con parole proprie, ogni «scelta nostra» dichiarata nella `Fonte:`; l'introduzione definisce controllo d'accesso, token, password, cookie di sessione e segreto, e rende giudicabili quasi tutte le regole.
- Frammento con la fonte per ogni pattern e marcatore, e i costi del testo fisso scritti nel commento.

### Rilievi

#### Critical

Nessuno.

#### Important

**I1 — [testo delle regole] `skills/rules-security/SKILL.md:60` (R-SECURITY-10, `[blocca]`): vieta ogni token «nel corpo di una risposta».** Alla lettera blocca l'endpoint di login che restituisce il token d'accesso al suo titolare (API con bearer token, client mobile, endpoint che crea una chiave d'API e la mostra una volta): l'introduzione stessa chiama «token» il JWT e la chiave di un'API, e R-SECURITY-07 parla dei token d'accesso che il diff crea. La regola approvata che dice di ripetere, R-BACKEND-08, si ferma al «corpo di una risposta **d'errore**», e la copia MIT citata («Sensitive Data Exposure») parla dei campi sensibili (hash, token di reset) dentro un oggetto restituito; la riga «Si sovrappone a» (`:62`) non dichiara questo allargamento. Perché conta: una `[blocca]` che scatta sul diff più tipico dell'area. Correzione: limitare la seconda frase a log, messaggi d'errore e, per le risposte, a hash di password, token di reset e segreti del server; dire che il token consegnato al chiamante a cui appartiene non è questo caso.

**I2 — [testo delle regole] `skills/rules-security/SKILL.md:36` (R-SECURITY-04, `[blocca]`): nessuna uscita per le funzioni che si chiamano senza credenziali.** «Una funzione del server che legge o cambia dati legati a un utente» comprende registrazione, richiesta di reset, callback di login e ogni dato pubblico per scelta (un profilo pubblico): lì «il controllo di chi chiama» non può esserci, e due revisori rispondono in modo diverso (uno blocca alla lettera, l'altro no). Sono le funzioni che il profilo vede più spesso. Correzione: dire quando la regola non si applica con un criterio che si vede nel diff (per esempio: la funzione è il login, la registrazione o il reset stessi, oppure il diff dichiara la rotta pubblica nel punto in cui la registra), o restringere a «dati che non sono pubblici».

**I3 — [testo delle regole] `skills/rules-security/SKILL.md:56` (R-SECURITY-09, `[blocca]`): chiede i tre attributi scritti nel codice anche quando il codice non li decide.** Tre casi innocui in cui scatta o divide i revisori: (a) il cookie lo scrive una libreria e il codice inoltra le opzioni che riceve (il middleware di sessione di Supabase per Next.js, che la tabella mette fra i file del profilo in S10; iron-session con i suoi predefiniti): nel diff gli attributi non compaiono e l'implementatore non ha un modo pulito di soddisfarla; ⚠️ da verificare sulla pagina ufficiale, che non è fra le copie, se i cookie di `@supabase/ssr` possono essere `HttpOnly` senza rompere il client del browser; (b) `secure: process.env.NODE_ENV === "production"`, la forma più comune: «dichiara `Secure`» sì o no?; (c) `SameSite=None` con `Secure`, legittimo per un contesto fra siti, escluso da «(`Strict` o `Lax`)». Il costo (a) è dichiarato nella `Fonte:` come scelta nostra, ma così la regola blocca codice corretto. Correzione: tenere «scritti nel codice» per il cookie che il codice costruisce da sé (`Set-Cookie`, `res.cookie`, `cookies().set` con opzioni proprie); per le opzioni di una libreria di sessioni chiedere solo che il diff non le indebolisca (`httpOnly: false`, `secure: false`, `sameSite: "none"` senza motivo scritto); dire come si giudica `secure` legato all'ambiente. La scelta fra le due forme va nella pagina, in «Da decidere tu».

#### Minor

- **m1 — [testo delle regole] `SKILL.md:36` (R-SECURITY-04), l'osservazione della terza mano.** È un difetto lieve, non un contrasto vero: la Server Function sta nell'elenco della prima frase, che ammette «una guardia applicata alla sua rotta», e l'ultima frase gliela toglie; in più `proxy.ts` e `middleware.ts` sono, per l'introduzione, proprio una guardia applicata a una rotta. Un revisore attento arriva alla risposta giusta, ma la regola si legge meglio con l'eccezione accanto all'alternativa: «dentro di essa o in una guardia applicata alla sua rotta (per una Server Function di Next.js solo dentro di essa: `proxy.ts` o `middleware.ts` da soli non bastano)». La stessa riscrittura toglie il calco dell'unica frase vicina a una traduzione alla lettera («lo verifica al suo interno e non si affida al solo `proxy.ts`…» contro la riga di una riga citata in `pagine/nextjs-proxy.md`, sezione «Execution order»): è un fatto di una pagina ufficiale e sta sotto la decina di parole identiche, ma la struttura è la stessa.
- **m2 — [testo delle regole] `SKILL.md:52` (R-SECURITY-08, `[blocca]`):** «un hash» non è qualificato, quindi scatta sul confronto di un checksum o di un ETag ricevuto da fuori, che non è un segreto; non esclude i test (`assertEqual(token, …)`); non dice se una ricerca nel database per token è un confronto. Correzione: «un segreto, un token, una firma o l'hash di un segreto», «nel codice che non è di test». Resta da far scegliere all'utente se blocca (già nel report).
- **m3 — [testo delle regole] `SKILL.md:40` (R-SECURITY-05, `[blocca]`):** vieta **ogni** valore di ripiego, mentre la scheda I-8 citata nella `Fonte:` parla di ripiego «permissivo», e la prima metà della frase accetta il codice che «nega l'accesso»: `origins = env.X?.split(",") ?? []` nega e insieme è un ripiego. L'esempio di CORS della copia MIT («Security Misconfiguration») usa proprio `|| 'http://localhost:3000'`. «Impostazione di sicurezza» è aperta (il numero di giri di bcrypt, la durata della sessione?). Correzione: per un segreto nessun ripiego; per un'impostazione il solo ripiego ammesso è il valore che nega; chiudere l'elenco delle impostazioni.
- **m4 — [testo delle regole] `SKILL.md:22` e `:86` (R-SECURITY-01 `[blocca]`, R-SECURITY-16):** «codice che non è solo test o documentazione» non dice cosa fare dei file dell'area che non sono codice (S39 `login.css`, S59 `middleware.config.json`, S70 `package.json`, S19 `policy.json`), e la frase è contorta. Correzione: «Se il diff cambia un file che non è un test né un documento». La via d'uscita («se da fuori non ci arriva nessuno, lo dice») tiene basso il costo. Le due regole restano vicine fra loro: già portato alla pagina dalla seconda mano.
- **m5 — [testo delle regole] `SKILL.md:48` (R-SECURITY-07):** «`algorithms` in `jwt.verify` e in `jwt.decode`» non dice di quale libreria è ciascuna; `jwt.decode` di jsonwebtoken è un'altra funzione. Correzione: «(`jwt.verify` di jsonwebtoken, `jwt.decode` di PyJWT)».
- **m6 — [testo delle regole] `SKILL.md:65` (R-SECURITY-11):** «quando la password è sbagliata» non vale per reset e recupero: lì il confronto è fra utente che esiste e utente che non esiste.
- **m7 — [testo delle regole] `SKILL.md:69` (R-SECURITY-12, `[blocca]`):** più larga di R-BACKEND-03 (intestazioni, cookie, token): un middleware che legge `Authorization` o un cookie e lo passa alla funzione di verifica di una libreria ha «controlli espliciti di tipo e forma»? Dire che la verifica della libreria vale come validazione di quel valore.
- **m8 — [testo delle regole] altri due ritocchi facoltativi:** R-SECURITY-06 (`:44`) non dice che non si applica quando il codice passa la password a un servizio di login che la controlla; R-SECURITY-13 (`:74`) può nominare `//host` fra ciò che non è un percorso interno.
- **m9 — [documenti d'uso] `docs/uso/comandi.md:178`:** il riassunto di 04 («non solo nel browser, nel middleware o nel proxy») è più largo della regola, che ammette una guardia di rotta e limita proxy e middleware alle sole Server Function; va riallineato comunque dopo il giro sul testo (I1-I3 cambiano 04, 09, 10).
- **m10 — [test] `tests/test_init.py:1914-1918`:** il docstring di `SecurityPrecedenceTest` dice che `detected` è dato «senza i file sotto un `exclude`», ma S43 (`:2145`) ne dà uno apposta, come vuole la riga della tabella: una parola nel docstring.
- **m11 — [test] `tests/test_init.py`, copertura:** `check_active` c'è solo dove la riga scrive «attivo»; i casi in cui un file sotto `auth/` va a un altro profilo senza quella parola (S14, S20, S42, S51, S52, S58, S65) non controllano che `security` resti attivo. Facoltativo.
- **m12 — [frammento] `templates/profiles/security.toml:53`:** il commento sul testo fisso può dire anche che `import jwt` accende `import jwt from 'jsonwebtoken'`, cioè la forma ESM di un marcatore tolto: serve alla pagina del Task 6, non cambia il frammento.

### Valutazione

**Qualità del task:** Da correggere

**Motivo:** test, frammento e pagina d'uso sono conformi e solidi (nessun rilievo Important); tre regole `[blocca]` della bozza (04, 09, 10) scattano alla lettera su codice corretto e tipico dell'area, o dividono due revisori. Basta un giro di Fable sul solo testo della skill (I1-I3, con m1-m8 nello stesso giro), poi un ritocco di opus a `comandi.md` e ai due punti dei test.
