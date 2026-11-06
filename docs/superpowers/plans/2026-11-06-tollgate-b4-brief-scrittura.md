# Brief per la sessione che scrive il piano di B4 (profilo `infra`)

Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa scrivere
Tre file, con la data di oggi nel nome, sul modello di quelli di B3 (`docs/superpowers/plans/2026-11-01-tollgate-b3-profilo-ai.md`, `-esecuzione.md`, `-brief-sessione.md`) e di B3-bis (`2026-11-04-tollgate-b3bis-*.md`):
- il piano di B4, con «Fatti verificati», «Global Constraints», «Decisioni di questo piano», «Review Focus», «Copertura» e i task con firme e test (non il codice);
- le istruzioni d'esecuzione (dove lavorare, scan pre-flight, ordine e modelli, regole di cautela con le sole eccezioni del controller, quando fermarsi e chiedere, chiusura);
- il brief della sessione che lo eseguirà, con la sezione «Il lavoro è finito quando».

Solo documenti: nessun codice, nessun `claude -p`, nessun eval. Rete solo per leggere con `WebFetch` le pagine ufficiali delle fonti di `rules-infra` (Vercel, Cloudflare e le altre che il catalogo nomina), per verificare che esistano e cosa dicono. Lavora su `main`, un commit per ogni giro di revisione, niente push.

## Da leggere
1. Il progetto di B `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, per intero: è l'autorità (sezione 4: `infra` livello minimo L1, va aggiunto **Vercel**; sezione 5: come nascono le regole e l'approvazione dell'utente).
2. Il catalogo dei profili `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`: le voci di `infra` (percorsi, skill, agenti, `dod`, fonti e licenze).
3. Il piano principale `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3 (interfacce B3 → B4-B7), 9 (i rinvii «A B4-B7, da B3» e «A B4-B8, da B3-bis»: forma dei pattern, prefisso `R-INFRA-`, rilevamento per contenuto che oggi guarda solo i file sorgente, agenti da derivare, test da copiare, le piccole cose rimaste aperte in `fragments` e `init`).
4. La spec del nucleo, revisione 30: 6.3, 7.1, 7.3, 11.2, 11.4, 16, 18.4.
5. Il registro di B3 `docs/sdd/2026-11-01-tollgate-b3-profilo-ai/` (`README.md`, `progress.md`, `final-review.md`): il primo profilo, con la scrittura delle regole, la verifica delle fonti e l'approvazione dell'utente. E quello di B3-bis `docs/sdd/2026-11-04-tollgate-b3bis-sentinella-modelli/` per il metodo più recente.
6. Gli esempi da copiare: `skills/rules-ai/SKILL.md`, `templates/profiles/ai.toml`, `docs/profili/ai.md`, `docs/profili/verifiche/ai-fonti.md`, `agents/implementer-ai.md`, `agents/reviewer-ai.md`, `tests/test_rules_ai.py`.
7. La memoria del progetto (`plugin-workflow-decisioni.md`, `feedback-domande.md`, `feedback-spiegazioni-semplici.md`).

## Scelte dell'utente, da non riaprire
- `infra` copre deploy, Vercel, Cloudflare e server; livello minimo L1 (progetto, sezione 4).
- Le regole nascono così: bozza con la fonte per ogni regola, verifica delle fonti da un agente di sola lettura, una pagina in parole semplici per l'utente, che approva, corregge o toglie; solo le regole approvate entrano nel plugin; senza approvazione il profilo non si accende (progetto, sezione 5).
- Il repo `ginz0ls/tollgate` è pubblico: dalle pagine dei fornitori si prendono fatti con parole nostre, mai testo intero; niente nomi di progetti privati dell'utente, niente nome utente né host.

## Da decidere nel piano
- La forma dei pattern di `infra`, che non sono solo cartelle (`vercel.json`, `wrangler.toml`/`wrangler.jsonc`, `Dockerfile`, `.github/workflows/`…): oggi un frammento accetta solo `**/<cartella>/**` (rinvio di B3). Come si adattano `fragments._PATTERN`, `init._FOLDER_PATTERN` e il calcolo dei percorsi concreti.
- Se il rilevamento per contenuto deve guardare anche file non sorgente (`.toml`, `.json`, `.yaml`, `Dockerfile`) o se per `infra` bastano i percorsi.
- Il rapporto con la CI del progetto (`.github/workflows/`), che il gate di tollgate tratta già in modo speciale: cosa accende `infra` e cosa resta del gate.
- Se B4 è abbastanza piccola da unirla a un'altra fetta (piano principale, sezione 2: «due per fetta se sono piccoli»).
- Le piccole cose rimaste aperte da B3 nel codice dei frammenti (piano principale, sezione 9): quali si chiudono qui.
- Dove la sessione d'esecuzione si ferma per l'approvazione delle regole (in B3 era il Task 7).

## Come lavorare
- Le scelte vere (compromessi, costi) si chiedono all'utente in parole semplici, con il costo esplicito (gratis, consumo dell'abbonamento o spesa vera) e un consiglio. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere. Il resto si decide con una `Ruling:` scritta nel piano.
- Revisione del piano da opus a contesto pulito, in sola lettura, a giri, finché un giro dice «pronto» con 0 critical e 0 important. La tabella dei giri va in fondo al piano.
- Le regole di cautela vanno nel brief di ogni subagente, al lancio.

## Finito quando
- I tre file esistono su `main`, committati.
- L'ultima riga della tabella dei giri dice «pronto», 0 critical, 0 important.
- `plugin-workflow-decisioni.md` nella memoria ha una voce sul piano di B4.
- L'utente ha ricevuto, in italiano semplice: cosa fa B4, le scelte che gli sono state chieste, quanto costerà eseguirlo, quando dovrà approvare le regole, il prossimo passo.
