# Leggere lo stato di tollgate da un gestionale

Questa pagina è per chi vuole costruire sopra tollgate un cruscotto o un gestionale: cosa leggere, in che forma, e cosa non aspettarsi. Tutto resta nello stato locale della macchina. Niente di ciò che segue passa da GitHub.

## Cosa si legge

Due comandi, tutti e due in sola lettura dei dati:

- `events --after-seq N`: gli eventi con `seq` maggiore di `N`, uno per riga in JSONL. Si tiene l'ultimo `seq` visto e si riparte da lì.
- `snapshot`: una fotografia in JSON dei lavori aperti, di tutti i repo che il DB conosce.

Il primo avvio dopo un aggiornamento di tollgate può migrare lo schema del DB, con una copia in `backup/`. Senza DB, `snapshot` stampa una fotografia vuota e non crea niente.

## La busta degli eventi

Ogni evento ha la stessa busta, alla versione 1:

```json
{"v": 1, "seq": 41, "at": "2026-11-21T10:00:00.000000Z", "host": "macchina", "session": "…",
 "work": 3, "repo_key": "github.com/o/r", "issue": 7, "type": "cost", "data": {}}
```

`seq` cresce di uno per volta in un solo DB. Con più macchine o più DB un evento si identifica con la coppia `host` e `seq`; un lavoro, con `repo_key` e `issue`. `work` è un numero interno del DB e non vale fuori da lì. I tipi nuovi e i campi nuovi in `data` non cambiano `v`.

## I cinque tipi nuovi

- `size_decided`: la taglia del lavoro. `data`: `proposed`, `applied`, `previous`, `cause`, `by` (`rules` o `user`), `reason`, `signals` (o nullo), `confirmed`.
- `ruling`: una decisione presa al posto dell'utente. `data`: `what`, `why`, `cost`, `by` (`agent` o `user`), `task`.
- `stop_asked`: una domanda diretta all'utente. `data`: `tool_use_id`, `questions` (`header`, `question`, `options`).
- `stop_answered`: la risposta, o il rifiuto. `data`: `tool_use_id`, `answers` (o nullo), `source` (`tool_response`, `tool_input`, `failure`, `none`). Ha la stessa `tool_use_id` della domanda.
- `cost`: il costo in token di un subagente. `data`: `agent`, `type`, `task`, `tokens`, `by_model` (`input`, `cache_creation`, `cache_read`, `output`), `usd` (sempre nullo: i dollari non si inventano), `source`.

Il tipo `session_start`, che già esisteva, ora si scrive davvero, con `data.source`.

Un `cost` è cumulativo per agente: un subagente ripreso rilegge tutta la sua trascrizione e scrive un `cost` nuovo. Per sapere cosa è costato un agente si prende l'ultimo, non la somma. Il costo di un lavoro è la somma dei subagenti: la sessione principale non ha un evento di chiusura e resta fuori.

## La fotografia

`snapshot` stampa `{"v": 1, "at", "host", "works": [...]}`. Per ogni lavoro non chiuso:

- identità e stato: `repo_key`, `issue`, `level`, `level_cap`, `phase`, `phase_before_block`, `branch`, `pr_number`, `created`, `updated`, `last_event_at`;
- taglia: `size` (`small`, `medium`, `large`), `size_by` (`rules` o `user`), `slices`;
- `tasks`: quanti task per stato;
- `turn`: `decision` se qualcosa aspetta una scelta dell'utente, `user` se il passo dopo è suo (fase `pr_open`, il merge, o `approval`, l'approvazione del piano), `agent` negli altri casi;
- `waiting`: le cose che aspettano una scelta, `{"kind": "block" | "effect" | "question", "id"}`, e `waiting_user`, il loro numero più uno se `turn` è `user`;
- `cost`: `tokens` (la somma, per agente, dell'ultimo `cost`) e `by_task`, il costo per task: somma anche i revisori del task, perché il loro `cost` porta il task rivisto in `data.task` (la riga del subagente e il suo `subagent_stop` restano senza task). I `cost` scritti prima di questa correzione non portano il task del revisore: per quei lavori `by_task` conta solo gli implementatori.

Nella fotografia non c'è testo libero: né i motivi dei blocchi, né le ruling, né le domande. Quel testo sta negli eventi. Fa eccezione `branch`, che nasce dal titolo dell'issue ed è già visibile su GitHub. Una fotografia si può quindi mostrare ovunque, salvo il limite di `repo_key` scritto nei limiti noti.

### Una domanda in attesa

Una domanda diretta all'utente è in attesa se non ha una risposta con la stessa `tool_use_id`, è l'ultima domanda della sua sessione e dopo di lei il lavoro non ha né un atto dell'utente né un `session_start`. Un turno interrotto senza un comando dopo resta in attesa fino al primo dei due: un'attesa che dura troppo, non una persa. Una sessione nuova aperta dalla radice del repo non è legata al lavoro, quindi il suo `session_start` non chiude niente; lo stesso per la ripresa con `/tollgate:start`.

### Versione

Un campo nuovo non cambia `v`; uno tolto o cambiato sì. Avanzamento, dipendenze e coda arrivano con le fette C4 e C5 del sotto-progetto C, come campi nuovi.

### Limiti noti

- `reopen plan` rinumera i task: `cost.by_task` può unire i costi dei due piani sotto lo stesso numero.
- `slices` è nullo per i lavori L1, per le fette dalla seconda in poi e per i lavori nati prima di C1; `size` è nullo per questi ultimi, e nessuna regola li ricalcola da sola.
- Nel JSON le chiavi di `cost.by_task` sono stringhe.
- Un profilo `vertical` senza `paths` conta come un'area per ogni file toccato, e quindi spinge la taglia.
- Il `cost` è in token, non in dollari, e non include la sessione principale.
- `repo_key` è l'`origin` del repo normalizzato: con un `origin` su GitHub è `github.com/<proprietario>/<repo>`, ma con un remoto locale è un percorso della macchina (e può contenere il nome utente). Chi mostra la fotografia fuori dalla macchina lo filtra.
- Con `events_days > 0` gli eventi archiviati escono dal DB: `cost.tokens`, `by_task` e `last_event_at` si calcolano sugli eventi che restano, quindi possono scendere o diventare nulli. La storia completa sta in `archive/`.

## L'archivio degli eventi

Gli eventi si conservano per sempre. `[retention] events_days` vale `0` per difetto, e `0` vuol dire «mai». Con un numero positivo, a ogni `start` gli eventi più vecchi del limite si scrivono prima in `archive/events-<primo seq>-<ultimo seq>.jsonl` nella cartella di stato, nella stessa forma di `events`, e solo dopo si cancellano dal DB. Se la scrittura fallisce non si cancella niente. Lo `0` non ha lo stesso senso nelle tre chiavi di `[retention]`: vale «mai» solo per `events_days`; per `lookups_days` e `retention_days` vuol dire «subito» (le letture dei lavori chiusi, o i file di `logs/` e `ctx/`, si cancellano a ogni `start`). Un numero negativo è un errore di configurazione. Il DB è uno per macchina: il limite del `tollgate.toml` di un repo vale per gli eventi di tutti i repo dello stato della macchina (l'archivio li tiene). Le letture registrate (`lookups`) non sono eventi: le pota `lookups_days`, 180 per difetto.

Un gestionale che legge con `events --after-seq` non perde niente se l'archivio è attivo, a patto di leggere più spesso del limite.

## Quanto occupano gli eventi

Non si legge lo stato vero della macchina. La misura viene dalle copie dello stato che stanno in `docs/verifiche/evidenze/eval-b8/` (88 file `tollgate.db`, schema 6, cioè prima di C1), aperte da una copia in una cartella temporanea, poi cancellata. Per ripeterla: si ordinano i percorsi dei file `tollgate.db` e si prendono il primo, quello di mezzo e l'ultimo, con `events --after-seq 0` su ciascuno. Su questi tre stati (11, 26 e 46 eventi) fanno 83 eventi e 27.787 byte di JSONL: circa 335 byte per evento. Una scansione fatta a parte su tutte le 88 copie dà lo stesso ordine: 1.002 eventi, 334.672 byte, 334 byte per evento.

Gli eval sono lavori corti, di pochi minuti. I byte per evento servono a stimare un lavoro vero: mille eventi pesano circa 335 KB. La stima è meno precisa di una misura sullo stato reale, che qui non si è potuta fare.
