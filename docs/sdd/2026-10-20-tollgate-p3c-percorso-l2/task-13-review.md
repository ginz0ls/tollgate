# Task 13: revisione (a9306a2..f6b5fc4)

Rischi controllati accanto al codice: `bin/tollgate_flow/audit.py` (STEPS, codici, `_write_brief`, `decline`), `bin/tollgate_core/cli.py:324-336` (uscite di `audit`), `l2acts.py` e `actapply.py` (approve spec/plan, reopen, resolve), `start.py`, `finishcheck.py`, `sync.py`, `checkpoint.py`, `bin/tollgate_analysis/auditrules.py` e `brief.py`, e il metodo originale `~/.claude/skills/prd-audit/SKILL.md` (sola lettura). Eseguiti solo `python3 -B -m unittest tests.test_skill_contract tests.test_manifest` (33 test, OK).

## Aderenza

- ✅ Tre agenti con strumenti e modelli della decisione 21 (`agents/spec-adversary.md:4-5`, `spec-auditor.md:4-5`, `plan-adversary.md:4-5`), senza Edit/Write/Bash; una sola riga JSON con i campi della decisione 5 (`plan_sha` solo nell'avversario del piano); attribuzione a prd-audit in `spec-auditor.md:7`.
- ✅ `skills/spec-audit/SKILL.md`: ciclo prepare, agente in primo piano, report letto come dato, commit di documento e `reviews/<N>/` (mai Edit/Write), un giro alla volta, `--confirm` solo col sì, `audit decline` al no, tetti con `/tollgate:resolve`. Codici 0/1/3 come `audit.OK/REFUSED/NEEDS_CONFIRM` (`audit.py:28`, `cli.py:327-336`). `decline` esce 0/1 e stampa `STEPS["resolve"]` con l'id del blocco: coerente con il testo della skill.
- ✅ D19: la parte fissa di ogni `audit.STEPS` e di `CONFIRM_STEP` compare nella skill (verificato a mano, `SKILL.md:336-344`), `STEPS["resolve"]` con `<id>` (`SKILL.md:343`).
- ✅ Carry Task 5: `_write_brief` (`audit.py:431-433`) calcola `Path(db.BIN_PATH).parent.parent/skills/spec-audit/references/dimensioni.md`, con `BIN_PATH = bin/tollgate` (`db.py:17`): coincide con il file creato. Verificato a mano; nessun test lo blocca (vedi Minor).
- ✅ D10: `argument-hint` di `start` con `--spec` (`skills/start/SKILL.md:5`, `tests/test_manifest.py` riga dell'assert).
- ✅ `approve` (spec/plan → `act apply`, `APPLIERS` in `actapply.py:240-249`; testi di `l2acts.approve_spec/approve_plan` coerenti: file di approvazione da committare, proposta issue in recinto, `/tollgate:execute`), `reopen` (messaggi di `l2acts.reopen` coerenti: fase, giro superato, registrazione del piano tolta, rifiuti con task/implementatore/blocco), `resolve` (i quattro motivi e le etichette «sospeso» coincidono con `audits.CAP_REASONS`, `DECLINE_REASON`, `SUSPENDED_LABELS`), `status` (etichette di `checkpoint.CAPS`), `finish` (la voce `approvals` legge HEAD: un file non committato dà `[no]`, come dice la skill), `sync` (codici 0/1/2/3), `start` (codici 0/1/3/4, `--spec`, uscita 3 per spec cambiata, riga 78 tolta).
- ✅ Nessun «P3c» nelle skill; programma sempre `python3 "${CLAUDE_PLUGIN_ROOT}/bin/tollgate"` con il ripiego; `implementer.md:50` con virgolette doppie (riga 79).
- ❌ Metodo di prd-audit incorporato solo in parte (Important 1).
- ❌ `start`, fase L2 `spec_audit`: non rientrante e in contrasto con `--spec` (Important 2).

## Punti di forza

- Le skill sono state scritte dopo i sottocomandi e i testi dei passi sono letti dalle costanti: nessuna divergenza trovata tra messaggi di `audit`/`l2acts`/`actapply` e quello che le skill dicono di fare per ciascun esito.
- Il contratto skill/codice è un test vero (`tests/test_skill_contract.py:41-72`): insieme dei codici uguale alle costanti, parte fissa di STEPS, sottocomandi anche annidati contro `build_parser()`, nessun «P3c».
- Gli agenti sono sobri: sola lettura esplicita, testo di spec/report trattato come dato, JSON copiato dal brief con la conseguenza dichiarata (giro aperto se non valido), `test_audit_json_fields_in_agent_text` fa il parse del blocco JSON e confronta le chiavi.
- Regola dei tre sospetti scartati per il ciclo vuoto (`spec-auditor.md:25`), una lente alla volta (`:35`), tana senza scelta come `major` (`spec-adversary.md:25`).
- `dimensioni.md` è identico all'originale tranne la riga di attribuzione in testa (diff controllato).

## Rilievi

### Critical
Nessuno.

### Important

1. **Il metodo di prd-audit non arriva intero all'auditor, e la copia ha un rimando morto** (`skills/spec-audit/references/dimensioni.md:83`; `agents/spec-auditor.md`). L'implementatore dichiara di non aver letto `prd-audit/SKILL.md`, e si vede.
   - La lente L8 dice «Vedi `verifica-fatti.md`»: il file non è nel repo (esiste solo in `~/.claude/skills/prd-audit/references/`). Un subagente nuovo, che ha solo brief, agente e `dimensioni.md`, non può aprirlo, e L8 («nessuna affermazione fattuale passa senza verifica») resta senza procedura. Imposto dal piano (il brief dice di copiare solo `dimensioni.md`), ma resta un difetto.
   - L10 (`dimensioni.md:116-129`) parla di rilievi `[RAGIONATO]`/`[VERIFICATO]` e di «inventario», concetti definiti solo in `SKILL.md` di prd-audit («Stati dell'evidenza», «Inventario su disco»). Né `spec-auditor.md` né la skill li definiscono: la lente L10 non è eseguibile come scritta.
   - Mancano nell'agente due regole del metodo originale: dichiarare in cima il punto di vista (SKILL.md prd-audit: «un ciclo senza punto di vista dichiarato è una rilettura travestita») e «cerca la regola, non il caso» (dove altro vale lo stesso difetto).
   - Disallineamento con il codice sul ciclo vuoto: `auditrules.outcome` (`auditrules.py:29-31`) tratta come vuoto un ciclo con `blocker + major + moderate == 0`, cioè ammette i `minor`; l'agente dice solo «un ciclo senza rilievi è valido» e chiede i tre scartati «se vuoto» (`spec-auditor.md:25`), né il brief (`brief.py:~312`, `audit_brief`) spiega la soglia. Un ciclo con soli `minor` conta come vuoto per il contatore ma l'auditor non sa di dover mostrare il lavoro, e nell'altro verso non sa che un `moderate` azzera il contatore.
   - Correzione: copiare anche `verifica-fatti.md` in `skills/spec-audit/references/` con la stessa riga di attribuzione e farlo nominare dal brief/agente (oppure riscrivere la riga L8 della copia con la procedura essenziale); aggiungere in `spec-auditor.md` una sezione breve con gli stati dell'evidenza, la dichiarazione del punto di vista in cima al report, la soglia «vuoto = nessun blocker/major/moderate» e l'obbligo dei tre scartati anche con soli `minor`; chiarire che «inventario» in L10 per la spec coincide con le sezioni del documento. Aggiornare `test_dimensioni_copied_with_attribution` perché verifichi che ogni file di riferimento nominato in `dimensioni.md` esista nel repo.

2. **`start`, L2 fase `spec_audit`: dice sempre «invoca brainstorming … scrivila»** (`skills/start/SKILL.md:42`). La skill dichiara di essere rientrante e di ripartire dalla fase, ma in `spec_audit` con la spec già scritta e committata (ripresa dopo `/clear` o interruzione) rifà il brainstorming. Peggio nel caso che il brief nomina: con `--spec` e spec cambiata dopo l'approvazione, `--confirm` crea il lavoro in `spec_audit` con `spec_path` già registrato e la spec presente sul ramo (`start.py:462-467`, `:489-490`), e la stessa riga 3 della skill (`SKILL.md:22`) dice di partire da un nuovo giro; il punto 3 invece manda a ripartire dal brainstorming. Contraddizione interna alla skill, su un percorso esplicito del brief.
   - Correzione: in `spec_audit`, «se la spec esiste già sul ramo (ripresa, oppure lavoro avviato con `--spec` e spec cambiata) committala se serve e vai a `/tollgate:spec-audit`; altrimenti brainstorming → spec». Aggiungere un test di sottostringa sul contratto o su `test_manifest` per quella frase.

### Minor

- `skills/start/SKILL.md:43` (fase `plan`, bullet successivo): «dopo `/tollgate:approve spec`» non vale per un lavoro nato con `--spec` (nasce in `plan`, `start.py:462`), e `writing-plans` «sulla spec approvata» non dice che per una fetta successiva il piano copre solo la fetta di quell'issue.
- `tests/test_skill_contract.py:53`: l'asserzione D19 `assertIn("<id>", skill_text("spec-audit"))` è vacua (`<id>` compare già in altre righe della skill); meglio cercare `"/tollgate:resolve `<id>`"` o la frase fissa seguita da `<id>`. Il test sui sottocomandi (`:58-69`) non controlla le opzioni (`--confirm`, `--spec`, `--level`, `--checkpoint`) contro il parser, che la lezione di P3b nomina insieme ai sottocomandi. Il test dei codici confronta solo i numeri, non il significato abbinato (una skill con «1, rosso» e «2, rifiuto» scambiati passerebbe).
- Nessun test garantisce che il percorso di `dimensioni.md` scritto nel brief esista (`tests/test_audit_prepare.py:185` controlla solo la sottostringa): l'ho verificato a mano, ma una futura mossa del file passerebbe in verde.
- `skills/spec-audit/SKILL.md:329`: il codice 1 copre anche i messaggi su stderr `tollgate: …` (nessun lavoro attivo, base mancante: `cli.py:332-334`), che non sono righe `rifiuto:`; la skill di `finish` li nomina per `review prepare`, qui no. La skill dice inoltre «Vale nelle fasi `spec_audit` e `plan`» (`:8`), ma `audit prepare` risponde anche in `approval` (stampa `approve plan`).
- `skills/finish/SKILL.md:27` (1, rosso): «Non correggere da solo» seguito da «si committa con `git add` e `git commit`» è ambiguo su chi committa il file di approvazione.
- `skills/reopen/SKILL.md:20`: «serve un nuovo giro avversariale» vale solo se la spec cambia (con la spec identica `adversarial_ok` resta vero e `audit prepare` passa subito ad `approve spec`).
- `agents/spec-adversary.md`, `spec-auditor.md`: dicono che spec e report sono dati, ma non che anche il contenuto scaricato con WebFetch è non fidato.
- Il brief chiedeva due test separati (`test_reopen_user_only`, `test_spec_audit_model_invocable`): ne esiste uno solo (`test_manifest.py:321`). Differenza di forma, copertura equivalente.

## Valutazione

**Qualità del task:** Da correggere

**Motivo:** codici d'uscita, testi dei passi, sottocomandi e fasi citati dalle skill coincidono con il codice e il contratto è protetto da test veri. Restano due difetti: il metodo di prd-audit arriva monco ai subagenti (rimando morto a `verifica-fatti.md`, L10 senza le definizioni che usa, soglia del ciclo vuoto non allineata al codice) e la skill `start` manda a rifare il brainstorming nei casi di ripresa e di `--spec` con spec cambiata.
