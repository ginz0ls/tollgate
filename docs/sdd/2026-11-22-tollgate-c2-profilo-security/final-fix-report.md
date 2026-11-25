# Giro di correzione dopo la revisione finale: report

## Mano Fable

Fable, 2026-11-24, sopra il commit `4cf2b97`. Toccate solo `docs/profili/security.md` e `docs/profili/database.md` (4 righe ciascuna: una frase e una nota di storia). Nessun commit, nessun `git add`, nessuna suite completa, nessun subagente, nessuna rete. Nessun test toccato.

### Cosa ho controllato sul codice

- **U1.** `bin/tollgate_flow/init.py:387-394`: il percorso esatto di un file trovato per contenuto si propone solo se il frammento non lo accende già con una sua forma (`found = … - set(lighting)`). `templates/profiles/frontend.toml:21-26` ha `**/*.tsx`, `**/*.jsx`, `**/*.vue`, `**/*.svelte`: per quei file `frontend` non propone il percorso esatto, e la forma per estensione perde contro la cartella `auth/` di `security`. È il caso X23 della sezione 5 di `final-review.md`. Per un `.ts` (S58) `frontend` non ha una forma, quindi propone il percorso esatto e vince.
- **U2.** `bin/tollgate_core/runner.py:47-58` (`gate_commands`: i comandi di `[commands] gate` più quelli della chiave `gate` dei profili attivi, che è un elenco di nomi di `commands`); `bin/tollgate_core/verify.py:88` (`verify` esegue `gate_commands` più `extra`); `bin/tollgate_flow/finishcheck.py:118-121` e `bin/tollgate_flow/openpr.py:326` (`dod_commands` entra solo lì, come `extra`); `runner.py:60-61` (un comando che è già nel gate non si ripete come `dod`); `bin/tollgate_gate/run.py:114` (il gate della PR usa `gate_commands`).

### U1, `docs/profili/security.md`, punto 3 di «Cosa hai deciso»

Vecchio:
> Lo stesso per un file riconosciuto da `frontend` (S58) o da `database` (S65).

Nuovo:
> Lo stesso per un file `.ts` riconosciuto da `frontend` (S58) o per un file riconosciuto da `database` (S65). Fa eccezione un file `.tsx` (o `.jsx`, `.vue`, `.svelte`) dentro `auth/`: anche quando `frontend` lo riconosce dalle sue librerie va agli agenti di sicurezza, come al punto 2, perché `frontend` quei file li prende già per l'estensione e non ne propone il percorso esatto.

Le righe `Proposta:` e «Hai approvato la proposta.» del punto non sono cambiate. Nota di storia, in un paragrafo a sé sotto «Approvata dall'utente il 2026-11-23.»:
> Il 2026-11-24, con il tuo OK, è stata precisata una frase del punto 3 (i file `.tsx` dentro `auth/`).

### U2, `docs/profili/database.md`, paragrafo «Attenzione» sotto l'esempio di `dod`

Vecchio:
> … le prove del database passano da `verify` (i comandi che metti nel `dod`).

Nuovo:
> … le prove del database passano da `verify`, che esegue i controlli del progetto e i comandi che scrivi nella riga `gate` del blocco del profilo. I comandi di `dod` girano solo a fine lavoro: se vuoi un comando anche durante il task, aggiungilo anche a `gate` (per esempio `gate = ["db_test"]`); i comandi di `gate` girano anche nel controllo prima della pull request.

Nota di storia, in un paragrafo a sé sotto «Approvata dall'utente il 2026-11-17.»:
> Il 2026-11-24, con il tuo OK, è stata corretta una frase su `verify` e `dod`.

Nient'altro delle due pagine è cambiato (`git diff --stat`: 4 righe per file, 3 aggiunte e 1 tolta ciascuno).

### Esito dei test

`python3 -B -m unittest tests.test_rules_security tests.test_rules_database tests.test_docs`:

```
----------------------------------------------------------------------
Ran 104 tests in 0.278s

OK (skipped=3)
```

### Test da adeguare

Nessuno: nessun test fissa le due frasi vecchie, e i tre file restano verdi senza toccarli. Per la mano opus: se vuole tenere ferma la correzione di U2 anche nella pagina, la parola da cercare è `` `gate` `` nel paragrafo «Attenzione» di `docs/profili/database.md`.

### Dubbi

1. **U2, la coda «i comandi di `gate` girano anche nel controllo prima della pull request».** Non era nel brief: l'ho aggiunta perché è vera (`bin/tollgate_gate/run.py:114`) ed è un costo per chi segue il consiglio (un comando che vuole lo stack locale di Supabase finirebbe anche nel gate della PR). Se è di troppo, si toglie da «; i comandi di `gate` …» in poi senza altri effetti. La mano opus può usare la stessa avvertenza nelle frasi di F1.
2. **U2, «i controlli del progetto»** al posto di «il gate del progetto»: nella pagina «gate» è già usato per il controllo della PR, e la riga `gate` del profilo è spiegata con l'esempio; così le due cose non si confondono.
3. **U1:** l'eccezione nomina le quattro estensioni che `frontend` copre e che il rilevamento per contenuto guarda (`.tsx`, `.jsx`, `.vue`, `.svelte`), come il caso X23.

## Mano opus

Opus, 2026-11-24, sopra `4cf2b97` e le modifiche della mano Fable alle due pagine (non toccate, solo `git add`).

### F1 e U2 (parte opus): il canale di `verify`

Controllo sul codice: `bin/tollgate_core/verify.py:88` (`gate = gate_commands(cfg, files) + extra`); `bin/tollgate_core/runner.py:47-57` (`gate_commands`: `[commands] gate` più la chiave `gate` dei profili attivi); `dod_commands` entra solo come `extra` in `bin/tollgate_flow/finishcheck.py:118-119` e `bin/tollgate_flow/openpr.py:326-327`; `bin/tollgate_gate/run.py:114` usa `gate_commands`; `config.PROFILE_DEFAULTS` ha `gate = []` (il frammento di `security` non la dichiara). La formula della revisione è vera.

Testo nuovo, uguale nei due agenti (`agents/implementer-security.md:53`, `agents/implementer-database.md:53`, solo quella frase): «le lanci con `<programma> verify`, che esegue il gate del progetto e i comandi che l'utente ha messo nel `gate` del profilo; i comandi di `dod` girano a fine lavoro, con `finish check`: li esegue tollgate, non tu.» La parola `dod` resta (la vuole `test_real_security_agent_names_forbidden_tools`).
- `docs/uso/comandi.md:34`, le due frasi di `database` e `security`: «le prove … passano da `verify`, che esegue il gate del progetto e i comandi che metti nel `gate` del profilo (quelli di `dod` girano solo a fine lavoro, con `finish check`: un comando che serve anche durante il task va messo anche nel `gate`)».
- Spec 6.3, voce di `database` (frase del costo: «lo fa `verify` se l'utente lo mette nel `gate` del profilo», con il perché nel codice e la storia); voce di `security` («passano da `<programma> verify`, che esegue il gate del progetto e i comandi che l'utente mette nel `gate` del profilo (i comandi di `dod` … girano solo a fine lavoro con `finish check` …)»); 8.7, paragrafo di `security` (la frase sul «canale» sostituita: `dod` solo a `finish check` e `open-pr`, `gate = ["denied"]` per il task, che gira anche nel gate della PR). Riga 37 della sezione 20: una frase sulle correzioni della revisione finale.
- Piano principale, sezione 8, voce «un limite da portare all'utente»: `verify` con il `gate`, `dod` solo a fine lavoro; «con `gate` e `dod` di `security` vuoti, nessun test del profilo gira durante il task finché l'utente non aggiunge un comando anche al `gate`».
- Test nuovo `tests/test_manifest.py` `test_real_verify_channel_is_the_gate`: nelle sezioni «Area» dei due implementatori «nel `gate` del profilo» e «finish check» ci sono e la frase vecchia no; in `comandi.md` la frase vecchia non c'è e «nel `gate` del profilo» sì; in `docs/profili/database.md` non c'è «(i comandi che metti nel `dod`)» e c'è «nella riga `gate` del blocco del profilo» (la frase della mano Fable).
- RED: `python3 -B -m unittest tests.test_manifest.ManifestTest.test_real_verify_channel_is_the_gate` → `AssertionError: 'nel `gate` del profilo' not found in "Questo task tocca la sicurezza: …" : security`, `FAILED (failures=1)`. GREEN dopo la correzione: `tests.test_manifest` → `Ran 67 tests … OK`.

### F2: `test_page_has_no_private_data`

`tests/test_rules_security.py`: costante `GENERIC_NAMES = {"root", "user", "runner", "ubuntu", "dev", "test", "admin", "github"}`; il confronto del nome utente e dell'host salta i nomi generici (`secret.lower() not in GENERIC_NAMES`); docstring aggiornata; il messaggio resta senza il valore; `/home/` e le forme di token restano controllati.
- RED: `LOGNAME=root python3 -B -m unittest tests.test_rules_security -k test_page_has_no_private_data` → `FAILED (failures=1)`.
- GREEN: lo stesso comando → `OK`; `tests.test_rules_security` intero con e senza `LOGNAME=root` → `OK (skipped=3)`.

### F3: S72 e S73

I due casi danno ciò che dice la revisione (sezione 5, X20/X24 e X23): nessun caso forzato.
- `tests/test_init.py`, `SecurityPrecedenceTest`: `test_real_precedence_s72` (X20: `src/auth/llm/middleware.ts` → `ai`; X24: `src/auth/routes/middleware.ts` → `backend`; proposte `ai: src/auth/llm/**` e `backend: src/auth/routes/**` con `security: src/auth/**`; `check_active` con `security` attivo) e `test_real_precedence_s73` (`src/auth/Guard.tsx` trovato da `frontend` → `security`; proposta `frontend: **/*.tsx`, `security: src/auth/**`; `check_active` con `frontend` e `security`).
- RED/GREEN: i test fissano un comportamento che c'era già (il codice non cambia); al primo lancio sono verdi: `tests.test_init.SecurityPrecedenceTest` → `Ran 73 tests … OK`. Il «rosso» era la tabella della spec senza i due casi.
- Spec 6.3: righe S72 e S73 dopo S71; il paragrafo d'apertura dice `s1` … `s73` (S72 e S73 dalla revisione finale); «In breve»: il percorso esatto vince «fuori da una cartella del profilo: dentro `auth/` … vince la cartella più profonda dell'altro profilo (S72)», e le cartelle perdono contro un percorso esatto «di un file che l'altro profilo non copre già con un'estensione … (S73; S58 vale per un `.ts`)». Aggiornati «S1-S73» nell'intestazione della spec, nel catalogo (sezione 6) e nella riga C2 del piano principale; nella riga 37 «S1-S71 … più S72 e S73 dalla revisione finale».

### Triage 1: `docs/uso/comandi.md`, «Modelli degli agenti»

«Se `availableModels` esclude il modello chiesto, …, con un avviso nelle sessioni interattive; … Con `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` Claude Code ignora sia la riga `model:` degli agenti sia il `model` della chiamata, e la scelta qui sopra non vale.» (tolti «solo» e la frase su cosa resta).

### Triage 4: `SONNET_PIN`

`tests/test_manifest.py:22-24`: `model: ['"]?(sonnet|haiku)|--model[ =]['"]?(sonnet|haiku)|MODEL=['"]?(sonnet|haiku|claude-sonnet|claude-haiku)|:-['"]?(sonnet|haiku)`. Test nuovo `test_sonnet_pin_sees_every_form` (nove forme che fissano, tre che non fissano: `model: opus`, `MODEL="claude-opus-5-5"`, l'indirizzo `…/models/sonnet-5-5/…`).
- RED: 5 sottotest rossi (`--model=haiku`, `MODEL="sonnet"`, `MODEL='claude-haiku-5-5'`, `MODEL="claude-sonnet-5-5"`, `--model "sonnet"`), `FAILED (failures=5)`.
- GREEN: `tests.test_manifest` → `OK`; `test_no_sonnet_in_skills_and_scripts` resta verde sugli script veri.

### Triage 32: `test_flow_case_l2_steps_refused_for_other_cases`

`tests/test_b1_scripts.py`: per il caso `b1` (`passo3`, `libero`) un `subTest` con `assertNotEqual(r.returncode, 0)` prima del messaggio. Lo script esce già con un codice diverso da 0, quindi l'asserzione è verde al primo lancio (nessun RED senza una mutazione dello script, che non ho fatto): `-k test_flow_case_l2_steps_refused_for_other_cases` → `OK`.

### n1-n3: `docs/verifiche/2026-11-22-c2-prova-flusso.md`

- n1 (riga 80): «nove dei quali senza rilievi sopra `minor`».
- n2 (riga 153): «lo chiede `agents/implementer-security.md` (passo 2 di «Il lavoro», il TDD)», senza numero di riga.
- n3 (riga 142): «`audit prepare` ha rifiutato per rilievi aperti solo dopo il giro 1 della spec e il giro 1 del piano».

### Test segnalati dalla mano Fable

Nessuno da adeguare; ho usato il suo suggerimento (la frase della riga `gate` di `docs/profili/database.md`) nel test di F1.

### Verifica

- `python3 -B -m unittest tests.test_manifest tests.test_docs tests.test_init tests.test_rules_security tests.test_rules_database tests.test_b1_scripts` → `Ran 645 tests … OK (skipped=3)`; `LOGNAME=root python3 -B -m unittest tests.test_rules_security` → `OK (skipped=3)`.
- `claude plugin validate --strict .` → «✔ Validation passed».
- Suite completa (`suite-final-fix.log`): Python 3.11 `Ran 4520 tests` OK (skipped=16); Python 3.13 `Ran 4520 tests` OK (skipped=14); `exit 0`; nessun «unclosed».
- Commit `c8b7640` «tollgate C2: correzioni dopo la revisione finale» (Co-Authored-By Opus 5.5 e Fable 5.2), con le due pagine della mano Fable.
- Sonda dopo il commit, `bash "<W>/sonda-preflight/rilancia.sh" HEAD`: `ESITO: 70 casi su 70 uguali alla tabella; S67 uguale; casi in più: 12 su 12 come attesi dallo scan`.

### Dubbi

1. Nelle frasi di F1 per `security` (spec 8.7 e `comandi.md`) ho ripreso l'avvertenza della mano Fable: un comando messo anche nel `gate` gira anche nel gate della PR. Nella voce di `database` in 6.3 non l'ho ripetuta (la dice la pagina).
2. Triage 32 e F3 non hanno un RED vero: fissano comportamenti già giusti.
3. La voce 16 del triage (i test di `database` e `frontend` con i nomi utente generici) resta rinviata, come dice la revisione; non ho toccato quei due file.

## Giro 2, mano Fable

Fable, 2026-11-24, sopra il commit `c8b7640`. Toccata una sola riga di `docs/profili/database.md` (rilievo D1 della ri-revisione). Nessun commit, nessun `git add`, nessuna suite completa.

Vecchio:
> … se vuoi un comando anche durante il task, aggiungilo anche a `gate` (per esempio `gate = ["db_test"]`); i comandi di `gate` girano anche nel controllo prima della pull request.

Nuovo:
> … se vuoi un comando anche durante il task, aggiungi anche a `gate` i comandi, nello stesso ordine (per esempio `gate = ["db_reset", "db_test"]`); i comandi di `gate` girano anche nel controllo prima della pull request.

L'ordine è quello dell'esempio della stessa pagina (`dod = ["db_reset", "db_test"]`): il reset prima del test delle policy. Il resto della frase e della pagina è invariato.

`python3 -B -m unittest tests.test_rules_database tests.test_docs tests.test_manifest`: `Ran 129 tests in 2.528s`, `OK`. Test da adeguare: nessuno.

## Giro 2, mano opus

Codice controllato: `bin/tollgate_flow/finishcheck.py:118-121` esegue i comandi di `dod` come `extra` di `verify.run_gate`; `bin/tollgate_flow/openpr.py:326-331` usa `dod_commands` solo per i nomi richiesti e per ricontrollare le ricevute su HEAD (`finishcheck.profile_receipts`), senza eseguirli.

D2, tre punti della spec:
- 6.3, voce di `database`: «i comandi di `dod` li esegue solo `finish check` (`finishcheck.py`, come `extra` di `verify.run_gate`), e `open-pr` ne ricontrolla le ricevute sul commit (`openpr.py`, `finishcheck.profile_receipts`)».
- 8.7, paragrafo di `security`: «I comandi di `dod` girano solo a fine lavoro, con `finish check` (`open-pr` non li riesegue: ne ricontrolla le ricevute sul commit)».
- Riga 37 della sezione 20: «non i comandi di `dod`, che girano solo con `finish check` (`open-pr` ne ricontrolla le ricevute)».
Nessun altro punto di spec, catalogo e piano principale lo diceva (ricerca di `open-pr` vicino a `dod`). Agenti, pagine e `comandi.md` non toccati; `docs/profili/database.md` (D1, mano Fable) aggiunto così com'era.

Verifica: `python3 -B -m unittest tests.test_docs tests.test_manifest tests.test_rules_database tests.test_rules_security` → OK (skipped=3); `claude plugin validate --strict .` → «✔ Validation passed»; suite completa (`suite-final-fix-2.log`): Python 3.11 `Ran 4520 tests` OK (skipped=16), Python 3.13 `Ran 4520 tests` OK (skipped=14), `exit 0`, nessun «unclosed». Commit «tollgate C2: correzioni dopo la ri-revisione finale».
