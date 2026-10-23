---
name: prova
description: Sonda di tollgate P5 (VE3, VE6, VE9): lancia bin/sonda e il subagente della sonda. Solo per i casi di eval.
disable-model-invocation: true
---

Esegui, nell'ordine, senza aggiungere altro:

1. Con lo strumento Bash lancia `python3 "${CLAUDE_PLUGIN_ROOT}/bin/sonda"` e riporta la sua uscita.
2. Lancia il subagente `sonda:sonda-sub` (strumento Agent) con l'istruzione di eseguire il suo comando, e riporta la sua risposta.
3. Chiudi con una riga che dice quali passi sono riusciti.
