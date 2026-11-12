---
name: rules-frontend
description: Regole di tollgate per il codice d'interfaccia (componenti, pagine, stili, accessibilità): le caricano in automatico gli agenti dell'area frontend, non serve invocarla.
version: 1
approved: 2026-11-11
---
# Regole frontend (versione 1)

Sono le regole per il codice che l'utente vede e tocca: componenti, pagine, stili, e l'accessibilità di tutto questo. Valgono in aggiunta a quelle di base. Chi scrive le segue prima di toccare un file. Chi rivede le applica guardando ciò che ha davanti, e per ognuna risponde sì o no: sotto ogni regola la riga «Si giudica su» dice se la risposta sta nel diff o nel report. Le regole segnate `[blocca]` si giudicano sul diff o sul report, perché nei lavori senza il passo «informati prima» la nota non c'è. Un difetto si segnala una volta sola, con la regola che viola.

Un componente è un file `.tsx`, `.jsx`, `.vue`, `.svelte` o `.astro` che esporta un elemento d'interfaccia (in `.tsx` e `.jsx` una funzione che restituisce markup; in `.vue`, `.svelte` e `.astro` il file stesso), nuovo o cambiato nel diff.

## Prima di scrivere

R-FRONTEND-01 [blocca] Se il diff usa per la prima volta nel file un'API di una libreria d'interfaccia (framework, router, libreria di componenti, Tailwind), il report ha l'indirizzo della documentazione ufficiale della versione scritta in `package.json`, con la versione; se il progetto non dichiara la versione di quella libreria (nessun `package.json`, libreria caricata da una CDN senza versione), il report lo dice e dà l'indirizzo della documentazione corrente.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `frontend`: per ogni libreria d'interfaccia toccata, la documentazione della versione in `package.json`); la pagina di Tailwind sul passaggio dalla 3 alla 4 https://tailwindcss.com/docs/upgrade-guide (la configurazione e quindi la documentazione cambiano con la versione); la via d'uscita per i progetti senza versione dichiarata è una scelta nostra

R-FRONTEND-02 [blocca] Se il diff crea un componente nuovo, il report nomina i componenti simili cercati nel progetto (percorsi) e perché non li riusa, o dice che non ce ne sono.
Si giudica su: report
Fonte: progetto di B, sezione 3.4 (riga `frontend`: prima di creare un componente si cerca se ne esiste uno simile); agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Component Architecture» (componenti piccoli e componibili); i percorsi e il motivo nel report sono una scelta nostra

## Mentre lavori

R-FRONTEND-03 [blocca] Un componente nuovo o cambiato che carica dati mostra uno stato di caricamento, uno d'errore e uno vuoto.
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Component Architecture» (il contenitore dei dati gestisce i tre stati), «Meaningful Empty and Error States» e «Loading and Transitions»

R-FRONTEND-04 [blocca] Se il progetto ha token o variabili di design (variabili CSS, tema di Tailwind), colori e spaziature nuovi li usano: nessun valore di colore scritto a mano in un componente.
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Design System Adherence» (scala delle spaziature) e «Color» (token semantici, non valori esadecimali)

R-FRONTEND-05 [blocca] Un elemento che reagisce a un clic è un `button` o un link `a` con `href`, non un `div` o uno `span` con un gestore di clic.
Si giudica su: diff
Fonte: WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 2.1.1 Keyboard (A) e 4.1.2 Name, Role, Value (A); W3C, Using ARIA, prima regola (bozza sospesa): se esiste l'elemento nativo si usa quello; agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Keyboard Navigation»; progetto di B, sezione 13

R-FRONTEND-06 [blocca] Un pulsante o un link con la sola icona ha un nome accessibile (`aria-label` o testo nascosto); un'immagine che informa ha `alt` con il contenuto, una decorativa `alt=""`.
Si giudica su: diff
Fonte: WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 1.1.1 Non-text Content (A) e 4.1.2 Name, Role, Value (A); agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «ARIA Labels», e references/accessibility-checklist.md, «Screen Readers»; progetto di B, sezione 13

R-FRONTEND-07 [blocca] Ogni campo di un modulo ha un'etichetta associata (`label` con `for` o `htmlFor`, `label` che lo contiene, oppure `aria-labelledby` o `aria-label`).
Si giudica su: diff
Fonte: WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 1.3.1 Info and Relationships (A) e 3.3.2 Labels or Instructions (A); agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «ARIA Labels», e references/accessibility-checklist.md, «Form Labels»; progetto di B, sezione 13

R-FRONTEND-08 [blocca] Il diff non toglie l'indicatore del focus (per esempio con `outline: none`) senza uno stile di focus visibile al suo posto.
Si giudica su: diff
Fonte: WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 2.4.7 Focus Visible (AA); agent-skills 0.6.9 (Addy Osmani, MIT), references/accessibility-checklist.md, «Keyboard Navigation» e «Common Anti-Patterns»; progetto di B, sezione 13

R-FRONTEND-09 [blocca] Un messaggio che compare senza spostare il focus (salvataggio riuscito, errore d'invio) sta in una regione `role="status"`, `role="alert"` o con `aria-live`.
Si giudica su: diff
Fonte: WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 4.1.3 Status Messages (AA); agent-skills 0.6.9 (Addy Osmani, MIT), references/accessibility-checklist.md, «ARIA Roles» e «Quick Reference: ARIA Live Regions»; progetto di B, sezione 13

R-FRONTEND-10 Un dialogo o un menu che si apre porta il focus al suo interno, si chiude con Esc e riporta il focus dove era.
Si giudica su: diff
Fonte: WCAG 2.2 del W3C (https://www.w3.org/TR/WCAG22/), 2.4.3 Focus Order (A) e 2.1.2 No Keyboard Trap (A); agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Focus Management», e references/accessibility-checklist.md, «Keyboard Navigation» (Esc per chiudere, focus restituito alla chiusura); progetto di B, sezione 13

R-FRONTEND-11 [blocca] Se il repo ha già test dei componenti (`*.test.tsx`, `*.spec.tsx`, una cartella `__tests__/`), un componente nuovo o cambiato con stato, gestori o condizioni ha un test dei componenti nel diff.
Si giudica su: diff
Fonte: catalogo 2.3 (riga `frontend`: nella definizione di fatto, i test dei componenti); agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Component Architecture» (il test accanto al componente); la condizione «se il repo ha già test dei componenti» è una scelta nostra

R-FRONTEND-12 Lo stile nuovo segue quello già presente nel progetto, senza le scelte predefinite da modello (viola o indaco ovunque, gradienti in eccesso, schede tutte uguali).
Si giudica su: diff
Fonte: agent-skills 0.6.9 (Addy Osmani, MIT), skills/frontend-ui-engineering/SKILL.md, «Avoid the AI Aesthetic»; frontend-design 1.1.1 (Anthropic, Apache-2.0), skills/frontend-design/SKILL.md, «Process» (i tratti che ricorrono nelle interfacce generate)

## Dove informarsi

Prima di scrivere si aprono i componenti e gli stili già presenti (R-FRONTEND-02, R-FRONTEND-04). Per ogni libreria si legge la versione in `package.json` e si cerca la pagina ufficiale di quella versione, per esempio Tailwind 3 o Tailwind 4; se la versione non si trova o la pagina non c'è, il report lo dice e non si inventa la sintassi.

- Le skill `frontend-design` (direzione estetica, tipografia), `ui-ux-pro-max` (stili, palette, linee guida di UX) e `frontend-ui-engineering` (architettura dei componenti, accessibilità), se i plugin sono installati.
- Accessibilità: WCAG 2.2 https://www.w3.org/TR/WCAG22/ e, come guida all'uso di ARIA (bozza sospesa del W3C), https://www.w3.org/TR/using-aria/.
- Per un framework, la pagina della versione in uso, per esempio https://nextjs.org/docs/app/api-reference/file-conventions/page, https://reactrouter.com/start/framework/routing, https://tanstack.com/router/latest/docs/framework/react/routing/routing-concepts, https://v2.remix.run/docs/discussion/routes, https://svelte.dev/docs/kit/routing, https://nuxt.com/docs/4.x/directory-structure/app/pages, https://vuejs.org/guide/scaling-up/sfc.html, https://docs.astro.build/en/basics/astro-pages/.
- Per gli stili: https://tailwindcss.com/docs/upgrade-guide per il passaggio dalla 3 alla 4.

## Fonti

Le regole sono scritte con parole nostre. Da `frontend-ui-engineering` di agent-skills 0.6.9 (Addy Osmani, licenza MIT, con la sua lista di controllo dell'accessibilità) e da `frontend-design` 1.1.1 (Anthropic, licenza Apache-2.0) vengono i temi e i nomi delle sezioni, senza testo copiato. Da WCAG 2.2 del W3C (Raccomandazione del 12 dicembre 2024) si cita il numero, il nome e il livello di ogni criterio, e dalla prima regola di «Using ARIA» (bozza sospesa del W3C) il solo principio; le pagine ufficiali di Next.js, React Router, TanStack Router, Remix, SvelteKit, Nuxt, Vue, Astro e Tailwind riportano i fatti, non il testo. Le scelte dell'utente stanno nel progetto di B (docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md, sezioni 3.4 e 13) e nel catalogo (sezione 2.3). I nomi dei file e i marcatori con cui `init` riconosce il profilo (`templates/profiles/frontend.toml`) vengono dalle stesse pagine: un commento del frammento dice quale per ogni gruppo.
