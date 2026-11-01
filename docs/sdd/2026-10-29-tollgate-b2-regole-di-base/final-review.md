# Revisione finale del ramo B2 (fbf7068..c71ab80)

Revisore: opus, sola lettura. Pacchetto letto per intero (codice, test, agenti, skill, pagina, rapporto delle fonti, spec rev 28, piano principale, catalogo, rapporto della prova); evidenze aperte solo per controlli mirati.

## Verdetto

**Non pronto per il merge**, per due Important che nascono dall'incontro tra le regole nuove e i brief dei revisori. Nessun Critical. Il meccanismo del blocco (interruttore, illeggibile, task senza modifiche, precaricamento, eval) è corretto e ben provato; i difetti stanno nel punto in cui le `R-BASE-…` diventano rilievi bloccanti.

Fatto bene: `rules_switch` separa davvero assente e illeggibile senza mai rifiutare; il task senza modifiche con nota non valida non dà più `major`; `research_prep` rende le prove a secco indipendenti dall'interruttore; skill, pagina e rapporto coincidono negli id e nei `[blocca]`; la prova reale è onesta sui suoi limiti (il rifiuto non visto dal vivo, la prova del precaricamento raccolta a mano).

### Verifiche eseguite

- Test mirati sul ramo, con `PYTHONWARNINGS=error::ResourceWarning`: `test_layers`, `test_rules_base`, `test_lookups`, `test_research`, `test_brief`, `test_manifest`, `test_docs`, `test_check_task_verdict`, `test_check_final_review`, `test_check_research_gate`: 262 OK.
- **Misura dell'indipendenza dall'interruttore** (punto 2 del brief): copia dei file tracciati (senza le evidenze) nello scratchpad, con la riga `approved:` tolta, e tutti i 124 moduli di test lanciati uno per uno con `python3`. Rossi: solo i quattro test che devono dipendere dall'interruttore acceso (`test_real_rules_base_blocks_l1`/`_l2`, `test_frontmatter`, `test_real_rules_base_is_approved`), più tre rossi ambientali dovuti alla copia (`test_eval_run.DryRunRealRegistryTest`: la copia sta sotto `/tmp`; `test_p5_scripts…budget_ledger`: le evidenze escluse dalla copia). `test_start` verde; `test_eval_cases` 99 su 100, l'unico rosso (`test_s9_dry_run`) è ambientale: la regex vuole il programma tra apici, e il percorso della copia non ha spazi. Nessun altro test dipende in silenzio dallo stato acceso.
- Prova diretta di `s1`/`s3` dal checkout principale con l'interruttore acceso e spento: esiti identici (il rinvio del Task 2 su `s3` è infondato, vedi il triage).
- `lookups.base_rules` sulla skill vera: 11 note, 8 bloccanti (01-06, 09, 10), uguali alla colonna «Blocca?».
- Anonimizzazione dei file nuovi: nessun nome utente, host o id di sessione (gli UUID rimasti sono `uuid` e `hook_id` dei messaggi, come in B1); `/home/USER/MEGA/BIZ/VIBE/...` resta, già deciso dall'utente.

## Critical

Nessuno.

## Important

### I-1. Le `R-BASE-…` `[blocca]` bloccano anche i lavori esclusi dal passo (lavori nati prima di B1, `research_note = false`)

- **Dove:** `bin/tollgate_checks/task_verdict.py:54-60`, `bin/tollgate_hooks/apply.py:84-86` (`_final_rules`), `bin/tollgate_core/lookups.py:183-194` (`base_rules`).
- **Cosa:** `lookups.base_rules(root)` aggiunge le `[blocca]` alle regole bloccanti del verdetto ogni volta che l'interruttore è acceso, senza guardare `research.active(work["research"], ctx.component("research_note"))`. Il gate (`research_gate.py:88-90`) e il brief (`taskcmd.py:343`, `research_on`) invece escludono quei lavori. Per un lavoro con `research = 0` o con il componente spento non c'è nota e il brief non ha la sezione «Nota di ricerca», ma l'agente ha `rules-base` precaricata, lo standard del brief dice «per le regole dei profili e di base solo quelle marcate `[blocca]`» e `final-reviewer.md` dice che le `R-BASE-…` «valgono per ogni diff». Un rilievo `major` su R-BASE-01, 02, 03, 04, 06 o 09 (tutte sulla nota, che lì non esiste per scelta) ferma il task o il ciclo finale.
- **Perché conta:** contraddice il progetto 8 (scelta dell'utente: un lavoro iniziato prima di B continua con le sue regole) e la spec 8.1/11.4 (`research_note = false` «spegne il passo del tutto»). Il test lo codifica già: `BaseRulesTest` in `tests/test_check_task_verdict.py` usa `Lab(toml=…)`, cioè `research=False`, e asserisce `changes` su R-BASE-01. Con il blocco acceso nel repo tutti i lavori legacy in corso sono esposti dal primo verdetto dopo l'installazione.
- **Come correggere:** in `task_verdict` e in `_final_rules` le `R-BASE-…` restano sempre **note** (così una non `[blocca]` non blocca mai come ignota), ma le `[blocca]` si aggiungono alle bloccanti solo se `research.active(work["research"], ctx.component("research_note"))`. Una funzione sola (per esempio `lookups.base_rules(root, active: bool)`) per non duplicare la condizione. Spec 8.6 rev 28 e piano principale sezione 3 da allineare («solo nei lavori con il passo»).
- **Test che fallirebbe oggi:** in `tests/test_check_task_verdict.py` una classe con `Lab(research=False)` e `make_base_root(True)`: un rilievo `major` su `R-BASE-01` deve dare `approved`; la gemella con `research=True` deve dare `changes`. Stesso test per il componente spento (`[components] research_note = false`) e per `_final_rules` in `tests/test_check_final_review.py`. `BaseRulesTest` va passata a `research=True`.

### I-2. Le regole che si giudicano sul report e sulla nota non hanno report né nota nei brief dei revisori che le applicano

- **Dove:** `skills/rules-base/SKILL.md:9` («Chi rivede le applica guardando il diff, la nota di ricerca o il report»), R-BASE-05 (`:25`), R-BASE-07 (`:31`), **R-BASE-10 `[blocca]`** (`:42`), R-BASE-11 (`:45`); `bin/tollgate_analysis/brief.py:240-265` (`review_brief`) e `bin/tollgate_flow/taskcmd.py:260-269` (`_concerns`); `brief.final_review_brief` e `agents/final-reviewer.md:37`.
- **Cosa:** il brief del revisore del task non contiene il report dell'implementatore (solo `concerns`, e solo con `DONE_WITH_CONCERNS`), né lo indica: `agents/task-reviewer.md` non dice dove trovarlo. Il revisore finale e il verificatore non hanno né il report né la nota (D6 rende inerte la frase sulla nota, ma lo standard dell'agente dice che le `R-BASE-…` valgono per ogni diff e le `[blocca]` danno `blocker`/`major`). Quindi R-BASE-10 `[blocca]` («il report mostra che il test fallisce senza la correzione e passa con la correzione») non è verificabile da nessun revisore; R-BASE-01..04, 06, 09 non lo sono dal revisore finale.
- **Perché conta:** il catalogo (principio 5) e il vincolo globale vogliono ogni regola verificabile con un sì o un no guardando diff, nota o report. Davanti a una regola `[blocca]` non verificabile il modello o la ignora (regola morta) o la dichiara violata: con il blocco acceso e la distinzione `[blocca]` ora meccanica (giro 1 del Task 6), ogni task che corregge un difetto rischia un `major` su R-BASE-10 e un giro di correzione che l'implementatore non può chiudere, perché il revisore successivo non vedrà comunque il report. La prova reale non lo mostra perché il task non era una correzione.
- **Come correggere** (scelta del controller o dell'utente, con costi diversi): (a) mettere nel brief del revisore del task il report dell'ultimo implementatore, in un recinto con `DATA_NOTE` (è testo non fidato; il dato è già in `subagents.report`, come per `_concerns`), e nel brief finale il percorso delle note `.tollgate-run/<N>/research-*.md` o l'indicazione che le regole sulla nota sono del revisore del task; oppure (b) togliere `[blocca]` alle regole giudicabili solo sul report (R-BASE-10, R-BASE-05 nella parte «report»), con un nuovo OK dell'utente sulla pagina (le regole sono approvate: cambiare un `[blocca]` è un cambio di regola); oppure (c) riformulare R-BASE-10 sul diff («il diff aggiunge un test che fallisce senza la correzione»), con verifica delle fonti e OK dell'utente. (a) non tocca le regole approvate ed è la meno costosa.
- **Test che fallirebbe oggi:** in `tests/test_taskcmd.py` (`ReviewDoneTest`), con un report dell'implementatore registrato, `review_prepare` produce un brief che contiene il campo `tests` del report dentro un recinto preceduto da `brief.DATA_NOTE`; in `tests/test_brief.py`, `review_brief` con `implementer_report="…```…"` lo recinta. Oggi il campo non esiste.

## Minor

1. **Spec 6.3, riferimento rotto** (`docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:476`, riga della «Skill:»). Il paragrafo su `rules-base` è stato inserito prima di «`SubagentStop` controlla che l'implementatore abbia invocato ognuna»: ora «ognuna» si legge riferito anche a `rules-base`, cioè il contrario di ciò che il paragrafo dice. Correzione: spostare il paragrafo dopo la frase su `SubagentStop` e «Una skill non installata…». Nessun test (documento).
2. **Spec 16, elenco «Tipi:» senza il tipo nuovo** (`nucleo-design.md:1802`): `research_switch_unreadable` c'è in `data` (`:1800`) e in `events.EVENT_TYPES`, non nell'elenco dei tipi. Correzione: aggiungerlo. Test possibile: `test_docs` che confronti `EVENT_TYPES` con l'elenco «Tipi:» della spec (oggi fallirebbe).
3. **«`rules_enforced` è il gate unico» non è più vero** (`bin/tollgate_core/lookups.py:196`, spec `:710`, piano principale sezione 3 riga B1→B2): `research_gate` usa `rules_switch`, solo `taskcmd` usa `rules_enforced`; la docstring cita anche `task review` (rinvio Task 1). Correzione: «il gate (`research_gate`) usa `rules_switch`; `taskcmd.review_prepare` usa `rules_enforced`».
4. **Piano principale sezione 3, riga B1→B2:** «B2 (rev 28) ha escluso anche `no`, `off`, `n` e `false`»: `false` era già in `_YAML_EMPTY` da B1. Correzione: «`no`, `off` e `n`, e il confronto dopo gli apici (anche per `false`)».
5. **Ruling del giro 1 del Task 6 contraddittoria, codice coerente con la seconda metà:** la ruling dice «con l'interruttore spento o illeggibile nessuna R-BASE blocca» e poi «se la skill non si legge, fail-closed». Il codice fa la seconda cosa (`lookups.base_rules` → `(vuoto, vuoto)`, una `R-BASE-…` `major` è ignota e blocca), e la spec 8.6 lo dice. Con l'illeggibile il brief dice «interruttore spento, `moderate`», quindi l'effetto pratico è piccolo; va solo tolta la prima metà dalla ruling riportata. Nessun test da cambiare.
6. **Nessun test di `research.base_rules` sulla skill vera** (`bin/tollgate_analysis/research.py:64-70`): i test del verdetto usano una skill finta con la stessa forma. Se la skill vera cambiasse forma (due spazi prima di `[blocca]`, un id a tre cifre) la distinzione meccanica si perderebbe in silenzio. Test: in `tests/test_rules_base.py`, `research.base_rules(skill_text())` uguale a `({r[0] for r in rules(...)}, {r[0] for r in rules(...) if r[1]})`.
7. **Rapporto delle fonti: una riga di fonte che la skill non cita** (`docs/profili/verifiche/base-fonti.md:21`): R-BASE-10 ha nel rapporto la riga `no` di `systematic-debugging`, che la skill non cita più. Il punto 3 del brief chiede fonti uguali: la riga va marcata come fonte scartata (o spostata sotto la tabella), così ogni riga della tabella è una fonte citata dalla skill. Test possibile: confronto tra le fonti di `rules()` e le righe `ok` del rapporto.
8. **Docstring del modulo `research_gate`** (`bin/tollgate_checks/research_gate.py:1-6`) non nomina l'interruttore illeggibile né l'evento nuovo. Correzione: una frase.
9. **`implementer.md` punto 1** («`rules-base`, già nel tuo contesto»): vero solo se la skill si legge; con l'interruttore illeggibile o assente l'implementatore non ha le regole e il punto non dice di leggere i file. Il brief del task lo dice comunque («leggi i file del progetto»), quindi l'effetto è piccolo.

## Triage dei minori rinviati (`W/final-deferred.md`)

| Voce | Esito | Motivo |
|---|---|---|
| T1: test dell'illeggibile non controlla l'ordine `_UNREADABLE` + avviso né la non ripetizione | Correggere prima del merge (costa due asserzioni) | `assertLess(r.stdout.index("non si legge"), r.stdout.index(WARNING))` e, sulla seconda modifica, `assertNotIn("non si legge", …)`: è il comportamento della decisione 5 e oggi nessun test lo blocca |
| T1: `"null"`, `"~"`, `"\|"` tra apici valgono vuoto | Rinviabile | Va verso «spento», il lato sicuro; nessuno scrive così una data |
| T1: docstring di `rules_enforced` | Correggere con il Minor 3 | Stessa frase |
| T2: test con la radice vera in `review_prepare` (`test_taskcmd` 476/491/660, `test_fixtask:180`, `test_criteria_p3a:114`) | Rinviabile | La mia misura con l'interruttore spento li dà verdi in entrambi gli stati; non asseriscono sulla gravità. Restano annotati nel piano principale |
| T2: `s3_the_veto_does_not_depend_on_the_starting_folder` senza `PREP` | Chiudere: infondato | Provato con l'interruttore acceso e spento: dal checkout principale `research_gate` non trova il proprietario e il veto contiene il solo motivo di scope, uguale nei due stati |
| T3: `test_model_name_rule` riconosce R-BASE-04 da parole italiane | Rinviabile | Annotato per B3 nel piano principale; dopo l'approvazione il numero è stabile, si può passare all'id |
| T3: «un difetto si segnala una volta sola» in `SKILL.md:9` | Chiudere | Coerente con la decisione 8 e D3; approvato dall'utente |
| T4: «N.» contro id tra parentesi non controllato | Rinviabile a B3 | Annotato per le pagine nuove |
| T4: `test_page_explains_what_changes` fragile | Rinviabile a B3 | Annotato |
| T4: `base.md:9` «agente» non spiegato | Chiudere | La riga 11 lo spiega («un agente a cui è affidato un task») |
| T5: data della pagina contro `approved` non confrontata | Correggere prima del merge (una riga di test) oppure rinviare dichiarato | Costa una riga; è un anti-obiettivo del progetto («regole mai lette da una persona») e la spec lo dichiara non provato |
| T5: `base.md:50-54` «Due… sono state tolte» con la regola rimessa | Rinviabile | La pagina è approvata dall'utente così; leggibile |
| T5: `base-fonti.md:3` cita `b17cbf0` | Correggere prima del merge, insieme al Minor 7 | Il rapporto dice «skill verificata al commit b17cbf0» ma la R-BASE-10 attuale è stata verificata dopo: aggiungere il commit della seconda verifica |
| T6: «la gravità del brief» senza fonte nel revisore finale | Rientra in I-2 | Stessa causa: il brief finale non ha nota né report |
| T6: persa la lettura dei file chiamanti | Rinviabile a B3 | Scelta della decisione 11, annotata nel piano principale |
| T6: `test_rejected_report_leaves_trace` con `plugin_root=ROOT` | Rinviabile | Verde con l'interruttore spento e acceso (misura sopra); il riporto è rifiutato prima di `_final_rules` |
| T7: il titolo non distingue precaricamento e `Read` | Chiudere | Il rapporto lo dice (sezione «Cosa dice la prova e cosa no») |
| T7: controllo dell'interruttore dopo `rot`/`mkdir` in `prepara` | Rinviabile | Codice di prova; nulla si perde |
| T7: `flowreg precarico` cerca `agent_transcript_path` | Rinviabile a B3 | Annotato nel piano principale |
| T7: `/home/USER/MEGA/BIZ/VIBE/...` in `comandi-modello.txt` | Rinviabile | Scelta dell'utente sui percorsi locali; utente già anonimizzato |
| T7 (nel ledger, non in `final-deferred.md`): `/home/USER/...` preesistente in `docs/verifiche/evidenze/gh-p4/` | Da confermare con l'utente | Fuori da B2, ma il repo è pubblico e contiene il nome utente reale; il controller lo porti all'utente |
| T8: «gli ultimi tre» nella riga del rinvio 31 | Correggere prima del merge | Frase falsa sulla prova (vale per due test) |
| T8: «se `rules-<area>` si precarichi» | Correggere (grammatica) | Una parola |
| T8: «la n. 11 tolta» | Correggere | Confondibile con la R-BASE-11 vera: «la bozza n. 11» |
| B1 rinvio 37: `cat` con glob non registra le letture | Rinviabile a B3, con una nota | La prova reale di B2 lo mostra di nuovo: la prima consegna è stata rifiutata per file visti solo con `cat`/`ls` a glob. Costa un giro di consegna, non un rifiuto di modifica (la nota arriva prima della modifica). Da B3: una riga in `implementer.md` o nel brief («i file che elenchi aprili con Read») costa poco e toglie il giro |

## Giudizio sulle `Ruling:`

- **D1-D16:** corrette. D2 e D14 sono confermate dalla mia misura (nessun rosso fuori dai moduli attesi). D5 è coerente con la spec 8.1. D16 è prudente.
- **Ruling del giro 1 del Task 6 (R-BASE note al verdetto): giusta nell'intento, incompleta.** Ha reso meccanica la distinzione `[blocca]` senza legarla a `research.active` del lavoro, e così ha aperto I-1; in più contiene la contraddizione del Minor 5. Non ha considerato che le regole sul report non sono visibili ai revisori, e la meccanica rende I-2 più costoso.
- **D3 e D6:** coerenti tra loro, ma presuppongono che il revisore veda ciò che giudica. D6 rende inerte la frase sulla nota nel revisore finale, mentre lo stesso agente dice che le `R-BASE-…` valgono per ogni diff: è la radice di metà di I-2.
- **Ruling sulla skill MIT di terzi nelle evidenze:** accettabile (testo pubblico, dichiarato nel rapporto).
- **Ruling sulla verifica del controller al posto di una ri-revisione per il giro di due righe del rapporto:** corretta; ho riletto il rapporto e le due righe corrispondono.
- **Ruling sui test mirati nel giro 1 del Task 4:** corretta (la suite completa si è ripetuta nel Task 5).
- **Ruling sui due minori dei testi (L0 e licenze) nel giro 1:** corretta.

## Fuori dal piano, considerati e lasciati

- `0` e `none` che accendono l'interruttore: scelta D5, conforme alla spec.
- L'evento `research_switch_unreadable` non conteggiato da `stats`: D10, dichiarato.
- Assenza di L0 nell'evento illeggibile: la decisione 5 lo limita a L1 e L2.
