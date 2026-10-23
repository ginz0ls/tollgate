# Brief per la sessione che scrive il piano P5

Questa sessione parte con il contesto pulito. Scrive il piano P5 di tollgate (eval e CI, ultimo piano del nucleo) e **non lo esegue**. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Da leggere, in quest'ordine

1. La memoria del progetto: `plugin-workflow-decisioni.md` (soprattutto le voci P0, P3a, P3c, P4 e «Piano P4 scritto»), `feedback-domande.md`, `sessioni-nei-worktree.md`, `p1-rilievi-rinviati.md` (i minori di P1 destinati a P5) e `github-500-transitorio.md`.
2. `docs/superpowers/plans/2026-10-08-tollgate-nucleo-piano-principale.md`, per intero. Contano soprattutto:
   - la riga P5 nella tabella dei piani (i 9 casi di `claude plugin eval`, la Action di CI del repo di tollgate, documentazione d'uso; «Eval con 3 esecuzioni per caso; CI verde»);
   - la sezione 3: ogni riga con destinazione P5, in particolare «Vincoli e rinvii per P5» di P4 (sei punti: fissaggio delle azioni per SHA, eval su ciò che le prove reali non hanno esercitato, limiti di 1.2 come documentazione d'uso, rinviati di P3c con motivo, CI con spazi nel percorso, cache `workflow_run` sul privato), i rinviati di P3a, P3b e P3c verso P5, e la sezione «Minori rinviati di P4» (compresi M-1, M-3, M-4, M-5, M-9 della revisione finale e i due residui);
   - la matrice dei criteri, con le colonne «Resta a» che puntano a P5, e le tabelle delle prove dei piani precedenti;
   - la sezione 5 (rischi), in particolare «Costo degli eval in P5».
3. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, alla revisione 25. È l'autorità. Per P5 contano: la sezione 14 (livelli di test, i 9 casi di eval, la CI come GitHub Action sul repo di tollgate), la 15 (criteri), la 1.2 (limiti da documentare), la 17 (cosa resta aperto), la 11 (skill e comandi da documentare) e le revisioni 20-25.
4. Gli esiti reali: `docs/verifiche/2026-10-21-p4-verifiche.md`, `docs/verifiche/2026-10-21-p4-prova-gate.md`, `docs/verifiche/2026-10-21-p4-prova-flusso.md` e le prove di flusso di P3a, P3b e P3c in `docs/verifiche/`. Dicono che cosa è già stato esercitato da un `claude -p` e che cosa no.
5. `docs/superpowers/plans/2026-10-21-tollgate-p4-gate.md`, come modello di forma, con i suoi compagni `2026-10-21-tollgate-p4-esecuzione.md` e `2026-10-21-tollgate-p4-brief-sessione.md`.
6. `docs/sdd/2026-10-21-tollgate-p4-gate/`: `README.md`, `progress.md` (le `Ruling:` e i minori rinviati), `final-review.md`, `final-rereview.md` e `cautele.md`.
7. La documentazione reale di `claude plugin eval` (formato dei casi, sandbox, JSON e report, uso in CI): va verificata sulla versione installata (`claude plugin eval --help`, e il subagente `claude-code-guide` per la documentazione), non presa a memoria. Se un fatto serve al disegno e non si ricava senza eseguire, va nel Task 1.
8. Il codice reale di `main`: `tests/` (struttura della suite, `tests/run`, `tests/flowkit.py`, `tests/fakegh.py`), `spikes/` (gli script delle prove reali), `.claude-plugin/`, le skill in `skills/` e gli agenti in `agents/`.

## Cosa deve fare il piano

- **Metodo.** Si scrive con `superpowers:writing-plans`.
- **Forma.** Firme e test, non codice completo. Gli implementatori sono sonnet.
- **Ambito.**
  - I 9 casi di eval della spec 14, con 3 esecuzioni per caso, più quelli che coprono ciò che le prove reali di P3c e P4 non hanno esercitato (punto 2 dei «Vincoli e rinvii per P5»), o il motivo per cui un caso resta ai test dal programma vero.
  - La CI del repo di tollgate: GitHub Action con la suite (`tests/run` su Python 3.11 e 3.13, anche con `-W error::ResourceWarning`), in un checkout con spazi nel percorso oppure con i test che ne dipendono corretti.
  - Il fissaggio per SHA delle azioni dei workflow del gate.
  - La documentazione d'uso: installazione, skill e comandi, modalità `protected` e `detect`, limiti di 1.2 della rev 25, emergenze e aggiornamenti.
  - I rinviati con destinazione P5, oppure la motivazione del rinvio a dopo la v1.
- **Task 1.** Verifiche reali solo per i fatti non ancora provati e necessari al disegno. Per esempio: forma e costo reale di un caso di `claude plugin eval`, e la sua sandbox (rete, `gh`, `~/.claude`); una Action sul repo di tollgate; la cache in sola lettura dei job `workflow_run` sul privato.
- **Penultimo task.** Gli eval reali (3 esecuzioni per caso) e la CI verde sul repo vero, con il costo misurato e riportato (token, tempo, minuti di Actions).
- **Ultimo task.** Le prove dei criteri, la revisione 26 della spec, l'aggiornamento del piano principale e la chiusura del nucleo (che cosa resta per dopo la v1).
- **Criteri.** Chiude quelli assegnati a P5 nella matrice.

## Domande da fare all'utente prima di scrivere i task

Sono compromessi veri: si chiedono, ognuno con una raccomandazione.

1. **Repo di tollgate su GitHub.** Il repo del plugin oggi **non ha un remote**. La CI della spec 14 richiede un repo GitHub. Domande:
   - si crea, e con quale nome;
   - pubblico o privato. Il privato consuma i minuti di GitHub Free; il pubblico rende visibile il codice prima della v1;
   - chi fa il primo push, e quali operazioni sono ammesse alla sessione che esegue.
2. **Costo degli eval.** 9 casi o più, 3 esecuzioni ciascuno, con il modello vero. Una prova di flusso con il modello costa da centinaia di migliaia a oltre 500k token. Domande:
   - il budget massimo;
   - quale modello usare;
   - se gli eval girano solo in locale dal controller oppure anche in CI. In CI servirebbe una chiave API come segreto del repo: da chiedere esplicitamente, perché oggi i segreti sono vietati.
3. **Repo di prova di P4.** `ginz0ls/tollgate-p4-protected` è pubblico e contiene il CLI; `ginz0ls/tollgate-p4-detect` è privato. Domanda: si riusano in P5, per il fissaggio delle azioni e la cache sul privato, o si cancellano. Li cancella l'utente.

Le risposte finiscono nelle decisioni del piano e nelle cautele di esecuzione. Fuori da ciò che l'utente autorizza restano vietati push in rete, `gh auth`, `gh api` in scrittura, segreti, `gh repo delete` e cambi di visibilità.

## Lezioni di P4 da portare nel piano

- **GitHub vero non è deterministico.** Arrivano 500 a corpo vuoto anche sui POST, e `gh pr edit` è rotto con gh 2.46 (si usa la PATCH REST). Con un controllo non obbligatorio rosso `mergeStateStatus` vale `UNSTABLE`. Un caso reale va scritto per essere ripetuto, con l'esito di ogni tentativo registrato: la prova composita di P4 ha richiesto fino a quattro tentativi per caso.
- **Controller in prima persona per GitHub vero e `claude -p`**, con un wrapper che registra e filtra ogni comando `gh`. Le evidenze vanno committate e il controllo dei comandi va fatto alla fine. Un falso positivo del controllo (P4: `ghguard.py`) fa fallire la suite: il controllo ha i suoi test.
- **Aggiornare il codice installato in un repo protetto** richiede una procedura: togliere la protezione, push, attesa del check-run `tollgate-base` finito, `protect.sh`. Il piano la scrive se la serve.
- **Tempi della suite.** Con 2465 test una corsa dura da 19 a 31 minuti quando la macchina è carica. Le istruzioni di esecuzione lo mettono in conto e dicono ai subagenti di non restare fermi ad aspettare notifiche: ciclo `until` limitato o lettura del file di output.
- **Breaker.** Il Task 16 di P4 è arrivato al giro 5 e oltre. Un task di prova reale va diviso tra preparazione (script con test) ed esecuzione (controller), con le correzioni del prodotto come giri del task di esecuzione.
- **Workspace e registro.** Il workspace SDD sta nel worktree e si copia in `docs/sdd/` alla chiusura. La riga «Stato» del piano principale non deve citare `.superpowers/` (è ignorato da git).

## File da scrivere (sul modello di P4)

- `docs/superpowers/plans/2026-10-23-tollgate-p5-eval-ci.md`: il piano, con la tabella Copertura che porta ogni criterio, vincolo e rinviato al suo task.
- `docs/superpowers/plans/2026-10-23-tollgate-p5-esecuzione.md`: come eseguirlo con `superpowers:subagent-driven-development`.
  - **Dove:** ramo `p5-eval-ci`, in un worktree sotto `.claude/worktrees/p5`.
  - **Come:** i modelli, lo scan pre-flight, le Ruling nel ledger, la revisione finale su opus, la suite tre volte (anche con `-W error::ResourceWarning`).
  - **Regole di cautela nel brief di ogni subagente, al lancio.** Le stesse di `docs/sdd/2026-10-21-tollgate-p4-gate/cautele.md`, con le sole eccezioni autorizzate dall'utente, scritte una per una.
  - **Chiusura:** niente merge senza l'OK dell'utente; registro in `docs/sdd/` con un `README.md`, memoria aggiornata, repo lasciati come l'utente ha deciso.
- `docs/superpowers/plans/2026-10-23-tollgate-p5-brief-sessione.md`: il brief per la sessione che esegue il piano.

## Come lavorare

- Prima di consegnare, il piano passa a un revisore opus a contesto pulito, che lo confronta con la spec rev 25, con il piano principale e con il codice reale di `main`. I rilievi vanno corretti, e dopo le correzioni una ri-revisione mirata.
- All'utente si chiedono solo le scelte che sono compromessi veri (le tre domande qui sopra). Il resto si decide e si registra nel piano, tra le decisioni. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere.
- I tre file si committano su `main`, con la riga `Co-Authored-By` del modello.
- Testi in italiano, identificatori in inglese. Risposte all'utente brevi.

## Stato al momento di questo brief

- `main` contiene P4 (fino a `6c59a24`, fast-forward) e il suo registro. La suite su `main` ha 2465 test verdi su Python 3.11 e 3.13.
- Sulla macchina: Claude Code 2.1.309, `gh` 2.46.0, Superpowers 7.0.0. Il worktree `.claude/worktrees/p4` e il ramo `p4-gate` esistono ancora: non toccarli.

## Hai finito quando

- i tre file sono committati su `main`;
- il piano copre ogni criterio, vincolo e rinviato destinato a P5, o ne motiva il rinvio;
- la revisione del piano non ha rilievi critical o important aperti;
- hai consegnato all'utente, in italiano, un riepilogo breve (numero di task, decisioni prese, domande aperte) e il prompt `/goal` per la sessione che eseguirà il piano.
