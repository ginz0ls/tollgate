# Ri-revisione Task 9, giro di correzione 1 (aad7df7..d8e8606)

Eseguiti solo test mirati (`python3 -B`: BoundaryTest, IssueRuleTest, MinorsTest, CliTest, 17 test OK).

### Verdetti sui rilievi

**I-1. Con `--publish` rami d'errore senza stato**: INDIRIZZATO.
- `verdict.py` `main`: lo SHA si legge fuori dal `try`, il resto (`_judge`) è nel confine `except Exception` (non `BaseException`). Con `publish` scrive `_statuses(... _error(reason))`: `verdict`=error con `DESC_ERROR: motivo`, `attention`=error con `DESC_ATTENTION_ERROR`; 0 se scritti, 1 se la scrittura fallisce; senza `publish` stampa e torna 1.
- Descrizione: `set_status` normalizza gli spazi e tronca a 140 (`github.py:132`); `BoundaryTest.assert_explicit_error` lo verifica.
- Percorsi che escono senza stati rimasti: «non applicabile» (`return 0 if pulls`) e «SHA superato» (`finish`, testa avanzata o risposta malformata), cioè i due consentiti. Ogni altro `return` passa da `finish(...)`.
- Copertura: `BoundaryTest` (GhError da `shared_sha_prs`, `pull`, ricontrollo; ValueError da `pr_from_rest`; RuntimeError da `evaluate`; stato non scrivibile, uscita 1; senza publish) e due test `CliTest` al posto del vecchio.

**I-2. Regola «issue della PR» duplicata**: INDIRIZZATO. `evaluate.pr_issue_number` (`evaluate.py:38`) è usata da `Context.issue_no` (`:72`) e da `verdict.py:110`; `_issue_number` rimossa (`IssueRuleTest.test_verdict_has_no_copy`). Corpo identico a quello di prima: per `tg/*` non da fork dà N del ramo, per fork `tg/*` e per `tollgate-config/*` (`issue_from_branch` riconosce solo `tg/`) ricade su `Closes #N`; esito invariato. L'altro uso di `issue_from_branch` (`evaluate.py:659`) è dopo la guardia `is_work`, già verificato.

**Minori**: tutti INDIRIZZATI.
- Commento NA ricontrollato e saltato per PR con altra testa: `verdict.py` `_not_applicable` + filtro sulla testa; test `MinorsTest`.
- Filtro `state == "open"`: presente, con test per entrambi i casi.
- Niente `KeyError` in `finish`: `_head_is` usa `.get`; test su risposta malformata.
- `_base_ids`: `stat()` dentro `try OSError`.
- `fakegh.py` docstring rientrata (righe entro 100).
- Test fork con issue chiusa aggiunto.

### Danni nuovi nel diff della correzione

- **Minor** `verdict.py` `main` (`sys.stderr.write(f"gate evaluate: {reason}\n")`): il motivo dell'eccezione va su stderr non codificato, mentre `_print` stampa con `json.dumps` proprio perché «mai un comando del runner». Un testo con a capo e `::comando::` in un messaggio di `gh` o git sarebbe interpretato dal runner. Rischio molto basso (i messaggi non contengono testo libero della PR), ma coerente sarebbe `json.dumps(reason)` o `" ".join(reason.split())`.
- **Minor** `verdict.py` `main`: il motivo (`type: str(e)`) entra senza neutralizzazione nella descrizione dello stato. Resta testo semplice su una riga, troncato a 140, e il percorso preesistente per `GitError` faceva lo stesso; non è markdown. Nessun blocco.
- **Minor** (caso limite): con una PR solo verso un altro ramo, un `GhError` nel nuovo `_head_is` dentro `_not_applicable` finisce nel confine e scrive `error` sullo SHA, che la decisione 5 vorrebbe senza stati per «non applicabile». Raro e fail-closed.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
