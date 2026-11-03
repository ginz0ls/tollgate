# Verifica delle fonti di `rules-ai` e dei marcatori (Task 6, Step 1)

Verificatore: Explore, sonnet, sola lettura, sulla skill del commit 21d8285. Uscita salvata dal controller. (Il verificatore ha creato per errore un file temporaneo fuori dal repo con una redirezione, copia ripulita di una pagina pubblica di Google; il controller lo ha controllato e rimosso.)

**Metodo.** Letti `skills/rules-ai/SKILL.md`, `templates/profiles/ai.toml`, `W/task-5-report.md`, `W/fonti/ai/FONTI.md` e `SHA256SUMS`, le copie in `W/fonti/ai/` (con `grep` e `sed -n`), la sezione 9 e la 3.4 del progetto di B e `skills/rules-base/SKILL.md` (R-BASE-03, 04, 06). `sha256sum -c SHA256SUMS` dentro `W/fonti/ai/`: 32 file, tutti `OK`. Le licenze in `FONTI.md` sono annotate per tutte le pagine (Google «CC BY 4.0», le altre «non dichiarata»), quindi il punto 4 vale per tutte le pagine ufficiali.

**Controllo di forma.** Nessuna regola contiene frasi copiate dalle pagine. Le regole sono in italiano, le fonti in inglese e le citazioni stanno solo in questo report.

## Tabella 1: regole e fonti

| Regola | Fonte (URL, sezione) | Citazione | Esito |
|---|---|---|---|
| R-AI-01 | progetto di B, sez. 9 | «il nome del modello sta in un solo punto del progetto, con l'indirizzo della pagina ufficiale e la data della verifica» | ok |
| R-AI-01 | platform.claude.com/docs/en/about-claude/models/model-ids-and-versions, «Dateless IDs are pinned snapshots» | «Every model ID, whether dated or dateless, has its own distinct deprecation and retirement schedule.» | ok |
| R-AI-02 | progetto di B, sez. 9 | stessa riga di R-AI-01 (indirizzo ufficiale e data della verifica) | ok |
| R-AI-02 | «Dove informarsi» della skill | rimando interno: la sezione esiste e elenca le pagine dei modelli di ogni fornitore. Non è una fonte esterna, nessun fatto da provare | ok |
| R-AI-02 | `rules-base`, R-BASE-04 | «ha in «Documentazione» l'indirizzo della pagina ufficiale dei modelli del fornitore» | ok |
| R-AI-03 | progetto di B, sez. 9 | ««il più recente della famiglia» è l'ultimo modello **stabile**»; «se ne usa uno più vecchio lo scrive con il motivo» | ok |
| R-AI-03 | Anthropic, api/models/list, campi `line` e `lifecycle` | «do not infer a line from the `id`»; «`active`: The model is available for use, open to new adopters, and not scheduled for retirement.» | ok |
| R-AI-03 | Anthropic, models/overview, «Compare models» | la sezione esiste; riga «Legacy models (still available): …» (nella copia è una riga di testo, non un titolo) | ok |
| R-AI-03 | Anthropic, model-deprecations, «Overview» e «Model status» | «**Active:** The model is fully supported and recommended for use.»; la tabella ha la colonna «Current state» | ok |
| R-AI-03 | Google, gemini-api/docs/models, «Model version name patterns» | «Stable: Points to a specific stable model.»; nella pagina i modelli portano l'etichetta «Stable» o «New Stable» | ok |
| R-AI-03 | OpenAI, api/docs/models | «Model ID gpt-6-astra», con linee Astra, Sol, Terra, Luna e nessuna etichetta di stabilità | ok |
| R-AI-03 | OpenAI, api/docs/deprecations, «Model deprecation notice periods» | «Preview models, identified by preview in the model name» | ok |
| R-AI-03 | OpenRouter, guides/overview/models.md, «Model Object Schema» | `id`: esempio «google/gemini-2.5-pro-preview»; `expiration_date`: «Deprecation date for the model endpoint (null if not deprecated)». «Non si sceglie» è un'inferenza della regola, non un testo della pagina | ok (con riserva) |
| R-AI-04 | progetto di B, sez. 9 | «Un modello in anteprima («preview», «experimental») si usa solo se il report lo dichiara con il motivo» | ok |
| R-AI-04 | Google, models, «Model version name patterns» | «will be deprecated with at least 2 weeks notice»; sperimentali: «typically not be suitable for production use» | ok |
| R-AI-04 | OpenAI, deprecations, «Model deprecation notice periods» | «may be retired with much shorter notice, such as 2 weeks … We don't recommend using preview models for business-critical production workloads» | ok |
| R-AI-05 | progetto di B, sez. 9 | «prima di cambiare modello legge le note di migrazione ufficiali, perché un modello nuovo può rifiutare parametri accettati dal precedente» | ok |
| R-AI-05 | Anthropic, about-claude/models/migration-guide | elenco di guide per modello (Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5) | ok |
| R-AI-05 | Anthropic, models/sonnet-5-5/migration-guide, «Send a request to Claude Sonnet 5.5» | «It leaves out five settings that return a 400 error» | ok |
| R-AI-05 | Anthropic, release-notes/overview | pagina di note di versione datate (ultima voce 30 ottobre 2026) | ok |
| R-AI-05 | Google, gemini-api/docs/changelog | pagina di note di versione («Released the …», date di spegnimento) | ok |
| R-AI-05 | Google, gemini-api/docs/deprecations | colonne «Shutdown date» e «Recommended replacement» | ok |
| R-AI-05 | OpenAI, api/docs/deprecations | colonna «Recommended replacement» | ok |
| R-AI-06 | progetto di B, sez. 3.4, riga `ai` | «Parametri e limiti delle API vengono dalla documentazione, non dalla memoria.» Non dice che l'indirizzo vada nel report | ok (per «dalla documentazione») |
| R-AI-06 | `rules-base`, R-BASE-04 («l'obbligo di citare l'indirizzo segue R-BASE-04») | R-BASE-04 riguarda solo il nome di un modello. Per limiti, prezzi e parametri l'indirizzo in «Documentazione» è chiesto da R-BASE-03 (pagina ufficiale per libreria o servizio) e da R-BASE-06 (indirizzi citati). Il rimando attribuisce a R-BASE-04 un obbligo che non contiene | **no** |
| R-AI-06 | Anthropic, models/overview, «Compare models» | righe «Pricing», «Context window», «Max output» (es. «1M tokens», «128K tokens») | ok |
| R-AI-06 | Anthropic, about-claude/pricing, «Model pricing» | «The following table shows pricing for all Claude models» | ok |
| R-AI-06 | Google, api/models | campi `inputTokenLimit` e `outputTokenLimit` | ok |
| R-AI-06 | Google, gemini-api/docs/pricing | «Paid Tier, per 1M tokens in USD / Input price» | ok |
| R-AI-06 | OpenAI, api/docs/models | «Input price … Max output 128K tokens … Context window 1.05M» | ok |
| R-AI-06 | OpenRouter, models | `context_length`: «Maximum context window size in tokens»; `pricing` | ok |
| R-AI-06 | Agno, models/overview | «Model capabilities vary by provider, API, and model ID.» | ok |
| R-AI-07 | progetto di B, sez. 9 | «il codice dà un errore chiaro quando un modello non è più disponibile». Il testo «nomina il modello e il punto della configurazione» ne è una precisazione | ok |
| R-AI-07 | Anthropic, model-deprecations, «Migrating to replacements» | «Requests to models past the retirement date will fail.» | ok |
| R-AI-07 | Anthropic, api/models/list, stato `retired` | «`retired`: The model is no longer available for use; inference requests naming it fail.» | ok |
| R-AI-07 | Google, deprecations, introduzione | «Once a model is "shutdown", it is completely turned off, and the endpoint is no longer available.» | ok |
| R-AI-07 | OpenAI, deprecations, «Deprecation vs. legacy» | «At the time of the shut down, the model or endpoint will no longer be accessible.» | ok |
| R-AI-08 | progetto di B, sez. 9 | «un alias che cambia da solo (per esempio i `*-latest` di Gemini) si usa solo se il report lo dichiara» | ok |
| R-AI-08 | Google, models, «Model version name patterns», voce Latest | «This alias will get hot-swapped with every new release … a 2-week notice will be provided» | ok |
| R-AI-08 | OpenRouter, quickstart.md | «`~openai/gpt-sol-latest`, a latest alias that always resolves to the newest model in the OpenAI GPT Sol family» | ok |
| R-AI-08 | Anthropic, model-ids-and-versions, «Before the 4.6 generation» | «shorter aliases … that point to the most recent dated snapshot for that minor version» | ok |
| R-AI-09 | Anthropic, mitigate-jailbreaks, «Indirect prompt injection», primo punto | «Put untrusted content only in tool results … inside `tool_result` blocks, never in `system` prompts or plain user `text` blocks.» | ok |
| R-AI-10 | Anthropic, mitigate-jailbreaks, «Indirect prompt injection» | «don't give Claude access to secrets it doesn't need, run tools in sandboxed environments, and scope permissions as narrowly as possible» | ok |
| R-AI-11 | Agno, models/overview, «Configure a Model» | tabella con `model="openai:gpt-5.4"` e `OpenAIResponses(id="gpt-5.4", ...)` | ok |
| R-AI-11 | Agno, anthropic/overview, «Model Selection» | «`Claude` defaults to `claude-sonnet-4-5-20250929`.» | ok |
| R-AI-11 | Anthropic, model-deprecations, «Model status» | «claude-sonnet-4-5-20250929 \| Deprecated \| September 30, 2026 \| November 30, 2026» | ok |

Nota su R-AI-11: i fatti delle fonti reggono. L'obbligo («passa l'ID in modo esplicito») non è in nessuna pagina. Lo deriva dalla scelta «l'ultimo modello, subito», come dichiara il report di Task 5, punto 3, e va confermato dall'utente.

## Tabella 2: marcatori

| Marcatore | Pagina | Citazione | Esito |
|---|---|---|---|
| `from anthropic import` | `anthropic-sdk-python.md` | «from anthropic import Anthropic» | ok |
| `import anthropic` | `anthropic-sdk-python.md` | «import anthropic» | ok |
| `@anthropic-ai/sdk` | `anthropic-sdk-typescript.md` | «import Anthropic, { toFile } from "@anthropic-ai/sdk";» e «import Anthropic from "npm:@anthropic-ai/sdk";» | ok |
| `api.anthropic.com` | `anthropic-api-models-list.md` | «curl https://api.anthropic.com/v1/models \» | ok |
| `from google import genai` | `agno-google.md` (pagina del framework Agno) | «from google import genai» | ok (nessuna copia di Google mostra l'import) |
| `@google/genai` | `google-gemini-libraries.html` | «Installation: npm install @google/genai» | ok con riserva: la copia mostra la riga di installazione, non una riga di import |
| `google.golang.org/genai` | `google-gemini-libraries.html` | «Installation: go get google.golang.org/genai» | ok con riserva: come sopra |
| `generativelanguage.googleapis.com` | `google-api-models-list.html` | «curl https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY» | ok |
| `from openai import` | `openai-sdk-python-readme.md` | «from openai import OpenAI» | ok |
| `import openai` | `openai-sdk-python-readme.md` | «import openai» (riga 689; l'esempio sulle eccezioni) | ok |
| `from 'openai'` | `openai-sdk-node-readme.md` | «import OpenAI from 'openai';» | ok |
| `from "openai"` | nessuna | la forma con virgolette doppie non compare in nessuna copia (lo ammette anche il report di Task 5) | **no**: non provato da una pagina |
| `npm:openai` | `openai-sdk-node-readme.md` | «import OpenAI from 'npm:openai';» | ok |
| `api.openai.com` | `openai-sdk-python-readme.md` | «audience="https://api.openai.com/v1"» | ok |
| `from openrouter import` | `openrouter-quickstart.md` | «from openrouter import OpenRouter» | ok |
| `@openrouter/sdk` | `openrouter-quickstart.md` | «import { OpenRouter } from '@openrouter/sdk';» | ok |
| `@openrouter/agent` | `openrouter-quickstart.md` | «import { OpenRouter, tool } from '@openrouter/agent';» | ok |
| `openrouter.ai/api/v1` | `openrouter-quickstart.md` | «url="https://openrouter.ai/api/v1/responses"» | ok |
| `from agno.agent import` | `agno-models-overview.md` | «from agno.agent import Agent» | ok |
| `from agno.models.` | `agno-models-overview.md` | «from agno.models.openai import OpenAIResponses» | ok |

Su tutti i marcatori: nessuno è il solo nome di un fornitore; nessuno è troppo generico (righe di import o host dell'API); nessuno è un pezzo di `@anthropic-ai/claude-code` (in `bin/tollgate_analysis/bash.py` quella stringa compare solo per il comando `claude`, e `@anthropic-ai/sdk` non vi compare).

## Riepilogo

- **Tabella 1:** 46 righe, 45 `ok` (1 con riserva), 1 `no`.
- **Tabella 2:** 20 righe, 19 `ok` (2 con riserva, 1 su una pagina del framework Agno), 1 `no`.
- **Regole senza nessuna fonte `ok`:** nessuna.
- **Regole con almeno una fonte `no`:** solo R-AI-06, per il rimando a R-BASE-04. Correzione minima: nella riga `Fonte:` di R-AI-06, sostituire «l'obbligo di citare l'indirizzo segue R-BASE-04» con «l'obbligo di citare l'indirizzo segue R-BASE-03 e R-BASE-06 della skill `rules-base`». In alternativa, dichiararlo obbligo nuovo di `rules-ai` da far approvare all'utente (la sez. 3.4 dice «dalla documentazione», non «con l'indirizzo nel report»).
- **Marcatori `no`:** `from "openai"` (nessuna pagina lo mostra): correzione minima toglierlo; `from 'openai'` resta e `import openai` copre gran parte dei casi.
- **Riserve non bloccanti:** `@google/genai` e `google.golang.org/genai` provati solo dalla riga di installazione; `from google import genai` provato solo dalla pagina di Agno; in R-AI-03 la parte OpenRouter «`expiration_date` valorizzata, non si sceglie» è un'inferenza da un campo che la pagina chiama «Deprecation date»; il rimando di R-AI-02 a «Dove informarsi» è interno alla skill.
