# Brief per la sessione che scrive il piano di C2 (profilo `security`)

Leggi questo file per intero prima di fare qualsiasi altra cosa. Questa sessione **scrive** il piano di C2 e i documenti per eseguirlo, e **non lo esegue**.

## Cosa scrivere

Quattro file, con la data del giorno in cui li scrivi nel nome (qui sotto `<data>`), sul modello di quelli di C1 (`docs/superpowers/plans/2026-11-20-tollgate-c1-tracciamento-locale.md`, `-esecuzione.md`, `-brief-sessione.md`, `-brief-goal.md`) e, per la parte del profilo, di quelli di B7 (`docs/superpowers/plans/2026-11-12-tollgate-b7-profilo-database.md` e gli altri tre):

1. **Il piano di C2**, `docs/superpowers/plans/<data>-tollgate-c2-profilo-security.md`, con `superpowers:writing-plans`. Contiene:
   - «Fatti verificati», con la fonte di ogni fatto;
   - «Global Constraints»;
   - «Decisioni di questo piano», ognuna con il costo se sbagliata;
   - la tabella delle precedenze con gli altri sei profili (`base`, `ai`, `infra`, `backend`, `frontend`, `database`), provata con una sonda sui frammenti veri;
   - «Review Focus», «Mappa dei file», «Copertura»;
   - i task, con firme e test, non con il codice (gli implementatori sono sonnet);
   - la tabella «Revisione del piano» in fondo.
2. **Le istruzioni d'esecuzione**, `<data>-tollgate-c2-esecuzione.md`: ramo `c2-profilo-security`, worktree `.claude/worktrees/c2`, sessione avviata dalla radice del repo; scan pre-flight; ordine e modelli; regole di cautela con le sole eccezioni del controller, una per una; quando fermarsi e chiedere; chiusura.
3. **Il brief della sessione d'esecuzione**, `<data>-tollgate-c2-brief-sessione.md`, con «Il lavoro è finito quando».
4. **Il brief corto per l'obiettivo**, `<data>-tollgate-c2-brief-goal.md`. In testa deve avere la sezione `## Prompt per /goal`, con il testo esatto da incollare dopo `/goal`. Poi ha «Finito quando» scritto a situazioni, come quello di B7:
   - regole approvate;
   - regole rinviate;
   - in attesa dell'utente;
   - fermata per un altro caso.

   Usa le righe esatte del ledger. Vedi la lezione sul transcript, più sotto: è vincolante.

Solo documenti: nessun codice, nessun `claude -p`, nessun eval. Rete solo per leggere con `WebFetch` le pagine ufficiali che servono ai fatti del piano. Lavora su `main`, con un commit per ogni passo e per ogni giro di revisione.

## Da leggere, in quest'ordine

1. **La memoria del progetto**: `plugin-workflow-decisioni.md` (voci di B7, B8, C e la riga «- C1 eseguito»), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.
2. **Il progetto di C** `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`.
   - Sezione 11 per intero: è l'autorità per C2.
   - Sezioni 2, 12 e 14.
   - Le scelte marcate «utente» non si discutono. Quelle marcate «mia scelta» si correggono solo con un motivo scritto nel piano.
3. **Il piano principale di C** `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`: sezione 1 (regole 1-6, soprattutto la 3 e la 4), riga C2 della sezione 2, riga «C2 → C3» della sezione 3, sezioni 6, 7 (decisione 4: Fable) e 8 (rinvii, con quelli di C1).
4. **Il catalogo** `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`:
   - riga `security` delle sezioni 2, 2.1 e 2.3;
   - riga `rules-security` della sezione 4;
   - le note sul modello e sul prefisso delle regole;
   - le righe di `ci`, perché `final-security` serve anche a C3.
5. **Il progetto di B** `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`: come si costruisce un profilo (sezioni 3.4, 4, 5, 11-14), con l'approvazione dell'utente prima che il blocco si accenda.
6. **La spec del nucleo**, oggi alla revisione 36 (C1): 6.3 (precedenza per segmenti letterali), 7.1, 7.3, 8.5, 8.7, 11.2, 16, 18.4, 20, e le parti sulla revisione finale L2 e sugli specialisti finali (`final_specialist`, `dod.specialists`).
7. **Il profilo modello più recente**, B7 (`database`, con il primo specialista finale di area):
   - `skills/rules-database/SKILL.md`, `templates/profiles/database.toml`, `docs/profili/database.md`, `docs/profili/verifiche/database-fonti.md`;
   - `agents/implementer-database.md`, `agents/reviewer-database.md`, `agents/final-database.md`;
   - `tests/test_rules_database.py` e la classe di test delle precedenze di `database` in `tests/test_init.py`;
   - il caso `database` di `spikes/run-b1-flow.sh`;
   - il registro `docs/sdd/2026-11-12-tollgate-b7-profilo-database/`.
8. **Il registro di C1** `docs/sdd/2026-11-20-tollgate-c1-tracciamento-locale/` (`README.md`, `progress.md`, `cautele.md`, `final-review.md`, `rapporto-merge.md`): il metodo più recente e le sue lezioni.
9. **Il codice reale di `main`**:
   - la proposta dei profili: `bin/tollgate_flow/init.py` (`profile_blocks`, `SOURCE_EXTENSIONS`, `EXCLUDED_PREFIXES`);
   - la scelta a runtime: `bin/tollgate_analysis/profiles.py` (`vertical_for`);
   - i subagenti di sola lettura: `bin/tollgate_core/config.py` (`review.readonly_agents`, `is_readonly`, che conta anche `<plugin>:reviewer-*` e `<plugin>:final-*`);
   - i test di deriva degli agenti di area in `tests/test_manifest.py` (`AREAS`, `FINAL_AREAS`, `test_area_agents_derive_from_generic`).
10. **Le fonti delle regole**, elencate nel catalogo:
    - `security-and-hardening` e `security-auditor` di agent-skills (MIT): sono installate sulla macchina, le copie le fa il controller;
    - `insecure-defaults` e `differential-review` di Trail of Bits e OWASP ASVS, che sono CC-BY-SA: solo idee, con parole nostre, mai testo;
    - la licenza di ogni fonte si verifica sulla pagina ufficiale, con `WebFetch`.

## Scelte dell'utente, da non riaprire

- `security` è una fetta a sé (C2), costruita con **Fable** (`claude-fable-5-2`) dove serve giudizio: la verifica delle fonti, la scrittura delle regole, la revisione del piano, la revisione finale. Gli implementatori meccanici restano sonnet (progetto di C 11, piano principale, decisione 4).
- Il profilo è quello del catalogo: si accende su `**/auth/**`, `**/middleware.*`, `**/*session*`, `**/security/**`, `**/rls/**`; livello minimo **L2**; implementatore e revisore di area; specialista finale `final-security`, che C3 userà anche per `ci`.
- Le regole nascono come in B2-B7:
  - una bozza con la fonte di ogni regola;
  - la verifica delle fonti da parte di un agente di sola lettura;
  - una pagina in parole semplici;
  - l'approvazione dell'utente.

  Senza approvazione il profilo non si propone. Il codice si può unire anche prima, con il profilo spento (piano principale, regola 4).
- I profili approvati (`base`, `ai`, `infra`, `backend`, `frontend`, `database`) non si toccano. Dove una regola di `security` si sovrappone a una già approvata (i segreti di `backend` e `database`, la RLS di `database`), la pagina del profilo lo dice e l'utente decide all'approvazione.
- Le prove dal vivo l'utente le fa tutte alla fine, con C6 (scelta del 22/11/2026). La prova reale corta di C2 con `claude -p`, come le fette di B, resta: la fa il controller.
- Il repo `ginz0ls/tollgate` è pubblico: dalle pagine e dalle skill si prendono fatti con parole nostre, mai testo intero. Niente nomi di progetti privati, nome utente, host o token.

## Punti aperti da decidere nel piano

- **I percorsi del catalogo contro gli altri profili.** Per ognuno decidi forma e costo, provati con la sonda su `init.profile_blocks` e `profiles.vertical_for` con i frammenti veri a ogni giro di revisione. Scrivi separati i costi di proposta e quelli di runtime: `exclude` ed `EXCLUDED_PREFIXES` decidono solo la proposta.
  - `**/middleware.*`: per esempio `middleware.ts` di Next.js, oggi di `frontend`, o un middleware di server, di `backend`.
  - `**/auth/**` dentro `server/`, `api/`, `routes/` (`backend`) o `supabase/functions/` (`database`).
  - `**/rls/**` contro `supabase/**` e `**/*.sql` di `database`.
  - `**/*session*`, che può accendere file che con la sicurezza non c'entrano.
  - `**/security/**` contro `.github/` e contro il gate.
- **Il rilevamento per contenuto.** Decidi se servono marcatori (librerie di autenticazione, hashing di password, JWT, cookie di sessione), con quale pagina ufficiale ciascuno, e quanto costano. Ricorda la regola di I-1: un file trovato per contenuto da un profilo non accende un altro profilo per la sola cartella.
- **`final-security`.**
  - Da cosa deriva (`agents/final-database.md`, `agents/final-reviewer.md`) e cosa riceve nel brief.
  - Se precarica `rules-security`, e come la tratta `is_readonly` (oggi un `final-*` è già di sola lettura).
  - Come lo coprono i test di deriva (`FINAL_AREAS` oggi ha solo `database`).
  - Quale modello usa, in accordo con il catalogo (`inherit` per `security`) e con la decisione 4 del piano principale (Fable).
  - Cosa guarda: la revisione del diff per rischio e raggio d'azione, secondo il catalogo 2.1.
- **Il `dod`.** Il catalogo 2.3 propone «test dei casi di accesso negato». Decidi come diventa un `dod` che dipende dal progetto, sapendo che i comandi del `dod` girano senza veto (spec 8.7).
- **Le sovrapposizioni con le regole approvate** (segreti, RLS, input non fidato): come le dice la pagina, e cosa chiede l'utente all'approvazione.
- **La prova reale.** Serve un lavoro L2 di sicurezza verificabile con la sola libreria standard di Python. Lo script è `spikes/run-b1-flow.sh`, con un caso nuovo come `database` in B7: decidi fino a dove arriva (anche la revisione finale con `final-security`) e quanto costa sull'abbonamento.
- **Quali rinvii chiude C2**, tra quelli della sezione 8 del piano principale di C e del blocco «Dopo B». Gli altri restano aperti, con il motivo.
- **Se C2 è abbastanza piccola o va divisa**, e dove la sessione d'esecuzione si ferma per l'approvazione delle regole.

## Lezioni di C1 da mettere nel piano e nelle istruzioni

- **Condizioni di fine verificabili sui file, mostrate alla fine (vincolante).** In C1 l'hook di Stop ha giudicato «Finito quando» su un transcript compattato. Le prove scritte nei primi messaggi della sessione (letture dei brief, titoli del rapporto prima del merge) non le vedeva più, e ha bloccato la chiusura in loop per ore anche con tutti i file in regola. Quindi, nel brief-goal di C2:
  - ogni condizione si controlla **leggendo un file su `main` o nel worktree**, mai solo il transcript;
  - il rapporto prima del merge si salva **anche** in un file del workspace (`rapporto-merge.md`), e si controlla da lì;
  - le decisioni prese dopo il rapporto del merge non si scrivono come righe `Ruling:`, ma come note: la condizione «una riga per ogni `Ruling:`» vale al momento del rapporto;
  - alla fine la sessione lancia **uno script di verifica** che stampa l'esito di ogni condizione, e ne mostra l'uscita nel suo ultimo messaggio. Lo script lo scrive questa sessione, nel brief-goal o accanto, e lo prova a secco.
- **La suite sotto carico** dura 1-2 ore per corsa (due interpreti). Il brief di ogni implementatore ha le tre righe della suite: uscita su file, attesa `until grep -q '^exit '` in primo piano, commit dopo `exit 0`.
- **I file nuovi vanno aggiunti a git prima della suite.** `tests/test_b1_scripts.py` copia il plugin dai soli file tracciati.
- **La CI di GitHub annulla la corsa precedente** quando arriva un push nuovo sullo stesso ramo (`cancel-in-progress`). Dopo il merge, i commit di documenti si inviano tutti insieme o a CI finita.
- **Revisioni in parallelo** solo su file diversi e con una `Ruling:`. Il revisore legge con `git show` e lancia i test su una copia `git archive`, mai nel worktree vivo. Due implementatori insieme mai.
- **I subagenti rimasti dalle sessioni vecchie** compaiono in `ListAgents` e l'hook li conta come lavori in corso. A fine sessione si fermano con `TaskStop` solo quelli della sessione, e si scrive quali.

## Come lavorare

- **Domande all'utente.** Si chiedono le scelte vere (compromessi, costi), in parole semplici, con il costo esplicito (gratis, consumo dell'abbonamento o spesa vera) e un consiglio. Le risposte si scrivono nel progetto di C, sezione 11, con la data. Miglioramenti utili, compatibili e a basso costo si fanno senza chiedere. Il resto si decide con una `Ruling:` scritta nel piano.
- **Revisione del piano.** La fa **Fable** (`claude-fable-5-2`) a contesto pulito, in sola lettura, a giri, finché un giro dice «pronto» con 0 critical e 0 important. I minor si correggono. La tabella dei giri va in fondo al piano. Le regole di cautela vanno nel brief di ogni subagente, al lancio.
- **Commit e push.**
  - Bastano `python3 -B -m unittest tests.test_docs` verde e `git status` pulito, perché si toccano solo documenti.
  - Il push si fa solo verso `https://github.com/ginz0ls/tollgate.git`, dopo `P4_PROFILE=p5 python3 -B spikes/gh-p4/ghguard.py gitcheck -- push https://github.com/ginz0ls/tollgate.git main` uscito con 0. Il repo locale non ha un remoto.
  - Se un commit trova `.git/index.lock`, ritenta dopo qualche secondo; non cancellarlo mai (la cartella è sincronizzata da MEGA).
- **Controlli su nome utente, host e token.** In questa shell `grep` è una funzione che salta i binari e i file ignorati: usa `/usr/bin/grep -ra`.
- **Lingua.** Testi in italiano, identificatori in inglese. Risposte all'utente brevi e semplici.

## Stato al momento di questo brief (22/11/2026)

- **`main`** contiene il nucleo, B e C1 completi. Il merge di C1 è `e0929a8`, il registro è in `docs/sdd/2026-11-20-tollgate-c1-tracciamento-locale/`, la spec del nucleo è alla revisione 36. Tutto è inviato a GitHub, e la CI di `main` è verde.
- **Suite:** 4349 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- **Sulla macchina:** Claude Code 2.1.329, `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0. Nessun worktree aperto.

## Finito quando

Ogni punto si controlla leggendo un file. Alla fine lancia i controlli e mostrane l'uscita nell'ultimo messaggio.

- Questo brief e i quattro file del piano di C2 sono su `main`, committati e inviati a GitHub: `git ls-tree main` li mostra, e `git ls-remote https://github.com/ginz0ls/tollgate.git main` dà lo stesso SHA di `git rev-parse main`.
- L'ultima riga della tabella «Revisione del piano» del piano di C2 dice «Pronto», 0 critical, 0 important.
- Il brief-goal di C2 ha la sezione `## Prompt per /goal` e lo script di verifica di «Finito quando», provato a secco.
- `plugin-workflow-decisioni.md` nella memoria ha una riga che comincia con «- Piano C2 scritto».
- L'utente ha ricevuto, in italiano semplice:
  - cosa fa C2;
  - le scelte chieste e le risposte;
  - quanto costerà eseguirla;
  - quando dovrà approvare le regole;
  - il testo per `/goal`, copiato dalla sezione `## Prompt per /goal`.
