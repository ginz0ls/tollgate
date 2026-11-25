# Task 6 — Revisione (commit `45bb07d`, base `3610a18`)

Revisore in sola lettura. Letti: regole del revisore, brief, vincoli globali, decisioni 15 e 19, report, pacchetto `review-3610a18..45bb07d.diff` (una volta), `task-5-proposte.md`, `docs/profili/database.md` come modello. I test mirati sono girati in una copia `git archive 45bb07d` in `/tmp/tollgate-rev-…`, resa repo privato e cancellata alla fine; niente nel worktree vivo, nessuna suite rilanciata.

## Aderenza

**Skill, frammento, file approvati**
- ✅ `skills/rules-security/SKILL.md`: una sola riga aggiunta, `approved: 2026-11-23` dopo `version: 1` (`git diff 3610a18 45bb07d -- skills/ templates/ agents/` ha una sola riga cambiata). Il testo delle regole non cambia di una parola.
- ✅ Frammento `templates/profiles/security.toml` non toccato; nessun `agents/*.md`; nessun file approvato degli altri profili. I file del commit sono sei, quelli del brief.

**Ciò che la pagina registra è ciò che l'utente ha approvato**
- ✅ `task-5-proposte.md` è identico alla sezione «Da decidere tu» di `3610a18` (`diff`: differisce solo una riga vuota in coda).
- ✅ La costante `PROPOSALS` (`tests/test_rules_security.py:424`) è la copia alla lettera delle 31 righe `Proposta:` di quel file (confronto fatto con uno script: 31 su 31, uguali a spazi normalizzati).
- ✅ `RETOUCHES` (`tests/test_rules_security.py:461`) contiene solo i due ritocchi decisi, ai punti 1 e 10, con la stessa clausola «(se il lavoro non tocca altri file del profilo)».
- ✅ «Cosa hai deciso» (`docs/profili/security.md:128`), confrontata punto per punto sul diff: 31 punti, stesso ordine, stessi titoli, stessi costi, stesse proposte. Le sole differenze di testo sono: il paragrafo d'apertura al passato (sparite «se non dici altro, resta quella» e «Se hai poco tempo…»); la riga «Hai approvato la proposta.» dopo ogni proposta; i due ritocchi; il costo del punto 5 al passato (`security.md:148`). Quest'ultimo non era nell'elenco dei cambi ammessi dal dispatch, ma è «forma al passato» di una frase che chiedeva una scelta («se vuoi che… serve…» → «perché… restassero… sarebbe servita…»): il senso del costo è lo stesso. Lo accetto.
- ✅ Riga «Approvata dall'utente il 2026-11-23.» nella pagina, stessa data della skill; introduzione nella forma di `database.md`.
- ✅ Tolte «Come rispondere» e «Rinvio»; «solo dopo che avrai approvato» → «solo dopo che le regole sono approvate».
- ✅ Resto della pagina: tabella delle regole, «Regole che si sovrappongono» (tabella), «Regole tolte dalla verifica» invariate; in «Cosa cambia nei tuoi progetti» e in «Regole che si sovrappongono» cambiano solo i due rimandi al titolo della sezione. Nessuna differenza in più.
- ✅ Voce «Attivo» (`security.md:33`): «quattro cose», con i comandi di gate e di `dod`. Rischio: che la frase fosse falsa. Controllo: `bin/tollgate_core/runner.py:47-70`, `gate_commands` e `dod_commands` iterano su `active_profiles`. È vera.
- ✅ Conteggi: diciassette regole, tredici che bloccano, trentuno punti (introduzione, apertura della sezione, elenco) coerenti.
- ✅ `docs/profili/verifiche/security-fonti.md`: solo tre rimandi al titolo, come `database-fonti.md` in B7. Nessuna riga di fonte cambia.
- ✅ Repo pubblico: nel diff nessun nome di progetto privato, utente, host, token; nessuna citazione di terzi nuova.

**`comandi.md` ed effetti dell'approvazione**
- ✅ `docs/uso/comandi.md:178`: «Le regole sono approvate dall'utente (2026-11-23): `init` propone il profilo `security` dove trova…», stessa forma di `rules-database`; i tre casi sono quelli di «Quando si accende».
- ✅ Rischio: che a questo commit `init` proponga agenti che non esistono. Controllo: nella copia, `init.profile_blocks` su un albero con `app/auth/login.py` propone `[profiles.security]` senza `agent`, `reviewer`, `final_specialist` e scrive le tre righe «non proposto: manca agents/…» (`bin/tollgate_flow/init.py:414`). Come dice il report.
- ✅ Rischio: testi d'uso resi falsi dall'approvazione. Controllo: `grep` su `README.md`, `docs/uso/`, `commands/`, `skills/init/` per «bozza», «non approvat…», «finché non», elenchi dei profili approvati. Nessun testo dice più che `security` è una bozza. `comandi.md:34` (aree con agenti propri) non nomina `security`: giusto a questo commit, gli agenti arrivano col Task 7.
- ✅ Commit: oggetto del piano, riga `Co-Authored-By` di opus. Evidenza della suite: `suite-task-6.log`, 4481 test, `OK` sui due interpreti, `exit 0`, nessun «unclosed».

**Test**
- ✅ Tutti i test dello Step 2 ci sono; i due in più (`test_page_retouches_of_task_6`, `test_commands_page_says_approved`) coprono requisiti del controller che altrimenti nessuno guardava. Non sono sovra-ingegnerizzazione.
- ✅ Mutazioni provate nella copia (base: 79 test, OK, 3 saltati):

| Mutazione | Esito |
|---|---|
| data della pagina diversa dalla skill | rosso: `test_page_approval_date_matches_skill` |
| data della skill diversa | rosso: `test_frontmatter` e il test della data |
| proposta del punto 25 cambiata («non farla bloccare») | rosso: `test_page_records_the_choices` (point=25) |
| una riga «Hai approvato la proposta.» tolta | rosso (point=10) |
| punto 31 tolto | rosso |
| «## Come rispondere» rimessa | rosso: `test_approved_page_has_no_pending_sections` |
| `comandi.md` di nuovo «bozza» | rosso: `test_commands_page_says_approved` |
| **costo del punto 3 cambiato di senso** | **verde** (vedi Minor 1) |
| **titolo del punto 25 cambiato** | **verde** (vedi Minor 1) |
| frase nuova «Dimmi «approvo» oppure «rinvio».» fuori da una sezione | verde (vedi Minor 2) |

- ✅ I tre test saltati con `skip_if_approved` non lasciano scoperto ciò che conta: i punti dello Step 3 li ricontrolla `check_choice_points` su «Cosa hai deciso»; numero dei punti, `Costo:` e proposta li ricontrolla `test_page_records_the_choices`; il test del rinvio guardava una sezione che non c'è più.

**Scostamenti dichiarati**
1. `PROPOSALS` alla lettera più `RETOUCHES` esplicito: giusto. Tiene separato ciò che l'utente ha letto da ciò che è cambiato dopo, e `approved_proposals` verifica che ogni ritocco trovi il suo testo una volta sola.
2. Test in più: giustificati (sopra).
3. `comandi.md` con i tre casi: è la forma delle altre sezioni, ed è vero.

**⚠️ Non verificabile dal diff**
- Che la risposta dell'utente sia stata «Approvo» senza modifiche e la data: è lo Step 1 del controller, lo prendo dal brief.
- `claude plugin validate --strict .`: non rilanciato (il report dice uscita 0).

## Punti di forza

- Diff della skill di una riga sola: il vincolo più importante del task è rispettato in modo verificabile a colpo d'occhio.
- Il confronto delle proposte è per uguaglianza, non per sottostringa: più stretto del modello di B7.
- I controlli di contenuto del Task 5 non sono spariti con l'approvazione: `check_choice_points` è stato estratto e riusato, senza duplicare logica.
- RED e GREEN riportati con i nomi dei test, e i dubbi dichiarati invece che nascosti.

## Rilievi

### Critical
Nessuno.

### Important
Nessuno.

### Minor

1. **`tests/test_rules_security.py:848` — titoli e costi dei punti non sono fissati.** `test_page_records_the_choices` confronta alla lettera solo la riga `Proposta:`; del costo controlla solo che esista «Costo: ». Nella copia ho cambiato il senso del costo del punto 3 («non le guarda nessuno» → «le guarda il revisore») e il titolo del punto 25: tutto verde. Oggi la pagina è giusta (l'ho confrontata sul diff), ma un ritocco futuro può cambiare un costo che l'utente ha approvato senza che un test lo dica. Il piano chiedeva solo il confronto delle proposte, quindi è copertura in più, non un requisito mancato. Come correggere, se il controller lo vuole: una costante con l'impronta (`hashlib.sha256`) del testo normalizzato di ogni punto senza la riga «Hai approvato la proposta.», oppure un test che confronti titolo e costo con una seconda costante.

2. **`tests/test_rules_security.py:822` — l'elenco delle frasi «da decidere» è chiuso.** `test_approved_page_has_no_pending_sections` cerca frasi precise; una richiesta nuova scritta con altre parole («Dimmi «approvo»…») passa. Aggiungere `dimmi «approvo»` e `«rinvio»` all'espressione costa una riga.

3. **`docs/profili/security.md:90` — «I tre agenti del profilo … arrivano dopo la tua approvazione».** Risposta al dubbio dell'implementatore: a `45bb07d` è vera (gli agenti non esistono e `init` non li propone) ed è la stessa forma che `database.md:95` ha tenuto. Non è un difetto di questo task. Diventa però stantia appena il Task 7 scrive gli agenti, e la pagina dice già «il profilo si può accendere» mentre a questo commit la proposta non ha lo specialista che lo stesso paragrafo descrive. Poiché C2 resta una fetta sola (decisione 19) nessuno vede questo stato intermedio su `main`. Consiglio al controller: nel Task 7 togliere la frase o metterla al presente («ci sono»), con il suo test; non serve un giro di correzione qui.

4. **`docs/profili/security.md:205, 221, 233, 237, 249` — proposte approvate ancora in forma di offerta** («Se li vuoi, dimmelo…», «puoi spostare ogni regola dicendomi il numero»). Risposta al dubbio: non è un difetto. È il testo che l'utente ha approvato, il brief chiede di confrontarlo con `task-5-proposte.md`, e la riga «Hai approvato la proposta.» subito sotto dice al lettore come è finita. Le offerte restano vere per una prossima revisione delle regole. Riscriverle al passato vorrebbe dire cambiare il testo approvato: meglio lasciarle.

## Valutazione

**Qualità del task:** Approvato

**Motivo:** La pagina registra esattamente ciò che l'utente ha approvato (31 punti, proposte alla lettera più i due ritocchi decisi), la skill cambia di una sola riga, nessun file vietato è toccato e i test nuovi reggono alle mutazioni che contano. Restano quattro Minor, nessuno dei quali chiede un giro di correzione: due sulla copertura dei test, uno da chiudere nel Task 7, uno è la risposta a un dubbio.
