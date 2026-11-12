# Report Task 3 (implementatore)

## Cosa ho fatto
- `skills/rules-frontend/SKILL.md` (75 righe, 12 regole, 9 che bloccano: 01-09 e 11; 10 e 12 no), senza `approved`.
- `templates/profiles/frontend.toml` (decisioni 3, 5, 7, 8, 10, 13), un commento per gruppo con la fonte.
- `tests/test_rules_frontend.py` (`RulesFrontendTest`, 27 test), `tests/test_fragments.py` (`test_real_fragments_load` legge `frontend`), `tests/test_init.py` (`_real_fragments_root(test, areas=None)`, usata da `test_real_trees_light_no_profile`; classe `FrontendPrecedenceTest`: P1-P38 + `test_real_frontend_exclude_several_prefixes`).
- `docs/uso/comandi.md`: sezione `/tollgate:rules-frontend` (bozza non approvata); `init`: «quattro forme» e frase sui pattern per estensione che nomina `frontend`; frase su `exclude` che nomina anche `frontend`.

## TDD
RED (prima di skill e frammento): `python3 -B -m unittest tests.test_init.FrontendPrecedenceTest` -> 30 FAIL + 1 ERROR (exclude); verdi come guardie: P2, P5, P7, P16, P17, P18, P21, P22. `tests.test_rules_frontend`: tutti in errore (skill assente).
GREEN: `python3 -B -m unittest tests.test_rules_frontend tests.test_init.FrontendPrecedenceTest tests.test_fragments` -> 96 OK; `tests.test_docs ... tests.test_init` (7 moduli) -> 361 OK (7 skipped, preesistenti). `claude plugin validate --strict .`: exit 0.

## Regole, fonte per fonte (file della copia in W/fonti/frontend/)
Sigle: FUE = agent-skills-0.6.9/frontend-ui-engineering-SKILL.md; ACL = agent-skills-0.6.9/accessibility-checklist.md; FD = frontend-design-1.1.1/frontend-design-SKILL.md; WCAG = pagine/w3c-wcag22.md.
- 01: progetto 3.4 (riga `frontend`); pagine/tailwind-upgrade-guide.md (v4 configura nel CSS, il file JS non è più letto da solo); via d'uscita «scelta nostra».
- 02: progetto 3.4; FUE «Component Architecture»; percorsi e motivo nel report «scelta nostra».
- 03: FUE «Component Architecture» (contenitore con i tre stati), «Meaningful Empty and Error States», «Loading and Transitions». Scartato «catalogo 4» della bozza: non serve.
- 04: FUE «Design System Adherence» (scala spaziature, gerarchia caratteri), «Color» (token semantici, non esadecimali).
- 05: WCAG 2.1.1 (A), 4.1.2 (A); pagine/w3c-using-aria.md prima regola, citata «(bozza sospesa)»; FUE «Keyboard Navigation»; sez. 13. (ACL «Buttons vs. Links» conferma, non citata.)
- 06: WCAG 1.1.1 (A), 4.1.2 (A); FUE «ARIA Labels»; ACL «Screen Readers»; sez. 13.
- 07: WCAG 1.3.1 (A), 3.3.2 (A); FUE «ARIA Labels»; ACL «Form Labels»; sez. 13.
- 08: WCAG 2.4.7 (AA); ACL «Keyboard Navigation» e «Common Anti-Patterns» (non FUE «Focus Management», che parla di spostare il focus, non di toglierlo); sez. 13.
- 09: WCAG 4.1.3 (AA); ACL «ARIA Roles» e «Quick Reference: ARIA Live Regions»; sez. 13.
- 10: WCAG 2.4.3 (A), 2.1.2 (A); FUE «Focus Management»; **ACL «Keyboard Navigation»** dice «Escape to close» e «Modals ... return focus on close»: la parte su Esc resta (carry D9) con quella voce nella `Fonte:`; sez. 13.
- 11: catalogo 2.3 (riga `frontend`, `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md:93`); FUE «Component Architecture» (test accanto al componente; «Verification» non usata); la condizione «se il repo ha già test» è «scelta nostra».
- 12: FUE «Avoid the AI Aesthetic»; FD «Process» (elenco dei tratti da modello, voce «SaaS-card kit», «template chrome»).

## Scostamenti dal piano / cose per il Task 4 («Da decidere tu»)
1. Tre `Fonte:` dichiarano «scelta nostra» (01, 02, 11): la via d'uscita senza versione (già prevista), il formato del report di 02 (percorsi e motivo) e la condizione «se il repo ha già test dei componenti» di 11. Un test (`test_extensions_of_the_sources_are_declared_as_our_choice`) le fissa; vanno nella pagina.
2. R-FRONTEND-07: tolto dalla bozza «un segnaposto non basta» (nessuna copia lo dice: ACL chiede un'etichetta, non nomina il segnaposto). La regola resta uguale nella sostanza.
3. R-FRONTEND-08: tolti `outline-0` e `focus:outline-none` della bozza: nessuna pagina in `fonti/` li mostra (la guida di Tailwind non parla di outline); resta «per esempio `outline: none`» (ACL).
4. R-FRONTEND-04: la bozza citava «Design System Adherence» e «Color» ed è rimasta tale.
5. `test_a11y_rules_name_a_wcag_criterion` del brief usa `\d\.\d\.\d+`, che sarebbe soddisfatto da «0.6.9» (versione di agent-skills): ho usato `[1-4]\.\d{1,2}\.\d{1,2} Nome (livello)` e controllo che il livello sia quello di WCAG (tabella nel test dai fatti verificati); in più `test_wcag_criteria_stay_in_the_verified_set`, `test_using_aria_is_cited_with_its_status`, `test_ui_ux_pro_max_is_not_a_source`.
6. `test_user_choices_covered`: tabella con tutte le otto regole che citano il progetto di B (01, 02, 05-10) e controllo che non ce ne siano altre (insieme uguale).
7. «Dove informarsi» cita per i framework solo URL presenti in `FONTI.md` (Next.js page, React Router routing, TanStack routing concepts, Remix routes, SvelteKit routing, Nuxt pages, Vue SFC, Astro pages). Nel frammento la fonte di `remix` è `https://v2.remix.run/docs/route/loader` (è la pagina che mostra `@remix-run/react`; `discussion/routes` no); quella di `react-router-dom` è il tutorial 6.30.1; quella di `react-router` la pagina route-module.
8. Tabella P1-P38: ogni caso passa senza correzioni alla tabella; nell'asserzione i `paths` sono confrontati ordinati (P33: `**/*.css` prima di `**/*.tsx`).
9. Commenti del frammento: `**/*.css`/`**/*.scss` hanno come fonte solo il catalogo 2.3 (le pagine dei framework in `fonti/` non parlano di CSS); lo segnalo al Task 4.

## Non toccato
`spikes/b1/flowreg.py`, `spikes/run-b1-flow.sh`, `tests/test_b1_scripts.py`, i file approvati dell'elenco, `approved` (Task 5).
