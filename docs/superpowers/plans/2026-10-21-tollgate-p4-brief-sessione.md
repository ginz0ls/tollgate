# Brief per la sessione che esegue P4

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano P4 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-10-21-tollgate-p4-gate.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-10-21-tollgate-p4-esecuzione.md`: ramo `p4-gate`, worktree `.claude/worktrees/p4`, workspace SDD nel worktree, modelli, scan pre-flight, regole di cautela con le eccezioni per GitHub, chiusura.

Il lavoro è finito quando:
- tutti i 17 task sono `complete` nel ledger, ognuno con la revisione pulita;
- la revisione finale (opus) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, anche con `-W error::ResourceWarning`;
- il rapporto all'utente è consegnato, con la richiesta dell'OK per il merge.

**Il merge su `main` non si fa senza l'OK dell'utente.**

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-10-21-tollgate-p4-esecuzione.md`: le istruzioni.
2. Il piano: per intero «Decisioni di questo piano» (27 decisioni), «Review Focus» e «Copertura».
3. La spec rev 24, sezioni 1.2, 3, 3.1, 5 («Nel gate»), 8.2, 8.3, 8.7, 9 per intero, 11.2, 11.4, 13, 15 (criteri 10, 11, 18, 21, 22, 27, 29, 30, 32-36, 39, 41, 42, 44), 16, 18.1-18.5.
4. Il piano principale, sezione 3: «Gate installato», blocco 18.1, «Vincoli per P4» di P3b, «Contratti verso il gate» e «Vincoli per P4 emersi in P3c».
5. `docs/verifiche/2026-10-08-p0-esiti.md` (G1-G5) e `docs/verifiche/evidenze/gh/gh-evidenze.md`: i fatti di GitHub già provati, da **non** riprovare. `spikes/gh/run-gh-experiments.sh` come modello e come lezione (l'incidente delle uscite perse: nel Task 1 le uscite vanno direttamente sotto `docs/verifiche/evidenze/gh-p4/`).
6. `docs/sdd/2026-10-20-tollgate-p3c-percorso-l2/`: `README.md`, `progress.md` (forma delle `Ruling:`), `final-review.md` (triage), `cautele.md`, le regole per implementatori e revisori.
7. La memoria del progetto: `plugin-workflow-decisioni.md`, `feedback-domande.md`, `sessioni-nei-worktree.md`.

## Come abbiamo lavorato (non cambiarlo)

- **La spec è l'autorità, il piano è il suo argomento.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 2**, con le ruling, `carry.md` e i `task-N-carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` e dei `task-N-carry.md` che nominano il task (anche fuori dalla sua sezione) e le regole di cautela. Mai la storia della sessione.
- **Regole di cautela nel brief di ogni subagente, al lancio**, compreso il divieto di `pkill`, `killall` e `kill` per pattern e di `git stash`. Le eccezioni per GitHub non vanno mai a un subagente.
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`.
- **Testi in italiano, identificatori in inglese.** Risposte all'utente brevi.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i tre casi delle istruzioni.

## Punti delicati del piano

- **GitHub vero solo dal controller** (decisione 25): Task 1 e Task 16, solo su `ginz0ls/tollgate-p4-protected` (pubblico, `protected`) e `ginz0ls/tollgate-p4-detect` (privato, `detect`), solo con le operazioni elencate. I repo li crea il Task 1 e li cancella l'utente. Il repo pubblico riceve il codice di tollgate solo nel Task 16 e va cancellato appena chiusi i giri di correzione della revisione finale («pubblico solo per la prova», scelta dell'utente).
- **Sicurezza dei workflow** (decisioni 5 e 17, dalla revisione del piano): nessuno stato `success` «non applicabile»; checkout del ramo predefinito con `persist-credentials: false` in ogni workflow con permessi di scrittura; artefatti e cache estratti sotto `runner.temp`.
- **Strati** (decisione 1): `tollgate_gate` non importa mai `tollgate_core.db` né `sqlite3`, nemmeno indirettamente; `test_layers.py` lo controlla anche a runtime. Per questo il Task 2 estrae `runner`, `ghcli` e `diffcheck` senza cambiare i nomi visti dai chiamanti.
- **Un solo calcolo** (decisione 3): `evaluate` decide le voci rosse e quelle di `attenzione` sia nel gate sia in `finish check`. Una regola nuova va lì, mai in uno solo dei due.
- **Testo non fidato** (Global Constraints, decisione 17): nessuna `${{ }}` nelle righe `run:` dei workflow; i commenti si scrivono da file (`-F body=@file`); i nomi dei rami e i corpi delle PR non entrano mai in un argomento.
- **Conflitti della spec già risolti** (decisione 7): PR non `tg/*` e `tollgate-config/*` con `attenzione` rosso; `allow_no_tests` informativo solo con ricevute tutte `green`. Decisione 8: una PR manuale senza `Closes` non è rossa.
- **Casi lasciati da P3c** (decisione 22): l'approvazione corrente vince su quella propria superata; cambiano alcuni test esistenti, ed è voluto.
- **Il Task 1 può smentire il disegno**: V2 (forma di `gh api --include`), V3 (campi degli eventi) e V4 (cache tra `workflow_run` e `pull_request`) reggono le decisioni 12, 16 e 18. Una forma diversa diventa una `Ruling:` prima dei Task 8-12.

## Stato al momento di questo brief

- `main` contiene P3c (fino a `3aa47c2`), il suo registro (`7e20855`), il brief di scrittura di P4 (`8dbd280`) e i tre file di questo piano. La suite su `main` ha 1753 test verdi.
- Sulla macchina: Claude Code 2.1.305, `gh` 2.46.0 (senza `--slurp`), Superpowers 7.0.0. Il token di `gh` ha gli scope `gist`, `read:org`, `repo`, `workflow` (P0); nessun `delete_repo`.
- Le trascrizioni delle sessioni nei worktree vanno spostate a fine lavoro nella cartella della radice, solo se la sessione è partita dal worktree (`sessioni-nei-worktree.md`).
