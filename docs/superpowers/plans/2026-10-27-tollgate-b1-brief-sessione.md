# Brief per la sessione che esegue B1

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano B1 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-10-27-tollgate-b1-informati-prima.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-10-27-tollgate-b1-esecuzione.md`: ramo `b1-informati-prima`, worktree `.claude/worktrees/b1`, sessione avviata dalla radice del repo, workspace SDD nel worktree, modelli, scan pre-flight dopo il Task 1, regole di cautela con le eccezioni del controller, chiusura.

Il lavoro è finito quando:
- tutti i 10 task sono `complete` nel ledger, ognuno con la revisione pulita;
- le verifiche del Task 1 sono nel rapporto, con i ripieghi scelti in `Ruling:` prima del Task 2;
- la prova reale del Task 9 è riuscita, oppure il rapporto dice con chiarezza perché no;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, anche con `-W error::ResourceWarning`;
- il rapporto all'utente è consegnato, in parole semplici, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-10-27-tollgate-b1-esecuzione.md`: le istruzioni.
2. Il piano B1: per intero «Decisioni di questo piano» (18 decisioni), «Review Focus» e «Copertura».
3. Il progetto di B, `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, per intero: è l'autorità.
4. Il piano principale di B, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: sezioni 2, 3 e 7.
5. La spec del nucleo rev 26, sezioni 3.2, 6.3, 7.1, 7.2, 8.1, 8.5, 8.6, 11.4, 12.2, 16, 18.4.
6. `docs/sdd/2026-10-23-tollgate-p5-eval-ci/`: `README.md`, `progress.md` (forma delle `Ruling:`), `final-review.md` (triage), `cautele.md`, le regole per implementatori e revisori.
7. La memoria del progetto: `plugin-workflow-decisioni.md` (voce «B, progetto approvato»), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di B è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight dopo il Task 1**, con le ruling, `carry.md` e i `task-N-carry-extract.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` e dei `task-N-carry-extract.md` che nominano il task e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio**, compreso il divieto di `pkill`, `killall` e `kill` per pattern e di `git stash`. Le eccezioni del controller non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- **Solo sviluppo software**: niente profili per testi legali, preventivi o mail.
- **L0 avvisa e basta; L1 e L2 bloccano** la prima modifica di un task senza una nota valida.
- **Le regole le scrive Claude con la fonte, un agente verifica le fonti, l'utente approva una pagina per profilo in parole semplici.** Un profilo senza approvazione non si attiva. In B1 non si scrive nessuna regola: il blocco resta spento finché `rules-base` (B2) non è approvata.
- **Il repo `ginz0ls/tollgate` è pubblico**, e l'utente ha scelto di lasciarci i percorsi locali già presenti. Nei file nuovi niente nomi di progetti privati dell'utente né citazioni dalle sue altre sessioni.

## Punti delicati del piano

- **Il Task 1 decide il disegno.** I fatti B1-V1..V6 scelgono i ripieghi già scritti nel progetto 3.5 e nello Step 4 del Task 1 (attribuzione delle letture senza `agent_id`, context7 assente, nota con un file se l'heredoc non passa). Il 27/10, nella sessione dell'utente, il plugin context7 esponeva solo gli strumenti di autenticazione: è probabile che il ripiego «solo `WebFetch`» scatti.
- **Documentazione già raccolta** (27/10, versione 2.1.311, dal subagente `claude-code-guide` sulla documentazione ufficiale): `tools` dei subagenti accetta `mcp__<server>__*`; gli strumenti MCP di un plugin si chiamano `mcp__plugin_<plugin>_<server>__<tool>`; `tool_input` di `WebFetch` ha `url`, `prompt` e `offset`, quello di `WebSearch` `query` e i domini; il `tool_response` di `WebFetch` e `WebSearch` **non è documentato**; `agent_id` e `agent_type` stanno negli eventi degli strumenti chiamati da un subagente, ma per MCP, `WebFetch` e `WebSearch` la documentazione non lo dice in modo esplicito. Il Task 1 prova questi ultimi punti.
- **Oggi context7 sarebbe negato come effetto esterno** (`bin/tollgate_checks/effects.py`, `pre_mcp`): la decisione 6 lo lascia passare.
- **La nota si consegna con un comando, non con `Write`** (decisione 1): una scrittura sarebbe la prima modifica. Heredoc con il delimitatore tra apici `'NOTA_DI_RICERCA_FINE'`.
- **In `claude -p` gli strumenti vanno concessi** con `--permission-mode acceptEdits --allowedTools …` (`WebFetch` e `WebSearch` compresi): uno strumento negato non arriva a `PostToolUse`, e un esito ottenuto così è «non determinato», non negativo.
- **Fino a B2 nessun lavoro si ferma per la nota**: avviso al posto del rifiuto, e il revisore usa `moderate` invece di `major` (decisione 13).
- **L'interruttore del blocco è il campo `approved` di `skills/rules-base/SKILL.md`** (decisione 8): in B1 il file non esiste, quindi su `main` il passo avvisa e basta. La prova reale lo accende **solo in una copia del plugin** sotto `/tmp/tollgate-b1/plugin/`.
- **Lavori nati prima di B1** (`work_items.research = 0`): mai un avviso né un rifiuto.
- **Eval di P5:** lo scaffold crea lavori col programma vero, che dopo B1 avranno `research = 1`. La prova a secco `tests/test_eval_cases.py` deve restare verde: se un caso cambia esito per l'avviso del passo, è un conflitto da decidere con una `Ruling:`.

## Stato al momento di questo brief

- `main` contiene il nucleo completo (P5), il progetto di B (`59c0f4a`) e i quattro file di questo piano. La suite su `main` ha 2897 test verdi su Python 3.11 e 3.13.
- Sulla macchina: Claude Code 2.1.311, `gh` 2.46.0, Superpowers 7.0.0. Il repo locale non ha un remoto configurato: il push di `main` si fa verso l'URL `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.
- I worktree e i rami locali di P4 e P5 sono stati rimossi; i rami remoti `p4-gate` e `p5-eval-ci` esistono ancora su GitHub: non toccarli.
- Le trascrizioni delle sessioni nei worktree vanno spostate a fine lavoro nella cartella della radice, solo se la sessione è partita dal worktree (`sessioni-nei-worktree.md`).
