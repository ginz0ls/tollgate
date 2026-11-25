# Task 4: report

## Mano 1 (Step 1, 2, 3a)

Opus, 23/11/2026, worktree `.claude/worktrees/c2`, ramo `c2-profilo-security`, HEAD `c0a60df`. Nessun commit, nessuna suite completa, nessun subagente.

### Cosa ho scritto

- `tests/test_rules_security.py` (nuovo, in git con `git add`): `RulesSecurityTest`, 21 test, dalla forma di `tests/test_rules_database.py` con le correzioni della decisione 17 di B7 (nessun ciclo vuoto: ogni test che itera controlla prima che ci siano regole; `assertTrue(re.search(…), "<messaggio fisso>")` invece di `assertIn` sul testo della skill dove serve; righe entro 100 caratteri; nessun aiuto non usato). I test: `test_frontmatter`, `test_has_title`, `test_first_section_is_prima_di_scrivere`, `test_rule_ids_consecutive`, `test_area_rules_of_research_match_rules`, `test_every_rule_has_a_source`, `test_every_rule_names_a_source_of_the_allowed_kinds` (vedi «Scostamenti»), `test_every_rule_names_what_is_judged`, `test_blocking_rules_judged_on_diff_or_report`, `test_blocca_lines_have_text`, `test_at_most_150_lines`, `test_denied_access_rule_exists`, `test_cc_by_sa_sources_are_ideas_only`, `test_where_to_look_names_skills`, `test_overlaps_name_approved_rules`, `test_user_choices_covered`, `test_fragment_matches_decisions`, `test_fragment_loads_through_the_loader`, `test_real_markers_not_in_tollgate_bin`, `test_real_security_markers_skip_tests`.
- `tests/test_init.py`: classe `SecurityPrecedenceTest` subito dopo `DatabasePrecedenceTest`, con `check = FrontendPrecedenceTest.check`, 71 test: `test_real_precedence_s1` … `s66`, `s67_manual_block`, `s68` … `s71`. I dati vengono dai `CASES` di `sonda-preflight/sonda.py` (generati da quei dati, poi riletti: sono la tabella della decisione 5). In più un metodo `check_active(files, active, detected=None)` che controlla `profiles.active_profiles` dove la tabella scrive «(`X` attivo)»: S4, S13, S16, S49, S50, S62, S63, S64, S68 (come fa la sonda). S67 è solo runtime: `vertical_for` e `active_profiles` sui due blocchi scritti a mano.
- `tests/test_fragments.py`: `test_real_fragments_load` con `security` (agente, `final_specialist`, marcatori presenti, `exclude == ("supabase/",)`, `keep_paths` vero, secondo pattern `name:middleware.*`) e `keep_paths` falso per gli altri cinque frammenti.
- `templates/profiles/security.toml` (nuovo, in git): decisioni 2, 3, 4, 10, 12, 13; i sei pattern in ordine, i 21 marcatori confermati (i quattro tolti non ci sono), `exclude = ["supabase/"]`, `keep_paths = true`, `min_level = "L2"`, `skills = []`, `reviewer_skills = []`, `commands = {}`, `dod = []`, i tre agenti, la `checklist` della decisione 10 alla lettera. Commenti come `database.toml`: per ogni pattern la fonte (catalogo 2, riga `security`; la pagina del Proxy di Next.js per `proxy.ts`/`proxy.js`), per ogni marcatore la pagina ufficiale della libreria (gli indirizzi di `pagine/marcatori.md`), per `exclude` il progetto di B, sezione 12, per `keep_paths` la scelta dell'utente del 22/11; in testa cosa resta fuori (decisione 1), in `[detect]` cosa non è un marcatore e il costo del testo fisso (`import jwt` accende anche `jwt-decode`, D10). Nessun testo copiato: solo indirizzi e nomi di sezione.
- `skills/rules-security/SKILL.md` (nuovo, in git): **solo lo scheletro**: frontmatter (`name: rules-security`, la `description` fissata da `test_frontmatter`, `version: 1`, nessun `approved`) e il titolo `# Regole security (versione 1)`, nella stessa forma di `rules-database` (titolo subito dopo `---`). Nessuna regola.
- `docs/uso/comandi.md`: la sezione `### \`/tollgate:rules-security\`` dopo quella di `rules-database` (niente «Argomenti:», niente «solo l'utente», niente data di approvazione: dice che è una bozza e che `init` non propone il profilo finché non è approvata; il Task 6 la cambia); nel paragrafo di `/tollgate:init`, accanto a `exclude`, una frase su `exclude` di `security` e una su `keep_paths` (D13).

**Come `init` e i test trattano la skill non approvata e gli agenti mancanti.** `fragments.load` non legge la skill (`skill_path` è solo un percorso), quindi il frammento si carica con la skill assente o non approvata. `init.profile_blocks` con il `PLUGIN_ROOT` vero non propone `security` finché la skill non ha `approved` (Task 6), e propone `agent`, `reviewer`, `final_specialist` solo se `agents/<nome>.md` esiste (`_agent_exists`; gli agenti li crea il Task 7). Per questo `SecurityPrecedenceTest` non ha bisogno di una copia preparata a mano: `check` usa `_real_fragments_root`, che copia **tutti** i frammenti veri (anche `security.toml`) con una skill finta approvata per ciascuno e senza la cartella `agents/`; la proposta ha quindi solo `paths` (le chiavi degli agenti non entrano, e `check` confronta solo i `paths`). La sonda invece crea agenti finti e controlla anche `final_specialist`. Effetto collaterale voluto: da ora anche `FrontendPrecedenceTest` e `DatabasePrecedenceTest` girano con `security` nei frammenti veri, e restano verdi senza toccarli (89 test).

### Evidenza RED (Step 2, prima del frammento e della skill)

Comando: `python3 -B -m unittest tests.test_init.SecurityPrecedenceTest`

```
Ran 71 tests in 0.356s
FAILED (failures=59)
```

Verdi già prima (con `-v`, le righe ` ... ok`): `test_real_precedence_s6`, `s11`, `s12`, `s23`, `s25`, `s32`, `s37`, `s38`, `s43`, `s48`, `s60` e `s67_manual_block` (12): esattamente quelli attesi (nessun blocco `security`, e S67 che è solo runtime). Gli altri 59 rossi per asserzione («Proposta»: manca il blocco `security`).

Comando: `python3 -B -m unittest -v tests.test_rules_security tests.test_fragments.RealFragmentsTest.test_real_fragments_load`

```
FAILED (failures=1, errors=20)
16 FileNotFoundError: …/skills/rules-security/SKILL.md
 2 FileNotFoundError: …/templates/profiles/security.toml
 2 ValueError: not enough values to unpack (expected 1, got 0)   (loader e detect_files: nessun frammento security)
 1 AssertionError: 'security' not found in {…}                    (test_real_fragments_load)
```

### Dopo il frammento, lo scheletro e la pagina d'uso (Step 3a)

Comando: `python3 -B -m unittest tests.test_rules_security tests.test_fragments tests.test_init tests.test_docs`

```
Ran 371 tests in 29.632s
FAILED (failures=18)
```

I 18 fallimenti sono tutti in `tests.test_rules_security` e sono **13 test** che aspettano il testo delle regole (sotto). Tutto il resto è verde: `SecurityPrecedenceTest` (71), `FrontendPrecedenceTest` e `DatabasePrecedenceTest` (89, invariati), `test_real_trees_light_no_profile`, i test della regola di I-1 e di `keep_paths`, `tests.test_fragments` intero, `tests.test_docs` intero (`test_every_skill_documented` con la sezione nuova). `python3 -B -m unittest tests.test_init.FrontendPrecedenceTest tests.test_init.DatabasePrecedenceTest tests.test_init.SecurityPrecedenceTest`: `Ran 160 tests`, `OK`. `python3 -B -m unittest tests.test_manifest`: `Ran 64 tests`, `OK` (lo scheletro non rompe i controlli generici sulle skill).

Verdi in `RulesSecurityTest` già con lo scheletro (8): `test_frontmatter`, `test_has_title`, `test_at_most_150_lines`, `test_fragment_matches_decisions`, `test_fragment_loads_through_the_loader`, `test_real_markers_not_in_tollgate_bin`, `test_real_security_markers_skip_tests` (più `test_real_fragments_load` in `tests.test_fragments`). Rossi in attesa delle regole (13): `test_first_section_is_prima_di_scrivere`, `test_rule_ids_consecutive`, `test_area_rules_of_research_match_rules`, `test_every_rule_has_a_source`, `test_every_rule_names_a_source_of_the_allowed_kinds`, `test_every_rule_names_what_is_judged`, `test_blocking_rules_judged_on_diff_or_report`, `test_blocca_lines_have_text`, `test_denied_access_rule_exists`, `test_cc_by_sa_sources_are_ideas_only`, `test_where_to_look_names_skills`, `test_overlaps_name_approved_rules`, `test_user_choices_covered` (5 sottotest più il conto finale).

### Sonda della tabella (Step 3a)

Una copia `git archive HEAD` in `/tmp/tollgate-sonda-t4-XXXXXX` con sopra i file non committati (`git status --short`), `TMPDIR`, `HOME` e `TOLLGATE_STATE` temporanei, poi `python3 -B "<W>/sonda-preflight/sonda.py" --codice <copia>`; cartella cancellata alla fine (verificato: nessuna `tollgate-sonda-t4-*` rimasta). La sonda ha usato il codice vero di `keep_paths` (Task 3) e il frammento del repo. Uscita 0:

```
keep_paths: del codice (Task 3); frammento security: del repo (Task 4); keep_paths del frammento = True
pattern: ['folder:auth', 'name:middleware.*', 'name:proxy.ts', 'name:proxy.js', 'folder:security', 'folder:rls']; exclude: ['supabase/']; marcatori: 21
== tabella della decisione 5 (S1-S66, S68-S71): 70 su 70 uguali
S67 (a mano, solo runtime): con **/auth/** → database (attivi ['database', 'security']); con supabase/functions/auth/** → security: uguale
== casi che la tabella non ha (attese dello scan): 12 su 12 uguali
ESITO: 70 casi su 70 uguali alla tabella; S67 uguale; casi in più: 12 su 12 come attesi dallo scan
```

Con i 21 marcatori (invece dei 25 del candidato) nessun caso cambia: la tabella dà i `detected` dal test, e i quattro marcatori tolti non compaiono nei casi. Nessuna differenza dalla tabella, quindi nessuna fermata né `Ruling:`. La stessa tabella sul codice vero è `SecurityPrecedenceTest` (71 verdi, sopra).

### `git status --short`

```
 M docs/uso/comandi.md
A  skills/rules-security/SKILL.md
A  templates/profiles/security.toml
 M tests/test_fragments.py
 M tests/test_init.py
A  tests/test_rules_security.py
```

Nessun `__pycache__` (tutto con `python3 -B`).

### Per la seconda mano (Step 3b): vincoli di forma che i test fissano

Il frontmatter e il titolo dello scheletro restano **uguali byte per byte** (`test_frontmatter` confronta la `description` alla lettera; `approved` non si scrive). Poi:

1. **Righe di regola:** `R-SECURITY-NN` a inizio riga, numeri consecutivi da `01`, eventualmente ` [blocca]`, poi uno spazio e il testo sulla stessa riga (`^R-SECURITY-\d{2}( \[blocca\])? \S`). Nessuna altra riga comincia con `R-SECURITY-`.
2. **Dopo ogni regola**, prima della successiva o del titolo successivo: una riga che comincia con `Fonte:` (la prima conta) e una riga esatta `Si giudica su: diff`, `Si giudica su: report` o `Si giudica su: nota` (riga intera, niente altro). Ogni `[blocca]` si giudica su `diff` o `report`, mai `nota`. Almeno una `[blocca]`.
3. **Tipi di fonte ammessi** (`test_every_rule_names_a_source_of_the_allowed_kinds`): la riga `Fonte:` contiene almeno uno di `https://`, `progetto di C, sezione`, `progetto di B, sezione`, `catalogo`, `spec del nucleo`, `idea di OWASP Cheat Sheet`, `idea di Trail of Bits`, oppure `security-and-hardening` o `security-auditor` con `MIT` nella stessa riga.
4. **CC BY-SA** (`test_cc_by_sa_sources_are_ideas_only`): ogni `OWASP` e ogni `Trail of Bits` di una `Fonte:` è preceduto subito da `idea di ` (forma: `idea di OWASP Cheat Sheet «Authorization»`, `idea di Trail of Bits \`insecure-defaults\``); se compare `insecure-defaults` o `differential-review` la riga ha `idea di Trail of Bits \`insecure-defaults\`` (o `\`differential-review\``) con i backtick; nessuna `Fonte:` contiene `ASVS` né `security-review`. Fra tutte le fonti almeno una `idea di OWASP Cheat Sheet` e almeno una `idea di Trail of Bits`.
5. **Accesso negato** (`test_denied_access_rule_exists`): almeno una regola `[blocca]`, `Si giudica su: diff`, con `catalogo 2.3` nella `Fonte:` e nel testo della regola una parola che comincia con `negat` e la parola `test`.
6. **Id fissati** (`test_user_choices_covered`, `test_overlaps_name_approved_rules`). Si cerca per id, quindi la numerazione deve avere:
   - `R-SECURITY-01`: chi può arrivare al codice cambiato, cosa può fare, quale controllo lo ferma (report); `Fonte:` con `progetto di C, sezione 11`;
   - `R-SECURITY-03`: il test del caso negato; `Fonte:` con `progetto di C, sezione 11` **e** `catalogo 2.3`;
   - `R-SECURITY-05`: valori predefiniti che rifiutano; `Fonte:` con `progetto di C, sezione 11`;
   - `R-SECURITY-10`: nessun segreto nel diff, nei log, nei messaggi d'errore; `Fonte:` con `progetto di C, sezione 11`; riga `Si sovrappone a: R-BACKEND-07, R-BACKEND-08, R-INFRA-05, R-INFRA-06, R-DATABASE-13` (esattamente questi cinque id, in qualunque ordine);
   - `R-SECURITY-12`: input non fidato validato al confine, query e comandi con parametri; `Fonte:` con `progetto di C, sezione 11`; riga `Si sovrappone a: R-BACKEND-03, R-BACKEND-06`;
   - **nessun'altra** regola ha `progetto di C, sezione 11` nella `Fonte:` né una riga `Si sovrappone a:` (il test confronta gli insiemi esatti).
   La riga `Si sovrappone a:` sta fra la regola e la successiva (come `Fonte:`); può avere dopo gli id una frase sulla differenza, purché non nomini altri id `R-<AREA>-NN`.
   Numerazione che ho in mente (dai temi della decisione 9, in ordine; solo una proposta, i test fissano solo 01, 03, 05, 10, 12): 01 chi arriva al codice (report); 02 documentazione ufficiale della versione di una libreria di sicurezza nuova nel file (report); 03 test del caso negato (diff); 04 autorizzazione sul server per ogni risorsa, non solo nel middleware o nel proxy (diff); 05 valori predefiniti chiusi (diff); 06 password con un hash lento con sale; 07 token verificati in firma e scadenza con l'algoritmo fissato; 08 confronto dei segreti a tempo costante; 09 cookie di sessione `HttpOnly`, `Secure`, `SameSite`; 10 segreti; 11 messaggi di login che non dicono se l'utente esiste; 12 input; 13 reindirizzamenti solo verso un elenco; 14 CORS senza `*` con credenziali; 15 limite di tentativi (nota, non `[blocca]`); 16 raggio d'azione (report); 17 nessuna azione sul sistema vero (report). Sono 17, uno più della stima «tra 12 e 16» della decisione 9: nessun test fissa il totale; per stare in 16 si possono unire 12 e 13 (gli id fissati restano).
7. **Sezioni:** il primo titolo `## ` è `## Prima di scrivere`; ci sono anche `## Mentre lavori`, `## Dove informarsi`, `## Fonti` (titoli esatti).
8. **Dove informarsi** (`test_where_to_look_names_skills`): la sezione `## Dove informarsi` (fino al titolo `## ` successivo) contiene `` `security-and-hardening` `` con i backtick; ogni riga di quella sezione che nomina `security-review` contiene anche `se installata` (e almeno una riga lo nomina).
9. **Al più 150 righe** in tutto il file (`len(text.split("\n")) <= 150`, frontmatter compreso).
10. Il paragrafo iniziale (Step 3b) e le sezioni non hanno vincoli di test oltre questi; `test_no_long_quotations` è del Task 5.

### Scostamenti dal piano e perché

- `test_every_rule_names_a_source_of_the_allowed_kinds` non è nell'elenco dello Step 1, ma è nella forma di `tests/test_rules_database.py` che il brief chiede di seguire, e mette nel test i tipi di fonte delle Global Constraints (MIT citate, CC BY-SA solo «idea di …», pagine ufficiali). Se il controller lo ritiene un extra, si toglie senza toccare il resto.
- `test_overlaps_name_approved_rules` controlla anche che ogni id nominato esista come regola nella skill approvata della sua area (e che quella skill sia approvata), oltre agli insiemi della decisione 15.
- `SecurityPrecedenceTest.check_active`: un metodo in più rispetto a `check` per le righe «(`X` attivo)» della tabella (come fa la sonda); `check` resta `FrontendPrecedenceTest.check`.
- La sezione di `comandi.md` riassume i temi della decisione 9, non le regole scritte (che non esistono ancora): se la seconda mano cambia un tema, la terza mano o il Task 6 la riallinea.

### Dubbi

- **«progetto di B 12» in `USER_CHOICES`** (domanda mandata al team-lead, nessuna risposta mentre scrivevo): non trovo una regola di `rules-security` che debba citare il progetto di B, sezione 12 (le edge function restano a `database`): è una scelta che il frammento applica (`exclude`), non una regola giudicabile sul diff. Per ora `USER_CHOICES` contiene solo le cinque scelte del 22/11 (progetto di C, sezione 11) e la sezione 12 del progetto di B è citata nel commento di `exclude` del frammento. Proposta: la seconda mano la scrive in una riga dell'introduzione della skill («una edge function sotto `supabase/` alla radice ha le regole di `database`»); se il controller vuole un controllo di test, è un'asserzione in più in `test_user_choices_covered` sull'introduzione, o una regola apposta (per esempio per la edge function annidata di S56). Da decidere prima della seconda mano.
- Gli id fissati (01, 03, 05, 10, 12) legano la numerazione della seconda mano: è la pratica di B7 («si cerca per id»), ma se Fable sceglie un altro ordine i test vanno cambiati da un giro di opus, non le regole.

## Mano 2 (Step 3b)

Fable, 23/11/2026. Ho scritto solo `skills/rules-security/SKILL.md` (aggiunto in coda allo scheletro: frontmatter e titolo invariati byte per byte) e `git add` di quel file. Nessun commit, nessuna suite completa, nessun subagente, nessuna rete. 107 righe, 17 regole, 13 `[blocca]`.

### Le regole

| Id | `[blocca]` | Si giudica su | Tema |
|---|---|---|---|
| 01 | sì | report | chi arriva al codice cambiato, cosa può fare, quale controllo lo ferma |
| 02 | no | report | documentazione ufficiale della versione di una libreria di sicurezza nuova nel file |
| 03 | sì | diff | test del caso negato per ogni controllo d'accesso nuovo o cambiato |
| 04 | sì | diff | autorizzazione sul server per ogni funzione, proprietario confrontato; non solo proxy o browser |
| 05 | sì | diff | valori predefiniti che rifiutano; nessun ripiego nel codice |
| 06 | sì | diff | password solo con hash lento e sale, da una libreria |
| 07 | sì | diff | token: firma e scadenza non spente, `algorithms` con jsonwebtoken e PyJWT, scadenza per i token creati |
| 08 | sì | diff | confronto dei segreti a tempo costante |
| 09 | sì | diff | cookie di sessione con `HttpOnly`, `Secure`, `SameSite` dichiarati; niente `localStorage` |
| 10 | sì | diff | segreti (con `Si sovrappone a:` e i cinque id) |
| 11 | no | diff | risposte di login, reset e recupero uguali se l'utente non esiste |
| 12 | sì | diff | input non fidato validato al confine, query e comandi con parametri (con `Si sovrappone a:` e i due id) |
| 13 | sì | diff | reindirizzamenti e richieste del server verso indirizzi del chiamante solo dopo un controllo |
| 14 | sì | diff | CORS con credenziali: origini da un elenco, mai `*` né l'origine rimandata indietro |
| 15 | no | report | limite di tentativi su login, reset e recupero: il report dice dove sta |
| 16 | no | report | raggio d'azione del cambio |
| 17 | sì | report | nessuna credenziale vera, nessuna azione su un servizio in linea |

### Fonte per regola, punto esatto (per il verificatore del Task 5)

Le copie sono in `W/fonti/security/`. «SH» = `agent-skills/security-and-hardening/SKILL.md`; «SA» = `agent-skills/security-auditor.md`; le schede I-n sono in `FONTI.md`.

- **01**: progetto di C, sezione 11, voce «Sicurezza fin dal progetto in ogni lavoro (utente)» (chi accede, dati, segreti, input ostili). SH, «Process: Threat Model First» (righe 21-40: confini di fiducia, casi d'abuso). Scelta nostra: che lo scriva il report, e la condizione «codice che non è solo test o documentazione».
- **02**: progetto di B, sezione 3.4 (la frase d'apertura sulle regole «Prima di scrivere» e la riga `base`: versione delle librerie dal file delle dipendenze). `pagine/marcatori.md`, voce jsonwebtoken («Fatti dal README, opzioni di `jwt.verify`»: `algorithms`, `ignoreExpiration`), indirizzo https://github.com/auth0/node-jsonwebtoken. Scelta nostra: l'estensione alle librerie di sicurezza e la via d'uscita (calcata su R-FRONTEND-01). **È la regola con la fonte più debole**: la sezione 3.4 di B non ha una riga `security`. Per questo non è `[blocca]`. Se il verificatore non la regge, si toglie e gli id da 03 in poi... **non** si possono rinumerare senza toccare i test (01, 03, 05, 10, 12 fissati): in quel caso serve un tema sostitutivo al posto 02 o un giro di opus sui test.
- **03**: progetto di C, sezione 11, stessa voce («accesso negato»). Catalogo 2.3, riga `security` («test dei casi di accesso negato», riga 96 del file). Scheda I-7. SH, «Process: Threat Model First», punto 4 (il caso d'abuso come primo test). Scelta nostra: «nel diff o già nel repo», e i due casi (senza credenziali, utente non proprietario; dalla decisione 9).
- **04**: SH, «Broken Access Control» (righe 130-148: confronto del proprietario) e «Never Do» (la validazione nel client non è un confine). Scheda I-6. `pagine/nextjs-proxy.md`, voce «Execution order» (riquadro «Good to know»). Scelta nostra: «dentro di essa o in una guardia applicata alla sua rotta» (per non vietare le guardie di rotta dei server). La frase su Next.js nomina solo le Server Function, come la pagina.
- **05**: progetto di C, sezione 11 («valori predefiniti chiusi»). Scheda I-8. Scheda I-6 («Deny by Default»). SH, «Sensitive Data Exposure» (righe 184-186: l'esempio lancia un errore se la chiave manca). Scelta nostra: gli esempi di ripiego (`process.env.X || "…"`, `os.environ.get("X", "…")`) e l'elenco di cosa è un'impostazione di sicurezza.
- **06**: SH, «Always Do (No Exceptions)» (hash delle password) e «Broken Authentication» (righe 94-100). SA, «2. Authentication & Authorization» (prima voce). Scheda I-1 (i nomi Argon2id, scrypt, bcrypt, PBKDF2 e degli hash veloci vengono dalla scheda). Scelta nostra: «attraverso una libreria».
- **07**: `pagine/marcatori.md`, voce jsonwebtoken (opzioni di `jwt.verify`) e voce PyJWT (la riga `jwt.decode(…, algorithms=[…])`). SH, «Security Review Checklist», «Authentication» (i token di reset scadono). SA, «2. Authentication & Authorization» (token di reset a tempo). Scelta nostra: la scadenza estesa a ogni token creato; «nessuna opzione spegne il controllo della firma» è formulata in generale ma l'unico esempio nominato è quello che ha una fonte (`ignoreExpiration`). Non nomino `jose` né python-jose: le copie non danno fatti sulle loro opzioni.
- **08**: scheda I-5. **Senza copia**: i nomi `hmac.compare_digest` e `crypto.timingSafeEqual` (librerie standard di Python e di Node.js) sono esempi miei, dichiarati tali nella `Fonte:`; nessun indirizzo, perché non ho una pagina copiata e non invento URL. Il verificatore decida se servono le due pagine ufficiali o se gli esempi si tolgono.
- **09**: SH, «Always Do (No Exceptions)» (cookie di sessione), «Never Do» (sessioni non in uno spazio leggibile dal client) e «Broken Authentication» (righe 102-113). Scheda I-2. Scelta nostra: chiedere i tre attributi scritti nel codice anche quando una libreria li imposta da sé (così la risposta è la stessa per due revisori).
- **10**: progetto di C, sezione 11 («segreti»). SH, «Never Do» (segreti nel controllo di versione, dati sensibili nei log, dettagli interni agli utenti), «Sensitive Data Exposure» (righe 177-182: hash e token di reset fuori dalle risposte), «Secrets Management». Scelta nostra: i valori finti nei test.
- **11**: scheda I-3. Scelta nostra: lo stesso codice di stato. Ho tolto «registrazione» perché la scheda non la nomina.
- **12**: progetto di C, sezione 11 («input non fidato»). SH, «Process: Threat Model First» (punto 1, da dove entra il dato non fidato), «Always Do (No Exceptions)» (validare l'input, query con parametri), «Injection (SQL, NoSQL, OS Command)», «Schema Validation at Boundaries». SA, «1. Input Handling». Scelta nostra: «con uno schema o con controlli espliciti di tipo e forma».
- **13**: SA, «1. Input Handling» (ultima voce: reindirizzamenti su un elenco) e «5. Third-Party Integrations» (ultima voce: SSRF). SH, «Server-Side Request Forgery (SSRF)». Scelta nostra: ammettere un percorso interno senza elenco; gli esempi `next` e `returnTo`.
- **14**: SH, «Security Misconfiguration» (righe 168-172) e «Red Flags» (origini `*`). SA, «4. Infrastructure». `pagine/nextjs-proxy.md`, voce «CORS». Scelta nostra: limitare la regola al caso con credenziali (decisione 9) e nominare l'origine rimandata indietro (conseguenza dell'elenco, non una frase di una fonte).
- **15**: SH, «Rate Limiting» (limite più stretto per le rotte di login; contatore condiviso). SA, «2. Authentication & Authorization» (ultima voce). Scheda I-4. Scelta nostra: giudicarla sul report (vedi «Dubbi»).
- **16**: scheda I-9. Catalogo 2.1, riga `security` (riga 61 del file: «revisione del diff per rischio e raggio d'azione»). Scelta nostra: che lo scriva il report e le tre cose che dice.
- **17**: spec del nucleo, sezione 8.5 (come la citano R-INFRA-12 e R-DATABASE-16; non ho riaperto la sezione). Scelta nostra: l'elenco delle azioni e la prova nel report. La `Fonte:` non nomina gli id delle altre aree.

Paragrafo iniziale: i criteri per riconoscere controllo d'accesso, token, password, cookie di sessione e segreto sono dichiarati «scelta nostra». `res.cookie` e `cookies().set` sono esempi miei (Express, Next.js), non in una copia; `session({ cookie: … })` è in SH «Broken Authentication». La frase su `supabase/` usa le parole «progetto di B, sezione 12». La frase «si segnala con la regola dell'area del file» viene dalla decisione 15.

In «Dove informarsi» gli indirizzi sono solo quelli di `FONTI.md`, `pagine/marcatori.md` e `pagine/nextjs-proxy.md`. «fino alla 15 `middleware.ts`» viene dalla voce «Version history» (rinominato dalla 16).

### Temi della decisione 9 tolti o cambiati

- Nessun tema tolto. 17 regole (la numerazione proposta dalla prima mano, invariata).
- **Reindirizzamenti (13) separati dall'input (12)**: sono due sì o no diversi, e solo 12 ripete regole approvate. 13 comprende anche le richieste del server verso un URL del chiamante (SSRF), che la decisione 9 metteva fra le fonti.
- **Token (07)**: «algoritmo fissato» vale come sì o no solo per jsonwebtoken e PyJWT, le due librerie di cui ho i fatti.
- **Limite di tentativi (15)**: non `[blocca]`, sul report e non sul diff.
- **Autorizzazione (04)**: allargata da «non solo nel middleware o nel proxy» a «sul server per ogni funzione, con il proprietario confrontato».

### Scelta dei `[blocca]`

Bloccano 13: 01, 03, 05, 10, 12 (scelte dell'utente), 04, 06, 07, 09, 13, 14 (difetto grave e visibile sul diff), 08, 17. Non bloccano 02 (fonte debole), 11 (gravità media), 15 (per decisione), 16 (una dichiarazione mancante non è un difetto grave). **Da far decidere all'utente:** 08 (confronto a tempo costante) è `[blocca]` perché sul diff si vede senza dubbi ed è il difetto tipico della verifica di una firma, ma lo sfruttamento è difficile: se sembra troppo, diventa una regola non bloccante senza altri cambi. 16 è il candidato opposto.

### Esito dei test

`python3 -B -m unittest tests.test_rules_security`:

```
....................
----------------------------------------------------------------------
Ran 20 tests in 0.099s

OK
```

`python3 -B -m unittest tests.test_docs tests.test_manifest`: `Ran 71 tests in 0.566s`, `OK`. Controllo a mano del futuro `test_no_long_quotations`: nessun testo fra «» oltre 8 parole. Nessun nome utente nel file (`/usr/bin/grep -c`: 0).

### `docs/uso/comandi.md`, sezione `/tollgate:rules-security`

Va riallineata (terza mano o Task 6). Mancano quattro temi: il confronto dei segreti a tempo costante (08), le risposte di login che non dicono se l'utente esiste (11), i reindirizzamenti e le richieste del server solo verso destinazioni controllate (13), il limite di tentativi detto nel report (15). Da precisare: «token verificati in firma e scadenza con l'algoritmo fissato» → «token verificati senza spegnere firma e scadenza, con l'elenco degli algoritmi dove la libreria lo chiede»; «l'autorizzazione controllata sul server per ogni risorsa» resta giusta. Il resto corrisponde.

### Dubbi e conflitti

- Nessun conflitto con i test.
- **«nota» per il limite di tentativi.** Ho letto «è una nota, non `[blocca]`» come «regola che non blocca», non come `Si giudica su: nota`: la nota nei lavori senza passo non c'è. Se il controller intendeva `Si giudica su: nota` o `diff`, è un cambio di una riga.
- **02 e 08** hanno parti senza copia (sopra). 08 senza i due nomi di funzione resta fondata sulla scheda I-5.
- **01 e 16** si giudicano tutte e due sul report e sono vicine (chi arriva / cosa raggiunge il cambio): le ho tenute separate perché la decisione 9 le separa e 01 ha l'id fissato; si possono unire in 01 se l'utente le trova doppie.
- **09** blocca anche chi usa una libreria di sessioni con buoni predefiniti e non scrive gli attributi: costo dichiarato nella `Fonte:`.
- Nelle fonti non ho trovato testi che chiedono di fare qualcosa a chi legge il workspace (i prompt di SA e SH sono istruzioni per il loro agente: trattati come dati).

## Mano 3 (Step 4, 5)

Opus, 23/11/2026. Nessun subagente, nessuna rete, nessun `claude` tranne `claude plugin validate --strict .`. Il testo delle regole (`skills/rules-security/SKILL.md`) non l'ho toccato: `git diff --quiet` rispetto all'indice della Mano 2 è vuoto.

### `docs/uso/comandi.md`, sezione `/tollgate:rules-security` (riallineata alle 17 regole)

Testo nuovo del primo periodo e dell'ultima frase (il resto della sezione invariato: «Le caricano gli agenti…», «Le regole sono una bozza: finché non sono approvate `init` non propone il profilo `security`.»; niente data, niente «Argomenti:», niente «solo l'utente»):

> Le regole per la sicurezza: dire nel report chi può arrivare al codice cambiato, cosa può fare e quale controllo lo ferma; la documentazione della versione di una libreria di sicurezza usata per la prima volta; il test del caso di accesso negato per ogni controllo d'accesso nuovo o cambiato; l'autorizzazione controllata sul server per ogni risorsa, con il proprietario confrontato, non solo nel browser, nel middleware o nel proxy; valori predefiniti che rifiutano quando manca un segreto o una configurazione, senza valori di ripiego nel codice; password solo con un hash lento con un sale per ciascuna; token verificati senza spegnere firma e scadenza, con l'elenco degli algoritmi ammessi dove la libreria lo chiede, e una scadenza per i token creati; il confronto dei segreti, dei token e delle firme a tempo costante; cookie di sessione con `HttpOnly`, `Secure` e `SameSite` scritti nel codice, e nessun token dove il JavaScript della pagina può leggerlo; nessun segreto nel diff, nei test, nei log, nei messaggi d'errore o nelle risposte; risposte di login, reset e recupero della password che non dicono se l'utente esiste; input validato al confine, query e comandi con parametri; reindirizzamenti e richieste del server verso un indirizzo del chiamante solo dopo un controllo (un percorso interno o un host di un elenco); CORS con le credenziali solo per origini di un elenco, mai `*`; il limite dei tentativi falliti su login, reset e recupero detto nel report; il raggio d'azione del cambio nel report; nessuna azione su credenziali vere o servizi in linea. […] Una edge function o una policy sotto `supabase/` alla radice ha le regole di `database`, non queste.

I 17 temi sono nell'ordine di R-SECURITY-01 … 17. Aggiunti i quattro mancanti (08, 11, 13, 15) e le precisazioni della Mano 2 (07 «senza spegnere firma e scadenza, con l'elenco degli algoritmi dove la libreria lo chiede»), più quelle che la lettura delle regole dava: 04 proprietario confrontato e «browser», 05 niente ripiego, 06 un sale per ciascuna, 07 scadenza dei token creati, 09 attributi scritti e niente `localStorage`, 10 test e risposte, 12 parametri, 14 «solo origini di un elenco». L'ultima frase (edge function a `database`) ripete l'introduzione della skill.

### Test aggiunto: `test_supabase_edge_functions_stay_with_database`

In `tests/test_rules_security.py`, subito dopo `test_user_choices_covered` (che resta com'era, perché quella scelta non è una regola con `Fonte:`). Prende l'introduzione (prima di `\n## Prima di scrivere\n`), cerca **un solo** paragrafo con `progetto di B, sezione 12` e controlla che lo stesso paragrafo abbia `edge function`, `policy`, `` `supabase/` alla radice `` e ``regole di `database` `` (sottotest per parola; `assertTrue` con messaggio fisso, decisione 17 di B7: nessun testo della skill stampato). Righe entro 100 caratteri.

Prova del rosso (script in scratchpad, con `SKILL` del modulo puntato a una copia in `tempfile.TemporaryDirectory(prefix="tollgate-red-t4-")`, cancellata alla fine; la skill vera non è cambiata):

```
frase tolta -> ROSSO ["AssertionError: 0 != 1 : l'introduzione non cita il progetto di B, sezione 12"]
solo la citazione tolta -> ROSSO ["AssertionError: 0 != 1 : l'introduzione non cita il progetto di B, sezione 12"]
database cambiato -> ROSSO ['AssertionError: False is not true : manca nella frase sul progetto di B, 12']
```

Sul testo vero: `python3 -B -m unittest -v tests.test_rules_security.RulesSecurityTest.test_supabase_edge_functions_stay_with_database` → `OK`. `tests.test_rules_security` intero: `Ran 21 tests`, `OK`.

### Verifica (Step 4)

`git add` dei sei file prima di tutto. Poi:

```
$ python3 -B -m unittest tests.test_rules_security tests.test_rules_database tests.test_rules_frontend tests.test_rules_backend tests.test_rules_ai tests.test_rules_infra tests.test_fragments tests.test_docs tests.test_init tests.test_manifest
Ran 659 tests in 30.292s
OK (skipped=10)

$ claude plugin validate --strict .
✔ Validation passed          (uscita 0; un avviso ICON_MISSING delle «plugin directory checks», che non cambia l'esito, già presente prima)

$ git status --short
M  docs/uso/comandi.md
A  skills/rules-security/SKILL.md
A  templates/profiles/security.toml
M  tests/test_fragments.py
M  tests/test_init.py
A  tests/test_rules_security.py
```

Nessun `__pycache__` (`find . -name __pycache__` vuoto).

### Suite completa

`{ PYTHONWARNINGS=error::ResourceWarning tests/run; echo "exit $?"; } > "<W>/suite-task-4.log" 2>&1`, con lo strumento Bash e `run_in_background`, poi il ciclo `until` in primo piano.

```
== Python 3.11.16
Ran 4458 tests in 2327.876s
OK (skipped=13)
== Python 3.13.5
Ran 4458 tests in 2259.671s
OK (skipped=11)
exit 0
```

Nessun «unclosed» né `ResourceWarning` nel log (`grep -ci`: 0). L'unica riga non di punti è `guard: la PR è avanzata dopo l'evento, nessuna scrittura (…)`, un messaggio del gate stampato da un test esistente, non un errore.

### Commit (Step 5)

`abccbe0 tollgate C2: bozza di rules-security, frammento del profilo security e tabella delle precedenze`: i sei file del task, con le due righe `Co-Authored-By` (Opus 5.5, Fable 5.2). Nessun amend, nessun `--no-verify`, nessun `index.lock` incontrato. `git status --short` dopo il commit: vuoto.

### Sonda sul codice committato

`bash "<W>/sonda-preflight/rilancia.sh" HEAD`:

```
ESITO: 70 casi su 70 uguali alla tabella; S67 uguale; casi in più: 12 su 12 come attesi dallo scan
```

### Dubbi sul testo delle regole (per il controller; non ho cambiato la skill)

- Nessun errore che contraddica i test o le decisioni. Due osservazioni di lettura, da far decidere a un giro di Fable se servono:
  - R-SECURITY-04 dice «In Next.js una Server Function lo verifica al suo interno», mentre la frase prima ammette anche «una guardia applicata alla sua rotta»: per le Server Function la guardia di rotta non basta (è proprio il punto della pagina del Proxy), quindi le due frasi sono coerenti, ma un revisore potrebbe leggerle in contrasto. Forse basta «(per una Server Function: al suo interno)».
  - Il paragrafo introduttivo dice «le regole segnate `[blocca]` si giudicano sul diff o sul report, perché nei lavori senza il passo «informati prima» la nota non c'è»: è vero per tutte le regole della skill (nessuna si giudica su `nota`), quindi la frase spiega un vincolo che qui non si vede. Innocuo.
- I dubbi della Mano 2 (02 con la fonte più debole, 08 con gli esempi senza copia, `[blocca]` di 08 e 16 da far scegliere all'utente) restano aperti per il Task 5 e il Task 6.

## Fix round 1, mano Fable

Fable, 23/11/2026, sopra il commit `abccbe0`. Ho toccato solo `skills/rules-security/SKILL.md` (28 righe cambiate, nessuna aggiunta né tolta). Nessun commit, nessun `git add`, nessuna suite completa, nessun subagente, nessuna rete. Frontmatter e titolo uguali byte per byte a `HEAD`; 17 regole nello stesso ordine; nessuna regola è passata da `[blocca]` a non bloccante o viceversa; `Si sovrappone a:` solo in 10 e 12 con gli stessi id; «progetto di C, sezione 11» solo in 01, 03, 05, 10, 12. Non toccate: 02 e 15. Il file ha 107 righe (`len(text.split("\n"))`). Nessun testo fra «» oltre 8 parole: vero.

### I1 (R-SECURITY-10) e il `no` della verifica delle fonti

Log e messaggi d'errore: tutto vietato. Corpo di una risposta: solo hash di password, token di reset e segreti del server; il token consegnato al suo titolare è escluso a parole. La parentesi della voce «progetto di C, sezione 11» è quella chiesta. La riga `Si sovrappone a:` dice l'allargamento (stessi cinque id).

> R-SECURITY-10 [blocca] Nessun segreto scritto nel codice, in un file versionato o in un test: nei test solo valori finti evidenti (come `PROVA-123`). Nessun segreto, token, password o hash di password in una riga di log o in un messaggio d'errore. Nel corpo di una risposta nessun hash di password, nessun token di reset e nessun segreto del server; il token consegnato al chiamante a cui appartiene (la risposta di un login, una chiave d'API mostrata al suo titolare quando la crea) non è questo caso.
> Si sovrappone a: R-BACKEND-07, R-BACKEND-08, R-INFRA-05, R-INFRA-06, R-DATABASE-13. Qui vale per ogni file dell'area, anche fuori da un server o da una configurazione, e comprende i test e, nelle risposte, gli hash delle password e i token di reset.
> Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: i segreti si considerano in ogni lavoro); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Never Do», «Sensitive Data Exposure» e «Secrets Management»; i valori finti nei test e l'eccezione per il token consegnato al suo titolare sono una scelta nostra

### I2 e m1 (R-SECURITY-04)

L'eccezione di Next.js sta fra parentesi accanto all'alternativa; la frase non segue più la riga della pagina. Due casi in cui non si applica, tutti e due visibili nel diff.

> R-SECURITY-04 [blocca] Se il diff aggiunge o cambia una funzione del server che legge o cambia dati legati a un utente (un endpoint, un gestore di rotta, una Server Function), il controllo di chi chiama gira sul server per quella funzione, mai solo nel codice del browser: dentro di essa o in una guardia applicata alla sua rotta (per una Server Function di Next.js solo dentro di essa: `proxy.ts` o `middleware.ts` da soli non bastano). Dove il dato ha un proprietario, il codice lo confronta con il chiamante. Non si applica a una funzione che è essa stessa il login, la registrazione, la richiesta di reset o la callback di un login, né a una funzione che legge solo dati pubblici, se il diff lo dichiara dove registra la rotta o in un commento accanto.
> Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Broken Access Control» (oltre a chi è il chiamante si controlla che la risorsa sia sua) e «Never Do» (un controllo fatto nel client non è un confine); idea di OWASP Cheat Sheet «Authorization» (permessi controllati a ogni richiesta e sul server); https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «Execution order»: un `matcher` che esclude un percorso salta anche le Server Function, che vanno protette una per una); la guardia di rotta e i due casi in cui la regola non si applica sono una scelta nostra

### I3 (R-SECURITY-09)

Cookie costruito dal codice: tre attributi dichiarati, `Secure` legato all'ambiente vale. Cookie di una libreria: solo non indebolire. `SameSite=None` solo con `Secure` e il motivo accanto (per questo ho tolto «(`Strict` o `Lax`)» e `sameSite: "none"` dagli esempi di indebolimento: lo regola la frase dopo). La frase su `localStorage` ora dice «il codice del diff», così non scatta su una libreria che lo fa da sé.

> R-SECURITY-09 [blocca] Se il diff costruisce da sé un cookie di sessione (l'intestazione `Set-Cookie`, una chiamata come `res.cookie` o `cookies().set` con opzioni proprie), il codice dichiara `HttpOnly`, `Secure` e `SameSite`; un `Secure` legato all'ambiente (vero in produzione) vale come dichiarato. Se il cookie lo scrive una libreria di sessioni o di login, il diff non ne indebolisce le opzioni (`httpOnly: false`, `secure: false`). In tutti e due i casi `SameSite=None` è ammesso solo insieme a `Secure` e con il motivo scritto accanto. Il codice del diff non salva un token di sessione o d'accesso dove il JavaScript della pagina può leggerlo (come `localStorage`).
> Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)», «Never Do» e «Broken Authentication»; idea di OWASP Cheat Sheet «Session Management» (i tre attributi si dichiarano, non si lasciano al browser); distinguere il cookie costruito dal codice da quello scritto da una libreria, accettare `Secure` legato all'ambiente e ammettere `SameSite=None` con il motivo sono una scelta nostra

### m2 (R-SECURITY-08)

> R-SECURITY-08 [blocca] Se il diff, nel codice che non è di test, confronta un segreto, un token, una firma o l'hash di un segreto con un valore ricevuto da fuori, usa una funzione a tempo costante (per esempio `hmac.compare_digest` in Python o `crypto.timingSafeEqual` in Node.js) o la funzione di verifica della libreria, non `==` né `===`. Una ricerca nel database per token non è un confronto.
> Fonte: idea di OWASP Cheat Sheet «Authentication» (hash e segreti si confrontano con una funzione sicura, non con l'uguaglianza normale); i due nomi di funzione sono esempi nostri, dalle librerie standard di Python e di Node.js; l'esclusione dei test e della ricerca nel database è una scelta nostra

### m3 (R-SECURITY-05)

La chiave di firma è nominata fra i segreti (nessun ripiego); l'elenco chiuso delle impostazioni ha le altre tre voci. Per l'interruttore il valore che nega è «il controllo acceso» (un `false` alla lettera dipenderebbe dal verso dell'interruttore).

> R-SECURITY-05 [blocca] Se il diff aggiunge o cambia codice che legge un segreto (anche una chiave di firma) o un'impostazione di sicurezza, quando il valore manca il codice si ferma o nega l'accesso. Per un segreto nessun valore di ripiego scritto nel codice (come `process.env.X || "…"` o `os.environ.get("X", "…")`). Per un'impostazione di sicurezza l'unico ripiego ammesso è il valore che nega (un elenco vuoto, il controllo acceso). Sono impostazioni di sicurezza solo queste: l'elenco delle origini ammesse, l'elenco dei ruoli ammessi, un interruttore che spegne un controllo. Un controllo d'accesso che non riconosce il caso (un ruolo sconosciuto, il ramo `default`) nega.
> Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: valori predefiniti chiusi); idea di Trail of Bits `insecure-defaults` (senza un segreto o una configurazione il programma rifiuta, non ripiega su un valore permissivo); idea di OWASP Cheat Sheet «Authorization» (si nega quando nessuna regola concede); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Sensitive Data Exposure» (l'esempio si ferma se la chiave non è configurata); gli esempi di ripiego e l'elenco chiuso delle impostazioni sono una scelta nostra

### m4 (R-SECURITY-01)

> R-SECURITY-01 [blocca] Se il diff cambia un file che non è un test né un documento, il report dice chi può arrivare al codice cambiato (un anonimo, un utente autenticato, un amministratore, un altro servizio), cosa può fare da lì e quale controllo lo ferma; se da fuori non ci arriva nessuno, lo dice.
> Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026, la sicurezza fin dal progetto: chi accede a ciò che si costruisce); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (i confini di fiducia e i casi d'abuso si pensano prima dei controlli); che il report lo scriva, e la condizione sul tipo di file, sono una scelta nostra

### m4 (R-SECURITY-16)

> R-SECURITY-16 Se il diff cambia un file che non è un test né un documento, il report dice il raggio d'azione del cambio: quali rotte e funzioni chiamano il codice cambiato, quali permessi e quali dati tocca, e cosa succede se è sbagliato (chi entra dove non deve, chi resta fuori).
> Fonte: idea di Trail of Bits `differential-review` (il raggio d'azione di un cambio si dichiara, non si dà per scontato); catalogo 2.1 (riga `security`: revisione del diff per rischio e raggio d'azione); che lo scriva il report, e la condizione sul tipo di file, sono una scelta nostra

### m5 (R-SECURITY-07)

> R-SECURITY-07 [blocca] Se il diff verifica un token firmato, nessuna opzione spegne il controllo della firma o della scadenza (come `ignoreExpiration: true` di jsonwebtoken), e con jsonwebtoken e PyJWT la chiamata passa l'elenco degli algoritmi ammessi, `algorithms` (`jwt.verify` di jsonwebtoken, `jwt.decode` di PyJWT). Un token che il diff crea (d'accesso, di sessione, di reset) ha una scadenza.
> Fonte: https://github.com/auth0/node-jsonwebtoken (opzioni di `jwt.verify`: `algorithms` è l'elenco degli algoritmi ammessi, `ignoreExpiration` salta la scadenza) e https://pypi.org/project/PyJWT/ (sezione «Usage»: la verifica passa `algorithms`); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Security Review Checklist», e `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization» (i token di reset scadono); l'obbligo di passare `algorithms`, il divieto di spegnere il controllo della firma e la scadenza per ogni token creato sono una scelta nostra

### m6 (R-SECURITY-11)

> R-SECURITY-11 Se il diff aggiunge o cambia la risposta di un login, di un reset o di un recupero della password, la risposta (messaggio e codice di stato) non fa capire quali account esistono: nel login è la stessa quando l'utente non esiste e quando la password è sbagliata; nel reset e nel recupero è la stessa quando l'utente esiste e quando non esiste.

### m7 (R-SECURITY-12)

> R-SECURITY-12 [blocca] Nel codice nuovo o cambiato un valore che arriva da fuori (corpo, parametri, query, intestazioni, cookie, il contenuto di un token non ancora verificato) si valida al confine, con uno schema o con controlli espliciti di tipo e forma, prima di usarlo. Le query al database e i comandi del sistema si costruiscono con parametri, mai concatenando quel valore. La verifica fatta dalla funzione di una libreria (di un token, di un cookie firmato) vale come validazione di quel valore.
> Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: input non fidato); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Process: Threat Model First», «Always Do (No Exceptions)», «Injection (SQL, NoSQL, OS Command)» e «Schema Validation at Boundaries»; `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Input Handling»; «con uno schema o con controlli espliciti» e la verifica di una libreria che vale come validazione sono una scelta nostra

### m8 (R-SECURITY-06)

> R-SECURITY-06 [blocca] Se il diff salva o controlla una password, usa attraverso una libreria una funzione di hash lenta nata per le password (Argon2id, scrypt, bcrypt, PBKDF2), con un sale diverso per ogni password. Nessuna password in chiaro o cifrata in modo reversibile, e nessun hash veloce (MD5, SHA-1, SHA-256 da solo). Non si applica quando il codice non salva la password e la passa a un servizio di login, che la controlla lui.
> Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Always Do (No Exceptions)» e «Broken Authentication»; `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Authentication & Authorization»; idea di OWASP Cheat Sheet «Password Storage» (funzione lenta per le password, un sale ciascuna, niente hash veloci); «attraverso una libreria» e il caso del servizio di login sono una scelta nostra

### m8 (R-SECURITY-13)

> R-SECURITY-13 [blocca] Se il diff reindirizza il browser, o fa partire una richiesta dal server, verso un indirizzo che viene dal chiamante (un parametro come `next` o `returnTo`, un URL nel corpo), l'indirizzo passa prima da un controllo: è un percorso interno del sito (non un URL completo, e nemmeno la forma `//host`), oppure il suo host è in un elenco di destinazioni ammesse.
> Fonte: `security-auditor` di agent-skills 0.6.9 (MIT), sezioni «Input Handling» (reindirizzamenti controllati su un elenco) e «Third-Party Integrations» (richieste del server verso un URL dell'utente); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Server-Side Request Forgery (SSRF)»; ammettere i percorsi interni, e dire cosa non lo è, sono una scelta nostra

### Fonti: «scelta nostra» dichiarata (R-SECURITY-03)

Il testo della regola non cambia.

> Fonte: progetto di C, sezione 11 (scelta dell'utente del 22/11/2026: l'accesso negato si considera in ogni lavoro); catalogo 2.3 (riga `security`: test dei casi di accesso negato); idea di OWASP Cheat Sheet «Authorization» (i test dell'autorizzazione provano anche il rifiuto); `security-and-hardening` di agent-skills 0.6.9 (MIT), sezione «Process: Threat Model First» (il caso d'abuso diventa il primo test); «nel diff o già nel repo» e i due casi da provare sono una scelta nostra

### Fonti: «scelta nostra» dichiarata (R-SECURITY-14)

Il testo della regola non cambia.

> Fonte: `security-and-hardening` di agent-skills 0.6.9 (MIT), sezioni «Security Misconfiguration» (CORS solo per origini note) e «Red Flags» (origini `*`); `security-auditor` di agent-skills 0.6.9 (MIT), sezione «Infrastructure»; https://nextjs.org/docs/app/api-reference/file-conventions/proxy (sezione «CORS»: l'intestazione si imposta solo per un'origine dell'elenco); limitare la regola al caso con le credenziali, e nominare l'origine rimandata indietro, sono una scelta nostra

### Fonti: «scelta nostra» dichiarata (R-SECURITY-17)

Il testo della regola non cambia.

> Fonte: spec del nucleo, sezione 8.5 (gli effetti esterni sono negati finché l'utente non li approva); l'elenco delle azioni e la prova detta nel report sono una scelta nostra, come nelle altre aree

### Sezione «Fonti»

Frase aggiunta (la sezione 8.5 «Effetti esterni» esiste nel file, riga 947):

> Il divieto di agire su un servizio vero senza l'approvazione dell'utente viene dalla spec del nucleo (docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md, sezione 8.5).

### Introduzione

La spiegazione sulla nota resta: lo spazio non serve (107 righe su 150).

### Esito dei test

`python3 -B -m unittest tests.test_rules_security tests.test_docs tests.test_manifest`:

```
----------------------------------------------------------------------
Ran 92 tests in 0.563s

OK
```

### Per la mano opus e per la pagina

- `docs/uso/comandi.md` (m9): cambiano i riassunti di 04, 05, 08, 09, 10, e anche 06 (caso del servizio di login), 11 (reset e recupero) e 13 (`//host`) se il riassunto scende a quel dettaglio.
- Da portare in «Da decidere tu»: le due forme di 09 (I3); 08 `[blocca]` o no; 01 e 16 vicine.

### Dubbi

- **09, cookie di una libreria con `sameSite: "none"`:** la regola chiede `Secure` e il motivo accanto anche lì; il controller lo aveva messo fra gli indebolimenti «senza un motivo scritto accanto», quindi l'esito è lo stesso, detto in una frase sola.
- **05, «il controllo acceso»** al posto di `false`: è la stessa decisione del controller detta senza dipendere dal nome dell'interruttore; se si preferisce `false` alla lettera è un cambio di due parole.
- **08:** ho dichiarato «scelta nostra» anche l'esclusione dei test e della ricerca nel database (non era nell'elenco della verifica, ma è una parte nuova senza fonte).
- **10:** «token di reset» nel corpo di una risposta resta vietato anche verso chi lo ha chiesto (arriva per un altro canale): viene da `security-and-hardening`, «Sensitive Data Exposure».

## Fix round 1, mano opus

Opus, 23/11/2026, sopra `abccbe0` e la modifica della mano Fable a `skills/rules-security/SKILL.md` (non toccata: solo `git add`). Nessun subagente, nessuna rete, nessun `claude` tranne `validate`.

### m9: `docs/uso/comandi.md`, sezione `/tollgate:rules-security`

Riallineati i riassunti di 04, 05, 06, 08, 09, 10, 11, 13 al testo corretto. Il resto della sezione è invariato (bozza, niente data, niente «Argomenti:», niente «solo l'utente»). Testo nuovo della sezione:

> Le regole per la sicurezza: dire nel report chi può arrivare al codice cambiato, cosa può fare e quale controllo lo ferma; la documentazione della versione di una libreria di sicurezza usata per la prima volta; il test del caso di accesso negato per ogni controllo d'accesso nuovo o cambiato; l'autorizzazione controllata sul server per ogni funzione che tocca dati di un utente, dentro di essa o in una guardia della sua rotta, mai solo nel browser, con il proprietario confrontato (una Server Function di Next.js la controlla al suo interno: `proxy.ts` o `middleware.ts` da soli non bastano), tranne che nel login, nella registrazione, nella richiesta di reset, nella callback di un login e nelle funzioni che leggono solo dati pubblici e lo dichiarano nel diff; valori predefiniti che rifiutano quando manca un segreto o un'impostazione di sicurezza: nessun ripiego per un segreto, per un'impostazione solo il valore che nega; password solo con un hash lento con un sale per ciascuna, quando il codice le salva o le controlla; token verificati senza spegnere firma e scadenza, con l'elenco degli algoritmi ammessi dove la libreria lo chiede, e una scadenza per i token creati; il confronto dei segreti, dei token, delle firme e degli hash dei segreti a tempo costante, fuori dai test; cookie di sessione con `HttpOnly`, `Secure` e `SameSite` scritti nel codice quando il codice li costruisce da sé, opzioni non indebolite quando li scrive una libreria, `SameSite=None` solo con `Secure` e un motivo scritto, e nessun token dove il JavaScript della pagina può leggerlo; nessun segreto nel diff o nei test, nessun segreto, token o hash di password nei log o nei messaggi d'errore, e nelle risposte nessun hash di password, token di reset o segreto del server (il token consegnato al suo titolare, come la risposta di un login, è ammesso); risposte di login, reset e recupero della password che non dicono quali account esistono; input validato al confine, query e comandi con parametri; reindirizzamenti e richieste del server verso un indirizzo del chiamante solo dopo un controllo (un percorso interno, non `//host`, o un host di un elenco); CORS con le credenziali solo per origini di un elenco, mai `*`; il limite dei tentativi falliti su login, reset e recupero detto nel report; il raggio d'azione del cambio nel report; nessuna azione su credenziali vere o servizi in linea. Le regole su segreti e input ripetono quelle di `backend`, `infra` e `database`, perché un file che va a `security` non riceve le loro. Una edge function o una policy sotto `supabase/` alla radice ha le regole di `database`, non queste. Le caricano gli agenti dell'area `security`, quindi non serve lanciarla a mano. Le regole sono una bozza: finché non sono approvate `init` non propone il profilo `security`.

Cosa cambia rispetto ad `abccbe0`: 04 non dice più «non solo nel middleware o nel proxy» in generale (m9: la guardia di rotta è ammessa, proxy e middleware non bastano solo per le Server Function) e nomina i due casi in cui la regola non si applica (I2); 05 distingue segreto (nessun ripiego) e impostazione (solo il valore che nega) (m3); 06 vale quando il codice salva o controlla la password (m8); 08 comprende gli hash dei segreti e non vale nei test (m2); 09 distingue il cookie costruito dal codice da quello di una libreria e dice di `SameSite=None` (I3); 10 separa log e messaggi d'errore dal corpo delle risposte, con il token consegnato al titolare ammesso (I1); 11 «quali account esistono» (m6); 13 nomina `//host` (m8).

### m10: docstring di `SecurityPrecedenceTest`

`tests/test_init.py:1914-1920`: «`detected` … lo dà il test, di norma senza i file sotto un `exclude` (come farebbe `detect_files`); S43 ne dà uno apposta, come la sua riga della tabella». La frase su `check_active` dice anche i casi nuovi di m11.

### m11: `check_active` su S14, S20, S42, S51, S52, S58, S65

Per ognuno, dopo `check`, `check_active` sul file sotto `auth/` che va a un altro profilo, con l'attesa `[<altro>, "security"]` (e lo stesso `detected` del caso dove c'è: S42, S58, S65). **Tutti e sette danno `security` attivo**: nessun caso da riportare, nessun caso cambiato. `python3 -B -m unittest tests.test_init.SecurityPrecedenceTest`: `Ran 71 tests`, `OK`.

### m12 e commenti dei pattern: `templates/profiles/security.toml`

- m12: il commento sul testo fisso dice che `import jwt` accende anche `import jwt from 'jsonwebtoken'`, la forma ESM di un marcatore tolto (la pagina di jsonwebtoken mostra solo `require`).
- `**/security/**` e `**/rls/**`: il commento dice che il pattern è del catalogo 2, riga `security`, che il catalogo non dice cosa contiene la cartella, e che la descrizione (intestazioni e politiche; policy di accesso alle righe) è una lettura nostra. Per `rls/` la parte su `supabase/` cita ora il progetto di B, sezione 12.
- `**/auth/**`: stessa correzione per coerenza («che ci stia il codice di login e di controllo d'accesso è una lettura nostra»), perché la frase aveva la stessa forma. È oltre la lettera del brief, ma nello spirito dell'osservazione della verifica; `**/middleware.*` e i `proxy.*` restano come sono (la verifica li ha trovati giusti).
- Nessuna chiave del frammento cambia: solo commenti. Righe nuove entro 100 caratteri (l'unica più lunga è `checklist`, già così in `abccbe0`).

### Verifica

```
$ git add docs/uso/comandi.md skills/rules-security/SKILL.md templates/profiles/security.toml tests/test_init.py
$ python3 -B -m unittest tests.test_rules_security tests.test_fragments tests.test_init tests.test_docs tests.test_manifest
Ran 436 tests in 24.186s
OK
$ claude plugin validate --strict .
✔ Validation passed   (uscita 0)
$ git status --short
M  docs/uso/comandi.md
M  skills/rules-security/SKILL.md
M  templates/profiles/security.toml
M  tests/test_init.py
```

Nessun `__pycache__`.

### Suite completa

Con le tre righe, uscita su `<W>/suite-task-4-fix-1.log`:

```
== Python 3.11.16
Ran 4458 tests in 1894.964s
OK (skipped=13)
== Python 3.13.5
Ran 4458 tests in 1864.451s
OK (skipped=11)
exit 0
```

Nessun «unclosed» né `ResourceWarning` (`grep -ci`: 0).

### Commit

`1749ee8 tollgate C2: rules-security, correzioni dopo la revisione e la verifica delle fonti`: i quattro file, con le due righe `Co-Authored-By` (Opus 5.5, Fable 5.2). Commit nuovo, nessun amend, nessun `--no-verify`, nessun `index.lock`. `git status --short` dopo il commit: vuoto.

### Sonda sul codice committato

`bash "<W>/sonda-preflight/rilancia.sh" HEAD`:

```
ESITO: 70 casi su 70 uguali alla tabella; S67 uguale; casi in più: 12 su 12 come attesi dallo scan
```

### Dubbi

- Il commento di `**/auth/**` l'ho corretto anche se il brief nominava solo `security/` e `rls/` (stessa forma del difetto). Se il controller lo vuole com'era, è un cambio di tre righe di commento.
- La sezione di `comandi.md` è ora lunga (un solo paragrafo con 17 temi): per la pagina del Task 6 si può spezzare in un elenco, ma `test_every_skill_documented` non lo chiede e le altre sezioni `rules-*` sono un paragrafo, quindi l'ho lasciata così.
