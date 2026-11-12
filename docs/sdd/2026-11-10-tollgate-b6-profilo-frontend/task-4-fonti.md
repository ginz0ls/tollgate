# Verifica delle fonti di rules-frontend (Task 4, Step 1)

**Metodo.** Letti `skills/rules-frontend/SKILL.md`, `templates/profiles/frontend.toml`, `backend.toml`, `infra.toml`, `FONTI.md`, tutte le copie di `W/fonti/frontend/` (skill con `LICENSE`, elenco dei criteri WCAG, pagine dei framework), il progetto di B (3.4, 12, 13) e il catalogo (sezione 2, 2.3). `W/task-3-report.md` non aperto: fonti verificate direttamente. `sha256sum -c SHA256SUMS` in `W/fonti/frontend/`: nessuna riga diversa da OK. `ui-ux-pro-max` non compare tra le fonti.

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-FRONTEND-01 | progetto di B, sezione 3.4 (riga `frontend`: per ogni libreria d'interfaccia toccata, la documentazione della versione in `package.json`) | «Per ogni libreria UI toccata, documentazione della versione in `package.json` (context7).» | ok |
| R-FRONTEND-01 | la pagina di Tailwind sul passaggio dalla 3 alla 4 https://tailwindcss.com/docs/upgrade-guide (la configurazione e quindi la documentazione cambiano con la versione) | «JavaScript config files are still supported for backward compatibility, but they are no longer detected automatically in v4.» | ok |
| R-FRONTEND-02 | progetto di B, sezione 3.4 (riga `frontend`: prima di creare un componente si cerca se ne esiste uno simile) | «Prima di creare un componente, cerca se ne esiste già uno simile nel progetto.» | ok |
| R-FRONTEND-02 | agent-skills 0.6.9, frontend-ui-engineering, «Component Architecture» (componenti piccoli e componibili) | «Prefer composition over configuration» e «Keep components focused» | ok |
| R-FRONTEND-03 | agent-skills 0.6.9, frontend-ui-engineering, «Component Architecture» (il contenitore dei dati gestisce i tre stati) | `if (isLoading) return <TaskListSkeleton />; if (error) return <ErrorState …/>; if (tasks.length === 0) return <EmptyState …/>` | ok |
| R-FRONTEND-03 | agent-skills 0.6.9, frontend-ui-engineering, «Meaningful Empty and Error States» | «// Don't show blank screens» (l'esempio mostra solo lo stato vuoto; il titolo nomina anche l'errore) | ok |
| R-FRONTEND-03 | agent-skills 0.6.9, frontend-ui-engineering, «Loading and Transitions» | «// Skeleton loading (not spinners for content)» | ok |
| R-FRONTEND-04 | agent-skills 0.6.9, frontend-ui-engineering, «Design System Adherence» (scala delle spaziature, gerarchia dei caratteri) e «Color» (token semantici, non valori esadecimali) | «Use semantic color tokens: `text-primary`, `bg-surface`, `border-default` — not raw hex values» (colore: regge). «Use a consistent spacing scale. Don't invent values» (una scala, non un token). «Respect the type hierarchy: h1 → Page title…» (livelli dei titoli, non caratteri o font) | no: la sezione «Typography» parla dei livelli dei titoli e non dice che caratteri o font nuovi vengano da token; la regola chiede che «colori, spaziature e caratteri nuovi» usino i token |
| R-FRONTEND-05 | WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 2.1.1 Keyboard (A) e 4.1.2 Name, Role, Value (A) | copia: «2.1.1 Keyboard (Level A)», «4.1.2 Name, Role, Value (Level A)»; glossa «tutto usabile da tastiera; nome, ruolo e valore determinabili» | ok |
| R-FRONTEND-05 | W3C, Using ARIA, prima regola (bozza sospesa): se esiste l'elemento nativo si usa quello | «First Rule of ARIA Use: If you can use a native HTML element or attribute with the semantics and behavior you require already built in,» (la copia dice «Discontinued Draft», la `Fonte:` lo scrive) | ok |
| R-FRONTEND-05 | agent-skills 0.6.9, frontend-ui-engineering, «Keyboard Navigation» | `<div onClick={handleClick}>Click me</div>  // ✗ Not focusable` e «But prefer <button>» (la parte «link `a` con `href`» sta nella checklist, «Buttons vs. Links») | ok |
| R-FRONTEND-05 | progetto di B, sezione 13 | «Le regole di accessibilità verificabili dal codice (dalla norma WCAG 2.2) diventano regole `R-FRONTEND-NN`» | ok |
| R-FRONTEND-06 | WCAG 2.2 del W3C, 1.1.1 Non-text Content (A) e 4.1.2 Name, Role, Value (A) | copia: «1.1.1 Non-text Content (Level A)»; glossa «alternativa testuale ai contenuti non testuali» | ok |
| R-FRONTEND-06 | agent-skills 0.6.9, frontend-ui-engineering, «ARIA Labels», e references/accessibility-checklist.md, «Screen Readers» | `<button aria-label="Close dialog"><XIcon /></button>`; checklist: «All images have `alt` text (or `alt=""` for decorative images)» e «Icon-only buttons have `aria-label`» | ok |
| R-FRONTEND-06 | progetto di B, sezione 13 | come sopra | ok |
| R-FRONTEND-07 | WCAG 2.2 del W3C, 1.3.1 Info and Relationships (A) e 3.3.2 Labels or Instructions (A) | copia: «1.3.1 Info and Relationships (Level A)», «3.3.2 Labels or Instructions (Level A)» | ok |
| R-FRONTEND-07 | agent-skills 0.6.9, frontend-ui-engineering, «ARIA Labels», e references/accessibility-checklist.md, «Form Labels» | `<label htmlFor="email">Email</label>`; checklist: «Explicit label association», «Implicit wrapping», `aria-label="Search tasks"` | ok |
| R-FRONTEND-07 | progetto di B, sezione 13 | come sopra | ok |
| R-FRONTEND-08 | WCAG 2.2 del W3C, 2.4.7 Focus Visible (AA) | copia: «2.4.7 Focus Visible (Level AA)» | ok |
| R-FRONTEND-08 | agent-skills 0.6.9, references/accessibility-checklist.md, «Keyboard Navigation» e «Common Anti-Patterns» | «Focus is visible (outline/ring on focused elements)»; «Removing focus outlines … Style outlines, don't remove them» | ok |
| R-FRONTEND-08 | progetto di B, sezione 13 | come sopra | ok |
| R-FRONTEND-09 | WCAG 2.2 del W3C, 4.1.3 Status Messages (AA) | copia: «4.1.3 Status Messages (Level AA)» | ok |
| R-FRONTEND-09 | agent-skills 0.6.9, references/accessibility-checklist.md, «ARIA Roles» e «Quick Reference: ARIA Live Regions» | `<div role="status" aria-live="polite">Task saved</div>`; `<div role="alert">Error: Title is required</div>` | ok |
| R-FRONTEND-09 | progetto di B, sezione 13 | come sopra | ok |
| R-FRONTEND-10 | WCAG 2.2 del W3C, 2.4.3 Focus Order (A) e 2.1.2 No Keyboard Trap (A) | copia: «2.4.3 Focus Order (Level A)», «2.1.2 No Keyboard Trap (Level A)»; «Esc» viene dall'altra fonte | ok |
| R-FRONTEND-10 | agent-skills 0.6.9, frontend-ui-engineering, «Focus Management», e references/accessibility-checklist.md, «Keyboard Navigation» (Esc per chiudere, focus restituito alla chiusura) | `if (isOpen) closeRef.current?.focus();`; checklist: «Custom widgets have keyboard support (Enter to activate, Escape to close)» e «Modals trap focus while open, return focus on close» | ok |
| R-FRONTEND-10 | progetto di B, sezione 13 | come sopra | ok |
| R-FRONTEND-11 | catalogo 2.3 (riga `frontend`: nella definizione di fatto, i test dei componenti) | `dod`: «`frontend` \| lint, typecheck, test dei componenti» | ok |
| R-FRONTEND-11 | agent-skills 0.6.9, frontend-ui-engineering, «Component Architecture» (il test accanto al componente) | «TaskList.test.tsx     # Tests» (sottosezione «File Structure») | ok |
| R-FRONTEND-12 | agent-skills 0.6.9, frontend-ui-engineering, «Avoid the AI Aesthetic» | «Purple/indigo everything», «Excessive gradients», «Stock card grids … Use the project's actual color palette» | ok |
| R-FRONTEND-12 | frontend-design 1.1.1 (Anthropic, Apache-2.0), skills/frontend-design/SKILL.md, «Process» (i tratti che ricorrono nelle interfacce generate) | «the SaaS-card kit: content chopped into identical rounded cards … and gradient washes as decoration» (schede e gradienti reggono; il «carattere di sistema» non compare in «Process» e i «default families» stanno in «Design principles») | no: «Process» non cita i caratteri predefiniti, e «default families» non equivale a «carattere di sistema» |

Scelte dichiarate «nostra» (non verificate, da portare all'utente): R-01 la via d'uscita per i progetti senza versione dichiarata; R-02 i percorsi e il motivo nel report; R-11 la condizione «se il repo ha già test dei componenti».

## Pattern dei percorsi

| Pattern | Fonte | Citazione | Esito |
|---|---|---|---|
| `**/components/**` | catalogo, sezione 2, riga `frontend` | «`**/components/**`» | ok: può accendere qualche `.ts` o file di prova dentro `components/`; scelta del catalogo |
| `web/**` | catalogo, sezione 2, riga `frontend` | «`web/**`» | ok: copre tutta la cartella, anche file non d'interfaccia; scelta del catalogo |
| `**/*.tsx` | catalogo; `pagine/nextjs-page.md` | «The `.js`, `.jsx`, or `.tsx` file extensions can be used for `page`.» | ok |
| `**/*.jsx` | catalogo; `pagine/nextjs-page.md` | stessa riga | ok |
| `**/*.vue` | catalogo; `pagine/vue-sfc.md` | «a special file format that allows us to encapsulate the template, logic, and styling of a Vue component in a single file. (*.vue)» | ok |
| `**/*.svelte` | catalogo; `pagine/svelte-files.md` | «They are written into .svelte files, using a superset of HTML.» | ok |
| `**/*.astro` | `pagine/astro-pages.md` (il catalogo non lo elenca) | «Supported page files: `.astro`, `.md`, `.mdx` …» | ok |
| `**/*.css` | catalogo, sezione 2, riga `frontend` | «`**/*.{tsx,jsx,vue,svelte,css,scss}`» | ok: nessuna pagina in copia lo nomina, lo regge il catalogo |
| `**/*.scss` | catalogo, sezione 2, riga `frontend` | stessa riga | ok |

Nota di forma: i commenti del frammento citano «catalogo 2.3, riga `frontend`» per cartelle e fogli di stile, ma i percorsi stanno nella sezione 2 (la 2.3 ha solo il `dod`).

## Marcatori di contenuto

| Marcatore | Fonte | Citazione | Esito |
|---|---|---|---|
| `from '@tanstack/react-router'` | `pagine/tanstack-routing-concepts.md` | «import { createFileRoute } from '@tanstack/react-router'» | ok |
| `from 'react-router'` | `pagine/reactrouter-route-module.md` | «import { Form } from "react-router";» | ok |
| `from 'react-router-dom'` | `pagine/reactrouter-v6-tutorial.md` | «import { useRouteError } from "react-router-dom";» | ok |
| `from '@remix-run/react'` | `pagine/remix-loader.md` | «import { useLoaderData } from "@remix-run/react";» | ok |

Tutti sono righe d'import di librerie di rotte d'interfaccia; nel frammento ci sono anche con le doppie virgolette.

## Esclusione

| Prefisso | Fonte | Citazione | Esito |
|---|---|---|---|
| `server/` | catalogo, sezione 2, riga `backend`; `templates/profiles/backend.toml` | `"server/**"` | ok |
| `api/` | idem | `"api/**"` («la cartella `api/` alla radice») | ok |
| `backend/` | catalogo, riga `backend`; progetto di B, sezione 12; backend.toml | `"backend/**"` | ok |
| `functions/` | catalogo, riga `backend`; backend.toml | `"functions/**"` («la cartella `functions/` alla radice del progetto Pages») | ok |
| `infra/` | catalogo, riga `infra`; `templates/profiles/infra.toml` | `"infra/**"` («La cartella `infra/` alla radice del progetto.») | ok |
| `supabase/` | progetto di B, sezione 12; catalogo, riga `database` | «il suo frammento esclude la cartella `supabase/`»; catalogo `supabase/**` | ok |

## Riepilogo

- Regole e fonti: 31 voci verificate, 29 `ok`, 2 `no`. Pattern: 9 `ok`, 0 `no`. Marcatori: 4 `ok`, 0 `no`. Esclusione: 6 `ok`, 0 `no`.
- Regole senza nessuna voce `ok`: nessuna.
- Regole con almeno una voce `no`:
  - R-FRONTEND-04 (voce agent-skills «Design System Adherence»): togliere «e caratteri» dalla regola, oppure citare una fonte che parli di token per i caratteri.
  - R-FRONTEND-12 (voce frontend-design «Process»): citare anche «Design principles» (solo «default families»), oppure togliere «carattere di sistema scelto per default». Le altre due voci (gradiente viola, schede tutte uguali) reggono.
- Regole di accessibilità senza criterio WCAG: nessuna; R-05 … R-10 nominano criteri con numero, nome e livello uguali alla copia. In R-10 «Esc» e «focus restituito» vengono solo da agent-skills.
- Parti «scelta nostra»: R-01 (via d'uscita senza versione), R-02 (percorsi e motivo nel report), R-11 (condizione sui test già presenti).
- Pattern, marcatori e prefissi `no`: nessuno.
- Frasi copiate: nessuna.
- Altro: la copia WCAG è un riassunto del modello, quindi «reggere» un criterio poggia su titolo e glosse. Le skill di agent-skills sono al livello WCAG 2.1 AA, la regola cita 2.2: nessun conflitto per questi criteri.
