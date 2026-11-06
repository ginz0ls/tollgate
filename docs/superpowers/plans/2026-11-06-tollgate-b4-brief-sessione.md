# Brief per la sessione che esegue B4

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B4 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-06-tollgate-b4-profilo-infra.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-06-tollgate-b4-esecuzione.md`: ramo `b4-profilo-infra`, worktree `.claude/worktrees/b4`, sessione avviata dalla radice del repo.

## Il lavoro è finito quando

- tutti i 10 task sono `complete` nel ledger, ognuno con la revisione pulita;
- `rules-infra` è approvata dall'utente (Task 6), con la data in `approved` e nella pagina `docs/profili/infra.md`;
- la prova reale del Task 9 è riuscita, oppure il rapporto dice con chiarezza perché no;
- le evidenze della prova sono ripulite e `test_committed_evidence_has_no_long_web_results` è verde;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente è consegnato, in parole semplici, con la richiesta dell'OK per il merge.

**Se l'utente rinvia l'approvazione** (decisione 15): i Task 1-5 sono già fatti; ti fermi al Task 6, Step 1, scrivi un Task 10 ridotto (la parte della revisione 31 che riguarda le decisioni 2-4, 10, 16-18, e lo stato nel piano principale), fai la revisione finale e proponi all'utente di unire su `main` solo i commit dei Task 1-3 più quello del Task 10 ridotto; bozza, pagina e frammento di `infra` restano sul ramo. In quel caso il lavoro è finito quando quei commit sono rivisti, la suite è verde tre volte e il rapporto all'utente lo dice.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-06-tollgate-b4-esecuzione.md`: le istruzioni.
2. Il piano B4: per intero «Fatti verificati», «Global Constraints», «Decisioni di questo piano» (18 decisioni), «Review Focus» e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`: sezioni 3.4, 4, 5 e **11** (le scelte dell'utente del 6 novembre).
4. Il piano principale di B, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3 e 9.
5. La spec del nucleo rev 30, sezioni 6.3, 7.1, 7.3, 8.5, 9.2, 11.2, 11.4, 16, 18.4.
6. Gli esempi da copiare: `skills/rules-ai/SKILL.md`, `templates/profiles/ai.toml`, `docs/profili/ai.md`, `docs/profili/verifiche/ai-fonti.md`, `agents/implementer-ai.md`, `agents/reviewer-ai.md`, `tests/test_rules_ai.py`; il codice di `bin/tollgate_core/fragments.py` e di `bin/tollgate_flow/init.py` (da `_FOLDER_PATTERN` a `profile_blocks`).
7. `docs/sdd/2026-11-01-tollgate-b3-profilo-ai/`: `README.md`, `progress.md` (forma delle `Ruling:`, approvazione delle regole), `final-review.md` (I-1 sul testo di terzi nelle evidenze, M-1 e M-4 che B4 chiude), `task-6-fonti-brief.md`, `task-7-brief.md`. E `docs/sdd/2026-11-04-tollgate-b3bis-sentinella-modelli/`: `cautele.md`, le regole per implementatori e revisori.
8. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B3 e B3-bis, l'incidente di `os.environ`), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

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

- **`infra` copre deploy, Vercel, Cloudflare e server, livello minimo L1** (progetto 4).
- **I workflow di GitHub restano al gate** (progetto 11): `.github/workflows/` non accende `infra`.
- **Il codice dei Worker di Cloudflare è `backend`** (progetto 11): `infra` copre la configurazione di Wrangler e il deploy, non il programma.
- **I comandi di servizio lanciati con `npx` chiedono l'approvazione** (progetto 11): B4 chiude il buco; alcuni comandi solo locali di Supabase e Vercel chiederanno il permesso come già fanno senza `npx` (quelli di Supabase li restringe B7).
- **Le regole nascono così** (progetto 5): bozza con la fonte per ogni regola, verifica da un agente di sola lettura, una pagina in parole semplici per l'utente che approva, corregge o toglie; solo le regole approvate entrano; senza approvazione il profilo non si propone.
- **Il repo `ginz0ls/tollgate` è pubblico:** dalle pagine dei fornitori si prendono fatti con parole nostre, mai testo intero; niente nomi di progetti privati dell'utente, niente nome utente né host, niente token.

## Punti delicati del piano

- **Le tre forme dei pattern stanno in un solo punto**, `fragments.parse_pattern` (decisione 2). `init` non ha più regex sue per i pattern.
- **Percorsi concreti** (decisione 3): la forma `name` si confronta sul solo nome del file (mai `globs.match`, che accenderebbe anche una cartella con quel nome) e propone il percorso esatto del file (`/vercel.json`, `services/api/Dockerfile.prod`), così vince per specificità su un `web/**` dichiarato. Le forme a cartella vengono prima, come in B3.
- **I documenti non accendono un profilo per cartella** (decisione 4), per tutte le aree: cambia anche la proposta di `ai` per `docs/ai/` e `.github/agents/`, ma non la pagina approvata di `ai`, che non si tocca.
- **Nessun comando vero di Vercel, Cloudflare o Docker**, mai, nemmeno dal controller: scaricano pacchetti o parlano con un servizio. Nella prova reale il progetto non è collegato a niente, lo script vieta quei comandi al modello e il piano del lavoro lo dice.
- **`npx wrangler deploy` è un effetto esterno** (decisione 17, Task 3): oggi tollgate guarda solo il nome del programma e `npx` lo nascondeva.
- **`dod` vuoto** (decisione 7): la prova del deploy dipende dal progetto; la pagina spiega come aggiungerla a mano.
- **Test d'area su `AREAS`** (decisione 9): gli id delle regole negli agenti si confrontano con la skill, non con elenchi scritti a mano nei test.
- **Prima della prova reale** controlla che `ANTHROPIC_API_KEY`, `VERCEL_TOKEN` e `CLOUDFLARE_API_TOKEN` non siano impostate (solo se ci sono, mai il valore), e che la riga `--disallowedTools` di `controlla` vieti `vercel`, `wrangler`, `docker` e `npx`: le credenziali salvate con `vercel login` o `wrangler login` stanno in file, non in variabili.

## Stato al momento di questo brief

- `main` contiene il nucleo completo, B1, B2, B3 e B3-bis (unita il 06/11/2026, registro in `docs/sdd/2026-11-04-tollgate-b3bis-sentinella-modelli/`), il brief di scrittura di B4, la sezione 11 del progetto di B e i tre file di questo piano. La suite su `main` ha 3572 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- `skills/rules-base/SKILL.md` e `skills/rules-ai/SKILL.md` sono approvate; il profilo `ai` si propone con `init`. Non esistono `skills/rules-infra/`, `templates/profiles/infra.toml`, `agents/*-infra.md`, `docs/profili/infra.md`, `spikes/b4/`.
- Sulla macchina: Claude Code 2.1.316 o successivo, `gh` 2.46.0, Superpowers 7.0.0, agent-skills 0.6.9. Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- I commit del piano di B4 su `main` non sono ancora stati inviati a GitHub: vanno con il primo push dopo il merge.

## Quanto costa

Nessun eval. B4 consuma l'abbonamento per i subagenti (implementatori, revisori e verificatore delle fonti sonnet, revisione finale opus) e per la prova reale del Task 9, l'unico `claude -p`: circa 1-1,5 USD stimati sull'abbonamento (B3: 1,32), nessuna spesa in denaro. Le pagine ufficiali si leggono con `WebFetch`, senza costo.
