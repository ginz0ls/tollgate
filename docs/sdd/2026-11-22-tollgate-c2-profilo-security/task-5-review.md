# Task 5: revisione (commit `12c0b2d`, pacchetto `review-1749ee8..12c0b2d.diff`)

Revisore Fable, 23/11/2026, sola lettura. Nessun subagente, nessuna rete, nessun `claude`. Suite non rilanciata (`suite-task-5.log`: 4474 test, `OK` sui due interpreti, `exit 0`, nessun avviso).

Controlli fatti oltre alla lettura del pacchetto, ognuno per un rischio preciso:

- **La pagina attribuisce al profilo un costo che c'è già.** Controllo: `bin/tollgate_core/config.py:40` (predefinito `levels.sensitive_paths = ["**/migrations/**", "**/auth/**"]`), `bin/tollgate_analysis/level.py:41` («un percorso sensibile dà sempre L2»), `bin/tollgate_checks/_common.py:322-331` (il ricalcolo). Esito: rilievo I-1.
- **«Note a chi rivede» dice più del vero.** Controllo: `bin/tollgate_checks/task_verdict.py:54-62` (`known_rules` e `blocking_rules` dei profili attivi entrano solo nel controllo del verdetto), `bin/tollgate_analysis/profiles.py:76-91` (`task_routing`: un solo revisore, quello del verticale che vince), `agents/reviewer-backend.md:5` (`skills: [rules-base, rules-backend]`), spec del nucleo riga 498 («non è precaricata, … restano note al verdetto»). Esito: rilievo I-2.
- **Un caso citato che non dice ciò che la pagina gli fa dire.** Controllo: ogni `S…` e `N…` di «Da decidere tu» contro la tabella della decisione 5 e la sezione 0 dello scan. Esito: tutti giusti (dettaglio in «Aderenza»).
- **Immagini e testi tradotti che in realtà non accendono la cartella.** Controllo: `bin/tollgate_flow/init.py:39-40` (`DOC_EXTENSIONS`: solo i documenti non accendono). Esito: il punto 10 è vero.
- **Il task «da dividere» del punto 4.** Controllo: `profiles.py:88-89` (`split` con due agenti diversi). Esito: vero.
- **Le sovrapposizioni descritte male.** Controllo: le righe di R-BACKEND-03, 06, 07, 08, 12, R-INFRA-05, 06, 12, R-DATABASE-13, 16 nelle skill approvate. Esito: la colonna «Cosa cambia» è fedele.
- **Citazioni del rapporto inventate o spostate.** Controllo a campione: 19 righe di `fonti/security/agent-skills/security-and-hardening/SKILL.md` (23, 38, 50, 52, 67-69, 72, 110, 137, 168, 178, 186, 206, 333, 340, 359, 434, 498) contro la cella del rapporto. Esito: tutte uguali.
- **Test che non proteggono.** Sei mutazioni e una simulazione dell'approvazione su una copia `git archive 12c0b2d` in `/tmp/tollgate-rev-…`, resa repo privato e cancellata alla fine (base: 37 test `OK`). Esito in «Test» e nel rilievo m-9.

## Aderenza

- ✅ **File del task.** Solo i cinque attesi; nessun `approved` nella skill; nessun agente né file approvato toccato; commit nuovo con le due righe `Co-Authored-By`.
- ✅ **Sezioni.** Pagina: «Cosa sono», «Quando si accende», «Le regole», «Cosa cambia nei tuoi progetti», «Regole che si sovrappongono», «Da decidere tu», «Regole tolte dalla verifica», «Come rispondere» con «Rinvio». Rapporto: le cinque sezioni fissate più «Sovrapposizioni».
- ✅ **Copia di «Da decidere tu».** `W/task-5-proposte.md` è uguale alla sezione della pagina (`diff`: solo una riga vuota in coda).
- ✅ **Tabella delle regole.** 17 righe nell'ordine; «Blocca?» e «Si giudica su» uguali alla skill (13 sì; report per 01, 02, 15, 16, 17); «Da dove viene» fedele a ogni `Fonte:`. Le semplificazioni del testo non cambiano il senso, salvo le due del rilievo m-1.
- ✅ **Step 3, punto per punto.** S4, S39, S54 (1); S49, S50 (3); S61-S64 con «scelta nostra» (6); S53 con la frase del piano alla lettera (5); terzi, immagini, testi tradotti, `middleware.yaml` con il rimedio (10); S51, S52, S16 (7); S9, S46, S57, S59 (8); `**/proxy.ts`/`.js` (9); forme fuori (11); S13, S34 (12); S19, S40, S44 (13); S68-S71 (14); `import jwt`, `jose`, `iron-session` (16-18); `supabase/`, S11, S56, S67 (20); sovrapposizioni (21, 22); `dod` (24); «scelta nostra» (31).
- ✅ **Decisioni del controller.** D8: N4 (2) e N9 (4); D10: `jwt-decode` e gli import JavaScript (16); marcatori tolti con «si rimettono» (19); D14 (5, con la frase dell'utente citata e il costo dell'altra strada); R-08 blocca o no (25); 01 e 16 (27); le due forme di 09 con il costo N3(c) (28); R-15 (29); 17 di cui 13 (30); esempi nostri (26); `iron-session` (18).
- ✅ **Casi citati.** Tutti dicono ciò che la pagina gli fa dire, compresi quelli in più: S30, S58, S65, S14, S20, S42, S29, S55, S66, S6, S60, S32, S22-S24, S38.
- ✅ **Conteggi.** 31 punti (introduzione, «Su trentuno punti», elenco); 17 regole, 13 bloccano; 7 sovrapposizioni; rapporto 43 righe (42 `ok`, 1 `no`), 21 marcatori, 6 pattern, 10 voci «idea letta dal controller sulla pagina».
- ✅ **Rinvio** coerente con la decisione 19 (Task 1-3 su `main` dal ramo `c2-parziale`; bozza, pagina e frammento sul ramo).
- ✅ **Vincoli.** Citazioni su una riga e solo nel rapporto; nessuna frase di terzi nella pagina; nessun percorso della home, nome utente, host, token; nessun conteggio dei progetti dell'utente (la frase sulle «sessioni di chat» è già nel progetto di C, riga 190, che è pubblico).
- ✅ **I quattro ritocchi alla skill.** Fanno ciò che la ruling chiede (N1 a e b, N2 a e b, N3 a e b, R-05); numero, tema e `[blocca]` invariati; 107 righe. **Passata del verificatore sulle righe toccate: tutte `ok`.** 04: la definizione di «dati pubblici» sta dentro «i due casi … sono una scelta nostra». 05: la frase sui test è dichiarata nostra nella `Fonte:`. 09: «dichiara accesi» regge su `security-and-hardening` riga 52 e sulla scheda I-2; il motivo di `SameSite=None` è tra le parti dichiarate. 10: la password nelle risposte regge su «Sensitive Data Exposure» (righe 178-182: campi sensibili, `passwordHash`, `resetToken`); la riga «Si sovrappone a» resta vera contro R-BACKEND-08. Nessun buco nuovo, nessuna frase uguale a una fonte.
- ✅ **`docs/uso/comandi.md`** riallineato ai ritocchi di 05, 09 e 10.
- ❌ **«La pagina dice il vero»**: due punti, I-1 e I-2.
- ⚠️ **Non verificabile qui:** quanto le schede I-1…I-9 siano lontane dal testo di OWASP e di Trail of Bits (le pagine non sono nel workspace, per la decisione 8); i due nomi di funzione di R-SECURITY-08 (la pagina lo dice al punto 26).

## Test

Mutazioni sulla copia (comando `python3 -B -m unittest tests.test_rules_security`):

| Mutazione | Esito |
|---|---|
| tolta la riga 8 dalla tabella delle regole | rosso: `test_page_lists_every_rule`, `test_page_blocca_matches_skill`, `test_page_judged_on_matches_skill` |
| riga 11, «Blocca?» da `no` a `sì` | rosso: `test_page_blocca_matches_skill` |
| riga 15, «Si giudica su» da report a diff | rosso: `test_page_judged_on_matches_skill` |
| tolto il punto 25, conteggi non toccati | rosso: `test_page_choices_count_matches_list` |
| tolto il punto 25, «trentuno» → «trenta» | **verde** |
| tolti i punti 21, 22, 25, 27, 28, 29, «trentuno» → «venticinque» | **verde** |
| `approved` nella skill, «Da decidere tu» e «Rinvio» tolti | 3 test saltati; rosso solo `RulesSecurityTest.test_frontmatter` (Task 4, lo cambia il Task 6 per forza) |

Nessun test nuovo fissa testo che il Task 6 deve cambiare senza `skip_if_approved`.

## Punti di forza

- La pagina segue la forma di `docs/profili/database.md` frase per frase dove il meccanismo è lo stesso (L2, gate, `/tollgate:finish`, `dod`), quindi l'utente ritrova parole che ha già approvato.
- Ogni punto ha un costo e una proposta; «Come rispondere» permette davvero una riga («approvo, ma al punto 25 non blocca»).
- Il punto 5 dice apertamente che tre casi non seguono la frase dell'utente del 22 novembre, e quanto costa l'altra strada.
- Il rapporto tiene la riga `no` come storia, dichiara le note del verificatore fuori dalla colonna dell'esito e dice che i ritocchi non erano ripassati.
- I test calcolano conteggi ed elenchi da skill e frammento; le asserzioni sui dati privati non stampano il valore trovato.

## Rilievi

### Critical

Nessuno.

### Important

**I-1 — testo della pagina (mano Fable).** `docs/profili/security.md:80`, `:124-125`, `:127`, `:151-152`, `:160`, `:163`, `:166`.
- **Cosa.** La pagina presenta «sale a L2» come costo del profilo anche per i file sotto una cartella `auth/`, e ai punti 1 e 10 dà come rimedio «togli quel percorso dal blocco». Ma sotto `auth/` il lavoro è L2 già oggi, senza il profilo: `**/auth/**` è tra i `levels.sensitive_paths` predefiniti e un percorso sensibile dà sempre L2.
- **Perché conta.** Su sei punti (1, 2, 10, 13, 14, 15) l'utente decide credendo che il profilo porti in L2 lavori che ci sono già. E il rimedio promesso non toglie L2 per `vendor/lib/auth/`, `public/auth/`, `i18n/auth/` e per il modulo di login: toglie solo gli agenti di sicurezza e lo specialista. Lo dicono la decisione 13 («sotto `auth/` succede già oggi») e il caso S22 («già oggi per `sensitive_paths`»); la pagina lo ha perso. Il rimedio viene dalla decisione 1: per quella parte è «imposto dal piano».
- **Come correggere.** Una frase in «Il lavoro sale a L2»: sotto `auth/` (e `migrations/`) il lavoro è già L2 anche senza il profilo; lì il profilo cambia chi scrive, chi rivede e lo specialista. L2 è nuovo per `security/`, `rls/`, i file `middleware` e `proxy` e i file riconosciuti dal contenuto. Poi nei punti 1, 2, 10, 13, 14, 15 il costo dice cosa cambia davvero, e il rimedio dei punti 1 e 10 dice che toglie agenti e specialista, non il livello (per `middleware.yaml` e `security/` toglie anche quello).

**I-2 — testo della pagina (mano Fable).** `docs/profili/security.md:92`, `:124`, `:130`, `:133`, `:157`, `:164`.
- **Cosa.** «Le regole restano note a chi rivede» e, al punto 3, «le applica solo chi rivede». Nel codice «note» vuol dire che il verdetto accetta quegli id; il revisore del task è quello dell'area che vince e ha caricate solo le regole della sua area.
- **Perché conta.** È una semplificazione che cambia il senso del costo.
  - Punto 3 e riga 92 (rotta di login che resta a `backend`): le regole di sicurezza le applica solo `final-security`, a fine lavoro e solo quelle sul diff. Le cinque sul report (1, 2, 15, 16, 17; la 1 e la 17 bloccano) per quel task non le ha davanti nessuno.
  - Punto 1 (modulo di login che va a `security`): le regole di `frontend` non le ha caricate né chi scrive né chi rivede, e `frontend` non ha uno specialista finale.
  - Punto 4 (agenti generici): né chi scrive né chi rivede ha le regole delle due aree.
  - Punti 12 e 14: per `database` c'è `final-database`, sul diff.
  La pagina approvata di `database` dice la cosa com'è: «quel file non segue le regole del database» (`docs/profili/database.md:168`). Il piano scrive «note al verdetto ma non precaricate» (decisioni 4, 5, 15): la pagina ha tenuto metà della frase.
- **Come correggere.** Sostituire «note a chi rivede» con la frase vera, caso per caso, in parole semplici: chi può citarle (il verdetto le accetta), chi le ha caricate (solo lo specialista finale, dove esiste, e solo per le regole sul diff), e che a livello di task non le ha davanti nessuno. Il punto 3 lo dice come costo.

### Minor

- **m-1 — testo della pagina (Fable).** `security.md:64` (riga 9) e `:214` (punto 31). La riga 9 dice «accende i tre interruttori», ma la regola ammette `SameSite=None` con `Secure` e un motivo scritto, e un `Secure` legato all'ambiente: due «scelte nostre» che la pagina non porta da nessuna parte. Il punto 31 per R-SECURITY-09 rimanda solo al punto 28, e per R-SECURITY-07 salta «il divieto di spegnere il controllo della firma». Aggiungerle al punto 31 e mezza frase alla riga 9. Stessa famiglia, più leggere: la riga 4 (`:59`) salta la callback di un login, la riga 5 (`:60`) salta «un interruttore che spegne un controllo» e i valori finti nei test.
- **m-2 — testo della pagina (Fable).** `security.md:154` (punto 11) o `:48`. La decisione 4 esclude dai marcatori anche `crypto`, `hashlib` e `hmac` delle librerie standard: un file che firma token con quelle non è riconosciuto dal contenuto. La pagina non lo dice. Una voce in più al punto 11.
- **m-3 — testo della pagina (Fable).** Termini usati senza spiegazione: «frammento» (`:92`, `:225`), «monorepo» (`:163`, e a `:181` spiegato solo a metà), «Server Function» (`:59`), «policy» (`:157-158`, dopo un titolo che dice «regole di accesso»). Una riga di glossario o due parole tra parentesi.
- **m-4 — testo della pagina (Fable).** `security.md:37`. Manca come arriva la proposta in un progetto che ha già tollgate (`/tollgate:init --update`; uno nuovo con `--propose`): la pagina di `database` lo dice (`database.md:41`), ed è la prima cosa che l'utente deve fare dopo l'approvazione.
- **m-5 — testo della pagina (Fable).** `security.md:225`. Il rinvio non dice il suo costo (decisione 19: C2 resta aperta e C3 aspetta). Mezza frase.
- **m-6 — testo della pagina (Fable).** `security.md:122`. Trentuno punti sono tanti per chi non è specialista. Una riga in testa che nomina i pochi punti dove la scelta cambia davvero qualcosa (5, 19, 25, 28) e dice che gli altri sono costi da conoscere aiuterebbe a rispondere. Facoltativo.
- **m-7 — testo del rapporto (Fable).** `security-fonti.md:136`. «I file che `init` riconosce come test sono saltati» è vera ma incompleta (già nel ledger come minor rinviato; confermo su `init.py:45-46`). La frase proposta dalla mano 3 va bene: salta le cartelle `tests/`, `test/`, `__tests__/` e i nomi `*.test.*`, `*.spec.*`, `*_test.*`, `test_*.py`, `conftest.py`; un test dentro una cartella del profilo si accende per il percorso (S22).
- **m-8 — testo del rapporto (Fable).** `security-fonti.md:17`. «Questi ritocchi non sono ripassati dal verificatore» non è più vero dopo questa revisione: le righe toccate di 04, 05, 09 e 10 sono state rilette qui, tutte `ok`. Aggiornare la frase.
- **m-9 — test (opus).** `tests/test_rules_security.py`, `CHOICE_NEEDLES` e `test_page_brings_the_open_choices_to_the_user`. Le parole chiave si cercano in tutta la sezione, e il punto 31 nomina tutti e 17 gli id: le voci `R-SECURITY-10`, `-12`, `-08`, `-01`, `-16`, `-09`, `-15` non provano niente. Tolti i punti 21, 22, 25, 27, 28, 29 con i conteggi aggiornati, la classe resta verde. Lo protegge solo il conteggio, che scatta se chi toglie un punto dimentica di cambiare «trentuno». Correzione: per quelle voci cercare l'id nel titolo in grassetto di un punto (o nel punto che ha anche una seconda parola: «blocca», «vicine», «forme»). Stesso difetto, più leggero, in `test_page_explains_what_changes`, che cerca i testi in tutta la pagina. Minor e non Important perché i test muoiono con il Task 6 e una perdita non voluta la ferma il conteggio.

Fuori dal task, già nel ledger: `tests/test_rules_database.py` e `tests/test_rules_frontend.py` stampano il valore trovato se un giorno trovano nome utente o host.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** rapporto, ritocchi e test reggono, ma la pagina dice due cose non vere proprio dove l'utente deve decidere: il livello L2 sotto `auth/` come costo del profilo (c'è già, e il rimedio promesso non lo toglie) e le regole dell'altra area «note a chi rivede» (non le ha caricate nessuno a livello di task). Sono correzioni di testo, una mano Fable; i nove Minor si possono fare nello stesso giro.
