# Revisione Task 12: `adopt` (224a508..d04bf07)

## Aderenza

- ✅ Atto `adopt` con `work=None` e `target=str(N)`, della stessa sessione, consumato solo dopo `create_work` (adopt.py:326, 371-375). Rifiuto senza atto e con atto di un'altra issue testati.
- ✅ Nessun lavoro attivo per (repo, N) (adopt.py:330); più rami candidati: rifiuto con l'elenco (adopt.py:337-339); PR unita: rifiuto prima di ogni effetto (adopt.py:271-273); PR chiusa: avviso C25 senza `pr_number` né tetto (adopt.py:196-199).
- ✅ Configurazione letta dal riferimento `origin/<predefinito>` (adopt.py:147), mai dal working tree. Testo dell'issue solo in `.tollgate-run/<N>/issue.md`, nessun argomento di git/gh con testo non fidato (`pr_body` prende solo il numero intero).
- ✅ Strati: `adopt.py` importa solo core, analysis e moduli di flusso.
- ✅ Tetto dal blocco JSON, con `cap_paths` ricalcolati come `actapply._approve_level` (adopt.py:414-421); `create_work` senza `from_approved_spec`. Deroghe: nessuna approvata, restano `pending` (test).
- ✅ Ultima riga `prossimo passo: EnterWorktree <percorso>` (adopt.py:410), testata.
- ✅ Task del piano registrati `pending` con `advance=False`.
- ❌ Fase da «prove nel ramo» (spec 12.4): i file di approvazione contano come prova senza verificare che siano ancora validi (vedi Important 1).

### Review Focus 5 (ramo già in un worktree o solo remoto)
- ✅ Nessun `--force`: `adopt.py` non passa mai `force` a `worktree_add` (adopt.py:313); un worktree registrato ma sparito è rifiutato con l'indicazione `git worktree prune` (adopt.py:296-298, test dedicato).
- ✅ Worktree esistente riusato senza chiamare `worktree add` (adopt.py:292-300); il test confronta l'elenco dei worktree prima e dopo, l'assenza di `.claude/worktrees` e un solo ramo `tg/*`. Ramo nel checkout principale: rifiuto.
- ✅ Solo remoto: ramo locale creato con `update-ref` atomico dal vecchio valore vuoto (`gitw.create_branch`), senza upstream (testato), con rimozione condizionata allo SHA se `worktree add` fallisce (adopt.py:316). Nessun ramo duplicato: i candidati sono un insieme locale ∪ remoto (adopt.py:169-171).
- ✅ Un `create_work` fallito lascia ramo e worktree, e una nuova esecuzione li riusa. Il messaggio lo dice.
- ⚠️ Non testato: ramo locale in ritardo sul remoto (si usa la punta locale); worktree riusato sporco o con rebase in corso.

## Punti di forza
- Tutti i rifiuti avvengono prima di creare ramo o worktree (`_gather` precede `_worktree`), quindi un rifiuto non lascia residui; i test dei rifiuti asseriscono atto ancora `pending` e zero righe.
- Fail-closed sulla lettura della PR (senza saperlo si adotterebbe una PR unita), con test.
- Il blocco JSON è validato (livello noto, `issue` coincidente) e la motivazione è troncata.
- Gli scostamenti dichiarati (`gh.pr_body`, fase `plan` per L2 senza piano) sono necessari e ragionevoli.
- Test sul comportamento reale con repo e remoto locali; evidenza `tests/run` su 3.11 e 3.13 riportata.

## Rilievi

### Important

1. **Le approvazioni sono prova anche se superate o riferite ad altro** (adopt.py:220-222, 278-280, 362, 429-430). `_approval` controlla solo `kind` e la presenza di `path`/`sha`. Non confronta `header["sha"]` con il blob di `spec_path`/`plan_path` in `sha`, né verifica che `plan-approval.path` sia il piano scelto da `_find_plan` o che la spec esista. `finishcheck.py:245-262` (e `finishcheck.py:199`) tratta invece un `sha` diverso come «approvazione superata». Conseguenze: un piano modificato dopo l'approvazione, o un `plan-approval.md` che si riferisce a un altro file, porta a `execution` con scope e task del piano *modificato*. Spec 12.4: senza prova valida la fase torna a `approval`/`spec_audit`, e 6.2 registra lo scope «alla versione approvata». Il gate rifiuterebbe poi il `finish`, ma l'adozione consegna una fase e uno scope non meritati. `SPEC_APPROVAL` e `PLAN_APPROVAL` di test_adopt.py:520-522 usano `sha: abc123`, che non è il blob, e il test (test_adopt.py:618-624) asserisce proprio `execution`, quindi fissa il comportamento errato. Correzione: la prova vale se `kind` coincide, `header["sha"]` è uguale a `git rev-parse <sha>:<path del documento>`, il documento esiste, e per il piano `header["path"] == path` del piano trovato. Altrimenti si scende di fase. Nei test usare lo sha reale e aggiungere i casi con sha superato (piano modificato dopo l'approvazione → `approval`; spec modificata → `spec_audit`) e con `path` diverso.

### Minor

2. **Output ingannevole se un passo fallisce** (adopt.py:386-395). «PR #n aperta: fase pr_open» e «tetto X ripristinato dalla PR» si aggiungono a `lines` anche quando `step(...)` ha fallito (per esempio `TransitionError` di `set_level_cap`). Escono insieme a «registrazione incompleta». Aggiungere la riga solo se `step` ha riuscito, oppure scrivere la riga dentro la lambda.
3. **Etichette dell'issue illeggibili = solo avviso** (adopt.py:245-249), mentre la PR illeggibile rifiuta. Il livello può scendere (e con esso la fase) per un errore transitorio di `gh`. È lo stesso comportamento di `openpr._labels`, e il gate ricalcola, quindi non è bloccante. Valutare un rifiuto o almeno un test. ⚠️ Nemmeno la regola «autore esterno → L2» di 6.1 (start.py:366) è applicata: la spec 12.4 dice «diff più etichette», quindi è coerente col testo, ma è una decisione da confermare.
4. **Ramo locale in ritardo sul remoto** (adopt.py:342-343): con ramo locale e remoto diversi si calcolano livello e fase sulla punta locale. Un avviso quando `origin/<ramo>` è avanti sarebbe utile (caso «altra macchina»).
5. **Accoppiamento** con `start._write_issue` e `start.EXCLUDES` (adopt.py:398, 463): già dichiarato; accettabile, meglio promuoverli a nomi pubblici quando si tocca `start`.
6. Se `acts.consume` solleva `sqlite3.Error` dopo `create_work`, `adopt()` risponde con un rifiuto (codice 1) pur lasciando il lavoro creato (adopt.py:160-161); la ripresa sarebbe `start`. Caso raro.

## Valutazione

**Qualità del task:** Da correggere
**Motivo:** Il rispetto di Review Focus 5 (nessun `--force`, nessun ramo duplicato, worktree riusato) e dei vincoli di rifiuto, atto e strati è solido. Resta però il rilievo Important 1: le approvazioni valgono come prova senza verificare lo sha del documento, quindi si può adottare in `execution` con un piano o una spec non più approvati, e il test lo fissa.
