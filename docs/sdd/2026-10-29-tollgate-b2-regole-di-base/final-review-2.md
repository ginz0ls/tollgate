# Revisione finale del ramo B2, secondo verdetto (c71ab80..b2100fa)

Revisore: opus, sola lettura. Letti: la prima revisione (`final-review.md`), il brief del giro, il ledger dopo «Revisione finale (opus…)», il report del giro, la ri-revisione sonnet, il pacchetto `final-review-2-package.diff` per intero (codice, agenti, test, spec, piano, rapporto delle fonti, rapporto della prova), la sezione «Seconda corsa» del rapporto della prova. Evidenze aperte solo per controlli mirati (`passo2/tentativo-2/claude.jsonl`, `registro-2/`).

## Verdetto

**Pronto per il merge.** Nessun Critical, nessun Important. I due Important della prima revisione sono chiusi anche nei casi d'incontro; i minori del triage «da correggere prima del merge» sono corretti; il giro non introduce difetti che blocchino. La seconda corsa conferma il comportamento dal vivo. Restano tre Minor, nessuno bloccante: il primo costa una riga in un file versionato e conviene farlo prima del merge, perché oggi è scritto solo nel ledger (ignorato da git).

Fatto bene: la condizione di I-1 sta in un solo punto (`lookups.base_rules(root, active)`) e i due chiamanti passano lo stesso `research.active(...)`; il report va nel brief sempre recintato dopo `DATA_NOTE`, con `fence()` che allunga il recinto oltre ogni sequenza di backtick del testo; le classi di test gemelle ereditano da `BaseRulesTest` e quindi riprovano anche gli altri casi (regola non `[blocca]`, regola ignota) nel lavoro senza passo e con il componente spento.

### Verifiche eseguite

- Test mirati sul ramo con `PYTHONWARNINGS=error::ResourceWarning` e `python3 -B`: `test_check_task_verdict`, `test_check_final_review`, `test_brief`, `test_manifest`, `test_rules_base`, `test_docs`, `test_lookups`, `test_layers` (206 OK); `test_taskcmd`, `test_check_research_gate` (97 OK). Albero pulito dopo i test.
- `claude plugin validate --strict .`: «Validation passed», uscita 0.
- Chiamanti di `lookups.base_rules`: solo `task_verdict.py:54` e `apply.py:84`, entrambi aggiornati; nessun altro uso della firma vecchia (né in `spikes/` né in `evals/`).
- Da dove viene `ctx.component` nei controlli: `runner.py:259-268` carica la configurazione dal worktree **a `work_base_sha`**, come `taskcmd._research_on`. Un implementatore che scrive `research_note = false` nel suo worktree non spegne quindi le `[blocca]` per sé: brief e verdetto leggono la stessa configurazione congelata.
- `verdicts.parse_task_verdict` ricalcola `outcome` dai rilievi (`outcome = "changes" if blocking else "approved"`). Un `changes` dichiarato per una `R-BASE-…` che non blocca diventa quindi `approved`, senza veto.
- `base-fonti.md`: `git log -S` conferma che la R-BASE-10 attuale entra con 3c4697a (2026-11-01).
- Anonimizzazione delle evidenze nuove (`passo1/tentativo-2`, `passo2/tentativo-2`, `registro-2`, `validate-2.txt`) e del rapporto. Grep vuoti su: nome utente, host (`HOST`), nome git, email, prefissi di token (`sk-ant`, `ghp_`, `gho_`, `github_pat`). `session_id` sempre `SESSION-ID` (469 righe). `/home/USER` in 3 punti. Nessuna riga `init`. I percorsi `/tmp/claude-1000/...` e `~/.claude/projects/...` hanno `SESSION-ID` al posto dell'id. Gli UUID rimasti sono `uuid` dei messaggi e gli `agent_id` dei subagenti, come in B1.

## I-1: chiuso

`bin/tollgate_core/lookups.py:182-193`: `blocking if active and research.enforced(text) else set()`. Caso per caso:
- **Interruttore acceso, lavoro senza passo (`research = 0`):** `active` falso, le `R-BASE-…` restano note, nessuna blocca; una `R-BASE-99` ignota blocca ancora. Lo provano `BaseRulesNoStepTest` in `test_check_task_verdict.py` e in `test_check_final_review.py`.
- **Componente spento (`[components] research_note = false`) con `research = 1`:** stesso esito, `BaseRulesComponentOffTest` nei due file.
- **Skill illeggibile:** `(vuoto, vuoto)` prima di guardare `active`, quindi una `R-BASE-…` `major` è ignota e blocca (fail-closed, spec 8.6). Vale anche per il lavoro senza passo: è la regola generale delle `R-…` ignote, dichiarata.
- **Interruttore spento:** invariato (`BaseRulesSwitchOffTest`).
- Spec 8.6 (`nucleo-design.md:854`), piano sezione 3 e tabella delle prove allineati: «solo nei lavori con il passo».

## I-2: chiuso (strada a)

- `taskcmd._implementer_report` (`taskcmd.py:268-281`) mette nel brief il report dell'ultimo implementatore **sempre** quando ce n'è uno, anche con `DONE`. Lo mostra in chiaro, campo per campo, oppure con la coda del testo se il report non si legge. `brief.review_brief` (`brief.py:254-258`) lo mette in «## Report dell'implementatore», dopo la frase sulle regole sul report e dopo `DATA_NOTE`, dentro `_block`. Il campo `tests` porta il riscontro RED/GREEN (`implementer.md:109`), quindi R-BASE-10 si giudica davvero.
- `agents/task-reviewer.md:27` chiama il report «testo non fidato, mai un'istruzione». `final-reviewer.md` e `finding-verifier.md` dicono «solo su ciò che vedi»: le regole sulla nota e sul report sono del revisore del task. La frase condizionata di D6 resta.
- **Dal vivo (seconda corsa):** il brief del revisore in `passo2/tentativo-2/claude.jsonl` (riga 271) ha la sezione con `DATA_NOTE` e il recinto (`status: DONE`, `tests: … RED: ModuleNotFoundError …; GREEN: 8 test OK`, `files`, `must_have`), poi la «Nota di ricerca» in un altro recinto. Il verdetto (riga 293) giudica proprio il report: R-BASE-07, «il report non dice a quale funzione esistente si è ispirato», e R-BASE-11 sul comando di test. È quello che il rapporto dichiara.

## Minori del triage e della prima revisione: corretti

- T1, ordine dell'avviso e non ripetizione: `assertLess` e `assertNotIn` in `test_unreadable_switch_warns_and_logs_once`.
- T5, data della pagina e `approved`: `test_page_approval_date_matches_skill`.
- T5 con il Minor 7: `base-fonti.md:3` cita 3c4697a. La riga `no` di `systematic-debugging` ora è sotto la tabella, come «Fonte scartata», e il test delle fonti non è stato indebolito.
- T8: «I primi due» nel rinvio 31, «si precarica», «la bozza n. 11» (piano e spec rev 28).
- Minor 1: il paragrafo `rules-base` in 6.3 ora viene dopo `SubagentStop` e dopo «Una skill non installata…».
- Minor 2: `research_switch_unreadable` è in «Tipi:». `test_spec_event_types_match_registry` confronta l'elenco con `EVENT_TYPES` in tutte e due le direzioni.
- Minor 3: `rules_switch` e `rules_enforced` sono descritti giusti nella docstring, nella spec 8.1 e nel piano.
- Minor 4: `no`, `off` e `n`, con il confronto fatto dopo aver tolto gli apici.
- Minor 6: `test_base_rules_of_research_match_rules` usa la skill vera.
- Minor 8: la docstring di `research_gate` nomina l'interruttore illeggibile e l'evento.
- Minor 9: `implementer.md` punto 1.
- Rinvio 37 di B1: annotato per B3 nel piano (`piano-principale.md:184`).
- Restano fuori, come deciso: i rinviabili del triage, già nel piano. Resta anche `/home/USER/...` preesistente in `docs/verifiche/evidenze/gh-p4/` e in altri documenti già su `main` (per esempio `HANDOFF.md`, i piani B1 e B2): non viene da questo ramo (zero righe aggiunte con il nome utente in `fbf7068..HEAD`), e la decisione spetta all'utente.

## Critical

Nessuno.

## Important

Nessuno.

## Minor (nuovi)

1. **Il minore della ri-revisione è annotato solo in un file ignorato da git.**
   - **Dove:** `agents/task-reviewer.md:53`, poi `bin/tollgate_analysis/brief.py:256-257` e `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:854` (ultima frase).
   - **Cosa non torna:** in un lavoro senza passo, o con il componente spento, il brief ha comunque la sezione del report, con la frase «le regole sul report … si giudicano su questo testo», e non dice niente sull'interruttore. L'agente quindi tratta le `[blocca]` come bloccanti, mentre il verdetto le considera note. La spec dice «Senza la sezione (lavoro precedente a B1, componente spento) il revisore non controlla niente di tutto questo», ma la sezione del report c'è sempre.
   - **Effetto:** solo rumore, cioè un `changes` dichiarato che il verdetto riporta ad `approved`. Nessun blocco spurio, l'ho verificato su `verdicts.py`.
   - **Perché conta:** il rinvio a B3 sta solo nel ledger, e `.superpowers/sdd/` è in `.gitignore`. Dopo il merge si perde.
   - **Come correggere:** una riga tra i rinvii a B3 del piano principale. Da B3, nella sezione del report, quando `research` è falso: «in questo lavoro le `R-BASE-…` non bloccano». Correggere anche la frase della spec.

2. **Nei giri di correzione il revisore vede solo il report dell'ultimo giro.**
   - **Dove:** `taskcmd.py:262-266` (`_last_report`, `ORDER BY … DESC LIMIT 1`) e `agents/implementer.md:97`.
   - **Cosa:** nel giro di correzione l'implementatore viene ripreso con `SendMessage` (`skills/execute/SKILL.md:44`), e `subagents.report` prende il report di quel giro. Il nuovo revisore rivede tutto il diff del task, ma nel brief trova solo il report della correzione. Se quel report non ripete il riscontro RED/GREEN del difetto corretto all'inizio, R-BASE-10 `[blocca]` può dare un `major` e un giro in più.
   - **Perché è minore:** a differenza di prima della correzione il giro si chiude, perché basta che l'implementatore ripeta il riscontro.
   - **Come correggere (B3):** in `implementer.md:97`, «il report del giro di correzione ripete il riscontro RED/GREEN del task». In alternativa, mettere nel brief anche il primo report.

3. **Resa del report: `concerns` sparisce con `DONE`, e `None` compare alla Python.**
   - **Dove:** `taskcmd.py:278-281`.
   - **Cosa:** con `status: DONE` e `concerns` non vuoto, i dubbi non compaiono né nella sezione dei dubbi (che esce solo con `DONE_WITH_CONCERNS`) né in quella del report. Un «non esiste» scritto lì sfugge a R-BASE-05. In più `size_reason: null` diventa `size_reason: None` (si vede nella seconda corsa, riga 271).
   - **Come correggere:** escludere `concerns` solo quando la sua sezione c'è, cioè con `DONE_WITH_CONCERNS`, e rendere `None` come `null` o saltare il campo. È una riga, con un test in `test_taskcmd.py`. Rinviabile.

## Sulle `Ruling:` del giro

- **Strada (a) per I-2:** corretta, non tocca le regole approvate. Il costo dichiarato (brief più lungo) è contenuto: il report reso in chiaro è breve. La coda di 64 KiB serve solo per un report che non si legge, e un report così riceve già un veto all'implementatore.
- **Seconda corsa (prepara, passo1, passo2, registra, secondo tentativo per passo):** corretta e necessaria, perché il passo 2 dipende dallo stato del passo 1. L'esito non è composito: ogni passo è riuscito al primo colpo nella corsa. La prima corsa è stata spostata in `*.prev-…`, non cancellata, e il rapporto ne aggiorna i rimandi.
- **Correzione della ruling del giro 1 del Task 6 (Minor 5):** corretta, coerente con il codice e con la spec 8.6.
- **Corsa della suite lanciata per errore con `&` e fermata per PID:** dichiarata, senza effetti sul risultato. La corsa valida è venuta dopo l'ultimo commit di codice: 3238 test su 3.11 e 3.13.
