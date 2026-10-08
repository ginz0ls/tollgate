---
name: probe-worktree
description: Sonda P0 per EnterWorktree.
disable-model-invocation: true
---
Usa lo strumento EnterWorktree per entrare nel worktree il cui percorso è scritto nel file /tmp/tollgate-p0/worktree-path.txt. Poi esegui `git rev-parse --abbrev-ref HEAD` e `pwd` con Bash e riporta l'output esatto. Se EnterWorktree rifiuta il percorso, riporta il messaggio d'errore esatto.
