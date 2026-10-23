# Revisione del Task 3 (commit 8210169)

### Aderenza
- ✅ `check_l2_detail`/`L2Problem`/`check_l2` sopra di esso: `bin/tollgate_analysis/approvals.py:182-285`. `check_l2` invariata nella firma.
- ✅ Caso (a) (D22): `locate_spec_approval` `approvals.py:152-176` (corrente vince: propria, poi issue più bassa; poi propria; `None` come prima). Test `test_current_beats_own_stale`, `tests/test_l2tree.py`, due test esistenti aggiornati come da D10.
- ✅ Caso (d): `spec_sha` dei report confrontato con lo `sha` dell'approvazione trovata (`_spec_reports`, `approvals.py:~250-275`); `plan_sha` con lo `sha` di `plan-approval.md`; `plan-approval.md` superato → `return` prima di ogni ricerca di report (`approvals.py:~215-218`); `path` diverso → `missing`; `spec_sha` del piano contro l'approvazione trovata (non `spec_blob`), come dice D10.
- ✅ D17a: `prref.issue_from_branch` è l'unica occorrenza di `^tg/(\d+)-` (grep su `bin/` e `tests/`); `_common.py` (percorso reale `bin/tollgate_checks/_common.py`) e `closing.py` invariati nel comportamento.
- ✅ Fixture (`tests/flowkit.py:write_report`, `tests/test_criteria_p3c.py:first_slice_files`): allineate ai report veri (`bin/tollgate_hooks/apply.py:196-199` scrive `spec_sha` e, per il piano, `plan_sha`). Nessuna asserzione indebolita: in `test_locate_own_then_other_issue` l'approvazione propria diventa corrente e la parte «altra issue» resta asserita.
- ❌ Decisione 10, `stale` contro `missing` per la sola approvazione di un'altra issue: vedi I-1.
- ❌ `workflows.problems` non è fail-closed su alcune forme: vedi I-2.
- ⚠️ `spec_reviews_dir` diverso → `approval_stale` (D10) non è nel task: la firma del brief non lo prevede. Da assegnare a un task successivo.
- ⚠️ Nessun chiamante legge ancora `L2Problem.kind` (`finishcheck.py:244` usa `check_l2`): l'effetto di I-1 sul gate si vedrà dal task che lo consuma.

### Punti di forza
- `check_l2` come proiezione di `check_l2_detail`: nessuna duplicazione; test di identità dei testi.
- `_valid_reports` riusato da `_reports`; `complete` evita il doppio messaggio quando il report manca del tutto.
- Test di messaggi molto precisi (riga 7 di P3c), TDD ricostruito con onestà dichiarata.
- `prref`: lookbehind su `[\w-]` (esclude `disclosures #3`), test dei casi negativi.
- `workflows`: nome di job `checks`/`statuses` non è un falso rosso; commenti ignorati; CRLF, forme a flusso, valore sulla riga seguente gestiti (verificato con prove mirate).

### Rilievi

**Important**

I-1. `approvals.py:~196-201` (ramo `found is None`) contro `bin/tollgate_gate/l2tree.py:46-49`. Due funzioni giudicano lo stesso fatto in modo diverso: spec approvata solo da un'altra issue e poi cambiata → `l2tree.spec_approval` dà `STALE` (cerca di nuovo con `spec_blob=None`), `check_l2_detail` dà `MISSING` («manca il file ... con lo sha attuale»). Con la decisione 10 `missing` è rosso e `stale` è `approval_stale` (la spec cambiata è già fuori scope): lo stesso evento (spec modificata dopo l'approvazione) è rosso per una fetta successiva e informativo per la prima. Oggi nessun comando legge `kind` (grep: solo `finishcheck.py:244` via `check_l2`, testo), ma il gate dei task successivi lo farà. È anche la lezione «un fatto condiviso in un posto». Correzione: in `check_l2_detail`, se `found is None`, chiamare `locate_spec_approval(..., spec_blob=None)`: se esiste → `STALE` con il suo testo e `approved_spec = header["sha"]`, altrimenti `MISSING`; meglio ancora far derivare `l2tree.spec_approval` dallo stesso calcolo. Aggiungere il test (approvazione solo dell'issue 3, `sha` vecchio → `["stale"]`), oggi assente. L'implementatore l'ha dichiarato come scostamento ma non lo giustifica con una decisione.

I-2. `bin/tollgate_analysis/workflows.py:~64-102`: la decisione 15 chiede fail-closed, ma restano non rosse (provato con `problems()`): (a) escape in chiave o evento tra virgolette doppie: `"\x73tatuses": write` e `on: "pull_request_\x74arget"` → `[]`, ma un parser YAML li decodifica; (b) chiave complessa `? statuses` / `: write` → `[]`. Sono evasioni dirette del controllo di sicurezza da parte dell'autore della PR. Correzione: rosso per un `\` dentro una stringa a doppie virgolette in posizione di chiave o nella riga `on:` (non nelle righe `run:`), e rosso per `^\s*\?\s` (chiave complessa); test per ciascuno.

**Minor**

- m-1 `prref.py:7-8`: `closes_issue` conta anche `<!-- Closes #N -->` (commento HTML di un template di PR) e righe citate/in recinto di codice; GitHub non le considera. Il «prima riga vince» può dare un falso rosso (non un bypass). Considerare di ignorare i commenti HTML.
- m-2 `workflows.py:15`: `{statuses:write}` (senza spazio) non è rosso; probabilmente non è una chiave valida per GitHub, ma in fail-closed meglio segnalarlo.
- m-3 `workflows.problems` ha controllo sui byte: `�` legittimo nei commenti dà rosso (accettabile, fail-closed).

### Valutazione
**Qualità del task:** Da correggere.
**Motivo:** l'implementazione è solida e ben testata, ma `check_l2_detail` e `l2tree.spec_approval` danno esiti diversi per lo stesso fatto (I-1, decisione 10) e `workflows.problems` non chiude due forme YAML che aggirano il guard (I-2).
