# Task 9: report

## Cosa ho fatto (solo documenti, nessun codice)

- `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`, revisione 34: intestazione; 4 (lo specialista finale esiste: `final-database`); 6.3 (diagramma e bullet «Giro di correzione in una sessione nuova», bullet «Gli agenti di `database` e lo specialista finale», profilo attivo per un `.sql` sotto un'altra cartella che alza il lavoro a L2, task misti, derivazione, P14 aggiornato, tabella Q1-Q47 con proposta, runtime e costo); 7.1 e 7.3 (`reviewer-database` e `final-database` di sola lettura); 8.5 (regola chiusa di Supabase con la tabella dei comandi, `REMOTE_FLAGS`, opzioni globali, ripiego testuale, lanciatori, Prisma e Drizzle, scelta dell'utente del 12/11, costo di `--local` deprecato, CLI 2, limiti); 8.7 (`dod` di `database` vuoto con l'esempio); 10 (specialista e `checklist` nel brief); 11.2 (rilevamento per contenuto di `database`, `supabase/**` e `prisma/**` alla radice, nessun `exclude`, `_concrete_paths`, `final_specialist` solo con l'agente presente, limite D12); 11.4 (`readonly_agents`, commento di `checklist` D11, frammento di `database`, `exclude`); 16 («Verificato in B7»: CLI 3, CLI 2 non verificata, struttura, RLS, PostgreSQL 18, Prisma e Drizzle, licenze, progetti sul disco, prova reale L2; «Ancora da verificare» aggiornato); riga 34 della sezione 20.
- `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`: intestazione, sezione 2 (riga `database` con i 4 pattern veri senza `**/schema.*`, marcatori, nota sulle graffe chiusa), 2.1 (`database-reviewer` non è fonte, `rules-database` precaricata, `final-database`), 2.2 (`WebFetch` per `reviewer-database`), 2.3 (`dod` vuoto), 4 (fonti vere), 6.
- `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md`: stato in testa, riga B7 della sezione 2, riga B7 → B8 della sezione 3, sezione 9 (rinvii chiusi o aperti con il motivo, blocco «A B8, da B7»), nuova sezione 16 «Prove di B7» con ogni riga della tabella «Copertura» e le prove oltre la tabella.
- `docs/superpowers/specs/2026-10-27-tollgate-b-profili-design.md`: solo la riga di avanzamento (B6 unita, B7 eseguita).
- Non toccati: pagine, skill e frammenti approvati; nessun codice.

## Scelte e scostamenti

- Il numero dei test della suite nel piano principale (4061, skipped 13 e 11) viene dall'ultima suite del Task 8; i file di questo task sono solo documenti. Il log di questo task conferma il numero (vedi sotto).
- La tabella Q1-Q47 della spec è generata dalla tabella di `decisions.md` (Q1-Q44) più Q45-Q47 di D15, con la colonna «Proposta» in più rispetto a quella di B6.
- Il registro `docs/sdd/` di B7 non esiste ancora: non l'ho citato nello stato (lo archivia l'unione, come B6).
- Nella sezione 16 della spec e in quella del piano non ho attribuito test dove non esistono (profilo attivo a runtime: scritto, come per B6, senza test nuovo).
- Nel testo ho scritto «dalla memoria del controller, non da una pagina» per la CLI 2, come chiede la regola «mai assunzioni».

## Test

- `tests.test_docs`, `tests.test_rules_database`, `tests.test_fragments`: 93 test OK prima della suite.
- Suite completa: `suite-task-9.log`.

## Dove ho portato ogni `Ruling:` del ledger (`progress.md`, in ordine di riga)

| Riga | Ruling | Dove |
|---|---|---|
| 9 | (a) opzioni globali della CLI 3 | spec 8.5 (opzioni globali), 16 (CLI 3) |
| 10 | (a) `inspect report`, `snippets list`/`download` | spec 8.5 (tabella), 16 |
| 11 | (a) `migration up/down/fetch`, `seed buckets`, `repair` | spec 8.5 (tabella: `unless_local`/`with_remote`), 16 |
| 12 | (a) CLI 2 | spec 8.5 («CLI 2»), 16 (riga «CLI di Supabase 2»); piano principale sezione 9, blocco «A B8, da B7» (Prisma, Drizzle e la CLI di Supabase) |
| 13 | (a) gruppi non nominati (`whoami`, `config pull`/`diff`, `backups list`, `snippets download`, …) | spec 8.5 (riga «tutto il resto», costi del permesso) |
| 14 | (b) Prisma 7 e 8 | spec 8.5 (Prisma e Drizzle), 11.4 (Prisma 8 e `contract.prisma`), 16; piano principale blocco «A B8, da B7» (Prisma 8 e `init --db`) |
| 15 | (b) Drizzle | spec 8.5, 16 |
| 17 | (d) fatti riconfermati | spec 16 (righe struttura, RLS, PostgreSQL 18, Prisma e Drizzle) |
| 18 | (d) Prisma 8 e `contract.prisma` | spec 11.4 (frammento di `database`), 16; piano principale blocco «A B8, da B7» |
| 20 | P14 cambia | spec 6.3 (riga P14, Q2); piano principale sezione 9 («Costi della tabella», chiuso da B7) |
| 21 | D1 `--help`/`-h` solo fuori dai valori | spec 8.5 (opzioni globali) |
| 22 | D2 `launcher_candidates` invariato | spec 8.5 (dietro un lanciatore) |
| 23 | D3 solo i tre test mancanti | spec 8.5 (test); piano principale sezione 9 («test di `bash`», chiuso) |
| 24 | D4 la tabella dei comandi va in 8.5 | spec 8.5 (tabella e nota sulla documentazione d'uso) |
| 25 | D5 `storage ls`, `unlink`, `bootstrap` chiedono | spec 8.5 (costi del permesso) |
| 26 | D6 `login` e `logout` chiedono | spec 8.5 (tabella e costi) |
| 27 | D7 ripiego testuale | spec 8.5 (ripiego testuale) |
| 28 | D8 `FlowBench.src_repo` e caso `backend` | piano principale sez. 3 (riga B7 → B8) e 16 (`test_real_flow_case_backend_proposal_has_database_block`); spec 16 (scan della radice vera nel piano 16) |
| 29 | D9 falsi positivi di percorso | spec 16 (prova reale: «la parola supabase compare solo come percorso»); piano 16 («Prova reale L2») |
| 30 | D10 `_concrete_paths` | spec 11.2; piano principale sezione 9 (chiuso) |
| 31 | D11 commento di `checklist` | spec 11.4 |
| 32 | D12 `init --update` non propone `min_level` e `checklist` | spec 11.2 (limite); piano principale blocco «A B8, da B7» (rinvio a B8) |
| 33 | D13 forme `push:pg`, opzioni prima del sottocomando di `prisma` | spec 8.5 (Prisma e Drizzle); piano blocco «A B8, da B7» |
| 34 | D14 `level_below_minimum` nella pagina | spec 6.3 (profilo attivo e L2), 8.7 |
| 35 | D15 Q45-Q47 | spec 6.3 (tabella Q45-Q47) |
| 43, 56, 63, 74, 102, 110 | revisioni in parallelo ai task (processo) | nessun contenuto da portare: scelte di conduzione dell'esecuzione |
| 46 | M1 `--local=<v>` solo con un valore vero | spec 8.5 (`REMOTE_FLAGS`); piano sezione 3 |
| 47 | M6 test che non provano niente | nessun contenuto da portare (difetto dei test del Task 1, corretto) |
| 69 | commit del Task 3 solo dopo `exit 0` | processo |
| 81 | eccezione 1, rilettura di `functions/deploy` e della pagina della configurazione | spec 16 (riga «Struttura di un progetto Supabase»); spec 11.4 (correzioni dopo la verifica); rapporto delle fonti |
| 82 | minor 3-5 del Task 3 (R-03, R-06, introduzione) | spec 11.4 (frammento di `database`: introduzione dichiarata «scelta nostra»); spec 20 (riga 34) |
| 87 | quattro minor a basso costo nel giro 1 del Task 4 | spec 20 (riga 34); piano sezione 9 («minori dei test di `rules-frontend`», chiuso nella copia) |
| 93 | introduzione dichiarata «scelta nostra» nel punto 17 | spec 11.4 e 20 |
| 129 | atto `approve spec 1` | spec 16 (riga prova reale L2); rapporto della prova |
| 132 | atto `approve plan` | spec 16; rapporto della prova |
| 137 | la decisione dell'utente arriva con `libero` | spec 16; piano sezione 3 (`libero`) |
| 140 | difetto del progetto di prova: `verify` con rapporto | piano blocco «A B8, da B7» («`verify` con rapporto nei progetti di prova L2»); spec 16; piano sezione 3 |
| 154, 157 | atti della seconda esecuzione | spec 16; piano 16 («Prova reale L2») |
| 166 | correzione del prodotto: giro di correzione tra due sessioni | spec 6.3 («Giro di correzione in una sessione nuova»), 20 |
| 167 | copia dei tre file del plugin nella copia della prova | spec 16 (riga prova reale: «tre file del plugin copiati a metà»); rapporto della prova |
| 181 | tre risultati di `WebFetch` sostituiti con il segnaposto | spec 16; piano 16 («Anonimizzazione e controllo dei dati»); rapporto |

## Dove ho portato ogni `minor (deferred)` del ledger

| Task | Minor | Dove |
|---|---|---|
| 1 | M2 `--help` come valore di un'opzione non globale | spec 8.5 («Limiti rimasti»); piano blocco «A B8, da B7» |
| 1 | M3 `npx --package supabase …` chiede | spec 8.5; piano blocco «A B8, da B7» |
| 1 | M4 ripiego testuale e `npx supabase@2 …`, `/usr/bin/supabase` | spec 8.5; piano blocco «A B8, da B7» |
| 1 | M5 Prisma e Drizzle con un'opzione prima del sottocomando | spec 8.5 (D13); piano blocco «A B8, da B7» |
| 1 | M7 motivo del veto poco leggibile | spec 8.5; piano blocco «A B8, da B7» |
| 1 | M8 tre scorrimenti di `FLAG_EFFECTS` | piano blocco «A B8, da B7» (rinvio: refactoring senza effetto sul comportamento) |
| 2 | riga di docstring di `_concrete_paths` di 103 caratteri | piano blocco «A B8, da B7» |
| 2 | `tool-results:` scritto in un comando conta come cartella | piano blocco «A B8, da B7» |
| 3 | riga 101 caratteri di `test_rules_database.py:317` | piano blocco «A B8, da B7» |
| 3 | Q46 senza `subTest` | piano blocco «A B8, da B7» |
| 3 | `test_draft_is_not_approved_before_task_5` sempre saltato | piano blocco «A B8, da B7» |
| 4 | test delle scelte aperte sull'intera sezione | piano blocco «A B8, da B7» |
| 4 | voci di R-DATABASE-04 su un riassunto | piano blocco «A B8, da B7» |
| 4 | frase sulla CLI 2 dalla memoria del controller | spec 8.5 (CLI 2) e 16; piano blocco «A B8, da B7» |
| 4 | citazione dei segreti di R-DATABASE-16 | piano blocco «A B8, da B7» |
| 5 | `test_page_records_the_choices` su tutta la sezione e senza i «Costo:» | piano blocco «A B8, da B7» |
| 5 | pagina approvata dice «arrivano dopo la tua approvazione» | piano blocco «A B8, da B7» (la pagina approvata si tocca solo con l'utente) |
| 5 | punto 17 «tutte e sei» e l'introduzione settimo elemento | piano blocco «A B8, da B7» |
| 6 | «oggi `database`» in `docs/uso/comandi.md` | piano blocco «A B8, da B7» |
| 6 | nome «real» di `DatabaseAgentsProposeTest` | piano blocco «A B8, da B7» |
| 7 | `approve spec $ISSUE` | piano blocco «A B8, da B7» (Task 7) |
| 7 | `test_real_flow_case_database_prepara_checks_l2_plan` non distingue L1 e L2 | piano blocco «A B8, da B7» |
| 7 | variabile `STEPS` senza uso | piano blocco «A B8, da B7» |
| 7 | nessun test sul salto di `libero-*.prev-*` | piano blocco «A B8, da B7» |
| 7 | due righe vuote nella classe | piano sezione 9 («agenti e prova reale») e blocco «A B8, da B7» |
| 7 | `FRONTEND_PROJECT` forse senza uso | piano blocco «A B8, da B7» |
| 7 | `unittest_junit.py` esce 1 senza test | piano blocco «A B8, da B7» |
| 7 | failure e error del rapporto junit solo con `message="x"` | piano blocco «A B8, da B7» |
| 8 | quattro minor del prodotto (più task in `resume`, `launch` e `resume`, scelta per `name`, ripiego di `apply.py`) | piano blocco «A B8, da B7» (Task 8, correzione del prodotto); spec 6.3 («Con più task in `resume`…») |
| 8 | lunghezze dei `SessionStart` tolti senza fonte | piano blocco «A B8, da B7» (rapporto della prova) |
| 8 | eventi `spec_audit_round` 5 contro 9 | piano blocco «A B8, da B7» (rapporto della prova) |

## Altre voci di carry portate

- D4, D11, D12, D13, Prisma 8, CLI 2: vedi sopra.
- Correzione del prodotto della prova (giro di correzione tra due sessioni): spec 6.3 e 20.
- `verify` con rapporto nei progetti L2: piano 9 (blocco) e sezione 3; spec 16.
- Esito composito della prova, due esecuzioni, scelte dell'utente, due difetti, costo equivalente (nessun addebito), `(select auth.uid())`, revisore che blocca per R-DATABASE-10, scostamento del task 1 della prima esecuzione, `final-database` ok e verificatore che scarta un rilievo: spec 16 e piano 16 («Prove oltre la tabella»); rinvio a B8 sui revisori che confrontano le colonne con il piano.
- `find /`: rinvio a B8 (limitare le letture fuori dal worktree nelle prove).
- Rinvii di decisione 17 rimasti aperti e «P1-P38»: piano blocco «A B8, da B7».
- Pagine di `frontend`, `backend` e `infra` che invecchiano: piano blocco «A B8, da B7».

## Dubbi

- Nessun dubbio sul contenuto. Un limite: la spec 16 e il piano 16 dicono «4061 test» presi dall'ultima suite del Task 8; il log di questo task li conferma.
