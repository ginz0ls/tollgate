# Revisione finale del ramo p5-eval-ci (tollgate P5, ultima fetta del nucleo)

Sei il revisore finale dell'intero ramo, prima del merge su main. Revisione in sola lettura.

## Regole vincolanti (leggi prima, per intero)
- W/cautele.md — regole di cautela. In più: niente scritture nel checkout (unico file scrivibile: W/final-review.md), niente comandi di rete o GitHub, niente `claude`, niente `evals/run.sh` vero, niente kill per nome, niente `git stash`/checkout/reset, niente lettura di .env, auth.json, token o segreti.
- W/global-constraints.md — vincoli globali del piano.
- Non lanci subagenti. Se il diff è grande, rivedilo in più passate tu e dillo.
- Test: puoi lanciare test mirati (`python3 -B -m unittest tests.test_<modulo>`), non la suite intera (dura ~25 minuti; la lancia il controller).

## Cosa è stato fatto
P5 «eval e CI»: 15 task. Guardia `spikes/gh-p4/ghguard.py` profilo p5 e `spikes/p5/run-p5-checks.sh`; CI su Python 3.11/3.13 con azioni fissate; `gate`/`guard`/sentinella su GitHub; kit di eval (`evals/`, scaffold, shim `gh`) e 14 casi (s1-s9 spec, e1-e5 extra); `evals/run.sh` con tetto di spesa; documentazione d'uso; eval reali (3 corse per caso, costo 9.0632 USD); CI verde (run 40252693867); chiusura del nucleo (spec rev 26, piano principale).

## Requisiti
- Piano: docs/superpowers/plans/2026-10-23-tollgate-p5-eval-ci.md
- Spec: docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md (rev 26)
- Decisioni: W/decisions.md; ruling del controller: righe `Ruling:` di W/progress.md
- Review Focus: W/review-focus.md — verifica ciascuna delle 7 voci con il test indicato (esiste, asserisce davvero ciò che dice).
- Copertura: W/coverage.md
- Rapporti chiave: W/task-1-report.md, W/task-13-report.md, W/task-14-*.md (fix-1, fix-2, report-review), W/task-15-report.md e W/task-15-review.md
- Rapporti in repo: docs/verifiche/2026-10-23-p5-eval.md, docs/verifiche/2026-10-23-p5-ci.md

## Range
Base: a9b37e319f02c00190f4676aea9c5089766c87fa (main). Head: indicata nel messaggio di lancio.
Escludi le evidenze grezze (~3900 file): `git diff BASE..HEAD -- . ':(exclude)docs/verifiche/evidenze'` (~171 file, ~13.9k righe). Delle evidenze guarda a campione solo budget.tsv e una cartella di caso, e controlla che nel commit non ci siano `__pycache__`, worktree annidati o segreti.

## Minori rinviati
Le righe `minor (deferred)` di W/progress.md sono già state giudicate non bloccanti. Non riproporle come nuove. Se però ritieni che una sia in realtà important (per esempio perché il Task 14 ha mostrato che succede), dillo in una sezione apposita.
Già noto al controller, da correggere nel giro finale: tests/test_p5_scripts.py:951 `open(reg).read()` non chiude il file.

## Cosa mi serve
Segui il formato del revisore di codice: Strengths; Issues Critical/Important/Minor con file:riga, cosa, perché, come; «Declined to judge» (ogni comportamento messo da parte, una riga con il motivo); Assessment (Ready to merge? Yes/No/With fixes).
La spec è un documento di visione: dove tace, vale ciò che un utente ragionevole si aspetta.
Scrivi tutto in W/final-review.md (W = .superpowers/sdd/2026-10-23-tollgate-p5-eval-ci). Restituisci solo verdetto, conteggi e una riga per ogni critical/important.
