# Revisione del Task 10 (C2): spec rev 37, catalogo, progetto di C, piano principale

Revisore: Fable, sola lettura. Commit rivisto: `3855816` (base `d9639cc`), quattro documenti di `docs/superpowers/`. I file sono stati letti con `git show 3855816:<percorso>`; nessun test lanciato (nessun dubbio a cui la suite riportata non rispondesse), nessuna cartella temporanea creata in `/tmp`.

Riferimenti brevi: «spec» = `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`; «catalogo» = `docs/superpowers/specs/2026-10-08-tollgate-profili-verticali.md`; «progetto» = `docs/superpowers/specs/2026-11-20-tollgate-c-tracciamento-design.md`; «piano principale» = `docs/superpowers/plans/2026-11-20-tollgate-c-piano-principale.md`. I numeri di riga sono quelli dei file al commit.

## Aderenza

### Step 1, spec rev 37

- ✅ Intestazione (spec:4) e riga 37 della sezione 20 (spec:2346): riassumono la revisione; l'elenco delle sezioni toccate (1.2, 3, 4, 6.3, 7.1, 7.3, 8.7, 10, 11.2, 11.4, 14, 16, 20) coincide con gli hunk del diff.
- ✅ 4 (spec:314): due specialisti dalla rev 37, `ci` con C3.
- ✅ 6.3: agenti `-security` (spec:508), file che va a un'altra area (spec:509), sicurezza fin dal progetto (spec:510), giro 4 (diagramma e spec:717), tabella S1-S71 (spec:610-683), costi N4 e N9 (spec:684).
- ✅ 7.1 (spec:809) e 7.3 (spec:844): i due agenti di sola lettura nei due elenchi.
- ✅ 8.7 (spec:1145): `dod` vuoto, R-SECURITY-03, esempio `denied`.
- ✅ 10 (spec:1307-1311): secondo specialista, `checklist` alla lettera, frase sul rischio non coperto, frase «Per C3».
- ✅ 11.2 (spec:1346-1347, 1353) e 11.4 (spec:1437, 1442, 1540, 1548, 1550, 1552): deroga `keep_paths`, marcatori, `exclude`, frammento, `models`.
- ✅ 16 (spec:2142-2154): Next.js 16, pagina dei subagenti con la data, `validate --strict`, librerie, licenze, conteggi, prova. ❌ per la frase sui segnali della prova (rilievo I1).
- ✅ D4: sezione 3 (spec:214-226), 1.2 (spec:115, titolo in grassetto invariato), 14 (spec:1786), esempio di 11.4 (spec:1442, `"tollgate:implementer" = "fable"`); le righe storiche della 16 non sono toccate.
- ✅ D12: nessuna voce in grassetto nuova in 1.2, `docs/uso/limiti.md:133-135` resta vero («Un solo modello…»), la riga `**Tipi:**` non compare nel diff (controllo: 0 righe `±**Tipi` nel diff).

### Step 2, catalogo

- ✅ Riga `security` di 2 (catalogo:40): 6 pattern veri, `**/*session*` fuori, `proxy` dentro. 2.1 (catalogo:61), 2.2 (catalogo:78-81, 21 agenti), 2.3 (catalogo:96), 4 (catalogo:143, 156), 6 (catalogo:173).
- ✅ Marcatori tolti e nessuna fonte ASVS (catalogo:143).
- ❌ «Sotto `auth/` il lavoro è L2 già senza il profilo: la spec **e il catalogo** lo dicono» (decisione del controller): nel catalogo manca (rilievo I2).

### Step 3, progetto e piano principale

- ✅ Frasi su sonnet: piano principale sezione 6 (piano:118), decisione 4 (piano:130), progetto sezione 11 (progetto:184) e 14 (progetto:216), tutte con la scelta dell'utente del 22/11/2026 e la frase vecchia lasciata come storia.
- ✅ Stato in testa (piano:8), riga C2 (piano:28), riga «C2 → C3» con D1 (piano:49), sezione 8 con i rinvii della decisione 17 e quelli nati nell'esecuzione (piano:155-165), «Dopo C» con D11 (piano:147) e il costo degli avversari (piano:148).
- ✅ Nessun «unita su `main`» per C2 nei quattro file (controllo: ricerca di `unit[ao] (su|in parte)` e di «su `main`» filtrata su C2 e `security`: 0 righe).

### Step 4

- ✅ Suite riportata: 4516 test verdi sui due interpreti, `exit 0`, nessun «unclosed» (`suite-task-10.log`, non rilanciata). Un solo commit, quattro file, 170 righe aggiunte e 48 tolte; nessun file approvato, agente o codice toccato.

### Controlli mirati (affermazione → controllo → esito)

| Affermazione | Controllo | Esito |
|---|---|---|
| Tabella S1-S71 uguale alla decisione 5 | confronto cella per cella fra le 71 righe di spec:613-683 e quelle di `decisions.md` | identiche, 71 su 71 |
| Tabella S1-S71 uguale ai test | script che legge `SecurityPrecedenceTest` con `ast` e confronta file e proposta di ogni `check`; runtime e `check_active` letti a occhio riga per riga; S53 e S67 letti a mano | nessuna differenza; `(X attivo)` corrisponde a `check_active` |
| 17 regole, 13 `[blocca]` (01, 03-10, 12-14, 17), sul report 01, 02, 15, 16, 17 | `skills/rules-security/SKILL.md` | vero; sul diff 03-14, dodici |
| 6 pattern nell'ordine, `min_level`, `final_specialist`, `checklist` alla lettera, `exclude`, `keep_paths` | `templates/profiles/security.toml` | vero |
| 21 marcatori e i quattro tolti | conteggio delle righe di `content` (4+2+4+2+2+2+5) | vero |
| Condizione di `lighting` | `bin/tollgate_flow/init.py:390-392` | alla lettera: `f in mine or f not in taken or fragment.keep_paths`; `exclude` resta in `concrete_for` e in `skip`; `vertical_for` non è toccata |
| `isinstance` per `keep_paths` | `bin/tollgate_core/fragments.py:106-108` | vero |
| `tools`, `skills`, `model` dei tre agenti; 21 agenti, 7 su opus e 14 su Fable | frontmatter di `agents/*.md` | vero |
| `READONLY_TYPES` e `readonly_agents` | `hooks/run:61`, `bin/tollgate_core/config.py:76-82` | stesso elenco e stesso ordine di spec:809 e spec:1437 |
| `AREAS`, `FINAL_AREAS` | `tests/test_manifest.py:9,11` | vero |
| `MODEL_HINT = "opus"` e `[review] models` dal giro 4 | `bin/tollgate_flow/taskcmd.py:22,174-178` | vero |
| Eval su `claude-opus-5-5`, predefinita `b8`, `CAMPAIGNS`, `--campagna` | `evals/run.sh:47,64`, `evals/cost.py:44` | vero |
| Sezione «Area» dei tre agenti (regole sul report e sul diff, programmi vietati, rischio non coperto, `[blocca]`) | testo di `agents/implementer-security.md`, `reviewer-security.md`, `final-security.md` | la spec lo riporta fedelmente |
| Sicurezza fin dal progetto (dove sta, riga `Sicurezza:`, `minor` per la riga assente, «non è `extra`», piano che rimanda alla spec) | `agents/implementer.md:55-64`, `task-reviewer.md:48`, `final-reviewer.md:31`, `spec-adversary.md:24`, `plan-adversary.md:26` | vero |
| L2 già sotto `auth/` | `config.py:40` (`sensitive_paths`) e `docs/profili/security.md:86` | vero nella spec |
| File che va a un'altra area | `docs/profili/security.md:100` | spec:509 dice lo stesso della pagina approvata |
| 34 nomi di test citati nei testi nuovi | `git grep "def <nome>"` sui test al commit | esistono tutti, una definizione ciascuno |
| Numeri della prova (19,55; 6,98; 12,55; 0,02; 9,53; 15 giri; 22 subagenti; 1.014.248; 58.388 e 47.120; 2.1.330; 2 → 13 must-have) | `docs/verifiche/2026-11-22-c2-prova-flusso.md` al commit | coincidono |
| Fatti della pagina dei subagenti e di Next.js | riga dei «Fatti verificati» del piano di C2 (righe 28 e 32) | coincidono, salvo la parola «solo» (minore m2) |
| Dati privati nella riga dei conteggi (spec:2151) | confronto con il piano di C2, già pubblico (riga 34); ricerca di nome utente, host e percorsi di casa nei quattro file con `/usr/bin/grep -ac` (valori ricavati a runtime, mai stampati) | solo numeri aggregati già pubblici, con meno dettaglio del piano; 0 occorrenze nei quattro file e nelle righe aggiunte |
| Residui del vecchio (`sonnet`, `inherit`, `session`, «12 e 16», `FINAL_AREAS = ("database",)`, «cinque») | ricerca nei quattro file | ogni occorrenza è storia dichiarata o corretta; resta una frase al presente nella voce di `database` (minore m4) |

### Le 20 decisioni

La tabella del report regge: ogni decisione è dove dice, con il costo. I fatti sostituiscono le stime (17 regole, marcatori tolti, nessuna fonte ASVS, 19,55 USD equivalenti). La decisione 18 è solo nella riga 37: accettabile, non cambia nessuna regola del prodotto.

### Scostamenti e dubbi dell'implementatore

- Scostamento 1 (tabella vecchia dei modelli come frase storica): corretto, serve a chi legge.
- Scostamento 2 (frase su sonnet lasciata nel progetto con la correzione datata): corretto, è la regola 3 del piano principale.
- Scostamento 3 (voci 8 e 9 di «Dopo C»): corretto, D11 è rispettata.
- Scostamento 4 (righe in più nella 16): corretto; la riga dei conteggi non rivela nulla di nuovo.
- Dubbio 1 (C1 «unita su `main`» nel progetto): è un fatto già scritto nel piano principale. Va bene.
- Dubbio 2 (minore rinviato del Task 6): non era nell'elenco del controller, quindi non è un requisito mancante. Vedi minore m6.
- Dubbio 3 (indicazioni per C3 nella riga «C2 → C3»): sono conseguenze vere dei test (`test_final_reviewers_leave_report_rules_of_areas` scorre `AREAS`, `test_agent_models_by_role` fissa i modelli per ruolo). Va bene tenerle.

## Punti di forza

- La tabella S1-S71 è copiata senza una sola differenza dalla decisione 5 e dai test, con S67 al suo posto e il paragrafo d'apertura che dice quali regole decidono.
- Dove il piano stimava, la spec dice i fatti e nomina la stima superata (17 regole, 19,55 USD, marcatori tolti, nessuna ASVS).
- Il vecchio non è cancellato ma dichiarato storia, con data e motivo (tabella dei modelli, `inherit` al giro 4, frase su sonnet del progetto).
- La voce «`security` attivo con un file che va agli agenti di un'altra area» dice il limite come la pagina approvata, senza addolcirlo.
- Nessun dato privato: i conteggi sono aggregati e meno dettagliati di quelli già pubblici.

## Rilievi

### Critical

Nessuno.

### Important

**I1. La sezione 16 presenta come segnale delle regole un dato che non lo è.** `spec:2152`:

> «**Segnali delle regole:** … il modello delle minacce e il raggio d'azione (R-SECURITY-01 e 16) ci sono in tutti e due i report, senza che il piano o la sezione «Sicurezza fin dal progetto» li chiedano (segnale non del tutto pulito: la `checklist` sta anche nel `tollgate.toml` letto dagli implementatori)»

Li chiede per esteso il testo dell'agente, `agents/implementer-security.md` (sezione «Area `security`»): «Scrivi nel report, nel campo `done`, ciò che serve: chi può arrivare al codice cambiato … cosa può fare da lì e quale controllo lo ferma …, il raggio d'azione del cambio …». La stessa spec lo scrive a `spec:508` («nel campo `done` vanno chi può arrivare al codice cambiato … il raggio d'azione del cambio»), quindi le due sezioni si contraddicono. Il dato prova l'instradamento all'agente dell'area, non il precaricamento di `rules-security`. L'implementatore ha copiato il rapporto com'era a `d9639cc`; la revisione del rapporto (`progress.md:158`, rilievo I1 del Task 9) ha trovato lo stesso errore e il giro di correzione in corso lo sta togliendo. Perché conta: C3 farà una prova uguale per `ci` e leggerà qui quali segnali provano il precaricamento.

Come correggere, dopo il commit del giro del Task 9 e leggendo il rapporto corretto: nella riga della prova di `spec:2152` dire che il modello delle minacce e il raggio d'azione li chiede il testo di `implementer-security` e provano l'instradamento; che la prova del precaricamento è il titolo `isMeta` nelle cinque trascrizioni; che gli id citati da revisori e specialista con il contenuto giusto sono un indizio forte (la divisione tra diff e report è scritta anche negli agenti). Nello stesso giro conviene riportare il fatto nuovo del rapporto corretto sui giri: i giri 4-9 della spec e 4-6 del piano non avevano rilievi sopra `minor` (vedi m3).

**I2. Il catalogo non dice che sotto `auth/` il lavoro è L2 già senza il profilo.** Requisito del controller («la spec e il catalogo lo dicono come la pagina approvata»). La spec lo dice (`spec:508`, `spec:1548`); nel catalogo la ricerca di `sensitive_paths`, «già L2» e «L2 già» dà 0 righe: `catalogo:40` scrive solo «**L2**» e i costi delle forme a cartella, e `catalogo:96` non ne parla. Chi legge il catalogo attribuisce al profilo un costo che sotto `auth/` c'era già (è lo stesso errore che la revisione del Task 5 ha fatto correggere nella pagina, `progress.md:91`).

Come correggere: una frase nella riga `security` di `catalogo:40`, per esempio «sotto `auth/` il lavoro è L2 già senza il profilo (`levels.sensitive_paths`, spec 11.4): il livello è nuovo per `security/`, `rls/`, `middleware.*`, `proxy.ts`, `proxy.js` e i file trovati per contenuto».

### Minor

- **m1.** `spec:509`: «accettate dal verdetto (`blocking_rules` dei profili attivi)». L'accettazione viene da `rules` (`profiles.known_rules`, `bin/tollgate_analysis/profiles.py:99`); `blocking_rules` decide solo se un rilievo può bloccare (`verdicts.is_blocking`, `bin/tollgate_analysis/verdicts.py:91`). Così com'è, R-SECURITY-11, 15 e 16 sembrerebbero non accettate. Scrivere «(`rules` e `blocking_rules` dei profili attivi)».
- **m2.** `spec:226` e `spec:2147`: «con un avviso **solo** nelle sessioni interattive», e a `spec:226` «Se l'account non può usare il modello chiesto» per ogni caso. Il fatto verificato (piano di C2, riga 28) dice «con un avviso nelle sessioni interattive» e riguarda `availableModels`. È il minore già rinviato del Task 1 su `docs/uso/comandi.md:192` (`progress.md:31`), ripetuto qui in una sezione di fatti verificati: ridurre al fatto almeno nella 16.
- **m3.** `piano:148`: «(oggi nessun tetto sotto quello dell'audit)». La spec ha `spec_rounds = 4` e `plan_rounds = 2` (`spec:420`, `spec:1425-1426`), che contano i giri chiusi e non superati; la prova ne ha avuti 9 e 6. ⚠️ Non verificato sul codice: la frase va riscritta dicendo perché quei tetti non hanno fermato i giri, con il dato del rapporto corretto.
- **m4.** `spec:507` (voce di `database`, rev 34): resta al presente «`AREAS` … è `("ai", "infra", "backend", "frontend", "database")`» e «`FINAL_AREAS = ("database",)`», mentre la riga dopo dà i valori nuovi. La stessa voce è stata ritoccata per il modello («`fable` dalla rev 37»): basta «era, fino alla rev 36» o un rimando alla voce di `security`.
- **m5.** `catalogo:40`: la riga riscritta non riporta più la riga originale, che il rapporto approvato `docs/profili/verifiche/security-fonti.md:83-88` cita alla lettera come fonte di quattro pattern («riga 40 del catalogo», con `**/*session*`). Imposto dal piano (Step 2). La riga originale si ricostruisce da «esce `**/*session*`», ma una frase «la riga dell'8/10/2026 era: …» terrebbe verificabile la citazione.
- **m6.** `piano:165`: la voce pronta riceve solo «i minori che la revisione finale lascerà rinviati». In `progress.md` ci sono una ventina di minori differiti dei task (per esempio `:109` del Task 6, `:110` sulla frase della pagina che invecchia, `:127` su `op` in `registra`) che non hanno un posto nel piano principale. Allargare la voce a «e i minori differiti dei task che il triage tiene», così il controller li scrive una volta sola.
- **m7.** `piano:49`: la riga «C2 → C3» non dice più che il catalogo, riga `ci` (`catalogo:68`), mette `rules-security` tra le skill del revisore di `ci`; la riga vecchia nominava `reviewer_skills`. È una scelta che C3 deve prendere insieme a quella su `rules-ci` (da B3 le regole sono precaricate dagli agenti, non nel brief): nominarla tra ciò che decide C3.
- **m8.** `spec:2151`: «quasi tutti sessioni di chat in due copie di terzi (100 documenti, 449 test)» fonde tre dati distinti del piano di C2 (riga 34: quasi tutti in due copie di terzi; 100 documenti; 449 test). Separare con una virgola al posto della parentesi.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** Il lavoro è accurato e quasi tutto verificato alla lettera contro codice, agenti, skill, pagina approvata e test (tabella S1-S71 identica, numeri e nomi giusti, nessun dato privato, nessun «unita su `main`»). Restano due correzioni di poche frasi: la riga della prova nella sezione 16 attribuisce alle regole un segnale che viene dal testo dell'agente e contraddice la 6.3 (va allineata al rapporto corretto del Task 9), e il catalogo non dice che sotto `auth/` il lavoro è L2 già senza il profilo, come chiedeva il controller.
