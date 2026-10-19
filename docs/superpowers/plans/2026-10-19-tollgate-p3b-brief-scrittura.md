# Brief per la sessione che scrive il piano P3b

Questa sessione parte con il contesto pulito. Scrive il piano P3b di tollgate (chiusura del lavoro) e **non lo esegue**. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Da leggere, in quest'ordine

1. La memoria del progetto: `plugin-workflow-decisioni.md`, `feedback-domande.md` e `sessioni-nei-worktree.md`.
2. `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`, per intero. Contano soprattutto:
   - la riga P3b nella tabella dei piani;
   - la sezione 3: i contratti reali di P3a, più le righe «Vincoli per P3b e P3c» e «Rinviati dalla revisione finale di P3a»;
   - la matrice dei criteri, con le colonne «Resta a» che puntano a P3b.
3. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, alla revisione 22. È l'autorità. Per P3b contano le sezioni su:
   - finish, revisione finale e verificatore;
   - open-pr e il blocco JSON 18.1;
   - sync, adopt, cleanup e abandon;
   - il rilevamento di merge e chiusura;
   - la 8.6, per le regole `[blocca]`.
4. `docs/superpowers/plans/2026-10-16-tollgate-p3a-avvio-e-task.md`, come modello di forma: Decisioni del piano, Review Focus, task con firme e test. Vanno letti anche i suoi due compagni, `2026-10-16-tollgate-p3a-esecuzione.md` e `2026-10-16-tollgate-p3a-brief-sessione.md`.
5. `docs/sdd/2026-10-16-tollgate-p3a-avvio-e-task/`: `README.md`, `progress.md` (le Ruling e l'incidente del `pkill`), `final-review.md` (il triage) e `cautele.md`. Servono per le lezioni del metodo.

## Cosa deve fare il piano

- **Metodo.** Si scrive con `superpowers:writing-plans`.
- **Forma.** Firme e test, non codice completo. Gli implementatori sono sonnet.
- **Task 1.** Verifiche reali su Claude Code, solo se servono fatti non ancora provati.
- **Penultimo task.** Una prova reale del flusso finish → open-pr con `claude -p`: solo in `/tmp`, con `--plugin-dir`, con `gh` finto e nessun push.
- **Ultimo task.** Le prove dei criteri, la revisione 23 della spec e l'aggiornamento del piano principale.
- **Criteri.** Chiude quelli assegnati a P3b: 9, 12, 16, 17, 26, 31, 40, 41, 42, più le parti rimaste di 1, 28 e 38.
- **Contratto con P4.** Fissa il blocco JSON 18.1, così P4 può partire.
- **Vincoli e rinviati di P3a.** Copre tutti quelli destinati a P3b: m9, m11, m12, m13, le righe 55, 56, 74, 102, 108 e 133, e il messaggio breve di `cli_calls` quando il parsing fallisce.
- **Regole del codice.** Rispetta gli strati: `tollgate_flow` importa solo core e analysis. Ogni comando destinato al modello passa da `paths.program_command`. Ogni sottocomando che legge la sessione passa dal segnale di `cli_calls`.

## File da scrivere (sul modello di P3a)

- `docs/superpowers/plans/2026-10-19-tollgate-p3b-chiusura.md`: il piano. Contiene una tabella che porta ogni criterio, vincolo e rinviato al suo task.
- `docs/superpowers/plans/2026-10-19-tollgate-p3b-esecuzione.md`: come eseguirlo con `superpowers:subagent-driven-development`.
  - **Dove:** ramo `p3b-chiusura`, in un worktree sotto `.claude/worktrees/p3b`.
  - **Come:** i modelli, lo scan pre-flight, le Ruling nel ledger, la revisione finale su opus, la suite tre volte.
  - **Regole di cautela nel brief di ogni subagente.** Comprendono il divieto di `pkill`, `killall` e `kill` per pattern.
  - **Chiusura:** niente merge senza l'OK dell'utente. Le trascrizioni della cartella del worktree in `~/.claude/projects` vanno spostate nella cartella della radice.
- `docs/superpowers/plans/2026-10-19-tollgate-p3b-brief-sessione.md`: il brief per la sessione che esegue il piano.

## Come lavorare

- Prima di consegnare, il piano passa a un revisore opus a contesto pulito, che lo confronta con la spec rev 22 e con il piano principale. I rilievi vanno corretti.
- All'utente si chiedono solo le scelte che sono compromessi veri. Il resto si decide e si registra nel piano, tra le decisioni.
- I tre file si committano su `main`, con la riga `Co-Authored-By` del modello.
- Testi in italiano, identificatori in inglese. Risposte all'utente brevi.

## Hai finito quando

- i tre file sono committati su `main`;
- il piano copre ogni criterio, vincolo e rinviato destinato a P3b;
- la revisione del piano non ha rilievi critical o important aperti;
- hai consegnato all'utente, in italiano, un riepilogo breve (numero di task, decisioni prese, domande aperte) e il prompt `/goal` per la sessione che eseguirà il piano.
