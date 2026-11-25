# Ri-revisione del giro di correzione dopo la revisione finale di C2 (Fable, sola lettura)

**Rilievi ancora aperti sull'intero ramo dopo il giro: `critical` 0, `important` 1** (D1, danno nuovo del giro: un esempio nella pagina di `database`; correzione di poche parole). I rilievi della revisione finale di questo giro (F1, F2, F3, U1, U2, triage 1, 4, 32, n1-n3) sono tutti chiusi. F4 non è di questo giro (controller, dopo il merge).

Oggetto: commit `c8b7640` (genitore `4cf2b97`), 13 file. Metodo: letti le regole, il brief del giro, la revisione finale, il rapporto della ri-revisione del Task 9, il report delle due mani e il diff `review-final-fix.diff` (una volta, riga per riga, con il confronto parola per parola delle righe lunghe). Codice letto nel worktree senza scrivere. Test e sonde solo su una copia `git archive c8b7640` in `/tmp/tollgate-rev-*` resa repo privato, con `HOME`, `TMPDIR` e `TOLLGATE_STATE` temporanei, cancellata alla fine. Nessun subagente, nessuna rete, nessun `claude`, suite completa non rilanciata.

Lanciati sulla copia: `tests.test_init.SecurityPrecedenceTest.test_real_precedence_s72` e `…_s73`, `tests.test_manifest`, `tests.test_rules_security`, `tests.test_rules_database` → 167 test, OK (3 saltati); `bash W/sonda-preflight/rilancia.sh c8b7640` → `ESITO: 70 casi su 70 uguali alla tabella; S67 uguale; casi in più: 12 su 12 come attesi dallo scan`.

## Verdetti sui rilievi

**F1. `<programma> verify` non esegue i comandi di `dod` (agente di sicurezza, `comandi.md`, spec 6.3 e 8.7, piano principale, test)** — INDIRIZZATO.
- Codice: `bin/tollgate_core/verify.py:88` (`gate = gate_commands(cfg, files) + extra`, e `run_verify` passa `extra=()`, `verify.py:33`); `bin/tollgate_core/runner.py:47-57` (`[commands] gate` più la chiave `gate` dei profili attivi); `runner.py:60-69` (`dod_commands`, senza quelli già nel `gate`); `bin/tollgate_flow/finishcheck.py:118-121` (l'unico `run_gate` con `extra`); `bin/tollgate_gate/run.py:114` (il gate della PR usa `gate_commands`). La formula è vera.
- `agents/implementer-security.md:53`: «le lanci con `<programma> verify`, che esegue il gate del progetto e i comandi che l'utente ha messo nel `gate` del profilo; i comandi di `dod` girano a fine lavoro, con `finish check`: li esegue tollgate, non tu». Cambia solo quella frase.
- `docs/uso/comandi.md:34` (frase di `security`); spec `:508` (6.3) e `:1147` (8.7, con `gate = ["denied"]` e l'avvertenza che gira anche nel gate della PR); riga 37 della sezione 20 (`:2348`); piano principale `:164`.
- Test: `tests/test_manifest.py:421` `test_real_verify_channel_is_the_gate` (sezione «Area» dei due implementatori: «nel `gate` del profilo» e «finish check» presenti, frase vecchia assente; `comandi.md`; pagina di `database`). Verde sulla copia.
- Le frasi nei sei posti (due agenti, `comandi.md`, pagina di `database`, spec, piano) dicono la stessa cosa. Due difetti nuovi, sotto: D1 (l'esempio della pagina di `database`) e D2 («e `open-pr`» nella spec).

**U2. La stessa frase per `database` (pagina, agente, `comandi.md`, spec, test)** — INDIRIZZATO.
- `docs/profili/database.md:109`: «le prove del database passano da `verify`, che esegue i controlli del progetto e i comandi che scrivi nella riga `gate` del blocco del profilo. I comandi di `dod` girano solo a fine lavoro…». La coda «i comandi di `gate` girano anche nel controllo prima della pull request» è vera (`bin/tollgate_gate/run.py:114`) ed è coerente con la riga 95 della pagina («Il gate è il controllo prima di aprire la pull request»). Nota di storia a `:7`; «Approvata dall'utente il 2026-11-17.» resta a `:5`. Il resto della pagina è intatto (3 righe aggiunte, 1 tolta).
- `agents/implementer-database.md:53`: la stessa frase dell'agente di sicurezza, una sola riga cambiata; `test_area_agents_derive_from_generic` verde.
- `docs/uso/comandi.md:34` (frase di `database`), spec `:507` (con la storia della frase).
- Test: lo stesso `test_real_verify_channel_is_the_gate` copre `database` (agente e pagina).
- La frase vecchia non esiste più. L'esempio aggiunto nella frase nuova ha un difetto suo: D1.

**U1. Punto 3 della pagina di sicurezza** — INDIRIZZATO. `docs/profili/security.md:142`: «Lo stesso per un file `.ts` riconosciuto da `frontend` (S58) o per un file riconosciuto da `database` (S65). Fa eccezione un file `.tsx` (o `.jsx`, `.vue`, `.svelte`) dentro `auth/`: … va agli agenti di sicurezza, come al punto 2, perché `frontend` quei file li prende già per l'estensione e non ne propone il percorso esatto.» Provato sulla copia con i frammenti veri: `Guard.jsx`, `Guard.vue`, `Guard.svelte` trovati da `frontend` dentro `src/auth/` vanno a `security`; `Guard.ts` va a `frontend` con il percorso esatto. Le righe `Proposta:` e «Hai approvato la proposta.» del punto sono righe di contesto del diff (intatte); «Approvata dall'utente il 2026-11-23.» resta a `:5`, nota di storia a `:7`. Nient'altro cambia nella pagina.

**F2. `test_page_has_no_private_data` rosso con un nome utente generico** — INDIRIZZATO. `tests/test_rules_security.py:28` (`GENERIC_NAMES`) e `:958`. Sulla copia: `LOGNAME=root` → OK; `LOGNAME=Root` → OK; `LOGNAME=token` (una parola non generica che il testo contiene) → `FAILED (failures=2)`, con il messaggio senza il valore. Il test ferma ancora un nome vero; `/home/` e le forme di token restano controllati.

**F3. S72 e S73 (spec, test, «In breve»)** — INDIRIZZATO.
- Spec `:685` (S72) e `:686` (S73), dopo S71; «In breve» a `:610`: «**fuori da una cartella del profilo**: dentro `auth/` il percorso esatto non si propone … e vince la cartella più profonda dell'altro profilo (S72)» e «dove il percorso esatto è di un file che l'altro profilo non copre già con un'estensione … (S73; S58 vale per un `.ts`)».
- `tests/test_init.py:2350` e `:2363`: usano `check` e `check_active` della classe, cioè i frammenti veri (`_real_fragments_root`), e asseriscono proposta, runtime e profili attivi uguali alle due righe (S72: `ai`/`security` e `backend`/`security`, il file ad `ai` e a `backend`, attivi `[ai, security]` e `[backend, security]`; S73: `frontend`: `**/*.tsx`, `security`: `src/auth/**`, `Guard.tsx` a `security`, attivi `[frontend, security]`). Verdi sulla copia; la sonda del pre-flight resta 70 su 70.
- «S1-S73» aggiornato nell'intestazione della spec, nel catalogo e nella riga C2 del piano principale; la riga 37 dice «S1-S71 … più S72 e S73 dalla revisione finale».

**Triage 1. `comandi.md`, «Modelli degli agenti»** — INDIRIZZATO. `docs/uso/comandi.md:198`: «Se `availableModels` esclude il modello chiesto…», «con un avviso nelle sessioni interattive» senza «solo», «con `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` Claude Code ignora sia la riga `model:` … sia il `model` della chiamata». È il fatto della riga 16 di `fatti-verificati.md` e dice la stessa cosa della spec `:226`.

**Triage 4. `SONNET_PIN`** — INDIRIZZATO. `tests/test_manifest.py:22-24`; `test_sonnet_pin_sees_every_form` a `:143` (nove forme che fissano, tre che non fissano). `test_no_sonnet_in_skills_and_scripts` resta verde: l'espressione è più larga, non più stretta.

**Triage 32. Il caso `b1` senza il controllo dell'uscita** — INDIRIZZATO. `tests/test_b1_scripts.py:2309-2312`: `assertNotEqual(r.returncode, 0)` prima del messaggio, in un `subTest`.

**n1** — INDIRIZZATO. `docs/verifiche/2026-11-22-c2-prova-flusso.md:80`: «nove dei quali senza rilievi sopra `minor`».
**n2** — INDIRIZZATO. `:153`: «(passo 2 di «Il lavoro», il TDD)»; il passo 2 di `agents/implementer-security.md` (riga 58) è la chiamata alla skill di TDD.
**n3** — INDIRIZZATO. `:142`: «ha rifiutato per rilievi aperti solo dopo il giro 1 della spec e il giro 1 del piano».

### Controlli chiesti dal controller

- **File approvati.** `git diff 4cf2b97 c8b7640 --stat` è vuoto su `skills/`, `templates/`, `docs/profili/verifiche/` e `bin/` (gate compreso). Le due pagine cambiano di 4 righe ciascuna; gli altri agenti non sono toccati.
- **Elenco dei file.** 13 file, tutti dentro il brief (`docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md` cambia solo «S1-S71» in «S1-S73»).
- **Dati privati.** Nome utente e host nel diff: 0; `/home/` nelle righe aggiunte: 0. Nessun «unita su `main`» scritto per C2. Le sole righe aggiunte con `sonnet` o `haiku` sono l'espressione e il test del triage 4.
- **Commit.** Nuovo (nessun amend), oggetto giusto.

## Danni nuovi nel diff della correzione

- **D1 (Important). `docs/profili/database.md:109`, l'esempio `gate = ["db_test"]`.** Sei righe sopra la pagina propone `dod = ["db_reset", "db_test"]` (prima si ricrea il database, poi si provano le policy). Chi segue l'esempio nuovo e aggiunge `gate = ["db_test"]` ottiene: durante il task `verify` lancia `db_test` senza `db_reset`, cioè su un database locale dove la migrazione nuova non è applicata; a fine lavoro l'ordine si rovescia, perché `dod_commands` salta i comandi già nel `gate` (`runner.py:66`) e `finish check` esegue il `gate` prima del `dod`. Provato sulla copia con il blocco della pagina: senza `gate` `finish check` esegue `verify, db_reset, db_test`; con `gate = ["db_test"]` esegue `verify, db_test, db_reset`. Il test delle policy gira quindi prima del reset, in tutti e due i momenti: o è rosso senza che l'implementatore possa rimediare (non può lanciare `supabase`), o è verde su uno schema vecchio. La frase non è falsa, ma l'esempio peggiora il controllo di chi lo copia, in una pagina approvata. Correzione (poche parole, mano Fable, dentro la frase che l'utente ha già deciso di correggere): `gate = ["db_reset", "db_test"]` («aggiungi anche a `gate` i comandi, nello stesso ordine»), oppure togliere l'esempio fra parentesi. `test_real_verify_channel_is_the_gate` resta verde in tutti e due i casi. Con `gate = ["db_reset", "db_test"]` l'ordine torna giusto sia a `verify` sia a `finish check` (provato).
- **D2 (Minor). Spec `:1147` e `:2348`: i comandi di `dod` «girano solo a fine lavoro, con `finish check` e `open-pr`»** (e `:507` «entrano solo a `finish check` e a `open-pr`»). `open-pr` non li esegue: `bin/tollgate_flow/openpr.py:326-331` usa `dod_commands` solo per i nomi e per ricontrollare le ricevute su HEAD; l'unica esecuzione è in `finishcheck.py:121`. La formula viene da F1 della revisione finale, che era imprecisa nello stesso punto. Correzione: «girano solo con `finish check`; `open-pr` ne ricontrolla le ricevute». Agenti, pagine e `comandi.md` dicono solo `finish check` e sono giusti. Non blocca: può andare nel commit di chiusura del controller.

Nessun danno Critical. Nessun test indebolito.

## Osservazioni fuori ambito

- `verify --related`, quando trova test correlati, non esegue il gate (`verify.py:135-139`), quindi nemmeno i comandi del `gate` del profilo. Solo `agents/implementer-frontend.md:53` nomina `--related`; gli agenti di `security` e `database` no. Da tenere presente per C3.

## Verdetto

Gli undici gruppi di rilievi del giro sono chiusi e la frase nuova su `verify` è vera contro il codice in ogni posto. Il giro ha però introdotto un esempio dannoso nella pagina approvata di `database` (D1): si corregge con poche parole nella stessa frase, senza toccare test né codice.

**Giro di correzione:** Rilievi ancora aperti: D1 (Important, danno nuovo: l'esempio `gate = ["db_test"]` di `docs/profili/database.md:109` fa girare il test prima del reset). D2 è Minor e non blocca.
