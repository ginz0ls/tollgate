# Ri-revisione del giro di correzione della revisione finale (c71ab80..7c8deb4)

Letti: regole del ruolo, revisione finale, brief del giro, ledger, report, diff (21 file). Eseguiti, sola lettura e `python3 -B` con `PYTHONWARNINGS=error::ResourceWarning`: `test_layers`, `test_brief`, `test_check_task_verdict`, `test_check_final_review`, `test_manifest`, `test_rules_base`, `test_docs` (188 OK) e `test_taskcmd` (58 OK).

## Verdetti sui rilievi

**I-1. Le `R-BASE-…` `[blocca]` bloccano anche i lavori senza il passo.** INDIRIZZATO.
- Una sola funzione per la condizione: `bin/tollgate_core/lookups.py` `base_rules(root, active)`; bloccanti solo con `active and research.enforced(text)`. Entrambi i chiamanti passano `research.active(work["research"], ctx.component("research_note"))`: `bin/tollgate_checks/task_verdict.py` (diff righe 54-60) e `bin/tollgate_hooks/apply.py` `_final_rules`. Nessuna condizione duplicata.
- Casi d'incontro:
  - interruttore acceso + lavoro senza passo (`research=False`): le `R-BASE-…` restano note, nessuna blocca. `BaseRulesNoStepTest` in `tests/test_check_task_verdict.py` e `tests/test_check_final_review.py`: `R-BASE-01` major → `approved` / `blocking 0`. In più `R-BASE-99` (ignota) blocca ancora.
  - componente spento (`[components] research_note = false`): `BaseRulesComponentOffTest` in entrambi i file, stesso esito.
  - skill illeggibile: `base_rules` torna `(vuoto, vuoto)` prima di guardare `active`, quindi una `R-BASE-…` major è ignota e blocca (fail-closed), come prima. `BaseRulesUnreadableTest` eredita da `BaseRulesTest`, ora con `research = True`, ed è verde.
  - interruttore spento con passo: invariato (`BaseRulesSwitchOffTest`).
- `BaseRulesTest` passa a `research = True` e le classi nuove sono le gemelle chieste dalla revisione. Spec 8.6 e piano sezione 3 allineati.

**I-2. Il report dell'implementatore non è nel brief dei revisori.** INDIRIZZATO.
- `bin/tollgate_analysis/brief.py`: `ReviewBrief.implementer_report` e la sezione «Report dell'implementatore», con la frase sulle regole sul report, poi `DATA_NOTE`, poi `_block(...)`. `_block` usa `fence()`, che prende un recinto più lungo di ogni sequenza di backtick del testo: il report con tre backtick va in un recinto da quattro, sempre dopo `DATA_NOTE`.
- `bin/tollgate_flow/taskcmd.py`: `_implementer_report` è valorizzato sempre quando c'è un report (anche con stato `DONE`), non solo con `DONE_WITH_CONCERNS`. Se il report non si legge, riporta la coda del testo registrato (tetto `MAX_SCAN_CHARS`); `concerns` resta nella sua sezione, quindi non compare due volte e `test_done_report_without_concerns_adds_none` resta valido. Nessun report, nessuna sezione.
- Test: `ReviewReportTest` (`tests/test_brief.py`: recinto a quattro backtick, `DATA_NOTE` prima del recinto, nessuna sezione senza report). `test_report_reaches_review_brief_even_when_done` e `test_no_report_no_report_section` (`tests/test_taskcmd.py`). Il `prepare()` della classe usa una radice temporanea esplicita (`taskcmd.db.BIN_PATH` mockato), non la radice vera.
- Agenti e brief non si smentiscono:
  - `agents/task-reviewer.md:27` e la frase del brief nominano le stesse regole (R-BASE-05, 07, 10, 11 e le parti sul report delle altre).
  - `final-reviewer.md` e `finding-verifier.md` dicono «solo su ciò che vedi» e che le regole su nota e report sono del revisore del task.
  - La frase condizionata di D6 («se il brief ti mostra la nota…») resta nel revisore finale.
  - `test_manifest` blocca le frasi nuove.

**3. Test dell'illeggibile: ordine dell'avviso e non ripetizione.** INDIRIZZATO. `tests/test_check_research_gate.py`: `assertLess(index("non si legge"), index(WARNING))` e `assertNotIn("non si legge", again.stdout)` alla seconda modifica.

**4. Data della pagina contro `approved`; `research.base_rules` sulla skill vera.** INDIRIZZATO. `tests/test_rules_base.py`: `test_page_approval_date_matches_skill` (la regex richiede la riga esatta e confronta con `approved`) e `test_base_rules_of_research_match_rules`.

**5. `base-fonti.md`: commit della seconda verifica e fonte scartata.** INDIRIZZATO. Riga 3 cita 3c4697a e la data 2026-11-01. La riga `no` di `systematic-debugging` esce dalla tabella e sta sotto come «Fonte scartata», con la nota che la skill non la cita. `test_sources_report_covers_every_rule` non è modificato.

**6. Spec del nucleo (6.3, «Tipi:», `rules_enforced`, frasi I-1/I-2).** INDIRIZZATO. Il paragrafo `rules-base` è dopo la frase su `SubagentStop`; `research_switch_unreadable` è nell'elenco «Tipi:»; `tests/test_docs.py::test_spec_event_types_match_registry` confronta l'elenco con `events.EVENT_TYPES`. La docstring di `rules_enforced` in `lookups.py` dice la distinzione giusta (gate = `rules_switch`).

**7. Piano principale (sezione 3, rinvio 31 «I primi due», «bozza n. 11», rinvii a B3).** INDIRIZZATO. Controllato sul diff: «I primi due», «la bozza n. 11» (anche nella spec rev 28), rinvio 37 di B1 e due note «Da B2» aggiunte tra i rinvii a B3.

**8. Docstring di `research_gate`.** INDIRIZZATO. Cita l'interruttore illeggibile, `rules_switch`, l'evento `research_switch_unreadable` e il «una volta per piano».

**9. `implementer.md` punto 1.** INDIRIZZATO. Aggiunta: «Se le regole di base non sono nel tuo contesto, leggi comunque i file che modifichi prima di scriverli». `test_manifest` verde.

## Danni nuovi nel diff della correzione

Nessun Critical o Important.
- **Minor.** `agents/task-reviewer.md:53` dice che le `R-BASE-…` `[blocca]` danno `blocker`/`major` «se il brief non dice che l'interruttore è spento». Per un lavoro senza passo (`research=False`) il brief non ha la sezione «Nota di ricerca» e non dice nulla sull'interruttore, mentre il verdetto ora le tratta come note. L'effetto è solo che il revisore può dichiarare `changes` per una `R-BASE-…` `[blocca]`, e il controllo del verdetto non la fa bloccare (come per i profili non bloccanti, il test «non-blocking → approved» lo mostra). Nessun blocco spurio; è rumore, da annotare per B3 (una riga nel brief o nell'agente: «senza la sezione nota, le `R-BASE-…` non bloccano»).
- Strati: `task_verdict.py` (checks) e `apply.py` (hooks) importano `tollgate_analysis.research`, già consentito (altri import da `tollgate_analysis` negli stessi moduli); `test_layers` verde.
- Test che leggono la radice vera in silenzio: nessuno di nuovo. `ReviewDoneTest.prepare()` usa la radice temporanea; i test nuovi del verdetto usano `make_base_root` con `addCleanup(rmtree)`.
- File aperti e non chiusi: nessuno (`read_text`, nessun handle). I test mirati passano con `error::ResourceWarning`.
- `skills/rules-base/SKILL.md` (regole e `approved`) e `docs/profili/base.md` non compaiono tra i file del diff.

## Osservazioni fuori ambito

- Il working tree ha modifiche non committate sotto `docs/verifiche/evidenze/b2/flusso/` (file `D` e cartelle `passo*.prev-…`, `tentativo-2`, `validate-2.txt`): è la ripetizione della prova reale decisa nel ledger, non fa parte del diff e non l'ho toccata.
- Il brief nomina gli id R-BASE-05, 07, 10, 11 nel testo (già dichiarato dall'implementatore): se l'elenco cambia in B3 va aggiornato anche lì.

## Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
