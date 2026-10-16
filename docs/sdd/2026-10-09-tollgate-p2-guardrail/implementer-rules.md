# Regole dell'implementatore (valgono per ogni task)

Rispondi e scrivi in italiano; identificatori in inglese.

## Prima di cominciare
Leggi il brief del tuo task (è i tuoi requisiti, con i valori esatti da usare alla lettera), poi `cautele.md` e `global-constraints.md` in questa stessa cartella, poi le voci del tuo task in `carry.md` (decisioni del controller che prevalgono sul testo del piano). Se qualcosa non è chiaro, fermati e riporta NEEDS_CONTEXT con domande precise. Non indovinare.

## Il lavoro
1. Implementa esattamente ciò che il task specifica, più le voci di `carry.md` per il tuo task.
2. Segui il TDD dove il task lo indica: test che fallisce (RED), poi codice (GREEN).
3. Mentre lavori lancia i test mirati; prima del commit lancia `tests/run` (python3.11 e python3) una volta: deve essere verde e con output pulito.
4. Committa (mai amend, mai `--no-verify`). Il messaggio di commit finisce, dopo una riga vuota, con la riga `Co-Authored-By:` indicata dal tuo promemoria di sessione (quella del tuo modello).
5. Lavora solo nel worktree `/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p2-guardrail` (ramo `p2-guardrail`). Mai nel checkout principale.
6. Nessun `__pycache__` nel repo (usa `python3 -B`).

## Non lanci subagenti
Fai tutto da solo. Mai un subagente, mai un revisore: la revisione la fa il controller dopo il tuo report.

## Organizzazione del codice
Segui la struttura dei file del piano. Se un file cresce oltre le intenzioni del piano, o il codice esistente è aggrovigliato, segnalalo come DONE_WITH_CONCERNS. Non ristrutturare fuori dal task.

## Se il codice del piano non funziona
Se un test o un blocco di codice del piano fallisce, correggi il minimo indispensabile perché rispetti la spec (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`) e scrivi nel report cosa hai cambiato rispetto al piano e perché. Se la correzione richiede una scelta architetturale, fermati: BLOCKED con i dettagli.

## Autorevisione prima del report
Completezza rispetto al brief e a `carry.md`; nomi chiari; niente extra non richiesti; test che verificano comportamento reale; output dei test pulito.

## Dopo i rilievi della revisione
Se vieni ripreso con dei rilievi: correggi, rilancia i test che coprono il codice cambiato, aggiungi in fondo al report un «Fix round N» con cosa hai cambiato, i test, il comando e l'output. Nuovo commit.

## Report
Scrivi il report completo nel file indicato nel dispatch: cosa hai implementato, test ed esiti, evidenza TDD (RED: comando e output del fallimento atteso; GREEN: comando e output), file cambiati, scostamenti dal piano e perché, risultati dell'autorevisione, dubbi.

Poi rispondi SOLO con (meno di 15 righe): **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT; commit (SHA corto + oggetto); riepilogo dei test in una riga; dubbi; percorso del report. Se BLOCKED o NEEDS_CONTEXT, metti i dettagli nel messaggio.
