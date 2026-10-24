# Piano: sottrazione senza segno

## Fatti verificati
Nessuno: piano di prova del banco degli eval.

## Decisioni
Nessuno: piano di prova del banco degli eval.

## Interfacce
Nessuno: piano di prova del banco degli eval.

## Must-have
M1. La somma resta corretta — test: tests.test_calc.CalcTest::test_somma
M2. La sottrazione resta corretta — test: tests.test_calc.CalcTest::test_sottrai

## Scope
I file dei due task, e nessun altro.

## Punti di arresto
Nessuno: piano di prova del banco degli eval.

## Rischi
Nessuno: piano di prova del banco degli eval.

### Task 1: Sottrazione senza segno
`sottrai(a, b)` restituisce la distanza tra i due numeri e non è mai negativa: `sottrai(0, 4)` vale 4.
- Modify: `src/calc.py`
- Test: `tests/test_calc.py`
**Must-have**: M1

