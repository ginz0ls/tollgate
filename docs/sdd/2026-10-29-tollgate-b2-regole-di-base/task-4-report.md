# Task 4: report

Implementato: verifica applicata (11 fonti ok, 2 no). Tolte le bozze n. 10 e n. 11 da `skills/rules-base/SKILL.md`; la n. 12 è R-BASE-10 (testo e fonte invariati, resta senza `[blocca]`). Creati `docs/profili/verifiche/base-fonti.md` (tabella con 11 righe ok, sezione «Regole tolte» senza id) e `docs/profili/base.md` (pagina in parole semplici, 10 regole, sezione delle regole tolte con le correzioni possibili). Nessun `approved`.

Test aggiunti in `tests/test_rules_base.py` (classe `RulesBasePageTest`): sources_report_covers_every_rule, page_lists_every_rule, page_blocca_matches_skill, page_explains_what_changes. `test_model_name_rule` e gli altri del Task 3 non dipendevano dal numero 12.

TDD: RED con `python3 -B -m unittest tests.test_rules_base`: 4 errori (file mancanti). GREEN: 13 test OK. Il test «Blocca?» ha intercettato un mio errore (R-BASE-10 segnata sì sulla pagina, nella skill non è `[blocca]`): corretto a no.

Suite completa (`PYTHONWARNINGS=error::ResourceWarning tests/run`): python3.11 3186 test OK (skipped=2), python3 (3.13.5) 3186 test OK. Il test instabile D16 non ha fallito.

Scostamenti: i test sul testo della pagina sono confrontati senza distinzione di maiuscole. Il piano (`docs/superpowers/plans/...`) conserva la numerazione a 12 regole, come storia.

## Fix round 1

Modifiche: `docs/profili/base.md` riscritta nelle sezioni «Cosa sono» e «Cosa cambia se approvi» (task, report, plugin, main, progetto di B, build spiegati alla prima comparsa; frasi più corte; L0 = avviso alla sessione principale di Claude Code; colonna «Da dove viene» accorciata). `docs/profili/verifiche/base-fonti.md`: aggiunta la verifica mia con `cmp` (le due licenze in `LICENSES/` identiche alle copie in `fonti/`, esito 0 e 0); tolta l'idea che il verificatore le abbia controllate. `tests/test_rules_base.py`: l'ultima frase attesa dalla pagina è ora «nei lavori veri vale da quando la nuova versione, una volta unita al ramo principale (main), viene installata sul tuo computer» (stessa forza).
Comando: `PYTHONWARNINGS=error::ResourceWarning python3 -B -m unittest tests.test_rules_base tests.test_docs`. Output: Ran 19 tests, OK.
