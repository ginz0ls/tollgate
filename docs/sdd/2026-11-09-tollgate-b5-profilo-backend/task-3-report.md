# Task 3 - report

## Implementato
- `skills/rules-backend/SKILL.md`: 12 regole (R-BACKEND-01..12, 10 `[blocca]`, 10 e 11 no), senza `approved`; paragrafo iniziale con la riga `Un endpoint è…`; sezioni Prima di scrivere / Mentre lavori / Dove informarsi / Fonti. 75 righe.
- `templates/profiles/backend.toml`: decisioni 2, 3, 4, 8, 9, 12 (6 pattern, 24 marcatori nelle due forme di virgolette, `exclude = ["supabase/"]`, `commands = {}`, `dod = []`), un commento con la fonte per gruppo.
- `tests/test_rules_backend.py` (`RulesBackendTest`, 22 test); `tests/test_fragments.py` (`test_real_fragments_load` legge anche `backend`).
- `docs/uso/comandi.md`: sezione `/tollgate:rules-backend` (bozza non approvata) e frase su `exclude` / `supabase/` in `/tollgate:init`.

## Fonte usata per regola (file di `fonti/backend/` e sezione)
| Regola | Fonti |
|---|---|
| 01 | progetto di B 3.4; `agent-skills-api-and-interface-design.SKILL.md`, «Contract First» |
| 02 | progetto di B 3.4; `workers-fetch-handler.md`, `workers-bindings.md`; `cloudflare-skills-workers-best-practices.md` (estratto «Prefer retrieval over pre-training»); estensione a libreria standard e framework: scelta nostra |
| 03 | `agent-skills-api-and-interface-design.SKILL.md`, «Validate at Boundaries»; `ecc-security-reviewer.md` (analisi OWASP / input) |
| 04 | `agent-skills-api-and-interface-design.SKILL.md`, «Consistent Error Semantics» |
| 05 | idem, «Hyrum's Law» e «Prefer Addition Over Modification» |
| 06 | `ecc-security-reviewer.md` («Code Pattern Review», riga SQL concatenato); `ecc-code-reviewer.md` («Security (CRITICAL)», SQL injection) |
| 07 | `workers-bindings.md`, `workers-secrets.md` (anche il divieto di `vars` per i segreti); `cloudflare-skills-workers-best-practices.md` (segreti nel controllo di versione); `ecc-security-reviewer.md` (segreti nel codice) |
| 08 | `agent-skills-observability-and-instrumentation.SKILL.md`, «Structured logging» (regola «Never log secrets…»); `ecc-security-reviewer.md` (segreti nei log) |
| 09 | catalogo 2.3; `agent-skills-api-and-interface-design.SKILL.md`, «Verification» |
| 10 | idem, «Pagination» |
| 11 | idem, «Predictable Naming» |
| 12 | spec del nucleo 8.5; progetto di B 12; `wrangler-kv.md`, `wrangler-d1.md`, `wrangler-r2.md`, `wrangler-v3-to-v4.md` |

Marcatori e pattern (commenti del frammento): `workers-bindings.md` (`cloudflare:workers`), `workers-python.md`, `kv-get-started.md`/`d1-get-started.md` (`ExportedHandler<`), pagine di Express, Fastify, Hono, FastAPI, Flask, Deno, Node, `vercel-functions.md`, `pages-functions-get-started.md`. `export function POST(` ha una pagina (`vercel-functions.md`, estratto `export async function POST(`) solo per la forma async: la forma non-async lo giudica il Task 4 (carry).

## Scostamenti dal piano
- `--local` non compare in R-BACKEND-12: `test_options_exist_in_parser` (tests/test_skill_contract.py) lo legge come opzione sconosciuta della CLI, quindi la regola dice «l'opzione della modalità locale» (indicazione di carry).
- Il test della `Fonte:` per i revisori ECC cita `everything-claude-code 1.4.1 (Affaan Mustafa, MIT)` nella forma di `rules-base`.
- Ordine TDD: ho scritto skill e frammento prima del test e poi ho mostrato il RED spostando temporaneamente i due file (22 errori su 22), poi rimessi: GREEN dopo una correzione di una regex del test sulla sezione Fonti (i punti di «0.6.9»).

## Test
- RED: `python3 -B -m unittest tests.test_rules_backend` senza skill e frammento: `Ran 22 tests, FAILED (errors=22)`.
- GREEN mirati: `python3 -B -m unittest tests.test_rules_backend tests.test_rules_ai tests.test_rules_infra tests.test_fragments tests.test_docs tests.test_init tests.test_skill_contract tests.test_manifest` -> `Ran 327 tests, OK (skipped=4)`.
- `claude plugin validate --strict .` -> Validation passed.
- `test_real_markers_not_in_tollgate_bin`: 0 marcatori in `bin/`.

- Suite completa: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> python3.11: 3707 test OK (skipped=7); python3.13: 3707 test OK (skipped=5); nessun «unclosed". Commit sotto.

## Fix round 1
- `Fonte:` di R-BACKEND-05 e R-BACKEND-09 dichiarano «scelta nostra» per le parti senza fonte (il task chiede il cambiamento; un caso d'errore per ogni input e risorsa). Regole invariate.
- Nuovo test `test_extensions_of_the_sources_are_declared_as_our_choice` (R-BACKEND-02, 05, 09); nessun test indebolito.
- Mirati: `python3 -B -m unittest tests.test_rules_backend tests.test_docs tests.test_fragments` -> 56 OK.
- Suite: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> 3708 test OK (python3.11 skipped=7, python3.13 skipped=5), exit 0.
