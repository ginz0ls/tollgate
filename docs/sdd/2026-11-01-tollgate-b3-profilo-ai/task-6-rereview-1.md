# Ri-revisione Task 6, giro di correzione 1 (dfc4835)

Diff: solo `docs/profili/ai.md`, `docs/profili/verifiche/ai-fonti.md`, `tests/test_rules_ai.py`. Skill e `ai.toml` non toccati; `approved` assente da `skills/rules-ai/SKILL.md` (grep: 0). Eseguito `python3 -B -m unittest tests.test_rules_ai`: 33 OK.

### Verdetti sui rilievi
1. **Colonna «Si giudica su»**: INDIRIZZATO. Colonna in `docs/profili/ai.md` (tabella «Le regole») con valori uguali alla skill; `test_page_judged_on_matches_skill` confronta per id.
2. **Test legati a `approved`**: INDIRIZZATO. `skip_if_approved` con `skipTest` e motivo; docstring espliciti in `test_page_is_a_proposal` e `test_page_brings_the_open_choices_to_the_user`.
3. **Intestazioni/filetti duplicati**: INDIRIZZATO. Righe doppie tolte in entrambe le tabelle di `ai-fonti.md` (diff); `test_tables_have_one_header` li vedrebbe (controlla filetto alla riga 2 e nessuna intestazione/filetto ripetuti).
4. **Riga `no` imposta / grassetto**: INDIRIZZATO. `assertTrue(no_rows)` sostituito da controllo per riga (ogni `no` riguarda una regola ancora coperta da `ok`); `**no**` diventato `no`; asserzione che nessun esito abbia `**`. I `no` restanti (R-BASE-04/03/06 di R-AI-06) sono fonti uscite; il marcatore `from "openai"` e' nella sezione «Regole tolte».
5. **R-AI-06 e R-AI-08 completi**: INDIRIZZATO. R-AI-06 dice che le scelte di configurazione (token, temperatura) restano fuori; R-AI-08 elenca `-latest` di Gemini, `~` e `-latest` di OpenRouter, alias senza data dei Claude precedenti alla 4.6. Coincidono con SKILL.md:36 e :46, regole invariate.
6. **«Quando si accende»**: INDIRIZZATO. Ora: propone solo dopo l'approvazione; «Prima della tua approvazione `init` non lo propone. Chi l'ha già copiato lo tiene finché non lo toglie.» Nessuna contraddizione. (`/tollgate:init --update` esiste in `skills/init/SKILL.md:4,26`.)
7. **Parole spiegate**: INDIRIZZATO. Elenco «Qualche parola, la prima volta che serve» in «Cosa sono» (API, ID del modello, alias, prompt injection, `tool_result`) prima della tabella dove compaiono.
8. **Aghi non generici**: INDIRIZZATO. Espressioni regolari su init+propone+«tu copi», «livello L1», «R-AI-01 ... solo diff», «il più recente» = ultimo modello stabile. Limite minore: la regex su R-AI-01 e' soddisfatta dal capoverso «Cosa sono» e non dalla riga della tabella (che dice «solo il diff»), ma entrambe le frasi esistono.
9. **Rimando autosufficiente**: INDIRIZZATO. La voce sulla bozza in `ai-fonti.md` ripete la motivazione senza rimandi al workspace.
10. **Ambito di R-AI-09/10**: INDIRIZZATO. In «Cosa sono»: «la 9 vale con l'API di Anthropic, la 10 con Claude»; tolta la sezione «Regole tolte» e l'affermazione sulle ricerche. Coerente con SKILL.md:50,54.

Coerenza pagina / skill / rapporto: confermata (id, Blocca?, Si giudica su, fonti `no`, marcatori).

### Danni nuovi nel diff della correzione
Nessuno Critical/Important. Minor: in «Quando si accende» la frase «Un progetto lo riceve solo quando lanci `/tollgate:init --update` e fai questa copia» e' leggermente ridondante con la precedente (init lo propone), ma non contraddittoria.

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
