# Regole del profilo security di tollgate

Questa pagina è per te: dice quali sono le regole per il codice che decide chi può entrare e cosa può fare (login, permessi, password, token, cookie di sessione, segreti), cosa cambia nei tuoi progetti e cosa hai deciso su trentuno punti dubbi. Le regole sono approvate e il profilo si può accendere.

Approvata dall'utente il 2026-11-23.

Il 2026-11-24, con il tuo OK, è stata precisata una frase del punto 3 (i file `.tsx` dentro `auth/`).

## Cosa sono

Sono diciassette regole in più rispetto a quelle di base. Tredici di queste bloccano il lavoro se non sono rispettate. Dicono, per esempio, di scrivere chi può arrivare al codice cambiato, di provare con un test che chi non ha il permesso viene respinto, di non salvare mai una password in chiaro e di non scrivere nessun segreto nel codice.

Qualche parola, la prima volta che serve:

- **Autenticazione**: capire chi è la persona che chiama. È il login.
- **Autorizzazione**: decidere se quella persona può fare ciò che chiede. Una persona può avere fatto il login e non avere il permesso di leggere i dati di un'altra.
- **Controllo d'accesso**: il pezzo di codice che fa una di queste due cose e, se la risposta è no, respinge la richiesta.
- **Password**: la parola segreta dell'utente. Non si salva mai com'è.
- **Hash**: il risultato di una funzione che trasforma una password in una sequenza da cui non si torna indietro. Si salva quello, non la password. Per le password serve una funzione lenta apposta, così chi ruba l'archivio non può provarle a milioni.
- **Token**: un biglietto che il server dà dopo il login e che il programma dell'utente mostra a ogni richiesta, al posto della password. Di solito è firmato e ha una scadenza.
- **Sessione**: il periodo in cui l'utente resta riconosciuto dopo il login.
- **Cookie di sessione**: il piccolo dato che il browser conserva e rimanda al server per dire «sono ancora io». Ha tre interruttori di protezione: `HttpOnly`, `Secure` e `SameSite`.
- **Segreto**: una chiave, un token o una password. Chi lo conosce può farsi passare per un altro.
- **Middleware**: codice che gira prima di ogni richiesta, spesso per controllare il login. In molti progetti sta in un file `middleware.ts`.
- **Proxy**: il nome nuovo del middleware di Next.js, dalla versione 16. Sta in un file `proxy.ts`.
- **CORS**: la regola con cui un server dice quali altri siti possono chiamarlo dal browser.
- **Profilo**: un gruppo di regole, di agenti e di file che tollgate usa per un tipo di lavoro (qui la sicurezza; gli altri sono `ai`, `infra`, `backend`, `frontend`, `database`).
- **Agente**: un aiutante di tollgate con un compito solo. Uno scrive il codice (l'implementatore), uno lo rivede (il revisore).
- **Specialista finale**: un revisore in più che guarda il lavoro intero alla fine, e solo per un tipo di codice. Quello della sicurezza è `final-security`.
- **Livello L2**: i lavori grandi. Chiedono una specifica (spec) e un piano che tu approvi prima di scrivere codice. Un lavoro L1 è medio, L0 è piccolo.
- **Marcatore**: una riga di codice che `init` cerca nei file per riconoscere un tipo di lavoro (qui, la riga che importa una libreria di password o di token).
- **Percorso esatto**: il nome completo di un solo file, scritto nel `tollgate.toml`. Vince su ogni cartella.
- **`tollgate.toml`**: il file di impostazioni di tollgate nella radice del progetto.
- **`dod`**: la lista dei controlli che devono essere verdi a fine lavoro.
- **Attivo**: un profilo è attivo in un lavoro quando il lavoro tocca un suo file, anche se quel file lo scrive l'agente di un altro profilo. Vuol dire quattro cose: il lavoro prende il livello del profilo, le sue regole si possono citare in revisione, girano i suoi comandi di gate e di `dod` (per `security` oggi sono vuoti), e a fine lavoro parte il suo specialista, se ne ha uno. Non vuol dire che qualcuno abbia quelle regole davanti mentre scrive o rivede il task (vedi «Cosa cambia nei tuoi progetti»).
- **Frammento**: il file del plugin che descrive un profilo: quali file lo accendono e quali agenti usa.
- **Monorepo**: un solo repo con dentro più progetti.
- **Server Function**: in Next.js, una funzione del server che la pagina chiama direttamente, senza passare da un indirizzo.
- **Policy**: nel database, la regola che dice chi può leggere o cambiare le righe di una tabella.

Le regole valgono per chi scrive il codice e per chi lo rivede. Chi rivede guarda due cose. Il «diff» è l'elenco delle righe cambiate. Il «report» è il resoconto che l'agente scrive alla fine. Per ogni regola chi rivede risponde sì o no. La colonna «Si giudica su» dice su quale delle due guarda.

## Quando si accende

Il profilo non si accende da solo. Si accende solo in un progetto dove il comando `/tollgate:init` lo propone e tu copi il blocco proposto nel `tollgate.toml` del progetto. `init` lo propone solo dopo che le regole sono approvate. Un progetto nuovo riceve la proposta con `/tollgate:init --propose`; uno che ha già tollgate con `/tollgate:init --update`.

`init` lo propone in tre casi.

1. Se nel progetto c'è una cartella che si chiama `auth/`, `security/` o `rls/`, a qualunque profondità.
2. Se c'è un file che si chiama `middleware` con qualunque estensione (`middleware.ts`, `middleware.py`), oppure `proxy.ts` o `proxy.js`.
3. Se un file di codice contiene la riga che importa una libreria di hash delle password o di token: `bcrypt`, `bcryptjs`, `argon2`, `jsonwebtoken`, `jose`, `iron-session` per JavaScript; `bcrypt`, `argon2`, `passlib`, `jwt`, `jose` per Python. Il file entra con il suo percorso esatto.

Cosa non lo accende, e perché:

- I file con «session» nel nome. Lo hai scelto tu il 22 novembre: nei progetti quei nomi sono quasi sempre sessioni di chat, non login.
- Le librerie di login complete (NextAuth, better-auth, Lucia, Clerk) e i programmi che parlano con un servizio (Supabase, Firebase). Anche questa è una tua scelta: si cercano solo le librerie di password e di token.
- Tutto ciò che sta nella cartella `supabase/` alla radice del progetto: resta al profilo `database`, come hai scelto per le edge function.
- I documenti da soli: una cartella `auth/` con dentro solo file `.md` non accende niente.

## Le regole

| N. | In parole semplici | Blocca? | Si giudica su | Da dove viene |
|---|---|---|---|---|
| 1 (R-SECURITY-01) | Se il lavoro cambia un file che non è un test né un documento, il report dice chi può arrivare al codice cambiato (chiunque, un utente con il login, un amministratore, un altro servizio), cosa può fare da lì e quale controllo lo ferma. Se da fuori non ci arriva nessuno, lo dice. | sì | il report | Una tua scelta del 22 novembre (progetto di C, sezione 11) e la skill `security-and-hardening` (MIT). Che lo scriva il report è una scelta nostra. |
| 2 (R-SECURITY-02) | La prima volta che un file usa una libreria di password, di token, di sessioni o di login, il report ha l'indirizzo della documentazione ufficiale per la versione che il progetto usa. Se il progetto non dichiara la versione, il report lo dice e dà l'indirizzo della documentazione corrente. | no | il report | Il progetto di B (sezione 3.4) e la pagina ufficiale di una libreria di token. Applicarlo alla sicurezza è una scelta nostra. |
| 3 (R-SECURITY-03) | Se il lavoro aggiunge o cambia un controllo d'accesso, c'è un test che prova il caso in cui l'accesso va rifiutato: una richiesta senza login valido e, dove il dato ha un proprietario, quella di un altro utente. | sì | il diff | Una tua scelta del 22 novembre, il catalogo dei profili (sezione 2.3), un'idea delle guide OWASP e la skill `security-and-hardening` (MIT). |
| 4 (R-SECURITY-04) | Una funzione del server che legge o cambia i dati di un utente controlla sul server chi la chiama, mai solo nel browser, e dove il dato ha un proprietario controlla che sia lui. Con Next.js il file `proxy.ts` da solo non basta per una Server Function. Non vale per il login stesso, la registrazione, la richiesta di reset e la callback di un login (la pagina a cui un servizio di login esterno rimanda l'utente), né per i dati che chiunque può già leggere, se il codice lo dichiara. | sì | il diff | La skill `security-and-hardening` (MIT), un'idea delle guide OWASP e la pagina di Next.js sul Proxy. Le eccezioni sono una scelta nostra. |
| 5 (R-SECURITY-05) | Se manca un segreto o un'impostazione di sicurezza, il codice si ferma o respinge: non prosegue con un valore di riserva scritto nel codice. Per un elenco di siti o di ruoli ammessi, o per un interruttore che spegne un controllo, l'unica riserva accettata è quella che non fa passare nessuno. Un controllo che non riconosce il caso respinge. Nei test è ammesso un valore finto evidente. | sì | il diff | Una tua scelta del 22 novembre, un'idea di Trail of Bits, un'idea delle guide OWASP e la skill `security-and-hardening` (MIT). |
| 6 (R-SECURITY-06) | Una password si salva solo come hash fatto da una funzione lenta nata per le password, con un sale (un pezzo casuale diverso per ogni password), usando una libreria. Mai in chiaro, mai con un hash veloce. Non vale se il codice passa la password a un servizio di login senza salvarla. | sì | il diff | La skill `security-and-hardening` e l'agente `security-auditor` (MIT), e un'idea delle guide OWASP. |
| 7 (R-SECURITY-07) | Quando il codice controlla un token firmato, non spegne il controllo della firma né quello della scadenza, e con le due librerie più comuni dice quali tipi di firma accetta. Ogni token che il codice crea ha una scadenza. | sì | il diff | Le pagine ufficiali di jsonwebtoken e di PyJWT, la skill `security-and-hardening` e l'agente `security-auditor` (MIT). La scadenza per ogni token è una scelta nostra. |
| 8 (R-SECURITY-08) | Quando il codice confronta un segreto, un token o una firma con un valore arrivato da fuori, usa una funzione di confronto che impiega sempre lo stesso tempo, non il normale «uguale». Così chi attacca non indovina il valore misurando i tempi di risposta. Non vale nei test. | sì | il diff | Un'idea delle guide OWASP. I due nomi di funzione che la regola dà come esempio sono nostri. |
| 9 (R-SECURITY-09) | Se il codice costruisce da sé il cookie di sessione, accende i tre interruttori di protezione. Due eccezioni: `Secure` può dipendere dall'ambiente (acceso in produzione), e il valore più aperto di `SameSite`, `None`, è ammesso solo con `Secure` e con il motivo scritto accanto. Se il cookie lo scrive una libreria, il codice non li spegne. Il codice non salva un token dove gli script della pagina possono leggerlo. | sì | il diff | La skill `security-and-hardening` (MIT) e un'idea delle guide OWASP. La differenza fra i due casi è una scelta nostra. |
| 10 (R-SECURITY-10) | Nessun segreto scritto nel codice, in un file versionato o in un test (nei test solo valori finti evidenti). Nessun segreto, token o password nei log e nei messaggi d'errore. In una risposta mai una password, un hash di password, un segreto del server o un token di reset; il token dato al suo titolare dopo il login va bene. | sì | il diff | Una tua scelta del 22 novembre e la skill `security-and-hardening` (MIT). Ripete regole già approvate: vedi «Regole che si sovrappongono». |
| 11 (R-SECURITY-11) | Le risposte di login, reset e recupero della password non fanno capire quali account esistono: stesso messaggio e stesso codice sia che l'utente esista sia che no. | no | il diff | Un'idea delle guide OWASP. Lo stesso codice di stato è una scelta nostra. |
| 12 (R-SECURITY-12) | Ogni valore che arriva da fuori si controlla prima di usarlo. Le domande al database e i comandi del sistema si costruiscono con parametri, mai incollando quel valore nel testo. | sì | il diff | Una tua scelta del 22 novembre, la skill `security-and-hardening` e l'agente `security-auditor` (MIT). Ripete regole già approvate: vedi «Regole che si sovrappongono». |
| 13 (R-SECURITY-13) | Se il codice manda il browser, o fa partire una richiesta dal server, verso un indirizzo scelto da chi chiama, prima controlla che sia una pagina interna del sito o un sito di un elenco di destinazioni ammesse. | sì | il diff | L'agente `security-auditor` e la skill `security-and-hardening` (MIT). Ammettere le pagine interne è una scelta nostra. |
| 14 (R-SECURITY-14) | Se il server accetta chiamate da altri siti insieme ai dati di login dell'utente, i siti ammessi vengono da un elenco: mai «tutti», e mai il sito di chi chiama accettato senza guardare l'elenco. | sì | il diff | La skill `security-and-hardening` e l'agente `security-auditor` (MIT), e la pagina di Next.js sul Proxy. |
| 15 (R-SECURITY-15) | Se il lavoro aggiunge un punto di login, di reset o di recupero, il report dice dove si limita il numero di tentativi sbagliati, e se il conto è per account. Se un limite non c'è, lo dice. | no | il report | La skill `security-and-hardening` e l'agente `security-auditor` (MIT), e un'idea delle guide OWASP. Che basti dirlo nel report è una scelta nostra. |
| 16 (R-SECURITY-16) | Se il lavoro cambia un file che non è un test né un documento, il report dice fin dove arriva il cambio: chi usa il codice cambiato, quali permessi e dati tocca, cosa succede se è sbagliato. | no | il report | Un'idea di Trail of Bits e il catalogo dei profili (sezione 2.1). Che lo scriva il report è una scelta nostra. |
| 17 (R-SECURITY-17) | Il lavoro non usa credenziali vere e non tocca un servizio in linea: nessun login, nessuna chiamata, nessuna chiave creata o cambiata su un servizio vero. Il report dice quale prova locale ha fatto, o perché non l'ha fatta. | sì | il report | La spec del nucleo (sezione 8.5), come nelle altre aree. |

La colonna «Blocca?» dice quali regole sono le più serie. Se una di queste non è rispettata, chi rivede ferma il task. Le altre quattro (2, 11, 15 e 16) sono segnalate ma non lo fermano. Un difetto viene segnalato una sola volta.

Le fonti sono state controllate una per una da un agente che può solo leggere. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/security-fonti.md`. Tre tipi di fonte. Le skill con licenza MIT, da cui abbiamo preso i temi scrivendo le regole con parole nostre. Le pagine ufficiali di Next.js e delle librerie, da cui abbiamo preso i fatti. Le guide OWASP e due strumenti di Trail of Bits, che hanno una licenza più stretta: da lì abbiamo preso solo l'idea, mai una frase.

## Cosa cambia nei tuoi progetti

**Il lavoro sale a L2.** Il profilo ha `min_level = "L2"`: un cambio al login o ai permessi è delicato, e il catalogo lo voleva così. Un lavoro avviato in L1 che tocca un file del profilo sale a L2 al primo ricalcolo e torna a chiedere spec e piano approvati. Attenzione a cosa è nuovo. Sotto una cartella `auth/` il lavoro è L2 già oggi, anche senza questo profilo: `auth/` è, insieme a `migrations/`, tra i percorsi che tollgate tratta come delicati fin dall'inizio (salvo che tu abbia cambiato quell'impostazione in un progetto). Lì il profilo non cambia il livello: cambia chi scrive e chi rivede, e aggiunge lo specialista finale. Il livello L2 è nuovo per le cartelle `security/` e `rls/`, per i file `middleware` e `proxy` e per i file riconosciuti dal contenuto, quando non stanno sotto `auth/`: per questi anche un cambio piccolo porta tutto il lavoro in L2, ed è il costo. Consiglio: un lavoro che tocca il login avvialo direttamente in L2. Il profilo resta attivo anche quando il file va all'agente di un altro profilo, e il lavoro sale a L2 lo stesso.

**Il gate della PR lo controlla.** Il gate è il controllo prima di aprire la pull request. Ferma un lavoro dichiarato sotto L2 che tocca file del profilo, con l'esito `level_below_minimum`.

**Revisione finale.** Lo specialista finale lavora nei lavori L2: con il profilo attivo la revisione finale ha un revisore in più, `final-security`. Guarda solo il diff, per rischio e per quanto lontano arriva il cambio, con questa lista di controllo: chi arriva al codice cambiato e cosa può fare, accesso negato provato da un test, nessun segreto nel diff, valori predefiniti che rifiutano. Parte con `/tollgate:finish`. Costo: un agente in più a ogni revisione finale di un lavoro che tocca la sicurezza. I tre agenti del profilo (`implementer-security`, `reviewer-security` e questo) arrivano dopo la tua approvazione.

**Chi scrive e chi rivede.** Lo hai scelto il 22 novembre e vale per tutti gli agenti di tollgate, non solo per questi: chi cerca i difetti usa Fable, il modello più capace, e chi scrive o corregge il codice usa opus. Nessuno usa più sonnet. Costo: più consumo dell'abbonamento a ogni lavoro, nessuna spesa in denaro.

**Sicurezza fin dal progetto, in ogni lavoro.** Anche questa è una tua scelta del 22 novembre e vale anche dove il profilo non è acceso. Chi controlla la spec e il piano cerca ciò che il documento non dice su chi accede, sui dati, sui segreti e sugli input ostili. Ogni implementatore chiude il report con una riga `Sicurezza:` che dice cosa ha considerato, e chi rivede la confronta con il diff. Il profilo `security` aggiunge a questo le diciassette regole, il livello L2 e lo specialista.

**La cartella `supabase/`.** Tutto ciò che sta in `supabase/` alla radice del progetto resta al profilo `database`, anche una funzione di login e le regole di accesso alle righe. È la tua scelta del progetto di B. Una funzione di login lì dentro segue le regole di `database` sui segreti, non queste (punto 20 di «Cosa hai deciso»).

**Un file riconosciuto anche da un altro profilo.** Di norma un file che un profilo riconosce dalle sue librerie è solo suo. Per `security` hai scelto diversamente: se quel file sta in una cartella `auth/`, `security` si accende lo stesso. Nel frammento è la chiave `keep_paths`. Il file può restare agli agenti dell'altro profilo: in quel caso `security` è attivo, con gli effetti e i limiti scritti qui sotto.

**Quando un file va agli agenti di un'altra area.** Ogni task ha un solo agente che scrive e uno solo che rivede, quelli dell'area che vince, e ognuno ha caricate solo le regole della sua area. Se un file di login resta agli agenti di `backend` con `security` attivo, succede questo: il lavoro è L2; chi rivede il task può citare una regola di sicurezza (tollgate la accetta), ma non le ha davanti, e nemmeno chi scrive; a fine lavoro lo specialista `final-security` controlla le regole di sicurezza che si giudicano sul diff. Le regole che si giudicano sul report (1, 2, 15, 16 e 17) per quel task non le ha davanti nessuno. Vale anche al contrario: se un file di un'altra area va agli agenti di sicurezza, le regole di quell'area non le ha caricate né chi scrive né chi rivede il task. Per `database` le guarda a fine lavoro il suo specialista, `final-database`, e solo quelle sul diff; `frontend`, `backend`, `infra` e `ai` non hanno uno specialista finale.

**`dod` e comandi restano vuoti.** Il catalogo proponeva come controllo di fine lavoro i test dei casi di accesso negato. Il comando che li lancia cambia da progetto a progetto, e un comando scritto da `init` fallirebbe dove il programma manca. Per questo il controllo è diventato la regola 3, che vale ovunque, e il `dod` parte vuoto. Se vuoi un controllo automatico in più lo scrivi tu nel `tollgate.toml`, per esempio così:

```
[profiles.security]
commands = { denied = "python3 -m unittest discover -s tests -k denied" }
dod = ["denied"]
```

Attenzione: i comandi di `dod` li lancia tollgate stesso a fine lavoro, senza chiedere e senza nessun controllo sugli effetti. Un comando lì dentro non deve usare credenziali vere né parlare con un servizio in linea.

## Regole che si sovrappongono

Due regole di `security` ripetono regole che hai già approvato per altre aree. Il motivo: quando un file va agli agenti di sicurezza (per esempio un file di login dentro `server/auth/`), chi scrive e chi rivede il task hanno caricate solo queste regole, non quelle di `backend`. Senza la ripetizione quel file non avrebbe davanti nessuna regola sui segreti. Se in un lavoro sono attive due aree, il difetto si segnala una volta sola, con la regola dell'area del file.

| Regola di security | Regola approvata | Cosa cambia |
|---|---|---|
| R-SECURITY-10 | R-BACKEND-07 | Quella di `backend` vieta i segreti nel codice dei server e nella configurazione di Wrangler. Questa vale per ogni file dell'area e anche per i test. |
| R-SECURITY-10 | R-BACKEND-08 | Quella di `backend` vieta segreti, token e password nei log e nelle risposte d'errore. Questa aggiunge le risposte riuscite: mai una password, un hash di password o un token di reset. |
| R-SECURITY-10 | R-INFRA-05 | Quella di `infra` riguarda i file di configurazione dei servizi e di Docker. Questa riguarda il codice. |
| R-SECURITY-10 | R-INFRA-06 | Quella di `infra` riguarda i file dei segreti locali (`.env`) e il `.gitignore`. Questa ripete solo che un file così non entra nel repo. |
| R-SECURITY-10 | R-DATABASE-13 | Quella di `database` riguarda le chiavi di Supabase e la password del database. Questa riguarda ogni segreto. |
| R-SECURITY-12 | R-BACKEND-03 | Quella di `backend` chiede di controllare i dati in ingresso di un endpoint. Questa vale anche fuori da un endpoint: in un middleware, in un proxy, in una funzione di login. |
| R-SECURITY-12 | R-BACKEND-06 | Stessa richiesta: domande al database e comandi con parametri. Qui vale per ogni file dell'area. |

La regola 17 tratta lo stesso tema di tre regole approvate (nessuna azione su un servizio vero), ma non le ripete: ognuna parla dei servizi della sua area. Per questo non è nella tabella (punto 23 di «Cosa hai deciso»).

## Cosa hai deciso

Su trentuno punti la fonte non diceva proprio quello che la regola chiede, o la scelta era tua, o la proposta aveva un costo che dovevi conoscere. Hai approvato la proposta in tutti e trentuno, il 23 novembre: resta quella scritta sotto, e i numeri delle regole non cambiano più. I codici come S4 sono i casi provati uno per uno sul codice di `init`.

1. **I moduli di login dell'interfaccia vanno agli agenti di sicurezza.** Un componente dentro una cartella `auth/` dell'interfaccia, per esempio `src/components/auth/LoginForm.tsx` con il suo foglio di stile, va a `security` e non a `frontend`: vince la cartella più lunga (casi S4, S39, S54; lo stesso sotto `web/auth/`, S30). Il livello non cambia: sotto `auth/` il lavoro è L2 già oggi. Costo: anche un ritocco grafico a un modulo di login lo scrive e lo rivede l'agente di sicurezza, e le regole di `frontend` per quel task non le ha caricate nessuno (`frontend` non ha uno specialista finale).
   Proposta: lasciare così, perché un modulo di login tratta password. Chi non lo vuole toglie quel percorso dal blocco prima di copiarlo: il file torna agli agenti di `frontend`, senza queste regole e senza lo specialista (se il lavoro non tocca altri file del profilo), ma il lavoro resta L2 perché sta sotto `auth/`.
   Hai approvato la proposta.

2. **Ogni schermata dentro una cartella `auth/`.** Un file `.tsx` dentro una cartella `auth/` che non sta sotto `components/`, per esempio `src/auth/Login.tsx`, va a `security`; `frontend` resta attivo, ma le sue regole per quel task non le ha caricate nessuno. Costo: come il punto 1, per ogni schermata che sta in una cartella con quel nome; il livello era già L2.
   Proposta: lasciare così.
   Hai approvato la proposta.

3. **Le rotte di login che `backend` riconosce restano a `backend`.** Una rotta come `app/api/auth/.../route.ts` che importa una libreria di server è riconosciuta da `backend` con il suo percorso esatto, e un percorso esatto vince sulla cartella (S49, S50). Lo stesso per un file `.ts` riconosciuto da `frontend` (S58) o per un file riconosciuto da `database` (S65). Fa eccezione un file `.tsx` (o `.jsx`, `.vue`, `.svelte`) dentro `auth/`: anche quando `frontend` lo riconosce dalle sue librerie va agli agenti di sicurezza, come al punto 2, perché `frontend` quei file li prende già per l'estensione e non ne propone il percorso esatto. `security` resta attivo: il lavoro è L2 e a fine lavoro parte lo specialista. È quello che hai chiesto il 22 novembre. Costo: né chi scrive né chi rivede quella rotta ha caricate queste regole; chi rivede può citarle, ma non le ha davanti. Le controlla solo lo specialista finale, a fine lavoro, e solo quelle che si giudicano sul diff: le cinque sul report (1, 2, 15, 16 e 17; la 1 e la 17 bloccano) per quel task non le guarda nessuno.
   Proposta: lasciare così.
   Hai approvato la proposta.

4. **Un file e il suo test possono finire a due gruppi diversi.** Se `src/auth/login.ts` va a `backend` (punto 3) e il suo test `src/auth/login.test.ts` va a `security`, un task che li tocca insieme va agli agenti generici, e tollgate lo segna come task da dividere. Costo: né chi scrive né chi rivede quel task ha caricate le regole di `backend` o queste. Le regole di sicurezza sul diff le guarda lo specialista a fine lavoro; quelle di `backend` nessuno.
   Proposta: lasciare così; se capita spesso in un progetto, togli dal blocco uno dei due percorsi.
   Hai approvato la proposta.

5. **Un file di login dentro una cartella del server.** In parole semplici: un file di login dentro una cartella del server va agli agenti di sicurezza; fuori da una cartella del server resta a quelli del server. Esempio: `server/auth/login.ts` va a `security` (S53), mentre la rotta del punto 3 resta a `backend`. Succede lo stesso a un componente in `src/components/auth/` (S54) e a un middleware dentro `server/` (S61). Il motivo: quando l'altro profilo propone tutta la cartella, vince il percorso più lungo di `security`; quando propone il file esatto, vince lui. La tua frase del 22 novembre diceva che il file «resta a quel profilo per l'implementatore»: in questi tre casi non è così. Costo: perché anche questi restassero a `backend` o a `frontend` sarebbe servita una regola nuova nel codice di `init`, cioè un altro giro di lavoro prima dell'approvazione.
   Proposta: lasciare così: un file di login lo scrive chi ha caricate le regole di sicurezza.
   Hai approvato la proposta.

6. **Middleware e proxy riconosciuti anche da un altro profilo.** Tu hai scelto `keep_paths` per le cartelle `auth/`; averla estesa ai file `middleware` e `proxy` è una scelta nostra, perché il caso più comune è proprio un middleware che importa una libreria di server. Effetto: se due profili propongono lo stesso file esatto, vince il primo in ordine alfabetico, quindi un `src/middleware.ts` va a `backend` (S62) o ad `ai` (S63) e un `proxy.ts` a `backend` (S64), con `security` attivo e i limiti del punto 3. Se l'altro profilo propone solo la cartella, il file va a `security` (S61). La stessa parità vale per un file riconosciuto dalle librerie di password e insieme da un altro profilo (S29, S55). Costo: qualche riga in più nel blocco proposto; il middleware più comune lo scrive l'agente di `backend`.
   Proposta: tenere l'estensione; senza, in questi casi `security` non si accenderebbe affatto.
   Hai approvato la proposta.

7. **Cartelle di altri profili dentro `auth/`.** Una cartella `routes/` o `handlers/` dentro `auth/` va a `backend` (S51, S52) e una cartella `components/` dentro `auth/` va a `frontend` (S16), perché sono più profonde. Lo stesso per una cartella di `ai` (S14), per un `Dockerfile` (S20) e per un file che `ai` riconosce (S42). `security` resta attivo. Costo: quel codice di login lo scrive e lo rivede l'agente di un altro profilo, con i limiti del punto 3.
   Proposta: lasciare così.
   Hai approvato la proposta.

8. **Middleware e proxy che non c'entrano con la sicurezza.** Il nome basta: un `server/middleware.ts` che scrive solo dei log (S9), un `src/utils/proxy.ts` che non è di Next.js (S46), un `infra/middleware.ts` (S57), un test o un file di configurazione che si chiama `middleware` (S59), un file di tipi (S66). Costo: quei lavori salgono a L2 e seguono queste regole senza motivo.
   Proposta: lasciare così, perché nella maggior parte dei progetti quel nome è davvero il controllo del login; chi ha un caso toglie il percorso dal blocco.
   Hai approvato la proposta.

9. **`**/proxy.ts` e `**/proxy.js` aggiunti all'elenco.** Il catalogo non li aveva. Li abbiamo aggiunti perché dalla versione 16 Next.js chiama così il vecchio middleware. Costo: si accende ogni file con quel nome, a qualunque profondità (punto 8).
   Proposta: tenerli.
   Hai approvato la proposta.

10. **File che non sono codice di login dentro `auth/` o `security/`.** La cartella porta con sé tutto: codice di terzi copiato nel repo (`vendor/lib/auth/`), immagini (`public/auth/`), testi tradotti (`i18n/auth/`). E il nome `middleware` prende anche un file come `middleware.yaml`. Costo: sotto `auth/` il livello non cambia (era già L2), ma quei file vanno agli agenti di sicurezza e fanno partire lo specialista. Per un file come `middleware.yaml`, e per una cartella `security/`, è nuovo anche il livello L2.
    Proposta: lasciare così. Il rimedio è gratuito: togli quel percorso dal blocco proposto prima di copiarlo nel `tollgate.toml`. Sotto `auth/` toglie gli agenti di sicurezza e lo specialista (se il lavoro non tocca altri file del profilo), non il livello L2; per `middleware.yaml` e per `security/` toglie anche quello.
    Hai approvato la proposta.

11. **Forme che restano fuori.** Non accendono il profilo: le cartelle `middleware/` e `middlewares/`; le cartelle con la maiuscola come `Auth/`; i gruppi di rotte di Next.js scritti `(auth)` (S6); `proxy.page.ts`; `_middleware.ts` di Cloudflare (S60); un file `auth.ts` di configurazione fuori da una cartella `auth/`; i file con «session» nel nome (tua scelta, S32); le librerie standard `crypto`, `hashlib` e `hmac`, per cui un file che firma token solo con quelle non è riconosciuto dal contenuto. Costo: quel codice resta al profilo della sua cartella o all'agente generico, senza queste regole e senza L2.
    Proposta: lasciarle fuori per ora; chi ne ha le aggiunge a mano al blocco, e si riprendono alla prossima revisione delle regole.
    Hai approvato la proposta.

12. **Regole di accesso e schemi del database dentro `rls/` o `auth/`.** Un file come `db/rls/policies.sql` va a `security`, con `database` attivo (S13); uno schema in `prisma/auth/` pure (S34). Le regole di `database` sulle policy non le ha caricate né chi scrive né chi rivede il task: le guarda a fine lavoro lo specialista `final-database`, e solo quelle sul diff. In più «rls» può essere la sigla di altro, in codice che non c'entra. Costo: una policy fuori da `supabase/` la scrive e la rivede l'agente di sicurezza; per la cartella `rls/` è nuovo anche il livello L2, se nel progetto non è già acceso il profilo `database` (che porta in L2 ogni file `.sql`).
    Proposta: lasciare così; chi tiene le policy in una cartella `rls/` può togliere quel percorso dal blocco.
    Hai approvato la proposta.

13. **Configurazione, istruzioni per i modelli e automazioni dentro `auth/` o `security/`.** Un file di configurazione in `infra/auth/` (S19), un prompt in `src/prompts/auth/` (S40) e un file in `.github/security/` (S44) vanno a `security`. Costo: non sono codice di login, ma li scrive e li rivede l'agente di sicurezza, senza le regole di `infra` o di `ai` caricate. Sotto `auth/` il livello era già L2; sotto `security/` è nuovo.
    Proposta: lasciare così, sono comunque file che parlano di accessi.
    Hai approvato la proposta.

14. **`auth/` e `security/` dentro le cartelle degli altri profili.** Una migrazione in `db/migrations/auth/` va a `security`, con `database` attivo (S68). La configurazione in `infra/security/` va a `security` (S69). Un pacchetto di un monorepo che si chiama `auth` va tutto a `security`, compreso il suo file delle dipendenze (S70). Un middleware dentro la cartella di `ai` va a `security` (S71). Costo: file di database, di infrastruttura e di `ai` scritti e rivisti dall'agente di sicurezza, senza le regole della loro area caricate. Per la migrazione le regole di `database` le guarda a fine lavoro il suo specialista, solo sul diff; per `infra` e `ai` nessuno. Il livello L2 è nuovo solo per `infra/security/` e per il middleware: la migrazione e il pacchetto `auth` erano già L2.
    Proposta: lasciare così.
    Hai approvato la proposta.

15. **Test e documenti.** Un lavoro sui soli test di una cartella `tests/auth/` è L2 (S22): lo era già, perché sta sotto `auth/`; con il profilo quei test vanno agli agenti di sicurezza. I documenti da soli non accendono niente (S23, S38), ma se nella cartella c'è anche un file di codice entrano con lei (S24). Costo: nessun livello in più sotto `auth/`; sotto `security/` un lavoro piccolo su test o documenti sale a L2.
    Proposta: lasciare così.
    Hai approvato la proposta.

16. **Il marcatore `import jwt`.** È testo fisso e non guarda il linguaggio. Riconosce la libreria Python, ma si accende anche su `import jwt_utils`, su una riga di commento e sugli import di JavaScript che cominciano così, compreso quello di `jwt-decode`, una libreria del browser che legge un token senza verificarlo. Costo: qualche file dell'interfaccia in L2.
    Proposta: tenerlo; un file che legge un token merita comunque queste regole.
    Hai approvato la proposta.

17. **Il marcatore `jose`.** La libreria gira anche nel browser, quindi può accendere codice dell'interfaccia. Costo: come il punto 16.
    Proposta: tenerlo.
    Hai approvato la proposta.

18. **`iron-session`.** È una libreria di sessioni dentro un cookie cifrato, non di password né di token firmati: sta al confine con la tua scelta «niente session». L'abbiamo tenuta perché quel cookie è proprio il cookie di sessione delle regole. Si accende su ogni file che legge la sessione, non solo sul login. Costo: in un progetto che la usa, molti lavori salgono a L2.
    Proposta: tenerla; se in un progetto pesa, togli quei percorsi dal blocco.
    Hai approvato la proposta.

19. **Due marcatori tolti.** `require('bcryptjs')` e `from 'jsonwebtoken'` sono usciti dall'elenco prima della bozza, perché nessuna pagina ufficiale mostra quella riga e noi mettiamo solo righe che hanno una fonte. Costo: un file che usa jsonwebtoken con `import { sign } from …` non è riconosciuto dal contenuto; lo è solo se sta in una cartella o in un file del profilo.
    Proposta: lasciarli fuori. Se li vuoi, dimmelo: si rimettono, dichiarati come scelta tua.
    Hai approvato la proposta.

20. **La cartella `supabase/`.** Alla radice è tutta di `database`: una funzione di login in `supabase/functions/auth/` segue le regole di `database` (S11), e così una cartella `supabase/rls/` e un file lì dentro che importa una libreria di token. In un monorepo una `supabase/` annidata dentro un'altra cartella non è esclusa: lì la funzione di login va a `security` (S56). Costo: la stessa funzione ha regole diverse secondo dove sta la cartella. Se vuoi una funzione di login alla radice sotto `security`, aggiungi a mano al blocco un percorso più lungo, `supabase/functions/auth/**`; un generico `**/auth/**` non basta, perché a parità vince `database` (S67).
    Proposta: lasciare così, è la tua scelta del progetto di B.
    Hai approvato la proposta.

21. **R-SECURITY-10 ripete cinque regole approvate.** Sono le regole sui segreti di `backend`, `infra` e `database` (tabella sopra). Costo: in un lavoro con due aree attive ci sono due regole sullo stesso difetto; viene segnalato una volta sola.
    Proposta: tenerla; senza, un file di login che va a `security` non avrebbe nessuna regola sui segreti caricata.
    Hai approvato la proposta.

22. **R-SECURITY-12 ripete due regole approvate.** Sono le regole di `backend` sui dati in ingresso e sulle domande al database. Costo: come il punto 21.
    Proposta: tenerla, per lo stesso motivo.
    Hai approvato la proposta.

23. **La regola 17 somiglia a tre regole approvate.** Le aree `infra`, `database` e `backend` hanno ognuna una regola che vieta di agire su un servizio vero. R-SECURITY-17 dice lo stesso per i servizi di login, ma non è scritta come ripetizione e non è nella tabella. Costo: nessuno; è solo una riga in meno nella tabella.
    Proposta: lasciarla così. Se la vuoi tra le sovrapposizioni, è un cambio di una riga.
    Hai approvato la proposta.

24. **`dod` vuoto.** Il catalogo proponeva i test dei casi di accesso negato come controllo di fine lavoro. Sono diventati la regola 3, e il profilo parte senza controlli automatici. Costo: nessun controllo automatico in più finché non lo aggiungi (l'esempio sta in «Cosa cambia»).
    Proposta: lasciarlo vuoto, come negli altri profili.
    Hai approvato la proposta.

25. **R-SECURITY-08 blocca oppure no.** Il difetto (confrontare un segreto con il normale «uguale») si vede bene nel diff ed è l'errore tipico di chi controlla una firma. Però sfruttarlo davvero è difficile. Costo: se blocca, un task si ferma per un difetto reale ma raro da sfruttare; se non blocca, il difetto è solo segnalato e può restare.
    Proposta: farla bloccare, perché correggerlo costa una riga.
    Hai approvato la proposta.

26. **Gli esempi di R-SECURITY-08 sono nostri.** La regola nomina due funzioni, `hmac.compare_digest` per Python e `crypto.timingSafeEqual` per Node.js. Vengono dalle librerie standard dei due linguaggi, ma non abbiamo una copia della pagina ufficiale tra le fonti. Costo: due nomi sulla nostra parola; l'idea della regola ha la sua fonte.
    Proposta: tenerli, perché dicono a chi scrive cosa usare. In alternativa si tolgono senza toccare la regola.
    Hai approvato la proposta.

27. **R-SECURITY-01 e R-SECURITY-16 sono vicine.** Tutte e due chiedono una cosa al report: la prima chi arriva al codice e cosa lo ferma, la seconda fin dove arriva il cambio e cosa succede se è sbagliato. Costo: due risposte da scrivere e da controllare dove ne basterebbe forse una.
    Proposta: tenerle separate: sono due domande diverse e la prima blocca, la seconda no. Se le trovi doppie, si uniscono nella prima.
    Hai approvato la proposta.

28. **Le due forme di R-SECURITY-09.** La forma scritta chiede i tre interruttori del cookie solo quando il codice costruisce il cookie da sé; se lo scrive una libreria, chiede solo di non spegnerli. Costo: una libreria che parte con protezioni deboli, aggiunta senza opzioni, non fa scattare la regola. L'altra forma li chiederebbe sempre scritti nel codice: non lascia buchi, ma ferma anche codice corretto che si affida a una libreria con buone protezioni.
    Proposta: tenere la forma scritta, per non fermare codice corretto.
    Hai approvato la proposta.

29. **R-SECURITY-15 non blocca e si giudica sul report.** Il limite ai tentativi di login spesso sta fuori dal codice, in un servizio davanti all'applicazione, e nel diff non si vede. Per questo la regola chiede solo che il report dica dove sta. Costo: un login senza nessun limite viene segnalato, non fermato.
    Proposta: lasciarla così.
    Hai approvato la proposta.

30. **Quante bloccano.** Sono diciassette regole, di cui tredici bloccano. Le quattro che non bloccano sono la 2 (ha l'appoggio più debole nelle fonti), la 11, la 15 e la 16. Costo: più regole bloccano, più task si fermano per una correzione.
    Proposta: tenere questa divisione; puoi spostare ogni regola dicendomi il numero.
    Hai approvato la proposta.

31. **I temi «scelta nostra».** Ogni regola ha una parte che va oltre le fonti, scritta da noi perché si possa rispettare e giudicare: R-SECURITY-01 (lo scrive il report; vale per i file che non sono test né documenti), R-SECURITY-02 (applicarla alle librerie di sicurezza; il caso senza versione), R-SECURITY-03 (il test può essere già nel repo; i due casi da provare), R-SECURITY-04 (la guardia di rotta; i due casi in cui non vale), R-SECURITY-05 (gli esempi; l'elenco chiuso delle impostazioni; i valori finti nei test), R-SECURITY-06 (usare una libreria; il caso del servizio di login), R-SECURITY-07 (l'elenco dei tipi di firma obbligatorio; il divieto di spegnere il controllo della firma; la scadenza per ogni token), R-SECURITY-08 (i due esempi; fuori i test), R-SECURITY-09 (le due forme del punto 28; `Secure` legato all'ambiente; `SameSite=None` con il motivo scritto), R-SECURITY-10 (i valori finti nei test; il token dato al suo titolare), R-SECURITY-11 (lo stesso codice di stato), R-SECURITY-12 (cosa conta come controllo), R-SECURITY-13 (le pagine interne ammesse), R-SECURITY-14 (solo quando viaggiano i dati di login), R-SECURITY-15 (basta il report), R-SECURITY-16 (lo scrive il report), R-SECURITY-17 (l'elenco delle azioni vietate). È nostro anche il modo in cui chi rivede riconosce nel diff un controllo d'accesso, un token, una password e un cookie di sessione. Costo: qualche riga in più nel report e qualche eccezione da ricordare.
    Proposta: tenerle tutte.
    Hai approvato la proposta.

## Regole tolte dalla verifica

Nessuna regola è uscita: ciascuna ha almeno una fonte che regge, e i numeri restano. Una sola voce di fonte non reggeva. La regola 10 attribuiva alla tua scelta del 22 novembre più parole di quelle che hai detto; ora dice solo ciò che hai scelto, e il resto poggia sulla skill che lo dice davvero. Dopo la revisione dodici regole sono state riscritte per essere più precise, senza cambiare tema né numero. Nessuna cartella e nessun nome di file è uscito; i due marcatori del punto 19 sono usciti prima della bozza.
