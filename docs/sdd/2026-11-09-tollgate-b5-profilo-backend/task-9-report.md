# Task 9: report dell'implementatore

Solo documenti. Base `09396ba`, ramo `b5-profilo-backend`. Nessun codice, nessun test cambiato. Fatti presi da `bin/tollgate_analysis/bash.py`, `bin/tollgate_core/fragments.py`, `bin/tollgate_flow/init.py`, `templates/profiles/backend.toml`, `skills/rules-backend/SKILL.md`, `agents/*-backend.md`, `docs/profili/backend.md`, `docs/profili/verifiche/backend-fonti.md` e `docs/verifiche/2026-11-09-b5-prova-flusso.md`.

## Sezioni cambiate

### `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 32)
- Intestazione: «Revisione: **32**» con prova reale, approvazione del 10/11/2026 e fatti verificati; la 31 diventa «Revisione 31».
- 6.3: task misti con `backend` e `infra` (sezione del test), file di `infra` dentro una cartella di `backend`, `server/ai/`; derivazione degli agenti «anche `backend`»; frase di `implementer-infra` aggiornata (le scritture di KV, D1 e R2 ora sono coperte, test `test_real_infra_agent_names_uncovered_commands`); `AREAS` a tre aree; voce nuova «Gli agenti di `backend`» (skill precaricate, sezione «Area», L0, `rules-performance` fuori da B).
- 7.1: `tollgate:reviewer-backend` in `READONLY_TYPES`. 7.3: `reviewer-backend` con `WebFetch`. 11.4: `readonly_agents` con il nuovo tipo.
- 8.5: i due buchi di B4 (scritture di KV, D1, R2 e script dei monorepo) marcati come chiusi dalla rev 32; blocco nuovo «Rev 32» con `ACCOUNT_GROUPS`, `FLAG_EFFECTS` (`unless_local`, `with_remote`), `_flag_present`, ripiego `text_effect`, scelta dell'utente contro «scelta nostra, compatibile» (decisioni 6, D6), `script_name` e `SCRIPT_VALUE_OPTIONS` (decisione 7), costo (gruppi nudi e `--help`, D8; lanciatori; `pnpm -F web deploy`), buchi (altri gruppi, opzioni globali, `dev --remote`, `npm run <script> -- <comando>`, `--local=0`/`--local=FALSE` su Wrangler 3 D9, orchestratori), e la differenza con la pagina approvata di `infra`.
- 8.7: `dod` e `commands` vuoti anche per `backend` (decisione 8), comandi aggiunti a mano senza veto.
- 11.2: voce «Esclusione per frammento» (`concrete_for(..., exclude=)`, `_is_detectable`, `_drift`, solo la proposta, test).
- 11.4: «oggi `ai.toml`, `infra.toml` e `backend.toml`»; chiave `exclude` nella descrizione di `[detect]`; frase su `infra` corretta (non più «Restano fuori `workers/**`», `workers/**` non è un pattern di nessun profilo, D1); paragrafo «Il frammento di `backend`» (6 pattern, 23 marcatori con le due virgolette, `export function POST(` uscito, costo, 12 regole 10 `[blocca]`, 51 `ok` e 3 `no`) e paragrafo «`[detect] exclude`» (forma, errori, `Fragment.exclude`, solo la proposta e non il runtime, monorepo).
- 16: blocco «Verificato in B5, il 9-10/11/2026» (Wrangler 4 locale, KV/D1/R2, altri gruppi, punto d'ingresso dei Worker, binding e segreti, Pages e Vercel, Supabase, righe dei framework, cartelle sul disco, prova reale con esito, costo, limiti, token); «Ancora da verificare dopo … B5» con `R-BACKEND-…` dal vivo, rami delle regole sul report e domanda di `WebFetch` per `reviewer-backend`.
- 20: riga 32.

### `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md` (catalogo)
Intestazione (B5), principio 6 (`backend` con `skills: [rules-base, rules-backend]`), intro della sezione 2 (marcatori ed esclusione di `backend`), riga `backend` della sezione 2 (6 pattern veri, senza `**/services/**`, con `backend/**` e `functions/**`, marcatori, esclusione), riga 41 di `infra` (`workers/**` corretta), 2.1 riga `backend` (`rules-backend` precaricata, skill in «Dove informarsi», `rules-performance` fuori da B), 2.2 (`reviewer-backend` con `WebFetch`), 2.3 riga `backend` del `dod` (vuoto, decisione 8), 4 (fonti vere di `rules-backend`), 6 (B5).

### `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`
Riga «Avanzamento» con B5.

### `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`
- Testata: spec alla revisione 32, catalogo aggiornato da B5; Stato (10 novembre 2026) con B5.
- Sezione 2: riga B5 con stato e scostamenti.
- Sezione 3: riga B5 → B6-B7 (`Fragment.exclude`, `concrete_for(..., exclude=)`, `FLAG_EFFECTS`, `AREAS` con `backend`, test da copiare).
- Sezione 9: rinvii di B4 chiusi da B5 (scritture di Wrangler, script nei monorepo con i buchi rimasti, `togli-pagine` per `Bash`, rinomina `test_real_` con i nomi di tutti gli 11 test, `.gitignore` di `spikes/b4/flow/` scritto come chiuso da B4, pagina approvata di `infra` che invecchia); voci «da B3» aggiornate («aperto per B6-B7», agenti nuovi, test da copiare); blocco nuovo «A B6-B8, da B5» con i rinvii delle decisioni 3, 6, 7, di 4 e le righe `minor (deferred)` dei Task 1, 2, 3-6 e 7.
- Sezioni 11 e 13: i nomi dei test rinominati con `test_real_` (11 test, nelle righe di B3 e B4 che li citano).
- Sezione 14 «Prove di B5»: ogni riga della tabella «Copertura» con test o evidenza (24 righe), più «Prove oltre la tabella».

## Scostamenti e dubbi
- Nessuno scostamento dal brief. Il numero dei test della suite nella testata (3755, 3.11 e 3.13) viene dal report del Task 7 (il Task 8 non ha toccato `tests/`): se la corsa dice altro, correggere la riga di Stato.
- Minori del ledger: ho messo nel blocco «A B6-B8, da B5» quelli dei Task 1, 2, 3-6 (per chi copia test e pagina) e 7. Non ho messo quelli del Task 8 (riguardano il rapporto) né i due del Task 6 sul testo di `agents/implementer-backend.md` (`psql`, `kv namespace` e `r2 bucket` presentati come sempre fermati): riguardano B5, li tria la revisione finale.
- Verifica prima della suite: `tests.test_docs`, `tests.test_specdoc`, `tests.test_rules_backend`, `tests.test_b1_scripts` verdi (143 test, skipped=3).

## Suite
`PYTHONWARNINGS=error::ResourceWarning tests/run`, uscita 0: Python 3.11.16, 3755 test OK (skipped=10); Python 3.13.5, 3755 test OK (skipped=8). Nessun «unclosed» nell'uscita (`task-9-suite.txt`). Il numero 3755 nella testata del piano principale è confermato; ho aggiunto gli skipped. Commit `6beebe8`.

## Fix round 1
- I-1: sezione 9 del piano principale, nuovo rinvio aperto «R-INFRA-06 ambigua» (M-4 di B4), nel blocco «A B6-B8, da B5».
- M-1: riga B4 della sezione 2: `workers/**` non è un pattern né di `infra` né di `backend`.
- M-2: spec 8.5 e sezione 9 (due punti): `yarn workspaces foreach` e `pnpm turbo run` letti come `workspaces`/`turbo`; `turbo run`, `nx run`, `lerna run` non sono gestori di pacchetti e `script_name` non li guarda.
- Comando: `PYTHONWARNINGS=error::ResourceWarning tests/run` (uscita in `task-9-suite-2.txt`): exit 0, 3.11 3755 OK (skipped=10), 3.13 3755 OK (skipped=8), nessun «unclosed».
