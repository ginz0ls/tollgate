# Ri-revisione della correzione finale (5d166cb, 9bb2da1)

## Verdetti sui rilievi
- **I-1 (base-publish esce 1 con suite rossa, in entrambe le modalità)**: INDIRIZZATO. `baseids.py` `_red`/`_publish`/`publish`/`publish_from` (rosso -> 1, verde -> 0; in `detect` dopo stato e issue, in `protected` senza chiamate a gh). Docstring e spec 9.1 aggiornate. Test: `test_gate_sentinel.py` (rosso/verde per modalità, `protected` senza chiamate). Eseguiti: 256 test dei moduli gate OK. `protect.sh` non toccato (`gate/` assente dal diff). Il workflow `tollgate-base.yml` ha `if: always()` sul job di pubblicazione: il codice 1 lo rende rosso senza altri effetti.
- **M-2 (`base_test_ids = false` non esegue la suite)**: INDIRIZZATO. `baseids.compute` salta setup e comandi e scrive `ids.json` valido con `commands`/`ids` vuoti; accettato da `read_result` e da `publish_from` (0). Test in `test_gate_run.py` (`BaseIdsComponentOffTest`). Resta un'incoerenza minore (dubbio 1).
- **M-6 (`unverified` con comando configurato = rosso)**: INDIRIZZATO. `evaluate.py` `_command_state`: `"red" if spec.command else "unverified"`, quindi `command_red` anche con `approve unverified-tests`. Il CLI vero scrive `unverified` solo per comando vuoto (`run.py:69-70`, `tollgate_core/verify.py:111`). Test nuovo con e senza atto; i tre test vecchi sono stati spostati su una configurazione senza comando (corretto: usavano l'artefatto incoerente).
- **M-8 (testo delle eccezioni codificato)**: INDIRIZZATO. `verdict.py` (due punti, anche «stato non scritto") e `cli.py:161` con `json.dumps(..., ensure_ascii=False)`; `json` è importato in entrambi. Test con `\n::error::x`. Il rimando `cli.py:570` della revisione era errato: il file è di 162 righe e l'unico punto è quello.
- **M-7 (righe > 100)**: INDIRIZZATO per tutte le righe elencate (verificato con `awk`: nessuna riga > 100 in `flow/gh.py`, `flow/init.py`, `evaluate.py`, `test_init.py`). `init.py:198`: `runs_path` è una stringa non-f con `{owner}/{repo}` e `$SHA` letterali, identica byte per byte all'originale (`{{owner}}` nell'f-string). Restano `tests/fakegh.py:46,230,231` (non elencate nel brief).
- **Limiti in 1.2 (M-1, M-3, M-4)**: INDIRIZZATO. Tre voci nuove nella sezione «Limiti dichiarati in P4» (spec, diff righe ~93-110), ciascuna con il rinvio a P5.
- **Piano principale (voci + M-5, M-9 + elenco puntato)**: INDIRIZZATO. La riga lunga è sostituita da un rimando e da un elenco sotto la tabella («Minori rinviati di P4») in tre gruppi, più il gruppo «Dalla revisione finale» con M-1, M-3, M-4, M-5, M-9. Contenuto invariato (non ricontrollato voce per voce contro la riga originale: ho verificato che le voci elencate coincidono per numero e tema con quanto il rapporto dichiara).

## Danni nuovi nel diff della correzione
Nessun Critical/Important. Il gate non si apre in nessun caso nuovo: I-1 e M-6 restringono; M-2 riguarda solo la suite della base (con il componente spento `verdict` non trova identificativi, come prima per `components_off`).
- Minor: spec riga 963 dice «`base_test_ids` si può spegnere; senza, `tollgate-base` non gira», ma il job gira ancora e pubblica `tollgate/base` `success`. Vedi dubbio 1.

## Dubbi dell'implementatore
1. `tollgate/base` «suite della base verde» con il componente spento: Minor. Fuorviante in `detect` ma non è un controllo obbligatorio e `components_off` compare già come voce `attenzione` sulle PR. Meglio una descrizione «non eseguita (base_test_ids spento)» o nessuno stato, e allineare la riga 963 della spec; rinviabile a P5.
2. `base-publish` senza `--publish` con suite rossa -> 1: accettabile e coerente (il codice riflette l'esito); nessuno lo usa senza `--publish` nei workflow.
3. M-8 a `cli.py:161`: corretto, il rimando originale era sbagliato.
4. Righe > 100 in `fakegh.py:46,230,231`: Minor, fuori dall'elenco del brief; chiudibili con una riga di formattazione o rinviabili.
5. Minori del piano in una sottosezione: va bene (una tabella non regge un elenco puntato).

## Osservazioni fuori ambito
Nessuna.

## Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important. Aperti solo due minori: descrizione di `tollgate/base` con componente spento (e riga 963 della spec), righe > 100 residue in `tests/fakegh.py`.
