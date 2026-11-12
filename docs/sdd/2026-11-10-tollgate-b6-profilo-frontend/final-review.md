# Revisione finale del ramo B6 (profilo `frontend`)

Revisore a contesto pulito, sola lettura. Ramo `b6-profilo-frontend`, `f3ca4a2..ab847d6` (13 commit), worktree pulito alla fine (`git status` vuoto). Sonde in `$CLAUDE_JOB_DIR/tmp/final/` (`sonda.py` e una seconda in linea), con i frammenti veri copiati in una radice temporanea come fa `_real_fragments_root`. Test mirati lanciati: `tests.test_rules_frontend`, `tests.test_init.FrontendPrecedenceTest`, `tests.test_fragments` e `tests.test_profiles` (141 test, OK, 3 saltati). Nessuna suite completa, nessuna rete, nessun programma della lista vietata.

## 1. Verdetto

**Pronto per il merge.** Critical 0, Important 0, Minor 4.

Il codice del nucleo è piccolo e corretto: la forma `ext` è riconosciuta in un solo punto, si prova per ultima in `_match`, rispetta le maiuscole come `globs.match` e non si accende sui documenti. Le dodici regole hanno ciascuna una fonte, le sei di accessibilità (05-10) citano ognuna almeno un criterio WCAG 2.2 con numero, nome e livello, e nessuna `[blocca]` si giudica sulla nota. Gli agenti differiscono dai generici solo per frontmatter e sezione d'area (l'attribuzione resta quella del generico). Nelle evidenze non ci sono dati dell'utente né testo di terzi oltre al riassunto di `WebFetch` già dichiarato nel rapporto. I quattro rilievi sotto sono precisazioni di testo, nessuno cambia il comportamento.

## 2. Rilievi

### M1 (Minor). Il divieto di `node`/`npm` per `implementer-frontend` non dice come si lanciano i test (giudizio sulla `Ruling:` della riga 78)

- **Dove:** `agents/implementer-frontend.md:53`; `final-rulings.md`, riga 78.
- **Cosa:** la sezione dice «Non lanci `node`, `npm`, `npx`… Verifichi con i test del progetto». In un progetto JavaScript i test si lanciano proprio con `npm` o `npx`, e la frase non dice come farlo. Il corpo generico dello stesso agente chiede poi di lanciare il test mirato a ogni giro (riga 50: TDD; riga 4 della sezione «Il lavoro»: «Mentre iteri lancia il test mirato»). La strada c'è già: `<programma> verify` (e `verify --related`, se il progetto ha `test_related`) lancia i comandi del gate del progetto, anche `npm test`, sotto il controllo di tollgate. Il brief lo chiede comunque prima di DONE (`brief.py:153`). La prova reale l'ha usata (`tollgate verify` nei comandi del modello). La motivazione della `Ruling:` («si affida ai comandi del `dod`») è imprecisa: il `dod` di `frontend` è vuoto per decisione 8, mentre il canale vero è `verify`.
- **Scenario:** progetto Vite + Vitest con `[commands] verify = "npm test"`, task solo sui componenti. L'implementatore `frontend` legge il divieto e non lancia `npx vitest run src/Button.test.tsx`. Può saltare il RED, scrivere il test e il codice insieme e lanciare `verify` solo alla fine. Il cancello finale tiene, perché `verify` gira comunque, ma il ciclo RED/GREEN che l'agente dichiara nella `description` non avviene.
- **Giudizio sulla `Ruling:`:** **costo accettabile, non un difetto.** Il divieto chiude i server di sviluppo, i browser e gli scaricamenti di pacchetti. I test restano possibili attraverso `verify`. Manca solo la frase che lo dice.
- **Correzione:** al posto di «Verifichi con i test del progetto» scrivere che i test del progetto si lanciano con `<programma> verify` (con `--related` per quelli del task, se il progetto lo configura), anche quando sono comandi `npm`. Correggere anche la motivazione nella `Ruling:` (o nel piano principale). `test_real_frontend_agent_names_forbidden_tools` resta verde, perché cerca solo i nomi.
- **Scelta dell'utente:** no. È la decisione 15 e il Task 6, Step 3, del piano; il progetto di B (3.4, 13) non ne parla e la pagina approvata non la nomina.

### M2 (Minor). Il rimedio di `routes/` (P9) non vale in un progetto che ha già il blocco `backend` di B5

- **Dove:** `docs/profili/frontend.md:67`; tabella della decisione 4 (spec 6.3, P1-P38); `bin/tollgate_flow/init.py:326` (`_drift` propone solo aggiunte di `paths`).
- **Cosa:** la pagina dice che un modulo di rotta trovato per contenuto «non tiene la cartella `routes/` a `backend`: la cartella resta fuori da `backend`». Vale solo per un `backend` proposto nella stessa corsa. Se il `tollgate.toml` ha già `[profiles.backend]` con `src/routes/**`, scritto da `init` prima di B6, `init --update` propone `frontend` con `**/*.tsx` ma non dice di togliere `src/routes/**` da `backend`. A runtime i moduli di rotta restano a `backend`.
- **Scenario (sonda N1):** `src/routes/index.tsx` e `src/routes/about.tsx` con l'import del router, `backend` già dichiarato con `src/routes/**`. Il risultato è `frontend: ["**/*.tsx"]`, e a runtime tutti e due i file vanno a `backend`. `init` lo segnala con una riga («`src/routes/about.tsx` corrisponde anche a «backend»: vince backend»), ma la pagina e la tabella non nominano questo caso. Chi aggiorna un progetto di B5 legge che il rimedio è automatico e trova il contrario. Il «Per correggere basta toglierla a mano» della stessa riga 67 lo copre solo per il caso del file senza import.
- **Correzione:** una riga P39 nella tabella della spec (6.3), con il test `test_real_precedence_p39` (`DEFAULT_TOML` più il blocco `backend` di B5). Una frase nella pagina, alla prossima revisione con l'utente: con `backend` già dichiarato la cartella si toglie a mano, e `init` lo segnala con «vince backend». In alternativa, `_drift` potrebbe proporre «togli» per una cartella di `backend` i cui file sono tutti trovati da `frontend`, ma questo è codice nuovo, da B7 in poi.
- **Scelta dell'utente:** tocca il testo della pagina approvata (la riga 67 descrive il rimedio); la scelta di P9 resta com'è. È lo stesso caso delle «pagine approvate che invecchiano» (decisione 16), e il piano principale lo tiene aperto.

### M3 (Minor). «`init` scrive i blocchi in ordine alfabetico» vale solo dentro una corsa

- **Dove:** spec 6.3, riga 483 («vince quello che viene prima nell'alfabeto, `backend` su `frontend`»); `docs/profili/frontend.md:161` (punto 18: «`init` scrive i blocchi in ordine alfabetico: va a `backend`»); P37.
- **Cosa:** con `init --update` un profilo nuovo va **in coda** al `tollgate.toml`, dopo quelli già dichiarati. A parità di percorso esatto vince quindi l'ordine di aggiunta, non l'alfabeto.
- **Scenario (sonda N13):** `frontend` già dichiarato (`**/*.tsx`), poi compare `src/lib/chatRoute.ts` con l'import del router e quello di un SDK dei modelli. `init --update` propone il blocco `ai` (in coda) e la riga «`[profiles.frontend] paths: aggiungi "src/lib/chatRoute.ts"`». Applicate tutte e due, l'ordine è `frontend`, `ai` e il file va a `frontend`, non ad `ai`. Lo stesso vale per P37 se `backend` arriva dopo `frontend` (un `src/lib/server.ts` con `express` e il router comparso più tardi): il punto 18 della pagina dice `backend`, il runtime dà `frontend`. Né la corsa né il runtime segnalano la parità.
- **Correzione:** nella spec 6.3 e in P37, «il primo dichiarato; in una sola corsa `init` scrive i blocchi in ordine alfabetico, con `--update` li aggiunge in coda». Il punto 18 della pagina si corregge alla prossima revisione con l'utente.
- **Scelta dell'utente:** tocca il testo del punto 18 della pagina approvata, non la scelta.

### M4 (Minor). `docs/uso/comandi.md:167` dice «Le caricheranno»

- **Dove:** `docs/uso/comandi.md:167`, sezione `/tollgate:rules-frontend`.
- **Cosa:** il futuro è rimasto dal Task 3, quando gli agenti non esistevano ancora. Ora ci sono (Task 6), e le sezioni di `ai`, `infra` e `backend` (righe 155, 159, 163) dicono «Le caricano».
- **Correzione:** «Le caricano gli agenti dell'area `frontend`». **Scelta dell'utente:** no.

Controllati senza rilievo (punti chiesti dal brief):

- **File sotto `.github/tollgate/`, `.claude/` o la cartella della proposta che fa proporre `frontend`:** nessuno (N6). A runtime li copre `**/*.tsx`, ma solo se altri file l'hanno fatto proporre: è il costo scritto di P36 e del punto 13. I file che `install.files` mette nel repo sono solo `.py`, `.yml` e tre senza estensione, quindi nessuno ha un'estensione di `frontend`.
- **Estensione in maiuscolo:** `src/Foo.TSX`, `A.CSS`, `README.MD` e `x.MDX` non accendono niente, né nella proposta né a runtime (N7). Un documento non accende mai `ext` (`_is_doc` abbassa le maiuscole, `_match` salta `ext` per i documenti).
- **Marcatori su test, documenti o codice di tollgate:** nel repo i marcatori compaiono solo in tre documenti (che il rilevamento non guarda: `SOURCE_EXTENSIONS`), nel frammento (`.toml`, non guardato) e in `spikes/b6/flow/src/routes/home.tsx` (il progetto di prova, voluto). In `bin/` non c'è nessun marcatore (`test_real_markers_not_in_tollgate_bin`), e `from 'react-router'` non è contenuto in `from 'react-router-dom'`.
- **`routes/` di server portata a `frontend` dal rimedio:** solo se il file importa una libreria di rotte d'interfaccia (P23 e P34, costi scritti). Una `routes/` d'interfaccia che resta a `backend` fuori dai costi scritti c'è solo nel caso di M2.
- **`tollgate.toml` dell'utente riscritto:** no. `profile_blocks` aggiunge in coda e su un profilo già dichiarato dà solo righe (N1, N9, N13).
- **`[blocca]` sulla sola nota:** nessuna. Le `[blocca]` sono 01-09 e 11, e si giudicano tutte sul diff o sul report.
- **Regola di accessibilità senza criterio WCAG:** nessuna (05: 2.1.1 e 4.1.2; 06: 1.1.1 e 4.1.2; 07: 1.3.1 e 3.3.2; 08: 2.4.7; 09: 4.1.3; 10: 2.4.3 e 2.1.2).
- **Test che dipendono dai file veri senza `test_real_` o dalle variabili della macchina:** quelli nuovi di `test_init`, `test_fragments`, `test_profiles`, `test_taskcmd` e `test_check_task_verdict` usano plugin temporanei o blocchi scritti nel test, mentre quelli sui frammenti veri hanno il prefisso. `test_page_has_no_private_data` confronta nome utente e host con `assertFalse(re.search(...), "<messaggio fisso>")`. Restano gli `assertIn` su `r.stdout` con `{ROOT}` (`tests/test_b1_scripts.py:1678`), che se falliscono stamperebbero il percorso del checkout. Lo stesso schema c'è già per B1-B5 (righe 653, 1177, 1184, 1350, 1525) e non esce dalla macchina, quindi non lo apro come rilievo.
- **Testo di terzi, token e dati dell'utente nelle evidenze:** nome utente, host, `/home/`, `sk-ant`, `ghp_`, `github_pat_` e i nomi delle cartelle private compaiono 0 volte in `evidenze/b6/flusso/` (conteggi senza stampare i valori). Nessun `Read`, `Grep` o `Bash` punta a `tool-results/`. L'unico `WebFetch` restituisce 1.238 caratteri, un riassunto del modello già dichiarato nel rapporto («Limiti»).
- **Agenti d'area:** `diff` di `implementer.md` contro `implementer-frontend.md` e di `task-reviewer.md` contro `reviewer-frontend.md`. Cambiano solo `name`, `description`, `skills`, `tools` (il revisore ha in più `WebFetch`) e la sezione «Area `frontend`». `READONLY_TYPES`, `readonly_agents`, `final-reviewer.md` e `finding-verifier.md` sono allineati con `backend`.
- **Coerenza:** codice, pagina, skill (12 regole, 10 `[blocca]`, 6 di accessibilità), frammento (9 pattern, 8 marcatori, 6 prefissi esclusi), agenti, `comandi.md` (salvo M4) e spec rev 33 (6.3, 11.2, 11.4, 16) coincidono. Le frasi rimaste false nel piano principale e nel catalogo sono già tra i minori rinviati 24 e 25 (vedi triage).

## 3. Casi di precedenza cercati

Sonda: `init.profile_blocks` con i quattro frammenti veri (`ai`, `backend`, `frontend`, `infra`) copiati in una radice temporanea con una skill approvata finta per ciascuno, `detected` dato dalla sonda (senza i file sotto un `exclude`). Poi `profiles.vertical_for` su ogni file, con i blocchi proposti aggiunti al `tollgate.toml` corrente.

| Caso | File (marcatore) | Proposta | Runtime | Esito |
|---|---|---|---|---|
| N1 | `backend` già dichiarato (B5) con `src/routes/**`; `src/routes/index.tsx`, `about.tsx` (router) | `frontend: **/*.tsx`; `backend` invariato, nessuna riga «togli» | tutti e due → `backend` | **nuovo**, non nella tabella: rilievo M2 |
| N2 | `src/lib/chatRoute.ts` (SDK dei modelli e router), `src/main.tsx` | `ai`: percorso esatto; `frontend`: `**/*.tsx` più lo stesso percorso esatto | `chatRoute.ts` → `ai` (parità, primo blocco) | come P37 con `ai` al posto di `backend`, coerente in una sola corsa; la variante con `--update` è N13 |
| N13 | come N2, ma `frontend` già dichiarato e `ai` aggiunto con `--update` | `ai` in coda; riga «aggiungi `src/lib/chatRoute.ts`» a `frontend` | `chatRoute.ts` → `frontend` | **nuovo**: smentisce «ordine alfabetico» della spec 6.3 e del punto 18, rilievo M3 |
| N3 | `web/index.html`, `web/prompts/system.ts`, `web/routes/home.ts`, `web/handlers/x.ts` | `ai: web/prompts/**`; `backend: web/handlers/**, web/routes/**`; `frontend: /web/**` | `ai`, `backend`, `backend`, `frontend` per `index.html` | coperto (punto 17, variante XB di P10; P28 per `prompts/`) |
| N4 | monorepo `apps/web/src/components/Button.tsx`, `apps/web/src/App.tsx`, `apps/api/src/index.ts`, `apps/api/src/components/Mail.tsx` | `frontend: **/*.tsx`, `apps/api/src/components/**`, `apps/web/src/components/**` | `Mail.tsx` → `frontend`; `index.ts` → nessuno | coperto (decisione 7: `exclude` vale alla radice, `apps/api/` non è coperta; punto 10) |
| N5 | `app/main.py`, `htmlcov/style.css`, `htmlcov/index.html` | `frontend: **/*.css` | `style.css` → `frontend` | coperto (D5, punto 22) |
| N6 | solo `.github/tollgate/x.css`, `.claude/skills/a/t.tsx`, `docs/superpowers/tollgate-init/files/x.tsx`, `app/main.py` | nessuna | nessuno | coperto (P16) |
| N7 | `src/Foo.TSX`, `src/styles/A.CSS`, `src/components/README.MD`, `docs/x.MDX` | nessuna | nessuno | coperto (P17, P18) |
| N8 | `src/ai/agent.py`, `src/ai/components/Chat.tsx`, `src/ai/routes/chat.ts` (router) | `ai: src/ai/**`; `frontend: src/ai/components/**`, `src/ai/routes/chat.ts` | `Chat.tsx` e `chat.ts` → `frontend` | coperto (P4, P26) |
| N9 | `frontend` dichiarato a mano `src/**`; `src/App.tsx`, `server/app.tsx`, `server/app.py` | `backend: /server/**`; `frontend` invariato | `server/*` → `backend`, `App.tsx` → `frontend` | nuovo, esito voluto |
| N10 | `src/components/Button.tsx`, `src/components/vercel.json`, `web/Dockerfile`, `web/index.css` | `infra`: due percorsi esatti; `frontend: /web/**, src/components/**` | `vercel.json` e `Dockerfile` → `infra` | nuovo, esito voluto (percorso esatto contro cartella, come P12) |
| N11 | `netlify/functions/ssr.ts` (router), `src/main.tsx` | `frontend: **/*.tsx`, `netlify/functions/ssr.ts` | `ssr.ts` → `frontend` | coperto (decisione 5: un `.ts` col router fuori dalle cartelle alla radice dei server va a `frontend`; punto 11) |
| N12 | `web/routes/home.tsx` (router), `web/routes/utils.ts`, `web/index.html` | `backend: web/routes/**`; `frontend: /web/**` | `home.tsx` → `backend` | coperto (punto 17) |

## 4. Triage dei minori rinviati (`final-deferred.md`)

| N. | Voce (in breve) | Esito | Motivo |
|---|---|---|---|
| 1 | `comandi.md:124` «tre forme» | nessuna azione | Già corretto nel Task 3: la riga ora dice «quattro forme» e spiega la forma per estensione. |
| 2 | f-string spezzata nel messaggio di `_parse` | nessuna azione | Solo estetica; il messaggio è giusto e lo provano i test. |
| 3 | `_concrete_paths` tiene un percorso esatto acceso da `name` anche se un `ext` proposto lo copre | rinviato | B7: nessun frammento di oggi ha insieme `name` ed `ext`. `database` potrebbe averli (`**/*.sql` con un nome): lì si toglie il ridondante con `globs.match_any` sui pattern `ext` proposti. |
| 4 | Lookahead di `SAVED_PATH` cieco alla sola cartella seguita da `,` `}` `]` `:` `\` | rinviato | B7, prima della prossima prova reale: è il lato non sicuro della pulizia delle evidenze. Le evidenze di B6 sono controllate (nessun `Bash` su `tool-results/`). |
| 5 | Test di `togli-pagine`: un solo prefisso dei sei, mancano i negativi e `stdout` più `stderr` insieme | rinviato | B7, insieme alla voce 4: stesso codice, stessi test. |
| 6 | Percorso tra virgolette con spazi: nome troncato nel segnaposto | nessuna azione | Solo estetica; il testo è tolto comunque. |
| 7 | Il report del Task 2 non riporta l'uscita di RED/GREEN | nessuna azione | Riguarda un report del processo, già chiuso; la suite è verde. |
| 8 | R-FRONTEND-12 con esempi che le fonti non dicono così | nessuna azione | Corretto nel Task 4 (ruling della riga 54): ora «viola o indaco ovunque, gradienti in eccesso, schede tutte uguali». |
| 9 | `test_a11y_rules_name_a_wcag_criterion` non controlla il nome del criterio | nessuna azione | Numero e livello sono legati alla tabella `WCAG`; i nomi li ha controllati il verificatore delle fonti e le regole sono approvate. |
| 10 | R-FRONTEND-07: `aria-label` contro etichetta visibile | nessuna azione | Portato nella pagina (punto 6) e approvato dall'utente. |
| 11 | R-FRONTEND-11 cita «Component Architecture» | nessuna azione | Confermato dal verificatore. |
| 12 | `test_removed_sources_are_not_in_the_skill`: ciclo vuoto, la docstring promette di più | da correggere | Far dire alla docstring che il ciclo vale quando il rapporto avrà righe `no` e che oggi contano i quattro `assertNotIn`. Una riga. |
| 13 | La pagina usa «l'utente» sia per chi usa il sito sia per chi legge | nessuna azione | La pagina è approvata e nel contesto si legge bene («tu» per chi legge); si riprende alla prossima revisione con l'utente. |
| 14 | `assertIn`/`assertNotIn` che stampano una sezione della skill | nessuna azione | File pubblico senza dati privati; vale la regola dei soli valori segreti. |
| 15 | Righe oltre 100 caratteri e rientri nelle `re.search` | nessuna azione | Il repo non ha un controllo di lunghezza; solo stile. |
| 16 | Test «prima dell'approvazione» sempre saltati | nessuna azione | Stesso schema di B5 (`test_rules_backend.py:459`); documentano lo stato prima dell'approvazione. |
| 17 | `test_page_records_the_choices` conta le frasi, non confronta il testo | nessuna azione | La pagina è approvata e congelata; il diff del Task 5 copre il resto. |
| 18 | `test_rules_frontend_not_required` vero su un blocco con `skills = []` | nessuna azione | Stesso schema di `backend`; la garanzia vera (`skills = []` nel frammento) la dà `test_fragment_matches_decisions`. |
| 19 | `test_real_frontend_agent_names_forbidden_tools` cerca i nomi nella sezione, non nella frase | nessuna azione | Nella sezione i nomi compaiono solo nella frase del divieto; resta vero anche dopo la correzione di M1. |
| 20 | Due «e» di fila in `final-reviewer.md:37` e `finding-verifier.md:13` | da correggere | «… le `R-INFRA-…` che `rules-infra`, le `R-BACKEND-…` che `rules-backend` e le `R-FRONTEND-…` …»: una virgola, controllando gli `assertIn` di `test_manifest.py` che fissano la frase. |
| 21 | `test_real_flow_case_frontend_project_verifies` confronta il `tollgate.toml` con quello di B1 | nessuna azione | Riguarda solo i progetti di prova; se il B1 cambia, il test fallisce in modo leggibile. |
| 22 | Due righe vuote in più in `test_b1_scripts.py` (~1819) | nessuna azione | Solo stile. |
| 23 | Test dei limiti di `backend` che legge i file veri senza `test_real_` | nessuna azione | Già rinominato nel giro 1 del Task 7: è `test_real_scrivi_limiti_heading_is_generic_backend` (riga 1955). Quello generico della riga 1948 usa il caso B1 con le regole finte, come il resto del file. |
| 24 | Piano principale, sezione 9 (~riga 207): «la forma con `*` iniziale resta rifiutata» | da correggere | Scrivere che da B6 `**/*.<estensione>` è ammessa (forma `ext`) e restano rifiutate le altre forme con `*` iniziale. Lo stesso nella riga di contratto di B4 (riga 53: «resta rifiutata… (e B6 per `frontend`)»). |
| 25 | Catalogo, sezione 2: «`init` non li copia così come sono» senza la deroga accanto | da correggere | Aggiungere subito la parentesi della spec 11.2 («per le forme a cartella e a nome; la forma `ext` è l'eccezione: il percorso proposto è il pattern stesso»), come chiedeva D10. |
| 26 | Spec 16 e piano principale 15 non citano il `tollgate plan-check` inesistente né che il task 1 non prova il precaricamento; «Stato (10 novembre 2026)» | da correggere | Una frase in ciascuna riga dei risultati (il comando inesistente e senza effetto; il task 2 come testimone pulito) e la data dello stato all'11 novembre. |
| 27 | Sezione 9 del piano principale: due voci con «Stato dopo B6» non in testa | da correggere | Spostarlo in testa, come dice la convenzione scritta nella stessa sezione («Stato dopo B4 in testa a ogni voce»). |
| 28 | Rapporto della prova: il punto sul task 1 cita «stream, riga 147» senza dire che è lo stream del passo 2 | da correggere | In `docs/verifiche/2026-11-10-b6-prova-flusso.md` scrivere «stream del passo 2 (`passo2/tentativo-1/claude.jsonl`), riga 147». Il rapporto cita anche lo stream del passo 1, quindi senza il passo il numero di riga non si ritrova. Una parola. |

Conteggio: `da correggere` 7 (12, 20, 24, 25, 26, 27, 28), `rinviato` 3 (3, 4, 5), `nessuna azione` 18.

## 5. Punti di forza

- La forma `ext` è minima e tiene in un solo posto la scelta più delicata: zero segmenti letterali, quindi perde sempre contro cartelle e file degli altri profili. Le sonde N3, N9 e N10 lo confermano anche su casi fuori dalla tabella.
- La tabella delle precedenze (P1-P38) ha un test per caso con i frammenti veri, e i costi sono portati all'utente con parole semplici nella pagina approvata (22 punti).
- `[detect] exclude` sulle cartelle alla radice dei server chiude in modo pulito i rilievi I2 e I3 del giro 1. `test_real_exclude_matches_root_folders_of_other_fragments` lega le cartelle escluse ai frammenti di `backend` e `infra`, così non possono andare fuori sincrono.
- Nelle regole ogni obbligo senza fonte è stato tolto invece di cercargli una fonte nuova. Lo stato di «Using ARIA» (bozza sospesa) è dichiarato e un test lo vigila.
- La prova reale è riuscita al primo tentativo e il rapporto è onesto: dice che il piano del passo 1 non è un testimone pulito e sposta la prova del precaricamento sul task 2 e sui titoli `isMeta`.
- `togli-pagine` ora sbaglia dalla parte sicura per ogni `Bash` sulle copie salvate, anche su `stderr`.
