# Ri-revisione 2 del Task 13 (giri di correzione 2 e 3, ef3f8d2..7f499d9)

### Verdetti sui rilievi
**Aggancio del run di guard di pulita-fissata sbagliato (ripiego temporale).** INDIRIZZATO. `spikes/run-p5-gate.sh:244-279`: con `fb=1` il filtro è `headBranch == ramo della PR` e `event == pull_request_target` (riga 529), senza ripiego temporale; su detect il guard 40225942870 ha esattamente quel ramo ed evento, il 40225794682 (ramo `tollgate-config/0.2.0`) è scartato. Il tetto senza run dà «nessun run» e la riga `pulita-fissata-aggancio` (righe 549-550).

**Ruling verdict (workflow_run, headBranch del predefinito): primo run creato dopo la fine del tollgate-run della PR, nessun filtro per ramo.** INDIRIZZATO. Righe 252-256 (`fb=2`): `event == $e and createdAt >= $a`, `sort_by(createdAt, databaseId) | first`. Prova mirata con jq sui dati veri (40225810127 @19:23:32, 40226084067 @19:27:01, 40225962034 @19:25:26; after = 19:25:24Z): sceglie 40225962034. Il confronto di date è tra stringhe ISO ma sono tutte nel formato `YYYY-MM-DDTHH:MM:SSZ` di gh (stesso fuso, stessa larghezza), quindi lessicografico = cronologico: nessun difetto. `RUN_END` = `updatedAt` di `run view` (riga 287), riempito prima del verdict (righe 533-539); se manca, il verdict resta «non determinato» e non si cerca (fail-closed). Il gh finto riproduce la forma vera (headBranch `main`, uno prima, uno dopo) e `controlla` verifica id < 800000; test `test_runs_are_matched_by_branch_not_by_recency`.

**Verifica del controller (verdict ha headBranch main).** INDIRIZZATO: nessun filtro per ramo sul verdict.

### Danni nuovi nel diff della correzione
Nessun Critical/Important.
- Minor, righe 252-256: due PR in parallelo. Un verdict di un'altra PR creato tra la fine del tollgate-run (`updatedAt`) e il verdict giusto (osservato +2 s) verrebbe preso al posto del giusto, e il «Cache mode» letto sarebbe quello sbagliato. È un limite, non un difetto: il controller lavora con una sola PR di prova aperta (PR aperte 0 a ogni raccolta), la finestra è di secondi, e un `workflow_run` non porta SHA né ramo della PR. Va dichiarato nel commento di `wait_run` e nel rapporto (`docs/verifiche/2026-10-23-p5-prova-gate.md`), oggi non lo è.
- Minor, righe 252-256: `createdAt >= updatedAt` senza tolleranza. Se `updatedAt` superasse di un secondo la creazione del verdict (osservato il contrario, +2 s), il giusto verrebbe scartato; con una sola PR l'esito è «non determinato» (visibile, non silenzioso).
- Minor, `spikes/run-p5-gate.sh` ~righe 517-518: commento stale, dice ancora «guard e verdict si cercano col ripiego "il più recente creato negli ultimi minuti"».

### Altri casi (regressioni)
- `rivalutazione`: nessuna regressione. Non usa `fb=1` né `fb=2`: `track ... 0` senza evento (riga 612), per SHA o ramo come in common.sh; il secondo verdict si segue dagli stati. Aggancia sempre il tollgate-run della prima valutazione.
- `aggiorna` (417), `rifiuto-v4` (589), `skip-ci` (430-431, 692, 720, sentinella con ramo vuoto): `fb=0`, `ev` vuoto, stesso filtro `headSha == sha or (ramo != "" and headBranch == ramo)` e stesso `sort_by(databaseId) | last` di common.sh. Il gh finto per la sentinella `push` non è cambiato (ramo `else` solo per gli altri workflow). `bash -n` ok.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. Restano 3 minor (limite delle due PR in parallelo da dichiarare, nessuna tolleranza su `updatedAt`, commento stale).
