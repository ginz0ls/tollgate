# Revisione Task 2 (B5): scritture di Wrangler su KV, D1, R2; script dei monorepo

Commit esaminato: dcae551 (`bin/tollgate_analysis/bash.py`, `tests/test_bash.py`). Sola lettura. Eseguiti solo `python3 -B -m unittest tests.test_bash` (89 OK) e sonde di testo con `bash.parse`/`effect_reason`/`text_effect`/`script_name` (nessun programma lanciato).

## Aderenza

- ✅ Decisione 6, ACCOUNT_GROUPS: tre prefissi, lettura = primo token `list|get|info` o sotto-voce + secondo token di lettura; `r2 bucket create list` resta effetto; D1 `create`, `delete`, `time-travel restore` in `_DEFAULT_EFFECTS` (`bash.py:1003-1005`, `1167-1180`).
- ✅ FLAG_EFFECTS: 10 voci `unless_local` (incluse le forme con i due punti) e 2 `with_remote` (`bash.py:1011-1023`); `_flag_present` unica, usata dai due modi (`bash.py:1162`); motivo con prefisso e opzione ("... (senza --local)", "... con --remote").
- ✅ Stesso punto di `effect_reason`, su argv e su ogni candidato di `launcher_candidates` (`bash.py:1239-1243`). Sonde: `npx`, `npx --yes`, `npx wrangler@latest`, `bunx`, `pnpm`/`yarn`/`pnpm exec`, `npm exec --`, `npx -c`, `npm exec -c`, `bash -c`, `sh -c`, `sudo`, `env`, assegnazioni `FOO=1`, `./node_modules/.bin/wrangler`: tutti con veto.
- ✅ `text_effect`: regex per i prefissi di ACCOUNT_GROUPS, `unless_local` (solo prefisso) e `with_remote` (prefisso + `--remote|--preview` nello stesso comando, `[^;&|]*`) (`bash.py:1327-1334`). Sonda: `x; wrangler d1 execute DB --command "a" ; wrangler d1 list --remote` dà `None` (il `;` ferma la regex).
- ✅ Decisione 7: `SCRIPT_VALUE_OPTIONS` e `script_name` identici al testo (eccezione `pnpm -w`, `workspace` solo per yarn, `run`/`run-script`). Confronto esaustivo su 4 gestori x sequenze fino a 4 token di un vocabolario di 17 token (`run`, `run-script`, `workspace`, `-w`, `--filter`, `-F`, `-C`, `--`, `exec`, ...): **0 casi** in cui `main` dava lo script `deploy`/`release` e ora no. I casi guadagnati sono tutti nella forma "opzioni del gestore poi comando" della decisione 7.
- ✅ Sonde sui nomi comuni (`docs`, `config`, `run`, `local`, `web`, `api`) in ogni posizione: `npm run docs`, `pnpm --filter docs build`, `pnpm -C config build`, `yarn workspace docs build`, `yarn run local`, `bun run web`, `npm run --workspace docs test`, `npm --prefix deploy run build`, `npm run build --prefix deploy`, `npm test -- --workspace deploy`, `npx run deploy`, `npx deploy`, `pnpm dlx deploy`, `npm install deploy`, `npm view deploy`, `npm exec -w web deploy`: tutti `None`. `--local`/`--remote`/`--preview` come valori tra virgolette (`--command "select --remote"`) non contano (token unico).
- ✅ `[external_effects] allow` e `commands` sono valutati prima di tutto (invariati); `project_scripts` invariato per `npm run deploy`; le guardie di B4 in `tests/test_bash.py` non sono toccate (il diff dei test è solo di aggiunte: 95 inserimenti, 0 cancellazioni).
- ✅ D5: nelle righe aggiunte di `bin/` nessun marcatore della decisione 3, nessun "Supabase", nessun messaggio con "tollgate init/approve".
- ✅ Carry: `_flag_present` spegne solo il valore esatto `false` (sonde: `--remote=False`, `=FALSE`, `=0` contano come presenti, lato sicuro per `with_remote`; per `unless_local` un `--local=False` non rende il comando locale, cioè resta veto). Forme con i due punti presenti.
- ✅ Report: le affermazioni verificabili (voci, funzioni, ordine delle tabelle prima di `_TEXT_EFFECTS`, nessuno scostamento) combaciano col diff. I conteggi RED/GREEN e della suite completa non sono ricontrollati (non rilanciata); `tests.test_bash` è verde.
- ⚠️ I fatti sulle opzioni di KV/D1/R2 (Step 0 del Task 3) e l'esistenza di alias corti (`-l`, `-r`) non sono verificabili dal diff; `-l` oggi non spegne il veto (lato sicuro).

## Punti di forza

- Una sola definizione di "opzione presente" e una sola funzione per i due modi; le tabelle sono dati, `effect_reason` cambia di sole 3 righe.
- Le regex di `text_effect` si costruiscono dalle tabelle, nessun elenco duplicato (`bash.py:1327-1334`).
- Lettura per esclusione in ACCOUNT_GROUPS: una sotto-voce nuova di Wrangler è un effetto da sola (fail-closed).
- `script_name` è una funzione sola, con `skip_options` annidata, senza regressioni misurate rispetto a `main`.
- I test coprono bene i casi del brief (tre elenchi di sicuri/non sicuri, lanciatori, motivo, `text_effect`, `script_name`, monorepo con casi negativi).

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

1. `bash.py:1169-1172` (`_account_group_read`): un comando del gruppo senza sotto-voce o con sola opzione di aiuto (`wrangler kv namespace --help`, `wrangler r2 bucket`, `wrangler r2 bucket --help`) è un effetto, mentre su `main` non lo era. La decisione 6 lo prevede alla lettera (il primo token deve essere `list|get|info`), quindi è nel perimetro, ma è un falso positivo gratuito di sola lettura. Se si vuole: trattare come lettura `rest == []` o `rest[0] in ("--help", "-h")`; altrimenti scriverlo tra i costi della decisione 6 in Task 9.
2. `tests/test_bash.py:~326-336` (`test_monorepo_deploy_scripts`): mancano i casi che la decisione 7 dichiara coperti ma nessun test esercita: `pnpm -w release` (eccezione `-w`), `npm run-script deploy`, i valori di `-C`/`--dir`/`--prefix`/`--cwd` (es. `npm --prefix deploy run build` deve restare `None`), e un nome di workspace uguale a `deploy` (`yarn workspace deploy build` `None`). Le sonde passano, ma un refactor di `script_name` potrebbe romperli senza che un test se ne accorga.
3. `tests/test_bash.py`: nessun test per `allow`/`commands` con le voci nuove (es. `allow=["wrangler kv key put K V"]` dà `None`). Funziona per costruzione (controllo precedente a tutto), ma la richiesta del controller di verificarlo resta solo sulle guardie di B4 con `deploy`.
4. `tests/test_bash.py` (`test_text_effect_flag_entries`): non copre `wrangler kv:namespace` né il ramo `--remote=...` di `with_remote` nel ripiego (`text_effect("x; wrangler d1 execute DB --remote=false --file y")` dà un effetto, scelta di sicurezza ma non asserita).
5. Costo già scritto, confermato dalle sonde (non un difetto): le opzioni globali prima del sottocomando (`wrangler --env prod kv key put K V`, `wrangler -c w.toml kv key put K V`) passano senza veto; idem `--loglevel info run deploy`; `yarn workspaces foreach run deploy` (non `workspace`) non è riconosciuto.

## Valutazione

**Qualità del task:** Approvato

**Motivo:** requisiti delle decisioni 6 e 7 e delle decisioni del controller rispettati; nessuna regressione sul confronto esaustivo degli script rispetto a `main`, nessun nuovo effetto spurio sui nomi comuni di cartelle/pacchetti, nessuna scrittura remota senza veto nelle forme dietro lanciatori e `-c`. Restano solo minori su copertura di test e un falso positivo di sola lettura (`--help`).
