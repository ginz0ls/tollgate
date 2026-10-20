# Revisione Task 16 (399b2c0..b208c80)

Sola lettura. Evidenze rilanciate: `python3 -B -m unittest tests.test_manifest` -> 24 OK; `claude plugin validate --strict .` -> passed; working tree pulito dopo.

## Aderenza

Controlli mirati sul codice reale (nome del controllo tra parentesi):

- ✅ Codici di `finish check` 0/1/2 (`finishcheck.py:24` OK, RED, REFUSED; `_refuse` -> 2; `_next_step` -> `finish open-pr` in L0, `review prepare` altrimenti). C9 applicata: 1 mostra le `[no]`, altro codice riporta e ferma.
- ✅ Righe `agente: <tipo> brief: "<path>"[ model: m]` (`finalreview._launch_line`), tipi `tollgate:final-reviewer` / `VERIFIER`, stadi review/verify, riga `ciclo N chiuso: <esito>` e `prossimo passo` (`_resume`, `_closing_step`); `review prepare` esce 1 con messaggio su stderr (`cli.py:308-314`). Descrizione della skill coerente.
- ✅ `task start --from-findings <ciclo>` (`cli.py:73`, `fixtask._findings`): richiede fase `execution`, che `close_cycle` ripristina su needs_fix (`reviews.py:331`). Atto `finish` che decade ad ogni commit successivo (`acts._FINISH_ALIVE`): «digita di nuovo `/tollgate:finish`» è corretto dopo il giro di correzione.
- ✅ `open-pr` codici 0/1, rifiuti tutti insieme come `rifiuto:` (`openpr.py:48`, 211); `--update` esiste (`cli.py:90`).
- ✅ `sync` 0/1/2/3 (`sync.py:25`), 3 = patch-id cambiato -> `/tollgate:finish`; PR non aperta -> `/tollgate:finish`.
- ✅ `adopt` 0/1/4 e ultima riga `prossimo passo: EnterWorktree <wt>` (`adopt.py:23, 359`); `abandon` 0/1, ramo/worktree/PR restano (`closing.abandon`); `cleanup` 3 = elenco senza consumo dell'atto, riga `per procedere:` con `--orphans` e `--confirm` (`closing.cleanup`), TTL 10 minuti (`config.py:34`), `da togliere:` / `orfano:` / `avviso:`.
- ✅ `act apply` per level/finding/rounds/unverified-review/rebase (`actapply.APPLIERS`); `unverified-tests`, `waiver`, `effect` dal DB; `resolve` al tetto concede un ciclo (`_resolve` -> `_grant_cycles(…, 1)`); `rounds` con più tetti rifiuta e rimanda a `resolve <id>` (`_approve_rounds`); `rebase` chiude il blocco e autorizza il force (`_approve_rebase`).
- ✅ Agenti: `tools: Read, Grep, Glob, Bash`, `final-reviewer` `inherit` con attribuzione MIT, `finding-verifier` `sonnet`; JSON con `"v": 1`, `sha`, `code`, campi coerenti con `verdicts.parse_final_verdict` / `parse_verifier_results` e con `brief.final_review_brief` / `verifier_brief`; id `f-<ciclo>-<n>` (`reviews.py:144`); un solo JSON; no subagenti; no test che scrivono (m13); cerca difetti (8.6); `file`/`line`/`rule`; solo blocker/major chiedono modifiche (`verdicts.BLOCKING`). C22 ok.
- ✅ Vincoli: forma `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` con ripiego «programma» in tutte le skill; `finish` senza `disable-model-invocation`, le altre quattro con; «mai `git push` né `gh pr create` da Bash»; agenti in primo piano, righe dello stesso stadio insieme; `cleanup` chiede il sì dell'utente prima di `--confirm`.
- ⚠️ Non verificabile dal diff: che l'hook registri davvero i verdetti al `SubagentStop` (la skill lo afferma); coperto da altri task.

## Punti di forza

Testi derivati dal codice (codici, righe, argomenti), non dal piano; `cleanup` e `adopt` precisi sui rischi (sì esplicito, TTL, `EnterWorktree` come `start`); `approve` riscritta oggetto per oggetto con l'effetto reale; agenti con JSON allineato al parser e un test che li confronta; report onesto sugli scostamenti.

## Rilievi

### Important

1. `skills/finish/SKILL.md:292` + `:284` (passo 1) - la skill impone di committare i file del coordinatore DOPO che l'utente ha digitato `/tollgate:finish`, ma un commit successivo all'atto lo fa decadere (`acts._FINISH_ALIVE`, `acts.py:19`; `find_usable` richiede `head_sha` uguale). `finish open-pr` poi rifiuta con «serve un atto dell'utente su questo SHA» (`openpr.py:152`) dopo tutto il lavoro di controllo e revisione. Il testo non lo dice: va scritto «se hai committato, a fine revisione l'atto è decaduto: chiedi all'utente di digitare di nuovo `/tollgate:finish` prima del passo 3», meglio ancora prima del passo 1 («fermati e chiedi di ridigitare dopo il commit»). Vale anche come lacuna di test: `test_finish_skill_keeps_worktree_clean` (`tests/test_manifest.py:480`) controlla solo l'ordine delle parole. (Il vincolo (3) è del piano, ma il suo effetto sull'atto non è gestito.)
2. `skills/finish/SKILL.md:304` - per il tetto «… cicli di revisione già fatti» (8 cicli, `finalreview.py:106`) indica «`/tollgate:approve rounds <n>` o `unverified-review`». `approve rounds` a 8 cicli fatti rifiuta sempre (`actapply._grant_cycles`: `done + n > MAX_CYCLES`); il messaggio della CLI dice solo `unverified-review`. Correggere: a quel tetto vale solo `unverified-review`; `rounds` è per il blocco «cicli di revisione esauriti» (4 cicli contati). Lo stesso al `:312`: `unverified-review` vale solo dopo 8 cicli (`_approve_unverified_review`), e `skills/approve/SKILL.md:211` lo dice, ma `finish` no.
3. `skills/sync/SKILL.md:393` - il codice 2 copre due casi (`sync.py:_block`): conflitto nel rebase E rami divergenti (`_remote_conflict`). La skill dice «Mostra le due strade» solo del primo (`/tollgate:approve rebase`, che per il secondo rifiuta: `_approve_rebase` richiede un blocco `SYNC_CONFLICT_REASON`); per i rami divergenti la strada è integrare a mano e `/tollgate:resolve <id>` o abandon. Distinguere i due casi, oppure dire di seguire le strade indicate nella riga `needs_you:`.

### Minor

4. `skills/finish/SKILL.md:311` - nel ramo `needs_fix` manca il caso in cui `close_cycle` ha anche aperto il blocco «cicli di revisione esauriti» (`reviews.py:333-335`): la fase è `blocked` e `task start --from-findings` rifiuta («la fase è blocked»). Fail-safe (C9 dice di fermarsi), ma la skill dovrebbe dire: con un blocco aperto non lanciare `task start`, vai a `resolve`/`approve rounds`.
5. `skills/start/SKILL.md:358` - la PR chiusa senza merge in `start` esce con codice 3 e righe `conferma:` (`start.py:139-141`, `CLOSED_HINT`), non con 1/`rifiuto:`. Le due strade stanno sotto la voce «1, rifiuto», che per questo caso non scatta; sotto la voce 3 manca il rimando ad `abandon`. Spostare/duplicare la frase.
6. `skills/finish/SKILL.md:292` - «il controllo e la revisione rifiutano un albero con modifiche»: vero per `finish check` (`verify.run_gate` -> `git.is_clean`), non per `review prepare` (nessun controllo in `finalreview.py`). Basta «il controllo».
7. `agents/final-reviewer.md:45` - «cartella temporanea a parte» per guardare un'altra revisione: un `git worktree add` scrive in `.git`; meglio `git show <sha>:<path>` o `git archive` in una cartella fuori dal repo.
8. `skills/adopt/SKILL.md:183` - dopo `adopt` in fase `pr_open` «`/tollgate:finish` per chiudere» rifiuterebbe (`finishcheck.py` ammette solo execution/review); lì vale `/tollgate:sync` o il flusso di start. Aggiungere la fase.
9. `skills/finish/SKILL.md:318` - `--update` non è necessario (`openpr` aggiorna comunque la PR aperta quando la fase è `review`); la frase «se ha già una PR aperta» fa pensare che sia obbligatorio. Chiarire che con la fase `pr_open` serve prima riportare il lavoro in `execution` (sync / `start --reopen-execution`).
10. `tests/test_manifest.py:480-487, 475-478` - test di sola presenza di sottostringhe («committa», `gh pr create`); non asseriscono la regola (es. «mai `gh pr create` da Bash» è presente solo come sottostringa). Accettabile, ma il rilievo 1 mostra cosa non catturano.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** testi e agenti sono nel complesso fedeli al codice (codici, righe, argomenti, JSON, vincoli e C9/C22 rispettati, test e validate verdi), ma tre istruzioni operative divergono dal comportamento reale: atto `finish` invalidato dal commit del passo 1, `approve rounds` indicato al tetto degli 8 cicli, codice 2 di `sync` ridotto al solo conflitto di rebase.
