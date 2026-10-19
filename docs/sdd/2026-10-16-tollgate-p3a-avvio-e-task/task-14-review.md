# Revisione Task 14 (8ef5a59..1d8906f)

Revisore in sola lettura. Controlli eseguiti: grep/AST su tutti i riferimenti della matrice, confronto con codice reale (APPLIERS, CAPS, GATE_FILES, OPS, REQUIRED_CONTEXTS, firme), `python3 -B -m unittest tests.test_criteria_p3a` (2 test, OK), conteggio dei test raccolti (984, senza lanciarli).

## Aderenza

### Step 1: test (`tests/test_criteria_p3a.py`)
- ✅ `test_start_from_wrapper_flow`: `PreToolUse Bash` di `start 7 --level L1` attraverso `hooks/run` reale (subprocess, `lab.env()` con HOME/stato/gh temporanei), verifica del segnale con `sessions.cli_session`, poi `bin/tollgate start` → 0, riga con fase `plan` e sessione legata, worktree esistente, riga «prossimo passo» (`tests/test_criteria_p3a.py:215-229`).
- ✅ `test_task_cycle_end_to_end`: tutta la catena del brief (piano registrato da `PostToolUse Write`, `task start`, `PreToolUse Agent` col nome del brief, `SubagentStart`, commit, `verify`, `SubagentStop` → `review`, `review-prepare`, `SubagentStop` del revisore → `approved`, `task done` → `done`), tutto da `hooks/run` e `bin/tollgate` veri (`:255-308`). Usa `FlowLab` (TempState dentro). Passa.
- ⚠️ Il commento «criteri 4 e 38» (`:255`) è generoso: il test percorre il ramo generico (nessun profilo verticale), quindi il criterio 38 non è provato qui ma dai test di `test_taskcmd`/`test_profiles` elencati in matrice. Vedi Minor 2.

### Step 2: matrice «Prove dei criteri di P3a»
- ✅ Tutti i 44 riferimenti `file::Classe.metodo` esistono (verifica AST: classe e metodo nello stesso file, nessun mancante).
- ✅ Spot check sul contenuto: `ReviewDoneTest.test_done_requires_approved_on_last_sha` (rifiuto senza revisione, senza approved, con commit dopo l'approved; ok dopo nuova revisione), `FixRoundsTest.test_fix_rounds_counted`, `ApproveLevelTest.test_approve_level_cap_holds_until_new_sensitive_path` (tetto, `level_cap_paths`, atto consumato, nuovo percorso sensibile rialza), `StatusReadOnlyTest.test_status_reports_stopped_by`, `StandardOffTest.test_reviewer_standard_component_off` (chiave a `false` → il `minor` resta `changes`), `ResumeTest.test_second_session_does_not_interrupt_live_implementer`. Provano il criterio, non solo esistono.
- ✅ Righe «Resta a» di 1, 4 (vuota: «P2 hook, P3 task» è chiusa), 22, 28, 38, 39, 40 coincidono con le parti che il brief e il criterio nella spec (sez. 15) assegnano a P3b/P4.
- ⚠️ Riga 18: la lettura dell'implementatore è giusta nella sostanza ma troppo vaga (Minor 1).
- ✅ Il piano elenca «Criteri 9, 12, 16, 17, 24-27, 31, 33-37, 41-44: non assegnati a P3a»: coerente con la tabella dei criteri.

### Step 3: revisione 22 della spec
Spuntate tutte le voci del brief, di carry «Task 14» e dei Ruling:
- ✅ Sezione 0: sessione viva con nota M3 (`Read`/`Grep`/`Glob` non contano; implementatore che legge a lungo risulta fermo, `interrupted`), checkpoint non committato.
- ✅ 3: strati con eccezione di `cli.py` (C1, `tests/test_layers.py`), manifest nella forma V4. 3.1: `start` con `--confirm`/`--reopen-execution` e codici 0/1/3/4, `act apply [<id>]`, segnale per sottocomando solo `start`/`act` con `cli_calls` che non solleva (C8), comandi negati ai subagenti (dec. 22), V2 `CLAUDE_CODE_SESSION_ID` come possibile semplificazione (non usata), D2 `python3 "<bin>"` con ripiego `python3.11`, riga «programma» con `off`/`on` esclusi (C16/C20).
- ✅ 5: tetto (fase nella sequenza, `level_cap_paths`, tetto che vince su `min_level` in locale).
- ✅ 6.1: ordine dei passi (C4), prerequisiti, stati obbligatori `tollgate/guard`/`tollgate/verdict` (C7), conferme, nomi con `--no-track` (C18), worktree e `exclude`, esito, codice 4, ripresa con `--reopen-execution`.
- ✅ 6.2: piano registrato committabile tale e quale (D1), con rinomina/cancellazione/symlink fuori scope.
- ✅ 6.3: precondizioni, task senza commit (C11), brief a `plan_sha`, instradamento, skill assenti, giri, prenotazione non atomica (C17), `task_verdict`, messaggi di rifiuto, checkpoint con ordine delle righe e `next_step` (C12 e Important 4 del Task 10), `reviewer_type`.
- ✅ 8.4: `act apply` (consumo sempre, `resolve writer` solo implementatori, C9) e riga «programma».
- ✅ 8.6: verdetto effettivo, validità, ultimo JSON vince, `dropped`, veto per soli rilievi bloccanti scartati, decisione 10 (due veti, poi `needs_you`), [blocca] rinviato a P3b (C14).
- ✅ 11.1 (intervallo `>= 6.4.1, < 8.0.0`, formato del registro, prefisso `superpowers@`, versione più alta: C5), 11.3 (`sh -c`, C21), 12.2 (migrazione 3), 12.3 (`--reopen-execution`), 16 (V1-V5 + prova reale + «nessuna voce aperta»), 20 riga 22, intestazione rev 22.
- ✅ D1, D2, D4 del Task 13: D1 e D2 in spec; D4 è nel codice (`agents/implementer.md:65`), non serve alla spec. D6 (non difetto): nessuna voce di spec necessaria.

### Step 4: piano principale
- ✅ «Stato»: P3a chiuso sul ramo, **merge in attesa dell'OK dell'utente**, 984 test. Il numero coincide con i 984 test raccolti ora.
- ✅ Sezione 3: moduli reali di `tollgate_flow` (`start`, `taskcmd`, `actapply`, `checkpoint`, `prereq`, `gh`, `gitw`, `housekeeping`: tutti presenti in `bin/tollgate_flow/`). Contratti con nomi verificati nel codice: `start.start(...)` e codici (`start.py:21,292`), `EXCLUDES` (`start.py:23`), `task_start/review_prepare/reviewer_type/task_done` (`taskcmd.py:72,238,250,310`), `APPLIERS` = `[("resolve", None), ("approve", "level")]` (`actapply.py:83`), `apply_act` (`:109`), `checkpoint.CAPS` (`checkpoint.py:17`), `write_checkpoint/next_step/stopped_by`, `prereq.GATE_FILES`, `.github/tollgate/VERSION` (`prereq.py:14`), `gh.REQUIRED_CONTEXTS` (`gh.py:17`), `apply.OPS` = 25 operazioni, `paths.program_command` (`paths.py:16`), `config.is_readonly/output_excludes` (`config.py:267,276`), `phases.set_level_cap`, `tasks.unblock_all`, `sessions.note_cli_call/cli_session`.
- ✅ Vincoli per P3b e P3c (9 punti).

### Step 5
- ✅ Il report dichiara `tests/run` e unittest completo verdi (984, 3.11 e 3.13) e un solo fallimento intermittente, riportato onestamente. Non rilancio la suite.

### Ruling aperti
- ❌ `progress.md:167`: il Ruling «`test_watchdog_is_capped_at_85` si rende robusto con un'attesa a polling nel giro di correzione del Task 14» non è applicato. Vedi Important 1.

## Punti di forza
- La matrice è precisa: ogni riga separa ciò che P3a prova da ciò che resta ad altri piani, con test nominati per comportamento e non per modulo; la riga 18 è l'unica imprecisa.
- La rev 22 è completa e coerente con il codice: ho trovato in spec i nomi, i codici e i limiti dichiarati (C17, [blocca] rinviato, `dropped`, V2 non usata) e li ho riscontrati nei sorgenti.
- I due test nuovi non fingono: processi veri, `hooks/run` vero, nessuna scorciatoia sul segnale, e controllano lo stato nel DB a ogni passo.
- Il report segnala senza edulcorare l'instabilità di un test di P2 e il dubbio sulla riga 18.

## Rilievi

### Critical
Nessuno.

### Important
1. **Ruling non applicato: `tests/test_wrapper.py:325-328`.** `test_watchdog_is_capped_at_85` aspetta `time.sleep(0.5)` fisso e poi cerca `^sleep 87$` con `pgrep`. Sotto carico fallisce (il report lo ha visto ripetutamente a load ~20, con 3.11 e 3.13). Il Ruling di `progress.md:167` lo assegna al giro di correzione del Task 14 perché la condizione «`tests/run` verde tre volte» non tollera un test instabile. Correzione: sostituire sleep + singolo controllo con un'attesa a polling con scadenza (stile `wait_gone`, `:74-80`, ma sul verso opposto: attendere che `sleep 87` compaia, entro qualche secondo), tenendo `p.wait(timeout=30)` dopo; la seconda asserzione (`sleep 902` assente) resta. Poi ripetere il test mirato sotto carico (`python3 -B -m unittest tests.test_wrapper.WrapperTest.test_watchdog_is_capped_at_85`).

### Minor
1. **Riga 18 della matrice (`piano principale`, sezione «Prove dei criteri di P3a»).** «Le chiavi con il modulo in P3b e P3c; il gate (P4)» è corretto ma non dice quali chiavi: dalle chiavi di `[components]` (`bin/tollgate_core/config.py:87-91`, spec 11.4) restano senza test `final_review` (P3b), `spec_adversary`, `spec_audit`, `plan_adversary`, `spec_pitch` (P3c), `base_test_ids`, `sentinel` (P4), e `definition_of_done` (P3b/P4 con la DoD). Elencarle rende la riga verificabile e chiude la lettura incerta dell'implementatore: la lettura è giusta, `reviewer_standard` è l'unica chiave di P3a non già provata in P2.
2. **`tests/test_criteria_p3a.py:255`.** Il commento «criteri 4 e 38» attribuisce al test una prova che non dà (nessun profilo verticale, nessuna scelta dell'agente per area). Il brief lo chiede così, ma la matrice cita correttamente `test_taskcmd`/`test_profiles` per il 38: o si toglie «38» dal commento, o si aggiunge un profilo `web` al banco. Basta togliere «38» (il test non diventa meno utile).
3. **Spec 3.1 (paragrafo «Il programma nei comandi del modello») e piano sezione 3, vincolo (2): «mai il percorso nudo» è più forte del codice.** `bin/tollgate_hooks/runner.py:50` stampa ancora `Programma: {db.BIN_PATH}` nel footer degli errori di hook (letto dal modello su stderr). È un rinviato del Task 13 (`progress.md`, minor deferred) che la rev 22 non dichiara. O si usa `program_command` nel footer (una riga, più un test), oppure la spec dichiara l'eccezione. Il secondo rinviato (D6, payload del `task_change` di `assign`) è solo di leggibilità e non ha bisogno della spec.
4. **Piano sezione 3, riga «Gate installato».** Dice «i cinque workflow … (costante `prereq.GATE_FILES`) e `.github/tollgate/VERSION`», ma nel codice `GATE_FILES` contiene sei voci, VERSION compresa (`prereq.py:15`; il valore di runtime è stato verificato). Per P4 conta il contenuto, non l'ambiguità: riscrivere in «`prereq.GATE_FILES`: i cinque workflow più `.github/tollgate/VERSION`».

## Valutazione
**Qualità del task:** Da correggere

**Motivo:** la rev 22, la matrice e i test sono completi e verificati contro il codice, ma il Ruling sul test instabile `test_watchdog_is_capped_at_85` (assegnato al giro di correzione del Task 14) non è applicato, e senza di esso la condizione «`tests/run` verde tre volte» del controller non è garantita. Con quella correzione (più le rifiniture Minor 1-4, tutte a costo quasi nullo) il task si approva.
