### Verdetti sui rilievi
- **I-1 push forzato fail-open**: INDIRIZZATO. `sentinel.py:_commits` ritorna `(commit, forzato)`: `before` non risolvibile -> `([after], True)`; non antenato (`git.ok merge-base --is-ancestor`, fail-closed anche su errore git, `git.py:62`) -> `rev_list` + forzato. `unverified` unisce `FORCED` al motivo di `after` (in aggiunta ai controlli per PR). Storia riscritta, ritorno indietro (rev_list vuoto, `after` comunque segnalato) e `before` assente danno tutti `after` non verificato. Fast-forward: antenato, `forced=False` (`test_fast_forward_is_not_forced`). Prima installazione e `before` zeri invariati (`sentinel.py:_commits` primo ramo, `skip` intatto). Eseguito `python3 -B -m unittest tests.test_gate_sentinel`: 38 OK.
- **I-2 fiducia in `github-actions`**: INDIRIZZATO. `ghcli.STATUS_BOT` (`ghcli.py:25`) usata in `sentinel.py:79`; `BOT_LOGINS` resta solo per i commenti (`github.py:176`). Grep su `bin/`: nessun altro punto giudica `creator.login` degli stati (`github.py:143` lo legge soltanto). Test `test_bot_login_without_suffix_not_trusted_for_statuses`.
- **Minore 3 (ordine stati/issue)**: INDIRIZZATO in `sentinel.run` (stati prima di `report_sentinel`) e in `baseids.publish` (stato `failure` prima del blocco issue). Test d'ordine su entrambi.
- **Minore 6 (`unverified` nella descrizione)**: INDIRIZZATO (`baseids.py`, `extra`); `set_status` tronca a 140 (`github.py:132`), quindi il limite vale sempre.
- **Minore 7 (`GITHUB_REPOSITORY` solo con `--publish`)**: INDIRIZZATO (`sentinel.run`, repo dall'evento senza `--publish`; `test_dry_run_does_not_need_github_repository`).

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minor: con `forced` e `after` nell'insieme `skip` (prima installazione) `after` viene comunque segnalato: comportamento prudente e coerente, non un difetto. Con molti comandi `unverified` il troncamento a 140 può tagliare l'elenco: accettabile.

### Osservazioni fuori ambito
Rilievi 4 e 5 (attese per commit, nome del test paginato) restano non fatti, come da ruling.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
