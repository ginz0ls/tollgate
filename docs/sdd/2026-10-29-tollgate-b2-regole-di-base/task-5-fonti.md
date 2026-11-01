# Verifica delle fonti della bozza n. 10 rimessa (Task 5)

Verificatore: Explore, sonnet, sola lettura (brief task-5-fonti-brief.md). Uscita riportata dal controller.

Metodo: letto il brief; `sha256sum -c SHA256SUMS` in `W/fonti/`: tutti e 6 i file OK; `grep -n` e `sed -n` su `fonti/superpowers/skills/systematic-debugging/SKILL.md` (righe 168-182) e `fonti/superpowers/skills/verification-before-completion/SKILL.md` (righe 74-90); intestazione di `fonti/superpowers-LICENSE` («MIT License, Copyright (c) 2025 Jesse Vincent»). Nessuna rete, nessuna modifica.

Regola verificata: «R-BASE-10 [blocca] La correzione di un difetto porta un test che lo riproduce: il report mostra che il test fallisce senza la correzione e passa con la correzione.»

| Regola | Fonte | Citazione | Esito |
|---|---|---|---|
| R-BASE-10 | superpowers 7.0.0, skills/systematic-debugging/SKILL.md, «Phase 4: Implementation» (punto 1) | «1. **Create Failing Test Case**» e, subito sotto, «MUST have before fixing» | no: regge solo la parte «porta un test che riproduce il difetto»; non dice che il report debba mostrare il fallimento senza la correzione e il successo con la correzione |
| R-BASE-10 | superpowers 7.0.0, skills/verification-before-completion/SKILL.md, «Key Patterns» («Regression tests (TDD Red-Green)») | «✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)» | ok |

Riepilogo: la regola ha una fonte `ok` (verification-before-completion). Il «report» come luogo dove si mostra l'esito non è citato da nessuna delle due fonti: è il veicolo del meccanismo di B (sezione 3.2), come per le altre regole (osservazione del verificatore del Task 4 su R-BASE-01, 02, 07); la seconda fonte si avvicina con «Evidence before claims» e «State claim WITH evidence».
