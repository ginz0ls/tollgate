# Brief per la sessione che esegue B6

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B6 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-10-tollgate-b6-profilo-frontend.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-10-tollgate-b6-esecuzione.md`: ramo `b6-profilo-frontend`, worktree `.claude/worktrees/b6`, sessione avviata dalla radice del repo.

## Il lavoro è finito quando

- tutti i 9 task sono `complete` nel ledger, ognuno con la revisione pulita;
- `rules-frontend` è approvata dall'utente (Task 5), con la data in `approved` e nella pagina `docs/profili/frontend.md`;
- la prova reale del Task 8 è riuscita, oppure il rapporto dice con chiarezza perché no;
- le evidenze della prova sono ripulite, verificate a mano prima del rapporto (anche i risultati di `WebFetch` sotto i 5000 caratteri, letti uno per uno), e `test_committed_evidence_has_no_long_web_results` è verde;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati, dopo aver cercato un caso di precedenza tra profili che la tabella della decisione 4 non ha;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente prima del merge è consegnato nella forma del punto 4 di «Chiusura» delle istruzioni (sezioni con il titolo, l'elenco completo delle `Ruling:` e dei minori rinviati, una voce per riga, la domanda finale sul merge);
- **dopo il merge** (solo con l'OK dell'utente) i passi del punto 5 di «Chiusura» sono fatti, l'utente ha ricevuto il rapporto di chiusura che comincia con «Chiusura di B6» e la domanda diretta sul worktree.

**Se l'utente rinvia l'approvazione** (decisione 14): i Task 1-4 sono già fatti; ti fermi al Task 5, Step 1, scrivi un Task 9 ridotto (la parte della revisione 33 che riguarda le decisioni 2 e 16, e lo stato nel piano principale), prepari il ramo `b6-parziale` da `main` con i commit dei Task 1-2 e quello del Task 9 ridotto, fai lì la revisione finale e le tre corse della suite, e proponi all'utente di unire su `main` solo `b6-parziale`; bozza, pagina e frammento di `frontend` restano sul ramo `b6-profilo-frontend`. In quel caso il lavoro è finito quando valgono le condizioni della situazione B del brief corto (`…-b6-brief-goal.md`).

**Il merge su `main` non si fa senza l'OK dell'utente.**

**Le condizioni esatte stanno nel brief corto** `docs/superpowers/plans/2026-11-10-tollgate-b6-brief-goal.md` (situazioni A-D, righe del ledger da scrivere con quelle parole). **A ogni fermata** (approvazione delle regole, una scelta della revisione finale, il merge, la rimozione del worktree, e i casi di «Quando fermarsi e chiedere») fai una **domanda diretta** all'utente con `AskUserQuestion`: in B5 l'hook di Stop chiedeva di proseguire a ogni fermata, e la domanda diretta l'ha risolto. Il rapporto prima del merge finisce con la riga «Posso unire su `main`?». Ogni altra fermata ha un messaggio che comincia con la riga `Fermata: <caso>`; se l'utente risponde a una fermata con una domanda, si risponde e si ripete la richiesta della fermata.

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-10-tollgate-b6-esecuzione.md`: le istruzioni (in particolare «La suite: implementatori e controller», con il ciclo `until` e le sentinelle giuste).
2. Il piano B6: per intero «Fatti verificati», «Global Constraints», «Decisioni di questo piano» (17 decisioni, con la tabella delle precedenze della decisione 4), «Review Focus» e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`: sezioni 2, 3.4, 4, 5, 12 e **13** (le scelte dell'utente del 10 novembre).
4. Il piano principale di B, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3, 9 (soprattutto «A B6-B8, da B5») e 14.
5. La spec del nucleo rev 32, sezioni 6.3, 7.1, 7.3, 8.5, 8.7, 11.2 (la regola di I-1 e l'esclusione per frammento), 11.4, 16, 18.4.
6. Gli esempi da copiare: `skills/rules-backend/SKILL.md`, `templates/profiles/backend.toml` (`[detect] content` con le due virgolette), `docs/profili/backend.md`, `docs/profili/verifiche/backend-fonti.md`, `agents/implementer-backend.md`, `agents/reviewer-backend.md`, `tests/test_rules_backend.py` (con le correzioni della decisione 16); il codice di `bin/tollgate_core/fragments.py` (`parse_pattern`), `bin/tollgate_flow/init.py` (da `EXCLUDED_PREFIXES` a `profile_blocks`), `bin/tollgate_analysis/profiles.py` (`vertical_for`), `spikes/b1/flowreg.py` (`_saved_copy`, `_swap_saved`, `_third_party`); il caso `backend` di `spikes/run-b1-flow.sh` e `spikes/b5/flow/`.
7. `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/`: `README.md`, `progress.md` (forma delle `Ruling:`, solleciti agli implementatori fermi, ruling sul ciclo `until`), `carry.md`, `preflight-scan.md`, `final-review.md` (I-1 sulle precedenze e il triage, voci 25, 26, 30 che B6 chiude), `task-4-fonti-brief.md`, `task-8-rapporto-brief.md`, `cautele.md`.
8. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B5 e del piano di B6), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di B è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 1**, con la sonda della tabella delle precedenze sui frammenti veri, e le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task, le regole di cautela e le tre righe sulla suite (lancio con l'uscita su file, ciclo `until` in primo piano, commit dopo `exit 0`). Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio.** Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli. Niente gergo nelle domande.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- **`frontend` ha livello minimo L0** (progetto 4): per i lavori piccoli solo l'avviso.
- **Le regole di accessibilità stanno dentro `rules-frontend`** come `R-FRONTEND-NN` (progetto 13): nessuna skill `rules-a11y`, nessun profilo trasversale.
- **Rimedio per `routes/` d'interfaccia** (progetto 13): i marcatori delle librerie di rotte (TanStack Router, React Router, Remix), con la regola di I-1, tengono fuori da `backend` una cartella `routes/` i cui moduli le importano; se un solo file non le importa la cartella resta a `backend`, e la pagina spiega come toglierla a mano.
- **`routes/` e `handlers/` restano di `backend` a qualunque profondità** (approvato il 10/11/2026, punto 5 della pagina di `backend`): B6 non cambia il frammento né la pagina di `backend`.
- **Le cartelle `services/` non sono di `backend`** (progetto 12); B6 le lascia al generico (decisione 6, «mia scelta» portata all'utente nella pagina).
- **Un file trovato per contenuto da un profilo non accende un altro profilo per la sola cartella** (correzione di I-1 di B5).
- **Le regole nascono così** (progetto 5): bozza con la fonte per ogni regola, verifica da un agente di sola lettura, una pagina in parole semplici per l'utente che approva, corregge o toglie; solo le regole approvate entrano; senza approvazione il profilo non si propone.
- **Il repo `ginz0ls/tollgate` è pubblico:** dalle pagine dei fornitori e dalle skill si prendono fatti con parole nostre, mai testo intero; niente nomi di progetti privati dell'utente, niente nome utente né host, niente token.

## Punti delicati del piano

- **La forma `ext`** (decisione 2): zero segmenti letterali, si propone così com'è e solo per ultima; perde contro ogni cartella di un altro profilo, ed è voluto. Maiuscole rispettate, mai per un documento. `vertical_for` e `globs` non cambiano.
- **La tabella delle precedenze** (decisione 4): ventiquattro casi, ognuno con un test `test_real_precedence_p<N>`; P2, P6, P10, P14, P15, P20, P23 e P24 sono costi scritti, non difetti. La revisione finale cerca un caso che manca.
- **`[detect] exclude` di `frontend`** (decisione 7): le cartelle alla radice di `backend` e `infra` più `supabase/`; senza, `**/components/**` e i percorsi esatti dei file che importano il router vincerebbero dentro i server. `test_exclude_matches_root_folders_of_other_fragments` tiene l'elenco allineato ai frammenti approvati.
- **I marcatori** sono solo le righe di import delle librerie di rotte, con le due virgolette; `from 'react'` e `'use client'` non lo sono (decisione 5). Un marcatore senza una pagina ufficiale che lo mostri esce. Un `.ts` o `.js` che importa il router entra come percorso esatto e vince su ogni cartella fuori da quelle escluse (P23).
- **`togli-pagine`** (Task 2): ogni `Bash` che nomina una copia salvata, senza elenco di lettori, anche `stderr`; le evidenze già committate restano verdi.
- **Nessun `node`, gestore di pacchetti, server di sviluppo o browser**, mai, nemmeno dal controller: la prova reale si verifica con `html.parser`.
- **`dod` vuoto** (decisione 8): lint, typecheck e test dei componenti dipendono dal progetto; la pagina spiega come aggiungerli a mano.
- **Prova reale** (decisione 15): il piano del lavoro non nomina ciò che le regole chiedono (nome accessibile, regione di stato, componenti simili, documentazione); `init` non deve proporre `backend` (P9 dal vivo).
- **Prima della prova reale** controlla che `ANTHROPIC_API_KEY`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN`, `SUPABASE_ACCESS_TOKEN`, `DATABASE_URL` e `NPM_TOKEN` non siano impostate (solo se ci sono, mai il valore), e che la riga `--disallowedTools` di `controlla` vieti `node`, i lanciatori, gli strumenti d'interfaccia e i browser.
- **Il rapporto prima del merge** ha le sezioni con il titolo e gli elenchi completi, una voce per riga (istruzioni, «Chiusura», punto 4), e dice che la pagina approvata di `backend` invecchia per il rimedio di `routes/`.

## Stato al momento di questo brief

- `main` contiene il nucleo completo, B1, B2, B3, B3-bis, B4 e B5 (unita il 10/11/2026 in `525d8d8`, registro in `docs/sdd/2026-11-09-tollgate-b5-profilo-backend/`), il brief di scrittura di B6, la sezione 13 del progetto di B e i quattro file di questo piano. La suite su `main` ha 3760 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- `skills/rules-base`, `rules-ai`, `rules-infra` e `rules-backend` sono approvate; i profili `ai`, `infra` e `backend` si propongono con `init`. Non esistono `skills/rules-frontend/`, `templates/profiles/frontend.toml`, `agents/*-frontend.md`, `docs/profili/frontend.md`, `spikes/b6/`.
- Sulla macchina: Claude Code 2.1.319 o successivo, `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0, agent-skills 0.6.9, `frontend-design` 1.1.1. Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- I commit del piano di B6 su `main` non sono ancora stati inviati a GitHub: vanno con il primo push dopo il merge.

## Quanto costa

Nessun eval. B6 consuma l'abbonamento per i subagenti (implementatori, revisori e verificatore delle fonti sonnet, revisione finale opus) e per la prova reale del Task 8, l'unico `claude -p`: circa 1-1,5 USD stimati sull'abbonamento (B5: 0,92), nessuna spesa in denaro. Le pagine ufficiali si leggono con `WebFetch`, senza costo.
