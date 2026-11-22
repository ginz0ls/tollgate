# C1: prova reale corta del tracciamento locale

Esito: riuscita

Data: 21 novembre 2026. Piano: C1 (tracciamento locale), Task 9. È una prova breve di un lavoro di livello L1, eseguita con `claude -p` vero, per vedere con i propri occhi le tre cose nuove di C1: la taglia del lavoro, il costo in token dei subagenti e la fotografia in JSON. Tutti i passi sono riusciti al primo tentativo e non è emerso nessun difetto del prodotto. Due cose non si potevano vedere con questo tipo di prova e restano fuori (vedi «Punti non provati»).

- Versioni: Claude Code `2.1.329` (`registro-1/versione-claude.txt`), modello `sonnet` (`claude-sonnet-5-5`).
- Script: `spikes/run-b1-flow.sh` con `B1_FLOW_RULES=vere`, `B1_FLOW_CASE=b1` (il caso predefinito) e `B1_FLOW_EVIDENCE=c1` (la variabile nuova del Task 9, che sceglie la cartella delle evidenze). Modi usati: `controlla`, `prepara`, `passo1`, `passo2`, `registra`. Nessun GitHub vero: `gh` finto (`tests/fakegh.py`), `origin` nudo locale, stato di prova separato da quello della macchina.
- Evidenze: `docs/verifiche/evidenze/c1/flusso/` (`validate/`, `passo1/tentativo-1/`, `passo2/tentativo-1/`, `registro-1/`, `exit-codes.txt`).
- Chi ha fatto cosa: la prova l'ha eseguita il controller; questo rapporto lo ha scritto l'implementatore partendo dalle evidenze e dal registro dei controlli del controller.
- Prima di partire: `ANTHROPIC_API_KEY` non impostata (controllata solo la presenza), spazio libero in `/tmp` sufficiente, albero git pulito. Il modo `controlla` ha dato ok.

## Passi

| Passo | Tentativi | Esito | Durata | Turni | Costo equivalente |
|---|---|---|---|---|---|
| `controlla` e `prepara` | 1 | ok; `plan-check` ok | n/d | n/d | nessuno |
| `passo1`: `/tollgate:start #1 L1` | 1 | uscita 0; lavoro #1 avviato e piano registrato | 78 s | 14 | 0,39 USD |
| `passo2`: `/tollgate:execute` | 1 | uscita 0; task 1 fatto, revisionato e chiuso | 75 s | 10 | 0,54 USD |
| `registra` | 1 | uscita 0, `fallimenti.txt` vuoto | n/d | n/d | nessuno |

Durata, turni e costo vengono dalla riga `result` di `claude.jsonl` di ogni tentativo. L'esito di `claude` (uscita 0) è in `esito.txt`.

Cosa è successo:

1. **`passo1`.** Il modello ha avviato il lavoro e ha scritto subito anche il piano, già nel primo passo. Nel registro ci sono due `veto` di questo passo (seq 4, regola `coordinator`, e seq 5, regola `plan_check`, piano senza task al primo tentativo di scrittura): sono voluti, il controllo ha fatto il suo lavoro e il piano si è registrato subito dopo, non sono un difetto.
2. **`passo2`.** Il modello ha eseguito il piano già scritto invece di quello del prompt, e ha segnalato lui la differenza dei nomi. Il task 1 è stato fatto dall'implementatore, revisionato dal revisore del task (approvato) e chiuso. La verifica del progetto risulta «uncounted»: il progetto di prova ha `allow_no_tests` acceso.

## La taglia

Nel registro ci sono due eventi `size_decided` (`registro-1/eventi-c1.jsonl`):

- il primo (seq 3) all'avvio, con causa `start`: taglia `small`, motivo «ancora nessun piano», segnali L1, 0 aree, 1 fetta, 0 task;
- il secondo (seq 9) dopo la registrazione del piano, con causa `plan`: taglia `small`, motivo «piano con 1 task», `previous` `small`, segnali L1, 1 task.

In tutti e due `by` vale `rules` e `confirmed` è vuoto: la taglia l'ha decisa la regola, nessuno l'ha confermata. Al modello sono arrivate le stesse due righe, «taglia: piccolo, ancora nessun piano» all'avvio e «taglia: piccolo, piano con 1 task» alla registrazione del piano.

## Il costo

Due subagenti hanno chiuso con una trascrizione leggibile, e quindi ci sono due eventi `cost`:

- l'implementatore (seq 19): 49528 token;
- il revisore del task (seq 24): 32293 token.

Ogni `cost` viene subito dopo il suo `subagent_stop` e ha gli stessi token. `by_model` contiene un solo modello, `claude-sonnet-5-5`. Il `task` è 1 per l'implementatore e vuoto per il revisore, come nel suo `subagent_stop`. In `registro-1/eventi-c1.jsonl`, per ogni `cost`, restano solo i token e i nomi dei modelli (lo sceglie `eventi-c1`); `registro-1/events.jsonl` ha invece il dettaglio per tipo di token. Questo vale per la prova, fatta prima della correzione F1 della revisione finale: da allora il `cost` del revisore del task porta il task rivisto in `data.task` (la riga del subagente e `subagent_stop` restano senza task).

Costo equivalente dell'intera prova: **0,93 USD** (passo1 0,39 più passo2 0,54), contati sulla quota dell'abbonamento. **Nessun addebito.**

## La fotografia

`registro-1/snapshot.json` (versione 1) ha un solo lavoro: livello L1, taglia `small` decisa da `rules`, fetta non impostata, fase `execution`, task `{done: 1}`, turno dell'agente, nessuna attesa. Il costo è 81821 token in tutto, con `by_task` `{"1": 49528}`: il costo per task conta solo ciò che è legato a un task.

Il totale 81821 coincide con la somma dei due `cost` (49528 + 32293 = 81821). Il revisore non ha un task nel suo evento, perciò sta nel totale ma non in `by_task` (la correzione F1 della revisione finale lo include dai lavori nuovi).

## `session_start`

Nel registro ci sono due `session_start`: il primo (seq 1) senza lavoro, perché la sessione è partita dalla radice (un limite noto), il secondo (seq 11) con il lavoro 1, perché la sessione è partita nel worktree.

## Punti non provati

- **Le fermate.** `AskUserQuestion` non c'è con `claude -p`, perciò gli eventi `stop_asked` e `stop_answered` non si possono produrre in questa prova. Restano alla prova vera di C6.
- **La crescita del costo di un subagente ripreso.** Il costo è cumulativo per agente, ma in questa prova nessun subagente è stato ripreso (nessun `resumes`): non si è potuto vedere che il secondo `cost` di un agente ripreso sia maggiore del primo.
- Il costo della sessione principale (il coordinatore) non è nella fotografia: non ha `SubagentStop`. È un limite già scritto nella pagina d'uso.

## Pulizia delle evidenze

- `togli-pagine`: `registra` l'ha già applicato (5 e 3 risultati sostituiti) e il controller l'ha ripassato sulle trascrizioni copiate: nessun risultato nuovo da togliere.
- Anonimizzazione: `evals/scrub.py anonymize` su `docs/verifiche/evidenze/c1` (8 file modificati dall'anonimizzazione su 41 nella cartella), con `USER` e `HOST` al posto di nome utente e host, `snapshot.json` ed `events.jsonl` compresi.
- Controllo con `grep -raF` del nome utente e dell'host: nessun file. Controllo delle forme di token: nessun file.
- `claude plugin validate --strict` sulla copia del plugin (`validate/validate-1.txt`): «Validation passed», con un solo avviso (il README della copia non ha la riga che installa tollgate da un marketplace); non blocca.
- `test_committed_evidence_has_no_long_web_results`: verde.
- Lettura a mano di `registro-1` (versione, limiti, lookups, `fakegh.log`, precarico, comandi del modello, uscite, git log): niente da togliere. Restano i percorsi con `USER`, come nelle prove di B.
