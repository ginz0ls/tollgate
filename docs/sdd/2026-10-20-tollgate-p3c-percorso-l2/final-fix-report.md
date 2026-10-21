# Giro di correzione unico della revisione finale (p3c-percorso-l2)

RED registrato (prima delle correzioni): 10 fallimenti e 5 errori su 167 test dei tre file toccati
(`tests.test_audit_prepare tests.test_l2acts tests.test_check_audit_round`), copia in
`/tmp/claude-1000/-home-crucco-MEGA-BIZ-VIBE-Plugin-IT-workflow/7559b7f5-d4d4-4aa4-9695-4b6c2897bf5d/scratchpad/red.txt`.

## I-1 ricerca unica dell'approvazione della spec
- Modifica: `l2tree.spec_approval` (`bin/tollgate_flow/l2tree.py:31-52`) cerca con lo `sha` attuale e
  solo se manca con `None`; dà `(CURRENT|STALE|MISSING, trovata)`. Usata da
  `audit._spec_approval_current` (`audit.py:327`, quindi anche `prepare`, `peek`, `status`) e da
  `l2acts._spec_approved` (`l2acts.py:185`).
- RED: `AttributeError: module 'tollgate_flow.l2tree' has no attribute 'spec_approval'` (4 test
  dell'helper); `test_prepare_in_plan_accepts_later_slice_approval` e
  `test_peek_does_not_say_reopen_spec` («spec cambiata dopo approve spec: /tollgate:reopen spec»);
  `test_later_slice_prepare_and_approve_plan_agree` (rifiuto a torto).
- GREEN: `tests/test_audit_prepare.py::SpecApprovalOfLaterSliceTest` (helper nelle tre combinazioni,
  `prepare` in `plan`, `peek`, caso con solo approvazioni superate), `tests/test_l2acts.py::
  ApprovePlanTest.test_later_slice_prepare_and_approve_plan_agree` (due approvazioni, issue 3
  superata e 5 corrente: `prepare` apre il giro, chiude, passa ad `approval`, `approve plan` ok).

## Riga 18 `_write_atomic`
- Modifica: `bin/tollgate_hooks/apply.py:125-137` rimuove il temporaneo anche su `ValueError`
  (`UnicodeEncodeError`); i due chiamanti in `_audit_report` catturano `(OSError, ValueError)` e
  danno un veto invece di un traceback.
- RED: `UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff'` (traceback del hook) e
  `Lists differ: ['.x.md.tmp'] != []`.
- GREEN: `tests/test_check_audit_round.py::WriteFailureTest.test_unencodable_body_leaves_no_temporary_file`
  e `test_write_atomic_removes_temporary_on_any_error`.

## Riga 38 rapporto di prova
`docs/verifiche/2026-10-20-p3c-prova-flusso.md`: backtick riga 5; `/tmp/tollgate-p3c/flow` ->
`/tmp/tollgate-p3c/prova-1/flow` alle righe 11, 13, 14, 21 (restano `/tmp/tollgate-p3c/flow` dove si
parla della cartella rigenerata e della prova accidentale); parentesi doppia nel «non esercitato».
Nessun test (documento).

## Riga 40 piano principale
`docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md:225`: «(P3c)» diventa «chiuse
in P3c (tabella «Prove dei criteri di P3c»)».

## m-1 `approval`
- Modifica: `audit._decide_approval` (`audit.py:395`) confronta piano e spec in HEAD con l'ultimo giro
  del piano (solo con `plan_adversary` acceso) e rifiuta con `audit.PLAN_CHANGED` («...riapri con
  /tollgate:reopen plan»); `peek` passa dalla stessa decisione (in `approval` il ripiego resta il
  passo `approve plan`); il rifiuto di `approve plan` (`l2acts._plan_adversarial`) usa lo stesso testo.
- RED: `'/tollgate:reopen plan' not found in "...lancia python3 '...' audit prepare"`.
- GREEN: `tests/test_audit_prepare.py::ApprovalPhaseTest` (invariato, piano cambiato, spec cambiata,
  avversario spento), `tests/test_l2acts.py::ApprovePlanTest.test_plan_changed_after_last_round_points_to_reopen_plan`.

## m-5 programma nei messaggi
`STEPS["resolve"]` (`audit.py:50`), `l2acts.py` (rifiuti dei giri sporchi di spec e piano) e i due
rifiuti di fase di `audit.py` (`prepare` e `decline`) usano `program_command`; skill `spec-audit`
aggiornata (riga del passo `resolve` con `<programma>`); il test del contratto confronta la parte fissa
(prima di `<id>`), che non cambia.
- RED: `test_resolve_step_names_the_program`, `test_dirty_plan_round_refused`,
  `test_refused_after_dirty_round_accepted_after_clean` (1 != 0 sul conteggio «audit prepare» nudo).
- GREEN: `assert_program_before_prepare` in `tests/test_audit_prepare.py` (usata anche in
  `tests/test_l2acts.py`).

## m-6
`skills/spec-audit/SKILL.md` (sezione «I tetti»): «In entrambi i casi il `resolve` sospende; per
l'audit a lenti la sospensione è definitiva.» Test: `tests/test_skill_contract.py::
SkillContractTest.test_caps_section_says_resolve_always_suspends`.

## Spec rev 24
6.2: paragrafo «Dove sta l'approvazione di una spec» (helper unico), punto 7 (stessa ricerca; controllo
in `approval`), punto 8 (rifiuto con `reopen plan`); riga 24 della sezione 20 (una frase). Nessuna
revisione nuova.

## Suite
- `tests/run` (python3.11 e python3 3.13.5): `Ran 1753 tests ... OK` per entrambe
  (927 s e 915 s).
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: `Ran 1753 tests in
  920.277s`, `OK`, nessun «unclosed database».
