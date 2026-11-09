# Brief per la sessione che scrive il piano di B5 (profilo `backend`)

Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa scrivere
Quattro file, con la data di oggi nel nome, sul modello di quelli di B4 (`docs/superpowers/plans/2026-11-06-tollgate-b4-profilo-infra.md`, `-esecuzione.md`, `-brief-sessione.md`, `-brief-goal.md`):
- il piano di B5, con «Fatti verificati», «Global Constraints», «Decisioni di questo piano», «Review Focus», «Copertura» e i task con firme e test (non il codice);
- le istruzioni d'esecuzione (dove lavorare, scan pre-flight, ordine e modelli, regole di cautela con le sole eccezioni del controller, quando fermarsi e chiedere, chiusura);
- il brief della sessione che lo eseguirà, con la sezione «Il lavoro è finito quando»;
- il brief corto per l'obiettivo (`/goal`) della sessione d'esecuzione, con la sezione «Finito quando». Le condizioni devono essere verificabili leggendo file e il transcript, senza interpretazioni: per esempio «il rapporto all'utente prima del merge contiene l'elenco completo delle `Ruling:` con il costo e dei minori rinviati, uno per riga» e «dopo il merge l'utente riceve un rapporto di chiusura». La chiusura di B4 è rimasta bloccata a lungo perché la condizione sul rapporto si poteva leggere in due modi.

Solo documenti: nessun codice, nessun `claude -p`, nessun eval. Rete solo per leggere con `WebFetch` le pagine ufficiali delle fonti di `rules-backend`, per verificare che esistano e cosa dicono. Lavora su `main`, un commit per ogni giro di revisione, niente push.

## Da leggere
1. Il progetto di B `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, per intero: è l'autorità. Per `backend`: riga della sezione 3.4 («leggi i contratti esistenti (tipi, schemi, rotte) prima di aggiungerne; per Supabase edge function e Cloudflare Worker, la documentazione del runtime»), sezione 4 (livello minimo **L0**: per i lavori piccoli solo l'avviso; va coperto anche il backend locale senza Supabase), sezione 5 (come nascono le regole e l'approvazione dell'utente), sezione 11 (il codice dei Worker di Cloudflare è `backend`).
2. Il catalogo dei profili `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`: le voci di `backend` (percorsi `api/**`, `server/**`, `**/routes/**`, `**/handlers/**`, `**/services/**`; skill; agenti; `dod` «test delle API, typecheck»; fonti e licenze di `rules-backend`; il rapporto con `rules-performance`).
3. Il piano principale `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2 (riga B5), 3 (righe B3 → B4-B7 e **B4 → B5-B7**: `parse_pattern`, `concrete_for`, `DOC_EXTENSIONS`, `EXCLUDED_PREFIXES`, `load_approved`, `launcher_candidates`, `AREAS`, `rules(text, area)`), 9 (i blocchi «A B4-B7, da B3», «A B4-B8, da B3-bis» e **«A B5-B8, da B4»**: scritture remote di `wrangler kv`, `d1`, `r2`; rilevamento per contenuto solo nei sorgenti; buchi della scansione dei lanciatori e degli script `deploy` nei monorepo; test da copiare con il prefisso `test_real_`; prove reali con `spikes/run-b1-flow.sh`), 13 («Prove di B4»).
4. La spec del nucleo, revisione 31: 6.3, 7.1, 7.3, 8.5, 8.7, 11.2, 11.4, 16, 18.4.
5. Il registro di B4 `docs/sdd/2026-11-06-tollgate-b4-profilo-infra/` (`README.md`, `progress.md`, `final-review.md`, `carry.md`, `preflight-scan.md`, `task-5-fonti-brief.md`, `task-9-rapporto-brief.md`): il metodo più recente, con le lezioni sotto. Per confronto quello di B3 `docs/sdd/2026-11-01-tollgate-b3-profilo-ai/`.
6. Gli esempi da copiare: `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml` e `ai.toml`, `docs/profili/infra.md`, `docs/profili/verifiche/infra-fonti.md`, `agents/implementer-infra.md`, `agents/reviewer-infra.md`, `tests/test_rules_infra.py`; il caso `infra` di `spikes/run-b1-flow.sh` e `spikes/b4/flow/`.
7. La memoria del progetto (`plugin-workflow-decisioni.md`, voce di B4; `feedback-domande.md`, `feedback-spiegazioni-semplici.md`).

## Scelte dell'utente, da non riaprire
- `backend` copre API e server, anche il backend locale senza Supabase; livello minimo L0 (progetto, sezione 4).
- Il codice dei Worker di Cloudflare è `backend`; `infra` copre la configurazione di Wrangler e il deploy (progetto, sezione 11).
- Le regole nascono così: bozza con la fonte per ogni regola, verifica delle fonti da un agente di sola lettura, una pagina in parole semplici per l'utente, che approva, corregge o toglie; solo le regole approvate entrano; senza approvazione il profilo non si propone (progetto, sezione 5).
- I comandi di servizio lanciati con `npx` chiedono l'approvazione (progetto, sezione 11; fatto in B4).
- Il repo `ginz0ls/tollgate` è pubblico: dalle pagine dei fornitori si prendono fatti con parole nostre, mai testo intero; niente nomi di progetti privati dell'utente, niente nome utente né host, niente token.

## Da decidere nel piano
- I pattern di `backend`: le forme `folder` del catalogo (`**/routes/**`, `**/handlers/**`, `**/services/**`) e `root_folder` (`api/**`, `server/**`); dove sta il codice dei Worker (nessun nome di cartella fisso: `src/index.ts` accanto a `wrangler.jsonc`?) e se serve un rilevamento per contenuto (`export default { fetch` , `cloudflare:workers`, `Deno.serve`, `express()`, `fastify(`…) con le estensioni di `init.SOURCE_EXTENSIONS`; i falsi positivi di `**/services/**` nei progetti frontend.
- Il rapporto con `infra` e con `database` (B7): un task che tocca `wrangler.jsonc` e il codice del Worker è misto (agente generico); le edge function di Supabase sono `backend` o `database`?
- Le scritture remote di `wrangler kv`, `d1`, `r2` (rinvio di B4): quali comandi diventano effetti esterni (`_DEFAULT_EFFECTS`, voci di tre parole), con i fatti dalle pagine ufficiali di Wrangler.
- Il `dod` di `backend` («test delle API, typecheck» nel catalogo): come in B4 il comando dipende dal progetto; se resta vuoto, la pagina dice come aggiungerlo.
- Le skill del catalogo (`agent-skills:api-and-interface-design`, `observability-and-instrumentation`): precaricate, nominate in «Dove informarsi» o fuori (decisione 8 di B4); il rapporto con `rules-performance`.
- Se B5 è abbastanza piccola da unirla a B6 (piano principale, sezione 2).
- Dove la sessione d'esecuzione si ferma per l'approvazione delle regole (in B4 era il Task 6).
- Quali rinvii della sezione 9 si chiudono qui (per esempio i due test senza `test_real_`, la riga del piano principale sul `.gitignore` di `spikes/b4/flow/`, già corretto dalla correzione finale di B4).

## Lezioni di B4 da mettere nel piano e nelle istruzioni
- Le evidenze di `claude -p` contengono anche `Read` e `Grep` sulle copie salvate delle pagine (`tool-results/`): `flowreg togli-pagine` ora le toglie, ma il rapporto della prova va scritto dopo averlo verificato.
- Nella prova reale il modello può scrivere da sé il piano già nel passo 1: il report dell'implementatore allora non prova il precaricamento delle regole. Il piano della prova dice come distinguerlo (rilievi del revisore su regole che il task non nomina).
- Gli implementatori si fermano spesso dopo la suite in background: il brief dice di leggere da soli l'uscita e committare; il controller sollecita.
- Una ruling che toglie elementi da un elenco di eccezioni del veto (come `PACKAGE_COMMANDS`) va controllata contro i nomi comuni di cartelle e pacchetti dei monorepo.

## Come lavorare
- Le scelte vere (compromessi, costi) si chiedono all'utente in parole semplici, con il costo esplicito (gratis, consumo dell'abbonamento o spesa vera) e un consiglio. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere. Il resto si decide con una `Ruling:` scritta nel piano.
- Revisione del piano da opus a contesto pulito, in sola lettura, a giri, finché un giro dice «pronto» con 0 critical e 0 important. La tabella dei giri va in fondo al piano.
- Le regole di cautela vanno nel brief di ogni subagente, al lancio.

## Finito quando
- I quattro file esistono su `main`, committati.
- L'ultima riga della tabella dei giri del piano dice «pronto», 0 critical, 0 important.
- `plugin-workflow-decisioni.md` nella memoria ha una voce sul piano di B5.
- L'utente ha ricevuto, in italiano semplice, nell'ultimo messaggio della sessione: cosa fa B5, le scelte che gli sono state chieste e cosa ha risposto, quanto costerà eseguirlo, quando dovrà approvare le regole, e la riga `/goal` pronta per la sessione d'esecuzione.
