# Brief per la sessione che scrive i piani di B

Questa sessione parte con il contesto pulito. Scrive il piano principale del sotto-progetto B di tollgate (profili con «informati prima») e il piano della sua prima fetta, B1, **e non li esegue**. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Da leggere, in quest'ordine

1. La memoria del progetto: `plugin-workflow-decisioni.md`, soprattutto le voci «Profili verticali», «Specializzazione», P5 e «B, progetto approvato». Poi `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md` e `github-500-transitorio.md`.
2. **Il progetto approvato** `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`, per intero. È l'autorità per B: le scelte marcate «utente» non si rimettono in discussione, quelle marcate «mia scelta» si possono correggere solo con un motivo scritto nel piano.
3. `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`, il catalogo. B ne usa solo sei profili: `base`, `infra`, `ai`, `frontend`, `backend` e `database`.
4. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, alla revisione 26. Per B contano le sezioni 1.3, 3.2, 5, 6.3, 7.2, 8.1, 8.5, 8.6, 8.7, 11.4, 12, 14, 16 e 18.5.
5. `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`: la tabella dei contratti della sezione 3 (le firme reali dei pacchetti) e la sezione «Chiusura del nucleo», con quello che resta dopo la v1.
6. `docs/superpowers/plans/2026-10-23-tollgate-p5-eval-ci.md`, come modello di forma, con i compagni `-esecuzione.md` e `-brief-sessione.md`. Poi `docs/sdd/2026-10-23-tollgate-p5-eval-ci/`: `README.md`, `progress.md` (le `Ruling:` e i minori rinviati), `cautele.md` e `final-review.md`.
7. Il codice reale di `main`:
   - `agents/implementer.md` e `agents/task-reviewer.md`;
   - `hooks/hooks.json` e `bin/tollgate_hooks/`;
   - `bin/tollgate_checks/`, cioè il registro dei controlli;
   - `bin/tollgate_analysis/profiles.py` e `brief.py`;
   - `bin/tollgate_flow/taskcmd.py`;
   - `bin/tollgate_core/` (stato, migrazioni, `subagents`, `tasks`);
   - `templates/tollgate.toml`;
   - `evals/`, cioè casi, kit e `run.sh`;
   - `tests/`.
8. La documentazione reale di Claude Code sui subagenti (strumenti, MCP nei subagenti di plugin) e sugli hook (`PreToolUse` e `PostToolUse` di `WebFetch`, `WebSearch` e degli strumenti MCP, presenza di `agent_id`). Va presa dalla versione installata e dal subagente `claude-code-guide`, non a memoria. Quello che non si ricava senza eseguire va nel Task 1 di B1.

## Cosa scrivere

1. **Il piano principale di B**, `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`, magro come quello del nucleo: le fette in ordine, cosa consegna ciascuna, le dipendenze, le interfacce tra le fette e quando B è finito (sezione 5 del progetto). Una possibile divisione, da confermare leggendo il codice:
   - **B1:** verifiche (3.5 del progetto), strumenti degli implementatori, nota di ricerca, registrazione delle letture, controllo in `PreToolUse` (avviso in L0, blocco in L1 e L2, spento finché `rules-base` non è approvata), controllo del revisore, test e prova reale;
   - **B2:** `rules-base`, con la pagina per l'utente e l'accensione del blocco;
   - **B3 e seguenti:** un profilo per fetta, oppure due per fetta se sono piccoli, ciascuno con regole, pagina per l'utente, agenti per area, percorsi, `dod` e attivazione;
   - **ultima fetta:** gli eval minimi (sezione 7 del progetto) e la chiusura di B.
2. **Il piano di B1**, `docs/superpowers/plans/2026-10-27-tollgate-b1-<nome>.md`, con `superpowers:writing-plans` e la tabella Copertura che porta ogni punto del progetto destinato a B1 al suo task.
   - **Forma:** firme e test, non codice completo. Gli implementatori sono sonnet.
   - **Task 1:** le tre verifiche della sezione 3.5 del progetto, eseguite dal controller, con i ripieghi già decisi lì. Il disegno dei task successivi dipende dagli esiti e lo dice.
   - **Penultimo task:** la prova reale di un lavoro L1. Va divisa tra preparazione (script con test) ed esecuzione (controller), come in P4 e P5.
   - **Ultimo task:** le prove, la nuova revisione della spec del nucleo (sezioni 7.2, 8.1, 11.4 e 16) e l'aggiornamento del piano principale di B.
3. `docs/superpowers/plans/2026-10-27-tollgate-b1-esecuzione.md`, sul modello di P5:
   - **Dove:** ramo `b1-<nome>`, in un worktree sotto `.claude/worktrees/b1`.
   - **Come:** `superpowers:subagent-driven-development`, revisione finale su opus, suite tre volte (anche con `-W error::ResourceWarning`).
   - **Cautele:** le regole di cautela di `docs/sdd/2026-10-23-tollgate-p5-eval-ci/cautele.md` nel brief di ogni subagente al lancio, con le sole eccezioni che servono a B1, scritte una per una.
4. `docs/superpowers/plans/2026-10-27-tollgate-b1-brief-sessione.md`, il brief per la sessione che esegue B1.

## Decisioni già prese dall'utente (non si richiedono)

- **Ambito:** solo sviluppo software. Niente profili per testi legali, preventivi o mail.
- **Comportamento del controllo:** L0 avvisa e basta; L1 e L2 bloccano la prima modifica di un task senza una nota valida.
- **Primo gruppo di profili:** `base`, `infra` (con Vercel), `ai` (con Gemini), `frontend`, `backend` e `database`. Gli altri profili vengono dopo.
- **Regole:** le scrive Claude con la fonte, un agente verifica le fonti, l'utente approva una pagina per profilo **in parole semplici**. Un profilo senza approvazione non si attiva.
- **Eval minimi:** 2-3 casi con `claude plugin eval`, tetto di 20 USD di costo stimato. L'utente usa l'abbonamento: i dollari sono una stima del consumo, non denaro, e all'utente va spiegato così.
- **Repo `ginz0ls/tollgate`:** è pubblico. La CI di GitHub è gratuita, e l'utente ha scelto di lasciare nel repo i percorsi locali già presenti. Nei file nuovi non vanno nomi di progetti privati dell'utente né citazioni dalle sue altre sessioni.

## Domande da fare all'utente

Solo i compromessi veri che emergono leggendo il codice, ognuno con una raccomandazione, in parole semplici e con il costo esplicito: gratis, consumo dell'abbonamento oppure spesa vera. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere, e si scrivono tra le decisioni del piano.

## Come lavorare

- Prima di consegnare, i piani passano a un revisore opus a contesto pulito, che li confronta con il progetto di B, con la spec rev 26 e con il codice reale di `main`. I rilievi vanno corretti, e dopo le correzioni serve una ri-revisione mirata.
- I file si committano su `main` dopo che `tests/run` è verde su python3.11 e python3, con la riga `Co-Authored-By` del modello. Push solo verso `https://github.com/ginz0ls/tollgate.git`, con il controllo `spikes/gh-p4/ghguard.py gitcheck` (profilo `p5`) prima del push.
- Testi in italiano, identificatori in inglese. Risposte all'utente brevi e semplici.

## Stato al momento di questo brief

- `main` contiene il nucleo completo (P5 unito fino a `3b5d365`, registro in `3b3bedb`) e il progetto di B. La suite ha 2897 test verdi su Python 3.11 e 3.13.
- I worktree e i rami locali di P4 e P5 sono stati rimossi. I rami remoti `p4-gate` e `p5-eval-ci` esistono ancora su GitHub.
- Sulla macchina: `gh` 2.46.0, Superpowers 7.0.0.

## Hai finito quando

- i quattro file sono committati su `main` e inviati a GitHub;
- il piano di B1 copre ogni punto del progetto destinato a B1, o ne motiva il rinvio a una fetta successiva;
- la revisione dei piani non ha rilievi critical o important aperti;
- hai dato all'utente, in italiano e in parole semplici, un riepilogo breve (fette di B, task di B1, decisioni prese, domande aperte) e il prompt `/goal` per la sessione che eseguirà B1.
