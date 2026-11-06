### Verdetti sui rilievi
1. **models_check importava modelsfetch in cima** — INDIRIZZATO. `bin/tollgate_flow/models_check.py:96` importa dentro `_check`, passato a `_provider_lines` (:66, :129); nessun import in cima (grep). Test del processo figlio `tests/test_models_check.py` (`test_importing_models_check_does_not_load_the_net_client`) eseguito: OK. I `mock.patch` su `tollgate_flow.modelsfetch.*` restano validi (risoluzione alla chiamata).
2. **`models._norm` privata usata da models_check** — INDIRIZZATO. `models.normalize` pubblica in `bin/tollgate_analysis/models.py:56`, usata in `models_check.py` (`_wanted`); test `NormalizeTest` (tests/test_models.py) eseguito: OK. `models.py` importa solo `re` e `dataclasses`: resta puro.
3. **Riga per fornitore riconosciuta dalla posizione** — INDIRIZZATO. `_provider_lines` filtra per forma (`modelli: <f>: ritiro|più nuovo non controllato:`, `_NOT_CHECKED`); le righe per modello non possono combaciare (il letterale non ha spazi). Test openai/openrouter eseguito: OK.
4. **providers_toml() leggeva templates/models.toml** — INDIRIZZATO. `tests/test_models_check.py` `providers_toml()` costruisce il file per intero da `HINTS/ENV/AUTH/PAGING`; nessuna lettura del template.

### Danni nuovi nel diff della correzione
Nessuno. (Minor trascurabile: `_wanted`/`_provider_lines` perdono le annotazioni di tipo di `Provider` per non importare `modelsfetch`; accettabile.)

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
