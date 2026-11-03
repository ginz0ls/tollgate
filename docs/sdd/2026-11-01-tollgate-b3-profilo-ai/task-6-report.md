# Task 6: rapporto delle fonti e pagina per l'utente

Commit 37f4519 «tollgate B3: fonti di rules-ai verificate e pagina per l'utente».

## Cosa ho fatto
- `skills/rules-ai/SKILL.md`: la riga `Fonte:` di R-AI-06 non rimanda più a R-BASE-04; dice che l'obbligo dell'indirizzo nel report è proprio della regola (per renderla controllabile) e che R-BASE-03 e R-BASE-06 chiedono lo stesso indirizzo solo nella nota. Nessun id cambia; 11 regole; nessun `approved`.
- `templates/profiles/ai.toml`: tolto il marcatore `from "openai"` (19 marcatori).
- `docs/profili/verifiche/ai-fonti.md`: rapporto (tabella regole con le fonti `no` scartate di R-AI-06, tabella marcatori, sezione «Regole tolte»), costruito dall'esito di `task-6-fonti.md`.
- `docs/profili/ai.md`: pagina in parole semplici (tabella N./In parole semplici/Blocca?/Da dove viene, «Quando si accende», «Da decidere tu» con i 4 punti a-d, «Regole tolte dalla verifica» con la bozza sul testo del modello, «Come rispondere»). Non c'è «Approvata dall'utente».
- `tests/test_rules_ai.py`: `RulesAiPageTest` (12 test): copertura regole nel rapporto, fonti scartate fuori dalla skill, `test_detect_markers_verified`, `test_real_markers_not_in_tollgate_bin` (tutti i file di `bin/`), pagina con tutte le regole, «N.» uguale all'id, Blocca? uguale alla skill, spiegazione di cosa cambia (cerca nomi e id), pagina non approvata, «Da decidere tu», sezione tolte senza id, niente `/home/`.

## TDD
RED: `python3 -B -m unittest tests.test_rules_ai` -> `FAILED (failures=1, errors=10)` (file mancanti, R-BASE-04 ancora in R-AI-06).
GREEN: stesso comando più test_fragments, test_docs, test_rules_base, test_skill_contract, test_manifest -> 135 test OK; test_init ProfileBlocksTest e DetectTest -> 46 OK. `claude plugin validate --strict .` -> uscita 0.
Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` (`task-6-suite.out`): python3.11 3359 test OK (skipped=2), python3.13 3359 OK, EXIT=0, nessun «unclosed».

## Scostamenti dal piano
- Il rapporto elenca anche le fonti proposte e scartate per R-AI-06 (R-BASE-03, R-BASE-06) con esito `no`, e il test richiede almeno una riga `no`.
- Il test sulla spiegazione cerca nomi (init, L1, diff, stabile, cartelle, fornitori), non frasi.

## Dubbi
- Nella pagina, sotto «Regole tolte», ho aggiunto una frase su R-AI-09/10 valide solo per Anthropic: è informazione, non una regola tolta; se la si vuole altrove, spostarla.
- Le riserve sui marcatori `@google/genai`, `google.golang.org/genai`, `from google import genai` restano dichiarate nel rapporto.

## Fix round 1
Rilievi 1-10 della revisione, tutti corretti (pagina, rapporto, test; skill e regole intatte, nessun `approved`).
- Pagina: colonna «Si giudica su» (test `test_page_judged_on_matches_skill`, per id); R-AI-06 e R-AI-08 dicono tutto ciò che la regola chiede; «Quando si accende» senza contraddizione (`/tollgate:init --update` e copia del blocco); definizioni di API, ID del modello, alias, prompt injection, `tool_result` in «Cosa sono»; la frase su R-AI-09/10 sta in «Cosa sono», senza «non ho trovato una pagina».
- Rapporto: intestazioni e filetti duplicati tolti (nuovo `test_tables_have_one_header`, che fallisce con l'intestazione doppia); `no` senza grassetto; rimando alla bozza tolta reso autosufficiente.
- Test: `test_removed_sources_are_not_in_the_skill` controlla che ogni riga `no` sia una fonte uscita (regola ancora coperta da `ok`) e non impone più che esista; `test_page_is_a_proposal` e `test_page_brings_the_open_choices_to_the_user` fanno `skipTest` se `approved` è nella skill (docstring); aghi di `test_page_explains_what_changes` sostituiti da espressioni regolari su init+copia, livello L1, R-AI-01 e solo diff, «il più recente» = ultimo modello stabile.
Comando: `python3.11 -B -m unittest tests.test_rules_ai tests.test_fragments tests.test_docs` e lo stesso con `python3` -> `Ran 55 tests ... OK` in entrambi. Suite completa non rilanciata (richiesto).
