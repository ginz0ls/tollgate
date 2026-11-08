# Task 10: revisione (c72bcd0, base 66e6dbf)

Revisore sola lettura. Documenti: spec rev 31, catalogo, piano principale, riga del progetto. Controlli fatti sul codice del ramo (`bin/tollgate_core/fragments.py`, `bin/tollgate_flow/init.py`, `bin/tollgate_analysis/bash.py`, `templates/profiles/infra.toml`, `agents/*-infra.md`, `hooks/run`, `config.py`, `skills/rules-infra/SKILL.md`) e sul rapporto `docs/verifiche/2026-11-06-b4-prova-flusso.md`.

## Aderenza

- ✅ Spec 6.3 (task misti per ogni coppia di aree, derivazione `<area>`, paragrafo sugli agenti `-infra`, `AREAS`/`test_area_agents_name_area_rules`): coincide con `tests/test_manifest.py:9,154` e con le sezioni «Area `infra`» degli agenti (R-INFRA 01/02/03/08/12 sul report, le altre sul diff: `agents/reviewer-infra.md:54`, `agents/implementer-infra.md:51`).
- ✅ 7.1 e 7.3: `tollgate:reviewer-infra` in `hooks/run:56` e `bin/tollgate_core/config.py:77`; `tools: Read, Grep, Glob, Bash, WebFetch` (`agents/reviewer-infra.md:4`).
- ✅ 8.5: le 14 voci di Wrangler (conteggio verificato su `bash.py:984-1002`, elenco identico), più `pages publish`, `docker image push`, `docker compose push`; `LAUNCHERS`, `PACKAGE_COMMANDS` senza `docs/config/help/repo/home/patch` (`bash.py:1005-1010`), `PACKAGE_PROGRAMS`, normalizzazione (`bash.py:1014-1024`), scarto dei candidati (`bash.py:1027-1043`), testo di `-c`/`--call`/`--call=` con ripiego su `text_effect` (`bash.py:1155-1164`), `is_claude` a parte. I buchi e i falsi positivi elencati sono quelli delle decisioni 17 e dei ruling D3/D13.
- ✅ 8.7: riferimenti corretti (`runner.run_one`, `verify.dod_commands` ri-esportato da `runner.dod_commands`, `finishcheck.py:118`, `bash.uses_tollgate_bin`); `dod` lanciato senza veto.
- ✅ 11.2: tre forme, `concrete_for` (`init.py:235`), ordine cartelle poi `name`, `fnmatch.fnmatchcase` sul solo nome (`init.py:226-228`), `DOC_EXTENSIONS` case-insensitive (`init.py:208`), `EXCLUDED_PREFIXES` con le due cartelle di GitHub (`init.py:37`), `load_approved` unico punto (`init.py:364,692`), sovrapposizioni con i profili proposti prima (`init.py:395-407`), conteggio che include i documenti (`init.py:403`), differenza per `ai` e per `prompts/` con la data 07/11/2026.
- ✅ 11.4: tre forme e regex (`fragments.py:17-21`), `Pattern(kind, name)`, `rules()` che solleva `FragmentError` (`fragments.py:127-135`), frammento di `infra` con 14 pattern nell'ordine di `templates/profiles/infra.toml`, senza `[detect]`, `commands = {}`, `dod = []`, perché; 12 regole e 7 `[blocca]` (01-06, 12) verificate sulla skill.
- ✅ 16: fatti del 6 novembre e correzione di `compatibility_date` («required» nella tabella delle chiavi); l'esito della prova coincide con il rapporto (un tentativo per passo, 0,46 + 0,57, 55.260 e 38.021 token, 5 `read` e 1 `fetch`, `paths = ["/Dockerfile", "/vercel.json"]`, `ai` non proposto, `isMeta` prima del primo turno, `comandi-rischiosi.txt` vuoto, modalità `detect`). La spec NON afferma che il piano fosse quello dello script né che le tre righe del report provino il precaricamento: dice solo «il piano è stato scritto dal modello già nel passo 1» (vedi Minor 2).
- ✅ Riga 31 della sezione 20: decisioni 1-18 e ruling elencati correttamente (D1, D2, D3, D4, D10, D11, D12, D13, D14, divisione R-INFRA-07/08, R-INFRA-12).
- ✅ Catalogo 2, 2.1, 2.2, 2.3, 4, 6: frase «fino a B4…» sostituita, nota sulle graffe (come `infra` le ha sciolte), riga `infra` con i 14 pattern, `rules-infra` precaricata con `wrangler` e `cloudflare` in «Dove informarsi» (`skills/rules-infra/SKILL.md:67`) e `workers-best-practices` a `backend`, `dod` vuoto, fonti vere.
- ✅ Piano principale: stato, riga B4, sezione 9 (chiusi: forma dei pattern, documenti nelle cartelle, piccole cose di B3, radice vera, id a mano; aperti con il motivo, scritture remote di `kv/d1/r2` a B5, nota sulla pagina approvata di `ai`, righe «minor (deferred)» per B5-B8), sezione 13 «Prove di B4» con tutte e 25 le righe della tabella «Copertura» (confrontate una a una) più le prove oltre la tabella. Tutti i nomi `test_…` citati esistono in `tests/` (controllo con script su 109 nomi).
- ✅ Progetto di B: solo la riga di avanzamento; le scelte «utente» non sono toccate.
- ✅ Nessun nome utente, host, `/home/`, `MEGA`, token nel diff (grep sulle righe aggiunte: zero).
- ⚠️ Suite: il report dichiara `tests/run` e la variante con `ResourceWarning` verdi (3667, skipped 7 e 5) ma per il Task 10 non c'è un `task-10-suite.log` come per i Task 4-8. Il commit è solo documentale e il conteggio è uguale a quello del Task 8, quindi plausibile; resta una lacuna di evidenza.
- ❌ Step 3 chiede, nella riga B4 → B5-B7 della sezione 3, anche `rules(text, area)` (l'helper dei test): non compare (Important 2).

## Punti di forza

- Le descrizioni seguono il codice, non il piano: 14 pattern (non 13), R-INFRA-12 per «non pubblicare», `PACKAGE_COMMANDS` ridotto, `pages publish`, `docker image push`/`compose push`, sovrapposizioni tra profili della stessa corsa. Ho cercato contraddizioni con il codice su una ventina di affermazioni e non ne ho trovate.
- Costi e buchi scritti dove servono (8.5, sezione 9), con gli esempi esatti che passano senza veto.
- Il rinvio della differenza per `ai` è scritto in tre posti coerenti (spec 11.2, piano sezione 9, righe della copertura) e dice che la pagina approvata non cambia.
- La sezione 13 ha anche le prove «oltre la tabella» e dice onestamente cosa non è provato (rilievo dal vivo, ramo «prova eseguita» di R-INFRA-12).

## Rilievi

### Critical
Nessuno.

### Important

1. **Tabella rotta nel piano principale, righe B3 → B4-B7 e B4 → B5-B7 della sezione 3** (`docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md:52` e `:53`). Le firme `parse_pattern(p) -> Pattern | None` e `concrete_for(...) -> str | None` hanno un `|` non escapato dentro una cella: in Markdown (anche dentro i backtick) il `|` apre una cella nuova. Conto delle colonne con uno script: la riga 52 ha 5 separatori contro 4 attesi, la riga 53 ne ha 6. Nel rendering la colonna «Contratto» si tronca a «`Pattern `» e il resto (compresi `concrete_for`, `DOC_EXTENSIONS`, `launcher_candidates`, `AREAS`) finisce in colonne extra scartate o fuori posto. Il testo della riga B3 già esistente usava `\|` (riga 51, `str \| None`). Correzione: scrivere `Pattern \| None` e `str \| None` nelle due righe (tre occorrenze), oppure togliere il tipo di ritorno.
2. **Manca `rules(text, area)` nella riga B4 → B5-B7** (stesso file, riga 53). Lo Step 3 del brief elenca `parse_pattern`, `concrete_for`, `DOC_EXTENSIONS`, `EXCLUDED_PREFIXES`, `load_approved`, `launcher_candidates`, `AREAS`, `rules(text, area)`. Gli altri sette ci sono; l'helper `tests/test_rules_ai.py:62` (`rules(text, area="ai")`, importato da `tests/test_rules_infra.py:8` e usato come `rules(skill_text(), AREA)`) non è nominato da nessuna parte nel piano. Chi scrive B5 deve sapere che si importa e si passa l'area. Correzione: una frase nella riga B4 → B5-B7 o nel punto «Test da copiare» della sezione 9.

### Minor

1. **Testo di B3 ricopiato per intero nei punti «chiusi» della sezione 9** (piano principale, righe 111, 112, 117 del diff, cioè i punti su radice vera, `agents/`+`prompts/`, piccole cose di B3): ogni punto ripete il paragrafo originale dopo «Testo di B3:» (con maiuscola dopo i due punti, «Con il secondo frammento…»). Allunga la sezione senza valore, perché lo stato nuovo è già in testa a ogni voce. Si può togliere o ridurre a una riga.
2. **Sezione 13, riga «Progetto 1: è su Vercel, leggi le cose prima» (e il rapporto in sezione 16)**: la prova citata («prova reale: il report nomina `vercel.json`, `Dockerfile` e il workflow, e dice che dove gira oggi il progetto non è dimostrato dai file») è la stessa che il rapporto corretto non considera una prova del precaricamento, perché il task scritto dal modello nel passo 1 chiedeva già quelle righe. La spec non afferma il contrario (dice solo che il piano era del modello), ma non spiega perché la cosa conta. Aggiungere «(il testo del task chiedeva già queste righe: prova che il task è stato eseguito, non del precaricamento; il precaricamento lo prova `isMeta` e il revisore che cita da sé R-INFRA-04 e 05)» a quella riga e alla riga di prova reale della sezione 16.
3. **Spec 6.3, paragrafo «Derivazione degli agenti per area»**: reso generico con `<area>` ma conserva «non si aprono rilievi `R-AI-…`». Dovrebbe dire `R-<AREA>-…`.
4. **Piano principale, riga B3 → B4-B7, riga 52**: dopo l'aggiornamento resta «(oggi `ai.toml`)»; la spec 11.4 dice «oggi `ai.toml` e `infra.toml`». Allineare.
5. **Spec 16, sette punti di «Da decidere tu»**: la spec cita l'approvazione e la differenza per `ai`, ma le altre decisioni dell'utente (eccezioni `.example`/`.sample`/`.template` di R-INFRA-06, R-INFRA-05 senza compose, R-INFRA-01 «dove gira oggi», estensione di R-INFRA-02 a Docker, «li imposta l'utente») stanno solo nel piano (sezione 13) e nella pagina. Non è un errore (le regole vivono nella skill), ma chi legge la spec non le trova. Una riga nella 16 o nella riga 31 basterebbe.
6. **Evidenza della suite del Task 10**: manca il log della corsa (vedi ⚠️). Aggiungere `task-10-suite.log` o citare l'uscita nel report.

## Valutazione

**Qualità del task:** Da correggere.

**Motivo:** i contenuti sono fedeli al codice e completi (nessun Critical, tutte le sezioni richieste e tutte le righe di «Copertura» presenti, nessun dato privato), ma due righe della sezione 3 del piano principale rendono male in Markdown (`|` non escapati) e una di esse omette `rules(text, area)` che il brief richiedeva. Sono correzioni di pochi caratteri; le Minor si possono accorpare nello stesso giro.
