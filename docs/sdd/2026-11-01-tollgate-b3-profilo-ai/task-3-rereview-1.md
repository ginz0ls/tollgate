# Ri-revisione giro di correzione 1, Task 3 (8e438c0)

### Verdetti sui rilievi
- **A. `test_real_trees_light_no_profile` deve essere una garanzia vera**: INDIRIZZATO. `tests/test_init.py` (nuovo corpo): `fragments.load(ROOT)`, `skipTest` con motivo se vuoto; plugin temporaneo con i frammenti veri copiati (`fr.source`) e una skill `rules-<area>` con `approved:` per ciascuno; tre alberi (push, installato, installato + proposta) in `subTest`, con asserzioni `text == ""` e nessuna riga «proposto con». Regge dopo il Task 7: i frammenti si leggono dalla cartella vera, non da un elenco fisso. Oggi `templates/profiles/` non esiste, quindi il test salta (verificato: la cartella è assente); l'implementatore dichiara una prova a mano con un `ai.toml` provvisorio, non ripetibile qui.
- **B. Albero vero dei test di init, non copia a mano**: INDIRIZZATO. L'albero «push» è `{*DEFAULT_FILES, "tollgate.toml"}` con `DEFAULT_FILES` importato da `tests/hookkit.py`, la stessa fonte che `FlowLab` usa (`tests/flowkit.py:109`); quello installato è `install.files(ROOT, …)`.
- **M1 ramo «togli» di `_drift`**: INDIRIZZATO. `test_declared_profile_stale_rule_removal_reported`: `R-X-09` dà «togli», `mia-regola` non compare.
- **M2 scarto con `ConfigError`**: INDIRIZZATO. `test_blocks_failing_validation_are_dropped`: `profile_blocks` mockato con testo non valido; code OK, righe finte scartate, «profili non valutati» in righe e README, nessun `[profiles` nel toml.
- **M3 `test_default_root_is_the_plugin`**: INDIRIZZATO. Rinominato `test_real_default_root_is_the_plugin`; il mock su `fragments.load` (patch sull'attributo del modulo, e `init.py:285` chiama `fragments.load`) registra la radice e si asserisce `== [ROOT]`.
- **M4 albero `{}`**: INDIRIZZATO. `init.py:~611`: `sizes` vuoto va in `_not_evaluated("git non ha elencato nessun file di <rif>")`; `test_empty_tree_is_not_a_verdict_on_the_repo` asserisce la riga «profili non valutati» e l'assenza di «corrisponde ai suoi percorsi».
- **M5 frase di `skills/init/SKILL.md`**: INDIRIZZATO. Divisa in due frasi corrette, nessuna riga `- **<n>` aggiunta.

### Danni nuovi nel diff della correzione
Nessuno. Nota Minor non bloccante: nell'albero «push» il test non include i file di prova (`src/x/...`) che altri test spingono, ma quelli appartengono a frammenti finti, non ai veri. Un repo vuoto (`sizes == {}`) ora salta la valutazione anche con zero file legittimi: accettabile, il messaggio lo dice.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
