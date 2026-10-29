# Revisione del Task 10 (commit 7e1aee2, base ad64d43)

Solo documentazione: spec del nucleo rev 27, piano principale di B, riga di stato nel progetto di B. Ho letto il diff, il rapporto della prova reale (versione corretta di ad64d43) e il rapporto delle verifiche, poi ho controllato le descrizioni sul codice di `bin/`, `hooks/`, `agents/`, `skills/`, `tests/`. Non ho rilanciato la suite.

## Controlli fatti (rischio -> controllo)

- Test citati nella sezione 8 del piano: script che associa ogni `test_*` al file indicato (`T\`test_x.py\``) e cerca `def <nome>` in quel file. 86 nomi, 0 mancanti.
- Matcher di `PostToolUse` (`hooks/hooks.json`), uscita anticipata e `UNNAMED_TOOLS` (`hooks/run:48-61`), `ATTRIBUTE_UNNAMED_TOOLS` vuoto (`research.py:26`): coerenti con 7.1 e 7.2.
- Via breve (`runner.py:174-205`): lavoro da `sessions.work_for_path`, `research = 1`, `subagents.touch`, `lookups.owner`, nessun `[components]`, nessun `session_seen`: coerente con 7.1 e con il glossario.
- `lookups.py` (`record`, `observed`, `owner`, `for_task`, `detach_tasks`, `note`, `prune`), `db.py:185-199` (migrazione 6), `housekeeping.py:40`, `scope.py:35`: coerenti con 12.2, 8.1, 8.2.
- `research_gate.py` (order 25, ordine delle condizioni, esclusioni, `_rules_enforced`, L0 solo sessione principale e solo Edit/Write, Bash di implementatore, reminder a `post_*` solo se la modifica è riuscita): coerente con la riga `PreToolUse` di 7.2.
- `cli_calls.py:57-65, 116-134` (divieto di `research submit` alla sessione principale, anche con programma non certo e comando non analizzabile): coerente con 3.1.
- `research_cmd.py` (codici 0/1/2, casi di rifiuto, `show`): coerente con la riga della tabella dei sottocomandi.
- `brief.py:182-201` e `taskcmd.py:87,359-362` (sezione «Nota di ricerca», `major` / `moderate`, `missing`, `first_diff_file`): coerenti con 8.6 e con il piano sezione 3.
- Esenzione MCP (`effects`), `DOC_MCP_TOOLS`, `apply.OPS` = 29 con `lookup` (`test_ops_count_is_29`), `skills/setup/SKILL.md:19`, `agents/implementer.md:4`, `phases.create_work(research=...)` da `start.py:497` e `adopt.py:349`: coerenti.
- Fatti della sezione 16 contro `docs/verifiche/2026-10-27-b1-verifiche.md` (B1-V1..V7) e `docs/verifiche/2026-10-27-b1-prova-flusso.md`: cifre di latenza, costi (0,41 + 0,50 = 0,91 USD), letture registrate (4 `read`, 1 `bash_read`, 1 `fetch`), prima consegna non valida per il glob di `cat`, nessun `research_reminder`, nessun `veto` di `research_gate`, versione di Claude Code e modello: tutti riportati correttamente. Eccezioni nei rilievi.

## Aderenza

- ✅ Step 1, tabella «Prove di B1» (piano sez. 8): copre ogni riga della tabella «Copertura»; i punti senza prova sono dichiarati con il motivo (obiettivi 3 e 5, «regole mai lette», 3.4, nomi dei modelli, profili, `rules-base` agli agenti, eval, L2 senza test dedicato, pertinenza del revisore solo in parte, `--fix` non col modello). Tutti i test citati esistono con quel nome e nel file indicato.
- ✅ Step 2, rev 27: tutte le sezioni richieste sono toccate (3.2, 7.1, 7.2, 8.1, 8.5, 8.6, 11.4, 12.2, 16, 18.4, riga 27 di 20) più 0, 3, 3.1, 11.3, 12.4. Le decisioni di `carry.md` per il Task 10 ci sono: D7 (glossario, 8.5 punto 3, 3.2 `record lookup` senza evento, 11.3), D18 («non tutte e due» e 8.000 caratteri in 8.1), esiti B1-V1..V7 e deroga di `adopt`. La frase «non si crede a quello che l'agente dice» è in 8.1.
- ❌ D8 (ruling del controller): la rev 27 12.2 non descrive il codice (rilievo I-1).
- ❌/⚠️ Sezione 16, riga della prova reale: un'attribuzione sbagliata (I-2) e omissioni dei limiti dichiarati nel rapporto (M-1).
- ✅ Step 3, piano principale: stato in testa, riga B1 della sezione 2, sezione 3 con i nomi reali (tutti verificati nel codice), sezione 9 con i rinvii a B2, B3-B7 e B8, incluso lo scan «punto 4» (s1, s2, s3, s9) e `_rules_enforced` con `OSError` come spento.
- ✅ Riga di stato nel progetto di B.
- ⚠️ Step 4 (suite e commit): affermato nel report (3121 test, 3.11 e 3.13, `-W error::ResourceWarning`), non rilanciato. Il diff è solo documentazione e `test_docs.py` non è toccato.
- ✅ In più: nessuna cosa non richiesta. Le nuove sezioni 8 e 9 del piano sono previste dal brief (prove, rinvii).
- «3.3 del progetto di B»: la spec del nucleo non ha una 3.3 (la 3.2 sono i principi di design). In 8.1 (spec riga 703) e 8.6 (riga 854) il rinvio è scritto come «controllo 3.3 del progetto di B» e porta il percorso del file del progetto: è chiaro per chi legge, e i criteri veri stanno in 8.1. Va bene così; vedi M-4 per un ritocco facoltativo.

## Punti di forza

- Le descrizioni del comportamento sono quasi tutte esatte contro il codice, anche nei dettagli fragili: `Grep` dormiente, via breve che non legge `[components]`, `Source.ref` di context7 senza prefisso, limiti reali di `cat` con glob e `cat < f`, `OSError` come interruttore spento.
- La tabella delle prove distingue con onestà cosa è provato da un test, cosa dalla prova reale e cosa non è provato (permessi interattivi di `WebFetch`, `--fix` col modello, L2).
- La sezione 9 del piano porta rinvii concreti e azionabili (`FileNotFoundError`, scan di B8, `Grep` da rimettere con una riga).

## Rilievi

### Critical
Nessuno.

### Important

**I-1. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:1280` (12.2, «Lavori in corso all'approvazione di `rules-base`») non descrive il codice e contraddice la ruling D8.**
Il testo dice: «Un task in cui l'implementatore ha già ricevuto l'avviso ma non ha una nota valida è negato alla modifica successiva, e dai task seguenti vale il rifiuto alla prima modifica». `research_gate._verdict` (`bin/tollgate_checks/research_gate.py:90-117`) legge l'interruttore a ogni modifica (`_rules_enforced`, riga 112) e, se acceso e senza nota valida, restituisce `deny` per qualunque task in corso, abbia o no ricevuto l'avviso. Un task in corso che non ha ancora toccato un file non rientra in nessuna delle due frasi della spec, e «dai task seguenti» fa credere che il task in corso abbia un trattamento diverso: è proprio la formulazione che la ruling dichiara superata. Il piano principale (sezione 9, riga 167) è invece corretto («il rifiuto vale dalla prima modifica senza nota valida»), quindi spec e piano ora si contraddicono.
Correzione: riscrivere la voce come nel piano, per esempio «quando l'interruttore si accende (B2), il rifiuto vale dalla prima modifica senza nota valida successiva, anche nel task in corso e anche per un implementatore che ha già ricevuto l'avviso; il messaggio di rifiuto dice come consegnare la nota».

**I-2. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:1686` (16, riga della prova reale): «piano di un task scritto e registrato dal modello» attribuisce al modello la registrazione.**
Il rapporto (`docs/verifiche/2026-10-27-b1-prova-flusso.md`, righe sul passo 1 e sul piano) dice che il modello ha scritto e committato il piano (`c568a8b`) e che l'ha registrato tollgate (evento `scope_registered`, `seq` 4). La ruling del controller lo elenca come fatto da riportare così. Correzione: «piano di un task scritto e committato dal modello e registrato da tollgate (`scope_registered`)».

### Minor

**M-1. Sezione 16, stessa riga (spec:1686), e piano sezione 8 riga «7 prova reale L1» (piano:155): omissioni di fatti che il rapporto dichiara.**
Mancano: il ramo di `passo2` che scrive il piano con `Write` non è stato esercitato; il `WebFetch` della sessione principale nel passo 1 non è in `lookups` (decisione 5, è il comportamento voluto); `prepara` ricopiato dal controller (lo script non ne salva l'uscita); token degli agenti 46.532 + 27.783 = 74.315; l'avviso `ICON_MISSING` (e `README_MISSING`) di `validate`, che non cambia l'esito (B1-V7 nella spec dice solo «Positivo»). Non sono errori, ma sono limiti della prova che il lettore della spec non trova. Almeno il ramo `Write` non esercitato e il `WebFetch` principale vanno detti nella riga o nei «Limiti».

**M-2. Spec 7.1, paragrafo «Latenza» (riga 607): i 250 ms sono un limite inferiore.**
Il Task 4 ha rilevato (`task-4-review.md`, M1, rinviato) che la serie `Read` da subagente rilegge lo stesso file, quindi dopo il riscaldamento `lookups.record` non fa né `INSERT` né commit. La spec riporta «mediana 250 ms» come misura della via breve senza il caveat; una prima lettura di un file nuovo costa di più. Aggiungere «(caso ripetuto: limite inferiore)». Nota anche che la frase «il costo dominante è l'avvio di Python» è una deduzione, non una misura: il rapporto delle verifiche la chiama così.

**M-3. Piano, stato in testa (piano:8) e riga B1 della sezione 2.** Dicono «B1 chiusa sul ramo», ma la riga B1 elenca tra i criteri «revisione finale senza `critical` né `important` aperti» e la sezione 5 chiede la revisione finale chiusa; non risulta ancora fatta (il report del Task 10 lo ammette). Il testo è quello prescritto dal brief, ma finché la revisione finale non c'è conviene scrivere «costruita sul ramo, revisione finale in corso» e passare a «chiusa» quando il controller la chiude.

**M-4. Chiarezza di «3.3» (spec 703, 854).** Facoltativo: aggiungere in 8.1 una frase «i punti 1-4 del progetto 3.3 sono (a)-(e) qui sotto», così chi cerca «3.3» nella spec del nucleo (che non ha quella sezione) trova il collegamento senza aprire il progetto di B. Il piano sezione 8 usa già «3.3 punti 1-4» nella colonna «Punto del progetto».

**M-5. Spec 12.2 (riga 1242): «una terna (work, task, kind, target)» sono quattro elementi.** Ripete l'imprecisione del docstring di `lookups.record` (`bin/tollgate_core/lookups.py:27`). Scrivere «quaterna» o «la stessa combinazione di».

**M-6. Spec 7.2, riga `PreToolUse` della nota: non dice dove gira `research_gate` rispetto agli altri controlli.** `order` 25 (`research_gate.py:20`): dopo `writes`, `bash_rules`, `agents` (20) e `cli_calls` (5), prima di `effects` (30). Siccome «il primo `deny` vince» (3.2), un rifiuto di scope o di regole Bash precede quello della nota. Una riga lo renderebbe esplicito; non è richiesta dal brief.

**M-7. Piano sezione 9, A B3-B7.** Dal triage finale del ledger (`final-deferred.md`) due rinvii toccano chi copia l'implementatore e potrebbero starci: l'avviso su `TOLLGATE_` nel testo della nota è solo in `agents/implementer.md` e non nel brief (Task 8), e `research submit` non sa chi lo chiama, quindi con più implementatori un subagente potrebbe consegnare la nota di un altro task `running` (Task 6, limite di progetto). Se il controller li lascia al triage finale va bene.

## Valutazione

**Aderenza ai requisiti:** Da correggere (I-1 contraddice una ruling esplicita del controller; I-2 è un fatto sbagliato rispetto al rapporto).
**Qualità del task:** Da correggere.
**Motivo:** La documentazione è molto accurata rispetto al codice e le prove sono complete e oneste, ma la voce 12.2 sul trattamento dei lavori in corso non rispecchia il comportamento e la ruling D8, e la riga della prova reale in 16 attribuisce al modello la registrazione del piano. Due correzioni di testo, nessuna al codice; poi il task è approvabile.
