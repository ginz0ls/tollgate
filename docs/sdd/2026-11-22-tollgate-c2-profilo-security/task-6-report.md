# Task 6 — Report dell'implementatore (Step 2-5)

**Status:** DONE
**Commit:** `45bb07d tollgate C2: rules-security approvata dall'utente` (ramo `c2-profilo-security`, padre 3610a18)

## Cosa ho fatto

L'utente ha risposto «Approvo» il 2026-11-23, senza modifiche (Step 1, controller). Ho registrato l'approvazione sul modello di B7 (`rules-database`):

- `skills/rules-security/SKILL.md`: solo la riga `approved: 2026-11-23` dopo `version: 1`. Il testo delle regole non cambia di una parola (diff: una riga aggiunta). Il frammento `templates/profiles/security.toml` non cambia.
- `docs/profili/security.md`: la pagina passa da proposta a registro delle scelte (dettaglio sotto).
- `docs/profili/verifiche/security-fonti.md`: le tre menzioni di «Da decidere tu» diventano «Cosa hai deciso» (correzione dei rimandi, come in `database-fonti.md`). Nessun altro cambio.
- `docs/uso/comandi.md`: la sezione `/tollgate:rules-security` non dice più «bozza»; ora «Le regole sono approvate dall'utente (2026-11-23): `init` propone il profilo `security` dove trova una cartella `auth/`, `security/` o `rls/`, un middleware o un proxy, o una libreria di password o di token.» (stessa forma di `rules-database`, con i tre casi di «Quando si accende» della pagina).
- Test (`tests/test_rules_security.py`, `tests/test_fragments.py`), sotto.

Nessun file approvato degli altri profili, nessun `agents/*.md`, nessun frammento toccato.

## Test

### Nuovi o cambiati

In `tests/test_rules_security.py`:
- costante `APPROVED = "2026-11-23"`;
- `test_frontmatter` invertito: `approved == APPROVED`, chiavi nell'ordine `name, description, version, approved`, `research.enforced(text)` vero;
- costante `PROPOSALS` (le 31 proposte copiate da `W/task-5-proposte.md`, verificato identico alla sezione «Da decidere tu» di 3610a18 con `diff`), `RETOUCHES` (i due ritocchi dei punti 1 e 10, testo del Task 5 → testo approvato) e `approved_proposals()` che li applica controllando che ogni ritocco trovi il suo testo una volta sola;
- `test_page_approval_date_matches_skill`: una sola riga `Approvata dall'utente il <data>.`, uguale a `approved`;
- `test_approved_skill_leaves_no_pending_decisions`: né pagina né rapporto nominano «Da decidere tu» o «va confermata dall'utente»;
- `test_approved_page_has_no_pending_sections`: niente `## Come rispondere`, `**Rinvio.**`, «finché non (le) approvi», «dopo che avrai approvato», «devi decidere», «Se hai poco tempo», «se non dici altro», «sono una bozza»;
- `test_page_records_the_choices`: sezione «Cosa hai deciso», 31 punti in ordine, ognuno con `Costo: `, una sola riga `Proposta: ` il cui testo (spazi normalizzati) è **uguale** alla proposta approvata (più stretto del confronto per sottostringa di B7), una riga `Hai approvato la proposta.`; «Su trentuno punti», «tutti e trentuno»; nell'introduzione «cosa hai deciso su trentuno punti dubbi» (numero confrontato con i punti) e «Le regole sono approvate e il profilo si può accendere.»; in più riusa i controlli di contenuto del Task 5 (casi S…, frase di S53, `CHOICE_POINTS`, punto «scelta nostra» con tutte le regole) sulla nuova sezione;
- `test_page_retouches_of_task_6`: la clausola «(se il lavoro non tocca altri file del profilo)» compare due volte; la voce `- **Attivo**: ` nomina gate, `dod` e «vuoti»;
- `test_commands_page_says_approved`: la sezione di `comandi.md` ha la frase con la data e non dice «bozza»;
- `check_choice_points(raw)`: estratto da `test_page_brings_the_open_choices_to_the_user` (che resta, con `skip_if_approved`, e ora lo chiama) per usarlo anche su «Cosa hai deciso»; due messaggi d'errore resi neutri rispetto al titolo della sezione;
- docstring del modulo e di `RulesSecurityPageTest` aggiornate al Task 6.

In `tests/test_fragments.py`: `test_real_security_fragment_approved`.

I tre test con `skip_if_approved` (`test_page_brings_the_open_choices_to_the_user`, `test_page_choices_count_matches_list`, `test_page_rinvio_says_what_stays_on_the_branch`) restano e ora saltano; `test_page_counts_match_skill` controlla ancora «Cosa sono» e salta solo la parte di «Da decidere tu».

### RED

```
$ python3 -B -m unittest tests.test_rules_security tests.test_fragments
ERROR: test_page_approval_date_matches_skill (…RulesSecurityPageTest…)      KeyError: 'approved'
ERROR: test_frontmatter (…RulesSecurityTest…)                                KeyError: 'approved'
FAIL: test_approved_page_has_no_pending_sections   — resta la sezione «Come rispondere»
FAIL: test_approved_skill_leaves_no_pending_decisions (path='security.md')        — resta un rimando a «Da decidere tu»
FAIL: test_approved_skill_leaves_no_pending_decisions (path='security-fonti.md')  — resta un rimando a «Da decidere tu»
FAIL: test_commands_page_says_approved             — manca la data dell'approvazione
FAIL: test_page_records_the_choices                — manca una sezione della pagina
FAIL: test_page_retouches_of_task_6                — 0 != 2 : i ritocchi dei punti 1 e 10
FAIL: test_real_security_fragment_approved (tests.test_fragments.RealFragmentsTest…)
Ran 79 tests — FAILED (failures=7, errors=2)
```

### GREEN

```
$ python3 -B -m unittest tests.test_rules_security tests.test_fragments
Ran 79 tests in 0.186s
OK (skipped=3)
```

Test con `init` sulla radice vera (dopo `approved`, `init` propone `security`):

```
$ python3 -B -m unittest tests.test_init tests.test_fragments tests.test_b1_scripts tests.test_manifest tests.test_docs tests.test_rules_security
Ran 598 tests in 171.901s
OK (skipped=3)
```

Nessun albero di test si accende per `security` (`test_real_trees_light_no_profile` e gli alberi dei test verdi); il frammento non cambia. Gli agenti `-security` non esistono ancora: `init._agent_exists` toglie `agent`, `reviewer`, `final_specialist` dalla proposta finché il Task 7 non li scrive.

`claude plugin validate --strict .`: «✔ Validation passed», uscita 0 (solo l'avviso già noto sull'icona, che non cambia l'esito).

Suite completa (`W/suite-task-6.log`):

```
== Python 3.11.16
Ran 4481 tests in 3058.635s
OK (skipped=16)
== Python 3.13.5
Ran 4481 tests in 1980.865s
OK (skipped=14)
exit 0
```

Nessun «unclosed» nel log (`grep -c -i unclosed` = 0).

## La pagina, sezione per sezione

- **Introduzione**: «su quali trentuno punti devi decidere. Le regole sono una bozza: finché non le approvi, il profilo non si accende in nessun progetto.» → «cosa hai deciso su trentuno punti dubbi. Le regole sono approvate e il profilo si può accendere.» e la riga «Approvata dall'utente il 2026-11-23.» (forma di `database.md`).
- **Cosa sono** (glossario): la voce «Attivo» dice «quattro cose», con in più «girano i suoi comandi di gate e di `dod` (per `security` oggi sono vuoti)». Verificato su `bin/tollgate_core/runner.py` (`gate_commands`, `dod_commands` iterano su `active_profiles`). Conteggi delle regole invariati (diciassette, tredici).
- **Quando si accende**: «solo dopo che avrai approvato le regole» → «solo dopo che le regole sono approvate».
- **Le regole**: invariata.
- **Cosa cambia nei tuoi progetti**: il rimando «punto 20 di «Da decidere tu»» → «Cosa hai deciso». La frase «I tre agenti del profilo … arrivano dopo la tua approvazione» resta (è vera, ed è la stessa forma che `database.md` ha tenuto dopo l'approvazione; gli agenti arrivano col Task 7).
- **Regole che si sovrappongono**: il rimando al punto 23 → «Cosa hai deciso». Tabella invariata.
- **Da decidere tu → Cosa hai deciso**: il paragrafo d'apertura passa al passato («la scelta era tua, … aveva un costo che dovevi conoscere. Hai approvato la proposta in tutti e trentuno, il 23 novembre: resta quella scritta sotto, e i numeri delle regole non cambiano più.»); spariscono «se non dici altro, resta quella» e «Se hai poco tempo, guarda questi sette…». Ogni punto ha dopo la proposta la riga «Hai approvato la proposta.» con lo stesso rientro. Il costo del punto 5 parlava di una scelta ancora aperta («se vuoi che… serve una regola nuova… prima dell'approvazione») e ora è al passato («perché anche questi restassero… sarebbe servita…»). I due ritocchi: punto 1 «senza queste regole e senza lo specialista (se il lavoro non tocca altri file del profilo), ma il lavoro resta L2…»; punto 10 «Sotto `auth/` toglie gli agenti di sicurezza e lo specialista (se il lavoro non tocca altri file del profilo), non il livello L2…».
- **Regole tolte dalla verifica**: invariata (parla al passato della bozza, resta vera).
- **Come rispondere** e **Rinvio**: tolte.

Nessun dato privato: `test_page_has_no_private_data` verde su pagina e rapporto.

## Scostamenti dal piano e perché

1. **Il testo di due proposte non è più identico a `task-5-proposte.md`**: i ritocchi dei punti 1 e 10 (decisione del controller) cadono proprio dentro la riga `Proposta:`. Per tenere insieme le due richieste (costante copiata dal file del workspace, ritocchi nella pagina) la costante `PROPOSALS` è la copia alla lettera del Task 5 e il test applica i ritocchi in modo esplicito (`RETOUCHES`, con controllo che ciascuno trovi il suo testo una volta sola). Così resta tracciabile cosa ha approvato l'utente e cosa è cambiato dopo.
2. **Test in più oltre ai sei dello Step 2**: `test_page_retouches_of_task_6` e `test_commands_page_says_approved` coprono i due ritocchi e la data in `comandi.md`, che nessun test guardava. In più `test_page_records_the_choices` riusa i controlli di contenuto del Task 5 (`check_choice_points`), che altrimenti dopo l'approvazione sarebbero spariti con `skip_if_approved`. Costano poco e sono compatibili.
3. **`comandi.md`**: oltre alla data, la frase dice dove `init` propone il profilo (come fa `rules-database`), con i tre casi della pagina.

## Autorevisione

- Completezza: Step 2 (tutti i test nominati, più i due sopra), Step 3 (`approved`, riga nella pagina, data in `comandi.md`), Step 4 (validate 0, test mirati PASS, suite verde sui due interpreti), Step 5 (commit con l'oggetto del piano e la riga Co-Authored-By di opus). Decisioni del controller: ritocchi, voce «Attivo», «Cosa hai deciso» con 31 punti, sparite le parti da decidere, conteggi veri, `comandi.md`.
- Skill: diff di una sola riga. Frammento, agenti, file approvati degli altri profili: non toccati (`git diff --stat` lo conferma).
- Nessun `__pycache__`, nessun file nuovo, nessun file del workspace nel commit.

## Dubbi

- Tre proposte approvate, copiate alla lettera, parlano ancora in forma di offerta («Se li vuoi, dimmelo: si rimettono…» al 19, «Se le trovi doppie, si uniscono nella prima» al 27, «puoi spostare ogni regola dicendomi il numero» al 30; anche «In alternativa si tolgono…» al 26 e «Se la vuoi tra le sovrapposizioni…» al 23). Le ho lasciate perché sono il testo approvato e il test le confronta con il Task 5 (come B7, che ha tenuto le proposte alla lettera). Restano vere come cambi possibili in una prossima revisione delle regole; se il controller le vuole al passato, è un cambio di testo e della costante.
- La frase «I tre agenti del profilo … arrivano dopo la tua approvazione» resta: vera, e uguale alla forma di `database.md`. Con il Task 7 si potrà dire che ci sono.
