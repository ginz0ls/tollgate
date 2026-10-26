# Task 15 — report

Commit: a9ae2c8 «tollgate P5: prove dei criteri, spec rev 26, piano principale, chiusura del nucleo» (BASE a9e2099). File: spec, piano principale, `docs/uso/limiti.md`, `docs/uso/eval-e-ci.md`, `tests/test_docs.py`.

## Cosa ho cambiato

- **Spec rev 26** (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`): intestazione; 1.2 (limiti rivisti: azioni fissate per SHA, comando senza report, verdetto precedente fino al `pending` di `guard`, `[skip ci]` sull'ultimo push, artefatti con la nota su `digest-mismatch`, cache sul privato; limiti nuovi: aggiornamento del CLI durante un run (M-5), le due voci di 17 in grassetto (D12), sandbox senza rete, un modello e tre corse, due casi extra ridotti); 1.3; 3 (albero, `PINS`, `evals/`, `ci.yml`, `README.md`, `docs/uso/`, paragrafo su eval, CI e documentazione); 9.1 (azioni fissate, riga `guard` con `pending`, riga sentinella, `config_sha` per blob, «Stato in attesa»); 9.2 (`base_ids_missing_command`); 9.3 (intervallo della sentinella); 9.4 (aggiornare le azioni fissate); 9.5 (testo `base_test_ids` spento, misurato in P5); 14 (righe Gate solo `detect`, Comportamento, CI; casi adattati, extra, grader deterministici, ablazione, soglia, esecutore); 16 (verificato in P5); 17 (= voci di 1.2); 20 (riga 26).
- **Piano principale**: Stato (P5 chiuso sul ramo, merge in attesa dell'OK, 2897 test, nessun riferimento a `.superpowers/`), sezione 2 riga P5, sezione 3 (riga `evals/_kit`, interfacce nuove del gate, esito dei vincoli per P5, esito dei minori rinviati di P4), sezione 4 («Prove dei criteri di P5»: 9 casi spec con esecutore, punteggi, Δ, prove a secco, rapporto; e1, e3, e4, e5, e2 senza esito con il motivo; CI con run 40252693867 e SHA 87cc62f; test delle voci nuove del gate; riga 17), sezione 5 (costo degli eval misurato), sezione 7 nuova «Dopo la v1».
- **`docs/uso/limiti.md`**: titoli allineati alle voci in grassetto di 1.2 (stesso insieme), senza punto finale; riscritti i tre titoli che contraddicevano il corpo; sezione «I guardrail locali» (era «Gli eval e i guardrail locali») e sezione «Gli eval» con tre voci.
- **`docs/uso/eval-e-ci.md`**: soglia 0,66 resa con i pesi (somma pesata dei grader passati sul totale, media delle corse; cammini corretti ≥ 0,75; esclusioni dei casi `spec`), rinvio al rapporto `docs/verifiche/2026-10-23-p5-eval.md` e a quello della CI, bersaglio senza `dependencies`, paragrafo su come sono girate le corse (esecutore, sessione non legata, `.git/config`, limite di `s5`), `e2` a secco.
- **`tests/test_docs.py`**: `spec_limit_titles` ridotto alla sola 1.2 (ruling Task 12); in più `/Users/` in `test_no_local_paths` e controllo delle ancore dei collegamenti (minor del Task 12).

## Voci del ledger coperte

- D12: le due voci di 17 in 1.2 in grassetto; 17 resta «le voci di 1.2». Fatto.
- D19: 9.1 «Stato in attesa» e riga `tollgate-guard`; 14 riga Gate solo `detect`; 1.3 casi extra; 1.2/9.3 `[skip ci]` sull'ultimo push non controllato fino al successivo; e2 con il testo reale di `reopen`: il testo («spec riaperto (…): fase spec_audit») non l'ho riportato nella spec, perché la rev 26 dice solo che `e2` è a secco (il test lo cerca; non c'è un punto della spec dove stia). Dubbio sotto.
- D1 definitivo (e2 a secco, e4 fino a `finish check`): decisione 6 in spec 14 e voce di 1.2.
- Ruling `digest-mismatch`: nell'item degli artefatti di 1.2 e in `limiti.md`.
- Ruling Task 12 su `test_limits_match_spec_1_2`: ridotto a 1.2.
- Minori del Task 12: tre titoli riscritti; punteggiatura dei titoli; nome della sezione; soglia 0,66 in `eval-e-ci.md`; `/Users/` e ancore aggiunti. Non fatto: `~/` in `test_no_local_paths` (`installazione.md` lo usa legittimamente per `~/.claude/settings.json`).
- Decisione 24: 1.2, 3, 9.1, 9.2, 9.4, 9.5, 14, 16, 17, 20 fatti. Aggiunte 1.3, 9.3, 9.5 misurato.

## Test

- `tests/run`: python3.11 `Ran 2897 tests in 2507s OK (skipped=2)`; python3 (3.13.5) `Ran 2897 tests in 2049s OK`.
- `python3 -B -W error::ResourceWarning -m unittest discover -s tests -t .`: `Ran 2897 tests in 2125s OK`, exit 0.
- Nessun «unclosed database» in nessuna delle tre uscite. Ricompare un `ResourceWarning: unclosed file` stampato (non fallito) da `tests/test_p5_scripts.py:951` (`open(reg).read()` senza chiusura, codice del Task 1), già presente nei log delle suite precedenti: non l'ho toccato.
- Nessun `__pycache__` in `git status`.

## Dubbi

1. La tabella del rapporto degli eval dà «sotto soglia: difetto corretto» per `s5` ed `e3` accanto a 0,75 e 1,00 (ultima invocazione). Ho scritto nella matrice il punteggio finale e il giro che era sotto soglia, come nella nota «due casi sotto soglia al primo giro» del rapporto.
2. «Δ medio +0,73» è quello del rapporto; l'ho ricontrollato (6,57/9).
3. Il testo reale di `reopen` (D19) non compare nella spec.
4. Sezione 7: ho incluso anche i minori dei task di P5 del ledger (che sta fuori dal repo) in un elenco unico con il motivo; se è troppo, si possono ridurre.
5. Non ho potuto verificare in CI che il commit passi: l'ultimo run verde è su 87cc62f.
