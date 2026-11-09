# Brief per la sessione che esegue B5

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B5 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-09-tollgate-b5-profilo-backend.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-09-tollgate-b5-esecuzione.md`: ramo `b5-profilo-backend`, worktree `.claude/worktrees/b5`, sessione avviata dalla radice del repo.

## Il lavoro è finito quando

- tutti i 9 task sono `complete` nel ledger, ognuno con la revisione pulita;
- `rules-backend` è approvata dall'utente (Task 5), con la data in `approved` e nella pagina `docs/profili/backend.md`;
- la prova reale del Task 8 è riuscita, oppure il rapporto dice con chiarezza perché no;
- le evidenze della prova sono ripulite, verificate a mano prima del rapporto, e `test_committed_evidence_has_no_long_web_results` è verde;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente prima del merge è consegnato nella forma del punto 4 di «Chiusura» delle istruzioni (sezioni con il titolo, l'elenco completo delle `Ruling:` e dei minori rinviati, una voce per riga, la domanda finale sul merge);
- **dopo il merge** (solo con l'OK dell'utente) i passi del punto 5 di «Chiusura» sono fatti e l'utente ha ricevuto il rapporto di chiusura che comincia con «Chiusura di B5».

**Se l'utente rinvia l'approvazione** (decisione 15): i Task 1-4 sono già fatti; ti fermi al Task 5, Step 1, scrivi un Task 9 ridotto (la parte della revisione 32 che riguarda le decisioni 4, 6 e 7, e lo stato nel piano principale), prepari il ramo `b5-parziale` da `main` con i commit dei Task 1-2 e quello del Task 9 ridotto (decisione 15), fai lì la revisione finale e le tre corse della suite, e proponi all'utente di unire su `main` solo `b5-parziale`; bozza, pagina e frammento di `backend` restano sul ramo `b5-profilo-backend`. In quel caso il lavoro è finito quando valgono le condizioni della situazione B del brief corto (`…-b5-brief-goal.md`).

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-09-tollgate-b5-esecuzione.md`: le istruzioni.
2. Il piano B5: per intero «Fatti verificati», «Global Constraints», «Decisioni di questo piano» (17 decisioni), «Review Focus» e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`: sezioni 2, 3.4, 4, 5, 11 e **12** (le scelte dell'utente del 9 novembre).
4. Il piano principale di B, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3, 9 e 13.
5. La spec del nucleo rev 31, sezioni 6.3, 7.1, 7.3, 8.5, 8.7, 11.2, 11.4, 16, 18.4.
6. Gli esempi da copiare: `skills/rules-infra/SKILL.md`, `templates/profiles/infra.toml` e `ai.toml` (`[detect]`), `docs/profili/infra.md`, `docs/profili/verifiche/infra-fonti.md`, `agents/implementer-infra.md`, `agents/reviewer-infra.md`, `tests/test_rules_infra.py`, `tests/test_rules_ai.py` (i test dei marcatori); il codice di `bin/tollgate_core/fragments.py`, `bin/tollgate_flow/init.py` (da `EXCLUDED_PREFIXES` a `profile_blocks`) e `bin/tollgate_analysis/bash.py` (da `EffectsCfg` a `text_effect`); il caso `infra` di `spikes/run-b1-flow.sh` e `spikes/b4/flow/`.
7. `docs/sdd/2026-11-06-tollgate-b4-profilo-infra/`: `README.md`, `progress.md` (forma delle `Ruling:`, approvazione delle regole, ruling D13 su `PACKAGE_COMMANDS`), `carry.md`, `preflight-scan.md`, `final-review.md` (I-1 sulle copie salvate, M-2 e M-5 che B5 chiude), `task-5-fonti-brief.md`, `task-9-rapporto-brief.md`, `cautele.md`.
8. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B4), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di B è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 1**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio.** Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli. Niente gergo nelle domande.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- **`backend` copre API e server, anche il backend locale senza Supabase, livello minimo L0** (progetto 4).
- **Il codice dei Worker di Cloudflare è `backend`; la configurazione di Wrangler e il deploy sono `infra`** (progetto 11).
- **Le cartelle `services/` non accendono `backend`** (progetto 12): nei progetti dell'utente sono codice d'interfaccia.
- **Le scritture di Wrangler su KV e R2 chiedono il permesso salvo `--local`; quelle di D1 solo con `--remote` o `--preview`** (progetto 12).
- **Le edge function di Supabase sono di `database`** (progetto 2 e 12): `backend` esclude `supabase/`.
- **I comandi di servizio lanciati con `npx` chiedono l'approvazione** (progetto 11, fatto in B4).
- **Le regole nascono così** (progetto 5): bozza con la fonte per ogni regola, verifica da un agente di sola lettura, una pagina in parole semplici per l'utente che approva, corregge o toglie; solo le regole approvate entrano; senza approvazione il profilo non si propone.
- **Il repo `ginz0ls/tollgate` è pubblico:** dalle pagine dei fornitori si prendono fatti con parole nostre, mai testo intero; niente nomi di progetti privati dell'utente, niente nome utente né host, niente token.

## Punti delicati del piano

- **`[detect] exclude`** (decisione 4) è una chiave nuova del frammento e decide solo la proposta di `init`: vale per il solo frammento che la dichiara, e `ai` e `infra` non cambiano.
- **Il codice dei Worker si trova per contenuto** (decisione 3), perché non ha una cartella fissa: un file trovato entra con il percorso esatto. Un marcatore che compare nei progetti di prova di B1-B4 o in `bin/` cambierebbe le prove vecchie: lo scan pre-flight lo controlla.
- **Le scritture di Wrangler** (decisione 6) hanno due modi: `unless_local` per KV e R2, `with_remote` per D1. I token `--local` e `--remote` vanno controllati contro i nomi comuni di cartelle e pacchetti (lezione di B4 su `PACKAGE_COMMANDS`).
- **Nessun comando vero di Wrangler, Vercel, Supabase, Deno o Node**, mai, nemmeno dal controller, e nessun server su una porta.
- **`dod` vuoto** (decisione 8): typecheck e test delle API dipendono dal progetto; la pagina spiega come aggiungerli a mano.
- **Prova reale** (decisione 14): il piano del lavoro non elenca le righe del report che le regole chiedono, così il report prova la lettura delle regole; se il modello scrive il piano nel passo 1, il rapporto lo dice.
- **Prima della prova reale** controlla che `ANTHROPIC_API_KEY`, `VERCEL_TOKEN`, `CLOUDFLARE_API_TOKEN`, `SUPABASE_ACCESS_TOKEN` e `DATABASE_URL` non siano impostate (solo se ci sono, mai il valore), e che la riga `--disallowedTools` di `controlla` vieti `wrangler`, `supabase`, `deno`, `node` e i lanciatori.
- **Il rapporto prima del merge** ha le sezioni con il titolo e gli elenchi completi, una voce per riga (istruzioni, «Chiusura», punto 4): la chiusura di B4 è rimasta bloccata perché la forma del rapporto si poteva leggere in due modi.

## Stato al momento di questo brief

- `main` contiene il nucleo completo, B1, B2, B3, B3-bis e B4 (unita il 09/11/2026 in `a1098ea`, registro in `docs/sdd/2026-11-06-tollgate-b4-profilo-infra/`), il brief di scrittura di B5, la sezione 12 del progetto di B e i quattro file di questo piano. La suite su `main` ha 3668 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- `skills/rules-base/SKILL.md`, `skills/rules-ai/SKILL.md` e `skills/rules-infra/SKILL.md` sono approvate; i profili `ai` e `infra` si propongono con `init`. Non esistono `skills/rules-backend/`, `templates/profiles/backend.toml`, `agents/*-backend.md`, `docs/profili/backend.md`, `spikes/b5/`.
- Sulla macchina: Claude Code 2.1.319 o successivo, `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0, agent-skills 0.6.9, everything-claude-code 1.4.1 sul disco ma spento. Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- I commit del piano di B5 su `main` non sono ancora stati inviati a GitHub: vanno con il primo push dopo il merge.

## Quanto costa

Nessun eval. B5 consuma l'abbonamento per i subagenti (implementatori, revisori e verificatore delle fonti sonnet, revisione finale opus) e per la prova reale del Task 8, l'unico `claude -p`: circa 1-1,5 USD stimati sull'abbonamento (B4: 1,03), nessuna spesa in denaro. Le pagine ufficiali si leggono con `WebFetch`, senza costo.
