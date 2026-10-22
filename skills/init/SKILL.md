---
name: init
description: Prepara l'installazione del gate di tollgate su GitHub: misura la modalità (protected o detect) e scrive una proposta con i file da copiare e i passi dell'utente. Non scrive mai nel repo.
argument-hint: "[--propose|--update] [--merges-per-month N] [--service NOME=IMMAGINE[,PORTA]]"
---

Sei il redattore di una proposta: lanci il comando, riferisci cosa ha misurato, elenchi all'utente i passi del `README.md` che il comando scrive. L'installazione la fa l'utente.

**Programma:** `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"`: l'interprete seguito dal percorso, sempre tra virgolette (il percorso può contenere spazi; senza `python3` davanti Claude Code rifiuta in un worktree un percorso con spazi). Se la variabile non risulta espansa nel testo, usa il comando `python3 <percorso>` della riga `tollgate: programma` del contesto. Se risponde «tollgate richiede Python >= 3.11», riprova con `python3.11` al posto di `python3`. Nel seguito `<programma>` indica il comando intero, cioè l'interprete più il percorso (`python3 "…/bin/tollgate"`), non il solo percorso.

**Regole ferme:** mai copiare i file al posto dell'utente, mai lanciare `protect.sh`. I file di tollgate (workflow, `tollgate.toml`) sono protetti dai hook: li copia l'utente, e la protezione del ramo la attiva lui con le sue credenziali di `gh`. Il comando non scrive su GitHub.

## 1. Prima di lanciare

Lancia dal **checkout principale**, nel repo da installare. Prima di lanciare chiedi all'utente due cose, senza assumere:

- **I servizi dei test** (per esempio un database): per ciascuno nome, immagine ed eventuale porta. Entrano in ogni job che esegue la suite del progetto: `head` e `base` di `tollgate-run`, `ids` di `tollgate-base` e si passano con `--service NOME=IMMAGINE` oppure `--service NOME=IMMAGINE,PORTA` (la virgola, perché i due punti sono del tag dell'immagine; con la porta il servizio è raggiungibile dal job sull'host). L'opzione si ripete. Senza servizi, nessuna opzione.
- **Il ritmo di merge**: quanti merge al mese, per la stima dei minuti di Actions. Si passa con `--merges-per-month N`; senza, il comando assume 20.

## 2. Lancio

```
<programma> init --propose [--merges-per-month N] [--service NOME=IMMAGINE[,PORTA]]
```

Con `--update` al posto di `--propose` il comando propone solo i file che differiscono dal ramo predefinito (dopo un aggiornamento di tollgate): serve che `tollgate.toml` esista già sul ramo predefinito. Le due opzioni si escludono.

## Codici d'uscita

- **0, proposta scritta**: la cartella `docs/superpowers/tollgate-init/` contiene `README.md`, `files/` e, in `protected` con protezione da attivare, `protection.json` e `protect.sh`. Con `--update` e niente di diverso, il comando dice «nulla da aggiornare» ed esce 0 senza scrivere.
- **1, rifiuto**: righe `tollgate: …` col motivo (nessun repo git, nessun `origin`, nessun ramo predefinito, `tollgate.toml` non valido, servizio non ammesso, modalità non determinata). Riportale così come sono e fermati.

Le righe `avviso:` (per esempio «senza rete») e le righe `workflow esistente fuori regola` vanno sempre mostrate all'utente.

## 3. Cosa riferire

- **La modalità misurata**: la riga `modalità del gate: protected` o `detect`. In `detect` (repo privato con GitHub Free) la protezione del ramo non esiste: il merge non è impedito e `tollgate-sentinel` segnala a valle i merge non verificati. In `protected` la riga può dire che il ramo è senza protezione e che la attiva `protect.sh`; le righe `protezione incompleta: manca …` dicono cosa `protect.sh` deve portare a posto.
- **Modalità non determinata**: la protezione non si legge con le credenziali in uso (di solito il token dell'agente, senza amministrazione). Il comando rifiuta e non sceglie `protected` per esclusione. Di' all'utente di rilanciare con le sue credenziali, digitando `! <programma> init --propose …` con il programma e le opzioni scritti per intero; l'output entra nella sessione.
- **La stima dei minuti di Actions**: dal `README.md`. Se dice che la durata del gate non è misurata, serve prima chiudere un lavoro con `/tollgate:finish` e poi rilanciare.

## 4. I passi dell'utente

Leggi `docs/superpowers/tollgate-init/README.md` e riporta i passi nell'ordine in cui il file li scrive. Sono dell'utente, non tuoi.

Prima installazione (`--propose`):

1. Copiare il contenuto di `docs/superpowers/tollgate-init/files` nella radice del repo (per esempio `cp -R docs/superpowers/tollgate-init/files/. .`). Se `tollgate.toml` viene dal modello, prima compilare `[commands]` (`setup`, `verify`, `report`).
2. Committare sul ramo predefinito e spingere, **prima** di attivare la protezione: il commit fa partire `tollgate-base`.
3. Solo in `protected` con protezione da attivare: quando `tollgate-base` è finito su quel commit, lanciare `bash docs/superpowers/tollgate-init/protect.sh` dalla radice del repo, con le proprie credenziali. Se il commit non è la punta di `origin/<ramo>`, lo SHA va come primo argomento.
4. In `detect` non c'è niente da attivare: la verifica avviene dopo il merge.

Aggiornamento (`--update`): l'utente crea il ramo `tollgate-config/<versione>` dal ramo predefinito, copia i file della proposta sopra gli esistenti, cancella i file elencati in «Da cancellare», fa il commit e **apre lui la PR**: contiene solo file di tollgate, `guard` la lascia passare e `attenzione` resta rosso, come previsto.

Il `README.md` può avere altre sezioni, da riferire se presenti: i servizi messi in `tollgate-run`, i workflow già presenti che violano le regole di `guard` (da valutare, restano fuori dal controllo), la configurazione di `jest-junit` per i repo che usano jest.

## 5. Il token dell'agente

Consiglia all'utente un token GitHub **separato** per l'agente, con soli permessi su contenuti, pull request e issue: senza amministrazione e senza `project`. Con il suo token l'agente potrebbe cambiare la protezione del ramo.
