# tollgate: catalogo dei profili verticali

Data: 8 ottobre 2026. Stato: **bozza: le regole `rules-<area>` vanno scritte e riviste dall'utente**.
Spec del nucleo: `2026-10-08-tollgate-nucleo-design.md` (revisione 18, sezioni 6.3, 8.6, 8.7, 10 e 11.4). Il nucleo dà il contratto e l'instradamento; questo documento dice **quali profili** esistono e cosa porta ciascuno. Li realizza il sotto-progetto B.

Fonti: tre ricerche dell'8 ottobre 2026 (catalogo di 1.015 skill e 644 agenti su disco, ricerca web per area e ruolo, raccolte esistenti di subagenti). I riassunti sono nella sezione 7.

---

## 1. Principi

1. **Due tipi di profilo.**
   - **Verticale**: un'area di codice riconoscibile dai percorsi. Ha implementatore e revisore del task propri. I percorsi dei profili verticali **non si sovrappongono**: un file appartiene al massimo a un profilo verticale, altrimenti l'instradamento di `task start` diventerebbe ambiguo. Se un file corrisponde a più profili verticali vince il pattern più specifico (più segmenti letterali), a parità il primo dichiarato (decisione dell'utente).
   - **Trasversale**: una qualità che attraversa le aree (accessibilità, performance). Non ha agenti: aggiunge regole e skill al revisore dei profili verticali che lo dichiarano.
2. **Regole nostre prima, skill esterne poi.** Ogni profilo ha una skill di regole scritta da noi, `tollgate:rules-<area>`, che sta nel plugin e quindi c'è su ogni macchina. Le skill esterne sono un rinforzo: se mancano, il lavoro procede con le sole regole.
3. **Stesse regole per chi scrive e per chi rivede.** Implementatore e revisore dello stesso profilo caricano la stessa `rules-<area>`: il primo la applica, il secondo la verifica regola per regola e cita l'identificativo nel rilievo (`R-FE-07`).
4. **Regole curate, non generate.** SkillsBench (arXiv 2602.12670) misura +16 punti con skill curate e −1,3 con skill scritte dal modello da solo; le skill corte e mirate battono la documentazione completa. Quindi ogni regola è **distillata da una fonte citata** e **rivista dall'utente** prima di entrare nel plugin. Una regola senza fonte e senza revisione non entra.
5. **Regole verificabili.** Una regola ha la forma «ogni pulsante con sola icona ha `aria-label`», non «cura l'accessibilità». Il revisore deve poter rispondere sì o no.
6. **Al massimo 3 skill obbligatorie per agente** (spec 6.3), compresa `rules-<area>`. Le skill comuni (sotto) non contano.
7. **Licenze.** Si distillano regole solo da fonti MIT o Apache-2.0, citandole. Da fonti CC-BY-SA (Trail of Bits, OWASP) o senza licenza (alcune skill Vercel) si prendono **idee**, scritte con parole nostre, oppure si consiglia la skill all'utente senza ridistribuirla.

**Skill comuni, fuori dal tetto.**
- Ogni implementatore: `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `superpowers:verification-before-completion`.
- Ogni revisore: `agent-skills:code-review-and-quality`.

---

## 2. Profili verticali

Percorsi predefiniti: `init` li propone e l'utente li adatta al progetto. Nomi degli agenti: `tollgate:implementer-<area>`, `tollgate:reviewer-<area>`, `tollgate:final-<area>`.

| Profilo | Percorsi predefiniti | Livello minimo | Specialista finale (L2) |
|---|---|---|---|
| `frontend` | `**/*.{tsx,jsx,vue,svelte,css,scss}`, `**/components/**`, `**/app/**/page.*`, `web/**` | L0 | no |
| `backend` | `api/**`, `server/**`, `**/routes/**`, `**/handlers/**`, `**/services/**` | L0 | no |
| `database` | `**/migrations/**`, `supabase/**`, `**/*.sql`, `prisma/**`, `**/schema.*` | **L2** | **sì** |
| `security` | `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**` | **L2** | **sì** |
| `infra` | `wrangler.{toml,jsonc}`, `workers/**`, `infra/**`, `Dockerfile*`, `**/*.tf` | L1 | no |
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
| `infra` | `rules-infra`, `cloudflare`, `workers-best-practices` · *wrangler* | `rules-infra`, `workers-best-practices` | — |
| `ai` | `rules-ai`, `claude-api` | `rules-ai`, `claude-api` | — |
| `3d` | `rules-3d`, `threejs-skills:threejs-fundamentals`, `threejs-game-skills:SKILL_08_Performance_Monitoring` | `rules-3d`, `threejs-game-skills:SKILL_08_Performance_Monitoring` | — |
| `e2e` | `rules-e2e`, `agent-skills:browser-testing-with-devtools` · *webapp-testing, playwright-cli* | `rules-e2e` | — |
| `copy` | `rules-copy`, `humanizer`, `copy-editing` | `rules-copy`, `humanizer` | — |
| `docs` | `rules-docs`, `agent-skills:documentation-and-adrs`, `humanizer` | `rules-docs`, `humanizer` | — |
| `ci` | `rules-ci`, `agent-skills:ci-cd-and-automation` | `rules-ci`, `rules-security` | `final-security` (stesso agente di `security`) |
| `mobile` | `rules-mobile` | `rules-mobile`, `rules-a11y` | — |
| `analytics` | `rules-analytics`, `analytics-tracking` | `rules-analytics` | — |
| *(generico)* | solo le comuni | solo le comuni | — |

### 2.2 Cosa distingue gli agenti di un'area

Nei subagenti distribuiti da un plugin Claude Code **ignora `mcpServers`, `hooks` e `permissionMode`** (documentazione dei subagenti, da confermare in P0). Un agente per area non può quindi avere server MCP propri. Si distingue per:
- **prompt**: obblighi comuni di `tollgate:implementer` più le regole dell'area;
- **skill**: precaricate con il campo `skills:` del frontmatter, che carica il contenuto intero (da qui il tetto di 3);
- **modello**: per esempio `inherit` per `security` e `database`, `sonnet` per `copy` e `docs`;
- **strumenti**: i revisori hanno solo `Read, Grep, Glob, Bash` e `disallowedTools: Edit, Write`; gli implementatori hanno `Write, Edit, Bash`.

Le `description` restano brevi: con circa 26 agenti, la documentazione avvisa oltre circa 15.000 token di descrizioni. L'instradamento non dipende comunque dalle descrizioni ma da `task start`.

---

### 2.3 Regole, revisione e Definition of Done (revisione 18)

- **Le regole sono la prova dei rilievi.** Con il disaccordo istruito (spec 8.6) ogni rilievo del revisore cita la regola violata: `R-FE-07`, `R-DB-03`… Un rilievo senza regola né file e riga viene scartato dal verificatore. Per questo ogni `rules-<area>` ha regole numerate e stabili: cambiare un numero rompe lo storico dei rilievi.
- **Standard del revisore.** Il prompt di ogni `reviewer-<area>` dice: approva se il task migliora la salute del codice; solo le regole marcate `[blocca]` danno rilievi `blocker` o `major`, le altre sono note.
- **Definition of Done per profilo** (campo `dod`, spec 8.7): i comandi del profilo che devono passare perché il lavoro conti. Proposte iniziali, da confermare quando si scrivono le regole:

| Profilo | `dod` |
|---|---|
| `frontend` | lint, typecheck, test dei componenti |
| `backend` | test delle API, typecheck |
| `database` | migrazione applicata e annullata su un DB vuoto (up e down) |
| `security` | test dei casi di accesso negato |
| `infra` | `wrangler deploy --dry-run` o equivalente |
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
R-FE-01 Ogni componente gestisce i quattro stati: caricamento, vuoto, errore, pieno.
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
| `rules-infra` | skill Cloudflare (Apache-2.0) |
| `rules-ai` | `claude-api` (Anthropic) |
| `rules-3d` | `threejs-skills`, `threejs-game-skills` (licenza da verificare) |
| `rules-e2e` | `browser-testing-with-devtools` (MIT), `webapp-testing` (Apache-2.0) |
| `rules-copy`, `rules-docs` | `humanizer` (licenza da verificare), `documentation-and-adrs` (MIT). Idee: Vercel writing-guidelines (senza licenza) |
| `rules-mobile`, `rules-analytics` | Da scrivere quasi da zero: nessuna fonte adatta trovata. Si scrivono solo quando un progetto reale le usa |
| `rules-performance` | `performance-optimization` (MIT), `web-perf` (Cloudflare, Apache-2.0) |
| `rules-ci` | `ci-cd-and-automation` (MIT), `gha-security-review` di getsentry (Apache-2.0, da leggere). Idee: Trail of Bits `agentic-actions-auditor` (CC-BY-SA). Regole minime: `permissions` esplicito e minimo, azioni fissate a uno SHA, nessun segreto in `pull_request` da fork, nessun `pull_request_target` con checkout del codice della PR |

**Processo per ogni `rules-<area>`.** Bozza distillata dalle fonti, con la fonte di ogni regola → revisione dell'utente → versione 1 nel plugin. Le regole cambiano con una PR, come il resto del plugin.

---

## 5. Problemi aperti emersi scrivendo il catalogo

1. ~~I workflow del progetto erano file protetti.~~ **Risolto (spec rev 17):** protetti solo i workflow `tollgate-*`; gli altri sono il profilo `ci` (L2), e `guard` rifiuta i workflow che potrebbero pubblicare stati falsi.
2. ~~Sovrapposizioni tra profili verticali.~~ **Risolto (spec rev 17):** vince il pattern più specifico.
3. **`mcpServers` ignorato nei subagenti di plugin.** Va confermato in P0 insieme a `skills:` nel frontmatter.
4. **Profili per progetti non web** (Python di dati, CLI, librerie) non sono coperti: cadono nel generico. Si aggiungono quando servono.

---

## 6. Cosa cambia nella spec del nucleo

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
