## Modelli per ogni lavoro (scelta dell'utente del 22/11/2026)

Chi trova i bug usa Fable, chi scrive o corregge usa opus, mai sonnet né haiku (progetto di C, sezione 11; memoria `feedback-modelli-fable-opus`). Consumo dell'abbonamento, nessuna spesa in denaro.

| Lavoro | Modello |
|---|---|
| Controller della sessione d'esecuzione (coordina, sonde, schede delle fonti, domande, prova reale) | la sessione: Fable |
| Scan pre-flight | Fable |
| Chi scrive codice e test: Task 1, 2, 3, 4 (Step 1, 2, 3a, 4, 5), 5 (Step 2, 4, 5), 6 (Step 2-5), 7, 8, 10, e il rapporto della prova (Task 9 Step 2) | opus |
| Chi scrive il testo delle regole (Task 4 Step 3b), il rapporto delle fonti e la pagina per l'utente (Task 5 Step 3): giudizio, scelta dell'utente del 20/11 | Fable |
| Giri di correzione: sul testo delle regole, del rapporto delle fonti o della pagina | Fable |
| Giri di correzione: su codice, test, frammento, documenti d'uso, spec | opus |
| Verifica delle fonti (Task 5, Step 1), revisori di ogni task, ri-revisioni | Fable |
| Revisione del piano (questa sessione) e revisione finale del ramo | Fable |
| Agenti di tollgate dopo il Task 1: ogni revisore (`task-reviewer`, `reviewer-<area>`, `final-reviewer`, `final-<area>`, `finding-verifier`, `spec-auditor`, `spec-adversary`, `plan-adversary`) | `fable` |
| Agenti di tollgate dopo il Task 1: ogni implementatore (`implementer`, `implementer-<area>`), anche dal giro 4 | `opus` |
| Sessione di `claude -p` nelle prove (`run-b1-flow.sh`, `run-b1-checks.sh`) | `opus` |
| Eval di `evals/` (`claude plugin eval`), dopo il Task 1 | `claude-opus-5-5` (scelta dell'utente del 22/11: anche gli eval, subito) |
