---
name: rules-security
description: Regole di tollgate per la sicurezza (accesso, login, token, password, cookie di sessione, middleware e proxy, segreti): le caricano in automatico gli agenti dell'area security, non serve invocarla.
version: 1
approved: 2026-11-23
---
# Regole security (versione 1)

Sono le regole per il codice che decide chi può fare cosa: login, controlli d'accesso, token, password, cookie di sessione, middleware e proxy, segreti. Valgono in aggiunta a quelle di base. Chi scrive le segue prima di toccare un file. Chi rivede le applica guardando ciò che ha davanti, e per ognuna risponde sì o no: sotto ogni regola la riga «Si giudica su» dice se la risposta sta nel diff o nel report. Le regole segnate `[blocca]` si giudicano sul diff o sul report, perché nei lavori senza il passo «informati prima» la nota non c'è. Una regola che comincia con «Se il diff» non si applica quando il diff non ha quel codice. Un difetto si segnala una volta sola, con la regola che viola.

Nel diff si riconoscono così (questi criteri sono una scelta nostra):

- un **controllo d'accesso** è codice nuovo o cambiato che decide se una richiesta prosegue guardando chi la fa: un confronto sull'utente, sul ruolo o sul proprietario seguito da un rifiuto (risposta 401 o 403, reindirizzamento al login, errore), una guardia o un decoratore applicato a una rotta, la funzione e il `matcher` di un `middleware.*` o di un `proxy.ts`;
- un **token** è un valore che prova chi è il chiamante (un JWT, un token di sessione o di reset, la chiave di un'API): si vede da una chiamata che lo crea, lo firma o lo verifica (`sign`, `verify`, `decode` di una libreria di token), o da un valore letto dall'intestazione `Authorization` o da un cookie e poi confrontato;
- una **password** è un campo o una variabile `password` (o `passwd`, `pwd`) che arriva da una richiesta e che il codice salva o controlla; si vede anche dalle chiamate a una libreria di hash (`bcrypt`, `argon2`, `passlib`);
- un **cookie di sessione** è un cookie che il server imposta dopo il login e che porta un token o un identificativo di sessione: si vede dal codice che lo imposta (l'intestazione `Set-Cookie`, una chiamata come `res.cookie` o `cookies().set`, le opzioni `cookie` di una libreria di sessioni);
- un **segreto** è una chiave, un token, una password o una chiave di firma: un valore che permette a chi lo conosce di farsi passare per un altro.

Una edge function e una policy sotto `supabase/` alla radice del progetto hanno le regole di `database` (progetto di B, sezione 12), non queste; le regole sulle policy RLS restano solo di `database`. Quando nello stesso lavoro è attiva un'altra area e un difetto cade sotto due regole (le righe «Si sovrappone a»), si segnala con la regola dell'area del file.

## Prima di scrivere

R-SECURITY-01 [blocca] Se il diff cambia un file che non è un test né un documento, il report dice chi può arrivare al codice cambiato (un anonimo, un utente autenticato, un amministratore, un altro servizio), cosa può fare da lì e quale controllo lo ferma; se da fuori non ci arriva nessuno, lo dice.
Si giudica su: report
Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026, la sicurezza fin dal progetto: chi accede a ciò che si costruisce); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (i confini di fiducia e i casi d'abuso si pensano prima dei controlli); che il report lo scriva, e la condizione sul tipo di file, sono una scelta nostra

R-SECURITY-02 Se il diff usa per la prima volta nel file una libreria di hash delle password, di token, di sessioni o di login, il report ha l'indirizzo della documentazione ufficiale della versione scritta nel file delle dipendenze, con la versione; se il progetto non la dichiara, il report lo dice e dà l'indirizzo della documentazione corrente.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (le regole «Prima di scrivere» di ogni area; la versione delle librerie viene dal file delle dipendenze, non dalla memoria); https://github.com/auth0/node-jsonwebtoken (le opzioni di `jwt.verify` decidono quali algoritmi valgono e se la scadenza si controlla: un'opzione ricordata male toglie un controllo); applicarlo alle librerie di sicurezza, e la via d'uscita per i progetti senza versione dichiarata, sono una scelta nostra

## Mentre lavori

R-SECURITY-03 [blocca] Se il diff aggiunge o cambia un controllo d'accesso, c'è un test (nel diff o già nel repo) del caso negato: una richiesta senza credenziali valide e, dove la risorsa ha un proprietario, quella di un utente che non lo è. Il test controlla che l'accesso sia rifiutato.
Si giudica su: diff
Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: l'accesso negato si considera in ogni lavoro); catalogo 2.3 (riga `security`: test dei casi di accesso negato); idea di OWASP Cheat Sheet «Authorization» (i test dell'autorizzazione provano anche il rifiuto); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (il caso d'abuso diventa il primo test); «nel diff o già nel repo» e i due casi da provare sono una scelta nostra

R-SECURITY-04 [blocca] Se il diff aggiunge o cambia una funzione del server che legge o cambia dati legati a un utente (un endpoint, un gestore di rotta, una Server Function), il controllo di chi chiama gira sul server per quella funzione, mai solo nel codice del browser: dentro di essa o in una guardia applicata alla sua rotta (per una Server Function di Next.js solo dentro di essa: `proxy.ts` o `middleware.ts` da soli non bastano). Dove il dato ha un proprietario, il codice lo confronta con il chiamante. Non si applica a una funzione che è essa stessa il login, la registrazione, la richiesta di reset o la callback di un login. Non si applica nemmeno a una funzione che legge solo dati pubblici (dati che chiunque può già leggere senza login), se il diff lo dichiara dove registra la rotta o in un commento accanto.
Si giudica su: diff
Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Broken Access Control» (oltre a chi è il chiamante si controlla che la risorsa sia sua) e «Never Do» (un controllo fatto nel client non è un confine); idea di OWASP Cheat Sheet «Authorization» (permessi controllati a ogni richiesta e sul server); https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «Execution order»: un `matcher` che esclude un percorso salta anche le Server Function, che vanno protette una per una); la guardia di rotta e i due casi in cui la regola non si applica sono una scelta nostra

R-SECURITY-05 [blocca] Se il diff aggiunge o cambia codice che legge un segreto (anche una chiave di firma) o un'impostazione di sicurezza, quando il valore manca il codice si ferma o nega l'accesso. Per un segreto nessun valore di ripiego scritto nel codice (come `process.env.X || "…"` o `os.environ.get("X", "…")`). Per un'impostazione di sicurezza l'unico ripiego ammesso è il valore che nega (un elenco vuoto, il controllo acceso). Sono impostazioni di sicurezza solo queste: l'elenco delle origini ammesse, l'elenco dei ruoli ammessi, un interruttore che spegne un controllo. Un controllo d'accesso che non riconosce il caso (un ruolo sconosciuto, il ramo `default`) nega. Nei file di test un valore finto evidente (come `PROVA-123`) è ammesso.
Si giudica su: diff
Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: valori predefiniti chiusi); idea di Trail of Bits `insecure-defaults` (senza un segreto o una configurazione il programma rifiuta, non ripiega su un valore permissivo); idea di OWASP Cheat Sheet «Authorization» (si nega quando nessuna regola concede); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Sensitive Data Exposure» (l'esempio si ferma se la chiave non è configurata); gli esempi di ripiego, l'elenco chiuso delle impostazioni e i valori finti ammessi nei test sono una scelta nostra

R-SECURITY-06 [blocca] Se il diff salva o controlla una password, usa attraverso una libreria una funzione di hash lenta nata per le password (Argon2id, scrypt, bcrypt, PBKDF2), con un sale diverso per ogni password. Nessuna password in chiaro o cifrata in modo reversibile, e nessun hash veloce (MD5, SHA-1, SHA-256 da solo). Non si applica quando il codice non salva la password e la passa a un servizio di login, che la controlla lui.
Si giudica su: diff
Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)» e «Broken Authentication»; `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization»; idea di OWASP Cheat Sheet «Password Storage» (funzione lenta per le password, un sale ciascuna, niente hash veloci); «attraverso una libreria» e il caso del servizio di login sono una scelta nostra

R-SECURITY-07 [blocca] Se il diff verifica un token firmato, nessuna opzione spegne il controllo della firma o della scadenza (come `ignoreExpiration: true` di jsonwebtoken), e con jsonwebtoken e PyJWT la chiamata passa l'elenco degli algoritmi ammessi, `algorithms` (`jwt.verify` di jsonwebtoken, `jwt.decode` di PyJWT). Un token che il diff crea (d'accesso, di sessione, di reset) ha una scadenza.
Si giudica su: diff
Fonte: https://github.com/auth0/node-jsonwebtoken (opzioni di `jwt.verify`: `algorithms` è l'elenco degli algoritmi ammessi, `ignoreExpiration` salta la scadenza) e https://pypi.org/project/PyJWT/ (sezione «Usage»: la verifica passa `algorithms`); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Security Review Checklist», e `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» (i token di reset scadono); l'obbligo di passare `algorithms`, il divieto di spegnere il controllo della firma e la scadenza per ogni token creato sono una scelta nostra

R-SECURITY-08 [blocca] Se il diff, nel codice che non è di test, confronta un segreto, un token, una firma o l'hash di un segreto con un valore ricevuto da fuori, usa una funzione a tempo costante (per esempio `hmac.compare_digest` in Python o `crypto.timingSafeEqual` in Node.js) o la funzione di verifica della libreria, non `==` né `===`. Una ricerca nel database per token non è un confronto.
Si giudica su: diff
Fonte: idea di OWASP Cheat Sheet «Authentication» (hash e segreti si confrontano con una funzione sicura, non con l'uguaglianza normale); i due nomi di funzione sono esempi nostri, dalle librerie standard di Python e di Node.js; l'esclusione dei test e della ricerca nel database è una scelta nostra

R-SECURITY-09 [blocca] Se il diff costruisce da sé un cookie di sessione (l'intestazione `Set-Cookie`, una chiamata come `res.cookie` o `cookies().set` con opzioni proprie), il codice dichiara accesi `HttpOnly` e `Secure` e dichiara `SameSite`; un `Secure` legato all'ambiente (vero in produzione) vale come dichiarato. Se il cookie lo scrive una libreria di sessioni o di login, il diff non ne indebolisce le opzioni (`httpOnly: false`, `secure: false`). In tutti e due i casi `SameSite=None` è ammesso solo insieme a `Secure` e con il motivo scritto accanto, che dice quale altro sito deve mandare il cookie. Il codice del diff non salva un token di sessione o d'accesso dove il JavaScript della pagina può leggerlo (come `localStorage`).
Si giudica su: diff
Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)», «Never Do» e «Broken Authentication»; idea di OWASP Cheat Sheet «Session Management» (i tre attributi si dichiarano, non si lasciano al browser); distinguere il cookie costruito dal codice da quello scritto da una libreria, accettare `Secure` legato all'ambiente e ammettere `SameSite=None` con il motivo sono una scelta nostra

R-SECURITY-10 [blocca] Nessun segreto scritto nel codice, in un file versionato o in un test: nei test solo valori finti evidenti (come `PROVA-123`). Nessun segreto, token, password o hash di password in una riga di log o in un messaggio d'errore. Nel corpo di una risposta nessuna password, nessun hash di password e nessun segreto del server, e mai un token di reset, nemmeno a chi lo chiede; il token consegnato al chiamante a cui appartiene (la risposta di un login, una chiave d'API mostrata al suo titolare quando la crea) non è questo caso.
Si giudica su: diff
Si sovrappone a: R-BACKEND-07, R-BACKEND-08, R-INFRA-05, R-INFRA-06, R-DATABASE-13. Qui vale per ogni file dell'area, anche fuori da un server o da una configurazione, e comprende i test e, nelle risposte, le password, gli hash delle password e i token di reset.
Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: i segreti si considerano in ogni lavoro); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Never Do», «Sensitive Data Exposure» e «Secrets Management»; i valori finti nei test e l'eccezione per il token consegnato al suo titolare sono una scelta nostra

R-SECURITY-11 Se il diff aggiunge o cambia la risposta di un login, di un reset o di un recupero della password, la risposta (messaggio e codice di stato) non fa capire quali account esistono: nel login è la stessa quando l'utente non esiste e quando la password è sbagliata; nel reset e nel recupero è la stessa quando l'utente esiste e quando non esiste.
Si giudica su: diff
Fonte: idea di OWASP Cheat Sheet «Authentication» (un solo messaggio generico per login, reset e recupero); lo stesso codice di stato è una scelta nostra, nella stessa direzione

R-SECURITY-12 [blocca] Nel codice nuovo o cambiato un valore che arriva da fuori (corpo, parametri, query, intestazioni, cookie, il contenuto di un token non ancora verificato) si valida al confine, con uno schema o con controlli espliciti di tipo e forma, prima di usarlo. Le query al database e i comandi del sistema si costruiscono con parametri, mai concatenando quel valore. La verifica fatta dalla funzione di una libreria (di un token, di un cookie firmato) vale come validazione di quel valore.
Si giudica su: diff
Si sovrappone a: R-BACKEND-03, R-BACKEND-06. Qui vale anche fuori da un endpoint: in un middleware, in un proxy, in una funzione di login.
Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: input non fidato); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Process: Threat Model First», «Always Do (No Exceptions)», «Injection (SQL, NoSQL, OS Command)» e «Schema Validation at Boundaries»; `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Input Handling»; «con uno schema o con controlli espliciti» e la verifica di una libreria che vale come validazione sono una scelta nostra

R-SECURITY-13 [blocca] Se il diff reindirizza il browser, o fa partire una richiesta dal server, verso un indirizzo che viene dal chiamante (un parametro come `next` o `returnTo`, un URL nel corpo), l'indirizzo passa prima da un controllo: è un percorso interno del sito (non un URL completo, e nemmeno la forma `//host`), oppure il suo host è in un elenco di destinazioni ammesse.
Si giudica su: diff
Fonte: `security-auditor` di agent-skills 0.6.9 (MIT), sezioni «Input Handling» (reindirizzamenti controllati su un elenco) e «Third-Party Integrations» (richieste del server verso un URL dell'utente); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Server-Side Request Forgery (SSRF)»; ammettere i percorsi interni, e dire cosa non lo è, sono una scelta nostra

R-SECURITY-14 [blocca] Se il diff aggiunge o cambia la configurazione di CORS e la risposta ammette le credenziali (`Access-Control-Allow-Credentials: true`, `credentials: true`), l'origine ammessa viene da un elenco di origini note: mai `*`, e mai l'origine della richiesta rimandata indietro senza confrontarla con l'elenco.
Si giudica su: diff
Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Security Misconfiguration» (CORS solo per origini note) e «Red Flags» (origini `*`); `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Infrastructure»; https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «CORS»: l'intestazione si imposta solo per un'origine dell'elenco); limitare la regola al caso con le credenziali, e nominare l'origine rimandata indietro, sono una scelta nostra

R-SECURITY-15 Se il diff aggiunge un endpoint di login, di reset o di recupero della password, il report dice dove si limitano i tentativi falliti (nel diff, in codice già presente o in un servizio davanti all'applicazione) e se il conto è per account; se un limite non c'è, lo dice.
Si giudica su: report
Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Rate Limiting» (un limite più stretto per le rotte di login; con più istanze il contatore è condiviso); `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization»; idea di OWASP Cheat Sheet «Authentication» (i tentativi falliti si contano e si limitano per account); che basti dirlo nel report è una scelta nostra

R-SECURITY-16 Se il diff cambia un file che non è un test né un documento, il report dice il raggio d'azione del cambio: quali rotte e funzioni chiamano il codice cambiato, quali permessi e quali dati tocca, e cosa succede se è sbagliato (chi entra dove non deve, chi resta fuori).
Si giudica su: report
Fonte: idea di Trail of Bits `differential-review` (il raggio d'azione di un cambio si dichiara, non si dà per scontato); catalogo 2.1 (riga `security`: revisione del diff per rischio e raggio d'azione); che lo scriva il report, e la condizione sul tipo di file, sono una scelta nostra

R-SECURITY-17 [blocca] Il task non usa credenziali vere e non agisce su un servizio in linea: nessun login, nessuna chiamata e nessuna scrittura verso un servizio di autenticazione, un database o un'API veri, nessuna chiave creata, ruotata o revocata. Il report non riporta comandi lanciati da lui che lo facciano e dice quale prova locale ha fatto (test con valori finti), o perché non l'ha fatta.
Si giudica su: report
Fonte: spec del nucleo, sezione 8.5 (gli effetti esterni sono negati finché l'utente non li approva); l'elenco delle azioni e la prova detta nel report sono una scelta nostra, come nelle altre aree

## Dove informarsi

Prima di scrivere si legge il codice del progetto che già controlla l'accesso (middleware, guardie, test dei casi negati) e se ne segue la forma. Per ogni libreria di sicurezza si apre la documentazione ufficiale della versione del progetto (R-SECURITY-02); se la pagina non c'è, il report lo dice e non si inventa un'opzione.

- La skill `security-and-hardening` (plugin `agent-skills`), se il plugin è installato: modello delle minacce, input, sessioni, segreti, limiti di tentativi.
- La skill `security-review`, se installata, per una revisione guidata delle vulnerabilità: si consulta e non si copia, perché il suo testo ha la licenza CC BY-SA 4.0.
- Next.js, il file `proxy.ts` (fino alla 15 `middleware.ts`): https://nextjs.org/docs/app/api-reference/file-conventions/proxy.
- Le librerie di token e di password, per la versione scritta nel file delle dipendenze: https://github.com/auth0/node-jsonwebtoken, https://github.com/panva/jose, https://pypi.org/project/PyJWT/, https://github.com/kelektiv/node.bcrypt.js, https://github.com/ranisalt/node-argon2, https://pypi.org/project/argon2-cffi/, https://passlib.readthedocs.io/en/stable/narr/hash-tutorial.html.
- Le pagine dell'OWASP Cheat Sheet Series, da leggere e non da copiare: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html, https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html, https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html, https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html.

## Fonti

Le regole sono scritte con parole nostre. Da `security-and-hardening` e da `security-auditor` di agent-skills 0.6.9 (Addy Osmani, licenza MIT) vengono i temi e i nomi delle sezioni, senza testo copiato. Dall'OWASP Cheat Sheet Series e dai plugin `insecure-defaults` e `differential-review` di Trail of Bits (https://github.com/trailofbits/skills), tutti con licenza CC BY-SA 4.0 e letti il 22/11/2026, vengono solo idee: nessuna frase, e la regola le cita come «idea di». La pagina di Next.js sul Proxy e le pagine ufficiali di jsonwebtoken e PyJWT (lette il 22/11/2026) riportano i fatti, non il testo. Le scelte dell'utente stanno nel progetto di C (docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md, sezione 11), nel progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md, sezioni 3.4 e 12) e nel catalogo (docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md, sezioni 2.1 e 2.3). Il divieto di agire su un servizio vero senza l'approvazione dell'utente viene dalla spec del nucleo (docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md, sezione 8.5). I nomi dei file e i marcatori con cui `init` riconosce il profilo (`templates/profiles/security.toml`) vengono dal catalogo e dalle pagine ufficiali delle librerie: un commento del frammento dice quale per ogni gruppo.
