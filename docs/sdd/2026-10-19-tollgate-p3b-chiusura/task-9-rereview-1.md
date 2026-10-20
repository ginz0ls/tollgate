# Task 9 - ri-revisione, giro di correzione 1

### Verdetti sui rilievi
1. **`_review` con `review_unverified` azzerava il ciclo dei rilievi**: INDIRIZZATO. `openpr.py` `_review`: `on_head = same and last["stage"] == "closed"` non dipende piu' da `review_unverified`; `ok = unverified or (on_head and outcome ok)`. Il ciclo su HEAD alimenta DoD e specialisti. Test `OpenUnverifiedTest`: bloccante confermato senza `approve finding` -> rifiuto «Nessun rilievo», dopo `dismissed` voce `findings` vera, corpo con «non verificata» e `verdict.unverified`; senza cicli chiusi passa con `verdict.outcome` None. Senza cicli `last` e' None, `same` False, nessun accesso a `last[...]`.
2. **`take_force` consumava l'autorizzazione prima del push**: INDIRIZZATO. `openpr.py` `_publish`: controllo in sola lettura con `intents.force_authorized` (intents.py:58, verificata), poi `push_sha`, poi `take_force` solo se `diverged`, prima del controllo `remote_sha`. `OpenForceTest.test_failed_push_keeps_force_authorization`: push fallito -> stato `authorized`, nessuna PR; secondo giro -> `used`, ramo remoto = HEAD.
3. **Tetto per sezione nascondeva le voci successive**: INDIRIZZATO. `prbody._section`: `_cap` per ogni voce, poi `neutralize(joined, len(joined))` (nessun troncamento ulteriore). Test con tre note lunghe e una riga DoD lunga: tutte le note, prima/ultima voce DoD, deroghe e avviso presenti, 4 «troncato», blocco parsabile.
4. **jq normalizzato (decisione del controller)**: INDIRIZZATO. `gh.py` PR_JQ ha la forma richiesta (`MERGED` se `merged_at`, altrimenti `ascii_upcase`); `test_gh` asserisce la stringa esatta passata; `fakegh` stampa la forma normalizzata (mergedAt -> MERGED, resto maiuscolo).
Minori di iniziativa: `ZWSP = "​"` equivalente al carattere letterale, test hostile invariato; `_note` senza «None» per file/rule/severity (test dedicato; `text` mancante darebbe ancora «None», irrilevante perche' sempre presente). Nulla rotto.

### Danni nuovi nel diff della correzione
Nessuno.

### Osservazioni fuori ambito
- Nessun tetto complessivo del corpo: con molte voci puo' superare il limite di GitHub (65536 caratteri) e `pr create` fallirebbe in modo visibile. Da valutare in seguito.
- In `_publish`, se `take_force` restituisse None dopo il push (concorrenza) l'esito viene ignorato; accettabile.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
