# Operazioni della calcolatrice

## Obiettivo
Aggiungere a `src/calc.py` la moltiplicazione, la divisione e la potenza, ognuna con il suo test, in tre fette successive.

## Fette previste
1. Moltiplicazione: `moltiplica(a, b)`, il suo test e una pagina d'uso
2. Divisione: `dividi(a, b)` e il suo test
3. Potenza: `eleva(a, b)` e il suo test

## Tane di coniglio
- Divisione per zero: `dividi(a, 0)` solleva `ZeroDivisionError`, nessun valore speciale.
- Esponenti negativi: `eleva(a, b)` con `b` negativo restituisce un decimale, senza arrotondare.

## Cosa non fare
- Niente funzioni oltre alle tre elencate.
- Niente conversioni di tipo: gli argomenti sono numeri.
