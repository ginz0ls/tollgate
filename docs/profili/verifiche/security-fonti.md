# Verifica delle fonti di `rules-security`, dei pattern e dei marcatori

Verificatore: agente di sola lettura (Explore, Fable), il 23/11/2026, sulla bozza di `skills/rules-security/SKILL.md` e di `templates/profiles/security.toml` al commit `abccbe0`. Ha letto le copie locali delle fonti (le due copie di agent-skills 0.6.9 con la licenza, gli estratti delle pagine ufficiali di Next.js e delle librerie, le schede delle idee; la somma di controllo di ogni file è corretta), le sezioni citate del progetto di C (11), del progetto di B (3.4 e 12), del catalogo (2, 2.1, 2.3 e 4) e della spec del nucleo (8.5). Per ogni voce di ogni `Fonte:`, ogni pattern e ogni marcatore ha cercato la riga che la regge. Non ha usato la rete e non ha scritto nel repo. Le copie stanno fuori dal repo: i nomi `pagine/marcatori.md` e `pagine/nextjs-proxy.md` e i numeri di riga nelle citazioni sono i loro.

Come leggere le tabelle. Una riga per ogni voce di una `Fonte:`. Le citazioni stanno su una riga e solo in questo file. Le voci che cominciano con «idea di» vengono da pagine con licenza CC BY-SA 4.0 (OWASP Cheat Sheet Series, Trail of Bits): le pagine non sono state copiate, e la riga è marcata «idea letta dal controller sulla pagina», con la frase della scheda che il controller ha scritto con parole sue il 22/11/2026. «Fatto del controller» vuol dire una riga di fatti scritta dal controller leggendo la pagina ufficiale, non una frase della pagina.

Esito: ogni regola ha almeno una fonte `ok` per ogni voce. Alla prima passata c'era una riga `no`, di R-SECURITY-10: la voce attribuiva alla scelta dell'utente le parole «nel codice né nei log», che il progetto di C non dice. La voce è stata riscritta (commit `1749ee8`) e la riga `no` resta qui sotto come storia, seguita dalla riga `ok` della voce nuova.

Seconda passata (ri-revisore Fable, sola lettura, 23/11/2026, commit `1749ee8`): ha riletto le diciannove voci cambiate dal giro di correzione, cioè la voce nuova di R-SECURITY-10 e le frasi «scelta nostra» aggiunte in coda a quattordici `Fonte:`, più la frase sulla spec del nucleo nella sezione «Fonti» e i commenti del frammento. Esito: tutte `ok`.

Dopo la seconda passata il controller ha deciso quattro ritocchi di poche parole al testo delle regole 04, 05, 09 e 10 (23/11/2026). Non cambiano nessuna voce di fonte: l'unica `Fonte:` toccata è quella di R-SECURITY-05, nella sola frase «scelta nostra». Li ha riletti il revisore del Task 5 (Fable, sola lettura, 23/11/2026, commit `12c0b2d`): le righe toccate di 04, 05, 09 e 10 sono tutte `ok`.

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-SECURITY-01 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026, la sicurezza fin dal progetto: chi accede a ciò che si costruisce) | «gli avversari della spec e del piano cercano ciò che il documento non dice su chi accede, dati, segreti e input ostili» (voce «Sicurezza fin dal progetto in ogni lavoro (utente)») | ok |
| R-SECURITY-01 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (i confini di fiducia e i casi d'abuso si pensano prima dei controlli) | «Controls bolted on without a threat model are guesses. Before hardening, spend five minutes thinking like an attacker:» (riga 23; i punti 1 e 4 nominano confini e casi d'abuso) | ok |
| R-SECURITY-02 | progetto di B, sezione 3.4 (le regole «Prima di scrivere» di ogni area; la versione delle librerie viene dal file delle dipendenze, non dalla memoria) | «Prendi la versione delle librerie dal file delle dipendenze del progetto, non dalla memoria.» (riga `base` della tabella di 3.4) Nota del verificatore: la 3.4 non ha una riga `security`: l'estensione è dichiarata «scelta nostra». | ok |
| R-SECURITY-02 | https://github.com/auth0/node-jsonwebtoken (le opzioni di `jwt.verify` decidono quali algoritmi valgono e se la scadenza si controlla: un'opzione ricordata male toglie un controllo) | fatto del controller in `pagine/marcatori.md`, riga 20: «`algorithms` è l'elenco degli algoritmi ammessi; `ignoreExpiration`, se `true`, non controlla la scadenza» Nota del verificatore: pagina ufficiale: fatti; la conseguenza «toglie un controllo» è una deduzione nostra. | ok |
| R-SECURITY-03 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: l'accesso negato si considera in ogni lavoro) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi, e lo scrive nel report» | ok |
| R-SECURITY-03 | catalogo 2.3 (riga `security`: test dei casi di accesso negato) | «\| `security` \| test dei casi di accesso negato \|» (riga 96 del catalogo) | ok |
| R-SECURITY-03 | idea di OWASP Cheat Sheet «Authorization» (i test dell'autorizzazione provano anche il rifiuto) | idea letta dal controller sulla pagina, scheda I-7: «La logica di autorizzazione ha test automatici, che provano anche che l'accesso è negato quando deve.» | ok |
| R-SECURITY-03 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (il caso d'abuso diventa il primo test) | «For each feature, ask "how would I misuse this?" — then make that your first test.» (riga 38) | ok |
| R-SECURITY-04 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Broken Access Control» (oltre a chi è il chiamante si controlla che la risorsa sia sua) e «Never Do» (un controllo fatto nel client non è un confine) | «// Check that the authenticated user owns this resource» (riga 137) / «**Never trust client-side validation** as a security boundary» (riga 69) Nota del verificatore: la fonte parla di validazione nel client; la regola dice «controllo»: stessa idea, parola più larga. | ok |
| R-SECURITY-04 | idea di OWASP Cheat Sheet «Authorization» (permessi controllati a ogni richiesta e sul server) | idea letta dal controller sulla pagina, scheda I-6: «i permessi si controllano a ogni richiesta e sul server, mai solo nel client» | ok |
| R-SECURITY-04 | https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «Execution order»: un `matcher` che esclude un percorso salta anche le Server Function, che vanno protette una per una) | «> Always verify authentication and authorization inside each Server Function rather than relying on Proxy alone.» (`pagine/nextjs-proxy.md`, riga 11) Nota del verificatore: pagina ufficiale: fatti. | ok |
| R-SECURITY-05 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: valori predefiniti chiusi) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi» | ok |
| R-SECURITY-05 | idea di Trail of Bits `insecure-defaults` (senza un segreto o una configurazione il programma rifiuta, non ripiega su un valore permissivo) | idea letta dal controller sulla pagina, scheda I-8: «il programma si rifiuta di partire o nega l'accesso (chiuso), invece di proseguire con un ripiego permissivo (aperto)» | ok |
| R-SECURITY-05 | idea di OWASP Cheat Sheet «Authorization» (si nega quando nessuna regola concede) | idea letta dal controller sulla pagina, scheda I-6: «L'accesso si nega se nessuna regola lo concede» | ok |
| R-SECURITY-05 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Sensitive Data Exposure» (l'esempio si ferma se la chiave non è configurata) | «if (!API_KEY) throw new Error('STRIPE_API_KEY not configured');» (riga 186) | ok |
| R-SECURITY-06 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)» e «Broken Authentication» | «**Hash passwords** with bcrypt/scrypt/argon2 (never store plaintext)» (riga 50) / «const hashedPassword = await hash(plaintext, SALT_ROUNDS);» (riga 99) | ok |
| R-SECURITY-06 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» | «Are passwords hashed with a strong algorithm (bcrypt, scrypt, argon2)?» (riga 20; il titolo nella copia è «2. Authentication & Authorization») | ok |
| R-SECURITY-06 | idea di OWASP Cheat Sheet «Password Storage» (funzione lenta per le password, un sale ciascuna, niente hash veloci) | idea letta dal controller sulla pagina, scheda I-1: «hash di una funzione lenta pensata per le password (Argon2id, scrypt, bcrypt, PBKDF2), con un sale diverso per ognuna» Nota del verificatore: Argon2id, PBKDF2, il sale e l'elenco degli hash veloci stanno solo nella scheda. | ok |
| R-SECURITY-07 | https://github.com/auth0/node-jsonwebtoken (opzioni di `jwt.verify`: `algorithms` è l'elenco degli algoritmi ammessi, `ignoreExpiration` salta la scadenza) | fatto del controller in `pagine/marcatori.md`, riga 20: «`algorithms` è l'elenco degli algoritmi ammessi; `ignoreExpiration`, se `true`, non controlla la scadenza» Nota del verificatore: pagina ufficiale: fatti. | ok |
| R-SECURITY-07 | https://pypi.org/project/PyJWT/ (sezione «Usage»: la verifica passa `algorithms`) | «> jwt.decode(encoded, "secret", algorithms=["HS256"])» (`pagine/marcatori.md`, riga 38) Nota del verificatore: pagina ufficiale: fatti. | ok |
| R-SECURITY-07 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Security Review Checklist» (i token di reset scadono) | «- [ ] Password reset tokens expire» (riga 434) | ok |
| R-SECURITY-07 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» (i token di reset scadono) | «Are password reset tokens time-limited and single-use?» (riga 24) | ok |
| R-SECURITY-08 | idea di OWASP Cheat Sheet «Authentication» (hash e segreti si confrontano con una funzione sicura, non con l'uguaglianza normale) | idea letta dal controller sulla pagina, scheda I-5: «Hash e segreti si confrontano con una funzione sicura a tempo costante, non con l'uguaglianza normale.» | ok |
| R-SECURITY-09 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)», «Never Do» e «Broken Authentication» | «**Use httpOnly, secure, sameSite cookies** for sessions» (riga 52) / «**Never store sessions in client-accessible storage** (localStorage for auth tokens)» (riga 72) / «sameSite: 'lax',    // CSRF protection» (riga 110) | ok |
| R-SECURITY-09 | idea di OWASP Cheat Sheet «Session Management» (i tre attributi si dichiarano, non si lasciano al browser) | idea letta dal controller sulla pagina, scheda I-2: «Il cookie di sessione ha `Secure`, `HttpOnly` e un `SameSite` dichiarato (`Strict` o `Lax`), senza affidarsi ai valori predefiniti del browser.» | ok |
| R-SECURITY-10 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: nessun segreto nel codice né nei log) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi» Nota del verificatore: la sezione 11 nomina solo «segreti» tra le cose da considerare; «nel codice né nei log» non è nella scelta dell'utente (viene da `security-and-hardening`, «Never Do»). La voce attribuisce all'utente più di quanto è scritto. | no |
| R-SECURITY-10 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: i segreti si considerano in ogni lavoro) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi» (voce «Sicurezza fin dal progetto in ogni lavoro (utente)»; seconda passata) | ok |
| R-SECURITY-10 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Never Do», «Sensitive Data Exposure» e «Secrets Management» | «**Never commit secrets** to version control (API keys, passwords, tokens)» (riga 67; riga 68 per i log) / «// Never return sensitive fields in API responses» (riga 178) / «├── .env          → NOT committed (contains real secrets)» (riga 359) | ok |
| R-SECURITY-11 | idea di OWASP Cheat Sheet «Authentication» (un solo messaggio generico per login, reset e recupero) | idea letta dal controller sulla pagina, scheda I-3: «Login, reset e recupero rispondono con lo stesso messaggio generico sia quando l'utente non esiste sia quando la password è sbagliata» | ok |
| R-SECURITY-12 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: input non fidato) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi» | ok |
| R-SECURITY-12 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Process: Threat Model First», «Always Do (No Exceptions)», «Injection (SQL, NoSQL, OS Command)» e «Schema Validation at Boundaries» | «Where does untrusted data cross into your system?» (riga 25) / «**Validate all external input** at the system boundary (API routes, form handlers)» (riga 46) / «// GOOD: Parameterized query» (riga 85) / «const result = CreateTaskSchema.safeParse(req.body);» (riga 238) Nota del verificatore: per i comandi del sistema la sezione «Injection» ha solo il titolo; l'esempio è SQL. | ok |
| R-SECURITY-12 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Input Handling» | «Is all user input validated at system boundaries?» (riga 13; riga 14 per SQL e comandi del sistema) | ok |
| R-SECURITY-13 | `security-auditor` di agent-skills 0.6.9 (MIT), sezioni «Input Handling» (reindirizzamenti controllati su un elenco) e «Third-Party Integrations» (richieste del server verso un URL dell'utente) | «Are URL redirects validated against an allowlist?» (riga 17) / «Are server-side fetches of user-supplied URLs allowlisted (SSRF)?» (riga 46) | ok |
| R-SECURITY-13 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Server-Side Request Forgery (SSRF)» | «if (!ALLOWED_HOSTS.has(url.hostname)) throw new Error('host not allowed');» (riga 206) | ok |
| R-SECURITY-14 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Security Misconfiguration» (CORS solo per origini note) e «Red Flags» (origini `*`) | «// CORS — restrict to known origins» (riga 168) / «Missing CORS configuration or wildcard (`*`) origins» (riga 498) | ok |
| R-SECURITY-14 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Infrastructure» | «Is CORS restricted to specific origins?» (riga 36) | ok |
| R-SECURITY-14 | https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «CORS»: l'intestazione si imposta solo per un'origine dell'elenco) | fatto del controller in `pagine/nextjs-proxy.md`, riga 13: «l'esempio usa un elenco di origini ammesse (`allowedOrigins`) e imposta `Access-Control-Allow-Origin` solo per un'origine dell'elenco» Nota del verificatore: pagina ufficiale: fatti. | ok |
| R-SECURITY-15 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Rate Limiting» (un limite più stretto per le rotte di login; con più istanze il contatore è condiviso) | «// Stricter limit for auth endpoints» (riga 333) / «**Count in a shared store once there is more than one process.**» (riga 340) | ok |
| R-SECURITY-15 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» | «Is rate limiting applied to authentication endpoints?» (riga 25) | ok |
| R-SECURITY-15 | idea di OWASP Cheat Sheet «Authentication» (i tentativi falliti si contano e si limitano per account) | idea letta dal controller sulla pagina, scheda I-4: «I tentativi di login falliti si contano e si limitano (per account, non solo per indirizzo).» | ok |
| R-SECURITY-16 | idea di Trail of Bits `differential-review` (il raggio d'azione di un cambio si dichiara, non si dà per scontato) | idea letta dal controller sulla pagina, scheda I-9: «Di un cambio si dichiara il raggio d'azione: quanti chiamanti e quali parti del sistema raggiunge, invece di darlo per scontato.» | ok |
| R-SECURITY-16 | catalogo 2.1 (riga `security`: revisione del diff per rischio e raggio d'azione) | «`final-security`: `rules-security`, revisione del diff per rischio e raggio d'azione» (riga 61 del catalogo, colonna «Specialista finale») | ok |
| R-SECURITY-17 | spec del nucleo, sezione 8.5 (gli effetti esterni sono negati finché l'utente non li approva) | «1. veto, con un identificativo;» seguito da «2. `/tollgate:approve effect <id>`;» (8.5, «Come funziona») Nota del verificatore: stessa dicitura di R-INFRA-12 e R-DATABASE-16. | ok |

Totale: 43 righe, 42 `ok` e 1 `no` (la voce uscita di R-SECURITY-10). Le voci «scelta nostra» e gli esempi nostri non sono in questa tabella: stanno più sotto.

## Sovrapposizioni

Le due regole che ripetono regole già approvate di altre aree (righe «Si sovrappone a:» della skill), con la riga della regola approvata.

| Regola | Id approvato | Stesso difetto? | Esito |
|---|---|---|---|
| R-SECURITY-10 | R-BACKEND-07 | sì: «Nessun segreto scritto nel codice né nei `vars` della configurazione di Wrangler» (`skills/rules-backend/SKILL.md`, riga 41) | ok |
| R-SECURITY-10 | R-BACKEND-08 | sì: «Un segreto, un token o una password non finisce in una riga di log né nel corpo di una risposta d'errore» (riga 45) | ok |
| R-SECURITY-10 | R-INFRA-05 | sì: «Nessun segreto (chiave, token, password) nei file versionati» (`skills/rules-infra/SKILL.md`, riga 31) | ok |
| R-SECURITY-10 | R-INFRA-06 | sì, in parte: i file dei segreti locali (`.dev.vars*`, `.env`) che entrano nel diff sono un segreto in un file versionato; la parte su `.gitignore` di R-INFRA-06 non è ripetuta (riga 35) | ok |
| R-SECURITY-10 | R-DATABASE-13 | sì: «Nessuna chiave segreta, password del database o chiave `service_role` di Supabase in un file versionato né nel codice che gira nel browser» (`skills/rules-database/SKILL.md`, riga 69) | ok |
| R-SECURITY-12 | R-BACKEND-03 | sì: «Un endpoint nuovo o cambiato valida corpo, parametri e query prima di usarli» (riga 25) | ok |
| R-SECURITY-12 | R-BACKEND-06 | sì: «Le query al database e i comandi del sistema si costruiscono con parametri, mai concatenando l'input della richiesta» (riga 37) | ok |

Fuori tabella: R-SECURITY-17 tratta lo stesso tema di R-INFRA-12, R-DATABASE-16 e R-BACKEND-12 (nessuna azione su un servizio vero, il report dice la prova locale) e la sua `Fonte:` lo dice con «come nelle altre aree», ma non ha una riga «Si sovrappone a:». La pagina per l'utente lo porta tra i punti da decidere.

## Pattern dei percorsi

| Pattern | Fonte | Citazione | Esito |
|---|---|---|---|
| `**/auth/**` | catalogo, sezione 2, riga `security` | «\| `security` \| `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**` \| **L2** \| **sì** \|» (riga 40 del catalogo) | ok |
| `**/middleware.*` | catalogo, sezione 2, riga `security`; `pagine/nextjs-proxy.md` per il nome | stessa riga 40 del catalogo; «> The `middleware` file convention is deprecated and has been renamed to `proxy`.» (`pagine/nextjs-proxy.md`, riga 5) | ok |
| `**/proxy.ts` | pagina ufficiale di Next.js, `pagine/nextjs-proxy.md` | «> Create a `proxy.ts` (or `.js`) file in the project root, or inside `src` if applicable, so that it is located at the same level as `pages` or `app`.» (riga 7) | ok |
| `**/proxy.js` | pagina ufficiale di Next.js, `pagine/nextjs-proxy.md` | stessa riga 7: «`proxy.ts` (or `.js`)» | ok |
| `**/security/**` | catalogo, sezione 2, riga `security` | stessa riga 40 del catalogo | ok |
| `**/rls/**` | catalogo, sezione 2, riga `security` | stessa riga 40 del catalogo | ok |

Nessun pattern esce. Il catalogo elencava anche `**/*session*`: non è nel frammento per una scelta dell'utente del 22/11/2026 (progetto di C, sezione 11), non per un esito `no`. `**/proxy.ts` e `**/proxy.js` non sono nel catalogo: li regge la pagina di Next.js, e averli aggiunti è una scelta nostra.

Quanto sono larghi i pattern (costi, non esiti `no`; la pagina per l'utente li porta tra i punti da decidere):

- `**/auth/**` e `**/security/**` accendono anche il codice di terzi copiato nel repo, le immagini, i testi tradotti, una migrazione sotto `migrations/auth/`, la configurazione sotto `infra/security/` e un intero pacchetto di un monorepo che si chiama `auth`.
- `**/middleware.*` accende anche un `middleware.ts` che fa solo log, un file di test, un file di configurazione, un file di tipi e un manifesto `middleware.yaml`; è un percorso esatto e vince contro la cartella di un altro profilo.
- `**/proxy.ts` e `**/proxy.js` valgono a qualunque profondità, mentre la pagina di Next.js parla della radice o di `src`: accendono anche un `proxy.ts` che non è di Next.js. Restano fuori `proxy.page.ts` e `proxy.mjs`.
- `**/rls/**`: «rls» può essere anche la sigla di altro, in codice che non c'entra con il database. Caso raro.
- La riga del catalogo elenca i pattern senza dire che cosa contengono le cartelle: quella lettura è nostra, e i commenti del frammento lo dicono.

Le altre due chiavi del rilevamento: `exclude = ["supabase/"]` regge sul progetto di B, sezione 12 (le edge function di Supabase restano a `database`); `keep_paths = true` regge sul progetto di C, sezione 11 (un file di login riconosciuto per contenuto da un altro profilo accende anche `security`), che parla della cartella `auth/`. Averla estesa ai file per nome (`middleware.*`, `proxy.ts`, `proxy.js`) è una scelta nostra.

## Marcatori di contenuto

Fonte di tutte le righe: gli estratti del controller dalle pagine ufficiali delle librerie (22/11/2026). Il confronto è a meno delle virgolette; `import … from` e `require(…)` sono righe diverse. Sono le sole librerie di hash delle password e di firma e verifica dei token, cercate come testo fisso.

| Marcatore | Fonte | Citazione | Esito |
|---|---|---|---|
| `from 'bcrypt'` | README di node.bcrypt.js, sezione «ESM import» | «> import bcrypt from "bcrypt";» (riga 8) Nota del verificatore: hash delle password. | ok |
| `from "bcrypt"` | README di node.bcrypt.js, sezione «ESM import» | «> import bcrypt from "bcrypt";» (riga 8) | ok |
| `require('bcrypt')` | README di node.bcrypt.js, sezione «Usage» | «> const bcrypt = require('bcrypt');» (riga 6) | ok |
| `require("bcrypt")` | README di node.bcrypt.js, sezione «Usage» | «> const bcrypt = require('bcrypt');» (riga 6) | ok |
| `from 'bcryptjs'` | README di bcrypt.js (dcodeIO), sezione «Usage» | «> import bcrypt from "bcryptjs";» (riga 11) Nota del verificatore: hash delle password. | ok |
| `from "bcryptjs"` | README di bcrypt.js (dcodeIO), sezione «Usage» | «> import bcrypt from "bcryptjs";» (riga 11) | ok |
| `from 'argon2'` | README di node-argon2, sezione «TypeScript usage» | «> import * as argon2 from "argon2";» (riga 16) Nota del verificatore: hash delle password. | ok |
| `from "argon2"` | README di node-argon2, sezione «TypeScript usage» | «> import * as argon2 from "argon2";» (riga 16) | ok |
| `require('argon2')` | README di node-argon2, sezione «Usage» | «> const argon2 = require("argon2");» (riga 14) | ok |
| `require("argon2")` | README di node-argon2, sezione «Usage» | «> const argon2 = require("argon2");» (riga 14) | ok |
| `require('jsonwebtoken')` | README di node-jsonwebtoken, sezione «jwt.sign(…)» | «> var jwt = require('jsonwebtoken');» (riga 19) Nota del verificatore: firma e verifica di token. | ok |
| `require("jsonwebtoken")` | README di node-jsonwebtoken, sezione «jwt.sign(…)» | «> var jwt = require('jsonwebtoken');» (riga 19) | ok |
| `from 'jose'` | README di jose (panva), sezione «Documentation» | «> import * as jose from 'jose'» (riga 22) Nota del verificatore: firma, cifra e verifica token. | ok |
| `from "jose"` | README di jose (panva), sezione «Documentation» | «> import * as jose from 'jose'» (riga 22) | ok |
| `from 'iron-session'` | README di iron-session, sezione «Usage» | «> import { getIronSession } from "iron-session";» (riga 25) Nota del verificatore: al confine: è una libreria di sessioni (cookie cifrato e firmato), non di hash né di JWT; non è una libreria di login completa né un client di un servizio. La decisione 4 lo porta già in «Cosa hai deciso». | ok |
| `from "iron-session"` | README di iron-session, sezione «Usage» | «> import { getIronSession } from "iron-session";» (riga 25) Nota del verificatore: al confine (come sopra). | ok |
| `import bcrypt` | pypi.org/project/bcrypt, «Usage», «Password Hashing» | «> >>> import bcrypt» (riga 30) Nota del verificatore: hash delle password. | ok |
| `from argon2 import` | pypi.org/project/argon2-cffi, descrizione del progetto | «> from argon2 import PasswordHasher» (riga 32) Nota del verificatore: hash delle password. | ok |
| `from passlib` | passlib.readthedocs.io, «Hashing» | «> from passlib.hash import pbkdf2_sha256» (riga 34) Nota del verificatore: hash delle password. | ok |
| `import jwt` | pypi.org/project/PyJWT, «Usage» | «> import jwt» (riga 36) Nota del verificatore: firma e verifica di token. | ok |
| `from jose import` | pypi.org/project/python-jose, «Usage» | «> >>> from jose import jwt» (riga 40) Nota del verificatore: firma e verifica di token. | ok |

Totale: 21 righe, 21 `ok`. Le due righe di `iron-session` sono `ok` «al confine»: è una libreria di sessioni in un cookie, non di hash né di token firmati.

Marcatori tolti dal controller prima della bozza (22/11/2026), perché nessuna pagina ufficiale mostra la riga: `require('bcryptjs')` e la stessa riga con le virgolette doppie (la pagina di bcryptjs mostra solo la forma `import`), `from 'jsonwebtoken'` e la stessa riga con le virgolette doppie (la pagina di jsonwebtoken mostra solo la forma `require`). Non sono nel frammento.

Cos'altro accende un marcatore, perché è testo fisso e non guarda il linguaggio (costi, non esiti `no`):

- Tutti: anche una riga di commento, una stringa o un file che contiene quel pezzo di testo. Il rilevamento per contenuto salta i file di test: le cartelle `tests/`, `test/`, `__tests__/` e i nomi `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`, `conftest.py`. Un test dentro una cartella del profilo si accende lo stesso, per il percorso (caso S22 della tabella delle precedenze). Un mock fuori da quelle cartelle e senza quei nomi resta rilevato.
- `import jwt`: anche `import jwt_utils`, `import jwtDecode from 'jwt-decode'` (una libreria del browser che legge un token senza verificarlo), `import jwt from 'jsonwebtoken'` e gli altri import di JavaScript che cominciano così.
- `import bcrypt`: anche `import bcryptjs from 'bcryptjs'` in un file JavaScript.
- `from 'jose'` e `from 'bcryptjs'`: anche codice che gira nel browser.
- `from 'iron-session'`: ogni file che legge la sessione, non solo il login.
- `from passlib`: è un prefisso, quindi ogni modulo di passlib.
- Di `jsonwebtoken` resta solo la forma `require`: `import { sign } from 'jsonwebtoken'` non accende niente.

## Parti dichiarate «scelta nostra»

Non hanno una fonte e la skill lo dice nella `Fonte:` di ogni regola. Stanno nella pagina per l'utente, nella sezione «Cosa hai deciso»:

- R-SECURITY-01: che lo scriva il report, e la condizione sul tipo di file.
- R-SECURITY-02: applicare la regola alle librerie di sicurezza, e la via d'uscita per i progetti senza versione dichiarata. Il progetto di B, sezione 3.4, non ha una riga per `security`: è la regola con l'appoggio più debole.
- R-SECURITY-03: «nel diff o già nel repo» e i due casi da provare.
- R-SECURITY-04: la guardia di rotta e i due casi in cui la regola non si applica.
- R-SECURITY-05: gli esempi di ripiego, l'elenco chiuso delle impostazioni e i valori finti ammessi nei test.
- R-SECURITY-06: «attraverso una libreria» e il caso del servizio di login.
- R-SECURITY-07: l'obbligo di passare `algorithms`, il divieto di spegnere il controllo della firma e la scadenza per ogni token creato.
- R-SECURITY-08: i due nomi di funzione (`hmac.compare_digest`, `crypto.timingSafeEqual`) sono esempi nostri, senza una pagina copiata; l'esclusione dei test e della ricerca nel database.
- R-SECURITY-09: distinguere il cookie costruito dal codice da quello scritto da una libreria, accettare `Secure` legato all'ambiente, ammettere `SameSite=None` con il motivo.
- R-SECURITY-10: i valori finti nei test e l'eccezione per il token consegnato al suo titolare.
- R-SECURITY-11: lo stesso codice di stato.
- R-SECURITY-12: «con uno schema o con controlli espliciti» e la verifica di una libreria che vale come validazione.
- R-SECURITY-13: ammettere i percorsi interni, e dire cosa non lo è.
- R-SECURITY-14: limitare la regola al caso con le credenziali, e nominare l'origine rimandata indietro.
- R-SECURITY-15: che basti dirlo nel report.
- R-SECURITY-16: che lo scriva il report, e la condizione sul tipo di file.
- R-SECURITY-17: l'elenco delle azioni e la prova detta nel report.
- L'introduzione della skill: i criteri per riconoscere nel diff un controllo d'accesso, un token, una password, un cookie di sessione e un segreto.
- Il frammento: `keep_paths` esteso ai file per nome, `**/proxy.ts` e `**/proxy.js` aggiunti al catalogo, e ciò che i commenti dicono del contenuto delle cartelle.
- Le precedenze tra profili (la tabella della decisione 5 del piano): costi che la pagina porta in «Cosa hai deciso».

## Regole tolte dalla verifica

Nessuna regola esce: ciascuna ha almeno una fonte `ok` per ogni voce, e i numeri restano. Nessun pattern e nessun marcatore esce dalla verifica; i quattro marcatori tolti li ha tolti il controller prima della bozza. Nessuna regola cita OWASP ASVS: la pagina letta dal controller non mostrava i capitoli, quindi nessuna scheda viene da lì. Nessuna regola cita la skill `security-review`, che la skill nomina solo in «Dove informarsi».

Una voce è uscita e una è entrata al suo posto: quella di R-SECURITY-10 sul progetto di C (riga `no` e riga `ok` nella tabella). Dopo la revisione sono cambiati i testi di dodici regole (01, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13 e 16) e, per le sole frasi «scelta nostra» della `Fonte:`, di altre tre (03, 14 e 17), senza aggiungere né togliere fonti che reggevano.

Frasi copiate: il verificatore non ha trovato nella skill nessuna frase uguale a una fonte di terzi per più di una decina di parole, nemmeno tradotta. Una frase di R-SECURITY-12 è uguale a quella di R-BACKEND-06, che è una regola nostra già approvata.
