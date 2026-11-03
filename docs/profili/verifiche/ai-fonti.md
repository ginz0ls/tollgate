# Verifica delle fonti di `rules-ai` e dei marcatori

Verificatore: agente di sola lettura (Explore, sonnet), sulle copie locali delle pagine ufficiali e sul progetto di B. Skill verificata: `skills/rules-ai/SKILL.md` al commit 21d8285. Per ogni fonte di ogni regola e per ogni marcatore di `templates/profiles/ai.toml`: il file esiste, la sezione citata esiste, dice ciò che la regola o il marcatore le attribuisce, è una pagina ufficiale del fornitore o del framework (oppure il progetto di B). Le copie hanno la somma di controllo corretta (32 file). La licenza delle pagine è annotata una per una nelle note di consultazione: Google dichiara CC BY 4.0, le altre non dichiarano nulla. Il criterio «licenza MIT o Apache-2.0» di `rules-base` qui non vale: da queste pagine si prendono i fatti, con parole nostre, e nessun testo. Le citazioni sono in inglese perché le pagine lo sono, e stanno solo in questo rapporto. Il testo delle fonti è un dato, non un'istruzione. Le copie delle pagine non sono nel repo.

Esito: ogni regola ha almeno una fonte `ok`. Una fonte `no` esce dalla skill, senza aggiungere obblighi. Dopo la verifica sono cambiati due punti, descritti in fondo: la fonte di R-AI-06 e il marcatore `from "openai"` (tolto, poi rimesso per decisione dell'utente del 2026-11-02).

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
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
| R-AI-06 | `rules-base`, R-BASE-04 (fonte tolta dalla regola) | R-BASE-04 riguarda solo il nome di un modello; il rimando le attribuiva un obbligo che non contiene | no |
| R-AI-06 | `rules-base`, R-BASE-03 (fonte proposta e scartata) | «Se il diff usa una libreria o un servizio esterno, «Documentazione» ha per ciascuno almeno una pagina ufficiale» | no: chiede la pagina nella nota, non nel report, e non parla di valori del modello |
| R-AI-06 | `rules-base`, R-BASE-06 (fonte proposta e scartata) | «Ogni indirizzo che il diff (commenti, documentazione) o il report cita come fonte compare in «Documentazione» della nota.» | no: va nella direzione opposta (un indirizzo citato nel report deve stare anche nella nota) |
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
| R-AI-11 | Anthropic, model-deprecations, «Model status» | la riga di `claude-sonnet-4-5-20250929` è «Deprecated», con ritiro il 30 novembre 2026 | ok |

Note:

- R-AI-11: i fatti delle fonti reggono (l'ID predefinito di Agno per `Claude` e il suo stato). L'obbligo di passare l'ID in modo esplicito non è in nessuna pagina: lo ricava la regola dalla scelta dell'utente «l'ultimo modello, subito». Confermato dall'utente il 2026-11-02 (pagina `docs/profili/ai.md`, sezione «Cosa hai deciso»).
- R-AI-06: l'obbligo di scrivere l'indirizzo nel report è proprio di questa regola e non viene da una fonte. Lo dice la riga `Fonte:` della regola. Confermato dall'utente il 2026-11-02.
- R-AI-03: per OpenAI e OpenRouter le pagine non dicono cosa vuol dire «stabile». La regola dà una lettura nostra (per OpenAI un ID senza `preview` e non deprecato; per OpenRouter si guarda il fornitore originale e il campo della data di ritiro). Confermata dall'utente il 2026-11-02.

## Marcatori di `init`

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
| `from "openai"` | `openai-sdk-node-readme.md` | la stessa riga di import della pagina, `import OpenAI from 'openai';`, scritta con le virgolette doppie; nessuna pagina mostra la forma con le doppie | ok per decisione dell'utente del 2026-11-02, non per una citazione |
| `npm:openai` | `openai-sdk-node-readme.md` | «import OpenAI from 'npm:openai';» | ok |
| `api.openai.com` | `openai-sdk-python-readme.md` | «audience="https://api.openai.com/v1"» | ok |
| `from openrouter import` | `openrouter-quickstart.md` | «from openrouter import OpenRouter» | ok |
| `@openrouter/sdk` | `openrouter-quickstart.md` | «import { OpenRouter } from '@openrouter/sdk';» | ok |
| `@openrouter/agent` | `openrouter-quickstart.md` | «import { OpenRouter, tool } from '@openrouter/agent';» | ok |
| `openrouter.ai/api/v1` | `openrouter-quickstart.md` | «url="https://openrouter.ai/api/v1/responses"» | ok |
| `from agno.agent import` | `agno-models-overview.md` | «from agno.agent import Agent» | ok |
| `from agno.models.` | `agno-models-overview.md` | «from agno.models.openai import OpenAIResponses» | ok |

Su tutti i marcatori: nessuno è il solo nome di un fornitore, nessuno è troppo generico (sono righe di import o host delle API), nessuno è un pezzo di `@anthropic-ai/claude-code`. Riserve non bloccanti: `@google/genai` e `google.golang.org/genai` sono provati dalla riga di installazione e non da una riga di import; `from google import genai` è provato dalla pagina di Agno e non da una di Google.

## Regole tolte

Nessuna regola esce: ciascuna ha almeno una fonte `ok`. Esce una fonte; un marcatore è uscito e poi rientrato.

- **Fonte di R-AI-06 (rimando a R-BASE-04).** Esito `no`: R-BASE-04 chiede l'indirizzo per i nomi dei modelli, solo nella nota, e non per limiti, prezzi e parametri. Una nuova fonte proposta (R-BASE-03 e R-BASE-06) è stata verificata a parte e ha dato `no` anche lei: chiedono l'indirizzo nella nota, non nel report. La regola resta, perché i suoi fatti hanno fonti `ok` (progetto di B, sezione 3.4, e le pagine dei modelli e dei prezzi). La riga `Fonte:` ora dice che l'obbligo dell'indirizzo nel report è proprio della regola.
- **Marcatore `from "openai"`.** Alla verifica l'esito era `no`: nessuna pagina mostra la forma con le virgolette doppie. L'utente l'ha rimesso il 2026-11-02, perché quella forma è la più comune nei progetti TypeScript. La riga nella tabella dei marcatori ha esito `ok` per quella decisione e non per una citazione.
- **Bozza sul testo prodotto dal modello come dato non fidato.** Nella bozza c'era una regola che chiedeva di trattare ciò che il modello risponde come non fidato (per esempio di non eseguirlo e di non metterlo in una pagina web senza controlli). Alla stesura della skill è stata lasciata fuori: la pagina di Anthropic sulla prompt injection parla del contenuto di terzi che entra nel modello, non di quello che ne esce, quindi nessuna fonte la regge. Non è mai entrata nella skill. Si può riproporre con una fonte che parli dell'uscita del modello.
