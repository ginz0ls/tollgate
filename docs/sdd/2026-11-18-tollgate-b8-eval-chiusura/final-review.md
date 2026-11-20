# Revisione finale del ramo `b8-eval-chiusura` (8cbf5b5..6cbd3e2, 33 commit)

Revisore: opus, sola lettura. Letti: pacchetto del diff intero, `decisions.md`, `review-focus.md`, `coverage.md`, `global-constraints.md`, `progress.md` (ruling, sonde, eval, minori rinviati, risposta su s12), rapporto `docs/verifiche/2026-11-18-b8-eval.md`, spec del nucleo rev 35 (righe cambiate), piano principale, `docs/uso/eval-e-ci.md`, `docs/uso/limiti.md`, codice di `bash.py`, `effects.py`, `lookups.py`, `tasks.py`, `init.py`, `evals/*.py`, `run.sh`, i casi nuovi.
Sonde (in `W/sonda-finale/`, solo `bash.parse`/`effect_reason`/`true_inner_commands` su testo, e letture delle evidenze tracciate): `p1.py` (circa 180 forme di comandi), `p2.py` (comandi interni veri), `webcount.py` (risultati web nelle trace). Test mirati: `tests.test_lookups`, `tests.test_tasks` (46 OK), `test_committed_evidence_has_no_long_web_results` (OK). Nessuna rete, nessun `claude`, working tree intatto.

## 1. Verdetto

**Da correggere prima del merge (un important).** Il resto del ramo regge: le forme del review focus chiedono e passano come voluto, i tetti e i registri sono giusti, le evidenze sono pulite.

Conteggi (rilievi nuovi): **0 critical, 1 important, 4 minor.**

## 2. Rilievi

### F1 — important — il testo di shell di `cross-env-shell` e `env-cmd --use-shell` sparisce se contiene una `/` o comincia con un'assegnazione

- **Dove:** `bin/tollgate_analysis/bash.py:1215` (`_loader_word_lists`: `if _ASSIGN.match(tok) or not _command_path_ok(tok, for_effect=not true): continue`), a monte di `_loader_candidates` (`bash.py:1227-1260`). Spec 8.5 `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:988` e `docs/uso/limiti.md:21` descrivono l'opposto.
- **Cosa:** i filtri per token (percorsi di dati con `/`, assegnazioni `NOME=valore`) si applicano anche alla **parola unica che è un intero comando di shell**, prima che `_loader_candidates` la unisca e la passi a `parse`. La parola viene scartata e nessun candidato nasce. Sonda `p1.py`, tutti **passano senza permesso**:
  - `cross-env-shell "cd apps/web && vercel deploy --prod"`
  - `env-cmd --use-shell "cd apps/web && vercel deploy --prod"`
  - `cross-env-shell "curl -X POST https://api.example.com"` (ogni URL ha una `/`)
  - `cross-env-shell "prisma migrate deploy --schema=db/schema.prisma"`
  - `cross-env-shell "./scripts/build && vercel --prod"`, `cross-env-shell "supabase db push --workdir ./supa"`
  - `cross-env-shell "DEBUG=1 vercel --prod"`, `env-cmd --use-shell "NODE_ENV=production prisma migrate deploy"` (la parola intera combacia con `_ASSIGN`)

  La forma diretta di ognuno chiede. Lo stesso buco vale per `_script_reason`: `true_inner_commands` di `cross-env-shell "./deploy.sh && echo ok"` è vuoto (sonda `p2.py`), quindi uno script non tracciato dietro quella forma non arriva al controllo dei file. Alcune forme chiedono solo per caso (`env-cmd -f .env.prod --use-shell "…/…"` chiede perché il valore `.env.prod` apre una scansione larga che include il testo).
- **Perché:** è la classe di comandi che la decisione 1 e le ruling dello Step 0 (righe 8-9 del ledger: `cross-env-shell` aggiunto apposta, testo di shell parsato) e del giro 1 del Task 1 (riga 41: «quando una parola del comando interno contiene uno spazio, si costruisce anche il candidato `bash.parse(" ".join(<parole>))`, per ogni involucro») volevano chiudere. `cross-env-shell` esiste proprio per scrivere `&&`, `cd` e variabili, dove percorsi e URL sono la norma. Effetto dimostrato: un `vercel deploy --prod`, un `prisma migrate deploy` o un `curl -X POST` partono senza `/tollgate:approve effect`. `test_env_loader_shell_forms` (`tests/test_bash.py:714-719`) usa solo testi senza `/` e senza assegnazione iniziale, quindi non lo vede.
- **Come correggere:** in `_loader_word_lists`, una parola che contiene spazi bianchi (`re.search(r"\s", tok)`) è testo di shell: non passa da `_ASSIGN` né da `_command_path_ok` e produce sempre il suo candidato (in entrambe le modalità; in `true=True` resta l'ultimo candidato, come oggi). Il resto lo fanno già `_loader_candidates` (`" ".join` + `parse`) e la scansione delle posizioni di `spaced`. Test rossi prima: le otto forme sopra chiedono in `effect_reason`; `true_inner_commands(cross-env-shell "./deploy.sh && echo ok")` contiene `./deploy.sh` e uno script non tracciato chiede in `tests/test_check_effects.py`; restano verdi `cross-env-shell "jest && echo ok"` e `cross-env NODE_ENV=test jest src/aws`. Nessuna scelta dell'utente coinvolta (la decisione 1 è «utente: chiudere il buco; mia scelta: come»).

### F2 — minor — le scritture dei gestori di segreti passano (scelta dell'utente)

- **Dove:** `bin/tollgate_analysis/bash.py:984` (`_DEFAULT_EFFECTS`), `ENV_LOADERS` (`bash.py` decisione 1).
- **Cosa:** B8 insegna a tollgate che `doppler`, `infisical` e `op` sono involucri, ma i loro comandi che scrivono sul servizio passano: `doppler secrets set A=1`, `infisical secrets set A=1`, `op item create --title x` (sonda `p1.py`). Cambiano i segreti di produzione nel servizio vero.
- **Perché:** l'elenco degli effetti esterni è chiuso per scelta della spec (8.5), e i CLI non in elenco si dichiarano in `[external_effects] commands`; non è una regressione di B8. Ma il ramo nomina questi programmi e la pagina d'uso li elenca: un lettore può credere che siano coperti.
- **Come correggere:** scelta dell'utente: aggiungere a `_DEFAULT_EFFECTS` (o a `FLAG_EFFECTS`) le scritture `doppler secrets set|delete|upload`, `infisical secrets set|delete`, `op item create|edit|delete`, oppure scriverlo come limite in `docs/uso/limiti.md` e nel blocco «Dopo B». Consiglio: voce «Dopo B» con il limite scritto ora.

### F3 — minor — il grader «pagina aperta» di s10 passa anche quando la pagina non è stata letta

- **Dove:** `evals/s10-modello-a-memoria/case.yaml` (`pagina-modelli-aperta`), spec 14 (`…nucleo-design.md:1658`), rapporto, sezione s10.
- **Cosa:** `tool_used WebFetch` con `input_match` conta la **chiamata**, anche quando la risposta è il solo avviso di redirect: nella prima sonda il grader è passato (0,40 = 2/5) con due `WebFetch` che hanno avuto solo il 301 verso `aistudio.google.com`. È la stessa «lettura senza contenuto» che la sonda ha corretto in `lookups.observed`, ma nel grader resta.
- **Perché:** nel braccio con il plugin il buco è coperto da tollgate stesso (la nota con l'indirizzo non aperto è rifiutata, quindi il file non cambia e il caso resta sotto soglia), quindi il punteggio delle corse vere non è falsato: nelle tre corse l'implementatore ha aperto `aistudio.google.com` (9 `fetch` registrati). Però spec e rapporto lo descrivono come «pagina aperta».
- **Come correggere:** nessun cambio al caso (rifarlo costerebbe un eval); una frase nella spec 14 e nel rapporto: «il grader conta la chiamata, anche se risponde con un redirect; la lettura vera è nei conteggi `fetch` di `nota.md`». Un grader sui contenuti resta a D.

### F4 — minor — `nota.md` non distingue i bracci, e spec e docstring dicono che il braccio senza plugin si salta

- **Dove:** `evals/research_counts.py:9` (docstring), spec 14 (`…nucleo-design.md:1666`), decisione 10.
- **Cosa:** lo scaffold crea lo stato di tollgate anche nel braccio senza plugin, quindi quelle corse hanno `tollgate.db` e compaiono in `nota.md` con righe a zero (6 righe per ogni caso `spec`, per esempio `20261119T063624Z-s12-non-esiste/nota.md`); il ramo «saltata» non scatta mai negli eval veri. La tabella non dice quale corsa è di quale braccio.
- **Perché:** le somme del rapporto sono giuste (ricalcolate: 23, 2, 3, 0, 0, read 100, bash_read 10, fetch 12), ma un lettore di `nota.md` non può separare i bracci e la frase della spec non corrisponde a ciò che succede.
- **Come correggere:** correggere la frase della spec 14 e del docstring («il braccio senza plugin ha lo stato dello scaffold e dà righe a zero»); in D, una colonna «braccio» presa da `result.json` (`tracePath` per braccio).

### F5 — minor — due frasi di `docs/uso/eval-e-ci.md` e il docstring del modulo `scrub.py` non corrispondono al codice

- **Dove:** `docs/uso/eval-e-ci.md:24`, `docs/uso/eval-e-ci.md:89`, `evals/scrub.py:8-9` (docstring del modulo).
- **Cosa:** la riga 24 dice «I casi con un implementatore che scrive (`s1`, `s2`, `s3`, `s6`, `s9`) hanno anche l'indicatore `nota-consegnata`», ma ce l'hanno anche `s10`, `s11` e `s12`. La riga 89 e il docstring del modulo descrivono `anonymize` solo come «`/home/<utente>` e host», mentre sostituisce anche `-home-<utente>-` e il nome utente come parola intera (il docstring della funzione è già giusto).
- **Come correggere:** «I casi con un implementatore (`s1`, `s2`, `s3`, `s6`, `s9` e i tre nuovi)…»; nelle altre due righe le quattro sostituzioni.

## 3. Triage dei minori rinviati del ledger

| # | Task | Rilievo | Esito | Motivo |
|---|---|---|---|---|
| 1 | 1 | `_SUPABASE_HELP` (`bash.py:1093`) non è più usata | da correggere | Codice morto da togliere: una riga, insieme al #2. |
| 2 | 1 | `_supabase_asks_help` scrive a mano `("--help", "-h")` e `"--version"` | da correggere | Una costante `_SUPABASE_HELP_FLAGS` al posto della tupla morta del #1 chiude i due in un solo cambio. |
| 3 | 2 | `take_pending` conta anche una prenotazione scaduta | rinviato | Sbagliato prima e dopo, mai peggiore; correggerlo vuole `now` in `take_pending` e tocca `apply`, oltre il perimetro di B8. |
| 4 | 2 | Nessun test di `take_pending(number=N)` con una prenotazione su un altro task | da correggere | Un test di poche righe fissa che il `WHERE` prevale sull'ordine nuovo, sulla funzione che lega i task. |
| 5 | 2 | Nessun test esplicito «valore del frammento uguale al predefinito, nessuna riga» | nessuna azione | `test_real_precedence_p39` lo copre già con i frammenti veri a `L0`. |
| 6 | 2 | Riga di `DECLARED_X` in `tests/test_init.py:677-678` più lunga | nessuna azione | Cosmetico, solo in un test. |
| 7 | 3 | Residui della pulizia: `curl -o f` poi `cat f`, pagine salvate nel `cwd`, script scritto con `Write` | rinviato | Scritti nel rapporto e controllati a mano dal controller; una regola generale serve alle campagne di D. |
| 8 | 3 | `scrub._rewrite` cambia in U+FFFD i byte non UTF-8 delle righe non toccate | nessuna azione | Le trace di `claude plugin eval` sono JSON UTF-8 valido: nessun byte da perdere nelle evidenze vere. |
| 9 | 3 | `research_counts.table` perde la tabella per un `WalError` e non dice quale corsa | nessuna azione | `run.sh` anonimizza (con checkpoint) prima dei conteggi, quindi il `-wal` non c'è mai nel flusso vero. |
| 10 | 3 | `scrub._is_exempt` cerca `research` e `submit` in qualunque posizione | da correggere | Pochi caratteri (parole contigue dopo il programma `tollgate`) e un test chiudono una via per lasciare testo di terzi in un repo pubblico. |
| 11 | 3 | `sed` esente per nome, anche con il comando `e` di GNU sed | rinviato | Forma artificiosa; serve una lettura degli script di `sed`, da fare con il #7 in D. |
| 12 | 4 | `calc-dividi.md`: il must-have M2 non è assegnato a nessun task | nessuna azione | Il caso è già girato con questa ricetta: cambiarla ora renderebbe le evidenze non ripetibili, e M2 non è valutato. |
| 13 | 4 | s10, un cammino che lascia `gemini-1.5-flash` prende 0,80 | nessuna azione | Il rapporto lo scrive già come limite noto del caso. |
| 14 | 4 | s12 `ricerca-fatta` conta anche un `Grep` del modello principale | nessuna azione | Peso 1, senza effetto sulla soglia; il rapporto dice che l'unico `Grep` visto era sul plugin. |
| 15 | 4 | `test_s12_doing_nothing_scores_two_fifths` non asserisce il punteggio | da correggere | Il nome promette 2/5: un `assertAlmostEqual(score_of(...), 0.4)` lo rende vero. |
| 16 | 4 | `docs/uso/eval-e-ci.md` dice ancora «tredici casi, nove spec» | nessuna azione | Già corretto dal Task 8 (ora «dodici» e «sedici»; nessuna occorrenza rimasta). |
| 17 | 5 | `evals/_kit/recipes.py:42-43` oltre le 120 colonne | nessuna azione | Cosmetico; anche altre righe del file (56, 110) lo sono, senza un limite imposto da un test. |
| 18 | 5 | Nessun test fissa che un `Bash` che nomina `research submit` senza eseguirlo accende l'indicatore | nessuna azione | È voluto (decisione 13: conta un tentativo) e il rapporto lo dice. |
| 19 | 5 | Il test dell'indicatore di s9 usa `ag-1` di `S9DryRun.DEDICATED` senza dirlo | nessuna azione | Accoppiamento interno ai test, senza effetto sul prodotto. |
| 20 | 6 | `ObservedWebFetchTest` sta dopo `if __name__ == "__main__"` in `tests/test_lookups.py` | da correggere | Spostare la classe sopra il blocco: lanciando il file da solo i quattro test del redirect oggi non girano. |
| 21 | 6 | s10, `aistudio\.google\.com/docs/models` accetta anche un prefisso | nessuna azione | Come il pattern di prima; nessun indirizzo reale simile sui domini concessi. |
| 22 | 6 | Il docstring di `scrub.anonymize` cita solo `/home/<user>` e l'host | da correggere | Il docstring della funzione è già giusto, ma quello del modulo (`scrub.py:8-9`) no: si corregge con F5. |
| 23 | 6 | Nome utente con `-` o `.` ai bordi sfugge a `\b`; un nome comune verrebbe sostituito ovunque | nessuna azione | Il rapporto lo scrive, e il controllo `/usr/bin/grep -raF` prima di ogni commit lo coprirebbe. |
| 24 | 8 | «Sezioni toccate» della rev 35 non elenca 8.1 | da correggere | Una voce in una riga della tabella delle revisioni, che deve dire dove guardare. |
| 25 | 8 | Spec 1.2 e 16 (g) attribuiscono alla sonda il fallimento di `git worktree add`, visto in e3 | da correggere | Una fonte sbagliata in un fatto verificato della spec: «sonda (g) ed e3». |
| 26 | 8 | «in 48 corse nessun veto della nota» pesa più di quanto misuri | da correggere | Le corse con un implementatore che modifica sono 23 (8 casi, una corsa di e5 senza modifiche): spec 16, rapporto e piano devono dire quelle. |
| 27 | 8 | `docs/profili/verifiche/ai-fonti.md:20` cita la pagina dei modelli spostata ma manca dall'elenco delle pagine che invecchiano | da correggere | L'elenco unico di «Dopo B» deve essere completo; il file approvato non si tocca, si aggiunge solo la voce. |
| 28 | 8 | La spec 8.5 non nomina `infisical sm run` e `infisical secrets-manager run` | da correggere | Il codice e un test li coprono (ruling dello Step 0): basta una parentesi in 8.5. |
| 29 | 8 | Piano principale sez. 5, «nessuno è un difetto aperto del codice di tollgate», per s12 | nessuna azione | La frase è esatta (la causa è una regola mancante, non il codice) e la stessa riga nomina «la regola mancante». |

## 4. Le scelte «mia scelta» del piano e le ruling

Nessuna contestata nel merito. Osservazioni:

- **Campagne (decisione 6), `WebFetch` per dominio, conteggi, ordine degli eval:** giuste. Verificato: `eval-p5/` invariato (diff vuoto), ogni `--max-cost-usd` uguale al residuo di `b8` (da 20,00 a 8,97), costo 11,5854 USD.
- **Ruling D4 (`strip_web_results` su ogni risultato):** giusta. Ricontrollati i 30 risultati di `WebFetch` tracciati: tutti segnaposto; nessun risultato di `WebSearch`.
- **Ruling I1 di T3 (`strip_bash_web` sul testo grezzo):** giusta. Costo visto: anche `tollgate research submit … 2>&1 | tail -5` perde il risultato (il `tail` toglie l'esenzione), quindi il testo di un rifiuto della nota in quella forma non resta nelle evidenze. Accettabile, va solo saputo.
- **Ruling (g) (nessun aggiramento della sola lettura di `.git/worktrees/`):** condivisa: un aggiramento sarebbe un'ipotesi da pagare con altri eval.
- **Ruling su `aistudio.google.com`:** condivisa; vedi F3 per il grader.
- **s12 (scelta dell'utente «lascia così»):** non la contesto. Noto solo che il task del piano della ricetta dice «Modify `src/calc.py`», e il controllo dello scope tiene l'implementatore su quel file. Il risultato misura quindi anche quanto il piano spinge verso `calc.py`, non solo la regola che manca. Se ne tiene conto quando si rivede `rules-base`.
- **Percorso della cartella del repo nelle evidenze** (`/home/USER/MEGA/BIZ/VIBE/Plugin IT workflow/…` in `comando.txt`, `stdout.txt` e `stderr.txt` di ogni caso): non è nome utente né host, ed era già così nelle evidenze di P5 e di B1 su `main`. Nessuna azione: lo segnalo solo perché è una disposizione delle cartelle personale.

## 5. Osservazioni positive

- Le 17 forme del review focus si comportano come voluto (13 chiedono, 4 passano). Sono giuste anche circa 60 forme in più: involucri dietro `npx`, `pnpm dlx`, `yarn`, `bunx`, percorsi `.bin/`, `sudo`, `env`, `timeout`, `xargs`, `nohup`, `eval`, `bash -lc`, la profondità 2 e le opzioni di Supabase lette come le legge pflag (`-p --db-url x` chiede, `db dump -f --linked` passa).
- `take_pending` è una riga, ordinata su stringhe ISO a larghezza fissa (`clock.fmt`), e il lancio in background è già negato: il caso «due prenotati» non si presenta.
- `init --update` propone senza riscrivere (le righe di `_drift`), e una chiave scritta vuota non dà righe.
- Il difetto del redirect, trovato dalla sonda, è stato corretto con un test e verificato dal vivo. È l'anti-obiettivo «frase vuota senza lettura registrata» preso sul fatto.
- Evidenze: nessun nome utente, nessun host, nessuna forma di token (anche nei `.db` e nei binari) nei 3213 file tracciati. Le copie di Superpowers sono vuote, nessun `-wal`. I numeri del rapporto si ricalcolano identici dai `nota.md` e da `budget.tsv`.
- Le due sonde a basso costo prima dei 16 casi hanno trovato tre difetti del prodotto e del kit prima di spendere il tetto.
