# Task 16 — giro di correzione 2

Leggi `task-16-rereview-1.md` (stessa cartella). Cautele invariate: solo `bash -n` e `controlla`, test offline, mai rete, mai gh vero, mai `claude`.

## Ruling del controller su R-1
Non inseguire altre forme di comando: l'elenco dei vettori non si chiude (python, eval, symlink, timeout, alias, ...). La garanzia vincolante diventa **la verifica dello stato**, non la lettura dei comandi. L'audit dei comandi resta come segnale aggiuntivo, con una sola estensione economica.

1. **Verifica dello stato prima e dopo ogni passo di `claude -p`** (in `claude_step` o equivalente), registrata nelle evidenze con rotazione:
   - hash (sha256) di ghbin/gh, `ghwrap.py`, `ghguard.py`, `flowcheck.py` e dello script stesso: devono essere invariati;
   - copia del registro `gh-wrap.log` subito dopo ogni passo nelle evidenze (così troncarlo dopo non cancella ciò che era già stato copiato), e controllo che il registro sia solo cresciuto (il nuovo inizia con il vecchio);
   - `git ls-remote origin` completo: `main` invariato; nessun ref cancellato; i ref nuovi o aggiornati sono solo `refs/heads/tg/*`; un ref `tg/*` già esistente aggiornato deve avere il vecchio SHA come antenato (nessun push forzato), verificato con `git merge-base --is-ancestor` dopo un fetch;
   - stato GitHub in sola lettura con le operazioni ammesse (`gh pr list --state all --json number,state,headRefName,baseRefName,mergedAt`, `gh issue list --state all --json number,state`, `gh api repos/ginz0ls/tollgate-p4-protected/branches/main/protection`): nessuna PR unita o chiusa e nessuna issue chiusa fuori dagli eventi attesi del passo; protezione di `main` identica a prima.
   Qualsiasi differenza rende il caso «non riuscito» con riga esplicita e ferma lo script (exit != 0). Le letture passano dallo `gh` con guardia del controller (profilo script), non dal wrapper del flusso.
2. **Audit dei comandi:** in `flowcheck.py`, `risky` segnala anche qualsiasi occorrenza di `git push` nella stringa grezza del comando (non solo come prima parola), di `eval`, `python`/`python3 -c`, `ln -s`, `chmod`, `rm`, `mv`, `sed -i`, `truncate` o `>` che toccano i file di ghbin, della guardia o il registro. È un segnale, non la garanzia.
3. **Commento dello script e scheletro del rapporto della prova:** dichiarano in modo esplicito il modello di minaccia: il modello è cooperativo (esegue le skill di tollgate); `--disallowedTools` e il wrapper sono un primo argine; l'audit dei comandi copre i vettori elencati; la garanzia è la verifica dello stato del punto 1, che rileva ogni effetto fuori elenco su GitHub qualunque sia il comando che lo ha prodotto; non previene un effetto, lo rileva e ferma la prova.

## N-1 (minor)
Il wrapper scarta anche `GH_HOST`, `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`, `GH_CONFIG_DIR`, `BASH_ENV`, `ENV` (non leggere mai i valori; scartali e basta). Test con ambiente ostile.

## N-2 (minor)
Il confronto transcript/registro usa la riga di comando completa normalizzata (tokenizzata con `shlex`), non le prime due parole; oppure il rapporto lo descrive esattamente com'è. Scegli il confronto completo se costa poco.

Test RED prima delle correzioni (con gh finto e `git` su repo locali bare sotto una cartella temporanea per la verifica dei ref: push forzato, cancellazione, push su main, ref non `tg/*` → «non riuscito»; hash del wrapper cambiato → «non riuscito»; registro troncato → «non riuscito»). Commit nuovo «tollgate P4: verifica dello stato attorno ai passi del flusso (Task 16, giro 2)» con la riga esatta «Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>». Sezione «Giro 2» nel report.
