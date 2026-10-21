# Decisioni del controller da portare nei task

Fonte: preflight-scan.md, rapporti dei task e revisioni. La spec rev 23 è l'autorità. Ogni voce prevale sul testo del brief del task. Prima di ogni lancio il controller copia nel dispatch **tutte** le voci che nominano il task, in qualunque sezione.

## Task 1
- Modello di forma per il rapporto: `docs/verifiche/2026-10-19-p3b-verifiche.md`. Le prove dei fatti della decisione 22 vanno cercate in `docs/verifiche/` (P0 `2026-10-08-p0-esiti.md`, P3a `2026-10-16-p3a-verifiche.md` V1, P3b `2026-10-19-p3b-prova-flusso.md`) e citate con file e sezione; un fatto che non trovi provato lì va scritto «non trovato» con dove hai cercato, mai inventato.

---
Voci dallo scan pre-flight (numeri D in preflight-scan.md; le Ruling complete sono in progress.md).

## Task 2
- D12: `render_approval` e `render_report` sollevano `ValueError` se un valore stringa contiene un a capo, `"` o un carattere di controllo (test dedicato).
- D3 (contratto): `locate_spec_approval` è pura: `files` lo sceglie il chiamante (HEAD, punta del predefinito o disco); il docstring lo dice.

## Task 4
- D11: `git.ls_files_at` usa `git ls-tree -r -z --name-only <ref> -- <prefix>` e divide su `\0`; `[]` se il riferimento non c'è.
- D15: nuova `git.blob_at(repo, ref: str, path: str) -> str | None` (SHA del blob di `path` nell'albero di `ref`, `None` se assente), con test in `test_git.py`.
- D16: firma `audits.last_closed(conn, work, kinds: tuple[str, ...]) -> sqlite3.Row | None` (al posto di `kind=None`): ultimo giro chiuso tra i tipi dati, **mai** una riga `superseded`; test dedicato (`superseded` più recente di un giro chiuso → restituito il chiuso).
- D17: `audits.suspended(...)` restituisce `{tipo: numero}` anche con numero 0; il docstring dice che si legge con `in`.
- D19: un solo costruttore `audits.cap_reason(kind: str, number: int) -> str` per i motivi dei blocchi dei tetti: `CAP_REASONS[kind]` più « (giro <n>)» per i tipi avversariali (es. «giri avversariali della spec esauriti (giro 4)»), il testo fisso per `spec-lens` («audit a lenti: tetto di cicli raggiunto»); `cap_kind` lo inverte. Test.
- D7: in `violations` `locked_docs` si calcola una volta per chiamata di `diff_violations` (parametro passato a `scope_exempt` o calcolo esterno al ciclo), non per file; `scope_exempt` esenta i file sotto `docs/superpowers/reviews/<issue del lavoro>/` (decisione 26).
- D10/D18e: in `tests/test_phases.py` le tabelle si chiamano `EXPECTED` e `CAUSES` (non «ALLOWED»): `EXPECTED["L2"]` prende `approve_spec`, `audit_clean`, `approve_plan`; `CAUSES` si estende. `tests/test_db.py:198-199` (`test_latest_version_is_4`) e la stringa `"4"` a riga ~219 passano a `db.latest_version()`/5.

## Task 5
- D1: i test del Task 5 creano i giri chiusi dalla **libreria** con un helper di banco `FlowLab.closed_round(kind: str, counts: dict, *, viewpoint: str | None = None, sha: str | None = None) -> int` (apre e chiude con `audits.open_round` + `audits.close_round` sul blob attuale in HEAD della spec o del piano, esito da `auditrules.outcome`; con `sha` dato usa quello). `FlowLab.report_round` NON si scrive nel Task 5: lo scrive il Task 6.
- D2 (variante B, spec 6.2 punto 4): in `spec_audit` l'ordine dei rami di `prepare` è:
  1. giro aperto sullo stesso SHA → ristampa (stesso codice); su un altro SHA → `superseded` e si prosegue;
  2. avversariale **non passato** — con `spec_adversary` acceso, «passato» = l'ultimo giro `spec-adversarial` chiuso è pulito (qualunque SHA) oppure è quello sospeso — → se l'ultimo giro avversariale è non pulito sullo stesso SHA e non sospeso: rifiuto `STEPS["fix_spec"]`; altrimenti nuovo giro avversariale;
  3. fette > 1, `spec_audit` acceso, audit a lenti né chiuso né sospeso → ciclo a lenti (conferma del costo al primo; ultimo ciclo chiuso sullo stesso SHA e non vuoto → rifiuto `fix_spec`);
  4. `adversarial_ok` falso (acceso e l'ultimo giro avversariale chiuso non sta sul blob attuale, o non è pulito né sospeso) → stesso trattamento del ramo 2 (rifiuto `fix_spec` se non pulito sullo stesso SHA, altrimenti giro avversariale **di conferma**);
  5. `spec_adversary` spento, audit a lenti chiuso o sospeso e ultimo ciclo a lenti non sul blob attuale → ciclo a lenti di conferma (decisione 3);
  6. altrimenti `STEPS["approve_spec"]`.
  `adversarial_ok(conn, work, cfg, spec_blob)` resta la condizione di `approve spec` (decisione 3/9). Aggiungi il test `test_lens_corrections_do_not_trigger_adversarial_until_lens_closed` (tre fette, giro avversariale pulito, ciclo a lenti con rilievi, spec corretta e committata → `prepare` lancia un ciclo a lenti, non un giro avversariale) e `test_adversarial_confirmation_after_lens_closed` (lenti chiuse su una spec cambiata dopo l'ultimo giro avversariale → giro avversariale di conferma, poi «approve spec»).
- D3: in `plan` l'approvazione della spec si cerca nei file **in HEAD** (`git.ls_files_at(wt, "HEAD", "docs/superpowers/reviews/")` e testo in HEAD); se `spec-approval.md` del lavoro c'è su disco ma non in HEAD → rifiuto «committa docs/superpowers/reviews/<N>/spec-approval.md prima del giro del piano».
- D12: rifiuto se il percorso della spec o del piano contiene a capo, `"` o caratteri di controllo.
- D15: promuovi `finalreview._launch_line` a `finalreview.launch_line` (pubblica, stessa forma) e `adopt._find_plan` a `adopt.find_plan` (pubblica); aggiorna i chiamanti esistenti; `audit` le riusa. Il blob «a HEAD» con `git.blob_at` (Task 4).
- D19: le righe che nominano il programma usano `paths.program_command`; nessun letterale `tollgate audit …` nudo in `bin/` (`tests/test_manifest.py:300-308` lo controlla). `STEPS["resolve"]` contiene `<id>`: chi lo stampa con un blocco noto sostituisce l'id.

## Task 6
- D1: qui nasce `FlowLab.report_round(kind=None, counts=None, *, bad_json=False, cut=False) -> subprocess.CompletedProcess` (testo del Task 5 nel brief del piano, «Produces in tests/flowkit.py»), esercitato dai test di questo task.
- D20: `report_round` assegna `self.lab.now = <opened> + 1 s` (mai un attributo nuovo su `FlowLab`, che delega in lettura con `__getattr__`) e lo scrive nel docstring, con la nota che l'orologio del banco può tornare indietro.
- D13: `audit_report` cattura `OSError` della scrittura del report: registra l'evento `veto` {event: "subagent_stop", rule: "audit_round", reason: "report non scritto: <errore>"} e lascia il giro aperto, mai un'eccezione; `audit_round` emette `subagent_finish` **prima** di `record("audit_report", …)`. Test con una cartella non scrivibile o un percorso occupato da una cartella.
- D14: `test_late_report_of_superseded_round_ignored` non modifica file del worktree tra lo start e lo stop dell'agente tardivo (lo dice in un commento): il controllo di manomissione di `subagent_stop` resta attivo per lui.
- Punto c dello scan: `awaiting_audit` usa il ripiego `governing_work` quando `row["work"]` è nullo, come `awaiting_review`/`awaiting_final` (`_common.py:89-92, 110-113`).
- D19: i blocchi dei tetti si aprono con `audits.cap_reason(kind, n)`.

## Task 7
- D2: `adversarial_ok` (Task 5) è la condizione di `approve spec`: l'ultimo giro avversariale chiuso sta sul blob attuale ed è pulito o sospeso.
- D6: `suspend_on_resolve(conn, work, block_reason, *, now)` decide dal DB: tipo da `audits.cap_kind(reason)`; scrive la sospensione solo se la condizione del tetto vale (tipi avversariali: ultimo giro chiuso del tipo non pulito e `len(rounds) >=` tetto, numero = quel giro; `spec-lens`: `len(rounds) >= spec_audit_cycles` con l'audit non chiuso, oppure motivo `DECLINE_REASON` con numero 0); altrimenti restituisce `None` e `resolve` chiude soltanto. Test: blocco con quel prefisso aperto a mano senza giri → nessuna sospensione.
- D16: `approve spec` legge l'ultimo giro chiuso con `audits.last_closed(conn, work, ("spec-adversarial", "spec-lens"))`.
- D17: test `test_decline_resolve_then_approve` (tre fette, `audit decline`, `resolve` → «audit a lenti sospeso» con numero 0; `audit prepare` non chiede più il costo; `approve spec 3` accettato con `lens: suspended`); la sospensione si legge con `in`.
- D3: `approve plan` cerca l'approvazione della spec nei file in HEAD; con `spec-approval.md` su disco ma non in HEAD rifiuta «committa docs/superpowers/reviews/<N>/spec-approval.md prima di approve plan». Test.
- D10: `tests/test_check_common.py:30` `test_spec_locked_after_approval_in_later_phase` (fixture righe 22-23 con «approvata\n») si riscrive con un'intestazione valida (`render_approval`) con `path == spec_path`: il blocco della spec ora la richiede (decisione 19).
- D7: `locked_docs` letto dal disco (`docs/superpowers/reviews/*/spec-approval.md` del worktree), calcolato una volta per chiamata di `diff_violations`.
- Atti nei test: applicati dalla libreria con `now=fl.now` (`ApplyCase.apply` come in `test_actapply.py:33-36`), perché gli atti registrati con l'ora del banco scadrebbero con l'ora reale (D20).

## Task 8
- D5: `reopen` rifiuta con la stessa regola di `sync._in_use` (`sync.py:132-147`: task `running`/`review`, implementatore `running`, task non `done` con commit): estraila in una funzione pubblica condivisa (in `tollgate_core`, nel modulo che possiede la query) usata da `sync` e da `reopen`; i messaggi di `sync` restano identici; `reopen` indica `/tollgate:resolve writer` per l'implementatore. Test anche per il task `pending` con commit.
- Atti nei test dalla libreria con `now=fl.now` (D20).

## Task 9
- D3: `files` di `locate_spec_approval`: `start --spec` legge la punta del ramo predefinito; `finish check`, `open-pr` (HEAD = SHA spinto) e `adopt` (punta del ramo) leggono l'albero di quel commit; mai il disco.
- D4: `openpr.facts` valorizza `spec_reviews_dir` e `spec_audit` solo se il lavoro ha `spec_path`; altrimenti null. `tests/test_openpr.py:777-795` `test_counters_and_reviews_dirs` si riscrive con un lavoro L2 con `spec_path`.
- D8/D10: si riscrivono `tests/test_adopt.py:146-152` e i tre sottocasi «approval» di `test_l2_superseded_or_mismatched_approvals_go_back` (`test_adopt.py:154-181`, ora `plan` con `plan_adversary` acceso), e l'helper `l2_lab`/`approve` di `tests/test_finishcheck.py:253-270` con `test_l2_approved_spec_and_reviews_files_exempt` (servono `spec_sha` e i report).
- D18b: `tests/test_criteria_p3c.py` nasce qui con `LaterSliceTest`; il Task 15 lo estende.

## Task 10
- D10: `tests/test_checkpoint.py:89-100` (oggi un lavoro L1 con la fase forzata) si riscrive su un lavoro L2, con `tollgate.toml` nella base (il banco lo committa già).
- D19: `_cap_step` per i blocchi dell'audit stampa `audit.STEPS["resolve"]` con `<id>` sostituito dall'id del blocco.
- D18f: il testo di `post_edit` in L2 (`bin/tollgate_checks/post_edit.py:44-45`, «plan-adversary, poi /tollgate:approve plan») punta a `/tollgate:spec-audit` (che lancia l'avversario del piano); file aggiunto al task, con il suo test in `tests/test_check_post_edit.py`.

## Task 11
- D18a: il passo 6 (riga 32) mette la frase «l'esenzione di docs/superpowers/reviews/<N>/ vale a ogni livello» nella docstring di `violations.scope_exempt` (dove sta l'esenzione dopo il Task 4), e non in `finishcheck._own_document` se il Task 9 l'ha tolta.
- D18c: `tests/test_git.py` è tra i file del task (test di `range_base`).

## Task 13
- D10: `tests/test_manifest.py:125` (`argument-hint: "#N [L1|L2]"` esatto) si aggiorna con `--spec`.
- D19: le skill citano i passi di `audit.STEPS` con la parte fissa; `STEPS["resolve"]` con `<id>`.

## Task 15
- D18b: `tests/test_criteria_p3c.py` esiste già dal Task 9: si estende.
- D2, D3, D5, D6, D7, D12, D13, D15, D16, D19: entrano nella rev 24 della spec dove cambiano il contratto (6.2 ordine dei giri, 8.4 `reopen` e sospensioni, 7.4/8.3 esenzione e calcolo una volta, 18.3 valori proibiti nelle intestazioni).

## Task 7 (dalla revisione del Task 6)
- `FlowLab` aggiunge `.tollgate-run/` (e le altre voci che `start` scrive in `info/exclude`, se mancano) all'`info/exclude` del banco alla creazione, come fa `start` in produzione; `RoundCase.lab` in `tests/test_check_audit_round.py` non lo ripete più.

## Task 11 (dalla revisione del Task 10)
- Riga 24 estesa: anche in `tests/test_checkpoint.py` la classe `CheckpointL2Case` sta dopo il blocco `if __name__ == "__main__"`: spostala sopra, come per `test_verdicts.py` e `test_profiles.py`; `python3 -B tests/test_checkpoint.py` esegue lo stesso numero di test della scoperta. Controlla con un grep che nessun altro file di `tests/` abbia classi dopo quel blocco.

## Task 12 (dalla revisione del Task 10)
- `audit.peek` non cattura `UnicodeDecodeError` di `git.text_at` (spec o piano non UTF-8): `peek` non solleva mai (decisione 20); verifica anche `prepare`, che deve dare un rifiuto e non un traceback. Test con un piano non UTF-8 committato.
- (dalla revisione del Task 11) `violations.active_profile_names` con `git.head(wt)` nullo restituisce `[]` invece di chiamare `changes(head=None)` (che includerebbe worktree e non tracciati); test.
