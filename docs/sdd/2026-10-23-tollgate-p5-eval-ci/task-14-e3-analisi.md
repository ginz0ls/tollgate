# Task 14 - analisi di e3-start-spec (0,00, soglia 0,66)

Evidenze: `docs/verifiche/evidenze/eval-p5/20261025T221559Z-e3-start-spec/` (result.json, stderr.txt, runs/claude-eval-{cRnx5g,iESTpJ,b2ydfn}/trace.jsonl, settings.json).

## 1. Le 3 corse

Tutte uguali nell'esito: punteggio 0, nessun errore di corsa (`error: null`), 2-3 turni, 15 s circa.

| Corsa | Comandi in ordine | Dove si ferma |
|---|---|---|
| cRnx5g | 1) `python3 "/tmp/tollgate-eval-target/bin/tollgate" start 2 --spec docs/superpowers/specs/calc-l2-tre-fette.md` -> exit 1; 2) `git rev-parse --show-toplevel; ls -la "$(git rev-parse --git-dir)"/config*; pgrep -a git` -> exit 1 (pgrep senza processi) ma l'`ls` mostra `crw-rw-rw- 1 nobody nogroup 1, 3 ... .git/config.lock` | Dopo il 2). Conclude che `config.lock` e' `/dev/null` messo dalla sandbox e non lo rimuove: «farlo significherebbe aggirare una restrizione del sandbox» |
| iESTpJ | solo il comando 1) -> exit 1 | Dopo il 1): ipotizza un lock orfano, non lo cancella |
| b2ydfn | solo il comando 1) -> exit 1 | Idem |

Esito identico del comando 1) in tutte e tre (stdout/trace):
`rifiuto: scrittura della configurazione git non riuscita: git config tollgate.defaultBranch main: error: impossibile bloccare il file di configurazione .git/config: File già esistente`
(più le due righe note `.bashrc: Permesso negato`).

Grader (result.json, `explanation`), tutti e tre a zero in ogni corsa:
- `lavoro-in-fase-plan` (peso 2): «pattern not found in trace». La riga `lavoro #2 avviato: ...` la stampa `start` solo a lavoro creato; non e' mai stata stampata.
- `spec-approvata-riconosciuta` (peso 1): idem, la riga e' stampata solo a lavoro creato.
- `worktree-creato` (peso 1): `**/worktrees/tg-2-divisione/src/calc.py missing`. Nel workspace c'e' solo `.claude/worktrees/tg-1-moltiplicazione` (quello dello scaffold).
I grader sono coerenti e non hanno colpa: misurano un lavoro mai creato.

## 2. Causa

Tipo (c), limite della sandbox di `claude plugin eval`, con un'aggravante (a) minore del prodotto e una premessa sbagliata del ledger.

Evidenza:
- La corsa cRnx5g mostra `.git/config.lock` come device a caratteri 1,3 (`/dev/null`) nel workspace (`home/cwd`): la sandbox impedisce a git di creare il lock, quindi qualunque `git config <chiave> <valore>` fallisce con «File già esistente», anche con lo stesso valore. Riprodotto fuori sandbox simulando il lock con una directory `.git/config.lock`: `git config tollgate.defaultBranch main` -> rc 255 con lo stesso messaggio.
- `settings.json` della corsa non elenca nessun `denyWrite` su `home/cwd/.git/*` (solo `home/.git/config`, `home/.git/hooks`, `home/.git/commondir`, riga ~42-110), quindi il blocco viene dalla protezione predefinita del sandbox di Claude Code sul `.git/config` della cartella di lavoro, non dalle impostazioni scritte da tollgate.
- Il punto che fallisce e' `bin/tollgate_flow/start.py:403-406`: `gitw.set_config(main, "tollgate.defaultBranch", default)` -> `_refuse(...)`, prima di sessione, ramo e worktree.
- La scrittura e' superflua: lo scaffold ha gia' impostato lo stesso valore (`evals/_kit/scaffold.py:254`, `git config tollgate.defaultBranch main`). `git config` prende comunque il lock anche se il valore non cambia.
- Il ruling di `progress.md:138` («la sandbox nega .git/config solo nella HOME, non nel workspace»; carry.md:108) era un'assunzione non provata (il rapporto verifiche, `docs/verifiche/2026-10-23-p5-verifiche.md:48`, la dava per non provata). E' falsa: e' il «costo se sbagliata» previsto («e3 rosso al Task 14»).

Non e' (b): ricetta, caso e grader sono corretti (lo scaffold costruisce lo stato giusto, i pattern sono quelli di `start`). Non e' (d): 3 corse su 3 identiche, la causa e' deterministica; l'agente ha anche fatto la cosa giusta (non aggirare la sandbox).

## 3. Plugin caricato?

Si'. Il messaggio `init` (terzo per corsa) riporta `plugins: [{name: tollgate, path: /tmp/tollgate-eval-target, source: tollgate@inline, version: 0.2.0}, ...]`, `slash_commands` con `tollgate:start` e tutti i `tollgate:*`, e `skills` idem. Il modello ha pure eseguito `bin/tollgate start`.

## 4. Correzione minima proposta (non applicata)

Prodotto, 3 righe in `bin/tollgate_flow/gitw.py:116` (`set_config`): se `git config --get <chiave>` vale gia' il valore, non scrivere. Beneficio reale anche fuori dagli eval (niente scrittura inutile in `.git/config`, niente lock concorrente). Prova fatta in una copia in una HOME temporanea dello scaffold `l2-first-slice-merged`: con `config.lock` bloccato, il prodotto attuale rifiuta con il messaggio sopra; la copia con `set_config` idempotente supera quel punto e si ferma subito dopo con «sessione non riconosciuta» solo perche' il mio ambiente manuale non ha gli hook di Claude Code (nella corsa vera li ha).

Non provato e rischio residuo: `create_branch` (`start.py:477`) e `git worktree add --no-track -b` (`gitw.py:56`) scrivono `.git/refs/heads/tg/2-divisione` e `.git/worktrees/`; non scrivono `.git/config` (`--no-track`), ma se la sandbox avesse altri device su `.git/*` il caso resterebbe impossibile. Va rilanciato solo e3 (`evals/run.sh e3-start-spec`, circa 0,21 USD) dopo la correzione.

Se il rilancio mostrasse altri blocchi in `.git` (worktree o refs): e3 e' impossibile nella forma attuale. Alternative, in ordine di preferenza:
1. Cambiare forma: lasciare che lo scaffold crei tutto tranne la riga finale e far verificare all'agente solo l'esito di `start` su un caso che non scrive in `.git` (non fattibile per `start`, che crea sempre ramo e worktree);
2. Passare e3 a prova a secco (come e2), con motivo scritto: «`start` crea ramo e worktree in `.git` del workspace, che la sandbox di `claude plugin eval` protegge; la copertura resta nei test di `tests/` e nella prova reale di P4/P5».
