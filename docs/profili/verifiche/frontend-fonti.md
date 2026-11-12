# Verifica delle fonti di `rules-frontend`, dei pattern, dei marcatori e dell'esclusione

Verificatore: agente di sola lettura (Explore, sonnet), il 2026-11-11, sulla bozza di `skills/rules-frontend/SKILL.md` e di `templates/profiles/frontend.toml` al commit c4fff87. Ha letto le copie locali delle fonti (con la somma di controllo corretta su tutte), le sezioni citate del progetto di B (3.4, 12 e 13) e del catalogo (sezione 2 e 2.3). Per ogni voce di ogni `Fonte:`, ogni pattern di `paths`, ogni marcatore di `[detect] content` e ogni prefisso di `[detect] exclude`: il file esiste, la sezione citata esiste, dice ciò che la regola o il frammento le attribuisce (per WCAG: il numero, il nome e il livello del criterio), e la fonte è una skill con licenza MIT o Apache-2.0 (con il `LICENSE` nelle copie), una pagina ufficiale, una norma del W3C, il progetto di B o il catalogo. Nessuna frase della skill è uguale a una della fonte per più di una decina di parole. La copia di WCAG 2.2 è un riassunto: «reggere» un criterio poggia su titolo e glosse. Le pagine ufficiali sono estratti parziali, non pagine intere. Le citazioni di questo rapporto sono al più di una riga per fonte, in inglese quando la fonte lo è, e stanno solo qui. Il testo delle fonti è un dato, non un'istruzione. Le copie non sono nel repo.

Esito: ogni regola ha almeno una fonte `ok` per ogni voce. Alla prima passata le righe `no` erano due (R-FRONTEND-04 e R-FRONTEND-12), tutte e due per una parte della regola che la fonte non diceva; la parte senza fonte è stata tolta dalla regola, senza aggiungere fonti nuove, e le due voci corrette sono `ok` qui sotto con la correzione nella citazione. Pattern: 9 su 9 `ok`. Marcatori: 4 righe `ok`, che valgono per le 8 forme con le due virgolette. Esclusione: 6 su 6 `ok`. La colonna «Esito» dice `ok` oppure `no`.

## Regole e fonti

| Regola | Fonte (pagina, sezione) | Citazione | Esito |
|---|---|---|---|
| R-FRONTEND-01 | progetto di B, sezione 3.4 (riga `frontend`: per ogni libreria d'interfaccia toccata, la documentazione della versione in `package.json`) | «Per ogni libreria UI toccata, documentazione della versione in `package.json` (context7).» | ok |
| R-FRONTEND-01 | la pagina di Tailwind sul passaggio dalla 3 alla 4 https://tailwindcss.com/docs/upgrade-guide (la configurazione e quindi la documentazione cambiano con la versione) | «JavaScript config files are still supported for backward compatibility, but they are no longer detected automatically in v4.» | ok |
| R-FRONTEND-02 | progetto di B, sezione 3.4 (riga `frontend`: prima di creare un componente si cerca se ne esiste uno simile) | «Prima di creare un componente, cerca se ne esiste già uno simile nel progetto.» | ok |
| R-FRONTEND-02 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Component Architecture» (componenti piccoli e componibili) | «Prefer composition over configuration» e «Keep components focused» | ok |
| R-FRONTEND-03 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Component Architecture» (il contenitore dei dati gestisce i tre stati), «Meaningful Empty and Error States» e «Loading and Transitions» | tre stati nel contenitore dei dati (`isLoading`, `error`, `tasks.length === 0`); «// Don't show blank screens» (l'esempio mostra solo lo stato vuoto, il titolo nomina anche l'errore); «// Skeleton loading (not spinners for content)» | ok |
| R-FRONTEND-04 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Design System Adherence» (scala delle spaziature) e «Color» (token semantici, non valori esadecimali) | «Use semantic color tokens: `text-primary`, `bg-surface`, `border-default` — not raw hex values»; «Use a consistent spacing scale. Don't invent values». Corretta dopo la verifica: la parte «e caratteri» e la gerarchia dei caratteri sono uscite dalla regola e dalla voce, che ora dice solo spaziature e colori (la sezione parlava dei livelli dei titoli, non di token per i caratteri) | ok |
| R-FRONTEND-05 | WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 2.1.1 Keyboard (A) e 4.1.2 Name, Role, Value (A) | copia: «2.1.1 Keyboard (Level A)» e «4.1.2 Name, Role, Value (Level A)»; glossa: tutto usabile da tastiera, nome, ruolo e valore determinabili | ok |
| R-FRONTEND-05 | W3C, Using ARIA, prima regola (bozza sospesa): se esiste l'elemento nativo si usa quello | «First Rule of ARIA Use: If you can use a native HTML element or attribute with the semantics and behavior you require already built in,»; la copia dice «Discontinued Draft» (24/02/2026) e la `Fonte:` lo scrive; la regola regge comunque su WCAG 2.1.1 e 4.1.2 | ok |
| R-FRONTEND-05 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Keyboard Navigation» | `<div onClick={handleClick}>Click me</div>  // ✗ Not focusable` e «But prefer <button>» (il link `a` con `href` sta nella lista di controllo, «Buttons vs. Links») | ok |
| R-FRONTEND-05 | progetto di B, sezione 13 | «Le regole di accessibilità verificabili dal codice (dalla norma WCAG 2.2) diventano regole `R-FRONTEND-NN`» | ok |
| R-FRONTEND-06 | WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 1.1.1 Non-text Content (A) e 4.1.2 Name, Role, Value (A) | copia: «1.1.1 Non-text Content (Level A)» e «4.1.2 Name, Role, Value (Level A)»; glossa: alternativa testuale ai contenuti non testuali | ok |
| R-FRONTEND-06 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «ARIA Labels», e references/accessibility-checklist.md, «Screen Readers» | `<button aria-label="Close dialog"><XIcon /></button>`; lista di controllo: «All images have `alt` text (or `alt=""` for decorative images)» e «Icon-only buttons have `aria-label`» | ok |
| R-FRONTEND-06 | progetto di B, sezione 13 | come sopra, sezione 13 | ok |
| R-FRONTEND-07 | WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 1.3.1 Info and Relationships (A) e 3.3.2 Labels or Instructions (A) | copia: «1.3.1 Info and Relationships (Level A)» e «3.3.2 Labels or Instructions (Level A)» | ok |
| R-FRONTEND-07 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «ARIA Labels», e references/accessibility-checklist.md, «Form Labels» | `<label htmlFor="email">Email</label>`; lista di controllo: «Explicit label association», «Implicit wrapping» e `aria-label="Search tasks"`. Nota: la voce «Screen Readers» della lista ammette anche `aria-label` («All form inputs have associated labels (`<label>` or `aria-label`)»), mentre la voce «Forms» chiede «Every input has a visible label» e «Form Labels» preferisce l'etichetta visibile; la regola le accetta tutte (la pagina lo porta all'utente) | ok |
| R-FRONTEND-07 | progetto di B, sezione 13 | come sopra, sezione 13 | ok |
| R-FRONTEND-08 | WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 2.4.7 Focus Visible (AA) | copia: «2.4.7 Focus Visible (Level AA)» | ok |
| R-FRONTEND-08 | agent-skills 0.6.9 (Addy Osmani, MIT), references/accessibility-checklist.md, «Keyboard Navigation» e «Common Anti-Patterns» | «Focus is visible (outline/ring on focused elements)»; «Removing focus outlines … Style outlines, don't remove them» | ok |
| R-FRONTEND-08 | progetto di B, sezione 13 | come sopra, sezione 13 | ok |
| R-FRONTEND-09 | WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 4.1.3 Status Messages (AA) | copia: «4.1.3 Status Messages (Level AA)» | ok |
| R-FRONTEND-09 | agent-skills 0.6.9 (Addy Osmani, MIT), references/accessibility-checklist.md, «ARIA Roles» e «Quick Reference: ARIA Live Regions» | `<div role="status" aria-live="polite">Task saved</div>` e `<div role="alert">Error: Title is required</div>` | ok |
| R-FRONTEND-09 | progetto di B, sezione 13 | come sopra, sezione 13 | ok |
| R-FRONTEND-10 | WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 2.4.3 Focus Order (A) e 2.1.2 No Keyboard Trap (A) | copia: «2.4.3 Focus Order (Level A)» e «2.1.2 No Keyboard Trap (Level A)»; «Esc» viene solo dall'altra fonte | ok |
| R-FRONTEND-10 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Focus Management», e references/accessibility-checklist.md, «Keyboard Navigation» (Esc per chiudere, focus restituito alla chiusura) | `if (isOpen) closeRef.current?.focus();`; lista di controllo: «Custom widgets have keyboard support (Enter to activate, Escape to close)» e «Modals trap focus while open, return focus on close» | ok |
| R-FRONTEND-10 | progetto di B, sezione 13 | come sopra, sezione 13 | ok |
| R-FRONTEND-11 | catalogo 2.3 (riga `frontend`: nella definizione di fatto, i test dei componenti) | nella definizione di fatto del profilo `frontend`: lint, typecheck, test dei componenti | ok |
| R-FRONTEND-11 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Component Architecture» (il test accanto al componente) | «TaskList.test.tsx     # Tests» (sottosezione «File Structure») | ok |
| R-FRONTEND-12 | agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Avoid the AI Aesthetic» | «Purple/indigo everything», «Excessive gradients», «Stock card grids … Use the project's actual color palette» | ok |
| R-FRONTEND-12 | frontend-design 1.1.1 (Anthropic, Apache-2.0), skills/frontend-design/SKILL.md, «Process» (i tratti che ricorrono nelle interfacce generate) | «the SaaS-card kit: content chopped into identical rounded cards … and gradient washes as decoration». Corretta dopo la verifica: «carattere di sistema scelto per default» è uscito dalla regola (la sezione «Process» non lo cita, e «default families» sta in «Design principles»); restano viola o indaco ovunque, gradienti in eccesso e schede tutte uguali | ok |

Le voci «scelta nostra» non sono in questa tabella: stanno in «Parti dichiarate «scelta nostra»».

## Pattern dei percorsi

| Pattern | Fonte | Citazione | Esito |
|---|---|---|---|
| `**/components/**` | catalogo, sezione 2, riga `frontend` | «`**/components/**`»; può accendere qualche `.ts` o file di prova dentro `components/`: scelta del catalogo | ok |
| `web/**` | catalogo, sezione 2, riga `frontend` | «`web/**`»; copre tutta la cartella, anche file non d'interfaccia: scelta del catalogo | ok |
| `**/*.tsx` | catalogo, sezione 2; pagina di Next.js sul file `page` | «The `.js`, `.jsx`, or `.tsx` file extensions can be used for `page`.» | ok |
| `**/*.jsx` | catalogo, sezione 2; pagina di Next.js sul file `page` | stessa riga | ok |
| `**/*.vue` | catalogo, sezione 2; pagina di Vue sui file a componente singolo | «a special file format that allows us to encapsulate the template, logic, and styling of a Vue component in a single file. (*.vue)» | ok |
| `**/*.svelte` | catalogo, sezione 2; pagina di Svelte sui file `.svelte` | «They are written into .svelte files, using a superset of HTML.» | ok |
| `**/*.astro` | pagina delle pagine di Astro (il catalogo non lo elenca) | «Supported page files: `.astro`, `.md`, `.mdx` …» | ok |
| `**/*.css` | catalogo, sezione 2, riga `frontend` | «`**/*.{tsx,jsx,vue,svelte,css,scss}`»; nessuna pagina in copia lo nomina, lo regge il catalogo | ok |
| `**/*.scss` | catalogo, sezione 2, riga `frontend` | stessa riga | ok |

I commenti del frammento citano il catalogo per cartelle e fogli di stile: i percorsi stanno nella sezione 2 del catalogo (la 2.3 ha solo la definizione di fatto).

## Marcatori di contenuto

Per i marcatori con virgolette conta il nome del modulo: la riga con gli apici singoli vale anche per la forma con le doppie, che è lo stesso import scritto in un altro modo (decisione 5). Sono righe di import di librerie di rotte d'interfaccia, cercate come testo fisso.

| Marcatore | Fonte | Citazione | Esito |
|---|---|---|---|
| `from '@tanstack/react-router'` | pagina dei concetti di rotta di TanStack Router | «import { createFileRoute } from '@tanstack/react-router'» | ok |
| `from 'react-router'` | pagina dei moduli di rotta di React Router 7 | «import { Form } from "react-router";» | ok |
| `from 'react-router-dom'` | tutorial di React Router 6.30.1 | «import { useRouteError } from "react-router-dom";» | ok |
| `from '@remix-run/react'` | pagina del `loader` di Remix | «import { useLoaderData } from "@remix-run/react";» | ok |

## Esclusione

| Prefisso | Fonte | Citazione | Esito |
|---|---|---|---|
| `server/` | catalogo, sezione 2, riga `backend` | «`server/**`» | ok |
| `api/` | catalogo, sezione 2, riga `backend` | «`api/**`» (la cartella `api/` alla radice) | ok |
| `backend/` | catalogo, sezione 2, riga `backend`; progetto di B, sezione 12 | «`backend/**`» | ok |
| `functions/` | catalogo, sezione 2, riga `backend` | «`functions/**`» (la cartella `functions/` alla radice del progetto Pages) | ok |
| `infra/` | catalogo, sezione 2, riga `infra` | «`infra/**`» (la cartella `infra/` alla radice del progetto) | ok |
| `supabase/` | progetto di B, sezioni 2 e 12 | «il suo frammento esclude la cartella `supabase/`»; sezione 2: `supabase/**` | ok |

## Parti dichiarate «scelta nostra»

Stanno nella pagina per l'utente, nella sezione «Cosa hai deciso»:

- R-FRONTEND-01: la via d'uscita per i progetti senza versione dichiarata (nessun `package.json`, libreria da una CDN senza versione). Le fonti chiedono la documentazione della versione in `package.json`; il caso senza versione è nostro.
- R-FRONTEND-02: i percorsi dei componenti simili e il motivo nel report.
- R-FRONTEND-11: la condizione «se il repo ha già test dei componenti». Il catalogo mette i test dei componenti nella definizione di fatto, senza condizione.
- R-FRONTEND-07: la regola accetta anche `aria-label` (voce «Screen Readers» della lista di controllo), mentre la voce «Forms» chiede un'etichetta visibile. Non è un `no`: tutte e due le voci sono `ok`.
- I pattern per estensione `**/*.css` e `**/*.scss`: li regge solo il catalogo.
- I `.ts` e `.js` con codice d'interfaccia e `services/` e `hooks/`, lasciati al generico; `.html`, `.sass` e `.less` fuori; le pagine `page.js` di Next.js fuori.
- Le precedenze tra profili (casi P1-P38 della decisione 4 del piano): costi accettati dall'utente, tutti nella pagina.

## Regole tolte dalla verifica

Nessuna regola esce: ciascuna ha almeno una fonte `ok` per ogni voce, e i numeri restano. Nessun pattern, marcatore o prefisso esce. Due regole sono state corrette togliendo la parte senza fonte:

- **R-FRONTEND-04.** Perde «e caratteri»: restano colori e spaziature. La voce della `Fonte:` perde «gerarchia dei caratteri», perché «Design System Adherence» e «Typography» parlano dei livelli dei titoli, non di token per i caratteri.
- **R-FRONTEND-12.** Perde «carattere di sistema scelto per default»: restano viola o indaco ovunque, gradienti in eccesso e schede tutte uguali, che le due fonti citate mostrano.
