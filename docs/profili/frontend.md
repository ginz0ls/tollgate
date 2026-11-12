# Regole del profilo frontend di tollgate

Questa pagina è per te: dice quali sono le regole per il codice d'interfaccia (componenti, pagine, stili) e per la sua accessibilità, e cosa hai deciso su ventidue punti dubbi. Le regole sono approvate e il profilo si può accendere.

Approvata dall'utente il 2026-11-11.

## Cosa sono

Sono dodici regole in più rispetto a quelle di base. Dieci di queste bloccano il lavoro se non sono rispettate. Valgono solo per il codice che l'utente vede e tocca: un componente, una pagina, un foglio di stile. Dicono, per esempio, di cercare un componente simile prima di crearne uno, di usare i colori del progetto invece di scriverli a mano, di non fare un pulsante con un `div` e di dare a ogni campo la sua etichetta.

Qualche parola, la prima volta che serve:

- **Interfaccia**: la parte del programma che l'utente vede e tocca.
- **Componente**: un pezzo riusabile dell'interfaccia, come un pulsante o una scheda. Nel codice è un file `.tsx`, `.jsx`, `.vue`, `.svelte` o `.astro` che esporta un pezzo di pagina.
- **Profilo**: un gruppo di regole, di agenti e di file che tollgate usa per un tipo di lavoro (qui l'interfaccia; ce ne sono altri, come `backend` per i server).
- **Percorso esatto**: il nome completo di un solo file, scritto nel `tollgate.toml`. Vince su ogni cartella.
- **Client delle API**: il codice che chiama i server per chiedere o mandare dati.
- **CDN**: un servizio che serve file (per esempio una libreria) da un indirizzo web, senza che tu li scarichi nel progetto.
- **Loader**: la funzione di una rotta che carica i dati prima di mostrare la schermata.
- **Gestore**: la funzione che reagisce a un'azione, per esempio un clic.
- **Pagina e rotta**: una pagina è una schermata del sito; la rotta è l'indirizzo a cui si arriva a quella schermata.
- **Modulo di rotta**: il file che definisce una rotta e la sua schermata, nei progetti che usano un router.
- **Libreria di rotte** (o router): il programma che collega gli indirizzi alle schermate. Quelle che tollgate riconosce sono TanStack Router, React Router e Remix.
- **Foglio di stile**: un file `.css` o `.scss` che dice come appare la pagina (colori, spazi, caratteri).
- **Token di design**: un valore con un nome (per esempio un colore o una distanza) definito una volta sola e riusato ovunque, invece di ripeterlo a mano.
- **Accessibilità**: far funzionare l'interfaccia anche con la sola tastiera o con un lettore di schermo, il programma che legge la pagina a voce.
- **Nome accessibile**: il testo che il lettore di schermo legge per un pulsante o un link. Un pulsante con la sola icona non ne ha uno, se non glielo dai.
- **Focus**: l'elemento che in questo momento riceve la tastiera (di solito ha un contorno visibile).
- **WCAG**: la norma del W3C (l'ente che scrive gli standard del web) sull'accessibilità. La versione 2.2 è del 12 dicembre 2024; ogni criterio ha un numero e un livello (A, AA).
- **Marcatore**: una riga di codice che `init` cerca nei file per riconoscere un tipo di lavoro (qui, la riga che importa un router).
- **Percorso per estensione**: un percorso che vale per tutti i file con una certa estensione, scritto come `**/*.tsx`.
- **`tollgate.toml`**: il file di impostazioni di tollgate nella radice del progetto.
- **`dod`**: la lista dei controlli che devono essere verdi a fine lavoro. Un **typecheck** è il controllo dei tipi del codice; un **lint** è il controllo dello stile e degli errori comuni.

Le regole di accessibilità vengono dalla norma WCAG 2.2 e dalla lista di controllo di una skill con licenza MIT, e stanno qui, in questo profilo: non c'è una skill a parte e non c'è un profilo a parte per l'accessibilità. Le regole sulla velocità di una pagina restano fuori: il profilo che le avrebbe non esiste ancora.

Valgono per chi scrive il codice e per chi lo rivede. Chi scrive può essere un agente a cui è affidato un task, cioè un pezzo del lavoro. Può essere anche Claude Code che lavora direttamente con te.

Chi rivede guarda tre cose. Il «diff» è l'elenco delle righe cambiate. Il «report» è il resoconto che l'agente scrive alla fine. La «nota di ricerca» è l'elenco di cosa ha letto prima di scrivere. Per ogni regola chi rivede risponde sì o no. La colonna «Si giudica su» dice su quale delle tre guarda: la regola 3, per esempio, si giudica sul solo diff. Nessuna regola di questo profilo si giudica sulla sola nota.

## Quando si accende

Il profilo non si accende da solo. Si accende solo in un progetto dove il comando `/tollgate:init` lo propone e tu copi il blocco proposto nel `tollgate.toml` del progetto, e `init` lo propone perché le regole sono approvate. Un progetto nuovo riceve la proposta con `/tollgate:init --propose`; uno che ha già tollgate la riceve con `/tollgate:init --update`. In tutti e due i casi la copia la fai tu. Conta nei lavori dei livelli L1 e L2, cioè medi e grandi. Un lavoro piccolo (L0), come cambiare un colore, lo scrive la sessione principale, senza task e senza agenti per area.

`init` lo propone in tre casi.

1. Se nel progetto c'è una cartella `components/` (a qualunque profondità) o la cartella `web/` alla radice.

2. Se nel progetto ci sono file con una di queste estensioni: `.tsx`, `.jsx`, `.vue`, `.svelte`, `.astro`, `.css`, `.scss`. `init` scrive un solo percorso per ogni estensione, per esempio `**/*.tsx`.

3. Se un file di codice contiene la riga che importa un router, nelle due forme di virgolette (`'` e `"`): `@tanstack/react-router` (TanStack Router), `react-router` e `react-router-dom` (React Router), `@remix-run/react` (Remix). Il file entra nel profilo con il suo percorso esatto.

Cosa non lo accende, e perché:

- Le cartelle dei server alla radice (`server/`, `api/`, `backend/`, `functions/`), la cartella `infra/` e la cartella `supabase/` sono escluse: nessun file lì sotto accende `frontend`, né per la cartella né per le righe di codice. Sono dei profili `backend` e `infra`; per `supabase/` il profilo del database arriva con B7, e fino ad allora vale il punto 19 di «Cosa hai deciso» (un `.tsx` lì sotto va a `frontend`). La riga «lo accendono N file» della proposta conta anche i file delle cartelle escluse, quindi il numero può essere più alto dei file che il profilo propone davvero.
- La configurazione degli strumenti (`vite.config.*`, `tsconfig.json`, `eslint.config.*`) resta all'agente generico.
- Le cartelle `services/` e `hooks/` non lo accendono, e i loro file `.ts` vanno all'agente generico (primo punto di «Cosa hai deciso»).
- I file `.html`, `.sass`, `.less` e le pagine `page.js` di Next.js non lo accendono (secondo punto).

**Le precedenze.** I percorsi per estensione perdono contro ogni cartella di un altro profilo e contro ogni file nominato da un altro profilo. Alcuni esempi, tutti provati:

- `server/components/Mail.tsx` va a `backend`, perché sta in una cartella di server alla radice; `frontend` lì non propone niente.
- Con `server/app.tsx` e `src/main.tsx` nello stesso progetto, `server/app.tsx` va a `backend` e `src/main.tsx` va a `frontend`.
- `src/ai/components/Chat.tsx`, senza righe che chiamano un modello, va a `frontend`, perché la cartella `components/` ha tre pezzi di percorso contro i due di `src/ai/`. Se il file contiene l'import di un programma per i modelli, va invece al profilo `ai`.
- `prompts/Card.tsx` va al profilo `ai` (la sua cartella `prompts/` vince sull'estensione).

**I moduli di rotta e la cartella `routes/`.** Il profilo `backend` considera sua ogni cartella `routes/`. Un modulo di rotta che importa una libreria di rotte viene trovato da `frontend` e non tiene la cartella `routes/` a `backend`: la cartella resta fuori da `backend` e il file va a `frontend`. Ma se nella cartella c'è anche un solo file senza alcun import di una libreria di rotte, per esempio una funzione di utilità, un test o un foglio di stile, la cartella `routes/` resta a `backend` e tutti i suoi file vanno lì: il rilevamento per contenuto non guarda i test e i fogli di stile. Per correggere basta toglierla a mano: cancelli dall'elenco `paths` del blocco di `backend` nel `tollgate.toml` la riga della cartella (per esempio `src/routes/**`). Questo vale per una proposta nuova. Se il `tollgate.toml` ha già un blocco `backend` con la cartella `routes/` (per esempio scritto da `init` per il profilo `backend`), `init --update` propone `frontend` ma non toglie la riga da `backend`: lo segnala con «vince backend», e la cartella si toglie a mano, come per il file senza import. Lo hai già deciso così per i moduli di rotta (costo accettato).

**Un file che è di tutti e due.** Se un file ha sia l'import di una libreria di rotte sia un marcatore di `backend` (per esempio `export async function GET(`), la cartella `routes/` resta a `backend` e quel file va a `frontend`: il contrario di quello che serve, ma raro.

## Le regole

| N. | In parole semplici | Blocca? | Si giudica su | Da dove viene |
|---|---|---|---|---|
| 1 (R-FRONTEND-01) | La prima volta che un file usa una parte di una libreria d'interfaccia (un framework, un router, una libreria di componenti, Tailwind), il report ha l'indirizzo della pagina ufficiale della versione scritta in `package.json`, con la versione. Se il progetto non dichiara la versione, il report lo dice e dà l'indirizzo della documentazione corrente. | sì | il report | Una proposta del progetto di B che hai rivisto (sezione 3.4) e la guida di Tailwind sul passaggio dalla 3 alla 4. Il caso senza versione è una scelta nostra. |
| 2 (R-FRONTEND-02) | Se il lavoro crea un componente nuovo, il report elenca i componenti simili cercati nel progetto (con i percorsi) e perché non li riusa, oppure dice che non ce ne sono. | sì | il report | La proposta del progetto di B che hai rivisto (sezione 3.4) e la skill `frontend-ui-engineering` (MIT). I percorsi e il motivo nel report sono una scelta nostra. |
| 3 (R-FRONTEND-03) | Un componente nuovo o cambiato che carica dati mostra tre stati: caricamento, errore e vuoto. | sì | il diff | La skill `frontend-ui-engineering` (MIT). |
| 4 (R-FRONTEND-04) | Se il progetto ha token o variabili di design (variabili CSS, il tema di Tailwind), colori e spaziature nuovi li usano: nessun colore scritto a mano in un componente. | sì | il diff | La skill `frontend-ui-engineering` (MIT). |
| 5 (R-FRONTEND-05) | Un elemento che reagisce a un clic è un `button` o un link `a` con `href`, non un `div` o uno `span` con un gestore di clic. | sì | il diff | WCAG 2.2 (tastiera e nome, ruolo e valore), la prima regola di «Using ARIA» del W3C (una bozza sospesa), la skill `frontend-ui-engineering` (MIT) e le tue scelte sull'accessibilità (progetto di B, sezione 13). |
| 6 (R-FRONTEND-06) | Un pulsante o un link con la sola icona ha un nome accessibile (`aria-label` o testo nascosto). Un'immagine che informa ha `alt` con il suo contenuto; una decorativa ha `alt=""`. | sì | il diff | WCAG 2.2 (contenuti non testuali, nome, ruolo e valore), la skill `frontend-ui-engineering` con la sua lista di controllo (MIT) e il progetto di B (sezione 13). |
| 7 (R-FRONTEND-07) | Ogni campo di un modulo ha un'etichetta associata: una `label` con `for` o `htmlFor`, una `label` che lo contiene, oppure `aria-labelledby` o `aria-label`. | sì | il diff | WCAG 2.2 (informazioni e relazioni, etichette), la skill `frontend-ui-engineering` con la sua lista di controllo (MIT) e il progetto di B (sezione 13). |
| 8 (R-FRONTEND-08) | Il diff non toglie l'indicatore del focus (per esempio con `outline: none`) senza metterne uno visibile al suo posto. | sì | il diff | WCAG 2.2 (focus visibile), la lista di controllo di `frontend-ui-engineering` (MIT) e il progetto di B (sezione 13). |
| 9 (R-FRONTEND-09) | Un messaggio che compare senza spostare il focus (salvataggio riuscito, errore d'invio) sta in una regione `role="status"`, `role="alert"` o con `aria-live`, così il lettore di schermo lo legge. | sì | il diff | WCAG 2.2 (messaggi di stato), la lista di controllo di `frontend-ui-engineering` (MIT) e il progetto di B (sezione 13). |
| 10 (R-FRONTEND-10) | Un dialogo o un menu che si apre porta il focus al suo interno, si chiude con il tasto Esc e riporta il focus dove era. | no | il diff | WCAG 2.2 (ordine del focus, nessuna trappola per la tastiera), la skill e la lista di controllo di `frontend-ui-engineering` (MIT) e il progetto di B (sezione 13). |
| 11 (R-FRONTEND-11) | Se il repo ha già test dei componenti (`*.test.tsx`, `*.spec.tsx`, una cartella `__tests__/`), un componente nuovo o cambiato con stato, gestori o condizioni ha un test dei componenti nel diff. | sì | il diff | Il catalogo dei profili (i test dei componenti nella definizione di fatto) e la skill `frontend-ui-engineering` (MIT). La condizione «se il repo ha già test» è una scelta nostra. |
| 12 (R-FRONTEND-12) | Lo stile nuovo segue quello già presente nel progetto, senza le scelte che un modello sceglie da solo: viola o indaco ovunque, gradienti in eccesso, schede tutte uguali. | no | il diff | La skill `frontend-ui-engineering` (MIT) e la skill `frontend-design` (Apache-2.0). |

La colonna «Blocca?» dice quali regole sono le più serie. Se una di queste non è rispettata, chi rivede ferma il task. Le altre sono segnalate ma non lo fermano. Un difetto viene segnalato una sola volta.

Le fonti sono state controllate una per una. Il rapporto completo, con le citazioni, è in `docs/profili/verifiche/frontend-fonti.md`. Anche ogni estensione, ogni cartella e ogni riga di codice che accende il profilo ha una fonte: una pagina ufficiale per le righe di codice e per le estensioni dei framework; il catalogo (cioè una tua scelta) per `components/`, `web/`, `.css` e `.scss`.

## Cosa cambia per i comandi

Una cosa da sapere, perché tocca il tuo modo di lavorare.

**Lint, typecheck e test dei componenti li aggiungi tu, a mano.** Il profilo parte senza un controllo nella definizione di «fatto» (la lista `dod`). Il comando cambia da progetto a progetto (`eslint`, `tsc --noEmit`, `vitest`) e un comando scritto da tollgate fallirebbe dove il programma manca. Se vuoi un controllo in più, lo scrivi nel `tollgate.toml`, per esempio così:

```
[profiles.frontend]
commands = { lint = "npx eslint .", typecheck = "npx tsc --noEmit" }
dod = ["lint", "typecheck"]
```

Attenzione: i comandi di `dod` li lancia tollgate stesso a fine lavoro, senza chiedere e senza nessun controllo sugli effetti, con le credenziali che hai salvato sul computer. Un comando lì dentro non deve scrivere su un servizio. Un comando aggiunto a mano in `dod` che non produce un report dei test conta verde solo se nel `tollgate.toml` c'è `[project] allow_no_tests = true`, oppure se approvi con `/tollgate:approve unverified-tests`.

## Cosa hai deciso

Su ventidue punti la fonte non diceva proprio quello che la regola chiede, o la scelta era tua, o la proposta aveva un costo che dovevi conoscere. Hai approvato la proposta in tutti e ventidue: resta com'era scritta.

1. **`services/` e `hooks/` restano all'agente generico.** Le cartelle `services/` (i client delle API) e `hooks/` (le funzioni riusabili di React) non accendono il profilo: i loro file `.ts` li scrive e li rivede l'agente generico, senza le regole di questa pagina. I loro `.tsx` vanno comunque a `frontend`. Il motivo: una cartella `hooks/` c'è anche nei plugin di Claude Code e in progetti come tollgate, e una `services/` dentro un server porterebbe a `frontend` il codice del server.
   Hai approvato: resta la proposta, cioè lasciare così.

2. **`.html`, `.sass`, `.less` e le pagine `page.js` restano fuori.** `.html` accenderebbe troppo (rapporti generati, modelli di un server, documentazione); `.sass` e `.less` compaiono in pochissimi progetti; le pagine di Next.js scritte in JavaScript (`page.js`) non si possono nominare con le forme di percorso che abbiamo. Costo: vanno all'agente generico.
   Hai approvato: resta la proposta, cioè lasciarli fuori. Chi ne ha li aggiunge a mano nel `tollgate.toml`.

3. **Regola 1 (R-FRONTEND-01), il progetto senza versione dichiarata.** Le fonti chiedono la documentazione della versione scritta in `package.json`. Dove la versione non c'è (nessun `package.json`, una libreria caricata da una CDN senza versione) la regola chiede che il report lo dica e dia l'indirizzo della documentazione corrente: è una scelta nostra. Senza questa via d'uscita la regola non si potrebbe rispettare in quei progetti.
   Hai approvato: resta la proposta, cioè tenerla.

4. **Regola 2 (R-FRONTEND-02), i percorsi e il motivo nel report.** Le fonti dicono di cercare un componente simile prima di crearne uno. Chiedere che il report elenchi i percorsi cercati e perché non li riusa è una scelta nostra: serve a chi rivede per capire che la ricerca è stata fatta.
   Hai approvato: resta la proposta, cioè tenerla.

5. **Regola 11 (R-FRONTEND-11), solo dove ci sono già test dei componenti.** Il catalogo mette i test dei componenti nella definizione di fatto, senza condizioni. Ma sul tuo disco pochi progetti hanno test dei componenti, e la regola li pretenderebbe da tutti. La condizione «se il repo ha già test dei componenti» è una scelta nostra. Costo: dove non ce ne sono, nessuna regola chiede di scriverli.
   Hai approvato: resta la proposta, cioè tenerla.

6. **Regola 7 (R-FRONTEND-07), l'`aria-label` al posto dell'etichetta.** La lista di controllo della skill ammette l'`aria-label` per un campo (voce «Screen Readers»), mentre un'altra voce («Forms») chiede un'etichetta visibile. La regola li accetta tutti. Costo: un campo che ha solo un `aria-label` passa, anche se chi vede lo schermo non ne vede l'etichetta.
   Hai approvato: resta la proposta, cioè tenerla così.

7. **I componenti con codice AI dentro `components/`, e i «componenti» che non sono d'interfaccia.** Se in una cartella `components/` dentro `ai/` c'è un componente che chiama un modello (importa un programma per i modelli) insieme ad altri componenti senza quella riga, la cartella è proposta a `frontend` e vanno a `frontend` tutti, anche quello con il codice AI. Se è l'unico file della cartella, resta di `ai`. Fuori da `ai/`, un componente che chiama un modello resta di `ai` anche dentro `components/`. Allo stesso modo, in una cartella `components/` dentro `ai/` i file che non sono d'interfaccia (per esempio i «componenti» di una pipeline) vanno a `frontend` se non importano un programma per i modelli. Costo: un file che dovrebbe seguire le regole di `ai` segue quelle di `frontend`.
   Hai approvato: resta la proposta, cioè lasciare così.

8. **`components/ai/`, `components/routes/`, `handlers/` e `app/agents/`.** Dentro la tua cartella `components/` una sottocartella `ai/` (o `prompts/`, `agents/`, `llm/`) va al profilo `ai`, perché il suo percorso ha tre pezzi contro i due di `components/`. Lo stesso per una sottocartella `routes/` o `handlers/`: va a `backend`, perché per `backend` queste due cartelle valgono a qualunque profondità. Una rotta di Next.js che si chiama come una cartella di `ai` (`app/agents/`) va a `ai`. Se il file ha l'import di una libreria di rotte, un componente in `components/routes/` va a `frontend`. Costo: un componente d'interfaccia messo in una di queste sottocartelle segue le regole dell'altro profilo.
   Hai approvato: resta la proposta, cioè lasciare così.

9. **I moduli di rotta dentro `ai/routes/`.** Un `.tsx` in una cartella `ai/routes/` che importa un router va al profilo `ai` (vince la cartella), mentre un `.ts` nello stesso posto, con lo stesso import, va a `frontend` (vince il suo percorso esatto). Senza import, un `.tsx` lì va a `backend`. Costo: lo stesso modulo dà esiti diversi secondo l'estensione.
   Hai approvato: resta la proposta, cioè lasciare così.

10. **I componenti dentro una cartella di server alla radice.** Un componente in `server/` (per esempio un modello di e-mail scritto in `.tsx`) va a `backend`; lo stesso vale per `api/`, `backend/` e `functions/`, mentre `infra/` va a `infra`; `supabase/` andrà al profilo del database, che arriva con B7 (fino ad allora vale il punto 19). `frontend` lì non propone niente, per non rubare a quei profili i file di una cartella `components/` o un `.ts` con un router. Costo: un componente d'interfaccia messo in una di queste cartelle segue le regole del profilo della cartella. Le cartelle valgono solo alla radice: `apps/api/` non è coperta.
    Hai approvato: resta la proposta, cioè lasciare così.

11. **I `.ts` e i `.js` che importano `react-router-dom`.** Un file `.ts` o `.js` che importa un router fuori dalle cartelle proposte entra nel profilo con il suo percorso esatto, e un percorso esatto vince su ogni cartella. Succede anche per un hook di `hooks/` o un file di `services/` che usa `useNavigate` da `react-router-dom` (comune con React Router 6): il file va a `frontend`, contro il punto 1. Costo: qualche riga di percorso esatto in più nella proposta.
    Hai approvato: resta la proposta, cioè lasciare così.

12. **Le rotte di sole risorse e i moduli di React Router 7 con i soli tipi.** Una rotta di sole risorse è una rotta lato server che risponde con dati e non mostra nessuna schermata (ha un `loader`, senza componente). Se importa la libreria di rotte va a `frontend`, e il suo codice di server segue le regole d'interfaccia: è il costo. Nei sorgenti ufficiali di React Router e di Remix queste rotte non importano la libreria, quindi non sono trovate e la cartella `app/routes/` resta a `backend`: è la parte sicura, perché `backend` ha le regole dei server. Quelle di server di TanStack Start la importano e vanno a `frontend`. In più, i moduli di React Router 7 che importano solo i tipi generati (`./+types/…`) non sono trovati per contenuto e tengono `app/routes/` a `backend`.
    Hai approvato: resta la proposta, cioè lasciare così.

13. **I file d'interfaccia sotto `.claude/` e `.github/`.** `init` non propone `frontend` per un file sotto `.claude/`, `.github/tollgate/`, `.github/actions/` o la cartella della proposta. Ma `**/*.tsx` e gli altri percorsi per estensione, una volta nel `tollgate.toml`, valgono in tutto il repo: un task su un file `.css` di un'azione di GitHub o su un `.tsx` di esempio di una skill di progetto va a `frontend`. Costo: quei file seguono le regole d'interfaccia.
    Hai approvato: resta la proposta, cioè lasciare così.

14. **`pages/api/`.** Le API del Pages Router di Next.js stanno in `pages/api/`, che non è un percorso di `backend`: un loro file `.tsx` va a `frontend`, e uno `.ts` all'agente generico (a meno che contenga una riga di `backend`).
    Hai approvato: resta la proposta, cioè lasciare così; chi ha API lì aggiunge la loro cartella al blocco di `backend`.

15. **SvelteKit.** Un modulo `.svelte` non ha una riga di import fissa che lo riconosca, e le pagine di SvelteKit stanno in `routes/`, che `backend` considera sua: in un progetto SvelteKit la cartella `routes/` va a `backend`, anche per i file `.svelte`. Sul tuo disco non c'è nessun progetto SvelteKit.
    Hai approvato: resta la proposta, cioè lasciare così, e riprendere il caso se arriva un progetto SvelteKit.

16. **Un test o un foglio di stile in `routes/`.** Il rilevamento per contenuto non guarda i test né i fogli di stile (`.css`, `.scss`), ma la cartella `routes/` li comprende: un test `.test.tsx` o un `index.module.css` dentro una cartella `routes/` la tengono a `backend`, anche se tutti gli altri file importano il router. Rimedio: togliere a mano la cartella dal blocco di `backend`, come sopra.
    Hai approvato: resta la proposta, cioè lasciare così.

17. **Una cartella `routes/` con un solo file senza import.** Anche un solo file senza import di un router, per esempio `src/routes/utils.ts`, tiene la cartella `routes/` a `backend` (lo hai accettato). Vale anche dentro `web/`: una cartella `web/routes/` con un file senza import va a `backend`, perché il suo percorso ha più pezzi di `web/`, anche se il resto di `web/` è di `frontend`.
    Hai approvato: resta la proposta, cioè lasciare così.

18. **Un file con l'import del router e un marcatore di `backend`, fuori da una cartella.** Se un file come `src/lib/server.ts` ha l'import di un router e anche un marcatore di `backend` (per esempio `from 'express'`), è trovato da tutti e due i profili. A parità di percorso vince il primo blocco del `tollgate.toml`. In una prima proposta `init` scrive i blocchi in ordine alfabetico, quindi va a `backend`; con `--update` un profilo nuovo va in coda, quindi l'esito dipende dall'ordine in cui i blocchi sono stati aggiunti. Dentro `routes/` vale quello che c'è sopra (la cartella resta a `backend`, il file va a `frontend`).
    Hai approvato: resta la proposta, cioè lasciare così.

19. **Un `.tsx` sotto `supabase/`.** `init` non propone `frontend` per `supabase/`, ma a runtime un `**/*.tsx` proposto per altri file copre anche una funzione `index.tsx` di Supabase, che va a `frontend` finché non arriva il profilo del database (B7); da allora vince il suo.
    Hai approvato: resta la proposta, cioè lasciare così e riprendere il caso in B7.

20. **Un `route.tsx` di Next.js senza marcatore di `backend`.** Un gestore come `src/app/api/og/route.tsx` con `export async function GET(` va a `backend` (il suo percorso esatto vince sull'estensione). Senza quella riga, per esempio con `export const GET = …`, va a `frontend`: non si riconosce da solo.
    Hai approvato: resta la proposta, cioè lasciare così.

21. **Il codice di un server dentro `web/`.** Le cartelle di `backend` valgono solo alla radice, quindi `web/api/`, `web/functions/` e `web/server/` vanno a `frontend` (prima andavano all'agente generico). Sul tuo disco non c'è nessun progetto con `web/`.
    Hai approvato: resta la proposta, cioè lasciare così.

22. **Un `.css` in un repo senza interfaccia.** Un sito di documentazione o un rapporto generato che ha un `.css` fa proporre `frontend` in un repo che non ha un'interfaccia da programmare. Rimedio: togliere `**/*.css` dal blocco di `frontend` nel `tollgate.toml`. In più, `dod` e `commands` restano vuoti (vedi «Cosa cambia per i comandi»): il catalogo proponeva «lint, typecheck, test dei componenti», ma il comando dipende dal progetto e uno scritto da `init` fallirebbe dove il programma manca.
    Hai approvato: resta la proposta, cioè lasciare così e togliere il `.css` a mano dove non serve; `dod` vuoto, come per `infra` e `backend`.

## Regole tolte dalla verifica

Nessuna regola è uscita: ciascuna ha almeno una fonte che regge, e i numeri restano. Rispetto alla bozza che è stata verificata sono cambiate due regole, tolte della parte che nessuna fonte diceva, senza aggiungere fonti nuove:

- La regola 4 diceva «colori, spaziature e caratteri nuovi». La fonte parla dei livelli dei titoli, non di un token per i caratteri: ora dice solo colori e spaziature.
- La regola 12 elencava, tra le scelte da modello, un «carattere di sistema scelto per default». Le due skill citate non lo dicono in quel punto: restano il viola o l'indaco ovunque, i gradienti in eccesso e le schede tutte uguali.

Nessun percorso, nessuna riga di codice e nessuna cartella esclusa sono usciti.
