# Brief per la sessione che esegue P3c

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano P3c senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-10-20-tollgate-p3c-percorso-l2.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-10-20-tollgate-p3c-esecuzione.md`: ramo `p3c-percorso-l2`, worktree `.claude/worktrees/p3c`, modelli, scan pre-flight, regole di cautela, chiusura.

Il lavoro è finito quando:
- tutti i 15 task sono `complete` nel ledger, ognuno con la revisione pulita;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, anche con `-W error::ResourceWarning`;
- il rapporto all'utente è consegnato, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-10-20-tollgate-p3c-esecuzione.md`: le istruzioni.
2. Il piano: per intero «Decisioni di questo piano» (27 decisioni), «Rilievi ripresi qui», «Review Focus» e «Copertura».
3. La spec rev 23, sezioni 0 (glossario: ciclo vuoto, lenti e punti di vista), 3, 3.1, 5 (fette), 6.1, 6.2, 8.4, 8.7, 11.4, 12.2-12.4, 15 (criteri 18, 24, 35, 37, 41), 18.1, 18.3, 18.4.
4. Il piano principale, sezione 3: contratti reali di P3a e P3b, «Vincoli per P3c».
5. `docs/sdd/2026-10-19-tollgate-p3b-chiusura/`: `README.md`, `progress.md` (forma delle `Ruling:`), `final-review.md` (triage), `deferred-minors.md` (le righe citate dai Task 11-13 del piano), `cautele.md`, le regole per implementatori e revisori.
6. La memoria del progetto: `plugin-workflow-decisioni.md`, `feedback-domande.md`, `sessioni-nei-worktree.md`.
7. Per il metodo dell'audit a lenti: `~/.claude/skills/prd-audit/SKILL.md` e `references/dimensioni.md` (il Task 13 copia il secondo nella skill `spec-audit`).

## Come abbiamo lavorato (non cambiarlo)

- **La spec è l'autorità, il piano è il suo argomento.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 2**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task (anche fuori dalla sua sezione) e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio**, compreso il divieto di `pkill`, `killall` e `kill` per pattern e di `git stash`.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i tre casi delle istruzioni.

## Punti delicati del piano

- **Strati.** Le regole pure (`specdoc`, `auditrules`, `approvals`) stanno in `tollgate_analysis` perché P4 le riusa; `audit_round` (hook) non scrive file né DB: lo fa l'operazione `audit_report` in `tollgate_hooks/apply.py`; `l2acts` non importa `actapply`.
- **Documento letto a HEAD** (decisione 3): ogni giro e ogni approvazione guardano il blob in HEAD, e rifiutano se il worktree è diverso. I report non committati non contano.
- **Cause nuove per i passaggi L2** (decisione 11): `spec_audit → plan` solo con `approve_spec`, `plan → approval` solo con `audit_clean`, `approval → execution` solo con `approve_plan`. Cambiano alcuni test di `test_phases.py`.
- **Tetti e sospensioni** (decisione 7): `resolve` sul blocco di un tetto dell'audit scrive la sospensione in `work_items.audit_suspended`; una sospensione avversariale vale solo per il giro sospeso.
- **Approvazione della spec di un lavoro** (decisione 13): `locate_spec_approval` trova anche l'approvazione di un'altra issue (fette successive). È usata da sei moduli: stessa firma ovunque.
- **File di `reviews/<N>/` esenti dallo scope dei commit** (decisione 26): senza, dopo `approve plan` ogni commit del lavoro sarebbe negato. È il rilievo critico della revisione del piano.
- **`reopen`** (decisione 12) toglie la registrazione del piano (`scope.reset_plan`): i task tornano `pending` e vanno rieseguiti.
- **Nessun push in rete**: nei test e nel Task 14 solo verso repo nudi locali in cartelle temporanee. Nel Task 14, dal passo 2, `claude -p` parte dal worktree.

## Stato al momento di questo brief

- `main` contiene P3b (fino a `6da05bb`), il suo registro (`9f57536`), il brief di scrittura di P3c (`acacf4f`) e i tre file di questo piano. La suite su `main` ha 1417 test verdi.
- Sulla macchina: Claude Code 2.1.304, `gh` 2.46.0 (senza `--slurp`), Superpowers 7.0.0.
- Le trascrizioni delle sessioni nei worktree vanno spostate a fine lavoro nella cartella della radice, solo se la sessione è partita dal worktree (`sessioni-nei-worktree.md`).
