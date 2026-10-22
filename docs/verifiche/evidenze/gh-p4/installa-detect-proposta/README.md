# Proposta di installazione di tollgate

Preparata il 2026-10-22T10:24:56.384024Z da tollgate 0.1.0. I file qui sotto sono una proposta: li copi tu, tollgate non scrive mai nel repo i propri file.

## Modalità del gate

Repo privato con GitHub Free: la protezione del ramo non è disponibile. Modalità `detect`: il merge non è impedito; `tollgate-sentinel` segnala a valle i merge non verificati.

## I tuoi passi

1. Copia il contenuto di `docs/superpowers/tollgate-init/files` nella radice del repo (per esempio `cp -R docs/superpowers/tollgate-init/files/. .`).
2. Fai un commit sul ramo predefinito (`main`) e spingilo, prima di attivare la protezione: il commit fa partire `tollgate-base`.
3. Nessuna protezione da attivare: in `detect` la verifica avviene dopo il merge, con `tollgate-sentinel`.

## Stima dei minuti di Actions

Durata del gate non misurata: manca una ricevuta di `finish check` o `verify` per ogni comando del gate sullo stesso commit. Chiudi un lavoro con /tollgate:finish e rilancia /tollgate:init.
Riferimento: GitHub Free include 2.000 minuti al mese per i repo privati.

## Token dell'agente

Per l'agente usa un token GitHub separato dal tuo, con soli permessi su contenuti, pull request e issue: senza amministrazione e senza `project`. Con il tuo token l'agente potrebbe cambiare la protezione del ramo.
