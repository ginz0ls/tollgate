# Brief per la sessione che esegue P3b

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano P3b senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-10-19-tollgate-p3b-chiusura.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-10-19-tollgate-p3b-esecuzione.md`: ramo `p3b-chiusura`, worktree `.claude/worktrees/p3b`, modelli, scan pre-flight, regole di cautela, chiusura.

Il lavoro è finito quando:
- tutti i 18 task sono `complete` nel ledger, ognuno con la revisione pulita;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, anche con `-W error::ResourceWarning`;
- il rapporto all'utente è consegnato, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-10-19-tollgate-p3b-esecuzione.md`: le istruzioni.
2. Il piano: per intero «Decisioni di questo piano» (26 decisioni), «Rilievi ripresi qui», «Review Focus» e «Copertura».
3. La spec rev 22, sezioni 3.1, 6.4, 6.5, 8.4, 8.6, 8.7, 10, 12.2-12.4, 15, 18.1, 18.5.
4. Il piano principale, sezione 3: contratti reali di P3a e i vincoli per P3b.
5. `docs/sdd/2026-10-16-tollgate-p3a-avvio-e-task/`: `README.md`, `progress.md` (forma delle `Ruling:` e incidente del `pkill`), `final-review.md` (triage), `cautele.md`, le regole per implementatori e revisori.
6. La memoria del progetto: `plugin-workflow-decisioni.md`, `feedback-domande.md`, `sessioni-nei-worktree.md`.

## Come abbiamo lavorato (non cambiarlo)

- **La spec è l'autorità, il piano è il suo argomento.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 2**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono. Gli esiti del Task 1 vanno subito in `carry.md` del Task 9.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, le decisioni da `carry.md` e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio**, compreso il divieto di `pkill`, `killall` e `kill` per pattern.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i tre casi delle istruzioni.

## Punti delicati del piano

- **Strati.** `finish check` sta in `tollgate_flow` e non può importare `tollgate_checks`: per questo il Task 4 sposta le violazioni in `tollgate_core.violations`. La suite degli hook deve restare verde senza toccare i test.
- **Programma nei comandi** (`paths.program_command`) e **segnale della CLI** con `argv` consumato (Task 2): ogni sottocomando nuovo che legge la sessione lo usa.
- **Ciclo di revisione** (decisioni 5-7): un codice per ciclo, stadi `review`/`verify`/`closed`, `review prepare` rientrante; un revisore `interrupted` per sola lettura vale ancora.
- **`open-pr`** (decisione 10): l'atto si consuma **per ultimo**; il push forzato solo con un intento `force_push`.
- **Blocco JSON 18.1** (decisione 11): è il contratto con P4. `prblock.FIELDS`, `render` e `parse` vanno fissati esattamente.
- **Nessun push in rete**: nei test e nel Task 17 solo verso repo nudi locali in cartelle temporanee.

## Stato al momento di questo brief

- `main` contiene P3a (fino a `ab64a9a`), il registro di P3a e i tre file di questo piano. La suite su `main` ha 997 test verdi.
- Sulla macchina: Claude Code 2.1.303, `gh` 2.46.0 (senza `--slurp`), Superpowers 7.0.0.
- Le trascrizioni delle sessioni nei worktree vanno spostate a fine lavoro nella cartella della radice (`sessioni-nei-worktree.md`).
