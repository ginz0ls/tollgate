# tollgate: catalogo dei profili verticali

Data: 8 ottobre 2026. Stato: **bozza: le regole `rules-<area>` vanno scritte e riviste dall'utente**.
Spec del nucleo: `2026-10-08-tollgate-nucleo-design.md` (revisione 20, sezioni 6.3, 8.6, 8.7, 10 e 11.4; aggiornamenti di B3 alla revisione 29: `ai` è il primo profilo costruito, vedi le sezioni 1, 2, 2.1, 2.2 e 4; aggiornamenti di B4 alla revisione 31: `infra` è il secondo, vedi le sezioni 2, 2.1, 2.2, 2.3, 4 e 6). Il nucleo dà il contratto e l'instradamento; questo documento dice **quali profili** esistono e cosa porta ciascuno. Li realizza il sotto-progetto B.

Fonti: tre ricerche dell'8 ottobre 2026 (catalogo di 1.015 skill e 644 agenti su disco, ricerca web per area e ruolo, raccolte esistenti di subagenti). I riassunti sono nella sezione 7.

---

## 1. Principi

1. **Due tipi di profilo.**
   - **Verticale**: un'area di codice riconoscibile dai percorsi. Ha implementatore e revisore del task propri. I percorsi dei profili verticali **non si sovrappongono**: un file appartiene al massimo a un profilo verticale, altrimenti l'instradamento di `task start` diventerebbe ambiguo. Se un file corrisponde a più profili verticali vince il pattern più specifico (più segmenti letterali), a parità il primo dichiarato (decisione dell'utente).
   - **Trasversale**: una qualità che attraversa le aree (accessibilità, performance). Non ha agenti: aggiunge regole e skill al revisore dei profili verticali che lo dichiarano.
2. **Regole nostre prima, skill esterne poi.** Ogni profilo ha una skill di regole scritta da noi, `tollgate:rules-<area>`, che sta nel plugin e quindi c'è su ogni macchina. Le skill esterne sono un rinforzo: se mancano, il lavoro procede con le sole regole.
3. **Stesse regole per chi scrive e per chi rivede.** Implementatore e revisore dello stesso profilo caricano la stessa `rules-<area>`: il primo la applica, il secondo la verifica regola per regola e cita l'identificativo nel rilievo (`R-FE-07`).
4. **Regole curate, non generate.** SkillsBench (arXiv 2602.12670, preprint letto solo nell'abstract) misura +16 punti con skill curate e −1,3 con skill scritte dal modello da solo; le skill corte e mirate battono la documentazione completa. Quindi ogni regola è **distillata da una fonte citata** e **rivista dall'utente** prima di entrare nel plugin. Una regola senza fonte e senza revisione non entra.
5. **Regole verificabili.** Una regola ha la forma «ogni pulsante con sola icona ha `aria-label`», non «cura l'accessibilità». Il revisore deve poter rispondere sì o no.
6. **Al massimo 3 skill obbligatorie per agente** (spec 6.3). `rules-<area>` conta nel tetto se sta nel campo `skills` del profilo, cioè nel brief. **Scelta di B3 per `ai`**: `rules-ai` la precarica l'agente (`skills: [rules-base, rules-ai]` nel frontmatter di `implementer-ai` e `reviewer-ai`), quindi non è nel frammento, non è nel brief, non conta nel tetto e non passa dal controllo di `SubagentStop`; il frammento ha `skills = []` e `reviewer_skills = []`. Le skill esterne consigliate (come `claude-api`) non vanno nel frammento: la regola di area le nomina in «Dove informarsi». Le skill comuni (sotto) non contano. La scelta vale come modello per B4-B7, salvo diversa decisione nel piano della fetta; B4 l'ha applicata a `infra` (`implementer-infra` e `reviewer-infra` con `skills: [rules-base, rules-infra]`).
7. **Licenze.** Si distillano regole solo da fonti MIT o Apache-2.0, citandole. **Le pagine ufficiali dei fornitori (documentazione, elenchi dei modelli, deprecazioni, prezzi) non hanno licenza aperta: sono fonte di fatti, che si riscrivono con parole nostre.** Il loro testo non si copia nelle regole; una citazione sta al più in una riga, solo nel rapporto delle fonti; le copie locali su cui lavora il verificatore non entrano mai nel repo, che è pubblico (B3). Da fonti CC-BY-SA (Trail of Bits, OWASP) o senza licenza (alcune skill Vercel) si prendono **idee**, scritte con parole nostre, oppure si consiglia la skill all'utente senza ridistribuirla.

**Skill comuni, fuori dal tetto.**
- Ogni implementatore: `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `superpowers:verification-before-completion`.
- Ogni revisore: `agent-skills:code-review-and-quality`.
- Ogni implementatore e ogni revisore di codice, generici e per area: `rules-base` (B2), la skill di regole del profilo `base`, nostra e approvata dall'utente. Non si chiede nel brief: la precaricano gli agenti con `skills: [rules-base]` nel frontmatter (spec del nucleo 6.3, rev 28), quindi non conta nel tetto di 3 né in `skills_required`.

---

## 2. Profili verticali

Percorsi predefiniti: sono i pattern dei frammenti di profilo (`templates/profiles/<area>.toml`, spec 11.4). `init` non li copia così come sono: propone **percorsi concreti** del progetto, ricavati dai file veri del repo (per `**/ai/**` e un repo con `src/ai/`, `src/ai/**`; per una cartella alla radice, `/ai/**`), senza contare `.claude/`, la copia di tollgate in `.github/tollgate/` e la cartella della proposta, e li aggiunge in coda a `tollgate.toml` per l'utente. Dove un'area ha codice fuori dalle cartelle tipiche, `init` lo trova anche **per contenuto**: il frammento ha una lista `[detect] content` di righe di import o di chiamata (il pacchetto dell'SDK come compare nell'import, l'host dell'API), che si cercano con `git grep` nei file sorgente non di test, e ogni file trovato entra con il suo percorso esatto. Per `ai` i marcatori coprono Anthropic, Google (Gemini), OpenAI, OpenRouter e Agno. L'utente adatta tutto al progetto. Un frammento ammette **tre forme** di pattern (B4, spec 11.4): `**/<cartella>/**` (la cartella a qualunque profondità), `<cartella>/**` (la sola cartella alla radice) e `**/<nome>` (un file con quel nome, a qualunque profondità, con al più un `*` finale: `Dockerfile*`). Per un file `init` propone il **percorso esatto** (`/vercel.json`, `services/api/Dockerfile.prod`); i documenti (`md`, `mdx`, `markdown`, `rst`, `txt`, `adoc`) non accendono un profilo per cartella, e `.github/workflows/` e `.github/actions/` non ne accendono nessuno.

**Nota per B4 e B6: le graffe.** `globs` (il dialetto di `.gitignore`, spec 3.2) **non espande** `{a,b}`: `**/*.{tsx,jsx}` non corrisponde a niente. I percorsi di questa tabella che le usano (`frontend`, `3d`) vanno scritti in più righe, uno per estensione o nome, e la loro forma nel frammento la decide il piano della fetta che li costruisce. `infra` (B4) le ha sciolte così: `wrangler.{toml,jsonc}` è diventato `**/wrangler.toml`, `**/wrangler.json` e `**/wrangler.jsonc` (Wrangler legge anche il JSON), e `Dockerfile*` è `**/Dockerfile*`. Nomi degli agenti: `tollgate:implementer-<area>`, `tollgate:reviewer-<area>`, `tollgate:final-<area>`.

| Profilo | Percorsi predefiniti | Livello minimo | Specialista finale (L2) |
|---|---|---|---|
| `frontend` | `**/*.{tsx,jsx,vue,svelte,css,scss}`, `**/components/**`, `**/app/**/page.*`, `web/**` | L0 | no |
| `backend` | `api/**`, `server/**`, `**/routes/**`, `**/handlers/**`, `**/services/**` | L0 | no |
| `database` | `**/migrations/**`, `supabase/**`, `**/*.sql`, `prisma/**`, `**/schema.*` | **L2** | **sì** |
| `security` | `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**` | **L2** | **sì** |
| `infra` | `infra/**`, `**/vercel.json`, `**/vercel.toml`, `**/vercel.ts`, `**/wrangler.toml`, `**/wrangler.json`, `**/wrangler.jsonc`, `**/Dockerfile*`, `**/.dockerignore`, `**/compose.yaml`, `**/compose.yml`, `**/compose.override.yaml`, `**/docker-compose.yaml`, `**/docker-compose.yml` (B4: 14 pattern, ognuno con una pagina ufficiale; fuori `workers/**`, che è `backend`, `**/*.tf` e `.github/workflows/**`) | L1 | no |
| `ai` | `**/llm/**`, `**/prompts/**`, `**/agents/**`, `**/ai/**` | L1 | no |
| `3d` | `**/three/**`, `**/scene*/**`, `**/*.{glsl,frag,vert}`, `**/*.glb` | L0 | no |
| `e2e` | `e2e/**`, `**/playwright.config.*`, `tests/e2e/**` | L1 | no |
| `copy` | `**/locales/**`, `**/i18n/**`, `**/messages/**`, `content/**` | L0 | no |
| `docs` | `docs/**` (escluso `docs/superpowers/**`), `README*`, `**/*.mdx` | L0 | no |
| `ci` | `.github/workflows/**` (esclusi `tollgate-*`), `.gitlab-ci.yml`, `scripts/ci/**` | **L2** | sì, `final-security` |
| `mobile` | `ios/**`, `android/**`, `capacitor.config.*` | L1 | no |
| `analytics` | `**/analytics/**`, `**/tracking/**` | L1 | no |
| *(generico)* | tutto il resto | — | — |

### 2.1 Agenti e skill

Colonna «Skill»: le 3 obbligatorie, la prima sempre la nostra. In corsivo le esterne **consigliate** (rinforzo, non obbligatorie).

| Profilo | Implementatore: skill | Revisore del task: skill | Specialista finale |
|---|---|---|---|
| `frontend` | `rules-frontend`, `frontend-design:frontend-design`, `ui-ux-pro-max` · *design-taste-frontend (taste-skill v1)* | `rules-frontend`, `rules-a11y`, `ui-ux-pro-max` · *anti-ui-slop (audit)* | — |
| `backend` | `rules-backend`, `agent-skills:api-and-interface-design`, `agent-skills:observability-and-instrumentation` | `rules-backend`, `agent-skills:api-and-interface-design`, `rules-performance` | — |
| `database` | `rules-database`, `postgres-best-practices:supabase-postgres-best-practices`, `agent-skills:deprecation-and-migration` · *supabase:supabase* | `rules-database`, `postgres-best-practices:supabase-postgres-best-practices` | `final-database`: `rules-database`, migrazioni reversibili, RLS, indici, dati esistenti |
| `security` | `rules-security`, `agent-skills:security-and-hardening` | `rules-security`, `agent-skills:security-and-hardening`, `security-review` · *differential-review, insecure-defaults (Trail of Bits)* | `final-security`: `rules-security`, revisione del diff per rischio e raggio d'azione |
| `infra` | `rules-infra` (precaricata dall'agente, B4: nessuna skill nel frammento), *`wrangler`* e *`cloudflare`* (nominate in «Dove informarsi» di `rules-infra`); `workers-best-practices` riguarda il codice dei Worker, che è `backend` | `rules-infra` (precaricata dall'agente) | — |
| `ai` | `rules-ai` (precaricata dall'agente, B3: nessuna skill nel frammento), *`claude-api`* (nominata in «Dove informarsi» di `rules-ai`) | `rules-ai` (precaricata dall'agente), *`claude-api`* (come a sinistra) | — |
| `3d` | `rules-3d`, `threejs-skills:threejs-fundamentals`, `threejs-game-skills:SKILL_08_Performance_Monitoring` | `rules-3d`, `threejs-game-skills:SKILL_08_Performance_Monitoring` | — |
| `e2e` | `rules-e2e`, `agent-skills:browser-testing-with-devtools` · *webapp-testing, playwright-cli* | `rules-e2e` | — |
| `copy` | `rules-copy`, `humanizer`, `copy-editing` | `rules-copy`, `humanizer` | — |
| `docs` | `rules-docs`, `agent-skills:documentation-and-adrs`, `humanizer` | `rules-docs`, `humanizer` | — |
| `ci` | `rules-ci`, `agent-skills:ci-cd-and-automation` | `rules-ci`, `rules-security` | `final-security` (stesso agente di `security`) |
| `mobile` | `rules-mobile` | `rules-mobile`, `rules-a11y` | — |
| `analytics` | `rules-analytics`, `analytics-tracking` | `rules-analytics` | — |
| *(generico)* | solo le comuni | solo le comuni | — |

### 2.2 Cosa distingue gli agenti di un'area

Nei subagenti distribuiti da un plugin Claude Code **ignora `mcpServers`, `hooks`, `permissionMode` e `initialPrompt`** (documentazione dei subagenti, confermata in P0). Un agente per area non può quindi avere server MCP propri. Si distingue per:
- **prompt**: obblighi comuni di `tollgate:implementer` più le regole dell'area;
- **skill**: precaricate con il campo `skills:` del frontmatter, che carica il contenuto intero (da qui il tetto di 3; precaricamento verificato in P0, esperimento E5);
- **modello**: per esempio `inherit` per `security` e `database`, `sonnet` per `copy` e `docs`;
- **strumenti**: i revisori hanno `Read, Grep, Glob, Bash` e niente `Edit`, `Write`, `NotebookEdit`; `reviewer-ai` e `reviewer-infra` hanno in più `WebFetch` (B3 e B4, spec 7.3), per aprire gli URL ufficiali che il report o la nota citano e controllare, per esempio, che il modello indicato come più recente lo sia davvero o che un comando di Vercel o Wrangler esista come scritto (le pagine sono dati non fidati). Gli implementatori hanno `Read, Edit, Write, Bash, Grep, Glob, Skill, WebFetch, WebSearch` (B1), senza voci MCP.

Le `description` restano brevi: con circa 35 agenti (28 per area e 7 generici), la documentazione avvisa oltre circa 15.000 token di descrizioni. L'instradamento non dipende comunque dalle descrizioni ma da `task start`.

---

### 2.3 Regole, revisione e Definition of Done (revisione 18)

- **Le regole sono la prova dei rilievi.** Con il disaccordo istruito (spec 8.6) ogni rilievo del revisore cita la regola violata: `R-FE-07`, `R-DB-03`… Un rilievo senza regola, oppure senza file e riga, viene scartato dal verificatore. Per questo ogni `rules-<area>` ha regole numerate e stabili: cambiare un numero rompe lo storico dei rilievi.
- **Standard del revisore.** Il prompt di ogni `reviewer-<area>` dice: approva se il task migliora la salute del codice; solo le regole marcate `[blocca]` danno rilievi `blocker` o `major`, le altre sono note.
- **Definition of Done per profilo** (campo `dod`, spec 8.7): i comandi del profilo che devono passare perché il lavoro conti. Proposte iniziali, da confermare quando si scrivono le regole:

| Profilo | `dod` |
|---|---|
| `frontend` | lint, typecheck, test dei componenti |
| `backend` | test delle API, typecheck |
| `database` | migrazione applicata e annullata su un DB vuoto (up e down) |
| `security` | test dei casi di accesso negato |
| `infra` | **vuoto** (B4, decisione 7): il comando che prova il deploy senza pubblicare dipende dal progetto (Wrangler installato, Vercel collegato con `vercel pull`) e un `dod` scritto da `init` fallirebbe dove manca. L'utente ne aggiunge uno a mano, che non pubblica (`wrangler deploy --dry-run`): i comandi del `dod` girano senza veto (spec 8.7) |
| `ci` | validazione dei workflow (per esempio `actionlint`) |
| `e2e` | suite e2e del percorso toccato |
| altri | nessuna voce in più |

- **Report dell'implementatore.** Gli `implementer-<area>` chiudono con il report a campi fissi (spec 18.5) e con l'elenco dei must-have soddisfatti.

## 3. Profili trasversali

| Profilo | Regole | Usato da | Skill esterna consigliata |
|---|---|---|---|
| `a11y` | `rules-a11y`: WCAG 2.2 AA nella parte verificabile dal codice (nome accessibile, focus visibile, ruoli semantici, contrasto dichiarato nei token, `aria-live` per i messaggi) | revisori `frontend` e `mobile` | *wcag-audit-patterns (wshobson, MIT)* |
| `performance` | `rules-performance`: query N+1, paginazione, cache, dimensioni del bundle, immagini, LCP/INP nella parte verificabile dal codice | revisori `backend` e `frontend` (tramite `rules-frontend`) | `web-perf`, `agent-skills:performance-optimization` |

---

## 4. Le regole: fonti e forma

**Forma di `rules-<area>`** (`skills/rules-<area>/SKILL.md`, al massimo circa 150 righe):

```markdown
---
name: rules-frontend
description: Regole di tollgate per il codice frontend. Usala sempre sui task del profilo frontend.
---
# Regole frontend (versione 1)

## Struttura
R-FE-01 [blocca] Ogni componente gestisce i quattro stati: caricamento, vuoto, errore, pieno.
R-FE-02 …

## Gusto e anti slop
R-FE-20 Nessun gradiente viola su bianco, nessun font predefinito di sistema come scelta di design.
…

Fonti: frontend-design (Anthropic, Apache-2.0), frontend-ui-engineering (Addy Osmani, MIT), …
```

**Fonti da distillare per area** (licenza verificata dove indicato):

| Regole | Fonti principali |
|---|---|
| `rules-frontend` | `frontend-design` di Anthropic (Apache-2.0: elenco dei «tell» e cluster di tratti AI), `frontend-ui-engineering` di addy (MIT: tabella «Avoid the AI Aesthetic»), `ui-ux-pro-max` (MIT: anti-pattern e Do/Don't), `taste-skill` (MIT: anti-ripetizione, pre-flight), `anti-ui-slop` (Apache-2.0: stati mancanti, controlli inerti, colori scritti a mano, finish gate). Idee, non testo: Vercel web-interface-guidelines (senza licenza) |
| `rules-a11y` | `frontend-ui-engineering` (MIT, sezione WCAG), WCAG 2.2 (W3C, si cita la norma) |
| `rules-backend` | `api-and-interface-design` (MIT), prompt dei revisori di everything-claude-code (MIT) |
| `rules-database` | `supabase-postgres-best-practices` (MIT), `database-reviewer` di everything-claude-code (MIT), `deprecation-and-migration` (MIT) |
| `rules-security` | `security-and-hardening` (MIT), `security-auditor` di addy (MIT). Idee: Trail of Bits `insecure-defaults` e `differential-review` (CC-BY-SA), OWASP ASVS (CC-BY-SA) |
| `rules-infra` (B4, approvata il 2026-11-07) | Le pagine ufficiali di Vercel (configurazione, collegamento del progetto, build in locale, variabili), Cloudflare (configurazione e comandi di Wrangler, segreti, date di compatibilità) e Docker (Dockerfile, contesto, buone pratiche, segreti di build, Compose), copie locali consultate il 2026-11-06, riscritte con parole nostre; la skill `wrangler` del repository delle skill di Cloudflare (Apache-2.0) per l'idea di leggere la documentazione della versione installata; più le scelte dell'utente nel progetto di B (sezioni 3.4 e 11) e la spec del nucleo 8.5 per gli effetti esterni. Il rapporto per regola e per pattern è `docs/profili/verifiche/infra-fonti.md` |
| `rules-ai` (B3, approvata il 2026-11-02) | Le pagine ufficiali dei fornitori, copie locali consultate il 2026-11-01, riscritte con parole nostre: Anthropic (modelli, deprecazioni, migrazione, elenco dei modelli, prezzi, guida alla prompt injection, SDK), Google/Gemini (modelli, deprecazioni, elenco dei modelli, novità, prezzi, SDK), OpenAI (modelli, deprecazioni, SDK), OpenRouter (modelli, API), Agno (modelli e import) e, per le forme `npm:` delle edge function, Supabase; più le scelte dell'utente nel progetto di B, sezione 9 (modelli stabili, nome del modello in un solo punto con indirizzo e data). `claude-api` non è una fonte: `rules-ai` la nomina per chi usa l'SDK di Anthropic. Il rapporto per regola e per marcatore è `docs/profili/verifiche/ai-fonti.md` |
| `rules-3d` | `threejs-skills`, `threejs-game-skills` (licenza da verificare) |
| `rules-e2e` | `browser-testing-with-devtools` (MIT), `webapp-testing` (Apache-2.0) |
| `rules-copy`, `rules-docs` | `humanizer` (licenza da verificare), `documentation-and-adrs` (MIT). Idee: Vercel writing-guidelines (senza licenza) |
| `rules-mobile`, `rules-analytics` | Da scrivere quasi da zero: nessuna fonte adatta trovata. Si scrivono solo quando un progetto reale le usa |
| `rules-performance` | `performance-optimization` (MIT), `web-perf` (Cloudflare, Apache-2.0) |
| `rules-base` (B2, approvata il 2026-11-01) | `agent-skills` 0.6.9 (Addy Osmani, MIT: `source-driven-development`, `context-engineering`) e `superpowers` 7.0.0 (Jesse Vincent, MIT: `verification-before-completion`), più le correzioni dell'utente raccolte nel progetto di B (sezioni 1 e 3.6: nomi dei modelli, «non esiste», fonti non aperte). Le fonti sono copie locali; il rapporto per regola è `docs/profili/verifiche/base-fonti.md` |
| `rules-ci` | `ci-cd-and-automation` (MIT), `gha-security-review` di getsentry (Apache-2.0, da leggere). Idee: Trail of Bits `agentic-actions-auditor` (CC-BY-SA). Regole minime: `permissions` esplicito e minimo, azioni fissate a uno SHA, nessun segreto in `pull_request` da fork, nessun `pull_request_target` con checkout del codice della PR |

**Forma reale (B2).** Il frontmatter ha anche `version: 1` e, dopo l'approvazione, `approved: <AAAA-MM-GG>`: la data è l'interruttore del blocco (spec del nucleo 8.1). Ogni regola ha sotto la riga `Fonte:` e il rapporto della verifica delle fonti dice, regola per regola, se la fonte regge. La pagina per l'utente è `docs/profili/<area>.md`.

**Nota per B4-B7: il prefisso delle regole.** `research.area_rules` riconosce `R-<AREA>-NN` con il nome dell'area **in maiuscolo**, quello del file `rules-<area>`: `R-AI-`, `R-BASE-`, e quindi `R-FRONTEND-`, `R-BACKEND-`, `R-DATABASE-`, `R-INFRA-`, non le sigle brevi di questo catalogo (`R-FE-`, `R-DB-`). O la skill usa il prefisso lungo, o `area_rules` cambia. Gli esempi `R-FE-07` e `R-DB-03` sopra sono illustrativi.

**Processo per ogni `rules-<area>`.** Bozza distillata dalle fonti, con la fonte di ogni regola → revisione dell'utente → versione 1 nel plugin. Le regole cambiano con una PR, come il resto del plugin.

---

## 5. Problemi aperti emersi scrivendo il catalogo

1. ~~I workflow del progetto erano file protetti.~~ **Risolto (spec rev 17):** protetti solo i workflow `tollgate-*`; gli altri sono il profilo `ci` (L2), e `guard` rifiuta i workflow che potrebbero pubblicare stati falsi.
2. ~~Sovrapposizioni tra profili verticali.~~ **Risolto (spec rev 17):** vince il pattern più specifico.
3. ~~`mcpServers` ignorato nei subagenti di plugin.~~ **Risolto (P0, spec rev 20):** confermato dalla documentazione, insieme a `hooks`, `permissionMode` e `initialPrompt`; `skills:` precarica davvero (E5).
4. **Profili per progetti non web** (Python di dati, CLI, librerie) non sono coperti: cadono nel generico. Si aggiungono quando servono.

---

## 6. Cosa cambia nella spec del nucleo

B4 (revisione 31): tre forme di pattern nei frammenti, percorsi esatti per i file, documenti e cartelle di GitHub che non accendono un profilo, agenti `-infra` con `tollgate:reviewer-infra` tra i tipi di sola lettura (6.3, 7.1, 7.3, 11.2, 11.4), comandi di servizio dietro `npx` e simili e voci nuove di Wrangler e Docker tra gli effetti esterni (8.5), comandi del `dod` senza veto (8.7).

B3 (revisione 29): agenti per area con `rules-<area>` precaricata (6.3), `tollgate:reviewer-ai` tra i tipi di sola lettura con `WebFetch` (7.1, 7.3), `init` che propone i profili approvati con percorsi concreti e rilevamento per contenuto (11.2), frammenti di profilo e calcolo di `rules` e `blocking_rules` dalla skill (11.4).

Applicato nelle revisioni 17 e 18 (campo `dod`, regole come prova dei rilievi): campi `kind` e `cross` (11.4), precedenza per specificità (6.3), file di tollgate ristretti e controllo dei workflow in `guard` (0, 9.2), verifica di `skills:` e `mcpServers` (16, e P0 esperimento E5).

---

## 7. Fonti delle ricerche

- **Raccolte esistenti**: nessuna fa il disegno completo (coppia implementatore e revisore per area, skill per agente, instradamento per file). Riutilizzabili con attribuzione: prompt di everything-claude-code, addy, VoltAgent (MIT); convenzione degli strumenti di VoltAgent; punteggi per glob di `claude-code-showcase` (MIT). https://github.com/VoltAgent/awesome-claude-code-subagents, https://github.com/wshobson/agents, https://github.com/ChrisWiles/claude-code-showcase
- **Gusto e anti slop**: https://github.com/Leonxlnx/taste-skill (MIT; v2 sperimentale, usare la v1 fissata a un commit), https://github.com/uizze/uizze (`anti-ui-slop`, Apache-2.0, poca adozione).
- **Sicurezza**: https://github.com/trailofbits/skills (CC-BY-SA-4.0).
- **Database**: https://github.com/supabase/agent-skills (MIT).
- **Test**: https://github.com/anthropics/skills (`webapp-testing`, Apache-2.0), https://github.com/microsoft/playwright-cli (Apache-2.0).
- **Efficacia delle skill**: https://arxiv.org/abs/2602.12670 (SkillsBench), https://arxiv.org/pdf/2604.04323 (benefici più fragili in condizioni realistiche).
- **Documentazione dei subagenti**: https://code.claude.com/docs/en/sub-agents
