---
name: leggi
description: Sonda di tollgate B1. Lancia il subagente probe:lettore con i passi di lettura dati dall'utente, più il passo finale dell'heredoc.
---

Lancia con lo strumento Agent il subagente `probe:lettore`. Come istruzioni gli dai, alla lettera, i passi che l'utente ti ha scritto, seguiti dal passo finale qui sotto, senza aggiungere né togliere nulla. Poi riporta la sua risposta.

Passo finale (Bash): fagli eseguire questo comando in un'unica chiamata, copiato alla lettera, comprese le righe interne e i backtick:

~~~~
python3 "${CLAUDE_PLUGIN_ROOT}/bin/eco" <<'NOTA_DI_RICERCA_FINE'
Nota di prova con `backtick` e un blocco:
```python
print("ciao")
```
EOF
La riga sopra è una finta chiusura.
Variabile non espansa: $HOME e $(echo no)
NOTA_DI_RICERCA_FINE
~~~~
