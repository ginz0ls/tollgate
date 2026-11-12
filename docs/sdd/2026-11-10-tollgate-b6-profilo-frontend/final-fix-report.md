# Giro di correzione della revisione finale B6

Commit `0e82c40` (tollgate B6: correzioni della revisione finale).

## Rilievi
- M1: `agents/implementer-frontend.md` (sezione «Area `frontend`», riga 53): i test del progetto si lanciano con `<programma> verify` (con `--related`), anche se sono comandi `npm`. Stessa motivazione corretta nella spec rev 33 (6.3, voce «Costo del divieto di `node` e `npm`») e nel piano principale (sezione 9, blocco «A B7-B8, da B6»): il canale è `verify`, il `dod` di `frontend` è vuoto.
- M2: P39 nella tabella della spec 6.3 (prima di P38 in ordine, dopo P38 nel file: P38, P39), test `test_real_precedence_p39` in `tests/test_init.py` (`FrontendPrecedenceTest`); frase sul rimedio di `routes/` in `docs/profili/frontend.md` (paragrafo «I moduli di rotta e la cartella `routes/`»); riga nella sezione 15 del piano principale; «P1-P38» diventa «P1-P39» in spec, catalogo e piano principale.
- M3: spec 6.3 (riga «Un file, un profilo verticale»), riga P37 e docstring di `test_real_precedence_p37`; punto 18 di `docs/profili/frontend.md`.
- M4: `docs/uso/comandi.md:167` «Le caricano».
- Triage 12: docstring di `test_removed_sources_are_not_in_the_skill` (`tests/test_rules_frontend.py:409`).
- Triage 20: virgola in `agents/final-reviewer.md:37` e `agents/finding-verifier.md:13`; gli `assertIn` di `test_manifest.py` non fissano quella frase.
- Triage 24: piano principale sezione 9 (voce «Chiuso da B4 per `infra` e da B6») e riga B4 della tabella di contratto (sezione 2): `**/*.<estensione>` ammessa da B6, le altre forme con `*` iniziale rifiutate.
- Triage 25: catalogo (`2026-10-08-tollgate-profili-verticali.md`, sezione 2): parentesi sulla forma `ext`.
- Triage 26: spec 16 (riga della prova `frontend`) e piano principale sezione 15 (riga «Prova reale corta»): `tollgate plan-check` inesistente e senza effetto, task 1 non prova il precaricamento; «Stato (11 novembre 2026)».
- Triage 27: tre voci del blocco «A B6-B8, da B5» (init/fragments, test di `rules-backend`, `flowreg`) con «Chiuso da B6» in testa.
- Triage 28: rapporto della prova: «stream del passo 2, `passo2/tentativo-1/claude.jsonl`, riga 147».

## Test mirati
`python3 -B -m unittest tests.test_init.FrontendPrecedenceTest` -> 40 test OK (include p39).
`python3 -B -m unittest tests.test_manifest tests.test_rules_frontend tests.test_docs tests.test_init.FrontendPrecedenceTest` -> 155 test, OK (skipped=3).

## Suite
`PYTHONWARNINGS=error::ResourceWarning tests/run` -> `suite-final-fix.log`: Python 3.11 e 3.13, 3895 test, OK (skipped=13 e 11), `exit 0`, nessun «unclosed».

## Note
Il test p39 passa subito (descrive un comportamento già vero del codice: è una prova della tabella, non un cambio). Non toccati i file approvati delle altre aree né `skills/rules-frontend/SKILL.md`.
