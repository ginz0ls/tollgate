# Task 5: bozza di rules-ai e frammento del profilo ai

(Report provvisorio: esito della suite e commit in fondo, aggiunti a corsa finita.)

## Cosa ho fatto
- `skills/rules-ai/SKILL.md`: 11 regole (R-AI-01..06 `[blocca]`, 07..11 no), senza `approved`, 83 righe. Ogni regola ha `Si giudica su: diff|report` e `Fonte:` con URL e sezione.
- `templates/profiles/ai.toml`: decisioni 2, 6, 9, 14; 20 marcatori.
- `tests/test_rules_ai.py` (con `rules()` a 5 elementi), `RealFragmentsTest` in `tests/test_fragments.py`, sezione `/tollgate:rules-ai` in `docs/uso/comandi.md`.

## Scostamenti dalla bozza (da giudicare nel Task 6)
1. **Bozza R-AI-08 (testo del modello come dato non fidato) non riportata.** La pagina di Anthropic sulla prompt injection parla del contenuto di terzi che ENTRA nel modello, non dell'USCITA del modello (eseguirla, metterla in HTML): nessuna fonte. Sostituita da R-AI-09 (contenuto di terzi in `tool_result`, solo API Anthropic) e R-AI-10 (privilegio minimo, solo Claude), entrambe non bloccanti. Nessuna fonte di OpenAI, Google, OpenRouter o Agno sull'argomento: nessuna regola per loro.
2. **R-AI-03 diviso**: R-AI-03 (ultimo stabile) e R-AI-04 (anteprima solo dichiarata). Id successivi scalati: migrazione R-AI-05, parametri/limiti/prezzi R-AI-06, errore R-AI-07, alias R-AI-08.
3. **R-AI-11 nuova** (Agno: `id` esplicito). Fatto da Agno (ID predefinito di `Claude` = `claude-sonnet-4-5-20250929`) più Anthropic (stato Deprecated, ritiro 2026-11-30). Obbligo derivato dalla scelta dell'utente sull'ultimo modello: da confermare.
4. **R-AI-06**: i valori per modello sono fatti delle pagine; l'obbligo di citare l'URL non è detto da nessuna pagina, rimanda a R-BASE-04.
5. **«Stabile» non definito da tutte le pagine**: Anthropic (`lifecycle: active`) e Gemini («Stable») sì; OpenAI e OpenRouter non etichettano. OpenAI: ID senza `preview` (la pagina delle deprecazioni dice che le anteprime lo portano nel nome) e non deprecato. OpenRouter: si rimanda al fornitore originale; `expiration_date` valorizzata = non si sceglie (inferenza dal campo «deprecation date»).
6. Esempi di Agno indietro rispetto ai fornitori (es. `gemini-3.5-flash`): lo dice «Dove informarsi».

## Tabella regola -> fonte
| Regola | Pagine (sezione) |
|---|---|
| R-AI-01 | progetto 9; Anthropic model-ids-and-versions («Dateless IDs are pinned snapshots», ultima frase) |
| R-AI-02 | progetto 9; R-BASE-04; pagine dei modelli di «Dove informarsi» |
| R-AI-03 | progetto 9; Anthropic api/models/list (`line`, `lifecycle`), models/overview («Compare models», «Legacy models»), model-deprecations («Overview», «Model status»); Google gemini-api/docs/models («Model version name patterns»); OpenAI api/docs/models + deprecations («Model deprecation notice periods»); OpenRouter models («Model Object Schema») |
| R-AI-04 | progetto 9; Google models («Model version name patterns»: Preview, Experimental); OpenAI deprecations («Model deprecation notice periods») |
| R-AI-05 | progetto 9; Anthropic migration-guide, sonnet-5-5/migration-guide («Send a request to Claude Sonnet 5.5»), release-notes; Google changelog + deprecations; OpenAI deprecations |
| R-AI-06 | Anthropic models/overview, pricing («Model pricing»); Google api/models (`inputTokenLimit`), pricing; OpenAI api/docs/models; OpenRouter models (`context_length`, `pricing`); Agno models/overview |
| R-AI-07 | progetto 9; Anthropic model-deprecations («Migrating to replacements»), models/list (`retired`); Google deprecations (intro); OpenAI deprecations («Deprecation vs. legacy») |
| R-AI-08 | progetto 9; Google models («Model version name patterns», Latest); OpenRouter quickstart (nota sugli alias latest); Anthropic model-ids («Before the 4.6 generation») |
| R-AI-09, R-AI-10 | Anthropic mitigate-jailbreaks («Indirect prompt injection», primo punto / punto sull'accesso minimo) |
| R-AI-11 | Agno models/overview («Configure a Model»), Agno anthropic («Model Selection»); Anthropic model-deprecations («Model status») |

## Marcatore -> pagina
| Marcatore | Pagina |
|---|---|
| `from anthropic import`, `import anthropic` | Anthropic SDK Python (copia `anthropic-sdk-python.md`, esempi) |
| `@anthropic-ai/sdk` (copre `npm:@anthropic-ai/sdk`) | Anthropic SDK TypeScript (import, e riga `npm:@anthropic-ai/sdk`) |
| `api.anthropic.com` | Anthropic api/models/list (esempio curl) |
| `from google import genai` | Agno Gemini («Context Caching») |
| `@google/genai`, `google.golang.org/genai` | Google gemini-api/docs/libraries («Language support and installation»: nome del pacchetto; la pagina non mostra la riga di import, il nome del pacchetto è lo specificatore) |
| `generativelanguage.googleapis.com` | Google api/models (URL di `models.list`) |
| `from openai import`, `import openai` | README SDK Python OpenAI (la seconda forma non è nel README: è la stessa libreria, `pip install openai` in developers.openai.com/api/docs/libraries) |
| `from 'openai'`, `npm:openai` | README SDK Node OpenAI (la variante con virgolette doppie `from "openai"` non è nella pagina: stesso specificatore) |
| `api.openai.com` | README SDK Python/Node OpenAI (`https://api.openai.com/v1`, `mtls.api.openai.com`) |
| `from openrouter import`, `@openrouter/sdk`, `@openrouter/agent`, `openrouter.ai/api/v1` | OpenRouter quickstart; Agno OpenRouter (base_url) |
| `from agno.agent import`, `from agno.models.` | Agno models/overview e pagine dei fornitori |

Note: nessuna pagina mostra `esm.sh` (Supabase mostra solo `npm:` e `jsr:`): nessun marcatore `esm.sh`; `@anthropic-ai/sdk` e `@openrouter/*` lo coprono per sottostringa, `esm.sh/openai` no. Nessun marcatore è pezzo di `@anthropic-ai/claude-code` (D11, verificato nel test). `api.anthropic.com` compare già in `statusline/statusline.sh` (non è file sorgente per `init`, non entra); nessun marcatore compare in `bin/`. Java/C# di Google omessi (la pagina dà groupId e pacchetto NuGet, non gli import).

## TDD
RED: `python3 -B -m unittest tests.test_rules_ai tests.test_fragments` -> `FAILED (failures=1, errors=19)` (file mancanti), uscita in `task-5-red.out`.
GREEN: `python3 -B -m unittest tests.test_rules_ai tests.test_fragments tests.test_docs tests.test_rules_base tests.test_skill_contract tests.test_manifest` -> 123 test OK; `tests.test_init.ProfileBlocksTest tests.test_init.ProfilesProposeTest tests.test_init.DetectTest` -> 56 OK.
`tests.test_init.ProfileBlocksTest.test_real_trees_light_no_profile`: ora ATTIVO, verde, non saltato (`ok`).
`claude plugin validate --strict .` -> uscita 0.

## Suite e commit
`PYTHONWARNINGS=error::ResourceWarning tests/run` (`task-5-suite.out`): python3.11 3347 test OK (skipped=2), python3.13 3347 test OK, uscita 0, nessun «unclosed». `test_real_trees_light_no_profile` verde e non saltato (verificato a parte, `ok`). Commit 0635303.

## Fix round 1
- R-AI-06 ristretta ai fatti del modello o del servizio (limiti, prezzo, parametri accettati o rifiutati, valori predefiniti); le scelte di configurazione del progetto restano fuori. Fonte aggiunta: «progetto di B, sezione 3.4, riga `ai`»; resta R-BASE-04 per l'indirizzo. Tabella: R-AI-06 -> + progetto di B 3.4 (riga `ai`).
- R-AI-08: il testo dice che l'alias è nel diff e che il report lo dichiara con il motivo (giudicata sul report).
- `ai.toml`: tolti i riferimenti a decisioni del piano e al Task 5; i commenti si capiscono da soli.
- Limiti noti dei marcatori: `require('openai')` (CommonJS) ed `esm.sh` non sono marcatori perché nessuna copia delle fonti li mostra.
