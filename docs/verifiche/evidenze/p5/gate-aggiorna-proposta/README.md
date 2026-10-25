# Proposta di installazione di tollgate

Preparata il 2026-10-25T19:23:10.685814Z da tollgate 0.2.0. I file qui sotto sono una proposta: li copi tu, tollgate non scrive mai nel repo i propri file.

## Modalità del gate

Repo privato con GitHub Free: la protezione del ramo non è disponibile. Modalità `detect`: il merge non è impedito; `tollgate-sentinel` segnala a valle i merge non verificati.

## I tuoi passi

1. Crea il ramo `tollgate-config/0.2.0` dal ramo predefinito `main`.
2. Copia i file di `docs/superpowers/tollgate-init/files` nella radice del repo, sopra gli esistenti.
3. Fai un commit sul ramo e apri la PR: contiene solo file di tollgate, `guard` la lascia passare e `attenzione` resterà rosso, come previsto.
4. Nessuna protezione da attivare: in `detect` la verifica avviene dopo il merge, con `tollgate-sentinel`.

## Stima dei minuti di Actions

Durata del gate non misurata: manca una ricevuta di `finish check` o `verify` per ogni comando del gate sullo stesso commit. Chiudi un lavoro con /tollgate:finish e rilancia /tollgate:init.
Riferimento: GitHub Free include 2.000 minuti al mese per i repo privati.

## Token dell'agente

Per l'agente usa un token GitHub separato dal tuo, con soli permessi su contenuti, pull request e issue: senza amministrazione e senza `project`. Con il tuo token l'agente potrebbe cambiare la protezione del ramo.
