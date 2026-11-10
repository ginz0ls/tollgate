# Revisione del Task 4 di B5 (commit 1423a9d, pacchetto 1dcc9c2..1423a9d)

Revisore: sonnet, sola lettura. Letti: regole del ruolo, brief, `task-4-fonti.md`, decisioni 2, 3, 4, 6, 8, 12, 15, vincoli globali, cautele, report, pacchetto del diff, `carry.md` (voci del Task 4). Controlli mirati fuori dal diff: R-BACKEND-04 nella skill (per il «blocca» della tabella), `skills/init` (opzioni `--propose` e `--update`), `docs/profili/infra.md` (confronto del paragrafo su `dod` e della forma della pagina), copie delle fonti (`ecc-security-reviewer.md`, `workers-secrets.md`) per le correzioni di R-07 e R-08. Nessun test rilanciato.

## Aderenza

Decisioni del controller (`carry.md`):
- ✅ Rapporto con le quattro tabelle di `task-4-fonti.md`, parole nostre, citazioni di una riga (`docs/profili/verifiche/backend-fonti.md`, sezioni «Regole e fonti», «Pattern dei percorsi», «Marcatori di contenuto», «Esclusione»). `**/routes/**` e `**/handlers/**` sono `ok` con il rilievo sulla larghezza accanto (righe 160-161 del rapporto nel pacchetto).
- ✅ `export function POST(` esce da `templates/profiles/backend.toml`; `MARKERS` a 23 e `len(...) == 23` in `test_detect_markers_verified`; la riga `no` resta nel rapporto, la voce c'è anche nella pagina («Regole tolte dalla verifica» e «Quando si accende»).
- ✅ Correzioni delle regole: R-01 senza «Contract First»; R-09 senza «Verification»; R-12 «scelta nostra»; R-07 riscritta sui fatti della pagina dei segreti (confermato su `workers-secrets.md`); R-08 con «Fail Securely» (confermato su `ecc-security-reviewer.md`, punto 3 dei principi). Numeri invariati, nessuna regola esce, sezione «Regole tolte dalla verifica» senza id.
- ✅ «Da decidere tu» ha nove punti, ognuno con proposta: R-02, 05, 09, 12 «scelta nostra»; `routes/` e `handlers/`; Worker senza import e senza `ExportedHandler` (con `workers/`); cartelle solo alla radice; `dod` vuoto; `supabase/` in un pacchetto di monorepo.
- ✅ `dod`: la pagina dice che un comando a mano senza report dei test vale verde solo con `allow_no_tests = true` o `/tollgate:approve unverified-tests` (pagina, sezione «Cosa cambia per i comandi»).
- ❌ Rinvio (decisione 15): vedi I-1.

Requisiti della pagina:
- ✅ Tabella: tutte e dodici le righe coincidono con la skill per numero, «blocca» (R-01..09 e R-12 sì; R-10 e R-11 no) e «si giudica su» (report per 01, 02, 05, 12; diff per le altre). Lo fissano anche `test_page_number_matches_id`, `test_page_blocca_matches_skill`, `test_page_judged_on_matches_skill`.
- ✅ Cosa accende `backend` e cosa no: `services/` (motivo dato), `supabase/` a `database`, Wrangler e Vercel a `infra`, L0 contro L1/L2, scritture di KV e R2 con `--local`, D1 solo con `--remote` o `--preview`: coerenti con le decisioni 1, 4, 6, 12. Il paragrafo sul `dod` è coerente con `docs/profili/infra.md`.
- ✅ Frammento: nessuna regola tolta dal rapporto resta nel frammento o nella skill; i file di `infra`, `ai`, `base` e i loro rapporti non sono nel diff; nessun `approved` nella skill.
- ✅ Dati privati: nessun nome utente, host, progetto privato o token nei due file nuovi.
- ✅ Nessuna frase delle fonti copiata nella pagina o nella skill; nel rapporto le citazioni sono di una riga.
- ⚠️ Che `turbo run deploy` e `nx run web:deploy` restino scoperti (pagina, «Gli script deploy e release nei monorepo») non si verifica dal diff né dalle decisioni 7 (non nominano né l'uno né l'altro); è plausibile (il gestore non è `npm`/`pnpm`/`yarn`/`bun`) ma conviene un controllo su `bash.script_name` nel Task 2.
- ⚠️ `docs/profili/infra.md` (approvata, intoccabile) dice che le scritture remote di `wrangler kv`, `d1`, `r2` «restano scoperte»: dopo B5 non è più vero. Non è un difetto di questo task, ma va ricordato al Task 9 / al rapporto finale.

## Punti di forza

- Il rapporto segue fedelmente `task-4-fonti.md` e aggiunge «Correzioni fatte dopo la verifica» e «Parti dichiarate scelta nostra», che rendono tracciabile cosa è passato alla pagina.
- La pagina ha una forma coerente con `infra.md`; le parole tecniche sono quasi tutte spiegate la prima volta (server, API, rotta, Worker, Wrangler, KV/D1/R2, `env`/`vars`, segreto, validare, query con parametri, paginare, `dod`, typecheck, monorepo, diff/report/nota). Frasi brevi, costo esplicito (il costo di `--local` e quello del lanciatore).
- I test nuovi leggono le tabelle per sezione, normalizzano le virgolette, confrontano l'esclusione con il frammento vero e verificano `scelta nostra` anche per R-12.
- Gli esiti `no` sono stati davvero applicati alla skill, con asserzioni su `Contract First`, `Verification`, `Fail Securely`.

## Rilievi

### Critical
Nessuno.

### Important

**I-1. «Come rispondere → Rinvio» non dice il vero (decisione 15, carry).** `docs/profili/backend.md`, ultima sezione (righe 101-102 del file nuovo). Dice che con «Rinvio» «il profilo `backend` resta spento» e che le parti già pronte «si possono unire lo stesso». Manca ciò che la decisione 15 chiede come requisito: su `main` si unisce solo la parte dei Task 1-2 (esclusione per frammento, scritture di Wrangler, script nei monorepo); bozza delle regole, pagina e frammento restano sul ramo `b5-profilo-backend`. Così com'è, l'utente può capire che le regole e il frammento arrivano comunque su `main` ma spenti. Nessun test lo copre. Correzione: aggiungere alla voce «Rinvio» una frase sul modello di «Se rinvii, su `main` si uniscono solo le parti già pronte che non dipendono da questa pagina (…). Le regole, questa pagina e il riconoscimento delle cartelle restano sul ramo di lavoro finché non decidi»; e un test che cerchi nella sezione «Come rispondere» una frase con `ramo` accanto a `Rinvio` (per id e parole chiave, come gli altri).

**I-2. «Quando si accende», ultima frase (`docs/profili/backend.md`, riga 36).** «Un file nuovo fuori dalle cartelle e senza una di quelle righe non è coperto finché non applichi la riga che `/tollgate:init --update` ti propone» è contraddittoria: un file senza cartella e senza righe non è mai trovato, quindi `--update` non propone nulla. E la frase prima («Un file che cambia quando il profilo è già acceso lo prende l'agente di `backend`») è vaga. Manca il fatto vero della decisione 3: un file trovato per le sue righe entra con il suo percorso esatto; gli altri file della stessa cartella (per esempio i file di un Worker che non hanno `cloudflare:workers`) vanno all'agente generico, e un task che tocca insieme un file trovato e uno non trovato va a `backend`. Correzione: riscrivere le due frasi su questi fatti, in parole semplici.

**I-3. «Regole tolte dalla verifica» descrive male cosa è cambiato (pagina, riga 93).** Dice che «tre regole avevano una parte che nessuna fonte contiene, e ora lo dicono apertamente» e che «due sono state riscritte sui fatti delle pagine ufficiali». Dal diff: R-05 e R-09 dichiaravano già la «scelta nostra» nel commit precedente (1dcc9c2; il diff le mostra invariate in questo commit); solo R-12 la riceve in questo task. È riscritta una sola regola (R-07); R-08 non è riscritta, ha solo una fonte in più. La pagina deve essere vera: correzione, per esempio «R-12 dichiara ora che riportare la prova locale è una scelta nostra; R-07 è riscritta sui fatti della pagina dei segreti; R-08 cita una fonte in più per la parte sul corpo delle risposte d'errore».

**I-4. «Le fonti sono state controllate…» (pagina, riga 57) è un'affermazione troppo larga.** Dice che la verifica ha controllato «su una pagina ufficiale, ogni cartella e ogni riga di codice che accende il profilo». Nel rapporto `server/**`, `backend/**`, `**/routes/**` e `**/handlers/**` hanno come fonte il catalogo e il progetto di B (cioè la scelta dell'utente), non una pagina ufficiale. Correzione: «ogni cartella e ogni riga di codice ha una fonte: una pagina ufficiale, oppure il catalogo e il progetto di B per `server/`, `backend/`, `routes/` e `handlers/`».

### Minor

- **M-1. Termini non spiegati nella pagina** (obiettivo «persona non tecnica»): «edge function» (riga 31), «namespace» e «bucket» (riga 63), «lanciatore come `npx`» (riga 63), «orchestratore di monorepo» (riga 75), «gestore» di rotta (righe 23, 33), `tollgate.toml`. Basta una mezza frase ciascuno. La riga della regola 2 (riga 43) è molto lunga per una cella.
- **M-2. Intestazione del rapporto** (`backend-fonti.md`, paragrafo iniziale) dice che delle pagine ufficiali «si prendono i fatti con parole nostre e nessun testo», mentre le tabelle citano righe di quelle pagine (ammesso dai vincoli globali: una riga, nel solo rapporto). Riformulare: «nella skill e nella pagina solo fatti con parole nostre; il rapporto cita al più una riga».
- **M-3. `test_page_has_no_private_data`** (`tests/test_rules_backend.py`, ultimo test) controlla solo `/home/`; il brief parla di nome utente, host, nomi di progetti, token. Aggiungere almeno `/Users/`, `@` con dominio e prefissi di token noti, oppure dire nel report che il controllo vero è a mano.
- **M-4. Codice morto:** `RulesBackendPageTest.sources_main` non è usato da nessun test (`tests/test_rules_backend.py`); rimuoverlo o usarlo.
- **M-5. Test deboli:** `test_page_explains_what_changes` usa regex come `KV e R2[^.]*`--local`` e `D1[^.]*`--remote`` che passerebbero anche con frasi contrarie; non copre la frase del rinvio (I-1) né la distinzione `--remote`/`--preview`. `test_page_brings_the_open_choices_to_the_user` cerca `monorepo` e `alla radice` ma non `supabase/` nel punto 9. Aggiungere `supabase/` ai needle.
- **M-6. Rapporto:** «Regole tolte» contiene la frase «Nessun pattern e nessuna voce di esclusione escono»; è corretta, ma il rapporto non riporta la nota di forma sulla licenza di `cloudflare/skills` (copia di `LICENSE` ora presente, carry riga 29) né l'esito dei controlli sulla somma di controllo come righe verificabili. Facoltativo.

## Valutazione

**Qualità del task:** Da correggere.

**Motivo:** i requisiti di rapporto, regole, frammento e «Da decidere tu» ci sono e sono costruiti bene, ma la pagina che l'utente approverà ha quattro affermazioni non vere o incomplete (il rinvio, la frase finale di «Quando si accende», il riepilogo delle regole tolte, la copertura «su una pagina ufficiale»). Sono correzioni di testo e di un test, senza toccare skill o frammento.
