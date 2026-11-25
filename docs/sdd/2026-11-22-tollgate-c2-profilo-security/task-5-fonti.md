# Verifica delle fonti di `rules-security`, dei pattern e dei marcatori (Task 5, Step 1)

**Metodo.** Verifica in sola lettura sul ramo `c2-profilo-security`, commit `abccbe0`. Letti per intero: `skills/rules-security/SKILL.md` (106 righe, 17 regole), `templates/profiles/security.toml`, `W/fonti/security/FONTI.md`, `agent-skills/security-and-hardening/SKILL.md`, `agent-skills/security-auditor.md`, `pagine/nextjs-proxy.md`, `pagine/marcatori.md`; letta l'intestazione di `agent-skills/LICENSE` (MIT, © 2025 Addy Osmani). Lette le sezioni citate: progetto di C, sezione 11; progetto di B, sezioni 3.4 e 12; catalogo, sezioni 2, 2.1, 2.3 e 4 (riga `rules-security`); spec del nucleo, sezione 8.5; `W/decisions.md` (1-4, 8, 9, 12, 15); le righe di `R-BACKEND-03/06/07/08`, `R-INFRA-05/06`, `R-DATABASE-13`. Il report `W/task-4-report.md` («Fonte per regola, punto esatto») è stato usato come indice e ricontrollato voce per voce sulle copie. `sha256sum -c SHA256SUMS` dentro `W/fonti/security/`: 6 file su 6 `OK`. Nessuna rete, nessun subagente, nessun file scritto oltre a questo. Le pagine OWASP e Trail of Bits non sono nel workspace: quelle voci sono verificate sulla sola scheda del controller.

Nota di lettura della tabella: una riga per ogni voce di ogni `Fonte:` (le voci sono separate da `;`). Due voci di R-SECURITY-07 nominano ciascuna due fonti unite da «e»: le ho divise in due righe ciascuna. Quando una voce nomina più sezioni, la cella ha una citazione di una riga per sezione, separate da ` / `. Le righe che in `pagine/*.md` non cominciano con `>` sono fatti scritti dal controller, non testo della pagina: lo dico nella cella.

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-SECURITY-01 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026, la sicurezza fin dal progetto: chi accede a ciò che si costruisce) | «gli avversari della spec e del piano cercano ciò che il documento non dice su chi accede, dati, segreti e input ostili» (voce «Sicurezza fin dal progetto in ogni lavoro (utente)») | ok |
| R-SECURITY-01 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (i confini di fiducia e i casi d'abuso si pensano prima dei controlli) | «Controls bolted on without a threat model are guesses. Before hardening, spend five minutes thinking like an attacker:» (riga 23; i punti 1 e 4 nominano confini e casi d'abuso) | ok |
| R-SECURITY-02 | progetto di B, sezione 3.4 (le regole «Prima di scrivere» di ogni area; la versione delle librerie viene dal file delle dipendenze, non dalla memoria) | «Prendi la versione delle librerie dal file delle dipendenze del progetto, non dalla memoria.» (riga `base` della tabella di 3.4) | ok (la 3.4 non ha una riga `security`: l'estensione è dichiarata «scelta nostra») |
| R-SECURITY-02 | https://github.com/auth0/node-jsonwebtoken (le opzioni di `jwt.verify` decidono quali algoritmi valgono e se la scadenza si controlla: un'opzione ricordata male toglie un controllo) | fatto del controller in `pagine/marcatori.md`, riga 20: «`algorithms` è l'elenco degli algoritmi ammessi; `ignoreExpiration`, se `true`, non controlla la scadenza» | ok (pagina ufficiale: fatti; la conseguenza «toglie un controllo» è una deduzione nostra) |
| R-SECURITY-03 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: l'accesso negato si considera in ogni lavoro) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi, e lo scrive nel report» | ok |
| R-SECURITY-03 | catalogo 2.3 (riga `security`: test dei casi di accesso negato) | «\| `security` \| test dei casi di accesso negato \|» (riga 96 del catalogo) | ok |
| R-SECURITY-03 | idea di OWASP Cheat Sheet «Authorization» (i test dell'autorizzazione provano anche il rifiuto) | idea letta dal controller sulla pagina, scheda I-7: «La logica di autorizzazione ha test automatici, che provano anche che l'accesso è negato quando deve.» | ok |
| R-SECURITY-03 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (il caso d'abuso diventa il primo test) | «For each feature, ask "how would I misuse this?" — then make that your first test.» (riga 38) | ok |
| R-SECURITY-04 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Broken Access Control» (oltre a chi è il chiamante si controlla che la risorsa sia sua) e «Never Do» (un controllo fatto nel client non è un confine) | «// Check that the authenticated user owns this resource» (riga 137) / «**Never trust client-side validation** as a security boundary» (riga 69) | ok (la fonte parla di validazione nel client; la regola dice «controllo»: stessa idea, parola più larga) |
| R-SECURITY-04 | idea di OWASP Cheat Sheet «Authorization» (permessi controllati a ogni richiesta e sul server) | idea letta dal controller sulla pagina, scheda I-6: «i permessi si controllano a ogni richiesta e sul server, mai solo nel client» | ok |
| R-SECURITY-04 | https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «Execution order»: un `matcher` che esclude un percorso salta anche le Server Function, che vanno protette una per una) | «> Always verify authentication and authorization inside each Server Function rather than relying on Proxy alone.» (`pagine/nextjs-proxy.md`, riga 11) | ok (pagina ufficiale: fatti) |
| R-SECURITY-05 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: valori predefiniti chiusi) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi» | ok |
| R-SECURITY-05 | idea di Trail of Bits `insecure-defaults` (senza un segreto o una configurazione il programma rifiuta, non ripiega su un valore permissivo) | idea letta dal controller sulla pagina, scheda I-8: «il programma si rifiuta di partire o nega l'accesso (chiuso), invece di proseguire con un ripiego permissivo (aperto)» | ok |
| R-SECURITY-05 | idea di OWASP Cheat Sheet «Authorization» (si nega quando nessuna regola concede) | idea letta dal controller sulla pagina, scheda I-6: «L'accesso si nega se nessuna regola lo concede» | ok |
| R-SECURITY-05 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Sensitive Data Exposure» (l'esempio si ferma se la chiave non è configurata) | «if (!API_KEY) throw new Error('STRIPE_API_KEY not configured');» (riga 186) | ok |
| R-SECURITY-06 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)» e «Broken Authentication» | «**Hash passwords** with bcrypt/scrypt/argon2 (never store plaintext)» (riga 50) / «const hashedPassword = await hash(plaintext, SALT_ROUNDS);» (riga 99) | ok |
| R-SECURITY-06 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» | «Are passwords hashed with a strong algorithm (bcrypt, scrypt, argon2)?» (riga 20; il titolo nella copia è «2. Authentication & Authorization») | ok |
| R-SECURITY-06 | idea di OWASP Cheat Sheet «Password Storage» (funzione lenta per le password, un sale ciascuna, niente hash veloci) | idea letta dal controller sulla pagina, scheda I-1: «hash di una funzione lenta pensata per le password (Argon2id, scrypt, bcrypt, PBKDF2), con un sale diverso per ognuna» | ok (Argon2id, PBKDF2, il sale e l'elenco degli hash veloci stanno solo nella scheda) |
| R-SECURITY-07 | https://github.com/auth0/node-jsonwebtoken (opzioni di `jwt.verify`: `algorithms` è l'elenco degli algoritmi ammessi, `ignoreExpiration` salta la scadenza) | fatto del controller in `pagine/marcatori.md`, riga 20: «`algorithms` è l'elenco degli algoritmi ammessi; `ignoreExpiration`, se `true`, non controlla la scadenza» | ok (pagina ufficiale: fatti) |
| R-SECURITY-07 | https://pypi.org/project/PyJWT/ (sezione «Usage»: la verifica passa `algorithms`) | «> jwt.decode(encoded, "secret", algorithms=["HS256"])» (`pagine/marcatori.md`, riga 38) | ok (pagina ufficiale: fatti) |
| R-SECURITY-07 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Security Review Checklist» (i token di reset scadono) | «- [ ] Password reset tokens expire» (riga 434) | ok |
| R-SECURITY-07 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» (i token di reset scadono) | «Are password reset tokens time-limited and single-use?» (riga 24) | ok |
| R-SECURITY-08 | idea di OWASP Cheat Sheet «Authentication» (hash e segreti si confrontano con una funzione sicura, non con l'uguaglianza normale) | idea letta dal controller sulla pagina, scheda I-5: «Hash e segreti si confrontano con una funzione sicura a tempo costante, non con l'uguaglianza normale.» | ok |
| R-SECURITY-09 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)», «Never Do» e «Broken Authentication» | «**Use httpOnly, secure, sameSite cookies** for sessions» (riga 52) / «**Never store sessions in client-accessible storage** (localStorage for auth tokens)» (riga 72) / «sameSite: 'lax',    // CSRF protection» (riga 110) | ok |
| R-SECURITY-09 | idea di OWASP Cheat Sheet «Session Management» (i tre attributi si dichiarano, non si lasciano al browser) | idea letta dal controller sulla pagina, scheda I-2: «Il cookie di sessione ha `Secure`, `HttpOnly` e un `SameSite` dichiarato (`Strict` o `Lax`), senza affidarsi ai valori predefiniti del browser.» | ok |
| R-SECURITY-10 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: nessun segreto nel codice né nei log) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi» | no: la sezione 11 nomina solo «segreti» tra le cose da considerare; «nel codice né nei log» non è nella scelta dell'utente (viene da `security-and-hardening`, «Never Do»). La voce attribuisce all'utente più di quanto è scritto |
| R-SECURITY-10 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Never Do», «Sensitive Data Exposure» e «Secrets Management» | «**Never commit secrets** to version control (API keys, passwords, tokens)» (riga 67; riga 68 per i log) / «// Never return sensitive fields in API responses» (riga 178) / «├── .env          → NOT committed (contains real secrets)» (riga 359) | ok |
| R-SECURITY-11 | idea di OWASP Cheat Sheet «Authentication» (un solo messaggio generico per login, reset e recupero) | idea letta dal controller sulla pagina, scheda I-3: «Login, reset e recupero rispondono con lo stesso messaggio generico sia quando l'utente non esiste sia quando la password è sbagliata» | ok |
| R-SECURITY-12 | progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: input non fidato) | «ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi» | ok |
| R-SECURITY-12 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Process: Threat Model First», «Always Do (No Exceptions)», «Injection (SQL, NoSQL, OS Command)» e «Schema Validation at Boundaries» | «Where does untrusted data cross into your system?» (riga 25) / «**Validate all external input** at the system boundary (API routes, form handlers)» (riga 46) / «// GOOD: Parameterized query» (riga 85) / «const result = CreateTaskSchema.safeParse(req.body);» (riga 238) | ok (per i comandi del sistema la sezione «Injection» ha solo il titolo; l'esempio è SQL) |
| R-SECURITY-12 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Input Handling» | «Is all user input validated at system boundaries?» (riga 13; riga 14 per SQL e comandi del sistema) | ok |
| R-SECURITY-13 | `security-auditor` di agent-skills 0.6.9 (MIT), sezioni «Input Handling» (reindirizzamenti controllati su un elenco) e «Third-Party Integrations» (richieste del server verso un URL dell'utente) | «Are URL redirects validated against an allowlist?» (riga 17) / «Are server-side fetches of user-supplied URLs allowlisted (SSRF)?» (riga 46) | ok |
| R-SECURITY-13 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Server-Side Request Forgery (SSRF)» | «if (!ALLOWED_HOSTS.has(url.hostname)) throw new Error('host not allowed');» (riga 206) | ok |
| R-SECURITY-14 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Security Misconfiguration» (CORS solo per origini note) e «Red Flags» (origini `*`) | «// CORS — restrict to known origins» (riga 168) / «Missing CORS configuration or wildcard (`*`) origins» (riga 498) | ok |
| R-SECURITY-14 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Infrastructure» | «Is CORS restricted to specific origins?» (riga 36) | ok |
| R-SECURITY-14 | https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «CORS»: l'intestazione si imposta solo per un'origine dell'elenco) | fatto del controller in `pagine/nextjs-proxy.md`, riga 13: «l'esempio usa un elenco di origini ammesse (`allowedOrigins`) e imposta `Access-Control-Allow-Origin` solo per un'origine dell'elenco» | ok (pagina ufficiale: fatti) |
| R-SECURITY-15 | `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Rate Limiting» (un limite più stretto per le rotte di login; con più istanze il contatore è condiviso) | «// Stricter limit for auth endpoints» (riga 333) / «**Count in a shared store once there is more than one process.**» (riga 340) | ok |
| R-SECURITY-15 | `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» | «Is rate limiting applied to authentication endpoints?» (riga 25) | ok |
| R-SECURITY-15 | idea di OWASP Cheat Sheet «Authentication» (i tentativi falliti si contano e si limitano per account) | idea letta dal controller sulla pagina, scheda I-4: «I tentativi di login falliti si contano e si limitano (per account, non solo per indirizzo).» | ok |
| R-SECURITY-16 | idea di Trail of Bits `differential-review` (il raggio d'azione di un cambio si dichiara, non si dà per scontato) | idea letta dal controller sulla pagina, scheda I-9: «Di un cambio si dichiara il raggio d'azione: quanti chiamanti e quali parti del sistema raggiunge, invece di darlo per scontato.» | ok |
| R-SECURITY-16 | catalogo 2.1 (riga `security`: revisione del diff per rischio e raggio d'azione) | «`final-security`: `rules-security`, revisione del diff per rischio e raggio d'azione» (riga 61 del catalogo, colonna «Specialista finale») | ok |
| R-SECURITY-17 | spec del nucleo, sezione 8.5 (gli effetti esterni sono negati finché l'utente non li approva) | «1. veto, con un identificativo;» seguito da «2. `/tollgate:approve effect <id>`;» (8.5, «Come funziona») | ok (stessa dicitura di R-INFRA-12 e R-DATABASE-16) |

Totale: 42 righe, 41 `ok`, 1 `no`.

## Sovrapposizioni

| Regola | Id approvato | Stesso difetto? | Esito |
|---|---|---|---|
| R-SECURITY-10 | R-BACKEND-07 | sì: «Nessun segreto scritto nel codice né nei `vars` della configurazione di Wrangler» (`skills/rules-backend/SKILL.md`, riga 41) | ok |
| R-SECURITY-10 | R-BACKEND-08 | sì: «Un segreto, un token o una password non finisce in una riga di log né nel corpo di una risposta d'errore» (riga 45) | ok |
| R-SECURITY-10 | R-INFRA-05 | sì: «Nessun segreto (chiave, token, password) nei file versionati» (`skills/rules-infra/SKILL.md`, riga 31) | ok |
| R-SECURITY-10 | R-INFRA-06 | sì, in parte: i file dei segreti locali (`.dev.vars*`, `.env`) che entrano nel diff sono un segreto in un file versionato; la parte su `.gitignore` di R-INFRA-06 non è ripetuta (riga 35) | ok |
| R-SECURITY-10 | R-DATABASE-13 | sì: «Nessuna chiave segreta, password del database o chiave `service_role` di Supabase in un file versionato né nel codice che gira nel browser» (`skills/rules-database/SKILL.md`, riga 69) | ok |
| R-SECURITY-12 | R-BACKEND-03 | sì: «Un endpoint nuovo o cambiato valida corpo, parametri e query prima di usarli» (riga 25) | ok |
| R-SECURITY-12 | R-BACKEND-06 | sì: «Le query al database e i comandi del sistema si costruiscono con parametri, mai concatenando l'input della richiesta» (riga 37) | ok |

Totale: 7 righe, 7 `ok`, 0 `no`. Gli id sono gli stessi della decisione 9 del piano.

Fuori tabella, per il controller (non è un `no`): R-SECURITY-17 ripete lo stesso tema di R-INFRA-12, R-DATABASE-16 e R-BACKEND-12 (nessuna azione su un servizio vero, il report dice la prova locale), e la sua `Fonte:` lo dice con «come nelle altre aree», ma non ha una riga «Si sovrappone a:». Se la pagina del profilo elenca le sovrapposizioni per la decisione dell'utente (decisione 15), questa manca dall'elenco.

## Pattern dei percorsi

| Pattern | Fonte | Citazione | Esito |
|---|---|---|---|
| `**/auth/**` | catalogo, sezione 2, riga `security` | «\| `security` \| `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**` \| **L2** \| **sì** \|» (riga 40 del catalogo) | ok |
| `**/middleware.*` | catalogo, sezione 2, riga `security`; `pagine/nextjs-proxy.md` per il nome | stessa riga 40 del catalogo; «> The `middleware` file convention is deprecated and has been renamed to `proxy`.» (`pagine/nextjs-proxy.md`, riga 5) | ok |
| `**/proxy.ts` | pagina ufficiale di Next.js, `pagine/nextjs-proxy.md` | «> Create a `proxy.ts` (or `.js`) file in the project root, or inside `src` if applicable, so that it is located at the same level as `pages` or `app`.» (riga 7) | ok |
| `**/proxy.js` | pagina ufficiale di Next.js, `pagine/nextjs-proxy.md` | stessa riga 7: «`proxy.ts` (or `.js`)» | ok |
| `**/security/**` | catalogo, sezione 2, riga `security` | stessa riga 40 del catalogo | ok |
| `**/rls/**` | catalogo, sezione 2, riga `security` | stessa riga 40 del catalogo | ok |

Totale: 6 righe, 6 `ok`, 0 `no`. Nessun pattern esce.

Larghezza dei pattern (punto 2). Costi già nominati dalle decisioni 1 e 2 del piano (si elencano, non sono un `no`):
- `**/auth/**` e `**/security/**`: accendono il codice di terzi copiato nel repo (`vendor/…/auth/`, `third_party/…/security/`), le immagini (`public/auth/`), i testi tradotti (`i18n/auth/`), una migrazione sotto `migrations/auth/`, i gruppi di sicurezza di Terraform sotto `infra/security/`, un intero pacchetto di un monorepo che si chiama `auth` (`package.json` compreso).
- `**/middleware.*`: accende anche un `middleware.ts` che fa solo log, `middleware.test.ts`, `middleware.config.json`, `middleware.d.ts`, un manifesto `middleware.yaml`; è un percorso esatto e vince contro la cartella di un altro profilo.
- `**/proxy.ts` e `**/proxy.js`: accendono anche un `proxy.ts` che non è di Next.js. La pagina dice «alla radice o dentro `src`»; il pattern vale a qualunque profondità, quindi prende anche, per esempio, `src/lib/proxy.ts` (un client di proxy HTTP) o `scripts/dev/proxy.js` (un proxy del server di sviluppo). Restano fuori `proxy.page.ts`, `proxy.mjs`.
Costi che le decisioni 1 e 2 non nominano (da portare alla pagina, non sono un `no`):
- `**/rls/**`: «rls» è anche la sigla di altro (per esempio una cartella `rls/` con un filtro «recursive least squares» in codice numerico): raro, ma nessuna decisione lo nomina.
- I commenti del frammento attribuiscono al catalogo una descrizione che il catalogo non ha: «Intestazioni e politiche di sicurezza (catalogo 2, riga `security`)» e «Policy di accesso alle righe fuori da `supabase/` (catalogo 2, riga `security`)». La riga 40 del catalogo elenca solo i pattern, senza dire cosa contengono: la descrizione è nostra, il pattern è del catalogo.

Altre chiavi di `[detect]` (non sono pattern, le riporto perché il brief le nomina): `exclude = ["supabase/"]` regge su progetto di B, sezione 12: «**Le edge function di Supabase restano a `database`** (dalla sezione 2, obiettivo 3, scelta dell'utente)»; `keep_paths = true` regge su progetto di C, sezione 11: «**I file di login riconosciuti per contenuto da un altro profilo accendono anche `security` (utente).**», che parla della cartella `auth/`; l'estensione ai file per nome (`middleware.*`, `proxy.*`) è dichiarata «nostra» nel commento del frammento e nella decisione 4.

## Marcatori di contenuto

Fonte di tutte le righe: `pagine/marcatori.md` (estratti del controller del 22/11/2026). Il confronto è a meno delle virgolette; `import … from` e `require(…)` sono righe diverse.

| Marcatore | Fonte | Citazione | Esito |
|---|---|---|---|
| `from 'bcrypt'` | README di node.bcrypt.js, sezione «ESM import» | «> import bcrypt from "bcrypt";» (riga 8) | ok (hash delle password) |
| `from "bcrypt"` | README di node.bcrypt.js, sezione «ESM import» | «> import bcrypt from "bcrypt";» (riga 8) | ok |
| `require('bcrypt')` | README di node.bcrypt.js, sezione «Usage» | «> const bcrypt = require('bcrypt');» (riga 6) | ok |
| `require("bcrypt")` | README di node.bcrypt.js, sezione «Usage» | «> const bcrypt = require('bcrypt');» (riga 6) | ok |
| `from 'bcryptjs'` | README di bcrypt.js (dcodeIO), sezione «Usage» | «> import bcrypt from "bcryptjs";» (riga 11) | ok (hash delle password) |
| `from "bcryptjs"` | README di bcrypt.js (dcodeIO), sezione «Usage» | «> import bcrypt from "bcryptjs";» (riga 11) | ok |
| `from 'argon2'` | README di node-argon2, sezione «TypeScript usage» | «> import * as argon2 from "argon2";» (riga 16) | ok (hash delle password) |
| `from "argon2"` | README di node-argon2, sezione «TypeScript usage» | «> import * as argon2 from "argon2";» (riga 16) | ok |
| `require('argon2')` | README di node-argon2, sezione «Usage» | «> const argon2 = require("argon2");» (riga 14) | ok |
| `require("argon2")` | README di node-argon2, sezione «Usage» | «> const argon2 = require("argon2");» (riga 14) | ok |
| `require('jsonwebtoken')` | README di node-jsonwebtoken, sezione «jwt.sign(…)» | «> var jwt = require('jsonwebtoken');» (riga 19) | ok (firma e verifica di token) |
| `require("jsonwebtoken")` | README di node-jsonwebtoken, sezione «jwt.sign(…)» | «> var jwt = require('jsonwebtoken');» (riga 19) | ok |
| `from 'jose'` | README di jose (panva), sezione «Documentation» | «> import * as jose from 'jose'» (riga 22) | ok (firma, cifra e verifica token) |
| `from "jose"` | README di jose (panva), sezione «Documentation» | «> import * as jose from 'jose'» (riga 22) | ok |
| `from 'iron-session'` | README di iron-session, sezione «Usage» | «> import { getIronSession } from "iron-session";» (riga 25) | ok, al confine: è una libreria di sessioni (cookie cifrato e firmato), non di hash né di JWT; non è una libreria di login completa né un client di un servizio. La decisione 4 lo porta già in «Da decidere tu» |
| `from "iron-session"` | README di iron-session, sezione «Usage» | «> import { getIronSession } from "iron-session";» (riga 25) | ok, al confine (come sopra) |
| `import bcrypt` | pypi.org/project/bcrypt, «Usage», «Password Hashing» | «> >>> import bcrypt» (riga 30) | ok (hash delle password) |
| `from argon2 import` | pypi.org/project/argon2-cffi, descrizione del progetto | «> from argon2 import PasswordHasher» (riga 32) | ok (hash delle password) |
| `from passlib` | passlib.readthedocs.io, «Hashing» | «> from passlib.hash import pbkdf2_sha256» (riga 34) | ok (hash delle password) |
| `import jwt` | pypi.org/project/PyJWT, «Usage» | «> import jwt» (riga 36) | ok (firma e verifica di token) |
| `from jose import` | pypi.org/project/python-jose, «Usage» | «> >>> from jose import jwt» (riga 40) | ok (firma e verifica di token) |

Totale: 21 righe, 21 `ok`, 0 `no` (due `ok` «al confine» per `iron-session`). I marcatori tolti dal controller non sono nel frammento: `require('bcryptjs')`, `require("bcryptjs")`, `from 'jsonwebtoken'`, `from "jsonwebtoken"` non compaiono (cercati con `grep` in `templates/profiles/security.toml`; di `jsonwebtoken` ci sono solo le due righe `require`). I commenti del frammento sui nomi delle sezioni («Usage», «ESM import», «TypeScript usage», «Documentation») corrispondono a `pagine/marcatori.md`.

Cos'altro accende ogni marcatore, come testo fisso (per la pagina dell'utente; non è un `no`):
- Tutti: una riga di commento, una stringa, un file di test o un mock che contiene quel pezzo; un `import type … from '…'` e un `export … from '…'`. Nessuno accende un `import('…')` dinamico, un `require( '…' )` con gli spazi o con il backtick.
- `from 'bcrypt'`, `from "bcrypt"`: solo il modulo `bcrypt` esatto (la virgoletta di chiusura esclude `bcryptjs` e `bcrypt-ts`).
- `require('bcrypt')`, `require("bcrypt")`: solo il modulo esatto. Un `require` di `bcryptjs` non accende niente (marcatore tolto).
- `from 'bcryptjs'`, `from "bcryptjs"`: anche codice del browser (la libreria gira anche lì).
- `from 'argon2'`, `from "argon2"`, `require(…)`: solo il pacchetto `argon2`; non `@node-rs/argon2`, `argon2-browser`, `hash-wasm`.
- `require('jsonwebtoken')`, `require("jsonwebtoken")`: solo CommonJS. La forma ESM più comune resta fuori: `import { sign } from 'jsonwebtoken'` e `import * as jwt from 'jsonwebtoken'` non accendono niente; `import jwt from 'jsonwebtoken'` si accende solo per via del marcatore Python `import jwt`, cioè solo se la variabile si chiama `jwt` (o comincia per `jwt`).
- `from 'jose'`, `from "jose"`: anche codice del browser, dei Worker, di Deno e di Bun; non gli import da un sottopercorso (`from 'jose/jwt/verify'`, delle versioni vecchie).
- `from 'iron-session'`, `from "iron-session"`: ogni file che legge la sessione (rotte, Server Component, azioni), non solo il login: tutti quei lavori salgono a L2; non gli import da un sottopercorso (`from 'iron-session/next'`).
- `import bcrypt`: anche `import bcrypt_utils`, `import bcryptjs from 'bcryptjs'` e `import bcrypt from 'bcrypt-ts'` in un file JavaScript o TypeScript (anche del browser).
- `from argon2 import`: anche `from argon2 import low_level`; non `import argon2` né `from argon2.exceptions import …`.
- `from passlib`: è un prefisso, quindi ogni modulo di passlib (`passlib.context`, `passlib.hash`, `passlib.totp`, `passlib.apache`, `passlib.utils`) e ogni pacchetto il cui nome comincia per `passlib`.
- `import jwt`: anche `import jwt_utils`, `import jwtDecode from 'jwt-decode'` (lettura di un token nel browser, senza verifica), `import jwt from 'jsonwebtoken'`, `import jwt from '@fastify/jwt'` o `'express-jwt'`, e in Go `import jwt "github.com/golang-jwt/jwt/v5"`.
- `from jose import`: anche `from jose import jwe`, `jwk`, `jws`; non `import jose` né `from jose.exceptions import …`.

## Riepilogo

**Righe per tabella.**
- Regole e fonti: 42 righe, 41 `ok`, 1 `no`.
- Sovrapposizioni: 7 righe, 7 `ok`, 0 `no`.
- Pattern dei percorsi: 6 righe, 6 `ok`, 0 `no`.
- Marcatori di contenuto: 21 righe, 21 `ok`, 0 `no`.

**Regole senza nessuna voce `ok`.** Nessuna. Tutte le 17 regole hanno almeno una voce `ok`.

**Regole con almeno una voce `no`.**
- R-SECURITY-10, voce «progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: nessun segreto nel codice né nei log)»: la sezione 11 dice solo che ogni implementatore considera i «segreti»; «nel codice né nei log» non è nella scelta dell'utente. Correzione minima: scrivere la parentesi come nelle altre regole, per esempio «(scelta dell'utente del 22/11/2026: i segreti si considerano in ogni lavoro)». La regola non perde appoggio: «nel codice» e «nei log» reggono su `security-and-hardening`, «Never Do» (righe 67 e 68), già citata nella stessa `Fonte:`. La correzione tiene le parole `progetto di C, sezione 11`, che i test cercano.

**`[blocca]` che non si giudicano su diff o report.** Nessuna. Le 13 `[blocca]` sono 01 e 17 (report) e 03, 04, 05, 06, 07, 08, 09, 10, 12, 13, 14 (diff). Le non bloccanti sono 02, 15, 16 (report) e 11 (diff). Nessuna regola si giudica sulla nota.

**Parti dichiarate «scelta nostra» (non verificate).**
- Paragrafo iniziale: i criteri per riconoscere nel diff controllo d'accesso, token, password, cookie di sessione e segreto.
- R-SECURITY-01: che il report lo scriva.
- R-SECURITY-02: applicare la regola alle librerie di sicurezza, e la via d'uscita per i progetti senza versione dichiarata.
- R-SECURITY-07: la scadenza per ogni token creato.
- R-SECURITY-08: i due nomi di funzione (`hmac.compare_digest`, `crypto.timingSafeEqual`), dichiarati «esempi nostri, dalle librerie standard di Python e di Node.js». Nel workspace non c'è nessuna copia che li mostri: restano sulla parola di chi ha scritto. Se serve una prova, il controller aggiunge due righe a `pagine/marcatori.md` dalle pagine ufficiali delle due librerie standard; altrimenti gli esempi si possono togliere senza toccare la regola, che regge sulla scheda I-5.
- R-SECURITY-09: chiedere i tre attributi scritti anche quando una libreria li imposta da sé.
- R-SECURITY-10: i valori finti nei test.
- R-SECURITY-11: lo stesso codice di stato.
- R-SECURITY-13: ammettere i percorsi interni.
- R-SECURITY-15: che basti dirlo nel report.
- R-SECURITY-16: che lo scriva il report.
- R-SECURITY-17: che il report dica la prova fatta.
- Frammento: `keep_paths` esteso ai file per nome («nostra per i nomi»).

**Parti di una regola senza una voce di fonte e non dichiarate «scelta nostra» nella `Fonte:`** (il report del Task 4 le chiama scelte nostre; la skill non lo dice; non sono un `no`, perché nessuna voce le attribuisce a una fonte):
- R-SECURITY-01 e R-SECURITY-16: la condizione «codice che non è solo test o documentazione».
- R-SECURITY-03: «nel diff o già nel repo» e i due casi (senza credenziali, utente non proprietario).
- R-SECURITY-04: «o in una guardia applicata alla sua rotta».
- R-SECURITY-05: gli esempi di ripiego (`process.env.X || "…"`, `os.environ.get("X", "…")`) e l'elenco di cosa è un'impostazione di sicurezza.
- R-SECURITY-06: «attraverso una libreria».
- R-SECURITY-07: «nessuna opzione spegne il controllo della firma»: le copie hanno un fatto solo sulla scadenza (`ignoreExpiration`); sulla firma nessuna voce porta un'opzione. E l'obbligo di passare `algorithms`: la fonte dice che cos'è l'opzione (jsonwebtoken) e la mostra in un esempio (PyJWT), non che sia obbligatoria.
- R-SECURITY-12: «con uno schema o con controlli espliciti di tipo e forma».
- R-SECURITY-14: limitare la regola al caso con le credenziali (le tre fonti chiedono origini note sempre) e l'origine «rimandata indietro senza confrontarla».
- R-SECURITY-17: l'elenco delle azioni (login, chiamate, chiavi create, ruotate o revocate).
Correzione minima, se il controller le vuole dichiarate: una frase «… è una scelta nostra» in coda alla `Fonte:`, come nelle altre regole.

**Pattern `no`.** Nessuno. **Marcatori `no`.** Nessuno; `from 'iron-session'` e `from "iron-session"` sono `ok` «al confine» (libreria di sessioni: la decisione 4 la porta all'utente).

**Frasi copiate (più di una decina di parole uguali a una fonte di terzi, anche tradotte alla lettera).** Nessuna trovata nelle copie MIT né negli estratti delle pagine. Tre casi vicini, che non conto come copiati e lascio al giudizio del controller:
- R-SECURITY-04, «In Next.js una Server Function lo verifica al suo interno e non si affida al solo `proxy.ts` o `middleware.ts`»: segue da vicino la riga citata della pagina di Next.js («> Always verify authentication and authorization inside each Server Function rather than relying on Proxy alone.», `pagine/nextjs-proxy.md`, riga 11). È una parafrasi di un fatto, con soggetto e parole diverse, non una traduzione parola per parola.
- R-SECURITY-12, «Le query al database e i comandi del sistema si costruiscono con parametri, mai concatenando quel valore»: uguale per più di dieci parole a R-BACKEND-06 (`skills/rules-backend/SKILL.md`, riga 37), che è una regola nostra già approvata, non testo di terzi.
- Parentesi delle `Fonte:` e testo di alcune regole vicini alle schede del controller, che sono parole sue e non testo delle pagine: R-SECURITY-08 («hash e segreti si confrontano con una funzione sicura, non con l'uguaglianza normale», scheda I-5), R-SECURITY-06 («(Argon2id, scrypt, bcrypt, PBKDF2), con un sale diverso per ogni password» e «(MD5, SHA-1, SHA-256 da solo)», scheda I-1), R-SECURITY-11 («quando l'utente non esiste e quando la password è sbagliata», scheda I-3). Quanto le schede siano lontane dal testo di OWASP e di Trail of Bits non si può controllare qui: le pagine non sono nel workspace (per scelta, decisione 8).

**Idee CC BY-SA senza la dicitura «idea di».** Nessuna. Le dieci voci OWASP e Trail of Bits (R-SECURITY-03, 04, 05 due volte, 06, 08, 09, 11, 15, 16) cominciano tutte con «idea di» e ognuna ha la sua scheda (I-1…I-9). Nessuna voce cita OWASP ASVS (`grep -i asvs` sulla skill e sul frammento: nessuna riga). La sezione «Fonti» della skill dà alle idee la licenza CC BY-SA 4.0 e la data di lettura.

**Segreti negli esempi.** Nessun segreto, token o chiave che sembri vero nella skill né nel frammento: l'unico valore è `PROVA-123`; gli esempi di ripiego hanno `"…"` al posto del valore.

**Altre osservazioni minori (non sono un `no`).**
- La sezione «Fonti» della skill elenca progetto di C, progetto di B e catalogo, ma non la spec del nucleo, che R-SECURITY-17 cita (sezione 8.5).
- Per R-SECURITY-02, R-SECURITY-07 (jsonwebtoken) e R-SECURITY-14 (Next.js, «CORS») la prova è una riga di fatti scritta dal controller, senza una citazione `>` della pagina: vale quanto l'estratto.
- R-SECURITY-17 non ha una riga «Si sovrappone a:» pur ripetendo il tema di R-INFRA-12, R-DATABASE-16 e R-BACKEND-12 (vedi «Sovrapposizioni»).
- Due commenti del frammento attribuiscono al catalogo la descrizione del contenuto di `security/` e `rls/`, che il catalogo non dà (vedi «Pattern dei percorsi»).

**Tracce di istruzioni di terzi nelle copie.** Nessun testo che chieda a chi legge il workspace di fare qualcosa (mandare dati, scaricare, cambiare impostazioni). Le due copie MIT sono, per natura, istruzioni per il loro agente e le ho trattate come dati, senza eseguirne nessuna: `security-auditor.md` comincia con un prompt di ruolo («You are an experienced Security Engineer conducting a security review.», riga 8) e ha una sezione «Composition» che dice quando invocarlo; `security-and-hardening/SKILL.md` contiene comandi d'esempio (per esempio la riga `git diff --cached | grep -i …` in «Secrets Management» e i comandi di audit dei pacchetti in «Supply-Chain Hygiene») e rimandi a un file `../../references/security-checklist.md` che non è nel workspace. Gli estratti `pagine/*.md` e `FONTI.md` non contengono istruzioni.
