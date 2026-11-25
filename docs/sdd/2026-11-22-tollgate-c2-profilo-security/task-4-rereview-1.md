# Task 4: ri-revisione del giro di correzione 1 (commit `1749ee8`, pacchetto `review-abccbe0..1749ee8.diff`)

Ri-revisore Fable, 23/11/2026, sola lettura. Nessun test rilanciato (nessun dubbio preciso che le esecuzioni riportate non coprissero), nessun subagente, nessuna rete. `HEAD` del worktree è `1749ee8` e l'albero è pulito, quindi i numeri di riga sono quelli dei file del commit.

Controlli fatti oltre alla lettura del diff:
- struttura della skill con uno script di sola lettura: prime 11 righe (frontmatter, titolo, introduzione) uguali ad `abccbe0`; 17 regole, stessi id, stesso ordine, stessi `[blocca]` (13); `Si sovrappone a:` solo in 10 e 12 con gli stessi id; «progetto di C, sezione 11» solo nelle `Fonte:` di 01, 03, 05, 10, 12; 107 righe; nessun `approved`; ogni voce OWASP o Trail of Bits con «idea di»;
- frammento: `tomllib.loads` del file ad `abccbe0` e a `1749ee8` dà lo stesso dizionario (cambiano solo i commenti);
- file del commit: solo i quattro attesi (`docs/uso/comandi.md`, `skills/rules-security/SKILL.md`, `templates/profiles/security.toml`, `tests/test_init.py`); nessun agente, nessuna skill approvata, nessuna pagina di profilo;
- fonti: progetto di C sezione 11 (righe 171-194), spec del nucleo 8.5 (riga 947), catalogo (riga 40), `rules-backend` (R-BACKEND-08, riga 45), le due copie MIT, `pagine/nextjs-proxy.md`, `pagine/marcatori.md`, le schede I-1…I-9 di `FONTI.md`.

Il report nomina i test, il comando e l'output per tutte e due le mani (`tests.test_rules_security tests.test_docs tests.test_manifest`: 92 OK; i cinque file: 436 OK; `SecurityPrecedenceTest`: 71 OK; suite 4458 verdi sui due interpreti; sonda 70 su 70). Le affermazioni controllate sul diff sono vere; una sola imprecisione senza effetto: la mano Fable scrive «28 righe cambiate» e il diff ne mostra 28 nella skill (56 fra tolte e aggiunte), coerente.

### Verdetti sui rilievi

**I1 — R-SECURITY-10 vietava ogni token nel corpo di una risposta.** INDIRIZZATO. `skills/rules-security/SKILL.md:60`: log e messaggi d'errore restano vietati per tutto; per il corpo di una risposta solo hash di password, token di reset e segreti del server; il token consegnato al suo titolare è escluso a parole, con i due esempi (risposta di un login, chiave d'API alla creazione). La riga `:62` dichiara l'allargamento rispetto alle regole approvate. Il login con bearer token non scatta più. Vedi N1 per un residuo minore.

**I2 — R-SECURITY-04 senza uscita per le funzioni senza credenziali.** INDIRIZZATO. `SKILL.md:36`, ultima frase: non si applica al login, alla registrazione, alla richiesta di reset, alla callback di un login (criterio che si vede dal diff: che cos'è la funzione) e a chi legge solo dati pubblici con la dichiarazione nel diff. L'eccezione vale solo per chi **legge**: una funzione che cambia dati resta sotto la regola. Vedi N2.

**I3 — R-SECURITY-09 chiedeva i tre attributi anche quando il codice non li decide.** INDIRIZZATO. `SKILL.md:56`: (a) cookie di una libreria: solo non indebolire; (b) `Secure` legato all'ambiente vale come dichiarato; (c) `SameSite=None` ammesso con `Secure` e il motivo accanto, in tutti e due i casi. La `Fonte:` (`:58`) dichiara le tre parti come scelta nostra. Vedi N3.

**m1 — eccezione di Next.js lontana dall'alternativa, frase a calco.** INDIRIZZATO. `SKILL.md:36`: la parentesi sta accanto a «in una guardia applicata alla sua rotta»; la frase non ha più la struttura della riga di `pagine/nextjs-proxy.md:11`.

**m2 — R-SECURITY-08: «un hash» non qualificato, test, ricerca nel database.** INDIRIZZATO. `SKILL.md:52`: «nel codice che non è di test», «l'hash di un segreto», «Una ricerca nel database per token non è un confronto».

**m3 — R-SECURITY-05: ogni ripiego vietato, elenco aperto.** INDIRIZZATO. `SKILL.md:40`: nessun ripiego per un segreto (chiave di firma compresa); per un'impostazione solo il valore che nega; elenco chiuso di tre voci («Sono impostazioni di sicurezza solo queste»). «il controllo acceso» al posto di `false` è più preciso della decisione del controller e dice la stessa cosa.

**m4 — R-SECURITY-01 e 16: condizione contorta.** INDIRIZZATO. `SKILL.md:22` e `:86`: «Se il diff cambia un file che non è un test né un documento».

**m5 — R-SECURITY-07: di quale libreria è ogni funzione.** INDIRIZZATO. `SKILL.md:48`: «(`jwt.verify` di jsonwebtoken, `jwt.decode` di PyJWT)».

**m6 — R-SECURITY-11: reset e recupero.** INDIRIZZATO. `SKILL.md:65`: due casi distinti, login (utente che non esiste, password sbagliata) e reset o recupero (utente che esiste, utente che non esiste).

**m7 — R-SECURITY-12: la verifica di una libreria.** INDIRIZZATO. `SKILL.md:69`, ultima frase. La frase sulle query con parametri resta, quindi un valore verificato concatenato in una query continua a scattare.

**m8 — R-SECURITY-06 (servizio di login) e R-SECURITY-13 (`//host`).** INDIRIZZATO. `SKILL.md:44` (ultima frase) e `:74` («non un URL completo, e nemmeno la forma `//host`»).

**m9 — `comandi.md` da riallineare.** INDIRIZZATO. `docs/uso/comandi.md:178`: i riassunti di 04, 05, 06, 08, 09, 10, 11, 13 dicono ciò che dicono le regole corrette; «non solo nel middleware o nel proxy» non c'è più. Confrontato tema per tema con la skill: nessuna differenza di sostanza (il riassunto di 10 scrive «segreto, token o hash di password» dove la regola ha anche «password»: la password è un segreto per l'introduzione della skill, quindi è coperta).

**m10 — docstring di `SecurityPrecedenceTest`.** INDIRIZZATO. `tests/test_init.py:1914-1920`: «di norma senza i file sotto un `exclude` … S43 ne dà uno apposta».

**m11 — `check_active` su S14, S20, S42, S51, S52, S58, S65.** INDIRIZZATO. `tests/test_init.py:1999`, `:2033`, `:2146`, `:2205`, `:2212`, `:2249`, `:2298`: dopo `check`, `check_active` con l'attesa `[<altro profilo>, "security"]` per uguaglianza e lo stesso `detected` del caso dove c'è. Nessun caso cambiato, nessun caso da riportare (report: tutti e sette danno `security` attivo).

**m12 — commento sul testo fisso.** INDIRIZZATO. `templates/profiles/security.toml:55-58`: `import jwt` accende anche `import jwt from 'jsonwebtoken'`; vero rispetto a `:97` (marcatore `import jwt`) e a `pagine/marcatori.md:20` e `:44` (il README non ha la riga `import … from`, la forma è stata tolta).

**Il `no` delle fonti (R-SECURITY-10, parentesi della voce «progetto di C, sezione 11»).** INDIRIZZATO. `SKILL.md:63`: «(scelta dell'utente del 22/11/2026: i segreti si considerano in ogni lavoro)»; regge sul progetto di C, sezione 11, riga 194 («ogni implementatore considera input non fidato, segreti, accesso negato e valori predefiniti chiusi»).

**Le «scelta nostra» da dichiarare (01, 16, 03, 04, 05, 06, 07, 12, 14, 17) e la spec del nucleo nella sezione «Fonti».** INDIRIZZATO. `SKILL.md:24`, `:88`, `:34`, `:38`, `:42`, `:46`, `:50`, `:72`, `:80`, `:92`: ognuna delle parti elencate dalla verifica ha la sua frase in coda alla `Fonte:`; in più 08, 09, 10 e 13 dichiarano le parti nuove di questo giro. `SKILL.md:106`: la frase sulla spec del nucleo, con il percorso (il file esiste, la sezione 8.5 è alla riga 947).

**I commenti del frammento (`**/security/**`, `**/rls/**`).** INDIRIZZATO. `templates/profiles/security.toml:29-30` e `:32-34`: il pattern è attribuito al catalogo, la descrizione del contenuto è detta «lettura nostra»; per `rls/` la parte su `supabase/` cita il progetto di B, sezione 12. La stessa correzione su `**/auth/**` (`:16-19`) è oltre la lettera del brief ma è la stessa forma di difetto ed è solo un commento: va bene.

### Fonti cambiate (seconda passata, solo le voci toccate dal diff)

| Voce | Esito | Su cosa regge |
|---|---|---|
| R-SECURITY-01, «… e la condizione sul tipo di file, sono una scelta nostra» | ok | dichiarata nostra; le altre voci invariate |
| R-SECURITY-03, «"nel diff o già nel repo" e i due casi da provare sono una scelta nostra» | ok | dichiarata nostra |
| R-SECURITY-04, «la guardia di rotta e i due casi in cui la regola non si applica sono una scelta nostra» | ok | dichiarata nostra; la parentesi di Next.js nel testo della regola regge su `pagine/nextjs-proxy.md:10-11` e non ne ricalca più la frase |
| R-SECURITY-05, «gli esempi di ripiego e l'elenco chiuso delle impostazioni sono una scelta nostra» | ok | dichiarata nostra; il testo ora è coerente con la scheda I-8 (ripiego «permissivo») |
| R-SECURITY-06, «"attraverso una libreria" e il caso del servizio di login sono una scelta nostra» | ok | dichiarata nostra |
| R-SECURITY-07, «l'obbligo di passare `algorithms`, il divieto di spegnere il controllo della firma e la scadenza per ogni token creato sono una scelta nostra» | ok | dichiarata nostra; i fatti restano su `pagine/marcatori.md:20` |
| R-SECURITY-08, «l'esclusione dei test e della ricerca nel database è una scelta nostra» | ok | dichiarata nostra; «l'hash di un segreto» sta dentro la scheda I-5 |
| R-SECURITY-09, «distinguere il cookie costruito dal codice … sono una scelta nostra» | ok | dichiarata nostra; la voce OWASP resta «idea di» (scheda I-2, che dice `Strict` o `Lax`: l'ammissione di `None` è fra le parti dichiarate) |
| R-SECURITY-10, parentesi di «progetto di C, sezione 11» | ok | progetto di C, sezione 11, riga 194: il `no` è chiuso |
| R-SECURITY-10, «… e l'eccezione per il token consegnato al suo titolare sono una scelta nostra» | ok | dichiarata nostra; hash di password e token di reset nelle risposte reggono sulla copia MIT, «Sensitive Data Exposure» (righe 178-182) |
| R-SECURITY-10, riga «Si sovrappone a» («… e, nelle risposte, gli hash delle password e i token di reset») | ok | vera rispetto a R-BACKEND-08 (`skills/rules-backend/SKILL.md:45`, che si ferma alla risposta d'errore); stessi cinque id |
| R-SECURITY-12, «"con uno schema o con controlli espliciti" e la verifica di una libreria … sono una scelta nostra» | ok | dichiarata nostra |
| R-SECURITY-13, «ammettere i percorsi interni, e dire cosa non lo è, sono una scelta nostra» | ok | dichiarata nostra |
| R-SECURITY-14, «limitare la regola al caso con le credenziali, e nominare l'origine rimandata indietro, sono una scelta nostra» | ok | dichiarata nostra |
| R-SECURITY-16, «… e la condizione sul tipo di file, sono una scelta nostra» | ok | dichiarata nostra |
| R-SECURITY-17, «l'elenco delle azioni e la prova detta nel report sono una scelta nostra» | ok | dichiarata nostra; la voce sulla spec del nucleo 8.5 invariata |
| Sezione «Fonti», frase sulla spec del nucleo | ok | `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:947` («8.5 Effetti esterni») |
| Frammento, commenti di `**/auth/**`, `**/security/**`, `**/rls/**` | ok | catalogo, riga 40 (i tre pattern); il resto è detto nostro; progetto di B, sezione 12 per `supabase/` |
| Frammento, commento sul testo fisso (`import jwt from 'jsonwebtoken'`) | ok | `pagine/marcatori.md:20` e `:44` |

Nessun `no`. Nessuna idea OWASP o Trail of Bits senza «idea di» (controllo automatico su tutte le `Fonte:`). Nessuna frase nuova uguale a una fonte per più di una decina di parole: le frasi aggiunte sono eccezioni e precisazioni che le copie non hanno. Nessuna voce nuova cita ASVS o `security-review`.

### Vincoli ancora veri

Frontmatter, titolo e introduzione uguali byte per byte; 17 regole nello stesso ordine; nessun passaggio fra `[blocca]` e non bloccante; `Si sovrappone a:` solo in 10 e 12 con gli stessi id; «progetto di C, sezione 11» solo in 01, 03, 05, 10, 12; la frase con «progetto di B, sezione 12» al suo posto (`SKILL.md:18`); 107 righe; nessun `approved`; ogni `[blocca]` si giudica su diff o report; nessun file approvato né agente toccato; frammento identico nei dati.

### Danni nuovi nel diff della correzione

Nessuno Critical né Important. Tre Minor, tutti sul testo delle regole e tutti figli di una decisione del controller seguita alla lettera: non bloccano il giro; vanno alla pagina («Da decidere tu») o a un ritocco di poche parole prima dell'approvazione.

- **N1 — Minor, `SKILL.md:60` (R-SECURITY-10).** (a) Dall'elenco per il corpo di una risposta è uscita la **password**: prima del giro la regola la vietava in ogni risposta, ora una risposta di successo che rimanda indietro la password ricevuta (per esempio `res.json(req.body)` in una registrazione) non viola nessuna regola dell'area, perché la password di un utente non è un «segreto del server». Ritocco: «nessuna password, nessun hash di password, nessun token di reset e nessun segreto del server». (b) L'eccezione «il token consegnato al chiamante a cui appartiene» segue il divieto del token di reset nella stessa frase: gli esempi fra parentesi la tengono stretta e due revisori direbbero no a un token di reset nella risposta, ma chi vuole forzarla può dire che il token di reset «appartiene» a chi lo chiede. Tre parole la chiudono: «il token di reset mai, nemmeno a chi lo chiede» (è ciò che la mano Fable scrive nei suoi dubbi, ma non nella regola).
- **N2 — Minor, `SKILL.md:36` (R-SECURITY-04).** (a) «Dati pubblici» non è definito: per una funzione che restituisce nome ed e-mail di un utente con il commento «rotta pubblica», un revisore si ferma alla dichiarazione e un altro dice che un'e-mail non è un dato pubblico. Alla lettera la regola scatta ancora (servono tutte e due le cose: i dati sono pubblici **e** il diff lo dichiara), quindi il buco non è aperto, ma il giudizio sul «pubblico» resta a chi rivede. Ritocco possibile: «dati che chiunque può già leggere senza login». (b) «se il diff lo dichiara…» dopo la virgola si può leggere riferito anche al login e alla registrazione, mentre la decisione del controller lo lega solo ai dati pubblici: basta spezzare la frase («…la callback di un login. Non si applica nemmeno a una funzione che legge solo dati pubblici, se il diff lo dichiara…»).
- **N3 — Minor, `SKILL.md:56` (R-SECURITY-09).** (a) Per `SameSite=None` basta «il motivo scritto accanto»: qualunque commento soddisfa la regola. È un sì o un no netto (il commento c'è o non c'è) ed è la decisione del controller; se si vuole che il motivo dica qualcosa, «il motivo dice quale altro sito deve mandare il cookie». (b) Nel primo caso «il codice dichiara `HttpOnly`, `Secure` e `SameSite`» non dice «accesi»: gli esempi di indebolimento (`httpOnly: false`, `secure: false`) stanno solo nella frase sulle librerie. La frase su `Secure` legato all'ambiente («vale come dichiarato») fa capire che dichiarato vuol dire acceso, quindi due revisori arrivano alla stessa risposta; una parola («dichiara accesi») toglie il dubbio. (c) Costo della forma scelta, da scrivere nella pagina: una libreria di sessioni con valori predefiniti deboli aggiunta senza opzioni non fa scattare la regola (⚠️ da verificare sulla pagina ufficiale, che non è fra le copie, se è il caso di `express-session`, dove a memoria `secure` è spento per difetto).

### Osservazioni fuori ambito

- R-SECURITY-05 (`SKILL.md:40`), già così prima del giro: la regola non esclude i test, mentre R-SECURITY-10 ammette nei test i valori finti. Un `os.environ.get("JWT_SECRET", "PROVA-123")` in un file di configurazione dei test divide i revisori. Da portare alla pagina insieme a 08, che ora i test li esclude.
- La sezione `/tollgate:rules-security` di `comandi.md` è un paragrafo molto lungo (lo dice anche la mano opus): spezzarla è lavoro del Task 6, non di questo giro.
- Restano da portare in «Da decidere tu» (già nel report): le due forme di 09, se 08 blocca, 01 e 16 vicine.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.

I1, I2, I3, m1-m12, il `no` delle fonti, le «scelta nostra» e i commenti del frammento sono chiusi; le 19 voci di fonte toccate sono `ok`; i vincoli strutturali reggono. Restano tre Minor nuovi (N1, N2, N3) sul testo di 10, 04 e 09: ritocchi di poche parole o domande per la pagina, a scelta del controller.
