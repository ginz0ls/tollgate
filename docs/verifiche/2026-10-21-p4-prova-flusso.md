# Prova reale del flusso L1 con `claude -p` (P4, decisioni 26 e 27)

Versioni: Claude Code [da compilare] (`claude --version`), tollgate [da compilare] (`tollgate_core.VERSION`), modello `sonnet`. Data: [da compilare].

Piano: Task 16 di P4, Step 5. Script: `spikes/run-p4-flow.sh` (`issue`, `prepara`, `shim`, `passo1`, `passo2`, `passo3`, `attendi`, `passo4`, `registra`, `controlla`);
controlli in `spikes/gh-p4/flowcheck.py`. Uscite grezze in `docs/verifiche/evidenze/gh-p4/flusso/` (mai cancellate): `passo*.jsonl` (stream-json), `*.argv`,
`events-*.jsonl`, `*-eventi.txt`, `*-gh-modello.txt`, `*-comandi-bash.txt`, `gh-wrap.log`, `attendi-esito.txt`, `shim-esito.txt`, `ricapitolo.txt`.

**Esito: [da compilare: riuscito / composito / non riuscito].**

## Modello di minaccia e garanzia

Il modello è cooperativo: esegue le skill di tollgate. `--disallowedTools` e il gh con guardia (wrapper generato, valori fissati nel file) sono un primo argine; l'audit dei comandi (`flowcheck.py audit`) copre i vettori che elenca (gh per percorso o dietro un prefisso, `git push` ovunque nella stringa, `eval`, `python -c`, manomissioni dei file della guardia e del registro) ed è un segnale. La **garanzia** è la verifica dello stato prima e dopo ogni passo (`flowstate.py`, `<passo>-stato.txt`): hash di wrapper, guardia e script, registro `gh-wrap.log` copiato e solo crescente, `git ls-remote` con `main` invariato e soli `refs/heads/tg/*` avanzati senza forzature, PR, issue e protezione di `main` invariate. Non impedisce un effetto: lo rileva, qualunque comando lo abbia prodotto, e rende il passo «non riuscito» (uscita 3). Per il rapporto: [da compilare: esito della verifica per ogni passo].

## Impianto

- Cartella `/tmp/tollgate-p4/flow`: clone di `ginz0ls/tollgate-p4-protected` in `protected/`, stato `state/` con la sentinella `.tollgate-test`, `shim/gh` (gh finto, solo per il passo `shim`),
  `ghbin/gh` (gh con guardia: ogni gh del modello e della CLI passa da `ghguard.py`, profilo `flow`). **Nessuna `TOLLGATE_GH`**: il flusso usa il gh vero, solo su protected.
- `claude -p` sempre da `/tmp/tollgate-p4/flow` (checkout o worktree del lavoro), con `--plugin-dir` sul worktree del ramo `p4-gate`, `--model sonnet`, `--permission-mode acceptEdits`,
  `--allowedTools Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob`, `--disallowedTools` per `gh repo`, `gh api`, `gh auth`, `gh secret`, `gh issue create`.
  Prima di ogni passo `git remote get-url --push origin` deve essere protected.
- Issue di prova: #[da compilare] (`dividi(a, b)` in `src/calc.py` con `test_dividi`).

## Sessioni reali (id e cartella)

| Passo | Sessione | Cartella |
|---|---|---|
| shim | [da compilare] | |
| 1 | [da compilare] | |
| 2 | [da compilare] | |
| 3 | [da compilare] | |
| 4 (se serve) | [da compilare] | |

## Passi ed esiti

| Passo | Prompt | Esito | Evidenza |
|---|---|---|---|
| shim | `command -v gh` e `echo "$PATH"` (gh finto, senza rete) | | `shim-esito.txt` |
| 1 | `/tollgate:start #N L1` | | |
| 2 | piano e `/tollgate:execute` | | |
| 3 | `/tollgate:finish` fino a `finish open-pr` | | |
| attendi | stati della PR | | `attendi-esito.txt` |
| 4 | solo se `verdict` è rosso: `/tollgate:start #N` e `task start --from-gate`, un solo giro | | |

Esito atteso: PR aperta dal flusso, `tollgate/guard` e `tollgate/verdict` `success`, commento con il marcatore e lo SHA della testa.

## PR, stati e veti

- PR: #[da compilare], ramo `tg/N-*`, testa [da compilare].
- Stati con autore: [da compilare]. Commento del gate con il marcatore `<!-- tollgate-verdict sha=<testa> -->`: [da compilare].
- Veti ed eventi `effect_*` per passo (`*-eventi.txt`): [da compilare]. gh del modello (`*-gh-modello.txt`): [da compilare].

## Token e costi

`bin/tollgate stats`: [da compilare]. Costo riportato da `claude -p` per passo: [da compilare].

## PATH del tool Bash

Uscita del tool Bash per `command -v gh` nel passo `shim`: [da compilare]; confronto con lo shim: [da compilare] (vincolo P3c (4)).

## Difetti e osservazioni

[da compilare]

## Ciò che resta non esercitato

[da compilare]
