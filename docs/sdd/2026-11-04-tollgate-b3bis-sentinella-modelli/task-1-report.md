# Report Task 1: confronto puro dei modelli

Commit a7db942 «tollgate B3-bis: confronto puro dei modelli con gli elenchi ufficiali».
File: `bin/tollgate_analysis/models.py` (nuovo), `tests/test_models.py` (nuovo, 37 test).

## Cosa
Modulo senza import di tollgate e senza rete: `PROVIDERS`, `ModelInfo` (frozen), `ModelsFormatError(ValueError)`, `parse_pages`, `literals`, `used`, `gemini_family`, `findings` con le firme del brief. Decisioni 2, 3, 13; carry D19 e D20 e la regola degli alias (Step 0 a) implementate.

## TDD
- RED: `python3 -B -m unittest tests.test_models` -> `ImportError: cannot import name 'models' from 'tollgate_analysis'`, `FAILED (errors=1)`.
- GREEN: `python3.11 -B -m unittest tests.test_models tests.test_analysis_isolation tests.test_layers` e con `python3` -> `Ran 46 tests ... OK` (poi 37 in `test_models` dopo due ritocchi).
- Suite completa `PYTHONWARNINGS=error::ResourceWarning tests/run` (uscita in `task-1-suite.out`): Python 3.11.16 `Ran 3431 tests in 5852s, OK (skipped=4)`; Python 3.13.5 `Ran 3431 tests in 4383s, OK (skipped=2)`; `EXIT=0`; nessun «unclosed»/ResourceWarning.

## Scelte di dettaglio (dove il brief lascia margine)
- `parse_pages`: una chiave mancante (`data`/`models`) è `ModelsFormatError`, come un valore non lista. Fornitore sconosciuto: `ModelsFormatError`.
- OpenAI e OpenRouter: `family=None`, `stable=False` (non servono: «più nuovo» non si controlla), `retires` = data, `retiring` = data presente.
- `used`: alias solo per `provider == "anthropic"`; con più ID datati vale il più recente. Il prefisso `<fornitore>:` si toglie solo se iniziale (`xanthropic:` non conta).
- `gemini_family`: la variante si ferma al primo suffisso (tre cifre, `preview`, `exp`, `experimental`, `latest`); `gemini-3.7-flash-preview-tts` -> `("flash", (3, 7))` ma non stabile, quindi mai proposto (D19). Un `*-latest` in uso non dà «più nuovo».
- Date mostrate come `AAAA-MM-GG` (prefisso ISO del valore, es. `retires_at` RFC 3339); se non c'è un prefisso ISO, il testo neutralizzato; se manca, «data non indicata».
- Nella riga per modello `<id>` è il letterale come scritto nel file; `where` mancante -> `?`.
- «Più nuovo» di OpenRouter: `più nuovo non controllato: l'elenco non lo dà, guarda la pagina del fornitore originale — <page>` (decisione 3, senza nominare il fornitore).
- Righe per modello ordinate per letterale, poi quelle «non è nell'elenco», poi quelle per fornitore; duplicati tolti.
- Le righe «non è nell'elenco» escono anche se il fornitore non ha altri modelli in uso; le righe «non controllato» solo con almeno un modello in uso.

## Scostamenti dal piano
Nessuno. Test in più rispetto al brief: D19, D20, alias più recente, alias solo Anthropic, letterali su più righe, gemini `(3,)` < `(3, 6)`, newer sceglie il più recente, `ModelInfo` frozen, `where` mancante.

## Autorevisione
Completa rispetto a brief e carry; nessun extra; nessun `__pycache__` (git status pulito prima di `add`, solo i due file); nessuna rete, chiave o file utente toccato. Un test iniziale sui duplicati era mal formulato e l'ho tolto (due letterali diversi danno due righe legittime).

## Dubbi
Nessuno bloccante. Da confermare al Task 2/3: `findings` presuppone che il chiamante passi `infos` di un solo fornitore.
