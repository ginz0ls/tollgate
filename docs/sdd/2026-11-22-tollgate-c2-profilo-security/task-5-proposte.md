## Da decidere tu

Su trentuno punti la fonte non diceva proprio quello che la regola chiede, o la scelta è tua, o la proposta ha un costo che devi conoscere. Per ognuno trovi la proposta; se non dici altro, resta quella. I codici come S4 sono i casi provati uno per uno sul codice di `init`. Se hai poco tempo, guarda questi sette, dove la tua scelta cambia davvero qualcosa: il 5 e il 19 (quali file prende il profilo), il 25 e il 30 (quali regole fermano un task), il 28 (quanto è severa la regola sui cookie), il 21 e il 22 (le regole ripetute). Gli altri sono costi da conoscere, e la proposta è lasciare com'è.

1. **I moduli di login dell'interfaccia vanno agli agenti di sicurezza.** Un componente dentro una cartella `auth/` dell'interfaccia, per esempio `src/components/auth/LoginForm.tsx` con il suo foglio di stile, va a `security` e non a `frontend`: vince la cartella più lunga (casi S4, S39, S54; lo stesso sotto `web/auth/`, S30). Il livello non cambia: sotto `auth/` il lavoro è L2 già oggi. Costo: anche un ritocco grafico a un modulo di login lo scrive e lo rivede l'agente di sicurezza, e le regole di `frontend` per quel task non le ha caricate nessuno (`frontend` non ha uno specialista finale).
   Proposta: lasciare così, perché un modulo di login tratta password. Chi non lo vuole toglie quel percorso dal blocco prima di copiarlo: il file torna agli agenti di `frontend`, senza queste regole e senza lo specialista, ma il lavoro resta L2 perché sta sotto `auth/`.

2. **Ogni schermata dentro una cartella `auth/`.** Un file `.tsx` dentro una cartella `auth/` che non sta sotto `components/`, per esempio `src/auth/Login.tsx`, va a `security`; `frontend` resta attivo, ma le sue regole per quel task non le ha caricate nessuno. Costo: come il punto 1, per ogni schermata che sta in una cartella con quel nome; il livello era già L2.
   Proposta: lasciare così.

3. **Le rotte di login che `backend` riconosce restano a `backend`.** Una rotta come `app/api/auth/.../route.ts` che importa una libreria di server è riconosciuta da `backend` con il suo percorso esatto, e un percorso esatto vince sulla cartella (S49, S50). Lo stesso per un file riconosciuto da `frontend` (S58) o da `database` (S65). `security` resta attivo: il lavoro è L2 e a fine lavoro parte lo specialista. È quello che hai chiesto il 22 novembre. Costo: né chi scrive né chi rivede quella rotta ha caricate queste regole; chi rivede può citarle, ma non le ha davanti. Le controlla solo lo specialista finale, a fine lavoro, e solo quelle che si giudicano sul diff: le cinque sul report (1, 2, 15, 16 e 17; la 1 e la 17 bloccano) per quel task non le guarda nessuno.
   Proposta: lasciare così.

4. **Un file e il suo test possono finire a due gruppi diversi.** Se `src/auth/login.ts` va a `backend` (punto 3) e il suo test `src/auth/login.test.ts` va a `security`, un task che li tocca insieme va agli agenti generici, e tollgate lo segna come task da dividere. Costo: né chi scrive né chi rivede quel task ha caricate le regole di `backend` o queste. Le regole di sicurezza sul diff le guarda lo specialista a fine lavoro; quelle di `backend` nessuno.
   Proposta: lasciare così; se capita spesso in un progetto, togli dal blocco uno dei due percorsi.

5. **Un file di login dentro una cartella del server.** In parole semplici: un file di login dentro una cartella del server va agli agenti di sicurezza; fuori da una cartella del server resta a quelli del server. Esempio: `server/auth/login.ts` va a `security` (S53), mentre la rotta del punto 3 resta a `backend`. Succede lo stesso a un componente in `src/components/auth/` (S54) e a un middleware dentro `server/` (S61). Il motivo: quando l'altro profilo propone tutta la cartella, vince il percorso più lungo di `security`; quando propone il file esatto, vince lui. La tua frase del 22 novembre diceva che il file «resta a quel profilo per l'implementatore»: in questi tre casi non è così. Costo: se vuoi che anche questi restino a `backend` o a `frontend`, serve una regola nuova nel codice di `init`, cioè un altro giro di lavoro prima dell'approvazione.
   Proposta: lasciare così: un file di login lo scrive chi ha caricate le regole di sicurezza.

6. **Middleware e proxy riconosciuti anche da un altro profilo.** Tu hai scelto `keep_paths` per le cartelle `auth/`; averla estesa ai file `middleware` e `proxy` è una scelta nostra, perché il caso più comune è proprio un middleware che importa una libreria di server. Effetto: se due profili propongono lo stesso file esatto, vince il primo in ordine alfabetico, quindi un `src/middleware.ts` va a `backend` (S62) o ad `ai` (S63) e un `proxy.ts` a `backend` (S64), con `security` attivo e i limiti del punto 3. Se l'altro profilo propone solo la cartella, il file va a `security` (S61). La stessa parità vale per un file riconosciuto dalle librerie di password e insieme da un altro profilo (S29, S55). Costo: qualche riga in più nel blocco proposto; il middleware più comune lo scrive l'agente di `backend`.
   Proposta: tenere l'estensione; senza, in questi casi `security` non si accenderebbe affatto.

7. **Cartelle di altri profili dentro `auth/`.** Una cartella `routes/` o `handlers/` dentro `auth/` va a `backend` (S51, S52) e una cartella `components/` dentro `auth/` va a `frontend` (S16), perché sono più profonde. Lo stesso per una cartella di `ai` (S14), per un `Dockerfile` (S20) e per un file che `ai` riconosce (S42). `security` resta attivo. Costo: quel codice di login lo scrive e lo rivede l'agente di un altro profilo, con i limiti del punto 3.
   Proposta: lasciare così.

8. **Middleware e proxy che non c'entrano con la sicurezza.** Il nome basta: un `server/middleware.ts` che scrive solo dei log (S9), un `src/utils/proxy.ts` che non è di Next.js (S46), un `infra/middleware.ts` (S57), un test o un file di configurazione che si chiama `middleware` (S59), un file di tipi (S66). Costo: quei lavori salgono a L2 e seguono queste regole senza motivo.
   Proposta: lasciare così, perché nella maggior parte dei progetti quel nome è davvero il controllo del login; chi ha un caso toglie il percorso dal blocco.

9. **`**/proxy.ts` e `**/proxy.js` aggiunti all'elenco.** Il catalogo non li aveva. Li abbiamo aggiunti perché dalla versione 16 Next.js chiama così il vecchio middleware. Costo: si accende ogni file con quel nome, a qualunque profondità (punto 8).
   Proposta: tenerli.

10. **File che non sono codice di login dentro `auth/` o `security/`.** La cartella porta con sé tutto: codice di terzi copiato nel repo (`vendor/lib/auth/`), immagini (`public/auth/`), testi tradotti (`i18n/auth/`). E il nome `middleware` prende anche un file come `middleware.yaml`. Costo: sotto `auth/` il livello non cambia (era già L2), ma quei file vanno agli agenti di sicurezza e fanno partire lo specialista. Per un file come `middleware.yaml`, e per una cartella `security/`, è nuovo anche il livello L2.
    Proposta: lasciare così. Il rimedio è gratuito: togli quel percorso dal blocco proposto prima di copiarlo nel `tollgate.toml`. Sotto `auth/` toglie gli agenti di sicurezza e lo specialista, non il livello L2; per `middleware.yaml` e per `security/` toglie anche quello.

11. **Forme che restano fuori.** Non accendono il profilo: le cartelle `middleware/` e `middlewares/`; le cartelle con la maiuscola come `Auth/`; i gruppi di rotte di Next.js scritti `(auth)` (S6); `proxy.page.ts`; `_middleware.ts` di Cloudflare (S60); un file `auth.ts` di configurazione fuori da una cartella `auth/`; i file con «session» nel nome (tua scelta, S32); le librerie standard `crypto`, `hashlib` e `hmac`, per cui un file che firma token solo con quelle non è riconosciuto dal contenuto. Costo: quel codice resta al profilo della sua cartella o all'agente generico, senza queste regole e senza L2.
    Proposta: lasciarle fuori per ora; chi ne ha le aggiunge a mano al blocco, e si riprendono alla prossima revisione delle regole.

12. **Regole di accesso e schemi del database dentro `rls/` o `auth/`.** Un file come `db/rls/policies.sql` va a `security`, con `database` attivo (S13); uno schema in `prisma/auth/` pure (S34). Le regole di `database` sulle policy non le ha caricate né chi scrive né chi rivede il task: le guarda a fine lavoro lo specialista `final-database`, e solo quelle sul diff. In più «rls» può essere la sigla di altro, in codice che non c'entra. Costo: una policy fuori da `supabase/` la scrive e la rivede l'agente di sicurezza; per la cartella `rls/` è nuovo anche il livello L2, se nel progetto non è già acceso il profilo `database` (che porta in L2 ogni file `.sql`).
    Proposta: lasciare così; chi tiene le policy in una cartella `rls/` può togliere quel percorso dal blocco.

13. **Configurazione, istruzioni per i modelli e automazioni dentro `auth/` o `security/`.** Un file di configurazione in `infra/auth/` (S19), un prompt in `src/prompts/auth/` (S40) e un file in `.github/security/` (S44) vanno a `security`. Costo: non sono codice di login, ma li scrive e li rivede l'agente di sicurezza, senza le regole di `infra` o di `ai` caricate. Sotto `auth/` il livello era già L2; sotto `security/` è nuovo.
    Proposta: lasciare così, sono comunque file che parlano di accessi.

14. **`auth/` e `security/` dentro le cartelle degli altri profili.** Una migrazione in `db/migrations/auth/` va a `security`, con `database` attivo (S68). La configurazione in `infra/security/` va a `security` (S69). Un pacchetto di un monorepo che si chiama `auth` va tutto a `security`, compreso il suo file delle dipendenze (S70). Un middleware dentro la cartella di `ai` va a `security` (S71). Costo: file di database, di infrastruttura e di `ai` scritti e rivisti dall'agente di sicurezza, senza le regole della loro area caricate. Per la migrazione le regole di `database` le guarda a fine lavoro il suo specialista, solo sul diff; per `infra` e `ai` nessuno. Il livello L2 è nuovo solo per `infra/security/` e per il middleware: la migrazione e il pacchetto `auth` erano già L2.
    Proposta: lasciare così.

15. **Test e documenti.** Un lavoro sui soli test di una cartella `tests/auth/` è L2 (S22): lo era già, perché sta sotto `auth/`; con il profilo quei test vanno agli agenti di sicurezza. I documenti da soli non accendono niente (S23, S38), ma se nella cartella c'è anche un file di codice entrano con lei (S24). Costo: nessun livello in più sotto `auth/`; sotto `security/` un lavoro piccolo su test o documenti sale a L2.
    Proposta: lasciare così.

16. **Il marcatore `import jwt`.** È testo fisso e non guarda il linguaggio. Riconosce la libreria Python, ma si accende anche su `import jwt_utils`, su una riga di commento e sugli import di JavaScript che cominciano così, compreso quello di `jwt-decode`, una libreria del browser che legge un token senza verificarlo. Costo: qualche file dell'interfaccia in L2.
    Proposta: tenerlo; un file che legge un token merita comunque queste regole.

17. **Il marcatore `jose`.** La libreria gira anche nel browser, quindi può accendere codice dell'interfaccia. Costo: come il punto 16.
    Proposta: tenerlo.

18. **`iron-session`.** È una libreria di sessioni dentro un cookie cifrato, non di password né di token firmati: sta al confine con la tua scelta «niente session». L'abbiamo tenuta perché quel cookie è proprio il cookie di sessione delle regole. Si accende su ogni file che legge la sessione, non solo sul login. Costo: in un progetto che la usa, molti lavori salgono a L2.
    Proposta: tenerla; se in un progetto pesa, togli quei percorsi dal blocco.

19. **Due marcatori tolti.** `require('bcryptjs')` e `from 'jsonwebtoken'` sono usciti dall'elenco prima della bozza, perché nessuna pagina ufficiale mostra quella riga e noi mettiamo solo righe che hanno una fonte. Costo: un file che usa jsonwebtoken con `import { sign } from …` non è riconosciuto dal contenuto; lo è solo se sta in una cartella o in un file del profilo.
    Proposta: lasciarli fuori. Se li vuoi, dimmelo: si rimettono, dichiarati come scelta tua.

20. **La cartella `supabase/`.** Alla radice è tutta di `database`: una funzione di login in `supabase/functions/auth/` segue le regole di `database` (S11), e così una cartella `supabase/rls/` e un file lì dentro che importa una libreria di token. In un monorepo una `supabase/` annidata dentro un'altra cartella non è esclusa: lì la funzione di login va a `security` (S56). Costo: la stessa funzione ha regole diverse secondo dove sta la cartella. Se vuoi una funzione di login alla radice sotto `security`, aggiungi a mano al blocco un percorso più lungo, `supabase/functions/auth/**`; un generico `**/auth/**` non basta, perché a parità vince `database` (S67).
    Proposta: lasciare così, è la tua scelta del progetto di B.

21. **R-SECURITY-10 ripete cinque regole approvate.** Sono le regole sui segreti di `backend`, `infra` e `database` (tabella sopra). Costo: in un lavoro con due aree attive ci sono due regole sullo stesso difetto; viene segnalato una volta sola.
    Proposta: tenerla; senza, un file di login che va a `security` non avrebbe nessuna regola sui segreti caricata.

22. **R-SECURITY-12 ripete due regole approvate.** Sono le regole di `backend` sui dati in ingresso e sulle domande al database. Costo: come il punto 21.
    Proposta: tenerla, per lo stesso motivo.

23. **La regola 17 somiglia a tre regole approvate.** Le aree `infra`, `database` e `backend` hanno ognuna una regola che vieta di agire su un servizio vero. R-SECURITY-17 dice lo stesso per i servizi di login, ma non è scritta come ripetizione e non è nella tabella. Costo: nessuno; è solo una riga in meno nella tabella.
    Proposta: lasciarla così. Se la vuoi tra le sovrapposizioni, è un cambio di una riga.

24. **`dod` vuoto.** Il catalogo proponeva i test dei casi di accesso negato come controllo di fine lavoro. Sono diventati la regola 3, e il profilo parte senza controlli automatici. Costo: nessun controllo automatico in più finché non lo aggiungi (l'esempio sta in «Cosa cambia»).
    Proposta: lasciarlo vuoto, come negli altri profili.

25. **R-SECURITY-08 blocca oppure no.** Il difetto (confrontare un segreto con il normale «uguale») si vede bene nel diff ed è l'errore tipico di chi controlla una firma. Però sfruttarlo davvero è difficile. Costo: se blocca, un task si ferma per un difetto reale ma raro da sfruttare; se non blocca, il difetto è solo segnalato e può restare.
    Proposta: farla bloccare, perché correggerlo costa una riga.

26. **Gli esempi di R-SECURITY-08 sono nostri.** La regola nomina due funzioni, `hmac.compare_digest` per Python e `crypto.timingSafeEqual` per Node.js. Vengono dalle librerie standard dei due linguaggi, ma non abbiamo una copia della pagina ufficiale tra le fonti. Costo: due nomi sulla nostra parola; l'idea della regola ha la sua fonte.
    Proposta: tenerli, perché dicono a chi scrive cosa usare. In alternativa si tolgono senza toccare la regola.

27. **R-SECURITY-01 e R-SECURITY-16 sono vicine.** Tutte e due chiedono una cosa al report: la prima chi arriva al codice e cosa lo ferma, la seconda fin dove arriva il cambio e cosa succede se è sbagliato. Costo: due risposte da scrivere e da controllare dove ne basterebbe forse una.
    Proposta: tenerle separate: sono due domande diverse e la prima blocca, la seconda no. Se le trovi doppie, si uniscono nella prima.

28. **Le due forme di R-SECURITY-09.** La forma scritta chiede i tre interruttori del cookie solo quando il codice costruisce il cookie da sé; se lo scrive una libreria, chiede solo di non spegnerli. Costo: una libreria che parte con protezioni deboli, aggiunta senza opzioni, non fa scattare la regola. L'altra forma li chiederebbe sempre scritti nel codice: non lascia buchi, ma ferma anche codice corretto che si affida a una libreria con buone protezioni.
    Proposta: tenere la forma scritta, per non fermare codice corretto.

29. **R-SECURITY-15 non blocca e si giudica sul report.** Il limite ai tentativi di login spesso sta fuori dal codice, in un servizio davanti all'applicazione, e nel diff non si vede. Per questo la regola chiede solo che il report dica dove sta. Costo: un login senza nessun limite viene segnalato, non fermato.
    Proposta: lasciarla così.

30. **Quante bloccano.** Sono diciassette regole, di cui tredici bloccano. Le quattro che non bloccano sono la 2 (ha l'appoggio più debole nelle fonti), la 11, la 15 e la 16. Costo: più regole bloccano, più task si fermano per una correzione.
    Proposta: tenere questa divisione; puoi spostare ogni regola dicendomi il numero.

31. **I temi «scelta nostra».** Ogni regola ha una parte che va oltre le fonti, scritta da noi perché si possa rispettare e giudicare: R-SECURITY-01 (lo scrive il report; vale per i file che non sono test né documenti), R-SECURITY-02 (applicarla alle librerie di sicurezza; il caso senza versione), R-SECURITY-03 (il test può essere già nel repo; i due casi da provare), R-SECURITY-04 (la guardia di rotta; i due casi in cui non vale), R-SECURITY-05 (gli esempi; l'elenco chiuso delle impostazioni; i valori finti nei test), R-SECURITY-06 (usare una libreria; il caso del servizio di login), R-SECURITY-07 (l'elenco dei tipi di firma obbligatorio; il divieto di spegnere il controllo della firma; la scadenza per ogni token), R-SECURITY-08 (i due esempi; fuori i test), R-SECURITY-09 (le due forme del punto 28; `Secure` legato all'ambiente; `SameSite=None` con il motivo scritto), R-SECURITY-10 (i valori finti nei test; il token dato al suo titolare), R-SECURITY-11 (lo stesso codice di stato), R-SECURITY-12 (cosa conta come controllo), R-SECURITY-13 (le pagine interne ammesse), R-SECURITY-14 (solo quando viaggiano i dati di login), R-SECURITY-15 (basta il report), R-SECURITY-16 (lo scrive il report), R-SECURITY-17 (l'elenco delle azioni vietate). È nostro anche il modo in cui chi rivede riconosce nel diff un controllo d'accesso, un token, una password e un cookie di sessione. Costo: qualche riga in più nel report e qualche eccezione da ricordare.
    Proposta: tenerle tutte.
