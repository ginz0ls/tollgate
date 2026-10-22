# Prova reale del flusso L1 con `claude -p` (P4, decisioni 26 e 27)

Versioni: Claude Code 2.1.305 (`claude --version`), tollgate 0.1.0 (`tollgate_core.VERSION`), modello `sonnet` (nei flussi stream-json: `claude-sonnet-5-5`). Data: 22 ottobre 2026, dalle 19:19 alle 19:24 UTC circa.

Piano: Task 16 di P4, Step 5. Script: `spikes/run-p4-flow.sh` (`issue`, `prepara`, `shim`, `passo1`, `passo2`, `passo3`, `attendi`, `passo4`, `registra`, `controlla`);
controlli in `spikes/gh-p4/flowcheck.py`. Uscite grezze in `docs/verifiche/evidenze/gh-p4/flusso/` (mai cancellate): `passo*.jsonl` (stream-json), `*.argv`,
`events-*.jsonl`, `*-eventi.txt`, `*-gh-modello.txt`, `*-comandi-bash.txt`, `gh-wrap.log`, `attendi-esito.txt`, `shim-esito.txt`, `ricapitolo.txt`.

**Esito: riuscito.** Quattro invocazioni di `claude -p` (shim, passo 1, 2 e 3), tutte con uscita 0, una sola esecuzione di ciascuna (nessun tentativo ripetuto in questa prova). PR #105 aperta dal flusso, `tollgate/guard` e `tollgate/verdict` `success`, `mergeStateStatus` `CLEAN`. Il passo 4 non è servito (verdict non rosso). Il protected usato è però quello già aggiornato con i ritentativi di D-3 e D-4 (b86dc8d): la prova del gate che lo precede è composita (vedi `2026-10-21-p4-prova-gate.md`), non questa.

## Modello di minaccia e garanzia

Il modello è cooperativo: esegue le skill di tollgate. `--disallowedTools` e il gh con guardia (wrapper generato, valori fissati nel file) sono un primo argine; l'audit dei comandi (`flowcheck.py audit`) copre i vettori che elenca (gh per percorso o dietro un prefisso, `git push` ovunque nella stringa, `eval`, `python -c`, manomissioni dei file della guardia e del registro) ed è un segnale. La **garanzia** è la verifica dello stato prima e dopo ogni passo (`flowstate.py`, `<passo>-stato.txt`): hash di wrapper, guardia e script, registro `gh-wrap.log` copiato e solo crescente, `git ls-remote` con `main` invariato e soli `refs/heads/tg/*` avanzati senza forzature, PR, issue e protezione di `main` invariate. Non impedisce un effetto: rileva gli effetti elencati, qualunque comando li abbia prodotti, e rende il passo «non riuscito» (il passo ritorna 3, lo script esce con 1). Restano fuori commenti, label, corpo e base di PR già esistenti, il repo detect e le impostazioni del repo.

Esito della verifica per passo (`<passo>-stato.txt`, `<passo>-audit.txt`):

| Passo | Stato prima/dopo | Audit dei comandi |
|---|---|---|
| shim | riuscito (0 differenze) | riuscito (0 voci fuori elenco) |
| 1 | riuscito (0 differenze) | riuscito (0 voci fuori elenco) |
| 2 | riuscito (0 differenze) | riuscito (0 voci fuori elenco) |
| 3 | riuscito (0 differenze) | riuscito (0 voci fuori elenco) |

Audit complessivo (`audit-esito.txt`): riuscito, 0 voci fuori elenco.

## Impianto

- Cartella `/tmp/tollgate-p4/flow`: clone di `ginz0ls/tollgate-p4-protected` in `protected/` (testa `b86dc8d`), stato `state/` con la sentinella `.tollgate-test`, `shim/gh` (gh finto, solo per il passo `shim`),
  `ghbin/gh` (gh con guardia: ogni gh del modello e della CLI passa da `ghguard.py`, profilo `flow`; gh vero `/usr/bin/gh`). **Nessuna `TOLLGATE_GH`**: il flusso usa il gh vero, solo su protected.
- `claude -p` sempre da `/tmp/tollgate-p4/flow` (checkout o worktree del lavoro), con `--plugin-dir` sul worktree del ramo `p4-gate`, `--model sonnet`, `--permission-mode acceptEdits`,
  `--allowedTools Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob`, `--disallowedTools` per `gh repo`, `gh api`, `gh auth`, `gh secret`, `gh issue create`, i `git push` forzati, `--mirror`, `--delete` e verso `main`/`master`, `*/gh`, `command gh`, `env`, `exec`, `xargs` e le variabili `P4_*` (`*.argv`), con `--output-format stream-json --verbose --include-hook-events`.
  Prima di ogni passo `git remote get-url --push origin` deve essere protected.
- Issue di prova: #104 (`dividi(a, b)` in `src/calc.py` con `test_dividi`; `issue.env`, creata con `flusso-issue-create`).

## Sessioni reali (id e cartella)

| Passo | Sessione | Cartella |
|---|---|---|
| shim | `83f31dcd-92cc-4a1c-8d6c-ada7d4c3d799` | `/tmp/tollgate-p4/flow/protected` |
| 1 | `482de4f5-099a-4911-9bcd-abc2d3aa7cc7` | `/tmp/tollgate-p4/flow/protected` |
| 2 | `0bae512a-c61c-49c1-8639-015b1320947e` | `/tmp/tollgate-p4/flow/protected/.claude/worktrees/tg-104-prova-p4-del-flusso-dividi-a-b-in-src-ca` |
| 3 | `02a55d4b-f373-44ec-a609-780106d8fa31` | `/tmp/tollgate-p4/flow/protected/.claude/worktrees/tg-104-prova-p4-del-flusso-dividi-a-b-in-src-ca` |
| 4 (se serve) | non eseguito: verdict `success` | |

## Passi ed esiti

| Passo | Prompt | Esito | Evidenza |
|---|---|---|---|
| shim | `command -v gh` e `echo "$PATH"` (gh finto, senza rete) | riuscito: uscita 0, 3 turni, costo 0,160 USD | `shim-esito.txt`, `shim.jsonl` |
| 1 | `/tollgate:start #104 L1` | riuscito: stato 0 differenze, audit 0 voci, uscita 0, 13 turni, costo 0,340 USD. Il modello ha invocato `superpowers:writing-plans`, scritto e committato il piano (`0780dec`) | `passo1-*`, `passo1.jsonl` |
| 2 | piano e `/tollgate:execute` | riuscito: stato 0 differenze, audit 0 voci, uscita 0, 11 turni, costo 0,431 USD. Skill `tollgate:execute`, un agente di implementazione e uno di revisione del task 1; commit `19369c2` «aggiungi dividi(a, b) in src/calc.py» | `passo2-*`, `passo2.jsonl` |
| 3 | `/tollgate:finish` fino a `finish open-pr` | riuscito: stato 0 differenze, audit 0 voci, uscita 0, 7 turni, costo 0,287 USD. Agente «Revisione finale ciclo 1»; `finish check`, `review prepare`, `finish open-pr` | `passo3-*`, `passo3.jsonl` |
| attendi | stati della PR | riuscito: guard, verdict e attention `success`, un commento del bot col marcatore e lo SHA; `mergeStateStatus` `CLEAN` | `attendi-esito.txt`, `flusso-attendi-*` |
| 4 | solo se `verdict` è rosso: `/tollgate:start #N` e `task start --from-gate`, un solo giro | non necessario: verdict `success` | |

Costo totale riportato da `claude -p` (somma di `total_cost_usd`): circa 1,22 USD, di cui 1,06 USD nei tre passi del flusso.

Esito atteso: PR aperta dal flusso, `tollgate/guard` e `tollgate/verdict` `success`, commento con il marcatore e lo SHA della testa. Ottenuto.

## PR, stati e veti

- PR: #105, ramo `tg/104-prova-p4-del-flusso-dividi-a-b-in-src-ca`, testa `19369c22f36d394cd9f6a7bbe90f71ba44a4b371` (`pr.env`). Aperta (non unita).
- Stati con autore: `tollgate/guard` `success`, `tollgate/verdict` `success`, `tollgate/attention` `success`, tutti `github-actions[bot]` (`attendi-esito.txt`). Commento del gate con il marcatore `<!-- tollgate-verdict sha=19369c22f36d394cd9f6a7bbe90f71ba44a4b371 -->`, «Nessuna voce.», autore `github-actions[bot]`, uno solo (`flusso-attendi-comments.out`).
- Run: `tollgate-run` 10 s, `tollgate-guard` 12 s, `tollgate-verdict` 18 s (`flusso-attendi-runs.tsv`), in tutto 40 s, fatturati 0. `mergeStateStatus` `CLEAN` (`flusso-attendi-merge-state.out`).
- Veti ed eventi `effect_*` per passo (`*-eventi.txt`): veto 0, `effect_requested` 0, `effect_executed` 0 in tutti e quattro i passi. `hooks.log`: vuoto.
- gh del modello (`*-gh-modello.txt`): vuoti per tutti i passi, il modello non ha lanciato alcun `gh`. Il registro `gh-wrap.log` ha 11 chiamate, tutte della CLI di tollgate: `gh auth status` e 5 `gh api` di lettura per `start` (issue, pulls, status del commit, permessi di Actions, protezione di `main` con `--include`); poi, per `open-pr`, `gh api` sull'issue, due `gh pr list`, un'altra lettura dell'issue e `gh pr create`.
- Vista dello stato dopo il flusso (`status.txt`): `#104 ... fase pr_open livello L1`, task 1 done.

## Token e costi

`bin/tollgate stats` (`stats.json`): token totali 87 631: `tollgate:implementer` 39 401, `tollgate:task-reviewer` 25 049, `tollgate:final-reviewer` 23 181. Cicli di review 1, giri di correzione 0, blocchi 0, deroghe 0, veti 0, override di rilievi 0, «needs you» 0. Ore di fase: execution 0,04, plan 0,01, pr_open 0,03, review 0,01. Costo riportato da `claude -p` per passo: shim 0,160 USD, passo 1 0,340 USD, passo 2 0,431 USD, passo 3 0,287 USD.

## PATH del tool Bash

Uscita del tool Bash per `command -v gh` nel passo `shim`: `/tmp/tollgate-p4/flow/shim/gh`; confronto con lo shim: uguale a `/tmp/tollgate-p4/flow/shim/gh` (`shim-esito.txt`; vincolo P3c (4): il `gh` risolto dal tool Bash è lo shim messo in testa dal chiamante). `echo "$PATH"` nel tool Bash (`shim.jsonl`): `/tmp/tollgate-p4/flow/shim:/home/crucco/.opencode/bin:/home/crucco/.kimi-code/bin:/home/crucco/.pyenv/shims:/home/crucco/.pyenv/bin:/home/crucco/.local/bin:/home/crucco/.local/bin:/home/crucco/.nvm/versions/node/v22.20.0/bin:/home/crucco/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games:/usr/local/sbin:/usr/sbin:/sbin:/home/crucco/MEGA/BIZ/VIBE/Plugin IT workflow/.claude/worktrees/p4/bin`. La cartella `bin` del plugin è in coda al `PATH`, la testa resta quella del chiamante.

## Difetti e osservazioni

- Nessun difetto nuovo emerso dalle evidenze del flusso: uscite 0, 0 differenze di stato, 0 voci fuori elenco nell'audit, 0 veti.
- Il clone del flusso in `/tmp/tollgate-p4/flow` è imposto dal brief; il controllo dei comandi (`raccogli-comandi-controllo.txt`) lo segnala come violazione, falso positivo del verificatore: il controllo vuole una cartella sotto `P4_WORK`. Riportato come tale nel rapporto del gate.
- Il modello ha scritto il piano da sé al passo 1 (invocando `superpowers:writing-plans`) e lo ha committato; al passo 2 il prompt di appoggio diceva di scriverlo solo se mancava, e non ha dovuto farlo.
- Il flusso è stato eseguito una sola volta: l'esito «riuscito» è su una sola esecuzione, non dice nulla sulla ripetibilità né su L2.

## Ciò che resta non esercitato

- Il passo 4 (rientro dal gate rosso con `task start --from-gate`): non necessario, verdict verde.
- Il livello L2, le issue con più task, più cicli di revisione e i veti con effetto reale: il flusso ha un solo task di livello L1 e 0 veti.
- L'unione della PR (`gh pr merge`) dal flusso: la PR #105 è rimasta aperta.
- Il flusso sul repo detect e con una protezione di `main` incompleta (vedi criterio 11 nel rapporto del gate).
- Un modello ostile: la prova è cooperativa, la garanzia è la verifica dello stato dopo ogni passo.
