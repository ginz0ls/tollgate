# Brief per la sessione che scrive il piano P3c

Questa sessione parte con il contesto pulito. Scrive il piano P3c di tollgate (percorso L2) e **non lo esegue**. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Da leggere, in quest'ordine

1. La memoria del progetto: `plugin-workflow-decisioni.md`, `feedback-domande.md` e `sessioni-nei-worktree.md`.
2. `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`, per intero. Contano soprattutto:
   - la riga P3c nella tabella dei piani (criteri 24, 35, 37 e la seconda frase del 41);
   - la sezione 3: i contratti reali di P3a e P3b, le righe «Vincoli per P3b e P3c», «Vincoli per P3c» (sei punti), il rinviato della riga 82 di P3a (recinto con rientro qualsiasi nel parser del piano);
   - la matrice dei criteri, con le colonne «Resta a» che puntano a P3c.
3. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, alla revisione 23. È l'autorità. Per P3c contano le sezioni su:
   - spec e piano in L2 (6.2), avvio con `--spec` (6.1), audit della spec a lenti e giri avversariali, `approve spec <fette>`, `approve plan`, `reopen spec|plan`;
   - i file di approvazione e i report (18.3), i verdetti degli avversari e degli auditor (18.5);
   - gli atti applicabili (8.4) e i tetti dei giri avversariali e dell'audit;
   - la sezione 16 e le revisioni 22-23 (esiti delle verifiche di P3a e P3b).
4. `docs/superpowers/plans/2026-10-19-tollgate-p3b-chiusura.md`, come modello di forma: Decisioni del piano, Rilievi ripresi qui, Review Focus, task con firme e test, tabella Copertura. Vanno letti anche i suoi due compagni, `2026-10-19-tollgate-p3b-esecuzione.md` e `2026-10-19-tollgate-p3b-brief-sessione.md`.
5. `docs/sdd/2026-10-19-tollgate-p3b-chiusura/`: `README.md`, `progress.md` (45 `Ruling:`), `preflight-scan.md`, `final-review.md` (il triage: le righe rinviate a P3c vanno coperte dal piano) e `cautele.md`. Servono per le lezioni del metodo e per i rinviati.

## Cosa deve fare il piano

- **Metodo.** Si scrive con `superpowers:writing-plans`.
- **Forma.** Firme e test, non codice completo. Gli implementatori sono sonnet.
- **Task 1.** Verifiche reali su Claude Code solo se servono fatti non ancora provati (per esempio come si comportano più subagenti avversari lanciati in parallelo). Se non servono, il Task 1 lo dice e il piano parte dal codice.
- **Penultimo task.** Una prova reale del percorso L2 con `claude -p`: `/tollgate:start #N --spec` (o L2), audit della spec, `approve spec`, piano, avversario del piano, `approve plan`, fino all'esecuzione del primo task. Solo in `/tmp`, con `--plugin-dir`, con `gh` finto e nessun push in rete.
- **Ultimo task.** Le prove dei criteri, la revisione 24 della spec e l'aggiornamento del piano principale.
- **Criteri.** Chiude quelli assegnati a P3c: 24, 35, 37 (con `plan_sha` di `approve plan`) e la seconda frase del 41 (spec L2 senza `## Cosa non fare` → rilievo dell'avversario), più le parti «Resta a P3c» della matrice.
- **Vincoli di P3b.** Copre i sei «Vincoli per P3c» della sezione 3 del piano principale, in particolare: `approve spec` e `approve plan` in `actapply.APPLIERS`, che scrivono `spec-approval.md` e `plan-approval.md` con i campi che P3b legge già (`kind`, `path`, `sha`, `adversarial`, `lens`, `spec_sha`; `approvals.parse_approval`, `approvals.is_current`); i campi `spec_reviews_dir`, `plan_reviews_dir` e `spec_audit` del blocco 18.1; ogni sottocomando nuovo che legge la sessione in `cli_calls._SIGNALLED` e `_COORDINATOR_ONLY`, con `argv` passato a `sessions.cli_session`.
- **Rinviati.** La riga 82 di P3a e le righe del triage di `docs/sdd/2026-10-19-tollgate-p3b-chiusura/final-review.md` con destinazione P3c (soprattutto test mancanti o deboli, testi delle skill e dei brief).
- **Regole del codice.** Rispetta gli strati (`tests/test_layers.py`): `tollgate_flow` importa solo core e analysis, `tollgate_analysis` non importa nulla di tollgate, `tollgate_checks` non scrive nel DB. Ogni comando destinato al modello passa da `paths.program_command`. Testo non fidato (issue, spec scritta dal modello, rilievi degli avversari) mai in un argomento di git o `gh`: su file, in un recinto, marcato come dato.

## Lezioni dell'esecuzione di P3b da portare nel piano

- **Interazioni tra task.** La revisione finale di P3b ha trovato 4 Important nati dall'incontro di task diversi (rilievi rimasti senza esito in cicli superati, `sync` con un task aperto, PR da fork con lo stesso ramo, permesso di push forzato non rinnovato). Nel piano: un Review Focus per ogni stato che due comandi diversi toccano, e test che attraversano i comandi.
- **Skill contro codice.** Il Task 16 di P3b aveva tre istruzioni che non corrispondevano al codice (per esempio un commit del coordinatore che fa decadere l'atto `finish`). Nel piano: le skill si scrivono dopo i sottocomandi, e un test controlla codici d'uscita e righe che la skill cita.
- **Prova reale e sessione legata.** In P3b un atto digitato in una sessione `claude -p` non legata al lavoro è stato rifiutato. Il penultimo task lancia i passi dopo `start` dalla cartella del worktree, e lo script lo controlla.
- **`gh`.** I nomi dei campi JSON (`headRefOid`, `mergedAt`, `comments`, `isCrossRepository`) non sono verificati sull'aiuto di `gh` 2.46: un campo nuovo usato da P3c va segnalato allo stesso modo.
- **Carry per task.** Le decisioni del controller per un task finiscono in più sezioni di `carry.md`: le istruzioni di esecuzione dicono di leggerle tutte.

## File da scrivere (sul modello di P3b)

- `docs/superpowers/plans/2026-10-20-tollgate-p3c-percorso-l2.md`: il piano. Contiene la tabella Copertura che porta ogni criterio, vincolo e rinviato al suo task.
- `docs/superpowers/plans/2026-10-20-tollgate-p3c-esecuzione.md`: come eseguirlo con `superpowers:subagent-driven-development`.
  - **Dove:** ramo `p3c-percorso-l2`, in un worktree sotto `.claude/worktrees/p3c`.
  - **Come:** i modelli, lo scan pre-flight, le Ruling nel ledger, la revisione finale su opus, la suite tre volte (anche con `-W error::ResourceWarning`).
  - **Regole di cautela nel brief di ogni subagente, al lancio.** Le stesse di `docs/sdd/2026-10-19-tollgate-p3b-chiusura/cautele.md`, comprese il divieto di `pkill`, `killall` e `kill` per pattern e di `git stash`.
  - **Chiusura:** niente merge senza l'OK dell'utente. Registro copiato in `docs/sdd/`, memoria aggiornata, trascrizioni della cartella del worktree in `~/.claude/projects` spostate nella cartella della radice (solo se la sessione è partita dal worktree).
- `docs/superpowers/plans/2026-10-20-tollgate-p3c-brief-sessione.md`: il brief per la sessione che esegue il piano.

## Come lavorare

- Prima di consegnare, il piano passa a un revisore opus a contesto pulito, che lo confronta con la spec rev 23, con il piano principale e con il codice reale di `main`. I rilievi vanno corretti, e dopo le correzioni una ri-revisione mirata.
- All'utente si chiedono solo le scelte che sono compromessi veri. Il resto si decide e si registra nel piano, tra le decisioni. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.
- I tre file si committano su `main`, con la riga `Co-Authored-By` del modello.
- Testi in italiano, identificatori in inglese. Risposte all'utente brevi.

## Stato al momento di questo brief

- `main` contiene P3b (fino a `6da05bb`) e il suo registro (`9f57536`). La suite su `main` ha 1417 test verdi.
- Sulla macchina: Claude Code 2.1.304, `gh` 2.46.0 (senza `--slurp`), Superpowers 7.0.0.

## Hai finito quando

- i tre file sono committati su `main`;
- il piano copre ogni criterio, vincolo e rinviato destinato a P3c;
- la revisione del piano non ha rilievi critical o important aperti;
- hai consegnato all'utente, in italiano, un riepilogo breve (numero di task, decisioni prese, domande aperte) e il prompt `/goal` per la sessione che eseguirà il piano.
