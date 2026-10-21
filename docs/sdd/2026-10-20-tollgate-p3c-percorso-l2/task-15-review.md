# Revisione Task 15: prove dei criteri, spec rev 24, piano principale

Commit esaminato: 4b4871a (214913e..4b4871a, 3 file). Sola lettura; nessun test rilanciato (le evidenze del report sono leggibili e coerenti; i controlli sotto sono statici).

Controlli eseguiti: lettura integrale del pacchetto; `audit.py` (tutto) e `l2acts.py` (tutto) confrontati con la 6.2, la 8.4 e la 3.1 riscritte; parsing AST di tutti i 44 `file::Classe.metodo` della tabella (esistono tutti); lettura di 4 test citati dalla matrice; grep dei nomi pubblici citati nella sezione 3 del piano (`audits.*`, `auditrules.*`, `specdoc.*`, `approvals.*`, `git.blob_at`, `scope.reset_plan`, `subagents.in_use`, `apply.OPS` = 28: tutti presenti); lettura di `docs/verifiche/2026-10-20-p3c-verifiche.md` e `-prova-flusso.md` contro la sezione 16.

## Aderenza

Rischio 1, sezione 6.2 contro il codice: ✅ nel complesso.
- Ordine dei passi di `audit prepare` (6.2 punto 4, passi 1-6) = `_decide_spec` / `_spec_branches` (`bin/tollgate_flow/audit.py:262-325`): ristampa/supera, avversariale non «passato» (qualunque SHA) con rifiuto «correggi» solo sullo stesso SHA (`_adv_or_fix`, :244), ciclo a lenti con conferma del costo, conferma avversariale sul blob attuale, ciclo a lenti di conferma solo con avversariale spento, `approve spec`. D2 variante B è riportata correttamente.
- Piano (punto 7): `_decide_plan` (:344-387) = testo (plan_path o primo file nuovo con `find_plan`, approvazione della spec a HEAD, giro valido su SHA piano + SHA spec, `advance` con `audit_clean`, immediato con `plan_adversary` spento).
- `approve spec` (punto 5) = `l2acts.approve_spec` (l2acts.py:177-204): fase, conteggio fette con messaggio, nessun giro aperto, `last_closed` sui due tipi della spec, `adversarial`/`lens` in `closed|suspended|off|null`, file prima della fase.
- `approve plan` (punto 8) = `l2acts.approve_plan` (:243-275), ordine `register_plan(advance=False)` saltato se `plan_sha` è già quello, file, fase.
- `reopen` (8.4, 12.3) = `l2acts.reopen` (:287-321); `suspend_on_resolve` (:325-352) = punto 6 «Sospensioni» (decide dal DB, numero 0 per il rifiuto, `>=` tetto, ultimo giro non pulito).
- Imprecisioni minori della 6.2 sono sotto (Minor).

Rischio 2, completezza della rev 24:
- ✅ Decisioni 1-16, 18-24, 26, 27 e i ruling D2, D3, D4, D5, D6, D7, D8, D9, D12, D13, D16, D17, D19 hanno un punto nella spec; riga 24 in sezione 20 presente; intestazione della revisione aggiornata; 12.2, 12.3, 12.4, 15, 18.1, 18.3, 18.4 coerenti con il codice.
- ❌ Decisione 17 (parser del piano: un recinto si apre con al più 3 spazi di rientro, come CommonMark, per `check_plan` e `task_text`) non ha un punto nella spec (7.5 non è toccata), ma la riga 24 della sezione 20 la elenca come riportata («17 (recinti del piano)») e la sua «Sezioni toccate» non include 7.5.
- ❌ Sezione 16: il testo scrive «Frontmatter dei tre agenti nuovi letto (tipi risolti in `subagents.type`)». Il rapporto della prova (`2026-10-20-p3c-prova-flusso.md`, O3) dice due agenti (`spec-adversary`, `plan-adversary`); `spec-auditor` non è mai stato lanciato, come ammette la stessa sezione 16 nella riga «Non esercitati». La spec afferma un fatto «verificato» che la prova non ha verificato.
- ⚠️ Sezione 16 e piano non riportano l'esecuzione accidentale di `claude -p` (rapporto, «Correzioni dopo la prova») né D5 (il passo 1 è girato con la forma precedente dello script; `tutto` end to end non eseguito). Il brief del Task 15 chiedeva l'incidente dichiarato; è dichiarato solo nel rapporto in `docs/verifiche`. Il «composito» del passo 1 invece c'è (spec 16 e Stato del piano).
- ⚠️ Decisione 25 e ruling di instradamento (riga 71 / I-1: gravità dichiarata blocker o major) e `active_profile_names` con HEAD nullo: la riga 24 dice «25 (rinviati di P3b)» ma nessuna sezione ne porta il contenuto. Sono contratti secondari di 6.3/6.4 e 8.6; la spec non li contraddice.

Rischio 3, matrice dei criteri: ✅ i 44 riferimenti esistono (AST). I test citati provano quanto dichiarato (letti: `ReopenTest.test_reopen_spec_from_plan_unlocks_and_requires_new_approval`, `InvalidReportTest.test_component_off_closes_only_the_agent_row`, `ApproveSpecTest.test_spec_adversary_off_accepted_without_rounds`). «Resta a» per P4 corretto per 18 e 35 (gate: `attenzione` rosso, `check_l2`). Due note: l'Edit di `spec-approval.md` (criterio 24, seconda riga) è citato con `OtherPathsTest.test_report_file_committable_and_protected`, che prova un report, non l'approvazione (la protezione generica di `reviews/**` è in `test_check_writes.py:67,133`, non citato); le tabelle P2 e P3b della stessa sezione 4 mantengono ancora «Resta a P3c» (righe 208, 249, 252), chiuse solo dalla frase finale sotto la nuova tabella.

Rischio 4, test dal programma vero e intermittenza: ✅ nessun rischio concreto. `hook()` lancia `hooks/run` come sottoprocesso (`tests/test_criteria_p3b.py:27`) e la CLI usa `clock.now()`: tutto a ora reale, nessuna ora del banco (`lab.now`) entra in questi test (D20). `started >= opened` è garantito perché `SubagentStart` segue sempre `audit prepare` nello stesso test (confronto su secondi troncati, `>=`). La scadenza degli atti (10 minuti) ha un margine di 25-50 volte sui 12-25 s dei test; solo una macchina sotto carico estremo la intaccherebbe. Il docstring di `L2Helpers.act` (tests/test_criteria_p3c.py, `act`) dichiara correttamente il rischio.

## Punti di forza

- Gli helper (`L2Helpers`: `round`, `act`, `refused`, `deny`, `prepare_step`, `commit_reviews`) estraggono il flusso senza cambiare `LaterSliceTest` (stesso comportamento) e i test nuovi sono leggibili come scenari del coordinatore e dell'utente.
- I test attraversano il programma vero: Write/Edit negati da `hooks/run`, rifiuto di `act apply`, `plan_sha` = blob del piano corretto, tre cause di fase in ordine, `plan_reset`, `spec_audit == {"adversarial": "suspended", "lens": None}` nel blocco della PR dopo `open-pr`.
- Il report ammette di non aver visto RED e spiega perché (test su codice esistente) e dichiara l'errore di asserzione nel primo giro del test di `reopen`.
- La 6.2 riscritta è fedele al codice nei rami difficili (D2, conferma sul blob attuale, sospensione decisa dal DB, numero 0 letto con `in`); la sezione 3 del piano porta nomi reali, verificati.

## Rilievi

### Important

1. **Sezione 16 inesatta** (spec, riga «Prova reale del percorso L2», rev 24). «Frontmatter dei tre agenti nuovi letto» contraddice `docs/verifiche/2026-10-20-p3c-prova-flusso.md` (O3: solo `spec-adversary` e `plan-adversary`) e la riga «Non esercitati» della stessa sezione. Correggere in «dei due agenti lanciati (`spec-adversary`, `plan-adversary`); `spec-auditor` non esercitato». Aggiungere in 16 (o nello Stato del piano) l'esecuzione accidentale di `claude -p` nel giro di correzione e il fatto che il passo 1 è girato con lo script precedente (D5), come chiede il brief.
2. **Decisione 17 assente dalla spec**, ma dichiarata riportata nella riga 24 di sezione 20. Aggiungere in 7.5 la regola (un recinto ``` si apre con al più 3 spazi di rientro; con 4 o più è codice indentato; vale per `check_plan` e `task_text`) e 7.5 nella «Sezioni toccate» della riga 24, oppure togliere «17» dalla riga. Stessa verifica per «25»: o si riporta la regola di instradamento del task di correzione (gravità dichiarata blocker/major, senza filtro sulla decisione dell'utente) in 6.3, o si toglie dalla riga.
3. **Asserzioni vuote nei test nuovi.** `self.assertTrue(self.prepare_step().startswith("prossimo passo: "), "approve spec")` in `tests/test_criteria_p3c.py`, nei test `test_cap_and_suspension_in_pr_block`, `test_three_slices_lens_audit_and_component_off` e `test_three_slices_with_spec_audit_off`: ogni uscita 0 di `audit prepare` (anche «lancia l'agente», che apre un giro) comincia con «prossimo passo: », e la stringa «approve spec» è il messaggio di errore, non il controllo. L'intento (la CLI dice «approve spec») è protetto solo indirettamente da `approve(...)` subito dopo, che fallirebbe con «giro ancora aperto». Correggere in `assertIn("/tollgate:approve spec", step)`.

### Minor

- 6.2 punto 4, passo 4: «a audit a lenti chiuso o sospeso, o con una fetta sola» non cita il caso `spec_audit = false` con più fette, che nel codice (`audit.py:307-309`) arriva al passo 4 e che `test_three_slices_with_spec_audit_off` esercita. Aggiungere «o spento».
- Piano, sezione 3, riga «Vincoli per P4 emersi in P3c», (1): «(D15: basta un'intestazione valida)» confonde la decisione 15 con il ruling D15 (`blob_at`/`launch_line`); scrivere «decisione 15». Più in generale, la spec cita D3, D5, D6, D12, D17, D19 (ruling) che stanno solo nel registro `.superpowers/sdd/…`, da portare in `docs/sdd/` (lo dice il piano): finché non è fatto, i riferimenti non si risolvono nel repo.
- Spec 8.4, tabella: la riga `reopen` non cita il rifiuto per «task non `done` con commit», che sta nel testo di `act apply` (stessa spec, poco sotto): allineare.
- Il setUp di `L2FlowTest` crea un banco e avvia un lavoro L2; `test_three_slices_with_spec_audit_off` (tests/test_criteria_p3c.py) ne crea un secondo e rifà `start`: ~qualche secondo sprecato e il primo banco resta inutilizzato fino al cleanup. Spostare il test in una classe con `setUp` proprio. I cinque test aggiungono circa 80 s a una suite da 440 s.
- Matrice, criterio 24: citare anche `test_check_writes.py` (righe 67, 133) per l'Edit di `spec-approval.md`, e aggiornare le colonne «Resta a» ormai chiuse di P2/P3b (righe 208, 249, 252 del piano) invece di affidarsi alla frase finale.
- La spec 3.1 dice che `audit prepare` esce con 0, 1, 3; un `AuditError` (db/base mancante) esce in un altro modo non documentato (`audit.py:454-455`); trascurabile.

## Valutazione

**Qualità del task:** Da correggere.

**Motivo:** i test dal programma vero sono solidi e senza rischio di intermittenza, la 6.2 e la 8.4 riscritte corrispondono al codice, la matrice regge. Restano da sistemare tre cose poco costose: la riga di sezione 16 che afferma come verificato il frontmatter di `spec-auditor` (e l'incidente non riportato), la decisione 17 (e 25) dichiarate nella riga 24 ma assenti dal corpo della spec, e le asserzioni vuote `startswith("prossimo passo: ")`.
