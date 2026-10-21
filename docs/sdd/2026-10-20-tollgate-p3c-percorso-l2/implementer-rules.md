# Regole dell'implementatore (valgono per ogni task)

Rispondi e scrivi in italiano; identificatori in inglese.

## Prima di cominciare
Leggi il brief del tuo task (è i tuoi requisiti, con i valori esatti da usare alla lettera), poi `cautele.md` e `global-constraints.md` in questa stessa cartella, poi le voci di `carry.md` che nominano il tuo task, in qualunque sezione (sono anche copiate nel dispatch: decisioni del controller che prevalgono sul testo del piano). Il brief contiene firme e test, non il codice: il corpo lo scrivi tu, leggendo prima il codice esistente che tocchi e i suoi chiamanti. Le «Decisioni di questo piano» citate nel brief come «decisione N» sono in `decisions.md`, in questa cartella. Se qualcosa non è chiaro, fermati e riporta NEEDS_CONTEXT con domande precise. Non indovinare.

## Il lavoro
1. Implementa esattamente ciò che il task specifica, più le voci di `carry.md` che nominano il tuo task.
2. Segui il TDD: test che fallisce (RED), poi codice (GREEN).
3. Mentre lavori lancia i test mirati; prima del commit lancia `tests/run` (python3.11 e python3) una volta: deve essere verde e con output pulito.
4. Committa (mai amend, mai `--no-verify`). Il messaggio di commit finisce, dopo una riga vuota, con la riga `Co-Authored-By:` del tuo modello (per esempio `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`).
5. Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p3c` (ramo `p3c-percorso-l2`). Mai nel checkout principale. Il percorso contiene spazi: usa sempre le virgolette.
6. Nessun `__pycache__` nel repo (usa `python3 -B`); controlla `git status` prima di `git add`.

## Non lanci subagenti
Fai tutto da solo. Mai un subagente, mai un revisore: la revisione la fa il controller dopo il tuo report.

## Organizzazione del codice
Segui la struttura dei file del piano e i pattern del codice esistente (nomi, stile, densità dei commenti). Se un file cresce oltre le intenzioni del piano, o il codice esistente è aggrovigliato, segnalalo come DONE_WITH_CONCERNS. Non ristrutturare fuori dal task.

## Se il piano non funziona
Se un test o una firma del piano contraddice il codice reale o la spec (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, rev 23, che è l'autorità; la rev 24 la scrive il Task 15), correggi il minimo indispensabile perché rispetti la spec e scrivi nel report cosa hai cambiato rispetto al piano e perché. Se la correzione richiede una scelta architetturale, fermati: BLOCKED con i dettagli.

## Autorevisione prima del report
Completezza rispetto al brief e a `carry.md`; nomi chiari; niente extra non richiesti; test che verificano comportamento reale; output dei test pulito.

## Dopo i rilievi della revisione
Se vieni ripreso con dei rilievi: correggi, rilancia i test che coprono il codice cambiato, aggiungi in fondo al report un «Fix round N» con cosa hai cambiato, i test, il comando e l'output. Nuovo commit.

## Report
Scrivi il report completo nel file indicato nel dispatch: cosa hai implementato, test ed esiti, evidenza TDD (RED: comando e output del fallimento atteso; GREEN: comando e output), file cambiati, scostamenti dal piano e perché, risultati dell'autorevisione, dubbi.

Poi rispondi SOLO con (meno di 15 righe): **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT; commit (SHA corto + oggetto); riepilogo dei test in una riga; dubbi; percorso del report. Se BLOCKED o NEEDS_CONTEXT, metti i dettagli nel messaggio.
