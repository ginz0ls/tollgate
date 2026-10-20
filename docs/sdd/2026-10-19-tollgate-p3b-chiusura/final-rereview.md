# Ri-revisione del giro di correzioni della revisione finale (a29f588..6da05bb)

Verificato sul diff e sul codice a 6da05bb. Eseguiti solo test mirati (`python3 -B`): test_layers (2 OK) e test_sync, test_openpr, test_adopt, test_actapply, test_gh, test_criteria_p3b (165 OK).

### Verdetti sui rilievi

1. **I-1 (rilievo senza esito di un ciclo superato / ottavo ciclo blocca open-pr per sempre)**: INDIRIZZATO. `reviews.mark_unverified` (reviews.py:210-219) è chiamata da `supersede` (reviews.py:230, motivo «ciclo superato») e da `actapply._approve_unverified_review` (actapply.py:281-286, stessa transazione di `set_review_unverified`). Un verificatore in ritardo non può sovrascrivere: `apply_verification` ignora i rilievi con `verification` non nulla (reviews.py:~205). Test: `OpenOrphanFindingTest.test_finding_of_superseded_cycle_does_not_block` (ciclo 1 in `verify` con rilievo, HEAD cambia, supersede, ciclo 2 ok, open-pr apre; verifica `("unverified","ciclo superato")`), `test_unverified_review_marks_findings_without_outcome` (ottavo ciclo), `test_actapply...test_findings_without_outcome_become_unverified` (percorso reale dell'atto). Il supersede è chiamato direttamente e non via `review prepare`, ma `finalreview.py:103` chiama la stessa funzione.
2. **I-2 (sync in execution con task in corso guasta l'intervallo)**: INDIRIZZATO. `sync._in_use` (sync.py, dopo il controllo di fase e prima di rebase/fetch/intento) rifiuta per task `running`/`review`/non `done` con `commits != '[]'` (default colonna `'[]'`, db.py:108) e per subagenti non di sola lettura `running`. L'atto non si consuma, come per gli altri rifiuti nello stesso punto. Test `SyncOpenWorkTest`: task in review con commit, task running, scrittore running (HEAD, intento e fase invariati), sola lettura ammesso.
3. **I-3 (PR da fork)**: INDIRIZZATO. `gh.pr_for_branch` chiede `isCrossRepository` e scarta `True` (gh.py:~143-152); `adopt` usa solo `pr_for_branch` (adopt.py:118) quindi eredita il filtro; `open-pr` rilegge dopo il push e modifica solo se numero e `headRefOid` coincidono con lo SHA spinto (openpr.py:~287-296). Test: `OpenForkPrTest` (PR fork lasciata intatta, si apre la nostra, `pr_number == 2`; PR con oid diverso non modificata), `test_gh`, `AdoptPrTest.test_fork_pr_with_same_branch_is_not_ours` (tetto non ripristinato).
4. **I-4 (lease vecchio mai rinnovato)**: INDIRIZZATO. `intents.refresh_lease` (intents.py:147-159) chiamato da `_realign` (sync.py:~639-641) quando l'autorizzazione esiste e `force_lease != remote`; il rifiuto del push con lease dice «il ramo remoto è avanzato: /tollgate:sync» (openpr.py:~476-481). Sicuro: `_realign` si raggiunge solo se `_remote_conflict` non ha bloccato (remoto antenato, ff, noto o integrato a mano). Test `test_stale_lease_is_renewed_and_open_pr_pushes` (lease R1 -> R2, open-pr spinge, intento `used`) e `test_failed_lease_push_points_to_sync`.
5. **Triage 58-59**: INDIRIZZATO. `adopt._level` legge sempre l'issue (GhError = rifiuto), `author_association` fuori da `flow_start.TRUSTED_AUTHORS` = almeno L2 con avviso (adopt.py:~354-358). Test `AdoptIssueTest` (2).
6. **Triage 63 / m6 (spec 12.4)**: INDIRIZZATO. Spec: «rami `tg/<N>-*`», coerente con `closing.py:24`.
7. **m1 (rilievi non verificati nel corpo PR)**: INDIRIZZATO. `prbody.render(unverified=)` + `openpr._unverified`, neutralizzati da `_section`. Test in `test_prbody` e `test_unverified_findings_are_listed_in_the_body`.
8. **m2 (finish check con GitError/OSError)**: INDIRIZZATO (finishcheck.py:~63-64; test dedicato).
9. **m3 (approve rebase registra i commit)**: INDIRIZZATO (actapply.py:308 `events.record_commits` dopo `set_base`; test con `PostToolUse Bash` senza blocchi e senza nuovi eventi).
10. **m4 (messaggio rifiuto vs rosso)**: INDIRIZZATO (sync.py `_finish`; due test).
11. **m5 (skill sync/adopt)**: INDIRIZZATO. Le due skill ora dicono quanto richiesto (fase `review` con PR, rifiuto di I-2, `start #N --reopen-execution` per adopt).
12. **Spec rev 23**: INDIRIZZATO. Verificato nel testo: 6.4 (fork, `headRefOid`, I-3), 6.5 (I-2 rifiuto senza consumare l'atto, I-4 lease rinnovato e messaggio), 8.6 e 10 (unverified), tabella atti (`unverified-review`, `approve rebase`), 12.4 (adopt, cleanup), riga 23 di «20. Revisioni» e «Stato» del piano (1417). Coerente col codice.

### Danni nuovi nel diff della correzione

Nessuno Critical o Important. Verificati:
- Strati: `events.py` importa `git` entro `tollgate_core` (stesso strato); `tests/test_layers.py` verde. `record_commits` spostata correttamente, `sync` usa `events.known_commits/record_commits`.
- Transazioni: `db.tx` si unisce a una transazione aperta (db.py:165-178), quindi `mark_unverified` dentro `supersede` e dentro il `with db.tx` di actapply è atomica; `refresh_lease` apre la sua.
- Controllo `headRefOid`: in caso di rifiuto dopo un push riuscito il `GhError` è in `SIDE_EFFECT_ERRORS`: `_refuse` senza `set_pr`, atto `finish` non consumato, intento `pr` resta `requested` (stessa chiave, riprendibile), l'autorizzazione forzata è già `used` e al nuovo giro il remoto coincide con HEAD, quindi niente secondo push. Con GitHub in ritardo basta ripetere (messaggio esplicito).
- Minor: il test I-4 marca R2 come commit «noto» con un evento invece di riprodurre «Update branch» + integrazione a mano; il ramo di codice provato (`_realign` -> `refresh_lease`) è però lo stesso. Minor: la creazione (`pr create`) non verifica `headRefOid` della PR creata; il filtro fork di `pr_for_branch` basta.
- `fakegh`: `headRefOid` calcolato dalla punta di origin quando la PR non lo dichiara, `isCrossRepository` default falso: i test di fork e di oid fisso dichiarano il campo e restano significativi.
- Asserzione tolta da `test_criteria_p3b.py` (`opened["headRefOid"] == wt_head`): ora la PR creata non memorizza più `headRefOid`; la stessa prova (la PR punta allo SHA di HEAD) resta data dall'asserzione successiva sul ref remoto del ramo e, per il percorso di modifica, dal controllo in `open-pr` coperto da `OpenForkPrTest`. Coperta.

### Osservazioni fuori ambito

- `gh.prs_for_branch_prefix` (usata da `start.py:305` e dai cleanup) non filtra le PR da fork (`PR_JQ` usa solo `head.ref`): non toccata dal giro, impatto limitato a rilevamento di PR esistenti per prefisso.
- Il nome `isCrossRepository` col `gh` vero resta da verificare al primo uso (già segnalato come G4 nel report).

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
