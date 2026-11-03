# Piano di prova: costante del modello per il riassunto

## Fatti verificati

- Il progetto ha `ai/__init__.py`, `ai/summary.py` (la funzione `riassumi(client, testo, model)` riceve il modello dal chiamante), `services/notify.py` e `tests/test_smoke.py`.
- `ai/models.py` non esiste ancora.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- `ai/models.py` contiene la sola costante `SUMMARY_MODEL`, una stringa con l'identificativo del modello Claude scelto dall'agente dalla pagina ufficiale di Anthropic.

## Interfacce

- `ai.models.SUMMARY_MODEL`: stringa non vuota che comincia con `claude-`.

## Must-have

- M1. `SUMMARY_MODEL` è una stringa non vuota che comincia con `claude-` — test: tests.test_models.ModelsTest::test_summary_model

## Scope

- `ai/models.py`, `tests/test_models.py`.

## Punti di arresto

- Nessuno: il task è una sola costante.

## Rischi

- Nessuno di rilievo.

### Task 1: Costante SUMMARY_MODEL

- Create: `ai/models.py`
- Test: `tests/test_models.py`
- Must-have: M1

In TDD: scrivi in `tests/test_models.py` un `ModelsTest.test_summary_model` che verifica che `ai.models.SUMMARY_MODEL` sia una stringa non vuota che comincia con `claude-`, poi crea `ai/models.py` con la costante. Esegui `python3 -m unittest discover -s tests -t .` e committa.
