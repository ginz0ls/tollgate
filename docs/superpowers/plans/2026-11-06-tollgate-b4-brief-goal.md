# Brief per l'agente che esegue B4 (obiettivo)

Leggi questo file per intero, poi `docs/superpowers/plans/2026-11-06-tollgate-b4-brief-sessione.md`, che è il brief completo: lì ci sono l'ordine di lettura, le scelte dell'utente da non riaprire, i punti delicati e lo stato del repo.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-06-tollgate-b4-profilo-infra.md` (profilo `infra`: Vercel, Cloudflare, Docker; 10 task) con `superpowers:subagent-driven-development`, seguendo alla lettera `docs/superpowers/plans/2026-11-06-tollgate-b4-esecuzione.md`:
- ramo `b4-profilo-infra`, worktree `.claude/worktrees/b4`;
- sessione avviata dalla radice del repo;
- regole di cautela nel brief di ogni subagente, al lancio.

## Fermate previste (non sono la fine del lavoro)

- **Task 6, Step 1:** mostri all'utente la pagina delle regole `docs/profili/infra.md`, in parole semplici, e aspetti che le approvi, le corregga o le tolga.
- **Prima del merge su `main`:** chiedi l'OK all'utente. Senza OK non si unisce niente.
- Le altre fermate sono solo quelle della sezione «Quando fermarsi e chiedere» delle istruzioni d'esecuzione.

## Finito quando

Valgono tutte:
1. Il ledger del workspace ha i 10 task `complete`, ognuno con la revisione pulita.
2. `skills/rules-infra/SKILL.md` ha `approved: <data>`, e `docs/profili/infra.md` ha la riga «Approvata dall'utente il <data>.» con la stessa data.
3. La prova reale del Task 9 è riuscita, oppure `docs/verifiche/2026-11-06-b4-prova-flusso.md` dice con chiarezza perché no.
4. Le evidenze sono ripulite e `test_committed_evidence_has_no_long_web_results` è verde.
5. La revisione finale opus del ramo è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati.
6. `PYTHONWARNINGS=error::ResourceWarning tests/run` è verde tre volte, su `python3.11` e `python3`.
7. L'utente ha ricevuto il rapporto in italiano semplice: commit e numero di test, regole approvate, `Ruling:` con il loro costo, minori rinviati, esito e consumo della prova reale, cosa cambia nei progetti. Il rapporto finisce con la richiesta dell'OK per il merge.

**Se l'utente rinvia l'approvazione delle regole**, vale la variante del brief della sessione: Task 1-5 fatti, Task 10 ridotto, revisione finale, suite verde tre volte, rapporto con la proposta di unire solo i commit dei Task 1-3 e del Task 10 ridotto.
