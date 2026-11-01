# Brief per la sessione che esegue B3

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B3 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-01-tollgate-b3-profilo-ai.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-01-tollgate-b3-esecuzione.md`: ramo `b3-profilo-ai`, worktree `.claude/worktrees/b3`, sessione avviata dalla radice del repo.

Il lavoro è finito quando:
- tutti i 9 task sono `complete` nel ledger, ognuno con la revisione pulita;
- la pagina `docs/profili/ai.md` è approvata dall'utente e `skills/rules-ai/SKILL.md` ha `approved` con la data;
- la prova reale del Task 8 è riuscita, oppure il rapporto dice con chiarezza perché no;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto all'utente è consegnato, in parole semplici, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-01-tollgate-b3-esecuzione.md`: le istruzioni.
2. Il piano B3: per intero «Decisioni di questo piano» (16 decisioni), «Review Focus», la tabella delle regole del Task 4 e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, per intero, **sezione 9 compresa**: è l'autorità.
4. Il piano principale di B, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 1, 2, 3 e 9.
5. La spec del nucleo rev 28, sezioni 6.3, 7.3, 11.2, 11.4, 18.4.
6. Il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, sezioni 1, 2, 2.1, 2.2, 2.3 e 4.
7. `docs/sdd/2026-10-29-tollgate-b2-regole-di-base/`: `README.md`, `progress.md` (forma delle `Ruling:`), `final-review.md` e `final-review-2.md` (lezioni e triage), `cautele.md`, le regole per implementatori e revisori.
8. I fatti raccolti per scrivere il piano, in `.superpowers/plan-b3/` della radice: `fatti-profili.md`, `fatti-sentinella.md` (per B3-bis), `fatti-modelli-web.md`, e le revisioni del piano `review-*.md`. Sono da verificare, non un'autorità.
9. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B2 e del 1° novembre sul profilo `ai`), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di B è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti. Le regole di `rules-ai` no: le decide l'utente.
- **Scan pre-flight prima del Task 1**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio.** Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- **Le regole le scrive Claude con la fonte, un agente verifica le fonti, l'utente approva una pagina per profilo in parole semplici.** Un profilo senza approvazione non si propone.
- **Sul profilo `ai` (progetto 9):** l'ultimo modello della famiglia appena esce; nome del modello in un solo punto con URL e data; note di migrazione prima di cambiare modello; errore chiaro per un modello ritirato; alias che cambiano da soli solo se dichiarati.
- **La sentinella dei modelli è B3-bis**, sul computer dell'utente all'avvio di un lavoro, senza segreti su GitHub. Non entra in B3.
- **Solo sviluppo software.** **Il repo `ginz0ls/tollgate` è pubblico:** nei file nuovi niente nomi di progetti privati dell'utente, niente nome utente né nome dell'host.

## Punti delicati del piano

- **`init` non cambia il nucleo a runtime.** Il profilo vive nel `tollgate.toml` del progetto, che l'utente copia dalla proposta. L'approvazione si legge solo quando `init` propone (decisione 4).
- **Il testo dell'utente in `tollgate.toml` non si riscrive mai**: i blocchi si aggiungono in coda, un profilo già dichiarato resta com'è (decisione 7).
- **`rules` e `blocking_rules` del profilo si calcolano dalla skill**, mai a mano (decisione 3): una `R-AI-NN` ignota al verdetto bloccherebbe sempre.
- **Gli agenti `-ai` si scrivono dopo l'approvazione** (Task 7 dopo il Task 6) e copiano i generici già corretti nel Task 1; il test di deriva lo controlla.
- **Dopo il Task 6 `init` propone `ai` per davvero**: i test di `init` devono usare una radice del plugin esplicita, altrimenti cambiano esito (come l'accensione di B2).
- **Le fonti sono pagine ufficiali, non testo MIT**: si citano i fatti, nessun testo copiato, citazioni di al più una riga nel rapporto. Il controller le scarica con l'eccezione 1, prima del Task 4.
- **La prova del Task 8** usa un progetto di prova nuovo (`spikes/b3/flow/`) con `B1_FLOW_CASE=ai`; il precaricamento si prova sulle trascrizioni dei subagenti.

## Stato al momento di questo brief

- `main` contiene il nucleo completo, B1, B2 (unita il 01/11/2026 fino a `a4742a4`, registro in `docs/sdd/2026-10-29-tollgate-b2-regole-di-base/`), la pulizia dei nomi nei documenti, la sezione 9 del progetto di B e i tre file di questo piano. La suite su `main` ha 3238 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`; la CI di `main` è verde.
- `skills/rules-base/SKILL.md` è approvata (11 regole, blocco acceso in L1 e L2). Non esistono `templates/profiles/`, `skills/rules-ai/`, `agents/implementer-ai.md`, `agents/reviewer-ai.md`.
- Sulla macchina: Claude Code 2.1.316, `gh` 2.46.0, Superpowers 7.0.0, agent-skills 0.6.9, Node 26, `bwrap`. Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- I worktree e i rami locali di B1 e B2 sono stati rimossi; i rami remoti `p4-gate` e `p5-eval-ci` esistono ancora su GitHub: non toccarli.
