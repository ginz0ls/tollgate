# Revisione Task 2 (c437557..4f203da)

### Aderenza
- ✅ `SAVED_READERS` tolto, nessun uso residuo (grep su spikes, tests, bin). `_saved_copy` (`spikes/b1/flowreg.py:296`) usa solo `SAVED_PATH`.
- ✅ D1: prefissi `< > , { [ @` in `SAVED_PATH` (`flowreg.py:33`); la sola cartella con o senza `/` è accettata (verificato a mano: `ls /x/tool-results/`, `ls /x/tool-results`, `cat</x/tool-results/a.txt`, `cat a>/x/tool-results/b`, `x@/y/tool-results/a` danno un nome; `cat app.py`, `tool-results.txt`, `tool-results-old/x`, `my-tool-results/x` danno None).
- ✅ `_swap_saved` (`:312-318`) sostituisce `stdout` e `stderr` non vuoti; `_third_party` (`:377-381`) li considera entrambi; idempotente (test `bash_stderr` fa due passate).
- ✅ Intestazione di `limiti.txt` e riga 2 di `run-b1-flow.sh` generiche; due test (b1 e backend).
- ✅ Evidenze committate non toccate; `test_committed_evidence_has_no_long_web_results` rieseguito da me: OK. `suite-task-2.log` finisce con `exit 0`. Vincolo `addCleanup` sul `mkdtemp` rispettato (`write_stream`).
- Scostamento dichiarato (test dell'intestazione in due metodi): accettabile.

### Punti di forza
- Il lookahead di fine percorso evita falsi positivi come `tool-results.txt` e `tool-results-old/`.
- I test usano la forma vera dello stream, controllano blocco, `stdout` e `stderr`, il JSON riletto e l'idempotenza.
- `test_third_party_detects_bash_stderr` copre il caso blocco già segnaposto con `stderr` ancora in chiaro.

### Rilievi
Critical: nessuno. Important: nessuno.

Minor
1. `flowreg.py:33`: il lookahead `(?![^\s'"|;&<>()])` fa mancare la sola cartella seguita da `,`, `}`, `]`, `:` o `\` (es. `ls {/x/tool-results,/y}`, `"${D:-/x/tool-results}"`). Con un file dentro (`.../a}`) il match avviene, quindi è solo la forma «cartella nuda». Va contro «si sbaglia dalla parte sicura», ma è rara; per chiuderla basta aggiungere `,}\]\\:` all'insieme del lookahead.
2. `test_b1_scripts.py` (`test_togli_pagine_bash_any_reader`): dei sei prefissi di D1 si prova solo `<`; mancano `>`, `,`, `{`, `[`, `@`. Mancano anche i casi negativi del lookahead (`tool-results.txt`, `tool-results-old/x`) e un `Bash` con `stdout` e `stderr` entrambi pieni.
3. `_saved_copy` su un percorso tra virgolette con spazi (`"/x/tool-results/a b"`) dà il nome `a`: solo estetico nel segnaposto.
4. Il report non porta evidenza di esecuzione oltre l'esito riassunto; ho verificato io `suite-task-2.log` e il test delle evidenze.

Falsi positivi per eccesso (`git commit -m 'fix tool-results'` diventa segnaposto): voluti dal piano.

### Valutazione
**Qualità del task:** Approvato. **Motivo:** i requisiti del piano e di D1 sono implementati e verificati; restano solo rifiniture minori sui test e due bordi rari del rilevatore.
