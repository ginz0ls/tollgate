# Task 8: revisione (commit 8606917, pacchetto 08cd53a..8606917)

Sola lettura. Controlli fatti su `bin/tollgate_analysis/bash.py`, `bin/tollgate_checks/effects.py`, `bin/tollgate_flow/init.py`, `bin/tollgate_core/tasks.py`, `bin/tollgate_core/lookups.py`, `bin/tollgate_core/config.py`, `evals/cost.py`, `evals/run.sh`, `evals/scrub.py`, `evals/research_counts.py`, sul rapporto `docs/verifiche/2026-11-18-b8-eval.md`, sul ledger (`progress.md`) e con grep sul ramo. Nessuna esecuzione della suite (il log `suite-task-8.log` finisce con `exit 0`, 4175 test OK su entrambi gli interpreti, nessun «unclosed»).

## Aderenza

- ✅ Solo sei file di documentazione toccati. `git diff --name-only main...HEAD` non include nessun file approvato (`skills/rules-*`, `templates/profiles/*.toml`, `docs/profili/**`, `agents/*.md`, `eval-p5/budget.tsv`).
- ✅ «B chiusa» non compare da nessuna parte. Il progetto dice «B8 eseguita sul ramo, unione in attesa» (`2026-10-27-tollgate-b-profili-design.md`, Avanzamento) e il piano principale dice che la chiusura la scrive il controller dopo il merge (righe 8 e 34).
- ✅ Nome utente e host: 0 occorrenze nei sette documenti toccati o citati (grep `-F` senza stampare i valori). L'unico `/home/` è `/home/USER`.
- ✅ D17: titolo della spec 1.2 (riga 114) e `###` di `docs/uso/limiti.md` cambiati insieme. Nessun rimando vivo al vecchio titolo: restano solo due `docs/sdd/2026-10-23-tollgate-p5-*` storici. I nomi dei test (`test_limits_match_spec_1_2`, `test_relative_links_exist`) esistono.
- ✅ D12: link al rapporto di B8 in `docs/uso/eval-e-ci.md`. Il file esiste.
- ✅ D2: la voce «s9 non è cambiato» è corretta (piano principale, sezione 9, blocco «A B8»). s9 è tra i cinque casi con la nota, in spec 14, progetto sez. 15, piano sez. 17.
- ✅ Il limite della piattaforma (`.git/worktrees/` di sola lettura in 2.1.328, cinque casi s1, s3, s6, e3, e4) è in spec 1.2, 14, 16 (sonda (g)), catalogo, progetto sez. 15, `limiti.md`, `eval-e-ci.md` e piano «Dopo B» voce 2. Nessun aggiramento nel kit, come da ruling (g).
- ✅ La scelta dell'utente su s12 («Lascia così») è nella riga 35 della sezione 20, in spec 16, nel progetto sez. 15 e nel «Dopo B» voce 1, con la data del 19/11 e il costo di ripetizione (circa 0,8 USD). Esito «non riuscito» coerente con la ruling di `progress.md` riga 149. Totali 10 + 5 + 1 = 16 e 11,59 USD (sonde 0,70) coincidono con ledger e rapporto.
- ✅ Frasi della spec contro il codice (tutte trovate come scritte):
  - `ENV_LOADERS` con `cross-env-shell`, `LOADER_PACKAGES` a due voci, `MAX_LOADER_DEPTH = 2`.
  - Le regole di `_command_path_ok`: `./x` senza punto solo per il controllo dei file, mai per `effect_reason`.
  - `inner_commands` / `true_inner_commands`, con lo scorrimento da dopo `run`.
  - La clausola `isfile` + `X_OK` in `script_path(inner=True)`.
  - `SUPABASE_COMMAND_VALUE_OPTIONS`: gli esempi di 8.5 coincidono con la tabella, senza `--local` né `REMOTE_FLAGS`.
  - `_supabase_asks_help` con `--version` solo prima del sottocomando.
  - `take_pending` con `ORDER BY (reserved_at IS NULL), reserved_at DESC, number`, e il limite «launch + resume» descritto correttamente.
  - `init._drift`: `min_level`/`checklist` solo se non vuoti e diversi da `PROFILE_DEFAULTS` (`L0`, ``). Gli `L1` di `ai` e `infra` e l'`L2` di `database` sono nei frammenti.
  - `lookups.observed`: codice intero fuori da 200-299 (bool escluso) e `REDIRECT DETECTED`.
  - `CAMPAIGNS` p5 80 / b8 20, `TOTAL_USD` e `DEFAULT_BUDGET` assenti.
  - `WEB_DOMAINS` a tre domini, `scrub.py domains`, `cost.py info`, `--allow-tools` per dominio più `WebSearch`.
  - Ordine della pulizia, uscita 5, `anonymize` con valore corto o riservato, `research_counts` con `mode=ro&immutable=1`, `-wal` come errore e tabella mancante a zero.
  - I quaranta circa nomi di test citati nella spec e nel piano esistono tutti in `tests/`.
- ✅ Catalogo 2.2: 18 agenti, 7 + 10 + 1 (verificabile con `ls agents`, il report lo dichiara).
- ✅ Ruling della sonda e di D3, D8, D10, D11 riportate in 8.5 e in `limiti.md`. Il costo «`./deploy` non eseguibile» è scritto.
- ⚠️ Non verificabile dal diff: i conteggi 23 note valide / 2 rifiutate / 3 promemoria / letture (100, 10, 12). La somma per caso (s10 3, s11 3, s12 3, s1 3, s3 3, s6 3, e4 3, e5 2 = 23) coincide con il ledger. I totali per tipo di lettura non li ho ricontrollati sulle evidenze.

## Punti di forza

- Le descrizioni di 8.5 sono scritte come limiti veri, con il costo e il test per ognuno. Il confine «i controlli su `argv[0]` non vedono dentro un involucro» è dichiarato per intero, come chiedeva D3.
- Il blocco «Dopo B» ha le frasi esatte e ha trovato una pagina in più (`docs/profili/database.md` riga 97) che il piano non elencava. Ho controllato: la riga dice ancora «non gli propone niente di nuovo».
- Il report e il piano ammettono che la voce di PP:288 era sbagliata e la correggono. L'esito del rapporto è «non riuscito» senza addolcirlo.
- Scostamenti dal piano dichiarati (blocco «Dopo B» in fondo alla sezione 9, minori del controller lasciati come segnaposto).

## Rilievi

### Critical
Nessuno.

### Important

**I1. La sezione 14 della spec dice ancora «I nove casi» subito sotto un elenco di dodici**
- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:1654`: «**Come girano i casi** (P5, decisioni 2 e 5-9 del piano). I nove casi sono `evals/s1-…`, …, `s9-implementatore-generico` (tag `spec`)».
- Qualche riga sopra la stessa sezione elenca ora 12 casi (`:1650-1652`, casi 10-12). L'indicatore `nota-consegnata` e le ricette sono nel paragrafo «Casi di B8» subito dopo. Il tag `spec` oggi vale 12 casi, quindi la frase non corrisponde al codice (`evals/` ha 12 cartelle `s*`). La parentesi «P5» non basta: si legge come stato attuale, mentre 1.3 e `eval-e-ci.md` dicono «dodici».
- Correzione: «I casi di P5 sono i nove … (`s1`-`s9`, tag `spec`); i tre di B8 sono sotto in «Casi di B8»», oppure «I dodici casi sono …» con `s10`-`s12` aggiunti alla lista.

### Minor

- **M1. «Sezioni toccate» incompleto.** La riga 35 della sezione 20, l'intestazione (rev 35), il catalogo sez. 6, il piano sez. 5 e sez. 17 elencano 1.2, 1.3, 6.3, 7.2, 8.5, 11.2, 14, 16, 20. Il diff tocca anche **8.1** («Cosa conta come lettura», spec riga 821: il redirect senza pagina non è una lettura). Aggiungere 8.1. Il report dice «7.2 (due punti: tabella dei hook e «Cosa conta come lettura»)», ma il secondo punto sta in 8.1.
- **M2. Attribuzione del fatto «`git worktree add` non può creare un worktree».** Spec 1.2 e riga (g) di 16 lo attribuiscono alla sonda (g). La sonda ha visto solo l'EROFS su `index.lock` (ledger riga 119). Il fatto viene da e3 (`progress.md` riga 143 e rapporto riga 154). Il fatto è vero e documentato, ma conviene scrivere «(visto in e3)» per tenere la provenienza esatta.
- **M3. Denominatore della frase «in 48 corse nessun veto della nota».** Spec 16, piano sez. 5, sez. 6 e sez. 17 la presentano come prova che «il blocco non ha rallentato i lavori piccoli». Le 48 corse includono casi senza un implementatore che scrive (s4, s5, s7, s8, e1, e3, e5 solo in parte, s9 dove il dedicato non parte). I veti possibili sono molti meno. È vero alla lettera, ma pesa più di quanto misuri. Meglio dire quante corse hanno un implementatore che modifica (dal ledger: circa 27 corse hanno un implementatore che consegna o decide, contro 48).
- **M4. Elenco delle pagine che invecchiano: una citazione in più.** `docs/profili/verifiche/ai-fonti.md:20` cita «Google, gemini-api/docs/models» (la pagina spostata). Non con l'URL completo, quindi non cade nel grep del brief, ma è un riferimento alla stessa pagina in un file approvato. Una riga nel «Dopo B» voce 3 la renderebbe completa.
- **M5. Ruling 11 (`infisical sm run` / `secrets-manager run`) non è in 8.5.** Il testo dice «da dopo `run`» senza nominare le due forme che la ruling del controller aveva fissato (`progress.md` riga 11 della sezione Ruling). Il codice le copre (`prefix[:3]`). Un inciso basta.
- **M6. «Nessuno è un difetto aperto del codice di tollgate»** (piano sez. 5, quarto punto). Per le cinque piattaforma è vero. Per s12 la causa è una regola che manca in `rules-base`, cioè del prodotto, anche se non del codice. È già detto nel «Dopo B» voce 1; basta una virgola che lo distingua nella sez. 5.

## Valutazione

**Qualità del task:** Da correggere (lieve: un solo Important, correzione di una frase).
**Motivo:** La documentazione corrisponde al codice del ramo su tutti i punti verificati (involucri, tabella di Supabase, `take_pending`, `init --update`, `lookups.observed`, campagne, pulizia, conteggi). Il limite della piattaforma e la scelta su s12 sono nei posti giusti, nessun file approvato è toccato, nessun dato privato, nessuna frase «B chiusa». Resta I1, una frase di P5 («I nove casi») che contraddice la lista di dodici nella stessa sezione 14.
