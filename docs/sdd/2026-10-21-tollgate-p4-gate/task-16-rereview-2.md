# Ri-revisione Task 16, giro di correzione 2 (fcb22a3..a768319)

Sola lettura. Eseguito: `python3 -B -m unittest tests.test_p4_flowstate tests.test_p4_ghguard` (64 test, ok), `bash spikes/run-p4-flow.sh controlla` (rc 0, 14 s: «manomissione hash/log/main/ref: rilevata», nessuna VIOLAZIONE), tre chiamate di `ghguard.py check` per le letture dello snapshot (tutte ammesse). Nessun gh vero, rete, claude.

## Verdetti sui rilievi

**R-1 (audit aggirabile, nessuna verifica di esito).** INDIRIZZATO, secondo il ruling del controller.
- `flowstate.py` fa un'istantanea prima e dopo ogni `claude_step` (`run-p4-flow.sh` `state_snapshot`/`state_compare`, chiamate in `claude_step` prima del lancio e dopo `verifica_push`) e `compare` dà una riga per ogni differenza. Letto il codice di `compare` (`flowstate.py`) contro l'elenco richiesto:
  - push su main: «main è cambiato» (ref `refs/heads/main` con SHA diverso); main cancellato: «ref cancellato»;
  - push forzato su `tg/*`: `merge-base --is-ancestor` con codice 1 → «push forzato»; oggetto assente → «antenato non verificabile» (fail-closed);
  - ref non `tg/*` nuovo (incluso tag e `refs/heads/altro`) o aggiornato o cancellato: tutti rilevati; `refs/pull/*` ignorati;
  - hash di `ghbin/gh`, `ghwrap.py`, `ghguard.py`, `flowcheck.py`, `flowstate.py`, `common.sh`, `run-p4-flow.sh` (file sparito = `None` ≠ hash);
  - registro troncato o riscritto: il nuovo deve cominciare con il vecchio (copia del vecchio dentro l'istantanea);
  - PR non più aperta o unita, PR nuova non aperta o non verso main; issue chiusa o nuova; protezione di main diversa; elenchi illeggibili e `ls-remote` fallito → «non riuscito».
  - Provato dal vivo: `controlla` simula hash, registro troncato, push su main e ref non tg e verifica «STATO CAMBIATO» e «NON RIUSCITO» con uscita != 0; `tests/test_p4_flowstate.py` copre il resto con repo bare locali (test passati).
- L'audit dei comandi (`risky`): `git push` ovunque nella stringa, alias/remoti, `eval`, `python -c`, comandi che toccano `ghbin|gh-p4|gh-wrap|ghwrap|ghguard|flowcheck|flowstate|run-p4` con `chmod|rm|mv|ln|cp|tee|truncate|dd|install|sed -i|>`. Segnale, come dichiarato.
- Lo script si ferma: `claude_step` ritorna 3 e tutti i chiamanti hanno `|| return 1`.

**N-1 (variabili scartate dal wrapper).** INDIRIZZATO: `ghwrap.py` `make_wrapper` scrive `unset ... GH_HOST GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN GH_CONFIG_DIR BASH_ENV ENV`; il test passa (il valore non si legge). Il compromesso sull'autenticazione via variabile d'ambiente è scritto nel commento dello script.

**N-2 (confronto transcript/registro).** INDIRIZZATO: `cmd_audit` confronta la riga intera con segnaposto espansi e `--repo` aggiunto (stessa espansione del wrapper), con un `Counter` (una chiamata consuma una voce). Un `pr view` diverso non copre.

## Risposte ai punti richiesti

**(a)** Sì per tutto l'elenco, con le limitazioni di copertura sotto (R2-1).

**(b) Falsi «non riuscito» sul flusso legittimo.** Nessuno trovato.
- `passo3`/`passo4b`: `openpr.py` fa `push_sha` senza forzatura (salvo `force_authorized`, vedi R2-3), poi `pr edit` (solo corpo) o `pr create` (base = predefinito, ramo `tg/*`): effetti ammessi dal confronto (ref `tg/*` nuovo o avanzato con antenato; PR nuova aperta verso main; PR esistente invariata nello stato). `passo4b` sullo stesso ramo è un fast-forward + `pr edit`: lecito. Il flusso non unisce, non chiude PR né issue, non crea issue (`gh.py` ha solo `pr_create`/`pr_edit`); sentinel apre issue solo in modalità detect, non su protected.
- Il confronto è uniforme per tutti i passi, non «per passo» come diceva il ruling («fuori dagli eventi attesi del passo»): `passo1`/`passo2` potrebbero aprire una PR senza che lo snapshot protesti. Il vincolo per passo resta a `flowcheck.py events` (nessuno|open-pr). Accettabile (Minor R2-2).
- Finestra `--limit 100` sulle liste: un PR/issue che esce dalla finestra non produce falsi positivi (si guarda solo cosa compare nel «dopo»); il repo protected ha qualche decina di voci dalle prove del gate.

**(c) Letture dello stato.** Passano da `gh_call` → `guard_args` (profilo script del controller) e `git ls-remote`/`git fetch` partono dopo `check_remote protected` (in `state_snapshot`). `pr list --state all --limit 100 --json ...`, `issue list ... --json number,state`, `api repos/ginz0ls/tollgate-p4-protected/branches/main/protection`: verificate con `ghguard.py check` (ammesse). Rientrano nella decisione 25 («`gh pr list|view`, `gh issue list|view`, `gh api` in lettura sui due repo»; `git` di rete solo sul remoto controllato). Le scritture in `$OUT` sono rotate (`rot`).

**(d) Commento sul modello di minaccia.** Quasi onesto, con un eccesso: dice che la verifica «rileva ogni effetto fuori elenco su GitHub qualunque sia il comando». Rileva solo gli effetti elencati (R2-1); il resto (commenti, corpo e base di PR esistenti, altro repo, impostazioni) non è coperto. Resta corretta l'ammissione «non impedisce, rileva» e «il modello è cooperativo».

## Danni nuovi nel diff della correzione

Nessun Critical o Important. Minori:

**R2-1 (Minor). Copertura dello stato più stretta di come la descrive il commento.** `flowstate.py` `_compare_github`: non vede commenti e corpo di PR/issue, cambio di `baseRefName` di una PR già esistente (confronta la base solo sulle PR nuove), label, issue riaperte, il repo `detect`, impostazioni del repo (visibilità, Actions, segreti), protezioni di altri rami; la verifica copre solo l'intervallo tra le due istantanee. Correzione: nel commento di `run-p4-flow.sh` e nel rapporto (`2026-10-21-p4-prova-flusso.md`, sezione «Modello di minaccia e garanzia») sostituire «ogni effetto fuori elenco» con «gli effetti elencati (ref, hash, registro, stato di PR e issue, protezione di main)»; se costa poco, aggiungere `baseRefName` e `headRefName` al confronto delle PR esistenti.

**R2-2 (Minor). Uscita dello script.** Il rapporto e i commenti dicono «uscita 3»; `claude_step` ritorna 3 ma i modi fanno `|| return 1` e il `case` finale restituisce 1. Per ciò che serve (uscita != 0) basta; allineare la descrizione («uscita non zero») o far propagare 3.

**R2-3 (Minor, nota). Push forzato legittimo di tollgate.** `bin/tollgate_flow/gitw.py:140-142` e `openpr.py:264-274` fanno `--force-with-lease` su `tg/*` quando l'utente ha autorizzato `/tollgate:sync` o `approve rebase`. Nei passi della prova non succede (nessun rebase richiesto), ma se capitasse `flowstate` lo darebbe «push forzato» e il passo sarebbe «non riuscito»: comportamento voluto (la prova non deve forzare), va solo saputo.

## Osservazioni fuori ambito

- `XDG_CONFIG_HOME`, `HTTPS_PROXY`, `SSL_CERT_FILE` non sono scartati dal wrapper: restano fuori dal modello di minaccia cooperativo dichiarato.

## Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. Minori aperti non bloccanti: R2-1 (togliere «ogni» dal commento e dal rapporto), R2-2 (descrizione dell'uscita), R2-3 (nota).
