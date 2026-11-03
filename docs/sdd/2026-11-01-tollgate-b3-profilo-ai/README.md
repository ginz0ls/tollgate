# Registro dell'esecuzione del piano B3 (infrastruttura dei profili e profilo `ai`)

Copia del workspace di subagent-driven-development del piano `docs/superpowers/plans/2026-11-01-tollgate-b3-profilo-ai.md` (ramo `b3-profilo-ai`, 22 commit `b35c538..7283c73`, unito su `main` **in un solo commit** (squash) `72ed64c` il 3 novembre 2026 con l'OK dell'utente; 3394 test). Nome utente e host sono anonimizzati (`USER`, `HOST`).

L'unione è in un solo commit perché un commit del ramo (`f8f5331`) conteneva nelle evidenze il testo intero di pagine di Anthropic e di skill esterne, poi tolto (revisione finale, I-1, e giro finale 2): così quel testo non è mai arrivato su GitHub. I commit citati nel registro sono quelli del ramo locale.

- `progress.md`: il ledger. Contiene:
  - lo scan dei conflitti prima del Task 1, con le decisioni D1-D20;
  - gli 11 task completati, con i giri di correzione e l'approvazione delle regole da parte dell'utente (2026-11-02, 11 regole, i quattro punti di «Da decidere tu» come proposto; il 2026-11-02, alla revisione finale, il marcatore `from "openai"` rimesso su sua richiesta);
  - le righe `Ruling:`, cioè le decisioni prese durante l'esecuzione, ognuna con il suo costo se sbagliata;
  - i minori rinviati, la revisione finale, i due giri di correzione finali, le tre corse finali della suite.
- `carry.md`: le decisioni del controller portate nei singoli task.
- `preflight-brief.md` e `preflight-scan.md`: la richiesta e l'esito dello scan dei conflitti del piano.
- File dati ai subagenti:
  - le parti del piano: `decisions.md`, `global-constraints.md`, `review-focus.md`, `coverage.md`, `file-map.md`, `cautele.md`, `plan-path`;
  - le regole del loro ruolo: `implementer-rules.md`, `reviewer-rules.md` e `rereview-rules.md`.
- Testo, report e revisioni dei task: `task-N-brief.md`, `task-N-report.md`, `task-N-review.md`, `task-N-rereview-1.md`.
- Verifica delle fonti di `rules-ai` (Task 6): `task-6-fonti-brief.md`, `task-6-fonti.md` (tutte le regole e i marcatori), `task-6-fonti-r-ai-06.md` (verifica mirata della fonte nuova proposta per R-AI-06). Le citazioni sono di al più una riga.
- Prova reale (Task 10): `task-10-fatti.md` (i fatti raccolti dal controller), `task-10-report.md`, `task-10-review.md`.
- Revisione finale dell'intero ramo:
  - `final-review-brief.md` e `final-review.md`: la revisione (opus: non pronto, 0 critical, 1 important, 7 minor), con il triage dei minori rinviati;
  - `final-deferred.md` e `final-rulings.md`: i minori e le ruling passati al revisore;
  - `final-fix-brief.md` e `final-fix-report.md`: i due giri di correzione;
  - `final-rereview-1.md` e `final-rereview-2.md`: le ri-revisioni (sonnet), entrambe senza rilievi aperti.
- `suite-finale.txt`: le tre corse finali di `PYTHONWARNINGS=error::ResourceWarning tests/run` su `7283c73` (python3.11 e python3).
- Dove sono gli esiti:
  - regole: `skills/rules-ai/SKILL.md`, frammento `templates/profiles/ai.toml`, pagina per l'utente `docs/profili/ai.md`, verifica delle fonti `docs/profili/verifiche/ai-fonti.md`;
  - prova reale: `docs/verifiche/2026-11-01-b3-prova-flusso.md`, evidenze in `docs/verifiche/evidenze/b3/`.

Non sono stati copiati: i pacchetti di revisione (`.diff`, si rigenerano con `git diff` sul ramo locale), i log delle corse della suite, `fonti/` (copie delle pagine dei fornitori, citate con URL e data nella verifica delle fonti), `fatti/` (appunti della scrittura del piano) e una cartella di copie di testo delle pagine creata da un subagente durante la verifica.
