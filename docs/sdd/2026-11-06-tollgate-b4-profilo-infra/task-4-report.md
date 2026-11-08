# Task 4: report dell'implementatore

## Cosa ho fatto
- `tests/test_rules_ai.py`: `rules(text, area="ai")` costruisce la regex da `area.upper()`; i test di `ai` non cambiano.
- `tests/test_rules_infra.py` (nuovo, `RulesInfraTest`, 20 test): tutti quelli del brief; `test_user_choices_covered` per id con le sezioni `progetto di B, sezione 3.4` e `sezione 11` per R-INFRA-01.
- `tests/test_fragments.py`: `test_real_fragments_load` legge anche `infra` (agente, nessun `detect`).
- `skills/rules-infra/SKILL.md` (79 righe, senza `approved`), `templates/profiles/infra.toml` (14 pattern nell'ordine di D4, un commento per gruppo con la pagina; `commands = {}`, `dod = []`, nessun `[detect]`), sezione `### \`/tollgate:rules-infra\`` in `docs/uso/comandi.md` (dice che le regole sono una bozza non approvata: il Task 6 la aggiorna con la data).

## TDD
- RED: `python3 -B -m unittest tests.test_rules_infra` -> `Ran 20 tests`, `FAILED (errors=20)` (`FileNotFoundError` su `skills/rules-infra/SKILL.md`).
- RED docs: con la skill e il frammento presenti, `tests.test_docs` falliva solo su `test_every_skill_documented` (skill `rules-infra`, intestazione mancante).
- GREEN: `python3 -B -m unittest tests.test_rules_infra tests.test_rules_ai tests.test_fragments tests.test_docs tests.test_init` -> `Ran 207 tests ... OK (skipped=2)`.
- `claude plugin validate --strict .` -> `Validation passed`, uscita 0 (solo un avviso sul README, che non riguarda il task).
- Suite completa: vedi in fondo.

## Regole: fonte e scostamenti dalla bozza
Le fonti sono le copie in `fonti/infra/`; i fatti sono riscritti con parole mie, i titoli di sezione stanno tra « » (al più 4 parole, nessuna frase copiata).

| Id | Fonte usata | Rispetto alla bozza |
|---|---|---|
| R-INFRA-01 | progetto di B 3.4 e 11 | Detta «versionati» (carry D16: `.vercel/` non è un file del repo).. |
| R-INFRA-02 | progetto 3.4; skill `wrangler` (Apache-2.0); pagine dei comandi di Wrangler e `vercel build` | Invariata. Per `docker` e `docker compose` non c'è una pagina di comandi nelle copie: regge sulla scelta del progetto 3.4. |
| R-INFRA-03 | progetto 3.4; pagine di configurazione di Vercel e Wrangler; skill `wrangler` | Invariata. |
| R-INFRA-04 | pagina della configurazione di Vercel («File-based configuration») e pagina di `vercel.ts` («Requirements») | Invariata; «cartella» è la traduzione operativa di «per progetto» (la pagina non parla di cartelle). |
| R-INFRA-05 | pagina dei segreti di Cloudflare; pagina `vercel.json` (`env`, `build.env`: sconsigliati); pagina delle variabili di Vercel; pagine dei segreti di build e delle buone pratiche di Docker (`ENV`) | **Tolto «né in un file compose»**: nessuna copia dice nulla sui segreti in compose, e il brief vieta obblighi senza fonte. Aggiunto `env`/`build.env` di Vercel, che la pagina `vercel.json` sconsiglia e che sono nei file versionati. |
| R-INFRA-06 | pagina dei segreti di Cloudflare (`.dev.vars*`, `.env*`, `.gitignore`); pagina delle variabili di Vercel | **Dubbio**: la pagina di Vercel non dice di non versionare `.env.local`/`.env` (lo nota il controller); la regola poggia sulla pagina di Cloudflare, e la riga `Fonte:` lo dice. L'eccezione `.example`/`.sample`/`.template` non ha una pagina: è dichiarata «nostra scelta» nella `Fonte:` (voluta da `test_secret_rules_allow_example_files` e da review-focus 4). |
| R-INFRA-07 | pagina della configurazione di Wrangler (`wrangler.jsonc` per i nuovi progetti; `compatibility_date` «required» nella tabella) e pagina delle date | **Diviso**: qui resta la sola parte sul diff (`wrangler.jsonc` e data del giorno in cui nasce la configurazione). Non bloccante; la `Fonte:` dice che la tabella segna la chiave richiesta mentre una data vecchia resta valida (carry). «Recente» è diventato «la data del giorno», come dice la pagina. |
| R-INFRA-08 (nuova) | pagina delle date di compatibilità | **Divisa da R-INFRA-07**: la clausola «il report dice di aver letto i flag quando il diff cambia la data» si giudica sul report, non sul diff; in una regola sola l'oggetto del giudizio sarebbe stato ambiguo. Non bloccante, `report`. |
| R-INFRA-09 (era 08) | buone pratiche Docker («Pin base image versions») | Invariata, rinumerata. |
| R-INFRA-10 (era 09) | buone pratiche Docker (`USER`, `.dockerignore`); pagina del contesto di build | `.dockerignore` precisato come la pagina del contesto: nella radice del context, oppure `<nome del Dockerfile>.dockerignore` accanto al Dockerfile (carry). |
| R-INFRA-11 (era 10) | buone pratiche Docker («Use multi-stage builds») | Invariata, rinumerata. |
| R-INFRA-12 (era 11) | spec del nucleo 8.5; pagine di `wrangler deploy`, di Pages, di `vercel build`, delle variabili di Vercel (`env add`) | Rinumerata; nell'ordine del file sta in fondo a «Mentre lavori», come nella bozza. |

**Rinumerazione:** la divisione di R-INFRA-07 sposta di uno le regole Docker e porta la regola «non pubblicare» da R-INFRA-11 a R-INFRA-12 (la decisione 14 e gli appunti del controller la chiamano R-INFRA-11). Gli id non sono ancora approvati e i test dei Task 7 estraggono gli id con la regex, ma i brief dei Task 5-9 e la revisione 31 vanno riletti: nel `grep` dei brief ho trovato solo `R-INFRA-01`, `02`, `03` e `07` citati con un numero (R-INFRA-07 resta quella sulla `compatibility_date`). Se il controller preferisce la numerazione della bozza, basta unire 07 e 08 e riportare 12 a 11 (due righe e `test_rule_ids_consecutive` si adegua da solo).

Ordine nella skill: «Prima di scrivere» 01-03, «Mentre lavori» 04-12 (R-INFRA-12 è in fondo a «Mentre lavori»). Bloccanti: 01-06 e 12; non bloccanti: 07-11. Le bloccanti sono tutte su `diff` (04-06) o `report` (01-03, 12).

## Frammento
14 pattern nell'ordine di D4. Fonti nei commenti: `vercel.*` (pagina della configurazione), `wrangler.*` (pagina della configurazione), `Dockerfile*` (pagina del Dockerfile: il `*` copre un suffisso dopo `Dockerfile`; la pagina nomina `<x>.Dockerfile`, che non è coperta: lo dirà la pagina del Task 5), `.dockerignore` (pagina del contesto), quattro nomi compose (pagina del modello di Compose) e `compose.override.yaml` (pagina del merge). `test_fragment_matches_decisions` ha l'elenco dei 14.

## Verifiche di trappola (D15)
La sezione di `comandi.md` non contiene «solo l'utente» né «Argomenti:». La skill non nomina `bin/tollgate`, né il programma nudo, né sigle come `P3`; non nomina `workers-best-practices` (decisione 8). Nessun valore di chiavi, nessun nome di progetto privato, nessun comando di servizio lanciato.

## Per il Task 5/6
- La sezione di `comandi.md` dice «bozza non approvata»: il Task 6 la riscrive con la data come per `rules-ai`.
- `init` non propone `infra` finché `approved` manca (`load_approved`); `test_real_trees_light_no_profile` resta verde.

## Suite completa
- Primo giro: `python3.11` rosso solo su `tests.test_skill_contract.test_options_exist_in_parser` (skill `rules-infra`): `test_skill_contract` controlla ogni `--opzione` scritta in una skill contro il parser di tollgate, e la skill nominava `--secret`, `--mount`, `--dry-run`, `--prod`. Corretto nella skill (le opzioni dei servizi sono descritte a parole: opzione `secret`, montaggio di tipo `secret`, modalità dry-run, pubblicazione in produzione), non nel test.
- Secondo giro, dopo la correzione: `PYTHONWARNINGS=error::ResourceWarning tests/run` -> python3.11: `Ran 3626 tests ... OK (skipped=5)`; python3 (3.13.5): `Ran 3626 tests ... OK (skipped=3)`. Nessun fallimento di `test_db_restore_interactive_eof_and_ctrl_c`. Uscita in `task-4-suite.log` del workspace.
- Nota per i Task successivi: nessuna skill di tollgate può contenere una `--opzione` che il parser non conosce.
