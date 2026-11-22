# Brief per la sessione che esegue C2

Questa sessione parte con il contesto pulito. Qui c'è quello che serve per eseguire il piano C2 senza riscoprire niente. Leggi questo file per intero prima di fare qualsiasi altra cosa.

## Cosa fare

Esegui il piano `docs/superpowers/plans/2026-11-22-tollgate-c2-profilo-security.md` con `superpowers:subagent-driven-development`, seguendo **alla lettera** `docs/superpowers/plans/2026-11-22-tollgate-c2-esecuzione.md`: ramo `c2-profilo-security`, worktree `.claude/worktrees/c2`, sessione avviata dalla radice del repo. Il piano ha 10 task: modelli degli agenti, sicurezza fin dal progetto, `keep_folders`, bozza delle regole con frammento e precedenze, verifica delle fonti e pagina, approvazione dell'utente, agenti di sicurezza, script della prova, prova reale, revisione della spec.

## Il lavoro è finito quando

- tutti i 10 task sono `complete` nel ledger, ognuno con la revisione pulita (il Task 9 per il rapporto);
- `skills/rules-security/SKILL.md` ha la riga `approved:` con la data dell'OK dell'utente, oppure il ledger ha `Task 6: rinviato dall'utente` e vale la variante del rinvio;
- la prova reale del Task 9 ha le sue righe `Prova:` nel ledger e il rapporto `docs/verifiche/2026-11-22-c2-prova-flusso.md` ha la riga `Esito:`; le correzioni nate dalla prova hanno un test;
- le evidenze della prova sono ripulite e verificate a mano, e `test_committed_evidence_has_no_long_web_results` è verde;
- la revisione finale (Fable) è chiusa, con i rilievi `critical` e `important` corretti e ri-revisionati;
- la suite è verde tre volte su `python3.11` e `python3`, con `PYTHONWARNINGS=error::ResourceWarning`;
- il rapporto prima del merge è salvato in `W/rapporto-merge.md` e consegnato all'utente nella forma del punto 4 di «Chiusura» delle istruzioni;
- **dopo il merge** (solo con l'OK dell'utente) i passi del punto 5 di «Chiusura» sono fatti, e l'utente ha ricevuto il rapporto «Chiusura di C2» e la domanda diretta sul worktree;
- nell'ultimo messaggio hai lanciato `python3 -B docs/superpowers/plans/2026-11-22-tollgate-c2-verifica-fine.py` e ne hai incollato l'uscita.

**Il merge su `main` non si fa senza l'OK dell'utente.**

**Le condizioni esatte stanno nel brief corto** `docs/superpowers/plans/2026-11-22-tollgate-c2-brief-goal.md`, e lo script di verifica le controlla tutte **sui file**. Ogni fermata si scrive nel ledger (`Fermata aperta: <caso>`, poi `Fermata chiusa: <caso> — <risposta>`) e si accompagna a una **domanda diretta** con `AskUserQuestion`.

## Da leggere, in quest'ordine

1. `docs/superpowers/plans/2026-11-22-tollgate-c2-esecuzione.md`: le istruzioni.
2. Il piano C2: per intero «Fatti verificati», «Global Constraints», «Modelli per ogni lavoro», «Decisioni di questo piano» (20 decisioni, con la tabella S1-S60), «Review Focus», «Mappa dei file» e «Copertura».
3. Il progetto di C, `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`: sezione 11 per intero (con le scelte dell'utente del 22/11/2026), sezioni 2, 12 e 14.
4. Il piano principale di C, `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`: sezioni 1, 2 (riga C2), 3 (riga C2 → C3), 6, 7 e 8.
5. Il catalogo `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`: righe `security` e `ci` di 2, 2.1, 2.3 e 4, nota sul prefisso.
6. La spec del nucleo rev 36: 6.3 (precedenza, agenti di area, tabelle P e Q), 7.1, 7.3, 8.7, 10, 11.2, 11.4, 16, 20.
7. Il profilo modello B7: `skills/rules-database/SKILL.md`, `templates/profiles/database.toml`, `docs/profili/database.md`, `docs/profili/verifiche/database-fonti.md`, `agents/*-database.md`, `tests/test_rules_database.py`, `DatabasePrecedenceTest` in `tests/test_init.py`, il caso `database` di `spikes/run-b1-flow.sh`, il registro `docs/sdd/2026-11-12-tollgate-b7-profilo-database/`.
8. Il registro di C1 `docs/sdd/2026-11-20-tollgate-c1-tracciamento-locale/`: `README.md`, `progress.md`, `cautele.md`, `final-review.md`, `rapporto-merge.md`.
9. Il codice: `bin/tollgate_flow/init.py` (`profile_blocks`, `_match`, `detect_files`, `EXCLUDED_PREFIXES`, `SOURCE_EXTENSIONS`), `bin/tollgate_analysis/profiles.py`, `bin/tollgate_core/fragments.py`, `bin/tollgate_core/config.py` (`readonly_agents`, `is_readonly`, `sensitive_paths`), `bin/tollgate_flow/finalreview.py`, `bin/tollgate_flow/taskcmd.py` (`MODEL_HINT`), `hooks/run` (`READONLY_TYPES`), `tests/test_manifest.py`, `skills/execute/SKILL.md`, gli agenti generici `agents/{implementer,task-reviewer,final-reviewer,spec-adversary,plan-adversary}.md`.
10. La memoria del progetto: `plugin-workflow-decisioni.md` (voci di B7, C1 e la riga «- Piano C2 scritto»), `feedback-modelli-fable-opus.md` (indicizzata in `MEMORY.md`), `feedback-domande.md`, `feedback-spiegazioni-semplici.md`, `sessioni-nei-worktree.md`, `github-500-transitorio.md`.

## Come abbiamo lavorato (non cambiarlo)

- **Il progetto di C è l'autorità, poi la spec, poi il piano.** I conflitti si decidono con una `Ruling: <cosa> — <perché> — <costo se sbagliata>` e si va avanti.
- **Scan pre-flight prima del Task 1**, con le ruling e `carry.md` aggiornati prima di lanciare i task che ne dipendono.
- **Brief e report su file.** Il dispatch contiene il percorso del brief, **tutte** le voci di `carry.md` che nominano il task, le regole di cautela e le tre righe sulla suite. Mai la storia della sessione. Ogni subagente di sola lettura scrive la sua uscita su un file del workspace.
- **Regole di cautela nel brief di ogni subagente, al lancio.** Le eccezioni del controller non vanno mai a un subagente.
- **Modelli:** chi trova i bug su Fable, chi scrive o corregge il codice su opus, il testo delle regole e della pagina su Fable, **mai sonnet né haiku** (scelta dell'utente del 22/11/2026, detta con forza: non riproporla e non chiederla di nuovo).
- **Minori nel ledger** come `Task N: minor (deferred): …`; il triage lo fa la revisione finale.
- **Commit dopo ogni task** con `Co-Authored-By`. Mai amend, mai `--no-verify`, mai `__pycache__`. I file nuovi in git prima della suite.
- **Lingua e tono.** Testi in italiano, identificatori in inglese. Risposte all'utente brevi e in parole semplici: cosa è successo, cosa costa (gratis, consumo dell'abbonamento o spesa vera), cosa consigli. Niente gergo nelle domande.
- **Non chiedere all'utente scelte tra miglioramenti utili, compatibili e a basso costo: falli.** Chiedi solo per compromessi veri o per i casi delle istruzioni.

## Scelte dell'utente, da non riaprire

- `security` è una fetta a sé, costruita con Fable dove serve giudizio (verifica delle fonti, scrittura delle regole, revisioni) e con opus per il codice.
- Il profilo è quello del catalogo, con L2, implementatore e revisore di area e lo specialista `final-security` (che C3 userà per `ci`), **senza `**/*session*`** (22/11/2026).
- Rilevamento per contenuto delle sole librerie di password e token (22/11/2026).
- Un file di login trovato per contenuto da un altro profilo dentro una cartella di `security` accende anche `security` (`keep_folders`, 22/11/2026): deroga alla regola di I-1 per il solo `security`.
- Sicurezza fin dal progetto in ogni lavoro (22/11/2026): avversari di spec e piano, ogni implementatore (riga `Sicurezza:` nel report) e ogni revisore ci pensano, anche fuori dal profilo.
- Modelli di tutti gli agenti di tollgate, anche delle aree approvate: revisori su Fable, implementatori su opus (22/11/2026). Le regole e le pagine approvate non cambiano.
- Le regole nascono come in B2-B7: bozza con le fonti, verifica di sola lettura, pagina in parole semplici, approvazione dell'utente. Senza approvazione il profilo non si propone.
- I profili approvati non si toccano; le sovrapposizioni le dice la pagina e le decide l'utente all'approvazione.
- Le edge function di Supabase restano a `database` (progetto di B, sezione 12).
- Prova reale fino alla revisione finale con `final-security` (22/11/2026); le prove dal vivo dell'utente sono tutte alla fine, con C6.
- Il repo `ginz0ls/tollgate` è pubblico: niente nomi di progetti privati, nome utente, host o token.

## Punti delicati del piano

- **La tabella delle precedenze** (S1-S60): la sonda si rilancia a ogni cambio di pattern o di marcatore; i casi di `FrontendPrecedenceTest` e `DatabasePrecedenceTest` non devono cambiare.
- **`keep_folders` cambia solo il frammento che la dichiara**: la proposta degli altri cinque deve restare identica (Task 3).
- **`exclude = ["supabase/"]` vale anche a runtime** solo perché `security` non ha forme `ext`: un pattern per estensione aggiunto dopo romperebbe S11 e S12.
- **Le fonti CC BY-SA** (OWASP, Trail of Bits, `security-review`) danno solo idee: nessuna frase copiata, e ogni regola lo dice («idea di …»).
- **I modelli** si cambiano solo nella riga `model:` degli agenti, nel suggerimento dal giro 4 (con `[review] models` che vince), in `skills/execute` e negli script delle prove; la sicurezza fin dal progetto entra con gli stessi paragrafi nel generico e in ogni copia. Nessun altro testo degli agenti approvati.
- **Le idee CC BY-SA** arrivano ai subagenti solo dalle schede scritte dal controller in `W/fonti/security/FONTI.md`.
- **Lo specialista** deve partire anche quando `database` è attivo insieme (due specialisti nello stesso ciclo).
- **Nessuna credenziale vera** nel progetto di prova né nei test: i segreti si leggono da variabili d'ambiente impostate dal test con valori finti.
- **`ANTHROPIC_API_KEY` non deve essere impostata** prima della prova reale (si guarda solo se c'è).

## Stato al momento di questo brief

- **`main`** contiene il nucleo, B e C1 completi (merge di C1 in `e0929a8`), il progetto di C con le scelte dell'utente del 22/11/2026 e i quattro file del piano di C2 con lo script di verifica (provato a secco su 18 situazioni).
- **Suite:** 4349 test verdi su Python 3.11 e 3.13 con `PYTHONWARNINGS=error::ResourceWarning`.
- **Sulla macchina:** Claude Code 2.1.329, `gh` 2.46.0 (`gh pr edit` rotto: memoria `github-500-transitorio`), Superpowers 7.0.0. Nessun worktree aperto.
- **Il repo locale non ha un remoto configurato**: il push di `main` si fa verso `https://github.com/ginz0ls/tollgate.git`, dopo `spikes/gh-p4/ghguard.py gitcheck` con `P4_PROFILE=p5`.

## Quanto costa

C2 consuma l'abbonamento, senza nessuna spesa in denaro:
- i subagenti: scan, verifica delle fonti, scrittura delle regole, revisioni e revisione finale su Fable; implementatori e correzioni su opus (più quota di B7, che usava sonnet);
- la prova reale del Task 9, l'unico `claude` vero: circa 10-18 USD equivalenti, nessun addebito;
- dopo C2, ogni lavoro in ogni progetto con tollgate consuma più quota, perché revisori e implementatori non usano più sonnet.
