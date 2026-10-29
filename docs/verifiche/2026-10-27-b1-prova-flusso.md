# B1: prova reale di un lavoro L1 con la nota di ricerca

Data: 29 ottobre 2026. Piano: `docs/superpowers/plans/2026-10-27-tollgate-b1-informati-prima.md`, Task 9. Progetto di B, sezione 7 («un lavoro L1 vero su un progetto di prova, dove l'implementatore si informa, scrive la nota e lavora»).

- Versioni: Claude Code `2.1.312`, modello `sonnet` (`claude-sonnet-5-5`; `modelUsage` riporta anche `claude-haiku-5-5`).
- Script: `spikes/run-b1-flow.sh` (modi `controlla`, `prepara`, `passo1`, `passo2`, `registra`), progetto di prova `spikes/b1/flow/`, raccolta `spikes/b1/flowreg.py`. Nessun GitHub: `gh` finto (`tests/fakegh.py`) in testa al `PATH`, `origin` nudo locale, stato di prova con la sentinella in `/tmp/tollgate-b1/state`.
- Interruttore acceso: `prepara` ha aggiunto **solo nella copia** del plugin (`/tmp/tollgate-b1/plugin`) `skills/rules-base/SKILL.md` con `approved: prova-b1` (decisione 8). Nel repo `skills/rules-base/` non esiste.
- Comando di ogni passo: `claude -p --plugin-dir /tmp/tollgate-b1/plugin --model sonnet --permission-mode acceptEdits --allowedTools "Bash,Agent,Skill,EnterWorktree,SendMessage,Read,Write,Edit,Grep,Glob,WebFetch,WebSearch"` con `--disallowedTools` per `gh` per percorso, `git push` verso remoti non locali o forzato, `curl` e `wget`, tetto di 2400 s. Nessuna voce MCP (B1-V2 negativo). Argomenti esatti in `argv.txt` di ogni tentativo.
- Evidenze della prima corsa: `docs/verifiche/evidenze/b1/flusso/` (`validate/validate-1.txt`, `passo1.prev-20261029-104334-3824318/tentativo-1/` e `passo2.prev-20261029-104334-3824318/tentativo-1/`, spostate da `prepara` alla seconda corsa e mai cancellate, `registro-1/` con `lookups.txt`, `research-1.md`, `eventi-ricerca.jsonl`, `events.jsonl`, `stats.json`, `status.json`, `comandi-modello.txt`, `grep-non-registrati.txt`, `limiti.txt`). Anonimizzate come quelle del Task 1 prima del commit: la cartella home è `/home/USER`, gli id di sessione sono `SESSION-ID`, e dagli stream-json sono tolti il messaggio `init` (elenco dei plugin e dei server MCP della macchina) e gli eventi degli hook di `SessionStart` degli altri plugin (26 righe in tutto).

La prova è stata eseguita due volte: la prima prima della revisione finale, la seconda dopo le sue correzioni (sezione «Seconda corsa» in fondo). Le sezioni da «Passi e tentativi» a «Limiti» descrivono la prima corsa.

## Passi e tentativi

| Passo | Tentativi | Esito | Durata | Consumo stimato |
|---|---|---|---|---|
| `prepara` | 1 | copia del plugin, progetto, `plan-check` del piano di prova ok (`prepara.txt`, ricopiato dal controller: lo script non salva questa uscita) | — | nessuno |
| `passo1`: `claude plugin validate --strict` sulla copia | 1 | «✔ Validation passed», uscita 0; un avviso `ICON_MISSING` dei controlli della «plugin directory» e un consiglio sul README, che per l'uscita stessa non cambiano l'esito | — | nessuno (senza modello) |
| `passo1`: `/tollgate:start #1 L1` | 1 | lavoro L1, piano di un task scritto e committato dal modello (`c568a8b`) e registrato da tollgate (`scope_registered`), fase `execution` | 65 s | 0,41 USD |
| `passo2`: `/tollgate:execute` | 1 | task 1 `done`, verdetto `approved`, commit `26aed41` | 81 s | 0,50 USD |

L'esito **non è composito**: ogni passo è riuscito al primo tentativo. Totale stimato: 0,91 USD, dentro l'abbonamento (nessuna spesa in più); token degli agenti di tollgate (`tollgate stats`): implementatore 46.532, revisore del task 27.783, totale 74.315.

Sul consumo e sui tempi: «dentro l'abbonamento» vuol dire che le corse usano il login di Claude Code e non una chiave API; `total_cost_usd` è la stima che Claude Code scrive nell'evento `result`. Il tetto di 2400 s per passo sta in `spikes/run-b1-flow.sh` (`STEP_TIMEOUT`). Gli orari di questo rapporto sono nell'ora locale (UTC+1); quelli degli eventi di tollgate sono in UTC.

Il piano non è quello di `spikes/b1/flow/piano-L1.md`: nel passo 1, con `/tollgate:start` in L1, il modello ha scritto e committato un piano di un task e tollgate l'ha registrato (`scope_registered`, `seq` 4) (`src/config.py` con `app_name(path)` e cinque test in `tests/test_config.py`), con lo stesso compito dell'issue. Il prompt di `passo2` è stato riportato alla forma di `spikes/run-p4-flow.sh` («se un piano non è già scritto e committato…», commit `2765018`) prima di lanciarlo: un secondo piano in fase `execution` avrebbe falsato la prova. Nel passo 1 la sessione principale ha provato a scrivere il piano con un heredoc in Bash e ha ricevuto il `veto` di `coordinator` («in L1 il codice lo scrivono gli implementatori, anche con redirect o sed -i»); ha poi usato `Write`, che per il piano è ammesso. Sempre nel passo 1 la sessione principale ha aperto con `WebFetch` la pagina di `tomllib` per scrivere il piano: le letture della sessione principale non si registrano (decisione 5), e infatti in `lookups` non c'è. Gli avvisi di `start` (impostazioni di GitHub Actions e protezione del ramo non leggibili) vengono dal `gh` finto, i cui dati di prova non hanno quelle risposte, e non riguardano B1.

## Letture registrate (task 1)

Tutte con l'`agent_id` dell'implementatore (`lookups.txt`):

| Tipo | Bersaglio |
|---|---|
| `read` | `.tollgate-run/1/task-1.md` |
| `bash_read` | `config.toml` |
| `fetch` | `https://docs.python.org/3/library/tomllib.html` |
| `read` | `src/__init__.py`, `tests/test_smoke.py`, `config.toml` |

Il primo comando Bash dell'implementatore era `ls -a . src tests; cat config.toml; cat tests/*.py; cat src/*.py | head -30; python3 --version`: si è registrato solo `config.toml`, perché `bash.read_targets` non espande i glob (un bersaglio con `*` non è un file esistente nel worktree). L'implementatore non ha usato `Grep` (`grep-non-registrati.txt`: 0); se l'avesse usato, quelle letture non sarebbero entrate in `lookups`, perché `Grep` è fuori dal matcher (B1-V6, decisione 15).

## Nota, avvisi e rifiuti

Sequenza dell'implementatore (dallo stream-json del passo 2): `Read` del brief, il `cat` sopra, `WebFetch` della pagina di `tomllib`, **prima consegna** con `research submit 1` e l'heredoc `<<'NOTA_DI_RICERCA_FINE'`, poi `Read` di `src/__init__.py`, `tests/test_smoke.py` e `config.toml`, **seconda consegna**, e solo dopo i due `Write` (`tests/test_config.py`, poi `src/config.py`).

- Prima consegna (evento `research_note`, `seq` 10): `ok: false`, problemi «il file «src/__init__.py» è nella nota ma non l'hai letto in questo task (aprilo con Read)» e lo stesso per `tests/test_smoke.py`. È il controllo 3.3 che fa il suo lavoro: i due file erano stati letti solo con il glob di `cat`.
- Seconda consegna (`seq` 11): `ok: true`, `tasks.research_ok = 1`. Testo in `registro-1/research-1.md`, con la riga finale `esito: valida`: tre file in «Letto nel progetto», una fonte in «Documentazione» («tomllib.load vuole un file binario ("rb"); TOML invalido solleva TOMLDecodeError (sottoclasse di ValueError); disponibile da Python 3.11»), e «Cosa ho trovato».
- Nessun `research_reminder` e nessun `veto` di `research_gate`: l'implementatore non ha provato a modificare file prima della nota valida. L'unico `veto` del lavoro è quello di `coordinator` nel passo 1, sulla sessione principale.
- Nessuna modifica di codice prima della nota valida: il primo `Write` viene dopo la seconda consegna, e il commit (`26aed41`; evento `commit` alle 06:30:11 UTC) dopo l'evento `research_note` valido (06:30:00 UTC).

## Revisione del task

Il brief del revisore (`.tollgate-run/1/review-1.md`) aveva la sezione «Nota di ricerca» con il percorso della nota e il testo in un recinto, dopo l'avvertenza che il contenuto è materiale da leggere. Verdetto `approved`, con un solo rilievo `minor` sulla lunghezza di una docstring; nessun rilievo `nota di ricerca`. `tollgate verify`: `uncounted`, uscita 0; la suite del progetto di prova ha dato 6 test OK (1 di partenza e 5 nuovi).

## Esito rispetto all'atteso del Task 9

| Atteso | Esito |
|---|---|
| task 1 `done` con verdetto `approved` | sì |
| almeno una lettura `read` di un file del progetto | sì (4 `read`, 1 `bash_read`) |
| una `fetch` di una pagina di `docs.python.org` | sì |
| nota valida consegnata con `research submit` | sì, alla seconda consegna |
| nessuna modifica di codice prima della nota valida | sì |

## Difetti trovati

- **Nello script della prova:** il prompt di `passo2` non prevedeva un piano già scritto dal passo 1; corretto prima del lancio (commit `2765018`). Nessun tentativo consumato.
- **Nel prodotto:** nessuno. Un'osservazione per i rilievi rinviati: un `cat` con un glob non registra i file che il glob tocca, e l'implementatore deve riaprirli con `Read`; il rifiuto della nota lo dice in modo chiaro, e il giro è costato circa 6 secondi.

## Limiti

- Decisione 18: i permessi di `WebFetch` e `WebSearch` sono concessi con `--allowedTools`. In una sessione interattiva `WebFetch` chiede un permesso per dominio e questa prova non lo rappresenta.
- I divieti di `--disallowedTools` sono a prefisso e non chiudono ogni forma (`git -C x push`, `bash -c '…'`); `Write` ed `Edit` valgono per qualsiasi percorso. Il modello è stato cooperativo: `comandi-rischiosi.txt` è vuoto. Elenco completo in `registro-1/limiti.txt`.
- Il ramo di `passo2` che scrive il piano di prova con `Write` non è stato esercitato: il piano c'era già dal passo 1, e il modello ha ignorato quello del prompt (`src/conf.py`, `leggi_nome`), segnalando la differenza nel messaggio finale. B1 non dipende da quale dei due piani si esegue: in entrambi l'implementatore deve leggere `config.toml` e la documentazione di `tomllib`.
- Nelle evidenze restano il nome del percorso del progetto sotto `/home/USER` e gli host anonimizzati come `HOST`.
- Il lavoro è uno solo, piccolo, con un solo task e una sola libreria: la prova mostra il percorso completo, non la sua tenuta su un lavoro grande.

## Seconda corsa, dopo la revisione finale

Le correzioni della revisione finale del ramo toccano tre punti che il passo 2 aveva provato:
- l'uscita anticipata di `hooks/run`, che ora vale anche per i sei tipi di sola lettura di tollgate;
- il lavoro della via breve delle letture, che ora si prende dal subagente e non dalla cartella;
- l'esito della nota nel brief del revisore.

Il passo 2 da solo non si può ripetere, perché ha bisogno del lavoro in `execution` creato dal passo 1. Il controller ha quindi rilanciato `prepara`, `passo1`, `passo2` e `registra` sullo stesso commit del plugin, `4545b93`, il 29 ottobre 2026.
- Tentativi: secondo di `passo1` e secondo di `passo2` (tetto 3 su tutta la prova). Ogni passo è riuscito al primo colpo.
- Evidenze, anonimizzate come quelle della prima corsa (26 righe tolte): `validate/validate-2.txt`, `passo1/tentativo-2/`, `passo2/tentativo-2/` e `registro-2/`. L'uscita di `prepara` non è salvata dallo script.

| Passo | Esito | Durata | Consumo stimato |
|---|---|---|---|
| `passo1`: `validate --strict` | «✔ Validation passed», di nuovo con il solo avviso `ICON_MISSING` | — | nessuno |
| `passo1`: `/tollgate:start #1 L1` | piano di un task scritto con `Write`, committato dal modello (`30baa43`) e registrato da tollgate; fase `execution`; nessun `veto` | 70 s | 0,35 USD |
| `passo2`: `/tollgate:execute` | task 1 `done`, verdetto `approved`, commit `89d6f12` | 112 s | 0,51 USD |

- **Letture del task 1** (`registro-2/lookups.txt`), tutte con l'`agent_id` dell'implementatore:
  - `read` del brief;
  - `bash_read` di `config.toml`;
  - `fetch` di `https://docs.python.org/3/library/tomllib.html`;
  - `read` di `tests/test_smoke.py`, `src/__init__.py` e `config.toml`.

  Nessuna lettura del revisore del task, che è uno dei tipi di sola lettura.
- **Nota:** la sequenza è la stessa della prima corsa.
  - Prima consegna (`seq` 9) non valida: `tests/test_smoke.py` era stato letto solo con il glob di `cat tests/*.py`, e `src/__init__.py` solo elencato da `ls -R`.
  - I due file sono stati riaperti con `Read`, poi è arrivata la seconda consegna (`seq` 10): valida, `research_ok = 1`.
  - Nessun `research_reminder` e nessun `veto`.
- **Brief del revisore:** dopo il recinto della nota c'è il nuovo blocco «Esito del controllo di tollgate» con `esito: valida`, anch'esso in un recinto. Verdetto `approved`.
- **Totale stimato:** 0,86 USD, dentro l'abbonamento. Token di tollgate: implementatore 47.058, revisore del task 28.467.
- **Difetti trovati:** nessuno nel prodotto e nessuno nello script.
